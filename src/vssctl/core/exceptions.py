class ValidationError(Exception):
    """Base validation exception."""


class DuplicateSignalError(ValidationError):
    pass


class InvalidDatatypeError(ValidationError):
    pass


class InvalidParentError(ValidationError):
    pass


class InvalidNameError(ValidationError):
    pass


class InvalidUnitError(ValidationError):
    pass