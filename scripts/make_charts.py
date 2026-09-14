"""Generate report figures directly from the real Weights & Biases run history."""
import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = str(OUT_DIR) + "/"
D = json.load(open("/tmp/wandb_final.json")) if Path("/tmp/wandb_final.json").exists() else {}

C_SCRATCH, C_ROB, C_DEB, C_LRG = "#E1812C", "#3A923A", "#0B3D91", "#8155A6"
GRID = dict(alpha=.28, linewidth=.7)
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 12, "axes.titleweight": "bold", "axes.labelsize": 10.5,
    "figure.dpi": 200,
})

def hist(name, key):
    h = D[name]["history"]
    pts = sorted([(r["epoch"], r[key]) for r in h if key in r and "epoch" in r])
    return [p[0] for p in pts], [p[1] for p in pts]

# ---------- FIG 1: grouped-split validation MAP@3 ----------
fig, ax = plt.subplots(figsize=(7.2, 4.0))
for nm, lbl, c in [("M1-scratch-transformer", "Model 2 · Scratch Transformer", C_SCRATCH),
                   ("M2-roberta-base", "Model 1b · RoBERTa-base", C_ROB),
                   ("M3-deberta-v3-base", "Model 1a · DeBERTa-v3-base", C_DEB)]:
    x, y = hist(nm, "val_map3")
    ax.plot(x, y, marker="o", ms=4.5, lw=2, color=c, label=lbl)
ax.axhline(0.3667, ls=":", lw=1.4, color="#888")
ax.text(11.85, 0.372, "random guessing (0.367)", ha="right", fontsize=8.5, color="#666")
ax.set_xlabel("Epoch"); ax.set_ylabel("Validation MAP@3")
ax.set_title("Figure 1 — Generalisation to unseen questions (grouped 80/20 split)")
ax.set_ylim(0.33, 0.66); ax.grid(**GRID); ax.legend(frameon=False, fontsize=9, loc="upper right")
fig.tight_layout(); fig.savefig(OUT + "fig1_val_map3.png"); plt.close(fig)

# ---------- FIG 2: training loss ----------
fig, ax = plt.subplots(figsize=(7.2, 4.0))
for nm, lbl, c in [("M1-scratch-transformer", "Model 2 · Scratch Transformer", C_SCRATCH),
                   ("M2-roberta-base", "Model 1b · RoBERTa-base", C_ROB),
                   ("M3-deberta-v3-base", "Model 1a · DeBERTa-v3-base", C_DEB)]:
    x, y = hist(nm, "train_loss")
    ax.plot(x, y, marker="o", ms=4.5, lw=2, color=c, label=lbl)
ax.set_xlabel("Epoch"); ax.set_ylabel("Training loss (cross-entropy)")
ax.set_title("Figure 2 — Training loss: scratch model collapses to ~0 by epoch 4")
ax.grid(**GRID); ax.legend(frameon=False, fontsize=9)
fig.tight_layout(); fig.savefig(OUT + "fig2_train_loss.png"); plt.close(fig)

# ---------- FIG 3: full-data fit ----------
fig, ax = plt.subplots(figsize=(7.2, 4.0))
for nm, lbl, c in [("M2-roberta-FULL", "RoBERTa-base · full 2 000 rows", C_ROB),
                   ("M3-deberta-FULL", "DeBERTa-v3-base · full 2 000 rows", C_DEB),
                   ("M4-deberta-large-FULL", "DeBERTa-v3-large · full 2 000 rows", C_LRG)]:
    x, y = hist(nm, "val_map3")
    ax.plot(x, y, marker="o", ms=4.5, lw=2, color=c, label=lbl)
ax.set_xlabel("Epoch"); ax.set_ylabel("Training-set MAP@3 (fit, not generalisation)")
ax.set_title("Figure 3 — Deployment regime: fit on 100 % of the data")
ax.set_ylim(0.4, 1.04); ax.grid(**GRID); ax.legend(frameon=False, fontsize=9, loc="lower right")
fig.tight_layout(); fig.savefig(OUT + "fig3_fulldata_fit.png"); plt.close(fig)

# ---------- FIG 4: comparison bars ----------
models = ["Scratch\nTransformer", "RoBERTa\n-base", "DeBERTa\n-v3-base"]
best = [0.5857, 0.5756, 0.6000]
final = [0.5136, 0.5291, 0.5360]
f1 = [0.3432, 0.3474, 0.3038]
cols = [C_SCRATCH, C_ROB, C_DEB]
fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.5))
for ax, vals, t in zip(axes, [best, final, f1],
                       ["Best val MAP@3", "Final-epoch val MAP@3", "Final-epoch val macro-F1"]):
    b = ax.bar(models, vals, color=cols, width=.6)
    ax.bar_label(b, fmt="%.4f", fontsize=8.5, padding=2)
    ax.set_title(t, fontsize=10.5); ax.set_ylim(0, max(vals) * 1.28)
    ax.grid(axis="y", **GRID); ax.tick_params(labelsize=8.5)
fig.suptitle("Figure 4 — Three tracked models on the identical grouped validation split",
             fontsize=12, fontweight="bold", y=1.0)
fig.tight_layout(); fig.savefig(OUT + "fig4_comparison.png"); plt.close(fig)

# ---------- FIG 5: two regimes ----------
fig, ax = plt.subplots(figsize=(7.6, 4.2))
labels = ["Scratch\nTransformer", "RoBERTa\n-base", "DeBERTa\n-v3-base", "DeBERTa\n-v3-large"]
gen = [0.5857, 0.5756, 0.6000, None]
fit = [None, 1.0000, 0.9830, 0.9441]
xs = range(len(labels))
ax.bar([x - .19 for x in xs], [g if g else 0 for g in gen], width=.38,
       color="#0B3D91", label="Unseen-question generalisation (grouped split)")
ax.bar([x + .19 for x in xs], [f if f else 0 for f in fit], width=.38,
       color="#C9930B", label="Seen-question recall (fit on full data)")
for i, g in enumerate(gen):
    if g: ax.text(i - .19, g + .015, f"{g:.3f}", ha="center", fontsize=8.5)
for i, f in enumerate(fit):
    if f: ax.text(i + .19, f + .015, f"{f:.3f}", ha="center", fontsize=8.5)
ax.set_xticks(list(xs)); ax.set_xticklabels(labels, fontsize=9)
ax.set_ylabel("MAP@3"); ax.set_ylim(0, 1.42)
ax.set_yticks([0, .2, .4, .6, .8, 1.0])
ax.set_title("Figure 5 — The two regimes: this benchmark measures recall, not reasoning",
             pad=42)
ax.grid(axis="y", **GRID)
ax.legend(frameon=False, fontsize=9, loc="upper left", bbox_to_anchor=(0, 1.005))
fig.tight_layout(); fig.savefig(OUT + "fig5_two_regimes.png"); plt.close(fig)

print("charts written")
