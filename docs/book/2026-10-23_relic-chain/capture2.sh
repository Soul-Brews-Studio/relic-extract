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
ONLY=($@)   # zsh capture2.sh 105 107 -> re-run only those captures
runsh() {
  (( ${#ONLY} )) && (( ! ${ONLY[(Ie)$1]} )) && return
  local nn=$1 slug=$2 disp=$3 cmd=$4
  local f=$C/$nn-$slug.txt t0=$(date +%s.%N)
  print -r -- "$ $disp" > $f
  (cd $WORKDIR && timeout $TIMEOUT zsh -c "$cmd") >> $f 2>&1; local rc=$?
  printf '(exit %d · %.1f s)\n' $rc $(( $(date +%s.%N) - t0 )) >> $f
  printf '%s %-28s exit %d  %4d lines\n' $nn $slug $rc $(wc -l < $f)
}

date "+== capture2 start %H:%M:%S"
# ── PART 4 (2026-10-24): windows, two models, spoken prompts, long jobs ──────
S=$HOME/.claude/projects/-opt-Code-github-com-Soul-Brews-Studio-relic-extract/008db2b3-17a7-47f4-b118-742ebc7ae6e7.jsonl
PO="python3 $B/paneout.py $S"
# ch9 windows: 3h, 1h, 15m
runsh 100 readings-help "python report/readings.py --help" ".venv/bin/python report/readings.py --help"
runsh 101 blocks-3h     "the 3-hour lane, as its pane reported (blocks.py)" "$PO 'PANE w12:pS' | tail -8"
runsh 102 blocks-1h     "the 1-hour lane, as its pane reported (blocks.py --hours 1)" "$PO 'PANE w12:pT'"
runsh 103 prompt-15m    "rg -n 'these 15 minutes|Describe the day' report/readings.py" "rg -n 'these 15 minutes|Describe the day' report/readings.py"
runsh 104 deep-keys     "rg -n 'friction|lesson|keys=keys|keys or KEYS' report/readings.py report/days.py" "rg -n 'friction|lesson|keys=keys|keys or KEYS' report/readings.py report/days.py | cut -c1-150"
runsh 105 deep-reading  "python3 deep.py any 1   (one 15-minute window, deep)" "python3 $B/deep.py any 1"
runsh 106 window-row    "one 1-hour row on the page, with its session ids (report.json)" "python3 -c \"import json,os;W=json.load(open(os.path.expanduser('~/.relic-extract/report/report.json')))['windows']['1h gb300']['rows'];[print(r[0], r[1]//60, r[2], r[3], r[4], ' '.join(s[:8] for s in (r[8] if len(r)>8 else [])[:4]), '+%d'%max(0,len(r[8])-4) if len(r)>8 else '') for r in W if r[0]=='2026-10-23' and r[1]>=1140]\""
runsh 107 progress      "python3 progress.py" "python3 $B/progress.py"
# ch10 two models, the same windows
runsh 110 build-report  "just report" "just report 2>&1 | rg '^report|windows|lane' | head -12"
runsh 111 lanes-table   "python3 lanes.py" "python3 $B/lanes.py"
runsh 112 lanes-agree   "python3 lanes.py agree" "python3 $B/lanes.py agree"
runsh 113 lane-speed    "python3 speed.py   (seconds per answer, per lane)" "python3 $B/speed.py"
# ch11 spoken or typed
runsh 120 wispr         "sqlite3 'file:flow.sqlite?mode=ro' (Wispr Flow history: counts only)" "sqlite3 -readonly \"$HOME/Library/Application Support/Wispr Flow/flow.sqlite\" \"select count(*) AS dictations, min(substr(timestamp,1,10)) AS first, max(substr(timestamp,1,10)) AS last from History; select app, count(*) from History group by 1 order by 2 desc limit 5;\""
runsh 121 stt-ngram     "uv run … python report/stt.py   (as its pane reported)" "$PO 'PANE w12:p13'"
runsh 128 stt-metrics   "ssh gb300 cat stt-train/metrics.json   (best epoch and the n-gram baseline, same split)" "ssh -o BatchMode=yes gb300 cat stt-train/metrics.json | python3 -c \"import json,sys;m=json.load(sys.stdin);print('fine-tuned  ', m['best']);print('n-gram base ', m['baseline']);print({k:m[k] for k in ('train','train_spoken','held_out','held_out_spoken','neg_per_pos','epochs','secs')})\""
runsh 122 stt-export    "rg -n 'neg-per-pos|cut = |w = torch|best is None' report/stt_train.py" "rg -n 'neg-per-pos|cut = |w = torch|best is None' report/stt_train.py | cut -c1-140"
runsh 123 stt-train     "ssh gb300 python stt_train.py   (as its pane reported)" "$PO 'PANE w12:p14' | rg -v 'UNEXPECTED|MISSING|Notes:|Writing model|Loading weights'"
runsh 124 stt-scores    "uv run … python report/stt.py --scores stt-data/scores.jsonl" "uv run --quiet --with rapidfuzz --with scikit-learn python report/stt.py --scores ~/.relic-extract/report/stt-data/scores.jsonl 2>&1 | rg -v '^direnv' | tail -20"
runsh 125 stt-projects  "the projects spoken most (stt.json)" "python3 -c \"import json,os;d=json.load(open(os.path.expanduser('~/.relic-extract/report/stt.json')));print('apps', d['apps']);[print(f\\\"{p['cat'][:40]:<40} {p['prompts']:>6,} prompts {p['spoken']/p['prompts']:5.0%} spoken\\\") for p in d['projects'][:8]]\""
runsh 126 stt-rescore   "zsh stt-rescore.sh   (export -> gb300 --score-only -> stt.py --scores, as its pane reported)" "$PO 'PANE w12:p19' | rg -v 'herdr pane close'"
runsh 127 stt-rescore-sh "cat stt-rescore.sh" "cat $B/stt-rescore.sh"
# ch12 long jobs that live through the night
runsh 130 refused       "the 15m lane's pane, 2026-10-24 08:05 (+07)" "$PO 'Connection refused' | head -9"
runsh 131 tunnel-code   "sed -n '/^_TUN/,/time.sleep(3)/p' report/days.py" "sed -n '/^_TUN/,/time.sleep(3)/p' report/days.py"
runsh 132 gaps          "python3 gaps.py gb300 2026-10-24" "python3 $B/gaps.py gb300 2026-10-24"
runsh 133 cycle         "cat /tmp/relic-gb15-cycle.sh" "cat /tmp/relic-gb15-cycle.sh"
runsh 134 kill-save     "git show 32368be -- report/readings.py | rg '^[-+] '" "git show 32368be -- report/readings.py | rg '^[-+] ' | cut -c1-120"
runsh 135 kill-test     "timeout -s TERM 15 python report/readings.py --unit 15m … --limit 40" "tail -7 /tmp/killtest2.log | cut -c1-110; python3 -c \"import json,re,os;c=json.load(open(os.path.expanduser('~/.relic-extract/report/readings-cache-15m-gb300-qwen3_14b-deep.json')));p=re.findall(r'^  (\\d{4}-\\S+ \\S+) ·',open('/tmp/killtest2.log').read(),re.M);print(len(p),'printed,',sum(x in c and 'friction' in c[x] for x in p),'in the cache with friction')\"; echo \"reopened lines: \$(rg -c reopened /tmp/killtest2.log || echo 0)\""
runsh 136 scan-sessions "duckdb: sessions in relic-scan's meta, now and in the kept copy" "duckdb -c \"select 'now' AS copy, count(*) AS sessions from '\$HOME/.relic-scan/meta/sessions.parquet' union all select 'before-nat-incident', count(*) from '\$HOME/.relic-scan.before-nat-incident-2026-10-24/meta/sessions.parquet'\""
runsh 139 scan-message  "what relic4-scan sent back, 2026-10-24 08:18 (+07)" "$PO 'From relic4-scan: ~/.relic-scan is whole' | head -2 | fold -s -w 94"
runsh 108 lane-restart  "herdr pane read w12:p17   (the gb300 queue, after the fixes)" "herdr pane read w12:p17 --source recent-unwrapped --lines 400 | rg '^== |^readings:' | head -4"
runsh 137 tz            "date; ls -l /etc/localtime" "date '+%Y-%m-%d %H:%M:%S %Z (%z)'; ls -l /etc/localtime | sed 's/.*-> //'"
runsh 138 git-log2      "git log --oneline 68ddcb2..HEAD" "git log --oneline 68ddcb2..HEAD | cut -c1-110"

runsh 140 merge-message "what relic4-scan answered about the jump, 2026-10-24 (+07)" "$PO 'the jump is real data' | head -2 | fold -s -w 94"
runsh 141 scan-log      "relic-scan log | head -8" "relic-scan log | head -8 | cut -c1-118"
runsh 142 scan-tiers    "duckdb: sessions by engine and tier (meta/sessions.parquet)" "duckdb -c \"select engine, tier, count(*) AS sessions from '\$HOME/.relic-scan/meta/sessions.parquet' group by all order by sessions desc\""
runsh 143 rerun-slip    "what the slipped capture2.sh re-ran (kept in /tmp/bk/captures-rerun-1024)" "ls /tmp/bk/captures-rerun-1024 | wc -l; rg -n 'Version ID|no leaks' /tmp/bk/captures-rerun-1024/60-publish.txt | sed 's/\\x1b\\[[0-9;]*m//g' | cut -c1-90"
date '+== capture2 end %H:%M:%S'
