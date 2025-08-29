#%%

from whichscript import enable_auto_logging, configure

configure(metadata=True, snapshot_script=False, snapshot_py=True)

enable_auto_logging()

#%%
import matplotlib.pyplot as plt

plt.plot([1, 6, 3,7], [4, 5, 8,10])
plt.savefig("U:\\eng_research_hrc_binauralhearinglab\\Sudan\\Labs\\Sen Lab\\whichscript\\plot_test_result\\my_plot.png")

# %%
