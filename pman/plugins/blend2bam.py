import fnmatch
import os
import pprint
import subprocess
import sys

from .common import ConverterInfo

class Blend2BamPlugin:
    converters = [
        ConverterInfo(supported_extensions=['.blend'])
    ]


    CONFIG_DEFAULTS = {
        'blend2bam': {
            'blender_dir': '',
            'material_mode': 'pbr',
            'physics_engine': 'builtin',
            'pipeline': 'gltf',
            'animations': 'embed',
            'overrides': [],
        },
    }

    def convert(self, config, srcdir, dstdir, assets):
        import blend2bam

        verbose = config['general']['verbose']

        blend2bam_version = [int(i) for i in blend2bam.__version__.split('.')]

        remaining_assets = set(assets)

        default_mat_mode = config['blend2bam']['material_mode']
        default_phy_engine = config['blend2bam']['physics_engine']
        default_pipeline = config['blend2bam']['pipeline']
        default_animations = config['blend2bam']['animations']
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
                'material_mode': override.get('material_mode', default_mat_mode),
                'physics_engine': override.get('physics_engine', default_phy_engine),
                'pipeline': override.get('pipeline', default_pipeline),
                'animations': override.get('animations', default_animations),
            })
            if verbose:
                print('blend2bam: Using the following override\n{}'.format(
                    pprint.pformat(runs[-1])
                ))
            remaining_assets -= files

        if remaining_assets:
            runs.append({
                'files': remaining_assets,
                'material_mode': default_mat_mode,
                'physics_engine': default_phy_engine,
                'pipeline': default_pipeline,
                'animations': default_animations,
            })


        for run in runs:
            args = [
                sys.executable,
                '-m', 'blend2bam',
                '--srcdir', f'"{srcdir}"',
                '--material-mode', run['material_mode'],
                '--physics-engine', run['physics_engine'],
                '--pipeline', run['pipeline'],
                '--textures', 'ref',
            ]

            if blend2bam_version[0] != 0 or blend2bam_version[1] >= 17:
                args += [
                    '--animations', run['animations']
                ]
            elif run['animations'] != default_animations:
                raise RuntimeError(
                    'blend2bam >= 0.17 is required for animations values other'
                    f' than "{default_animations}"'
                )

            blenderdir = config['blend2bam']['blender_dir']
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

            subprocess.check_call(args, env=os.environ.copy(), stdout=subprocess.DEVNULL)
