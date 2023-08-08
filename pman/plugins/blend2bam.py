import fnmatch
import os
import pprint
import subprocess
import sys

from .common import ConverterInfo

class Blend2BamPlugin:
    converters = [
        ConverterInfo(
            name='blend2bam',
            supported_extensions=['.blend'],
        )
    ]

    BATCH_SIZE = 3


    CONFIG_DEFAULTS = {
        'blend2bam': {
            'blender_dir': '',
            'material_mode': 'pbr',
            'physics_engine': 'builtin',
            'animations': 'embed',
            'overrides': [],
        },
    }

    def convert(self, config, srcdir, dstdir, assets):
        verbose = config['general']['verbose']

        remaining_assets = set(assets)

        runs = []

        for override in config['blend2bam']['overrides']:
            files = {
                i for i in assets
                if (
                    fnmatch.fnmatchcase(i, override['pattern'])
                    or fnmatch.fnmatchcase(os.path.basename(i), override['pattern'])
                )
            }

            if not files:
                continue

            runs.append({
                'files': files,
                'config': config['blend2bam'] | override
            })
            if verbose:
                print(f'blend2bam: Using the following override\n{pprint.pformat(runs[-1])}')
            remaining_assets -= files

        if remaining_assets:
            runs.append({
                'files': remaining_assets,
                'config': config['blend2bam'],
            })


        for run in runs:
            conf = run['config']
            args = [
                sys.executable,
                '-m', 'blend2bam',
                '--srcdir', f'"{srcdir}"',
                '--material-mode', conf['material_mode'],
                '--physics-engine', conf['physics_engine'],
                '--textures', 'ref',
            ]

            blenderdir = conf['blender_dir']
            if blenderdir:
                args += [
                    '--blender-dir', f'"{blenderdir}"',
                ]
            args += [f'"{i}"' for i in run['files']]
            args += [
                f'"{dstdir}"'
            ]

            if verbose:
                print(f'Calling blend2bam: {" ".join(args)}')

            proc = subprocess.run(
                args,
                env=os.environ.copy(),
                text=True,
                capture_output=True,
                check=True
            )
            if verbose:
                print(proc.stdout)
            if proc.stderr:
                print(proc.stderr)
