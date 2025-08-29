# Windows launcher: double-click or use in context menu
import sys

try:
    from whichscript.open_script import main
except Exception as e:
    sys.stderr.write("Failed to import whichscript.open_script: %s\n" % e)
    sys.exit(1)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
