#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""footer 全量一致性校验（单一数据源闸门）· 2026-10-10 建

原理：独立复算（不 import site_components，避免同源 bug）——
从 src/data/site_footer.json 自行构建每个页面的期望 footer，与 public/ 下
全部 HTML 的实际 footer 逐字节比对；另做 SPA 侧轻校验（App.jsx 必须引用 JSON）。

用法：python3 check_footer_parity.py   （每次改 site_footer.json 或重生成后必跑）
退出码：0=全过；1=有差异（列出全部不一致文件）
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
PUBLIC = ROOT / "public"
D = json.loads((ROOT / "src" / "data" / "site_footer.json").read_text(encoding="utf-8"))


def build(lang, row2, trailer):
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


def classify(rel: str):
    """返回 (lang, row2_variant, trailer) 或 None"""
    sc = rel.startswith("cn/")
    lang = "sc" if sc else "tc"
    rest = rel[3:] if sc else rel
    if rest.startswith("hexagram/"):
        inner = rest[len("hexagram/"):]
        return (lang, "hexindex" if inner == "index.html" else "hexpage", None)
    if rest.startswith("blog/"):
        return (lang, "default", "blog")
    if rest.split("/")[0] in ("about", "privacy", "disclaimer"):
        return (lang, "default", None)
    return None


def main():
    fails, counts = [], {}
    for f in sorted(PUBLIC.rglob("*.html")):
        rel = f.relative_to(PUBLIC).as_posix()
        cat = classify(rel)
        if cat is None:
            fails.append((rel, "未分类（新页面？请更新 classify()）"))
            continue
        lang, row2, trailer = cat
        m = re.search(r"<footer>[\s\S]*?</footer>", f.read_text(encoding="utf-8"))
        if not m:
            fails.append((rel, "页面缺 footer"))
            continue
        if m.group(0) != build(lang, row2, trailer):
            fails.append((rel, "footer 与 site_footer.json 不一致"))
        key = f"{lang}/{row2}{'/' + trailer if trailer else ''}"
        counts[key] = counts.get(key, 0) + 1

    # SPA 侧轻校验
    app = (ROOT / "src" / "App.jsx").read_text(encoding="utf-8")
    if "site_footer.json" not in app:
        fails.append(("src/App.jsx", "未引用 site_footer.json（SPA 脱离数据源）"))

    print("分类统计:")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]} 页")
    if fails:
        print(f"\n✗ {len(fails)} 处不一致:")
        for rel, why in fails:
            print(f"  {rel}: {why}")
        sys.exit(1)
    total = sum(counts.values())
    print(f"\n✓ 全部 {total} 个页面 footer 与数据源一致；SPA 引用正常。")


if __name__ == "__main__":
    main()
