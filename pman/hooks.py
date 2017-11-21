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
def converter_blend_bam(_config, user_config, srcdir, dstdir, _assets):
    use_last_path = user_config['blender']['use_last_path']
    blender_path = user_config['blender']['last_path'] if use_last_path else 'blender'
    args = [
        blender_path,
        '-b',
        '-P',
        os.path.join(os.path.dirname(__file__), 'pman_build.py'),
        '--',
        srcdir,
        dstdir,
    ]

    #print("Calling blender: {}".format(' '.join(args)))

    subprocess.call(args, env=os.environ.copy())
