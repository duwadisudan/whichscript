"""Utility to track scripts that generate outputs."""

from .tracker import (
    save_output,
    enable_auto_logging,
    disable_auto_logging,
)

__all__ = ["save_output", "enable_auto_logging", "disable_auto_logging"]
