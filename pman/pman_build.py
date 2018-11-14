from __future__ import print_function

import sys
import os

#pylint:disable=import-error
import bpy
import addon_utils


if 'FileExistsError' not in globals():
    #pylint:disable=redefined-builtin
    FileExistsError = IOError


def main():
    # Make sure BlenderPanda addon is enabled
    addon_utils.enable("BlenderPanda", persistent=True)

    args = sys.argv[sys.argv.index('--')+1:]

    #print(args)
    srcdir, dstdir = args[0], args[1]

    #print('Exporting:', srcdir)
    #print('Export to:', dstdir)

    for root, _dirs, files in os.walk(srcdir):
        for asset in files:
            src = os.path.join(root, asset)
            dst = src.replace(srcdir, dstdir).replace('.blend', '.bam')

            if not asset.endswith('.blend'):
                # Only convert blend files with pman_build stub
                continue

            if os.path.exists(dst) and os.stat(src).st_mtime <= os.stat(dst).st_mtime:
                # Don't convert up-to-date-files
                continue

            if asset.endswith('.blend'):
                print('Converting .blend file ({}) to .bam ({})'.format(src, dst))
                try:
                    os.makedirs(os.path.dirname(dst))
                except FileExistsError:
                    pass
                bpy.ops.wm.open_mainfile(filepath=src)
                bpy.ops.panda_engine.export_bam(
                    filepath=dst, copy_images=False, skip_up_to_date=True
                )


if __name__ == '__main__':
    main()
