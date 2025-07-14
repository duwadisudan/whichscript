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
