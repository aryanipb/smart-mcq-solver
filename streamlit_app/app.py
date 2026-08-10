"""
Smart MCQ Solver — live demo (Streamlit Community Cloud).

Loads the fine-tuned RoBERTa-base multiple-choice cross-encoder
(aryanbabar170205/smart-mcq-roberta-base) and predicts the top-3 most likely
correct options, in ranked order, for a 5-option multiple-choice question —
the same AutoModelForMultipleChoice formulation used in the project notebook.

Part of: DL & GenAI Project [BSDA2001P] — Smart MCQ Solver Challenge.
"""
import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForMultipleChoice

MODEL_ID = "aryanbabar170205/smart-mcq-roberta-base"
LETTERS = ["A", "B", "C", "D", "E"]
MAX_LEN = 256

st.set_page_config(page_title="Smart MCQ Solver", page_icon="🧠", layout="centered")


@st.cache_resource(show_spinner="Loading fine-tuned RoBERTa-base from the Hugging Face Hub...")
def load_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForMultipleChoice.from_pretrained(MODEL_ID).to(device).eval()
    return tok, model, device


st.title("🧠 Smart MCQ Solver")
st.caption(
    "Fine-tuned **RoBERTa-base** (`AutoModelForMultipleChoice` cross-encoder) — "
    "*DL & GenAI Project [BSDA2001P]*, Smart MCQ Solver Challenge. "
    "[Model](https://huggingface.co/aryanbabar170205/smart-mcq-roberta-base) · "
    "[Project repo](https://github.com/aryanipb/smart-mcq-solver)"
)
st.write(
    "Each option is scored as a separate `(question, option)` pair through one "
    "shared encoder, then ranked by softmax probability — exactly the multiple-choice "
    "formulation described in the project report."
)

tok, model, device = load_model()

with st.form("mcq_form"):
    question = st.text_area(
        "Question",
        "What is the Heisenberg uncertainty principle?",
        height=80,
    )
    defaults = [
        "It states that position and momentum of a particle cannot both be known exactly at the same time.",
        "It states that energy is always conserved in a closed system.",
        "It states that entropy always increases in an isolated system.",
        "It states that mass and energy are equivalent.",
        "It states that all matter exhibits both particle and wave properties.",
    ]
    options = [
        st.text_input(f"Option {LETTERS[i]}", defaults[i]) for i in range(5)
    ]
    submitted = st.form_submit_button("Predict top-3", type="primary")

if submitted:
    if not question.strip() or any(not o.strip() for o in options):
        st.warning("Please fill in the question and all five options.")
    else:
        with torch.no_grad():
            first = [question] * 5
            second = options
            enc = tok(first, second, truncation=True, max_length=MAX_LEN,
                      padding="max_length", return_tensors="pt")
            ids = enc["input_ids"].unsqueeze(0).to(device)
            mask = enc["attention_mask"].unsqueeze(0).to(device)
            logits = model(input_ids=ids, attention_mask=mask).logits[0]
            probs = torch.softmax(logits, -1).cpu().numpy()

        order = probs.argsort()[::-1]
        top3 = " ".join(LETTERS[i] for i in order[:3])

        st.success(f"**Top-3 ranked prediction:  `{top3}`**")
        for rank, i in enumerate(order):
            marker = "🥇🥈🥉"[rank] if rank < 3 else "  "
            st.write(f"{marker}  **{LETTERS[i]}**  —  {probs[i]*100:5.1f}%   {options[i]}")
            st.progress(float(probs[i]))
