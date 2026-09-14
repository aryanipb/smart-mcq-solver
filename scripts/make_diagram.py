"""Generate the Model-2 (ScratchMCQ) architecture diagram for the project report."""
from PIL import Image, ImageDraw, ImageFont
import textwrap

FONT_DIR = "/usr/share/fonts/TTF/"
font_bold  = ImageFont.truetype(FONT_DIR + "DejaVuSans-Bold.ttf", 20)
font_reg   = ImageFont.truetype(FONT_DIR + "DejaVuSans.ttf", 17)
font_small = ImageFont.truetype(FONT_DIR + "DejaVuSans.ttf", 14)
font_title = ImageFont.truetype(FONT_DIR + "DejaVuSans-Bold.ttf", 24)

W, H = 1100, 1850
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

NAVY   = (11, 61, 145)
DARK   = (30, 30, 30)
LIGHT  = (233, 240, 252)
BORDER = (11, 61, 145)
GREY   = (120, 120, 120)

def box(cx, y, w, h, title, body_lines, fill=LIGHT, border=BORDER, title_font=font_bold, body_font=font_reg):
    x0, x1 = cx - w // 2, cx + w // 2
    d.rounded_rectangle([x0, y, x1, y + h], radius=14, fill=fill, outline=border, width=3)
    ty = y + 12
    if title:
        tw = d.textlength(title, font=title_font)
        d.text((cx - tw / 2, ty), title, font=title_font, fill=NAVY)
        ty += 30
    for line in body_lines:
        lw = d.textlength(line, font=body_font)
        d.text((cx - lw / 2, ty), line, font=body_font, fill=DARK)
        ty += 24
    return y + h

def arrow(cx, y0, y1, label=None):
    d.line([(cx, y0), (cx, y1 - 14)], fill=GREY, width=3)
    d.polygon([(cx - 8, y1 - 14), (cx + 8, y1 - 14), (cx, y1)], fill=GREY)
    if label:
        lw = d.textlength(label, font=font_small)
        d.text((cx + 18, (y0 + y1) / 2 - 8), label, font=font_small, fill=GREY)

cx = W // 2
y = 20

title = "Model 2 — ScratchMCQ: From-Scratch Multiple-Choice Transformer"
tw = d.textlength(title, font=font_title)
d.text((cx - tw / 2, y), title, font=font_title, fill=NAVY)
y += 45
sub = "Forward pass for one training batch"
tw = d.textlength(sub, font=font_small)
d.text((cx - tw / 2, y), sub, font=font_small, fill=GREY)
y += 40

steps = [
    ("1 · Input", ["Question paired with each option A–E,", "one (question, option) pair per choice"], 90),
    ("2 · Tokenizer", ["input_ids, attention_mask", "shape: (B, 5, 256)  —  B questions × 5 choices × 256 tokens"], 90),
    ("3 · Flatten choice dim", ["(B, 5, 256)  →  (B×5, 256)", "so every choice is processed as one flat batch"], 90),
    ("4 · Embeddings", ["Token Embedding (vocab × 256)", "+ Learned Positional Embedding (256 × 256)"], 90),
    ("5 · Transformer Encoder × 4 layers", ["4 attention heads · d_model = 256 · feed-forward = 512", "pre-norm · dropout = 0.1  (nn.TransformerEncoder)"], 100),
    ("6 · Masked Mean-Pooling", ["Σ (hidden × attention_mask) / Σ (attention_mask)", "→ one 256-dim vector per (question, option) pair"], 90),
    ("7 · Linear Head", ["Linear(256 → 1)", "→ one relevance score per option"], 90),
    ("8 · Un-flatten", ["(B×5, 1)  →  (B, 5)", "five raw scores per question"], 90),
    ("9 · Softmax", ["softmax across the 5 scores", "→ ranked probability for options A–E"], 90),
]

box_w = 760
for title_txt, body, h in steps:
    y2 = box(cx, y, box_w, h, title_txt, body)
    y = y2
    if title_txt != steps[-1][0]:
        arrow(cx, y, y + 40)
        y += 40

y += 20
note = ["Key design point: ONE shared encoder scores every option.", "There are no option-specific weights — the model must tell A from E", "purely by reading and comparing meaning, not by position or index."]
y_end = box(cx, y, box_w + 40, 120, "Why this matters", note, fill=(255, 251, 230), border=(201, 147, 11), title_font=font_bold, body_font=font_small)

from pathlib import Path

out_dir = Path(__file__).resolve().parent.parent / "figures"
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "model2_architecture.png"
img = img.crop((0, 0, W, y_end + 30))
img.save(str(out_path))
print("saved", img.size, "to", out_path)
