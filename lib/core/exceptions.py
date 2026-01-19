"""
Custom Exceptions for NS-3 Simulations

Hierarchical exception classes for better error handling and debugging.
"""


class SimulationError(Exception):
    """Base exception for all simulation-related errors."""
    pass


class ConfigurationError(SimulationError):
    """Raised when simulation configuration is invalid."""
    pass


class NetworkSetupError(SimulationError):
    """Raised when network configuration fails."""
    pass


class NodeCreationError(SimulationError):
    """Raised when node creation or configuration fails."""
    pass


class MobilityConfigurationError(SimulationError):
    """Raised when mobility model configuration fails."""
    pass


class ProtocolError(SimulationError):
    """Raised when protocol setup or execution fails."""
    pass


class FeatureExtractionError(SimulationError):
    """Raised when feature extraction or export fails."""
    pass


class VisualizationError(SimulationError):
    """Raised when visualization setup fails (non-critical)."""
    pass
