#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""站点共享组件（单一数据源）· 2026-10-10 建

背景：footer 曾散落 5 处定义（hex 页面模板 / hex 索引模板 / blog page_shell /
static footer_html / App.jsx），每次改动需同步多遍且已出现文案漂移。
现在：数据=src/data/site_components.json（footer + 导航；SPA 同读一份）；渲染器=本模块（Python）+ App.jsx（SPA）。

用法：
    from site_components import footer_html
    footer_html(lang, row2="default", trailer=None)
      - lang: "tc" / "sc"
      - row2: "default" | "hexpage" | "hexindex"（surface 变体，数据在 JSON）
      - trailer: None=品牌行；字符串=自定义尾行 HTML（如 blog 的免责声明段）
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
_DATA = json.loads((ROOT / "src" / "data" / "site_components.json").read_text(encoding="utf-8"))

# sitemap lastmod：真实内容变更日（不是构建日，避免每次部署制造假新鲜度）
SITE_URL = _DATA["site_url"].rstrip("/")
SITE_LASTMOD = _DATA.get("content_dates", {}).get("site", "")
HEX_LASTMOD = _DATA.get("content_dates", {}).get("hexagrams", SITE_LASTMOD)

# 全站 head 资源（单一数据源）：favicon 套装 / manifest / theme-color
HEAD_TAGS = _DATA["head_tags"]

# 社交分享图（绝对 URL，供 og / twitter 使用）
_OG = _DATA["og_image"]
OG_IMAGE_TAGS = (
    f'<meta property="og:image" content="{SITE_URL}{_OG["path"]}">\n'
    f'<meta property="og:image:width" content="{_OG["width"]}">\n'
    f'<meta property="og:image:height" content="{_OG["height"]}">\n'
    '<meta property="og:image:alt" content="決策之書 · 易經商業決策">\n'
    '<meta name="twitter:card" content="summary_large_image">\n'
    f'<meta name="twitter:image" content="{SITE_URL}{_OG["path"]}">'
)


def _href(item, lang):
    href = item["href"]
    if lang == "sc" and href != "/":
        return "/cn" + href
    if lang == "sc":
        return "/cn/"
    return href


def _label(item, lang):
    return item[lang]


def footer_row(items, lang):
    return " · ".join(f'<a href="{_href(it, lang)}">{_label(it, lang)}</a>' for it in items)


def nav_html(lang, active=None, switch_href=None):
    """三栏目常驻导航：提問｜易經｜筆記 + 语言切换
    active: None | "ask" | "hex" | "blog"；switch_href: 目标语言同页 URL（各页传入）"""
    p = "" if lang == "tc" else "/cn"
    brand = (
        f'    <a class="nav-brand" href="{p}/" aria-label="決策之書" '
        'style="position:absolute;left:clamp(16px,4vw,24px);top:50%;transform:translateY(-50%);line-height:0;display:flex">'
        '<img src="/mark.svg" alt="" width="22" height="22"></a>'
    )
    rows = [brand]
    for it in _DATA["nav"]["items"]:
        cls = "nav-item active" if active == it["id"] else "nav-item"
        rows.append(f'    <a class="{cls}" href="{p + it["href"]}">{it[lang]}</a>')
    target = "sc" if lang == "tc" else "tc"
    hl = "zh-Hans" if target == "sc" else "zh-Hant"
    rows.append(f'    <a class="lang-switch" href="{switch_href}" hreflang="{hl}" rel="alternate">{_DATA["nav"]["switch_names"][target]}</a>')
    return '<nav class="site-nav">\n  <div class="site-nav-inner">\n' + "\n".join(rows) + '\n  </div>\n</nav>'


def footer_html(lang, row2="default", trailer=None):
    rows = [
        f'<div class="f-links">{footer_row(_DATA["row1"], lang)}</div>',
        f'<div class="f-links">{footer_row(_DATA["row2"][row2], lang)}</div>',
    ]
    if trailer is None:
        rows.append(f'<div class="f-brand">{_DATA["brand"][lang]}</div>')
    elif trailer == "blog":
        rows.append(f'<p style="margin-top:10px">{_DATA["blog_disclaimer"][lang]}</p>')
    else:
        rows.append(trailer)
    return "<footer>\n" + "\n".join("  " + r for r in rows) + "\n</footer>"
