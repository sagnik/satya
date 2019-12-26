from annotate.consts import *


class CustomException(Exception):
    """
    if there is an error reading the config
    """

    def __init__(self, msg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg = msg


class ConfigReadError(CustomException):
    def __init__(self, msg, *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


class UnknownFileFormatError(CustomException):
    def __init__(self, file_name, *args, **kwargs):
        super().__init__(
            f'{file_name} has unknown file format, use following extension {ALLOWED_FILE_TYPE}', *args, **kwargs
        )


class NoFileFoundError(CustomException):
    def __init__(self, file_name, *args, **kwargs):
        super().__init__(f'no file at location {file_name}', *args, **kwargs)


class NoTagSelectedError(CustomException):
    def __init__(self, msg, *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


class TagLevelHierarchyError(CustomException):
    def __init__(self, msg, *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
