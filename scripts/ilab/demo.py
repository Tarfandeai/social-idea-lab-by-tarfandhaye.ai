# Social Idea Lab by Tarfandhaye.ai — © 2026 Tarfandhaye.ai — All rights reserved. Personal use only; see LICENSE.md.
"""Sample run for previewing and recording the dashboard. It works in its own folder (<work>/.lab/demo) and never touches
real work. Every page, number and handle here is made up; the dashboard shows a DEMO badge."""
import shutil
import time
import webbrowser

from . import scout, server, store

PAGE = {
    "handle": "@roast.demo", "name": "کافه رُست (نمونه)", "followers": 18400, "niche": "کافه و قهوه‌ی تخصصی",
    "audience": "۲۰ تا ۳۵ ساله‌های شهری، اهل کافه‌گردی و قهوه‌ی خونگی", "language": "fa",
    "tone": "گرم، صمیمی، کمی شوخ؛ آموزش ساده بدون پز دادن",
    "pillars": ["دم‌آوری قهوه", "پشت صحنه‌ی کافه", "منوی فصل", "فرهنگ قهوه"],
    "visual": {"palette": ["#3B2A20", "#C8A27A", "#F3E9DC", "#6B8F71"], "style": "مینیمال گرم؛ نور طبیعی پنجره، چوب و سرامیک",
               "fonts": "تیتر دست‌نویس + متن سنس", "look": "آرام و دنج، بدون نئون و رنگ تند"},
    "production": {"can_film": True, "on_camera": "باریستا، فقط دست‌ها و نیم‌رخ (بدون چهره‌ی کامل)", "location": "خود کافه، بار کنار پنجره",
                   "equipment": "موبایل + سه‌پایه + یک نور LED", "motion_skills": "موشن ساده (CapCut / Claude)"},
    "dont": ["رقص ترند", "طنز تند و پرنک", "رنگ نئونی", "ادعای قیمت"],
    "keywords": ["قهوه تخصصی", "دم‌آوری", "latte art", "coffee tips"], "hashtags": ["#قهوه_تخصصی", "#coffeetok"],
    "client": "مدیر کافه (نمونه)",
    "url": "",
    "youtube": {"channel": "@roast.demo", "url": "", "subscribers": 2300},
    "linkedin": {"page": "Roast Café (نمونه)", "url": "", "followers": 640},
    "strategy": {
        "source": "استراتژی برند کافه رست (نمونه).pdf",
        "summary": "کافه‌ی تخصصی محله. هدف اینستاگرام: فالوئر رو به مشتری حضوری و خریدار دونه‌ی قهوه تبدیل کنه، نه فقط بازدید.",
        "goals": ["۳۰٪ رشد فروش دونه‌ی قهوه تا آخر پاییز", "معرفی منوی فصل", "اعتماد: «این‌ها قهوه رو بلدن»"],
        "audience": "۲۰ تا ۳۵ ساله‌های شهری، اهل کافه‌گردی و قهوه‌ی خونگی",
        "voice": "گرم، صمیمی، کمی شوخ؛ آموزش ساده بدون پز دادن",
        "pillars": ["آموزش دم‌آوری", "پشت صحنه‌ی کافه", "منوی فصل", "فرهنگ قهوه"],
        "dos": ["دست‌های باریستا و نور طبیعی", "آموزش کوتاه با یه نتیجه‌ی واضح", "اسم دونه‌ها روی صفحه"],
        "donts": ["رقص ترند", "پرنک و طنز تند", "رنگ نئونی", "ادعای قیمت"],
        "competitors": ["@brewlab.sample", "@slowpour.sample"],
        "keywords": ["قهوه تخصصی", "دم‌آوری", "latte art", "coffee tips"],
        "kpis": ["اشتراک‌گذاری", "ذخیره", "مراجعه‌ی حضوری با کد ریل"],
    },
}

QUERIES = ["#قهوه_تخصصی", "#coffeetok", "latte art reels", "YouTube Shorts: coffee mistakes"]

# arrival order = the order Claude "finds" them; key links QC / pre-production / storyboard data below
ROWS = [
    dict(key="bitter", title="۳ اشتباهی که قهوه‌ی خونگیت رو تلخ می‌کنه", hook="قهوه‌ت تلخه؟ تقصیر دونه نیست.",
         summary="باریستا با دست‌هاش ۳ اشتباه رایج دم‌آوری رو نشون می‌ده و درستش رو کنارش.", source_page="@brewlab.sample",
         followers=210000, views=1900000, likes=142000, comments=3100, shares=48000, saves=31000, age_days=6, kind="filmed",
         colors=("#4A3426", "#D9B48F"), emoji="☕"),
    dict(key="dance", title="چالش رقص باریستاها پشت بار", hook="وقتی مدیر کافه نیست 💃",
         summary="سه باریستا روی یه ترند موزیک پشت بار می‌رقصن؛ نور رنگی و کات‌های تند.", source_page="@baristas.daily.sample",
         followers=400000, views=3400000, likes=290000, comments=6800, shares=72000, saves=9000, age_days=4, kind="filmed",
         colors=("#7A00FF", "#00E5A0"), emoji="💃"),
    dict(key="personality", title="قهوه‌ت رو بر اساس شخصیتت انتخاب کن", hook="بگو چی سفارش می‌دی، بگم کی هستی.",
         summary="موشن‌گرافیک ساده: هر نوشیدنی یه تیپ شخصیتی، آخرش «تو کدومی؟».", source_page="@coffee.charts.sample",
         followers=95000, views=1200000, likes=88000, comments=5400, shares=61000, saves=22000, age_days=9, kind="motion",
         colors=("#B8A2F0", "#FFD6E8"), emoji="🧠"),
    dict(key="pov", title="یه روز کافه در ۳۰ ثانیه (POV)", hook="۶ صبح، قبل از اینکه در رو باز کنیم…",
         summary="نمای اول‌شخص از باز کردن کافه تا اولین سفارش.", source_page="@morningcup.sample",
         followers=190000, views=860000, likes=71000, comments=1100, shares=12000, saves=9000, age_days=12, kind="filmed",
         colors=("#2F3A2E", "#E8C9A0"), emoji="🌅"),
    dict(key="bean", title="سفر دونه‌ی قهوه از مزرعه تا فنجون", hook="این دونه ۱۲ هزار کیلومتر اومده.",
         summary="انیمیشن نقشه: مسیر دونه از اتیوپی تا فنجون، با عدد و آیکون.", source_page="@bean.story.sample",
         followers=160000, views=640000, likes=39000, comments=900, shares=9000, saves=6000, age_days=15, kind="motion",
         colors=("#3E5F44", "#F2D7A6"), emoji="🗺️"),
    dict(key="blind", title="تست کور قهوه‌ی گرون و ارزون", hook="فرقشو می‌فهمی؟",
         summary="چهار نفر با چشم بسته دو قهوه رو مقایسه می‌کنن.", source_page="@tastetest.sample",
         followers=380000, views=2100000, likes=120000, comments=8900, shares=33000, saves=7000, age_days=8, kind="filmed",
         colors=("#1E1E1E", "#C9A46B"), emoji="🙈"),
    dict(key="neon", title="لاته‌آرت نئونی زیر نور RGB", hook="لاته‌آرت، ولی نسخه‌ی سایبرپانک",
         summary="سه طرح لاته‌آرت پشت هم، در اتاق تاریک با نور صورتی و آبی نئونی.", source_page="@neon.latte.sample",
         followers=150000, views=1500000, likes=98000, comments=1700, shares=25000, saves=18000, age_days=5, kind="filmed",
         colors=("#FF2BD6", "#00E5FF"), emoji="🌈"),
    dict(key="asmr", title="ASMR دم‌آوری V60", hook="فقط صدا. بدون حرف.",
         summary="کلوزآپ‌های آروم با صدای واقعی آب و آسیاب.", source_page="@slowpour.sample",
         followers=260000, views=520000, likes=44000, comments=600, shares=9000, saves=12000, age_days=10, kind="filmed",
         colors=("#5A4636", "#EADBC8"), emoji="🎧"),
    dict(key="menu", title="منوی پاییزی در ۵ ثانیه", hook="منوی جدید اومد 🍂",
         summary="موشن کوتاه معرفی منو با کارت‌های رنگی.", source_page="@menu.motion.sample",
         followers=70000, views=300000, likes=18000, comments=400, shares=3000, saves=2000, age_days=7, kind="motion",
         colors=("#B5532A", "#F6D8A8"), emoji="🍂"),
    dict(key="prank", title="واکنش مشتری‌ها به قهوه‌ی ۲ میلیونی", hook="قیمتو که شنید…",
         summary="پرنک خیابونی: به رهگذرها قهوه‌ی «فوق‌گرون» تعارف می‌کنن.", source_page="@prank.cafe.sample",
         followers=900000, views=2800000, likes=150000, comments=12000, shares=14000, saves=3000, age_days=3, kind="filmed",
         colors=("#E63946", "#1D3557"), emoji="😱"),
    dict(key="caffeine", title="چرا بعد از قهوه خوابت می‌گیره؟", hook="کافئین دروغ می‌گه؟",
         summary="موشن علمی ساده درباره‌ی آدنوزین و کافئین.", source_page="@sci.sip.sample",
         followers=300000, views=900000, likes=61000, comments=2900, shares=14000, saves=10000, age_days=11, kind="motion",
         colors=("#264653", "#E9C46A"), emoji="🧪"),
    dict(key="dessert", title="دسر ۳ سوته با اسپرسو", hook="فقط سه چیز لازم داری.",
         summary="دست‌ها از بالا یه دسر ساده با اسپرسو درست می‌کنن.", source_page="@dessert.drip.sample",
         followers=300000, views=700000, likes=52000, comments=1300, shares=14000, saves=9000, age_days=9, kind="filmed",
         colors=("#6D4C41", "#FFE0B2"), emoji="🍮"),
    dict(key="methods", title="۵ روش دم‌آوری، یه کادر", hook="یه قهوه، پنج طعم.",
         summary="صفحه به ۵ ستون تقسیم می‌شه؛ هر ستون یه روش دم‌آوری، آخرش جدول مقایسه.", source_page="@brewlab.sample",
         followers=210000, views=1100000, likes=79000, comments=3300, shares=52000, saves=41000, age_days=13, kind="motion",
         colors=("#8D6E63", "#FFF3E0"), emoji="⚗️"),
    dict(key="reno", title="قبل و بعد بازسازی کافه", hook="از انباری تا کافه",
         summary="تایم‌لپس بازسازی با اسلایدر قبل/بعد.", source_page="@cafe.design.sample",
         followers=240000, views=450000, likes=30000, comments=700, shares=6000, saves=5000, age_days=20, kind="filmed",
         colors=("#9E9E9E", "#D7CCC8"), emoji="🔨"),
    dict(key="timelapse", title="تایم‌لپس یه روز شلوغ کافه", hook="۷ صبح تا ۱۰ شب در ۲۰ ثانیه",
         summary="دوربین ثابت گوشه‌ی کافه، تایم‌لپس کل روز.", source_page="Busy Bar (Shorts)", platform="youtube",
         followers=130000, views=380000, likes=21000, comments=300, shares=None, saves=None, age_days=18, kind="filmed",
         colors=("#37474F", "#FFCC80"), emoji="⏱️"),
    dict(key="odd", title="۷ قهوه‌ی عجیب دنیا", hook="شماره ۴ رو جرئت نداری بخوری",
         summary="لیست‌وار با فوتیج آرشیوی و متن بزرگ.", source_page="@odd.cups.sample",
         followers=500000, views=1700000, likes=72000, comments=4100, shares=21000, saves=15000, age_days=7, kind="motion",
         colors=("#FF8F00", "#4E342E"), emoji="🌍"),
    dict(key="ask", title="باریستا جواب کامنت‌ها رو می‌ده", hook="«چرا لاته‌تون انقدر گرونه؟»",
         summary="باریستا رو به دوربین به کامنت‌ها جواب می‌ده.", source_page="@askbarista.sample",
         followers=220000, views=410000, likes=33000, comments=6200, shares=5000, saves=2000, age_days=6, kind="filmed",
         colors=("#455A64", "#CFD8DC"), emoji="💬"),
    dict(key="never", title="۵ قهوه‌ای که هیچ‌وقت نباید سفارش بدی", hook="از زبون یه باریستا",
         summary="باریستا با تیکه‌های طنز ۵ سفارش «اشتباه» رو می‌گه.", source_page="@barista.truth.sample",
         followers=640000, views=1300000, likes=69000, comments=9800, shares=26000, saves=19000, age_days=10, kind="filmed",
         colors=("#3E2723", "#BCAAA4"), emoji="🚫"),
    dict(key="future", title="منوی کافه‌ی آینده با هوش مصنوعی", hook="قهوه‌ی سال ۲۰۴۰",
         summary="تصاویر AI از نوشیدنی‌های فضایی و موشن ساده.", source_page="Future Menu (Shorts)", platform="youtube",
         followers=45000, views=260000, likes=12000, comments=900, shares=None, saves=None, age_days=5, kind="motion",
         colors=("#311B92", "#80DEEA"), emoji="🤖"),
    dict(key="moka", title="آموزش ۳۰ ثانیه‌ای موکاپات", hook="بدون دستگاه اسپرسو",
         summary="آموزش قدم‌به‌قدم موکاپات با نمای بالا.", source_page="@moka.home.sample",
         followers=300000, views=590000, likes=41000, comments=1900, shares=11000, saves=14000, age_days=14, kind="filmed",
         colors=("#5D4037", "#FFCCBC"), emoji="🫖"),
]


def alt(title, hook, why, kind):
    return {"title": title, "hook": hook, "why": why, "kind": kind}


QC = {
    "bitter": dict(verdict="fit", fit=92, checks=[
        ("موضوع", True, "آموزش دم‌آوری، ستون اصلی پیجه"), ("مخاطب", True, "قهوه‌ی خونگی دقیقاً دغدغه‌ی همین مخاطبه"),
        ("لحن", True, "آموزشی و صمیمی، بدون پز"), ("بصری", True, "نور طبیعی، چوب و سرامیک، همون حس پیج"),
        ("تولید", True, "فقط دست باریستا؛ موبایل + سه‌پایه کافیه"), ("برند", True, "تخصص کافه رو نشون می‌ده")],
        source_palette=["#4A3426", "#D9B48F", "#F5EDE3", "#2E2E2E"],
        adapt="با دونه‌های خود کافه و اسم دونه روی صفحه؛ آخرش «دونه‌ی این هفته»."),
    "personality": dict(verdict="fit", fit=84, checks=[
        ("موضوع", True, "فرهنگ قهوه، یکی از ستون‌های پیج"), ("مخاطب", True, "شخصیت‌سنجی برای ۲۰ تا ۳۵ ساله‌ها خیلی اشتراک می‌خوره"),
        ("لحن", True, "شوخی ملایم، به لحن پیج می‌خوره"), ("بصری", "warn", "منبع پاستلی بنفش و صورتیه؛ باید با پالت پیج بازسازی بشه"),
        ("تولید", True, "موشن ساده، بدون ضبط"), ("برند", True, "منوی خود کافه رو معرفی می‌کنه")],
        source_palette=["#B8A2F0", "#FFD6E8", "#7FD1C7", "#FFFFFF"],
        adapt="رنگ‌ها رو با قهوه‌ای، کرم و سبز پیج عوض کن و فقط نوشیدنی‌هایی رو بیار که توی منوی کافه هست."),
    "dance": dict(verdict="unfit", fit=28, checks=[
        ("موضوع", "warn", "توی کافه‌ست، ولی محورش رقصه نه قهوه"), ("مخاطب", True, "سن مخاطب می‌خوره"),
        ("لحن", False, "رقص ترند جزو «نکن»‌های پیجه"), ("بصری", False, "نور رنگی کلاب و کات‌های تند، ضد حس دنج پیج"),
        ("تولید", False, "چهره‌ی کامل باریستا لازمه؛ پیج فقط دست و نیم‌رخ نشون می‌ده"), ("برند", False, "جدیت قهوه‌ی تخصصی رو کم می‌کنه")],
        logic="عددهاش عالیه (۳٫۴ میلیون بازدید، ۷۲ هزار اشتراک)، ولی این عددها مال خود ترند رقص و چهره‌ی باریستاهاست، نه قهوه. اگه پیج تو همینو بسازه، فالوئری میاد که دنبال رقصه و بعداً با پست‌های قهوه تعامل نمی‌کنه. رقص صریحاً جزو کارهای «نکن» پیجه و باریستای کافه هم جلوی دوربین چهره نشون نمی‌ده.",
        visual="منبع با نور رنگی بنفش و سبز، کات‌های تند و صورت کامل باریستاها ساخته شده. پیج تو نور طبیعی پنجره، چوب و سرامیک و پالت قهوه‌ای-کرم داره و چهره نشون نمی‌ده. همین رو بسازی، توی گرید پیج مثل یه وصله‌ی ناجور دیده می‌شه.",
        source_palette=["#7A00FF", "#00E5A0", "#111111", "#FF3D7F"],
        alternative=alt("ریتم بار: ۴ نوشیدنی روی یه بیت", "صدای بار کافه، ولی روی بیت 🎧",
                        "انرژی و ریتم موزیک ترند رو نگه می‌داره، ولی به‌جای رقص، دست‌های باریستا و صدای دستگاه روی ضرب کات می‌خوره. بدون چهره، با نور گرم خود کافه.", "filmed")),
    "neon": dict(verdict="unfit", fit=41, checks=[
        ("موضوع", True, "لاته‌آرت دقیقاً مال پیج توئه"), ("مخاطب", True, "مخاطب لاته‌آرت دوست داره"),
        ("لحن", True, "مشکلی نداره"), ("بصری", False, "نئون صورتی و آبی روی مشکی، ضد پالت گرم پیج"),
        ("تولید", "warn", "اتاق تاریک و نور RGB لازم داره که کافه نداره"), ("برند", False, "حس «گیمینگ» به‌جای «دنج»")],
        logic="موضوع و عددهاش عالیه؛ نرخ ذخیره‌ی بالا یعنی مردم طرح‌ها رو دوست دارن. ولی بخش بزرگی از جذابیت این ریل از نور نئونیه، نه از خود لاته‌آرت. اگه همین ظاهر رو کپی کنی، چیزی رو تبلیغ کردی که کافه‌ی تو نیست.",
        visual="رنگ غالب منبع صورتی و آبی نئونی روی زمینه‌ی مشکیه. پالت پیج تو قهوه‌ای، کرم و سبز ملایمه و «رنگ نئونی» صریحاً جزو «نکن»‌هاست. نور نئون رنگ قهوه و شیر رو هم خاکستری و سرد نشون می‌ده.",
        source_palette=["#FF2BD6", "#00E5FF", "#0B0B16", "#7A00FF"],
        alternative=alt("لاته‌آرت در نور طلایی صبح", "یه قلب، یه قو، یه گل… کدومش؟",
                        "همون لاته‌آرت و همون ساختار «سه طرح پشت هم» که ریل منبع رو پربازدید کرده، ولی کنار پنجره با نور طلایی صبح و نمای بالا. با گرید پیج کاملاً می‌خونه.", "filmed")),
    "methods": dict(verdict="partial", fit=71, checks=[
        ("موضوع", True, "مقایسه‌ی روش‌های دم‌آوری، ستون اصلی پیج"), ("مخاطب", True, "نرخ ذخیره‌ی خیلی بالا: مخاطب نگهش می‌داره"),
        ("لحن", True, "آموزشی"), ("بصری", "warn", "۵ ستون هم‌زمان روی موبایل خیلی ریز و شلوغ می‌شه"),
        ("تولید", "warn", "کافه فقط ۳ روش سرو می‌کنه؛ نسخه‌ی ۵تایی ادعای چیزیه که نیست"), ("برند", True, "تخصص کافه رو نشون می‌ده")],
        logic="ایده قویه، ولی کافه فقط V60، موکاپات و اسپرسو سرو می‌کنه. نسخه‌ی ۵ روشی یعنی دو تا روش که مشتری نمی‌تونه از کافه بخره، و ضبط ۵ پلان جدا هم کار رو دو برابر می‌کنه.",
        visual="۵ کادر عمودی کنار هم روی صفحه‌ی ۶ اینچی هر کدوم کمتر از ۲ سانت می‌شه و متن‌ها خونده نمی‌شن. ۳ کادر با برچسب بزرگ و رنگ‌های پیج خواناتره.",
        source_palette=["#8D6E63", "#FFF3E0", "#90A4AE", "#212121"],
        adapt="همین ایده با ۳ روش خود کافه.",
        alternative=alt("۳ روش دم‌آوری کافه، یه کادر", "کدوم قهوه‌ی ما مال توئه؟",
                        "همون ساختار مقایسه‌ای پربازدید، فقط با ۳ روشی که کافه واقعاً سرو می‌کنه و کادرهای بزرگ‌تر.", "motion")),
}


def _items(*xs):
    out = []
    for x in xs:
        if isinstance(x, tuple):
            name, note, have = (list(x) + [None, None])[:3]
            out.append({k: v for k, v in (("name", name), ("note", note), ("have", have)) if v is not None})
        else:
            out.append({"name": x})
    return out


def F(shot, time_, dur, visual, text=None, vo=None, camera=None, sfx=None, transition=None):
    return {k: v for k, v in dict(shot=shot, time=time_, dur=dur, visual=visual, text=text, vo=vo, camera=camera, sfx=sfx,
                                   transition=transition).items() if v}


PREPROD = {
    "bitter": dict(format="ریل ۹:۱۶ · ۳۰ ثانیه", summary="آموزش ۳ اشتباه دم‌آوری با دست‌های باریستا؛ هر اشتباه کنار نسخه‌ی درستش.",
                   hook="قهوه‌ت تلخه؟ تقصیر دونه نیست.",
                   people=_items(("باریستا", "فقط دست‌ها", True)), location=_items(("بار کنار پنجره‌ی شرقی", "نور صبح ۸ تا ۱۰", True)),
                   equipment=_items(("موبایل 4K/60fps", None, True), ("سه‌پایه + بازوی بالای سر", None, True), ("لنز ماکرو کلیپسی", "برای قطره‌ها", False),
                                    ("نور LED نرم + سافت‌باکس کوچیک", None, True)),
                   props=_items("دریپر V60 و فیلتر کاغذی", "کتری گوسفندی با دماسنج", "ترازوی قهوه", "دونه‌ی کامل + آسیاب ریز و درست", "فنجون سرامیکی کرم"),
                   software=_items(("CapCut", "کات، زیرنویس، کاور"), ("Claude", "متن روی صفحه و کپشن")),
                   assets=_items("فونت دست‌نویس فارسی", "لوگوی کافه (PNG شفاف)", ("موزیک lo-fi آروم", "Pixabay"), "SFX چکه و ریختن آب"),
                   schedule=[{"step": "ست نور و صحنه", "time": "۲۰ دقیقه"}, {"step": "ضبط ۶ پلان", "time": "۴۵ دقیقه"},
                             {"step": "تدوین و زیرنویس", "time": "۲ ساعت"}, {"step": "کاور و کپشن", "time": "۲۰ دقیقه"}],
                   checklist=["باتری و حافظه‌ی موبایل", "بار و فنجون تمیز", "حالت پرواز", "قفل نوردهی و فوکوس (AE/AF lock)"],
                   risks=["بخار توی نور کم دیده نمی‌شه ← نور از پشت (بک‌لایت)"], time="حدود ۴ ساعت", budget="تقریباً صفر"),
    "personality": dict(format="ریل ۹:۱۶ · ۲۵ ثانیه", summary="موشن‌گرافیک: هر نوشیدنی منو = یه تیپ شخصیتی؛ آخرش سؤال برای کامنت.",
                        hook="بگو چی سفارش می‌دی، بگم کی هستی.",
                        people=_items(("صداپیشه یا نریشن AI", "اختیاری", None)), location=_items(("لازم نیست", "تمام‌گرافیک", None)),
                        equipment=_items(("لپ‌تاپ", None, True), ("هدفون برای تنظیم صدا", None, True)),
                        props=_items(("لازم نیست", None, None)),
                        software=_items(("After Effects یا CapCut", "کی‌فریم و ترنزیشن"), ("Claude", "متن تیپ‌ها و کپشن"),
                                        ("Nano Banana / Gemini", "آیکون فنجون‌ها با پالت پیج")),
                        assets=_items("۴ آیکون فنجون (SVG)", "پالت پیج: قهوه‌ای، کرم، سبز", "فونت تیتر", "SFX پاپ و ووش", ("موزیک بانمک", "۱۰۰ تا ۱۱۰ BPM")),
                        schedule=[{"step": "متن تیپ‌ها", "time": "۳۰ دقیقه"}, {"step": "طراحی آیکون‌ها", "time": "۱ ساعت"},
                                  {"step": "انیمیشن", "time": "۳ ساعت"}, {"step": "صدا و خروجی", "time": "۳۰ دقیقه"}],
                        checklist=["متن‌ها داخل سیف‌زون (بالا ۲۲۰، پایین ۴۰۰ پیکسل)", "خوانایی روی موبایل", "فقط نوشیدنی‌های منوی کافه"],
                        risks=["کلیشه شدن تیپ‌ها ← از مشتری‌های واقعی کافه الهام بگیر"], time="حدود ۵ ساعت", budget="صفر"),
    "methods": dict(format="ریل ۹:۱۶ · ۳۵ ثانیه", summary="تقسیم صفحه به ۵ ستون دم‌آوری و جدول مقایسه‌ی آخر.", hook="یه قهوه، پنج طعم.",
                    people=_items(("باریستا", "فقط دست‌ها", True)), location=_items(("بار کافه", None, True)),
                    equipment=_items(("موبایل + سه‌پایه", None, True), ("فرنچ‌پرس و ایروپرس", "کافه نداره؛ باید قرض یا خریده بشه", False)),
                    props=_items("V60", "موکاپات", "اسپرسوساز", "فرنچ‌پرس", "ایروپرس", "۵ فنجون یکسان"),
                    software=_items(("CapCut", "تقسیم صفحه"), ("Claude", "جدول مقایسه")),
                    assets=_items("آیکون هر روش", "موزیک آروم"), time="حدود ۷ ساعت", budget="خرید دو دستگاه",
                    risks=["۵ ستون روی موبایل ریز می‌شه"]),
    "methods_alt": dict(format="ریل ۹:۱۶ · ۳۰ ثانیه", summary="سه ستون: V60، موکاپات، اسپرسو؛ هم‌زمان دم می‌کشن، آخرش جدول طعم با رنگ‌های پیج.",
                        hook="کدوم قهوه‌ی ما مال توئه؟",
                        people=_items(("باریستا", "فقط دست‌ها", True)), location=_items(("بار کافه", "سه ایستگاه کنار هم", True)),
                        equipment=_items(("موبایل + سه‌پایه", None, True), ("نور LED نرم", None, True)),
                        props=_items("V60", "موکاپات", "اسپرسوساز", "۳ فنجون یکسان", "تخته‌ی چوبی برای پس‌زمینه"),
                        software=_items(("CapCut", "تقسیم صفحه به ۳ ستون"), ("Claude", "جدول طعم (تلخی، بدنه، زمان)")),
                        assets=_items("آیکون هر روش با رنگ پیج", "فونت تیتر دست‌نویس", ("موزیک آروم", "Pixabay"), "SFX تیک ساعت"),
                        schedule=[{"step": "ضبط ۳ دم‌آوری از یک زاویه", "time": "۱ ساعت"}, {"step": "تقسیم صفحه و جدول", "time": "۲ ساعت"},
                                  {"step": "صدا و خروجی", "time": "۳۰ دقیقه"}],
                        checklist=["زاویه و فاصله‌ی دوربین برای هر ۳ ایستگاه یکی باشه", "تایمر هم‌زمان برای هر ۳ روش"],
                        risks=["رنگ قهوه‌ها توی ۳ ستون فرق کنه ← وایت‌بالانس دستی"], time="حدود ۴ ساعت", budget="صفر"),
    "dance": dict(format="ریل ۹:۱۶ · ۱۵ ثانیه", summary="نسخه‌ی اصلی: رقص ترند پشت بار.", people=_items(("۳ نفر جلوی دوربین", "با چهره", False)),
                  location=_items("پشت بار"), equipment=_items(("نور RGB", None, False), ("موبایل + سه‌پایه", None, True)),
                  software=_items("CapCut"), assets=_items("موزیک ترند (مجوزش چک بشه)"),
                  risks=["خلاف «نکن»‌های پیج", "چهره‌ی کارکنان جلوی دوربین"], time="۳ ساعت", budget="نور RGB"),
    "dance_alt": dict(format="ریل ۹:۱۶ · ۲۰ ثانیه", summary="ساخت ۴ نوشیدنی پشت سر هم؛ هر کات روی یه ضرب موزیک. فقط دست‌ها و دستگاه.",
                      hook="صدای بار کافه، ولی روی بیت 🎧",
                      people=_items(("باریستا", "فقط دست‌ها", True)), location=_items(("بار کافه", "ساعت خلوت", True)),
                      equipment=_items(("موبایل 4K/60fps", "برای اسلوموشن", True), ("سه‌پایه + بازوی بالای سر", None, True),
                                       ("میکروفون یقه‌ای", "صدای دستگاه و شیر", False)),
                      props=_items("دستگاه اسپرسو و پیچر شیر", "۴ لیوان مختلف", "یخ و سیروپ"),
                      software=_items(("CapCut", "کات روی ضرب با Beat Sync"), ("Claude", "ترتیب پلان‌ها روی بیت")),
                      assets=_items(("موزیک ۱۲۰ BPM بی‌کلام", "Pixabay"), "صدای واقعی بار"),
                      schedule=[{"step": "ضبط پلان‌ها", "time": "۴۰ دقیقه"}, {"step": "کات روی بیت", "time": "۲ ساعت"}],
                      checklist=["مترونوم یا موزیک پخش موقع ضبط", "دست‌ها تمیز و بدون انگشتر براق"],
                      risks=["صدای دستگاه روی موزیک گم بشه ← ضبط جدا با میکروفون"], time="حدود ۳ ساعت", budget="میکروفون یقه‌ای (اختیاری)"),
    "neon": dict(format="ریل ۹:۱۶ · ۲۰ ثانیه", summary="نسخه‌ی اصلی: لاته‌آرت در اتاق تاریک با نور نئون.",
                 location=_items(("اتاق تاریک", None, False)), equipment=_items(("نور RGB/نئون", None, False), ("موبایل", None, True)),
                 props=_items("پیچر شیر", "فنجون مشکی"), software=_items("CapCut"), risks=["خلاف پالت و «نکن»‌های پیج"],
                 time="۳ ساعت", budget="نور RGB"),
    "neon_alt": dict(format="ریل ۹:۱۶ · ۲۰ ثانیه", summary="سه طرح لاته‌آرت پشت هم از نمای بالا، کنار پنجره با نور طلایی صبح؛ آخرش «کدومش؟».",
                     hook="یه قلب، یه قو، یه گل… کدومش؟",
                     people=_items(("باریستا", "فقط دست‌ها", True)), location=_items(("میز کنار پنجره", "۸ تا ۹ صبح، نور طلایی", True)),
                     equipment=_items(("موبایل + بازوی بالای سر", None, True), ("رفلکتور سفید", "پر کردن سایه", False)),
                     props=_items("پیچر شیر ۳۵۰ میلی", "فنجون سرامیکی کرم", "سینی چوبی"),
                     software=_items(("CapCut", "کات و شماره‌گذاری ۱، ۲، ۳"), ("Claude", "کپشن و سؤال کامنت")),
                     assets=_items("فونت عدد دست‌نویس", ("موزیک آکوستیک آروم", "Pixabay")),
                     schedule=[{"step": "ضبط ۳ طرح (هر کدوم ۲ بار)", "time": "۴۰ دقیقه"}, {"step": "تدوین", "time": "۱ ساعت"}],
                     checklist=["فنجون دقیقاً وسط کادر", "قفل نوردهی روی سفیدی شیر"],
                     risks=["نور پنجره زود عوض می‌شه ← اول همه‌ی طرح‌ها، بعد پلان‌های اضافه"], time="حدود ۲ ساعت", budget="صفر"),
}

STORYBOARD = {
    "bitter": dict(style="نور طبیعی، رنگ گرم ملایم، زیرنویس دست‌نویس کرم", music="lo-fi آروم، ۸۵ BPM", frames=[
        F("closeup", "۰–۲s", 2, "قطره‌ی تیره‌ی قهوه از فیلتر می‌چکه، فوکوس آروم جابه‌جا می‌شه", "قهوه‌ت تلخه؟", "اگه قهوه‌ی خونگیت تلخه، احتمالاً یکی از این سه تا اشتباه رو می‌کنی.", "ماکرو، اسلاید آروم", "چکه + بیس نرم"),
        F("topdown", "۲–۹s", 7, "دو کپه دونه‌ی آسیاب‌شده کنار هم: پودر خیلی ریز و ریز متوسط", "اشتباه ۱: آسیاب خیلی ریز", "یک: آسیاب خیلی ریز. قهوه زیادی عصاره می‌ده و تلخ می‌شه.", "نمای بالا", transition="کات روی ضرب"),
        F("closeup", "۹–۱۶s", 7, "کتری با دماسنج: عدد ۱۰۰ قرمز، بعد ۹۳ سبز", "اشتباه ۲: آب ۱۰۰ درجه", "دو: آب جوش. بذار یه دقیقه بمونه؛ ۹۳ درجه بهترینه.", "کلوزآپ دماسنج", "تیک"),
        F("hands", "۱۶–۲۳s", 7, "دست‌ها روی ترازو: ۱۵ گرم قهوه، ۲۵۰ گرم آب", "اشتباه ۳: پیمونه‌ی چشمی", "سه: اندازه‌ی چشمی. با ترازو بریز، یک به شونزده.", "نیم‌رخ، هم‌سطح میز"),
        F("product", "۲۳–۲۸s", 5, "فنجون نهایی کنار پنجره، بخار پشت‌نور", "حالا بچش ☕", "حالا فرقش رو بچش.", "پوش‌این خیلی آروم"),
        F("logo", "۲۸–۳۰s", 2, "لوگوی کافه روی کرم + «دونه‌ی این هفته»", "@roast.demo", "دونه‌ی این هفته رو از کافه بگیر.", transition="محو")],
        caption="قهوه‌ی تلخ همیشه تقصیر دونه نیست ☕ کدوم اشتباه رو می‌کردی؟"),
    "personality": dict(style="تمام‌گرافیک، زمینه‌ی کرم با گرید محو، آیکون‌های تخت قهوه‌ای و سبز", music="بانمک، ۱۰۵ BPM", frames=[
        F("text", "۰–۲s", 2, "تیتر بزرگ روی زمینه‌ی کرم، فنجون از پایین بالا میاد", "قهوه‌ی تو چی می‌گه؟", "بگو چی سفارش می‌دی، بگم چه آدمی هستی.", sfx="پاپ"),
        F("infographic", "۲–۷s", 5, "فنجون اسپرسوی انیمیشنی با برچسب", "اسپرسو = رک و عجول", "اسپرسو؟ رکی و حوصله‌ی حاشیه نداری.", transition="ووش به چپ"),
        F("infographic", "۷–۱۲s", 5, "لاته با قلب لاته‌آرت که تپش داره", "لاته = مهربون و اهل دورهمی", "لاته؟ همه دوستت دارن.", transition="ووش به چپ"),
        F("infographic", "۱۲–۱۷s", 5, "کلدبرو با یخ‌هایی که می‌چرخن", "کلدبرو = خونسرد و برنامه‌ریز", "کلدبرو؟ همیشه یه قدم جلویی."),
        F("split", "۱۷–۲۲s", 5, "چهار فنجون کنار هم، یکی خالی با علامت سؤال", "تو کدومی؟ کامنت کن 👇", "تو کدومی؟ برامون کامنت کن."),
        F("logo", "۲۲–۲۵s", 3, "لوگوی کافه", "@roast.demo")]),
    "methods": dict(style="تقسیم صفحه به ۵ ستون", frames=[
        F("text", "۰–۲s", 2, "تیتر روی زمینه‌ی چوب", "یه قهوه، پنج طعم"),
        F("split", "۲–۲۰s", 18, "۵ ستون عمودی: V60، موکاپات، اسپرسو، فرنچ‌پرس، ایروپرس", "۵ روش هم‌زمان"),
        F("infographic", "۲۰–۳۰s", 10, "جدول مقایسه‌ی ۵ روش", "کدوم تلخ‌تره؟"),
        F("logo", "۳۰–۳۵s", 5, "لوگو")]),
    "methods_alt": dict(style="سه ستون با قاب گرد، رنگ‌های پیج، برچسب بزرگ", music="آروم، ۹۰ BPM", frames=[
        F("text", "۰–۲s", 2, "تیتر روی تخته‌ی چوبی، سه فنجون خالی", "کدوم قهوه‌ی ما مال توئه؟", "سه روش دم‌آوری کافه، یه قهوه. کدومش مال توئه؟", sfx="تیک ساعت"),
        F("split", "۲–۱۴s", 12, "سه ستون: V60 | موکاپات | اسپرسو؛ هر سه هم‌زمان شروع می‌شن", "V60 · موکاپات · اسپرسو", "هر سه رو با یه دونه و یه وزن دم کردیم.", "هر ستون نمای بالا، یکسان"),
        F("infographic", "۱۴–۲۲s", 8, "جدول طعم: تلخی، بدنه، زمان؛ نوارها پر می‌شن", "تلخی · بدنه · زمان", "V60 سبک و میوه‌ای، موکاپات پرقدرت، اسپرسو غلیظ و کوتاه."),
        F("product", "۲۲–۲۷s", 5, "سه فنجون نهایی کنار پنجره", "تو کدومی؟ ۱، ۲ یا ۳", "تو کدومی؟ کامنت کن."),
        F("logo", "۲۷–۳۰s", 3, "لوگو + «هر سه توی منوی کافه»", "@roast.demo")]),
    "dance": dict(style="نور رنگی، کات تند", frames=[
        F("wide", "۰–۳s", 3, "سه باریستا پشت بار شروع به رقص می‌کنن", "وقتی مدیر نیست 💃"),
        F("person", "۳–۱۰s", 7, "رقص هماهنگ، نور رنگی"),
        F("closeup", "۱۰–۱۳s", 3, "یکی فنجون رو می‌چرخونه"),
        F("logo", "۱۳–۱۵s", 2, "لوگو")]),
    "dance_alt": dict(style="نور گرم کافه، کات روی ضرب، اسلوموشن روی ضرب‌های قوی", music="بی‌کلام ۱۲۰ BPM", frames=[
        F("hands", "۰–۲s", 2, "دست باریستا تمپ رو روی ضرب اول فشار می‌ده", "صدای بار، روی بیت 🎧", sfx="تمپ + کیک", camera="کلوزآپ هم‌سطح"),
        F("closeup", "۲–۶s", 4, "استیم‌وند شیر رو فوم می‌کنه؛ صدا روی ضرب", sfx="هیس بخار", transition="کات روی ضرب"),
        F("topdown", "۶–۱۰s", 4, "ریختن شیر و قلب لاته‌آرت", camera="نمای بالا، ۶۰fps"),
        F("timelapse", "۱۰–۱۵s", 5, "چهار نوشیدنی پشت سر هم روی بار ردیف می‌شن", "۴ نوشیدنی، ۱۵ ثانیه", transition="کات سریع ۴تایی"),
        F("product", "۱۵–۱۸s", 3, "چهار لیوان کنار هم، نور پنجره", "کدومو سفارش می‌دی؟"),
        F("logo", "۱۸–۲۰s", 2, "لوگوی کافه", "@roast.demo")]),
    "neon": dict(style="اتاق تاریک، نئون صورتی و آبی", frames=[
        F("wide", "۰–۳s", 3, "اتاق تاریک، روشن شدن نئون", "لاته‌آرت سایبرپانک"),
        F("topdown", "۳–۱۵s", 12, "سه طرح زیر نور RGB"),
        F("closeup", "۱۵–۱۸s", 3, "بخار در نور صورتی"),
        F("logo", "۱۸–۲۰s", 2, "لوگو")]),
    "neon_alt": dict(style="نور طلایی صبح، نمای بالا، شماره‌ی دست‌نویس", music="آکوستیک آروم", frames=[
        F("topdown", "۰–۶s", 6, "طرح ۱: قلب، از نمای بالا کنار پنجره", "۱", "یه قلب…", "بازوی بالای سر، ثابت"),
        F("topdown", "۶–۱۲s", 6, "طرح ۲: قو", "۲", "یه قو…", transition="کات روی آخرین قطره"),
        F("topdown", "۱۲–۱۸s", 6, "طرح ۳: گل لاله", "۳", "یه گل…"),
        F("text", "۱۸–۲۰s", 2, "سه فنجون کنار هم، سؤال", "کدومش؟ ۱، ۲ یا ۳", "کدومش؟ کامنت کن.", sfx="پاپ"),
        F("logo", "۲۰–۲۲s", 2, "لوگوی کافه", "@roast.demo")]),
}

AUTO = [("bitter", "approve"), ("personality", "approve"), ("dance", "approve_alt"), ("neon", "delete"), ("methods", "approve_alt")]
VERDICT_FA = {"fit": "مناسب", "partial": "نیمه‌مناسب", "unfit": "نامناسب"}


def thumb_svg(c1, c2, emoji):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 90 160"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>'
            '<rect width="90" height="160" fill="url(#g)"/><rect y="118" width="90" height="42" fill="#000" opacity=".18"/>'
            f'<text x="45" y="92" font-size="42" text-anchor="middle">{emoji}</text></svg>')


def qc_for(key, page_palette):
    q = dict(QC[key])
    checks = [{"area": a, "ok": ok, "note": n} for a, ok, n in q.pop("checks")]
    return {"verdict": q["verdict"], "fit": q["fit"], "checks": checks, "logic": q.get("logic", ""), "visual": q.get("visual", ""),
            "source_palette": q.get("source_palette", []), "page_palette": page_palette, "adapt": q.get("adapt", ""),
            "alternative": q.get("alternative"), "at": store.now_iso()}


def storyboard_for(variant):
    sb = dict(STORYBOARD[variant])
    frames = [dict(f, n=n) for n, f in enumerate(sb["frames"], 1)]
    return {"frames": frames, "duration": sum(f.get("dur") or 0 for f in frames), "style": sb.get("style"), "music": sb.get("music"),
            "caption": sb.get("caption"), "version": 1, "at": store.now_iso()}


def preprod_for(variant):
    pp = {k: v for k, v in PREPROD[variant].items()}
    for g in store.PREPROD_GROUPS:
        pp.setdefault(g, [])
    pp.setdefault("schedule", [])
    pp.setdefault("checklist", [])
    pp.setdefault("risks", [])
    pp["at"] = store.now_iso()
    return pp


YT_LONG = {"methods", "bean", "caffeine", "odd"}  # these work better as long videos on YouTube (16:9 storyboard)


def youtube_rows(rows):
    """the same made-up ideas as YouTube Shorts / long videos: YouTube shows views, likes and comments, not shares or saves"""
    out = []
    for r in rows:
        y = dict(r, platform="youtube", shares=None, saves=None, format="long" if r["key"] in YT_LONG else "short",
                 views=int(r["views"] * 0.62), likes=int(r["likes"] * 0.55), comments=int(r["comments"] * 0.7),
                 followers=int(r["followers"] * 0.8))
        if y["key"] == "dance":
            y.update(views=2_600_000, likes=180_000)
        elif y["key"] == "neon":
            y.update(views=1_250_000, likes=95_000)
        elif y["key"] == "pov":
            y.update(views=420_000)
        elif y["key"] == "methods":
            y.update(views=900_000, likes=70_000)
        out.append(y)
    return out


def youtube_board(yt, rows):
    ranked = scout.rank(youtube_rows(rows), keep=20, top=5)
    for r in ranked:
        r["id"] = f"i{r['rank']:02d}"
        if r.get("top") and r["key"] in QC:
            r["qc"] = qc_for(r["key"], PAGE["visual"]["palette"])
    board = {"scan": {"queries": ["coffee tips shorts", "latte art", "قهوه تخصصی"], "status": "done", "scanned": len(rows),
                      "kept": len(ranked), "at": store.now_iso()}, "ideas": ranked}
    yt.save_board(board)
    return board, [i for i in ranked if i.get("top")]


LI_SKIP = {"dance", "neon"}  # trend dances and neon looks don't travel to LinkedIn; keep the demo believable


def linkedin_rows(rows):
    """the same made-up ideas as LinkedIn video posts: reactions, comments and reposts are public, views usually are not"""
    out = []
    for n, r in enumerate(x for x in rows if x["key"] not in LI_SKIP):
        name = r["source_page"].lstrip("@").replace(".sample", "").replace(".", " ").title() + " (نمونه)"
        out.append(dict(r, platform="linkedin", views=None, saves=None, format="long" if r["key"] in YT_LONG else "short",
                        likes=max(40, int(r["likes"] * 0.02)), comments=max(5, int(r["comments"] * 0.05)),
                        shares=max(2, int((r.get("shares") or 0) * 0.004)), followers=max(800, int(r["followers"] * 0.06)),
                        source_page=name, url=f"https://www.linkedin.com/posts/demo-{r['key']}-activity-70000000000000{n:05d}-demo/"))
    return out


def linkedin_board(li, rows):
    ranked = scout.rank(linkedin_rows(rows), keep=20, top=5)
    for r in ranked:
        r["id"] = f"i{r['rank']:02d}"
        if r.get("top") and r["key"] in QC:
            r["qc"] = qc_for(r["key"], PAGE["visual"]["palette"])
    board = {"scan": {"queries": ["specialty coffee business", "café team behind the scenes", "قهوه تخصصی"], "status": "done",
                      "scanned": len(ranked), "kept": len(ranked), "at": store.now_iso()}, "ideas": ranked}
    li.save_board(board)
    return board, [i for i in ranked if i.get("top")]


def run(ws, speed=1.0, auto=False, port=8771, serve=True, open_browser=False, say=print, flush=None):
    if ws.root.exists():
        shutil.rmtree(ws.root, ignore_errors=True)
    ws.ensure()
    ws.save_config(demo=True, created=store.now_iso(), platform="instagram")
    ig, yt, li = ws.for_platform("instagram"), ws.for_platform("youtube"), ws.for_platform("linkedin")
    yt.ensure()
    li.ensure()

    def pause(s):
        time.sleep(s / max(speed, 0.05))

    def E(agent, type_, msg, **d):
        store.add_event(ws, agent, type_, msg, d, demo=True)

    thumbs = ws.root / "thumbs"
    thumbs.mkdir(parents=True, exist_ok=True)
    rows = []
    for r in ROWS:
        (thumbs / f"{r['key']}.svg").write_text(thumb_svg(*r["colors"], r["emoji"]), encoding="utf-8")
        row = {k: v for k, v in r.items() if k not in ("colors", "emoji")}
        row["thumb"] = f"/ws/thumbs/{r['key']}.svg"
        rows.append(row)
    ranked = scout.rank(rows, keep=20, top=5)
    for r in ranked:
        r["id"] = f"i{r['rank']:02d}"
    by_key = {r["key"]: r for r in ranked}

    if serve:
        def ready(url):
            ws.save_config(dashboard=url)
            say(f"📺 داشبورد نمونه: {url}   (برای بستن: Ctrl+C)")
            if flush:
                flush()
            if open_browser:
                webbrowser.open(url)
        server.serve(ws, port, ready, block=False)
        pause(2.5)
    say("▶ اجرای نمایشی: همه‌ی پیج‌ها و عددها ساختگی‌اند (برچسب DEMO).")

    # 1. reference page
    E("page", "read", "خوندن سند استراتژی برند: هدف، مخاطب، لحن، بایدها و نبایدها")
    pause(1.4)
    E("page", "read", f"دیدن پیج {PAGE['handle']} بدون لاگین: بایو، گرید، رنگ‌ها، بازدید ریل‌ها")
    pause(1.4)
    store.write_json(ws.page_path, PAGE)
    E("page", "profile", f"پیج رفرنس: {PAGE['handle']} — {PAGE['niche']}")
    say("  پیج رفرنس ثبت شد")
    pause(1.2)

    # 2. scout: 20 reels arrive one by one, then the top 5 are marked
    board = {"scan": {"queries": [], "status": "scanning", "scanned": 0}, "ideas": []}
    for n, r in enumerate(ROWS):
        if n % 5 == 0 and n // 5 < len(QUERIES):
            q = QUERIES[n // 5]
            board["scan"]["queries"].append(q)
            E("scout", "search", f"جستجو: {q}", query=q)
            pause(0.7)
        idea = by_key[r["key"]]
        board["ideas"].append(idea)
        board["scan"]["scanned"] = n + 1
        ig.save_board(board)
        E("scout", "found", f"{idea['title']} — {idea['source_page']}", id=idea["id"])
        pause(0.35)
    board["ideas"].sort(key=lambda i: i["rank"])
    board["scan"].update(status="done", kept=len(ranked), at=store.now_iso())
    ig.save_board(board)
    tops = [i for i in board["ideas"] if i.get("top")]
    E("scout", "summary", f"{len(ROWS)} ریل بررسی شد؛ ۲۰ ایده مرتب شد")
    E("scout", "top", "تاپ ۵: " + "، ".join(i["title"][:24] for i in tops))
    say("  ۲۰ ایده ثبت شد، تاپ ۵: " + "، ".join(i["key"] for i in tops))
    pause(1.5)

    # 3. QC of the top 5 (nothing is removed)
    for idea in tops:
        E("qc", "checking", f"بررسی «{idea['title'][:36]}» با پیج رفرنس…", id=idea["id"])
        pause(1.5)
        idea["qc"] = qc_for(idea["key"], PAGE["visual"]["palette"])
        ig.save_board(board)
        E("qc", "check", f"QC «{idea['title'][:36]}»: {VERDICT_FA[idea['qc']['verdict']]}", id=idea["id"])
        pause(0.6)
    counts = {v: sum(1 for i in tops if i["qc"]["verdict"] == v) for v in VERDICT_FA}
    E("qc", "summary", f"QC تموم شد: {counts['fit']} مناسب، {counts['partial']} نیمه‌مناسب، {counts['unfit']} نامناسب. هیچ ایده‌ای حذف نشد؛ تصمیم با کارفرماست.")
    say("  QC تمام شد؛ منتظر تصمیم کارفرما روی داشبورد")

    # 4. the same flow on YouTube (its own 20 ideas, top 5 and QC), shown when the platform switch is set to YouTube
    yboard, ytops = youtube_board(yt, rows)
    E("scout", "summary", f"یوتیوب: {len(yboard['ideas'])} ویدیو (Shorts و بلند) بررسی و QC شد — از سوییچ بالای داشبورد ببین")
    say("  بُرد یوتیوب هم آماده شد (سوییچ «یوتیوب»)")
    lboard, ltops = linkedin_board(li, rows)
    E("scout", "summary", f"لینکدین: {len(lboard['ideas'])} پست ویدیویی بررسی و QC شد — از سوییچ بالای داشبورد ببین")
    say("  بُرد لینکدین هم آماده شد (سوییچ «لینکدین»)")

    produced = {}
    BOARDS = [(ig, board, tops), (yt, yboard, ytops), (li, lboard, ltops)]

    def produce(wsx, bx, idea, status):
        variant = idea["key"] + ("_alt" if status == "approved_alt" else "")
        if variant not in PREPROD:
            variant = idea["key"]
        pid = wsx.platform + idea["id"]
        if produced.get(pid) == variant:
            return
        produced[pid] = variant
        title = idea["qc"]["alternative"]["title"] if status == "approved_alt" else idea["title"]
        E("prod", "working", f"نوشتن سند پیش‌تولید «{title[:36]}»…", id=idea["id"])
        pause(1.6)
        idea["preprod"] = preprod_for(variant)
        idea.pop("storyboard", None)
        wsx.save_board(bx)
        E("prod", "preprod", f"سند پیش‌تولید «{title[:36]}» آماده شد", id=idea["id"])
        pause(0.8)
        E("prod", "working", f"طراحی استوری‌بورد «{title[:36]}»…", id=idea["id"])
        pause(2.0)
        idea["storyboard"] = storyboard_for(variant)
        wsx.save_board(bx)
        E("prod", "storyboard", f"استوری‌بورد «{title[:36]}» آماده شد ({len(idea['storyboard']['frames'])} فریم)", id=idea["id"])
        say(f"  پیش‌تولید و استوری‌بورد ({store.PLATFORM_FA[wsx.platform]}): {title}")

    def revise(wsx, bx, idea):
        sb = idea["storyboard"]
        E("prod", "working", f"اصلاح استوری‌بورد «{idea['title'][:36]}»…", id=idea["id"])
        pause(2.5)
        sb["version"] = int(sb.get("version") or 1) + 1
        sb["at"] = store.now_iso()
        wsx.save_board(bx)
        wsx.clear_storyboard_decision(idea["id"])
        E("prod", "storyboard", f"نسخه‌ی {sb['version']} استوری‌بورد آماده شد", id=idea["id"])

    def step():
        for wsx, bx, tx in BOARDS:
            dec = wsx.decisions()
            for idea in tx:
                d = dec["ideas"].get(idea["id"], {})
                if d.get("status") in ("approved", "approved_alt") and idea.get("qc"):
                    produce(wsx, bx, idea, d["status"])
                    if dec["storyboards"].get(idea["id"], {}).get("status") == "revise" and idea.get("storyboard"):
                        revise(wsx, bx, idea)
                    dec = wsx.decisions()

    if auto:
        ids = {i["key"]: i["id"] for i in tops}
        for key, action in AUTO:
            if key not in ids:
                continue
            pause(1.0)
            ig.decide(ids[key], action)
            idea = by_key[key]
            t = idea["qc"]["alternative"]["title"] if action == "approve_alt" else idea["title"]
            msg = {"approve": "تأیید شد", "approve_alt": "جایگزین تأیید شد", "delete": "از ایده‌های ساخت حذف شد"}[action]
            E("client", "decision", f"«{t[:36]}» {msg}", id=ids[key], action=action)
        step()
        if "bitter" in ids:
            pause(1.0)
            ig.decide_storyboard(ids["bitter"], "approve")
            E("client", "storyboard", f"«{by_key['bitter']['title'][:36]}»: استوری‌بورد تأیید شد ← مرحله‌ی تولید", id=ids["bitter"])
        say("  تصمیم‌های نمایشی کارفرما زده شد")
    if not serve:
        return
    say("  ✋ حالا روی داشبورد تأیید یا حذف کن؛ پیش‌تولید و استوری‌بورد خودکار ساخته می‌شه. برای بستن: Ctrl+C")
    if flush:
        flush()
    try:
        while True:
            step()
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
