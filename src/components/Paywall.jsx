import { useState } from 'react';
import { track } from '@vercel/analytics/react';

export default function Paywall({ lang, hexagram, onUnlock }) {
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [fullReport, setFullReport] = useState("");

  const handleUnlock = async () => {
    track('unlock_attempted', { hexagram: hexagram?.number });

    if (password.trim() !== "AURA-888") {
      track('unlock_failed', { reason: 'wrong_password' });
      return alert(lang === "tc" ? "密碼驗證失敗，請確認購買後的感謝信內容。" : "密码验证失败，请确认购买后的感谢信内容。");
    }
    track('unlock_success');
    setLoading(true);

    try {
      const response = await fetch('/api/dify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          inputs: {
            User_Question: onUnlock.question,
            Region: onUnlock.region,
            Hexagram_Name: hexagram["sc"].name
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
          setFullReport(text);
        } else {
          setFullReport(lang === "tc" ? "⚠️ 數據解析失敗" : "⚠️ 数据解析失败");
        }
      }
    } catch {
      setFullReport(lang === "tc" ? "系統繁忙，請稍後重試。" : "系统繁忙，请稍后重试。");
    } finally {
      setLoading(false);
    }
  };

  if (fullReport) {
    return (
      <div className="mt-6 whitespace-pre-wrap text-sm text-gray-700 leading-relaxed border-t border-gray-100 pt-4">
        {fullReport}
      </div>
    );
  }

  return (
    <div className="relative mt-6 border-t border-gray-100 pt-4">
      <div className="blur-sm text-gray-400 text-sm leading-relaxed select-none opacity-60">
        {lang === "tc" ? (
          <>
            【現狀刺透】這裏將輸出深度分析文本，直擊你的核心痛點與處境。<br/><br/>
            【避坑指南】這裏是商業紅線警告，告訴你在此抉擇下絕對不能做什麽。<br/><br/>
            【破局行動】這裏是符合第一性原理的具體實操建議。<br/><br/>
            【未來演進】這裏是對未來三個月客觀趨勢的推演。
          </>
        ) : (
          <>
            【现状刺透】这里将输出深度分析文本，直击你的核心痛点与处境。<br/><br/>
            【避坑指南】这里是商业红线警告，告诉你在此抉择下绝对不能做什么。<br/><br/>
            【破局行动】这里是符合第一性原理的具体实操建议。<br/><br/>
            【未来演进】这里是对未来三个月客观趋势的推演。
          </>
        )}
      </div>

      <div className="absolute inset-0 flex flex-col items-center justify-center p-4 bg-white/50 backdrop-blur-xs">
        <a
          href="https://ko-fi.com/s/c35a082076"
          target="_blank"
          rel="noreferrer"
          onClick={() => track('payment_link_clicked', { hexagram: hexagram?.number })}
          className="mb-5 text-sm font-bold text-[#7C2D12] underline hover:text-black transition-colors"
        >
          🛒 {lang === "tc" ? "解鎖完整解讀 · $3.99/週" : "解锁完整解读 · $3.99/周"}
        </a>
        <input
          type="text"
          placeholder={lang === "tc" ? "輸入解鎖密碼" : "输入解锁密码"}
          className="w-full max-w-[220px] text-center p-2.5 border border-gray-300 rounded-md mb-4 bg-white/90 focus:outline-none"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button
          onClick={handleUnlock}
          className="bg-[#1A1A1A] text-white px-8 py-2.5 rounded-md text-sm font-medium hover:bg-black transition-colors"
        >
          {lang === "tc" ? "解鎖深度推演" : "解锁深度推演"}
        </button>
      </div>
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/60">
          <span className="animate-pulse flex items-center space-x-2 text-sm text-gray-500">
            <span className="h-2 w-2 bg-gray-400 rounded-full" />
            <span className="h-2 w-2 bg-gray-400 rounded-full animation-delay-200" />
            <span className="h-2 w-2 bg-gray-400 rounded-full animation-delay-400" />
            {lang === "tc" ? "正在構建高維度決策報告..." : "正在构建高维度决策报告..."}
          </span>
        </div>
      )}
    </div>
  );
}
