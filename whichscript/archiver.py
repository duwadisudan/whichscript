import json
import os
import zipfile
import datetime
import subprocess
import sys
import site
import sysconfig
from pathlib import Path
from typing import Optional, Sequence


def _is_std_or_site(path: str) -> bool:
    path = os.path.abspath(path)
    stdlib = sysconfig.get_paths().get("stdlib")
    if stdlib and path.startswith(os.path.abspath(stdlib)):
        return True
    for sp in site.getsitepackages() + [site.getusersitepackages()]:
        if sp and path.startswith(os.path.abspath(sp)):
            return True
    if path.startswith(os.path.abspath(sys.base_prefix)):
        return True
    return False


def _norm(p: str) -> str:
    return os.path.normcase(os.path.abspath(p))


def _select_local_imports(roots: Sequence[str] | None) -> list[str]:
    files: list[str] = []
    root_list = [_norm(r) for r in (roots or []) if r]
    for mod in list(sys.modules.values()):
        f = getattr(mod, "__file__", None)
        if not f or not f.endswith(".py"):
            continue
        af = _norm(f)
        if _is_std_or_site(af):
            continue
        if root_list:
            if not any(af.startswith(r + os.sep) or af == r for r in root_list):
                continue
        files.append(af)
    # de-dup preserve order
    seen = set()
    uniq: list[str] = []
    for p in files:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def _archive_dest(archive_dir: Path, target_base: Path) -> Path:
    now = datetime.datetime.now()
    out_name = target_base.name
    date_dir = now.strftime('%Y-%m-%d')
    run_dir = archive_dir / out_name / date_dir / f"run-{now.strftime('%Y%m%d-%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir / f"{out_name}.ws.zip"


def build_archive_for_output(
    output_path: str,
    archive_dir: str,
    *,
    local_roots: Sequence[str] | None = None,
    max_files: int = 500,
    max_bytes: int = 50_000_000,
    metadata: dict | None = None,
) -> Optional[str]:
    out = Path(output_path)
    if not out.exists():
        return None

    archive_root = Path(archive_dir)
    archive_root.mkdir(parents=True, exist_ok=True)
    dest = _archive_dest(archive_root, out)

    meta = metadata or {}
    script_py = out.with_suffix(out.suffix + ".script.py")
    script_raw = out.with_suffix(out.suffix + ".script")

    with zipfile.ZipFile(dest, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        # metadata.json inside archive
        if meta:
            zf.writestr('metadata.json', json.dumps(meta, indent=2))
        # script snapshot(s)
        if script_py.exists():
            zf.write(script_py, arcname='script.py')
        elif script_raw.exists():
            zf.write(script_raw, arcname='script.script')
        # local deps scanned live
        dep_list = _select_local_imports(local_roots)
        if dep_list:
            base = local_roots[0] if local_roots else out.parent
            total = 0
            count = 0
            for p in dep_list:
                try:
                    sz = os.path.getsize(p)
                except OSError:
                    continue
                if count >= max_files or (total + sz) > max_bytes:
                    break
                arc = Path('deps') / Path(os.path.relpath(p, start=base))
                try:
                    zf.write(p, arcname=str(arc))
                    total += sz
                    count += 1
                except Exception:
                    continue

    return str(dest)
