import os
import subprocess
from typing import (
    ClassVar,
)

from .common import ConverterInfo


class Native2BamPlugin:
    converters: ClassVar[list[ConverterInfo]] = [
        ConverterInfo(
            name='native2bam',
            supported_extensions=[
                '.egg.pz', '.egg',
                '.obj', '.mtl',
                '.fbx', '.dae',
                '.ply',
            ]
        )
    ]

    def convert(self, config, _converter_config, srcdir, dstdir, assets):
        verbose = config['general']['verbose']
        processes = []
        for asset in assets:
            if asset.endswith('.mtl'):
                # Handled by obj
                continue

            ext = '.' + asset.split('.', 1)[1]
            dst = asset.replace(srcdir, dstdir).replace(ext, '.bam')
            args = [
                'native2bam',
                asset,
                dst
            ]

            if verbose:
                print(f'Calling native2bam: {" ".join(args)}')
            processes.append(
                subprocess.Popen(args, env=os.environ.copy(), stdout=subprocess.DEVNULL)
            )

        for proc in processes:
            proc.wait()
