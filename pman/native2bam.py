import argparse
import os

import panda3d.core as p3d


CONFIG_DATA = """
assimp-gen-normals true
bam-texture-mode unchanged
"""

p3d.load_prc_file_data('', CONFIG_DATA)


def make_texpath_relative(node, srcdir):
    geomnode = node.node()
    for idx, renderstate in enumerate(geomnode.get_geom_states()):
        texattrib = renderstate.get_attrib(p3d.TextureAttrib)
        if texattrib:
            for texstage in texattrib.get_on_stages():
                texture = texattrib.get_on_texture(texstage)
                texture.filename = os.path.relpath(texture.filename, srcdir)
            renderstate = renderstate.set_attrib(texattrib)
        geomnode.set_geom_state(idx, renderstate)



def main():
    parser = argparse.ArgumentParser(
        description='A tool for creating BAM files from Panda3D supported file formats'
    )

    parser.add_argument('src', type=str, help='source path')
    parser.add_argument('dst', type=str, help='destination path')

    args = parser.parse_args()

    src = p3d.Filename.from_os_specific(os.path.abspath(args.src))
    dst = p3d.Filename.from_os_specific(os.path.abspath(args.dst))

    dst.make_dir()

    loader = p3d.Loader.get_global_ptr()
    options = p3d.LoaderOptions()
    options.flags |= p3d.LoaderOptions.LF_no_cache

    scene = p3d.NodePath(loader.load_sync(src, options))

    # Update texture paths
    for node in scene.find_all_matches('**/+GeomNode'):
        make_texpath_relative(node, src.get_dirname())

    scene.write_bam_file(dst)


if __name__ == '__main__':
    main()
