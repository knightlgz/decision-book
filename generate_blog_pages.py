#!/usr/bin/env python3
"""
生成 blog 板块静态页（双语：繁 /blog/ + 简 /cn/blog/）
用法：python3 generate_blog_pages.py

输入：blog_src/*.md（繁体源）+ blog_src_cn/*.md（简体源，opencc 转换生成可精修）
输出：
  public/blog/<slug>/index.html       ← 繁体文章页
  public/cn/blog/<slug>/index.html    ← 简体文章页
  public/blog/index.html              ← 繁体索引
  public/cn/blog/index.html           ← 简体索引
  public/sitemap.xml                  ← 增量更新（两语言）
"""
import json
import re
import datetime
from pathlib import Path

ROOT = Path(__file__).parent
PUBLIC = ROOT / "public"
BASE_URL = "https://decision-book.vercel.app"

# ---------- 语言配置（未来加语言=加一项） ----------
LANGS = {
    "tc": {
        "src": ROOT / "blog_src",
        "out": PUBLIC / "blog",
        "prefix": "",                    # URL 前缀（sc 为 /cn）
        "html_lang": "zh-Hant",
        "alternate_hreflang": "zh-Hans",
        "brand": "決策之書",
        "nav_sub": "易經 × 職場決策",
        "switch_label": "简体中文",
        "switch_lang": "sc",
        "author_line": "凱森讀易",
        "cta_h": "你的處境，換一雙眼睛看看？",
        "cta_p": "輸入你正在糾結的職場難題，起一卦，讓易經給你一個不同的視角。",
        "cta_btn": "開始起卦 →",
        "footer_about": "決策之書——把易經做成一張陪你算帳、也陪你下決定的鏡子。卦不是算盤，不預測吉凶，只把你自己的處境翻給你看。",
        "footer_disclaimer": "本文僅供決策思考參考，不構成任何投資、法律或職業建議。",
        "index_title": "職場決策筆記",
        "index_sub": "易經 × 職場 —— 把真實的難題，想清楚",
        "related_label": "延伸閱讀",
    },
    "sc": {
        "src": ROOT / "blog_src_cn",
        "out": PUBLIC / "cn" / "blog",
        "prefix": "/cn",
        "html_lang": "zh-Hans",
        "alternate_hreflang": "zh-Hant",
        "brand": "决策之书",
        "nav_sub": "易经 × 职场决策",
        "switch_label": "繁體中文",
        "switch_lang": "tc",
        "author_line": "凯森读易",
        "cta_h": "你的处境，换一双眼睛看看？",
        "cta_p": "输入你正在纠结的职场难题，起一卦，让易经给你一个不同的视角。",
        "cta_btn": "开始起卦 →",
        "footer_about": "决策之书——把易经做成一枚陪你算账、也陪你下决定的镜子。卦不是算盘，不预测吉凶，只把你自己的处境翻给你看。",
        "footer_disclaimer": "本文仅供决策思考参考，不构成任何投资、法律或职业建议。",
        "index_title": "职场决策笔记",
        "index_sub": "易经 × 职场 —— 把真实的难题，想清楚",
        "related_label": "延伸阅读",
    },
}

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

def inline_md(s, prefix=""):
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    def fix_link(m):
        text, href = m.group(1), m.group(2)
        # 站内绝对链接加语言前缀（外链/已有前缀/锚点不动）
        if prefix and href.startswith("/") and not href.startswith("//") and not href.startswith(prefix + "/") and href != prefix:
            href = prefix + href
        return f'<a href="{href}">{text}</a>'
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", fix_link, s)
    return s

def md_to_html(body, prefix=""):
    html, para, in_ul = [], [], False
    def flush_para():
        if para:
            html.append("<p>" + inline_md(" ".join(para), prefix) + "</p>")
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
            flush_para(); close_ul(); html.append("<h3>" + inline_md(line[4:], prefix) + "</h3>")
        elif line.startswith("## "):
            flush_para(); close_ul(); html.append("<h2>" + inline_md(line[3:], prefix) + "</h2>")
        elif line.startswith("# "):
            flush_para(); close_ul(); html.append("<h2>" + inline_md(line[2:], prefix) + "</h2>")
        elif line.startswith("- "):
            flush_para()
            if not in_ul:
                html.append("<ul>"); in_ul = True
            html.append("<li>" + inline_md(line[2:], prefix) + "</li>")
        else:
            close_ul(); para.append(line)
    flush_para(); close_ul()
    return "\n".join(html)

# ---------- 页面模板 ----------

CSS = """
:root{--ink:#1a1a1a;--sub:#666;--line:#e5e5e5;--bg:#fafaf8;--accent:#8a6d3b}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,"PingFang TC","PingFang SC","Noto Sans TC","Noto Sans SC",sans-serif;background:var(--bg);color:var(--ink);line-height:1.9;font-size:16px}
.wrap{max-width:680px;margin:0 auto;padding:48px 22px 80px}
.nav{display:flex;justify-content:space-between;align-items:center;padding-bottom:18px;border-bottom:1px solid var(--line);margin-bottom:36px}
.nav a{color:var(--ink);text-decoration:none;font-weight:700;letter-spacing:.12em}
.nav .sub{color:var(--sub);font-size:12px;letter-spacing:.2em}
.nav .lang-switch{font-weight:400;font-size:12.5px;color:var(--sub);letter-spacing:0;border:1px solid var(--line);border-radius:6px;padding:3px 10px;margin-left:12px}
.nav .lang-switch:hover{color:var(--accent);border-color:var(--accent)}
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

def page_shell(lang, title, desc, slug, body_html, meta_extra=None, related_html=""):
    cfg = LANGS[lang]
    meta_extra = meta_extra or {}
    prefix = cfg["prefix"]
    path = f"blog/{slug}/" if slug else "blog/"
    canonical = f"{BASE_URL}{prefix}/{path}"
    alt_lang = cfg["switch_lang"]
    alt_path = f"{LANGS[alt_lang]['prefix']}/{path}"
    alt_url = f"{BASE_URL}{alt_path}"
    ld = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": title, "description": desc,
        "author": {"@type": "Person", "name": cfg["author_line"]},
        "publisher": {"@type": "Organization", "name": cfg["brand"]},
        "mainEntityOfPage": canonical,
    }
    if meta_extra.get("date"):
        ld["datePublished"] = meta_extra["date"]
    ld_json = json.dumps(ld, ensure_ascii=False)
    xdefault = f"{BASE_URL}/blog/{slug}/" if slug else f"{BASE_URL}/blog/"
    return f"""<!DOCTYPE html>
<html lang="{cfg['html_lang']}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}｜{cfg['brand']}</title>
<meta name="description" content="{desc}">
<meta name="keywords" content="{meta_extra.get('keywords', '')}">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="{cfg['html_lang']}" href="{canonical}">
<link rel="alternate" hreflang="{cfg['alternate_hreflang']}" href="{alt_url}">
<link rel="alternate" hreflang="x-default" href="{xdefault}">
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
  <a href="{BASE_URL}{prefix}/">{cfg['brand']}</a>
  <span class="sub">{cfg['nav_sub']}</span>
  <a class="lang-switch" href="{alt_url}">{cfg['switch_label']}</a>
</div>
{body_html}
{related_html}
<footer>
  <p><strong>{'關於本站' if lang == 'tc' else '关于本站'}</strong>：{cfg['footer_about']}</p>
  <p style="margin-top:8px">{cfg['footer_disclaimer']}</p>
</footer>
</div>
</body>
</html>"""

# ---------- 主流程 ----------

def main():
    # 读取两语言的文章
    all_posts = {}   # lang -> [ {meta, body} ]
    slugs_by_lang = {}   # lang -> {slug: title}
    for lang, cfg in LANGS.items():
        posts = []
        for f in sorted(cfg["src"].glob("*.md")):
            meta, body = parse_md(f)
            posts.append({"meta": meta, "body": body})
        posts.sort(key=lambda p: p["meta"].get("date", ""), reverse=True)
        all_posts[lang] = posts
        slugs_by_lang[lang] = {p["meta"]["slug"]: p["meta"]["title"] for p in posts}
        print(f"[{lang}] 读取 {len(posts)} 篇（{cfg['src'].name}/）")

    for lang, cfg in LANGS.items():
        posts = all_posts[lang]
        prefix = cfg["prefix"]
        slugs = slugs_by_lang[lang]

        # 1. 文章页
        for p in posts:
            m, body = p["meta"], p["body"]
            content = md_to_html(body, prefix)
            cta = f"""<div class="cta">
<p>{cfg['cta_h']}</p>
<p style="margin-bottom:16px">{cfg['cta_p']}</p>
<a class="btn" href="{BASE_URL}{prefix}/">{cfg['cta_btn']}</a>
</div>"""
            rel = []
            for rslug in [s.strip() for s in m.get("related", "").split(",") if s.strip()]:
                if rslug in slugs:
                    rel.append(f'<a href="{prefix}/blog/{rslug}/">→ {slugs[rslug]}</a>')
            related = ""
            if rel:
                related = f'<div class="related"><h3>{cfg["related_label"]}</h3>' + "\n".join(rel) + "</div>"
            body_html = f'<h1>{m["title"]}</h1>\n<p class="meta">{m.get("date","")} · {cfg["author_line"]}</p>\n{content}\n{cta}'
            html = page_shell(lang, m["title"], m.get("description", ""), m["slug"], body_html, m, related)
            out = cfg["out"] / m["slug"] / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(html, encoding="utf-8")
            print(f"  ✓ {prefix}/blog/{m['slug']}/")

        # 2. 索引页
        items = []
        for p in posts:
            m = p["meta"]
            items.append(
                f'<a class="list-item" href="{prefix}/blog/{m["slug"]}/">'
                f'<div class="t">{m["title"]}</div>'
                f'<div class="d">{m.get("description","")[:80]}</div></a>'
            )
        desc = "易經 × 職場決策的內容站：離職、轉職、迷茫、被裁員——用真實的判斷方法，陪你把難題想清楚。" if lang == "tc" else "易经 × 职场决策的内容站：离职、跳槽、迷茫、被裁员——用真实的判断方法，陪你把难题想清楚。"
        idx_body = f'<h1>{cfg["index_title"]}</h1><p class="meta">{cfg["index_sub"]}</p>' + "\n".join(items)
        idx_html = page_shell(lang, cfg["index_title"], desc, "", idx_body)
        out = cfg["out"] / "index.html"
        out.write_text(idx_html, encoding="utf-8")
        print(f"  ✓ {prefix}/blog/（索引页）")

    # 3. sitemap 增量（清理旧 blog 条目再追加；正则同时匹配 /blog/ 与 /cn/blog/）
    sm_path = PUBLIC / "sitemap.xml"
    if sm_path.exists():
        sm = sm_path.read_text(encoding="utf-8")
        sm = re.sub(r"\n?\s*<url>\s*<loc>[^<]*/blog/[^<]*</loc>\s*<changefreq>[^<]*</changefreq>\s*</url>", "", sm)
        today = datetime.date.today().isoformat()
        urls = []
        for lang, cfg in LANGS.items():
            prefix = cfg["prefix"]
            urls.append(f"{BASE_URL}{prefix}/blog/")
            urls += [f"{BASE_URL}{prefix}/blog/{p['meta']['slug']}/" for p in all_posts[lang]]
        block = "\n".join(
            f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>weekly</changefreq>\n  </url>"
            for u in urls
        )
        sm = sm.replace("</urlset>", block + "\n</urlset>")
        sm_path.write_text(sm, encoding="utf-8")
        print(f"  ✓ sitemap.xml 已更新（+{len(urls)} 条 blog URL·两语言）")
    else:
        print("  ⚠️ sitemap.xml 不存在，跳过（先跑 generate_hexagram_pages.py）")


if __name__ == "__main__":
    main()
