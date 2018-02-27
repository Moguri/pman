import imp
import os

try:
    import pman
except ImportError:
    try:
        from . import pman
    except ImportError:
        import blenderpanda.pman as pman


_SRGB_VERT = """
#version 120

uniform mat4 p3d_ModelViewProjectionMatrix;

attribute vec4 p3d_Vertex;
attribute vec2 p3d_MultiTexCoord0;

varying vec2 texcoord;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    texcoord = p3d_MultiTexCoord0;
}
"""


_SRGB_FRAG = """
#version 120

uniform sampler2D tex;

varying vec2 texcoord;


void main() {
    vec3 color = pow(texture2D(tex, texcoord).rgb, vec3(1.0/2.2));
    gl_FragColor = vec4(color, 1.0);
}
"""


class BasicRenderManager:
    def __init__(self, base):
        import panda3d.core as p3d
        from direct.filter.FilterManager import FilterManager

        self.base = base
        self.base.render.set_shader_auto()

        p3d.Texture.setTexturesPower2(p3d.ATS_none)

        manager = FilterManager(base.win, base.cam)
        self.post_tex = p3d.Texture()
        post_quad = manager.renderSceneInto(colortex=self.post_tex)
        post_quad.set_shader(p3d.Shader.make(p3d.Shader.SL_GLSL, _SRGB_VERT, _SRGB_FRAG))
        post_quad.set_shader_input('tex', self.post_tex)


def create_render_manager(base, config=None):
    if config is None:
        try:
            config = pman.get_config()
        except pman.NoConfigError:
            print("RenderManager: Could not find pman config, falling back to basic plugin")
            config = None

    renderplugin = config['general']['render_plugin'] if config else ''

    if not renderplugin:
        return BasicRenderManager(base)

    rppath = pman.get_abs_path(config, renderplugin)
    maindir = os.path.dirname(pman.get_abs_path(config, config['run']['main_file']))
    rppath = os.path.splitext(os.path.relpath(rppath, maindir))[0]
    module_parts = rppath.split(os.sep)

    modname = '.'.join(module_parts)
    print(modname)
    try:
        mod = pman.load_module(modname, config)
    except ImportError:
        print("RenderManager: Could not find module ({}), falling back to basic plugin".format(modname))
        return BasicRenderManager(base)

    return mod.get_plugin()(base)
