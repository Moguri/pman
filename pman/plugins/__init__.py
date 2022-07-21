import collections
import functools


@functools.lru_cache
def _get_all_plugins():
    import pkg_resources

    def load_plugin(entrypoint):
        plugin_class = entrypoint.load()
        if not hasattr(plugin_class, 'name'):
            plugin_class.name = entrypoint.name
        return plugin_class()

    return [
        load_plugin(entrypoint)
        for entrypoint in pkg_resources.iter_entry_points('pman.plugins')
    ]


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
