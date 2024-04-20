import panda3d.core as p3d

from ._build import build
from ._utils import (
    get_config,
    is_frozen,
)


def init(_base):
    assetdir_rel = p3d.Filename('assets')
    config = None

    if not is_frozen():
        config = get_config()
        if config['run']['auto_build']:
            build(config)
        assetdir_rel = p3d.Filename.from_os_specific(config['build']['export_dir'])

    # Add assets directory to model path
    assetdir = p3d.Filename(p3d.Filename.expand_from('$MAIN_DIR'), assetdir_rel)
    p3d.get_model_path().prepend_directory(assetdir)
