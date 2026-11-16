# Social Idea Lab by Tarfandhaye.ai — © 2026 Tarfandhaye.ai — All rights reserved. Personal use only; see LICENSE.md.
"""Entry point for every command: checks the license, then runs the command. Standard library only, nothing to install.
Usage: python run.py <command> [args]   (python run.py help)"""
import sys
from pathlib import Path

for stream in (sys.stdout, sys.stderr):  # Persian output through a pipe on Windows (cp1252) must not crash
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
if sys.version_info < (3, 9):
    sys.exit("⛔ این اسکیل پایتون ۳٫۹ یا جدیدتر می‌خواهد. از python.org نصبش کن.")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ilab import brand, cli  # noqa: E402

if __name__ == "__main__":
    brand.check()
    sys.exit(cli.main(sys.argv[1:]))
