"""Render faithful preview images of each app screen using the REAL data and
matching engine, drawn with Pillow in the app's actual colour scheme.

These are high-fidelity mockups (Chromium cannot run in this sandbox), using the
genuine matcher output and member records so the content is accurate.
"""
import json
import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

import data_loader
import matcher

OUT = "/projects/sandbox/docs/screenshots"
os.makedirs(OUT, exist_ok=True)

FREG = "/usr/share/fonts/google-noto-vf/NotoSans[wght].ttf"
FBOLD = "/inner_container/usr/share/fonts/google-noto/NotoSans-Bold.ttf"
FSEMI = "/inner_container/usr/share/fonts/google-noto/NotoSans-SemiBold.ttf"

# palette (from static/style.css)
NAVY = (11, 37, 69)
BLUE = (19, 64, 116)
ACCENT = (31, 122, 140)
ACCENT2 = (230, 167, 0)
BG = (245, 247, 250)
CARD = (255, 255, 255)
LINE = (226, 232, 240)
TEXT = (26, 36, 51)
MUTED = (91, 107, 127)
GOOD = (26, 141, 95)
WHY_BG = (255, 251, 233)
TAG_BG = (238, 244, 246)
TAG_SECTOR_BG = (243, 238, 251)
TAG_SECTOR_FG = (107, 63, 160)
TAG_COUNTRY_BG = (238, 247, 240)
TAG_COUNTRY_FG = (47, 122, 77)

W = 1200


def font(path, size):
    return ImageFont.truetype(path, size)


def reg(s): return font(FREG, s)
def bold(s):
    try: return font(FBOLD, s)
    except Exception: return font(FREG, s)
def semi(s):
    try: return font(FSEMI, s)
    except Exception: return bold(s)


def new_canvas(h):
    img = Image.new("RGB", (W, h), BG)
    return img, ImageDraw.Draw(img)


def rrect(d, box, radius, fill, outline=None, width=1):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def topbar(d):
    d.rectangle([0, 0, W, 60], fill=NAVY)
    rrect(d, [24, 14, 56, 46], 8, ACCENT2)
    d.text((31, 20), "SG", font=bold(18), fill=NAVY)
    d.text((66, 20), "Member Community Assistant", font=semi(17), fill=(255, 255, 255))
    for i, label in enumerate(["Dashboard", "Find partners", "Contribute", "Staff view"]):
        d.text((W - 430 + i * 105, 22), label, font=reg(13), fill=(205, 217, 229))


def tag(d, x, y, text, kind=""):
    f = reg(13)
    tw = d.textlength(text, font=f)
    pad = 10
    bg, fg = TAG_BG, ACCENT
    if kind == "sector": bg, fg = TAG_SECTOR_BG, TAG_SECTOR_FG
    elif kind == "country": bg, fg = TAG_COUNTRY_BG, TAG_COUNTRY_FG
    rrect(d, [x, y, x + tw + pad * 2, y + 26], 13, bg, outline=LINE)
    d.text((x + pad, y + 5), text, font=f, fill=fg)
    return x + tw + pad * 2 + 8


def tags_row(d, x, y, items, maxx=W - 60):
    cx = x
    for it in items:
        kind = it[1] if isinstance(it, tuple) else ""
        label = it[0] if isinstance(it, tuple) else it
        w = d.textlength(label, font=reg(13)) + 20 + 8
        if cx + w > maxx:
            break
        cx = tag(d, cx, y, label, kind)
    return y + 34


def footer(d, h):
    d.text((60, h - 34), "SGTech x AWS \u201cBuild with AI\u201d Hackathon \u00b7 MVP demo on 2,080 member companies \u00b7 dummy request log, no live CRM",
            font=reg(12), fill=MUTED)


# ---------------------------------------------------------------------------
members = data_loader.load_members()
stats = data_loader.directory_stats()
me = data_loader.find_member_by_name("1-Net Singapore Pte Ltd")


def screen_home():
    h = 760
    img, d = new_canvas(h)
    topbar(d)
    d.text((W/2, 86), "SGTECH \u00d7 AWS \u00b7 BUILD WITH AI", font=semi(13), fill=ACCENT, anchor="mm")
    d.text((W/2, 120), "Member Community Assistant", font=bold(30), fill=NAVY, anchor="mm")
    sub = "Discover who else is in the SGTech community, find the right partners in plain language,"
    sub2 = "request a meeting, and see where your company can contribute \u2014 all self-serve."
    d.text((W/2, 152), sub, font=reg(15), fill=MUTED, anchor="mm")
    d.text((W/2, 174), sub2, font=reg(15), fill=MUTED, anchor="mm")
    # stats card
    rrect(d, [60, 210, W-60, 300], 12, CARD, outline=LINE)
    cols = [("2080", "Member companies"), ("17", "Areas of expertise"),
            ("29", "Business sectors"), ("6", "Chapters")]
    for i, (n, l) in enumerate(cols):
        cx = 60 + (W-120)/4 * (i+0.5)
        d.text((cx, 240), n, font=bold(28), fill=BLUE, anchor="mm")
        d.text((cx, 272), l, font=reg(13), fill=MUTED, anchor="mm")
    # login card
    rrect(d, [60, 320, W-60, h-60], 12, CARD, outline=LINE)
    d.text((80, 338), "Mock login", font=bold(20), fill=TEXT)
    d.text((80, 370), "Pick a sample member company to explore the experience as that member.", font=reg(14), fill=MUTED)
    samples = ["1-Net Singapore Pte Ltd", "2Stallions Pte. Ltd.", "8C8 Cloud",
               "Fortinet Singapore Pte Ltd", "Crayon Pte Ltd", "A*STAR Research Entities"]
    for i, name in enumerate(samples):
        col = i % 3; rowi = i // 3
        bx = 80 + col * ((W-160)/3)
        by = 405 + rowi * 70
        rrect(d, [bx, by, bx + (W-160)/3 - 14, by + 56], 10, CARD, outline=LINE)
        d.text((bx + 14, by + 10), name[:34], font=semi(14), fill=NAVY)
        m = data_loader.find_member_by_name(name)
        subt = ", ".join(m["expertise"][:2]) if m and m["expertise"] else "Member company"
        d.text((bx + 14, by + 32), subt[:38], font=reg(12), fill=MUTED)
    footer(d, h)
    img.save(f"{OUT}/01-home-login.png")
    print("  01-home-login")


def screen_dashboard():
    h = 560
    img, d = new_canvas(h)
    topbar(d)
    rrect(d, [60, 84, W-60, 240], 12, CARD, outline=LINE)
    d.text((80, 100), "SIGNED IN AS A MEMBER", font=semi(12), fill=ACCENT)
    d.text((80, 122), me["name"], font=bold(26), fill=NAVY)
    y = tags_row(d, 80, 168, [(e, "") for e in me["expertise"]] +
                 [(s, "sector") for s in me["sectors"]] +
                 [(c, "country") for c in me["countries"]])
    d.text((80, 206), "Chapters: " + "; ".join(me["chapters"]), font=reg(13), fill=MUTED)
    cards = [("\U0001F50D  Find partners", "Describe what you need in plain language and get the top 5 matching member companies, each with a reason."),
             ("\U0001F91D  Find where to contribute", "See chapters, committees and sponsorship opportunities matched to your profile."),
             ("\U0001F4CA  Staff view", "The secretariat dashboard: number of successful matches and sponsorship leads.")]
    for i, (t, body) in enumerate(cards):
        cx = 60 + i * ((W-120)/3)
        rrect(d, [cx, 260, cx + (W-120)/3 - 14, 470], 12, CARD, outline=LINE)
        d.text((cx + 16, 278), t, font=bold(16), fill=NAVY)
        for j, ln in enumerate(textwrap.wrap(body, 34)):
            d.text((cx + 16, 310 + j*20), ln, font=reg(13), fill=MUTED)
    footer(d, h)
    img.save(f"{OUT}/02-dashboard.png")
    print("  02-dashboard")


def screen_find(results=None):
    need = "cybersecurity firms with healthcare clients in Malaysia" if results else ""
    h = 980 if results else 340
    img, d = new_canvas(h)
    topbar(d)
    rrect(d, [60, 84, W-60, 250], 12, CARD, outline=LINE)
    d.text((80, 100), "FIND PARTNERS", font=semi(12), fill=ACCENT)
    d.text((80, 122), "Who are you looking for?", font=bold(24), fill=NAVY)
    d.text((80, 158), "Describe your need in plain language. The assistant interprets it and ranks matching SGTech members.", font=reg(14), fill=MUTED)
    rrect(d, [80, 188, W-320, 224], 9, CARD, outline=LINE)
    d.text((94, 197), need or "e.g. cybersecurity firms with healthcare clients in Malaysia", font=reg(15), fill=TEXT if need else MUTED)
    rrect(d, [W-300, 188, W-80, 224], 9, ACCENT)
    d.text((W-190, 197), "Find matches", font=semi(15), fill=(255,255,255), anchor="ma")
    if not results:
        d.text((80, 236), "Try:  AI and data analytics partners   \u00b7   fintech software company in Indonesia", font=reg(13), fill=MUTED)
        footer(d, h); img.save(f"{OUT}/03-find-empty.png"); print("  03-find-empty"); return
    # interpreted terms
    _, terms = results
    y = tags_row(d, 80, 262, terms)
    d.text((80, y+4), "Top 5 matches", font=bold(20), fill=NAVY)
    yy = y + 40
    for i, r in enumerate(results[0]):
        card_h = 118
        rrect(d, [60, yy, W-60, yy+card_h], 12, CARD, outline=LINE)
        d.text((80, yy+14), f"#{i+1}", font=bold(18), fill=ACCENT2)
        d.text((120, yy+14), r["member"]["name"], font=bold(17), fill=NAVY)
        pill = f"match score {r['score']}"
        pw = d.textlength(pill, font=semi(12))
        rrect(d, [W-90-pw-20, yy+14, W-80, yy+40], 13, BLUE)
        d.text((W-90-pw-10, yy+19), pill, font=semi(12), fill=(255,255,255))
        # why box
        rrect(d, [80, yy+44, W-80, yy+74], 6, WHY_BG)
        d.rectangle([80, yy+44, 83, yy+74], fill=ACCENT2)
        why = "Why this match: " + r["reason"]
        d.text((92, yy+51), why[:120], font=reg(13), fill=TEXT)
        tags_row(d, 80, yy+82, [(e,"") for e in r["member"]["expertise"]] +
                 [(s,"sector") for s in r["member"]["sectors"]] +
                 [(c,"country") for c in r["member"]["countries"]])
        yy += card_h + 12
    footer(d, h)
    img.save(f"{OUT}/04-find-results.png")
    print("  04-find-results")


def screen_contribute():
    opps = json.load(open("/projects/sandbox/data/opportunities.json"))
    sugg = matcher.find_contributions(me, opps, top_n=3)
    h = 760
    img, d = new_canvas(h)
    topbar(d)
    rrect(d, [60, 84, W-60, 200], 12, CARD, outline=LINE)
    d.text((80, 100), "FIND WHERE TO CONTRIBUTE", font=semi(12), fill=ACCENT)
    d.text((80, 122), f"Ways {me['name']} can get involved", font=bold(22), fill=NAVY)
    d.text((80, 160), "Based on your profile, here are the chapters and sponsorship opportunities that fit best.", font=reg(14), fill=MUTED)
    yy = 216
    for s in sugg:
        opp = s["opportunity"]
        card_h = 150
        rrect(d, [60, yy, W-60, yy+card_h], 12, CARD, outline=LINE)
        d.text((80, yy+14), opp["name"], font=bold(17), fill=NAVY)
        kind = opp["type"]
        kw = d.textlength(kind, font=reg(12))
        rrect(d, [W-90-kw-20, yy+14, W-80, yy+38], 12, TAG_SECTOR_BG if kind=="sponsorship" else TAG_BG)
        d.text((W-90-kw-10, yy+19), kind, font=reg(12), fill=TAG_SECTOR_FG if kind=="sponsorship" else ACCENT)
        for j, ln in enumerate(textwrap.wrap(opp["blurb"], 110)[:2]):
            d.text((80, yy+44+j*20), ln, font=reg(13), fill=TEXT)
        rrect(d, [80, yy+86, W-80, yy+114], 6, WHY_BG); d.rectangle([80,yy+86,83,yy+114], fill=ACCENT2)
        d.text((92, yy+93), ("Why this fits: " + s["reason"])[:118], font=reg(13), fill=TEXT)
        rrect(d, [80, yy+120, 230, yy+144], 9, ACCENT2)
        d.text((104, yy+125), "Express interest", font=semi(13), fill=NAVY)
        yy += card_h + 12
    footer(d, h)
    img.save(f"{OUT}/06-contribute.png")
    print("  06-contribute")


def screen_admin():
    log = json.load(open("/projects/sandbox/data/request_log.json"))
    mr = [e for e in log if e["kind"] == "meeting_request"]
    leads = [e for e in log if e["kind"] == "sponsorship_lead"]
    success = [e for e in mr if e["status"] in ("accepted","meeting_held")]
    h = 720
    img, d = new_canvas(h)
    topbar(d)
    rrect(d, [60, 84, W-60, 190], 12, CARD, outline=LINE)
    d.text((80, 100), "STAFF VIEW \u00b7 SECRETARIAT & CHAPTER MANAGERS", font=semi(12), fill=ACCENT)
    d.text((80, 122), "Community activity dashboard", font=bold(22), fill=NAVY)
    d.text((80, 158), "Instead of answering every enquiry by hand, staff see requests, matches and leads here.", font=reg(14), fill=MUTED)
    metrics = [(str(len(success)), "Successful matches", GOOD),
               (str(len(leads)), "Sponsorship leads", ACCENT2),
               (str(len(mr)), "Total meeting requests", BLUE)]
    for i, (n, l, c) in enumerate(metrics):
        cx = 60 + i * ((W-120)/3)
        rrect(d, [cx, 206, cx + (W-120)/3 - 14, 316], 12, CARD, outline=LINE)
        d.text((cx + (W-120)/6 - 7, 230), n, font=bold(40), fill=c, anchor="ma")
        d.text((cx + (W-120)/6 - 7, 288), l, font=reg(13), fill=MUTED, anchor="ma")
    # requests table
    rrect(d, [60, 332, W-60, h-60], 12, CARD, outline=LINE)
    d.text((80, 348), "Meeting / collaboration requests", font=bold(17), fill=NAVY)
    cols = [("#", 80), ("FROM", 120), ("TO", 360), ("NEED", 640), ("STATUS", 980)]
    for label, x in cols:
        d.text((x, 384), label, font=semi(11), fill=MUTED)
    d.line([80, 404, W-80, 404], fill=LINE)
    for i, e in enumerate(mr):
        ry = 414 + i*34
        d.text((80, ry), str(e["id"]), font=reg(13), fill=TEXT)
        d.text((120, ry), e["requester"][:22], font=reg(13), fill=TEXT)
        d.text((360, ry), e["target"][:28], font=reg(13), fill=TEXT)
        d.text((640, ry), e["need"][:28], font=reg(13), fill=MUTED)
        st = e["status"].replace("_", " ")
        stc = {"meeting held": GOOD, "accepted": GOOD}.get(st, BLUE)
        stbg = {"meeting held": TAG_COUNTRY_BG, "accepted": TAG_COUNTRY_BG}.get(st, TAG_BG)
        sw = d.textlength(st, font=semi(12))
        rrect(d, [980, ry-2, 980+sw+18, ry+22], 11, stbg)
        d.text((989, ry+2), st, font=semi(12), fill=stc)
        d.line([80, ry+28, W-80, ry+28], fill=LINE)
    footer(d, h)
    img.save(f"{OUT}/07-admin-dashboard.png")
    print("  07-admin-dashboard")


if __name__ == "__main__":
    print("Rendering screens with real data + matcher output:")
    screen_home()
    screen_dashboard()
    res = matcher.find_partners("cybersecurity firms with healthcare clients in Malaysia",
                                members, exclude_id=me["id"], top_n=5)
    screen_find(results=res)
    screen_find(results=None)
    screen_contribute()
    screen_admin()
    print("DONE ->", OUT)
