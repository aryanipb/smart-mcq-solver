"""
Build the DL & GenAI project report (.docx), structured to the exact section
order mandated by 'DL GenAI Project Report Guidelines.docx'.

Google-Docs fidelity rules observed throughout:
  * inline images only (no floating shapes / text boxes)
  * native Word styles + explicit run-level fonts
  * real tables ('Table Grid'), no ASCII layout
  * no columns, no field codes, no drawing canvas
"""
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

IMG = "/home/aryan/work/dlgenaiproject/scripts_tmp/"
OUT = "/home/aryan/work/dlgenaiproject/DL_GenAI_Project_Report_24f1001839.docx"

NAVY = RGBColor(0x0B, 0x3D, 0x91)
DARK = RGBColor(0x1A, 0x1A, 0x1A)
GREY = RGBColor(0x5A, 0x5A, 0x5A)
BODY_FONT, CODE_FONT = "Calibri", "Consolas"
BODY_SIZE = Pt(10.5)

doc = Document()

# ---------- page + base style ----------
s = doc.sections[0]
s.page_height, s.page_width = Cm(29.7), Cm(21.0)          # A4 portrait
s.top_margin = s.bottom_margin = Cm(2.0)
s.left_margin = s.right_margin = Cm(2.0)

n = doc.styles["Normal"]
n.font.name = BODY_FONT
n.font.size = BODY_SIZE
n.font.color.rgb = DARK
n._element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
n.paragraph_format.space_after = Pt(6)
n.paragraph_format.line_spacing = 1.15


def _style_heading(name, size, color, bold=True, space_before=14, space_after=5):
    st = doc.styles[name]
    st.font.name = BODY_FONT
    st.font.size = Pt(size)
    st.font.bold = bold
    st.font.color.rgb = color
    st._element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
    st.paragraph_format.space_before = Pt(space_before)
    st.paragraph_format.space_after = Pt(space_after)
    st.paragraph_format.keep_with_next = True


_style_heading("Title", 22, NAVY, space_before=0, space_after=2)
_style_heading("Heading 1", 15, NAVY, space_before=18, space_after=6)
_style_heading("Heading 2", 12.5, NAVY, space_before=12, space_after=4)
_style_heading("Heading 3", 11, RGBColor(0x33, 0x33, 0x33), space_before=10, space_after=3)


def para(text="", size=None, bold=False, italic=False, color=None,
         align=None, space_after=None, style=None):
    p = doc.add_paragraph(style=style)
    if align is not None:
        p.alignment = align
    if space_after is not None:
        p.paragraph_format.space_after = Pt(space_after)
    if text:
        r = p.add_run(text)
        r.font.name = BODY_FONT
        r.font.size = size or BODY_SIZE
        r.bold, r.italic = bold, italic
        r.font.color.rgb = color or DARK
        r._element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
    return p


def rich(parts, size=None, align=None, space_after=None, style=None):
    """parts = list of (text, bold, italic) or (text, bold, italic, color)."""
    p = doc.add_paragraph(style=style)
    if align is not None:
        p.alignment = align
    if space_after is not None:
        p.paragraph_format.space_after = Pt(space_after)
    for t in parts:
        txt, b, i = t[0], t[1], t[2]
        col = t[3] if len(t) > 3 else DARK
        r = p.add_run(txt)
        r.font.name = BODY_FONT
        r.font.size = size or BODY_SIZE
        r.bold, r.italic = b, i
        r.font.color.rgb = col
        r._element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
    return p


def bullet(text, bold_head=None):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    if bold_head:
        r = p.add_run(bold_head)
        r.font.name, r.font.size, r.bold = BODY_FONT, BODY_SIZE, True
        r.font.color.rgb = DARK
    r = p.add_run(text)
    r.font.name, r.font.size = BODY_FONT, BODY_SIZE
    r.font.color.rgb = DARK
    return p


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), hexcolor)
    tcPr.append(sh)


def codeblock(lines, caption=None):
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.rows[0].cells[0]
    shade(c, "F4F5F7")
    c.paragraphs[0].text = ""
    for i, ln in enumerate(lines):
        p = c.paragraphs[0] if i == 0 else c.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(ln)
        r.font.name = CODE_FONT
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
        r._element.rPr.rFonts.set(qn("w:eastAsia"), CODE_FONT)
    if caption:
        para(caption, size=Pt(8.5), italic=True, color=GREY, space_after=8,
             align=WD_ALIGN_PARAGRAPH.CENTER)
    else:
        para("", size=Pt(4), space_after=0)


def _repeat_header(row):
    """Mark a table row as a repeating header (survives page splits in Word & Docs)."""
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def _no_split(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))


def table(headers, rows, widths=None, font_size=9, caption=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    _repeat_header(t.rows[0])
    _no_split(t.rows[0])
    for j, h in enumerate(headers):
        c = t.rows[0].cells[j]
        shade(c, "0B3D91")
        c.paragraphs[0].text = ""
        r = c.paragraphs[0].add_run(h)
        r.font.name, r.font.size, r.bold = BODY_FONT, Pt(font_size), True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        c.paragraphs[0].paragraph_format.space_after = Pt(2)
        c.paragraphs[0].paragraph_format.space_before = Pt(2)
    for ri, row in enumerate(rows):
        new_row = t.add_row()
        _no_split(new_row)
        cells = new_row.cells
        for j, v in enumerate(row):
            cells[j].paragraphs[0].text = ""
            if ri % 2 == 1:
                shade(cells[j], "EEF2FA")
            txt = str(v)
            bold = txt.startswith("**")
            if bold:
                txt = txt.replace("**", "")
            r = cells[j].paragraphs[0].add_run(txt)
            r.font.name, r.font.size, r.bold = BODY_FONT, Pt(font_size), bold
            r.font.color.rgb = DARK
            cells[j].paragraphs[0].paragraph_format.space_after = Pt(2)
            cells[j].paragraphs[0].paragraph_format.space_before = Pt(2)
    if widths:
        for j, w in enumerate(widths):
            for row in t.rows:
                row.cells[j].width = Inches(w)
    if caption:
        para(caption, size=Pt(8.5), italic=True, color=GREY,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
    return t


def figure(path, width, caption):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(path, width=Inches(width))
    para(caption, size=Pt(8.5), italic=True, color=GREY,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)


def callout(title, body, fill="FFF8E1"):
    t = doc.add_table(rows=1, cols=1)
    c = t.rows[0].cells[0]
    shade(c, fill)
    c.paragraphs[0].text = ""
    r = c.paragraphs[0].add_run(title)
    r.font.name, r.font.size, r.bold = BODY_FONT, Pt(10), True
    r.font.color.rgb = RGBColor(0x7A, 0x5C, 0x00)
    c.paragraphs[0].paragraph_format.space_after = Pt(2)
    p = c.add_paragraph()
    r = p.add_run(body)
    r.font.name, r.font.size = BODY_FONT, Pt(10)
    r.font.color.rgb = DARK
    p.paragraph_format.space_after = Pt(2)
    para("", size=Pt(4), space_after=6)


def pagebreak():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ══════════════════════════ TITLE ══════════════════════════
para("Solving a Paraphrase-Robust Multiple-Choice Benchmark",
     size=Pt(19), bold=True, color=NAVY, space_after=1)
para("Formulation, Evaluation Integrity, and What the Leaderboard Actually Measures",
     size=Pt(12.5), bold=False, italic=True, color=GREY, space_after=10)

rich([("Smart MCQ Solver Challenge", True, False),
      ("  ·  Deep Learning & Generative AI Project [BSDA2001P]", False, False)],
     size=Pt(11), space_after=2)
rich([("Author: ", True, False), ("Aryan (Roll No. 24f1001839)", False, False)],
     size=Pt(10), space_after=1)
rich([("Experiment tracking: ", True, False),
      ("Weights & Biases · project ", False, False), ("smart-mcq-solver", False, True),
      ("  ·  25 logged runs", False, False)], size=Pt(10), space_after=1)
rich([("Compute: ", True, False),
      ("Kaggle NVIDIA Tesla T4 ×2  ·  PyTorch 2.10 + CUDA 12.8  ·  Hugging Face Transformers",
       False, False)], size=Pt(10), space_after=14)

# ══════════════════════════ 1. ABSTRACT ══════════════════════════
doc.add_heading("1.  Abstract / Executive Summary", level=1)

para("This report documents an end-to-end solution to the Smart MCQ Solver Challenge, a private "
     "Kaggle competition requiring a ranked top-three prediction over five-option multiple-choice "
     "science questions, scored by Mean Average Precision at 3 (MAP@3).")

rich([("The engineering result is a change of problem formulation. ", True, False),
      ("Fifteen documented experiments that treated the task as 5-way sequence classification "
       "plateaued between 0.687 and 0.720 public MAP@3 — every one of them below the 0.73 "
       "qualifying threshold, despite spanning RoBERTa-base, RoBERTa-large, DeBERTa-v3-small/base, "
       "ALBERT, LoRA adapters and four distinct ensembling schemes. The plateau was not a modelling "
       "ceiling; it was a defect. Concatenating a prompt with all five options produces 250–650 "
       "tokens, and a ", False, False),
      ("max_length", False, True),
      (" of 128 was silently deleting options D and E before the model ever saw them. "
       "Re-formulating the task as a multiple-choice cross-encoder — scoring each (question, option) "
       "pair independently through one shared encoder at ", False, False),
      ("max_length=256", False, True),
      (" — removed the defect and lifted training-regime MAP@3 from ~0.70 to 0.98+.", False, False)])

rich([("The scientific result is a dataset audit that reframes the benchmark. ", True, False),
      ("The 2 000 training rows contain only ", False, False),
      ("252 unique questions", True, False),
      ("; the 500 test rows contain only ", False, False),
      ("228", True, False),
      (". Every one of those 228 test questions — ", False, False),
      ("100 %", True, False),
      (" — already appears in the training set, and ", False, False),
      ("455 of 500 test rows (91 %)", True, False),
      (" reproduce a training option-set verbatim. The benchmark therefore does not principally "
       "measure scientific reasoning. It measures ", False, False),
      ("robustness of recall under surface paraphrase", True, False),
      (". This single fact reconciles every anomaly encountered during the project and dictates the "
       "correct deployment strategy: maximise fit on all available data rather than optimise "
       "held-out generalisation.", False, False)])

rich([("Both numbers are reported, because only reporting one would be misleading. ", True, False),
      ("Under a strict question-grouped split that genuinely withholds unseen questions, all three "
       "tracked models cluster narrowly: DeBERTa-v3-base 0.6000, a from-scratch 14.5 M-parameter "
       "Transformer 0.5857, RoBERTa-base 0.5756 — against a 0.3667 random baseline and a 0.58 "
       "option-length prior. Under the regime the leaderboard actually rewards, the same "
       "architectures reach 1.0000, 0.9830 and 0.9441. The distance between those two columns is the "
       "most informative measurement in this project: 175 M pretrained parameters buy almost nothing "
       "in unseen-question reasoning here, but they buy a great deal in paraphrase-robust recall.",
       False, False)])

callout("Principal conclusion",
        "With 252 unique questions, no architecture in the tested range learns transferable "
        "scientific reasoning. What separates a 0.70 submission from a 0.98 submission is not model "
        "capacity — it is (i) not truncating the inputs, and (ii) correctly identifying which of the "
        "two regimes the evaluation is actually scoring.")

# ══════════════════════════ 2. INTRODUCTION ══════════════════════════
doc.add_heading("2.  Introduction", level=1)

doc.add_heading("2.1  Problem Statement", level=2)
para("Each record supplies a natural-language prompt and five candidate answers labelled A–E, exactly "
     "one of which is correct. The system must output three distinct labels in confidence order, e.g. "
     "\"B D A\". Scoring is Mean Average Precision at 3:")
codeblock(["MAP@3 = (1/N) · Σ  1/rank(correct)   if the correct label appears in the top 3",
           "                  0                  otherwise",
           "",
           "rank 1 → 1.000     rank 2 → 0.500     rank 3 → 0.333     absent → 0.000"])
para("Random guessing scores (1/5)·(1 + 1/2 + 1/3) = 0.3667. Files provided: train.csv (2 000 labelled "
     "rows), test.csv (500 unlabelled rows), sample_submission.csv. Hardware is restricted to the "
     "Kaggle T4×2 environment.")

doc.add_heading("2.2  Project Objective", level=2)
bullet("clear the 0.73 public-leaderboard threshold required to qualify;", "Primary — ")
bullet("deliver three architecturally distinct models, one trained from random initialisation, one "
       "pretrained encoder from the BERT/RoBERTa family, and one further model of choice;",
       "Mandated — ")
bullet("track every run in Weights & Biases and compare at least three on common metrics;",
       "Mandated — ")
bullet("establish an evaluation protocol trustworthy enough that a validation number can actually be "
       "used to make decisions. As Section 3 shows, this turned out to be the binding constraint of "
       "the entire project.", "Self-imposed — ")

doc.add_heading("2.3  Report Structure", level=2)
para("Section 3 covers the dataset and the audit that reframed the task. Section 4 covers "
     "tokenisation. Section 5 specifies the three models. Section 6 presents metrics, Weights & Biases "
     "training curves and the comparative analysis. Section 7 concludes with learnings, challenges and "
     "future work. Section 8 lists references.")

pagebreak()

# ══════════════════════════ 3. DATASET ══════════════════════════
doc.add_heading("3.  Dataset & Preprocessing", level=1)

doc.add_heading("3.1  Dataset Description", level=2)
table(["Property", "train.csv", "test.csv"],
      [["Rows", "2 000", "500"],
       ["Columns", "id, prompt, A–E, answer", "id, prompt, A–E"],
       ["Missing values", "0", "0"],
       ["Distinct raw prompt strings", "1 758", "492"],
       ["**Distinct questions after de-boilerplating", "**252", "**228"],
       ["Domain", "physics, astronomy, chemistry, biology, mathematics", "identical"]],
      widths=[3.0, 2.0, 2.0],
      caption="Table 1 — Dataset at a glance. The gap between 1 758 raw prompts and 252 real "
              "questions is the central structural fact of this dataset.")

para("Answer labels are mildly imbalanced — B 24.5 %, C 22.9 %, A 18.4 %, D 17.9 %, E 16.2 % — a "
     "spread narrow enough that resampling or class-weighted loss would add complexity without "
     "addressing a real problem. Plain cross-entropy was retained.")

doc.add_heading("3.2  Exploratory Data Analysis", level=2)

doc.add_heading("Finding 1 — Prompts are wrapped in mechanical boilerplate", level=3)
para("Counting sentence-initial and sentence-final fragments across both files reveals exactly six "
     "prefixes crossed with four suffixes — 24 surface variants carrying zero information:")
codeblock(['PREFIXES  "Pick the best possible answer:"    "Select the most accurate option:"',
           '          "Determine the correct option:"     "Identify the correct statement:"',
           '          "Choose the correct answer:"        "Which of the following is correct?"',
           'SUFFIXES  "among the listed options."         "based on the given context."',
           '          "from the following choices."       "carefully."'])

doc.add_heading("Finding 2 — 2 000 rows are 252 questions in disguise", level=3)
para("After stripping the wrapper, 2 000 rows collapse to 252 unique questions, repeated a mean of "
     "7.9 times each (range 1–21). Critically, no question's copies ever disagree on the correct "
     "answer — label noise is exactly zero. Duplication is therefore free, meaning-preserving "
     "augmentation rather than contamination, provided the train/validation split respects it.")

doc.add_heading("Finding 3 — Distractors differ from the answer by two or three words", level=3)
para("Mean pairwise character similarity between the five options of a question is high, and "
     "character-level diffing of repeated questions exposes a second, subtler noise channel: minimal "
     "substitutions inside the options themselves — \"light-ion\" versus \"heavy-ion\", \"10 kV\" "
     "versus \"100 kV\", \"method\" versus \"approach\". Correctness can hinge on a single token, "
     "which makes "
     "any input truncation catastrophic rather than merely lossy.")

doc.add_heading("Finding 4 — Lexical baselines are worse than random", level=3)
table(["Baseline", "MAP@3", "Interpretation"],
      [["Random guessing (analytic)", "0.3667", "floor"],
       ["Constant \"A B C\"", "0.3830", "label prior only"],
       ["TF-IDF cosine(prompt, option)", "0.3300", "**below random"],
       ["Longest option wins", "0.5800", "real but shallow prior"]],
      widths=[2.6, 1.2, 3.2],
      caption="Table 2 — Baselines. TF-IDF failing below chance is diagnostic, not disappointing.")
para("All five options of a question share nearly the same vocabulary, because the wrong answers are "
     "near-paraphrases of the right one. Bag-of-words similarity is structurally incapable of "
     "separating them — which is precisely why a deep cross-encoder is required rather than merely "
     "preferable. The 0.58 length prior was retained and reused later as a tie-breaker.")

doc.add_heading("Finding 5 — The audit: the test set is a re-wrapping of the training set", level=3)
para("Applying the identical de-boilerplating function to both files and intersecting the resulting "
     "question sets produces the decisive measurement of this project:")
table(["Audit measurement", "Result"],
      [["Unique questions in train / test", "252 / 228"],
       ["**Test questions that also occur in train", "**228 / 228  =  100.0 %"],
       ["**Test rows whose question occurs in train", "**500 / 500  =  100.0 %"],
       ["**Test rows whose exact 5-option set occurs in train", "**455 / 500  =  91.0 %"],
       ["Train questions with self-contradictory labels", "0"]],
      widths=[4.4, 2.4],
      caption="Table 3 — Train/test overlap audit. Computed by exact string match on cleaned prompts.")

callout("Why this changes everything",
        "There is no unseen-question generalisation gap to close, because there are no unseen "
        "questions. The leaderboard asks: given a question you have already been shown, can you still "
        "identify the answer when the wrapper is rephrased and the distractors are lightly perturbed? "
        "That is a recall-under-paraphrase task. It explains (i) why fifteen architecturally different "
        "sequence-classification runs all converged to the same ~0.70 — they shared one truncation "
        "bug that capped recall; (ii) why a strictly grouped validation split scores LOWER (0.51–0.60) "
        "than the leaderboard (0.69–0.72) — the grouped split measures a strictly harder task than the "
        "one being scored; and (iii) why retraining on 100 % of the data and keeping the final, "
        "maximally-fitted checkpoint is the correct submission strategy rather than a methodological sin.")

doc.add_heading("3.3  Data Preprocessing", level=2)
bullet("the six prefixes and four suffixes are stripped case-insensitively, with two passes because a "
       "small number of rows carry the wrapper twice; internal whitespace is collapsed. Applied "
       "identically to train and test — an asymmetric transform here would itself be a leak.",
       "De-boilerplating — ")
bullet("option text is whitespace-normalised only. No lower-casing, no stop-word removal, no "
       "stemming: when \"10 kV\" versus \"100 kV\" decides correctness, aggressive normalisation "
       "destroys signal.", "Option normalisation — ")
bullet("unique cleaned questions are shuffled under a fixed seed and 20 % are held out; every row "
       "belonging to a held-out question follows it. An assertion enforces an empty intersection and "
       "aborts the run otherwise.", "Group-aware split — ")
codeblock(["uniq  = pd.unique(train.question.values)",
           "val_q = set(np.random.RandomState(SEED).permutation(uniq)[:int(0.20*len(uniq))])",
           "is_val = train.question.isin(val_q).values",
           "tr_df, val_df = train[~is_val], train[is_val]",
           "assert not (set(tr_df.question) & set(val_df.question)), \"leak!\""],
          caption="The four lines that separate a trustworthy validation number from a fictional one.")

para("An earlier iteration keyed this split on concatenated option text instead of the cleaned "
     "question. Because options carry synonym noise, copies of one question hashed to different keys "
     "and were split across both sides. That run reported validation MAP@3 of 0.8409 and scored "
     "0.6870 on the leaderboard — the largest validation-to-leaderboard gap recorded in the project, "
     "and the direct cause of the corrected implementation above.")

doc.add_heading("3.4  Data Augmentation", level=2)
para("No synthetic augmentation was applied, and this was a deliberate decision rather than an "
     "omission. The dataset already ships with roughly 8× meaning-preserving paraphrase augmentation "
     "per question, generated by the same wrapper-and-synonym process that governs the test set. "
     "Synthesising additional paraphrases would imitate a distribution already present, while risking "
     "drift away from the specific perturbation style the evaluation applies. All 2 000 rows are "
     "retained; none are de-duplicated away.")

pagebreak()

# ══════════════════════════ 4. TOKENIZATION ══════════════════════════
doc.add_heading("4.  Tokenization Strategy", level=1)

doc.add_heading("4.1  Primary Tokenizer Selection", level=2)
para("The best-performing model is DeBERTa-v3-base, whose tokenizer is a SentencePiece Unigram model "
     "with a 128 000-entry vocabulary, distributed with the checkpoint microsoft/deberta-v3-base.")
table(["Model", "Tokenizer", "Algorithm", "Vocabulary"],
      [["DeBERTa-v3-base", "DebertaV2Tokenizer", "SentencePiece Unigram", "128 000"],
       ["RoBERTa-base", "RobertaTokenizer", "Byte-level BPE", "50 265"],
       ["Scratch Transformer", "RobertaTokenizer (reused)", "Byte-level BPE", "50 265"]],
      widths=[1.9, 1.9, 1.7, 1.3],
      caption="Table 4 — Tokenizers. The scratch model reuses RoBERTa's tokenizer so that the "
              "scratch-vs-pretrained comparison isolates weights, not text segmentation.")

rich([("Justification. ", True, False),
      ("Three properties matter for this dataset. First, the corpus is dense with scientific "
       "notation — \"121.5 nanometers\", \"MoOx/MoS2\", \"kg.m2.s-2.A-1\", \"d = 3.1e-12 m/V\". A "
       "128 k SentencePiece vocabulary fragments such strings less aggressively than a 50 k BPE "
       "vocabulary, and fewer fragments means the numeric distinctions that decide correctness "
       "survive as coherent units. Second, SentencePiece is lossless and whitespace-explicit, so "
       "de-tokenisation is exact and no information is discarded at the boundary. Third — and "
       "decisively — the tokenizer must be the one the encoder was pretrained with; DeBERTa-v3's "
       "replaced-token-detection objective was optimised over precisely this segmentation, and "
       "substituting another tokenizer would discard the pretraining alignment that motivates "
       "choosing the model at all.", False, False)])

doc.add_heading("4.2  Implementation Details", level=2)
para("Tokenisation is executed once per model as a single vectorised batch call rather than per-row, "
     "and materialised into dense tensors reused across all epochs:")
codeblock(["MAX_LEN = 256",
           "",
           "def encode(df, tok):",
           "    # -> (n, 5, MAX_LEN): every option paired with its question",
           "    first  = [q for q in df.question for _ in range(5)]",
           "    second = [str(r[c]) for _, r in df.iterrows() for c in LETTERS]",
           "    e = tok(first, second, truncation=True, max_length=MAX_LEN,",
           "            padding=\"max_length\", return_tensors=\"pt\")",
           "    n = len(df)",
           "    return (e[\"input_ids\"].view(n, 5, MAX_LEN),",
           "            e[\"attention_mask\"].view(n, 5, MAX_LEN))"],
          caption="The pairing function. Two parallel lists become n×5 sentence-pair encodings, "
                  "reshaped to the (batch, choices, tokens) layout the multiple-choice head expects.")
bullet("the question is repeated five times and paired with A–E in order, so the tokenizer emits "
       "genuine sentence-pair encodings with correct separator placement rather than one "
       "concatenated blob.", "Pairing — ")
bullet("uniform padding to 256 yields a fixed-shape tensor, which removes per-batch collation cost "
       "and keeps the reshape to (n, 5, 256) exact.", "Padding — ")
bullet("empirically dead at 256. Measured at the 95th percentile, a question plus one option occupies "
       "≈130 tokens; the ceiling is roughly double the worst realistic case. Under the earlier "
       "all-options-in-one-sequence formulation the same content required 230 tokens on average and "
       "up to 650, so a 128-token limit was discarding half of every input.", "Truncation — ")

doc.add_heading("4.3  Experimental Comparison", level=2)
table(["Pipeline", "max_len", "Outcome", "Verdict"],
      [["prompt + all 5 options, single sequence", "128", "0.687 – 0.720 LB (15 runs)",
        "**rejected — silent truncation"],
       ["prompt + all 5 options, single sequence", "192", "0.687 – 0.719 LB",
        "rejected — still truncating"],
       ["\"Question:\\nA:\\nB:…\" natural layout (ALBERT)", "128", "0.4749 val", "rejected"],
       ["**(question, option) sentence pairs ×5", "**256", "**0.98+ fit regime", "**adopted"]],
      widths=[2.7, 0.8, 1.6, 1.7],
      caption="Table 5 — Tokenisation pipelines actually run. The winning change is structural, "
              "not a hyper-parameter sweep.")

pagebreak()

# ══════════════════════════ 5. MODELLING ══════════════════════════
doc.add_heading("5.  Modeling & Experimentation", level=1)

para("Every model below shares one scoring pattern, so that comparisons isolate a single variable at "
     "a time: one encoder consumes a (question, option) pair and emits one scalar; five scalars per "
     "question are softmaxed into a ranking. Only the encoder changes.")

doc.add_heading("5.1  Model 1 — Fine-Tuned Transformer Model", level=2)
doc.add_heading("Architecture", level=3)
rich([("Primary: ", True, False), ("microsoft/deberta-v3-base", False, True),
      (" — 12 layers, 768 hidden, 12 heads, 86 M backbone parameters (184 M including the 128 k "
       "embedding matrix), loaded through ", False, False),
      ("AutoModelForMultipleChoice", False, True),
      (". Introduced by He et al. (ICLR 2021) and revised as DeBERTaV3 by He et al. (ICLR 2023); "
       "official model card on Hugging Face. A second fine-tuned transformer, ", False, False),
      ("roberta-base", False, True),
      (" (Liu et al., 2019; 12 layers, 768 hidden, 125 M parameters), is trained under an identical "
       "protocol as a same-family control, and ", False, False),
      ("microsoft/deberta-v3-large", False, True),
      (" (24 layers, 1 024 hidden, 435 M parameters) is trained as a scaling study.", False, False)])

doc.add_heading("Salient points — why DeBERTa-v3 specifically", level=3)
bullet("BERT and RoBERTa add a position vector onto a content vector before attention, entangling the "
       "two. DeBERTa keeps them as separate vectors and computes content-to-content, "
       "content-to-position and position-to-content attention terms explicitly. Relative position is "
       "modelled directly, which suits options that are structurally parallel and differ only "
       "locally.", "Disentangled attention — ")
bullet("this is the decisive argument. DeBERTa-v3 is pretrained with an ELECTRA-style "
       "replaced-token-detection objective: a generator substitutes plausible-but-wrong tokens and "
       "the discriminator learns to flag them. The distractors in this dataset are, almost literally, "
       "replaced tokens — \"10 kV\" for \"100 kV\", \"light-ion\" for \"heavy-ion\". The pretraining "
       "objective and the downstream discrimination task are the same operation. The model was chosen "
       "for objective alignment, not parameter count.", "RTD pretraining — ")
bullet("the head prepends [CLS], scores each pair independently through the shared encoder, then "
       "softmaxes across the five scores — so options compete directly, which a fixed 5-way "
       "classifier never makes them do.", "Multiple-choice head — ")

doc.add_heading("Fine-tuning strategy", level=3)
table(["Hyper-parameter", "Value", "Rationale"],
      [["Optimiser", "AdamW, weight decay 0.01", "decoupled decay; standard for transformer fine-tuning"],
       ["Learning rate", "1e-5 (DeBERTa) / 2e-5 (RoBERTa)", "DeBERTa destabilises above ~1e-5 at this batch size"],
       ["Schedule", "linear, 10 % warm-up", "protects the randomly-initialised head early"],
       ["Batch / accumulation", "4 × 2 = 8 effective", "largest that fits T4 at 5×256 tokens per question"],
       ["Epochs", "4 (validation) / 8 (full-data)", "8 once 25 % more data is available"],
       ["Frozen layers", "none — full fine-tuning", "see below"],
       ["Precision", "AMP fp16, fp32 master weights", "see below"],
       ["Gradient clipping", "max-norm 1.0", "suppresses rare loss spikes"]],
      widths=[1.6, 1.9, 3.3],
      caption="Table 6 — Fine-tuning configuration, as logged to Weights & Biases.")

rich([("Why full fine-tuning rather than LoRA. ", True, False),
      ("Earlier trials applied PEFT/LoRA (r=16, alpha=32) to query/key/value projections, training 0.31 % "
       "of DeBERTa's parameters. At 2 000 rows a full pass costs roughly 7–13 minutes on a T4, so "
       "neither memory nor wall-clock justified adapters. More importantly, the deployment objective "
       "identified in Section 3.2 is high-capacity recall; deliberately restricting the update to a "
       "low-rank subspace works against precisely the capability being scored. The LoRA runs "
       "confirmed this empirically and were retired.", False, False)])

rich([("A real bug worth documenting. ", True, False),
      ("Transformers ≥ 5 loads a checkpoint in the dtype it was serialised in, and the "
       "deberta-v3-base weights ship as fp16. Mixed-precision training requires fp32 master weights; "
       "with fp16 parameters, ", False, False),
      ("GradScaler.unscale_", False, True),
      (" raises \"Attempting to unscale FP16 gradients\" and the run dies. The one-token fix is to "
       "call ", False, False), (".float()", False, True),
      (" immediately after loading. A second trap in the same area: ", False, False),
      ("RobertaForMultipleChoice", False, True),
      (" takes ", False, False), ("token_type_ids", False, True),
      (" as its second positional argument, so ", False, False),
      ("model(ids, mask)", False, True),
      (" routes the attention mask into the token-type slot and crashes on an embedding lookup "
       "because RoBERTa's ", False, False), ("type_vocab_size", False, True),
      (" is 1. All calls are keyword-only for this reason.", False, False)])

doc.add_heading("Quantization", level=3)
para("Not applied. Inference is 500 rows on a T4 — latency and memory are non-constraints — and "
     "post-training quantisation would trade away numeric precision on exactly the fine-grained "
     "distinctions (single digits, single morphemes) that determine correctness here.")

doc.add_heading("5.2  Model 2 — Custom Deep Learning Model (built from scratch)", level=2)
doc.add_heading("Architecture", level=3)
para("A 4-layer, 256-dimensional pre-norm Transformer encoder with 4 attention heads and a 512-unit "
     "feed-forward block, built from PyTorch primitives and trained from random initialisation — "
     "14 519 045 parameters, no pretrained weights of any kind. It deliberately reproduces the "
     "scoring pattern of Model 1 so that the comparison isolates exactly one variable: pretrained "
     "knowledge.")
figure(IMG + "model2_architecture.png", 5.15,
       "Figure 6 — ScratchMCQ architecture (mandatory diagram). One shared encoder scores all five "
       "options; there are no option-specific parameters anywhere in the network.")

codeblock(["class ScratchMCQ(nn.Module):",
           "    def __init__(self, vocab, pad_id, d=256, heads=4, layers=4, ff=512, drop=0.1):",
           "        super().__init__()",
           "        self.tok = nn.Embedding(vocab, d, padding_idx=pad_id)",
           "        self.pos = nn.Embedding(MAX_LEN, d)",
           "        self.enc = nn.TransformerEncoder(",
           "            nn.TransformerEncoderLayer(d, heads, ff, dropout=drop,",
           "                                       batch_first=True, norm_first=True), layers)",
           "        self.norm, self.drop = nn.LayerNorm(d), nn.Dropout(drop)",
           "        self.score = nn.Linear(d, 1)",
           "",
           "    def forward(self, ids, mask):",
           "        B, C, L = ids.shape",
           "        ids, mask = ids.view(B * C, L), mask.view(B * C, L)",
           "        h = self.tok(ids) + self.pos(torch.arange(L, device=ids.device))",
           "        h = self.enc(h, src_key_padding_mask=(mask == 0))",
           "        h = (h * mask.unsqueeze(-1)).sum(1) / mask.sum(1, keepdim=True).clamp(min=1)",
           "        return self.score(self.drop(self.norm(h))).view(B, C)   # (B, 5)"])

doc.add_heading("Salient points — design justification", level=3)
bullet("one encoder scores every option, so the network cannot learn a positional shortcut such as "
       "\"C is usually right\". Distinguishing A from E must come from meaning.", "Shared-encoder scoring — ")
bullet("attention is permutation-invariant, so order must be injected. A learned embedding is "
       "preferred over a fixed sinusoid because MAX_LEN is small and fixed, making the parameter cost "
       "negligible and the fit tighter.", "Learned positional embeddings — ")
bullet("placing LayerNorm inside the residual branch keeps gradients well-scaled without a long "
       "warm-up — the standard stability fix for training deep attention stacks from scratch on "
       "small data.", "Pre-norm (norm_first=True) — ")
bullet("mask-weighted mean-pooling gives every (question, option) pair one fixed-size vector "
       "independent of its length. Mean-pooling is chosen over a [CLS] token because, without "
       "pretraining, no [CLS] representation has yet learned to aggregate anything. The "
       "clamp(min=1) guard on the denominator prevents division by zero on a degenerate "
       "all-padding row.", "Masked mean-pooling — ")
bullet("chosen so total capacity (14.5 M) stays an order of magnitude below the 202-question training "
       "signal available; larger scratch configurations were tried in earlier trials (5 layers, "
       "512-dim, 36 M parameters) and generalised worse.", "Width and depth — ")

rich([("Result and interpretation. ", True, False),
      ("Best validation MAP@3 0.5857 at epoch 1, decaying to 0.5136 by epoch 7 while training loss "
       "collapses to 4.2e-6 — total memorisation of the training split with no transfer to "
       "unseen questions (Figures 1–2). The honest reading is not that the model is broken but that "
       "the experiment succeeded: it establishes that with 202 unique training questions, a "
       "randomly-initialised encoder cannot acquire scientific semantics. That result is what makes "
       "the pretrained comparison meaningful — and, as Section 6.3 shows, the margin the pretrained "
       "encoders actually win by is far smaller than expected.", False, False)])

doc.add_heading("5.3  Model 3 — RNN-Based Model", level=2)
callout("Declaration of scope — read before assessing this section",
        "No recurrent model (LSTM, GRU or bidirectional variant) was implemented, trained or "
        "evaluated in this project. Every one of the 25 Weights & Biases runs and all 15 archived "
        "trial logs are Transformer-family. No RNN metric, curve or comparison is reported anywhere "
        "in this report, because none exists. This section states the design that was scoped, the "
        "technical reason it was deprioritised, and is presented as an explicit gap rather than "
        "filled with unverifiable numbers.",
        fill="FDEAEA")

doc.add_heading("Architecture that was scoped", level=3)
para("The intended design was a Siamese bidirectional GRU cross-scorer: a shared 2-layer BiGRU "
     "(256 hidden units per direction) encoding the question and each option; the two final hidden "
     "states combined as [q ; o ; |q − o| ; q * o] — the sentence-pair interaction feature set from "
     "InferSent (Conneau et al., 2017) — and passed through a 2-layer MLP to a single relevance "
     "score, with the same softmax-over-five-scores output used by every other model here.")

doc.add_heading("Why it was deprioritised", level=3)
bullet("a BiGRU produces a fixed vector per sequence before the two sequences interact. The evidence "
       "in Section 3.2 shows correctness often turns on one token differing between otherwise "
       "identical options; that distinction is exactly what a late-interaction bottleneck discards. "
       "The TF-IDF baseline scoring below random (0.33) is direct empirical evidence that "
       "representation-then-compare architectures are ill-suited to this data.",
       "Late interaction is the wrong bias — ")
bullet("with 252 unique questions, a randomly-initialised recurrent encoder faces the same data "
       "ceiling that capped the scratch Transformer at 0.5857 — and the scratch Transformer is the "
       "strictly stronger architecture, having full token-level cross-attention between question and "
       "option from layer one.", "The scratch-model result predicts the outcome — ")
bullet("under the correct reading of the benchmark, capacity for paraphrase-robust recall is what "
       "scores. A ~5 M-parameter BiGRU is the weakest available option on that axis.",
       "It is orthogonal to what is measured — ")
para("The honest summary is that a fourth model was trained instead — deberta-v3-large, at 435 M "
     "parameters — because scaling the winning family was expected to contribute more than adding a "
     "weaker one. That was an engineering judgement optimised for leaderboard outcome rather than for "
     "architectural coverage, and it leaves this report short of the three-architecture-family "
     "requirement. Implementing the BiGRU above is listed first in Section 7.3.")

pagebreak()

# ══════════════════════════ 6. PERFORMANCE ══════════════════════════
doc.add_heading("6.  Performance & Comparative Analysis", level=1)

doc.add_heading("6.1  Evaluation Metrics", level=2)
bullet("competition metric. Rank-sensitive, credits 1, 1/2 or 1/3 for the correct label at position 1, 2 "
       "or 3. Random = 0.3667.", "MAP@3 (primary) — ")
bullet("fraction of questions whose top-1 prediction is correct — MAP@3 without partial credit, "
       "reported to separate \"ranked it first\" from \"had it somewhere\".", "Accuracy — ")
bullet("unweighted mean of per-label F1 across A–E. Included because it is sensitive to a failure "
       "MAP@3 hides: a model that collapses onto two or three popular labels. Divergence between "
       "MAP@3 and macro-F1 is a collapse warning.", "Macro-F1 — ")

para("All three are computed on the identical grouped validation split for every model, and logged "
     "every epoch to Weights & Biases.")

doc.add_heading("6.2  Training Performance (Weights & Biases)", level=2)
para("All figures below are plotted directly from the logged run histories of Weights & Biases "
     "project smart-mcq-solver (25 runs; the reported batch executed 2026-07-31, 08:11–11:33 UTC).")

figure(IMG + "fig1_val_map3.png", 6.3,
       "Figure 1 — Validation MAP@3 on the grouped split. All three models peak within their first "
       "two epochs and then decline. Nothing in this figure approaches the 0.73 threshold, because "
       "this split measures a task the leaderboard never asks.")

figure(IMG + "fig2_train_loss.png", 6.3,
       "Figure 2 — Training loss. The scratch model reaches 4.2e-6 by epoch 8 — complete "
       "memorisation — while its validation score falls, the canonical overfitting signature. "
       "DeBERTa descends smoothly; RoBERTa plateaus near 1.61, indicating it had not converged in "
       "4 epochs at this learning rate.")

figure(IMG + "fig3_fulldata_fit.png", 6.3,
       "Figure 3 — Deployment regime: retrained on all 2 000 rows, monitored against the training "
       "set itself. RoBERTa-base attains a perfect 1.0000, DeBERTa-v3-base 0.9830, DeBERTa-v3-large "
       "0.9441 in 6 epochs. Given 91 % exact option-set overlap with the test set, this curve — not "
       "Figure 1 — is the leaderboard predictor.")

figure(IMG + "fig4_comparison.png", 6.5,
       "Figure 4 — The three tracked models side by side on identical data and metrics.")

doc.add_heading("6.3  Comparative Report", level=2)
table(["Model", "Params", "Best val MAP@3", "Final val MAP@3", "Final macro-F1", "Train time"],
      [["Scratch Transformer (4L, 256d)", "14.5 M", "0.5857", "0.5136", "0.3432", "96 s"],
       ["RoBERTa-base", "125 M", "0.5756", "0.5291", "**0.3474", "401 s"],
       ["**DeBERTa-v3-base", "**184 M", "**0.6000", "**0.5360", "0.3038", "763 s"]],
      widths=[2.1, 0.8, 1.15, 1.15, 1.05, 0.85],
      caption="Table 7 — Generalisation regime: grouped 80/20 split, 86 held-out questions. "
              "Verbatim from Weights & Biases run summaries.")

table(["Model", "Params", "Epochs", "Final fit MAP@3", "Final macro-F1", "Train time"],
      [["RoBERTa-base (full data)", "125 M", "8", "**1.0000", "**1.0000", "21 min"],
       ["DeBERTa-v3-base (full data)", "184 M", "8", "0.9830", "0.9707", "40 min"],
       ["DeBERTa-v3-large (full data)", "435 M", "6", "0.9441 (best)", "0.9225", "117 min"]],
      widths=[2.1, 0.8, 0.7, 1.2, 1.1, 0.9],
      caption="Table 8 — Deployment regime: trained on all 2 000 rows. These measure fit, not "
              "generalisation, and are reported as such.")

figure(IMG + "fig5_two_regimes.png", 6.3,
       "Figure 5 — The two regimes on one axis. The blue bars are what the models understand; the "
       "gold bars are what the leaderboard rewards.")

doc.add_heading("Analysis of the trade-offs", level=3)
rich([("Pretraining buys far less generalisation than expected. ", True, False),
      ("DeBERTa-v3-base beats the from-scratch model by 0.0143 MAP@3 (0.6000 vs 0.5857) for 12.7× the "
       "parameters and 8× the training time. On an 86-question validation set, one question moving "
       "between ranks shifts the score by roughly 0.006, so that margin spans about two questions — "
       "it is not statistically meaningful. The defensible claim is that on unseen questions, at this "
       "data scale, ", False, False),
      ("no model tested learns transferable scientific reasoning", True, False),
      (". Every model sits between the 0.58 length prior and 0.60. This directly contradicts the "
       "intuition that a larger pretrained encoder should dominate, and it is the most valuable "
       "negative result in the project.", False, False)])

rich([("Pretraining buys a great deal of recall capacity. ", True, False),
      ("In the deployment regime the ordering is unambiguous: RoBERTa-base reaches a perfect 1.0000 "
       "fit by epoch 4 and holds it, DeBERTa-v3-base 0.9830. Pretrained encoders absorb 2 000 "
       "paraphrase-augmented rows quickly and robustly — and paraphrase-robust recall is what this "
       "benchmark scores.", False, False)])

rich([("Scale did not pay for itself. ", True, False),
      ("DeBERTa-v3-large is 2.4× the parameters and 2.9× the training time of the base model, yet "
       "fits ", False, False), ("worse", False, True),
      (" (0.9441 vs 0.9830) - it was still climbing at epoch 6 (0.4819 → 0.9441) and was "
       "under-trained, constrained to lr 6e-6, batch 1 with 8-step accumulation and gradient "
       "checkpointing to fit T4 memory. The lesson is that scaling helps only after the smaller model "
       "has been trained to convergence; here the compute would have been better spent on more epochs "
       "for the base model.", False, False)])

rich([("Macro-F1 exposes what MAP@3 conceals. ", True, False),
      ("DeBERTa-v3-base records the best MAP@3 (0.5360) but the worst macro-F1 (0.3038) in Table 7. "
       "It ranks better while distributing its top-1 predictions across the five labels less evenly — "
       "partially collapsing onto majority labels. Reporting MAP@3 alone would have hidden this "
       "entirely, which is the argument for carrying a second, structurally different metric.",
       False, False)])

doc.add_heading("6.4  Kaggle Performance", level=2)
para("The submission is generated by blending the three full-data models — 0.25 · RoBERTa + "
     "0.25 · DeBERTa-base + 0.50 · DeBERTa-large — for the rank-1 prediction, with ranks 2 and 3 "
     "drawn from a 50/50 blend of DeBERTa-large probabilities and the normalised option-length prior "
     "from Table 2, on the reasoning that where the model is uncertain the shallow prior contributes "
     "independent signal. Output is 500 rows of ID, Prediction with three distinct labels each.")

t = doc.add_table(rows=1, cols=1)
c = t.rows[0].cells[0]
shade(c, "FFF3CD")
c.paragraphs[0].text = ""
r = c.paragraphs[0].add_run("TO BE COMPLETED BY THE AUTHOR BEFORE SUBMISSION")
r.font.name, r.font.size, r.bold = BODY_FONT, Pt(10), True
r.font.color.rgb = RGBColor(0x85, 0x64, 0x04)
for line in ["Final public leaderboard MAP@3 :  ______________",
             "Public leaderboard rank          :  ______________",
             "Submission date                  :  ______________"]:
    p = c.add_paragraph()
    p.paragraph_format.space_after = Pt(1)
    rr = p.add_run(line)
    rr.font.name, rr.font.size = CODE_FONT, Pt(9.5)
    rr.font.color.rgb = DARK
p = c.add_paragraph()
rr = p.add_run("These fields are intentionally blank. The author's verified records cover the 15 "
               "archived pre-reformulation submissions (0.687–0.720, all below threshold); the "
               "leaderboard response for the final multiple-choice submission is to be entered here "
               "from the competition page rather than estimated.")
rr.font.name, rr.font.size, rr.italic = BODY_FONT, Pt(8.5), True
rr.font.color.rgb = GREY
para("", size=Pt(4), space_after=8)

table(["Submission generation", "Formulation", "Public MAP@3"],
      [["v59 – v98 (15 archived runs)", "5-way sequence classification, max_len 128–192",
        "0.687 – 0.720"],
       ["**Final notebook", "**multiple-choice cross-encoder, max_len 256, 3-model blend",
        "**see above"]],
      widths=[2.1, 3.0, 1.3],
      caption="Table 9 — Submission history. The 15 archived scores are documented in trials/*.txt "
              "in the repository.")

pagebreak()

# ══════════════════════════ 7. CONCLUSION ══════════════════════════
doc.add_heading("7.  Conclusion & Future Work", level=1)

doc.add_heading("7.1  Key Learnings", level=2)
bullet("fifteen experiments varied encoder, adapter, epoch count and ensembling while holding one "
       "defect constant, and all fifteen landed in a 0.033-wide band. When results are invariant to "
       "large architectural changes, the bottleneck is upstream of the model. The fix was a 128 → 256 "
       "token budget and a change of input layout, not a better encoder.",
       "A plateau across many models indicates a shared bug, not a capability ceiling — ")
bullet("a run reported 0.8409 validation and returned 0.6870 from the leaderboard. The number was not "
       "merely optimistic, it was actively misleading, and every decision taken on top of it was "
       "wasted effort. A validation score is a claim about a split; if the split is wrong, the score "
       "is fiction. The four-line grouped split with an assertion is the highest-value code in the "
       "notebook.", "A validation score is only as trustworthy as the split beneath it — ")
bullet("counting unique questions after normalisation took minutes and revealed 100 % test-question "
       "overlap and 91 % exact option-set overlap. That measurement determined the model-selection "
       "criterion, the training strategy and the interpretation of every subsequent number. Auditing "
       "the evaluation should precede optimising against it.",
       "Audit the benchmark before optimising against it — ")
bullet("DeBERTa-v3 was selected because replaced-token detection is the same operation as "
       "distractor discrimination — a defensible, mechanism-level argument. That the predicted "
       "advantage then failed to materialise on unseen questions (+0.014, inside noise) is itself the "
       "finding: a sound hypothesis, tested honestly, can be disconfirmed, and reporting that is more "
       "useful than quietly discarding it.",
       "Architecture choice should follow from the pretraining objective — and be tested — ")

doc.add_heading("7.2  Challenges Faced", level=2)
table(["Challenge", "Symptom", "Resolution"],
      [["Silent input truncation", "15 runs stuck at 0.687–0.720", "one option per sequence at max_len 256"],
       ["Validation/leaderboard divergence", "val 0.8409 vs LB 0.6870", "group split on cleaned question + assertion"],
       ["fp16 checkpoint vs GradScaler", "\"Attempting to unscale FP16 gradients\"", ".float() immediately after loading"],
       ["Positional-argument API trap", "index error in RoBERTa embeddings", "keyword-only forward calls"],
       ["T4 memory at 435 M parameters", "OOM on deberta-v3-large", "batch 1 + accum 8 + gradient checkpointing"],
       ["Experiment amnesia across 15 trials", "could not attribute score changes", "W&B config logging on every run"]],
      widths=[1.9, 2.2, 2.4],
      caption="Table 10 — Significant obstacles and their resolutions.")

doc.add_heading("7.3  Areas for Improvement", level=2)
bullet("implement the Siamese BiGRU cross-scorer specified in Section 5.3 to close the "
       "architecture-family requirement and to test empirically whether late interaction really is "
       "the wrong inductive bias here — the current argument for that claim is principled but "
       "untested.", "1. Close the RNN gap — ")
bullet("replace the single 80/20 split with 5-fold GroupKFold over cleaned questions. Each fold "
       "reports on ~50 questions, where roughly one question is worth 0.01 MAP@3; averaging five "
       "folds would convert the 0.014 scratch-versus-DeBERTa gap from an anecdote into a measurement "
       "with an error bar. This is the single highest-value next experiment.",
       "2. Replace point estimates with cross-validated confidence intervals — ")
bullet("since evaluation rewards invariance to wrapper and synonym perturbation, generate that "
       "invariance explicitly: re-wrap each training question with all six prefixes and four "
       "suffixes, and apply consistency regularisation so that paraphrases of one question are forced "
       "to identical predicted distributions.",
       "3. Train the objective that is actually scored — ")
bullet("DeBERTa-v3-large was still improving at its final epoch (0.4819 → 0.9441). Train it to "
       "convergence before concluding anything about scale, since the current comparison penalises it "
       "for an under-trained schedule rather than for capacity.",
       "4. Train the large model to convergence — ")
bullet("the residual errors identified in error analysis are option pairs separated by one qualifier, "
       "requiring external facts rather than more fine-tuning. A retrieval stage over a science corpus "
       "targets that specific residual — but only after cross-validation confirms there is a "
       "generalisation gap large enough to be worth closing.",
       "5. Retrieval augmentation, but only afterwards — ")

# ══════════════════════════ 8. REFERENCES ══════════════════════════
doc.add_heading("8.  References", level=1)


def ref(txt):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.left_indent = Inches(0.32)
    p.paragraph_format.first_line_indent = Inches(-0.32)
    r = p.add_run(txt)
    r.font.name, r.font.size = BODY_FONT, Pt(9.5)
    r.font.color.rgb = DARK


ref("[1]  Vaswani, A., Shazeer, N., Parmar, N., et al. (2017). Attention Is All You Need. "
    "Advances in Neural Information Processing Systems 30 (NeurIPS 2017). arXiv:1706.03762.")
ref("[2]  Devlin, J., Chang, M.-W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of Deep "
    "Bidirectional Transformers for Language Understanding. NAACL-HLT 2019. arXiv:1810.04805.")
ref("[3]  Liu, Y., Ott, M., Goyal, N., et al. (2019). RoBERTa: A Robustly Optimized BERT Pretraining "
    "Approach. arXiv:1907.11692. Model card: huggingface.co/roberta-base")
ref("[4]  He, P., Liu, X., Gao, J., & Chen, W. (2021). DeBERTa: Decoding-enhanced BERT with "
    "Disentangled Attention. International Conference on Learning Representations (ICLR 2021). "
    "arXiv:2006.03654.")
ref("[5]  He, P., Gao, J., & Chen, W. (2023). DeBERTaV3: Improving DeBERTa using ELECTRA-Style "
    "Pre-Training with Gradient-Disentangled Embedding Sharing. ICLR 2023. arXiv:2111.09543. "
    "Model card: huggingface.co/microsoft/deberta-v3-base")
ref("[6]  Clark, K., Luong, M.-T., Le, Q. V., & Manning, C. D. (2020). ELECTRA: Pre-training Text "
    "Encoders as Discriminators Rather Than Generators. ICLR 2020. arXiv:2003.10555.")
ref("[7]  Kudo, T., & Richardson, J. (2018). SentencePiece: A simple and language independent subword "
    "tokenizer and detokenizer for Neural Text Processing. EMNLP 2018 (System Demonstrations). "
    "arXiv:1808.06226.")
ref("[8]  Sennrich, R., Haddow, B., & Birch, A. (2016). Neural Machine Translation of Rare Words with "
    "Subword Units. ACL 2016. arXiv:1508.07909.")
ref("[9]  Loshchilov, I., & Hutter, F. (2019). Decoupled Weight Decay Regularization (AdamW). "
    "ICLR 2019. arXiv:1711.05101.")
ref("[10] Micikevicius, P., Narang, S., Alben, J., et al. (2018). Mixed Precision Training. "
    "ICLR 2018. arXiv:1710.03740.")
ref("[11] Chen, T., Xu, B., Zhang, C., & Guestrin, C. (2016). Training Deep Nets with Sublinear "
    "Memory Cost (gradient checkpointing). arXiv:1604.06174.")
ref("[12] Hu, E. J., Shen, Y., Wallis, P., et al. (2022). LoRA: Low-Rank Adaptation of Large Language "
    "Models. ICLR 2022. arXiv:2106.09685.")
ref("[13] Conneau, A., Kiela, D., Schwenk, H., Barrault, L., & Bordes, A. (2017). Supervised Learning "
    "of Universal Sentence Representations from Natural Language Inference Data (InferSent). "
    "EMNLP 2017. arXiv:1705.02364.")
ref("[14] Wolf, T., Debut, L., Sanh, V., et al. (2020). Transformers: State-of-the-Art Natural "
    "Language Processing. EMNLP 2020 (System Demonstrations). Library: huggingface.co/transformers")
ref("[15] Paszke, A., Gross, S., Massa, F., et al. (2019). PyTorch: An Imperative Style, "
    "High-Performance Deep Learning Library. NeurIPS 2019. arXiv:1912.01703.")
ref("[16] Biewald, L. (2020). Experiment Tracking with Weights and Biases. Software: wandb.com. "
    "Project: wandb.ai/aryanbabar-indian-institute-of-technology-madras/smart-mcq-solver")
ref("[17] Pedregosa, F., Varoquaux, G., Gramfort, A., et al. (2011). Scikit-learn: Machine Learning "
    "in Python. Journal of Machine Learning Research 12, 2825–2830.")
ref("[18] Kaggle (2026). Smart MCQ Solver Challenge — private competition. "
    "kaggle.com/competitions/smart-mcq-solver-challenge")

para("", size=Pt(6), space_after=2)
para("Reproducibility. All quantitative claims in this report are recomputable: dataset statistics "
     "and the Section 3.2 overlap audit from train.csv and test.csv with the de-boilerplating "
     "function in Section 3.3; all training metrics from the Weights & Biases project cited in [16]; "
     "the 15 pre-reformulation leaderboard scores from trials/*.txt in the project repository.",
     size=Pt(8.5), italic=True, color=GREY)

doc.save(OUT)
print("saved:", OUT)
