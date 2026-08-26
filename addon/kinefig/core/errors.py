"""KineFig core exceptions."""


class KineFigError(Exception):
    """Base exception for all KineFig errors."""
    pass


class KineFigValidationError(KineFigError, ValueError):
    """Raised when a user parameter or geometric constraint is invalid."""
    pass


class KineFigGeometryError(KineFigError, RuntimeError):
    """Raised when a geometry operation (e.g. Boolean union, mesh evaluation) fails."""
    pass
