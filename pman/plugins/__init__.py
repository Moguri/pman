import collections
import functools


@functools.lru_cache(maxsize=None)
def _get_all_plugins():
    import os
    import sys
    import glob
    
    sys.path = [os.getcwd()] + sys.path
    import pkg_resources
    
    pkg_resources.working_set.add_entry(os.getcwd())
    localplugins = []
    for modulefile in glob.glob(os.path.join(os.getcwd(), "plugins") + "/*.py"):
        modulename = os.path.splitext(os.path.basename(modulefile))[0]
        if not modulename.startswith('__'):
            localplugins.append((modulename, "plugins."+modulename, modulename.title()+"Plugin"))

    distributions, errors = pkg_resources.working_set.find_plugins(pkg_resources.Environment(sys.path))
    new_entries = []
    for dist in distributions:
        if dist.location == os.getcwd():
            for plugin in localplugins:
                name, group, classname = plugin
                new_entries.append(pkg_resources.EntryPoint(name, group, attrs=([classname]), extras=(), dist=dist))

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
    ] + [
        load_plugin(entrypoint)
        for entrypoint in new_entries
    ] if plugin is not None]


def get_plugins(*, filter_names=None, has_attr=None):
    plugins = _get_all_plugins()

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
        'supported_extensions',
        'output_extension',
        'function'
    ])

    return [
        Converter(
            cinfo.supported_extensions,
            cinfo.output_extension,
            getattr(plugin, cinfo.function_name)
        )
        for plugin in plugins
        for cinfo in plugin.converters
    ]
