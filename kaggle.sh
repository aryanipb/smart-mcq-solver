#!/usr/bin/env bash
# =============================================================================
# kaggle.sh — DLGenAI Project Kaggle Helper
# Usage:
#   ./kaggle.sh pull          — Pull latest notebook from Kaggle
#   ./kaggle.sh push          — Push local notebook to Kaggle & trigger run
#   ./kaggle.sh status        — Check if notebook run has finished
#   ./kaggle.sh submit        — Submit submission.csv to competition
#   ./kaggle.sh output        — Download output files from last notebook run
#   ./kaggle.sh open          — Print browser URL to your notebook
# =============================================================================

set -e

# To authenticate, set KAGGLE_API_TOKEN environment variable or configure ~/.kaggle/kaggle.json
export KAGGLE_API_TOKEN="${KAGGLE_API_TOKEN:-}"

# Use virtualenv kaggle binary if present, otherwise fallback to PATH
if [ -x "$(dirname "$0")/venv/bin/kaggle" ]; then
  KAGGLE="$(dirname "$0")/venv/bin/kaggle"
else
  KAGGLE="kaggle"
fi

KERNEL="aryanb170205/dl-24f1001839-notebook-t22026"
COMPETITION="smart-mcq-solver-challenge"
NOTEBOOK_DIR="$(dirname "$0")/notebooks"
PROJECT_DIR="$(dirname "$0")"

case "$1" in

  pull)
    echo "⬇️  Pulling notebook from Kaggle..."
    $KAGGLE kernels pull "$KERNEL" -p "$NOTEBOOK_DIR" --metadata
    echo "✅ Done. Files in $NOTEBOOK_DIR:"
    ls -lh "$NOTEBOOK_DIR"
    ;;

  push)
    echo "⬆️  Pushing notebook to Kaggle and triggering run..."
    $KAGGLE kernels push -p "$NOTEBOOK_DIR"
    echo "✅ Push complete! Notebook is now queued on Kaggle."
    echo "   Check status with:  ./kaggle.sh status"
    echo "   Or view at:         https://www.kaggle.com/code/$KERNEL"

    echo "🔃 Syncing notebook + kernel environment to git..."
    git -C "$PROJECT_DIR" add \
      "$NOTEBOOK_DIR/dl-24f1001839-notebook-t22026.ipynb" \
      "$NOTEBOOK_DIR/kernel-metadata.json"
    if ! git -C "$PROJECT_DIR" diff --cached --quiet; then
      git -C "$PROJECT_DIR" commit -m "Update Kaggle notebook and kernel environment ($(date '+%Y-%m-%d %H:%M'))"
      git -C "$PROJECT_DIR" push origin main
      echo "✅ Git sync complete."
    else
      echo "ℹ️  No notebook/kernel changes to commit."
    fi
    ;;

  status)
    echo "📊 Notebook run status..."
    $KAGGLE kernels status "$KERNEL"
    ;;

  output)
    echo "⬇️  Downloading output files from last run..."
    mkdir -p "$PROJECT_DIR/kaggle_output"
    $KAGGLE kernels output "$KERNEL" -p "$PROJECT_DIR/kaggle_output"
    echo "✅ Files saved to kaggle_output/"
    ls -lh "$PROJECT_DIR/kaggle_output/"
    ;;

  submit)
    if [ ! -f "$PROJECT_DIR/submission.csv" ]; then
      echo "❌ submission.csv not found in project root!"
      echo "   Run the model first, then try again."
      exit 1
    fi
    echo "📤 Submitting submission.csv to $COMPETITION..."
    $KAGGLE competitions submit -c "$COMPETITION" \
      -f "$PROJECT_DIR/submission.csv" \
      -m "Submission from local machine $(date '+%Y-%m-%d %H:%M')"
    echo "✅ Submitted! Check leaderboard at:"
    echo "   https://www.kaggle.com/competitions/$COMPETITION/leaderboard"
    ;;

  leaderboard)
    echo "🏆 Competition leaderboard (top 20)..."
    $KAGGLE competitions leaderboard "$COMPETITION" --show | head -25
    ;;

  open)
    echo "🔗 Open your notebook in browser:"
    echo "   https://www.kaggle.com/code/$KERNEL"
    ;;

  *)
    echo "DLGenAI Kaggle Helper"
    echo ""
    echo "Usage: ./kaggle.sh <command>"
    echo ""
    echo "Commands:"
    echo "  pull        — Pull latest notebook .ipynb from Kaggle"
    echo "  push        — Push notebook to Kaggle & trigger a run (uses GPU if enabled)"
    echo "  status      — Check if the notebook run has finished"
    echo "  output      — Download output files (submission.csv etc.) from last run"
    echo "  submit      — Submit local submission.csv to the competition"
    echo "  leaderboard — Show competition leaderboard"
    echo "  open        — Print browser URL to your Kaggle notebook"
    ;;

esac
