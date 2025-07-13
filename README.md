# whichscript

This project aims to build a software solution that tracks intermediate outputs and keeps a record of the script that generated them.

## Installation

Clone the repository and make sure `python3` is available on your system. The package does not require any third-party dependencies.

## Usage

Use `whichscript.save_output` to write text results to a file. A metadata JSON file and a copy of the executing script will be saved alongside your output.

```bash
python example_analysis.py
```

This will create `output/result.txt`, `output/result.txt.metadata.json`, and `output/result.txt.script`.

## License

This project is licensed under the [MIT License](LICENSE).
