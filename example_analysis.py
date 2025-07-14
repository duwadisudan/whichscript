from whichscript import save_output, enable_auto_logging

if __name__ == "__main__":
    # Activate global logging so all file writes are recorded
    enable_auto_logging()

    result = "some important results"
    save_output(result, "output/result.txt")
    print("Output and metadata saved in 'output/' directory")
