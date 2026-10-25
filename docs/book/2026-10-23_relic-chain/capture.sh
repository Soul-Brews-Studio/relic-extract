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
runsh() {
  local nn=$1 slug=$2 disp=$3 cmd=$4
  local f=$C/$nn-$slug.txt t0=$(date +%s.%N)
  print -r -- "$ $disp" > $f
  (cd $WORKDIR && timeout $TIMEOUT zsh -c "$cmd") >> $f 2>&1; local rc=$?
  printf '(exit %d · %.1f s)\n' $rc $(( $(date +%s.%N) - t0 )) >> $f
  printf '%s %-28s exit %d  %4d lines\n' $nn $slug $rc $(wc -l < $f)
}

date '+== capture start %H:%M:%S'
run 00 help -- --help      # the help text: reviewers check every flag against it

# ── COMMANDS (one line per thing the book shows; group by chapter) ──────────
# ch1 relic-scan: what is on the machine, what changed
runsh 01 scan-help      "relic-scan --help | head -30" "relic-scan --help | head -30"
runsh 02 scan-dry       "relic-scan run --dry-run" "relic-scan run --dry-run"
runsh 03 scan-log       "relic-scan log | head -12" "relic-scan log | head -12"
runsh 04 scan-files     "ls ~/.relic-scan ~/.relic-scan/meta" "ls ~/.relic-scan ~/.relic-scan/meta"
runsh 05 scan-count     "duckdb: rows by what they are" "duckdb -c \"select coalesce(nullif(kind,''), nullif(role,''), '(none)') AS what, count(*) AS n from '\$HOME/.relic-scan/*.parquet' group by 1 order by n desc\""
# ch2 relic-extract: config, status, analyse, run
run    10 config         -- config
run    11 status         -- status
runsh 12 analyse        "relic-extract analyse --months 2026-10 --top 4" "relic-extract analyse --months 2026-10 --top 4 2>&1 | head -60"
runsh 13 whatif         "relic-extract analyse --months 2026-10 --what-if min_chars=24 --top 3 | head -14" "relic-extract analyse --months 2026-10 --what-if min_chars=24 --top 3 2>&1 | head -14"
run    14 run            -- run --no-after
runsh 15 parts          "ls ~/.relic-extract/text | head; cat ~/.relic-extract/text/_extract.json | head -12" "ls ~/.relic-extract/text | head; cat ~/.relic-extract/text/_extract.json | head -12"
runsh 16 schema         "duckdb -c \"select month, chunk, role, cat, left(text, 40) AS text, left(key, 12) AS key from '~/.relic-extract/text/2026-10.parquet' limit 3\"" "duckdb -c \"select month, chunk, role, cat, left(text, 40) AS text, left(key, 12) AS key from '\$HOME/.relic-extract/text/2026-10.parquet' limit 3\""
runsh 17 config-clean   "sed -n '/streams.text.clean/,/redact/p' ~/.arra/relic.toml" "sed -n '/streams.text.clean/,/redact/p' ~/.arra/relic.toml"
# ch3 embed on gb300
runsh 20 gb300          "ssh gb300 nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv" "ssh -o BatchMode=yes gb300 nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv"
runsh 21 cache          "du -sh ~/relic4-fresh/vec/_cache/* ~/relic4-fresh/vec/streams/*/*.lance" "du -sh ~/relic4-fresh/vec/_cache/* ~/relic4-fresh/vec/streams/*/*.lance ~/relic4-fresh/vec/text-v2/*/*.lance"
runsh 22 embed-meta     "cat ~/relic4-fresh/vec/streams/*/tools._meta.json" "cat ~/relic4-fresh/vec/streams/*/tools._meta.json"
runsh 23 embed-again    "RELIC4_ROOT=~/relic4-fresh just embed" "$R4 just embed 2>&1 | rg -v 'WARN|Warning|^cd ' | tail -4"
# ch4 search: ours against relic3
runsh 30 search-fused   "RELIC4_ROOT=~/relic4-fresh just search 'why did black.local keep rebooting' -n 6" "$R4 just search 'why did black.local keep rebooting' -n 6 2>&1 | rg -v 'WARN|Warning|redirects|Hub|^W1|Loading|^uv run'"
runsh 31 search-file    "RELIC4_ROOT=~/relic4-fresh just search semantics_14_umap_map -n 3 --mode icu" "$R4 just search semantics_14_umap_map -n 3 --mode icu 2>&1 | rg -v 'WARN|Warning|redirects|^uv run'"
runsh 32 relic3-file    "relic3 search semantics_14_umap_map --all-tiers --horizon archive" "relic3 search semantics_14_umap_map --all-tiers --horizon archive --limit 3 2>&1 | head -6"
runsh 33 relic3-sem     "relic3 search \"which model answers API calls…\" --semantic …" "relic3 search 'which model answers API calls, rolling 7 day share and output tokens per month' --semantic --model embeddinggemma-mlx-fp16 --all-tiers --horizon archive --limit 3 --no-warn 2>&1 | rg -v '^\\s*\$' | head -14"
# ch5 the report pipeline
runsh 40 topics         "just topics" "just topics 2>&1 | rg '^topics|^  '"
runsh 41 work           "just work | tail -12" "just work 2>&1 | tail -12"
runsh 42 oracles        "just oracles | tail -7" "just oracles 2>&1 | tail -7"
runsh 43 memory         "RELIC4_ROOT=~/relic4-fresh just memory | head -10" "$R4 just memory 2>&1 | rg '^memory|^  ' | head -10"
runsh 44 build          "just report && just report-public" "just report 2>&1 | rg '^report' && just report-public 2>&1 | rg '^report'"
runsh 45 jsdom          "node check.js   (every view, both languages)" "node /tmp/jsdom-run/check.js 2>&1 | rg -v getContext"
# ch6 the day on gb300
runsh 50 models         "ssh gb300 curl -s localhost:11434/api/tags" "ssh -o BatchMode=yes gb300 'curl -s localhost:11434/api/tags' | python3 -c \"import json,sys;[print(m['name'], m['details'].get('parameter_size')) for m in json.load(sys.stdin)['models']]\""
runsh 51 compare        "the 4-model table (compare-models-*.json)" "python3 -c \"import json,os,glob
R=os.path.expanduser('~/.relic-extract/report/')
for f in sorted(glob.glob(R+'compare-models-*.json')):
  for m,v in json.load(open(f))['models'].items():
    s=v['score']; print(f\\\"{m:<24} json {s['json']} thai {s['thai']} names {s['names']} generic {s['generic']} secs {s['secs']}\\\")\""
runsh 52 day-reading    "one day's reading (days.json, qwen3:14b v3)" "python3 -c \"import json,os;d={x['day']:x for x in json.load(open(os.path.expanduser('~/.relic-extract/report/days.json')))['days']};x=d['2026-10-22'];print(json.dumps({'shape':x['shape'],'summary':x['summary']},ensure_ascii=False,indent=1))\""
runsh 53 readings-log   "wc -l readings.jsonl; tail -1 | cut" "wc -l ~/.relic-extract/report/readings.jsonl; tail -1 ~/.relic-extract/report/readings.jsonl | cut -c1-400"
# ch7 publish
runsh 60 publish        "just publish" "just publish 2>&1 | rg 'report:|INF|Uploaded|Deployed|relic.buildwithoracle|Version'"
runsh 61 live           "curl -sI https://relic.buildwithoracle.com/report/" "curl -sI https://relic.buildwithoracle.com/report/ | head -8"
# evidence
runsh 90 just-list      "just --list" "just --list"
runsh 91 sizes          "du -sh ~/.relic-scan ~/.relic-extract/* ~/relic4-fresh" "du -sh ~/.relic-scan ~/.relic-extract/text ~/.relic-extract/thinking ~/.relic-extract/tools ~/.relic-extract/vault ~/.relic-extract/report ~/relic4-fresh"
runsh 92 git-log        "git log --oneline -12" "git log --oneline -12"
runsh 93 errors         "python3 errors.py <this session>.jsonl" "python3 $B/errors.py $HOME/.claude/projects/-opt-Code-github-com-Soul-Brews-Studio-relic-extract/008db2b3-17a7-47f4-b118-742ebc7ae6e7.jsonl"
runsh 94 zai-keys       "python3 zai-keys.py glm/zai-2 glm/zai-3 glm/nat-wrw" "python3 $B/zai-keys.py glm/zai-2 glm/zai-3 glm/nat-wrw"

date '+== capture end %H:%M:%S'
ls $C | wc -l
