import os
import shutil


def create_dirs(projectdir, dirs):
    dirs = [os.path.join(projectdir, i) for i in dirs]

    for i in dirs:
        if os.path.exists(i):
            print(f'\tSkipping existing directory: {i}')
        else:
            print(f'\tCreating directory: {i}')
            os.mkdir(i)


def get_template_dir():
    pmandir = os.path.dirname(__file__)
    return os.path.join(pmandir, 'templates')


def copy_template_files(projectdir, templatedir, templatefiles):
    for tmplfile in templatefiles:
        src = os.path.join(templatedir, tmplfile[0])
        dst = os.path.join(projectdir, tmplfile[1])
        print(f'Creating {dst}')
        if os.path.exists(dst):
            print(f'\t{dst} already exists, skipping')
        else:
            shutil.copyfile(src, dst)
            print(f'\t{src} copied to {dst}')
