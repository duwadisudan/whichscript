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
out = Path(r"<your_output_dir>\my_plot.png")
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=300, bbox_inches='tight')