import { useState, useEffect, useCallback } from 'react';
import { Analytics, track } from '@vercel/analytics/react';
import { SpeedInsights } from '@vercel/speed-insights/react';
import HEXAGRAMS from './data/hexagrams';
import { generateHexagramIndex } from './lib/seed';
import Paywall from './components/Paywall';

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
  const [region, setRegion] = useState("台灣/港澳");
  const [hexagram, setHexagram] = useState(null);
  // 会话内解锁一次即生效：新问题不再要求重新付费
  const [unlocked, setUnlocked] = useState(false);
  const [report, setReport] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  const lang = region.includes("台灣") ? "tc" : "sc";

  const fetchReport = useCallback(async (q, reg, hex) => {
    setGenerating(true);
    setError(null);
    try {
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

      const data = await response.json();
      if (data?.data?.outputs) {
        let text = data.data.outputs.Report || data.data.outputs.text || data.data.outputs.answer;
        if (text) {
          text = text.replace(/<think>[\s\S]*?<\/think>\n*/gi, '').trim();
          setReport(text);
        } else {
          setError(lang === "tc" ? "⚠️ 數據解析失敗" : "⚠️ 数据解析失败");
        }
      } else {
        setError(lang === "tc" ? "⚠️ 數據解析失敗" : "⚠️ 数据解析失败");
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

        <header className="text-center space-y-2">
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
            placeholder={lang === "tc" ? "請輸入你當下最糾結的抉擇..." : "请输入你当下最纠结的抉择..."}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />

          <select
            className="w-full p-3 border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-gray-400"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
          >
            <option value="台灣/港澳">台灣/港澳地區 (繁體)</option>
            <option value="新加坡/大馬">新加坡/大馬地区 (简体)</option>
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

            <p className="text-sm font-medium text-gray-600 mb-6 leading-relaxed">
              {hexagram[lang].insight}
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
