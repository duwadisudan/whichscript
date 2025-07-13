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

