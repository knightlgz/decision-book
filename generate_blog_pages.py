#!/usr/bin/env python3
"""
生成 blog 板块静态页（SEO 问答线内容）
用法：python3 generate_blog_pages.py

输入：blog_src/*.md（每篇带 frontmatter：title/slug/description/keywords/date/related）
输出：
  public/blog/<slug>/index.html   ← 每篇文章页
  public/blog/index.html          ← 文章索引
  public/sitemap.xml              ← 增量更新（清理旧 blog 条目后追加）
"""
import json
import re
import datetime
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "blog_src"
PUBLIC = ROOT / "public"
BASE_URL = "https://decision-book.vercel.app"

# ---------- frontmatter 解析 ----------

def parse_md(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n([\s\S]*?)\n---\n([\s\S]*)$", text)
    if not m:
        raise ValueError(f"{path.name}: 缺 frontmatter")
    meta_raw, body = m.group(1), m.group(2)
    meta = {}
    for line in meta_raw.split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, body.strip()

# ---------- 轻量 Markdown → HTML ----------

def inline_md(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s

def md_to_html(body):
    html, para, in_ul = [], [], False
    def flush_para():
        if para:
            html.append("<p>" + inline_md(" ".join(para)) + "</p>")
            para.clear()
    def close_ul():
        nonlocal in_ul
        if in_ul:
            html.append("</ul>")
            in_ul = False
    for line in body.split("\n"):
        line = line.rstrip()
        if not line:
            flush_para(); close_ul(); continue
        if line.startswith("### "):
            flush_para(); close_ul(); html.append("<h3>" + inline_md(line[4:]) + "</h3>")
        elif line.startswith("## "):
            flush_para(); close_ul(); html.append("<h2>" + inline_md(line[3:]) + "</h2>")
        elif line.startswith("# "):
            flush_para(); close_ul(); html.append("<h2>" + inline_md(line[2:]) + "</h2>")
        elif line.startswith("- "):
            flush_para()
            if not in_ul:
                html.append("<ul>"); in_ul = True
            html.append("<li>" + inline_md(line[2:]) + "</li>")
        else:
            close_ul(); para.append(line)
    flush_para(); close_ul()
    return "\n".join(html)

# ---------- 页面模板 ----------

CSS = """
:root{--ink:#1a1a1a;--sub:#666;--line:#e5e5e5;--bg:#fafaf8;--accent:#8a6d3b}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,"PingFang TC","Noto Sans TC",sans-serif;background:var(--bg);color:var(--ink);line-height:1.9;font-size:16px}
.wrap{max-width:680px;margin:0 auto;padding:48px 22px 80px}
.nav{display:flex;justify-content:space-between;align-items:center;padding-bottom:18px;border-bottom:1px solid var(--line);margin-bottom:36px}
.nav a{color:var(--ink);text-decoration:none;font-weight:700;letter-spacing:.12em}
.nav .sub{color:var(--sub);font-size:12px;letter-spacing:.2em}
h1{font-size:26px;line-height:1.5;margin-bottom:10px;letter-spacing:.02em}
.meta{color:var(--sub);font-size:13px;margin-bottom:34px}
h2{font-size:19px;margin:36px 0 14px;padding-left:10px;border-left:3px solid var(--ink)}
h3{font-size:16.5px;margin:26px 0 10px}
p{margin-bottom:16px}
ul{margin:0 0 16px 22px}
li{margin-bottom:8px}
strong{font-weight:700}
a{color:var(--accent)}
.cta{margin:44px 0;padding:26px 24px;background:#fff;border:1px solid var(--line);border-radius:12px;text-align:center}
.cta p{color:var(--sub);font-size:14px;margin-bottom:14px}
.cta a.btn{display:inline-block;background:var(--ink);color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;letter-spacing:.1em;font-size:15px}
.related{margin-top:44px;padding-top:22px;border-top:1px solid var(--line)}
.related h3{font-size:14px;color:var(--sub);letter-spacing:.15em;margin-bottom:14px}
.related a{display:block;padding:10px 0;border-bottom:1px dashed var(--line);text-decoration:none;color:var(--ink)}
.related a:hover{color:var(--accent)}
footer{margin-top:56px;padding-top:22px;border-top:1px solid var(--line);color:var(--sub);font-size:12.5px;line-height:1.8}
.list-item{display:block;padding:20px 0;border-bottom:1px solid var(--line);text-decoration:none;color:var(--ink)}
.list-item .t{font-size:17px;font-weight:700;margin-bottom:6px}
.list-item .d{color:var(--sub);font-size:13.5px}
"""

def page_shell(title, desc, slug, body_html, meta_extra=None, related_html=""):
    meta_extra = meta_extra or {}
    canonical = f"{BASE_URL}/blog/{slug}/" if slug else f"{BASE_URL}/blog/"
    ld = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": title, "description": desc,
        "author": {"@type": "Person", "name": "凱森"},
        "publisher": {"@type": "Organization", "name": "決策之書"},
        "mainEntityOfPage": canonical,
    }
    if meta_extra.get("date"):
        ld["datePublished"] = meta_extra["date"]
    ld_json = json.dumps(ld, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}｜決策之書</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:url" content="{canonical}">
<style>{CSS}</style>
<script type="application/ld+json">{ld_json}</script>
</head>
<body>
<div class="wrap">
<div class="nav">
  <a href="{BASE_URL}/">決策之書</a>
  <span class="sub">易經 × 職場決策</span>
</div>
{body_html}
{related_html}
<footer>
  <p><strong>關於本站</strong>：決策之書——把易經做成一張陪你算帳、也陪你下決定的鏡子。卦不是算盤，不預測吉凶，只把你自己的處境翻給你看。</p>
  <p style="margin-top:8px">本文僅供決策思考參考，不構成任何投資、法律或職業建議。</p>
</footer>
</div>
</body>
</html>"""

# ---------- 主流程 ----------

def main():
    posts = []
    for f in sorted(SRC.glob("*.md")):
        meta, body = parse_md(f)
        posts.append({"meta": meta, "body": body})
    # 按日期倒序
    posts.sort(key=lambda p: p["meta"].get("date", ""), reverse=True)
    print(f"读取 {len(posts)} 篇文章")

    slugs = {p["meta"]["slug"]: p["meta"]["title"] for p in posts}

    # 1. 文章页
    for p in posts:
        m, body = p["meta"], p["body"]
        content = md_to_html(body)
        # CTA 块
        cta = """<div class="cta">
<p>你的處境，換一雙眼睛看看？</p>
<p style="margin-bottom:16px">輸入你正在糾結的職場難題，起一卦，讓易經給你一個不同的視角。</p>
<a class="btn" href="https://decision-book.vercel.app/">開始起卦 →</a>
</div>"""
        # 相关文章
        rel = []
        for rslug in [s.strip() for s in m.get("related", "").split(",") if s.strip()]:
            if rslug in slugs:
                rel.append(f'<a href="/blog/{rslug}/">→ {slugs[rslug]}</a>')
        related = ""
        if rel:
            related = '<div class="related"><h3>延伸閱讀</h3>' + "\n".join(rel) + "</div>"
        body_html = f'<h1>{m["title"]}</h1>\n<p class="meta">{m.get("date","")} · 凱森讀易</p>\n{content}\n{cta}'
        html = page_shell(m["title"], m.get("description", ""), m["slug"], body_html, m, related)
        out = PUBLIC / "blog" / m["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        print(f"  ✓ /blog/{m['slug']}/")

    # 2. 索引页
    items = []
    for p in posts:
        m = p["meta"]
        items.append(
            f'<a class="list-item" href="/blog/{m["slug"]}/">'
            f'<div class="t">{m["title"]}</div>'
            f'<div class="d">{m.get("description","")[:80]}</div></a>'
        )
    idx_body = "<h1>職場決策筆記</h1><p class=\"meta\">易經 × 職場 —— 把真實的難題，想清楚</p>" + "\n".join(items)
    idx_html = page_shell("職場決策筆記", "易經 × 職場決策的內容站：离职、转职、迷茫、被裁员——用真实的判断方法，陪你把难題想清楚。", "", idx_body)
    out = PUBLIC / "blog" / "index.html"
    out.write_text(idx_html, encoding="utf-8")
    print("  ✓ /blog/（索引页）")

    # 3. sitemap 增量（清理旧 blog 条目再追加）
    sm_path = PUBLIC / "sitemap.xml"
    if sm_path.exists():
        sm = sm_path.read_text(encoding="utf-8")
        sm = re.sub(r"\n?\s*<url>\s*<loc>[^<]*/blog/[^<]*</loc>\s*<changefreq>[^<]*</changefreq>\s*</url>", "", sm)
        today = datetime.date.today().isoformat()
        urls = [f"{BASE_URL}/blog/"] + [f"{BASE_URL}/blog/{p['meta']['slug']}/" for p in posts]
        block = "\n".join(
            f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>weekly</changefreq>\n  </url>"
            for u in urls
        )
        sm = sm.replace("</urlset>", block + "\n</urlset>")
        sm_path.write_text(sm, encoding="utf-8")
        print(f"  ✓ sitemap.xml 已更新（+{len(urls)} 条 blog URL）")
    else:
        print("  ⚠️ sitemap.xml 不存在，跳过（先跑 generate_hexagram_pages.py）")


if __name__ == "__main__":
    main()
