#!/usr/bin/env bash
# Start (or rejoin) the tmux session for the agent team.
# The lead Claude runs in the first pane; each teammate the lead spawns gets
# its own split pane (teammateMode "tmux" in .claude/settings.json).
#
#   scripts/team-tmux.sh            # session "bulk-team"
#   scripts/team-tmux.sh my-session # custom name
set -euo pipefail

SESSION="${1:-bulk-team}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux not found. Install it with: brew install tmux" >&2
  exit 1
fi

configure() {
  # Session-scoped so the user's own tmux setup is untouched.
  tmux set-option -t "$1" mouse on                 # click a pane to focus it, scroll its history
  tmux set-option -t "$1" history-limit 20000
  tmux set-option -w -t "$1" pane-border-status top
  tmux set-option -w -t "$1" pane-border-format ' #{pane_index}: #{pane_title} '
  tmux set-option -w -t "$1" main-pane-width 50%
}

if [ -n "${TMUX:-}" ]; then
  # Already inside tmux: configure this session and run the lead in this pane.
  current="$(tmux display-message -p '#S')"
  configure "$current"
  tmux select-pane -T lead
  cd "$ROOT"
  exec claude
fi

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux new-session -d -s "$SESSION" -c "$ROOT" -n team
  configure "$SESSION"
  tmux select-pane -t "$SESSION" -T lead
  tmux send-keys -t "$SESSION" 'claude' Enter
fi
exec tmux attach -t "$SESSION"
