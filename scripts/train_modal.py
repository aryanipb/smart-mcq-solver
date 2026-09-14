"""
Train RoBERTa-base (AutoModelForMultipleChoice, cross-encoder formulation) on a
Modal A10G GPU, then push the resulting checkpoint straight to the Hugging Face Hub.

Run with:  ../venv/bin/modal run scripts_tmp/train_modal.py
"""
import modal

app = modal.App("smart-mcq-deploy-train")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch==2.5.1",
        "transformers==4.46.1",
        "pandas",
        "numpy",
        "huggingface_hub",
        "scikit-learn",
    )
)


@app.function(image=image, gpu="A10G", timeout=1800)
def train_and_push(train_csv_bytes: bytes, hf_token: str, hf_repo: str) -> str:
    import io
    import re
    import numpy as np
    import pandas as pd
    import torch
    import torch.nn as nn
    from transformers import (
        AutoTokenizer, AutoModelForMultipleChoice, get_linear_schedule_with_warmup,
    )
    from huggingface_hub import HfApi, create_repo

    device = "cuda"
    LETTERS = list("ABCDE")

    # ---- data (identical cleaning logic to the project notebook) ----
    train = pd.read_csv(io.BytesIO(train_csv_bytes))
    PREFIXES = ["Pick the best possible answer:", "Select the most accurate option:",
                "Determine the correct option:", "Identify the correct statement:",
                "Choose the correct answer:", "Which of the following is correct?"]
    SUFFIXES = ["among the listed options.", "based on the given context.",
                "from the following choices.", "carefully."]

    def clean_prompt(p):
        s = str(p).strip()
        for _ in range(2):
            for x in PREFIXES:
                if s.lower().startswith(x.lower()):
                    s = s[len(x):].strip()
            for x in SUFFIXES:
                if s.lower().endswith(x.lower()):
                    s = s[:-len(x)].strip()
        return re.sub(r"\s+", " ", s).strip()

    train["question"] = train.prompt.map(clean_prompt)
    train["label"] = train.answer.map({c: i for i, c in enumerate(LETTERS)})
    for c in LETTERS:
        train[c] = train[c].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()

    print(f"train rows: {len(train)} | unique questions: {train.question.nunique()}")

    # ---- tokenize: cross-encoder (question, option) pairs, deployment regime = full data ----
    MAX_LEN = 256
    tok = AutoTokenizer.from_pretrained("roberta-base")

    def encode(df):
        first = [q for q in df.question for _ in range(5)]
        second = [str(r[c]) for _, r in df.iterrows() for c in LETTERS]
        e = tok(first, second, truncation=True, max_length=MAX_LEN,
                padding="max_length", return_tensors="pt")
        n = len(df)
        return e["input_ids"].view(n, 5, MAX_LEN), e["attention_mask"].view(n, 5, MAX_LEN)

    Xtr, Mtr = encode(train)
    ytr = torch.tensor(train.label.values)
    print("encoded:", tuple(Xtr.shape))

    # ---- model ----
    model = AutoModelForMultipleChoice.from_pretrained("roberta-base").float().to(device)

    EPOCHS, BS, LR = 6, 8, 2e-5
    from torch.utils.data import TensorDataset, DataLoader
    loader = DataLoader(TensorDataset(Xtr, Mtr, ytr), batch_size=BS, shuffle=True, drop_last=True)
    steps = len(loader) * EPOCHS
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    sch = get_linear_schedule_with_warmup(opt, int(0.1 * steps), steps)
    scaler = torch.amp.GradScaler("cuda")
    lossf = nn.CrossEntropyLoss()

    model.train()
    for ep in range(1, EPOCHS + 1):
        tot = 0.0
        for ids, msk, lab in loader:
            ids, msk, lab = ids.to(device), msk.to(device), lab.to(device)
            with torch.amp.autocast("cuda"):
                out = model(input_ids=ids, attention_mask=msk)
                loss = lossf(out.logits, lab)
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(opt)
            scaler.update()
            sch.step()
            tot += loss.item()
        print(f"epoch {ep}/{EPOCHS}  loss={tot/len(loader):.4f}")

    # ---- fit check (deployment regime: measure recall on the training data itself) ----
    model.eval()
    correct = 0
    with torch.no_grad():
        for i in range(0, len(Xtr), 32):
            ids = Xtr[i:i+32].to(device)
            msk = Mtr[i:i+32].to(device)
            with torch.amp.autocast("cuda"):
                logits = model(input_ids=ids, attention_mask=msk).logits
            pred = logits.argmax(-1).cpu()
            correct += (pred == ytr[i:i+32]).sum().item()
    fit_acc = correct / len(Xtr)
    print(f"final training-set fit accuracy: {fit_acc:.4f}")

    # ---- push to hub ----
    api = HfApi(token=hf_token)
    create_repo(hf_repo, token=hf_token, exist_ok=True, repo_type="model")
    save_dir = "/tmp/mcq_model"
    model.save_pretrained(save_dir)
    tok.save_pretrained(save_dir)

    readme = f"""---
license: mit
tags:
- multiple-choice
- roberta
- smart-mcq-solver
---
# RoBERTa-base — Smart MCQ Solver Challenge

Fine-tuned `roberta-base` on the Smart MCQ Solver Challenge dataset using the
`AutoModelForMultipleChoice` cross-encoder formulation: each of the 5 options is
scored as a separate (question, option) pair through one shared encoder, then
softmaxed into a ranking.

- Base model: roberta-base (125M params)
- Trained on: 2,000 rows, full-data deployment regime, {EPOCHS} epochs
- Final training-set fit accuracy: {fit_acc:.4f}
- Part of: DL & GenAI Project [BSDA2001P], Smart MCQ Solver Challenge

See the project repository for the full notebook, EDA and report.
"""
    with open(f"{save_dir}/README.md", "w") as f:
        f.write(readme)

    api.upload_folder(folder_path=save_dir, repo_id=hf_repo, repo_type="model")
    return f"pushed to https://huggingface.co/{hf_repo}  |  fit_acc={fit_acc:.4f}"


@app.local_entrypoint()
def main(hf_token: str, hf_repo: str, train_csv_path: str = "data/train.csv"):
    import os
    if not os.path.exists(train_csv_path) and os.path.exists("train.csv"):
        train_csv_path = "train.csv"
    with open(train_csv_path, "rb") as f:
        csv_bytes = f.read()
    result = train_and_push.remote(csv_bytes, hf_token, hf_repo)
    print(result)
