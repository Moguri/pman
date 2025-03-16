import collections
import concurrent.futures
import contextlib
import dataclasses
import fnmatch
import itertools
import json
import os
import pprint
import signal
import sys
import time

from rich import (
    live,
    print,  # noqa
    progress,
    table,
)

from . import plugins
from ._utils import (
    disallow_frozen,
    ensure_config,
    get_abs_path,
    get_rel_path,
    run_hooks,
)
from .plugins.common import ConverterResult


def gather_files(srcdir, include_patterns, exclude_patterns, *, verbose=False):
    found_assets = []
    for root, _dirs, files in os.walk(srcdir):
        for asset in files:
            src = os.path.join(root, asset)
            asset_path = src.replace(srcdir, '')
            include_asset = False

            for pattern in include_patterns:
                if fnmatch.fnmatch(asset_path, pattern) or fnmatch.fnmatch(asset, pattern):
                    include_asset = True
                    break

            if not include_asset:
                continue

            ignore_pattern = None
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(asset_path, pattern) or fnmatch.fnmatch(asset, pattern):
                    ignore_pattern = pattern
                    break
            if ignore_pattern is not None:
                if verbose:
                    print(
                        f'Skip building file {asset_path} that '
                        f'matched ignore pattern {ignore_pattern}'
                    )
                continue

            found_assets.append(src)

    return found_assets


def generate_auto_streams(config, converters):
    verbose = config['general']['verbose']
    srcdir = get_abs_path(config, config['build']['asset_dir'])
    ignore_patterns = config['build']['ignore_patterns']

    if verbose:
        print(f'Ignoring file patterns: {ignore_patterns}')

    # Gather files (skipping ignored files)
    found_assets = gather_files(srcdir, '*', ignore_patterns, verbose=verbose)

    # Group assets by extensions
    ext_asset_map = collections.defaultdict(list)
    for asset in found_assets:
        ext = '.' + asset.split('.', 1)[1]
        ext_asset_map[ext].append(asset)

    # Find converters for extensions
    ext_converter_map = {
        ext: converter
        for converter in converters
        for ext in converter.supported_extensions
    }
    copyfile_converter = plugins.get_converters(['copyfile'])[0]
    streams = collections.defaultdict(list)
    for ext, assets in ext_asset_map.items():
        converter = ext_converter_map.get(ext, copyfile_converter)
        streams[converter].extend(assets)

    # Build streams for each converter (including overrides)
    streams_with_overrides = []
    for converter, files in streams.items():
        confkey = getattr(converter.plugin, 'CONFIG_KEY', converter.name)
        converter_config = config.plugins.get(confkey, {})
        remaining_files = set(files)

        for override in converter_config.get('overrides', []):
            override_files = {
                i for i in files
                if (
                    fnmatch.fnmatch(i, override['pattern'])
                    or fnmatch.fnmatch(os.path.basename(i), override['pattern'])
                )
            }

            if not files:
                continue

            streams_with_overrides.append([
                converter,
                override_files,
                converter_config | override
            ])
            if verbose:
                print(
                    f'{converter.name}: Using the following override\n'
                    f'{pprint.pformat(streams_with_overrides[-1])}'
                )
            remaining_files -= override_files

        if remaining_files:
            streams_with_overrides.append([
                converter,
                remaining_files,
                converter_config
            ])

    return streams_with_overrides


def generate_explicit_streams(config, converters):
    verbose = config['general']['verbose']
    srcdir = get_abs_path(config, config['build']['asset_dir'])

    converter_map = {
        converter.name: converter
        for converter in converters
    }

    streams = []
    for stream_configs in config['build']['streams']:
        found_assets = gather_files(
            srcdir,
            stream_configs.get('include_patterns', []),
            stream_configs.get('exclude_patterns', []),
            verbose=verbose
        )
        plugin_name = stream_configs['plugin']
        converter = converter_map.get(plugin_name)
        if not converter:
            print(
                f'Failed to find plugin ({plugin_name}) for stream\n'
                f'{pprint.pformat(stream_configs)}'
            )
        streams.append([
            converter,
            found_assets,
            config.plugins.get(plugin_name, {}) | stream_configs.get('options', {})
        ])

    return streams


@ensure_config
@disallow_frozen
@run_hooks
def build(config=None):
    verbose = config['general']['verbose']
    builddb_path = os.path.join(
        config['internal']['projectdir'],
        '.pman_builddb'
    )
    show_all_jobs = config['build']['show_all_jobs']
    converters = plugins.get_converters(config['general']['plugins'])

    stime = time.perf_counter()
    print('Starting build')

    builddb = []
    try:
        if os.path.exists(builddb_path):
            with open(builddb_path, encoding='utf8') as builddb_file:
                builddb = [
                    ConverterResult(**i)
                    for i in json.load(builddb_file)
                ]
    except json.decoder.JSONDecodeError:
        pass

    builddb = {
        result.output_file: result
        for result in builddb
    }

    srcdir = get_abs_path(config, config['build']['asset_dir'])
    dstdir = get_abs_path(config, config['build']['export_dir'])

    if verbose:
        print(f'Read assets from: {srcdir}')
        print(f'Export them to: {dstdir}')


    if not os.path.exists(dstdir):
        print(f'Creating asset export directory at {dstdir}')
        os.makedirs(dstdir)


    if not os.path.exists(srcdir) or not os.path.isdir(srcdir):
        print(f'warning: could not find asset directory: {srcdir}')
        return

    if config['build']['streams']:
        streams = generate_explicit_streams(config, converters)
    else:
        streams = generate_auto_streams(config, converters)

    # Process assets
    def skip_build(converter, asset):
        if converter.output_extension:
            dst = asset.split('.', 1)[0] + converter.output_extension
        else:
            dst = asset
        dst = dst.replace(srcdir, dstdir)
        builddb_key = os.path.relpath(dst, dstdir)
        deps = [asset]
        if builddb_key in builddb:
            deps += [
                os.path.join(config['build']['asset_dir'], dep)
                for dep in builddb[builddb_key].dependencies
            ]
        skip = (
            os.path.exists(dst)
            and all(os.stat(i).st_mtime <= os.stat(dst).st_mtime for i in deps)
        )
        if skip:
            if verbose:
                print(f'Skip building up-to-date file: {get_rel_path(config, dst)}')
            return True
        return False

    max_workers = config['build']['jobs']
    if max_workers <= 0:
        max_workers = None
    pool = concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)
    jobs = []
    for converter, stream_assets, converter_config in streams:
        assets = [
            asset
            for asset in stream_assets
            if not skip_build(converter, asset)
        ]

        if not assets:
            continue

        max_batch = getattr(converter.plugin, 'BATCH_SIZE', 1)
        chunk_it = iter(assets)
        while chunk := tuple(itertools.islice(chunk_it, max_batch)):
            jobstr = f'{converter.name}: {", ".join(get_rel_path(config, i) for i in chunk)}'
            fut = pool.submit(converter.function, config, converter_config, srcdir, dstdir, chunk)
            jobs.append((jobstr, fut))


    # Display progress
    job_progress = progress.Progress(
        '[progress.description]{task.description}',
        progress.SpinnerColumn(
            finished_text='[progress.percentage]:heavy_check_mark:'
        ),
    )
    show_all = verbose or show_all_jobs
    taskids = []
    for jobstr, fut in jobs:
        taskid = job_progress.add_task(jobstr, total=None, visible=verbose)
        taskids.append((taskid, fut))

    overall_progress = progress.Progress(
        '[progress.description]{task.description}',
        progress.BarColumn(),
        progress.MofNCompleteColumn(),
    )
    overall_task = overall_progress.add_task(
        "All jobs",
        total=len(taskids),
    )

    progress_table = table.Table.grid()
    progress_table.add_row(job_progress)
    progress_table.add_row(overall_progress)

    def update_progress():
        for taskid, fut in taskids:
            job_progress.update(
                taskid,
                completed=1 if fut.done() else 0,
                total=1 if fut.running() or fut.done() else None,
                visible=fut.running() or show_all
            )
        overall_progress.update(
            overall_task,
            completed=len(jobs) - len(unfinished)
        )

    try:
        if len(jobs) > 0:
            with live.Live(progress_table):
                while unfinished := [x for x in taskids if not x[1].done()]:
                    update_progress()
                update_progress()
        pool.shutdown(wait=True)
        for _, fut in jobs:
            for result in fut.result():
                builddb[result.output_file] = result
    except KeyboardInterrupt:
        for pid in pool._processes: # noqa
            with contextlib.suppress(ProcessLookupError):
                os.kill(pid, signal.SIGKILL)
        shutdown_args = {
            'wait': False
        }
        if sys.version_info >= (3, 9):
            shutdown_args['cancel_futures'] = True
        pool.shutdown(**shutdown_args)
        raise

    with open(builddb_path, 'w', encoding='utf8') as builddb_file:
        json.dump([dataclasses.asdict(i) for i in builddb.values()], builddb_file)
    print(f':stopwatch: Build took [json.number]{time.perf_counter() - stime:.2f}s')
