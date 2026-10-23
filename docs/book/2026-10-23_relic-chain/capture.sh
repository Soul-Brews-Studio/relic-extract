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
TOOL=mytool                              # the name printed after "$ " in every capture
TOOLCMD=(mytool)                         # how to actually run it, e.g. (bun /path/src/cli.ts)
WORKDIR=$PWD                             # where commands run (matters for --cwd style flags)
TIMEOUT=180

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
$TOOLCMD --help > $C/00-help.txt 2>&1      # the help text: reviewers check every flag against it

# ── COMMANDS (one line per thing the book shows; group by chapter) ──────────
# ch1
# run 01 status          -- status
# ch2
# run 02 search-literal  -- search SomeUniqueString --limit 5
# a server: start, probe, stop — all inside one runsh
# runsh 03 serve "mytool serve --port 4399   (+ curl)" "$TOOLCMD serve --port 4399 & SP=\$!; sleep 1; curl -s 127.0.0.1:4399/health; kill \$SP"
# evidence for prose claims
# runsh 90 source-x "cat x.py" "cat /abs/path/x.py"
# runsh 91 disk      "du -sh ~/data" "du -sh ~/data"

date '+== capture end %H:%M:%S'
ls $C | wc -l
