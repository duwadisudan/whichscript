import builtins
import inspect
import json
import os
import shutil
import sys
import platform
import hashlib
import subprocess
from datetime import datetime
from typing import Any


# --- helpers ---------------------------------------------------------------

def _find_calling_script(current_file: str) -> str | None:
    """Return the top-level user script that ultimately triggered the write."""
    for frame in reversed(inspect.stack()):
        raw_filename = frame.filename
        if raw_filename == current_file or raw_filename.startswith("<"):
            continue
        filename = os.path.abspath(raw_filename)
        if filename.startswith(sys.base_prefix) or "site-packages" in filename:
            continue
        return filename
    return None


def _env_flag(name: str, default: str = "1") -> bool:
    val = os.environ.get(name, default)
    if val is None:
        val = default
    return str(val).strip().lower() not in ("0", "false", "no", "off")


# --- runtime configuration (env + runtime overrides) ----------------------

_cfg_write_metadata: bool = _env_flag("WHICH_SCRIPT_METADATA", "1")
_cfg_snapshot_script: bool = _env_flag("WHICH_SCRIPT_SNAPSHOT", "1")
_cfg_snapshot_py: bool = _env_flag("WHICH_SCRIPT_SNAPSHOT_PY", "1")


def configure(*, metadata: bool | None = None,
              snapshot_script: bool | None = None,
              snapshot_py: bool | None = None) -> None:
    """Configure whichscript behavior at runtime.

    Parameters
    ----------
    metadata : bool | None
        If False, skip writing `<output>.metadata.json` files.
    snapshot_script : bool | None
        If False, skip writing `<output>.script` snapshots.
    snapshot_py : bool | None
        If False, skip writing `<output>.script.py` snapshots.
    """
    global _cfg_write_metadata, _cfg_snapshot_script, _cfg_snapshot_py
    if metadata is not None:
        _cfg_write_metadata = bool(metadata)
    if snapshot_script is not None:
        _cfg_snapshot_script = bool(snapshot_script)
    if snapshot_py is not None:
        _cfg_snapshot_py = bool(snapshot_py)



def _write_script_snapshots(target_base: str, script_path: str) -> None:
    """Write side-by-side script snapshots according to config flags, safely."""
    global _skip_logging
    # Avoid recursion if we are handling snapshot files themselves
    if target_base.endswith(".script") or target_base.endswith(".script.py"):
        return
    if not (_cfg_snapshot_script or _cfg_snapshot_py):
        return
    try:
        _skip_logging = True
        if _cfg_snapshot_script:
            try:
                shutil.copy(script_path, target_base + ".script")
            except Exception:
                pass
        if _cfg_snapshot_py:
            try:
                shutil.copy(script_path, target_base + ".script.py")
            except Exception:
                pass
    finally:
        _skip_logging = False
_runtime_cache: dict[str, Any] | None = None


def _safe_pip_freeze() -> list[str]:
    try:
        out = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True, timeout=20)
        if out.returncode == 0:
            return [line.strip() for line in out.stdout.splitlines() if line.strip()]
    except Exception:
        pass
    return []


def _git_info(script_path: str | None) -> dict[str, Any] | None:
    try:
        if not script_path:
            return None
        repo_dir = os.path.dirname(os.path.abspath(script_path))
        if shutil.which("git") is None:
            return None
        def _run(args: list[str]) -> str | None:
            try:
                cp = subprocess.run(["git", "-C", repo_dir] + args, capture_output=True, text=True, timeout=5)
                if cp.returncode == 0:
                    return cp.stdout.strip()
            except Exception:
                return None
            return None
        root = _run(["rev-parse", "--show-toplevel"]) or None
        commit = _run(["rev-parse", "HEAD"]) or None
        status = _run(["status", "--porcelain"]) or None
        return {"root": root, "commit": commit, "dirty": bool(status)}
    except Exception:
        return None


def _sha256(path: str) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def _collect_runtime_metadata(calling_script: str | None) -> dict[str, Any]:
    global _runtime_cache
    if _runtime_cache is None:
        try:
            from . import __version__ as whichscript_version  # type: ignore
        except Exception:
            whichscript_version = None  # type: ignore
        _runtime_cache = {
            "whichscript": {"version": whichscript_version},
            "python": {
                "version": sys.version,
                "executable": sys.executable,
                "implementation": platform.python_implementation(),
            },
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
            },
            "env": {
                "conda_env": os.environ.get("CONDA_DEFAULT_ENV"),
                "virtual_env": os.environ.get("VIRTUAL_ENV"),
                "pythonpath": os.environ.get("PYTHONPATH"),
            },
            "packages": {"pip_freeze": _safe_pip_freeze()},
        }
    meta = {
        "timestamp": datetime.now().isoformat(timespec='seconds'),
        "cwd": os.getcwd(),
        "argv": sys.argv,
        "git": _git_info(calling_script),
        "script_hash": _sha256(calling_script) if calling_script else None,
    }
    merged = dict(_runtime_cache)
    merged.update(meta)
    return merged


# --- public API ------------------------------------------------------------

def save_output(data: Any, output_path: str) -> str:
    """Save data to *output_path* and record the script that produced it.

    Returns the (expected) path to the metadata file. When metadata is
    disabled via config, the returned path may not exist.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(data))

    calling_script = os.environ.get("WHICH_SCRIPT_PATH") or _find_calling_script(__file__)
    meta_path = output_path + ".metadata.json"

    if _cfg_write_metadata:
        metadata = {
            "script_path": calling_script,
            "runtime": _collect_runtime_metadata(calling_script),
        }
        with open(meta_path, "w", encoding="utf-8") as mf:
            json.dump(metadata, mf, indent=2)

    if calling_script and os.path.exists(calling_script):
        _write_script_snapshots(output_path, calling_script)

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
    calling_script = os.environ.get("WHICH_SCRIPT_PATH") or _find_calling_script(__file__)

    if _cfg_write_metadata:
        metadata = {
            "script_path": calling_script,
            "open_params": params,
            "runtime": _collect_runtime_metadata(calling_script),
        }
        meta_path = path + ".metadata.json"
        try:
            _skip_logging = True
            with _original_open(meta_path, "w", encoding="utf-8") as mf:
                json.dump(metadata, mf, indent=2)
        finally:
            _skip_logging = False

    if calling_script and os.path.exists(calling_script):
        _write_script_snapshots(path, calling_script)


