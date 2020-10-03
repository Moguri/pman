import fnmatch
import os
import pprint
import subprocess
import sys

from . import creationutils

class Converter(object):
    def __init__(self, supported_exts, ext_dst_map=None):
        self.supported_exts = supported_exts
        if ext_dst_map is None:
            self.ext_dst_map = {
                ext: '.bam'
                for ext in supported_exts
            }
        else:
            self.ext_dst_map = ext_dst_map

    def __call__(self, func):
        func.supported_exts = self.supported_exts
        func.ext_dst_map = self.ext_dst_map
        return func


@Converter(['.blend'])
def converter_blend_bam(config, srcdir, dstdir, assets):
    import blend2bam

    remaining_assets = set(assets)

    default_mat_mode = config['blend2bam']['material_mode']
    default_phy_engine = config['blend2bam']['physics_engine']
    default_pipeline = config['blend2bam']['pipeline']
    runs = []

    for override in config['blend2bam']['overrides']:
        files = {
            i for i in assets if fnmatch.fnmatchcase(i, override['pattern'])
        }

        if not files:
            continue

        runs.append({
            'files': files,
            'material_mode': override.get('material_mode', default_mat_mode),
            'physics_engine': override.get('physics_engine', default_phy_engine),
            'pipeline': override.get('pipeline', default_pipeline),
        })
        print('blend2bam: Using the following override\n{}'.format(
            pprint.pformat(runs[-1])
        ))
        remaining_assets -= files

    runs.append({
        'files': remaining_assets,
        'material_mode': default_mat_mode,
        'physics_engine': default_phy_engine,
        'pipeline': default_pipeline,
    })


    for run in runs:
        args = [
            sys.executable,
            '-m', 'blend2bam',
            '--srcdir', f'"{srcdir}"',
            '--material-mode', run['material_mode'],
            '--physics-engine', run['physics_engine'],
            '--pipeline', run['pipeline'],
        ]

        blenderdir = config['blend2bam']['blender_dir']
        if blenderdir:
            args += [
                '--blender-dir', f'"{blenderdir}"',
            ]
        args += [f'"{i}"' for i in run['files']]
        args += [
            f'"{dstdir}"'
        ]

        print("Calling blend2bam: {}".format(' '.join(args)))

        subprocess.check_call(args, env=os.environ.copy(), stdout=subprocess.DEVNULL)

@Converter([
    '.egg.pz', '.egg',
    '.obj', '.mtl',
    '.fbx', '.dae',
    '.ply',
])
def converter_native_bam(_config, srcdir, dstdir, assets):
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

        # print("Calling native2bam: {}".format(' '.join(args)))
        processes.append(subprocess.Popen(args, env=os.environ.copy(), stdout=subprocess.DEVNULL))

    for proc in processes:
        proc.wait()


def create_git(projectdir, config):
    if not os.path.exists(os.path.join(projectdir, '.git')):
        args = [
            'git',
            'init',
            '.'
        ]
        subprocess.call(args, env=os.environ.copy())

    templatedir = creationutils.get_template_dir()
    creationutils.copy_template_files(projectdir, templatedir, (
        ('panda.gitignore', '.gitignore'),
    ))

    gitignorepath = os.path.join(projectdir, '.gitignore')
    add_export_dir = False
    with open(gitignorepath, 'r') as gitignorefile:
        if config['build']['export_dir'] not in gitignorefile.readlines():
            add_export_dir = True

    if add_export_dir:
        with open(gitignorepath, 'a') as gitignorefile:
            gitignorefile.write(config['build']['export_dir'])
