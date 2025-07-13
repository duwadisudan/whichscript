import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from whichscript import save_output


def test_save_output_creates_metadata_and_script_copy(tmp_path):
    output_file = tmp_path / "result.txt"

    meta_path = save_output("hello", str(output_file))

    # check files exist
    assert output_file.exists(), "Output file was not created"
    metadata_path = Path(meta_path)
    assert metadata_path.exists(), "Metadata file was not created"
    script_copy = Path(str(output_file) + ".script")
    assert script_copy.exists(), "Script copy was not created"

    # validate metadata content
    with metadata_path.open() as f:
        metadata = json.load(f)
    assert metadata.get("script_path") == os.path.abspath(__file__)
