# whichscript

This project aims to build a software solution that tracks intermediate outputs and keeps a record of the script that generated them.

## Installation

Clone the repository and make sure `python3` is available on your system. The package does not require any third-party dependencies.

## Usage

To manually save an output, call `whichscript.save_output` with the data and
path. A metadata JSON file and a copy of the executing script will be written
next to your output.

For automatic logging of all file writes, call
`whichscript.enable_auto_logging()` once at the start of your script. Any file
opened in write mode will have its metadata and a copy of the calling script
saved alongside it.

```bash
python example_analysis.py
```

This will create `output/result.txt`, `output/result.txt.metadata.json`, and `output/result.txt.script`.

## License

This project is licensed under the [MIT License](LICENSE).

## Interactive sessions

In notebooks or interactive cells, there may be no real script file.
Set an environment variable to provide a script path to record:

- On Windows PowerShell:
  $env:WHICH_SCRIPT_PATH = "C:\\path\\to\\your_script.py"
- In Python before enabling logging:
  import os; os.environ["WHICH_SCRIPT_PATH"] = r"C:\\path\\to\\your_script.py"

When set, whichscript stores this path in the metadata and, if the file
exists, writes a .script copy alongside your output files.

## Open Generating Script (CLI)

You can open the generating script (prefers the snapshot) for any output
file using a small helper:

- Run: python -m whichscript.open_script <path/to/your/output.ext>
- Behavior:
  - If <output>.script exists, it opens that snapshot.
  - Else, it reads <output>.metadata.json and opens script_path if present.
  - It tries VS Code first (if code is on PATH); otherwise falls back to
    the OS default application. You can force the default with --force-default.

### Windows right-click integration (optional)

Add a context menu entry to open the generating script directly from File Explorer.
Create a .reg file with the following contents and double-click to import:

`
Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\*\shell\whichscript_open]
@="Open Generating Script"

[HKEY_CLASSES_ROOT\*\shell\whichscript_open\command]
@="C:\\Path\\To\\python.exe -m whichscript.open_script \"%1\""
`

Adjust the Python path accordingly. You can also point it to a bundled EXE if
you package this tool.

## Packaging to EXE (Windows)

Build a single-file EXE of the opener using PyInstaller:

- From a terminal in whichscript/whichscript:
  - scripts\\build_open_exe.bat
- Result: dist\\whichscript-open.exe

You can then point the context menu at that EXE instead of pythonw.exe:

`
Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\*\shell\whichscript_open]
@="Open Generating Script"

[HKEY_CLASSES_ROOT\*\shell\whichscript_open\command]
@="U:\\path\\to\\dist\\whichscript-open.exe \"%1\""
`

If you prefer not to use a .spec file, the batch script invokes PyInstaller
with --onefile and --noconsole. You can customize icons or metadata via
standard PyInstaller flags.

## Script Snapshot Convenience (.script.py)

By default, whichscript now writes a second snapshot next to each output:

- `<output>.<ext>.script` (raw script copy, as before)
- `<output>.<ext>.script.py` (same content with .py extension for easy opening)

To disable the `.script.py` convenience file, set an environment variable before
running your script:

- Windows PowerShell: `$env:WHICH_SCRIPT_SNAPSHOT_PY = "0"`
- Python: `import os; os.environ["WHICH_SCRIPT_SNAPSHOT_PY"] = "0"`

The CLI opener prefers the `.script.py` snapshot when present, then falls back
to `.script`, then to the original `script_path` recorded in metadata.
