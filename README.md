# whichscript

File‑first, friction‑free provenance for Python outputs.

whichscript makes every file you save (plots, tables, text, etc.) self‑describing by:

- Writing a hidden script snapshot next to the output (so you can jump straight to the code).
- Building a compact, output‑centric archive (.ws.zip) that contains your script, metadata, and only your local imported .py modules.
- Requiring only two lines in your script: `configure(...)` and `enable_auto_logging()` — no wrappers, no decorators, no servers.

## Highlights

- Output‑first archives: one .ws.zip per output ⇒ easy to share and audit.
- Hidden local sidecars: `<output>.script.py` (and optionally metadata). No clutter in folders.
- Zero infra: No DB or UI required; integrates well with lab shares and Windows.
- Script snapshot (not just git): captures exact code even with uncommitted changes; still records git commit/dirty when available.
- Friendly on Windows/network drives: safe writes and Hidden attributes

---

## Installation

Choose one:

- Install editable (recommended):
  ```bash
  pip install -e .
  ```
- Or add to PYTHONPATH (one‑off):
  ```powershell
  $env:PYTHONPATH = '<your_repo_path>'
  ```

---


## Example: example_analysis.py

```python

#start of whichscript code
from whichscript import configure, enable_auto_logging

configure(
    archive=True,
    archive_only=False,
    archive_dir=r"<your_archive_dir>",
    hide_sidecars=True,
    metadata=False,
    snapshot_script=False,
    snapshot_py=True,
    local_imports_snapshot=False,
)

enable_auto_logging()

#end of whichscript code

# your usual code and imports of dependent modules
from whichscript.localmod_demo import transform_points
import matplotlib.pyplot as plt
from pathlib import Path

xs, ys = transform_points([1, 6, 3, 7], [4, 5, 8, 10], offset=2)
fig, ax = plt.subplots(); ax.plot(xs, ys)
out = Path(r"<your_output_dir>\\my_plot.png")
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=300, bbox_inches='tight')

```

What you get:

- Next to the PNG (Hidden): `my_plot.png.script.py` (only)
- Central archive: `whichscript_master_log/my_plot.png/YYYY-MM-DD/run-YYYYMMDD-HHMMSS/my_plot.png.ws.zip` containing:
  - `metadata.json` (script path, runtime info, git, etc.)
  - `script.py` (snapshot of the exact code)
  - `deps/` (your local imported .py modules, excludes stdlib/site‑packages)

---

Verify:

- Folder: `...\plot_test_result` has `my_plot.png` and Hidden `my_plot.png.script.py`.
- Archive: `...\whichscript_master_log\my_plot.png\YYYY-MM-DD\run-...\my_plot.png.ws.zip`

---

## Configuration

Call `configure(...)` once per script, or use env vars. Flags:

- `archive` (bool): build central .ws.zip per output.
- `archive_only` (bool): if True, suppress all local sidecars (not recommended for Windows shares). If False (default here), keep local Hidden `script.py`.
- `archive_dir` (str): root folder for central archives.
- `hide_sidecars` (bool): mark local sidecars Hidden on Windows.
- `metadata` (bool): write local `<output>.metadata.json`. Recommended False on network shares; metadata is always embedded in the central archive.
- `snapshot_script` / `snapshot_py` (bool): control local script sidecars; keep `snapshot_py=True` for `script.py`.
- `local_imports_snapshot` (bool): write `<output>.deps.zip` locally (usually False; the archive packs deps for you).
- `local_imports_root` (list[str]): optional roots to restrict which .py files count as “local”.

Environment variable equivalents (set before Python):

- `WHICH_SCRIPT_ARCHIVE` (1/0)
- `WHICH_SCRIPT_ARCHIVE_DIR`
- `WHICH_SCRIPT_ARCHIVE_ONLY` (1/0)
- `WHICH_SCRIPT_HIDE_SIDECARS` (1/0)
- `WHICH_SCRIPT_METADATA` (1/0)
- `WHICH_SCRIPT_SNAPSHOT_PY` (1/0)
- `WHICH_SCRIPT_LOCAL_IMPORTS` (1/0)

Interactive sessions (cells/notebooks): optionally set `WHICH_SCRIPT_PATH` to label the snapshot:
```python
import os; os.environ['WHICH_SCRIPT_PATH'] = r'<your_path>
```

---




## How it works

- Hooks Python’s file writes (via a safe wrapper) to attach provenance.
- Writes the script snapshot (`.script.py`) next to the output (Hidden) for instant open.
- Builds an output‑centric archive with script, metadata, and local deps.
- Avoids truncating Hidden files on network shares; metadata is embedded in the archive by default.

---

## Troubleshooting

- “Permission denied … metadata.json” on U: shares ⇒ set `metadata=False` (recommended), or re‑enable later after we roll an atomic replace.
- “No module named whichscript.open_script” ⇒ ensure repo installed (`pip install -e path`) or set `PYTHONPATH`.
- Right‑click shows “no app associated” ⇒ associate `.py` with VS Code/Notepad, or use the registry command above with `pythonw.exe`.
- Hidden files not visible ⇒ enable “Hidden items” in Explorer to inspect sidecars.

---

## Why whichscript (vs other available tools)

- File‑first provenance: every saved file is self‑describing without a service or UI.
- Minimal: import + configure + enable; no run managers, no decorators.
- Snapshot exact script (not just git), and still record git commit/dirty if present.
- Output‑centric archives: focused, portable bundles — easy to email, zip, or pin.
- Windows‑friendly: Hidden sidecars, Explorer integration, safe behavior on network shares.
- Plays nice with others: archives can be pushed to DVC/MLflow later.

---

## License

MIT (or your preferred license).

## Contributing

Issues and PRs welcome. Please include a minimal repro script and a sample output file when reporting problems.

---

## How to Cite

If you use whichscript in your work, please cite it.

- Plain: Replace placeholders after you mint a DOI via Zenodo.
  - YourLastName, YourInitials. (2025). whichscript (v0.2.0). Zenodo. https://doi.org/10.5281/zenodo.TBD

- BibTeX
  ```bibtex
  @software{whichscript2025,
    author  = {YOUR-LAST-NAME, YOUR-FIRST-NAME and Coauthor, FirstName},
    title   = {whichscript: File-first provenance for Python outputs},
    year    = {2025},
    version = {0.2.0},
    doi     = {10.5281/zenodo.TBD},
    url     = {https://github.com/YOUR-ORG/whichscript}
  }
  ```

- APA
  - YourLastName, Y. (2025). whichscript (v0.2.0). Zenodo. https://doi.org/10.5281/zenodo.TBD

This repository also includes a `CITATION.cff` (GitHub will render a “Cite this repository” box automatically).



---

## AI Assistance Disclosure

Portions of this project (code, refactors, and documentation) were developed with assistance from ChatGPT/Codex (OpenAI). All generated outputs were reviewed, edited, and validated by the maintainers prior to inclusion. Any mistakes or omissions remain the responsibility of the authors.


