# Social Idea Lab by Tarfandhaye.ai — © 2026 Tarfandhaye.ai — All rights reserved. Personal use only; see LICENSE.md.
"""Turns what Claude read from Instagram / YouTube / LinkedIn into numbers, scores every idea and picks the top 5 (standard library only).
The score is relative to the batch: views 35%, engagement 30%, share rate 20%, reach beyond the page's size 15%.
Age counts: a video older than MAX_AGE_DAYS is left out, and views are scored per day since posting (with reach per day), so an
old video does not win only because it has had more time to collect views."""
import json
import math
import re
from datetime import datetime, timedelta, timezone

FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٫٬", "01234567890123456789.,")
UNITS = {"k": 1e3, "m": 1e6, "b": 1e9, "هزار": 1e3, "میلیون": 1e6, "میلیارد": 1e9, "هزارتا": 1e3, "th": 1e3}
WEIGHTS = {"views": 0.35, "er": 0.30, "share_rate": 0.20, "reach": 0.15}
MAX_AGE_DAYS = 180   # about 6 months: older videos are not benchmarks of what works now
MIN_DAYS = 7         # a brand-new video is counted as a week old for views per day
PLATFORMS = ("instagram", "youtube", "linkedin", "tiktok", "other")


def parse_count(v):
    """'1.2M' '۱۲ هزار' '12,400' '3.4k views' 1200 → int; anything unreadable → None"""
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v).translate(FA_DIGITS).strip().lower()
    m = re.search(r"(\d+(?:[.,]\d+)*)\s*(k|m|b|هزارتا|هزار|میلیون|میلیارد|th)?", s)
    if not m:
        return None
    num, unit = m.group(1), m.group(2)
    if unit:
        num = num.replace(",", ".") if num.count(",") == 1 and "." not in num else num.replace(",", "")
        try:
            return int(float(num) * UNITS[unit])
        except ValueError:
            return None
    try:
        return int(float(num.replace(",", "")))
    except ValueError:
        return None


def parse_age(row):
    """age_days, or an 'age' like '3 days ago' / '۲ هفته پیش' / '5d' / '2w', or a 'posted' ISO date"""
    if row.get("age_days") not in (None, ""):
        try:
            return max(0.5, float(str(row["age_days"]).translate(FA_DIGITS)))
        except ValueError:
            pass
    posted = row.get("posted") or row.get("published")
    if posted:
        try:
            t = datetime.fromisoformat(str(posted).replace("Z", "+00:00"))
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            return max(0.5, (datetime.now(timezone.utc) - t).total_seconds() / 86400)
        except ValueError:
            pass
    age = str(row.get("age") or "").translate(FA_DIGITS).lower()
    m = re.search(r"(\d+(?:\.\d+)?)\s*(h|hour|ساعت|d|day|روز|w|week|هفته|mo|month|ماه|y|year|سال)", age)
    if not m:
        return None
    n = float(m.group(1))
    u = m.group(2)
    mult = 1 / 24 if u in ("h", "hour", "ساعت") else 7 if u in ("w", "week", "هفته") else \
        30 if u in ("mo", "month", "ماه") else 365 if u in ("y", "year", "سال") else 1
    return max(0.5, n * mult)


def platform_of(row):
    p = str(row.get("platform") or "").lower()
    if p in PLATFORMS:
        return p
    url = str(row.get("url") or "")
    if "instagram.com" in url:
        return "instagram"
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    if "linkedin.com" in url or "lnkd.in" in url:
        return "linkedin"
    if "tiktok.com" in url:
        return "tiktok"
    return "other"


def clean_row(r):
    out = dict(r)
    for k in ("views", "likes", "comments", "shares", "saves", "followers"):
        out[k] = parse_count(r.get(k))
    # LinkedIn words: reactions = likes, reposts = shares
    if out["likes"] is None and r.get("reactions") not in (None, ""):
        out["likes"] = parse_count(r.get("reactions"))
    if out["shares"] is None and r.get("reposts") not in (None, ""):
        out["shares"] = parse_count(r.get("reposts"))
    rg = str(r.get("region") or "").lower()   # source page: ir (Iranian / Persian) or intl (foreign)
    out["region"] = rg if rg in ("ir", "intl") else None
    rv = str(r.get("read_via") or "").lower()   # how the numbers were read: page | grid | screenshot | search | user
    out["read_via"] = rv if rv in ("page", "grid", "screenshot", "search", "user") else None
    out["age_days"] = parse_age(r)
    posted = str(r.get("posted") or r.get("published") or "")[:10]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", posted):
        out["posted_on"] = posted
    elif out["age_days"] is not None:
        out["posted_on"] = (datetime.now(timezone.utc) - timedelta(days=out["age_days"])).strftime("%Y-%m-%d")
    else:
        out["posted_on"] = None
    out["platform"] = platform_of(r)
    src = str(r.get("source_page") or r.get("page") or r.get("channel") or "").strip()
    out["source_page"] = src if (not src or src.startswith("@") or " " in src or out["platform"] != "instagram") else "@" + src
    kind = str(r.get("kind") or "").lower()
    out["kind"] = kind if kind in ("motion", "filmed") else None
    fmt_ = str(r.get("format") or "").lower()
    url = str(r.get("url") or "")
    if fmt_ not in ("short", "long"):
        fmt_ = "long" if (out["platform"] == "youtube" and "/shorts/" not in url and not r.get("is_short")) else "short"
    out["format"] = fmt_
    v = out["views"]
    if v:
        eng = (out["likes"] or 0) + 2 * (out["comments"] or 0) + 3 * (out["shares"] or 0) + 2 * (out["saves"] or 0)
        out["er"] = round(eng / v * 100, 2)
        out["share_rate"] = round(out["shares"] / v * 100, 2) if out["shares"] is not None else None
        # views per day, counting at least a week: a video gets most views in its first days, so 1 day old ≠ 1 day of its normal pace
        out["vpd"] = int(v / max(out["age_days"], MIN_DAYS)) if out["age_days"] else None
        out["reach"] = round(v / out["followers"], 1) if out["followers"] else None
    else:
        out["er"] = out["share_rate"] = out["vpd"] = out["reach"] = None
    return out


def _pct(values):
    """percentile rank 0..1 of each value inside the batch (None stays None)"""
    known = sorted(x for x in values if x is not None)
    n = len(known)
    out = []
    for x in values:
        if x is None or n < 2:
            out.append(None if x is None else 0.5)
            continue
        lo = sum(1 for y in known if y < x)
        eq = sum(1 for y in known if y == x)
        out.append((lo + (eq - 1) / 2) / (n - 1))
    return out


SIGNAL_FA = {"views": "بازدید روزانه‌ی بالا", "er": "تعامل بالا", "share_rate": "اشتراک‌گذاری زیاد", "reach": "بیشتر از اندازه‌ی پیجش دیده شده"}


def too_old(rows, max_age=MAX_AGE_DAYS):
    """rows posted more than max_age days ago (unknown age is kept: say so on the dashboard instead)"""
    return [r for r in (clean_row(x) for x in rows if isinstance(x, dict)) if r.get("age_days") is not None and r["age_days"] > max_age]


def rank(rows, keep=20, top=5, max_age=MAX_AGE_DAYS):
    """score 0..100 relative to the batch, keep the best `keep`, mark the best `top`"""
    rows = [clean_row(r) for r in rows if r.get("title") or r.get("url")]
    rows = [r for r in rows if r.get("age_days") is None or r["age_days"] <= max_age]
    if not rows:
        return []
    def volume(r):
        s = (r.get("likes") or 0) + 2 * (r.get("comments") or 0) + 3 * (r.get("shares") or 0)
        return s or None

    any_views = any(r.get("views") for r in rows)
    per_day = sum(1 for r in rows if r.get("vpd")) * 2 >= sum(1 for r in rows if r.get("views"))   # most rows have a date
    if any_views and per_day:   # views per day since posting: old videos don't win on time alone
        views_col = [math.log10(r["vpd"]) if r.get("vpd") else None for r in rows]
        reach_col = [math.log10(r["vpd"] / r["followers"] * 1000) if r.get("vpd") and r.get("followers") else None for r in rows]
    elif any_views:
        views_col = [math.log10(r["views"]) if r.get("views") else None for r in rows]
        reach_col = [r.get("reach") if r.get("reach") is not None else (math.log10(r["vpd"]) if r.get("vpd") else None) for r in rows]
    else:  # no views visible at all (e.g. Instagram without the Reels grid): engagement volume stands in, relative to the source's size
        views_col = [math.log10(volume(r)) if volume(r) else None for r in rows]
        reach_col = [round(volume(r) / r["followers"], 3) if volume(r) and r.get("followers") else None for r in rows]
    cols = {
        "views": _pct(views_col),
        "er": _pct([r.get("er") for r in rows]),
        "share_rate": _pct([r.get("share_rate") for r in rows]),
        "reach": _pct(reach_col),
    }
    for i, r in enumerate(rows):
        total = wsum = 0.0
        best, best_v = None, -1
        for k, w in WEIGHTS.items():
            p = cols[k][i]
            if p is None:
                continue
            total += w * p
            wsum += w
            if p > best_v:
                best, best_v = k, p
        r["score"] = round(100 * total / wsum) if wsum else 0
        r["signal"] = (SIGNAL_FA.get(best) if any_views or best != "views" else "تعامل زیاد") if best and best_v >= 0.6 else None
    rows.sort(key=lambda r: (r["score"], r.get("views") or 0), reverse=True)
    rows = rows[:keep]
    for n, r in enumerate(rows, 1):
        r["rank"] = n
        r["top"] = n <= top
    return rows


RAW_SEP = ";;"
META_KEYS = ("title", "hook", "summary", "kind", "region", "format", "thumb")


def _raw_lines(text):
    """the browser's output as Claude saved it: plain lines, or a JSON string / list of strings"""
    s = (text or "").strip().lstrip("﻿")
    if s[:1] in ('"', "["):
        try:
            v = json.loads(s)
            s = "\n".join(v) if isinstance(v, list) else str(v)
        except ValueError:
            pass
    return [ln.strip() for ln in s.replace("\\n", "\n").splitlines() if ln.strip()]


def rows_from_raw(text, meta=None, platform="youtube"):
    """Compact lines from the browser (`id;;title;;channel;;views;;age[;;likes;;subs]`, `s/ID` = a Short)
    + a small meta {id: {title (Persian), hook, summary, kind, region}} → normal scan rows. Numbers are never retyped.
    Lines starting with `= ` are meta in line form: `= id;;title;;hook;;summary;;kind;;region`.
    When meta names ids, only those ids are kept (Claude's pick after dropping ads and duplicates).
    Returns (rows, queries, dropped, missing_meta_ids)."""
    meta = dict(meta or {})
    queries = []
    if isinstance(meta.get("ideas"), dict):
        queries = list(meta.get("queries") or [])
        meta = meta["ideas"]
    found, order = {}, []
    for ln in _raw_lines(text):
        if ln.startswith("#"):
            q = re.match(r"#\s*(?:q|query)\s*:\s*(.+)", ln, re.I)
            if q:
                queries.append(q.group(1).strip())
            continue
        if ln.startswith("="):
            f = [x.strip() for x in ln[1:].split(RAW_SEP)]
            meta.setdefault(f[0], {}).update({k: v for k, v in zip(("title", "hook", "summary", "kind", "region"), f[1:]) if v})
            continue
        f = [x.strip() for x in ln.split(RAW_SEP)]
        if len(f) < 4 or not f[0]:
            continue
        f += [""] * (7 - len(f))
        rid, short = f[0], False
        if rid.startswith("s/"):
            rid, short = rid[2:], True
        cur = found.get(rid)
        if cur is None:
            cur = found[rid] = {"src_title": f[1], "channel": f[2], "views": f[3], "age": f[4], "likes": f[5], "subs": f[6], "short": short}
            order.append(rid)
        else:  # the same video from two searches: keep what is filled
            for k, v in (("likes", f[5]), ("subs", f[6]), ("age", f[4]), ("views", f[3])):
                if v and not cur.get(k):
                    cur[k] = v
    keep = [i for i in order if i in meta] if meta else order
    rows = []
    for rid in keep:
        x, m = found[rid], meta.get(rid) or {}
        if rid.startswith("http"):
            url = rid
        elif platform == "youtube":
            url = f"https://www.youtube.com/shorts/{rid}" if x["short"] else f"https://www.youtube.com/watch?v={rid}"
        else:
            url = rid
        row = {"title": m.get("title") or x["src_title"], "source_title": x["src_title"], "url": url, "platform": platform,
               "source_page": x["channel"] or None, "views": x["views"] or None, "age": x["age"] or None,
               "likes": x["likes"] or None, "followers": x["subs"] or None, "shares": None,
               "read_via": "page" if (x["likes"] or x["subs"]) else "grid"}
        for k in META_KEYS:
            if m.get(k) and k != "title":
                row[k] = m[k]
        rows.append(row)
    missing = [i for i in meta if i not in found]
    return rows, queries, len(order) - len(keep), missing


def fmt(n):
    if n is None:
        return "—"
    n = float(n)
    for div, unit in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(n) >= div:
            v = n / div
            return (f"{v:.1f}".rstrip("0").rstrip(".") if v < 100 else f"{v:.0f}") + unit
    return f"{int(n)}"
