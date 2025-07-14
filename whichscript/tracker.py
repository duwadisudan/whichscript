import builtins
import inspect
import json
import os
import shutil
from typing import Any


def _find_calling_script(current_file: str) -> str | None:
    """Return the absolute path to the calling script, if found."""
    stack = inspect.stack()
    for frame in stack:
        filename = frame.filename
        if filename != current_file:
            return os.path.abspath(filename)
    return None


def save_output(data: Any, output_path: str) -> str:
    """Save data to *output_path* and record the script that produced it.

    Parameters
    ----------
    data : Any
        Text data to store in the output file.
    output_path : str
        Path to the output file.

    Returns
    -------
    str
        Path to the metadata file describing the output.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(data))

    calling_script = _find_calling_script(__file__)
    metadata = {
        "script_path": calling_script,
    }
    meta_path = output_path + ".metadata.json"
    with open(meta_path, "w", encoding="utf-8") as mf:
        json.dump(metadata, mf, indent=2)

    if calling_script and os.path.exists(calling_script):
        shutil.copy(calling_script, output_path + ".script")

    return meta_path


# --- automatic logging ----------------------------------------------------

_original_open = builtins.open
_log_active = False
_skip_logging = False


def enable_auto_logging() -> None:
    """Start logging all file writes globally."""

    global _log_active
    if not _log_active:
        builtins.open = _logging_open  # type: ignore[assignment]
        _log_active = True


def disable_auto_logging() -> None:
    """Stop global file write logging."""

    global _log_active
    if _log_active:
        builtins.open = _original_open  # type: ignore[assignment]
        _log_active = False


def _logging_open(file: str, mode: str = "r", buffering: int = -1, encoding: str | None = None,
                  errors: str | None = None, newline: str | None = None,
                  closefd: bool = True, opener=None):
    fh = _original_open(file, mode, buffering, encoding, errors, newline, closefd, opener)
    if _log_active and not _skip_logging and any(m in mode for m in ("w", "a", "x")):
        _record_write(file, {
            "mode": mode,
            "buffering": buffering,
            "encoding": encoding,
            "errors": errors,
            "newline": newline,
            "closefd": closefd,
            "opener": bool(opener),
        })
    return fh


def _record_write(path: str, params: dict[str, Any]) -> None:
    global _skip_logging
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    calling_script = _find_calling_script(__file__)
    metadata = {
        "script_path": calling_script,
        "open_params": params,
    }
    meta_path = path + ".metadata.json"
    try:
        _skip_logging = True
        with _original_open(meta_path, "w", encoding="utf-8") as mf:
            json.dump(metadata, mf, indent=2)
        if calling_script and os.path.exists(calling_script):
            shutil.copy(calling_script, path + ".script")
    finally:
        _skip_logging = False

