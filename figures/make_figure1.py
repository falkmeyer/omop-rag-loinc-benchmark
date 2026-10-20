"""Figure 1 for the MIE 2027 full paper: (a) pipeline and evaluation design, (b) Top-1 accuracy.

Numbers from analysis/final_metrics.py (n = 581 items paired by ITEMID).
Run: python make_figure1.py  ->  writes figure1.png (600 dpi) and figure1.pdf next to this script.
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).parent / "figure1"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "font.size": 6.5,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "pdf.fonttype": 42,
    "mathtext.fontset": "custom",
    "mathtext.rm": "Arial",
    "mathtext.it": "Arial:italic",
})

INK = "#1f2933"
GREY = "#9aa5b1"
LIGHT = "#8fb8de"
DARK = "#1d4e89"
ACCENT = "#c8553d"
BODY = 5.3

CM = 1 / 2.54
fig = plt.figure(figsize=(12.4 * CM, 5.7 * CM))
ax_a = fig.add_axes([0.0, 0.0, 0.57, 1.0])
ax_b = fig.add_axes([0.665, 0.16, 0.325, 0.66])

# ---------------------------------------------------------------- (a) schematic
ax_a.set_xlim(0, 100)
ax_a.set_ylim(0, 100)
ax_a.axis("off")


def box(x, y, w, h, face, edge, lw=0.7):
    ax_a.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=2",
                                  fc=face, ec=edge, lw=lw))


def label(x, y, title, body=None, color=INK, gap=5.2):
    ax_a.text(x, y, title, fontsize=6.0, fontweight="bold", color=color, va="top")
    if body:
        ax_a.text(x, y - gap, body, fontsize=BODY, color=INK, va="top", linespacing=1.3)


def arrow(x0, y0, x1, y1):
    ax_a.annotate("", xy=(x1, y1), xytext=(x0, y0),
                  arrowprops=dict(arrowstyle="-|>", lw=0.7, color=INK, mutation_scale=6,
                                  shrinkA=0, shrinkB=0))


ax_a.text(0.5, 99.5, "a", fontsize=8, fontweight="bold", va="top")

# source table
box(4, 84, 93, 14, "#f5f7fa", GREY)
label(6.5, 95.8, "Source: MIMIC-III D_LABITEMS        Target: OMOP vocabulary",
      "753 lab items, 585 with reference LOINC  →  113,667 LOINC concepts")

# pipeline branch
box(4, 27, 59, 50, "#eef4fb", DARK)
label(6.5, 74.8, "Two-stage RAG pipeline",
      "Removal of 53 administrative items;\nquery = label + fluid + category", color=DARK)
box(8, 47, 51, 14.5, "white", LIGHT)
label(10.5, 59.5, "1  Embedding retrieval", "text-embedding-005, exact FAISS\nsearch, top-5 LOINC candidates")
box(8, 29.5, 51, 14.5, "white", DARK)
label(10.5, 42, "2  LLM reranking", "Gemini 2.0 Flash picks the best\nof 5 candidates with rationale")
arrow(33.5, 47, 33.5, 44)

# baseline branch
box(67, 27, 30, 50, "#f5f7fa", GREY)
label(69.5, 74.8, "Baseline: Usagi",
      "OHDSI string-\nsimilarity matching\non label only;\nstandard LOINC\nmeasurements;\ntop-1 suggestion")

arrow(33.5, 84, 33.5, 77)
arrow(82, 84, 82, 77)

# evaluation
box(4, 1.5, 93, 21, "#fdf3f0", ACCENT)
label(6.5, 20.5, r"Match criteria: prediction $c$ vs. reference code $y$", color=ACCENT)
levels = [("L1", r"$c = y$"), ("L2", r"L1 or $c$ parent of $y$"), ("L3", r"L2 or $c$, $y$ siblings")]
for x, (lvl, txt) in zip((6.5, 26, 61.5), levels):
    ax_a.text(x, 11.5, lvl, fontsize=6.3, fontweight="bold", color=ACCENT, va="center")
    ax_a.text(x + 5.4, 11.5, txt, fontsize=BODY, color=INK, va="center")
ax_a.text(6.5, 5.0, r"Correctly mapped items per level: $C_1 \subseteq C_2 \subseteq C_3$", fontsize=BODY,
          color=INK, va="center")
arrow(33.5, 27, 33.5, 22.5)
arrow(82, 27, 82, 22.5)

# ---------------------------------------------------------------- (b) results
fig.text(0.585, 0.995, "b", fontsize=8, fontweight="bold", va="top")
cats = ["L1\nexact", "L2\n+ parent", "L3\n+ sibling"]
usagi = [10.67, 10.67, 39.41]
retrieval = [3.27, 29.78, 34.60]
pipeline = [17.21, 37.35, 52.32]
p_vals = ["p<0.001", "p<0.001", "p<0.001"]

w = 0.27
xs = list(range(len(cats)))
series = [("Usagi", usagi, GREY), ("Retrieval only", retrieval, LIGHT),
          ("Retrieval + LLM reranking", pipeline, DARK)]
for k, (name, vals, col) in enumerate(series):
    pos = [x + (k - 1) * w for x in xs]
    ax_b.bar(pos, vals, w * 0.9, color=col, label=name, zorder=2)
    for x, v in zip(pos, vals):
        ax_b.text(x, v + 0.8, f"{v:.0f}", ha="center", va="bottom", fontsize=5.0, color=INK)

for x, u, p, s in zip(xs, usagi, pipeline, p_vals):
    top = max(u, p) + 6.5
    ax_b.plot([x - w, x - w, x + w, x + w], [top - 1.4, top, top, top - 1.4], lw=0.5, color=INK)
    ax_b.text(x, top + 0.6, s, ha="center", va="bottom", fontsize=4.9, color=INK)

ax_b.set_xticks(xs)
ax_b.set_xticklabels(cats, fontsize=5.4, linespacing=1.1)
ax_b.set_xlim(-0.55, 2.55)
ax_b.set_ylim(0, 60)
ax_b.set_yticks(range(0, 61, 10))
ax_b.set_ylabel("Top-1 accuracy (%)", fontsize=6.0)
ax_b.tick_params(axis="y", labelsize=5.4, length=2)
ax_b.tick_params(axis="x", length=0)
ax_b.yaxis.grid(True, lw=0.4, color="#e4e7eb", zorder=0)
for side in ("top", "right"):
    ax_b.spines[side].set_visible(False)
fig.legend(*ax_b.get_legend_handles_labels(), frameon=False, fontsize=5.3, loc="upper left",
           bbox_to_anchor=(0.62, 0.995), ncol=1, handlelength=1.0, handletextpad=0.4,
           labelspacing=0.25, borderaxespad=0)

fig.savefig(OUT.with_suffix(".png"), dpi=600)
fig.savefig(OUT.with_suffix(".pdf"))
print("wrote", OUT.with_suffix(".png"))
