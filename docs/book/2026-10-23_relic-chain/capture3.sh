#!/usr/bin/env zsh
# Run every command the book will show, for real, and keep what it printed.
# Each capture: captures/NN-slug.txt = "$ <shown command>" + output + "(exit N · T s)".
# The .txt files are the book's evidence: writers quote them, reviewers check against them,
# and cards.py renders them to images/NN-slug.png. Anything the book will claim — a number,
# a source file, a directory listing — gets a capture, or a reviewer will call it invented.
#
# Edit the CONFIG and the COMMANDS section, then run it in a herdr pane (it can be slow):
#   herdr pane run <PANE> "zsh capture.sh; RC=\$?; herdr agent prompt <AGENT> \"captures rc=\$RC\""
setopt pipefail
B=${0:A:h}; C=$B/captures; mkdir -p $C

# ── CONFIG ──────────────────────────────────────────────────────────────────
TOOL=relic-extract                       # the name printed after "$ " in every capture
TOOLCMD=($HOME/.local/bin/relic-extract)  # how to actually run it
WORKDIR=/opt/Code/github.com/Soul-Brews-Studio/relic-extract
TIMEOUT=300
export PATH=$HOME/.local/bin:$HOME/.cargo/bin:/opt/homebrew/bin:$PATH
R4="RELIC4_ROOT=$HOME/relic4-fresh"

# run NN slug -- args...          → "$ TOOL args"   (runs TOOLCMD args)
run() {
  local nn=$1 slug=$2; shift 3
  local f=$C/$nn-$slug.txt t0=$(date +%s.%N)
  print -r -- "$ $TOOL $*" > $f
  (cd $WORKDIR && timeout $TIMEOUT $TOOLCMD "$@") >> $f 2>&1; local rc=$?
  printf '(exit %d · %.1f s)\n' $rc $(( $(date +%s.%N) - t0 )) >> $f
  printf '%s %-28s exit %d  %4d lines\n' $nn $slug $rc $(wc -l < $f)
}
# runsh NN slug "shown command" "shell command"   → for pipes, ssh, servers, cat of a source file
ONLY=($@)   # zsh capture3.sh 150 153 -> re-run only those captures
runsh() {
  (( ${#ONLY} )) && (( ! ${ONLY[(Ie)$1]} )) && return
  local nn=$1 slug=$2 disp=$3 cmd=$4
  local f=$C/$nn-$slug.txt t0=$(date +%s.%N)
  print -r -- "$ $disp" > $f
  (cd $WORKDIR && timeout $TIMEOUT zsh -c "$cmd") >> $f 2>&1; local rc=$?
  printf '(exit %d · %.1f s)\n' $rc $(( $(date +%s.%N) - t0 )) >> $f
  printf '%s %-28s exit %d  %4d lines\n' $nn $slug $rc $(wc -l < $f)
}

date "+== capture3 start %H:%M:%S"
# ── PART 5 (2026-10-25): gb300 against z.ai, the whole year ──────────────────
# capture3.sh holds ONLY part 5: re-running it never touches parts 1-4's captures or publishes anything.
S=$HOME/.claude/projects/-opt-Code-github-com-Soul-Brews-Studio-relic-extract/008db2b3-17a7-47f4-b118-742ebc7ae6e7.jsonl
PO="python3 $B/paneout.py $S"
TO="python3 $B/toolout.py $S"
VS="python3 $B/vs.py"
# ch13 the same windows, two models
runsh 150 vs-agree     "python3 vs.py agree" "$VS agree"
runsh 151 vs-trial     "python3 vs.py trial" "$VS trial"
runsh 152 vs-opening   "python3 vs.py opening" "$VS opening"
runsh 153 vs-example   "python3 vs.py example" "$VS example"
# ch14 friction and lesson
runsh 154 vs-friction  "python3 vs.py friction" "$VS friction"
runsh 170 vs-lesson    "rg -A2 'lesson:' captures/154-vs-friction.txt" "rg -A2 'lesson:' $B/captures/154-vs-friction.txt"
runsh 155 vs-months    "python3 vs.py months" "$VS months"
# ch15 speed, and whose GPU
runsh 156 vs-speed     "python3 vs.py speed" "$VS speed"
runsh 157 pace-1025    "python3 vs.py pace 2026-10-25" "$VS pace 2026-10-25"
runsh 158 gpu-100      "ssh gb300 nvidia-smi …   (2026-10-24 23:59 +07, as it came back)" "$TO 'utilization.gpu,memory.used' 1 20 | tail -2"
runsh 159 three-workers "answers with --gb-workers 3, from readings.jsonl (as it came back)" "$TO 'h.seek(-8_000_000' 1"
runsh 160 gpu-who      "ssh gb300 nvidia-smi --query-compute-apps …   (2026-10-25 09:50 +07)" "$TO 'utilization.gpu,memory.used,memory.total' 1 20 | cut -c1-110"
runsh 161 gpu-vllm     "ssh gb300 'curl 127.0.0.1:PORT/metrics' per vLLM server (09:50 +07)" "$TO 'vllm:(num_requests_running' 1 40 | rg -v 'success_total 0.0' | awk '!(/success_total/ && seen[\$0]++)'"
runsh 162 queue-done   "the gb300 queue's pane, when it ended" "$PO 'PANE w12:p1Y gb300-queue rc=0'"
runsh 163 zai-slow     "z.ai pane, last 200 lines, 20:50 +07: rg -c failed|429|rate, median s" "$TO \"rg -c 'failed|429|rate'\" 1; $TO \"rg 'failed|429|rate' | cut -c1-160\" 1 | tail -n +2 | sed -E 's/^ +1 +//' | cut -c1-70"
# ch16 the numbers on the page that were wrong
runsh 164 st-paused    "what the watcher sent, 2026-10-25 15:15 +07" "$PO 'gb300-15m  paused   15,416' | head -10"
runsh 165 st-keys      "git show (PR #31) -- report/status.py | rg '^[-+] '" "git log --format=%h -1 --grep='cache keys days.py and blocks.py really write' | xargs -I{} git show {} -- report/status.py | rg '^[-+] ' | cut -c1-118"
runsh 166 st-empty     "why 355 windows stayed unread (as it came back)" "$TO 'empty of first 60' 1"
runsh 167 watch-fix    "diff relic-watch.sh.bak-20261025 relic-watch.sh" "diff ~/.relic-extract/lanes/relic-watch.sh.bak-20261025 ~/.relic-extract/lanes/relic-watch.sh"
runsh 168 st-now       "uv run python report/status.py" "uv run python report/status.py 2>&1 | rg -v '^direnv'"
runsh 169 git-log3     "git log --oneline 8bbefad..HEAD -- report" "git log --oneline 8bbefad..HEAD -- report | cut -c1-110"
date '+== capture3 end %H:%M:%S'
