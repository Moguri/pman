import typing

from dataclasses import dataclass, field

@dataclass(frozen=True)
class ConverterInfo:
    name: str
    supported_extensions: typing.List[str]
    output_extension: str = '.bam'
    function_name: str = 'convert'

@dataclass
class ConverterResult:
    input_file: str
    output_file: str
    dependencies: list[str] = field(default_factory=list)
