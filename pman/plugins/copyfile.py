import os
import shutil

from .common import (
    ConverterInfo,
    ConverterResult,
)


class CopyFilePlugin:
    converters = [
        ConverterInfo(
            name='copyfile',
            supported_extensions=[],
            output_extension='',
        )
    ]

    def convert(self, config, srcdir, dstdir, assets):
        results: list[ConverterResult] = []
        assetdir = config['build']['asset_dir']
        exportdir = config['build']['export_dir']

        for asset in assets:
            src = asset
            dst = src.replace(srcdir, dstdir)
            if not os.path.exists(os.path.dirname(dst)):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            results.append(ConverterResult(
                input_file=os.path.relpath(src, assetdir),
                output_file=os.path.relpath(dst, exportdir)
            ))

        return results
