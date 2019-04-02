import panda3d.core as p3d

from . import core as pman


def init(base):
    if pman.is_frozen():
        config = None
        # Add fix asset directory to model path
        p3d.load_prc_file_data('pman', 'model-path $MAIN_DIR/assets')
    else:
        config = pman.get_config()
        if config['run']['auto_build']:
            pman.build(config)
        exportdir = pman.get_abs_path(config, config['build']['export_dir'])

        # Add export directory to model path
        exportdir = p3d.Filename.from_os_specific(exportdir)
        p3d.get_model_path().prepend_directory(exportdir)

    # Setup renderer
    pman.create_renderer(base, config)
