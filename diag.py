from playwright.sync_api import sync_playwright
import sys

URL = "http://localhost:8765/cell-editor/"
WIDTHS = [(390, "phone"), (768, "tablet"), (1280, "desktop")]

FIND_OVERFLOW = """
() => {
  const vw = document.documentElement.clientWidth;
  const out = [];
  document.querySelectorAll('body *').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return;
    if (r.right > vw + 1 || r.left < -1) {
      out.push({
        tag: el.tagName.toLowerCase(),
        cls: (el.className && el.className.toString().slice(0, 40)) || '',
        left: Math.round(r.left), right: Math.round(r.right),
        w: Math.round(r.width),
        scrollW: el.scrollWidth, clientW: el.clientWidth
      });
    }
  });
  return { vw, docW: document.documentElement.scrollWidth, items: out.slice(0, 25) };
}
"""

with sync_playwright() as p:
    b = p.chromium.launch()
    for w, name in WIDTHS:
        pg = b.new_page(viewport={"width": w, "height": 900}, device_scale_factor=2)
        pg.goto(URL, wait_until="networkidle")
        pg.wait_for_timeout(600)
        res = pg.evaluate(FIND_OVERFLOW)
        print(f"\n=== {name} {w}px ===")
        print(f"viewport {res['vw']}  document scrollWidth {res['docW']}",
              "  ПЕРЕВИЩЕННЯ" if res['docW'] > res['vw'] + 1 else "  ok")
        if not res["items"]:
            print("  жоден елемент не виходить за межі")
        for it in res["items"]:
            print(f"  {it['tag']:6s} .{it['cls']:34s} left={it['left']:5d} right={it['right']:5d} w={it['w']:5d}")
        pg.screenshot(path=f"/home/claude/shot-{name}.png", full_page=False)
        pg.close()
    b.close()
print("\nзнімки збережено")
