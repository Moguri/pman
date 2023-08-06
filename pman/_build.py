import collections
import concurrent.futures
import fnmatch
import itertools
import os
import signal
import time

# pylint: disable=redefined-builtin
from rich import (
    live,
    print,
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

@ensure_config
@disallow_frozen
@run_hooks
def build(config=None):
    verbose = config['general']['verbose']
    converters = plugins.get_converters(config['general']['plugins'])

    stime = time.perf_counter()
    print('Starting build')

    srcdir = get_abs_path(config, config['build']['asset_dir'])
    dstdir = get_abs_path(config, config['build']['export_dir'])

    if verbose:
        print(f'Read assets from: {srcdir}')
        print(f'Export them to: {dstdir}')

    ignore_patterns = config['build']['ignore_patterns']

    if verbose:
        print(f'Ignoring file patterns: {ignore_patterns}')

    if not os.path.exists(dstdir):
        print(f'Creating asset export directory at {dstdir}')
        os.makedirs(dstdir)


    if not os.path.exists(srcdir) or not os.path.isdir(srcdir):
        print(f'warning: could not find asset directory: {srcdir}')
        return

    # Gather files (skipping ignored files)
    found_assets = []
    for root, _dirs, files in os.walk(srcdir):
        for asset in files:
            src = os.path.join(root, asset)

            ignore_pattern = None
            asset_path = src.replace(srcdir, '')
            for pattern in ignore_patterns:
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

    # Process assets
    def skip_build(converter, asset):
        if converter.output_extension:
            dst = asset.split('.', 1)[0] + converter.output_extension
        else:
            dst = asset
        dst = dst.replace(srcdir, dstdir)
        if os.path.exists(dst) and os.stat(asset).st_mtime <= os.stat(dst).st_mtime:
            if verbose:
                print(f'Skip building up-to-date file: {get_rel_path(config, dst)}')
            return True
        return False

    max_workers = config['build']['jobs']
    max_batch = 1
    if max_workers <= 0:
        max_workers = None
    pool = concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)
    jobs = []
    for converter, assets in streams.items():
        assets = [
            asset
            for asset in assets
            if not skip_build(converter, asset)
        ]

        if not assets:
            continue

        chunk_it = iter(assets)
        while chunk := tuple(itertools.islice(chunk_it, max_batch)):
            jobstr = f'{converter.name}: {", ".join(get_rel_path(config, i) for i in chunk)}'
            fut = pool.submit(converter.function, config, srcdir, dstdir, chunk)
            jobs.append((jobstr, fut))


    # Display progress
    job_progress = progress.Progress(
        '[progress.description]{task.description}',
        progress.SpinnerColumn(
            finished_text='[progress.percentage]:heavy_check_mark:'
        ),
    )
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
        total = len(taskids)
    )

    progress_table = table.Table.grid()
    progress_table.add_row(job_progress)
    progress_table.add_row(overall_progress)

    def update_progress():
        for taskid, fut in taskids:
            job_progress.update(
                taskid,
                completed=1 if fut.done() else 0,
                total=1 if fut.running() or fut.done() else 0,
                visible=fut.running() or verbose
            )
        overall_progress.update(
            overall_task,
            completed=len(jobs) - len(unfinished)
        )

    try:
        with live.Live(progress_table):
            while unfinished := [x for x in taskids if not x[1].done()]:
                update_progress()
            update_progress()
        pool.shutdown(wait=True)
        for _, fut in jobs:
            fut.result()
    except KeyboardInterrupt as exc:
        for pid in pool._processes: # pylint: disable=protected-access
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        pool.shutdown(wait=False, cancel_futures=True)
        raise exc

    print(f':stopwatch: Build took {time.perf_counter() - stime:.4f}s')
