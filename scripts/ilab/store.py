# Social Idea Lab by Tarfandhaye.ai — © 2026 Tarfandhaye.ai — All rights reserved. Personal use only; see LICENSE.md.
"""Workspace layout, the board (ideas, QC, pre-production, storyboards), client decisions and the events log.
Standard library only. board.json is written by the commands, decisions.json by the dashboard buttons (and `decide`)."""
import json
import os
import re
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from . import brand as _brand

BRAND_SHA256 = "193414c9b7e51815c4c795077d78a0174d824e3fe4cea2e081ce23c65ca4794e"  # set by dev/build.py
if BRAND_SHA256 and (not _brand.LICENSE_SHA256 or _brand.code_digest(Path(__file__).with_name("brand.py")) != BRAND_SHA256):
    raise SystemExit(f"⛔ {_brand.NAME}: فایل‌های اسکیل تغییر کرده‌اند، پس اسکیل اجرا نمی‌شود. نسخه‌ی اصل را از {_brand.OWNER} بگیرید.")
_brand.check()

HOME = Path(os.environ.get("ILAB_HOME") or (Path.home() / ".tarfandhaye"))
POINTER = HOME / "social-idea-lab.json"
DEFAULT_WORK = Path.home() / "Social Idea Lab"
AGENTS = ("page", "scout", "qc", "client", "prod", "system")
KINDS = ("motion", "filmed")
VERDICTS = ("fit", "partial", "unfit")
IDEA_ACTIONS = ("approve", "approve_alt", "delete", "restore")
SB_ACTIONS = ("approve", "revise", "reset")
PREPROD_GROUPS = ("people", "location", "equipment", "props", "software", "assets")

PAGE_TEMPLATE = {
    "handle": "",
    "name": "",
    "url": "",
    "followers": None,
    "niche": "",
    "audience": "",
    "language": "fa",
    "tone": "",
    "pillars": [],
    "visual": {"palette": [], "style": "", "fonts": "", "look": ""},
    "production": {"can_film": True, "on_camera": "", "location": "", "equipment": "", "motion_skills": ""},
    "dont": [],
    "keywords": [],
    "hashtags": [],
    "competitors": [],
    "client": "",
    "youtube": {"channel": "", "url": "", "subscribers": None},
    "linkedin": {"page": "", "url": "", "followers": None},
    # brand strategy: from the client's strategy document (optional; the page link alone also works)
    "strategy": {"source": "", "summary": "", "goals": [], "audience": "", "voice": "", "pillars": [], "dos": [], "donts": [],
                 "competitors": [], "keywords": [], "kpis": []},
}


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as e:
        raise SystemExit(f"⛔ فایل «{path}» خراب است (JSON نامعتبر، خط {e.lineno}). درستش کن و دوباره اجرا کن.")


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    for _ in range(40):  # Windows: the dashboard may be reading the file this very moment
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.05)
    os.replace(tmp, path)


@contextmanager
def locked(path, timeout=5.0):
    """Cross-process lock (the dashboard server and a command may write decisions at the same time)."""
    lock = Path(str(path) + ".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    while True:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > 15:
                    lock.unlink()
                    continue
            except FileNotFoundError:
                continue
            if time.time() - t0 > timeout:
                raise SystemExit("⛔ فایل تصمیم‌ها قفل مانده. چند ثانیه بعد دوباره امتحان کن.")
            time.sleep(0.05)
    try:
        yield
    finally:
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


PLATFORMS = ("instagram", "youtube", "linkedin")
PLATFORM_FA = {"instagram": "اینستاگرام", "youtube": "یوتیوب", "linkedin": "لینکدین"}
UNIT_FA = {"instagram": "ریل", "youtube": "ویدیو", "linkedin": "پست"}
MODES = ("strategy", "login")
REGIONS = ("ir", "intl", "both")
WINDOWS = (180, 365, 730)   # how far back a benchmark looks, in days; 180 (6 months) unless the user asks for more
WINDOW_FA = {180: "۶ ماه اخیر", 365: "یک سال اخیر", 730: "دو سال اخیر"}
REGION_FA = {"ir": "پیج‌های ایرانی", "intl": "پیج‌های خارجی", "both": "ایرانی و خارجی"}
MODE_FA = {"strategy": "بررسی با سند استراتژی (بدون لاگین)", "login": "بررسی با لاگین (حساب خودت، فقط خواندن)"}
BRIEF_EXT = {".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".jpg", ".jpeg", ".png", ".webp", ".zip", ".pptx", ".ppt"}


class Workspace:
    """One brand. The brand profile and strategy are shared; each platform (Instagram / YouTube) has its own
    ideas, QC, client decisions, pre-production and storyboards. Instagram keeps the original paths."""

    def __init__(self, root, platform=None):
        self.root = Path(root).expanduser().resolve()
        self.hidden = self.root / ".lab"
        self.config_path = self.hidden / "config.json"
        self.events_path = self.hidden / "events.jsonl"
        self.last_path = self.hidden / "last.txt"
        self.page_path = self.root / "page.json"
        self.brand_dir = self.root / "brand"
        self.inbox_path = self.hidden / "inbox.json"
        self._platform = platform if platform in PLATFORMS else None

    @property
    def platform(self):
        p = self._platform or self.config.get("platform") or "instagram"
        return p if p in PLATFORMS else "instagram"

    def for_platform(self, p):
        return Workspace(self.root, p)

    @property
    def mode(self):
        m = self.config.get("mode") or "strategy"
        return m if m in MODES else "strategy"

    # ---- brand brief sent from the dashboard (links, sample posts, text, documents) ----
    @property
    def brief_path(self):
        return self.brand_dir / "brief.json"

    def brief(self):
        return read_json(self.brief_path, None) or {}

    def save_brief(self, page_link="", samples=None, text="", files=None, by="dashboard"):
        b = self.brief()
        b["page_link"] = page_link or b.get("page_link", "")
        b["samples"] = list(dict.fromkeys((b.get("samples") or []) + [s for s in (samples or []) if s]))[:40]
        if text:
            b["text"] = text
        saved = b.get("files") or []
        self.brand_dir.mkdir(parents=True, exist_ok=True)
        for name, data in files or []:
            safe = clean_name(Path(name).stem, 60) + Path(name).suffix.lower()
            dst = self.brand_dir / safe
            n = 2
            while dst.exists():
                dst = self.brand_dir / f"{clean_name(Path(name).stem, 56)} ({n}){Path(name).suffix.lower()}"
                n += 1
            dst.write_bytes(data)
            saved.append({"name": name, "path": str(dst), "size": len(data), "at": now_iso()})
        b["files"] = saved
        b["at"] = now_iso()
        b["by"] = by
        b["read"] = False
        write_json(self.brief_path, b)
        return b

    @property
    def _pdir(self):
        return self.root if self.platform == "instagram" else self.root / self.platform

    @property
    def board_path(self):
        return self._pdir / "board.json"

    @property
    def scans_dir(self):
        return self._pdir / "scans"

    @property
    def ideas_dir(self):
        return self._pdir / "ideas"

    @property
    def decisions_path(self):
        return self.hidden / ("decisions.json" if self.platform == "instagram" else f"decisions-{self.platform}.json")

    def exists(self):
        return self.hidden.is_dir()

    def ensure(self):
        for d in (self.hidden, self.scans_dir, self.ideas_dir, self.brand_dir):
            d.mkdir(parents=True, exist_ok=True)
        if not self.page_path.exists():
            write_json(self.page_path, PAGE_TEMPLATE)

    @property
    def config(self):
        return read_json(self.config_path, {}) or {}

    def save_config(self, **kv):
        c = self.config
        c.update(kv)
        write_json(self.config_path, c)

    @property
    def page(self):
        return read_json(self.page_path, {}) or {}

    # ---- board ----
    def board(self):
        b = read_json(self.board_path, None) or {}
        b.setdefault("ideas", [])
        b.setdefault("scan", {})
        return b

    def save_board(self, b):
        b["updated"] = now_iso()
        write_json(self.board_path, b)

    # ---- client decisions ----
    def decisions(self):
        d = read_json(self.decisions_path, None) or {}
        d.setdefault("ideas", {})
        d.setdefault("storyboards", {})
        return d

    def decide(self, idea_id, action, by="client", note=None):
        with locked(self.decisions_path):
            d = self.decisions()
            if action == "restore":
                d["ideas"].pop(idea_id, None)
            else:
                status = {"approve": "approved", "approve_alt": "approved_alt", "delete": "deleted"}[action]
                d["ideas"][idea_id] = {"status": status, "at": now_iso(), "by": by, **({"note": note} if note else {})}
            write_json(self.decisions_path, d)
        return d

    def decide_storyboard(self, idea_id, action, by="client", note=None):
        with locked(self.decisions_path):
            d = self.decisions()
            if action == "reset":
                d["storyboards"].pop(idea_id, None)
            else:
                status = {"approve": "approved", "revise": "revise"}[action]
                d["storyboards"][idea_id] = {"status": status, "at": now_iso(), "by": by, **({"note": note} if note else {})}
            write_json(self.decisions_path, d)
        return d

    def clear_storyboard_decision(self, idea_id):
        if idea_id in self.decisions()["storyboards"]:
            self.decide_storyboard(idea_id, "reset", by="system")

    # ---- reel links sent from the dashboard ("add a reel") ----
    def inbox(self):
        return read_json(self.inbox_path, None) or []

    def add_inbox(self, url, note=None, by="dashboard"):
        with locked(self.inbox_path):
            items = self.inbox()
            if any(canonical_reel(i.get("url")) == canonical_reel(url) for i in items):
                return None
            item = {"id": f"r{len(items) + 1:02d}", "url": url, "note": note or "", "by": by, "at": now_iso(), "status": "new"}
            items.append(item)
            write_json(self.inbox_path, items)
        return item

    def mark_inbox(self, urls, status="done"):
        keys = {canonical_reel(u) for u in urls if u}
        with locked(self.inbox_path):
            items = self.inbox()
            n = 0
            for i in items:
                if i.get("status") == "new" and canonical_reel(i.get("url")) in keys:
                    i["status"] = status
                    n += 1
            if n:
                write_json(self.inbox_path, items)
        return n

    # ---- "new benchmark" requests from the dashboard button (Claude runs them) ----
    @property
    def requests_path(self):
        return self.hidden / "requests.json"

    @staticmethod
    def _bench_map(r):
        """{platform: request}; an older single request (key "benchmark") belongs to its own platform"""
        m = dict(r.get("benchmarks") or {})
        old = r.get("benchmark")
        if old and (old.get("platform") or "instagram") not in m:
            m[old.get("platform") or "instagram"] = old
        return m

    def benchmark_request(self):
        """this platform's request (queued / running / done / cancelled)"""
        return self._bench_map(read_json(self.requests_path, None) or {}).get(self.platform) or {}

    def benchmarks(self):
        return {p: self.for_platform(p).benchmark_request() for p in PLATFORMS}

    def set_benchmark(self, status, **extra):
        with locked(self.requests_path):
            r = read_json(self.requests_path, None) or {}
            m = self._bench_map(r)
            r.pop("benchmark", None)
            b = m.get(self.platform) or {}
            extra["platform"] = self.platform
            b.update({"status": status, f"{status}_at": now_iso()}, **{k: v for k, v in extra.items() if v is not None})
            if status == "queued":
                for k in ("running_at", "done_at"):
                    b.pop(k, None)
            m[self.platform] = b
            r["benchmarks"] = m
            write_json(self.requests_path, r)
        return b

    def summary(self):
        """small counters for the platform switch"""
        b, d = self.board(), self.decisions()
        return {"ideas": len(b["ideas"]), "approved": sum(1 for v in d["ideas"].values() if v.get("status") in ("approved", "approved_alt"))}

    def rev(self):
        parts = [self.platform]
        others = [self.for_platform(p) for p in PLATFORMS if p != self.platform]
        parts.append(self.mode)
        for p in (self.page_path, self.board_path, self.decisions_path, self.inbox_path, self.brief_path, self.requests_path,
                  *[o.board_path for o in others], *[o.decisions_path for o in others]):
            try:
                parts.append(str(p.stat().st_mtime_ns))
            except FileNotFoundError:
                parts.append("0")
        return "-".join(parts)


REEL_RE = re.compile(r"^https://(www\.|m\.)?(instagram\.com/(reels?|p|tv)/[\w-]+|instagram\.com/[\w.]+/(reels?|p)/[\w-]+|"
                     r"(www\.|m\.)?youtube\.com/(shorts/[\w-]+|watch\?v=[\w-]+)|youtu\.be/[\w-]+|(www\.|vm\.|vt\.)?tiktok\.com/[\w@./-]+|"
                     r"([a-z]{2,3}\.)?linkedin\.com/(posts/[\w%.~-]+|feed/update/urn:li:(activity|share|ugcPost):\d+/?)|lnkd\.in/[\w-]+)", re.I)
LINKEDIN_ID = re.compile(r"(?:activity[-:]|urn:li:(?:share|ugcPost):)(\d{12,})", re.I)


def canonical_reel(url):
    """https://www.instagram.com/reel/ABC/?igsh=… → instagram:ABC (so a link with tracking parameters matches the scanned one)"""
    u = str(url or "").strip()
    m = re.search(r"instagram\.com/(?:[\w.]+/)?(?:reels?|p|tv)/([\w-]+)", u)
    if m:
        return "instagram:" + m.group(1)
    m = re.search(r"(?:youtube\.com/shorts/|youtu\.be/|youtube\.com/watch\?v=)([\w-]+)", u)
    if m:
        return "youtube:" + m.group(1)
    if "linkedin.com" in u.lower():
        m = LINKEDIN_ID.search(u)
        if m:
            return "linkedin:" + m.group(1)
    return u.split("?")[0].rstrip("/").lower()


# ---------- several brands in one work folder ----------
# WORK/.lab/brands.json lists them; the first brand of an older single-brand folder is WORK itself (path "."),
# every new brand lives in WORK/brands/bNN/ with its own page, ideas, decisions, platform, mode and requests.

def _brands_file(lab):
    return lab.hidden / "brands.json"


def list_brands(lab):
    items = read_json(_brands_file(lab), None) or []
    if items:
        return items
    p = lab.page
    if p.get("name") or p.get("handle") or lab.board_path.exists() or lab.for_platform("youtube").board_path.exists():
        return [{"id": "main", "name": p.get("name") or p.get("handle") or "برند اصلی", "path": "."}]
    return []


def find_brand(lab, key):
    items = list_brands(lab)
    k = str(key or "").strip().lower().lstrip("@")
    for it in items:
        if it["id"].lower() == k:
            return it
    hits = [it for it in items if k and k in str(it.get("name", "")).lower()]
    if len(hits) == 1:
        return hits[0]
    names = "، ".join(f"{it['id']} ({it['name']})" for it in items) or "هنوز برندی نیست"
    raise SystemExit(f"⛔ برند «{key}» پیدا نشد یا چندتا جور درآمد. یکی از این‌ها: {names}")


def brand_ws(lab, key=None, platform=None):
    """(workspace of the chosen or active brand, its registry entry). No brands yet → the work folder itself."""
    items = list_brands(lab)
    if not items:
        return Workspace(lab.root, platform), None
    it = find_brand(lab, key) if key else next((b for b in items if b["id"] == lab.config.get("brand")),
                                               next((b for b in items if not b.get("hidden")), items[0]))
    return Workspace((lab.root / it["path"]).resolve(), platform), it


def add_brand(lab, name, bid=None, **profile):
    """bid: keep the id a brand already has elsewhere (a brand registered on the online dashboard is "w-…"),
    so everything the client does there for it keeps pointing at it"""
    name = str(name or "").strip()
    if not name:
        raise SystemExit("⛔ اسم برند لازم است.")
    with locked(_brands_file(lab)):
        items = list_brands(lab)
        if any(b["name"].strip() == name for b in items):
            raise SystemExit(f"⛔ برندی به اسم «{name}» از قبل هست.")
        nums = [int(b["id"][1:]) for b in items if re.fullmatch(r"b\d+", b["id"])]
        arch = lab.hidden / "archive" / "brands"  # never reuse the id of a removed (archived) brand
        nums += [int(m.group(1)) for p in (arch.iterdir() if arch.is_dir() else []) for m in [re.match(r"b(\d+)-", p.name)] if m]
        if not (bid and re.fullmatch(r"w-[a-z0-9]{1,16}", str(bid)) and not any(b["id"] == bid for b in items)):
            bid = f"b{max(nums, default=1 if items else 0) + 1:02d}"
        it = {"id": bid, "name": name, "path": f"brands/{bid}", "created": now_iso()}
        items.append(it)
        write_json(_brands_file(lab), items)
    ws = Workspace(lab.root / it["path"])
    ws.ensure()
    page = json.loads(json.dumps(PAGE_TEMPLATE))
    page["name"] = name
    for k, v in profile.items():
        if v:
            if k in ("youtube", "linkedin"):
                page[k]["url"] = v
            else:
                page[k] = v
    if page.get("handle") and not str(page["handle"]).startswith("@"):
        page["handle"] = "@" + page["handle"]
    write_json(ws.page_path, page)
    ws.save_config(created=now_iso(), demo=bool(lab.config.get("demo")))
    return ws, it


def use_brand(lab, key):
    """select a brand; selecting a hidden one (the main brand after «حذف») brings it back to the list"""
    it = find_brand(lab, key)
    with locked(_brands_file(lab)):
        items = list_brands(lab)
        if it.get("hidden"):
            items = [{k: v for k, v in b.items() if k not in ("hidden", "hidden_at")} if b["id"] == it["id"] else b for b in items]
            it = next(b for b in items if b["id"] == it["id"])
            write_json(_brands_file(lab), items)
        elif not read_json(_brands_file(lab), None):  # write the implicit first brand down before switching
            write_json(_brands_file(lab), items)
    lab.save_config(brand=it["id"])
    return it


def visible_brands(lab):
    return [b for b in list_brands(lab) if not b.get("hidden")]


def remove_brand(lab, key):
    """Take a brand off the list. Nothing is ever deleted:
    - an added brand (brands/bNN): its folder moves to WORK/.lab/archive/brands/<id>-<time>/
      (to bring it back: move the folder back to WORK/brands/<id> and add its line to .lab/brands.json);
    - the main brand is the work folder itself, so its data stays where it is and it is only hidden
      (to bring it back: `brand use main`).
    The last visible brand cannot be removed. Returns (entry, archive folder or None, new active id)."""
    dst = None
    with locked(_brands_file(lab)):
        items = list_brands(lab)
        it = find_brand(lab, key)
        if it.get("hidden"):
            raise SystemExit(f"⛔ برند «{it['name']}» از قبل از فهرست برداشته شده.")
        if not any(b["id"] != it["id"] and not b.get("hidden") for b in items):
            raise SystemExit("⛔ این آخرین برند فهرسته و حذف نمی‌شه؛ اول یه برند دیگه اضافه کن.")
        is_main = it["id"] == "main" or str(it.get("path") or ".").strip() in (".", "", "./")
        src = (lab.root / it["path"]).resolve()
        if not is_main and src.parent != (lab.root / "brands").resolve():
            raise SystemExit(f"⛔ مسیر برند «{it['name']}» عجیبه ({it['path']}); دست نزدم.")
        for pl in PLATFORMS:   # every platform's open request goes with the brand
            ws = Workspace(src, pl)
            if src.exists() and ws.benchmark_request().get("status") in ("queued", "running"):
                ws.set_benchmark("cancelled", by="remove")
        if is_main:
            rest = [dict(b, hidden=True, hidden_at=now_iso()) if b["id"] == it["id"] else b for b in items]
        else:
            if src.exists():
                dst = lab.hidden / "archive" / "brands" / f"{it['id']}-{datetime.now():%Y%m%d-%H%M%S}"
                dst.parent.mkdir(parents=True, exist_ok=True)
                try:
                    os.replace(src, dst)
                except OSError as e:
                    raise SystemExit(f"⛔ پوشه‌ی برند جابه‌جا نشد (شاید فایلی از آن باز است): {e}")
            rest = [b for b in items if b["id"] != it["id"]]
        write_json(_brands_file(lab), rest)
    shown = [b for b in rest if not b.get("hidden")]
    active = lab.config.get("brand")
    if not any(b["id"] == active for b in shown):
        active = shown[0]["id"] if shown else None
        lab.save_config(brand=active)
    return it, dst, active


def handle_from_url(url):
    m = re.search(r"instagram\.com/([\w.]+)", str(url or ""))
    return "@" + m.group(1) if m and m.group(1) not in ("p", "reel", "reels", "explore") else ""


def resolve(work=None, platform=None):
    if work:
        return Workspace(work, platform)
    env = os.environ.get("ILAB_WORK")
    if env:
        return Workspace(env, platform)
    p = read_json(POINTER, {}) or {}
    if p.get("work"):
        return Workspace(p["work"], platform)
    return Workspace(DEFAULT_WORK, platform)


def remember(ws):
    write_json(POINTER, {"work": str(ws.root)})


# ---------- ideas ----------

def find_idea(board, key):
    ideas = board.get("ideas", [])
    if not ideas:
        raise SystemExit("⛔ هنوز هیچ ایده‌ای ثبت نشده. اول `scout --import` را اجرا کن.")
    k = str(key).strip().lower()
    if re.fullmatch(r"\d+", k):  # a rank number: 1..20
        for it in ideas:
            if str(it.get("rank")) == k:
                return it
        k = f"i{int(k):02d}"
    for it in ideas:
        if it.get("id", "").lower() == k:
            return it
    ids = "، ".join(f"{it['id']} (#{it.get('rank')})" for it in ideas[:8])
    raise SystemExit(f"⛔ ایده‌ی «{key}» پیدا نشد. شناسه یا رتبه را بده، مثلاً: {ids}")


def clean_name(title, n=40):
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f#%]', " ", title or "").strip()
    s = re.sub(r"\s+", " ", s)[:n].strip(" .")
    return s or "idea"


def idea_dir(ws, idea):
    d = ws.ideas_dir / f"{idea['id']} - {clean_name(production_title(idea))}"
    for old in ws.ideas_dir.glob(f"{idea['id']} - *"):
        if old.is_dir() and old != d and not d.exists():
            try:
                old.rename(d)
            except OSError:
                return old
    d.mkdir(parents=True, exist_ok=True)
    return d


def production_title(idea, decision=None):
    if decision and decision.get("status") == "approved_alt" and (idea.get("qc") or {}).get("alternative"):
        return idea["qc"]["alternative"].get("title") or idea.get("title", "")
    return idea.get("title", "")


def production_kind(idea, decision=None):
    """motion / filmed of what will actually be made (the alternative's kind when the client chose it)"""
    if (idea.get("preprod") or {}).get("kind") in KINDS:
        return idea["preprod"]["kind"]
    alt = (idea.get("qc") or {}).get("alternative") or {}
    if decision and decision.get("status") == "approved_alt" and alt.get("kind") in KINDS:
        return alt["kind"]
    return idea.get("kind")


def stage_of(idea, decisions):
    """candidate → qc → approved → preprod → storyboard → production → done (or deleted)."""
    dec = decisions["ideas"].get(idea["id"], {})
    sb = decisions["storyboards"].get(idea["id"], {})
    if dec.get("status") == "deleted":
        return "deleted"
    if idea.get("done"):
        return "done"
    if dec.get("status") in ("approved", "approved_alt"):
        if idea.get("storyboard") and sb.get("status") == "approved":
            return "production"
        if idea.get("storyboard"):
            return "storyboard"
        if idea.get("preprod"):
            return "preprod"
        return "approved"
    if idea.get("qc"):
        return "qc"
    return "candidate"


# ---------- events (live log on the dashboard) ----------

def now_iso_z():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def add_event(ws, agent, type_, msg="", data=None, demo=False):
    ev = {"t": round(time.time(), 3), "agent": agent, "type": type_, "msg": msg,
          "data": {k: v for k, v in (data or {}).items() if v is not None}}
    if demo:
        ev["demo"] = True
    ws.hidden.mkdir(parents=True, exist_ok=True)
    with open(ws.events_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


def read_events(ws, since=0, limit=2000):
    """Complete lines only, so a line being written right now is picked up on the next poll instead of being lost."""
    try:
        text = ws.events_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [], 0
    lines = text.split("\n")
    lines.pop()
    since = max(0, min(since, len(lines)))
    out = []
    end = min(len(lines), since + limit)
    for i in range(since, end):
        try:
            ev = json.loads(lines[i])
        except ValueError:
            continue
        ev["i"] = i
        out.append(ev)
    return out, end


def archive(ws):
    """Move the board, decisions and events aside (nothing is deleted)."""
    stamp = f"{datetime.now():%y%m%d-%H%M%S}"
    moved = []
    for p in (ws.board_path, ws.decisions_path, ws.events_path):
        if p.exists() and p.stat().st_size:
            dst = ws.hidden / "archive" / stamp / p.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            os.replace(p, dst)
            moved.append(dst)
    return (ws.hidden / "archive" / stamp) if moved else None
