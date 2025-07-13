from whichscript import save_output

if __name__ == "__main__":
    result = "some important results"
    save_output(result, "output/result.txt")
    print("Output and metadata saved in 'output/' directory")
