#%%


from whichscript import configure, enable_auto_logging

# Minimal: configure auto-archive via tracker
configure(
    archive=True,
    archive_only=False,
    archive_dir=r"u:\eng_research_hrc_binauralhearinglab\Sudan\Labs\Sen Lab\whichscript\whichscript_master_log",
    hide_sidecars=True,
    metadata=True,
    snapshot_script=False,
    snapshot_py=True,
    local_imports_snapshot=False,
)

enable_auto_logging()

#%%
from pathlib import Path
import matplotlib.pyplot as plt

from whichscript.localmod_demo import transform_points

#%%
xs, ys = transform_points([1, 6, 3, 9], [4, 5, 8, 10], offset=2)
fig, ax = plt.subplots()
ax.plot(xs, ys)

out_path = Path(r"u:\eng_research_hrc_binauralhearinglab\Sudan\Labs\Sen Lab\whichscript\plot_test_result\my_plot.png")
out_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out_path, dpi=300, bbox_inches="tight")
plt.close(fig)

# %%

