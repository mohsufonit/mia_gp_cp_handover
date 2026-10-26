"""
Builds handover/index.html (Collection page tab + Gifting page WIP tab) in the Troopod handover style.

Inputs  : ../../figma-export/{states.csv, HANDOVER-CARDS.md, QUESTIONS.md, desktop-1440/, mobile-390/}
          reference brand CSS + logos from the two earlier docs (mia_gp_handover, mia_poa), cloned to REF
Outputs : ../index.html and ../assets/frames/*.webp|jpg
Run     : python -I -X utf8 build_handover.py <REF dir containing gp/ and poa/>
"""
import csv
import html
import os
import re
import sys

from PIL import Image

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, ".."))
FX = os.path.abspath(os.path.join(HERE, "..", "..", "figma-export"))
REF = sys.argv[1]
ASSETS = os.path.join(OUT, "assets", "frames")
os.makedirs(os.path.join(ASSETS, "desktop"), exist_ok=True)
os.makedirs(os.path.join(ASSETS, "mobile"), exist_ok=True)

FIGMA = "https://www.figma.com/design/qGeAfcHPwMm86maQRkLyvt/Mia---Collection-Page?node-id=49-2"
PROTO = "https://mohsufonit.github.io/mia_cp/"

SECTIONS = {
    1: "Full Page", 2: "Header", 3: "Hero Carousel", 4: "Trust Ticker", 5: "Breadcrumb and Title",
    6: "Filters and Sort", 7: "Quick Filters and Result Count", 8: "Product Grid and Cards", 9: "Image Viewer",
    10: "Size Sheet and Mini-cart", 11: "Compare Tray and Modal", 12: "Break: Recently Viewed",
    13: "Break: Gifting Banner", 14: "Break: Mia Fiora Spotlight", 15: "Break: Store Finder",
    16: "Break: Dhanteras and Diwali", 17: "Break: Shop by Metal", 18: "Break: Shop by Gemstones",
    19: "Break: Complete Your Ring Stack", 20: "Break: Karatage", 21: "Break: Budget",
    22: "Break: Visit the Store", 23: "Pagination and Result Count", 24: "Recommendations Rail", 25: "FAQ",
    26: "Ring Guide (SEO text)", 27: "Footer", 28: "Popups and Sticky Elements",
}


def esc(t):
    return html.escape(t, quote=False)


def md(t):
    """escape, then turn **bold** into <b>"""
    t = esc(t).replace("`", "")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)


# ------------------------------------------------------------------ brand assets
gp = open(os.path.join(REF, "gp", "index.html"), encoding="utf-8").read()
poa = open(os.path.join(REF, "poa", "index.html"), encoding="utf-8").read()
BRAND_CSS = re.findall(r"<style>(.*?)</style>", gp, flags=re.S)[0]
logos = re.findall(r'<img src="(data:image/svg\+xml;base64,[^"]+)"', poa)
LOGO_T, LOGO_M = logos[0], logos[1]
GP_PNG = re.search(r'<img src="(data:image/png;base64,[^"]+)"', gp).group(1)

# ------------------------------------------------------------------ frames (webp, collapsed in the page)
rows = list(csv.DictReader(open(os.path.join(FX, "states.csv"), encoding="utf-8")))
FRAMES = {}  # sec -> {"Desktop": [(code, state, desc, relpath)], "Mobile": [...]}


def save(src, dest, maxw, fmt="WEBP"):
    im = Image.open(src).convert("RGB")
    if im.size[0] > maxw:
        k = maxw / im.size[0]
        im = im.resize((maxw, round(im.size[1] * k)), Image.LANCZOS)
    if fmt == "WEBP":
        im.save(dest, "WEBP", quality=78, method=6)
    else:
        im.save(dest, "JPEG", quality=76, optimize=True)
    return im.size


for r in rows:
    dev = r["device"]
    sec = int(r["code"].split(".")[0])
    idx = int(r["code"].split(".")[1])
    if sec == 1:
        continue  # full pages are handled below
    d = "desktop" if dev == "Desktop" else "mobile"
    rel = "assets/frames/%s/%02d-%02d.webp" % (d, sec, idx)
    w, h = save(os.path.join(FX, r["file"]), os.path.join(OUT, rel), 1000 if d == "desktop" else 390)
    FRAMES.setdefault(sec, {"Desktop": [], "Mobile": []})[dev].append((r["code"], r["state"], r["description"], rel, w, h))

# full pages: page 1 + page 2, desktop (JPEG, 900 wide) and mobile (parts stitched, JPEG)
fp = FRAMES.setdefault(1, {"Desktop": [], "Mobile": []})
for i, (fn, label, desc) in enumerate([("01-page-1-full.png", "Page 1", "Page 1 of the grid (rings 1 to 28) with its breaks."),
                                       ("02-page-2-full.png", "Page 2", "Page 2 of the grid (rings 29 to 54) with the page 2 breaks.")], 1):
    rel = "assets/frames/desktop/01-%02d.jpg" % i
    w, h = save(os.path.join(FX, "desktop-1440", "01-full-page", fn), os.path.join(OUT, rel), 900, "JPEG")
    fp["Desktop"].append(("01.%d" % i, label + " full", desc, rel, w, h))
for i, parts in enumerate([("01-page-1-full-part-1-of-2.png", "02-page-1-full-part-2-of-2.png"),
                           ("03-page-2-full-part-1-of-2.png", "04-page-2-full-part-2-of-2.png")], 1):
    ims = [Image.open(os.path.join(FX, "mobile-390", "01-full-page", p)).convert("RGB") for p in parts]
    big = Image.new("RGB", (ims[0].size[0], sum(x.size[1] for x in ims)), (255, 255, 255))
    y = 0
    for x in ims:
        big.paste(x, (0, y))
        y += x.size[1]
    tmp = os.path.join(HERE, "_tmp_full.png")
    big.save(tmp)
    rel = "assets/frames/mobile/01-%02d.jpg" % i
    w, h = save(tmp, os.path.join(OUT, rel), 390, "JPEG")
    fp["Mobile"].append(("01.%d" % i, "Page %d full" % i, "Whole page %d on a phone." % i, rel, w, h))
    os.remove(tmp)


def frames_html(sec):
    f = FRAMES.get(sec)
    if not f:
        return ""
    nd, nm = len(f["Desktop"]), len(f["Mobile"])
    out = ['<details class="frames"><summary><span>Frames for this section</span><em>%d desktop &middot; %d mobile</em><i class="arrow">&#9662;</i></summary><div class="frames-body">' % (nd, nm)]
    for dev, label in (("Desktop", "Desktop, 1440 wide"), ("Mobile", "Mobile, 390 wide")):
        if not f[dev]:
            continue
        out.append('<div class="fgrp"><div class="flab">%s</div><div class="fwrap %s">' % (label, dev.lower()))
        for code, state, desc, rel, w, h in f[dev]:
            fw = min(w, 260) if dev == "Mobile" else min(w, 1000)
            out.append('<figure style="--fw:%dpx"><a href="%s" target="_blank" rel="noopener"><img loading="lazy" decoding="async" src="%s" width="%d" height="%d" alt="%s"></a><figcaption><b>%s &middot; %s</b><span>%s</span></figcaption></figure>'
                       % (fw, rel, rel, w, h, esc(code + " " + state + " " + dev), esc(code), esc(state), esc(desc)))
        out.append("</div></div>")
    out.append("</div></details>")
    return "".join(out)


# ------------------------------------------------------------------ cards -> structured modules
cards_md = open(os.path.join(FX, "HANDOVER-CARDS.md"), encoding="utf-8").read()
q_md = open(os.path.join(FX, "QUESTIONS.md"), encoding="utf-8").read()

LEAD = re.compile(r"^\*\*([^*]+?)\*\*\s*(.*)$")
FIELD_OF = [
    ("what it does", "does"), ("what you can change", "change"), ("where it goes", "where"),
    ("edge cases", "edge"), ("rules", "rules"), ("important", "rules"), ("page order", "does"),
    ("page 2", "does"), ("design notes", "notes"),
]


def field_for(label):
    l = label.lower().strip(". ")
    for k, v in FIELD_OF:
        if l.startswith(k):
            return v
    return None


MODS = {}
parts = re.split(r"^## (\d\d) · (.*)$", cards_md, flags=re.M)
for i in range(1, len(parts), 3):
    n = int(parts[i])
    title = parts[i + 1].strip()
    body = parts[i + 2].split("\n---")[0]
    meta = re.search(r"\*\*Priority\*\* (P\d) · \*\*Status\*\* (.+)", body)
    prio, status = (meta.group(1), meta.group(2).strip()) if meta else ("", "")
    fields = {k: [] for k in ("does", "change", "where", "edge", "rules", "notes", "extra")}
    cur = "extra"
    for ln in body.split("\n"):
        s = ln.strip()
        if not s or s.startswith("**Priority**") or s.startswith("> "):
            continue
        m = LEAD.match(s)
        if m and field_for(m.group(1)):
            cur = field_for(m.group(1))
            rest = m.group(2).strip()
            if cur == "rules":
                fields[cur].append(("h", m.group(1).strip(". ")))
            if rest:
                fields[cur].append(("p", rest))
            continue
        if s.startswith("- "):
            fields[cur].append(("b", s[2:]))
        elif re.match(r"^\d+\.\s", s):
            fields[cur].append(("n", re.sub(r"^\d+\.\s", "", s)))
        else:
            fields[cur].append(("p", s))
    MODS[n] = dict(title=title, prio=prio, status=status, f=fields)


def render_items(items):
    out, buf, kind = [], [], None

    def flush():
        nonlocal buf, kind
        if buf:
            tag = "ol" if kind == "n" else "ul"
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % md(x) for x in buf), tag))
            buf, kind = [], None
    for k, t in items:
        if k == "h":
            flush()
            out.append('<p class="sub"><b>%s</b></p>' % md(t))
        elif k == "p":
            flush()
            out.append("<p>%s</p>" % md(t))
        else:
            if kind and kind != k:
                flush()
            kind = k
            buf.append(t)
    flush()
    return "".join(out)


# questions keyed by section
Q_BY_SEC, Q_GROUPS = {}, []
grp = None
for ln in q_md.split("\n"):
    h = re.match(r"^## (.*)$", ln)
    if h:
        grp = (h.group(1).strip(), [])
        Q_GROUPS.append(grp)
        continue
    qm = re.match(r"^(\d+)\.\s+(.*)$", ln)
    if qm and grp is not None:
        num, txt = int(qm.group(1)), qm.group(2)
        grp[1].append((num, txt))
        refs = set()
        for g in re.findall(r"\(([0-9, ]{2,40})\)", txt):
            for x in re.findall(r"\d+", g):
                if 1 <= int(x) <= 28:
                    refs.add(int(x))
        for s in refs:
            Q_BY_SEC.setdefault(s, []).append((num, txt))

PURPOSE_FALLBACK = {
    6: "Lets the shopper narrow the list and change its order: a left rail on desktop, a bottom bar with a sheet on a phone.",
    10: "Asks for a ring size before anything goes to the bag, then confirms the add with a mini-cart.",
    15: "Lets a shopper find stores, and the rings in stock, near a pincode.",
    28: "The popups and the always-on layers that sit over or around the page.",
}

PRIO_LABEL = {"P0": "P0 blocks launch", "P1": "P1 ships with launch", "P2": "P2 follows launch"}


def status_class(s):
    k = s.split()[0].strip(",(").upper() if s else ""
    return {"BUILT": "ok", "SIMULATED": "sim", "PLACEHOLDER": "ph"}.get(k, "ok")


def module_html(n):
    m = MODS[n]
    f = m["f"]
    out = ['<details class="mod" id="m%02d"><summary><div class="mod-title"><span class="mod-num">%02d</span><h3>%s</h3></div>' % (n, n, esc(m["title"]))]
    out.append('<div class="chips"><span class="pill p%s">%s</span><span class="pill %s">%s</span></div><span class="arrow">&#9662;</span></summary><div class="mod-body">' % (m["prio"][-1:], esc(PRIO_LABEL.get(m["prio"], m["prio"])), status_class(m["status"]), esc(m["status"])))
    does = f["does"]
    if does and does[0][0] == "p":
        purpose, logic = [does[0]], does[1:] + f["rules"]
    else:  # the card opens with a list: use a one-line purpose and keep the whole list as the logic
        purpose = [("p", PURPOSE_FALLBACK.get(n, ""))] if PURPOSE_FALLBACK.get(n) else []
        logic = does + f["rules"]
    if purpose:
        out.append('<div class="field"><div class="lbl">Purpose</div>%s</div>' % render_items(purpose))
    if logic:
        out.append('<div class="field"><div class="lbl">Core logic</div>%s</div>' % render_items(logic))
    if f["change"]:
        out.append('<div class="field"><div class="lbl">Data needed and what the team can change</div>%s</div>' % render_items(f["change"]))
    if f["where"]:
        out.append('<div class="field"><div class="lbl">Where it goes</div>%s</div>' % render_items(f["where"]))
    if f["edge"]:
        out.append('<div class="edge-box"><div class="lbl">Edge cases</div>%s</div>' % render_items(f["edge"]))
    if f["notes"]:
        out.append('<div class="open-box note"><div class="lbl">Design notes from Page 1</div>%s</div>' % render_items(f["notes"]))
    qs = Q_BY_SEC.get(n, [])
    if qs:
        out.append('<div class="open-box"><div class="lbl">Open decisions</div><ul>%s</ul></div>' % "".join("<li><b>Q%d.</b> %s</li>" % (a, md(b)) for a, b in qs))
    out.append(frames_html(n))
    out.append("</div></details>")
    return "".join(out)


# ------------------------------------------------------------------ strategy content (authored)
VISUAL = [
    ("Pink where it is a banner, a light tint where the products are the point",
     "The client's first review feedback was that the page read as too flashy and that the background pulled focus from the categories and products (the audience is mainly women of roughly 28 to 35). So the strong pink is kept for true banners (the gifting banner), and the sections whose job is to show product (Shop by Metal, Shop by Gemstones, the Mia Fiora strip, Dhanteras and Diwali, Store finder and the page 2 breaks) sit on a light pink tint with a faint grid, so the swatches, tiles and photographs carry the colour."),
    ("Gold and yellow do not go with the pink",
     "The client was clear that yellow and pink clash. Wherever a button or label sits next to the pink, it is white with pink text, never gold. The Dhanteras and Diwali block lost its gold-foil lettering for the same reason."),
    ("Two button styles, used everywhere",
     "Primary is pink with white text. Secondary is white with pink text and a pink outline, which switches on hover. On a pink banner the button is white with pink text. A grey outlined button reads as disabled, so none are left (the \"View ring\" button in the recommendation row was the last one)."),
    ("The same pink across the main pages",
     "Home, collection, product, bag and checkout all use the site's defined pink. Only the Gifting and Diwali pages are free to play with colour. This page was brought back to the site pink after an earlier, brighter version."),
    ("The same gap above and below every break",
     "Every break clears the rings by exactly one row gap: 32px on desktop and tablet, 28px on a phone. An earlier version had 38px above a banner and 10px below it, which the client noticed."),
    ("One title size, centred swatch sections",
     "\"All 495 rings, your way\" was too loud next to the section titles, so it is smaller and sits under a breadcrumb. The Shop by Metal and Shop by Gemstones titles are centred on the same line as their swatch row and their products."),
]

PERSONAS = [
    ("The diamond shortlister", "Needs to narrow a large list quickly, see what a price is made of, and often see the piece in a store before buying.",
     "13,992 diamond pieces were added to bag in four weeks, more than any other type, and only about 1 in 100 was bought. On phones just 6.0% of diamond pieces added to bag reach checkout, against 22.5% on desktop. 5,642 people asked a store to call them in the same period, six for every online buyer. (Mia's website data, four weeks to 15 October 2026, from the CRO and growth plan.)",
     "Stone and karat filters, the price breakdown on every card, compare, the store finder and the Visit the store form."),
    ("The gold and coin buyer", "Wants a known weight at today's rate, quickly, with a purity they trust.",
     "57,249 visits landed on the gold rate page in four weeks and only 3 purchases followed. \"Gold coin\" and \"Silver coin\" are the top site searches. (Same source.)",
     "The Dhanteras and Diwali tiles with \"Today's gold rate\", the Karatage tiles and Shop by Metal."),
    ("The gifter", "Buys for someone else, usually without knowing size or taste; needs a safe starting point and a budget.",
     "\"Under ₹15K\" is the most clicked price tile on the site, and 60% of the visitors Google can identify are men. 3,333 people had a birthday or anniversary code refused, most likely shopping for someone's occasion. (Same source.) The prototype's own notes record that around 30% of buyers are gift-motivated.",
     "The Gifting quick chip, the gifting banner, the Budget bands and the ring sizer."),
    ("The first-time buyer", "Has not bought from Mia before and needs proof: hallmark, certificate, returns, delivery.",
     "94% of website buyers are first-time buyers. (Same source.)",
     "The trust strip, the price breakdown, the FAQ and the ring guide."),
    ("The returning member", "Comes back for something they saw before, and wants to pick up where they stopped.",
     "Returning visitors on desktop who start on the homepage convert at 1.18%, the highest of any group. (Same source.)",
     "Recently viewed, wishlist and compare."),
]

STAGES = [
    ("Stage 1", "Arrival and orientation", [2, 3, 4, 5]),
    ("Stage 2", "Narrowing the list", [6, 7]),
    ("Stage 3", "Browsing and deciding", [8, 9, 11, 10]),
    ("Stage 4", "Curated breaks between the rings", [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]),
    ("Stage 5", "Closing and reassurance", [23, 24, 25, 26, 27, 28]),
]

WHY = {
    1: ("Everyone", "Shows the order a shopper meets things in. The breaks are placed on whole rows of four rings, so a desktop row never ends half-filled, and they travel with the rings they introduce, so page 2 opens with Shop by Gemstones."),
    2: ("Cold visitor", "Familiar site chrome so the shopper never feels they have left Mia, with Rings marked as the current page. Search is first-class because on the homepage it is the first thing visitors use (6,460 uses in four weeks)."),
    3: ("Cold visitor", "Sets the offer and the mood in the first viewport. Two slides are video so a ring is seen in movement; the rest show one ring with its price and offer and go straight to that ring."),
    4: ("First-time buyer", "Answers the quiet questions (hallmark, delivery, warranty, returns, certified diamonds) before the shopper has to ask. 94% of buyers are first-time buyers."),
    5: ("Everyone", "Orients the shopper (Home, then Rings) and gives search engines the same trail. The title is deliberately smaller than the section titles, per the client's feedback, so the rings lead."),
    6: ("Diamond shortlister", "Replaces a drag price slider with tap-friendly chips (the prototype's note records under 20% mobile completion for the slider). On desktop the filters stay in view as a left rail; on a phone they are a bottom sheet within thumb reach."),
    7: ("Everyone", "Seven one-tap shortcuts for the most common narrowings, so many shoppers never need to open the full filter list. The count underneath says how much is left."),
    8: ("Everyone", "Each card carries enough to decide without opening the page: photo, rating, price, what the price is before the making-charge offer, tags, and a real low-stock note only when stock is low. Compare and wishlist sit on the card."),
    9: ("Diamond shortlister", "Jewellery is judged on detail, so a full-screen viewer with zoom and the key facts is one tap away, without leaving the list."),
    10: ("Gifter", "Size is asked first and the mini-cart comes after, because not knowing the size is a leading reason to hesitate (sizing is one of Mia's two most recurring recorded complaints). Bag to checkout is 18.4% today against a 40% benchmark."),
    11: ("Diamond shortlister", "Rings from ₹15,900 to ₹74,424 are compared before buying; the tray lets that happen on the page instead of across browser tabs."),
    12: ("Returning member", "Puts the last few rings a shopper opened back in front of them, so a second visit does not start from zero."),
    13: ("Gifter", "A single click into the gifting range for someone who knows they are buying a present but not what. Not the start of a quiz."),
    14: ("Cold visitor", "A curated way in for shoppers who prefer a collection to a filter list, which limits choice overload."),
    15: ("Diamond shortlister", "Turns \"I want to see it first\" into a next step. 5,642 people asked a store to call them in four weeks, so the intent is already there."),
    16: ("Gold and coin buyer", "Festival timing (Dhanteras on 6 November and Diwali on 8 November 2026) with a direct tile to today's gold rate, which draws 57,249 visits and almost no purchases."),
    17: ("Gold and coin buyer", "Browse by finish rather than by product. The client asked for a lighter ground and a centred title so the metal swatches and the products are the focus."),
    18: ("Diamond shortlister", "Same pattern as metal, keyed to the stone. The client asked for realistic stone pictures with different shapes."),
    19: ("Gifter", "Two rings made to be worn together, added in one step. Raises the basket without adding a decision."),
    20: ("Gold and coin buyer", "Gold purity is a real decision (22KT carries the most gold; lower karats cost less per gram), so it is offered as four plain tiles with a link to today's gold rate."),
    21: ("Gifter", "A budget is how a gifter starts. In Mia's data \"Under ₹15K\" is the most clicked price tile; this page offers Under ₹10K, ₹10–20K, ₹20–50K and ₹50–90K, so the bands should be checked against that evidence."),
    22: ("Diamond shortlister", "Captures the shoppers who want to try a piece, with the fewest fields possible (name and mobile) and the 1800 number for those who would rather call."),
    23: ("Everyone", "Page numbers, not endless scroll, so the footer stays reachable and the breaks stay tied to the rings they introduce. The progress bar shows how much of the list has been seen."),
    24: ("Returning member", "Gives a shopper who reached the end of the list somewhere to go next."),
    25: ("First-time buyer", "Answers what is asked at the point of buying: ring size, BIS hallmark, 14KT against 18KT, returns, EMI, care and certification."),
    26: ("Everyone", "The long search text from the live Mia rings page, laid out as a guide and kept below the FAQ, as the client asked. All of it stays on the page so search engines read it."),
    27: ("Everyone", "The live site's footer takes this place at launch; the prototype's own footer is only there to complete the page."),
    28: ("Gifter", "A first-purchase reward and an occasion-date reminder (two popups), each shown once per visit. The gift finder is built but has no entry point yet."),
}

CROSS = [
    ("One source of truth for every count and price",
     "The page says 495 rings in its title, 28 on this page, and \"1 to 28 of 54\" under the list; the Karatage tiles add to 363. Title, count, pager, filter counts and tile counts must all read from the same catalogue number. Prices, the struck-through price, the price breakdown and the compare values must come from the same price service, so a card, the breakdown and the product page never disagree."),
    ("Filters, sort and page number live in the web address",
     "Today none of them do, so Back leaves the page, refresh loses the filters and a shared link cannot open page 2. The address must carry the filters, the sort and the page so every state can be shared, reloaded and reached with the Back button."),
    ("The prototype is a sample",
     "Ratings, review counts, stock notes, the price breakdown, the compare values, the store finder results and the Recently viewed pre-fill are all made up inside the page. Each must be connected to its real system (reviews, stock, price, store service) before launch. The footer's prototype note, the page title (\"Merged Build\", \"CRO Rebuild\") and the missing main heading (H1) must be fixed for search."),
    ("Links",
     "27 links on the page go nowhere. Header and footer links come from the live site; the others (Checkout, wishlist, bag, login, gold price) need real destinations. Product links open in the same tab and break links open a new tab; decide one rule."),
    ("Popups and fixed layers",
     "The reward popup (after 20 seconds), the exit popup (after three scroll gestures) and the gift finder must never open over another popup or over a filter sheet, and the sticky layers (header, filter rail or Filter and Sort bar, compare tray, mini-cart) need an agreed stacking order. On a phone the tray and mini-cart sit above the bar."),
    ("Mobile parity",
     "91% of traffic in the prototype's own notes is mobile. Every desktop behaviour (hover icons, the left filter rail, the viewer's arrows) has an explicit phone equivalent (always-visible icons, the bottom sheet, swipe). The Filter and Sort bar needs a clearer look against a white page, and the Filter button should show how many filters are on."),
    ("Accessibility, motion and speed",
     "Reduced motion stops the hero, the ticker and the card photo cycling. The hero needs a pause control. Filter options need an on/off state a screen reader can announce; popups must trap focus and close with Escape. The prototype is one 5 MB file with every picture inside; the real page loads photos from the catalogue and should load them as they come into view."),
    ("Promises need an owner",
     "Free shipping, 1 year warranty, 30-day return, certified natural diamonds, BIS hallmark, lifetime exchange, no-cost EMI, 0% purity deduction, the free ring sizer, \"wrapped, noted\" and the ₹500 reward are each a promise to the shopper. Each needs the policy owner's sign-off before it ships (see Open questions)."),
]


# ------------------------------------------------------------------ html pieces
def persona_html():
    out = ['<div class="persona-list">']
    for name, need, ev, answer in PERSONAS:
        out.append('<details class="persona"><summary>%s <span class="arrow">&#9662;</span></summary><div class="persona-body"><p><b>What they need to see:</b> %s</p><p><b>What the page gives them:</b> %s</p><hr><p class="evidence">%s</p></div></details>' % (esc(name), esc(need), esc(answer), esc(ev)))
    out.append("</div>")
    return "".join(out)


def stage_html():
    out = ['<div class="stage-list">']
    full = ('<div class="sec-card"><div class="sec-top"><h4>01 &middot; The whole page</h4><span class="persona-tag">Everyone</span></div><p><b>Why it is built this way:</b> %s</p>%s</div>' % (esc(WHY[1][1]), frames_html(1)))
    out.append('<details class="stage" open><summary><div class="stage-title"><span class="stage-num">Overview</span><h3>The page from top to bottom</h3><span class="stage-sub">page 1 and page 2</span></div><span class="arrow">&#9662;</span></summary><div class="stage-body">%s</div></details>' % full)
    for num, title, secs in STAGES:
        cards = []
        for s in secs:
            persona, why = WHY[s]
            cards.append('<div class="sec-card"><div class="sec-top"><h4>%02d &middot; %s</h4><span class="persona-tag">%s</span></div><p><b>Why here:</b> %s</p>%s</div>' % (s, esc(SECTIONS[s]), esc(persona), esc(why), frames_html(s)))
        out.append('<details class="stage"><summary><div class="stage-title"><span class="stage-num">%s</span><h3>%s</h3><span class="stage-sub">%d sections</span></div><span class="arrow">&#9662;</span></summary><div class="stage-body">%s</div></details>' % (num, esc(title), len(secs), "".join(cards)))
    out.append("</div>")
    return "".join(out)


def glance_html():
    out = ['<div class="tscroll"><table class="glance"><thead><tr><th>#</th><th>Section</th><th>Priority</th><th>Status</th><th>Open questions</th></tr></thead><tbody>']
    for n in sorted(MODS):
        m = MODS[n]
        qn = ", ".join("Q%d" % a for a, _ in Q_BY_SEC.get(n, []))
        out.append('<tr><td class="k">%02d</td><td><a href="#m%02d" class="jump" data-open="m%02d">%s</a></td><td><span class="pill p%s">%s</span></td><td><span class="pill %s">%s</span></td><td>%s</td></tr>'
                   % (n, n, n, esc(SECTIONS[n]), m["prio"][-1:], esc(m["prio"]), status_class(m["status"]), esc(m["status"].split("(")[0].strip()), esc(qn)))
    out.append("</tbody></table></div>")
    return "".join(out)


def questions_html():
    out = ['<div class="mod-list">']
    for title, items in Q_GROUPS:
        lis = "".join('<li value="%d">%s</li>' % (n, md(t)) for n, t in items)
        out.append('<details class="mod"><summary><div class="mod-title"><h3>%s</h3></div><span class="count">%d</span><span class="arrow">&#9662;</span></summary><div class="mod-body"><div class="field"><ol>%s</ol></div></div></details>' % (esc(title), len(items), lis))
    out.append("</div>")
    return "".join(out)


mods_html = "".join(module_html(n) for n in sorted(MODS))
cross_html = "".join('<details class="mod"><summary><div class="mod-title"><h3>%s</h3></div><span class="arrow">&#9662;</span></summary><div class="mod-body"><div class="field"><p>%s</p></div></div></details>' % (esc(t), esc(x)) for t, x in CROSS)
vis_html = "".join('<div class="callout"><span class="tag">Our call</span><p style="margin-bottom:0;"><b>%s.</b> %s</p></div>' % (esc(t), esc(x)) for t, x in VISUAL)

EXTRA_CSS = """
.topbar{background:rgba(10,10,12,.94);border-bottom:1px solid var(--border);position:sticky;top:0;z-index:30;backdrop-filter:blur(6px)}
.tb{display:flex;align-items:center;gap:14px;padding:12px 24px;max-width:960px;margin:0 auto}
.brand{display:flex;align-items:center;gap:8px}.lg-t{height:22px;width:auto}
.brandmark{font-weight:700;font-size:15px;letter-spacing:-.01em;white-space:nowrap;color:var(--purple)}
.tb-x{font-family:'DM Mono',monospace;color:var(--text-dim);font-size:13px}
.lg-m{display:inline-flex;align-items:center;background:#F7F2F4;border-radius:7px;padding:2px 8px;height:30px}.lg-m img{height:26px;width:auto}
.tb-div{width:1px;height:22px;background:var(--border)}
.tb-title b{font-weight:600;font-size:14px;white-space:nowrap}.tb-sub{color:var(--text-dim);font-size:13px;margin-left:10px;white-space:nowrap}
.tb-date{margin-left:auto;font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--text-dim);white-space:nowrap}
@media (max-width:760px){.tb-sub,.tb-date,.tb-div,.tb-title{display:none}}
h1 em{font-style:normal;background:linear-gradient(120deg,#B49CFB,#8B6BF7);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.tab-bar.sub{margin:-8px 0 30px;gap:4px;border-bottom:none}
.tab-bar.sub .tab-btn{font-size:11.5px;border:1px solid var(--border);border-radius:999px;padding:7px 16px;margin-right:0;background:var(--bg-card)}
.tab-bar.sub .tab-btn.active{border-color:rgba(139,107,247,.6);background:var(--purple-dim)}
.tab-btn .wip{font-size:9.5px;letter-spacing:.08em;margin-left:8px;padding:2px 7px;border-radius:999px;background:var(--amber-dim);color:var(--amber)}
.page-panel{display:none}.page-panel.active{display:block}
.sub-panel{display:none}.sub-panel.active{display:block}
.tool{display:flex;justify-content:flex-end;gap:8px;margin:-6px 0 10px}
.tool button{font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--text-dim);background:none;border:1px solid var(--border);border-radius:999px;padding:5px 12px;cursor:pointer}
.tool button:hover{color:var(--purple);border-color:var(--purple)}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-left:auto;margin-right:12px}
.pill{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.05em;text-transform:uppercase;padding:3px 9px;border-radius:999px;white-space:nowrap;border:1px solid var(--border);color:var(--text-dim)}
.pill.p0{color:#F87171;border-color:rgba(248,113,113,.45);background:rgba(248,113,113,.1)}
.pill.p1{color:var(--purple);border-color:rgba(139,107,247,.45);background:var(--purple-dim)}
.pill.p2{color:var(--text-dim)}
.pill.ok{color:#34D399;border-color:rgba(52,211,153,.4);background:rgba(52,211,153,.1)}
.pill.sim{color:var(--amber);border-color:rgba(232,184,75,.4);background:var(--amber-dim)}
.pill.ph{color:var(--text-dim);background:rgba(154,154,165,.1)}
@media (max-width:700px){.chips{display:none}}
.count{font-family:'DM Mono',monospace;font-size:11px;color:var(--text-dim);margin-left:auto;margin-right:12px}
.sub{margin:10px 0 4px!important}.sub b{color:var(--text)}
.field ul,.field ol,.edge-box ul,.edge-box ol,.open-box ul,.open-box ol{padding-left:20px;margin-top:4px}
.edge-box li,.open-box li{font-size:14px;color:var(--text-dim);margin-bottom:6px}
.edge-box li b,.open-box li b{color:var(--text)}
.edge-box p,.open-box p{font-size:14px;color:var(--text-dim);margin-bottom:6px}
.edge-box,.open-box{margin-bottom:16px}
.open-box.note{background:rgba(139,107,247,.08)}
details.frames{margin-top:16px;border:1px dashed var(--border);border-radius:10px;background:var(--bg)}
details.frames>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:12px;padding:12px 16px;font-size:13.5px;font-weight:600;color:var(--text)}
details.frames>summary::-webkit-details-marker{display:none}
details.frames>summary em{font-style:normal;font-family:'DM Mono',monospace;font-size:10.5px;color:var(--text-faint);letter-spacing:.05em;text-transform:uppercase}
details.frames>summary .arrow{margin-left:auto;font-family:'DM Mono',monospace;color:var(--purple);font-size:13px;transition:transform .15s}
details.frames[open]>summary .arrow{transform:rotate(180deg)}
.frames-body{padding:4px 16px 18px}
.fgrp{margin-top:14px}.flab{font-family:'DM Mono',monospace;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--purple);margin-bottom:10px}
.fwrap{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start}
.fwrap figure{margin:0;background:var(--bg-card);border:1px solid var(--border);border-radius:10px;overflow:hidden;max-width:100%}
.fwrap.desktop figure{flex:1 1 440px;max-width:100%}
.fwrap.mobile figure{flex:0 0 auto;width:min(100%,var(--fw))}
.fwrap img{display:block;width:100%;height:auto;background:#fff}
.fwrap figcaption{padding:9px 12px 11px;font-size:12px;color:var(--text-dim);line-height:1.5}
.fwrap figcaption b{display:block;color:var(--text);font-weight:600;font-size:12.5px;margin-bottom:2px}
.fwrap figcaption span{display:block}
.fwrap.desktop figure{width:100%}
.fwrap.desktop figure[style*="--fw:2"]{flex:0 0 auto;width:min(100%,var(--fw))}
.tscroll{overflow-x:auto;margin:0 0 6px}
table.glance{width:100%;border-collapse:collapse;background:var(--bg-card);border:1px solid var(--border);border-radius:10px;overflow:hidden;min-width:640px}
table.glance th,table.glance td{padding:10px 14px;text-align:left;border-bottom:1px solid var(--border);font-size:13.5px}
table.glance th{font-family:'DM Mono',monospace;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--text-dim);font-weight:500}
table.glance td{color:var(--text-dim)}table.glance td.k{font-family:'DM Mono',monospace;color:var(--purple)}
table.glance a{color:var(--text);text-decoration:none;border-bottom:1px solid var(--border)}table.glance a:hover{border-color:var(--purple);color:var(--purple)}
table.glance tr:last-child td{border-bottom:none}
.wipbox{background:var(--bg-card);border:1px dashed rgba(232,184,75,.5);border-radius:12px;padding:34px 28px;text-align:center}
.wipbox b{display:block;font-size:20px;margin-bottom:8px}.wipbox p{color:var(--text-dim);max-width:520px;margin:0 auto 6px}
.wipbox .tag{font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--amber);display:block;margin-bottom:12px}
.src{font-family:'DM Mono',monospace;font-size:11px;color:var(--text-faint);line-height:1.9;margin-top:40px;border-top:1px solid var(--border);padding-top:18px}
.meta-row a+a{margin-left:18px}
.legend{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px}
"""

JS = """
(function(){
  function group(btnSel, panelSel, attr, attrPrefix){
    document.querySelectorAll(btnSel).forEach(function(b){
      b.addEventListener('click',function(){
        var scope=b.closest('[data-scope]')||document;
        var g=b.getAttribute('data-group');
        document.querySelectorAll(btnSel+'[data-group="'+g+'"]').forEach(function(x){x.classList.remove('active')});
        document.querySelectorAll(panelSel+'[data-group="'+g+'"]').forEach(function(x){x.classList.remove('active')});
        b.classList.add('active');
        var p=document.getElementById(b.getAttribute('data-target'));if(p)p.classList.add('active');
        try{history.replaceState(null,'','#'+b.getAttribute('data-target'))}catch(e){}
      });
    });
  }
  group('.tab-btn','.tab-panel');
  document.querySelectorAll('[data-expand]').forEach(function(b){
    b.addEventListener('click',function(){
      var root=document.getElementById(b.getAttribute('data-expand'));
      var open=b.getAttribute('data-state')!=='open';
      root.querySelectorAll('details.mod').forEach(function(d){d.open=open});
      b.setAttribute('data-state',open?'open':'closed');b.textContent=open?'Collapse all':'Expand all';
    });
  });
  document.querySelectorAll('a.jump').forEach(function(a){
    a.addEventListener('click',function(e){
      var id=a.getAttribute('data-open'),el=document.getElementById(id);
      if(!el)return;e.preventDefault();
      var sub=el.closest('.sub-panel');if(sub&&!sub.classList.contains('active')){var bt=document.querySelector('.tab-btn[data-target="'+sub.id+'"]');if(bt)bt.click()}
      el.open=true;el.scrollIntoView({behavior:'smooth',block:'start'});
    });
  });
  var h=location.hash.replace('#','');
  if(h){var bt=document.querySelector('.tab-btn[data-target="'+h+'"]');if(bt)bt.click();}
})();
"""

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mia Collection Page - Handover</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
%(brand)s
%(extra)s
</style>
</head>
<body>
<div class="topbar"><div class="tb">
  <span class="brand"><img src="%(logo_t)s" alt="" class="lg-t"><span class="brandmark">Troopod</span></span><span class="tb-x">&times;</span><span class="lg-m"><img src="%(logo_m)s" alt="Mia by Tanishq"></span>
  <span class="tb-div"></span>
  <div class="tb-title"><b>Handover</b><span class="tb-sub">Collection page and gifting page</span></div>
  <div class="tb-date">October 2026</div>
</div></div>

<div class="wrap">
  <div class="eyebrow">Mia by Tanishq &middot; Handover</div>
  <h1>Collection Page <em>Handover</em></h1>
  <p class="subtitle">Why the collection page is built the way it is, and the logic behind how each section works, with frames for every state. Written for the team building and approving the page.</p>
  <div class="meta-row">
    <img src="%(png)s" alt="Troopod">
    <a href="%(proto)s" target="_blank" rel="noopener">mohsufonit.github.io/mia_cp</a>
    <a href="%(figma)s" target="_blank" rel="noopener">Frames in Figma &rarr;</a>
  </div>

  <div class="tab-bar" role="tablist">
    <button class="tab-btn active" data-group="page" data-target="page-collection">Collection page</button>
    <button class="tab-btn" data-group="page" data-target="page-gifting">Gifting page<span class="wip">WIP</span></button>
  </div>

  <div class="tab-panel page-panel active" data-group="page" id="page-collection">
    <div class="tab-bar sub" role="tablist">
      <button class="tab-btn active" data-group="coll" data-target="coll-strategy">Strategy</button>
      <button class="tab-btn" data-group="coll" data-target="coll-dev">Developer handover</button>
      <button class="tab-btn" data-group="coll" data-target="coll-questions">Open questions</button>
    </div>

    <div class="tab-panel sub-panel active" data-group="coll" id="coll-strategy">
      <div class="exec-summary"><p><b>The short version:</b> a shopper on the collection page is choosing between many similar rings, mostly on a phone, and the page has three jobs: help them narrow quickly (quick chips, filters, sort), reassure them where they would otherwise hesitate (trust strip, price breakdown, size, certificate, store), and keep them moving, to a product page or to a store, without losing them at size or at the bag. Sections are organised below by where the shopper is in that journey, not by scroll order. Visually the rule is simple: pink where we want a banner to be noticed, a light tint where the products are the point. Every section can be traced to Mia's own data, to a recorded client decision, or to a design note kept in the prototype. Expand any persona, stage or frame set for the full reasoning.</p></div>

      <h2><span class="num">01</span>Visual &amp; Creative Direction</h2>
      <p class="section-intro">What the client asked for in review, and what we did about it.</p>
      %(vis)s

      <h2><span class="num">02</span>Who Is Actually On This Page</h2>
      <p class="section-intro">Five kinds of shopper, from Mia's website data (four weeks to 15 October 2026, in the CRO and growth plan) and the prototype's own design notes. Click a name to expand.</p>
      %(personas)s

      <h2><span class="num">03</span>Section-By-Section, By Journey Stage</h2>
      <p class="section-intro">Grouped by where each section sits in the shopper's journey. Each section has its frames, collapsed; open them to see every state on desktop and mobile.</p>
      %(stages)s
    </div>

    <div class="tab-panel sub-panel" data-group="coll" id="coll-dev">
      <div class="exec-summary"><p><b>Why this section exists:</b> the frames show what each section looks like once it is working. They do not say what decides which rings appear, what happens when a filter returns nothing, or what a banner does the day after a festival. This is that missing layer, written as rules and cases, not code, so each section can be built correctly the first time and checked against something concrete. <b>Important:</b> the page you can open is a working prototype with sample data. Fifty-four rings are loaded but the title says 495; filters and sort change how the buttons look but not the list; ratings, stock notes, the price breakdown and the store finder results are worked out inside the page. Anything marked SIMULATED must be connected to the real system.</p></div>

      <h2><span class="num">01</span>Sections At A Glance</h2>
      <p class="section-intro">Priority: P0 blocks launch, P1 ships with launch, P2 follows. Status: BUILT works as designed; SIMULATED looks and acts right but its data or result is made up; PLACEHOLDER stands in for the live site's own header or footer. Click a section to jump to it.</p>
      %(glance)s

      <h2><span class="num">02</span>Section-By-Section Build Logic</h2>
      <p class="section-intro">In page order. Each module covers its purpose, the rules that govern it, what the team can change, where each button goes, and the edge cases to handle explicitly. Frames sit at the bottom of each module, collapsed.</p>
      <div class="tool"><button data-expand="coll-dev" data-state="closed">Expand all</button></div>
      <div class="mod-list" id="mods">%(mods)s</div>

      <h2><span class="num">03</span>Cross-Cutting Concerns</h2>
      <p class="section-intro">Rules that apply across the whole page, not to any single section. Worth agreeing once.</p>
      <div class="mod-list">%(cross)s</div>
    </div>

    <div class="tab-panel sub-panel" data-group="coll" id="coll-questions">
      <div class="exec-summary"><p><b>For the client:</b> the answers still needed before build, in one list. The same questions also appear inside the section they belong to (under Open decisions). The last group comes from the design notes written on Page 1 of the Figma file.</p></div>
      <div class="tool"><button data-expand="coll-questions" data-state="closed">Expand all</button></div>
      %(questions)s
    </div>
  </div>

  <div class="tab-panel page-panel" data-group="page" id="page-gifting">
    <div class="wipbox"><span class="tag">Work in progress</span><b>Gifting page handover</b><p>The gifting page handover will be brought into this same format, with its own strategy, developer handover and open questions, once the collection page handover is approved.</p><p>Nothing here is final.</p></div>
  </div>

  <div class="src">Sources &nbsp;Mia's website data and the CRO and growth plan (four weeks to 15 October 2026), the client review of 9 October 2026, the annotated design on Page 1 of the Figma file, and the working prototype<br>Frames &nbsp;1440 px desktop and 390 px mobile, captured from the prototype; every number in a frame is sample data</div>
</div>
<script>%(js)s</script>
</body>
</html>
"""

doc = PAGE % dict(brand=BRAND_CSS, extra=EXTRA_CSS, logo_t=LOGO_T, logo_m=LOGO_M, png=GP_PNG, proto=PROTO, figma=FIGMA,
                  vis=vis_html, personas=persona_html(), stages=stage_html(), glance=glance_html(), mods=mods_html,
                  cross=cross_html, questions=questions_html(), js=JS)
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(doc)
tot = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(os.path.join(OUT, "assets")) for f in fs)
print("index.html %d KB; frames %d MB; modules %d; questions %d" % (os.path.getsize(os.path.join(OUT, "index.html")) // 1024, tot // 1048576, len(MODS), sum(len(i) for _, i in Q_GROUPS)))
