# Social Idea Lab by Tarfandhaye.ai — © 2026 Tarfandhaye.ai — All rights reserved. Personal use only; see LICENSE.md.
"""The dashboard as ONE self-contained HTML file (standard library only).

It needs no server, no Python and no Claude to be open: put the file on any web host, open it from a folder, or show it as an
Artifact in claude.ai. Every brand and every platform is inside it. Approve / delete / platform switch / new-benchmark request
work inside the page and are kept in the viewer's browser; the "پیام برای Claude" button copies them as one pack that
`import-pack` applies to the real work folder."""
import base64
import json
import mimetypes
import re
import urllib.parse
from pathlib import Path

from . import server, store

HTML = Path(__file__).with_name("dashboard.html")
MARK = "/*ILAB_STATIC*/null"
MAX_IMG = 250 * 1024
DATA_IMG = re.compile(r"^data:image/(png|jpeg|webp|svg\+xml);base64,")


def _inline(obj, root):
    """/ws/… image paths point at the local server; in the file they become data: URIs (or nothing when too big)"""
    if isinstance(obj, dict):
        return {k: _inline(v, root) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_inline(v, root) for v in obj]
    if isinstance(obj, str) and obj.startswith("/ws/"):
        p = (root / urllib.parse.unquote(obj[4:])).resolve()
        if root in p.parents and p.suffix.lower() in server.IMAGE_TYPES and p.is_file() and p.stat().st_size <= MAX_IMG \
                and (root / ".lab") not in p.parents:
            ctype = "image/svg+xml" if p.suffix.lower() == ".svg" else (mimetypes.guess_type(str(p))[0] or "image/png")
            return f"data:{ctype};base64," + base64.b64encode(p.read_bytes()).decode("ascii")
        return ""
    return obj


def build_data(lab, demo=False):
    """everything the page needs, for every visible brand and every platform"""
    brands = store.visible_brands(lab) or [None]
    active_info = store.brand_ws(lab)[1]
    active = (active_info or brands[0] or {}).get("id") or ""
    data = {"v": 1, "id": store.now_iso().replace(":", "").replace("-", ""), "exported": store.now_iso(), "demo": bool(demo),
            "order": [(b or {}).get("id") or "" for b in brands], "active": {"brand": active, "platform": lab.platform},
            "states": {}, "events": {}, "applied": {} if demo else dict(lab.config.get("online_applied") or {})}
    for b in brands:
        bid = (b or {}).get("id") or ""
        bws = store.Workspace((lab.root / b["path"]).resolve()) if b else store.Workspace(lab.root)
        data["states"][bid] = {}
        for p in store.PLATFORMS:
            st = server.state(bws.for_platform(p), None, lab, b)
            st["board"]["ideas"] = _inline(st["board"].get("ideas") or [], bws.root)
            st.pop("rev", None)
            data["states"][bid][p] = st
        events, _ = store.read_events(bws, 0, 400)
        data["events"][bid] = events[-60:]
    return data


def to_html(data):
    page = HTML.read_text(encoding="utf-8")
    if MARK not in page:
        raise SystemExit("⛔ داشبورد جای داده‌ی نسخه‌ی آنلاین را ندارد (dashboard.html خراب است).")
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return page.replace(MARK, blob, 1)


def write(lab, out, demo=False):
    out = Path(out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_html(build_data(lab, demo)), encoding="utf-8", newline="\n")
    return out


# ---------- applying what the client did on the online dashboard ----------

def _samples(v):
    lines = v if isinstance(v, list) else str(v or "").splitlines()
    return [str(s).strip()[:300] for s in lines if str(s).strip().startswith("http")][:30]


def apply_pack(lab, pack, say=print, ledger=None):
    """pack = {"v":1,"items":[{"t": decide|storyboard|inbox|benchmark|mode|brief|brand_add|brand_remove, "brand","platform",…}]}.
    The items come from the online dashboard (its shared "actions" collection, or the copied pack). Same rules as the
    dashboard server: nothing is deleted, approvals are the client's own. Returns (applied, files): applied = the items
    taken in (with their `_key`/`_version` when they came from the shared store), files = brand documents uploaded on
    the online dashboard that Claude still has to fetch ({brand, name, asset}).
    ledger = {item key: its time} of items already taken in: an item is applied once, and again only when the client
    changed it later (a newer time). The ledger is embedded in the next export, so the page stops showing them as pending."""
    applied, files = [], []
    ledger = {} if ledger is None else ledger
    for it in (pack.get("items") or []):
        if not isinstance(it, dict) or it.get("applied"):
            continue
        key, when = it.get("_key"), str(it.get("at") or "")
        if key and key in ledger and ledger[key] >= when:
            continue
        if key:
            ledger[key] = when
        t = it.get("t")
        if t == "brand_add":
            name = str(it.get("name") or "").strip()[:80]
            link = str(it.get("page_link") or "").strip()[:300]
            try:
                nws, info = store.add_brand(lab, name, bid=it.get("wid") or None, url=link if "instagram.com" in link else "", handle=store.handle_from_url(link),
                                            youtube=str(it.get("youtube") or "") or (link if "youtube.com" in link or "youtu.be" in link else ""),
                                            linkedin=str(it.get("linkedin") or "") or (link if "linkedin.com" in link else ""),
                                            niche=str(it.get("niche") or "")[:200])
            except SystemExit as e:
                say(f"⚠ برند «{name}» اضافه نشد: {e.code}")
                applied.append(it)   # a duplicate name stays handled: the request is answered
                continue
            if link or it.get("text"):
                nws.save_brief(link, [], str(it.get("text") or "")[:20000], [], by="online")
            if it.get("benchmark"):
                nws.set_benchmark("queued", mode=nws.mode, region="both", by="online")
            store.add_event(nws, "client", "brand", f"برند تازه از داشبورد آنلاین: {name}", {"brand": info["id"]})
            say(f"✓ برند تازه: {name} ({info['id']})" + (" — بنچ‌مارک در صف" if it.get("benchmark") else ""))
            applied.append(it)
            continue
        if t == "brand_remove":
            try:
                rem, dst, _ = store.remove_brand(lab, str(it.get("brand") or ""))
                say(f"✓ برند «{rem['name']}» از فهرست برداشته شد ({'بایگانی شد' if dst else 'فقط پنهان شد'})")
            except SystemExit as e:
                say(f"⚠ برند برداشته نشد: {e.code}")
            applied.append(it)
            continue
        bid = str(it.get("brand") or "") or None
        plat = it.get("platform") if it.get("platform") in store.PLATFORMS else None
        try:
            ws, info = store.brand_ws(lab, bid, plat)
        except SystemExit as e:
            say(f"⚠ برند «{bid}» پیدا نشد؛ رد شد ({e.code})")
            continue
        label = (info or {}).get("name") or "برند"
        idea = next((i for i in ws.board()["ideas"] if i.get("id") == it.get("id")), None)
        if t == "decide" and it.get("action") in store.IDEA_ACTIONS and idea and (it["action"] != "approve_alt" or (idea.get("qc") or {}).get("alternative")):
            ws.decide(it["id"], it["action"], by="online", note=it.get("note"))
            if it["action"] in ("delete", "restore"):
                ws.clear_storyboard_decision(it["id"])
        elif t == "storyboard" and it.get("action") in store.SB_ACTIONS and idea:
            ws.decide_storyboard(it["id"], it["action"], by="online", note=it.get("note"))
        elif t == "inbox" and store.REEL_RE.match(str(it.get("url") or "")):
            ws.add_inbox(str(it["url"]), str(it.get("note") or "")[:500] or None, by="online")
        elif t == "benchmark" and it.get("cancel"):
            if ws.benchmark_request().get("status") == "queued":
                ws.set_benchmark("cancelled", by="online")
        elif t == "benchmark":
            if ws.benchmark_request().get("status") not in ("queued", "running"):
                ws.set_benchmark("queued", mode=it.get("mode") if it.get("mode") in store.MODES else ws.mode,
                                 region=it.get("region") if it.get("region") in store.REGIONS else "both",
                                 max_age=it.get("max_age") if it.get("max_age") in store.WINDOWS else 180, by="online")
        elif t == "mode" and it.get("mode") in store.MODES:
            ws.save_config(mode=it["mode"])
        elif t == "brief" and any(it.get(k) for k in ("page_link", "samples", "text", "files")):
            ws.save_brief(str(it.get("page_link") or "")[:300], _samples(it.get("samples")), str(it.get("text") or "")[:20000], [], by="online")
            for f in it.get("files") or []:
                if isinstance(f, dict) and f.get("asset"):
                    files.append({"brand": (info or {}).get("id") or "", "name": Path(str(f.get("name") or "file")).name, "asset": str(f["asset"])})
        else:
            say(f"⚠ یک مورد رد شد: {json.dumps({k: v for k, v in it.items() if not k.startswith('_')}, ensure_ascii=False)[:120]}")
            continue
        store.add_event(ws, "client", "online", f"از داشبورد آنلاین رسید ({label}): {t}", {"id": it.get("id")})
        applied.append(it)
    return applied, files


def load_dir(folder):
    """the shared "actions" collection as ArtifactData saved it (out_dir): one JSON file per document"""
    items = []
    for f in sorted(Path(folder).rglob("*.json")):
        try:
            obj = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if not isinstance(obj, dict):
            continue
        body = dict(obj)
        # ArtifactData names each file after the document id, spelling "~" as "@" (our ids never contain "@")
        body["_key"] = f.stem.replace("@", "~")   # the document id (the body's own "id" is the idea's)
        items.append(body)
    items.sort(key=lambda x: str(x.get("at") or ""))
    return {"v": 1, "items": items}
