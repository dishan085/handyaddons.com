from playwright.sync_api import sync_playwright
PAGES = ["/cell-editor/", "/cell-editor/privacy/", "/terms/", "/support/"]
WIDTHS = [320, 360, 390, 430, 600, 768, 1024, 1280, 1440]
CHECK = """() => {
  const vw = document.documentElement.clientWidth;
  const bad = [];
  document.querySelectorAll('body *').forEach(el => {
    if (el.closest('.sitemenu') || el.classList.contains('skip')) return;
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return;
    if (r.right > vw + 1) bad.push(el.tagName.toLowerCase() + '.' +
      (el.className ? el.className.toString().split(' ')[0] : '') +
      ' right=' + Math.round(r.right));
  });
  return { vw, doc: document.documentElement.scrollWidth, bad: bad.slice(0, 5) };
}"""
fails = 0
with sync_playwright() as p:
    b = p.chromium.launch()
    for path in PAGES:
        row = []
        for w in WIDTHS:
            pg = b.new_page(viewport={"width": w, "height": 900})
            pg.goto("http://localhost:8765" + path, wait_until="networkidle")
            pg.wait_for_timeout(200)
            r = pg.evaluate(CHECK)
            ok = r["doc"] <= r["vw"] + 1 and not r["bad"]
            row.append(f"{w}{'ok' if ok else '!!'}")
            if not ok:
                fails += 1
                print(f"  {path} @{w}: doc={r['doc']} vw={r['vw']} {r['bad']}")
            pg.close()
        print(f"{path:26s} " + "  ".join(row))
    b.close()
print("\nПІДСУМОК:", "усе чисто" if fails == 0 else f"{fails} проблем")
