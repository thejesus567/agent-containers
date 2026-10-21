#!/usr/bin/env bash
set -euo pipefail
umask 077

history_dir=/home/node/codex-history
mkdir -p "$CODEX_HOME" "$history_dir/sessions" "$history_dir/archived_sessions" "$history_dir/sqlite"

# Persist an explicit set of conversation files, never the whole credential directory.
for directory in sessions archived_sessions; do
  ln -s "$history_dir/$directory" "$CODEX_HOME/$directory"
done
for file in history.jsonl session_index.jsonl; do
  touch "$history_dir/$file"
  ln -s "$history_dir/$file" "$CODEX_HOME/$file"
done

# This configuration and any auth.json created by other CLI invocations stay in tmpfs.
cat > "$CODEX_HOME/config.toml" <<'CONFIG'
cli_auth_credentials_store = "ephemeral"
sqlite_home = "/home/node/codex-history/sqlite"

[history]
persistence = "save-all"
CONFIG

exec codex "$@"
