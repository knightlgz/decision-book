import { useState } from 'react';
import { track } from '@vercel/analytics/react';

// 分享按钮（无图版，2026-09-18）：payload 只含 卦名+金句（text）与链接（url）——
// 隐私=结构性不含：禁止在此组件里加入问题/报告任何片段。设计规格见
// decision-book-dev/references/share-save-design.md。
// 移动端 = navigator.share 系统面板；桌面/不支持 = 复制 text+url 到剪贴板。
export default function ShareButton({ lang, text, url, hint }) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(`${text}\n${url}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
      track('share_copy', { lang });
    } catch {
      // 剪贴板不可用（非安全上下文等）：静默
    }
  };

  const handleShare = async () => {
    if (!text || !url) return;
    if (navigator.share) {
      try {
        await navigator.share({ text, url });
        track('share_native', { lang });
        return;
      } catch (err) {
        if (err && err.name === 'AbortError') return; // 用户取消：不兜底
        // 其他失败（权限/系统中断）→ 复制兜底
      }
    }
    await copyToClipboard();
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        onClick={handleShare}
        className="border border-gray-200 dark:border-[#2A2E3A] bg-white dark:bg-[#171A22] rounded-lg px-5 py-2 text-sm text-gray-600 dark:text-[#C5C1B8] hover:border-[#C9B896] dark:hover:border-[#C8A96A]/60 hover:text-[#8A6D3B] dark:hover:text-[#C8A96A] active:scale-[0.99] transition-all"
      >
        {copied
          ? (lang === "tc" ? "✓ 已複製" : "✓ 已复制")
          : (lang === "tc" ? "分享這卦" : "分享这卦")}
      </button>
      {hint && (
        <span className="text-xs text-gray-400 dark:text-[#6A6E78]">{hint}</span>
      )}
    </div>
  );
}
