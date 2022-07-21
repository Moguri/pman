class PManException(Exception):
    pass


class NoConfigError(PManException):
    pass


class ConfigError(PManException):
    pass


class CouldNotFindPythonError(PManException):
    pass


class BuildError(PManException):
    pass


class FrozenEnvironmentError(PManException):
    def __init__(self):
        super().__init__("Operation not supported in frozen applications")
