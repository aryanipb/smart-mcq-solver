# Level 1 Viva Presentation Script: Smart MCQ Solver Challenge
**Duration: 30 minutes**
**Goal: Explain the complete notebook, methodology, struggles, and code with 100% authenticity.**

---

## Part 1: Introduction & The Core Problem (Minutes 0 - 5)

**[Examiner introduces themselves and asks you to begin]**

**You:**
"Hello! Today I’ll be walking you through my project for the Smart MCQ Solver Challenge. The goal of this competition was to build an intelligent system capable of solving complex multiple-choice questions and predicting the top three most likely answers, ranked by probability, evaluated using Mean Average Precision at 3 (MAP@3).

Before I show you the final notebook, I want to talk about my journey. It wasn't a straight line. In my first few weeks, I made a critical error in my problem formulation. I treated this as a standard 5-class sequence classification task (`AutoModelForSequenceClassification`). I simply concatenated the question and all five options together like this: `[CLS] Prompt [SEP] Option A Option B Option C Option D Option E`. 

This approach completely failed. My public leaderboard scores were stuck at 0.69-0.70. Why? Two massive reasons I later discovered through EDA:
1. **Truncation:** Sticking 5 options together created sequences of 250-650 tokens. Because I was using `max_length=128` to save memory, options D and E were literally being truncated and thrown away by the tokenizer. The model never even saw them!
2. **Wrong Inductive Bias:** A sequence classifier evaluates the massive text block as a whole. It doesn't compare Option A *against* Option B. The options weren't competing; they were just noise to the model.

Once I realized this, I completely scrapped my approach and rebuilt the pipeline from the ground up. This brings us to my final, successful notebook, which easily crosses the 0.73 cutoff."

---

## Part 2: Exploratory Data Analysis & Smart Preprocessing (Minutes 5 - 12)

**You:**
"Let me walk you through the EDA in my notebook, which drove all my design decisions. 

**Finding 1: Boilerplate Noise**
When I looked at the text, I noticed that almost every prompt had meaningless boilerplate wrappers like 'Pick the best possible answer:' or 'Identify the correct statement:'. I wrote regular expressions to strip these prefixes and suffixes completely so the model only focuses on the actual physics or science question.

**Finding 2: The 'Fake' 2000 Rows & Data Leakage**
This was my biggest breakthrough. The training set has 2,000 rows. But when I cleaned the prompts, I found there are only **252 genuinely unique questions**. Each question is repeated about 7-8 times. 
Why? Because the distractors (the wrong options) have tiny synonym swaps. For example, one row might say 'light-ion' and another says 'heavy-ion', or 'method' versus 'approach'. 

In my early trials, I used a standard `train_test_split`. Because of these duplicated questions, the same core question ended up in both the training set and the validation set. My model was simply memorizing the answers, giving me a 'fake' validation score of 0.85, but bombing on the leaderboard. 
**My Fix:** I implemented a strict Group-Aware Split based on the unique 'cleaned' question strings. Now, a question and all its copies stay entirely on one side of the split. My validation score finally became honest.

**Finding 3: Why TF-IDF Failed**
I also tested a TF-IDF cosine similarity baseline. It scored lower than random guessing (~0.33). Because the distractors are near-perfect copies of the correct answer differing by only 2 or 3 words, bag-of-words completely fails. I knew I needed a Deep Cross-Encoder."

---

## Part 3: The Architecture & The 3 Models (Minutes 12 - 20)

**You:**
"So, I reformulated the task. Instead of `AutoModelForSequenceClassification`, I explicitly used `AutoModelForMultipleChoice`. 
This architecture takes the question and pairs it individually with each option: `(Question, Option A)`, `(Question, Option B)`, etc. It passes them through a shared encoder, generates 5 distinct logits, and then applies a softmax over them. Because I process one option at a time, the sequence lengths drop significantly, allowing me to comfortably use `max_length=256` without truncating anything.

To meet the project criteria, I trained three distinct models, fully tracked in Weights and Biases (WandB):

**1. The Scratch Transformer (Model 1)**
I built a 4-layer, 256-dimensional Transformer Encoder entirely from scratch using standard PyTorch `nn.TransformerEncoderLayer`. I initialized it with random weights. 
*Result:* It severely underperformed (MAP@3 around 0.57). Why? With only 252 unique questions, it is impossible for a randomly initialized model to learn complex science semantics. It proved that pretrained knowledge is absolutely mandatory for this task.

**2. RoBERTa-base (Model 2 - Pretrained)**
I used the classic `roberta-base`. It comes with robust pretrained representations. After full fine-tuning for 8 epochs, it achieved a strong MAP@3 of around ~0.83 on my honest deduplicated validation set.

**3. DeBERTa-v3-base (Model 3 - Pretrained)**
This was my secret weapon. DeBERTa-v3 uses disentangled attention (separating content and position) and was pretrained using ELECTRA-style replaced-token detection. Because our distractors are essentially 'replaced tokens' (e.g., swapping '10 kV' for '100 kV'), DeBERTa is mathematically perfectly suited for this task. It was consistently my strongest individual model."

---

## Part 4: Ensemble & W&B Tracking (Minutes 20 - 25)

**You:**
"To maximize my score, I didn't rely on a single model. I built a weighted probability ensemble. 
I extracted the raw softmax probabilities from my models. Using a grid search on my validation set, I optimized the weights. Since the scratch model was basically guessing based on string length, I gave it 0 weight in the final blend. The ensemble heavily favored DeBERTa and RoBERTa.

*Note: For the final Kaggle submission, I also utilized `microsoft/deberta-v3-large` trained on 100% of the dataset to push my score even higher.*

**Weights and Biases:**
Throughout this entire process, I used WandB to log my training loss, validation MAP@3, Macro-F1, and accuracy. You can see the `train_model` function in my notebook explicitly instantiating `wandb.init()`. It allowed me to instantly visualize that my scratch model was overfitting while DeBERTa was generalizing beautifully."

---

## Part 5: Code Walkthrough & Live Coding Prep (Minutes 25 - 30)

**[The examiner will likely ask you to explain a specific block of code or write a small function.]**

**If asked to explain the `AutoModelForMultipleChoice` data processing:**
**You:** "I created an `encode` function. It takes a dataframe and the tokenizer. It duplicates the 'question' string 5 times, and pairs it with the strings for options A, B, C, D, and E. The tokenizer processes these 5 pairs. I then `.view(n, 5, MAX_LEN)` the resulting tensors so that PyTorch processes them as a single batch of 5 choices per question."

**If asked about the GitHub history:**
**You:** "My progress over the last few weeks has been iterative. I have a script called `kaggle.sh` in my repository that I built to automatically pull and push notebooks to Kaggle, trigger runs, and commit the metadata to Git. That’s how I maintained a consistent, continuous deployment pipeline."

**If asked to write a Live Code snippet (e.g., How does MAP@3 work?):**
**You:** (Be ready to write this pseudo-code conceptually)
```python
def map_at_3(predictions, true_labels):
    score = 0.0
    for pred_top3, true_label in zip(predictions, true_labels):
        for rank, pred_label in enumerate(pred_top3):
            if pred_label == true_label:
                score += 1.0 / (rank + 1)
                break
    return score / len(true_labels)
```

**Final Concluding Statement:**
**You:** "Ultimately, this project taught me that blindly throwing a huge model at a problem doesn't work. The data is everything. Fixing the sequence truncation, removing the boilerplate noise, grouping the validation set by unique questions to prevent leakage, and selecting an architecture with the right inductive bias (Cross-Encoder vs Sequence Classifier) was what allowed me to conquer the leaderboard."

---

## Likely Examiner Questions & How to Answer

**Q: Why didn't you use LoRA in your final notebook?**
**A:** "In my earlier trials (like v95 and v97), I experimented heavily with PEFT/LoRA. However, since the dataset is relatively small (2000 rows) and I was using base models, a full fine-tuning pass only took about 7 minutes on a T4 GPU. Full fine-tuning adapted the encoder more aggressively to this specific scientific domain without hitting memory bottlenecks, so I favored it for the final submission."

**Q: How did you handle the class imbalance?**
**A:** "In my EDA, I plotted the distribution of the correct answers across A, B, C, D, and E. The distribution ranged from 16% to 25%. This is a very mild imbalance, so I determined that complex techniques like SMOTE or class weighting were unnecessary and would overcomplicate the loss function."

**Q: Did you use external data?**
**A:** "No external data or RAG was used in the final submission. I realized that the models already possess enough internal knowledge to solve the questions if formulated correctly. RAG was an option, but keeping the pipeline elegant and focused on pure model inference yielded excellent results above 0.73."

**Q: What is the purpose of the length prior in your ensemble?**
**A:** "During EDA, I noticed a shallow heuristic: longer text options had a slightly higher statistical chance of being the correct answer. In my final blend, for the 'tail' predictions (ranks 2 and 3), I factored in the normalized character length of the options to give a tiny boost to longer answers when the models were uncertain."
