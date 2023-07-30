import collections
import fnmatch
import os
import time

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
    for converter, assets in streams.items():
        def skip_build(asset):
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

        assets = list(filter(lambda x: not skip_build(x), assets))

        if not assets:
            continue

        print(f'Processing files with {converter.plugin.__class__.__name__}:')
        for asset in assets:
            print(f'\t{get_rel_path(config, asset)}')

        converter.function(config, srcdir, dstdir, assets)


    print(f'Build took {time.perf_counter() - stime:.4f}s')
