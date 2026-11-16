# Social Idea Lab by Tarfandhaye.ai — © 2026 Tarfandhaye.ai — All rights reserved. Personal use only; see LICENSE.md.
"""Local live dashboard (standard library only).
Only answers on this computer (127.0.0.1); nothing is ever reachable from the Wi-Fi or the internet.
GET  /api/state    page + board + client decisions + reel inbox      GET /api/events  live log
POST /api/decide   {id, action: approve|approve_alt|delete|restore}
POST /api/storyboard {id, action: approve|revise|reset, note?}
POST /api/inbox    {url, note?}   a reel link sent from the dashboard
POST /api/platform {platform: instagram|youtube|linkedin}   which platform the dashboard (and Claude's next search) works on
POST /api/mode     {mode: strategy|login}          how Claude researches: from the brand's documents, or with a signed-in browser
POST /api/brief    {page_link, samples, text, files:[{name, data(base64)}]}   brand inputs for the strategy mode
POST /api/brand/select {id} · /api/brand/add {name, page_link, ...} · /api/brand/remove {id} (never deleted: bNN archived, main only hidden)"""
import base64
import binascii
import json
import mimetypes
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import brand, store

HERE = Path(__file__).resolve().parent
PAGE = HERE / "dashboard.html"
LOGO = HERE.parents[1] / "assets" / "logo.png"
IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
ACTION_FA = {"approve": "تأیید شد", "approve_alt": "جایگزین تأیید شد", "delete": "از ایده‌های ساخت حذف شد",
             "restore": "برگشت به صف تصمیم"}
SB_FA = {"approve": "استوری‌بورد تأیید شد ← مرحله‌ی تولید", "revise": "استوری‌بورد نیاز به اصلاح دارد",
         "reset": "تصمیم استوری‌بورد برداشته شد"}


def busy_or(w):
    """a brand chip shows Claude at work when any of its platforms is queued or running"""
    m = w.benchmarks()
    run = [r for r in m.values() if r.get("status") in ("queued", "running")]
    if run:
        return {"status": "running" if any(r.get("status") == "running" for r in run) else "queued"}
    return w.benchmark_request()


def brands_view(lab, active_id):
    out = []
    for b in store.visible_brands(lab):  # a removed main brand is only hidden (its data stays in place)
        w = store.Workspace((lab.root / b["path"]).resolve())
        page = w.page
        out.append({"id": b["id"], "name": b["name"], "handle": page.get("handle") or "", "active": b["id"] == active_id,
                    "platforms": {p: w.for_platform(p).summary() for p in store.PLATFORMS},
                    "benchmark": busy_or(w), "benchmarks": w.benchmarks(), "strategy": bool((page.get("strategy") or {}).get("summary") or (page.get("strategy") or {}).get("source"))})
    return out


def state(ws, srv=None, lab=None, info=None):
    cfg = ws.config
    brief = ws.brief()
    brief_view = {k: brief.get(k) for k in ("page_link", "samples", "text", "at", "by", "read")}
    brief_view["files"] = [{"name": f.get("name"), "size": f.get("size")} for f in brief.get("files") or []]
    out = {"rev": ws.rev(), "platform": ws.platform, "platforms": {p: ws.for_platform(p).summary() for p in store.PLATFORMS},
           "mode": ws.mode, "brief": brief_view if brief else {},
           "page": ws.page, "board": ws.board(), "decisions": ws.decisions(), "inbox": ws.inbox(),
           "demo": bool(cfg.get("demo") or (lab is not None and lab.config.get("demo"))), "name": brand.NAME, "version": brand.VERSION,
           "benchmark": ws.benchmark_request(), "benchmarks": ws.benchmarks()}
    if lab is not None:
        out["brand"] = (info or {}).get("id") or ""
        out["brands"] = brands_view(lab, out["brand"])
        out["rev"] = out["brand"] + "|" + out["rev"] + "|" + lab_rev(lab)
    return out


def lab_rev(lab):
    """changes when a brand is added or any brand's benchmark request moves"""
    parts = []
    for p in [lab.hidden / "brands.json", lab.config_path] + [(lab.root / b["path"]).resolve() / ".lab" / "requests.json" for b in store.list_brands(lab)]:
        try:
            parts.append(str(p.stat().st_mtime_ns))
        except FileNotFoundError:
            parts.append("0")
    return ".".join(parts)


def make_handler(lab):
    class Handler(BaseHTTPRequestHandler):
        def _ws(self):
            ws, info = store.brand_ws(lab)
            return ws, info

        def _state(self, ws, info):
            return state(ws, self.server if self._is_local() else None, lab, info)

        def _send(self, code, body, ctype, extra=None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code=200):
            self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def _is_local(self):
            return self.client_address[0] in ("127.0.0.1", "::1", "::ffff:127.0.0.1")

        def _allowed(self, q):
            """only this computer, and only with a Host header of 127.0.0.1/localhost (stops DNS rebinding);
            a page from another site (Origin) is refused"""
            port = self.server.server_address[1]
            host = self.headers.get("Host", "")
            if not (self._is_local() and host in (f"127.0.0.1:{port}", f"localhost:{port}")):
                return False
            origin = self.headers.get("Origin")
            return not (origin and urllib.parse.urlparse(origin).netloc != host)

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            q = urllib.parse.parse_qs(u.query)
            if not self._allowed(q):
                return self._send(403, "⛔ داشبورد فقط روی همین کامپیوتر و از آدرس http://127.0.0.1 باز می‌شه.".encode("utf-8"),
                                  "text/plain; charset=utf-8")
            if u.path in ("/", "/index.html"):
                return self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            ws, info = self._ws()
            if u.path == "/api/state":
                rev = ((info or {}).get("id") or "") + "|" + ws.rev() + "|" + lab_rev(lab)
                if q.get("rev", [""])[0] == rev:
                    return self._json({"same": True})
                return self._json(self._state(ws, info))
            if u.path == "/api/events":
                try:
                    since = int(q.get("since", ["0"])[0])
                except ValueError:
                    since = 0
                events, nxt = store.read_events(ws, since)
                return self._json({"events": events, "next": nxt, "brand": (info or {}).get("id") or ""})
            if u.path == "/logo.png" and LOGO.exists():
                return self._send(200, LOGO.read_bytes(), "image/png")
            if u.path.startswith("/ws/"):
                rel = urllib.parse.unquote(u.path[4:])
                p = (ws.root / rel).resolve()
                if ws.root in p.parents and p.suffix.lower() in IMAGE_TYPES and p.is_file() and ws.hidden not in p.parents:
                    ctype = "image/svg+xml" if p.suffix.lower() == ".svg" else (mimetypes.guess_type(str(p))[0] or "image/png")
                    return self._send(200, p.read_bytes(), ctype,
                                      {"Content-Security-Policy": "default-src 'none'; img-src data:; style-src 'unsafe-inline'; sandbox"})
            self._send(404, b"not found", "text/plain")

        def do_POST(self):
            u = urllib.parse.urlparse(self.path)
            q = urllib.parse.parse_qs(u.query)
            if not self._allowed(q) or "application/json" not in self.headers.get("Content-Type", ""):
                return self._json({"ok": False, "error": "forbidden"}, 403)
            limit = 40 * 1024 * 1024 if u.path == "/api/brief" else 8192
            try:
                n = int(self.headers.get("Content-Length") or 0)
                if n > limit:
                    return self._json({"ok": False, "error": "فایل خیلی بزرگه (حداکثر حدود ۳۰ مگابایت)"}, 413)
                body = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
            except (ValueError, UnicodeDecodeError):
                return self._json({"ok": False, "error": "bad json"}, 400)
            ws, info = self._ws()
            demo = bool(ws.config.get("demo") or lab.config.get("demo"))
            note = str(body.get("note") or "").strip()[:500] or None
            who = "client"
            try:
                if u.path == "/api/brand/select":
                    it = store.use_brand(lab, str(body.get("id") or ""))
                    ws, info = self._ws()
                    store.add_event(ws, "client", "brand", f"برند: {it['name']}", {"brand": it["id"]}, demo=demo)
                    return self._json({"ok": True, "state": self._state(ws, info)})
                if u.path == "/api/brand/remove":  # nothing is deleted: archived (bNN) or only hidden (main)
                    it, dst, _ = store.remove_brand(lab, str(body.get("id") or ""))
                    ws, info = self._ws()
                    how = "پوشه‌ش بایگانی شد" if dst else "داده‌هاش سر جاشه، فقط پنهان شد"
                    store.add_event(ws, "client", "brand", f"برند «{it['name']}» از فهرست برداشته شد ({how})",
                                    {"brand": it["id"]}, demo=demo)
                    return self._json({"ok": True, "removed": it["id"], "archived": bool(dst), "state": self._state(ws, info)})
                if u.path == "/api/brand/add":
                    name = str(body.get("name") or "").strip()[:80]
                    link = str(body.get("page_link") or "").strip()[:300]
                    yt = str(body.get("youtube") or "").strip()[:300]
                    li = str(body.get("linkedin") or "").strip()[:300]
                    nws, it = store.add_brand(lab, name, url=link if "instagram.com" in link else "", handle=store.handle_from_url(link),
                                              youtube=yt or (link if "youtube.com" in link or "youtu.be" in link else ""),
                                              linkedin=li or (link if "linkedin.com" in link else ""),
                                              niche=str(body.get("niche") or "").strip()[:200])
                    text = str(body.get("text") or "").strip()[:20000]
                    if link or text:
                        nws.save_brief(link, [], text, [], by=who)
                    store.use_brand(lab, it["id"])
                    store.add_event(nws, "client", "brand", f"برند تازه اضافه شد: {name}", {"brand": it["id"]}, demo=demo)
                    if body.get("benchmark"):
                        nws.set_benchmark("queued", mode=nws.mode, region="both", by=who)
                        store.add_event(nws, "client", "benchmark", f"درخواست بنچ‌مارک برای «{name}» در صف Claude", {}, demo=demo)
                    ws, info = self._ws()
                    return self._json({"ok": True, "state": self._state(ws, info)})
                if u.path == "/api/benchmark":   # {platforms: [...], region: ir|intl|both} or {cancel: true, platforms: [...]}
                    plats = [x for x in (body.get("platforms") or [ws.platform]) if x in store.PLATFORMS] or [ws.platform]
                    region = body.get("region") if body.get("region") in store.REGIONS else "both"
                    window = int(body.get("max_age") or 180) if str(body.get("max_age") or 180).isdigit() and int(body.get("max_age") or 180) in store.WINDOWS else 180
                    name = (info or {}).get("name") or ws.page.get("name") or ws.page.get("handle") or "برند"
                    done_, busy = [], []
                    for pl in plats:
                        wp = ws.for_platform(pl)
                        cur = wp.benchmark_request().get("status")
                        if body.get("cancel"):
                            if cur == "queued":
                                wp.set_benchmark("cancelled", by=who)
                                done_.append(pl)
                            continue
                        if cur in ("queued", "running"):
                            busy.append(pl)
                            continue
                        wp.set_benchmark("queued", mode=ws.mode, region=region, max_age=window, by=who)
                        done_.append(pl)
                    if not body.get("cancel") and busy and not done_:
                        return self._json({"ok": False, "error": "بنچ‌مارک " + "، ".join(store.PLATFORM_FA[x] for x in busy) + " از قبل در جریانه"}, 409)
                    if done_:
                        fa_ = "، ".join(store.PLATFORM_FA[x] for x in done_)
                        store.add_event(ws, "client", "benchmark", (f"درخواست بنچ‌مارک لغو شد ({fa_})" if body.get("cancel") else
                                        f"بنچ‌مارک جدید برای «{name}»: {fa_} · {store.REGION_FA[region]} · {store.WINDOW_FA[window]}"), {"platforms": done_, "region": region}, demo=demo)
                    return self._json({"ok": True, "queued": done_, "busy": busy, "state": self._state(ws, info)})
            except SystemExit as e:
                return self._json({"ok": False, "error": str(e.code).replace("⛔ ", "")}, 400)
            if u.path == "/api/mode":
                m = str(body.get("mode") or "")
                if m not in store.MODES:
                    return self._json({"ok": False, "error": "unknown mode"}, 400)
                if m != ws.mode:
                    ws.save_config(mode=m)
                    store.add_event(ws, "client", "mode", "روش بررسی: " + store.MODE_FA[m], {"mode": m}, demo=demo)
                return self._json({"ok": True, "state": self._state(ws, info)})
            if u.path == "/api/brief":
                link = str(body.get("page_link") or "").strip()[:300]
                samples = [s.strip()[:300] for s in str(body.get("samples") or "").splitlines() if s.strip().startswith("http")][:30]
                text = str(body.get("text") or "").strip()[:20000]
                files = []
                for f in (body.get("files") or [])[:10]:
                    name = Path(str(f.get("name") or "file")).name
                    if Path(name).suffix.lower() not in store.BRIEF_EXT:
                        return self._json({"ok": False, "error": f"این نوع فایل پذیرفته نمی‌شه: {name}"}, 400)
                    try:
                        files.append((name, base64.b64decode(str(f.get("data") or ""), validate=True)))
                    except (ValueError, binascii.Error):
                        return self._json({"ok": False, "error": f"فایل خراب رسید: {name}"}, 400)
                if not (link or samples or text or files):
                    return self._json({"ok": False, "error": "چیزی برای ثبت نیست"}, 400)
                ws.save_brief(link, samples, text, files, by=who)
                parts = [p for p in ("لینک پیج" if link else "", f"{len(samples)} نمونه پست" if samples else "", "توضیح متنی" if text else "",
                                     f"{len(files)} فایل" if files else "") if p]
                store.add_event(ws, "client", "brief", "ورودی برند رسید: " + "، ".join(parts), {}, demo=demo)
                return self._json({"ok": True, "state": self._state(ws, info)})
            if u.path == "/api/platform":
                p = str(body.get("platform") or "")
                if p not in store.PLATFORMS:
                    return self._json({"ok": False, "error": "unknown platform"}, 400)
                if p != ws.platform:
                    ws.save_config(platform=p)
                    store.add_event(ws, "client", "platform", f"پلتفرم: {store.PLATFORM_FA[p]}", {"platform": p}, demo=demo)
                return self._json({"ok": True, "state": self._state(ws, info)})
            if u.path == "/api/inbox":
                url = str(body.get("url") or "").strip()
                m = store.REEL_RE.match(url)
                if not m:
                    return self._json({"ok": False, "error": "لینک ریل اینستاگرام، ویدیوی یوتیوب، پست لینکدین یا تیک‌تاک نیست"}, 400)
                item = ws.add_inbox(url, note, by=who)
                if not item:
                    return self._json({"ok": False, "error": "این لینک قبلاً اضافه شده"}, 409)
                store.add_event(ws, "client", "inbox", "لینک ریل تازه " + "از داشبورد" + " اضافه شد",
                                {"url": url}, demo=demo)
                return self._json({"ok": True, "state": self._state(ws, info)})
            idea_id, action = str(body.get("id", "")), str(body.get("action", ""))
            board = ws.board()
            idea = next((i for i in board["ideas"] if i.get("id") == idea_id), None)
            if not idea:
                return self._json({"ok": False, "error": "unknown idea"}, 404)
            try:
                if u.path == "/api/decide" and action in store.IDEA_ACTIONS:
                    if action == "approve_alt" and not (idea.get("qc") or {}).get("alternative"):
                        return self._json({"ok": False, "error": "no alternative"}, 400)
                    ws.decide(idea_id, action, by=who, note=note)
                    if action in ("delete", "restore"):
                        ws.clear_storyboard_decision(idea_id)
                    title = (idea["qc"]["alternative"].get("title") if action == "approve_alt" else idea.get("title")) or idea_id
                    store.add_event(ws, "client", "decision", f"«{title}» {ACTION_FA[action]}",
                                    {"id": idea_id, "action": action, "note": note}, demo=demo)
                elif u.path == "/api/storyboard" and action in store.SB_ACTIONS:
                    if not idea.get("storyboard"):
                        return self._json({"ok": False, "error": "no storyboard"}, 400)
                    ws.decide_storyboard(idea_id, action, by=who, note=note)
                    store.add_event(ws, "client", "storyboard", f"«{idea.get('title', idea_id)}»: {SB_FA[action]}",
                                    {"id": idea_id, "action": action, "note": note}, demo=demo)
                else:
                    return self._json({"ok": False, "error": "unknown action"}, 400)
            except SystemExit as e:
                return self._json({"ok": False, "error": str(e.code)}, 409)
            return self._json({"ok": True, "state": self._state(ws, info)})

        def log_message(self, *a):
            pass

    return Handler


def serve(ws, port=8770, on_ready=None, block=True):
    """127.0.0.1 only: the dashboard is never reachable from the Wi-Fi or the internet."""
    last = None
    for p in range(port, port + 20):
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", p), make_handler(ws))
            break
        except OSError as e:
            last = e
    else:
        raise SystemExit(f"⛔ پورت آزادی برای داشبورد پیدا نشد ({last}).")
    srv.daemon_threads = True
    real_port = srv.server_address[1]
    url = f"http://127.0.0.1:{real_port}/"
    if on_ready:
        on_ready(url)
    if not block:
        import threading
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        return srv
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
