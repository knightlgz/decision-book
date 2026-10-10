#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""静态页生成器：關於本站 / 隱私聲明 / 免責聲明（繁简双语）· 2026-10-08
- 复用 blog 生成器的 md_to_html（支持 ##/-/*bold*/链接）
- 三栏目常驻导航（无高亮）+ 统一 footer（关于/隐私/免责 + 栏目 + 品牌）
- 输出：public/{about,privacy,disclaimer}/index.html + public/cn/...
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate_blog_pages import md_to_html          # noqa: E402
from generate_hexagram_pages import GA_SNIPPET      # noqa: E402
import site_components

ROOT = Path(__file__).parent
PUBLIC = ROOT / "public"
BASE_URL = "https://decision-book.vercel.app"
IG_URL = "https://www.instagram.com/kysonsdecisionbook/"

# ============================================================
# 页面内容（草稿级；改动只需改这里）
# ============================================================
PAGES = {
    "about": {
        "tc": {
            "title": "關於本站",
            "meta": "把易經，用回它本來的樣子",
            "desc": "決策之書是什麼？為什麼做這個站、怎麼用它、我們的立場與聯繫方式，一次說清楚。",
            "body": """## 為什麼會有這個站

在職場混跡十幾年，見識過好老闆、壞老闆、好同事、惡同事。被辭過職，也做過艱難的選擇，和一些夥伴分別。做成過一些成果，更被坑入過谷底。

五六年前，曾仕強教授的易經內容把我從一段難熬的日子裡拉了出來。他早已作古，我學的，是他留下的東西。讓我看清的，不是命，是人心與選擇：職場困局、生意難題，繞來繞去，都在這裡。

遺憾的是，他分析問題、解決問題的這套方法，還沒來得及傳給更多人。我是一個普通的學習者，做了一件笨功夫：借助 AI，把他的方法整理出來，做成一個你隨時能問、隨時能用的工具。我把自己當作曾師的AI學徒，學到的，還給需要的人。

## 這個站怎麼用

- 把眼下最糾結的那件事寫下來，起一卦；
- 你會拿到一份五段報告：核心洞察、現狀刺透、避坑指南、破局行動、未來演進；
- 重點從來不是卦，是你。卦是鏡子，不是算盤，它照見的，是你心裡早就知道的答案。

## 我們的立場

- 不預測吉凶，不承諾成敗；
- 不替代任何專業意見。投資、法律、醫療這類重大決定，請找對口的專業人士；
- 免費使用，不需註冊。

## 聯繫我們

使用上的問題、建議，或想刪除你的使用資料，歡迎 IG 私訊：[@kysonsdecisionbook](%s)

凱森""" % IG_URL,
        },
        "sc": {
            "title": "关于本站",
            "meta": "把易经，用回它本来的样子",
            "desc": "决策之书是什么？为什么做这个站、怎么用它、我们的立场与联系方式，一次说清楚。",
            "body": """## 为什么会有这个站

在职场混迹十几年，见识过好老板、坏老板、好同事、恶同事。被辞过职，也做过艰难的选择，和一些伙伴分别。做成过一些成果，更被坑入过谷底。

五六年前，曾仕强教授的易经内容把我从一段难熬的日子里拉了出来。他早已作古，我学的，是他留下的东西。让我看清的，不是命，是人心与选择：职场困局、生意难题，绕来绕去，都在这里。

遗憾的是，他分析问题、解决问题的这套方法，还没来得及传给更多人。我是一个普通的学习者，做了一件笨功夫：借助 AI，把他的方法整理出来，做成一个你随时能问、随时能用的工具。我把自己当作曾师的AI学徒，学到的，还给需要的人。

## 这个站怎么用

- 把眼下最纠结的那件事写下来，起一卦；
- 你会拿到一份五段报告：核心洞察、现状刺透、避坑指南、破局行动、未来演进；
- 重点从来不是卦，是你。卦是镜子，不是算盘，它照见的，是你心里早就知道的答案。

## 我们的立场

- 不预测吉凶，不承诺成败；
- 不替代任何专业意见。投资、法律、医疗这类重大决定，请找对口的专业人士；
- 免费使用，不需注册。

## 联系我们

使用上的问题、建议，或想删除你的使用资料，欢迎 IG 私信：[@kysonsdecisionbook](%s)

凯森""" % IG_URL,
        },
    },
    "privacy": {
        "tc": {
            "title": "隱私聲明",
            "meta": "最後更新：2026 年 10 月",
            "desc": "決策之書的隱私聲明：我們收集哪些資料、如何使用、第三方服務與資料刪除方式。",
            "body": """## 我們收集哪些資料

- 你輸入的問題：僅用於生成你的報告；
- 你選擇的地區與語言：用於讓報告貼近你的處境；
- 匿名使用統計：頁面瀏覽與按鈕點擊（Google Analytics、Vercel Analytics，含 Cookie 及類似技術），用於了解使用情況、改進產品。

說明：本站不需要註冊；我們不收集你的姓名、電話、郵箱；起卦的推演過程在你自己的瀏覽器裡完成，不上傳任何資料。

## 這些資料怎麼被使用

- 問題文本會傳送給 AI 服務（Dify）以生成報告，報告只在你的瀏覽器呈現；
- 我們不會把資料賣給任何人，也不會用於廣告投放；
- 統計數據為匿名匯總，用於產品改進。

## 第三方服務

本站使用以下第三方服務，它們會依各自規範處理數據：Vercel（網站託管）、Dify（AI 報告生成）、Google Analytics（流量統計）。你可以在瀏覽器設定中管理或清除 Cookie。

## 資料的保留與刪除

本站不建立用戶帳戶資料庫。如需查詢或刪除與你相關的處理記錄，請 IG 私訊 [@kysonsdecisionbook](%s)，我們會盡快處理。

## 變更

本聲明如有更新，將直接更新於本頁。""" % IG_URL,
        },
        "sc": {
            "title": "隐私声明",
            "meta": "最后更新：2026 年 10 月",
            "desc": "决策之书的隐私声明：我们收集哪些资料、如何使用、第三方服务与资料删除方式。",
            "body": """## 我们收集哪些资料

- 你输入的问题：仅用于生成你的报告；
- 你选择的地区与语言：用于让报告贴近你的处境；
- 匿名使用统计：页面浏览与按钮点击（Google Analytics、Vercel Analytics，含 Cookie 及类似技术），用于了解使用情况、改进产品。

说明：本站不需要注册；我们不收集你的姓名、电话、邮箱；起卦的推演过程在你自己的浏览器里完成，不上传任何资料。

## 这些资料怎么被使用

- 问题文本会传送给 AI 服务（Dify）以生成报告，报告只在你的浏览器呈现；
- 我们不会把资料卖给任何人，也不会用于广告投放；
- 统计数据为匿名汇总，用于产品改进。

## 第三方服务

本站使用以下第三方服务，它们会依各自规范处理数据：Vercel（网站托管）、Dify（AI 报告生成）、Google Analytics（流量统计）。你可以在浏览器设置中管理或清除 Cookie。

## 资料的保留与删除

本站不建立用户账户数据库。如需查询或删除与你相关的处理记录，请 IG 私信 [@kysonsdecisionbook](%s)，我们会尽快处理。

## 变更

本声明如有更新，将直接更新于本页。""" % IG_URL,
        },
    },
    "disclaimer": {
        "tc": {
            "title": "免責聲明",
            "meta": "卦不預測吉凶，請把它當成思考工具",
            "desc": "決策之書免責聲明：卦不預測吉凶，報告僅供決策思考參考，不構成任何專業建議。",
            "body": """## 關於卦

決策之書提供的是基於《易經》的思考工具：幫你整理處境、打開視角。它不預測吉凶，也不承諾任何結果。

## 關於報告

- 報告內容由 AI 根據你的問題生成，僅供決策思考參考；
- 不構成投資、法律、醫療、財務、職業等任何專業建議；重大決定請諮詢相應專業人士；
- 請結合你自身的實際情況獨立判斷。

## 關於內容

卦辭爻辭原文出自《周易》，屬公版內容；站內的解讀、報告與其他文字，僅供個人參考使用。

## 使用責任

你依據本站內容作出的任何決定，由你自己負責。""",
        },
        "sc": {
            "title": "免责声明",
            "meta": "卦不预测吉凶，请把它当成思考工具",
            "desc": "决策之书免责声明：卦不预测吉凶，报告仅供决策思考参考，不构成任何专业建议。",
            "body": """## 关于卦

决策之书提供的是基于《易经》的思考工具：帮你整理处境、打开视角。它不预测吉凶，也不承诺任何结果。

## 关于报告

- 报告内容由 AI 根据你的问题生成，仅供决策思考参考；
- 不构成投资、法律、医疗、财务、职业等任何专业建议；重大决定请咨询相应专业人士；
- 请结合你自身的实际情况独立判断。

## 关于内容

卦辞爻辞原文出自《周易》，属公版内容；站内的解读、报告与其他文字，仅供个人参考使用。

## 使用责任

你依据本站内容作出的任何决定，由你自己负责。""",
        },
    },
}

# ============================================================
# 样式（沿用博客模板的变量与导航规格）
# ============================================================
CSS = """
:root{--ink:#1a1a1a;--sub:#666;--line:#e5e5e5;--bg:#fafaf8;--accent:#8a6d3b}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,"PingFang TC","PingFang SC","Noto Sans TC","Noto Sans SC",sans-serif;background:var(--bg);color:var(--ink);line-height:1.9;font-size:16px}
.site-nav{position:sticky;top:0;z-index:40;background:rgba(250,250,248,.86);-webkit-backdrop-filter:blur(12px) saturate(1.6);backdrop-filter:blur(12px) saturate(1.6);border-bottom:1px solid var(--line)}
.site-nav-inner{max-width:680px;margin:0 auto;padding:0 22px;height:48px;display:flex;align-items:center;justify-content:center;gap:36px;position:relative}
.site-nav a.nav-item{color:var(--sub);text-decoration:none;font-size:14px;letter-spacing:.2em;padding:6px 2px;transition:color .2s}
.site-nav a.nav-item:hover{color:var(--accent)}
.site-nav .lang-switch{position:absolute;right:22px;top:50%;transform:translateY(-50%);font-weight:400;font-size:12.5px;color:var(--sub);letter-spacing:0;border:1px solid var(--line);border-radius:6px;padding:3px 10px}
.site-nav .lang-switch:hover{color:var(--accent);border-color:var(--accent)}
.wrap{max-width:680px;margin:0 auto;padding:44px 22px 80px}
h1{font-size:28px;letter-spacing:.06em;margin-bottom:8px}
.meta{color:var(--sub);font-size:13px;letter-spacing:.06em;margin-bottom:36px}
article h2{font-size:19px;margin:36px 0 14px;padding-left:10px;border-left:3px solid var(--ink)}
article p{margin-bottom:14px}
article ul{padding-left:22px;margin-bottom:14px}
article li{margin-bottom:6px}
article a{color:var(--accent)}
footer{margin-top:56px;padding-top:22px;border-top:1px solid var(--line);color:var(--sub);font-size:12.5px;line-height:1.9;text-align:center}
.f-links{margin-bottom:2px}
.f-links a{color:var(--sub);text-decoration:none}
.f-links a:hover{color:var(--accent)}
.f-brand{color:var(--sub);margin-top:6px}
@media (prefers-color-scheme: dark){
:root{--ink:#E8E6E0;--sub:#8B8F98;--line:#2A2E3A;--bg:#0F1115;--accent:#C8A96A}
.site-nav{background:rgba(15,17,21,.86)}
}
@media (max-width:640px){
.site-nav-inner{padding:0 16px;gap:22px}
.site-nav .lang-switch{right:16px}
.site-nav a.nav-item{letter-spacing:.15em}
}
"""


def nav_html(lang, slug):
    tc = lang == "tc"
    p = "" if tc else "/cn"
    alt = ("/cn/" if tc else "") + slug + "/"
    return f"""<nav class="site-nav">
  <div class="site-nav-inner">
    <a class="nav-item" href="{p}/">{'提問' if tc else '提问'}</a>
    <a class="nav-item" href="{p}/hexagram/">{'易經' if tc else '易经'}</a>
    <a class="nav-item" href="{p}/blog/">{'筆記' if tc else '笔记'}</a>
    <a class="lang-switch" href="{alt}">{'简体中文' if tc else '繁體中文'}</a>
  </div>
</nav>"""


def footer_html(lang):
    return site_components.footer_html(lang, "default")


def build_page(slug, lang):
    cfg = PAGES[slug][lang]
    tc = lang == "tc"
    prefix = "" if tc else "/cn"
    canonical = f"{BASE_URL}{prefix}/{slug}/"
    alt_url = f"{BASE_URL}/cn/{slug}/" if tc else f"{BASE_URL}/{slug}/"
    html_lang = "zh-Hant" if tc else "zh-Hans"
    brand = "決策之書" if tc else "决策之书"
    body_html = md_to_html(cfg["body"])
    return f"""<!DOCTYPE html>
<html lang="{html_lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{cfg['title']}｜{brand}</title>
<meta name="description" content="{cfg['desc']}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="{html_lang}" href="{canonical}">
<link rel="alternate" hreflang="{'zh-Hans' if tc else 'zh-Hant'}" href="{alt_url}">
<link rel="alternate" hreflang="x-default" href="{BASE_URL}/{slug}/">
<meta property="og:type" content="website">
<meta property="og:title" content="{cfg['title']}｜{brand}">
<meta property="og:description" content="{cfg['desc']}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{brand}">
<style>{CSS}</style>
{GA_SNIPPET}
</head>
<body>
{nav_html(lang, slug)}
<div class="wrap">
  <h1>{cfg['title']}</h1>
  <p class="meta">{cfg['meta']}</p>
  <article>
{body_html}
  </article>
  {footer_html(lang)}
</div>
</body>
</html>"""


def main():
    n = 0
    for slug in PAGES:
        for lang in ("tc", "sc"):
            out_dir = PUBLIC / ("cn" if lang == "sc" else "") / slug
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "index.html").write_text(build_page(slug, lang), encoding="utf-8")
            n += 1
            print(f"  ✓ {'/cn' if lang == 'sc' else ''}/{slug}/ ({lang})")
    print(f"\n完成 {n} 页。提交 git 后 Vercel 自动部署。")


if __name__ == "__main__":
    main()
