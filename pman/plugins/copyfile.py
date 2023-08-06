import os
import shutil

from .common import ConverterInfo


class CopyFilePlugin:
    converters = [
        ConverterInfo(
            name='copyfile',
            supported_extensions=[],
            output_extension='',
        )
    ]

    def convert(self, _config, srcdir, dstdir, assets):
        for asset in assets:
            src = asset
            dst = src.replace(srcdir, dstdir)
            if not os.path.exists(os.path.dirname(dst)):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
