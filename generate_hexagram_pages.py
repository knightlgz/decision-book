#!/usr/bin/env python3
"""
生成 64 卦象 SEO 落地页（繁简双语 + 原文 + FAQ schema）
用法：python3 generate_hexagram_pages.py

输出结构：
  public/hexagram/NN/index.html        ← 繁体页 (zh-Hant, 主市场 TW/HK)
  public/cn/hexagram/NN/index.html     ← 简体页 (zh-Hans, 目标 MY/SG 华语用户)
  public/hexagram/index.html           ← 繁体索引
  public/cn/hexagram/index.html        ← 简体索引
  public/sitemap.xml                   ← 全量 URL（130+）
"""
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "src" / "data" / "hexagrams.js"
ORIGINAL_FILE = ROOT / "src" / "data" / "iching_original.json"
INTERP_FILE = ROOT / "src" / "data" / "hexagram_interpretations.json"
PUBLIC = ROOT / "public"
BASE_URL = "https://decision-book.vercel.app"


def parse_original():
    """读取原文数据（卦辞+爻辞），按卦序号索引"""
    data = json.loads(ORIGINAL_FILE.read_text(encoding="utf-8"))
    return {d["id"]: d for d in data}


def parse_interpretations():
    """读取白话解读（DeepSeek 生成），返回 {number: {meaning, career, advice}}"""
    if not INTERP_FILE.exists():
        return {}
    return json.loads(INTERP_FILE.read_text(encoding="utf-8"))


def parse_hexagrams():
    """用 Node.js 解析 ES module"""
    tmp_js = Path(tempfile.gettempdir()) / "dump_hexagrams.mjs"
    tmp_js.write_text("""
import HEXAGRAMS from '%s';
console.log(JSON.stringify(HEXAGRAMS));
""" % DATA_FILE.as_posix(), encoding="utf-8")
    result = subprocess.run(["node", tmp_js.as_posix()], capture_output=True, text=True, cwd=ROOT)
    if result.returncode != 0:
        print("Node 解析失败:", result.stderr[:300])
        return []
    return json.loads(result.stdout)


FAQ_TC = [
    {
        "q": "這個卦象適合問什麼問題？",
        "a": "適合工作與事業上的抉擇，例如轉職、與主管同事相處、創業方向、升遷時機等情境。",
    },
    {
        "q": "如何獲得專屬於我的卦象解讀？",
        "a": "在決策之書輸入你的具體困惑即可免費起卦；輸入解鎖密碼後，AI 會基於曾仕強教授易經思想體系，生成一份結合你情境的完整商業決策報告。",
    },
    {
        "q": "卦象解讀可以代替專業意見嗎？",
        "a": "易經解讀提供的是東方智慧視角與思考框架，重大商業或人生決策仍建議結合自身判斷與專業意見。",
    },
]

FAQ_SC = [
    {
        "q": "这个卦象适合问什么问题？",
        "a": "适合工作与事业上的抉择，例如转职、与主管同事相处、创业方向、升迁时机等情境。",
    },
    {
        "q": "如何获得专属于我的卦象解读？",
        "a": "在决策之书输入你的具体困惑即可免费起卦；输入解锁密码后，AI 会基于曾仕强教授易经思想体系，生成一份结合你情境的完整商业决策报告。",
    },
    {
        "q": "卦象解读可以代替专业意见吗？",
        "a": "易经解读提供的是东方智慧视角与思考框架，重大商业或人生决策仍建议结合自身判断与专业意见。",
    },
]


def faq_jsonld(faq_items, url):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["q"],
                "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
            }
            for item in faq_items
        ],
    }, ensure_ascii=False)


# 试点页 SEO 优化（2026-08-28）：热门关键词 → 卦页映射
# 标题场景词 + Meta 描述 + 热点 FAQ。验证 2 周后决定是否全量推广
SEO_PILOT = {
    "27": {  # 山雷頤 → 精神內耗
        "tc": {"kw": "精神內耗", "kw2": "消耗還是滋養",
               "faq_q": "工作讓我越來越內耗，是山雷頤卦的意思嗎？該怎麼調適？",
               "faq_a": "頤卦講「自求口實」：先分清工作是消耗你還是滋養你，再決定去留，答案會慢慢浮現。"},
        "sc": {"kw": "精神内耗", "kw2": "消耗还是滋养",
               "faq_q": "工作让我越来越内耗，是山雷颐卦的意思吗？该怎么调适？",
               "faq_a": "颐卦讲「自求口实」：先分清工作是消耗你还是滋养你，再决定去留，答案会慢慢浮现。"},
    },
    "38": {  # 火澤睽 → 被主管針對
        "tc": {"kw": "被主管針對", "kw2": "職場對立",
               "faq_q": "感覺主管一直針對我，火澤睽卦怎麼看這種職場對立？",
               "faq_a": "睽卦講「小事吉」：對立之中仍有轉圜，先別把矛盾升級，找雙方都能接受的共識點。"},
        "sc": {"kw": "被主管针对", "kw2": "职场对立",
               "faq_q": "感觉主管一直针对我，火泽睽卦怎么看这种职场对立？",
               "faq_a": "睽卦讲「小事吉」：对立之中仍有转圜，先别把矛盾升级，找双方都能接受的共识点。"},
    },
    "3": {  # 水雷屯 → 面試失敗/求職碰壁
        "tc": {"kw": "面試失敗", "kw2": "求職碰壁",
               "faq_q": "面試一直碰壁，是水雷屯卦的暗示嗎？該怎麼調適？",
               "faq_a": "屯卦代表萬事起頭難：碰壁不代表你不夠好，而是時機與位置還沒對上，先蓄力再出發。"},
        "sc": {"kw": "面试失败", "kw2": "求职碰壁",
               "faq_q": "面试一直碰壁，是水雷屯卦的暗示吗？该怎么调适？",
               "faq_a": "屯卦代表万事起头难：碰壁不代表你不够好，而是时机与位置还没对上，先蓄力再出发。"},
    },
    "47": {  # 澤水困 → 中年失業/被資遣
        "tc": {"kw": "中年失業", "kw2": "被資遣",
               "faq_q": "中年被資遣怎麼辦？澤水困卦給什麼啟示？",
               "faq_a": "困卦講「困而不失其所亨」：困境中守住本心與專業，暫時的困頓反而是重新定位的契機。"},
        "sc": {"kw": "中年失业", "kw2": "被资遣",
               "faq_q": "中年被资遣怎么办？泽水困卦给什么启示？",
               "faq_a": "困卦讲「困而不失其所亨」：困境中守住本心与专业，暂时的困顿反而是重新定位的契机。"},
    },
}


# GA4 埋码（G-SGYWZGNCSH，2026-08-28 添加）
GA_SNIPPET = """  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-SGYWZGNCSH"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-SGYWZGNCSH');
  </script>
"""


def page_html(hx, orig, interp, prev_num, next_num, lang="tc", related=None):
    """单个卦象页。lang: tc=繁体 / sc=简体
    related: [(num, tc_name, sc_name), ...] 相关卦列表（同上卦）"""
    n = hx["number"]
    is_tc = lang == "tc"
    name = hx["tc"]["name"] if is_tc else hx["sc"]["name"]
    insight = hx["tc"]["insight"] if is_tc else hx["sc"]["insight"]
    num_label = f"第 {int(n)} 卦"

    # 白话解读（繁→简转换）
    interp_text = interp if interp else {"meaning": "", "career": "", "advice": ""}
    if not is_tc:
        try:
            from opencc import OpenCC
            cc = OpenCC("t2s")
            interp_text = {k: cc.convert(v) for k, v in interp_text.items()}
        except ImportError:
            pass

    # 试点页 SEO 覆盖（标题场景词 + 描述关键词）
    pilot = SEO_PILOT.get(str(int(n)), {})

    if is_tc:
        title = f"{name}卦｜第{int(n)}卦｜曾仕強易經商業決策解讀"
        desc = f"易經第{int(n)}卦{name}：{insight}。卦辭爻辭原文、商業與職場核心解讀，基於曾仕強教授易經思想體系。"
        if pilot:
            p = pilot["tc"]
            title = f"{name}卦 {p['kw']}｜{p['kw2']}｜曾仕強易經解讀"
            desc = f"易經第{int(n)}卦{name}：{p['kw']}、{p['kw2']}。{insight}基於曾仕強教授易經思想體系，卦辭爻辭原文與職場解讀。"
        html_lang = "zh-Hant"
        url = f"{BASE_URL}/hexagram/{n}/"
        alt_url = f"{BASE_URL}/cn/hexagram/{n}/"
        home = "/"
        idx_link = "/hexagram/"
        prev_label = "← 上一卦"
        next_label = "下一卦 →"
        all_label = "全部六十四卦"
        breadcrumb_home = "決策之書"
        breadcrumb_idx = "六十四卦"
        insight_label = "核心解讀"
        cta_h2 = "你正在面對類似的職場或商業抉擇嗎？"
        cta_p = "免費起卦，看看你的能量切片對應哪一卦；針對你處境的完整行動方案，可輸入解鎖密碼後查看。"
        cta_btn = "免費起卦 →"
        cta_mini_text = "你的困惑，也可以起一卦看看"
        orig_label = "《易經》原文"
        gua_label = "卦辭"
        yao_label = "爻辭"
        scripture_note = "原文出自《周易》，公版內容。"
        footer = "曾仕強教授易經思想體系"
        subtitle_line = "曾仕強易經思想體系 · 商業與職場解讀"
        faq_heading = "常見問題"
        related_label = "相關卦象"
        interp_labels = ["白話釋義", "職場啟示", "行動建議"]
    else:
        title = f"{name}卦｜第{int(n)}卦｜曾仕强易经商业决策解读"
        desc = f"易经第{int(n)}卦{name}：{insight}。卦辞爻辞原文、商业与职场核心解读，基于曾仕强教授易经思想体系。"
        if pilot:
            p = pilot["sc"]
            title = f"{name}卦 {p['kw']}｜{p['kw2']}｜曾仕强易经解读"
            desc = f"易经第{int(n)}卦{name}：{p['kw']}、{p['kw2']}。{insight}基于曾仕强教授易经思想体系，卦辞爻辞原文与职场解读。"
        html_lang = "zh-Hans"
        url = f"{BASE_URL}/cn/hexagram/{n}/"
        alt_url = f"{BASE_URL}/hexagram/{n}/"
        home = "/"
        idx_link = "/cn/hexagram/"
        prev_label = "← 上一卦"
        next_label = "下一卦 →"
        all_label = "全部六十四卦"
        breadcrumb_home = "决策之书"
        breadcrumb_idx = "六十四卦"
        insight_label = "核心解读"
        cta_h2 = "你正在面对类似的职场或商业抉择吗？"
        cta_p = "免费起卦，看看你的能量切片对应哪一卦；针对你处境的完整行动方案，可输入解锁密码后查看。"
        cta_btn = "免费起卦 →"
        cta_mini_text = "你的困惑，也可以起一卦看看"
        orig_label = "《易经》原文"
        gua_label = "卦辞"
        yao_label = "爻辞"
        scripture_note = "原文出自《周易》，公版内容。"
        footer = "曾仕强教授易经思想体系"
        subtitle_line = "曾仕强易经思想体系 · 商业与职场解读"
        faq_heading = "常见问题"
        related_label = "相关卦象"
        interp_labels = ["白话释义", "职场启示", "行动建议"]

    faq_items = FAQ_TC if is_tc else FAQ_SC
    # 试点页追加热点 FAQ（SEO_PILOT）
    if pilot:
        pf = pilot["tc"] if is_tc else pilot["sc"]
        faq_items = faq_items + [{"q": pf["faq_q"], "a": pf["faq_a"]}]
    faq_lines = "\n".join(
        f'<div class="faq-item"><div class="faq-q">{item["q"]}</div><div class="faq-a">{item["a"]}</div></div>'
        for item in faq_items
    )

    prev_link = f'<a href="{idx_link}{prev_num}/" class="nav-link">{prev_label}</a>' if prev_num else '<span class="nav-link muted">首卦</span>'
    next_link = f'<a href="{idx_link}{next_num}/" class="nav-link">{next_label}</a>' if next_num else '<span class="nav-link muted">末卦</span>'

    # 语言切换链接
    if is_tc:
        lang_switch = f'<span class="lang-switch"><a href="{alt_url}" hreflang="zh-Hans" rel="alternate">简体中文</a></span>'
    else:
        lang_switch = f'<span class="lang-switch"><a href="{alt_url}" hreflang="zh-Hant" rel="alternate">繁體中文</a></span>'

    # 原文
    scripture_html = ""
    if orig:
        scripture_html += f'<p class="gua-ci">{orig.get("scripture","")}</p>'
        lines_html = ""
        for line in orig.get("lines", []):
            lines_html += f'<div class="yao-line"><span class="yao-name">{line["name"]}</span><span class="yao-text">{line["scripture"]}</span></div>'
        scripture_html += lines_html

    # 白话解读区块（DeepSeek 生成）
    # 策略：释义全量展示；职场启示截为2句引子；行动建议不上页面（付费产品核心价值）
    def to_paragraphs(text):
        """优先按 LLM 语义分段标记 ||| 分，无标记时退回原样"""
        if "|||" in text:
            parts = [p.strip() for p in text.split("|||") if p.strip()]
            return "".join(f"<p>{p}</p>" for p in parts)
        return f"<p>{text}</p>"

    interp_html = ""
    meaning_text = interp_text.get("meaning", "")
    career_text = interp_text.get("career", "")
    if meaning_text or career_text:
        blocks = []
        if meaning_text:
            blocks.append(f'<div class="interp-block"><h3>{interp_labels[0]}</h3>{to_paragraphs(meaning_text)}</div>')
        if career_text:
            # 截取前两句作为引子
            sentences = re.split(r'(?<=[。！？])', career_text)
            teaser = "".join(sentences[:2]).strip()
            if len(teaser) < 30 and len(sentences) > 2:
                teaser += sentences[2]
            teaser += "…"
            blocks.append(f'<div class="interp-block"><h3>{interp_labels[1]}</h3><p>{teaser}</p></div>')
        interp_html = f'<div class="interpretation">{"".join(blocks)}</div>'

    # 相关卦模块（錯綜交互，含关系标签）
    related_html = ""
    if related:
        rel_links = []
        for rn, rtc, rsc, rlabel in related[:4]:
            r_name = rtc if is_tc else rsc
            rel_links.append(f'<a href="{idx_link}{rn}/"><span class="rel-name">{r_name}</span><span class="rel-tag">{rlabel}</span></a>')
        if rel_links:
            related_html = f'<div class="related"><h3>{related_label}</h3><div class="grid">{"".join(rel_links)}</div></div>'

    # 六爻卦象图（小白也能看懂卦长什么样）
    TRI_SYMBOLS = {"乾": "☰", "兌": "☱", "離": "☲", "震": "☳", "巽": "☴", "坎": "☵", "艮": "☶", "坤": "☷"}
    gua_visual = ""
    if orig and orig.get("array"):
        arr = orig["array"]  # 自下而上：arr[0]=初爻
        comb = orig.get("combination", [])
        lines_html = []
        pos_names = ["初", "二", "三", "四", "五", "上"]
        for i in range(5, -1, -1):  # 上爻在最上
            yang = arr[i] == 1
            # 爻名规则：初/上爻位置在前（初九/上六），中爻九/六在前（九三/六四）
            if i == 0:
                yao = f"初{'九' if yang else '六'}"
            elif i == 5:
                yao = f"上{'九' if yang else '六'}"
            else:
                yao = f"{'九' if yang else '六'}{pos_names[i]}"
            bar = "bar yang" if yang else "bar yin"
            if yang:
                lines_html.append(f'<div class="line"><span class="bar yang"></span><span class="yao-name">{yao}</span></div>')
            else:
                lines_html.append(f'<div class="line"><span class="bar yin"><span class="yin-seg"></span><span class="yin-seg"></span></span><span class="yao-name">{yao}</span></div>')
        gua_visual = (
            f'<div class="hexagram-visual">'
            f'<div class="hexagram-lines">{"".join(lines_html)}</div>'
            f'<div class="hexagram-side">'
            f'<div class="gua-name">{name}</div>'
            f'<div class="tri-label">上{comb[1] if len(comb) == 2 else ""} · 下{comb[0] if len(comb) == 2 else ""}</div>'
            f'</div></div>'
        )

    ga_snippet = GA_SNIPPET

    # Article + FAQ 双 schema
    article_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": desc,
        "author": {"@type": "Organization", "name": breadcrumb_home},
        "publisher": {"@type": "Organization", "name": breadcrumb_home},
        "mainEntityOfPage": url,
        "inLanguage": html_lang,
    }, ensure_ascii=False)
    faq_ld = faq_jsonld(faq_items, url)

    return f"""<!DOCTYPE html>
<html lang="{html_lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="zh-Hant" href="{BASE_URL}/hexagram/{n}/">
<link rel="alternate" hreflang="zh-Hans" href="{BASE_URL}/cn/hexagram/{n}/">
<link rel="alternate" hreflang="x-default" href="{BASE_URL}/hexagram/{n}/">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="{breadcrumb_home}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<script type="application/ld+json">{article_ld}</script>
<script type="application/ld+json">{faq_ld}</script>
<style>
  :root {{
    --bg:#0f1115; --text:#e8e6e0; --text-strong:#f5f2ea; --muted:#8b8f98; --muted2:#5a5e68;
    --card:#171a22; --card2:#131621; --border:#2a2e3a; --accent:#c8a96a; --accent-hover:#d9ba7a;
    --accent-border:#c8a96a33; --accent-border2:#c8a96a44; --text2:#a8a5a0; --text3:#dcd8cf;
    --cta-bg1:#1c2030; --cta-bg2:#151823;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{
      --bg:#faf8f4; --text:#3a3833; --text-strong:#22201c; --muted:#7a766d; --muted2:#aaa69c;
      --card:#ffffff; --card2:#f4f1ea; --border:#e5e0d5; --accent:#9a7b3f; --accent-hover:#7d6433;
      --accent-border:#9a7b3f33; --accent-border2:#9a7b3f44; --text2:#5f5b52; --text3:#4a4740;
      --cta-bg1:#f0ece2; --cta-bg2:#faf8f4;
    }}
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:var(--bg); color:var(--text); font-family:"PingFang TC","PingFang SC","Noto Sans TC","Noto Sans SC","Microsoft JhengHei",sans-serif; line-height:1.9; font-size:16px; }}
  .container {{ max-width:900px; margin:0 auto; padding:48px 24px; }}
  .topbar {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; }}
  .breadcrumb {{ font-size:14px; color:var(--muted); }}
  .breadcrumb a {{ color:var(--accent); text-decoration:none; }}
  .lang-switch a {{ color:var(--muted); text-decoration:none; font-size:14px; border:1px solid var(--border); padding:4px 12px; border-radius:16px; transition:all .2s; }}
  .lang-switch a:hover {{ color:var(--accent); border-color:var(--accent); }}
  .lang-switch a.active {{ color:var(--accent); border-color:var(--accent); }}
  .hexagram-badge {{ display:inline-block; background:var(--card); border:1px solid var(--accent-border); color:var(--accent); padding:4px 14px; border-radius:20px; font-size:13px; letter-spacing:2px; white-space:nowrap; }}
  .title-row {{ display:flex; align-items:center; gap:14px; margin-bottom:6px; flex-wrap:wrap; }}
  h1 {{ font-size:40px; margin:0; color:var(--text-strong); line-height:1.3; }}
  .subtitle {{ color:var(--muted); font-size:14px; margin-bottom:32px; }}
  .insight {{ background:var(--card); border-left:3px solid var(--accent); padding:24px; border-radius:0 8px 8px 0; font-size:18px; color:var(--text3); margin-bottom:48px; box-shadow:0 2px 12px rgba(0,0,0,.04); }}
  .insight-label {{ color:var(--accent); font-size:13px; letter-spacing:3px; margin-bottom:12px; display:block; }}
  .interpretation {{ margin-bottom:48px; }}
  .interp-block {{ background:var(--card); border-radius:10px; padding:20px 24px; margin-bottom:12px; box-shadow:0 2px 10px rgba(0,0,0,.04); }}
  .interp-block h3 {{ color:var(--accent); font-size:15px; letter-spacing:2px; margin-bottom:10px; }}
  .interp-block p {{ color:var(--text3); font-size:15px; line-height:1.9; margin-bottom:12px; }}
  .interp-block p:last-child {{ margin-bottom:0; }}
  .scripture {{ background:var(--card2); border:1px solid var(--border); border-radius:12px; padding:24px; margin-bottom:48px; }}
  .scripture-label {{ color:var(--accent); font-size:13px; letter-spacing:3px; margin-bottom:16px; display:block; }}
  .gua-ci {{ font-size:20px; color:var(--text-strong); border-bottom:1px solid var(--border); padding-bottom:16px; margin-bottom:16px; }}
  .yao-line {{ display:flex; gap:16px; padding:8px 0; font-size:16px; }}
  .yao-name {{ color:var(--accent); min-width:44px; font-weight:700; }}
  .yao-text {{ color:var(--text3); }}
  .scripture-note {{ font-size:12px; color:var(--muted2); margin-top:12px; }}
  .cta {{ text-align:center; background:linear-gradient(135deg,var(--cta-bg1),var(--cta-bg2)); border:1px solid var(--accent-border2); border-radius:12px; padding:32px 24px; margin-bottom:48px; }}
  .cta h2 {{ font-size:22px; margin-bottom:12px; color:var(--text-strong); }}
  .cta p {{ color:var(--text2); font-size:15px; margin-bottom:20px; }}
  .cta a.btn {{ display:inline-block; background:var(--accent); color:var(--bg); text-decoration:none; padding:12px 32px; border-radius:24px; font-weight:700; font-size:16px; transition:all .2s; }}
  .cta a.btn:hover {{ background:var(--accent-hover); transform:translateY(-2px); box-shadow:0 6px 16px rgba(0,0,0,.15); }}
  /* 首屏迷你 CTA（移动端第一屏可见） */
  .cta-mini {{ margin:24px 0 40px; padding:16px 20px; border:1px solid var(--accent-border2); border-radius:10px; display:flex; align-items:center; justify-content:space-between; gap:12px; background:var(--card); }}
  .cta-mini span {{ font-size:15px; color:var(--text); }}
  .cta-mini a {{ white-space:nowrap; background:var(--accent); color:var(--bg); text-decoration:none; padding:8px 20px; border-radius:20px; font-size:14px; font-weight:700; }}
  .cta-mini a:hover {{ background:var(--accent-hover); }}
  /* 相关卦模块 */
  .related {{ margin-bottom:48px; }}
  .related h3 {{ color:var(--accent); font-size:13px; letter-spacing:3px; margin-bottom:12px; }}
  .related .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:10px; }}
  .related .grid a {{ display:block; background:var(--card); border:1px solid var(--border); color:var(--text); text-decoration:none; padding:12px 16px; border-radius:8px; font-size:14px; transition:border-color .2s; }}
  .related .grid a:hover {{ border-color:var(--accent); color:var(--accent); }}
  .related .rel-name {{ display:block; }}
  .related .rel-tag {{ display:inline-block; font-size:11px; color:var(--accent); border:1px solid var(--accent-border2); border-radius:10px; padding:1px 8px; margin-top:4px; }}
  .faq {{ margin-bottom:48px; }}
  .faq h3 {{ font-size:16px; color:var(--muted); letter-spacing:2px; margin-bottom:16px; }}
  .faq-item {{ background:var(--card); border-radius:8px; padding:16px; margin-bottom:8px; }}
  .faq-q {{ color:var(--text-strong); font-weight:700; font-size:15px; margin-bottom:6px; }}
  .faq-a {{ color:var(--text2); font-size:14px; }}
  .nav {{ display:flex; justify-content:space-between; padding:16px 0; border-top:1px solid var(--border); font-size:15px; }}
  .nav a {{ color:var(--accent); text-decoration:none; }}
  .muted {{ color:var(--muted2); }}
  footer {{ text-align:center; padding:24px; color:var(--muted2); font-size:13px; }}
  footer a {{ color:var(--muted); }}
  /* 六爻卦象图（Hero 视觉焦点） */
  .hexagram-visual {{ display:flex; align-items:center; gap:32px; margin-bottom:32px; padding:32px 28px; background:linear-gradient(135deg,var(--card),var(--card2)); border:1px solid var(--accent-border2); border-radius:16px; box-shadow:0 6px 24px rgba(0,0,0,.06); }}
  .hexagram-lines {{ display:flex; flex-direction:column; gap:7px; }}
  .hexagram-lines .line {{ display:flex; align-items:center; gap:10px; }}
  .hexagram-lines .bar {{ display:block; height:12px; border-radius:3px; background:var(--text-strong); }}
  .hexagram-lines .bar.yang {{ width:160px; }}
  .hexagram-lines .bar.yin {{ display:flex; justify-content:space-between; width:160px; background:transparent; }}
  .hexagram-lines .bar.yin .yin-seg {{ width:70px; height:12px; background:var(--text-strong); border-radius:3px; }}
  .hexagram-lines .yao-name {{ font-size:12px; color:var(--muted); width:28px; }}
  .hexagram-side {{ flex:1; }}
  .hexagram-side .tri-label {{ font-size:13px; color:var(--muted); letter-spacing:2px; margin-bottom:6px; }}
  .hexagram-side .gua-name {{ font-size:32px; font-weight:700; color:var(--text-strong); margin-bottom:8px; }}
  @media (max-width:600px) {{
    .container {{ padding:24px 16px; }}
    .title-row {{ gap:10px; }}
    h1 {{ font-size:28px; }}
    .subtitle {{ margin-bottom:20px; font-size:13px; }}
    .hexagram-visual {{ flex-direction:row; align-items:center; text-align:left; gap:14px; padding:16px 14px; margin-bottom:20px; }}
    .hexagram-lines {{ gap:4px; }}
    .hexagram-lines .bar {{ height:9px; }}
    .hexagram-lines .bar.yang, .hexagram-lines .bar.yin {{ width:90px; }}
    .hexagram-lines .bar.yin .yin-seg {{ width:38px; }}
    .hexagram-lines .yao-name {{ font-size:10px; width:22px; }}
    .hexagram-side .tri-label {{ font-size:11px; margin-bottom:3px; }}
    .hexagram-side .gua-name {{ font-size:22px; margin-bottom:4px; }}
    .cta-mini {{ flex-wrap:wrap; margin:16px 0 28px; }}
    .cta-mini a {{ flex:1; text-align:center; padding:12px 16px; font-size:16px; }}
    .cta a.btn {{ display:block; width:100%; padding:14px 0; font-size:17px; }}
  }}
</style>
  {ga_snippet}
 </head>
 <body>
 <div class="container">
  <div class="topbar">
    <div class="breadcrumb"><a href="{home}">{breadcrumb_home}</a> / <a href="{idx_link}">{breadcrumb_idx}</a> / {name}</div>
    {lang_switch}
  </div>
  <div class="title-row">
    <span class="hexagram-badge">{num_label}</span>
    <h1>{name}</h1>
  </div>
  <p class="subtitle">{subtitle_line}</p>

  {gua_visual}

  <div class="cta-mini">
    <span>{cta_mini_text}</span>
    <a href="{home}">{cta_btn}</a>
  </div>

  <div class="insight">
    <span class="insight-label">{insight_label}</span>
    {insight}
  </div>

  <div class="scripture">
    <span class="scripture-label">{orig_label}</span>
    {scripture_html}
    <p class="scripture-note">{scripture_note}</p>
  </div>

  {interp_html}

  {related_html}

  <div class="cta">
    <h2>{cta_h2}</h2>
    <p>{cta_p}</p>
    <a class="btn" href="{home}">{cta_btn}</a>
  </div>

  <div class="faq">
    <h3>{faq_heading}</h3>
    {faq_lines}
  </div>

  <div class="nav">
    {prev_link}
    <a href="{idx_link}" class="nav-link">{all_label}</a>
    {next_link}
  </div>
</div>
<footer>
  <a href="{idx_link}">{breadcrumb_idx}</a> · <a href="{home}">{breadcrumb_home}</a> · {footer}
</footer>
</body>
</html>"""


def index_html(hexagrams, lang="tc"):
    """六十四卦索引页"""
    is_tc = lang == "tc"
    ga_snippet = GA_SNIPPET
    items = "\n".join(
        f'<a href="{"/hexagram/" if is_tc else "/cn/hexagram/"}{h["number"]}/"><span class="num">第 {int(h["number"])} 卦</span>{(h["tc"]["name"] if is_tc else h["sc"]["name"])}</a>'
        for h in hexagrams
    )
    if is_tc:
        title = "易經六十四卦｜曾仕強商業決策解讀全索引"
        desc = "易經六十四卦完整索引：每卦的卦辭爻辭原文、商業與職場核心解讀，基於曾仕強教授易經思想體系。"
        html_lang = "zh-Hant"
        url = f"{BASE_URL}/hexagram/"
        home_label = "決策之書"
        idx_label = "六十四卦"
        h1 = "易經六十四卦"
        subtitle = "曾仕強教授易經思想體系 · 商業與職場雙語境解讀"
        footer = "曾仕強教授易經思想體系"
        back = "回到決策之書"
        lang_switch = f'<span class="lang-switch"><a href="{BASE_URL}/cn/hexagram/" hreflang="zh-Hans" rel="alternate">简体中文</a></span>'
    else:
        title = "易经六十四卦｜曾仕强商业决策解读全索引"
        desc = "易经六十四卦完整索引：每卦的卦辞爻辞原文、商业与职场核心解读，基于曾仕强教授易经思想体系。"
        html_lang = "zh-Hans"
        url = f"{BASE_URL}/cn/hexagram/"
        home_label = "决策之书"
        idx_label = "六十四卦"
        h1 = "易经六十四卦"
        subtitle = "曾仕强教授易经思想体系 · 商业与职场双语境解读"
        footer = "曾仕强教授易经思想体系"
        back = "回到决策之书"
        lang_switch = f'<span class="lang-switch"><a href="{BASE_URL}/hexagram/" hreflang="zh-Hant" rel="alternate">繁體中文</a></span>'

    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "description": desc,
        "url": url,
        "inLanguage": html_lang,
    }, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="{html_lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<script type="application/ld+json">{ld}</script>
<style>
  :root {{
    --bg:#0f1115; --text:#e8e6e0; --text-strong:#f5f2ea; --muted:#8b8f98; --muted2:#5a5e68;
    --card:#171a22; --border:#2a2e3a; --accent:#c8a96a; --accent-hover:#d9ba7a;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{
      --bg:#faf8f4; --text:#3a3833; --text-strong:#22201c; --muted:#7a766d; --muted2:#aaa69c;
      --card:#ffffff; --border:#e5e0d5; --accent:#9a7b3f; --accent-hover:#7d6433;
    }}
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:var(--bg); color:var(--text); font-family:"PingFang TC","PingFang SC","Noto Sans TC","Noto Sans SC","Microsoft JhengHei",sans-serif; line-height:1.8; }}
  .container {{ max-width:900px; margin:0 auto; padding:48px 24px; }}
  .topbar {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; }}
  .breadcrumb {{ font-size:14px; color:var(--muted); }}
  .breadcrumb a {{ color:var(--accent); text-decoration:none; }}
  .lang-switch a {{ color:var(--muted); text-decoration:none; font-size:14px; border:1px solid var(--border); padding:4px 12px; border-radius:16px; }}
  .lang-switch a:hover {{ color:var(--accent); border-color:var(--accent); }}
  h1 {{ font-size:32px; margin-bottom:8px; color:var(--text-strong); }}
  .subtitle {{ color:var(--muted); font-size:15px; margin-bottom:40px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:12px; }}
  .grid a {{ display:block; background:var(--card); border:1px solid var(--border); color:var(--text); text-decoration:none; padding:16px; border-radius:10px; font-size:15px; transition:border-color .2s; }}
  .grid a:hover {{ border-color:var(--accent); color:var(--accent); }}
  .grid a .num {{ display:block; font-size:12px; color:var(--muted); letter-spacing:2px; margin-bottom:4px; }}
  footer {{ text-align:center; padding:24px; color:var(--muted2); font-size:13px; }}
  footer a {{ color:var(--muted); }}
</style>
  {ga_snippet}
</head>
<body>
<div class="container">
  <div class="topbar">
    <div class="breadcrumb"><a href="/">{home_label}</a> / {idx_label}</div>
    {lang_switch}
  </div>
  <h1>{h1}</h1>
  <p class="subtitle">{subtitle}</p>
  <div class="grid">
{items}
  </div>
</div>
<footer>
  <a href="/">{back}</a> · {footer}
</footer>
</body>
</html>"""


def build_sitemap(hexagrams):
    urls = [f"{BASE_URL}/", f"{BASE_URL}/hexagram/", f"{BASE_URL}/cn/hexagram/"]
    for h in hexagrams:
        urls.append(f"{BASE_URL}/hexagram/{h['number']}/")
        urls.append(f"{BASE_URL}/cn/hexagram/{h['number']}/")
    body = "\n".join(
        f"  <url>\n    <loc>{u}</loc>\n    <changefreq>weekly</changefreq>\n  </url>"
        for u in urls
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>"""


def main():
    hexagrams = parse_hexagrams()
    original = parse_original()
    interpretations = parse_interpretations()
    print(f"解析到 {len(hexagrams)} 个卦象, {len(original)} 条原文, {len(interpretations)} 条白话解读")
    if len(hexagrams) != 64:
        print("⚠️ 卦象数量不对")
        return

    # 相关卦：錯綜交互（易經正統關聯體系）
    # 錯卦=六爻全變 / 綜卦=上下顛倒 / 交卦=上下卦互換 / 互卦=2-4爻+3-5爻重組
    bin_map = {}
    for h in hexagrams:
        arr = original.get(int(h["number"]), {}).get("array")
        if arr:
            bin_map[tuple(arr)] = h["number"]

    def related_hexagrams(num):
        arr = original.get(num, {}).get("array")
        if not arr:
            return []
        rels = []
        seen = set()

        def add(rel_arr, label):
            target = bin_map.get(tuple(rel_arr))
            if target and int(target) != num and target not in seen:
                seen.add(target)
                rels.append((target, label))

        add([1 - x for x in arr], "錯卦")
        add(arr[::-1], "綜卦")
        add(arr[3:] + arr[:3], "交卦")
        add([arr[1], arr[2], arr[3], arr[2], arr[3], arr[4]], "互卦")
        return rels

    for i, hx in enumerate(hexagrams):
        n = hx["number"]
        num_int = int(n)
        orig = original.get(num_int)
        interp = interpretations.get(n, {})
        prev_num = hexagrams[i - 1]["number"] if i > 0 else None
        next_num = hexagrams[i + 1]["number"] if i < 63 else None

        # 相關卦（含關係標籤）
        num_to_hx = {h["number"]: h for h in hexagrams}
        related = []
        for rn, label in related_hexagrams(num_int):
            rh = num_to_hx.get(rn)
            if rh:
                related.append((rn, rh["tc"]["name"], rh["sc"]["name"], label))

        # 繁体页
        tc_dir = PUBLIC / "hexagram" / n
        tc_dir.mkdir(parents=True, exist_ok=True)
        (tc_dir / "index.html").write_text(page_html(hx, orig, interp, prev_num, next_num, "tc", related), encoding="utf-8")

        # 简体页
        sc_dir = PUBLIC / "cn" / "hexagram" / n
        sc_dir.mkdir(parents=True, exist_ok=True)
        (sc_dir / "index.html").write_text(page_html(hx, orig, interp, prev_num, next_num, "sc", related), encoding="utf-8")

        if num_int % 16 == 1:
            print(f"  ✓ 第{num_int}卦 {hx['tc']['name']}（繁+简）")

    (PUBLIC / "hexagram" / "index.html").write_text(index_html(hexagrams, "tc"), encoding="utf-8")
    (PUBLIC / "cn" / "hexagram" / "index.html").write_text(index_html(hexagrams, "sc"), encoding="utf-8")
    print("  ✓ 繁简索引页")

    (PUBLIC / "sitemap.xml").write_text(build_sitemap(hexagrams), encoding="utf-8")
    print(f"  ✓ sitemap.xml（{64*2+3} 个 URL）")
    print("\n完成！提交 git 后 Vercel 自动部署。")


if __name__ == "__main__":
    main()
