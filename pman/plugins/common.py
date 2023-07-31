import typing

from dataclasses import dataclass

@dataclass(frozen=True)
class ConverterInfo:
    name: str
    supported_extensions: typing.List[str]
    output_extension: str = '.bam'
    function_name: str = 'convert'
