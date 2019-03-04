import argparse
import os

import panda3d.core as p3d


CONFIG_DATA = """
assimp-gen-normals true
"""

p3d.load_prc_file_data('', CONFIG_DATA)


def main():
    parser = argparse.ArgumentParser(
        description='A tool for creating BAM files from Panda3D supported file formats'
    )

    parser.add_argument('src', type=str, help='source path')
    parser.add_argument('dst', type=str, help='destination path')

    args = parser.parse_args()

    src = p3d.Filename.from_os_specific(os.path.abspath(args.src))
    dst = p3d.Filename.from_os_specific(os.path.abspath(args.dst))


    loader = p3d.Loader.get_global_ptr()
    options = p3d.LoaderOptions()
    options.flags |= p3d.LoaderOptions.LF_no_cache

    p3d.NodePath(loader.load_sync(src, options)).write_bam_file(dst)


if __name__ == '__main__':
    main()
