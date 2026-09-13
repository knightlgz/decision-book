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
  const [region, setRegion] = useState(INIT_CN ? "新加坡/大馬" : "台灣/港澳");
  const [hexagram, setHexagram] = useState(null);
  // 会话内解锁一次即生效：新问题不再要求重新付费
  // 付费墙暂停（2026-09-14）：首卦体验免费，报告直接生成。
  // 恢复：改回 useState(false)。付费墙未来接入 Ko-fi（追问付费时再启用）。
  const [unlocked, setUnlocked] = useState(true);
  const [report, setReport] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  const lang = INIT_CN ? "sc" : "tc";
  const switchLang = () => {
    window.location.href = lang === "tc" ? "/cn/" : "/";
  };

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
        text = text.replace(/<think>[\s\S]*?<\/think>\n*/gi, '').trim();
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
    <div className="min-h-dvh bg-[#FAFAFA] text-[#333333] font-sans p-4 sm:p-6 selection:bg-gray-200">
      <div className="max-w-md mx-auto space-y-6 sm:space-y-8 mt-6 sm:mt-12">

        <header className="text-center space-y-2 relative">
          <button
            onClick={switchLang}
            className="absolute right-0 top-0 text-xs text-gray-400 border border-gray-200 rounded-md px-2.5 py-1 hover:text-gray-700 hover:border-gray-400 transition-colors"
          >
            {lang === "tc" ? "简体中文" : "繁體中文"}
          </button>
          <h1 className="text-3xl font-bold tracking-widest text-gray-900">
            {lang === "tc" ? "決策之書" : "决策之书"}
          </h1>
          <p className="text-xs text-gray-500 tracking-[0.2em]">
            {lang === "tc" ? "易經商業決策 · 曾仕強思想體系" : "易经商业决策 · 曾仕强思想体系"}
          </p>
        </header>

        <section className="space-y-4">
          <textarea
            className="w-full p-4 border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-gray-400 bg-white shadow-sm resize-none"
            rows="3"
            maxLength={256}
            placeholder={lang === "tc" ? "請輸入你當下最糾結的抉擇..." : "请输入你当下最纠结的抉择..."}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          {/* 字数提示：上限与 Dify 工作流 User_Question 变量限制保持同步（当前 256） */}
          <div className="flex justify-end -mt-2">
            <span className={`text-xs ${question.length > 230 ? "text-amber-500" : "text-gray-400"}`}>
              {question.length > 230
                ? (lang === "tc"
                    ? `已輸入 ${question.length}/256 字 — 接近上限，建議精簡`
                    : `已输入 ${question.length}/256 字 — 接近上限，建议精简`)
                : `${question.length}/256`}
            </span>
          </div>

          <select
            className="w-full p-3 border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-gray-400"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
          >
            <option value="台灣/港澳">台灣/港澳地區</option>
            <option value="新加坡/大馬">新加坡/大馬地区</option>
          </select>

          <button
            onClick={handleGenerate}
            className="w-full bg-[#1A1A1A] text-white py-3.5 rounded-lg tracking-widest font-medium hover:bg-black transition-colors"
          >
            {lang === "tc" ? "生成推演報告" : "生成推演报告"}
          </button>
        </section>

        {hexagram && (
          <section className="mt-8 border border-gray-200 p-6 rounded-xl bg-white relative overflow-hidden shadow-sm">
            <div className="flex items-baseline space-x-3 mb-2">
              <span className="text-3xl font-black text-gray-200 select-none">
                {hexagram.number}
              </span>
              <h2 className="text-lg font-bold">
                🔮 {lang === "tc" ? "你的能量切片：" : "你的能量切片："}{hexagram[lang].name}
              </h2>
            </div>

            {(() => {
              const orig = ORIGINALS.find(o => numKey(o.id) === numKey(hexagram.number));
              if (!orig) return null;
              const l = lang === "tc" ? "tc" : "sc";
              const lines = [...orig.array].reverse(); // 视觉从上到下 = 爻位从下到上反转
              return (
                <div className="flex items-center gap-5 mb-5 bg-stone-50 border border-stone-100 rounded-xl px-5 py-4">
                  {/* 爻线图 */}
                  <div className="flex flex-col gap-[3px] shrink-0" aria-label={`${hexagram[lang].name} 六爻`}>
                    {lines.map((v, idx) => (
                      <div key={idx} className="flex gap-[3px]">
                        {v === 1 ? (
                          <div className="w-9 h-[5px] rounded-[2px] bg-gray-800" />
                        ) : (
                          <>
                            <div className="w-4 h-[5px] rounded-[2px] bg-gray-800" />
                            <div className="w-4 h-[5px] rounded-[2px] bg-gray-800" />
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                  {/* 卦象信息 */}
                  <div className="text-sm leading-relaxed">
                    <div className="font-bold text-gray-800">
                      {orig.symbol} {lang === "tc"
                        ? `第${orig.id}卦 · 上${orig.upper_tc.name}${orig.upper_tc.nature}，下${orig.lower_tc.name}${orig.lower_tc.nature}`
                        : `第${orig.id}卦 · 上${orig.upper_sc.name}${orig.upper_sc.nature}，下${orig.lower_sc.name}${orig.lower_sc.nature}`}
                    </div>
                    <div className="text-gray-500 mt-1">
                      {lang === "tc" ? "卦辭：" : "卦辞："}
                      <span className="text-gray-700 font-medium">
                        「{lang === "tc" ? orig.guaci_tc : orig.guaci_sc}」
                      </span>
                    </div>
                  </div>
                </div>
              );
            })()}

            <p className="text-sm font-medium text-gray-600 mb-6 leading-relaxed">
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

        <footer className="mt-10 pt-6 border-t border-gray-100 text-center space-y-1.5">
          <a
            href={lang === "tc" ? "/hexagram/" : "/cn/hexagram/"}
            className="inline-block text-sm text-gray-500 hover:text-gray-800 underline underline-offset-4"
          >
            {lang === "tc" ? "📖 易經六十四卦索引 · 卦辭爻辭原文" : "📖 易经六十四卦索引 · 卦辞爻辞原文"}
          </a>
          <div>
            <a
              href="/blog/"
              className="inline-block text-sm text-gray-500 hover:text-gray-800 underline underline-offset-4"
            >
              {lang === "tc" ? "✍️ 職場決策筆記 · 離職、轉職、迷茫的真實解法" : "✍️ 职场决策笔记 · 离职、转职、迷茫的真实解法"}
            </a>
          </div>
          <p className="text-xs text-gray-400 tracking-wider">
            {lang === "tc" ? "曾仕強教授易經思想體系" : "曾仕强教授易经思想体系"}
          </p>
        </footer>
      </div>
      <Analytics />
      <SpeedInsights />
    </div>
  );
}
