import { useState, useEffect } from 'react';
import { track } from '@vercel/analytics/react';

// ---- 生成中动态步骤文案（把处理过程翻译成"学者翻书"叙事；3.5s/条，走完停在末条不循环）----
const GEN_STEPS = {
  tc: [
    "正在理解你的問題",
    "正在翻閱《易經》，查看這一卦的卦象",
    "回想一下曾師在講這段的時候是怎麼說的",
    "正在檢索所選地區的文化與社會現實",
    "正在草擬決策報告",
    "正在潤色報告文書",
  ],
  sc: [
    "正在理解你的问题",
    "正在翻阅《易经》，查看这一卦的卦象",
    "回想一下曾师在讲这段的时候是怎么说的",
    "正在检索所选地区的文化与社会现实",
    "正在草拟决策报告",
    "正在润色报告文书",
  ],
};

// ---- 轻量报告 Markdown 渲染（模型输出含 ** 加粗 / - 列表 / emoji 标题行，此前裸显示符号）----
function inlineMd(text, keyBase = "s") {
  const parts = String(text).split(/\*\*(.+?)\*\*/g);
  return parts.map((p, i) =>
    i % 2 === 1 ? <strong key={keyBase + i} className="font-semibold text-gray-900 dark:text-[#F5F2EA]">{p}</strong> : p
  );
}

function ReportBody({ text }) {
  const lines = String(text || "").split("\n");
  const nodes = [];
  let listBuf = [];
  let olBuf = [];
  const flushList = () => {
    if (listBuf.length) {
      nodes.push(
        <ul key={"ul" + nodes.length} className="list-disc pl-5 my-2 space-y-2">{listBuf}</ul>
      );
      listBuf = [];
    }
  };
  const flushOl = () => {
    if (olBuf.length) {
      nodes.push(
        <ol key={"ol" + nodes.length} className="list-decimal pl-5 my-2 space-y-2">{olBuf}</ol>
      );
      olBuf = [];
    }
  };
  const flushAll = () => { flushList(); flushOl(); };
  lines.forEach((raw, i) => {
    const line = raw.trim();
    if (!line) {
      flushAll();
      nodes.push(<div key={"g" + i} className="h-3" />);
      return;
    }
    const li = line.match(/^[-·•]\s+(.+)$/);
    if (li) {
      flushOl();
      listBuf.push(<li key={"li" + i} className="leading-relaxed">{inlineMd(li[1], "l" + i)}</li>);
      return;
    }
    const oli = line.match(/^\d+[.、]\s+(.+)$/);
    if (oli) {
      flushList();
      olBuf.push(<li key={"oli" + i} className="leading-relaxed">{inlineMd(oli[1], "o" + i)}</li>);
      return;
    }
    flushAll();
    if (/^(?:🔮|👁️|⚠️|🚀|⏳)/.test(line)) {
      nodes.push(
        <p key={"t" + i} className="font-bold text-gray-900 dark:text-[#F5F2EA] mt-5 first:mt-0">{inlineMd(line, "t" + i)}</p>
      );
      return;
    }
    nodes.push(<p key={"p" + i} className="my-1.5 leading-relaxed">{inlineMd(line, "p" + i)}</p>);
  });
  flushAll();
  return <>{nodes}</>;
}

export default function Paywall({ lang, hexagram, unlocked, generating, report, error, onUnlock, onRetry }) {
  const [password, setPassword] = useState("");
  // 生成中步骤轮播（~7s/条；生成结束自动复位；重试不重置）
  const steps = GEN_STEPS[lang] || GEN_STEPS.sc;
  const [stepIdx, setStepIdx] = useState(0);
  useEffect(() => {
    if (!generating) {
      setStepIdx(0);
      return;
    }
    setStepIdx(0);
    const t = setInterval(() => {
      setStepIdx((i) => Math.min(i + 1, steps.length - 1));
    }, 3500);
    return () => clearInterval(t);
  }, [generating, lang]);

  const handleUnlockClick = () => {
    onUnlock(password);
  };

  // 已解锁：显示生成中 / 报告 / 错误重试
  if (unlocked) {
    if (generating) {
      return (
        <div className="mt-6 border-t border-gray-100 dark:border-[#1E222C] pt-8 flex flex-col items-center justify-center py-8">
          <span className="flex items-center space-x-2 text-sm text-gray-500 dark:text-[#8B8F98]">
            <span className="h-2 w-2 bg-gray-400 dark:bg-[#C8A96A] rounded-full animate-pulse" />
            <span className="h-2 w-2 bg-gray-400 dark:bg-[#C8A96A] rounded-full animate-pulse" style={{ animationDelay: "0.2s" }} />
            <span className="h-2 w-2 bg-gray-400 dark:bg-[#C8A96A] rounded-full animate-pulse" style={{ animationDelay: "0.4s" }} />
            <span>{steps[stepIdx]}</span>
            <span className="h-2 w-2 bg-gray-400 dark:bg-[#C8A96A] rounded-full animate-pulse" style={{ animationDelay: "0.2s" }} />
            <span className="h-2 w-2 bg-gray-400 dark:bg-[#C8A96A] rounded-full animate-pulse" style={{ animationDelay: "0.4s" }} />
            <span className="h-2 w-2 bg-gray-400 dark:bg-[#C8A96A] rounded-full animate-pulse" style={{ animationDelay: "0.6s" }} />
          </span>
        </div>
      );
    }

    if (error) {
      return (
        <div className="mt-6 border-t border-gray-100 dark:border-[#1E222C] pt-8 text-center">
          <p className="text-sm text-gray-600 dark:text-[#C5C1B8] mb-4">{error}</p>
          <button
            onClick={onRetry}
            className="bg-[#1A1A1A] text-white dark:bg-[#C8A96A] dark:text-[#14120E] px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-black dark:hover:bg-[#D9BA7A] transition-colors"
          >
            {lang === "tc" ? "重新生成" : "重新生成"}
          </button>
        </div>
      );
    }

    if (report) {
      return (
        <div className="mt-6 text-sm text-gray-700 dark:text-[#DCD8CF] leading-relaxed border-t border-gray-100 dark:border-[#1E222C] pt-4">
          <ReportBody text={report} />
        </div>
      );
    }

    return null;
  }

  // 未解锁：支付墙
  return (
    <div className="relative mt-6 border-t border-gray-100 dark:border-[#1E222C] pt-4">
      <div className="blur-sm text-gray-400 dark:text-[#6A6E78] text-sm leading-relaxed select-none opacity-60">
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

      <div className="absolute inset-0 flex flex-col items-center justify-center p-4 bg-white/50 dark:bg-[#0F1115]/60 backdrop-blur-xs">
        <a
          href="https://ko-fi.com/s/c35a082076"
          target="_blank"
          rel="noreferrer"
          onClick={() => track('payment_link_clicked', { hexagram: hexagram?.number })}
          className="mb-5 text-sm font-bold text-[#7C2D12] dark:text-[#E8A87C] underline hover:text-black dark:hover:text-[#F5F2EA] transition-colors"
        >
          🛒 {lang === "tc" ? "解鎖完整解讀 · $3.99/週" : "解锁完整解读 · $3.99/周"}
        </a>
        <input
          type="text"
          placeholder={lang === "tc" ? "輸入解鎖密碼" : "输入解锁密码"}
          className="w-full max-w-[220px] text-center p-2.5 border border-gray-300 dark:border-[#3A3E4A] rounded-lg mb-4 bg-white/90 dark:bg-[#171A22]/95 focus:outline-none"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button
          onClick={handleUnlockClick}
          className="bg-[#1A1A1A] text-white dark:bg-[#C8A96A] dark:text-[#14120E] px-8 py-2.5 rounded-lg text-sm font-medium hover:bg-black dark:hover:bg-[#D9BA7A] transition-colors"
        >
          {lang === "tc" ? "解鎖深度推演" : "解锁深度推演"}
        </button>
      </div>
    </div>
  );
}
