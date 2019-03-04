import os
import subprocess


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
def converter_blend_bam(config, user_config, srcdir, dstdir, assets):
    args = [
        'blend2bam',
        '--srcdir', srcdir,
        '--material-mode', config['general']['material_mode'],
        '--physics-engine', config['general']['physics_engine'],
    ]
    if user_config['blender']['use_last_path']:
        blenderdir = os.path.dirname(user_config['blender']['last_path'])
        args += [
            '--blender-dir', blenderdir,
        ]
    args += assets
    args += [
        dstdir
    ]

    # print("Calling blend2bam: {}".format(' '.join(args)))

    subprocess.call(args, env=os.environ.copy(), stdout=subprocess.DEVNULL)

@Converter(['.egg', '.egg.pz'])
def converter_egg_bam(_config, _user_config, srcdir, dstdir, assets):
    for asset in assets:
        dst = asset.replace(srcdir, dstdir).replace('.egg.pz', '.bam').replace('.egg', '.bam')
        args = [
            'egg2bam',
            '-o', dst,
            '-pd', srcdir,
            '-ps', 'rel',
            asset,
        ]

        # print("Calling egg2bam: {}".format(' '.join(args)))
        subprocess.call(args, env=os.environ.copy(), stdout=subprocess.DEVNULL)
