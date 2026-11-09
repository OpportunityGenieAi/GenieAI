"""Pure rendering helpers for website articles (no database or web framework here)."""
import html
import json
import os
import re

BASE = os.environ.get("SITE_URL", "https://opportunitygenie.org").rstrip("/")
PLAY = "https://play.google.com/store/apps/details?id=opportunitygenie.org"
NAME = "OpportunityGenie AI"

GUIDES = [
    ("fully-funded-scholarships", "Fully funded", "Fully funded scholarships for international students"),
    ("scholarships-without-ielts", "Without IELTS", "Scholarships without IELTS: how to apply without the test"),
    ("scholarships-without-application-fees", "No application fee", "Scholarships and applications without application fees"),
    ("scholarships-for-african-students", "For African students", "Scholarships for African students"),
    ("masters-scholarships", "Master's", "Master's scholarships for international students"),
    ("phd-scholarships", "PhD", "PhD scholarships and funded doctoral positions"),
]

# Articles that exist as static files in /website/articles/
STATIC_ARTICLES = [
    {
        "slug": "how-to-write-a-scholarship-motivation-letter",
        "title": "How to write a winning scholarship motivation letter",
        "description": "A step-by-step structure for a scholarship motivation letter, with common mistakes to avoid and how to get feedback.",
    }
]

STATIC_URLS = ["/"] + [f"/{g[0]}/" for g in GUIDES] + ["/articles/"] + [f"/articles/{a['slug']}/" for a in STATIC_ARTICLES]


def play(src: str) -> str:
    return f"{PLAY}&referrer=utm_source%3Dwebsite%26utm_medium%3D{src}"


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:90].strip("-")


def _inline(s: str) -> str:
    s = html.escape(s, quote=True)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)

    def link(m):
        label, url = m.group(1), m.group(2)
        ext = url.startswith("http")
        extra = ' rel="noopener" target="_blank"' if ext else ""
        return f'<a href="{url}"{extra}>{label}</a>'

    return re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+|/[^\s)]*)\)", link, s)


def cta_html(src: str) -> str:
    return (
        '<div class="cta-inline"><b>Track these opportunities in one place</b>'
        "<span>OpportunityGenie AI lists scholarships with official links and deadlines.</span>"
        f'<a class="btn" href="{play(src)}" rel="noopener">Install on Google Play</a></div>'
    )


def md_to_html(text: str, src: str = "article") -> str:
    """Tiny, safe Markdown: ## / ### headings, paragraphs, - and 1. lists, > notes, **bold**, [text](url), [[install]]."""
    out, para, lst = [], [], None

    def flush_p():
        nonlocal para
        if para:
            out.append("<p>" + _inline(" ".join(para)) + "</p>")
            para = []

    def flush_l():
        nonlocal lst
        if lst:
            tag, items = lst
            out.append(f"<{tag}>" + "".join(f"<li>{_inline(i)}</li>" for i in items) + f"</{tag}>")
            lst = None

    for raw in (text or "").replace("\r", "").split("\n"):
        line = raw.rstrip()
        if not line.strip():
            flush_p(); flush_l(); continue
        if line.strip() == "[[install]]":
            flush_p(); flush_l(); out.append(cta_html(src)); continue
        m = re.match(r"^(#{2,3})\s+(.*)", line)
        if m:
            flush_p(); flush_l()
            n = len(m.group(1))
            out.append(f"<h{n}>{_inline(m.group(2))}</h{n}>"); continue
        m = re.match(r"^\s*[-*]\s+(.*)", line)
        if m:
            flush_p()
            if not lst or lst[0] != "ul":
                flush_l(); lst = ("ul", [])
            lst[1].append(m.group(1)); continue
        m = re.match(r"^\s*\d+[.)]\s+(.*)", line)
        if m:
            flush_p()
            if not lst or lst[0] != "ol":
                flush_l(); lst = ("ol", [])
            lst[1].append(m.group(1)); continue
        if line.startswith(">"):
            flush_p(); flush_l()
            out.append('<div class="note">' + _inline(line.lstrip("> ").strip()) + "</div>"); continue
        flush_l()
        para.append(line.strip())
    flush_p(); flush_l()
    return "\n".join(out)


def _ld(obj) -> str:
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def header_html() -> str:
    nav = "".join(f'<a href="/{s}/">{n}</a>' for s, n, _ in GUIDES[:4])
    return (
        f'<header class="top"><div class="wrap bar"><a class="brand" href="/"><img src="/logo-96.png" width="44" height="44" alt="{NAME} logo">{NAME}</a>'
        f'<nav class="main" aria-label="Main">{nav}<a href="/articles/">Guides</a></nav>'
        f'<a class="btn sm" href="{play("article_header")}" rel="noopener">Install app</a></div></header>'
    )


def footer_html() -> str:
    links = "".join(f'<a href="/{s}/">{n}</a>' for s, n, _ in GUIDES)
    return (
        f'<footer><div class="wrap"><div class="cols">{links}<a href="/articles/">Articles</a>'
        '<a href="/static/privacy-policy.html">Privacy policy</a></div>'
        f"<p>© {NAME}. Scholarship information is gathered from official sources and can change. "
        "Always confirm eligibility and deadlines on the funder's website. Not affiliated with any scholarship provider.</p></div></footer>"
    )


def shell(title: str, desc: str, path: str, body: str, ld: str = "", noindex: bool = False) -> str:
    t, d = html.escape(title), html.escape(desc, quote=True)
    robots = "noindex,nofollow" if noindex else "index,follow,max-image-preview:large"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{t}</title>
<meta name="description" content="{d}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{BASE}{path}">
<meta property="og:type" content="article"><meta property="og:title" content="{t}"><meta property="og:description" content="{d}"><meta property="og:url" content="{BASE}{path}"><meta property="og:site_name" content="{NAME}"><meta property="og:image" content="{BASE}/logo-512.png">
<meta name="twitter:card" content="summary"><meta name="theme-color" content="#0071BB">
<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@600&family=Open+Sans:wght@400;600&display=swap">
<link rel="stylesheet" href="/style.css">
{ld}</head><body>
{header_html()}{body}{footer_html()}
</body></html>
"""


def _side(src: str) -> str:
    return (
        '<aside class="side"><h3>Find these in the app</h3><p>Search over 1,000 scholarships, filter by region, '
        "save deadlines and get help with your motivation letter from the AI Advisor.</p>"
        f'<a class="btn" href="{play(src)}" rel="noopener">Get it on Google Play</a></aside>'
    )


def article_page(a: dict) -> str:
    slug = a["slug"]
    path = f"/articles/{slug}/"
    faq = [f for f in (a.get("faq") or []) if f.get("q") and f.get("a")]
    faq_html = ""
    if faq:
        faq_html = "<h2>Frequently asked questions</h2>" + "".join(
            f"<details><summary>{html.escape(f['q'])}</summary><p>{html.escape(f['a'])}</p></details>" for f in faq
        )
    related = "".join(f'<li><a href="/{s}/">{html.escape(t)}</a></li>' for s, _, t in GUIDES)
    lead = f'<p class="lead">{html.escape(a.get("lead") or "")}</p>' if a.get("lead") else ""
    body = (
        f'<main class="wrap page"><article><div class="crumbs"><a href="/">Home</a> / <a href="/articles/">Articles</a> / {html.escape(a["title"])}</div>'
        f'<h1>{html.escape(a["title"])}</h1>{lead}{md_to_html(a.get("body") or "", "art_" + slug[:30])}{faq_html}'
        f'<div class="related"><h2>More guides</h2><ul>{related}</ul></div></article>{_side("art_" + slug[:30] + "_side")}</main>'
    )
    ld = _ld({
        "@context": "https://schema.org", "@type": "Article", "headline": a["title"],
        "description": a.get("description") or "", "mainEntityOfPage": BASE + path,
        "datePublished": a.get("published_at") or "", "dateModified": a.get("updated_at") or "",
        "image": BASE + "/logo-512.png", "publisher": {"@type": "Organization", "name": NAME, "logo": {"@type": "ImageObject", "url": BASE + "/logo-512.png"}},
    })
    if faq:
        ld += _ld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faq]})
    return shell(f"{a['title']} | {NAME}", a.get("description") or a["title"], path, body, ld)


def index_page(items: list) -> str:
    cards = "".join(
        f'<a href="/articles/{i["slug"]}/"><b>{html.escape(i["title"])}</b><span>{html.escape(i.get("description") or "")}</span></a>' for i in items
    )
    body = (
        '<main class="wrap band"><div class="crumbs"><a href="/">Home</a> / Articles</div>'
        '<h1 style="font-size:2.4rem;margin-bottom:12px">Scholarship application guides</h1>'
        '<p class="sub">Guides on motivation letters, statements of purpose, interviews and finding funding.</p>'
        f'<div class="guides">{cards}</div></main>'
    )
    return shell(f"Scholarship Application Guides | {NAME}",
                 "Guides on scholarship motivation letters, statements of purpose, interviews and finding funding abroad.", "/articles/", body)


def not_found_page() -> str:
    body = '<main class="wrap band"><h1>Page not found</h1><p class="sub">This page does not exist. <a href="/articles/">See all guides</a>.</p></main>'
    return shell(f"Page not found | {NAME}", "Page not found", "/articles/", body, noindex=True)


def sitemap_xml(entries: list) -> str:
    """entries: [(path, lastmod_or_None)]"""
    rows = "".join(
        f"<url><loc>{BASE}{p}</loc>" + (f"<lastmod>{m}</lastmod>" if m else "") + "</url>\n" for p, m in entries
    )
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + "</urlset>\n"
