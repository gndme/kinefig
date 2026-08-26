"""KineFig core exceptions."""


class KineFigError(Exception):
    """Base exception for all KineFig errors."""
    pass


class KineFigValidationError(KineFigError, ValueError):
    """Raised when a user parameter or geometric constraint is invalid."""
    pass
