#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML 站点地图（繁简双语）· 2026-11-23 建

目的：给爬虫一个静态、可点、全量的内链入口（首页是 SPA，原始 HTML 无链接）。
输出：public/sitemap/index.html + public/cn/sitemap/index.html
"""
import re
from pathlib import Path

import site_components
from generate_hexagram_pages import parse_hexagrams
from generate_static_pages import CSS, GA_SNIPPET

ROOT = Path(__file__).parent
PUBLIC = ROOT / "public"
BASE_URL = site_components.SITE_URL

STATIC_PAGES = [
    ("/about/", "關於本站", "关于本站"),
    ("/contact/", "聯繫我們", "联系我们"),
    ("/privacy/", "隱私聲明", "隐私声明"),
    ("/disclaimer/", "免責聲明", "免责声明"),
]


def parse_posts(folder):
    posts = []
    for path in sorted((ROOT / folder).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        m = re.match(r"^---\n([\s\S]*?)\n---\n", text)
        if not m:
            continue
        meta = {}
        for line in m.group(1).split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        if meta.get("slug") and meta.get("title"):
            posts.append(meta)
    return sorted(posts, key=lambda x: (x.get("date", ""), x.get("title", "")), reverse=True)


def build_page(lang):
    tc = lang == "tc"
    prefix = "" if tc else "/cn"
    title = "網站地圖" if tc else "网站地图"
    meta = "全部易經卦象與決策筆記" if tc else "全部易经卦象与决策笔记"
    desc = ("決策之書全站目錄：六十四卦、決策筆記、關於本站與聯絡方式。"
            if tc else "决策之书全站目录：六十四卦、决策笔记、关于本站与联系方式。")
    canonical = f"{BASE_URL}{prefix}/sitemap/"
    alt_url = f"{BASE_URL}/sitemap/" if not tc else f"{BASE_URL}/cn/sitemap/"
    html_lang = "zh-Hant" if tc else "zh-Hans"
    brand = "決策之書" if tc else "决策之书"
    switch = "/cn/sitemap/" if tc else "/sitemap/"

    hexagrams = parse_hexagrams()
    posts = parse_posts("blog_src" if tc else "blog_src_cn")

    def hex_li(h):
        n = h["number"]
        name = h["tc"]["name"] if tc else h["sc"]["name"]
        return f'<li><a href="{prefix}/hexagram/{n}/">第 {int(n)} 卦 · {name}</a></li>'

    def post_li(p):
        return f'<li><a href="{prefix}/blog/{p["slug"]}/">{p["title"]}</a> <span class="muted">{p.get("date", "")}</span></li>'

    static_li = "\n".join(
        f'<li><a href="{prefix}{href}">{label_tc if tc else label_sc}</a></li>'
        for href, label_tc, label_sc in STATIC_PAGES
    )
    hex_links = "\n".join(hex_li(h) for h in hexagrams)
    post_links = "\n".join(post_li(p) for p in posts)

    body = f"""
<h1>{title}</h1>
<p class="meta">{meta}</p>
<article>
<p>共 {len(hexagrams)} 卦 × 2 語言、{len(posts)} 篇決策筆記，全部集中在這一頁；每一條都可以直接點進去。</p>

<h2>易經六十四卦</h2>
<ul>
{hex_links}
</ul>

<h2>決策筆記</h2>
<ul>
{post_links}
</ul>

<h2>關於本站</h2>
<ul>
{static_li}
</ul>

<h2>語言</h2>
<p><a href="{switch}">{"简体中文版" if tc else "繁體中文版"}</a></p>
</article>
"""

    return f"""<!DOCTYPE html>
<html lang="{html_lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{site_components.HEAD_TAGS}
<title>{title}｜{brand}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="{html_lang}" href="{canonical}">
<link rel="alternate" hreflang="{'zh-Hans' if tc else 'zh-Hant'}" href="{alt_url}">
<link rel="alternate" hreflang="x-default" href="{BASE_URL}/sitemap/">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}｜{brand}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{brand}">
{site_components.OG_IMAGE_TAGS}
<style>{CSS}</style>
{GA_SNIPPET}
</head>
<body>
{site_components.nav_html(lang, None, switch)}
<div class="wrap">
{body}
{site_components.footer_html(lang, "default")}
</div>
</body>
</html>"""


def main():
    for lang in ("tc", "sc"):
        out = PUBLIC / ("cn" if lang == "sc" else "") / "sitemap"
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(build_page(lang), encoding="utf-8")
        print(f"  ✓ {'/cn' if lang == 'sc' else ''}/sitemap/")
    print("完成 2 页。")


if __name__ == "__main__":
    main()
