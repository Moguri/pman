class PManError(Exception):
    pass


class NoConfigError(PManError):
    pass


class ConfigError(PManError):
    pass


class CouldNotFindPythonError(PManError):
    pass


class BuildError(PManError):
    pass


class FrozenEnvironmentError(PManError):
    def __init__(self):
        super().__init__("Operation not supported in frozen applications")
