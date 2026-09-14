import { useState } from 'react';
import { track } from '@vercel/analytics/react';

// ---- 轻量报告 Markdown 渲染（模型输出含 ** 加粗 / - 列表 / emoji 标题行，此前裸显示符号）----
function inlineMd(text, keyBase = "s") {
  const parts = String(text).split(/\*\*(.+?)\*\*/g);
  return parts.map((p, i) =>
    i % 2 === 1 ? <strong key={keyBase + i} className="font-semibold text-gray-900">{p}</strong> : p
  );
}

function ReportBody({ text }) {
  const lines = String(text || "").split("\n");
  const nodes = [];
  let listBuf = [];
  const flushList = () => {
    if (listBuf.length) {
      nodes.push(
        <ul key={"ul" + nodes.length} className="list-disc pl-5 my-2 space-y-2">{listBuf}</ul>
      );
      listBuf = [];
    }
  };
  lines.forEach((raw, i) => {
    const line = raw.trim();
    if (!line) {
      flushList();
      nodes.push(<div key={"g" + i} className="h-3" />);
      return;
    }
    const li = line.match(/^[-·•]\s+(.+)$/);
    if (li) {
      listBuf.push(<li key={"li" + i} className="leading-relaxed">{inlineMd(li[1], "l" + i)}</li>);
      return;
    }
    flushList();
    if (/^(?:🔮|👁️|⚠️|🚀|⏳)/.test(line)) {
      nodes.push(
        <p key={"t" + i} className="font-bold text-gray-900 mt-5 first:mt-0">{inlineMd(line, "t" + i)}</p>
      );
      return;
    }
    nodes.push(<p key={"p" + i} className="my-1.5 leading-relaxed">{inlineMd(line, "p" + i)}</p>);
  });
  flushList();
  return <>{nodes}</>;
}

export default function Paywall({ lang, hexagram, unlocked, generating, report, error, onUnlock, onRetry }) {
  const [password, setPassword] = useState("");

  const handleUnlockClick = () => {
    onUnlock(password);
  };

  // 已解锁：显示生成中 / 报告 / 错误重试
  if (unlocked) {
    if (generating) {
      return (
        <div className="mt-6 border-t border-gray-100 pt-8 flex flex-col items-center justify-center py-8">
          <span className="animate-pulse flex items-center space-x-2 text-sm text-gray-500">
            <span className="h-2 w-2 bg-gray-400 rounded-full" />
            <span className="h-2 w-2 bg-gray-400 rounded-full animation-delay-200" />
            <span className="h-2 w-2 bg-gray-400 rounded-full animation-delay-400" />
            {lang === "tc" ? "正在構建高維度決策報告..." : "正在构建高维度决策报告..."}
          </span>
        </div>
      );
    }

    if (error) {
      return (
        <div className="mt-6 border-t border-gray-100 pt-8 text-center">
          <p className="text-sm text-gray-600 mb-4">{error}</p>
          <button
            onClick={onRetry}
            className="bg-[#1A1A1A] text-white px-6 py-2.5 rounded-md text-sm font-medium hover:bg-black transition-colors"
          >
            {lang === "tc" ? "重新生成" : "重新生成"}
          </button>
        </div>
      );
    }

    if (report) {
      return (
        <div className="mt-6 text-sm text-gray-700 leading-relaxed border-t border-gray-100 pt-4">
          <ReportBody text={report} />
        </div>
      );
    }

    return null;
  }

  // 未解锁：支付墙
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
          onClick={handleUnlockClick}
          className="bg-[#1A1A1A] text-white px-8 py-2.5 rounded-md text-sm font-medium hover:bg-black transition-colors"
        >
          {lang === "tc" ? "解鎖深度推演" : "解锁深度推演"}
        </button>
      </div>
    </div>
  );
}
