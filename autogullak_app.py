#!/usr/bin/env python3
"""
AutoGullak AI v2.0 (Real-Money Edition)
- Zero fake demo balances (tracks real clicks + real EarnKaro/Cuelinks affiliate links)
- Blocks placeholder 'yourname@upi' mistakes
- Built-in 1-Tap Copy Title, Description & Live Storefront URL for Pinterest
- Auto-converts links via Cuelinks Publisher ID OR lets you paste real EarnKaro (ekaro.in) links
"""

import json
import os
import sqlite3
import subprocess
import sys
import textwrap
import threading
import time
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

for pkg, mod in [("Pillow", "PIL"), ("requests", "requests")]:
    try:
        __import__(mod)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])

import requests
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "autogullak_v2.db")
PINS_DIR = os.path.join(BASE_DIR, "generated_pins")
os.makedirs(PINS_DIR, exist_ok=True)

BUILT_IN_ROUTINES = [
    {
        "slug": "oily-skin-humid-morning-499",
        "niche": "Skincare",
        "board": "Oily & Acne Skin Routines India",
        "pin_headline": "3-Step Oily Skin Morning Routine (Under ₹499)",
        "pin_title": "Simple 3-Step Morning Skincare Routine for Oily Skin in India (Under ₹499)",
        "pin_desc": "Sticky face and college pimples in Indian humidity? Follow this 3-step morning checklist under ₹499. Tap for full routine & budget links! #skincareindia #ad",
        "palette": ("#ECFDF5", "#065F46", "#10B981", "#D1FAE5"),
        "steps": [
            {"name": "Step 1: Salicylic / Tea Tree Gel Cleanser", "tip": "Massage 45s on damp skin to clear excess sebum.", "price": "₹249", "url": "https://mamaearth.in/product/tea-tree-face-wash"},
            {"name": "Step 2: Oil-Free Niacinamide Gel Hydrator", "tip": "Pea-sized dot stops rebound oiliness without grease.", "price": "₹299", "url": "https://mamaearth.in/product/oil-free-face-moisturizer"},
            {"name": "Step 3: Matte Aqua Sunscreen SPF 50 PA+++", "tip": "2-finger rule; zero white cast on Indian skin.", "price": "₹349", "url": "https://mamaearth.in/product/ultra-light-indian-sunscreen"},
        ],
    },
    {
        "slug": "hard-water-hairfall-fix-499",
        "niche": "Haircare",
        "board": "Hard Water Hairfall & Dandruff Fixes India",
        "pin_headline": "Stop Hard-Water Hairfall: 3-Step Wash Routine",
        "pin_title": "3-Step Hard Water Hairfall & Frizzy Hair Routine Under ₹499 (India Guide)",
        "pin_desc": "Hostel or borewell hard water causing hairfall? Save this gentle 3-step wash-day routine under ₹499 for stronger roots. #haircareindia #hairfallcontrol #ad",
        "palette": ("#EFF6FF", "#1E3A8A", "#3B82F6", "#DBEAFE"),
        "steps": [
            {"name": "Step 1: Rosemary + Redensyl Scalp Oil (Pre-Wash)", "tip": "Apply 45 mins before bath twice a week.", "price": "₹319", "url": "https://mamaearth.in/product/rosemary-hair-oil"},
            {"name": "Step 2: Sulphate-Free Chelating Mild Shampoo", "tip": "Removes hard-water mineral buildup gently.", "price": "₹279", "url": "https://mamaearth.in/product/rosemary-anti-hair-fall-shampoo"},
            {"name": "Step 3: Peptide Frizz-Lock Conditioner (Ends Only)", "tip": "Never apply on scalp; rinse with cool water.", "price": "₹299", "url": "https://mamaearth.in/product/rosemary-anti-hair-fall-conditioner"},
        ],
    },
    {
        "slug": "no-white-cast-tan-removal-399",
        "niche": "Sun Care",
        "board": "Sunscreen & Tan Removal Under ₹499 India",
        "pin_headline": "College Sun Tan Fix: 3-Step Glow Under ₹399",
        "pin_title": "De-Tan & No-White-Cast Sunscreen Routine Under ₹399 for Indian Skin",
        "pin_desc": "Walking in harsh afternoon sun? Use this affordable 3-step tan removal + SPF 50 protection checklist made for wheatish & dusky Indian skin. #detan #sunscreenindia #ad",
        "palette": ("#FFFBEB", "#78350F", "#F59E0B", "#FEF3C7"),
        "steps": [
            {"name": "Step 1: Ubtan / Vitamin C Brightening Wash", "tip": "Gently lifts daily dust and dullness after college.", "price": "₹229", "url": "https://mamaearth.in/product/ubtan-face-wash"},
            {"name": "Step 2: Weekly Clay De-Tan Pack (2x Week)", "tip": "Apply thin layer for 10 mins on tanned forehead/neck.", "price": "₹349", "url": "https://mamaearth.in/product/ubtan-face-mask"},
            {"name": "Step 3: Invisible Gel Sunscreen SPF 50", "tip": "Reapply every 3 hours outdoors; zero chalky finish.", "price": "₹349", "url": "https://mamaearth.in/product/vitamin-c-daily-glow-sunscreen"},
        ],
    },
    {
        "slug": "winter-skin-barrier-repair-499",
        "niche": "Barrier Care",
        "board": "Glowing Skin & Dark Spot Routines India",
        "pin_headline": "Dry Flaky Skin? 3-Step Barrier Repair Checklist",
        "pin_title": "Simple Ceramide & Rice Water Skin Barrier Routine Under ₹499 (India)",
        "pin_desc": "Over-exfoliated or dry flaky skin? Heal your skin barrier fast with this soothing 3-step Indian budget routine under ₹499. #skinbarrier #indianskincare #ad",
        "palette": ("#FDF2F8", "#831843", "#EC4899", "#FCE7F3"),
        "steps": [
            {"name": "Step 1: Creamy Non-Foaming Hydrating Cleanser", "tip": "Cleans without tight squeaky feeling.", "price": "₹249", "url": "https://mamaearth.in/product/rice-face-wash"},
            {"name": "Step 2: Ceramide + Hyaluronic Barrier Cream", "tip": "Locks moisture for 12 hours on damp skin.", "price": "₹349", "url": "https://mamaearth.in/product/rice-oil-free-face-moisturizer"},
            {"name": "Step 3: Dewy Hydrating Sunscreen SPF 50", "tip": "Protects healing skin from UV pigmentation.", "price": "₹369", "url": "https://mamaearth.in/product/hydra-gel-indian-sunscreen"},
        ],
    },
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)")
    c.execute("""
        CREATE TABLE IF NOT EXISTS routines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE,
            niche TEXT,
            board TEXT,
            pin_headline TEXT,
            pin_title TEXT,
            pin_desc TEXT,
            steps_json TEXT,
            pin_image TEXT,
            link_mode TEXT DEFAULT 'Add EarnKaro Links',
            views INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engine TEXT,
            message TEXT,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS wallet (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            real_withdrawn_inr REAL DEFAULT 0.0,
            gold_vault_inr REAL DEFAULT 0.0
        )
    """)
    c.execute("INSERT OR IGNORE INTO wallet (id) VALUES (1)")
    defaults = {
        "autopilot_enabled": os.environ.get("AUTOPILOT_ENABLED", "1"),
        "upi_id": os.environ.get("UPI_ID", "9430883276@upi"),
        "gold_split_pct": os.environ.get("GOLD_SPLIT_PCT", "50"),
        "cuelinks_cid": os.environ.get("CUELINKS_CID", ""),
        "earnkaro_refer_url": os.environ.get("EARNKARO_REFER_URL", ""),
        "gemini_api_key": os.environ.get("GEMINI_API_KEY", ""),
        "pinterest_token": os.environ.get("PINTEREST_TOKEN", ""),
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", (k, v))
        if os.environ.get(k.upper()):
            c.execute("UPDATE config SET value = ? WHERE key = ?", (os.environ[k.upper()], k))
    c.execute("UPDATE config SET value = '9430883276@upi' WHERE key = 'upi_id' AND (value = '' OR value = 'yourname@upi')")
    conn.commit()
    conn.close()


def log_event(engine, message):
    conn = get_db()
    now = datetime.now().strftime("%d %b %I:%M %p")
    conn.execute("INSERT INTO logs (engine, message, created_at) VALUES (?, ?, ?)", (engine, message, now))
    conn.commit()
    conn.close()


def load_font(size, bold=False):
    candidates = (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"]
        if bold
        else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"]
    )
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def render_pin_png(slug, headline, board, steps, palette):
    bg_hex, dark_hex, accent_hex, card_hex = palette
    img = Image.new("RGB", (1000, 1500), bg_hex)
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([48, 48, 952, 430], radius=36, fill=card_hex)
    draw.rounded_rectangle([78, 78, 495, 134], radius=28, fill=accent_hex)

    f_badge = load_font(24, bold=True)
    f_title = load_font(52, bold=True)
    f_step_h = load_font(28, bold=True)
    f_step_p = load_font(24, bold=False)
    f_cta = load_font(32, bold=True)
    f_small = load_font(21, bold=False)

    draw.text((104, 92), "INDIA BUDGET CHECKLIST", fill="#FFFFFF", font=f_badge)

    wrapped_h = textwrap.wrap(headline, width=22)[:3]
    y_h = 165
    for line in wrapped_h:
        draw.text((82, y_h), line, fill=dark_hex, font=f_title)
        y_h += 68

    y_card = 475
    for idx, st in enumerate(steps[:3], start=1):
        draw.rounded_rectangle([56, y_card, 944, y_card + 245], radius=30, fill="#FFFFFF", outline=card_hex, width=4)
        draw.ellipse([86, y_card + 34, 154, y_card + 102], fill=accent_hex)
        draw.text((111, y_card + 49), str(idx), fill="#FFFFFF", font=f_step_h)

        step_title = textwrap.wrap(st["name"], width=40)[0]
        draw.text((178, y_card + 38), step_title, fill=dark_hex, font=f_step_h)

        tip_lines = textwrap.wrap(st["tip"], width=46)[:2]
        ty = y_card + 88
        for tl in tip_lines:
            draw.text((178, ty), tl, fill="#374151", font=f_step_p)
            ty += 34

        draw.rounded_rectangle([178, y_card + 172, 390, y_card + 218], radius=16, fill=card_hex)
        draw.text((198, y_card + 181), f"Approx {st['price']}", fill=dark_hex, font=f_badge)
        y_card += 275

    draw.rounded_rectangle([56, 1325, 944, 1435], radius=32, fill=dark_hex)
    draw.text((135, 1360), "Tap Link for Full Step-by-Step List ->", fill="#FFFFFF", font=f_cta)
    draw.text((64, 1452), f"Board: {board}  |  #ad Affiliate Guide", fill="#6B7280", font=f_small)

    filename = f"pin_{slug}.png"
    img.save(os.path.join(PINS_DIR, filename), "PNG")
    return filename


def get_config_dict():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM config").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}


def build_final_affiliate_url(raw_url, cfg):
    # If user pasted an EarnKaro ekaro.in link directly, use it untouched!
    if "ekaro.in" in raw_url or "earnkaro" in raw_url or "bitli.in" in raw_url:
        return raw_url, "EarnKaro Live ✅"
    # If user configured Cuelinks Publisher ID, auto-monetize EVERY product link automatically!
    cid = cfg.get("cuelinks_cid", "").strip()
    if cid:
        encoded = urllib.parse.quote(raw_url, safe="")
        return f"https://linksredirect.com/?cid={urllib.parse.quote(cid)}&source=js&url={encoded}", "Cuelinks Auto-Monetized ✅"
    return raw_url, "Paste ekaro.in Link ⚠️"


def maybe_generate_ai_routine(api_key, existing_slugs):
    if not api_key:
        return None
    prompt = (
        "Generate 1 low-competition Indian budget skincare or haircare 3-step routine under ₹499 as strict JSON "
        "with keys: slug, niche, board, pin_headline, pin_title, pin_desc, steps (list of 3 objects with name, tip, price, url). "
        f"Avoid these slugs: {list(existing_slugs)}."
    )
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}",
            json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json"}},
            timeout=15,
        )
        if resp.status_code == 200:
            txt = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            data = json.loads(txt)
            data["palette"] = ("#ECFDF5", "#065F46", "#10B981", "#D1FAE5")
            return data
    except Exception as exc:
        log_event("AI Brain", f"Used built-in Indian library ({exc})")
    return None


def run_autonomous_cycle():
    cfg = get_config_dict()
    conn = get_db()
    existing = {r["slug"] for r in conn.execute("SELECT slug FROM routines").fetchall()}
    conn.close()

    chosen = maybe_generate_ai_routine(cfg.get("gemini_api_key", ""), existing)
    if not chosen:
        for item in BUILT_IN_ROUTINES:
            if item["slug"] not in existing:
                chosen = item
                break
        if not chosen:
            # All 4 starter routines already exist; don't create duplicates unless Gemini key is added
            log_event("Cloud Check", "All 4 starter routines & Pins are live and healthy. Add free Gemini Key in Setup for unlimited new topics!")
            return "all-live"

    tagged_steps = []
    mode_label = "Paste ekaro.in Link ⚠️"
    for st in chosen["steps"]:
        st_copy = dict(st)
        final_u, mode_label = build_final_affiliate_url(st["url"], cfg)
        st_copy["aff_url"] = final_u
        tagged_steps.append(st_copy)

    pin_file = render_pin_png(
        chosen["slug"],
        chosen["pin_headline"],
        chosen["board"],
        tagged_steps,
        chosen.get("palette", ("#ECFDF5", "#065F46", "#10B981", "#D1FAE5")),
    )

    conn = get_db()
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")
    conn.execute(
        """INSERT INTO routines
           (slug, niche, board, pin_headline, pin_title, pin_desc, steps_json, pin_image, link_mode, views, clicks, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)""",
        (
            chosen["slug"],
            chosen["niche"],
            chosen["board"],
            chosen["pin_headline"],
            chosen["pin_title"],
            chosen["pin_desc"],
            json.dumps(tagged_steps),
            pin_file,
            mode_label,
            now,
        ),
    )
    conn.commit()
    conn.close()

    log_event("AI Studio", f"Created Routine '/r/{chosen['slug']}' + 1000x1500 Pin ({pin_file}).")
    return chosen["slug"]


def render_routine_public_html(row, cfg):
    steps = json.loads(row["steps_json"])
    cards_html = ""
    for i, st in enumerate(steps, 1):
        out_link = f"/go/{row['slug']}/{i - 1}"
        cards_html += f"""
        <div style="background:#fff;border:1px solid #e5e7eb;border-radius:16px;padding:18px;margin-bottom:14px;box-shadow:0 2px 8px rgba(0,0,0,0.03)">
            <div style="font-size:12px;font-weight:700;color:#059669;text-transform:uppercase;margin-bottom:4px">Step {i} · Approx {st['price']}</div>
            <h3 style="margin:0 0 8px;font-size:17px;color:#111827">{st['name']}</h3>
            <p style="margin:0 0 14px;font-size:14px;color:#4b5563;line-height:1.5">{st['tip']}</p>
            <a href="{out_link}" target="_blank" rel="nofollow sponsored"
               style="display:block;text-align:center;background:#059669;color:#fff;text-decoration:none;font-weight:700;padding:12px;border-radius:12px;font-size:14px">
               Check Latest Price & Offers ->
            </a>
        </div>
        """
    refer_html = ""
    if cfg.get("earnkaro_refer_url"):
        refer_html = f"""
        <div style="text-align:center;margin-top:18px;padding:12px;background:#ecfdf5;border-radius:12px;font-size:13px">
          Want cashback when sharing beauty deals? <a href="{cfg['earnkaro_refer_url']}" target="_blank" style="color:#065f46;font-weight:700">Join EarnKaro Free -></a>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{row['pin_title']}</title></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f8fafc;margin:0;padding:16px;color:#1f2937">
  <div style="max-width:480px;margin:0 auto">
    <p style="font-size:12px;color:#6b7280;background:#f1f5f9;padding:10px 12px;border-radius:10px">
      <strong>Disclosure (#ad):</strong> This guide contains affiliate links. If you purchase through them, we may earn a small commission at zero extra cost to you.
    </p>
    <span style="display:inline-block;background:#d1fae5;color:#065f46;font-size:12px;font-weight:700;padding:4px 10px;border-radius:99px">{row['board']}</span>
    <h1 style="font-size:22px;line-height:1.3;margin:10px 0 6px;color:#0f172a">{row['pin_title']}</h1>
    <p style="font-size:14px;color:#475569;margin-bottom:18px">{row['pin_desc']}</p>
    {cards_html}
    {refer_html}
  </div>
</body></html>"""


MOBILE_APP_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>AutoGullak AI v2 — Real-Money Edition</title>
<style>
  :root {
    --bg: #f4f7f5; --card: #ffffff; --ink: #0f172a; --muted: #64748b;
    --brand: #059669; --brand-dark: #065f46; --brand-soft: #d1fae5;
    --gold: #d97706; --gold-soft: #fef3c7; --line: #e2e8f0;
  }
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  body { margin: 0; background: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: var(--ink); }
  .phone-shell { max-width: 460px; min-height: 100vh; margin: 0 auto; background: var(--bg); padding-bottom: 92px; box-shadow: 0 0 40px rgba(15,23,42,0.12); }
  .topbar { background: linear-gradient(135deg, #064e3b, #059669); color: #fff; padding: 18px 18px 20px; border-bottom-left-radius: 24px; border-bottom-right-radius: 24px; }
  .status-pill { display: inline-flex; align-items: center; gap: 7px; background: rgba(255,255,255,0.16); padding: 5px 12px; border-radius: 99px; font-size: 12px; font-weight: 600; }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 8px #4ade80; }
  .topbar h1 { margin: 10px 0 3px; font-size: 21px; }
  .topbar p { margin: 0; font-size: 12.5px; opacity: 0.9; }
  .section { padding: 14px 16px 0; display: none; }
  .section.active { display: block; }
  .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }
  .card { background: var(--card); border: 1px solid var(--line); border-radius: 18px; padding: 15px; margin-bottom: 12px; }
  .stat-num { font-size: 20px; font-weight: 800; margin-top: 4px; }
  .stat-label { font-size: 11.5px; color: var(--muted); font-weight: 600; }
  .btn { width: 100%; border: none; border-radius: 13px; padding: 12px 14px; font-size: 14px; font-weight: 700; cursor: pointer; }
  .btn-sm { padding: 8px 10px; font-size: 12px; border-radius: 10px; width: auto; }
  .btn-primary { background: var(--brand); color: #fff; }
  .btn-gold { background: linear-gradient(135deg, #d97706, #b45309); color: #fff; }
  .btn-outline { background: #f8fafc; color: var(--ink); border: 1px solid var(--line); }
  .tag { display: inline-block; font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 99px; background: var(--brand-soft); color: var(--brand-dark); }
  .tag-warn { background: #fef3c7; color: #92400e; }
  .pin-card { border: 1px solid var(--line); border-radius: 14px; padding: 12px; margin-bottom: 12px; background: #fff; }
  .log-row { font-size: 12.5px; padding: 7px 0; border-bottom: 1px dashed var(--line); }
  label { display: block; font-size: 12px; font-weight: 700; color: var(--muted); margin: 10px 0 4px; }
  input, select { width: 100%; padding: 10px 12px; border-radius: 10px; border: 1px solid var(--line); font-size: 13.5px; background: #f8fafc; }
  .bottom-nav { position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 460px; background: #fff; border-top: 1px solid var(--line); display: grid; grid-template-columns: repeat(4, 1fr); padding: 8px 6px 12px; z-index: 20; }
  .nav-btn { background: none; border: none; font-size: 11px; font-weight: 700; color: var(--muted); display: flex; flex-direction: column; align-items: center; gap: 3px; cursor: pointer; }
  .nav-btn.active { color: var(--brand); }
  .toast { position: fixed; top: 14px; left: 50%; transform: translateX(-50%); background: #0f172a; color: #fff; font-size: 13px; font-weight: 600; padding: 10px 16px; border-radius: 99px; display: none; z-index: 99; }
</style>
</head>
<body>
<div class="toast" id="toast">Copied!</div>
<div class="phone-shell">
  <div class="topbar">
    <div class="status-pill"><span class="dot"></span><span>Real-Money Mode · Zero Fake Numbers</span></div>
    <h1>AutoGullak AI v2</h1>
    <p id="upiBanner">Checking UPI setup...</p>
  </div>

  <!-- TAB 1: HOME -->
  <div class="section active" id="tab-home">
    <div id="setupAlert" class="card" style="background:#fffbeb;border-color:#fde68a;display:none">
      <strong style="color:#92400e;font-size:13.5px">⚠️ Step 1 Required: Set Your Real UPI & Links!</strong>
      <p style="font-size:12.5px;color:#78350f;margin:5px 0 10px">
        Add your real UPI ID in <strong>⚙️ Setup</strong>, and paste your real <strong>EarnKaro (ekaro.in)</strong> links inside <strong>📌 AI Pins</strong> so real commissions go to YOUR account!
      </p>
      <button class="btn btn-gold" onclick="switchTab('setup')">Go to ⚙️ Setup Now -></button>
    </div>

    <div class="grid-3">
      <div class="card" style="margin-bottom:0;padding:12px">
        <div class="stat-label">Pages Live</div>
        <div class="stat-num" id="statPages">0</div>
      </div>
      <div class="card" style="margin-bottom:0;padding:12px">
        <div class="stat-label">Real Page Views</div>
        <div class="stat-num" id="statViews">0</div>
      </div>
      <div class="card" style="margin-bottom:0;padding:12px">
        <div class="stat-label">Shopper Clicks</div>
        <div class="stat-num" style="color:var(--brand)" id="statClicks">0</div>
      </div>
    </div>

    <div class="card" style="margin-top:12px">
      <strong style="font-size:14.5px">⚡ Build Next Routine Page + 1000x1500 Pin</strong>
      <p style="font-size:12.5px;color:var(--muted);margin:6px 0 12px">
        Creates a ready-to-share Routine Webpage + downloadable Pinterest Pin PNG:
      </p>
      <button class="btn btn-primary" id="runBtn" onclick="triggerCycle()">⚡ Generate Routine + Pin Now</button>
    </div>

    <div class="card">
      <strong style="font-size:14px;display:block;margin-bottom:6px">Real Activity Log</strong>
      <div id="logsBox"></div>
    </div>
  </div>

  <!-- TAB 2: AI PINS & REAL EARNKARO LINKS -->
  <div class="section" id="tab-pins">
    <div class="card">
      <strong style="font-size:15px">📌 Your Pins & Real EarnKaro Links</strong>
      <p style="font-size:12px;color:var(--muted);margin:4px 0 0">
        1. Paste your 3 real <strong>ekaro.in</strong> links once per routine.<br>
        2. Download the Pin PNG & tap "Copy Pin Link" to post on Pinterest!
      </p>
    </div>
    <div id="pinsList"></div>
  </div>

  <!-- TAB 3: REAL EARNKARO + GOLD VAULT -->
  <div class="section" id="tab-vault">
    <div class="card" style="background:linear-gradient(135deg,#064e3b,#047857);color:#fff;border:none">
      <div style="font-size:12px;opacity:0.9;font-weight:700">HOW REAL PAYOUTS WORK (NO PAN CARD)</div>
      <p style="font-size:13px;line-height:1.5;margin:8px 0 14px">
        When shoppers click your Routine Pages and buy, real rupees appear inside your <strong>EarnKaro App ("My Earnings")</strong>. Once ₹10+ is Confirmed, tap below to withdraw straight to your UPI (<strong id="vaultUpiText">Not set</strong>)!
      </p>
      <a href="https://earnkaro.com/profile" target="_blank" class="btn" style="display:block;text-align:center;text-decoration:none;background:#fff;color:#064e3b">
        1. Open EarnKaro -> Withdraw Real ₹ to UPI ↗
      </a>
    </div>

    <div class="card">
      <strong style="font-size:14.5px">🪙 24K Digital Gold Vault Tracker</strong>
      <p style="font-size:12.5px;color:var(--muted);margin:5px 0 12px">
        Record every real EarnKaro payout + daily ₹10 Gold save you make on PhonePe / Paytm (MMTC-PAMP):
      </p>
      <div class="grid-3" style="margin-bottom:12px">
        <div style="background:#f8fafc;padding:10px;border-radius:12px">
          <div class="stat-label">Withdrawn</div>
          <div class="stat-num" style="font-size:17px">₹<span id="realWithdrawn">0</span></div>
        </div>
        <div style="background:#fffbeb;padding:10px;border-radius:12px">
          <div class="stat-label">In Gold Vault</div>
          <div class="stat-num" style="font-size:17px;color:#b45309">₹<span id="goldSaved">0</span></div>
        </div>
        <div style="background:#ecfdf5;padding:10px;border-radius:12px">
          <div class="stat-label">Shopper Clicks</div>
          <div class="stat-num" style="font-size:17px;color:#059669" id="vaultClicks">0</div>
        </div>
      </div>
      <div style="display:flex;gap:8px;margin-bottom:10px">
        <input id="logAmt" type="number" placeholder="Enter real ₹ earned (e.g. 50)" style="margin:0">
        <button class="btn btn-primary btn-sm" onclick="recordRealPayout()" style="white-space:nowrap">+ Log Real ₹</button>
      </div>
      <a href="https://paytm.com/digitalgold" target="_blank" class="btn btn-gold" style="display:block;text-align:center;text-decoration:none">
        2. Put ₹10 / Profit into MMTC-PAMP Digital Gold ↗
      </a>
    </div>
  </div>

  <!-- TAB 4: SETUP -->
  <div class="section" id="tab-setup">
    <div class="card">
      <strong style="font-size:15px">⚙️ Permanent Setup (Your Real Account)</strong>
      <label>Your Real UPI ID (So you never see a demo ID)</label>
      <input id="cfgUpi" placeholder="e.g. 9876543210@ybl">

      <label>Auto-Monetize Option: Cuelinks Publisher ID (Optional)</label>
      <input id="cfgCuelinks" placeholder="Leave blank if pasting EarnKaro ekaro.in links">

      <label>Your EarnKaro 10% Referral Link (Optional Footer Bonus)</label>
      <input id="cfgRefer" placeholder="https://topdeal.app.link/...">

      <label>Gold Vault Split %</label>
      <select id="cfgSplit">
        <option value="50">Save 50% in Gold / Keep 50%</option>
        <option value="100">Save 100% in Gold</option>
        <option value="30">Save 30% in Gold / Keep 70%</option>
      </select>

      <label>Free Gemini API Key (Optional — Unlimited New AI Topics)</label>
      <input id="cfgGemini" type="password" placeholder="AIza...">

      <button class="btn btn-primary" style="margin-top:14px" onclick="saveSettings()">Save My Real Settings</button>
      <p style="font-size:11.5px;color:var(--muted);margin-top:10px;line-height:1.4">
        💡 <strong>Tip for Render Free Plan:</strong> Also add <code>UPI_ID</code> in Render -> Environment Variables so Render keeps it even after server sleep!
      </p>
    </div>
  </div>

  <div class="bottom-nav">
    <button class="nav-btn active" onclick="switchTab('home')" id="nav-home"><span>⚡</span>Home</button>
    <button class="nav-btn" onclick="switchTab('pins')" id="nav-pins"><span>📌</span>AI Pins</button>
    <button class="nav-btn" onclick="switchTab('vault')" id="nav-vault"><span>🪙</span>₹ Vault</button>
    <button class="nav-btn" onclick="switchTab('setup')" id="nav-setup"><span>⚙️</span>Setup</button>
  </div>
</div>

<script>
let state = {};

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.display = 'block';
  setTimeout(() => { t.style.display = 'none'; }, 2600);
}

function switchTab(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  document.getElementById('nav-' + name).classList.add('active');
}

function copyText(txt, label) {
  navigator.clipboard.writeText(txt);
  showToast('Copied ' + label + '!');
}

async function fetchState() {
  const res = await fetch('api/status');
  const data = await res.json();
  state = data;

  const upi = (data.config.upi_id || '').trim();
  const hasRealUpi = upi && upi !== 'yourname@upi';
  document.getElementById('upiBanner').textContent = hasRealUpi
    ? ('Linked UPI: ' + upi)
    : 'Tap ⚙️ Setup to enter your real UPI ID';
  document.getElementById('vaultUpiText').textContent = hasRealUpi ? upi : 'Set in ⚙️ Setup first';
  document.getElementById('setupAlert').style.display = hasRealUpi ? 'none' : 'block';

  let totalViews = 0, totalClicks = 0;
  data.routines.forEach(r => { totalViews += r.views; totalClicks += r.clicks; });

  document.getElementById('statPages').textContent = data.routines.length;
  document.getElementById('statViews').textContent = totalViews;
  document.getElementById('statClicks').textContent = totalClicks;
  document.getElementById('vaultClicks').textContent = totalClicks;
  document.getElementById('realWithdrawn').textContent = Math.round(data.wallet.real_withdrawn_inr);
  document.getElementById('goldSaved').textContent = Math.round(data.wallet.gold_vault_inr);

  document.getElementById('cfgUpi').value = hasRealUpi ? upi : '';
  document.getElementById('cfgCuelinks').value = data.config.cuelinks_cid || '';
  document.getElementById('cfgRefer').value = data.config.earnkaro_refer_url || '';
  document.getElementById('cfgSplit').value = data.config.gold_split_pct || '50';

  document.getElementById('logsBox').innerHTML = data.logs.map(l =>
    `<div class="log-row"><strong style="color:#065f46">[${l.engine}]</strong> ${l.message} <span style="color:#94a3b8;font-size:11px">(${l.created_at})</span></div>`
  ).join('') || '<div class="log-row">System ready.</div>';

  const origin = window.location.origin;
  document.getElementById('pinsList').innerHTML = data.routines.map(r => {
    const steps = JSON.parse(r.steps_json);
    const pageUrl = origin + '/r/' + r.slug;
    const isWarn = r.link_mode.includes('⚠️');
    return `
      <div class="pin-card">
        <div style="display:flex;gap:12px;align-items:flex-start">
          <a href="pins/${r.pin_image}" download="${r.pin_image}">
            <img src="pins/${r.pin_image}" style="width:68px;height:102px;border-radius:10px;border:1px solid #e2e8f0;object-fit:cover">
          </a>
          <div style="flex:1;min-width:0">
            <span class="tag ${isWarn ? 'tag-warn' : ''}">${r.link_mode}</span>
            <div style="font-size:14px;font-weight:700;margin:5px 0 3px">${r.pin_headline}</div>
            <div style="font-size:11.5px;color:#64748b;margin-bottom:8px">Board: ${r.board} · Views: ${r.views} · Clicks: ${r.clicks}</div>
            <div style="display:flex;flex-wrap:wrap;gap:6px">
              <a href="pins/${r.pin_image}" download="${r.pin_image}" class="btn btn-outline btn-sm" style="text-decoration:none">⬇ Save Pin PNG</a>
              <button class="btn btn-outline btn-sm" onclick='copyText(${JSON.stringify(r.pin_title)}, "Pin Title")'>Copy Title</button>
              <button class="btn btn-outline btn-sm" onclick='copyText(${JSON.stringify(r.pin_desc)}, "Description")'>Copy Desc</button>
              <button class="btn btn-primary btn-sm" onclick='copyText(${JSON.stringify(pageUrl)}, "Page Link")'>Copy Page Link</button>
            </div>
          </div>
        </div>
        <details style="margin-top:10px;border-top:1px dashed #e2e8f0;padding-top:8px">
          <summary style="font-size:12.5px;font-weight:700;color:#059669;cursor:pointer">🔗 Paste Your 3 Real EarnKaro (ekaro.in) Links Here</summary>
          <div style="margin-top:8px">
            <label>Step 1 Link (${steps[0].name})</label>
            <input id="lnk_${r.id}_0" value="${steps[0].aff_url}">
            <label>Step 2 Link (${steps[1].name})</label>
            <input id="lnk_${r.id}_1" value="${steps[1].aff_url}">
            <label>Step 3 Link (${steps[2].name})</label>
            <input id="lnk_${r.id}_2" value="${steps[2].aff_url}">
            <button class="btn btn-primary" style="margin-top:10px" onclick="saveRoutineLinks(${r.id}, '${r.slug}')">Save Real Links for This Page</button>
          </div>
        </details>
      </div>
    `;
  }).join('');
}

async function saveRoutineLinks(id, slug) {
  const urls = [
    document.getElementById(`lnk_${id}_0`).value.trim(),
    document.getElementById(`lnk_${id}_1`).value.trim(),
    document.getElementById(`lnk_${id}_2`).value.trim(),
  ];
  await fetch('api/update-links', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slug, urls })
  });
  await fetchState();
  showToast('Real EarnKaro Links Saved!');
}

async function triggerCycle() {
  const btn = document.getElementById('runBtn');
  btn.disabled = true;
  btn.textContent = '⏳ Building...';
  await fetch('api/run-cycle', { method: 'POST' });
  await fetchState();
  btn.disabled = false;
  btn.textContent = '⚡ Generate Routine + Pin Now';
  showToast('Done! Check AI Pins tab.');
}

async function recordRealPayout() {
  const upi = (state.config.upi_id || '').trim();
  if (!upi || upi === 'yourname@upi') {
    showToast('Set your real UPI ID in ⚙️ Setup first!');
    switchTab('setup');
    return;
  }
  const val = parseFloat(document.getElementById('logAmt').value || '0');
  if (val <= 0) { showToast('Enter a valid ₹ amount'); return; }
  await fetch('api/log-payout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount: val })
  });
  document.getElementById('logAmt').value = '';
  await fetchState();
  showToast('Logged real payout + Gold split!');
}

async function saveSettings() {
  const upi = document.getElementById('cfgUpi').value.trim();
  if (!upi || upi === 'yourname@upi' || !upi.includes('@')) {
    showToast('Please enter a valid UPI ID (with @)!');
    return;
  }
  await fetch('api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      upi_id: upi,
      cuelinks_cid: document.getElementById('cfgCuelinks').value.trim(),
      earnkaro_refer_url: document.getElementById('cfgRefer').value.trim(),
      gold_split_pct: document.getElementById('cfgSplit').value,
      gemini_api_key: document.getElementById('cfgGemini').value.trim(),
    })
  });
  await fetchState();
  showToast('Your Real UPI & Settings Saved!');
}

fetchState();
</script>
</body>
</html>
"""


class AutoGullakHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            return self._send(200, MOBILE_APP_HTML, "text/html; charset=utf-8")

        if path == "/api/status":
            conn = get_db()
            routines = [dict(r) for r in conn.execute("SELECT * FROM routines ORDER BY id DESC LIMIT 30").fetchall()]
            logs = [dict(l) for l in conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 12").fetchall()]
            wallet = dict(conn.execute("SELECT * FROM wallet WHERE id = 1").fetchone())
            conn.close()
            return self._send(200, json.dumps({"config": get_config_dict(), "routines": routines, "logs": logs, "wallet": wallet}))

        if path.startswith("/pins/"):
            fname = os.path.basename(path)
            fpath = os.path.join(PINS_DIR, fname)
            if os.path.exists(fpath):
                with open(fpath, "rb") as f:
                    return self._send(200, f.read(), "image/png")
            return self._send(404, b"Pin not found", "text/plain")

        if path.startswith("/r/"):
            slug = path.split("/r/", 1)[1].strip("/")
            conn = get_db()
            row = conn.execute("SELECT * FROM routines WHERE slug = ?", (slug,)).fetchone()
            if row:
                conn.execute("UPDATE routines SET views = views + 1 WHERE slug = ?", (slug,))
                conn.commit()
                conn.close()
                return self._send(200, render_routine_public_html(dict(row), get_config_dict()), "text/html; charset=utf-8")
            conn.close()
            return self._send(404, "Routine not found", "text/plain")

        # Click tracker redirect (/go/<slug>/<step_idx>) so user sees REAL shopper clicks!
        if path.startswith("/go/"):
            parts = path.split("/go/", 1)[1].strip("/").split("/")
            if len(parts) == 2:
                slug, idx_str = parts[0], parts[1]
                conn = get_db()
                row = conn.execute("SELECT steps_json FROM routines WHERE slug = ?", (slug,)).fetchone()
                if row and idx_str.isdigit():
                    steps = json.loads(row["steps_json"])
                    idx = int(idx_str)
                    if 0 <= idx < len(steps):
                        target = steps[idx]["aff_url"]
                        conn.execute("UPDATE routines SET clicks = clicks + 1 WHERE slug = ?", (slug,))
                        conn.commit()
                        conn.close()
                        self.send_response(302)
                        self.send_header("Location", target)
                        self.end_headers()
                        return
                conn.close()
            return self._send(404, "Link not found", "text/plain")

        return self._send(404, "Not found", "text/plain")

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        body = json.loads(raw or "{}")

        if path == "/api/run-cycle":
            slug = run_autonomous_cycle()
            return self._send(200, json.dumps({"ok": True, "slug": slug}))

        if path == "/api/update-links":
            slug = body.get("slug", "")
            urls = body.get("urls", [])
            conn = get_db()
            row = conn.execute("SELECT steps_json FROM routines WHERE slug = ?", (slug,)).fetchone()
            if row and len(urls) == 3:
                steps = json.loads(row["steps_json"])
                all_ekaro = True
                for i in range(3):
                    steps[i]["aff_url"] = urls[i]
                    if "ekaro.in" not in urls[i] and "linksredirect" not in urls[i]:
                        all_ekaro = False
                badge = "EarnKaro Live ✅" if all_ekaro else "Custom Links Saved ✅"
                conn.execute("UPDATE routines SET steps_json = ?, link_mode = ? WHERE slug = ?", (json.dumps(steps), badge, slug))
                conn.commit()
                log_event("Real Links", f"Updated 3 affiliate links on '/r/{slug}' ({badge}).")
            conn.close()
            return self._send(200, json.dumps({"ok": True}))

        if path == "/api/log-payout":
            amt = float(body.get("amount", 0))
            cfg = get_config_dict()
            split = float(cfg.get("gold_split_pct", "50")) / 100.0
            to_gold = round(amt * split, 2)
            conn = get_db()
            conn.execute("UPDATE wallet SET real_withdrawn_inr = real_withdrawn_inr + ?, gold_vault_inr = gold_vault_inr + ? WHERE id = 1", (amt, to_gold))
            conn.commit()
            conn.close()
            log_event("Real Payout", f"Logged ₹{int(amt)} withdrawn to {cfg.get('upi_id')} (₹{int(to_gold)} earmarked for Gold Vault).")
            return self._send(200, json.dumps({"ok": True}))

        if path == "/api/config":
            conn = get_db()
            for k, v in body.items():
                if v != "" or k in ("cuelinks_cid", "earnkaro_refer_url"):
                    conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (k, str(v)))
            conn.commit()
            conn.close()
            log_event("Setup", f"Saved permanent account settings (UPI: {body.get('upi_id', 'updated')}).")
            return self._send(200, json.dumps({"ok": True}))

        return self._send(404, json.dumps({"error": "Not found"}))


def background_scheduler_loop():
    while True:
        time.sleep(43200)
        try:
            if get_config_dict().get("autopilot_enabled") == "1":
                run_autonomous_cycle()
        except Exception:
            pass


if __name__ == "__main__":
    init_db()
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) AS c FROM routines").fetchone()["c"]
    conn.close()
    if count == 0:
        for _ in range(4):
            run_autonomous_cycle()

    if "--cron" in sys.argv:
        slug = run_autonomous_cycle()
        print(f"[AutoGullak v2 Cron] Completed -> {slug}")
        sys.exit(0)

    threading.Thread(target=background_scheduler_loop, daemon=True).start()
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), AutoGullakHandler)
    print(f"AutoGullak AI v2 running on http://0.0.0.0:{port}")
    server.serve_forever()
