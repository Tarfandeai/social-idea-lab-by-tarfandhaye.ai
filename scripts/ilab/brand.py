# Social Idea Lab by Tarfandhaye.ai — © 2026 Tarfandhaye.ai — All rights reserved. Personal use only; see LICENSE.md.
"""Brand, license notice and the integrity check every command runs first (standard library only)."""
import hashlib
import re
import sys
from pathlib import Path

NAME = "Social Idea Lab by Tarfandhaye.ai"
OWNER = "Tarfandhaye.ai"
VERSION = "2.0.5"
HEADER = "Social Idea Lab by Tarfandhaye.ai — © 2026 Tarfandhaye.ai — All rights reserved. Personal use only; see LICENSE.md."
NOTICE_FA = "© ۱۴۰۵ Tarfandhaye.ai — همه‌ی حقوق محفوظ است. فقط برای استفاده‌ی شخصی."
COPY = "© tarfandhaye.ai"  # the page's copyright, shown everywhere on the dashboard and in every document
LICENSE_SHA256 = "cbbbbdefb1b1fdf62f61a7283a7fd08b2f9aff41a44261017eafb21b6d7a9319"  # set by dev/build.py when the release zip is built; empty = development copy
LOGO_SHA256 = "0492e4515772337d1d4a096216b4852b6b0ee25e4d0726c9e8022c7221dcb21c"  # set by dev/build.py
FILES_SHA256 = "977d4e4d03cff024755cebd54c3488c732edc8874bed07733ccdbc6317a21b38"  # set by dev/build.py: every shipped file of the skill

SKILL_ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    """sha256 of a text file with line endings normalized, so a checkout on any OS gives the same value"""
    text = Path(path).read_text(encoding="utf-8").replace("\r\n", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


STAMP = re.compile(r'^[A-Z_]+_SHA256 = "[0-9a-f]*".*$', re.M)
SHIPPED = (".md", ".py", ".html", ".cmd", ".sh", ".png", ".json", ".txt")
BINARY = (".png",)


def code_digest(path):
    """sha256 of one file; text with line endings normalized and the stamp lines left out (so stamping is stable)"""
    p = Path(path)
    if p.suffix.lower() in BINARY:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    text = p.read_text(encoding="utf-8").replace("\r\n", "\n")
    return hashlib.sha256(STAMP.sub("", text).encode("utf-8")).hexdigest()


def shipped_files():
    return sorted(f for f in SKILL_ROOT.rglob("*") if f.is_file() and f.suffix.lower() in SHIPPED
                  and not any(part.startswith(".") or part == "__pycache__" for part in f.relative_to(SKILL_ROOT).parts))


def files_digest():
    h = hashlib.sha256()
    for f in shipped_files():
        h.update(f"{f.relative_to(SKILL_ROOT).as_posix()}\0{code_digest(f)}\n".encode("utf-8"))
    return h.hexdigest()


def problems():
    guard = SKILL_ROOT / "scripts" / "ilab" / "store.py"
    stamped_guard = bool(re.search(r'^BRAND_SHA256 = "[0-9a-f]{64}"', guard.read_text(encoding="utf-8"), re.M)) if guard.exists() else False
    if not LICENSE_SHA256:
        return ["scripts/ilab/brand.py"] if stamped_guard else []
    found = []
    if not stamped_guard:
        found.append("scripts/ilab/store.py")
    if not FILES_SHA256 or files_digest() != FILES_SHA256:
        found.append("files")
    lic = SKILL_ROOT / "LICENSE.md"
    if not lic.exists() or digest(lic) != LICENSE_SHA256:
        found.append("LICENSE.md")
    logo = SKILL_ROOT / "assets" / "logo.png"
    if LOGO_SHA256 and (not logo.exists() or hashlib.sha256(logo.read_bytes()).hexdigest() != LOGO_SHA256):
        found.append("assets/logo.png")
    skill = SKILL_ROOT / "SKILL.md"
    text = skill.read_text(encoding="utf-8") if skill.exists() else ""
    if NAME not in text or HEADER not in text:
        found.append("SKILL.md")
    for f in sorted((SKILL_ROOT / "scripts").rglob("*.py")):
        if HEADER not in f.read_text(encoding="utf-8")[:400]:
            found.append(str(f.relative_to(SKILL_ROOT)))
    page = SKILL_ROOT / "scripts" / "ilab" / "dashboard.html"
    body = page.read_text(encoding="utf-8") if page.exists() else ""
    if HEADER not in body or NOTICE_FA not in body or body.count(COPY) < 6:
        found.append("scripts/ilab/dashboard.html")
    return found


def check():
    bad = problems()
    if bad:
        print(f"⛔ {NAME}: فایل‌های اسکیل یا مجوز آن تغییر کرده‌اند، پس اسکیل اجرا نمی‌شود.\n"
              f"   نسخه‌ی اصل را دوباره از {OWNER} بگیرید.\n"
              f"   The skill's files or license were modified, so it will not run: {', '.join(bad)}", flush=True)
        sys.exit(3)


def banner():
    return f"✦ {NAME}  v{VERSION}  —  {NOTICE_FA}"
