#!/bin/zsh
# score the merged data with the kept fine-tuned model (no retraining): export -> gb300 score-only -> stt.json
set -e
cd /opt/Code/github.com/Soul-Brews-Studio/relic-extract
D=$HOME/.relic-extract/report/stt-data
uv run --quiet --with rapidfuzz --with scikit-learn python report/stt.py --export $D
scp -q $D/all.jsonl report/stt_train.py gb300:stt-train/
ssh -o BatchMode=yes gb300 'cd ~/stt-train && ~/fm17-voice/.venv/bin/python stt_train.py --data ~/stt-train --score-only 2>&1 | grep -v -e Warning -e "Loading weights"'
scp -q gb300:stt-train/scores.jsonl $D/scores.jsonl && chmod 600 $D/scores.jsonl
uv run --quiet --with rapidfuzz --with scikit-learn python report/stt.py --scores $D/scores.jsonl 2>&1 | grep -v '^direnv' | tail -20
