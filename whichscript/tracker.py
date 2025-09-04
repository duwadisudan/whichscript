import builtins
import inspect
import json
import os
import shutil
import sys
import platform
import hashlib
import subprocess
import zipfile
import site
import sysconfig
from datetime import datetime
from typing import Any, Sequence
from pathlib import Path

from .archiver import build_archive_for_output as _ws_build_archive

# --- helpers ---------------------------------------------------------------

def _find_calling_script(current_file: str) -> str | None:
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


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except Exception:
        return default

# --- runtime configuration (env + runtime overrides) ----------------------

_cfg_write_metadata: bool = _env_flag("WHICH_SCRIPT_METADATA", "0")  # default off per user
_cfg_snapshot_script: bool = _env_flag("WHICH_SCRIPT_SNAPSHOT", "0")
_cfg_snapshot_py: bool = _env_flag("WHICH_SCRIPT_SNAPSHOT_PY", "1")
_cfg_local_imports_snapshot: bool = _env_flag("WHICH_SCRIPT_LOCAL_IMPORTS", "0")
_cfg_local_imports_roots: list[str] | None = None
_cfg_local_imports_max_files: int = _env_int("WHICH_SCRIPT_LOCAL_IMPORTS_MAX_FILES", 500)
_cfg_local_imports_max_bytes: int = _env_int("WHICH_SCRIPT_LOCAL_IMPORTS_MAX_BYTES", 50_000_000)

# archive controls (env or configure)
_CFG_ARCHIVE = _env_flag("WHICH_SCRIPT_ARCHIVE", "1")
_CFG_ARCHIVE_ONLY = _env_flag("WHICH_SCRIPT_ARCHIVE_ONLY", "0")
_CFG_ARCHIVE_DIR = os.environ.get("WHICH_SCRIPT_ARCHIVE_DIR")
_CFG_HIDE_SIDECARS = _env_flag("WHICH_SCRIPT_HIDE_SIDECARS", "1")


def configure(*,
              metadata: bool | None = None,
              snapshot_script: bool | None = None,
              snapshot_py: bool | None = None,
              local_imports_snapshot: bool | None = None,
              local_imports_root: Sequence[str] | str | None = None,
              local_imports_max_files: int | None = None,
              local_imports_max_bytes: int | None = None,
              archive: bool | None = None,
              archive_only: bool | None = None,
              archive_dir: str | None = None,
              hide_sidecars: bool | None = None) -> None:
    global _cfg_write_metadata, _cfg_snapshot_script, _cfg_snapshot_py
    global _cfg_local_imports_snapshot, _cfg_local_imports_roots
    global _cfg_local_imports_max_files, _cfg_local_imports_max_bytes
    global _CFG_ARCHIVE, _CFG_ARCHIVE_ONLY, _CFG_ARCHIVE_DIR, _CFG_HIDE_SIDECARS

    if metadata is not None:
        _cfg_write_metadata = bool(metadata)
    if snapshot_script is not None:
        _cfg_snapshot_script = bool(snapshot_script)
    if snapshot_py is not None:
        _cfg_snapshot_py = bool(snapshot_py)
    if local_imports_snapshot is not None:
        _cfg_local_imports_snapshot = bool(local_imports_snapshot)
    if local_imports_root is not None:
        if isinstance(local_imports_root, str):
            _cfg_local_imports_roots = [os.path.abspath(local_imports_root)]
        else:
            _cfg_local_imports_roots = [os.path.abspath(p) for p in local_imports_root]
    if local_imports_max_files is not None:
        _cfg_local_imports_max_files = int(local_imports_max_files)
    if local_imports_max_bytes is not None:
        _cfg_local_imports_max_bytes = int(local_imports_max_bytes)

    if archive is not None:
        _CFG_ARCHIVE = bool(archive)
    if archive_only is not None:
        _CFG_ARCHIVE_ONLY = bool(archive_only)
    if archive_dir is not None:
        _CFG_ARCHIVE_DIR = archive_dir
    if hide_sidecars is not None:
        _CFG_HIDE_SIDECARS = bool(hide_sidecars)

# --- reproducibility metadata --------------------------------------------

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

# --- snapshot helpers ------------------------------------------------------

_skip_logging = False


def _maybe_set_hidden(path: str, hide: bool) -> None:
    if not hide:
        return
    try:
        if sys.platform.startswith('win') and os.path.exists(path):
            subprocess.run(['attrib', '+H', path], check=False)
    except Exception:
        pass



def _atomic_copy_script(dst: str, src: str, hide: bool) -> None:
    """Copy src -> dst atomically, handling Hidden attr on Windows."""
    tmp = dst + ".tmp"
    if sys.platform.startswith('win') and os.path.exists(dst):
        try:
            subprocess.run(['attrib', '-H', dst], check=False)
        except Exception:
            pass
    shutil.copyfile(src, tmp)
    os.replace(tmp, dst)
    _maybe_set_hidden(dst, hide)


def _write_script_snapshots(target_base: str, script_path: str) -> None:
    global _skip_logging
    try:
        _skip_logging = True
        if _cfg_snapshot_py:
            dst = target_base + ".script.py"
            try:
                _atomic_copy_script(dst, script_path, _CFG_HIDE_SIDECARS)
            except Exception:
                pass
    finally:
        _skip_logging = False

# --- central archive -------------------------------------------------------

def _auto_archive(target_base: str, metadata: dict[str, Any] | None, calling_script: str | None) -> None:
    if not _CFG_ARCHIVE:
        return
    try:
        roots = _cfg_local_imports_roots or ([os.path.dirname(calling_script)] if calling_script else [])
        archive_dir = _CFG_ARCHIVE_DIR or os.path.join(os.path.expanduser('~'), 'whichscript_logs')
        _ws_build_archive(
            target_base,
            archive_dir=archive_dir,
            local_roots=roots,
            metadata=metadata or {},
        )
    except Exception:
        pass

# --- public API ------------------------------------------------------------

def save_output(data: Any, output_path: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(data))

    calling_script = _find_calling_script(__file__)
    metadata: dict[str, Any] | None = None
    if _cfg_write_metadata:
        metadata = {
            "script_path": calling_script,
            "runtime": _collect_runtime_metadata(calling_script),
        }

    if calling_script and os.path.exists(calling_script):
        _write_script_snapshots(output_path, calling_script)

    _auto_archive(output_path, metadata, calling_script)

    # Do not write local metadata sidecar per user preference
    return output_path + ".metadata.json"

# --- automatic logging ----------------------------------------------------

_original_open = builtins.open
_log_active = False

def enable_auto_logging() -> None:
    global _log_active
    if not _log_active:
        builtins.open = _logging_open  # type: ignore[assignment]
        _log_active = True

def disable_auto_logging() -> None:
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

    metadata: dict[str, Any] | None = None
    if _cfg_write_metadata:
        metadata = {
            "script_path": calling_script,
            "open_params": params,
            "runtime": _collect_runtime_metadata(calling_script),
        }

    if calling_script and os.path.exists(calling_script):
        _write_script_snapshots(path, calling_script)

    _auto_archive(path, metadata, calling_script)

    # No local metadata write

