import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

ssr_path = Path("../mrio_pipeline_results_260713/ssr/self_sufficiency_ratios.csv")

df = pd.read_csv(ssr_path)

cfilter = ["GBR", "FRA", "DEU", "NLD", "USA", "CHN", "BRA"]

fig, ax = plt.subplots(figsize=(10, 6))

colors = plt.cm.tab10.colors
fs = 12

for country in df.country.unique():

    if country not in cfilter:
        continue

    dat = df[df.country == country]
    color = colors[df.country.unique().tolist().index(country) % len(colors)]
    ax.plot(dat.year, dat.ratio_full, label=country,
            linewidth = 4, alpha = 0.8,
            color=color)

ax.set_xticks(ax.get_xticks(), labels=ax.get_xticks(), fontsize=fs)
ax.set_yticks(ax.get_yticks(), labels=[round(_, 2) for _ in ax.get_yticks()], fontsize=fs)

ax.set_xlabel("Year", fontsize=fs)  
ax.set_ylabel("Self-Sufficiency Ratio (1=fully self-sufficient)", fontsize=fs)
ax.legend(fontsize=fs, loc="lower left")
ax.set_ylim(0, 1)
ax.set_xlim(1986, 2021)
fig.tight_layout()

plt.show()