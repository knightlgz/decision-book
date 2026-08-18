#!/usr/bin/env python3
"""
生成 64 卦象 SEO 落地页 + 索引页 + sitemap
用法：python3 generate_hexagram_pages.py
输出：public/hexagram/XX/index.html (64页) + public/hexagram/index.html + public/sitemap.xml
"""
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "src" / "data" / "hexagrams.js"
OUT_DIR = ROOT / "public" / "hexagram"
SITEMAP = ROOT / "public" / "sitemap.xml"
BASE_URL = "https://decision-book.vercel.app"


def parse_hexagrams():
    """用 Node.js 解析 ES module，输出 JSON"""
    import subprocess, tempfile
    # 写一个临时 mjs 脚本来 require 数据
    tmp_js = Path(tempfile.gettempdir()) / "dump_hexagrams.mjs"
    tmp_js.write_text("""
import HEXAGRAMS from '%s';
console.log(JSON.stringify(HEXAGRAMS));
""" % DATA_FILE.as_posix(), encoding="utf-8")
    result = subprocess.run(["node", tmp_js.as_posix()], capture_output=True, text=True, cwd=ROOT)
    if result.returncode != 0:
        print("Node 解析失败:", result.stderr[:300])
        return []
    data = json.loads(result.stdout)
    return [{
        "number": d["number"],
        "sc_name": d["sc"]["name"], "sc_insight": d["sc"]["insight"],
        "tc_name": d["tc"]["name"], "tc_insight": d["tc"]["insight"],
    } for d in data]


def page_html(hx, prev_num, next_num):
    """单个卦象页 HTML（繁体为主，lang=zh-Hant）"""
    n = hx["number"]
    name = hx["tc_name"]
    insight = hx["tc_insight"]
    title = f"{name}卦｜第{n}卦｜曾仕強易經商業決策解讀"
    desc = f"易經第{n}卦{name}：{insight}。基於曾仕強教授易經思想體系，用 AI 為你推演職場與商業抉擇。"

    prev_link = f'<a href="/hexagram/{prev_num}/" class="nav-link">← 上一卦</a>' if prev_num else '<span class="nav-link muted">首卦</span>'
    next_link = f'<a href="/hexagram/{next_num}/" class="nav-link">下一卦 →</a>' if next_num else '<span class="nav-link muted">末卦</span>'

    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": desc,
        "author": {"@type": "Organization", "name": "決策之書"},
        "publisher": {"@type": "Organization", "name": "決策之書"},
        "mainEntityOfPage": f"{BASE_URL}/hexagram/{n}/",
        "inLanguage": "zh-Hant"
    }, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{BASE_URL}/hexagram/{n}/">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{BASE_URL}/hexagram/{n}/">
<meta property="og:site_name" content="決策之書">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<script type="application/ld+json">{jsonld}</script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#0f1115; color:#e8e6e0; font-family:"PingFang TC","Noto Sans TC","Microsoft JhengHei",sans-serif; line-height:1.8; min-height:100vh; display:flex; flex-direction:column; }}
  .container {{ max-width:720px; margin:0 auto; padding:48px 24px; flex:1; }}
  .breadcrumb {{ font-size:14px; color:#8b8f98; margin-bottom:32px; }}
  .breadcrumb a {{ color:#c8a96a; text-decoration:none; }}
  .hexagram-badge {{ display:inline-block; background:#1c2030; border:1px solid #c8a96a33; color:#c8a96a; padding:4px 16px; border-radius:20px; font-size:14px; letter-spacing:2px; margin-bottom:16px; }}
  h1 {{ font-size:36px; margin-bottom:8px; color:#f5f2ea; }}
  .subtitle {{ color:#8b8f98; font-size:15px; margin-bottom:40px; }}
  .insight {{ background:#171a22; border-left:3px solid #c8a96a; padding:24px; border-radius:0 8px 8px 0; font-size:18px; color:#dcd8cf; margin-bottom:48px; }}
  .insight-label {{ color:#c8a96a; font-size:13px; letter-spacing:3px; margin-bottom:12px; display:block; }}
  .cta {{ text-align:center; background:linear-gradient(135deg,#1c2030,#151823); border:1px solid #c8a96a44; border-radius:12px; padding:32px 24px; margin-bottom:48px; }}
  .cta h2 {{ font-size:22px; margin-bottom:12px; color:#f5f2ea; }}
  .cta p {{ color:#a8a5a0; font-size:15px; margin-bottom:20px; }}
  .cta a.btn {{ display:inline-block; background:#c8a96a; color:#0f1115; text-decoration:none; padding:12px 32px; border-radius:24px; font-weight:700; font-size:16px; }}
  .cta a.btn:hover {{ background:#d9ba7a; }}
  .nav {{ display:flex; justify-content:space-between; padding:16px 0; border-top:1px solid #2a2e3a; font-size:15px; }}
  .nav a {{ color:#c8a96a; text-decoration:none; }}
  .muted {{ color:#4a4e58; }}
  .related {{ margin-top:48px; }}
  .related h3 {{ font-size:16px; color:#8b8f98; letter-spacing:2px; margin-bottom:16px; }}
  .related-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(140px,1fr)); gap:8px; }}
  .related-grid a {{ color:#dcd8cf; text-decoration:none; background:#171a22; padding:8px 12px; border-radius:6px; font-size:14px; text-align:center; }}
  .related-grid a:hover {{ border-color:#c8a96a; color:#c8a96a; }}
  footer {{ text-align:center; padding:24px; color:#5a5e68; font-size:13px; }}
  footer a {{ color:#8b8f98; }}
</style>
</head>
<body>
<div class="container">
  <div class="breadcrumb"><a href="/">決策之書</a> / <a href="/hexagram/">六十四卦</a> / {name}</div>
  <span class="hexagram-badge">第 {int(n)} 卦</span>
  <h1>{name}</h1>
  <p class="subtitle">曾仕強易經思想體系 · 商業與職場解讀</p>

  <div class="insight">
    <span class="insight-label">核心解讀</span>
    {insight}
  </div>

  <div class="cta">
    <h2>你正在面對類似的職場或商業抉擇嗎？</h2>
    <p>輸入你的具體困惑，讓 AI 以曾仕強教授的易經智慧，為你推演專屬的決策報告。</p>
    <a class="btn" href="/">開始免費推演 →</a>
  </div>

  <div class="nav">
    {prev_link}
    <a href="/hexagram/" class="nav-link">全部六十四卦</a>
    {next_link}
  </div>
</div>
<footer>
  <a href="/hexagram/">六十四卦索引</a> · <a href="/">決策之書</a> · 曾仕強教授易經思想體系
</footer>
</body>
</html>"""


def index_html(hexagrams):
    """六十四卦索引页"""
    items = "\n".join(
        f'<a href="/hexagram/{h["number"]}/">{int(h["number"])}. {h["tc_name"]}</a>'
        for h in hexagrams
    )
    title = "易經六十四卦｜曾仕強商業決策解讀全索引"
    desc = "易經六十四卦完整索引：每卦的商業與職場核心解讀，基於曾仕強教授易經思想體系。免費查看卦象智慧，AI 推演你的決策。"
    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "description": desc,
        "url": f"{BASE_URL}/hexagram/",
        "inLanguage": "zh-Hant"
    }, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{BASE_URL}/hexagram/">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{BASE_URL}/hexagram/">
<script type="application/ld+json">{jsonld}</script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#0f1115; color:#e8e6e0; font-family:"PingFang TC","Noto Sans TC","Microsoft JhengHei",sans-serif; line-height:1.8; }}
  .container {{ max-width:900px; margin:0 auto; padding:48px 24px; }}
  .breadcrumb {{ font-size:14px; color:#8b8f98; margin-bottom:32px; }}
  .breadcrumb a {{ color:#c8a96a; text-decoration:none; }}
  h1 {{ font-size:32px; margin-bottom:8px; color:#f5f2ea; }}
  .subtitle {{ color:#8b8f98; font-size:15px; margin-bottom:40px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:12px; }}
  .grid a {{ display:block; background:#171a22; border:1px solid #2a2e3a; color:#dcd8cf; text-decoration:none; padding:16px; border-radius:10px; font-size:15px; transition:border-color .2s; }}
  .grid a:hover {{ border-color:#c8a96a; color:#c8a96a; }}
  .grid a .num {{ display:block; font-size:12px; color:#8b8f98; letter-spacing:2px; margin-bottom:4px; }}
  footer {{ text-align:center; padding:24px; color:#5a5e68; font-size:13px; }}
  footer a {{ color:#8b8f98; }}
</style>
</head>
<body>
<div class="container">
  <div class="breadcrumb"><a href="/">決策之書</a> / 六十四卦</div>
  <h1>易經六十四卦</h1>
  <p class="subtitle">曾仕強教授易經思想體系 · 商業與職場雙語境解讀</p>
  <div class="grid">
{items}
  </div>
</div>
<footer>
  <a href="/">回到決策之書</a> · 曾仕強教授易經思想體系
</footer>
</body>
</html>"""


def build_sitemap(hexagrams):
    urls = [f"{BASE_URL}/", f"{BASE_URL}/hexagram/"]
    for h in hexagrams:
        urls.append(f"{BASE_URL}/hexagram/{h['number']}/")
    body = "\n".join(
        f"  <url>\n    <loc>{u}</loc>\n    <changefreq>weekly</changefreq>\n    <priority>{'1.0' if u.endswith('/') and u.count('/')==3 else '0.7'}</priority>\n  </url>"
        for u in urls
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>"""


def main():
    hexagrams = parse_hexagrams()
    print(f"解析到 {len(hexagrams)} 个卦象")
    if len(hexagrams) != 64:
        print("⚠️ 数量不对，检查解析逻辑")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for i, hx in enumerate(hexagrams):
        n = hx["number"]
        prev_num = hexagrams[i - 1]["number"] if i > 0 else None
        next_num = hexagrams[i + 1]["number"] if i < 63 else None
        page_dir = OUT_DIR / n
        page_dir.mkdir(exist_ok=True)
        (page_dir / "index.html").write_text(page_html(hx, prev_num, next_num), encoding="utf-8")
        print(f"  ✓ /hexagram/{n}/ {hx['tc_name']}")

    (OUT_DIR / "index.html").write_text(index_html(hexagrams), encoding="utf-8")
    print("  ✓ /hexagram/ 索引页")

    SITEMAP.write_text(build_sitemap(hexagrams), encoding="utf-8")
    print("  ✓ sitemap.xml 已更新（66 个 URL）")
    print("\n完成！提交 git 后 Vercel 自动部署。")


if __name__ == "__main__":
    main()
