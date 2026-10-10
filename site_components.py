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
    rows = []
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
