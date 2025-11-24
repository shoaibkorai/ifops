"""
Custom exceptions for IFOps CLI.
"""


class IFOpsError(Exception):
    """Base exception for IFOps."""
    pass


class AWSError(IFOpsError):
    """AWS-related errors."""
    pass


class ConfigurationError(IFOpsError):
    """Configuration-related errors."""
    pass


class ValidationError(IFOpsError):
    """Input validation errors."""
    pass


class ResourceNotFoundError(IFOpsError):
    """Resource not found errors."""
    pass


class ResourceAlreadyExistsError(IFOpsError):
    """Resource already exists errors."""
    pass


class DeploymentError(IFOpsError):
    """Deployment-related errors."""
    pass


class AuthenticationError(IFOpsError):
    """Authentication-related errors."""
    pass
