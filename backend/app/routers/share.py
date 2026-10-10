"""Public share page for scholarships + Android App Links verification file.

GET /s/{scholarship_id}               -> small web page: summary + "Open in the app" / "Get it on Google Play".
                                         It never shows the official application link, so applying
                                         is only possible inside the app.
GET /.well-known/assetlinks.json      -> lets Android open https://opportunitygenie.org/s/... directly in the app.
"""
import html
import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Scholarship
from app.schemas import ScholarshipOut

router = APIRouter(tags=["share"])

ANDROID_PACKAGE = "opportunitygenie.org"
SITE = "https://opportunitygenie.org"
PLAY_URL = f"https://play.google.com/store/apps/details?id={ANDROID_PACKAGE}"

# SHA-256 certificate fingerprints allowed to open these links in the app.
# 1) Play App Signing key (what people get from the Play Store) - required.
# 2) Optional: add your EAS upload key here so preview/development builds open links too.
APP_CERT_SHA256 = [
    "64:A9:B2:34:ED:3E:C2:F0:7D:63:35:8D:24:26:FC:0B:5C:75:9F:E6:13:7D:CC:5D:ED:1E:C5:C2:90:AA:1C:25",
]

CSS = """
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:#EEF1FB;color:#1B2140;line-height:1.5}
.wrap{max-width:560px;margin:0 auto;padding:20px 16px 40px}
.brand{font-weight:800;font-size:15px;color:#3B5BDB;margin:6px 0 16px}
.card{background:#fff;border:1px solid #DDE3F8;border-radius:16px;padding:20px}
h1{font-size:22px;line-height:1.25;margin:0 0 4px}
.provider{color:#5B6385;font-size:14px;margin:0 0 14px}
.blurb{font-size:15px;color:#3A4268;margin:0 0 14px}
.meta{list-style:none;padding:0;margin:0 0 14px;font-size:14px;color:#5B6385}
.meta li{margin:4px 0}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 16px}
.tag{background:#E6EBFF;color:#3B5BDB;border-radius:20px;padding:3px 10px;font-size:12px;font-weight:700}
.note{background:#F3F5FF;border-radius:10px;padding:12px 14px;font-size:14px;margin:0 0 6px}
.btn{display:block;text-align:center;text-decoration:none;font-weight:700;font-size:15px;border-radius:12px;padding:13px 16px;margin-top:10px}
.primary{background:#3B5BDB;color:#fff}
.secondary{background:#fff;color:#3B5BDB;border:2px solid #3B5BDB}
.foot{text-align:center;font-size:12px;color:#8089AD;margin-top:18px}
"""

JS = """
if (!/Android/i.test(navigator.userAgent)) {
  var b = document.getElementById('open-app');
  if (b) { b.style.display = 'none'; }
}
"""


def _page(title: str, description: str, body: str, canonical: str = "") -> str:
    og_url = (
        f'<meta property="og:url" content="{html.escape(canonical, quote=True)}">' if canonical else ""
    )
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description, quote=True)}">
<meta property="og:site_name" content="OpportunityGenie AI">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(title, quote=True)}">
<meta property="og:description" content="{html.escape(description, quote=True)}">
{og_url}
<style>{CSS}</style>
</head><body><div class="wrap">
<div class="brand">OpportunityGenie AI</div>
{body}
<div class="foot">&copy; OpportunityGenie AI &middot; <a href="/static/privacy-policy.html" style="color:inherit">Privacy Policy</a></div>
</div><script>{JS}</script></body></html>"""


def _not_found_page() -> str:
    body = f"""<div class="card">
<h1>This scholarship isn't available</h1>
<p class="blurb">It may have been removed. Open OpportunityGenie AI to browse current scholarships.</p>
<a class="btn primary" href="{PLAY_URL}">Get it on Google Play</a>
</div>"""
    return _page("Scholarship not found | OpportunityGenie AI", "Scholarship not found.", body)


@router.get("/.well-known/assetlinks.json")
def assetlinks():
    return JSONResponse(
        [
            {
                "relation": ["delegate_permission/common.handle_all_urls"],
                "target": {
                    "namespace": "android_app",
                    "package_name": ANDROID_PACKAGE,
                    "sha256_cert_fingerprints": APP_CERT_SHA256,
                },
            }
        ],
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/s/{scholarship_id}", response_class=HTMLResponse)
def share_page(scholarship_id: str, db: Session = Depends(get_db)):
    try:
        uuid.UUID(scholarship_id)
    except ValueError:
        return HTMLResponse(_not_found_page(), status_code=404)

    s = db.query(Scholarship).filter(Scholarship.id == scholarship_id).first()
    if not s:
        return HTMLResponse(_not_found_page(), status_code=404)

    out = ScholarshipOut.model_validate(s)
    esc = html.escape

    meta_items = []
    if out.country:
        meta_items.append(f"<li>&#128205; {esc(out.country)}</li>")
    if out.funding:
        meta_items.append(f"<li>&#128176; {esc(out.funding)}</li>")
    if out.deadline_window:
        meta_items.append(f"<li>&#9200; Deadline: {esc(out.deadline_window)}</li>")
    meta_html = f'<ul class="meta">{"".join(meta_items)}</ul>' if meta_items else ""

    tags = [t for t in (out.tags or []) if t]
    tags_html = (
        '<div class="tags">' + "".join(f'<span class="tag">{esc(str(t))}</span>' for t in tags) + "</div>"
        if tags
        else ""
    )

    intent = (
        f"intent://opportunitygenie.org/s/{scholarship_id}#Intent;scheme=https;"
        f"package={ANDROID_PACKAGE};S.browser_fallback_url={quote(PLAY_URL, safe='')};end"
    )

    body = f"""<div class="card">
<h1>{esc(out.name)}</h1>
<p class="provider">{esc(out.provider or "")}</p>
<p class="blurb">{esc(out.blurb or "")}</p>
{meta_html}
{tags_html}
<p class="note">To see the full details and apply, open this scholarship in the OpportunityGenie AI app.</p>
<a id="open-app" class="btn primary" href="{esc(intent, quote=True)}">Open in the app</a>
<a class="btn secondary" href="{PLAY_URL}">Get it on Google Play</a>
</div>"""

    description = (out.blurb or "A scholarship opportunity on OpportunityGenie AI.")[:200]
    page = _page(
        f"{out.name} | OpportunityGenie AI",
        description,
        body,
        canonical=f"{SITE}/s/{scholarship_id}",
    )
    return HTMLResponse(page, headers={"Cache-Control": "public, max-age=300"})
