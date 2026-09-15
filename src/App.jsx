import { useState, useEffect, useCallback } from 'react';
import { Analytics, track } from '@vercel/analytics/react';
import { SpeedInsights } from '@vercel/speed-insights/react';
import HEXAGRAMS from './data/hexagrams';
import ORIGINALS from './data/hexagram_originals.json';
import INSIGHT_GEN from './data/insight_gen.json';
import { generateHexagramIndex } from './lib/seed';
import Paywall from './components/Paywall';

// 卦号归一化匹配：hexagrams.js 用 "01" 格式、数据文件用 1 格式，String(1)≠String("01")
const numKey = (v) => String(Number(v));

// 示例问题与 FAQ（2026-09-15 借鉴对标 tarotap 首页）：降低启动门槛 + 期望管理
const EXAMPLES = {
  tc: [
    "主管帶頭排擠我，重要項目都不讓我碰，該忍還是該走？",
    "拿到兩個 offer：一個錢多但加班嚴重，一個錢少但穩定，該怎麼選？",
    "在職十二年，想辭職做自己的生意，但家人反對，該不該賭一把？",
  ],
  sc: [
    "领导带头排挤我，重要项目都不让我碰，该忍还是该走？",
    "拿到两个 offer：一个钱多但加班严重，一个钱少但稳定，该怎么选？",
    "在职十二年，想辞职做自己的生意，但家人反对，该不该赌一把？",
  ],
};
const FAQ = {
  tc: [
    { q: "卦能預測未來嗎？", a: "不能。卦不是算盤，它不預測吉凶，只是把你自己看不清的處境翻給你看——答案，始終在你手上。" },
    { q: "可以對同一問題重複起卦嗎？", a: "不建議。卦反映的是當下處境；短時間反覆問同一件事，只會讓自己更亂。處境真的變了，再起一卦。" },
    { q: "報告能代替專業意見嗎？", a: "不能。醫療、法律、投資等專業問題，請諮詢持牌專業人士。本工具僅供決策思考參考。" },
    { q: "為什麼要選擇地區？", a: "職場規則、社會保障、人情壓力因地而異。報告會結合你所在地區，給出更貼近現實的建議。" },
  ],
  sc: [
    { q: "卦能预测未来吗？", a: "不能。卦不是算盘，它不预测吉凶，只是把你自己看不清的处境翻给你看——答案，始终在你手上。" },
    { q: "可以对同一问题重复起卦吗？", a: "不建议。卦反映的是当下处境；短时间反复问同一件事，只会让自己更乱。处境真的变了，再起一卦。" },
    { q: "报告能代替专业意见吗？", a: "不能。医疗、法律、投资等专业问题，请咨询持牌专业人士。本工具仅供决策思考参考。" },
    { q: "为什么要选择地区？", a: "职场规则、社会保障、人情压力因地而异。报告会结合你所在地区，给出更贴近现实的建议。" },
  ],
};
// 博客精选（2026-09-15 借鉴对标：首页直达内容，降低发现门槛）
const BLOG_POSTS = {
  tc: [
    { title: "易經到底是不是用來算命的？", desc: "從「善易者不卜」說起——它不是水晶球，是一套看清處境的方法。", href: "/blog/is-i-ching-fortune-telling/" },
    { title: "為什麼同一個問題，每個人抽到的卦不一樣？", desc: "同題不同卦，恰恰說明它照的是處境，不是答案。", href: "/blog/why-different-hexagram/" },
    { title: "問卦之前，先把這三件事想清楚", desc: "處境、選項、最在意什麼——問題寫清楚，報告才有用。", href: "/blog/how-to-ask/" },
  ],
  sc: [
    { title: "易经到底是不是用来算命的？", desc: "从「善易者不卜」说起——它不是水晶球，是一套看清处境的方法。", href: "/cn/blog/is-i-ching-fortune-telling/" },
    { title: "为什么同一个问题，每个人抽到的卦不一样？", desc: "同题不同卦，恰恰说明它照的是处境，不是答案。", href: "/cn/blog/why-different-hexagram/" },
    { title: "问卦之前，先把这三件事想清楚", desc: "处境、选项、最在意什么——问题写清楚，报告才有用。", href: "/cn/blog/how-to-ask/" },
  ],
};

export default function App() {
  const [prefilled] = useState(() => {
    // 支持 ?q= 预填问题（来自卦页「真實職場提問」卡片的引导链接）
    try {
      const params = new URLSearchParams(window.location.search);
      return params.get("q") || "";
    } catch {
      return "";
    }
  });
  const [question, setQuestion] = useState(prefilled);
  // 语言由 URL 驱动（2026-09-14 全局语言切换重构）：/ = 繁體、/cn/ = 简体；切换=页面跳转（SEO 干净）
  const INIT_CN = typeof window !== "undefined" && window.location.pathname.startsWith("/cn");
  // 地区档位（2026-09-14 定稿）：文化距离圈内单列 + 圈外按华裔体量列；排序=用户体量。
  // 与语言完全独立；localStorage 记忆（切语言往返后保住选择）。
  const REGIONS = ["中国大陆", "港澳台", "东南亚", "日韩", "北美", "欧洲", "澳洲/新西兰", "其他地区"];
  // 繁体页面显示用标签（值恒为简体，与 Dify 端档位对齐）
  const TC_REGION_LABELS = { "中国大陆": "中國大陸", "东南亚": "東南亞", "日韩": "日韓", "欧洲": "歐洲", "澳洲/新西兰": "澳洲/紐西蘭", "其他地区": "其他地區" };
  const [region, setRegion] = useState(() => {
    if (typeof window === "undefined") return INIT_CN ? "中国大陆" : "港澳台";
    try {
      const saved = window.localStorage.getItem("db_region");
      if (saved && REGIONS.includes(saved)) return saved;
    } catch {}
    return INIT_CN ? "中国大陆" : "港澳台";
  });
  const changeRegion = (v) => {
    setRegion(v);
    try { window.localStorage.setItem("db_region", v); } catch {}
  };
  const [hexagram, setHexagram] = useState(null);
  // 会话内解锁一次即生效：新问题不再要求重新付费
  // 付费墙暂停（2026-09-14）：首卦体验免费，报告直接生成。
  // 恢复：改回 useState(false)。付费墙未来接入 Ko-fi（追问付费时再启用）。
  const [unlocked, setUnlocked] = useState(true);
  const [report, setReport] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  const lang = INIT_CN ? "sc" : "tc";
  // 浏览器标签标题跟随语言（/ 繁体站、/cn/ 简体站各自显示对应标题）
  useEffect(() => {
    document.title = lang === "tc" ? "決策之書 · 易經職場與商業決策助手" : "决策之书 · 易经职场与商业决策助手";
  }, [lang]);
  const switchLang = () => {
    window.location.href = lang === "tc" ? "/cn/" : "/";
  };
  // 回顶部浮动按钮（长报告页场景）：滚过 600px 后出现
  const [showTop, setShowTop] = useState(false);
  useEffect(() => {
    const onScroll = () => setShowTop(window.scrollY > 600);
    onScroll(); // 挂载时先跑一次：刷新恢复滚动位置时按钮也可立即显示
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const fetchReport = useCallback(async (q, reg, hex) => {
    setGenerating(true);
    setError(null);
    try {
      let data = null;
      // 工作流失败自动重试一次（Dify 云端偶发瞬时失败：模型连接重置/插件抖动）
      for (let attempt = 0; attempt < 2; attempt++) {
        const response = await fetch('/api/dify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            inputs: {
              User_Question: q,
              Region: reg,
              Language: lang === "tc" ? "繁體中文" : "简体中文",
              Hexagram_Name: hex["sc"].name
            },
            response_mode: "blocking",
            user: "web_user_" + Date.now()
          })
        });
        data = await response.json();
        const out = data?.data?.outputs;
        if (out?.Report || out?.text || out?.answer) break;
        if (attempt === 0 && data?.data?.status === "failed") continue; // 重试
        break;
      }

      let text = data?.data?.outputs?.Report || data?.data?.outputs?.text || data?.data?.outputs?.answer;
      if (text) {
        // 剥离推理段（DeepSeek reasoning 会混入输出；实测单次最长 6K+ 字）
        text = text.replace(/<think\b[^>]*>[\s\S]*?<\/think\s*>\s*/gi, ''); // ① 成对标签（容忍大小写/空格变体）
        text = text.replace(/<!--\s*dify-deepseek-reasoning\s*-->/gi, ''); // ② Dify 推理注释标记
        if (/<think/i.test(text)) {
          // ③ 兜底：未闭合（输出截断）→ 从【最后一个】正式抬头处截取（think 内引用的模板在更早位置）
          const last = Math.max(text.lastIndexOf('【決策之書'), text.lastIndexOf('【决策之书'));
          if (last > 0) text = text.slice(last);
        }
        text = text.trim();
        setReport(text);
      } else if (data?.code === "invalid_param") {
        // 参数类错误（如问题超长）：显示服务端原因，人话化
        const m = (data?.message || "").match(/less than (\d+)/);
        setError(
          m
            ? (lang === "tc" ? `⚠️ 問題太長，請精簡到 ${m[1]} 字以內再生成。` : `⚠️ 问题太长，请精简到 ${m[1]} 字以内再生成。`)
            : (lang === "tc" ? `⚠️ 請求參數有誤：${data?.message || ""}` : `⚠️ 请求参数有误：${data?.message || ""}`)
        );
      } else {
        setError(lang === "tc" ? "⚠️ 生成服務暫時不穩，請稍等片刻再點一次「生成」。" : "⚠️ 生成服务暂时不稳，请稍等片刻再点一次「生成」。");
      }
    } catch {
      setError(lang === "tc" ? "系統繁忙，請稍後重試。" : "系统繁忙，请稍后重试。");
    } finally {
      setGenerating(false);
    }
  }, [lang]);

  const handleGenerate = () => {
    if (!question.trim()) {
      return alert(lang === "tc" ? "請輸入具體問題" : "请输入具体问题");
    }
    const index = generateHexagramIndex(question);
    const result = HEXAGRAMS[index];
    setHexagram(result);
    // 新问题：清空旧报告，进入生成中状态
    setReport(null);
    setError(null);

    track('hexagram_generated', {
      hexagram: result.number,
      region,
      questionLength: question.length
    });

    // 会话内已解锁：自动生成新报告，不再显示支付墙
    if (unlocked) {
      fetchReport(question, region, result);
    }
  };

  const handleUnlock = async (password) => {
    track('unlock_attempted', { hexagram: hexagram?.number });

    if (password.trim() !== "AURA-888") {
      track('unlock_failed', { reason: 'wrong_password' });
      alert(lang === "tc" ? "密碼驗證失敗，請確認購買後的感謝信內容。" : "密码验证失败，请确认购买后的感谢信内容。");
      return false;
    }
    track('unlock_success');
    setUnlocked(true);
    fetchReport(question, region, hexagram);
    return true;
  };

  const handleRetry = () => {
    if (hexagram) fetchReport(question, region, hexagram);
  };

  // 预填问题自动起卦（付费解码仍由用户手动操作）
  useEffect(() => {
    if (prefilled.trim()) {
      const index = generateHexagramIndex(prefilled);
      const result = HEXAGRAMS[index];
      setHexagram(result);
      track('hexagram_generated', {
        hexagram: result.number,
        region,
        questionLength: prefilled.length,
        source: 'question_card'
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-dvh bg-[#FAFAFA] dark:bg-[#0F1115] text-[#333333] dark:text-[#E8E6E0] font-sans p-4 sm:p-6 selection:bg-gray-200 dark:selection:bg-[#2A2E3A]">
      <div className="max-w-md mx-auto space-y-6 sm:space-y-8 mt-6 sm:mt-12">

        <header className="text-center space-y-2 relative">
          <button
            onClick={switchLang}
            title={lang === "tc" ? "切換至簡體中文 · Switch to Simplified Chinese" : "切換至繁體中文 · Switch to Traditional Chinese"}
            className="absolute right-0 top-0 text-xs text-gray-500 dark:text-[#8B8F98] border border-gray-300 rounded-lg px-3 py-1.5 hover:text-gray-700 hover:border-gray-400 transition-colors"
          >
            🌐 {lang === "tc" ? "简体中文" : "繁體中文"}
          </button>
          <h1 className="text-3xl font-bold tracking-widest text-gray-900 dark:text-[#F5F2EA]">
            <button
              onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
              title={lang === "tc" ? "回到頂部" : "回到顶部"}
              className="tracking-widest cursor-pointer hover:opacity-70 transition-opacity"
            >
              {lang === "tc" ? "決策之書" : "决策之书"}
            </button>
          </h1>
          <p className="text-xs text-gray-500 dark:text-[#8B8F98] tracking-[0.2em]">
            {lang === "tc" ? "職場與商業的抉擇 · 曾仕強思想體系" : "职场与商业的抉择 · 曾仕强思想体系"}
          </p>
          {/* 卖点三连（2026-09-15 鎏金主题色） */}
          <div className="flex justify-center gap-2 pt-2">
            {(lang === "tc" ? ["免費", "免註冊", "30 秒出報告"] : ["免费", "免注册", "30 秒出报告"]).map((x) => (
              <span key={x} className="text-xs text-[#8A6D3B] dark:text-[#C8A96A] bg-[#FAF6ED] dark:bg-[#C8A96A]/10 border border-[#C9B896] dark:border-[#C8A96A]/40 rounded-full px-3 py-1">
                {x}
              </span>
            ))}
          </div>
        </header>

        <section className="space-y-4">
          <textarea
            className="w-full p-4 border border-gray-200 dark:border-[#2A2E3A] rounded-lg focus:outline-none focus:ring-1 focus:ring-gray-400 bg-white dark:bg-[#171A22] shadow-sm resize-none"
            rows="3"
            maxLength={256}
            placeholder={lang === "tc" ? "請輸入你當下最糾結的抉擇..." : "请输入你当下最纠结的抉择..."}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          {/* 提问指导 + 字数提示（上限与 Dify User_Question 变量同步，当前 256） */}
          <div className="flex justify-between items-center -mt-3">
            <span className="text-xs text-gray-400 dark:text-[#6A6E78]">
              {lang === "tc" ? "寫清楚背景、你的選項、最在意什麼" : "写清楚背景、你的选项、最在意什么"}
            </span>
            <span className={`text-xs ${question.length > 230 ? "text-amber-500" : "text-gray-400 dark:text-[#6A6E78]"}`}>
              {question.length > 230
                ? (lang === "tc"
                    ? `已輸入 ${question.length}/256 字 — 接近上限，建議精簡`
                    : `已输入 ${question.length}/256 字 — 接近上限，建议精简`)
                : `${question.length}/256`}
            </span>
          </div>

          {/* 示例问题（2026-09-15 借鉴对标）：降低启动门槛，点击直接填入 */}
          <div className="pt-2">
            <p className="text-xs text-gray-400 dark:text-[#6A6E78] mb-1.5">
              {lang === "tc" ? "不知道怎麼問？試試這些：" : "不知道怎么问？试试这些："}
            </p>
            <div className="flex flex-col gap-1.5">
              {EXAMPLES[lang].map((ex) => (
                <button
                  key={ex}
                  onClick={() => setQuestion(ex)}
                  className="group flex justify-between items-center gap-2 text-left text-xs text-gray-600 dark:text-[#C5C1B8] bg-white dark:bg-[#171A22] border border-gray-200 dark:border-[#2A2E3A] rounded-lg px-3 py-2.5 hover:border-[#C9B896] dark:hover:border-[#C8A96A]/60 hover:text-gray-900 dark:hover:text-[#F5F2EA] transition-colors"
                >
                  <span>{ex}</span>
                  <span className="text-gray-300 dark:text-[#4A4E58] group-hover:text-[#8A6D3B] group-hover:translate-x-0.5 transition-all shrink-0">→</span>
                </button>
              ))}
            </div>
          </div>

          <div className="pt-2">
            <label className="block text-xs text-gray-500 dark:text-[#8B8F98] mb-1.5">
              {lang === "tc" ? "你所在的地區" : "你所在的地区"}
            </label>
            <select
              className="w-full p-3 border border-gray-200 dark:border-[#2A2E3A] rounded-lg bg-white dark:bg-[#171A22] focus:outline-none focus:ring-1 focus:ring-gray-400"
              value={region}
              onChange={(e) => changeRegion(e.target.value)}
            >
              {REGIONS.map((r) => (
                <option key={r} value={r}>{lang === "tc" ? (TC_REGION_LABELS[r] || r) : r}</option>
              ))}
            </select>
            <p className="text-xs text-gray-400 dark:text-[#6A6E78] mt-1.5">
              {region === "其他地区"
                ? (lang === "tc"
                    ? "「其他地區」暫無本地化適配，報告將以通用框架分析，請結合所在地的實際情況參考——內容僅供參考，不構成任何專業建議"
                    : "「其他地区」暂无本地化适配，报告将以通用框架分析，请结合所在地的实际情况参考——内容仅供参考，不构成任何专业建议")
                : (lang === "tc"
                    ? "報告會結合當地的職場與制度環境，給出更貼近你處境的建議"
                    : "报告会结合当地的职场与制度环境，给出更贴近你处境的建议")}
            </p>
          </div>

          <button
            onClick={handleGenerate}
            className="w-full bg-[#1A1A1A] text-white dark:bg-[#C8A96A] dark:text-[#14120E] py-3.5 rounded-lg tracking-widest font-medium hover:bg-black dark:hover:bg-[#D9BA7A] active:scale-[0.99] transition-all"
          >
            {lang === "tc" ? "生成推演報告" : "生成推演报告"}
          </button>
        </section>

        {hexagram && (
          <section className="mt-8 border border-gray-200 dark:border-[#2A2E3A] p-6 rounded-xl bg-white dark:bg-[#171A22] relative overflow-hidden shadow-sm">
            <div className="flex items-baseline space-x-3 mb-2">
              <span className="text-3xl font-black text-gray-200 dark:text-[#2A2E3A] select-none">
                {hexagram.number}
              </span>
              <h2 className="text-lg font-bold">
                🔮 {lang === "tc" ? "你的卦象：" : "你的卦象："}{hexagram[lang].name}
              </h2>
            </div>

            {(() => {
              const orig = ORIGINALS.find(o => numKey(o.id) === numKey(hexagram.number));
              if (!orig) return null;
              const l = lang === "tc" ? "tc" : "sc";
              const lines = [...orig.array].reverse(); // 视觉从上到下 = 爻位从下到上反转
              return (
                <div className="flex items-center gap-5 mb-5 bg-white dark:bg-[#171A22] border border-gray-200 dark:border-[#2A2E3A] rounded-xl px-5 py-4 shadow-sm">
                  {/* 爻线图 */}
                  <div className="flex flex-col gap-[3px] shrink-0" aria-label={`${hexagram[lang].name} 六爻`}>
                    {lines.map((v, idx) => (
                      <div key={idx} className="flex gap-[3px]">
                        {v === 1 ? (
                          <div className="w-9 h-[5px] rounded-[2px] bg-gray-800 dark:bg-[#DCD8CF]" />
                        ) : (
                          <>
                            <div className="w-4 h-[5px] rounded-[2px] bg-gray-800 dark:bg-[#DCD8CF]" />
                            <div className="w-4 h-[5px] rounded-[2px] bg-gray-800 dark:bg-[#DCD8CF]" />
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                  {/* 卦象信息 */}
                  <div className="text-sm leading-relaxed">
                    <div className="font-bold text-gray-900 dark:text-[#F5F2EA]">
                      {orig.symbol} {lang === "tc"
                        ? `第${orig.id}卦 · 上${orig.upper_tc.name}${orig.upper_tc.nature}，下${orig.lower_tc.name}${orig.lower_tc.nature}`
                        : `第${orig.id}卦 · 上${orig.upper_sc.name}${orig.upper_sc.nature}，下${orig.lower_sc.name}${orig.lower_sc.nature}`}
                    </div>
                    <div className="text-gray-500 dark:text-[#8B8F98] mt-1">
                      {lang === "tc" ? "卦辭：" : "卦辞："}
                      <span className="text-gray-700 dark:text-[#DCD8CF] font-medium">
                        「{lang === "tc" ? orig.guaci_tc : orig.guaci_sc}」
                      </span>
                    </div>
                  </div>
                </div>
              );
            })()}

            <p className="text-sm font-medium text-gray-600 dark:text-[#C5C1B8] mb-6 leading-relaxed">
              {(() => {
                const g = INSIGHT_GEN.find(o => numKey(o.id) === numKey(hexagram.number));
                return g ? (lang === "tc" ? g.tc : g.sc) : hexagram[lang].insight;
              })()}
            </p>

            <Paywall
              lang={lang}
              hexagram={hexagram}
              unlocked={unlocked}
              generating={generating}
              report={report}
              error={error}
              onUnlock={handleUnlock}
              onRetry={handleRetry}
            />
          </section>
        )}

        {/* 博客精选入口（2026-09-15 借鉴对标 tarotap：内容直达，降低发现门槛） */}
        <section className="mt-10 pt-6 border-t border-gray-100 dark:border-[#1E222C]">
          <h2 className="text-sm font-medium text-gray-700 dark:text-[#DCD8CF] mb-1 text-center tracking-wider">
            {lang === "tc" ? "決策筆記" : "决策笔记"}
          </h2>
          <p className="text-xs text-gray-400 dark:text-[#6A6E78] text-center mb-4">
            {lang === "tc" ? "易經入門 · 提問方法 · 真實案例" : "易经入门 · 提问方法 · 真实案例"}
          </p>
          <div className="space-y-2">
            {BLOG_POSTS[lang].map(({ title, desc, href }) => (
              <a
                key={href}
                href={href}
                className="group flex items-center gap-3 bg-white dark:bg-[#171A22] border border-gray-200 dark:border-[#2A2E3A] rounded-xl px-4 py-3.5 hover:border-[#C9B896] dark:hover:border-[#C8A96A]/60 hover:shadow-sm transition-all"
              >
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-gray-900 dark:text-[#F5F2EA] font-medium mb-1 leading-snug">{title}</div>
                  <div className="text-xs text-gray-500 dark:text-[#8B8F98] leading-relaxed">{desc}</div>
                </div>
                <span className="text-gray-300 dark:text-[#4A4E58] group-hover:text-[#8A6D3B] group-hover:translate-x-0.5 transition-all shrink-0">→</span>
              </a>
            ))}
          </div>
          <div className="text-center mt-3">
            <a
              href={lang === "tc" ? "/blog/" : "/cn/blog/"}
              className="text-xs text-gray-500 dark:text-[#8B8F98] hover:text-gray-900 dark:hover:text-[#F5F2EA] underline underline-offset-4"
            >
              {lang === "tc" ? "查看全部文章 →" : "查看全部文章 →"}
            </a>
          </div>
        </section>

        {/* 首页 FAQ（2026-09-15 借鉴对标）：合规声明 + 期望管理 */}
        <section className="mt-10 pt-6 border-t border-gray-100 dark:border-[#1E222C]">
          <h2 className="text-sm font-medium text-gray-700 dark:text-[#DCD8CF] mb-3 text-center tracking-wider">
            {lang === "tc" ? "常見問題" : "常见问题"}
          </h2>
          <div className="space-y-2">
            {FAQ[lang].map(({ q, a }) => (
              <details key={q} className="bg-white dark:bg-[#171A22] border border-gray-200 dark:border-[#2A2E3A] rounded-xl px-4 py-3 group transition-colors hover:border-[#C9B896] dark:hover:border-[#C8A96A]/60">
                <summary className="text-sm text-gray-700 dark:text-[#DCD8CF] cursor-pointer list-none flex justify-between items-center hover:text-gray-900 dark:hover:text-[#F5F2EA] transition-colors">
                  {q}
                  <span className="text-gray-400 dark:text-[#6A6E78] group-open:rotate-180 transition-transform inline-block">▾</span>
                </summary>
                <p className="text-xs text-gray-500 dark:text-[#8B8F98] mt-2 leading-relaxed">{a}</p>
              </details>
            ))}
          </div>
        </section>

        <footer className="mt-10 pt-6 border-t border-gray-100 dark:border-[#1E222C] text-center space-y-1.5">
          <a
            href={lang === "tc" ? "/hexagram/" : "/cn/hexagram/"}
            className="inline-block text-sm text-gray-500 dark:text-[#8B8F98] hover:text-gray-900 dark:hover:text-[#F5F2EA] underline underline-offset-4"
          >
            {lang === "tc" ? "📖 易經六十四卦索引 · 卦辭爻辭原文" : "📖 易经六十四卦索引 · 卦辞爻辞原文"}
          </a>
          <div>
            <a
              href="/blog/"
              className="inline-block text-sm text-gray-500 dark:text-[#8B8F98] hover:text-gray-900 dark:hover:text-[#F5F2EA] underline underline-offset-4"
            >
              {lang === "tc" ? "✍️ 職場決策筆記 · 離職、轉職、迷茫的真實解法" : "✍️ 职场决策笔记 · 离职、跳槽、迷茫的真实解法"}
            </a>
          </div>
          <p className="text-xs text-gray-400 dark:text-[#6A6E78] tracking-wider">
            {lang === "tc" ? "曾仕強教授易經思想體系" : "曾仕强教授易经思想体系"}
          </p>
        </footer>
      </div>
      {showTop && (
        <button
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          title={lang === "tc" ? "回到頂部" : "回到顶部"}
          aria-label={lang === "tc" ? "回到頂部" : "回到顶部"}
          className="fixed bottom-6 right-6 w-11 h-11 rounded-full bg-white dark:bg-[#171A22] border border-gray-200 dark:border-[#2A2E3A] shadow-sm text-gray-500 dark:text-[#8B8F98] hover:text-gray-900 dark:hover:text-[#F5F2EA] hover:border-gray-300 dark:hover:border-[#4A4E58] transition-colors flex items-center justify-center text-lg"
        >
          ↑
        </button>
      )}
      <Analytics />
      <SpeedInsights />
    </div>
  );
}
