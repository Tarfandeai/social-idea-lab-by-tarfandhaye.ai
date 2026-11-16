# Social Idea Lab by Tarfandhaye.ai — © 2026 Tarfandhaye.ai — All rights reserved. Personal use only; see LICENSE.md.
"""Writing QC, pre-production and storyboards onto the board. Used by the commands. Standard library only."""
import json
import re
import urllib.parse
from pathlib import Path

from . import brand, store

KIND_FA = {"motion": "موشن", "filmed": "ضبط ویدئو", None: "نامشخص"}
VERDICT_FA = {"fit": "مناسب", "partial": "نیمه‌مناسب (با تغییر)", "unfit": "نامناسب"}
DECISION_FA = {"approved": "تأیید کارفرما", "approved_alt": "جایگزین تأیید شد", "deleted": "حذف شد", None: "منتظر کارفرما"}
GROUP_FA = {"people": "آدم‌ها", "location": "لوکیشن", "equipment": "تجهیزات", "props": "وسایل صحنه", "software": "نرم‌افزار و ابزار AI",
            "assets": "فایل‌ها و المان‌ها"}
SHOTS = ("closeup", "wide", "pov", "topdown", "text", "split", "product", "person", "hands", "infographic", "map", "screen",
         "timelapse", "logo", "transition")
DOC_FOOTER = f"\n\n---\n{brand.COPY} · {brand.NAME} — همه‌ی حقوق محفوظ است.\n"


def _quiet(*a):
    pass


def ev(ws, agent, type_, msg="", **data):
    return store.add_event(ws, agent, type_, msg, data, demo=bool(ws.config.get("demo")))


def ws_url(ws, path):
    try:
        rel = Path(path).expanduser().resolve().relative_to(ws.root)
    except (ValueError, OSError):
        return None
    return "/ws/" + urllib.parse.quote(rel.as_posix())


def as_items(v):
    if not v:
        return []
    if isinstance(v, (str, dict)):
        v = [v]
    out = []
    for x in v:
        if isinstance(x, str) and x.strip():
            out.append({"name": x.strip()})
        elif isinstance(x, dict) and (x.get("name") or x.get("title")):
            out.append({"name": str(x.get("name") or x.get("title")), **{k: x[k] for k in ("note", "have", "qty", "cost") if k in x}})
    return out


def extract_json(text):
    """the JSON part of a chat answer: a ```json block, or the outermost {...} / [...]"""
    t = str(text or "").strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", t)
    if m:
        t = m.group(1).strip()
    for o, c in (("{", "}"), ("[", "]")):
        i, j = t.find(o), t.rfind(c)
        if i != -1 and j > i:
            try:
                return json.loads(t[i:j + 1])
            except ValueError:
                continue
    raise SystemExit("⛔ توی جواب، JSON درست پیدا نشد. فایل JSON رو دوباره بساز.")


# ---------- QC ----------

def compact_checks(checks):
    """checks as a list [{area, ok, note}] or compact {area: true | false | "warn" | [ok, note] | "warn: note"}"""
    if isinstance(checks, dict):
        out = []
        for area, v in checks.items():
            if isinstance(v, (list, tuple)):
                out.append({"area": area, "ok": v[0] if v else None, "note": v[1] if len(v) > 1 else ""})
            elif isinstance(v, str) and v.split(":")[0].strip().lower() in ("warn", "false", "true", "x", "no", "ok"):
                head, _, note = v.partition(":")
                h = head.strip().lower()
                out.append({"area": area, "ok": "warn" if h == "warn" else h in ("true", "ok"), "note": note.strip()})
            else:
                out.append({"area": area, "ok": v, "note": ""})
        return out
    return [c for c in (checks or []) if isinstance(c, dict)]


def apply_qc(ws, items, say=_quiet):
    board = ws.board()
    page_palette = ((ws.page.get("visual") or {}).get("palette") or [])
    done = 0
    for it in items:
        if not isinstance(it, dict):
            continue
        key = it.get("id") or it.get("rank")
        idea = None
        if it.get("url"):  # safest: match by the video's link (ids follow the score order and can change between imports)
            want = store.canonical_reel(it["url"])
            idea = next((i for i in board["ideas"] if store.canonical_reel(i.get("url")) == want), None)
            if not idea:
                raise SystemExit(f"⛔ ایده‌ای با این لینک در دسته نیست: {it['url']}")
            if key and str(key).lower() not in (idea["id"].lower(), str(idea.get("rank"))):
                say(f"⚠ برای {it['url']} شناسه‌ی «{key}» داده شده ولی این ویدیو {idea['id']} است؛ با لینک جلو رفتم.")
        if idea is None:
            idea = store.find_idea(board, key)
        if it.get("kind") in store.KINDS:
            idea["kind"] = it["kind"]
        if "verdict" not in it:  # kind-only row (categorising the other 15)
            continue
        verdict = it.get("verdict")
        if verdict not in store.VERDICTS:
            raise SystemExit(f"⛔ verdict برای {key} باید یکی از این‌ها باشد: {' '.join(store.VERDICTS)}")
        alt = it.get("alternative") or None
        if alt and not isinstance(alt, dict):
            alt = None
        if verdict != "fit" and not alt:
            say(f"⚠ {idea['id']}: «{VERDICT_FA[verdict]}» است ولی جایگزین ندارد. طبق قاعده باید جایگزین بدهی.")
        if alt and alt.get("kind") not in store.KINDS:
            alt["kind"] = idea.get("kind")
        checks = []
        for c in compact_checks(it.get("checks")):
            ok = c.get("ok")
            ok = "warn" if ok in ("warn", "partial", None) else bool(ok)
            note = str(c.get("note") or "")
            checks.append({"area": str(c.get("area", "")), "ok": ok, "note": note})
            if ok is not True and not note:
                say(f"⚠ {idea['id']}: بخش «{c.get('area')}» ✓ نیست ولی یادداشت ندارد؛ برای ✗ و warn دلیل بنویس.")
        fit = it.get("fit") if it.get("fit") is not None else it.get("score")
        try:
            fit = max(0, min(100, int(fit))) if fit is not None else None
        except (TypeError, ValueError):
            fit = None
        idea["qc"] = {"verdict": verdict, "fit": fit, "checks": checks, "logic": str(it.get("logic") or ""), "visual": str(it.get("visual") or ""),
                      "source_palette": [str(c) for c in (it.get("source_palette") or [])][:6],
                      "page_palette": it.get("page_palette") or page_palette, "adapt": str(it.get("adapt") or ""), "alternative": alt,
                      "by": it.get("_by") or "claude", "at": store.now_iso()}
        done += 1
        ev(ws, "qc", "check", f"QC «{idea.get('title', '')[:40]}»: {VERDICT_FA[verdict]}",
           id=idea["id"], verdict=verdict)
        say(f"🔎 {idea['id']}: {VERDICT_FA[verdict]}  ({KIND_FA.get(idea.get('kind'))})" + (f"  ← جایگزین: {alt.get('title')}" if alt else ""))
    ws.save_board(board)
    if done and ws.benchmark_request().get("status") in ("queued", "running"):
        ws.set_benchmark("done")
        ev(ws, "scout", "benchmark", "بنچ‌مارک تموم شد؛ ایده‌ها و QC روی داشبورد")
    return done


# ---------- pre-production ----------

def approved_or_warn(ws, idea, say=_quiet):
    dec = ws.decisions()["ideas"].get(idea["id"], {})
    if dec.get("status") not in ("approved", "approved_alt"):
        say(f"⚠ کارفرما هنوز «{idea.get('title', '')[:40]}» را تأیید نکرده ({DECISION_FA.get(dec.get('status'))}). ثبت شد، ولی معمولاً این مرحله بعد از تأیید است.")
    return dec


def preprod_md(idea, title, pp):
    lines = [f"# سند پیش‌تولید: {title}", "", f"- دسته: {KIND_FA.get(pp.get('kind') or idea.get('kind'))}",
             f"- قالب: {pp.get('format', '')}", f"- ایده‌ی منبع: {idea.get('title', '')} — {idea.get('source_page', '')} {idea.get('url', '')}", ""]
    if pp.get("summary"):
        lines += ["## خلاصه", pp["summary"], ""]
    if pp.get("hook"):
        lines += ["## هوک", pp["hook"], ""]
    for g in store.PREPROD_GROUPS:
        if pp.get(g):
            lines.append(f"## {GROUP_FA[g]}")
            for x in pp[g]:
                lines.append(f"- [{'x' if x.get('have') else ' '}] {x['name']}" + (f" — {x['note']}" if x.get("note") else ""))
            lines.append("")
    if pp.get("schedule"):
        lines += ["## برنامه‌ی کار", "| مرحله | زمان |", "|---|---|"] + [f"| {s.get('step', '')} | {s.get('time', '')} |" for s in pp["schedule"]] + [""]
    for key, name in (("checklist", "چک‌لیست پیش از ضبط/ساخت"), ("risks", "ریسک‌ها و راه‌حل")):
        if pp.get(key):
            lines += [f"## {name}"] + [f"- {x}" for x in pp[key]] + [""]
    for key, name in (("time", "زمان کل"), ("budget", "هزینه")):
        if pp.get(key):
            lines.append(f"**{name}:** {pp[key]}")
    return "\n".join(lines) + DOC_FOOTER


def apply_preprod(ws, key, data, say=_quiet, by="claude"):
    if not isinstance(data, dict):
        raise SystemExit("⛔ پیش‌تولید باید یک شیء JSON باشد (ساختارش در modules/4-preproduction.md).")
    board = ws.board()
    idea = store.find_idea(board, key)
    dec = approved_or_warn(ws, idea, say)
    pp = {k: str(data.get(k)) for k in ("summary", "hook", "format", "duration", "time", "budget") if data.get(k)}
    pp["kind"] = data.get("kind") if data.get("kind") in store.KINDS else None
    for g in store.PREPROD_GROUPS:
        pp[g] = as_items(data.get(g))
    pp["schedule"] = [s for s in (data.get("schedule") or []) if isinstance(s, dict)]
    pp["checklist"] = [str(x) for x in (data.get("checklist") or [])]
    pp["risks"] = [str(x) for x in (data.get("risks") or [])]
    pp["by"] = by
    pp["at"] = store.now_iso()
    idea["preprod"] = pp
    ws.save_board(board)
    title = store.production_title(idea, dec)
    d = store.idea_dir(ws, idea)
    (d / "preprod.md").write_text(preprod_md(idea, title, pp), encoding="utf-8")
    n = sum(len(pp[g]) for g in store.PREPROD_GROUPS)
    ev(ws, "prod", "preprod", f"سند پیش‌تولید «{title[:40]}» آماده شد ({n} قلم)", id=idea["id"])
    say(f"📋 سند پیش‌تولید {idea['id']} ثبت شد: {d / 'preprod.md'}")
    return idea


# ---------- storyboard ----------

def storyboard_md(title, sb):
    dur = sb.get("duration")
    dur = f"{dur:g}" if isinstance(dur, (int, float)) else (dur or "—")
    lines = [f"# استوری‌بورد: {title}", "", f"- طول کل: {dur} ثانیه · {len(sb['frames'])} فریم", ""]
    if sb.get("style"):
        lines += [f"**سبک:** {sb['style']}", ""]
    for f in sb["frames"]:
        lines.append(f"## فریم {f['n']} · {f.get('time', '')} · {f.get('shot', '')}")
        for key, name in (("visual", "تصویر"), ("text", "متن روی صفحه"), ("vo", "نریشن/دیالوگ"), ("camera", "دوربین/حرکت"),
                          ("sfx", "صدا"), ("transition", "ترنزیشن")):
            if f.get(key):
                lines.append(f"- **{name}:** {f[key]}")
        if f.get("sketch"):
            lines.append(f"- طرح: `{f['sketch']}`")
        lines.append("")
    if sb.get("music"):
        lines += [f"**موزیک:** {sb['music']}", ""]
    if sb.get("caption"):
        lines += ["## کپشن پیشنهادی", sb["caption"], ""]
    return "\n".join(lines) + DOC_FOOTER


def apply_storyboard(ws, key, data, say=_quiet, by="claude"):
    if isinstance(data, list):
        data = {"frames": data}
    if not isinstance(data, dict) or not data.get("frames"):
        raise SystemExit("⛔ استوری‌بورد باید frames داشته باشد (ساختارش در modules/5-storyboard.md).")
    board = ws.board()
    idea = store.find_idea(board, key)
    dec = approved_or_warn(ws, idea, say)
    d = store.idea_dir(ws, idea)
    frames = []
    for n, f in enumerate(data["frames"], 1):
        if not isinstance(f, dict):
            continue
        fr = {k: str(f.get(k)) for k in ("time", "visual", "text", "vo", "camera", "sfx", "transition", "accent") if f.get(k)}
        fr["n"] = n
        try:
            fr["dur"] = float(f.get("dur") or f.get("duration") or 0) or None
        except (TypeError, ValueError):
            fr["dur"] = None
        shot = str(f.get("shot") or "").lower()
        fr["shot"] = shot if shot in SHOTS else "wide"
        sk = f.get("sketch") if by == "claude" else None
        if sk:
            p = Path(sk).expanduser()
            if not p.is_absolute():
                p = d / p
            url = ws_url(ws, p) if p.is_file() else None
            if url:
                fr["sketch"] = url
            else:
                say(f"⚠ طرح فریم {n} پیدا نشد: {sk}")
        frames.append(fr)
    old = idea.get("storyboard") or {}
    dur = data.get("duration")
    try:
        dur = float(dur) if dur else (sum(float(f.get("dur") or 0) for f in frames) or None)
    except (TypeError, ValueError):
        dur = sum(float(f.get("dur") or 0) for f in frames) or None
    sb = {"frames": frames, "duration": dur, "style": data.get("style"), "music": data.get("music"), "caption": data.get("caption"),
          "palette": [str(c) for c in (data.get("palette") or [])][:6] or None, "version": int(old.get("version") or 0) + 1,
          "by": by, "at": store.now_iso()}
    idea["storyboard"] = sb
    ws.save_board(board)
    if ws.decisions()["storyboards"].get(idea["id"], {}).get("status") == "revise":
        ws.clear_storyboard_decision(idea["id"])
    title = store.production_title(idea, dec)
    (d / "storyboard.md").write_text(storyboard_md(title, sb), encoding="utf-8")
    ev(ws, "prod", "storyboard", f"استوری‌بورد «{title[:40]}» آماده شد ({len(frames)} فریم، نسخه‌ی {sb['version']})",
       id=idea["id"])
    say(f"🎞 استوری‌بورد {idea['id']} (نسخه‌ی {sb['version']}، {len(frames)} فریم) ثبت شد: {d / 'storyboard.md'}")
    return idea
