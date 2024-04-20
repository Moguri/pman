import collections
import functools


@functools.lru_cache(maxsize=None)
def _get_all_plugins():
    from importlib.metadata import entry_points

    def load_plugin(entrypoint):
        plugin_class = entrypoint.load()
        if not hasattr(plugin_class, 'name'):
            plugin_class.name = entrypoint.name
        return plugin_class()

    eps = entry_points()
    if isinstance(eps, dict): # Python 3.8 and 3.9 # noqa: SIM108
        plugins = eps.get('pman.plugins')
    else:
        plugins = eps.select(group='pman.plugins')

    return [
        load_plugin(entrypoint)
        for entrypoint in plugins
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
