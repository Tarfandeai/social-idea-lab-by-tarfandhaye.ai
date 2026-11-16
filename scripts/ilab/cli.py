# Social Idea Lab by Tarfandhaye.ai — © 2026 Tarfandhaye.ai — All rights reserved. Personal use only; see LICENSE.md.
"""Every command of the skill: python run.py <command> [options]. Output is also saved to <work>/.lab/last.txt."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from . import apply, brand, demo, export, scout, server, store
from .apply import DECISION_FA, KIND_FA, VERDICT_FA, ev, ws_url

OUT = []
STAGE_FA = {"candidate": "کاندید", "qc": "QC شد، منتظر کارفرما", "approved": "تأیید شد ← پیش‌تولید", "preprod": "پیش‌تولید آماده ← استوری‌بورد",
            "storyboard": "استوری‌بورد منتظر تأیید", "production": "در تولید", "done": "ساخته شد", "deleted": "حذف شد"}

HELP = """
فرمان‌ها (RUN = python "<SKILL_DIR>/scripts/run.py"):
  همه‌ی فرمان‌ها روی برند و پلتفرمی کار می‌کنند که روی داشبورد انتخاب شده؛ با --brand ID و --platform instagram|youtube|linkedin عوضش کن.
  brands | brand add "اسم" [--link URL] [--youtube URL] [--linkedin URL] [--niche ..] | brand use ID    چند برند (هر کدام جدا)
  brand remove ID                   برداشتن برند از فهرست (فقط وقتی کاربر خواست؛ پاک نمی‌شه: bNN بایگانی، main فقط پنهان)
  requests                          صف «بنچ‌مارک جدید» که از دکمه‌ی داشبورد آمده
  bench request|start|done|cancel [--brand ID]   ثبت یا جلو بردن بنچ‌مارک یک برند
  init [--work DIR]                 ساخت پوشه‌ی کار و فایل پیج رفرنس (page.json)
  use [instagram|youtube|linkedin]  نمایش یا انتخاب پلتفرم (همان سوییچ بالای داشبورد)
  mode [strategy|login]             روش بررسی: با سند استراتژی (بدون لاگین) یا با مرورگر لاگین‌شده (فقط خواندن)
  brief [--done]                    ورودی‌های برند که از داشبورد آمده: لینک، نمونه پست، توضیح متنی، فایل‌ها
  doctor                            وضعیت پوشه، پیج رفرنس و ایده‌ها
  page [--file FILE.json] [--doc سند]   ثبت یا نمایش پروفایل پیج رفرنس و استراتژی برند (بدون لاگین)
  inbox [--all] [--done URL]        لینک ریل‌هایی که از داشبورد فرستاده شده
  scout --import FILE.json [--new]  ثبت ریل‌هایی که Claude خوانده ← امتیاز، ۲۰ ایده، تاپ ۵
  scout --raw RAW.txt --meta M.json  همان، از خط‌های فشرده‌ی مرورگر (عددها دوباره تایپ نمی‌شوند)
  qc --file FILE.json               ثبت نتیجه‌ی QC (مناسب/نامناسب، دلیل منطقی و بصری، جایگزین، موشن/ضبط)
  kind ID motion|filmed             عوض کردن دسته‌ی یک ایده
  preprod ID --file FILE.json       ثبت سند پیش‌تولید (ابزار، المان، تجهیزات…)
  storyboard ID --file FILE.json    ثبت استوری‌بورد (فریم‌به‌فریم)
  status [--json]                   وضعیت همه‌ی ایده‌ها و تصمیم‌های کارفرما
  decide ID approve|approve_alt|delete|restore   ثبت تصمیم کارفرما از چت (فقط وقتی خود کاربر گفت)
  sb ID approve|revise [--note ..]  تصمیم کارفرما درباره‌ی استوری‌بورد (فقط وقتی خود کاربر گفت)
  done ID                           علامت «ساخته شد»
  log AGENT TYPE --msg ".." [--id ID] [--query Q]   ثبت کاری که در مرورگر انجام شد (AGENT: page scout qc prod system)
  app                               داشبورد به‌صورت پنجره‌ی جدا (بدون نوار مرورگر)
  dashboard [--open]                داشبورد زنده (با دکمه‌های تأیید و حذف)
  demo [--auto] [--speed 1]         داشبورد با داده‌ی نمونه (پوشه‌ی جدا؛ به کار واقعی دست نمی‌زند)
  export [--out FILE.html] [--demo]  داشبورد آنلاین: یک فایل HTML مستقل (همه‌ی برندها و پلتفرم‌ها)، هر بار با ورژن تازه
  online [--url URL]                آدرس Artifact داشبورد آنلاین این پوشه‌ی کار (ثبت یا نمایش)
  import-pack --dir DIR | --file F  اعمال کارهای کارفرما از داشبورد آنلاین (پوشه‌ی actions یا متن «پیام برای Claude»)
  reset                             بایگانی ایده‌ها و تصمیم‌ها و خالی کردن داشبورد
"""


def say(*parts):
    s = " ".join(str(p) for p in parts)
    print(s, flush=True)
    OUT.append(s)


def flush_last(ws):
    try:
        ws.hidden.mkdir(parents=True, exist_ok=True)
        ws.last_path.write_text("\n".join(OUT), encoding="utf-8")
    except OSError:
        pass


def load_list(path, key):
    data = store.read_json(path, None)
    if data is None:
        raise SystemExit(f"⛔ فایل پیدا نشد: {path}")
    if isinstance(data, dict):
        data = data.get(key, data.get("items", data if key == "_self" else []))
    return data


# ---------- commands ----------

def cmd_init(ws, a):
    first = not ws.config_path.exists()
    ws.ensure()
    store.remember(ws)
    if first:
        ws.save_config(created=store.now_iso())
        ev(ws, "system", "log", "پوشه‌ی کار آماده شد")
    say(brand.banner())
    say(f"📁 پوشه‌ی کار: {ws.root}")
    say(f"   پیج رفرنس: {ws.page_path}")
    say("قدم بعد: پروفایل پیج رفرنس را پر کن (`page --file`)، بعد داشبورد را باز کن (`dashboard --open`).")


def page_missing(p):
    st = p.get("strategy") or {}
    miss = []
    if not (p.get("handle") or p.get("name")):
        miss.append("handle/name")
    for k, alt_k in (("niche", "summary"), ("audience", "audience"), ("tone", "voice")):
        if not p.get(k) and not st.get(alt_k):
            miss.append(k)
    if not (p.get("visual") or {}).get("style") and not (p.get("visual") or {}).get("palette"):
        miss.append("visual")
    return miss


def cmd_doctor(ws, a):
    say(brand.banner())
    say(f"پایتون: {sys.version.split()[0]}")
    say(f"پوشه‌ی کار: {ws.root}  {'✓' if ws.exists() else '✗ هنوز init نشده'}")
    if not ws.exists():
        return 1
    p = ws.page
    miss = page_missing(p)
    say(f"پیج رفرنس: {p.get('handle') or p.get('name') or '—'}  " + ("✓ کامل" if not miss else "ناقص: " + "، ".join(miss)))
    st = p.get("strategy") or {}
    say("استراتژی برند: " + (f"✓ {st.get('source') or 'خلاصه ثبت شده'}" if (st.get("summary") or st.get("source")) else "داده نشده (اختیاری)"))
    say(f"پلتفرم انتخاب‌شده: {store.PLATFORM_FA[ws.platform]}  ·  روش بررسی: {store.MODE_FA[ws.mode]}")
    for pl in store.PLATFORMS:
        w = ws.for_platform(pl)
        b, d = w.board(), w.decisions()
        say(f"  {store.PLATFORM_FA[pl]}: ایده‌ها {len(b['ideas'])}  ·  QC شده {sum(1 for i in b['ideas'] if i.get('qc'))}  ·  تصمیم کارفرما {len(d['ideas'])}")
    if ws.config.get("dashboard"):
        say(f"داشبورد (آخرین آدرس): {ws.config['dashboard']}")


def cmd_page(ws, a):
    if not a.file and not a.doc:
        say(json.dumps(ws.page, ensure_ascii=False, indent=2))
        return 0
    data = store.read_json(a.file, None) if a.file else {}
    if not isinstance(data, dict):
        raise SystemExit("⛔ فایل پیج باید یک شیء JSON باشد (مثل page.json).")
    page = json.loads(json.dumps(store.PAGE_TEMPLATE))
    old = ws.page
    if not a.file:  # only attaching a strategy document to the existing profile
        data = old
    for k, v in data.items():
        if isinstance(v, dict) and isinstance(page.get(k), dict):
            page[k].update(v)
        else:
            page[k] = v
    if a.doc:
        src = Path(a.doc).expanduser()
        if not src.is_file():
            raise SystemExit(f"⛔ سند استراتژی پیدا نشد: {a.doc}")
        dst = ws.brand_dir / src.name
        if src.resolve() != dst.resolve():
            ws.brand_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        page["strategy"]["source"] = src.name
        say(f"📎 سند استراتژی برند کنار پروژه ذخیره شد: {dst}")
    if page.get("handle") and not str(page["handle"]).startswith("@"):
        page["handle"] = "@" + str(page["handle"]).strip()
    page["followers"] = scout.parse_count(page.get("followers"))
    if page.get("avatar") and not str(page["avatar"]).startswith(("http", "/ws/")):
        page["avatar"] = ws_url(ws, page["avatar"])
    store.write_json(ws.page_path, page)
    miss = page_missing(page)
    who = page.get("handle") or page.get("name") or "—"
    has_st = bool((page.get("strategy") or {}).get("summary") or (page.get("strategy") or {}).get("source"))
    ev(ws, "page", "profile", f"پیج رفرنس: {who} — {page.get('niche', '')}" + (" · با استراتژی برند" if has_st else ""), handle=page.get("handle"))
    say(f"✅ پیج رفرنس ثبت شد: {who} ({page.get('name', '')})" + ("  ·  استراتژی برند ✓" if has_st else ""))
    if miss:
        say("⚠ این بخش‌ها خالی است و QC بدون آن‌ها دقیق نیست: " + "، ".join(miss))


def raw_scan(ws, a):
    """--raw: the browser's compact lines + Claude's small meta (Persian title, hook, summary, kind, region) → rows"""
    p = Path(a.raw)
    if not p.is_file():
        raise SystemExit(f"⛔ فایل پیدا نشد: {a.raw}")
    meta = {}
    if a.meta:
        meta = store.read_json(a.meta, None)
        if not isinstance(meta, dict):
            raise SystemExit(f"⛔ فایل meta باید JSON به شکل {{id: {{title, hook, summary, kind, region}}}} باشد: {a.meta}")
    plat = a.platform or ws.platform
    rows, queries, dropped, missing = scout.rows_from_raw(p.read_text(encoding="utf-8"), meta, plat)
    if missing:
        say(f"⚠ این شناسه‌ها در meta هست ولی در خط‌های خام نیست (رد شد): {', '.join(missing[:10])}")
    if dropped:
        say(f"ℹ {dropped} ویدیو در خط‌های خام بود ولی در meta نه (تبلیغ، تکراری یا بی‌ربط؛ کنار رفت).")
    say(f"📄 {len(rows)} ردیف از خط‌های خام ساخته شد ({sum(1 for r in rows if r['read_via'] == 'page')} با جزئیات صفحه).")
    return rows, queries


def cmd_scout(ws, a):
    if not a.import_file and not a.raw:
        say("⛔ فایل نتیجه‌ها را بده: `scout --raw RAW.txt --meta META.json` یا `scout --import FILE.json` (ساختارش در modules/2-scout.md).")
        return 2
    if a.raw:
        rows_in, queries = raw_scan(ws, a)
        source = a.raw
    else:
        data = store.read_json(a.import_file, None)
        if data is None:
            raise SystemExit(f"⛔ فایل پیدا نشد: {a.import_file}")
        rows_in = data.get("rows", []) if isinstance(data, dict) else data
        queries = (data.get("queries") if isinstance(data, dict) else None) or []
        source = a.import_file
    plats = [scout.platform_of(r) for r in rows_in if isinstance(r, dict)]
    other = [p for p in plats if p in store.PLATFORMS and p != ws.platform]
    say(f"پلتفرم: {store.PLATFORM_FA[ws.platform]}")
    if plats and len(other) > len(plats) / 2 and not a.platform:
        say(f"⛔ بیشتر این ردیف‌ها مال {store.PLATFORM_FA[other[0]]} است ولی داشبورد روی {store.PLATFORM_FA[ws.platform]} است. "
            f"اگر درست است، با `--platform {other[0]}` اجرا کن (یا از کاربر بپرس کدام پلتفرم را می‌خواهد).")
        return 2
    old, dec = ws.board(), ws.decisions()
    requested = ws.benchmark_request().get("status") in ("queued", "running")  # a "new benchmark" request means: start a fresh batch
    if old["ideas"] and dec["ideas"] and not a.new and not requested:
        say("⛔ دسته‌ی قبلی ایده‌ها تصمیم کارفرما دارد. اگر واقعاً دسته‌ی تازه می‌خواهی، با `--new` اجرا کن (قبلی بایگانی می‌شود).")
        return 2
    if old["ideas"]:
        p = store.archive(ws)
        say(f"🗂 دسته‌ی قبلی بایگانی شد: {p}")
    for q in queries:
        ev(ws, "scout", "search", f"جستجو: {q}", query=q)
    req = ws.benchmark_request()
    window = a.max_age or (req.get("max_age") if req.get("status") in ("queued", "running") else None) or scout.MAX_AGE_DAYS
    old_rows = scout.too_old(rows_in, window)
    if old_rows:
        say(f"🗓 {len(old_rows)} مورد قدیمی‌تر از {window // 30} ماه کنار گذاشته شد (عددشون بیشتر از زمانه، نه کیفیت):")
        for r in old_rows[:8]:
            say(f"   · {r.get('title', '')[:50]} — {r.get('posted_on') or ''} ({int(r['age_days'])} روز پیش)")
    rows = scout.rank(rows_in, keep=a.keep, top=a.top, max_age=window)
    no_date = sum(1 for r in rows if r.get("age_days") is None)
    if no_date:
        say(f"⚠ تاریخ انتشار {no_date} مورد معلوم نیست؛ امتیازشون بر اساس بازدید کله و ممکنه قدیمی باشن. اگه می‌شه تاریخشون رو بخون و دوباره ثبت کن.")
    if not rows:
        say("⛔ هیچ ردیف قابل‌استفاده‌ای در فایل نبود (هر ردیف title یا url لازم دارد).")
        return 2
    for r in rows:
        r["id"] = f"i{r['rank']:02d}"
        if r.get("thumb") and not str(r["thumb"]).startswith(("http", "/ws/")):
            r["thumb"] = ws_url(ws, r["thumb"])
    board = {"scan": {"queries": queries, "scanned": len(rows_in), "kept": len(rows), "at": store.now_iso(),
                      "source": source}, "ideas": rows}
    ws.save_board(board)
    if ws.benchmark_request().get("status") == "queued":  # the dashboard's "new benchmark" button: this scan is it
        ws.set_benchmark("running", mode=ws.mode)
    store.write_json(ws.scans_dir / f"scan-{store.now_iso().replace(':', '')}.json", {"queries": queries, "rows": rows})
    used = ws.mark_inbox([r.get("url") for r in rows_in if isinstance(r, dict)])
    if used:
        say(f"📥 {used} لینک از صندوق ریل‌ها (داشبورد) در این دسته بود و «بررسی‌شده» شد.")
    unit = store.UNIT_FA.get(ws.platform, "ویدیو")
    ev(ws, "scout", "summary", f"{len(rows_in)} {unit} بررسی شد؛ {len(rows)} ایده نگه داشته شد", scanned=len(rows_in), kept=len(rows))
    tops = [r for r in rows if r.get("top")]
    ev(ws, "scout", "top", "تاپ ۵: " + "، ".join(r.get("title", "")[:28] for r in tops), ids=[r["id"] for r in tops])
    say(f"✅ {len(rows)} ایده ثبت و مرتب شد (از {len(rows_in)} {unit}). تاپ {len(tops)}:")
    for r in rows[:max(a.top, 10)]:
        star = "★" if r.get("top") else " "
        say(f" {star} {r['id']} #{r['rank']:<2} {r.get('score'):>3} | {r.get('title', '')[:48]} — {r.get('source_page') or ''} | "
            f"👁 {scout.fmt(r.get('views'))} ♥ {scout.fmt(r.get('likes'))} 💬 {scout.fmt(r.get('comments'))} ↗ {scout.fmt(r.get('shares'))}"
            f" · 🗓 {r.get('posted_on') or 'تاریخ نامعلوم'}" + (f" · {scout.fmt(r.get('vpd'))}/روز" if r.get("vpd") else ""))
    missing_kind = [r["id"] for r in rows if not r.get("kind")]
    if missing_kind:
        say(f"ℹ دسته‌ی موشن/ضبط برای {len(missing_kind)} ایده مشخص نیست؛ در فایل QC با `kind` بده.")
    say("قدم بعد: QC تاپ ۵ (modules/3-qc.md).")


def cmd_qc(ws, a):
    items = load_list(a.file, "results")
    if not isinstance(items, list) or not items:
        raise SystemExit("⛔ فایل QC باید فهرستی از نتیجه‌ها باشد: [{id, verdict, ...}]")
    done = apply.apply_qc(ws, items, say)
    say(f"✅ QC {done} ایده ثبت شد. حالا کارفرما روی داشبورد تأیید یا حذف می‌کند. هیچ ایده‌ای حذف نشده.")


def cmd_kind(ws, a):
    if a.kind not in store.KINDS:
        raise SystemExit("⛔ دسته باید motion یا filmed باشد.")
    board = ws.board()
    idea = store.find_idea(board, a.id)
    idea["kind"] = a.kind
    ws.save_board(board)
    ev(ws, "qc", "kind", f"«{idea.get('title', '')[:40]}» ← {KIND_FA[a.kind]}", id=idea["id"])
    say(f"✓ {idea['id']} ← {KIND_FA[a.kind]}")


def cmd_preprod(ws, a):
    data = store.read_json(a.file, None)
    if data is None:
        raise SystemExit(f"⛔ فایل پیدا نشد: {a.file}")
    apply.apply_preprod(ws, a.id, data, say)


def cmd_storyboard(ws, a):
    data = store.read_json(a.file, None)
    if data is None:
        raise SystemExit(f"⛔ فایل پیدا نشد: {a.file}")
    apply.apply_storyboard(ws, a.id, data, say)
    say("   حالا کارفرما روی داشبورد استوری‌بورد را تأیید می‌کند تا وارد مرحله‌ی تولید شود.")


def cmd_status(ws, a):
    board, dec = ws.board(), ws.decisions()
    if a.json:
        out = []
        for i in board["ideas"]:
            out.append({"id": i["id"], "rank": i.get("rank"), "top": i.get("top"), "title": i.get("title"),
                        "production_title": store.production_title(i, dec["ideas"].get(i["id"])),
                        "kind": store.production_kind(i, dec["ideas"].get(i["id"])), "verdict": (i.get("qc") or {}).get("verdict"),
                        "decision": dec["ideas"].get(i["id"]), "storyboard_decision": dec["storyboards"].get(i["id"]),
                        "stage": store.stage_of(i, dec)})
        say(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    say(f"روش بررسی: {store.MODE_FA[ws.mode]}  ·  {bench_line(ws.benchmark_request())}")
    if ws.benchmark_request().get("status") == "queued":
        say("📋 برای همین برند «بنچ‌مارک جدید» در صف است: `bench start`، بعد دور جستجو و QC.")
    if ws.brief() and not ws.brief().get("read"):
        say("📄 ورودی تازه‌ی برند از داشبورد رسیده (`brief`). اول آن را بخوان.")
    new_links = [i for i in ws.inbox() if i.get("status") == "new"]
    if new_links:
        say(f"📥 {len(new_links)} لینک ریل تازه از داشبورد منتظر بررسی است (`inbox`).")
    if not board["ideas"]:
        say("هنوز ایده‌ای ثبت نشده.")
        return 0
    say(f"پلتفرم: {store.PLATFORM_FA[ws.platform]}  ·  پیج رفرنس: {ws.page.get('handle') or ws.page.get('name') or '—'}  ·  {len(board['ideas'])} ایده")
    say("| # | id | ایده | پیج منبع | 👁 | ♥ | 💬 | ↗ | امتیاز | دسته | QC | کارفرما | مرحله |")
    say("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    todo = []
    for i in board["ideas"]:
        d = dec["ideas"].get(i["id"], {})
        st = store.stage_of(i, dec)
        if not (i.get("top") or d or i.get("qc")) and not a.all:
            continue
        say(f"| {i.get('rank')}{'★' if i.get('top') else ''} | {i['id']} | {store.production_title(i, d)[:40]} | {i.get('source_page', '')} | "
            f"{scout.fmt(i.get('views'))} | {scout.fmt(i.get('likes'))} | {scout.fmt(i.get('comments'))} | {scout.fmt(i.get('shares'))} | "
            f"{i.get('score')} | {KIND_FA.get(store.production_kind(i, d))} |{VERDICT_FA.get((i.get('qc') or {}).get('verdict'), '—')} | "
            f"{DECISION_FA.get(d.get('status'))} | {STAGE_FA[st]} |")
        sbd = dec["storyboards"].get(i["id"], {})
        if st == "approved":
            todo.append(f"{i['id']}: سند پیش‌تولید و استوری‌بورد را بساز")
        elif st == "preprod":
            todo.append(f"{i['id']}: استوری‌بورد را بساز")
        elif st == "storyboard" and sbd.get("status") == "revise":
            todo.append(f"{i['id']}: استوری‌بورد را اصلاح کن" + (f" — یادداشت کارفرما: {sbd['note']}" if sbd.get("note") else ""))
        elif i.get("top") and i.get("qc") is None:
            todo.append(f"{i['id']}: QC نشده")
    if not a.all:
        say("(فقط تاپ‌ها و ایده‌های تصمیم‌دار؛ همه: `status --all`)")
    if todo:
        say("\nکارهای بعدی:")
        for t in todo:
            say("  • " + t)


def cmd_decide(ws, a):
    if a.action not in store.IDEA_ACTIONS:
        raise SystemExit(f"⛔ تصمیم باید یکی از این‌ها باشد: {' '.join(store.IDEA_ACTIONS)}")
    board = ws.board()
    idea = store.find_idea(board, a.id)
    if a.action == "approve_alt" and not (idea.get("qc") or {}).get("alternative"):
        raise SystemExit("⛔ این ایده جایگزین ندارد.")
    ws.decide(idea["id"], a.action, by="chat", note=a.note)
    if a.action in ("delete", "restore"):
        ws.clear_storyboard_decision(idea["id"])
    msg = {"approve": "تأیید شد", "approve_alt": "جایگزین تأیید شد", "delete": "از ایده‌های ساخت حذف شد", "restore": "برگشت به صف تصمیم"}[a.action]
    ev(ws, "client", "decision", f"«{idea.get('title', '')[:40]}» {msg} (از چت)", id=idea["id"], action=a.action)
    say(f"✓ {idea['id']}: {msg}")


def cmd_sb(ws, a):
    if a.action not in store.SB_ACTIONS:
        raise SystemExit(f"⛔ تصمیم باید یکی از این‌ها باشد: {' '.join(store.SB_ACTIONS)}")
    board = ws.board()
    idea = store.find_idea(board, a.id)
    if not idea.get("storyboard"):
        raise SystemExit("⛔ این ایده هنوز استوری‌بورد ندارد.")
    ws.decide_storyboard(idea["id"], a.action, by="chat", note=a.note)
    msg = {"approve": "استوری‌بورد تأیید شد ← تولید", "revise": "استوری‌بورد نیاز به اصلاح دارد", "reset": "تصمیم برداشته شد"}[a.action]
    ev(ws, "client", "storyboard", f"«{idea.get('title', '')[:40]}»: {msg} (از چت)", id=idea["id"], action=a.action)
    say(f"✓ {idea['id']}: {msg}")


def cmd_done(ws, a):
    board = ws.board()
    idea = store.find_idea(board, a.id)
    idea["done"] = store.now_iso()
    ws.save_board(board)
    ev(ws, "prod", "done", f"«{idea.get('title', '')[:40]}» ساخته شد", id=idea["id"])
    say(f"✅ {idea['id']} ساخته شد.")


def cmd_log(ws, a):
    if a.agent not in store.AGENTS:
        raise SystemExit(f"⛔ AGENT باید یکی از این‌ها باشد: {' '.join(store.AGENTS)}")
    data = {k: v for k, v in (("query", a.query), ("id", a.id)) if v}
    if a.id:
        try:
            data["id"] = store.find_idea(ws.board(), a.id)["id"]
        except SystemExit:
            pass
    msg = a.msg or a.query or a.type
    ev(ws, a.agent, a.type, msg, **data)
    say(f"✓ ثبت شد: {a.agent}/{a.type} — {msg[:60]}")


def cmd_mode(ws, a):
    if a.name:
        if a.name != ws.mode:
            ws.save_config(mode=a.name)
            ev(ws, "system", "mode", "روش بررسی: " + store.MODE_FA[a.name], mode=a.name)
        say(f"✓ روش بررسی: {store.MODE_FA[a.name]} (داشبورد هم عوض شد)")
    else:
        say(f"روش بررسی: {store.MODE_FA[ws.mode]}")
    if ws.mode == "login":
        say("  مرورگر با حساب خود کاربر یا آژانس لاگین است (نه حساب برند). فقط بخوان؛ خودت هیچ‌وقت لاگین نکن. عددهای کامل‌تر: لایک، کامنت، ری‌پست، اشتراک، جستجو و هشتگ.")
    else:
        say("  بدون لاگین: از سند استراتژی، لینک‌ها، نمونه پست‌ها و توضیح متنی (`brief`)، و صفحه‌های عمومی به‌عنوان بازدیدکننده.")


def cmd_brief(ws, a):
    b = ws.brief()
    if not b:
        say("هنوز از داشبورد ورودی برندی نیامده. (کارفرما در «پیج رفرنس و استراتژی برند» ← «ورودی‌های برند» می‌فرستد.)")
        return 0
    say(f"📄 ورودی برند (از داشبورد، {b.get('at', '')}):")
    if b.get("page_link"):
        say(f"  لینک پیج/کانال: {b['page_link']}")
    for s in b.get("samples") or []:
        say(f"  نمونه پست: {s}")
    if b.get("text"):
        say("  توضیح متنی:\n" + "\n".join("    " + line for line in b["text"].splitlines()))
    for f in b.get("files") or []:
        say(f"  فایل: {f['path']}  ({f.get('size', 0) // 1024} KB)")
    say("همه را بخوان (PDF/Word/عکس با ابزار خودش)، page.json را کامل کن و `page --file` بزن. بعد `brief --done`.")
    if a.done:
        b["read"] = True
        store.write_json(ws.brief_path, b)
        say("✓ علامت «خوانده شد» خورد.")


def cmd_use(ws, a):
    if a.name:
        if a.name != ws.config.get("platform", "instagram"):
            ws.save_config(platform=a.name)
            ev(ws, "system", "platform", f"پلتفرم: {store.PLATFORM_FA[a.name]}", platform=a.name)
        say(f"✓ پلتفرم: {store.PLATFORM_FA[a.name]} (داشبورد هم عوض شد)")
    else:
        say(f"پلتفرم فعلی: {store.PLATFORM_FA[ws.platform]}")
    for p in store.PLATFORMS:
        s = ws.for_platform(p).summary()
        say(f"  {store.PLATFORM_FA[p]}: {s['ideas']} ایده، {s['approved']} تأییدشده")


def cmd_inbox(ws, a):
    items = ws.inbox()
    if a.done:
        n = ws.mark_inbox(a.done, "done")
        say(f"✓ {n} لینک «بررسی‌شده» شد.")
        return 0
    if a.skip:
        n = ws.mark_inbox(a.skip, "skipped")
        say(f"✓ {n} لینک کنار گذاشته شد.")
        return 0
    show = items if a.all else [i for i in items if i.get("status") == "new"]
    if not show:
        say("صندوق ریل‌ها خالی است." if not items else "لینک تازه‌ای نیست (همه: `inbox --all`).")
        return 0
    say(f"📥 {len(show)} لینک ریل (از داشبورد):")
    for i in show:
        say(f"  [{i['id']}] {i['url']}  ·  {i.get('status')}" + (f"  ·  یادداشت: {i['note']}" if i.get("note") else ""))
    say("این لینک‌ها را هم مثل بقیه بخوان (بدون لاگین) و در فایل scout بگذار؛ `scout --import` خودش علامتشان می‌زند.")


def cmd_dashboard(ws, a):
    def ready(url):
        full = url + (f"?theme={a.theme}" if a.theme else "")
        ws.save_config(dashboard=full)
        say(f"📺 داشبورد زنده: {full}")
        say("   تا وقتی این فرمان در حال اجراست داشبورد کار می‌کند. برای بستن: Ctrl+C")
        flush_last(ws)
        if a.open:
            webbrowser.open(full)

    server.serve(a.lab, a.port, ready)


def app_browser():
    """Edge or Chrome, the ones every Windows PC has; they can open a window without browser bars (app mode)"""
    found = shutil.which("msedge") or shutil.which("chrome") or shutil.which("google-chrome")
    if found:
        return found
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"), os.environ.get("LOCALAPPDATA")):
        if not base:
            continue
        for rel in (r"Microsoft\Edge\Application\msedge.exe", r"Google\Chrome\Application\chrome.exe"):
            p = Path(base) / rel
            if p.exists():
                return str(p)
    return None


def cmd_app(ws, a):
    """the dashboard as its own window: no tabs or address bar. Closing the window stops the program.
    Runs on this computer only."""
    urls = {}

    def ready(url):
        urls["url"] = url
        ws.save_config(dashboard=url)

    srv = server.serve(ws, a.port, ready, block=False)
    url = urls["url"]
    say(f"🖥 برنامه‌ی داشبورد: {url}")
    flush_last(ws)
    browser = app_browser()
    try:
        if browser:
            profile = store.HOME / "app-window"   # its own profile: the window never mixes with your normal browser
            profile.mkdir(parents=True, exist_ok=True)
            proc = subprocess.Popen([browser, f"--app={url}", f"--user-data-dir={profile}", "--no-first-run",
                                     "--window-size=1400,900"])
            say("پنجره‌ی برنامه باز شد. برای بستن برنامه همان پنجره را ببند.")
            proc.wait()
        else:
            webbrowser.open(url)
            say("⚠ Edge یا Chrome پیدا نشد؛ داشبورد توی مرورگر معمولی باز شد. برای بستن این پنجره: Ctrl+C")
            while True:
                time.sleep(3600)
    finally:
        srv.shutdown()
        srv.server_close()
    return 0


def bench_line(b):
    st = (b or {}).get("status")
    if not st:
        return "بنچ‌مارک: هنوز درخواستی نیست"
    fa_ = {"queued": "در صف", "running": "در حال انجام", "done": "انجام شد", "cancelled": "لغو شد"}.get(st, st)
    when = b.get(f"{st}_at", "")
    extra = f" · {store.PLATFORM_FA.get(b.get('platform'), '')}" if b.get("platform") else ""
    return f"بنچ‌مارک: {fa_} ({when}){extra}"


def cmd_brands(ws, a):
    lab = a.lab
    items = store.list_brands(lab)
    if not items:
        say("هنوز برندی ثبت نشده. `brand add \"اسم برند\"` یا دکمه‌ی «+ برند» روی داشبورد.")
        return 0
    active = store.brand_ws(lab)[1]
    say(f"{len(items)} برند:")
    for b in items:
        w = store.Workspace((lab.root / b["path"]).resolve())
        s = {p: w.for_platform(p).summary() for p in store.PLATFORMS}
        mark = "▶" if active and b["id"] == active["id"] else " "
        counts = "، ".join(f"{store.PLATFORM_FA[p]} {s[p]['ideas']} ایده" for p in store.PLATFORMS)
        gone = "  (پنهان؛ با brand use برمی‌گرده)" if b.get("hidden") else ""
        say(f" {mark} {b['id']:<5} {b['name']}{gone}  ·  {counts}  ·  {bench_line(w.benchmark_request())}")


def cmd_brand(ws, a):
    lab = a.lab
    if a.action == "add":
        if not a.name:
            raise SystemExit("⛔ اسم برند را بده: brand add \"اسم\"")
        nws, it = store.add_brand(lab, a.name, url=a.link if a.link and "instagram.com" in a.link else "",
                                  handle=store.handle_from_url(a.link), youtube=a.youtube or "", linkedin=a.linkedin or "", niche=a.niche or "")
        store.use_brand(lab, it["id"])
        ev(nws, "system", "brand", f"برند تازه اضافه شد: {a.name}", brand=it["id"])
        say(f"✅ برند «{a.name}» با شناسه‌ی {it['id']} ساخته و انتخاب شد: {nws.root}")
        say("قدم بعد: پروفایل و استراتژی همین برند (modules/1-reference-page.md)، با `--brand " + it["id"] + "` یا همین برندِ انتخاب‌شده.")
    elif a.action == "use":
        it = store.use_brand(lab, a.name)
        bws = store.brand_ws(lab)[0]
        ev(bws, "system", "brand", f"برند: {it['name']}", brand=it["id"])
        say(f"✓ برند فعال: {it['name']} ({it['id']}) — داشبورد هم عوض شد")
    elif a.action == "remove":
        if not a.name:
            raise SystemExit("⛔ شناسه‌ی برند را بده: brand remove ID (فهرست: brands)")
        it, dst, active = store.remove_brand(lab, a.name)
        bws = store.brand_ws(lab)[0]
        how = "پوشه‌ش بایگانی شد" if dst else "داده‌هاش سر جاشه، فقط پنهان شد"
        ev(bws, "system", "brand", f"برند «{it['name']}» از فهرست برداشته شد ({how})", brand=it["id"])
        if dst:
            say(f"✓ برند «{it['name']}» ({it['id']}) از فهرست برداشته شد. چیزی پاک نشد؛ پوشه‌ش رفت توی بایگانی: {dst}")
        else:
            say(f"✓ برند «{it['name']}» ({it['id']}) از فهرست پنهان شد. داده‌هاش سر جای خودشه؛ با `brand use {it['id']}` برمی‌گرده.")
        say(f"   برند فعال حالا: {active or '—'}")
    else:
        raise SystemExit("⛔ brand add \"اسم\" | brand use ID | brand remove ID")


def cmd_requests(ws, a):
    lab = a.lab
    q = []
    for b in store.list_brands(lab) or [{"id": "main", "name": lab.page.get("name") or "برند اصلی", "path": "."}]:
        w = store.Workspace((lab.root / b["path"]).resolve())
        for pl, r in w.benchmarks().items():
            if r.get("status") in ("queued", "running"):
                q.append((b, pl, r))
    if not q:
        say("صف بنچ‌مارک خالی است.")
        return 0
    say(f"📋 {len(q)} درخواست بنچ‌مارک (هر پلتفرم جدا):")
    for b, pl, r in q:
        say(f"  {b['id']:<9} {b['name']}  ·  {store.PLATFORM_FA[pl]}  ·  {bench_line(r)}  ·  پیج‌ها: {store.REGION_FA.get(r.get('region') or 'both')}"
            f"  ·  بازه: {store.WINDOW_FA.get(r.get('max_age') or 180, str(r.get('max_age')) + ' روز')}  ·  روش: {store.MODE_FA.get(r.get('mode'), '—')}")
    say("برای هر ردیف: `bench start --brand ID --platform P` ← دور جستجو، امتیاز، QC (با همان --brand و --platform؛ پیج‌ها طبق «پیج‌ها») ← `bench done --brand ID --platform P`.")


def cmd_bench(ws, a):
    if a.action == "request":
        cur = ws.benchmark_request().get("status")
        if cur in ("queued", "running"):
            say(f"ℹ از قبل {bench_line(ws.benchmark_request())}")
            return 0
        ws.set_benchmark("queued", mode=ws.mode, region=a.region or "both", max_age=a.max_age or 180, by="chat")
        ev(ws, "client", "benchmark", f"درخواست بنچ‌مارک جدید ({store.PLATFORM_FA[ws.platform]} · {store.REGION_FA[a.region or 'both']}) در صف")
    elif a.action == "start":
        ws.set_benchmark("running", platform=ws.platform, mode=ws.mode)
        ev(ws, "scout", "benchmark", f"Claude بنچ‌مارک جدید رو شروع کرد ({store.PLATFORM_FA[ws.platform]})")
    elif a.action == "done":
        ws.set_benchmark("done")
        ev(ws, "scout", "benchmark", "بنچ‌مارک تموم شد؛ ایده‌ها و QC روی داشبورد")
    elif a.action == "cancel":
        ws.set_benchmark("cancelled")
        ev(ws, "system", "benchmark", "درخواست بنچ‌مارک لغو شد")
    say(f"✓ {bench_line(ws.benchmark_request())}")
    url = a.lab.config.get("online_url")
    if url and a.action in ("start", "done"):   # tell the online dashboard, so the client sees Claude working
        bid = (store.brand_ws(a.lab, a.brand)[1] or {}).get("id") or "main"
        doc_id = f"{bid}~{ws.platform}"
        msg = {"start": f"Claude بنچ‌مارک «{ws.page.get('name') or bid}» رو شروع کرد ({store.PLATFORM_FA[ws.platform]})",
               "done": "بنچ‌مارک تموم شد؛ ایده‌ها و QC اومد"}[a.action]
        doc = {"brand": bid, "platform": ws.platform, "benchmark": {"status": "running" if a.action == "start" else "done", "platform": ws.platform,
                                           "at": store.now_iso_z(), "msg": msg}}
        out = next_version(a.lab.hidden / "online-out", f"status-{bid}-{ws.platform}", ".json")
        store.write_json(out, doc)
        say(f"روی داشبورد آنلاین نشونش بده: ArtifactData با url={url}، collection «status»، doc_id «{doc_id}»: "
            f"اول get (اگه بود، version رو بردار)، بعد set با file_path «{out}» (و if_version اگه سند از قبل بود).")


def cmd_demo(ws, a):
    dws = store.Workspace(ws.root / ".lab" / "demo")
    demo.run(dws, speed=a.speed, auto=a.auto, port=a.port, serve=not a.no_serve, open_browser=a.open, say=say,
             flush=lambda: flush_last(ws))


def next_version(folder, stem, ext):
    """files are never overwritten: <stem>_v1, _v2, …"""
    folder.mkdir(parents=True, exist_ok=True)
    n = 1
    while (folder / f"{stem}_v{n}{ext}").exists():
        n += 1
    return folder / f"{stem}_v{n}{ext}"


def cmd_export(ws, a):
    lab = store.Workspace(ws.root / ".lab" / "demo") if a.demo else ws
    if a.demo and not lab.exists():
        raise SystemExit("⛔ نمونه هنوز ساخته نشده: اول `demo --no-serve --auto --speed 80` را بزن.")
    out = a.out or next_version(ws.root / "online", "dashboard-demo" if a.demo else "dashboard", ".html")
    path = export.write(lab, out, demo=a.demo)
    say(f"✅ داشبورد آنلاین ساخته شد: {path}  ({path.stat().st_size // 1024} کیلوبایت)")
    url = ws.config.get("online_url") if not a.demo else None
    caps = '{"db": {}, "user": {}, "assets": {"upload": "interact"}}'
    if url:
        say(f"منتشر کن روی همون آدرس: Artifact با file_path همین فایل و url={url} (capabilities رو نفرست، همون قبلی می‌مونه).")
    else:
        say(f"منتشر کن: Artifact با file_path همین فایل، icon \"dashboard\" و capabilities {caps}؛ بعد آدرس رو با `online --url` ثبت کن.")
    say("اگه ابزار Artifact نداری: همین فایل رو بده؛ هر جا باز می‌شه و تصمیم‌ها با «پیام برای Claude» برمی‌گرده.")


def cmd_online(ws, a):
    if a.url:
        if not str(a.url).startswith("https://claude.ai/"):
            raise SystemExit("⛔ آدرس Artifact باید با https://claude.ai/ شروع بشه.")
        ws.save_config(online_url=a.url)
        say(f"✓ داشبورد آنلاین این پوشه: {a.url}")
        return 0
    url = ws.config.get("online_url")
    say(f"داشبورد آنلاین: {url}" if url else "هنوز داشبورد آنلاینی ثبت نشده (`export` بعد انتشار، بعد `online --url`).")
    if url:
        say(f"خوندن کارهای کارفرما: ArtifactData list با url={url}، collection «actions»، query.limit 1000، out_dir «{ws.hidden / 'online-in'}»؛ بعد `import-pack --dir \"{ws.hidden / 'online-in' / 'actions'}\"`، بعد export و انتشار روی همین آدرس.")


def cmd_import_pack(ws, a):
    if a.dir:
        pack = export.load_dir(a.dir)
    else:
        text = Path(a.file).read_text(encoding="utf-8") if a.file else ""
        pack = apply.extract_json(text)
    if not isinstance(pack, dict) or "items" not in pack:
        raise SystemExit("⛔ کار کارفرما پیدا نشد (پوشه‌ی actions یا متن ILAB-PACK).")
    ledger = dict(ws.config.get("online_applied") or {})
    applied, files = export.apply_pack(ws, pack, say, ledger)
    ws.save_config(online_applied=ledger)
    say(f"✅ {len(applied)} مورد اعمال شد." + ("" if applied else " (چیز تازه‌ای نبود؛ قبلی‌ها یک بار اعمال شده‌اند)"))
    for f in files:
        say(f"📎 فایل برند «{f['name']}» (برند {f['brand'] or 'main'}): با Artifact read، path={f['asset']} بگیرش، بعد `page --doc <فایل> --brand {f['brand'] or 'main'}`.")
    if applied:
        say("قدم بعد: `status` (کارهای بعدی)، برای تأییدشده‌ها پیش‌تولید و استوری‌بورد بساز، بعد `export` و انتشار روی همون آدرس.")


def cmd_reset(ws, a):
    p = store.archive(ws)
    say(f"🧹 داشبورد خالی شد. ایده‌ها، تصمیم‌ها و گزارش قبلی بایگانی شد: {p}" if p else "داشبورد از قبل خالی بود.")


HANDLERS = {"init": cmd_init, "doctor": cmd_doctor, "page": cmd_page, "scout": cmd_scout, "qc": cmd_qc, "kind": cmd_kind,
            "preprod": cmd_preprod, "storyboard": cmd_storyboard, "status": cmd_status, "decide": cmd_decide, "sb": cmd_sb,
            "done": cmd_done, "log": cmd_log, "dashboard": cmd_dashboard, "demo": cmd_demo, "reset": cmd_reset, "inbox": cmd_inbox,
            "use": cmd_use, "mode": cmd_mode, "brief": cmd_brief, "brands": cmd_brands, "brand": cmd_brand,
            "requests": cmd_requests, "bench": cmd_bench, "app": cmd_app, "export": cmd_export, "online": cmd_online, "import-pack": cmd_import_pack}
LAB_COMMANDS = ("init", "dashboard", "app", "demo", "brands", "brand", "requests", "export", "online", "import-pack")


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--work", help="پوشه‌ی کار (پیش‌فرض: همان که init ساخته)")
    common.add_argument("--platform", choices=store.PLATFORMS, help="پیش‌فرض: همان که روی داشبورد انتخاب شده")
    common.add_argument("--brand", help="شناسه یا اسم برند (پیش‌فرض: برندی که روی داشبورد انتخاب شده)")
    p = argparse.ArgumentParser(prog="run.py", description=brand.NAME)
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name):
        return sub.add_parser(name, parents=[common])

    add("init")
    add("doctor")
    s = add("page")
    s.add_argument("--file")
    s.add_argument("--doc", help="سند استراتژی برند (pdf, docx, md, txt…) که کنار پروژه نگه داشته می‌شود")
    s = add("use")
    s.add_argument("name", nargs="?", choices=store.PLATFORMS)
    s = add("mode")
    s.add_argument("name", nargs="?", choices=store.MODES)
    add("brands")
    s = add("brand")
    s.add_argument("action", choices=("add", "use", "remove"))
    s.add_argument("name", nargs="?")
    s.add_argument("--link", help="لینک پیج اینستاگرام")
    s.add_argument("--youtube", help="لینک کانال یوتیوب")
    s.add_argument("--linkedin", help="لینک پیج یا پروفایل لینکدین")
    s.add_argument("--niche", help="زمینه‌ی کاری")
    add("requests")
    s = add("bench")
    s.add_argument("action", choices=("request", "start", "done", "cancel"))
    s.add_argument("--region", choices=store.REGIONS, help="پیج‌های ایرانی، خارجی یا هر دو (فقط برای request)")
    s.add_argument("--max-age", type=int, choices=store.WINDOWS, help="بازه‌ی زمانی به روز (فقط برای request؛ پیش‌فرض ۱۸۰)")
    s = add("brief")
    s.add_argument("--done", action="store_true")
    s = add("inbox")
    s.add_argument("--all", action="store_true")
    s.add_argument("--done", action="append", help="لینکی که بررسی شد")
    s.add_argument("--skip", action="append", help="لینکی که به کار نمی‌آید")
    s = add("scout")
    s.add_argument("--import", dest="import_file")
    s.add_argument("--raw", help="خط‌های فشرده‌ی مرورگر: id;;title;;channel;;views;;age;;likes;;subs")
    s.add_argument("--meta", help="JSON کوچک: {id: {title, hook, summary, kind, region}} (فقط همین شناسه‌ها نگه داشته می‌شوند)")
    s.add_argument("--keep", type=int, default=20)
    s.add_argument("--top", type=int, default=5)
    s.add_argument("--max-age", type=int, help="روزهای قبل (پیش‌فرض ۱۸۰ = ۶ ماه؛ بیشتر فقط وقتی کاربر خودش خواست)")
    s.add_argument("--new", action="store_true")
    s = add("qc")
    s.add_argument("--file", required=True)
    s = add("kind")
    s.add_argument("id")
    s.add_argument("kind")
    for name in ("preprod", "storyboard"):
        s = add(name)
        s.add_argument("id")
        s.add_argument("--file", required=True)
    s = add("status")
    s.add_argument("--json", action="store_true")
    s.add_argument("--all", action="store_true")
    for name in ("decide", "sb"):
        s = add(name)
        s.add_argument("id")
        s.add_argument("action")
        s.add_argument("--note")
    s = add("done")
    s.add_argument("id")
    s = add("log")
    s.add_argument("agent")
    s.add_argument("type")
    s.add_argument("--msg")
    s.add_argument("--query")
    s.add_argument("--id", help="شناسه یا رتبه‌ی ایده (برای qc و prod)")
    s = add("app")
    s.add_argument("--port", type=int, default=8770)
    s = add("dashboard")
    s.add_argument("--port", type=int, default=8770)
    s.add_argument("--open", action="store_true")
    s.add_argument("--theme", choices=("dark", "light"))
    s = add("demo")
    s.add_argument("--speed", type=float, default=1.0)
    s.add_argument("--auto", action="store_true", help="تصمیم‌های کارفرما را هم نمایشی بزن (برای پیش‌نمایش کامل)")
    s.add_argument("--port", type=int, default=8771)
    s.add_argument("--open", action="store_true")
    s.add_argument("--no-serve", action="store_true", help="فقط داده‌ی نمونه را بنویس، سرور را بالا نیاور")
    s = add("export")
    s.add_argument("--out", help="مسیر فایل خروجی .html")
    s.add_argument("--demo", action="store_true", help="از داده‌ی نمونه (اول demo --no-serve)")
    s = add("online")
    s.add_argument("--url", help="آدرس Artifact داشبورد آنلاین")
    s = add("import-pack")
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--dir", help="پوشه‌ای که ArtifactData با out_dir از collection «actions» ساخته")
    g.add_argument("--file", help="فایلی که متن «پیام برای Claude» داخلشه")
    add("reset")
    return p


def main(argv):
    if not argv or argv[0] in ("help", "-h", "--help"):
        say(brand.banner())
        say(HELP)
        return 0
    a = build_parser().parse_args(argv)
    lab = store.resolve(a.work, a.platform)   # the work folder; with several brands, each brand is its own workspace in it
    a.lab = lab
    ws = lab
    rc = 0
    try:
        if a.cmd != "doctor":
            lab.ensure()
        if a.cmd not in LAB_COMMANDS:
            ws, info = store.brand_ws(lab, a.brand, a.platform)
            if info and (a.brand or len(store.list_brands(lab)) > 1) and a.cmd not in ("status", "doctor"):
                say(f"برند: {info['name']} ({info['id']})")
            if a.cmd != "doctor":
                ws.ensure()
        rc = HANDLERS[a.cmd](ws, a) or 0
    except SystemExit as e:
        if isinstance(e.code, str):
            say(e.code)
            rc = 1
        else:
            rc = e.code or 0
    except KeyboardInterrupt:
        rc = 130
    finally:
        flush_last(lab)
    return rc
