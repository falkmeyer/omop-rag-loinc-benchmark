"""Figure 1 for the MIE 2027 full paper: (a) pipeline, (b) evaluation levels, (c) Top-1 accuracy.

Numbers from analysis/final_metrics.py (n = 581 items paired by ITEMID).
Run: python make_figure1.py  ->  writes figure1.png (600 dpi) and figure1.pdf next to this script.

Layout: all panels share one content frame (FRAME_BOTTOM..FRAME_TOP). The top boxes of (a) and the top of the
axis in (c) align with FRAME_TOP; the bottom boxes of (b) and the zero line of (c) align with FRAME_BOTTOM.
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).parent / "figure1"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "font.size": 6.6,
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
NEUTRAL = "#c3cad2"  # outlines of boxes that carry no system colour
BODY = 6.4
TITLE = 6.7
LETTER = 9

CM = 1 / 2.54
FRAME_BOTTOM, FRAME_TOP = 0.135, 0.97
LEFT_X0, LEFT_W = 0.035, 0.56
RIGHT_X0, RIGHT_W = 0.685, 0.31

fig = plt.figure(figsize=(12.4 * CM, 6.2 * CM))
ax_a = fig.add_axes([LEFT_X0, FRAME_BOTTOM, LEFT_W, FRAME_TOP - FRAME_BOTTOM])
ax_c = fig.add_axes([RIGHT_X0, FRAME_BOTTOM, RIGHT_W, FRAME_TOP - FRAME_BOTTOM])


def frame_y(v):
    """Figure y coordinate of value v (0..100) of the left panel."""
    return FRAME_BOTTOM + v / 100 * (FRAME_TOP - FRAME_BOTTOM)


def letter(x, y, s):
    fig.text(x, y, s, fontsize=LETTER, fontweight="bold", va="top", ha="left")


# ---------------------------------------------------------------- (a) pipeline, (b) evaluation levels
ax_a.set_xlim(0, 100)
ax_a.set_ylim(0, 100)
ax_a.axis("off")


def node(x, y, w, h, title, body, face="white", edge=NEUTRAL, lw=0.7, color=INK):
    ax_a.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=2", fc=face, ec=edge, lw=lw,
                                  clip_on=False))
    ax_a.text(x + w / 2, y + h - 2.6, title, fontsize=TITLE, fontweight="bold", color=color, ha="center", va="top")
    ax_a.text(x + w / 2, y + h - 8.8, body, fontsize=BODY, color=color, ha="center", va="top", linespacing=1.2)


def arrow(x0, y0, x1, y1):
    ax_a.annotate("", xy=(x1, y1), xytext=(x0, y0),
                  arrowprops=dict(arrowstyle="-|>", lw=0.7, color=INK, mutation_scale=7, shrinkA=0, shrinkB=0))


def tag(x, y, lvl):
    """Level marker: a prediction at this concept counts as correct from this level on."""
    ax_a.text(x, y, lvl, fontsize=6.6, fontweight="bold", color="white", ha="center", va="center",
              bbox=dict(boxstyle="round,pad=0.28", fc=ACCENT, ec="none"))


# (a) lanes from the MIMIC item to the three predictions, ordered as the legend in (c)
letter(0.0, FRAME_TOP, "a")
node(0, 58, 17, 42, "MIMIC-III", "lab item:\nlabel,\nfluid,\ncategory")
node(21, 85, 60, 15, "Usagi string matching", "label only, standard LOINC", face=GREY, edge=GREY)
node(21, 58, 30, 21, "Retrieval", "embedding search,\ntop 5 of 113,667", face=LIGHT, edge=LIGHT)
node(55, 58, 26, 13.5, "LLM reranking", "Gemini 2.0 Flash", face=DARK, edge=DARK, color="white")
Y_USAGI, Y_RET, Y_RAG = 92.5, 75.5, 64.75
arrow(17, Y_USAGI, 21, Y_USAGI)
arrow(17, Y_RAG, 21, Y_RAG)
arrow(81, Y_USAGI, 85, Y_USAGI)
arrow(51, Y_RET, 85, Y_RET)          # retrieval alone: top-ranked candidate passes over the reranker
arrow(51, Y_RAG, 55, Y_RAG)
arrow(81, Y_RAG, 85, Y_RAG)
for y, sub in ((Y_USAGI, "Usagi"), (Y_RET, "Ret"), (Y_RAG, "RAG")):
    ax_a.text(85.8, y, r"$\hat{y}_{\mathrm{%s}}$" % sub, fontsize=8, color=INK, ha="left", va="center")

# (b) evaluation levels on a real LOINC hierarchy fragment
letter(0.0, frame_y(50), "b")
ax_a.text(5, 50, r"Example: Glucose (blood gas), reference code $y$ = 2339-0", fontsize=BODY, color=INK,
          va="top", style="italic")
node(30, 25, 40, 15, "LP385526-1", "Glucose | Blood")
node(0, 0, 46.5, 20, r"2339-0 = $y$", "Glucose [Mass/volume]\nin Blood", face="#fdf3f0", edge=ACCENT, lw=1.0)
node(53.5, 0, 46.5, 20, "2341-6", "Glucose [Mass/volume] in\nBlood by Test strip manual")
for xs, ys in (([50, 50], [25, 22.5]), ([23.25, 76.75], [22.5, 22.5]), ([23.25, 23.25], [22.5, 20]),
               ([76.75, 76.75], [22.5, 20])):
    ax_a.plot(xs, ys, lw=0.6, color=NEUTRAL)
tag(3.5, 20, "L1")
tag(33.5, 40, "L2")
tag(57, 20, "L3")

# ---------------------------------------------------------------- (c) results
letter(RIGHT_X0 - 0.075, FRAME_TOP, "c")
cats = ["L1\nexact", "L2\n+ parent", "L3\n+ sibling"]
usagi = [10.67, 10.67, 39.41]
retrieval = [3.27, 29.78, 34.60]
pipeline = [17.21, 37.35, 52.32]
p_vals = ["p<0.001", "p<0.001", "p<0.001"]

w = 0.27
xs = list(range(len(cats)))
series = [(r"Usagi ($\hat{y}_{\mathrm{Usagi}}$)", usagi, GREY), (r"Retrieval only ($\hat{y}_{\mathrm{Ret}}$)", retrieval, LIGHT),
          (r"Full pipeline ($\hat{y}_{\mathrm{RAG}}$)", pipeline, DARK)]
for k, (name, vals, col) in enumerate(series):
    pos = [x + (k - 1) * w for x in xs]
    ax_c.bar(pos, vals, w * 0.9, color=col, label=name, zorder=2)
    for x, v in zip(pos, vals):
        ax_c.text(x, v + 0.8, f"{v:.0f}", ha="center", va="bottom", fontsize=6.0, color=INK)

for x, u, p, s in zip(xs, usagi, pipeline, p_vals):
    top = max(u, p) + 6.5
    ax_c.plot([x - w, x - w, x + w, x + w], [top - 1.4, top, top, top - 1.4], lw=0.5, color=INK)
    ax_c.text(x, top + 0.6, s, ha="center", va="bottom", fontsize=5.9, color=INK)

ax_c.set_xticks(xs)
ax_c.set_xticklabels(cats, fontsize=6.6, linespacing=1.1)
ax_c.set_xlim(-0.5, 2.5)
ax_c.set_ylim(0, 65)
ax_c.set_yticks(range(0, 61, 10))
ax_c.set_ylabel("Top-1 accuracy (%)", fontsize=6.9)
ax_c.tick_params(axis="y", labelsize=6.6, length=2)
ax_c.tick_params(axis="x", length=0, pad=3)
ax_c.yaxis.grid(True, lw=0.4, color="#e4e7eb", zorder=0)
for side in ("top", "right"):
    ax_c.spines[side].set_visible(False)
ax_c.legend(frameon=True, facecolor="white", edgecolor="none", framealpha=1, fontsize=6.6, loc="upper left",
            bbox_to_anchor=(0.0, 1.02), handlelength=1.0, handletextpad=0.4, labelspacing=0.25, borderaxespad=0.2)

fig.savefig(OUT.with_suffix(".png"), dpi=600)
fig.savefig(OUT.with_suffix(".pdf"))
print("wrote", OUT.with_suffix(".png"))
