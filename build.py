#!/usr/bin/env python3
"""Generates every page of handyaddons.com from shared templates."""
import pathlib, datetime

OUT = pathlib.Path("site")
SITE = "https://handyaddons.com"
EMAIL = "pobi.olex@gmail.com"
OWNER = "handyaddons, a sole proprietorship registered in Ukraine"
OWNER_SHORT = "handyaddons"
UPDATED = "11 September 2026"

# ---------------------------------------------------------------------------
# When Google issues the Marketplace listing URL, paste it here, re-run this
# script, and every install button on the site becomes live at once.
MARKETPLACE_URL = ""
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# THE ADD-ON REGISTRY
#
# Everything that differs between add-ons lives here. To add a second add-on,
# append another dictionary: its privacy policy, its entry in the shared terms
# and its entry on the support page are all generated from these fields.
#
#   slug        the folder name, and therefore the URL
#   price       "free", or a short description of what it costs. The shared
#               terms build their pricing table from this field.
#   name        as shown to people
#   host        the Google application it lives in
#   scopes      (scope string, what it allows, why this add-on needs it)
#   absent      permissions deliberately not requested, and what that rules out
#   prefs       what the add-on remembers between sessions
#   limits      (heading, explanation) — appears in the shared terms and,
#               in summary, on the support page
#   uninstall   how to remove it
# ---------------------------------------------------------------------------

# Pixel sizes of the screenshots, so the build needs no image library.
# Regenerate with:  python3 -c "from PIL import Image;..."  if you replace a file.
SHOT_SIZES = {
    "editor.webp": (1381, 1139),
    "emoji.webp": (1600, 848),
    "formula.webp": (1530, 807),
    "hints.webp": (932, 812),
    "rich-text.webp": (1600, 845),
    "sidebar.webp": (911, 922),
}

ADDONS = [
    {
        "slug": "cell-editor",
        "name": "Cell Editor",
        "host": "Google Sheets",
        "price": "free",
        "tagline": "a full editor for the contents of a spreadsheet cell",
        "scopes": [
            ("script.container.ui",
             "Display the add-on's own interface in a sidebar or dialog inside Google Sheets.",
             "The editor window and the sidebar are that interface. Without this the add-on has nothing to draw."),
            ("spreadsheets.currentonly",
             "Read and change <b>only the one spreadsheet that is currently open</b>, and only while it is open.",
             "To read the cell you are editing, write your changes back, and let you pick ranges with the mouse."),
        ],
        "absent": ("Cell Editor does <b>not</b> request permission to see your other spreadsheets, your "
                   "Google Drive, your email, your contacts or your calendar. It also does not request "
                   "<code>script.external_request</code>, the permission an Apps Script add-on needs in order "
                   "to contact any server on the internet. Without it, the add-on is technically incapable of "
                   "transmitting your data anywhere — this is enforced by Google, not merely promised by us."),
        "prefs": ("whether you last used the sidebar or the window, your chosen font size, and the size of "
                  "the window"),
        "limits": [
            ("Firefox",
             "The separate editor window opens there as a modal dialog. It cannot be dragged, and the sheet "
             "behind it is unreachable while it is open, so ranges cannot be picked with the mouse. Use the "
             "sidebar in Firefox, or another browser for range work. This is a constraint of that browser, "
             "not a defect we can repair."),
            ("The 50 000 character limit",
             "A single Google Sheets cell holds no more than that. The editor shows a counter as you approach "
             "the limit and refuses to save past it, rather than truncating your text silently."),
            ("The validation checks are an aid, not a guarantee",
             "They catch the syntax mistakes listed on the add-on's page. A formula that passes every check "
             "can still return the wrong answer, and checking the result of your own work remains yours to do."),
        ],
        "uninstall": ("Open the Extensions menu in Google Sheets, choose Add-ons, then Manage add-ons, and "
                      "remove Cell Editor."),
    },
]


def faq_html():
    return "\n".join(
        f'    <details>\n      <summary>{q}</summary>\n      <div class="ans"><p>{a}</p></div>\n    </details>'
        for q, a in FAQ)


def faq_schema():
    """FAQPage markup, so Google can show these questions in the results."""
    import json
    items = [{"@type": "Question", "name": q,
              "acceptedAnswer": {"@type": "Answer",
                                 "text": __import__("re").sub(r"<[^>]+>", "", a)}}
             for q, a in FAQ]
    data = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": items}
    return '<script type="application/ld+json">\n' + json.dumps(data, indent=1) + "\n</script>\n"


def categories_html():
    out = []
    for name, blurb, fns in CATEGORIES:
        names = fns.split()
        chips = "".join(f"<code>{n}</code>" for n in names)
        out.append(
            f'    <details>\n'
            f'      <summary>{name}<span class="n">{len(names)}</span></summary>\n'
            f'      <div class="fns">{chips}</div>\n'
            f'    </details>')
    return "\n".join(out)


def cell_examples():
    rows = [
        ("B7", "Order status",
         '&#9989; <b>Shipped</b> &middot; &#128666; left the warehouse 12 Sep',
         "One cell carries the state and the note together, so no extra column is needed for a colored dot."),
        ("D12", "Handover procedure",
         '<ol><li>Export the monthly report</li><li>Reconcile the totals against the ledger</li>'
         '<li>Send to the client and copy the account manager</li></ol>',
         "A real numbered list inside one cell — the numbers come from the list, not typed in by hand, "
         "so inserting a step renumbers the rest."),
        ("A3", "Definition with a source",
         '<b>Net 30</b> &mdash; payment falls due thirty days after the invoice date. '
         'See the <a href="#cells">payment policy</a>.',
         "Bold on one fragment, a link on another, and the rest plain — all within one cell."),
        ("C5", "Product line with two links",
         'Steelcase Leap v2 &mdash; <a href="#cells">spec sheet</a> &middot; '
         '<a href="#cells">warranty terms</a>',
         "Google Sheets attaches one link per cell on its own. Cell Editor attaches one per fragment."),
    ]
    out = []
    for addr, label, body, note in rows:
        out.append(
            f'    <div class="cellbox">\n'
            f'      <div class="cellbox-h"><b>{addr}</b>{label}</div>\n'
            f'      <div class="cellbox-b">{body}</div>\n'
            f'      <p class="cellbox-n">{note}</p>\n'
            f'    </div>')
    return "\n".join(out)


def asset(path):
    """Appends a short hash of the file's own contents to its address.

    Browsers cache stylesheets and scripts by address. When only the contents
    change, the address stays the same and a visitor keeps the old copy — which
    looks exactly like "I published the update and nothing happened". With the
    hash in the address, a changed file gets a new address and the browser is
    obliged to fetch it; an unchanged file keeps its address and stays cached.
    """
    import hashlib
    data = (OUT / path.lstrip("/")).read_bytes()
    return f'{path}?v={hashlib.sha256(data).hexdigest()[:10]}'



def figure(name, alt, caption, cls="shot"):
    """A screenshot in its own frame. The frame carries the picture's real
    aspect ratio, so the image can never be squashed and the page does not
    shift while it loads."""
    w, h = SHOT_SIZES[name]
    return (f'<figure class="{cls}" data-full="/assets/screenshots/{name}">\n'
            f'      <div class="shot-frame" style="aspect-ratio:{w}/{h}">\n'
            f'        <img src="/assets/screenshots/{name}" width="{w}" height="{h}" '
            f'loading="lazy" decoding="async" alt="{alt}">\n'
            f'      </div>\n'
            f'      <figcaption>{caption}</figcaption>\n'
            f'    </figure>')


def install_button(label="Install from Google Workspace Marketplace"):
    if MARKETPLACE_URL:
        return f'<a class="btn btn-solid" href="{MARKETPLACE_URL}">{label}</a>'
    return '<span class="btn-pending">Install (Coming Soon)</span>'


def head(title, desc, canonical, og_image="/assets/brand/og-cell-editor.png"):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{SITE}{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="handyaddons">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{SITE}{canonical}">
<meta property="og:image" content="{SITE}{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="color-scheme" content="light">
<link rel="icon" href="/assets/brand/handyaddons.svg" type="image/svg+xml">
<link rel="icon" href="/assets/brand/handyaddons-32.png" sizes="32x32">
<link rel="icon" href="/assets/brand/handyaddons-16.png" sizes="16x16">
<link rel="apple-touch-icon" href="/assets/brand/handyaddons-apple-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600&amp;family=Roboto+Mono:wght@400;500;700&amp;display=swap" rel="stylesheet">
<link rel="stylesheet" href="{asset("/assets/css/site.css")}">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
"""


def header(nav_links=True):
    links = ""
    if nav_links:
        links = """      <a href="/cell-editor/#features">Features</a>
      <a href="/cell-editor/#formulas">Formulas</a>
      <a href="/cell-editor/#functions">Functions</a>
      <a href="/cell-editor/#checks">Checks</a>
      <a href="/cell-editor/#cells">Cells</a>
      <a href="/cell-editor/#screenshots">Screenshots</a>
      <a href="/cell-editor/#faq">FAQ</a>
      <a href="/cell-editor/#languages">Languages</a>
"""
    else:
        links = '      <a href="/cell-editor/">Cell Editor</a>\n'
    return f"""<header class="nav">
  <div class="wrap">
    <button type="button" class="menu-btn" id="menu-btn" aria-expanded="false" aria-controls="sitemenu" aria-label="Open menu">
      <span></span><span></span><span></span>
    </button>
    <a class="brand" href="/cell-editor/"><img src="/assets/brand/handyaddons-64.png" alt=""><span class="wm"><i>handy</i>addons</span></a>
    <a class="btn btn-solid btn-sm cta" href="/cell-editor/#install"><span class="long">Install (Coming Soon)</span><span class="short">Install</span></a>
    <!-- Below the breakpoint this is a slide-out panel; above it, an ordinary
         row of links. It has to sit inside the header for the wide layout to
         work, which is why the header carries no backdrop-filter: that property
         would make the header the containing block for the fixed panel and pin
         it to the header's own height. -->
    <nav id="sitemenu" class="sitemenu" aria-label="Sections">
      <div class="sitemenu-top">
        <span>Sections</span>
        <button type="button" id="menu-close" aria-label="Close menu">&#10005;</button>
      </div>
{links}    </nav>
  </div>
</header>
<div class="menu-veil" id="menu-veil" hidden></div>
"""


FOOTER = f"""<footer class="wrap">
  <div class="foot">
    <a class="brand" href="/cell-editor/"><img src="/assets/brand/handyaddons-64.png" alt=""><span class="wm"><i>handy</i>addons</span></a>
    <a href="/cell-editor/privacy/">Privacy policy</a>
    <a href="/terms/">Terms of use</a>
    <a href="/support/">Support</a>
    <span class="sp">handyaddons.com</span>
  </div>
</footer>
<button type="button" class="totop" id="totop" aria-label="Back to top">&#8593;</button>
<script src="{asset("/assets/js/site.js")}" defer></script>
</body>
</html>
"""

LIGHTBOX = """<div class="lb" id="lb" role="dialog" aria-modal="true" aria-label="Screenshot gallery">
  <div class="lb-bar">
    <span class="lb-count" id="lb-count">1 / 5</span>
    <span class="sp">
      <button type="button" id="lb-prev" aria-label="Previous screenshot">&#8592;</button>
      <button type="button" id="lb-next" aria-label="Next screenshot">&#8594;</button>
      <button type="button" id="lb-zoom">Zoom in</button>
      <button type="button" id="lbx">Close</button>
    </span>
  </div>
  <div class="lb-stage" id="lb-stage"><img id="lbi" alt=""></div>
  <p class="lb-cap" id="lb-cap"></p>
</div>
"""

LANGS = [
    ("English", "English"), ("Українська", "Ukrainian"), ("Deutsch", "German"),
    ("Français", "French"), ("Español", "Spanish"), ("Italiano", "Italian"),
    ("Nederlands", "Dutch"), ("Polski", "Polish"), ("Čeština", "Czech"),
    ("Slovenčina", "Slovak"), ("Magyar", "Hungarian"), ("Hrvatski", "Croatian"),
    ("Српски", "Serbian"), ("Български", "Bulgarian"), ("Dansk", "Danish"),
    ("Svenska", "Swedish"), ("Norsk", "Norwegian"), ("Suomi", "Finnish"),
    ("Íslenska", "Icelandic"), ("Português", "Portuguese"),
    ("Português do Brasil", "Brazilian Portuguese"), ("Русский", "Russian"),
    ("Euskara", "Basque"), ("ქართული", "Georgian"), ("Հայերեն", "Armenian"),
]

FAQ = [
    ('Is Cell Editor really free?',
     'Yes, and it stays free. There is no trial, no paid tier, no account to create and no card to enter. Install it from the Google Workspace Marketplace and use it on as many spreadsheets as you like.'),
    ('Can the add-on see my other spreadsheets?',
     'No. It asks for one permission over your documents, <code>spreadsheets.currentonly</code>, which covers only the file you have open at that moment. Your Drive, your other sheets, your email and your calendar are all outside what it can reach.'),
    ('Is my data sent anywhere?',
     "It cannot be. The add-on does not request <code>script.external_request</code>, the permission an Apps Script add-on needs before it can contact any server. Without it, Google itself blocks every outbound request. Your cell content is read and written inside your own browser and Google's runtime, and nowhere else."),
    ('Does it work in Excel or LibreOffice?',
     'No. Cell Editor is built on Google Apps Script and runs only inside Google Sheets, in a desktop browser.'),
    ('Does it work in Firefox?',
     'The sidebar does, fully. The separate window opens in Firefox as a modal dialog, so it cannot be dragged and the sheet behind it cannot be clicked — which means picking ranges with the mouse is unavailable there. Chrome, Edge and Safari have no such restriction.'),
    ('Can I put two different links in one cell?',
     'Yes, and that is one thing Google Sheets will not do on its own. Select a fragment of text, attach a link to it, then select another fragment and attach a different one. Both survive the save.'),
    ('Will it change how my formula is stored?',
     'No. Line breaks and indentation you add in the editor are part of the formula text, exactly as they would be if you typed them in the formula bar. Google Sheets ignores them when calculating, so the result is identical — the formula is simply readable afterwards.'),
    ('What happens to my text if it is too long?',
     'A Google Sheets cell holds at most 50 000 characters. A counter appears as you approach that limit and turns red past it, and the editor refuses to save rather than cutting your text off silently.'),
    ('Which languages does the interface use?',
     "Twenty-five, chosen automatically from your spreadsheet's locale — the same setting that decides whether your argument separator is a comma or a semicolon. Function descriptions are translated into twenty of them; the rest show the descriptions in English."),
    ('How do I remove it?',
     'Extensions menu, then Add-ons, then Manage add-ons, and remove Cell Editor. Your saved preferences go with it, and nothing of yours is left behind anywhere else, because nothing was ever stored outside your Google account.'),
]

CATEGORIES = [
    ('Statistical', 'Averages, distributions, regressions, counts with conditions.', 'AVEDEV AVERAGE AVERAGE.WEIGHTED AVERAGEA AVERAGEIF AVERAGEIFS BETA.DIST BETA.INV BETADIST BETAINV BINOM.DIST BINOM.INV BINOMDIST CHIDIST CHIINV CHISQ.DIST CHISQ.DIST.RT CHISQ.INV CHISQ.INV.RT CHISQ.TEST CHITEST CONFIDENCE CONFIDENCE.NORM CONFIDENCE.T CORREL COUNT COUNTA COVAR COVARIANCE.P COVARIANCE.S CRITBINOM DEVSQ EXPON.DIST EXPONDIST F.DIST F.DIST.RT F.INV F.INV.RT F.TEST FDIST FINV FISHER FISHERINV FORECAST FORECAST.LINEAR FTEST GAMMA GAMMA.DIST GAMMA.INV GAMMADIST GAMMAINV GAUSS GEOMEAN HARMEAN HYPGEOM.DIST HYPGEOMDIST INTERCEPT KURT LARGE LOGINV LOGNORM.DIST LOGNORM.INV LOGNORMDIST MARGINOFERROR MAX MAXA MAXIFS MEDIAN MIN MINA MINIFS MODE MODE.MULT MODE.SNGL NEGBINOM.DIST NEGBINOMDIST NORM.DIST NORM.INV NORM.S.DIST NORM.S.INV NORMDIST NORMINV NORMSDIST NORMSINV PEARSON PERCENTILE PERCENTILE.EXC PERCENTILE.INC PERCENTRANK PERCENTRANK.EXC PERCENTRANK.INC PERMUT PERMUTATIONA PHI POISSON POISSON.DIST PROB QUARTILE QUARTILE.EXC QUARTILE.INC RANK RANK.AVG RANK.EQ RSQ SKEW SKEW.P SLOPE SMALL STANDARDIZE STDEV STDEV.P STDEV.S STDEVA STDEVP STDEVPA STEYX T.DIST T.DIST.2T T.DIST.RT T.INV T.INV.2T T.TEST TDIST TINV TRIMMEAN TTEST VAR VAR.P VAR.S VARA VARP VARPA WEIBULL WEIBULL.DIST Z.TEST ZTEST'),
    ('Math', 'Arithmetic, trigonometry, rounding, matrices, random numbers.', 'ABS ACOS ACOSH ACOT ACOTH ASIN ASINH ATAN ATAN2 ATANH BASE CEILING CEILING.MATH CEILING.PRECISE COMBIN COMBINA COS COSH COT COTH COUNTBLANK COUNTIF COUNTIFS COUNTUNIQUE CSC CSCH DECIMAL DEGREES ERFC.PRECISE EVEN EXP FACT FACTDOUBLE FLOOR FLOOR.MATH FLOOR.PRECISE GAMMALN GAMMALN.PRECISE GCD IMLN IMPOWER IMSQRT INT ISEVEN ISO.CEILING ISODD LCM LN LOG LOG10 MOD MROUND MULTINOMIAL MUNIT ODD PI POWER PRODUCT QUOTIENT RADIANS RAND RANDARRAY RANDBETWEEN ROUND ROUNDDOWN ROUNDUP SEC SECH SEQUENCE SERIESSUM SIGN SIN SINH SQRT SQRTPI SUBTOTAL SUM SUMIF SUMIFS SUMSQ TAN TANH TRUNC'),
    ('Financial', 'Interest, depreciation, bonds, yields, cash flows.', 'ACCRINT ACCRINTM AMORLINC COUPDAYBS COUPDAYS COUPDAYSNC COUPNCD COUPNUM COUPPCD CUMIPMT CUMPRINC DB DDB DISC DOLLARDE DOLLARFR DURATION EFFECT FV FVSCHEDULE INTRATE IPMT IRR ISPMT MDURATION MIRR NOMINAL NPER NPV PDURATION PMT PPMT PRICE PRICEDISC PRICEMAT PV RATE RECEIVED RRI SLN SYD TBILLEQ TBILLPRICE TBILLYIELD VDB XIRR XNPV YIELD YIELDDISC YIELDMAT'),
    ('Engineering', 'Number-base conversion, bitwise operations, Bessel and error functions.', 'BIN2DEC BIN2HEX BIN2OCT BITAND BITLSHIFT BITOR BITRSHIFT BITXOR COMPLEX DEC2BIN DEC2HEX DEC2OCT DELTA ERF ERF.PRECISE ERFC GESTEP HEX2BIN HEX2DEC HEX2OCT IMABS IMAGINARY IMARGUMENT IMCONJUGATE IMCOS IMCOSH IMCOT IMCOTH IMCSC IMCSCH IMDIV IMEXP IMLOG IMLOG10 IMLOG2 IMPRODUCT IMREAL IMSEC IMSECH IMSIN IMSINH IMSUB IMSUM IMTAN IMTANH OCT2BIN OCT2DEC OCT2HEX'),
    ('Text', 'Splitting, joining, searching, regular expressions, case and padding.', 'ARABIC ASC CHAR CLEAN CODE CONCATENATE DOLLAR EXACT FIND FINDB FIXED JOIN LEFT LEFTB LEN LENB LOWER MID MIDB PROPER REGEXEXTRACT REGEXMATCH REGEXREPLACE REPLACE REPLACEB REPT RIGHT RIGHTB ROMAN SEARCH SEARCHB SPLIT SUBSTITUTE T TEXT TEXTJOIN TRIM UNICHAR UNICODE UPPER VALUE'),
    ('Array', 'Whole-range operations, reshaping, mapping and reducing.', 'ARRAY_CONSTRAIN ARRAYFORMULA BYCOL BYROW CHOOSECOLS CHOOSEROWS FLATTEN FREQUENCY GROWTH HSTACK LINEST LOGEST MAKEARRAY MAP MDETERM MINVERSE MMULT REDUCE SCAN SUMPRODUCT SUMX2MY2 SUMX2PY2 SUMXMY2 TOCOL TOROW TRANSPOSE TREND VSTACK WRAPCOLS WRAPROWS'),
    ('Date', 'Dates, times, weekdays, working days, differences.', 'DATE DATEDIF DATEVALUE DAY DAYS DAYS360 EDATE EOMONTH EPOCHTODATE HOUR ISOWEEKNUM MINUTE MONTH NETWORKDAYS NETWORKDAYS.INTL NOW SECOND TIME TIMEVALUE TODAY WEEKDAY WEEKNUM WORKDAY WORKDAY.INTL YEAR YEARFRAC'),
    ('Info', 'Tests for blanks, errors, types and cell properties.', 'CELL ERROR.TYPE ISBLANK ISDATE ISEMAIL ISERR ISERROR ISFORMULA ISLOGICAL ISNA ISNONTEXT ISNUMBER ISREF ISTEXT N NA SHEET SHEETS TYPE'),
    ('Lookup', 'Finding values across ranges, addresses, rows and columns.', 'ADDRESS CHOOSE COLUMN COLUMNS FORMULATEXT GETPIVOTDATA HLOOKUP INDEX INDIRECT LOOKUP MATCH OFFSET ROW ROWS VLOOKUP XLOOKUP XMATCH'),
    ('Operator', 'The function forms of +, −, ×, ÷ and the comparisons.', 'ADD CONCAT DIVIDE EQ GT GTE LT LTE MINUS MULTIPLY NE POW UMINUS UNARY_PERCENT UPLUS'),
    ('Logical', 'Conditions, error trapping, TRUE and FALSE.', 'AND FALSE IF IFERROR IFNA IFS ISBETWEEN LAMBDA LET NOT OR SWITCH TRUE XOR'),
    ('Database', 'Queries over a labelled table by criteria.', 'DAVERAGE DCOUNT DCOUNTA DGET DMAX DMIN DPRODUCT DSTDEV DSTDEVP DSUM DVAR DVARP'),
    ('Web', 'Importing from the web, URLs, hyperlinks, feeds.', 'ENCODEURL HYPERLINK IMPORTDATA IMPORTFEED IMPORTHTML IMPORTRANGE IMPORTXML ISURL'),
    ('Google', 'QUERY, GOOGLETRANSLATE, GOOGLEFINANCE, SPARKLINE and the AI function.', 'AI DETECTLANGUAGE GOOGLEFINANCE GOOGLETRANSLATE IMAGE QUERY SPARKLINE'),
    ('Parser', 'Conversion between units, dates, numbers and text.', 'CONVERT TO_DATE TO_DOLLARS TO_PERCENT TO_PURE_NUMBER TO_TEXT'),
    ('Filter', 'Filtering, sorting and removing duplicates from ranges.', 'FILTER SORT SORTN UNIQUE'),
]

FEATURES = [
    ("Sidebar or window", "A narrow panel that stays beside the sheet, or a wide resizable window for long content. One button switches, and your choice is remembered."),
    ("Colored syntax", "Functions, references, numbers, strings and brackets each take their own color, and every distinct reference gets its own shade."),
    ("Hints while you type", "Open a bracket and the function signature appears with the current argument highlighted, described in your spreadsheet's language."),
    ("Pick ranges with the mouse", "Put the cursor where the address belongs, select cells on the sheet, and the reference lands in the formula — cross-sheet names quoted correctly."),
    ("Move without closing", "Step to the next cell with the arrow keys or type an address to jump, across sheets. Unsaved changes are flagged before you leave."),
    ("Scale the text", "Enlarge the editor's font without changing the size of the characters in the cell itself. Built for long sessions and for low vision."),
    ("Rich text mode", "Bold, italic, underline, strikethrough, color, point sizes, lists, several hyperlinks inside one cell, and an emoji picker with search."),
    ("Your locale decides", "Argument and decimal separators follow your spreadsheet's own setting, and the pair in force is always shown at the bottom of the window."),
    ("Character counter", "It appears as content nears the 50 000 character cell limit and turns red past it, blocking the save rather than truncating silently."),
]

CHECKS = [
    ("e", "Unclosed quote in a text string"),
    ("e", "Unclosed quote in a sheet name"),
    ("e", "Extra closing bracket"),
    ("e", "Unclosed bracket"),
    ("e", "Too few arguments for the function"),
    ("e", "Too many arguments for the function"),
    ("e", "Unexpected character"),
    ("w", "Unknown function name — likely a typo"),
    ("w", "Nesting too deep — split it across helper cells"),
]

SHORTCUTS = [
    ("Move to the next cell", "Alt + &larr; &rarr; &uarr; &darr;"),
    ("Save and stay in the editor", "Ctrl + Enter"),
    ("Undo", "Ctrl + Z"),
    ("Redo", "Ctrl + Y"),
    ("Browse functions by category", "Ctrl + Space"),
]

SCHEMA = """<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "Cell Editor",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Web browser, Google Sheets",
  "description": "A full editor for Google Sheets cells: colored formula syntax, live function hints and nine validation checks.",
  "url": "https://handyaddons.com/cell-editor/",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "author": { "@type": "Organization", "name": "handyaddons", "url": "https://handyaddons.com/" }
}
</script>
"""


def landing():
    feats = "\n".join(
        f'    <div class="cellx"><h3>{t}</h3><p>{p}</p></div>' for t, p in FEATURES)
    checks = "\n".join(
        f'      <li><span class="tag {k}">{"error" if k=="e" else "warning"}</span>{t}</li>'
        for k, t in CHECKS)
    langs = "".join(f"<span>{native}<i>{eng}</i></span>" for native, eng in LANGS)
    cats = categories_html()
    faqs = faq_html()
    cellboxes = cell_examples()
    keys = "\n".join(
        f'    <div><span>{n}</span><kbd>{k}</kbd></div>' for n, k in SHORTCUTS)

    return head(
        "Cell Editor — a real editor for Google Sheets cells | handyaddons",
        "Cell Editor replaces the Google Sheets formula bar with a full editor: colored syntax, "
        "live function hints, nine validation checks, 516 functions recognized, 25 languages. Free.",
        "/cell-editor/",
    ) + SCHEMA + faq_schema() + header() + f"""<main id="main">

<section class="hero" id="top">
  <div class="wrap hero-grid">
    <div>
      <p class="eyebrow"><img src="/assets/brand/cell-editor-256.png" alt="" width="256" height="256"><span><b>Cell Editor</b> for Google Sheets</span></p>
      <h1>The formula bar was never big enough.</h1>
      <p class="lede">Cell Editor opens the cell you are editing into a full editor inside Google Sheets. Colored syntax, live function hints, and nine checks that catch a broken formula before it reaches the sheet.</p>
      <div class="hero-actions">
        {install_button()}
        <a class="btn btn-ghost" href="#screenshots">See it in the sheet</a>
      </div>
      <p class="free">Free. Google Sheets in a desktop browser.</p>
    </div>

    <div>
      <p class="before-cap">What Sheets gives you</p>
      <div class="fbar">
        <span class="fx">fx</span>
        <span class="line">=SORT(QUERY({{Sale1!A2:C100; Sale2!A2:C100}}, "select Col1, Col2, Col3 where Col1 is not null and Col2 &gt; 0", 0), 1, TRUE)</span>
      </div>

      <p class="after-cap">What Cell Editor gives you</p>
      {figure("editor.webp", "The Cell Editor window open over a Google Sheet, with a nested SORT and QUERY formula broken across fifteen numbered lines in colored syntax", "Formula mode: the same formula, on fifteen lines, colored by token", "shot hero-shot")}
    </div>
  </div>
</section>

<div class="strip">
  <div class="wrap">
    <div class="stat"><b data-count="516">516</b><span>functions recognized</span></div>
    <div class="stat"><b data-count="16">16</b><span>categories of functions</span></div>
    <div class="stat"><b data-count="9">9</b><span>validation checks</span></div>
    <div class="stat"><b data-count="25">25</b><span>interface languages</span></div>
    <div class="stat"><b>$0</b><span>now and later</span></div>
  </div>
</div>

<section id="features" class="wrap">
  <h2>Everything the formula bar left out</h2>
  <p class="sec-lede">One editor, two modes. Rich text for notes and descriptions, a code editor for formulas — each with its own tools.</p>
  <div class="feat reveal">
{feats}
  </div>
</section>

<section id="formulas" class="wrap">
  <h2 class="reveal">Formulas you can actually read</h2>
  <p class="sec-lede reveal">A nested QUERY inside a SORT is unreadable on one line. Broken across lines and colored by token, it is just a formula again.</p>
  {figure("formula.webp", "Cell Editor open in a window over a Google Sheet, showing a nested SORT and QUERY formula with colored syntax and line numbers", "Formula mode in a resizable window, with the text zoom controls and the launcher icon marked", "figure-full reveal")}
  <div class="points reveal">
    <div>
      <h3>Every reference in its own shade</h3>
      <p>Two ranges from two different sheets take two different colors, so a repeated reference is obvious without reading character by character.</p>
    </div>
    <div>
      <h3>Room to break it up</h3>
      <p>Line numbers down the side and line breaks wherever you want them. Brackets and quotes are colored too, which is how a missing one becomes visible.</p>
    </div>
    <div>
      <h3>The answer, as you type</h3>
      <p>The result is recalculated and shown below the editor, and the separators in force are printed at the bottom of the window.</p>
    </div>
  </div>
</section>

<section class="wrap" style="padding-top:0">
  <div class="split wide reveal">
    <div>
      <h3>Five hundred and sixteen functions, recognized by name</h3>
      <p>Press Ctrl + Space to browse by category or start typing to match. Where a function has a described signature — 450 of them do — the hint shows it and links to Google's own reference page, opened in your language.</p>
      <ul class="mini">
        <li>Argument names stay in English, matching Google's documentation</li>
        <li>Sixteen categories, from statistical to the AI function</li>
        <li>Argument counts checked against the signature wherever one exists</li>
      </ul>
    </div>
    {figure("hints.webp", "A tooltip over the formula showing the QUERY signature with the data argument highlighted and a one-line description", "The signature of the function you are inside, with the current argument highlighted", "shot")}
  </div>
</section>

<section id="functions" class="wrap">
  <h2>Sixteen categories, 516 functions</h2>
  <p class="sec-lede">The whole catalogue the editor recognises, used for autocompletion and for checking how many arguments you have passed. Open a category to see what is inside.</p>
  <div class="cats reveal">
{cats}
  </div>
</section>

<section id="cells" class="wrap">
  <h2>What one cell can hold</h2>
  <p class="sec-lede">Text mode is not decoration. These are four things a single cell can carry once you can format inside it — each one saving a column, a row, or a workaround.</p>
  <div class="cells reveal">
{cellboxes}
  </div>
</section>

<section id="checks" class="wrap">
  <h2>Nine checks, two levels</h2>
  <p class="sec-lede">Seven are errors and block the save. Two are warnings — they flag the formula and let you through.</p>
  <div class="checks reveal">
    <ul class="list">
{checks}
    </ul>
    <div class="panel">
      <div class="code-wrap">
        <div class="ln" aria-hidden="true">1</div>
<pre class="code"><span class="fn">=SUMIF</span>(<span class="ref">A2:A40</span>, <span class="err-tok err-line">"paid</span>, <span class="ref2">B2:B40</span>)</pre>
      </div>
      <div class="panel-msg">Unclosed quote in a text string. Saving is blocked until it is fixed.</div>
    </div>
  </div>
</section>

<section id="text" class="wrap">
  <h2>Cells hold more than numbers</h2>
  <p class="sec-lede">Switch to text mode for notes, descriptions and anything that needs formatting inside a single cell.</p>
  <div class="split wide reveal">
    {figure("rich-text.webp", "Cell Editor in text mode showing bold italic and colored text, numbered and bulleted lists, and a hyperlink being added", "Text mode: styles, lists and several links inside one cell", "shot")}
    <div>
      <h3>Formatting that survives the save</h3>
      <p>Bold, italic, underline and strikethrough, text color on individual fragments, and a point size that sets the real size of the characters in the cell. Lists come out as lists.</p>
      <ul class="mini">
        <li>Several hyperlinks attached to different fragments of one cell</li>
        <li>Clear formatting resets a fragment back to plain text</li>
        <li>Undo and redo inside the editor</li>
      </ul>
    </div>
  </div>
</section>

<section id="privacy-note" class="wrap" style="padding-top:0">
  <p class="note good"><b>Your spreadsheet stays yours.</b> Cell Editor asks for exactly two permissions: to draw its window inside Google Sheets, and to work with the one spreadsheet you currently have open. It has no permission to reach the internet, so it cannot send your data anywhere even in principle. The <a href="/cell-editor/privacy/">privacy policy</a> spells this out.</p>
</section>

<!-- ==========================================================
     VIDEO SECTION — switched off until the walkthrough is recorded.
     To bring it back: delete this comment opener and the closer
     below, then drop the YouTube embed into the .video block.
     The "Watch the walkthrough" button in the hero points at
     #screenshots while this is off — change it back to #video.
     ========================================================== -->
<!--
<section id="video" class="wrap">
  <h2>Three minutes, start to finish</h2>
  <p class="sec-lede">Both modes, picking ranges with the mouse, and the function browser.</p>
  <div class="video reveal">
    <div><div class="play" aria-hidden="true">&#9654;</div><p>Video walkthrough — publishing shortly</p></div>
  </div>
</section>

-->

<section id="screenshots" class="wrap">
  <h2>See it in the sheet</h2>
  <p class="sec-lede">Both surfaces, both modes. Click any image to enlarge.</p>
  <div class="gal reveal">
    {figure("sidebar.webp", "Cell Editor docked as a narrow sidebar beside the spreadsheet", "Sidebar mode, always within reach of the sheet", "shot")}
    {figure("emoji.webp", "The emoji picker open inside Cell Editor with a search field and category grid", "Emoji picker with search, inside text mode", "shot")}
    {figure("formula.webp", "Formula mode in a window over the sheet", "Formula mode in a resizable window", "shot")}
    {figure("hints.webp", "A tooltip over the formula showing the QUERY signature with the data argument highlighted and a one-line description", "The signature of the function you are inside, with the current argument highlighted", "shot")}
  </div>
</section>

<section id="languages" class="wrap">
  <h2>Twenty-five languages, chosen for you</h2>
  <p class="sec-lede">The interface, the help and the function descriptions follow your spreadsheet's locale — the same setting that decides whether your separator is a comma or a semicolon. Function descriptions are translated into twenty of the twenty-five; the rest show them in English.</p>
  <div class="langs reveal">{langs}</div>
</section>

<section id="faq" class="wrap">
  <h2>Questions people ask first</h2>
  <p class="sec-lede">Short answers. Anything not here, write to support and it gets answered the same way.</p>
  <div class="cats faq reveal">
{faqs}
  </div>
</section>

<section id="shortcuts" class="wrap">
  <h2>Keyboard</h2>
  <p class="sec-lede">On macOS, Cmd replaces Ctrl.</p>
  <div class="kbd reveal">
{keys}
  </div>
  <p class="note" style="margin-top:34px"><b>One thing to know about Firefox.</b> There the separate window opens as a modal, so it cannot be dragged and the sheet is unreachable while it is open — which means picking ranges with the mouse does not work. Use the sidebar, or another browser, for range work.</p>
</section>
</main>

<div class="close" id="install">
  <div class="wrap">
    <h2>Add it to your spreadsheet</h2>
    <p>Installs from the Google Workspace Marketplace and appears under the Extensions menu. Free, with no account to create.</p>
    {install_button("Install Cell Editor")}
  </div>
</div>

""" + LIGHTBOX + FOOTER


def privacy_page(a):
    """The privacy policy for one add-on. Everything common lives here once;
    only the scope table, the remembered preferences and the name come from
    the registry."""
    rows = "\n".join(
        f'  <tr><td data-label="Permission"><code>{code}</code></td>'
        f'<td data-label="What it allows">{allows}</td>'
        f'<td data-label="Why it is needed">{why}</td></tr>' 
        for code, allows, why in a["scopes"])
    n = len(a["scopes"])
    count = {1: "one permission", 2: "exactly two permissions"}.get(n, f"{n} permissions")

    return head(
        f'Privacy policy — {a["name"]} | handyaddons',
        f'{a["name"]} does not collect, store or transmit your data. Full privacy policy and an '
        f'explanation of every permission the add-on requests.',
        f'/{a["slug"]}/privacy/',
    ) + header(False) + f"""<main id="main" class="doc">
<h1>Privacy policy</h1>
<p class="updated">{a["name"]} for {a["host"]} &middot; last updated {UPDATED}</p>

<p class="note good" style="margin-bottom:36px"><b>In one sentence.</b> {a["name"]} does not collect, store, sell or transmit any of your data. It cannot: the add-on has no permission to make network requests, so there is nowhere for your data to go.</p>

<h2>1. What this covers</h2>
<p>This policy applies to the {a["host"]} add-on <b>{a["name"]}</b>, distributed through the Google Workspace Marketplace. Each handyaddons add-on has its own policy, because each one asks for its own permissions. The website you are reading is covered in section 8.</p>

<h2>2. Who publishes it</h2>
<p>The add-on is developed and published by {OWNER}. Under the EU General Data Protection Regulation that business is the data controller, reachable at <a href="mailto:{EMAIL}">{EMAIL}</a>. Because the add-on collects no personal data, the role has very little to do — but you are entitled to know who stands behind it, and full registration details are available on request at the same address.</p>

<h2>3. What the add-on does with your spreadsheet</h2>
<p>{a["name"]} reads the content you open in it, lets you edit that content, and writes it back. All of this happens inside Google's own infrastructure — in your browser and in the Google Apps Script runtime attached to your document.</p>
<p>Your content is never sent to handyaddons or to any third party. No copy of it is retained anywhere after you close the editor.</p>

<h2>4. The permissions we request, and why</h2>
<p>When you install {a["name"]}, Google asks you to approve {count}. There are no others.</p>
<table>
  <tr><th>Permission</th><th>What it allows</th><th>Why the add-on needs it</th></tr>
{rows}
</table>

<h3>What is deliberately absent</h3>
<p>{a["absent"]}</p>

<h2>5. What is stored, and where</h2>
<p>{a["name"]} remembers a small number of your preferences so it can open the way you left it: {a["prefs"]}. These are stored using Google's own properties service, inside your Google account, and are visible only to the add-on. They contain no document content and no personal information.</p>
<p>Removing the add-on removes these preferences with it.</p>

<h2>6. Analytics, advertising and tracking</h2>
<p>The add-on contains no analytics, no advertising, no tracking pixels and no cookies. We do not know how often you use it or what you do with it. We receive no usage reports of any kind.</p>

<h2>7. Limited use disclosure</h2>
<p>handyaddons' use and transfer of information received from Google APIs to any other app will adhere to the <a href="https://developers.google.com/terms/api-services-user-data-policy">Google API Services User Data Policy</a>, including the Limited Use requirements.</p>

<h2>8. This website</h2>
<p>handyaddons.com is a set of static pages served by GitHub Pages. It sets no cookies and runs no analytics. GitHub keeps standard server logs, which include visitors' IP addresses, as described in the <a href="https://docs.github.com/en/site-policy/privacy-policies/github-privacy-statement">GitHub Privacy Statement</a>. The site loads its typefaces from Google Fonts, which means your browser's IP address is visible to Google when a page loads.</p>

<h2>9. Your rights</h2>
<p>The GDPR gives you the right to ask what personal data is held about you, to have it corrected or erased, to object to its processing, and to receive a copy of it. The same rights, under different names, exist in the UK, California and a growing number of other places.</p>
<p>In our case the honest answer to all of them is the same: we hold nothing to show you, correct, or erase. We have no account for you, no record of your use of the add-on, and no copy of anything from your documents. The preferences described in section 5 live inside your own Google account and disappear when you remove the add-on.</p>
<p>You are welcome to ask anyway, at <a href="mailto:{EMAIL}">{EMAIL}</a>, and we will answer within thirty days. If the answer does not satisfy you, you may complain to your national data protection authority.</p>

<h2>10. Links to other places</h2>
<p>The add-on links to Google's own reference pages, and this site links to Google's policies and to the Marketplace. Those destinations are not ours, and their own privacy practices apply once you arrive there.</p>

<h2>11. Children</h2>
<p>{a["name"]} is a productivity tool and is not directed at children. We do not knowingly collect information from anyone, including children.</p>

<h2>12. Changes to this policy</h2>
<p>If the add-on ever requests a new permission or begins handling data differently, this page will be updated before that change reaches you, and the date at the top will change with it.</p>

<h2>13. Contact</h2>
<p>Questions about this policy, or about anything the add-on does with your data: <a href="mailto:{EMAIL}">{EMAIL}</a>. We answer in English and Ukrainian.</p>

<p style="margin-top:40px"><a href="/{a["slug"]}/">Back to {a["name"]}</a> &middot; <a href="/terms/">Terms of use</a> &middot; <a href="/support/">Support</a></p>
</main>
""" + FOOTER


def limits_html():
    """The known-limitations section of the shared terms, one block per add-on.
    A new add-on appends its own block here simply by joining the registry."""
    out = []
    for a in ADDONS:
        items = "\n".join(
            f'<p><b>{h}.</b> {txt}</p>' for h, txt in a["limits"])
        out.append(f'<h3>{a["name"]}</h3>\n{items}')
    return "\n\n".join(out)


def terms_page():
    names = [a["name"] for a in ADDONS]
    listed = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
    plural = "add-on" if len(names) == 1 else "add-ons"

    return head(
        "Terms of use | handyaddons",
        "Terms of use for the handyaddons add-ons: the license granted, the warranty "
        "position, limitation of liability and the known limitations of each add-on.",
        "/terms/",
    ) + header(False) + f"""<main id="main" class="doc">
<h1>Terms of use</h1>
<p class="updated">All handyaddons {plural} &middot; last updated {UPDATED}</p>

<p>These terms govern your use of the {plural} published by {OWNER} — at present {listed}. Installing or using an add-on means you accept them. If you do not accept them, uninstall it.</p>
<p>How each add-on handles data is set out in its own privacy policy, because each one asks for its own permissions. For {ADDONS[0]["name"]} that is the <a href="/{ADDONS[0]["slug"]}/privacy/">{ADDONS[0]["name"]} privacy policy</a>, which forms part of these terms.</p>

<h2>1. What you are getting</h2>
<p>Each add-on is a tool that runs inside a Google application and does the job described on its page on this site. They are provided free of charge, for personal and commercial use alike, with no account to create and no subscription.</p>
<p>We may change, add or remove features at any time. If a feature you depend on is going away, we will try to say so on this site first, but we cannot promise notice in every case.</p>

<h2>2. Your license</h2>
<p>The add-ons themselves — their code, their interfaces and their texts — remain the property of the publisher. Nothing here transfers ownership of them to you.</p>
<p>What you receive is a license to use them: personal or commercial, worldwide, free of charge, non-exclusive and non-transferable, on as many documents and in as many accounts as you like, for as long as these terms are in force. The license is revocable, but in practice the only thing that would end it is your breaking the rules in the next section.</p>
<p>Note that this is a real commercial license, not a "personal, non-commercial viewing" permission of the kind that boilerplate website terms often grant by accident. Using a handyaddons add-on at work, inside a company, is exactly what it is for.</p>

<h2>3. What you may not do</h2>
<p>You may not resell an add-on, redistribute it as your own, decompile or reverse engineer it, strip out its authorship notices, or use it to do anything unlawful or to interfere with Google's services.</p>

<h2>4. Your data and your documents</h2>
<p>Your content remains entirely yours. We neither claim rights over it nor receive a copy of it. The privacy policy of each add-on describes exactly what it touches and what it remembers.</p>

<h2>5. Provided as is</h2>
<p>The add-ons are provided as is and as available, without warranty of any kind, whether express or implied, including any implied warranty of merchantability, fitness for a particular purpose, or non-infringement. We do not warrant that they will be uninterrupted, error free, or compatible with every browser, locale or document.</p>

<h2>6. Back up your work</h2>
<p>These add-ons write to your documents. Google keeps its own version history, and we strongly recommend relying on it. Keep backups of anything you cannot afford to lose, as you would with any tool that edits your files.</p>

<h2>7. Limitation of liability</h2>
<p>To the fullest extent permitted by law, handyaddons and its developer will not be liable for any indirect, incidental, special or consequential damages, nor for any loss of data, profits, revenue or business, arising out of or connected with your use of or inability to use an add-on — even if we have been advised that such damages are possible.</p>
<p>Nothing in these terms limits liability that cannot be limited under applicable law.</p>

<h2>8. Known limitations</h2>
<p>Every add-on has boundaries it cannot cross, usually imposed by a browser or by Google itself. They are listed here, by add-on, so that nothing in section 5 comes as a surprise.</p>

{{limits}}

<h2>9. Not affiliated with Google</h2>
<p>These are independent add-ons. handyaddons is not affiliated with, endorsed by or sponsored by Google LLC. Google, Google Sheets and Google Workspace are trademarks of Google LLC. Your use of Google's own applications remains governed by your agreement with Google.</p>

<h2>10. Ending it</h2>
<p>You may stop using an add-on at any time by removing it from the Extensions menu or from your Google Workspace Marketplace app list. We may discontinue an add-on, in whole or in part, at any time.</p>

<h2>11. Changes to these terms</h2>
<p>These terms may be updated, including when a new add-on is added to the list above. The date at the top of this page shows when they last changed. Continuing to use an add-on after a change means you accept the revised terms.</p>

<h2>12. Governing law</h2>
<p>These terms are governed by the laws of Ukraine, the country in which the publisher is registered, without regard to conflict of law rules.</p>

<h2>13. Contact</h2>
<p>Questions, bug reports and feature requests: <a href="mailto:{EMAIL}">{EMAIL}</a>, or see the <a href="/support/">support page</a>.</p>
</main>
""" + FOOTER


def support_page():
    rows = "\n".join(
        f'  <li><b>{a["name"]}</b> — <a href="/{a["slug"]}/">what it does</a>, '
        f'<a href="/{a["slug"]}/privacy/">privacy policy</a></li>' for a in ADDONS)
    uninst = "\n".join(f'<p><b>{a["name"]}.</b> {a["uninstall"]}</p>' for a in ADDONS)

    return head(
        "Support | handyaddons",
        "How to get help with a handyaddons add-on: contact, response times, what to "
        "include in a bug report and how to uninstall.",
        "/support/",
    ) + header(False) + f"""<main id="main" class="doc">
<h1>Support</h1>
<p class="updated">All handyaddons add-ons &middot; last updated {UPDATED}</p>

<p>These add-ons are built and supported by a single developer. There is no ticket system and no chatbot in between — you write, and the person who wrote the code reads it.</p>

<h2>Get in touch</h2>
<p>Email <a href="mailto:{EMAIL}">{EMAIL}</a> for bug reports, questions, feature requests and anything else. Messages in English and Ukrainian are both welcome.</p>
<p>Expect a reply within two working days. A fix takes as long as the bug deserves; if something blocks your work, say so in the subject line and it goes to the front of the queue.</p>

<h2>What to include in a bug report</h2>
<p>You do not have to write any of this — a sentence saying what went wrong is already useful. But the more of the following you include, the faster it gets fixed:</p>
<ul>
  <li>Which add-on, and which browser on which operating system.</li>
  <li>Where you were working: the sidebar or a separate window, and which mode.</li>
  <li>The content involved, if you are able to share it. A screenshot works too.</li>
  <li>Your document's locale, if the problem concerns separators or number formats. It is under File, then Settings.</li>
  <li>What you expected to happen, and what happened instead.</li>
</ul>
<p>Please do not send the document itself, and please strip anything confidential out of screenshots. Nothing in a support message is needed to identify you, and nothing sent this way is stored beyond the email thread.</p>

<h2>Before you write</h2>
<p>Some things are boundaries rather than bugs — a browser restriction, or a limit Google imposes on its own documents. Each add-on's are listed in the <a href="/terms/#main">known limitations section of the terms of use</a>. The most common one by far: in Firefox, an add-on window opens as a modal dialog, so it cannot be dragged and the document behind it cannot be clicked.</p>

<h2>The add-ons</h2>
<ul>
{rows}
</ul>

<h2>Uninstalling</h2>
{uninst}
<p>Your preferences go with the add-on. Nothing of yours is left behind anywhere, because nothing of yours was ever held outside your own Google account.</p>

<h2>The documents</h2>
<p>Each add-on's privacy policy explains what that add-on does and does not do with your data. The <a href="/terms/">terms of use</a> cover the license, the warranty position and the known limitations, and apply to every add-on.</p>
</main>
""" + FOOTER


REDIRECT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>handyaddons</title>
<link rel="canonical" href="https://handyaddons.com/cell-editor/">
<meta http-equiv="refresh" content="0; url=/cell-editor/">
<link rel="icon" href="/assets/brand/handyaddons-32.png">
<script>location.replace('/cell-editor/');</script>
</head>
<body>
<p>Redirecting to <a href="/cell-editor/">Cell Editor</a>&hellip;</p>
</body>
</html>
"""

NOT_FOUND = head(
    "Page not found | handyaddons", "This page does not exist on handyaddons.com.", "/404.html"
) + header(False) + """<main id="main" class="doc">
<h1>That page is not here</h1>
<p class="updated">Error 404</p>
<p>The address you followed does not exist on this site. It may have been renamed, or the link that brought you here may have a typo in it.</p>
<p><a href="/cell-editor/">Go to Cell Editor</a></p>
</main>
""" + FOOTER

SITEMAP = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{SITE}/cell-editor/</loc><lastmod>{datetime.date.today()}</lastmod><priority>1.0</priority></url>
""" + "".join(
    f'  <url><loc>{SITE}/{a["slug"]}/privacy/</loc><lastmod>{datetime.date.today()}</lastmod><priority>0.5</priority></url>\n'
    for a in ADDONS) + f"""  <url><loc>{SITE}/terms/</loc><lastmod>{datetime.date.today()}</lastmod><priority>0.5</priority></url>
  <url><loc>{SITE}/support/</loc><lastmod>{datetime.date.today()}</lastmod><priority>0.6</priority></url>
</urlset>
"""

ROBOTS = f"""User-agent: *
Allow: /

Sitemap: {SITE}/sitemap.xml
"""

README = f"""# handyaddons.com

The website for handyaddons — add-ons for Google Sheets. Plain static HTML, no build step.
GitHub Pages serves these files exactly as they are.

## Pages

| Address | File |
|---|---|
| handyaddons.com | `index.html` — redirects to the Cell Editor page |
| handyaddons.com/cell-editor/ | `cell-editor/index.html` — the landing page |
| handyaddons.com/cell-editor/privacy/ | `cell-editor/privacy/index.html` — one policy per add-on |
| handyaddons.com/terms/ | `terms/index.html` — shared by every add-on |
| handyaddons.com/support/ | `support/index.html` — shared by every add-on |

All of these are generated by `build.py`. Edit that file, not the HTML, then run
`python3 build.py`. Everything an add-on does not share with the others — its
permissions, its known limitations, how to uninstall it — lives in the `ADDONS`
list at the top of the script. A second add-on is a second dictionary there.

`/cell-editor/` is the permanent address of the add-on's page, because the add-on's own
Help window links to it. The root of the site redirects there for now; when a second add-on
arrives, the root becomes a catalogue instead and the redirect is removed.

## Changing text

Open the file on GitHub, press the pencil icon, edit, then press "Commit changes".
The live site updates within a minute or two.

## When Google issues the Marketplace link

Every install button is currently a grey non-clickable label. To turn them all into
real buttons, find this line in `cell-editor/index.html` (it appears twice):

    <span class="btn-pending">Publishing to the Google Workspace Marketplace</span>

and replace it with:

    <a class="btn btn-solid" href="PASTE-THE-MARKETPLACE-URL-HERE">Install from Google Workspace Marketplace</a>

## Adding the video

In `cell-editor/index.html`, find the block with `class="video"` and replace its contents
with the YouTube embed code. The surrounding section, heading and anchor `#video` stay as they are.

## Files you should not delete

- `CNAME` — holds the domain name. Deleting it disconnects the site from handyaddons.com.
- `.nojekyll` — stops GitHub from trying to process the files as a blog.
- `404.html` — shown for addresses that do not exist.
"""


def write(path, text):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    print(f"  {path:44s} {len(text):>7,} bytes")


print("Generating handyaddons.com")
write("cell-editor/index.html", landing())
for _a in ADDONS:
    write(f"{_a['slug']}/privacy/index.html", privacy_page(_a))
write("terms/index.html", terms_page().replace("{limits}", limits_html()))
write("support/index.html", support_page())
write("index.html", REDIRECT)
write("404.html", NOT_FOUND)
write("sitemap.xml", SITEMAP)
write("robots.txt", ROBOTS)
# README.md is maintained by hand at the repository root, not generated
write("CNAME", "handyaddons.com\n")
write(".nojekyll", "")
print("done")
