import os
import subprocess


class Converter(object):
    def __init__(self, supported_exts, ext_dst_map=None):
        self.supported_exts = supported_exts
        self.ext_dst_map = ext_dst_map if ext_dst_map is not None else {}

    def __call__(self, func):
        func.supported_exts = self.supported_exts
        func.ext_dst_map = self.ext_dst_map
        return func


@Converter(['.blend'], {'.blend': '.bam'})
def converter_blend_bam(config, user_config, srcdir, dstdir, _assets):
    files_to_convert = []
    for root, _dirs, files in os.walk(srcdir):
        for asset in files:
            src = os.path.join(root, asset)
            dst = src.replace(srcdir, dstdir).replace('.blend', '.bam')

            if not asset.endswith('.blend'):
                # Only convert blend files
                continue

            if os.path.exists(dst) and os.stat(src).st_mtime <= os.stat(dst).st_mtime:
                # Don't convert up-to-date-files
                continue

            files_to_convert.append(os.path.abspath(src))

    if files_to_convert is None:
        return

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
    args += files_to_convert
    args += [
        dstdir
    ]

    print("Calling blend2bam: {}".format(' '.join(args)))

    subprocess.call(args, env=os.environ.copy())
