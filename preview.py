#!/usr/bin/env python3
"""Builds self-contained preview copies with a visible build stamp."""
import base64, pathlib, re, datetime, html5lib, glob
root = pathlib.Path("site"); out = pathlib.Path("/mnt/user-data/outputs")

for f in sorted(glob.glob("site/**/*.html", recursive=True)):
    try: html5lib.HTMLParser(strict=True).parse(pathlib.Path(f).read_text(encoding="utf-8"))
    except Exception as e: print("MARKUP ERROR", f, str(e)[:140])

stamp = datetime.datetime.now().strftime("%H%M")
label = datetime.datetime.now().strftime("%d.%m.%Y, %H:%M")
BANNER = ('<div style="position:fixed;right:12px;bottom:76px;z-index:9999;background:#10231b;color:#fff;'
          'font:500 13px/1.3 system-ui,sans-serif;padding:8px 13px;border-radius:8px;'
          'box-shadow:0 6px 20px rgba(0,0,0,.28)">PREVIEW &middot; %s</div>' % label)
MIME = {"png": "image/png", "webp": "image/webp", "svg": "image/svg+xml"}

def data_uri(rel):
    p = root / rel.lstrip("/")
    return "data:" + MIME[p.suffix[1:]] + ";base64," + base64.b64encode(p.read_bytes()).decode()

css = (root / "assets/css/site.css").read_text()
js = (root / "assets/js/site.js").read_text()
names = {"cell-editor/index.html": f"landing-{stamp}.html",
         "cell-editor/privacy/index.html": f"privacy-{stamp}.html",
         "terms/index.html": f"terms-{stamp}.html",
         "support/index.html": f"support-{stamp}.html"}
for src, dst in names.items():
    h = (root / src).read_text()
    h = h.replace('<link rel="stylesheet" href="/assets/css/site.css">', f"<style>{css}</style>")
    h = h.replace('<script src="/assets/js/site.js" defer></script>', f"<script>{js}</script>")
    h = re.sub(r'(href|src|data-full)="(/assets/(?:brand|screenshots)/[\w.-]+\.(?:png|webp|svg))"',
               lambda m: f'{m.group(1)}="{data_uri(m.group(2))}"', h)
    h = h.replace('href="/cell-editor/privacy/"', f'href="{names["cell-editor/privacy/index.html"]}"')
    h = h.replace('href="/terms/"', f'href="{names["terms/index.html"]}"')
    h = h.replace('href="/terms/#main"', f'href="{names["terms/index.html"]}"')
    h = h.replace('href="/support/"', f'href="{names["support/index.html"]}"')
    h = h.replace('href="/cell-editor/"', f'href="{names["cell-editor/index.html"]}"')
    h = re.sub(r'href="/cell-editor/(#[\w-]+)"', r'href="%s\1"' % names["cell-editor/index.html"], h)
    h = h.replace("</body>", BANNER + "\n</body>")
    (out / dst).write_text(h, encoding="utf-8")
    print(dst)
for old in out.glob("*.html"):
    if stamp not in old.name: old.unlink()
print("build:", label)
