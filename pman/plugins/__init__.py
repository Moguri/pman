import collections
import functools


@functools.lru_cache(maxsize=None)
def _get_all_plugins():
    import pkg_resources

    def load_plugin(entrypoint):
        try:
            plugin_class = entrypoint.load()
        except ModuleNotFoundError:
            return None
        if not hasattr(plugin_class, 'name'):
            plugin_class.name = entrypoint.name
        return plugin_class()

    return [plugin for plugin in [
        load_plugin(entrypoint)
        for entrypoint in pkg_resources.iter_entry_points('pman.plugins')
    ] if plugin is not None]


def _get_project_plugins():
    import glob
    import importlib
    import os
    import sys
    
    plugins = []
    sys.path = [os.getcwd()] + sys.path
    
    plugins_path = os.path.join(os.getcwd(), "plugins")
    for python_file in glob.glob(plugins_path + "/*.py"):
        plugin_name = os.path.splitext(os.path.basename(python_file))[0]
        if plugin_name == "__init__":
            continue
        module = importlib.import_module("plugins." + plugin_name)
        for attrib in dir(module):
            if attrib.endswith("Plugin"):
                project_plugin = getattr(module, attrib)()
                project_plugin.name = plugin_name
                plugins.append(project_plugin)
                
    return plugins


def get_plugins(*, filter_names=None, has_attr=None):
    plugins = _get_all_plugins() + _get_project_plugins()

    def use_plugin(plugin):
        return (
            (not has_attr or hasattr(plugin, has_attr))
            and (not filter_names or plugin.name in filter_names)
        )

    return [
        plugin
        for plugin in plugins
        if use_plugin(plugin)
    ]


def get_converters(plugin_names):
    plugins = get_plugins(filter_names=plugin_names, has_attr='converters')

    Converter = collections.namedtuple('Converter', [
        'name',
        'supported_extensions',
        'output_extension',
        'function',
        'plugin',
    ])

    return [
        Converter(
            cinfo.name,
            tuple(cinfo.supported_extensions),
            cinfo.output_extension,
            getattr(plugin, cinfo.function_name),
            plugin,
        )
        for plugin in plugins
        for cinfo in plugin.converters
    ]
