"""Utility to track scripts that generate outputs."""

__version__ = "0.2.0"

from .tracker import (
    save_output,
    enable_auto_logging,
    disable_auto_logging,
    configure,
)

__all__ = [
    "save_output",
    "enable_auto_logging",
    "disable_auto_logging",
    "configure",
    "__version__",
]
