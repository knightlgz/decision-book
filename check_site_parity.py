#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""站点组件全量一致性校验（单一数据源闸门）· 2026-10-10 建（同日扩 footer+nav）

覆盖：全站 footer + 三栏目导航 + 语言切换链接。
原理：独立复算——从 src/data/site_components.json 自行构建每个页面的期望
footer/nav，与 public/ 下全部 HTML 逐字节比对；另做：
  - switch 链接可达性校验（必须站内绝对路径，且对方语言页面真实存在）
  - SPA 侧轻校验（App.jsx 必须引用 site_components.json）

用法：python3 check_site_parity.py   （改数据源或重生成后必跑）
退出码：0=全过；1=有差异（列出全部不一致文件）
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
PUBLIC = ROOT / "public"
D = json.loads((ROOT / "src" / "data" / "site_components.json").read_text(encoding="utf-8"))


def build_footer(lang, row2, trailer):
    p = "" if lang == "tc" else "/cn"

    def row(items):
        return " · ".join(f'<a href="{p + it["href"]}">{it[lang]}</a>' for it in items)

    lines = [
        f'  <div class="f-links">{row(D["row1"])}</div>',
        f'  <div class="f-links">{row(D["row2"][row2])}</div>',
    ]
    if trailer == "blog":
        lines.append(f'  <p style="margin-top:10px">{D["blog_disclaimer"][lang]}</p>')
    else:
        lines.append(f'  <div class="f-brand">{D["brand"][lang]}</div>')
    return "<footer>\n" + "\n".join(lines) + "\n</footer>"


def build_nav(lang, active, switch_href):
    p = "" if lang == "tc" else "/cn"
    rows = []
    for it in D["nav"]["items"]:
        cls = "nav-item active" if active == it["id"] else "nav-item"
        rows.append(f'    <a class="{cls}" href="{p + it["href"]}">{it[lang]}</a>')
    target = "sc" if lang == "tc" else "tc"
    hl = "zh-Hans" if target == "sc" else "zh-Hant"
    rows.append(f'    <a class="lang-switch" href="{switch_href}" hreflang="{hl}" rel="alternate">{D["nav"]["switch_names"][target]}</a>')
    return '<nav class="site-nav">\n  <div class="site-nav-inner">\n' + "\n".join(rows) + "\n  </div>\n</nav>"


def classify(rel):
    """(lang, row2_variant, trailer, nav_active) 或 None"""
    sc = rel.startswith("cn/")
    lang = "sc" if sc else "tc"
    rest = rel[3:] if sc else rel
    if rest.startswith("hexagram/"):
        inner = rest[len("hexagram/"):]
        return (lang, "hexindex" if inner == "index.html" else "hexpage", None, "hex")
    if rest.startswith("blog/"):
        return (lang, "default", "blog", "blog")
    if rest.split("/")[0] in ("about", "privacy", "disclaimer"):
        return (lang, "default", None, None)
    return None


def switch_counterpart(rel):
    """相对路径 → 对方语言同页相对路径（存在性校验用）"""
    sc = rel.startswith("cn/")
    rest = rel[3:] if sc else rel
    return rest if sc else "cn/" + rest


def switch_href_of(rel):
    """相对路径 → 语言切换 href（对方语言同页 URL）"""
    sc = rel.startswith("cn/")
    rest = rel[3:] if sc else rel
    dir_ = rest[: -len("index.html")]
    return ("/" if sc else "/cn/") + dir_


def main():
    fails, counts = [], {}
    for f in sorted(PUBLIC.rglob("*.html")):
        rel = f.relative_to(PUBLIC).as_posix()
        cat = classify(rel)
        if cat is None:
            fails.append((rel, "未分类（新页面？请更新 classify()）"))
            continue
        lang, row2, trailer, active = cat
        text = f.read_text(encoding="utf-8")
        m = re.search(r"<footer>[\s\S]*?</footer>", text)
        if not m:
            fails.append((rel, "页面缺 footer"))
        elif m.group(0) != build_footer(lang, row2, trailer):
            fails.append((rel, "footer 与数据源不一致"))
        n = re.search(r'<nav class="site-nav">[\s\S]*?</nav>', text)
        if not n:
            fails.append((rel, "页面缺 site-nav"))
        else:
            if n.group(0) != build_nav(lang, active, switch_href_of(rel)):
                fails.append((rel, "nav 与数据源不一致"))
            got = re.search(r'class="lang-switch" href="([^"]+)"', n.group(0))
            if not got or not got.group(1).startswith("/"):
                fails.append((rel, "switch 链接非站内绝对路径"))
            elif not (PUBLIC / switch_counterpart(rel)).exists():
                fails.append((rel, "switch 指向的对方语言页面不存在"))
        key = f"{lang}/{row2}{'/' + trailer if trailer else ''}"
        counts[key] = counts.get(key, 0) + 1

    app = (ROOT / "src" / "App.jsx").read_text(encoding="utf-8")
    if "site_components.json" not in app:
        fails.append(("src/App.jsx", "未引用 site_components.json（SPA 脱离数据源）"))

    print("分类统计:")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]} 页")
    if fails:
        print(f"\n✗ {len(fails)} 处不一致:")
        for rel, why in fails:
            print(f"  {rel}: {why}")
        sys.exit(1)
    total = sum(counts.values())
    print(f"\n✓ 全部 {total} 个页面 footer+nav 与数据源一致；switch 全部站内可达；SPA 引用正常。")


if __name__ == "__main__":
    main()
