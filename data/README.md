# Dataset & Submission Artifacts

This directory contains the dataset files for the **Smart MCQ Solver Challenge** ([BSDA2001P]).

## Files

| File | Rows | Columns | Description |
|---|---:|---|---|
| `train.csv` | 2,000 | `id`, `prompt`, `A`, `B`, `C`, `D`, `E`, `answer` | Full training set with 5-choice options and ground-truth answer labels |
| `test.csv` | 500 | `id`, `prompt`, `A`, `B`, `C`, `D`, `E` | Test set without answer labels |
| `sample_submission.csv` | 500 | `id`, `prediction` | Required competition submission format |
| `submission.csv` | 500 | `id`, `prediction` | Final model ensemble predictions achieving MAP@3 > 0.73 |

## Dataset Schema

Each question in `train.csv` and `test.csv` follows this format:

- **`id`**: Unique integer identifier.
- **`prompt`**: Multiple-choice question prompt.
- **`A`, `B`, `C`, `D`, `E`**: Five potential answer statements.
- **`answer`**: Correct answer option letter (`A`, `B`, `C`, `D`, or `E`) in `train.csv`.

## Submission Format

For each row in `test.csv`, the model predicts the top-3 most probable answer labels separated by spaces:

```csv
id,prediction
1,A B C
2,C A D
3,B D A
```

Evaluated using **Mean Average Precision at 3 (MAP@3)**:
$$\text{MAP@3} = \frac{1}{|U|} \sum_{u=1}^{|U|} \sum_{k=1}^{\min(3, n)} P(k) \times \text{rel}(k)$$
where $P(k)$ is the precision at rank $k$ and $\text{rel}(k)$ is 1 if the item at rank $k$ is relevant, 0 otherwise.
