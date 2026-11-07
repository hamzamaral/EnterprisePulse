# -*- coding: utf-8 -*-
"""Generate sellable, print-ready HTML manuals from markdown + screenshots."""
from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

ROOTS = [
    {
        "docs": Path(r"c:/github/EnterprisePulse.NET/docs"),
        "shots_src": Path(r"c:/github/EnterprisePulse.NET/docs/screenshots"),
        "brand": "EnterprisePulse.NET",
        "tag": "ASP.NET Core 10 · Blazor",
        "accent": "#4338ca",
    },
    {
        "docs": Path(r"c:/github/EnterprisePulse.Java/docs"),
        "shots_src": Path(r"c:/github/EnterprisePulse.Java/docs/screenshots"),
        "brand": "EnterprisePulse.Java",
        "tag": "Spring Boot 3.5 · Vaadin 24",
        "accent": "#4338ca",
    },
    {
        "docs": Path(r"c:/github/EnterprisePulse/docs"),
        "shots_src": Path(r"c:/github/EnterprisePulse/web/docs/screenshots"),
        "brand": "EnterprisePulse",
        "tag": "NestJS 11 · React 19",
        "accent": "#4338ca",
    },
]

# Section number → screenshot filenames (relative to screenshots/)
SECTION_SHOTS = {
    0: [("dashboard.png", "Gösterge paneli"), ("login.png", "Giriş ekranı")],
    1: [("dashboard.png", "Gösterge paneli")],
    2: [("my-leave.png", "İzinlerim")],
    7: [("support.png", "Destek kuyruğu")],
    9: [("assets.png", "Demirbaşlar"), ("asset-detail.png", "Demirbaş detayı")],
    10: [("inventory.png", "Stok durumu")],
    13: [("crm-opportunity.png", "Satış fırsatı"), ("crm-pipeline.png", "CRM hattı")],
    14: [("sales-invoices.png", "Satış faturaları")],
    15: [("treasury.png", "Kasa ve bankalar"), ("finance-accounts.png", "Kasa / banka")],
    16: [("accounting.png", "Muhasebe")],
    17: [("contracts.png", "Sözleşmeler")],
}

CSS = r"""
:root {
  --ink: #0f172a;
  --muted: #64748b;
  --line: #e2e8f0;
  --bg: #f8fafc;
  --card: #ffffff;
  --accent: ACCENT;
  --accent-soft: color-mix(in srgb, var(--accent) 12%, white);
  --radius: 14px;
  --shadow: 0 10px 30px rgba(15, 23, 42, .06);
  --font: "Segoe UI", Inter, system-ui, -apple-system, sans-serif;
  --mono: ui-monospace, Consolas, "Cascadia Mono", monospace;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: var(--font);
  color: var(--ink);
  background:
    radial-gradient(1200px 500px at 10% -10%, color-mix(in srgb, var(--accent) 18%, transparent), transparent 60%),
    radial-gradient(900px 400px at 100% 0%, rgba(14,165,233,.12), transparent 55%),
    var(--bg);
  line-height: 1.55;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 0;
  min-height: 100vh;
}
.toc {
  position: sticky;
  top: 0;
  height: 100vh;
  overflow: auto;
  padding: 28px 18px 40px;
  background: rgba(255,255,255,.82);
  backdrop-filter: blur(10px);
  border-right: 1px solid var(--line);
}
.toc .brand {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 18px;
  padding: 0 8px 16px;
  border-bottom: 1px solid var(--line);
}
.toc .brand strong { font-size: 1.05rem; letter-spacing: -.01em; }
.toc .brand span { color: var(--muted); font-size: .82rem; }
.toc nav a {
  display: block;
  padding: 7px 10px;
  border-radius: 8px;
  color: var(--ink);
  font-size: .88rem;
}
.toc nav a:hover { background: var(--accent-soft); text-decoration: none; }
.toc nav a.h2 { font-weight: 650; margin-top: 6px; }
.toc nav a.h3 { padding-left: 18px; color: var(--muted); font-size: .82rem; }
.main { padding: 28px 36px 80px; max-width: 980px; }
.hero {
  background: linear-gradient(135deg, #312e81 0%, var(--accent) 55%, #0ea5e9 120%);
  color: #fff;
  border-radius: 22px;
  padding: 36px 36px 30px;
  box-shadow: var(--shadow);
  margin-bottom: 28px;
  position: relative;
  overflow: hidden;
}
.hero::after {
  content: "";
  position: absolute;
  right: -40px; top: -40px;
  width: 220px; height: 220px;
  border-radius: 50%;
  background: rgba(255,255,255,.08);
}
.hero .eyebrow {
  display: inline-flex;
  gap: 8px;
  align-items: center;
  background: rgba(255,255,255,.14);
  border: 1px solid rgba(255,255,255,.22);
  padding: 6px 12px;
  border-radius: 999px;
  font-size: .8rem;
  margin-bottom: 14px;
}
.hero h1 {
  margin: 0 0 10px;
  font-size: clamp(1.7rem, 3vw, 2.35rem);
  letter-spacing: -.03em;
  line-height: 1.15;
  border: 0;
  color: #fff;
}
.hero p { margin: 0; opacity: .92; max-width: 46rem; }
.hero .meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
}
.pill {
  background: rgba(255,255,255,.14);
  border: 1px solid rgba(255,255,255,.2);
  padding: 6px 12px;
  border-radius: 999px;
  font-size: .8rem;
}
.print-hint {
  margin: 0 0 18px;
  color: var(--muted);
  font-size: .9rem;
}
.card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 22px 24px;
  margin: 18px 0;
}
h1 { font-size: 1.9rem; letter-spacing: -.02em; margin: 0 0 .4em; }
h2 {
  font-size: 1.35rem;
  letter-spacing: -.015em;
  margin: 2rem 0 .75rem;
  padding-bottom: .35rem;
  border-bottom: 2px solid color-mix(in srgb, var(--accent) 35%, var(--line));
  page-break-after: avoid;
}
h3 {
  font-size: 1.08rem;
  margin: 1.35rem 0 .45rem;
  color: #1e293b;
  page-break-after: avoid;
}
p { margin: .55rem 0; }
ul, ol { padding-left: 1.2rem; margin: .45rem 0 .9rem; }
li { margin: .28rem 0; }
blockquote {
  margin: 12px 0;
  padding: 12px 16px;
  border-left: 4px solid var(--accent);
  background: var(--accent-soft);
  border-radius: 0 12px 12px 0;
  color: #1e293b;
}
code {
  font-family: var(--mono);
  font-size: .88em;
  background: #f1f5f9;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: .08em .4em;
}
pre {
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 12px;
  padding: 14px 16px;
  overflow: auto;
  font-family: var(--mono);
  font-size: .85rem;
}
pre code { background: none; border: 0; color: inherit; padding: 0; }
hr { border: 0; border-top: 1px solid var(--line); margin: 1.8rem 0; }
.gallery {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
  margin: 14px 0 8px;
}
.shot {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow);
  break-inside: avoid;
}
.shot img {
  display: block;
  width: 100%;
  height: auto;
  background: #eef2ff;
}
.shot figcaption {
  padding: 8px 12px 10px;
  font-size: .82rem;
  color: var(--muted);
  border-top: 1px solid var(--line);
}
.section-intro {
  color: var(--muted);
  font-size: .95rem;
}
.footer-note {
  margin-top: 48px;
  padding-top: 18px;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: .85rem;
}
@media (max-width: 960px) {
  .layout { grid-template-columns: 1fr; }
  .toc { position: relative; height: auto; max-height: 280px; }
  .main { padding: 18px 16px 48px; }
}
@media print {
  body { background: #fff; }
  .toc { display: none; }
  .layout { display: block; }
  .main { max-width: none; padding: 0; }
  .hero { box-shadow: none; break-after: avoid; }
  .card, .shot { box-shadow: none; }
  a { color: inherit; text-decoration: none; }
  .print-hint { display: none; }
}
"""


def inline(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def parse_md(md: str) -> list[dict]:
    blocks: list[dict] = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            buf = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            blocks.append({"t": "pre", "v": "\n".join(buf)})
            i += 1
            continue
        if line.strip() == "---":
            blocks.append({"t": "hr"})
            i += 1
            continue
        if line.startswith("# "):
            blocks.append({"t": "h1", "v": line[2:]})
            i += 1
            continue
        if line.startswith("## "):
            blocks.append({"t": "h2", "v": line[3:]})
            i += 1
            continue
        if line.startswith("### "):
            blocks.append({"t": "h3", "v": line[4:]})
            i += 1
            continue
        if line.startswith("> "):
            blocks.append({"t": "quote", "v": line[2:]})
            i += 1
            continue
        if line.startswith("- ") or re.match(r"^\d+\. ", line):
            items = []
            while i < len(lines) and (lines[i].startswith("- ") or re.match(r"^\d+\. ", lines[i])):
                items.append(re.sub(r"^(?:- |\d+\. )", "", lines[i]))
                i += 1
            blocks.append({"t": "ul", "v": items})
            continue
        if not line.strip():
            i += 1
            continue
        para = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", ">", "-", "```", "---")) and not re.match(r"^\d+\. ", lines[i]):
            para.append(lines[i])
            i += 1
        blocks.append({"t": "p", "v": " ".join(para)})
    return blocks


def slug(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^\w\s\-çğıöşüÇĞİÖŞÜ]", "", s, flags=re.I)
    s = re.sub(r"\s+", "-", s.strip())
    return s[:80] or "sec"


def section_num(heading: str) -> int | None:
    m = re.match(r"^(\d+)\.", heading.strip())
    return int(m.group(1)) if m else None


def ensure_shots(docs: Path, src: Path, names: set[str]) -> None:
    dest = docs / "screenshots"
    dest.mkdir(parents=True, exist_ok=True)
    for name in names:
        s = src / name
        d = dest / name
        if s.exists() and (not d.exists() or s.stat().st_mtime > d.stat().st_mtime):
            shutil.copy2(s, d)
        # also try alternate locations for nest
        if not d.exists():
            for alt in [
                Path(r"c:/github/EnterprisePulse.NET/docs/screenshots") / name,
                Path(r"c:/github/EnterprisePulse.Java/docs/screenshots") / name,
                Path(r"c:/github/EnterprisePulse/web/docs/screenshots") / name,
            ]:
                if alt.exists():
                    shutil.copy2(alt, d)
                    break


def gallery_html(docs: Path, section: int | None) -> str:
    if section is None or section not in SECTION_SHOTS:
        return ""
    parts = ['<div class="gallery">']
    for fname, caption in SECTION_SHOTS[section]:
        path = docs / "screenshots" / fname
        if not path.exists():
            continue
        parts.append(
            f'<figure class="shot"><img src="screenshots/{html.escape(fname)}" alt="{html.escape(caption)}"/>'
            f"<figcaption>{html.escape(caption)}</figcaption></figure>"
        )
    parts.append("</div>")
    return "\n".join(parts) if len(parts) > 2 else ""


def render(md_path: Path, cfg: dict) -> Path:
    docs: Path = cfg["docs"]
    md = md_path.read_text(encoding="utf-8")
    blocks = parse_md(md)

    # collect needed shots
    needed = set()
    for pairs in SECTION_SHOTS.values():
        for n, _ in pairs:
            needed.add(n)
    ensure_shots(docs, cfg["shots_src"], needed)

    toc = []
    body = []
    title = cfg["brand"]
    current_section: int | None = None
    first_h1 = True
    hero_done = False

    for b in blocks:
        if b["t"] == "h1":
            title = b["v"]
            if first_h1:
                first_h1 = False
                body.append(
                    f'''<section class="hero">
  <div class="eyebrow">{html.escape(cfg["tag"])} · Satış / demo dokümanı</div>
  <h1>{inline(b["v"])}</h1>
  <p>Modül gruplarına göre ekran kılavuzu. Yetkiye göre menü öğeleri görünür; demo veri Pulse Teknoloji üzerindedir.</p>
  <div class="meta">
    <span class="pill">TR / EN</span>
    <span class="pill">Ctrl+P → PDF</span>
    <span class="pill">{html.escape(cfg["brand"])}</span>
  </div>
</section>'''
                )
                # lead gallery
                g = gallery_html(docs, 0)
                if g:
                    body.append('<div class="card">' + g + "</div>")
                hero_done = True
            else:
                sid = slug(b["v"])
                toc.append(("h1", b["v"], sid))
                body.append(f'<h1 id="{sid}">{inline(b["v"])}</h1>')
            continue
        if b["t"] == "h2":
            current_section = section_num(b["v"])
            if current_section == 0:
                current_section = 0
            sid = slug(b["v"])
            toc.append(("h2", b["v"], sid))
            body.append(f'<h2 id="{sid}">{inline(b["v"])}</h2>')
            g = gallery_html(docs, current_section if current_section and current_section > 0 else None)
            # for "## 0. Giriş" also show nothing extra (hero has shots)
            if current_section and current_section > 0 and g:
                body.append(g)
            continue
        if b["t"] == "h3":
            sid = slug(b["v"])
            toc.append(("h3", b["v"], sid))
            body.append(f'<div class="card"><h3 id="{sid}">{inline(b["v"])}</h3>')
            # close card later — track with marker
            body.append("<!--card-open-->")
            continue
        if b["t"] == "quote":
            body.append(f"<blockquote>{inline(b['v'])}</blockquote>")
            continue
        if b["t"] == "ul":
            body.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in b["v"]) + "</ul>")
            continue
        if b["t"] == "pre":
            body.append(f"<pre><code>{html.escape(b['v'])}</code></pre>")
            continue
        if b["t"] == "hr":
            # close open card if any
            body.append("</div>" if "<!--card-open-->" in body[-5:] else "")
            # cleaner: flush open cards
            joined = "\n".join(body)
            # replace dangling card-open markers by closing after next few blocks — simpler close before hr
            body = [x for x in body if x != "<!--card-open-->"]
            # If last card opened without close, close it
            # Count card opens vs closes roughly
            body.append("<hr/>")
            continue
        if b["t"] == "p":
            body.append(f"<p>{inline(b['v'])}</p>")
            continue

    # Close any unclosed cards: after h3 we left card open — wrap subsequent until next h2/h3/hr
    # Rebuild body properly
    rebuilt: list[str] = []
    open_card = False
    for x in body:
        if x == "<!--card-open-->":
            open_card = True
            continue
        if x.startswith("<h2") or x.startswith("<hr") or x.startswith('<section class="hero"'):
            if open_card:
                rebuilt.append("</div>")
                open_card = False
            rebuilt.append(x)
            continue
        if x.startswith('<div class="card"><h3'):
            if open_card:
                rebuilt.append("</div>")
            rebuilt.append(x)
            open_card = True
            continue
        rebuilt.append(x)
    if open_card:
        rebuilt.append("</div>")
    body = rebuilt

    toc_html = []
    for kind, text, sid in toc:
        cls = "h2" if kind == "h2" else "h3" if kind == "h3" else "h1"
        if kind == "h1":
            continue
        toc_html.append(f'<a class="{cls}" href="#{sid}">{html.escape(text)}</a>')

    css = CSS.replace("ACCENT", cfg["accent"])
    out = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{html.escape(title)}</title>
<style>{css}</style>
</head>
<body>
<div class="layout">
  <aside class="toc">
    <div class="brand">
      <strong>{html.escape(cfg["brand"])}</strong>
      <span>{html.escape(cfg["tag"])}</span>
    </div>
    <nav>
      <a class="h2" href="#top">Başa dön</a>
      {"".join(toc_html)}
    </nav>
  </aside>
  <main class="main" id="top">
    <p class="print-hint">Satış / demo kılavuzu · Yazdır: <strong>Ctrl+P → PDF olarak kaydet</strong></p>
    {"".join(body)}
    <p class="footer-note">EnterprisePulse — {html.escape(cfg["brand"])}. Bu HTML, markdown kaynaktan üretilmiştir; güncelleme için md dosyasını düzenleyin.</p>
  </main>
</div>
</body>
</html>
"""
    out_path = md_path.with_suffix(".html")
    out_path.write_text(out, encoding="utf-8")
    return out_path


def main() -> None:
    for cfg in ROOTS:
        docs = cfg["docs"]
        for name in ("kullanici-kilavuzu.md", "teknik-kilavuz.md"):
            md = docs / name
            if not md.exists():
                print("skip", md)
                continue
            path = render(md, cfg)
            print("wrote", path, path.stat().st_size)


if __name__ == "__main__":
    main()
