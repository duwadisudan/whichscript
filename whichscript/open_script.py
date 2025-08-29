import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _find_target_from_sidecars(output_path: Path) -> Path | None:
    """Given a produced output file, decide which script to open.

    Preference order:
    1) Python snapshot alongside the output: <file>.script.py
    2) Raw snapshot alongside the output: <file>.script
    3) The original script from metadata.json: metadata["script_path"]
    """
    # Prefer the .script.py snapshot
    snapshot_py = output_path.with_suffix(output_path.suffix + ".script.py")
    if snapshot_py.exists():
        return snapshot_py

    # Fallback to the raw .script snapshot
    snapshot = output_path.with_suffix(output_path.suffix + ".script")
    if snapshot.exists():
        return snapshot

    # Look for metadata to get original script path
    meta = output_path.with_suffix(output_path.suffix + ".metadata.json")
    if meta.exists():
        try:
            with open(meta, "r", encoding="utf-8") as f:
                data = json.load(f)
            script_path = data.get("script_path")
            if script_path:
                p = Path(script_path)
                if p.exists():
                    return p
        except Exception:
            pass
    return None


def _open_in_vscode(path: Path) -> bool:
    """Try to open file in VS Code, return True on success.

    Searches PATH first, then common Windows install locations.
    """
    code_cmd = shutil.which("code")
    candidates: list[str] = []
    if code_cmd:
        candidates.append(code_cmd)

    # Windows typical locations
    if sys.platform.startswith("win"):
        local = os.getenv("LOCALAPPDATA")
        pf = os.getenv("ProgramFiles")
        pfx86 = os.getenv("ProgramFiles(x86)")
        possible = []
        if local:
            possible.append(os.path.join(local, "Programs", "Microsoft VS Code", "Code.exe"))
        if pf:
            possible.append(os.path.join(pf, "Microsoft VS Code", "Code.exe"))
        if pfx86:
            possible.append(os.path.join(pfx86, "Microsoft VS Code", "Code.exe"))
        candidates.extend([p for p in possible if p and os.path.exists(p)])

    # Environment override
    override = os.getenv("VSCODE_BIN") or os.getenv("CODE_BIN")
    if override:
        candidates.insert(0, override)

    for cmd in candidates:
        try:
            subprocess.run([cmd, "-g", str(path)], check=False)
            return True
        except Exception:
            continue
    return False


def _open_in_explorer_select(path: Path) -> bool:
    try:
        if sys.platform.startswith("win"):
            subprocess.run(["explorer", f"/select,\"{path}\""], check=False)
            return True
    except Exception:
        return False
    return False


def _open_default(path: Path) -> bool:
    """Open file with OS default handler."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
            return True
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
            return True
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
            return True
    except Exception:
        return False


def _open_in_notepad(path: Path) -> bool:
    """Windows-only Notepad fallback for unknown extensions like .script."""
    if not sys.platform.startswith("win"):
        return False
    try:
        system_root = os.environ.get("WINDIR", r"C:\\Windows")
        notepad = os.path.join(system_root, "system32", "notepad.exe")
        if not os.path.exists(notepad):
            notepad = "notepad.exe"
        subprocess.run([notepad, str(path)], check=False)
        return True
    except Exception:
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Open the script that generated an output file (prefers snapshot .script.py)."
        )
    )
    parser.add_argument(
        "output_file",
        help="Path to an output file that has whichscript sidecars",
    )
    parser.add_argument(
        "--force-default",
        action="store_true",
        help="Skip VS Code attempt and use system default opener",
    )
    args = parser.parse_args(argv)

    output_path = Path(args.output_file)
    if not output_path.exists():
        print(f"Output file not found: {output_path}", file=sys.stderr)
        return 2

    target = _find_target_from_sidecars(output_path)
    if not target:
        print(
            "No script sidecars found. Expected '<file>.script(.py)' or '<file>.metadata.json' with 'script_path'.",
            file=sys.stderr,
        )
        return 3

    # Try VS Code first unless forced to default
    if not args.force_default and _open_in_vscode(target):
        return 0

    # For snapshot files with unknown association, try Notepad before default
    if target.suffix.lower() in (".script", ".py"):
        if _open_in_notepad(target):
            return 0

    # Fall back to default opener
    if _open_default(target):
        return 0

    # As a last attempt on Windows, try Notepad again
    if _open_in_notepad(target):
        return 0

    # If interactive, ask user how to proceed
    if sys.stdin and sys.stdin.isatty():
        print("VS Code not available. Choose an option:")
        print("  [1] Open with system default")
        print("  [2] Reveal in Explorer (Windows)")
        print("  [3] Print path and exit")
        print("  [4] Enter custom command to run (use {path} placeholder)")
        choice = input("> ").strip()
        if choice == "1":
            if _open_default(target):
                return 0
        elif choice == "2":
            if _open_in_explorer_select(target):
                return 0
        elif choice == "3":
            print(str(target))
            return 0
        elif choice == "4":
            cmd = input("Command: ").strip()
            if cmd:
                cmd_to_run = cmd.replace("{path}", str(target))
                try:
                    subprocess.run(cmd_to_run, shell=True, check=False)
                    return 0
                except Exception:
                    pass

    print(
        f"Found script at: {target}\n"
        "Could not auto-open it. You can open it manually or rerun with --force-default.",
        file=sys.stderr,
    )
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
