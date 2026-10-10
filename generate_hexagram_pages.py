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
import site_components

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "src" / "data" / "hexagrams.js"
ORIGINAL_FILE = ROOT / "src" / "data" / "iching_original.json"
# 繁体原文：权威源=ctext.org「周易」逐卦页（2026-10 建立，抽取配方见 decision-book-dev 技能）
ORIGINAL_TC_FILE = ROOT / "src" / "data" / "iching_original_tc.json"
INTERP_FILE = ROOT / "src" / "data" / "hexagram_interpretations.json"
# 简体版=LLM 语际转译（由 translate_interp_sc.py 产出；禁机翻铁律——不得用 opencc 等机械转换替代）
INTERP_SC_FILE = ROOT / "src" / "data" / "hexagram_interpretations_sc.json"
INSIGHT_GEN_FILE = ROOT / "src" / "data" / "insight_gen.json"
PUBLIC = ROOT / "public"
BASE_URL = "https://decision-book.vercel.app"


def parse_original():
    """读取原文数据（卦辞+爻辞），按卦序号索引"""
    data = json.loads(ORIGINAL_FILE.read_text(encoding="utf-8"))
    return {d["id"]: d for d in data}


def parse_original_tc():
    """读取繁体原文（ctext.org 权威源），按卦序号索引"""
    data = json.loads(ORIGINAL_TC_FILE.read_text(encoding="utf-8"))
    return {d["id"]: d for d in data}


def parse_interpretations():
    """读取白话解读（DeepSeek 生成），返回 {number: {meaning, career, advice}}"""
    if not INTERP_FILE.exists():
        return {}
    return json.loads(INTERP_FILE.read_text(encoding="utf-8"))


def parse_interpretations_sc():
    """读取简体白话解读（LLM 语际转译版，translate_interp_sc.py 产出）"""
    if not INTERP_SC_FILE.exists():
        return {}
    return json.loads(INTERP_SC_FILE.read_text(encoding="utf-8"))


def parse_insight_gen():
    """通用版一句话金句（分享文案用；与起卦展示同源）"""
    if not INSIGHT_GEN_FILE.exists():
        return {}
    data = json.loads(INSIGHT_GEN_FILE.read_text(encoding="utf-8"))
    return {int(d["id"]): d for d in data}


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
        "a": "適合事業與生意上的抉擇，例如合夥經營、用人帶人、定價取捨、轉型時機等情境。",
    },
    {
        "q": "如何獲得專屬於我的卦象解讀？",
        "a": "在決策之書輸入你的具體困惑即可免費起卦；起卦後，AI 會基於曾仕強教授易經思想體系，生成一份結合你情境的完整易經決策報告。",
    },
    {
        "q": "卦象解讀可以代替專業意見嗎？",
        "a": "易經解讀提供的是東方智慧視角與思考框架，重大商業或人生決策仍建議結合自身判斷與專業意見。",
    },
]

FAQ_SC = [
    {
        "q": "这个卦象适合问什么问题？",
        "a": "适合事业与生意上的抉择，例如合伙经营、用人带人、定价取舍、转型时机等情境。",
    },
    {
        "q": "如何获得专属于我的卦象解读？",
        "a": "在决策之书输入你的具体困惑即可免费起卦；起卦后，AI 会基于曾仕强教授易经思想体系，生成一份结合你情境的完整易经决策报告。",
    },
    {
        "q": "卦象解读可以代替专业意见吗？",
        "a": "易经解读提供的是东方智慧视角与思考框架，重大商业或人生决策仍建议结合自身判断与专业意见。",
    },
]


def parse_scenario_faq():
    """场景痛点 FAQ（第一页页群 B 方案；2026-10-07）→ {卦号int: value}"""
    p = ROOT / "src/data/scenario_faq.json"
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    return {int(k): v for k, v in data.items()}


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


# 第一页页群场景标题扩张（2026-10-07 Kyson 批准 A 方案）：非试点 20 卦
# 词均经 Google suggest 实测（2026-10-07）；配不上痛点的用通用尾部（31/63 无 kw2=不改 desc）
SEO_SCENARIO = {
    "24": {"tc": {"kw": "低谷期怎麼辦", "kw2": "低谷期"}, "sc": {"kw": "低谷期怎么办", "kw2": "低谷期"}},
    "63": {"tc": {"kw": "商業決策解讀"}, "sc": {"kw": "商业决策解读"}},
    "18": {"tc": {"kw": "公司管理混亂怎麼辦", "kw2": "管理混亂"}, "sc": {"kw": "公司管理混乱怎么办", "kw2": "管理混乱"}},
    "30": {"tc": {"kw": "人生迷茫怎麼辦", "kw2": "人生迷茫"}, "sc": {"kw": "人生迷茫怎么办", "kw2": "人生迷茫"}},
    "43": {"tc": {"kw": "猶豫不決怎麼辦", "kw2": "猶豫不決"}, "sc": {"kw": "犹豫不决怎么办", "kw2": "犹豫不决"}},
    "58": {"tc": {"kw": "嘴笨怎麼辦", "kw2": "不會說話"}, "sc": {"kw": "嘴笨怎么办", "kw2": "不会说话"}},
    "31": {"tc": {"kw": "商業決策解讀"}, "sc": {"kw": "商业决策解读"}},
    "15": {"tc": {"kw": "老實人吃虧怎麼辦", "kw2": "老實人吃虧"}, "sc": {"kw": "老实人吃亏怎么办", "kw2": "老实人吃亏"}},
    "8": {"tc": {"kw": "怎麼累積人脈", "kw2": "人脈"}, "sc": {"kw": "怎么积累人脉", "kw2": "人脉"}},
    "7": {"tc": {"kw": "怎麼帶團隊", "kw2": "帶團隊"}, "sc": {"kw": "怎么带团队", "kw2": "带团队"}},
    "57": {"tc": {"kw": "不會拒絕別人怎麼辦", "kw2": "不會拒絕"}, "sc": {"kw": "不会拒绝别人怎么办", "kw2": "不会拒绝"}},
}

# GA4 埋码（G-SGYWZGNCSH，2026-08-28 添加；2026-10-07 增 cta_click CTA 点击事件）
GA_SNIPPET = """  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-SGYWZGNCSH"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-SGYWZGNCSH');
  </script>
  <script>
  (function(){
    document.addEventListener('click', function(e){
      try {
        var a = e.target && e.target.closest ? e.target.closest('.cta-mini a, .cta a') : null;
        if (!a || !window.gtag) return;
        var c = a.closest('.cta-mini') || a.closest('.cta');
        var pos = (c && c.classList.contains('cta-mini')) ? 'mini' : 'bottom';
        var parts = location.pathname.split('hexagram/');
        var hx = parts.length > 1 ? (parseInt(parts[1], 10) || '') : '';
        gtag('event', 'cta_click', { pos: pos, hexagram: String(hx), page_lang: document.documentElement.lang || '' });
      } catch (err) {}
    }, true);
  })();
  </script>
"""

# 无图分享按钮（2026-09-18；2026-10-07 兜底链加固）：系统分享 → 剪贴板 → execCommand → 手动面板（消除全静默路径）；payload 只含 卦名+金句 与 本页链接
SHARE_TEMPLATE = """<div class="float-stack">
<button class="float-btn" id="shareBtn" type="button" title="@@TITLE@@" aria-label="@@LABEL@@">@@SHAREICON@@</button>
<button class="float-btn" id="topBtn" type="button" title="@@TOPTITLE@@" aria-label="@@TOPTITLE@@" style="display:none"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="6" y1="4.5" x2="18" y2="4.5"/><line x1="12" y1="19.5" x2="12" y2="9.5"/><polyline points="7.5 14 12 9.5 16.5 14"/></svg></button>
</div>
<script>
(function(){
  var shareBtn = document.getElementById("shareBtn");
  var topBtn = document.getElementById("topBtn");
  var SHARE_TEXT = @@TEXT@@, SHARE_URL = @@URL@@;
  var SHARE_ICON = @@SHAREICONJS@@, COPIED_ICON = @@COPIEDICONJS@@;
  var copiedT = null;
  var toastT = null;
  function onScroll(){ topBtn.style.display = (window.scrollY > 600) ? "flex" : "none"; }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  topBtn.addEventListener("click", function(){ window.scrollTo({ top: 0, behavior: "smooth" }); });
  function showToast(){
    var old = document.getElementById("shareToast");
    if (old && old.parentNode) old.parentNode.removeChild(old);
    var el = document.createElement("div");
    el.id = "shareToast";
    el.textContent = @@COPIEDTIP@@;
    el.style.cssText = "position:fixed;left:50%;transform:translateX(-50%);bottom:122px;z-index:98;background:var(--card);border:1px solid var(--accent-border2);color:var(--text);border-radius:20px;padding:8px 16px;font-size:13px;line-height:1.5;box-shadow:0 6px 20px rgba(0,0,0,.28);max-width:86vw;text-align:center;";
    document.body.appendChild(el);
    if (toastT) clearTimeout(toastT);
    toastT = setTimeout(function(){ if (el.parentNode) el.parentNode.removeChild(el); }, 2400);
  }
  function setCopied(){
    shareBtn.innerHTML = COPIED_ICON;
    if (copiedT) clearTimeout(copiedT);
    copiedT = setTimeout(function(){ shareBtn.innerHTML = SHARE_ICON; }, 2500);
    showToast();
  }
  function trackShare(method){
    if (window.gtag) { try { gtag("event", "share", { method: method }); } catch(e){} }
  }
  function legacyCopy(text){
    try {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.cssText = "position:fixed;top:-1000px;opacity:0;";
      document.body.appendChild(ta);
      ta.select();
      ta.setSelectionRange(0, ta.value.length);
      var ok = document.execCommand("copy");
      document.body.removeChild(ta);
      return ok;
    } catch(e){ return false; }
  }
  function showManual(){
    var old = document.getElementById("shareManual");
    if (old && old.parentNode) old.parentNode.removeChild(old);
    var d = document.createElement("div");
    d.id = "shareManual";
    d.style.cssText = "position:fixed;left:14px;right:14px;bottom:76px;z-index:99;background:var(--card);border:1px solid var(--accent-border2);border-radius:12px;padding:14px 16px;box-shadow:0 10px 30px rgba(0,0,0,.25);font-size:14px;color:var(--text);line-height:1.8;";
    var tip = document.createElement("div");
    tip.style.cssText = "color:var(--accent);font-size:13px;margin-bottom:6px;";
    tip.textContent = @@MANUALTIP@@;
    var body = document.createElement("div");
    body.style.cssText = "white-space:pre-wrap;word-break:break-all;-webkit-user-select:text;user-select:text;";
    body.textContent = SHARE_TEXT + "\\n" + SHARE_URL;
    var close = document.createElement("button");
    close.type = "button";
    close.textContent = @@CLOSELABEL@@;
    close.style.cssText = "margin-top:10px;border:1px solid var(--border);background:transparent;color:var(--muted);border-radius:16px;padding:4px 14px;font-size:13px;cursor:pointer;";
    close.addEventListener("click", function(){ d.parentNode.removeChild(d); });
    d.appendChild(tip); d.appendChild(body); d.appendChild(close);
    document.body.appendChild(d);
    trackShare("manual");
  }
  function fallbackCopy(){
    var text = SHARE_TEXT + "\\n" + SHARE_URL;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function(){
        setCopied();
        trackShare("copy_link");
      }).catch(function(){
        if (legacyCopy(text)) { setCopied(); trackShare("copy_link"); }
        else { showManual(); }
      });
    } else if (legacyCopy(text)) {
      setCopied();
      trackShare("copy_link");
    } else {
      showManual();
    }
  }
  shareBtn.addEventListener("click", function(){
    if (navigator.share) {
      try {
        var p = navigator.share({ text: SHARE_TEXT, url: SHARE_URL });
        if (p && typeof p.then === "function") {
          p.then(function(){ trackShare("native"); }).catch(function(err){
            if (err && err.name === "AbortError") return;
            fallbackCopy();
          });
          return;
        }
        trackShare("native");
        return;
      } catch(e) {
        /* 同步抛错（部分 WebView 禁用分享）：落入复制兜底 */
      }
    }
    fallbackCopy();
  });
})();
</script>"""


def share_js_str(value):
    """安全嵌入 <script> 的 JS 字符串字面量（json.dumps + 转义 <）"""
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")


# 悬浮按钮图标（stroke=currentColor 继承按钮颜色；分享=三节点连线·Android 风，2026-09-18 Kyson 选定）
SHARE_ICON_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>'
CHECK_ICON_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>' 




def page_html(hx, orig, interp, prev_num, next_num, lang="tc", related=None, insight_gen=None, scenario_faq=None):
    """单个卦象页。lang: tc=繁体 / sc=简体
    related: [(num, tc_name, sc_name), ...] 相关卦列表（同上卦）
    insight_gen: {int_id: {sc, tc}} 通用版金句（分享文案用）"""
    n = hx["number"]
    is_tc = lang == "tc"
    name = hx["tc"]["name"] if is_tc else hx["sc"]["name"]
    insight = hx["tc"]["insight"] if is_tc else hx["sc"]["insight"]
    num_label = f"第 {int(n)} 卦"

    # 无图分享（2026-09-18）：文案=卦名+通用版金句（insight_gen 与起卦展示同源）；链接=本页 canonical
    _ig = (insight_gen or {}).get(int(n), {})
    share_insight = (_ig.get("tc") if is_tc else _ig.get("sc")) or insight
    share_text = f"{name}：{share_insight}"
    share_label = "分享這卦" if is_tc else "分享这卦"
    share_title = "分享這卦（只含卦名與金句）" if is_tc else "分享这卦（只含卦名与金句）"
    top_title = "回到頂部" if is_tc else "回到顶部"
    manual_tip = "長按選取以下文字複製，即可分享：" if is_tc else "长按选取以下文字复制，即可分享："
    close_label = "關閉" if is_tc else "关闭"
    copied_tip = "已複製，貼到 LINE／微信即可分享" if is_tc else "已复制，粘贴到微信／LINE 即可分享"

    # 白话解读（按语言直接取数据：tc=繁版 / sc=LLM 语际转译版；禁机翻铁律——运行时不机翻）
    interp_text = interp if interp else {"meaning": "", "career": "", "advice": ""}

    # 页群场景标题（2026-10-07 A 方案；2026-10-10 职场场景词清理后仅保留商业/通用项）
    seo = SEO_SCENARIO.get(str(int(n)), {})

    if is_tc:
        title = f"{name}卦｜第{int(n)}卦｜曾仕強易經商業決策解讀"
        desc = f"{name}卦在商業決策上代表什麼？{insight}卦辭爻辭原文白話釋義、商業決策啟示一次看懂，幫你看清當下該怎麼走。"
        if seo:
            p = seo["tc"]
            title = f"{name}卦是什麼意思？{p['kw']}"
            if p.get("kw2"):
                desc = f"{name}卦是什麼意思？{insight}卦辭爻辭原文白話、遇到{p['kw2']}時的商業決策啟示。想看清自己的處境，免費起一卦對照看看。"
        html_lang = "zh-Hant"
        url = f"{BASE_URL}/hexagram/{n}/"
        alt_url = f"{BASE_URL}/cn/hexagram/{n}/"
        home = "/"
        idx_link = "/hexagram/"
        prev_label = "← 上一卦"
        next_label = "下一卦 →"
        all_label = "全部六十四卦"
        breadcrumb_home = "決策之書"
        insight_label = "核心解讀"
        cta_h2 = "你正在面對類似的商業抉擇嗎？"
        cta_p = "免費起卦，看看你的處境對應哪一卦；完整行動方案，起卦後即可免費查看。"
        cta_btn = "免費起卦 →"
        cta_mini_text = "你的困惑，也可以起一卦看看"
        orig_label = "《易經》原文"
        gua_label = "卦辭"
        yao_label = "爻辭"
        scripture_note = "原文出自《周易》，公版內容。"
        subtitle_line = "曾仕強易經思想體系 · 商業決策解讀"
        faq_heading = "常見問題"
        related_label = "相關卦象"
        interp_labels = ["白話釋義", "商業決策啟示", "行動建議"]
    else:
        title = f"{name}卦｜第{int(n)}卦｜曾仕强易经商业决策解读"
        desc = f"{name}卦在商业决策上代表什么？{insight}卦辞爻辞原文白话释义、商业决策启示一次看懂，帮你看清当下该怎么走。"
        if seo:
            p = seo["sc"]
            title = f"{name}卦是什么意思？{p['kw']}"
            if p.get("kw2"):
                desc = f"{name}卦是什么意思？{insight}卦辞爻辞原文白话、遇到{p['kw2']}时的商业决策启示。想看清自己的处境，免费起一卦对照看看。"
        html_lang = "zh-Hans"
        url = f"{BASE_URL}/cn/hexagram/{n}/"
        alt_url = f"{BASE_URL}/hexagram/{n}/"
        home = "/cn/"
        idx_link = "/cn/hexagram/"
        prev_label = "← 上一卦"
        next_label = "下一卦 →"
        all_label = "全部六十四卦"
        breadcrumb_home = "决策之书"
        insight_label = "核心解读"
        cta_h2 = "你正在面对类似的商业抉择吗？"
        cta_p = "免费起卦，看看你的处境对应哪一卦；完整行动方案，起卦后即可免费查看。"
        cta_btn = "免费起卦 →"
        cta_mini_text = "你的困惑，也可以起一卦看看"
        orig_label = "《易经》原文"
        gua_label = "卦辞"
        yao_label = "爻辞"
        scripture_note = "原文出自《周易》，公版内容。"
        subtitle_line = "曾仕强易经思想体系 · 商业决策解读"
        faq_heading = "常见问题"
        related_label = "相关卦象"
        interp_labels = ["白话释义", "商业决策启示", "行动建议"]

    faq_items = FAQ_TC if is_tc else FAQ_SC
    # 场景痛点 FAQ（第一页页群 B 方案；2026-10-07）——问题取自标题同源场景词
    if scenario_faq:
        _sf = scenario_faq.get(int(n), {}).get("tc" if is_tc else "sc")
        if _sf:
            faq_items = faq_items + [{"q": _sf["q"], "a": _sf["a"]}]
    faq_lines = "\n".join(
        f'<div class="faq-item"><div class="faq-q">{item["q"]}</div><div class="faq-a">{item["a"]}</div></div>'
        for item in faq_items
    )

    prev_link = f'<a href="{idx_link}{prev_num}/" class="nav-link">{prev_label}</a>' if prev_num else '<span class="nav-link muted">首卦</span>'
    next_link = f'<a href="{idx_link}{next_num}/" class="nav-link">{next_label}</a>' if next_num else '<span class="nav-link muted">末卦</span>'

    # 语言切换链接
    if is_tc:
        switch_href = f"/cn/hexagram/{n}/"
    else:
        switch_href = f"/hexagram/{n}/"

    # 原文
    scripture_html = ""
    if orig:
        scripture_html += f'<p class="gua-ci">{orig.get("scripture","")}</p>'
        lines_html = ""
        for line in orig.get("lines", []):
            lines_html += f'<div class="yao-line"><span class="yao-name">{line["name"]}</span><span class="yao-text">{line["scripture"]}</span></div>'
        scripture_html += lines_html

    # 白话解读区块（DeepSeek 生成）
    # 策略：释义全量展示；启示段截为2句引子；行动建议不上页面（付费产品核心价值）
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
            r_label = rlabel[0] if is_tc else rlabel[1]
            rel_links.append(f'<a href="{idx_link}{rn}/"><span class="rel-name">{r_name}</span><span class="rel-tag">{r_label}</span></a>')
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

    # 分享按钮片段（本页 canonical + 卦名金句；payload 禁含其他数据）
    share_html = (
        SHARE_TEMPLATE
        .replace("@@TEXT@@", share_js_str(share_text))
        .replace("@@URL@@", share_js_str(url))
        .replace("@@TITLE@@", share_title)
        .replace("@@TOPTITLE@@", top_title)
        .replace("@@MANUALTIP@@", share_js_str(manual_tip))
        .replace("@@CLOSELABEL@@", share_js_str(close_label))
        .replace("@@COPIEDTIP@@", share_js_str(copied_tip))
        .replace("@@SHAREICONJS@@", share_js_str(SHARE_ICON_SVG))
        .replace("@@COPIEDICONJS@@", share_js_str(CHECK_ICON_SVG))
        .replace("@@LABEL@@", share_label)
        .replace("@@SHAREICON@@", SHARE_ICON_SVG)
    )

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
  /* 三栏目常驻导航（2026-10-08）：提问｜易经｜笔记 */
  .site-nav {{ position:sticky; top:0; z-index:40; background:rgba(15,17,21,.86); -webkit-backdrop-filter:blur(12px) saturate(1.6); backdrop-filter:blur(12px) saturate(1.6); border-bottom:1px solid var(--border); }}
  .site-nav-inner {{ max-width:900px; margin:0 auto; padding:0 24px; height:48px; display:flex; align-items:center; justify-content:center; gap:36px; position:relative; }}
  .site-nav a.nav-item {{ color:var(--muted); text-decoration:none; font-size:14px; letter-spacing:3px; padding:6px 2px; transition:color .2s; }}
  .site-nav a.nav-item:hover {{ color:var(--accent); }}
  .site-nav a.nav-item.active {{ color:var(--accent); font-weight:700; text-decoration:underline; text-underline-offset:6px; text-decoration-thickness:2px; }}
  .site-nav .lang-switch {{ position:absolute; right:24px; top:50%; transform:translateY(-50%); font-weight:400; font-size:12.5px; color:var(--muted); letter-spacing:0; text-decoration:none; border:1px solid var(--border); border-radius:6px; padding:3px 10px; }}
  .site-nav .lang-switch:hover {{ color:var(--accent); border-color:var(--accent); }}
  @media (prefers-color-scheme: light) {{ .site-nav {{ background:rgba(250,248,244,.86); }} }}
  @media (max-width:640px) {{ .site-nav-inner {{ padding:0 16px; gap:22px; }} .site-nav .lang-switch {{ right:16px; }} .site-nav a.nav-item {{ letter-spacing:2px; }} }}

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
  /* 悬浮按钮组：分享 + 回到顶部（符号型，2026-09-18 Kyson 定） */
  .float-stack {{ position:fixed; right:16px; bottom:16px; z-index:50; display:flex; flex-direction:column; align-items:flex-end; gap:10px; }}
  .float-btn {{ width:44px; height:44px; border-radius:50%; background:var(--card); border:1px solid var(--border); color:var(--muted); cursor:pointer; display:flex; align-items:center; justify-content:center; font-size:17px; font-family:inherit; box-shadow:0 4px 14px rgba(0,0,0,.12); transition:all .2s; padding:0; }}
  .float-btn:hover {{ border-color:var(--accent); color:var(--accent); }}
  .float-btn svg {{ display:block; }}
  /* 相关卦象 */
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
  footer .f-links {{ margin-bottom:4px; }}
  footer .f-links a {{ color:var(--muted); text-decoration:none; }}
  footer .f-links a:hover {{ color:var(--accent); }}
  footer .f-brand {{ margin-top:6px; }}
  /* 六爻卦象图（Hero 视觉焦点） */
  .hexagram-visual {{ display:flex; align-items:center; justify-content:center; gap:32px; margin-bottom:32px; padding:32px 28px; background:linear-gradient(135deg,var(--card),var(--card2)); border:1px solid var(--accent-border2); border-radius:16px; box-shadow:0 6px 24px rgba(0,0,0,.06); }}
  .hexagram-lines {{ display:flex; flex-direction:column; gap:7px; }}
  .hexagram-lines .line {{ display:flex; align-items:center; gap:10px; }}
  .hexagram-lines .bar {{ display:block; height:12px; border-radius:3px; background:var(--text-strong); }}
  .hexagram-lines .bar.yang {{ width:160px; }}
  .hexagram-lines .bar.yin {{ display:flex; justify-content:space-between; width:160px; background:transparent; }}
  .hexagram-lines .bar.yin .yin-seg {{ width:43.75%; height:100%; background:var(--text-strong); border-radius:3px; }}
  .hexagram-lines .yao-name {{ font-size:12px; color:var(--muted); width:28px; }}
  .hexagram-side {{ flex:0 0 auto; }}
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
    .hexagram-lines .yao-name {{ font-size:10px; width:22px; }}
    .hexagram-side .tri-label {{ font-size:11px; margin-bottom:3px; }}
    .hexagram-side .gua-name {{ font-size:22px; margin-bottom:4px; }}
    .cta-mini {{ flex-wrap:wrap; margin:16px 0 28px; }}
    .cta-mini a {{ flex:1; text-align:center; padding:12px 16px; font-size:16px; }}
    .cta a.btn {{ display:block; width:100%; padding:14px 0; font-size:17px; }}
    .float-stack {{ right:12px; bottom:12px; gap:8px; }}
    .float-btn {{ width:40px; height:40px; }}
  }}
</style>
  {ga_snippet}
 </head>
 <body>
{site_components.nav_html(lang, 'hex', switch_href)}
<div class="container">
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
{site_components.footer_html(lang, 'hexpage')}
{share_html}
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
        desc = "易經六十四卦完整索引：每卦的卦辭爻辭原文、商業決策核心解讀，基於曾仕強教授易經思想體系。"
        html_lang = "zh-Hant"
        url = f"{BASE_URL}/hexagram/"
        h1 = "易經六十四卦"
        subtitle = "曾仕強教授易經思想體系 · 商業決策解讀"
        switch_href = "/cn/hexagram/"
    else:
        title = "易经六十四卦｜曾仕强商业决策解读全索引"
        desc = "易经六十四卦完整索引：每卦的卦辞爻辞原文、商业决策核心解读，基于曾仕强教授易经思想体系。"
        html_lang = "zh-Hans"
        url = f"{BASE_URL}/cn/hexagram/"
        h1 = "易经六十四卦"
        subtitle = "曾仕强教授易经思想体系 · 商业决策解读"
        switch_href = "/hexagram/"

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
  /* 三栏目常驻导航（2026-10-08）：提问｜易经｜笔记 */
  .site-nav {{ position:sticky; top:0; z-index:40; background:rgba(15,17,21,.86); -webkit-backdrop-filter:blur(12px) saturate(1.6); backdrop-filter:blur(12px) saturate(1.6); border-bottom:1px solid var(--border); }}
  .site-nav-inner {{ max-width:900px; margin:0 auto; padding:0 24px; height:48px; display:flex; align-items:center; justify-content:center; gap:36px; position:relative; }}
  .site-nav a.nav-item {{ color:var(--muted); text-decoration:none; font-size:14px; letter-spacing:3px; padding:6px 2px; transition:color .2s; }}
  .site-nav a.nav-item:hover {{ color:var(--accent); }}
  .site-nav a.nav-item.active {{ color:var(--accent); font-weight:700; text-decoration:underline; text-underline-offset:6px; text-decoration-thickness:2px; }}
  .site-nav .lang-switch {{ position:absolute; right:24px; top:50%; transform:translateY(-50%); font-weight:400; font-size:12.5px; color:var(--muted); letter-spacing:0; text-decoration:none; border:1px solid var(--border); border-radius:6px; padding:3px 10px; }}
  .site-nav .lang-switch:hover {{ color:var(--accent); border-color:var(--accent); }}
  @media (prefers-color-scheme: light) {{ .site-nav {{ background:rgba(250,248,244,.86); }} }}
  @media (max-width:640px) {{ .site-nav-inner {{ padding:0 16px; gap:22px; }} .site-nav .lang-switch {{ right:16px; }} .site-nav a.nav-item {{ letter-spacing:2px; }} }}
  h1 {{ font-size:32px; margin-bottom:8px; color:var(--text-strong); }}
  .subtitle {{ color:var(--muted); font-size:15px; margin-bottom:40px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:12px; }}
  .grid a {{ display:block; background:var(--card); border:1px solid var(--border); color:var(--text); text-decoration:none; padding:16px; border-radius:10px; font-size:15px; transition:border-color .2s; }}
  .grid a:hover {{ border-color:var(--accent); color:var(--accent); }}
  .grid a .num {{ display:block; font-size:12px; color:var(--muted); letter-spacing:2px; margin-bottom:4px; }}
  footer {{ text-align:center; padding:24px; color:var(--muted2); font-size:13px; }}
  footer a {{ color:var(--muted); }}
  footer .f-links {{ margin-bottom:4px; }}
  footer .f-links a {{ color:var(--muted); text-decoration:none; }}
  footer .f-links a:hover {{ color:var(--accent); }}
  footer .f-brand {{ margin-top:6px; }}
</style>
  {ga_snippet}
</head>
<body>
{site_components.nav_html(lang, 'hex', switch_href)}
<div class="container">
  <h1>{h1}</h1>
  <p class="subtitle">{subtitle}</p>
  <div class="grid">
{items}
  </div>
</div>
{site_components.footer_html(lang, 'hexindex')}
</body>
</html>"""


def build_sitemap(hexagrams):
    urls = [f"{BASE_URL}/", f"{BASE_URL}/hexagram/", f"{BASE_URL}/cn/hexagram/"]
    for _p in ("about", "privacy", "disclaimer"):
        urls.append(f"{BASE_URL}/{_p}/")
        urls.append(f"{BASE_URL}/cn/{_p}/")
    for h in hexagrams:
        urls.append(f"{BASE_URL}/hexagram/{h['number']}/")
        urls.append(f"{BASE_URL}/cn/hexagram/{h['number']}/")
    body = "\n".join(
        f"  <url>\n    <loc>{u}</loc>\n    <changefreq>weekly</changefreq>\n  </url>"
        for u in urls
    )
    # 保留既有 blog 条目（由 generate_blog_pages.py 维护；单独重跑本脚本时不可丢失）
    blog_blocks = ""
    sm_path = PUBLIC / "sitemap.xml"
    if sm_path.exists():
        import re as _re
        old = sm_path.read_text(encoding="utf-8")
        blocks = _re.findall(r"<url>\s*<loc>[^<]*/blog/[^<]*</loc>[\s\S]*?</url>", old)
        seen, kept = set(), []
        for b in blocks:
            loc = _re.search(r"<loc>([^<]+)</loc>", b)
            k = loc.group(1) if loc else b
            if k not in seen:
                seen.add(k)
                kept.append(b)
        if kept:
            blog_blocks = "\n" + "\n".join("  " + b for b in kept)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}{blog_blocks}
</urlset>"""


def main():
    hexagrams = parse_hexagrams()
    original = parse_original()
    original_tc = parse_original_tc()
    interpretations = parse_interpretations()
    interpretations_sc = parse_interpretations_sc()
    insight_gen = parse_insight_gen()
    scenario_faq = parse_scenario_faq()
    print(f"解析到 {len(hexagrams)} 个卦象, {len(original)}+{len(original_tc)} 条原文（简+繁）, {len(interpretations)} 条白话解读")
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

        add([1 - x for x in arr], ("錯卦", "错卦"))
        add(arr[::-1], ("綜卦", "综卦"))
        add(arr[3:] + arr[:3], ("交卦", "交卦"))
        add([arr[1], arr[2], arr[3], arr[2], arr[3], arr[4]], ("互卦", "互卦"))
        return rels

    for i, hx in enumerate(hexagrams):
        n = hx["number"]
        num_int = int(n)
        orig = original.get(num_int)
        interp = interpretations.get(n, {})
        interp_sc = interpretations_sc.get(n, {})
        prev_num = hexagrams[i - 1]["number"] if i > 0 else None
        next_num = hexagrams[i + 1]["number"] if i < 63 else None

        # 相關卦（含關係標籤）
        num_to_hx = {h["number"]: h for h in hexagrams}
        related = []
        for rn, label in related_hexagrams(num_int):
            rh = num_to_hx.get(rn)
            if rh:
                related.append((rn, rh["tc"]["name"], rh["sc"]["name"], label))

        # 繁体页（原文用 ctext.org 繁体权威源）
        orig_tc = original_tc.get(num_int)
        tc_dir = PUBLIC / "hexagram" / n
        tc_dir.mkdir(parents=True, exist_ok=True)
        (tc_dir / "index.html").write_text(page_html(hx, orig_tc, interp, prev_num, next_num, "tc", related, insight_gen, scenario_faq=scenario_faq), encoding="utf-8")

        # 简体页
        sc_dir = PUBLIC / "cn" / "hexagram" / n
        sc_dir.mkdir(parents=True, exist_ok=True)
        (sc_dir / "index.html").write_text(page_html(hx, orig, interp_sc, prev_num, next_num, "sc", related, insight_gen, scenario_faq=scenario_faq), encoding="utf-8")

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
