#!/bin/sh
# Social Idea Lab by Tarfandhaye.ai - start script for macOS and Linux.
# Installs uv (if missing) and a uv-managed Python 3.12, then runs the skill with it.
#   sh start.sh              opens the dashboard
#   sh start.sh <command>    runs any command (sh start.sh help)
set -e
ILAB_DIR="$(cd "$(dirname "$0")" && pwd)"
ILAB_PY=3.12
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8

# 1. uv: on PATH, or where its installer puts it
for d in "$HOME/.local/bin" "$HOME/.cargo/bin"; do
  if ! command -v uv >/dev/null 2>&1 && [ -x "$d/uv" ]; then PATH="$d:$PATH"; fi
done
if ! command -v uv >/dev/null 2>&1; then
  echo "[Social Idea Lab] uv is not installed. Installing it from astral.sh (one time)..." >&2
  if command -v curl >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh >&2
  else
    wget -qO- https://astral.sh/uv/install.sh | sh >&2
  fi
  PATH="$HOME/.local/bin:$PATH"
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "[Social Idea Lab] uv could not be installed. Check the internet, or install it from https://docs.astral.sh/uv/" >&2
  exit 1
fi
export PATH

# 2. Python, installed and managed by uv (one time, about 30 MB)
PY="$(uv python find --managed-python "$ILAB_PY" 2>/dev/null || true)"
if [ -z "$PY" ]; then
  echo "[Social Idea Lab] Installing Python $ILAB_PY with uv (one time)..." >&2
  uv python install --no-bin --compile-bytecode "$ILAB_PY" >&2
  PY="$(uv python find --managed-python "$ILAB_PY")"
fi

# 3. run the skill with uv's Python (standard library only: no packages to install)
if [ $# -eq 0 ]; then set -- dashboard --open; fi
exec "$PY" -I "$ILAB_DIR/scripts/run.py" "$@"
