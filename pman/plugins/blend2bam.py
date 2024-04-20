import os
import subprocess
import sys
from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Any,
    ClassVar,
    Literal,
)

from .common import (
    ConverterInfo,
    ConverterResult,
)


class Blend2BamPlugin:
    converters: ClassVar[list[ConverterInfo]] = [
        ConverterInfo(
            name='blend2bam',
            supported_extensions=['.blend'],
        )
    ]

    BATCH_SIZE = 3

    CONFIG_KEY='blend2bam'
    @dataclass
    class Config:
        blender_dir: str = ''
        material_mode: Literal['pbr', 'legacy'] = 'pbr'
        physics_engine: Literal['builtin', 'bullet'] = 'builtin'
        animations: Literal['embed', 'skip'] = 'embed'
        textures: Literal['ref', 'copy', 'embed'] = 'ref'
        overrides: dict[str, Any] = field(default_factory=dict)

        def __getitem__(self, key):
            return getattr(self, key)

    def convert(self, config, converter_config, srcdir, dstdir, assets):
        verbose = config['general']['verbose']
        assetdir = config['build']['asset_dir']
        results: list[ConverterResult] = []

        args = [
            sys.executable,
            '-u',
            '-m', 'blend2bam',
            '--srcdir', f'"{srcdir}"',
            '--material-mode', converter_config['material_mode'],
            '--physics-engine', converter_config['physics_engine'],
            '--textures', converter_config['textures'],
            '--animations', converter_config['animations'],
        ]

        blenderdir = converter_config['blender_dir']
        if blenderdir:
            args += [
                '--blender-dir', f'"{blenderdir}"',
            ]
        args += [f'"{i}"' for i in assets]
        args += [
            f'"{dstdir}"'
        ]

        if verbose:
            print(f'Calling blend2bam: {" ".join(args)}')

        proc = subprocess.run(
            args,
            env=os.environ.copy(),
            text=True,
            capture_output=True,
            check=False,
        )
        if verbose:
            print(proc.stdout)
        if proc.stderr:
            print(proc.stderr)

        output = proc.stdout.split('Read blend: ')[1:]
        for blend in output:
            input_file = os.path.relpath(blend.splitlines()[0].replace('"', ''), assetdir)
            output_file = input_file.rsplit('.blend', 1)[0] + '.bam'
            results.append(ConverterResult(
                input_file=input_file,
                output_file=output_file,
                dependencies=[
                    os.path.relpath(i.split()[3].replace("'", '').replace(',', ''), assetdir)
                    for i in blend.splitlines()
                    if i.startswith('Info: Read library')
                ]
            ))

        proc.check_returncode()
        return results
