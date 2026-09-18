import { useState } from 'react';
import { track } from '@vercel/analytics/react';

// 分享按钮（无图版·符号型悬浮，2026-09-18）：payload 只含 卦名+金句（text）与链接（url）——
// 隐私=结构性不含：禁止在此组件里加入问题/报告任何片段。设计规格见
// decision-book-dev/references/share-save-design.md。
// 定位由外层容器负责（App 中与「回到顶部」叠放为右下角悬浮组）。
// 移动端 = navigator.share 系统面板；桌面/不支持 = 复制 text+url 到剪贴板（图标短暂变 ✓）。
const ShareIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="18" cy="5" r="3" />
    <circle cx="6" cy="12" r="3" />
    <circle cx="18" cy="19" r="3" />
    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
  </svg>
);
const CheckIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M20 6 9 17l-5-5" />
  </svg>
);

export default function ShareButton({ lang, text, url }) {
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
    <button
      onClick={handleShare}
      title={lang === "tc" ? "分享這卦（只含卦名與金句）" : "分享这卦（只含卦名与金句）"}
      aria-label={lang === "tc" ? "分享這卦" : "分享这卦"}
      className="w-11 h-11 rounded-full bg-white dark:bg-[#171A22] border border-gray-200 dark:border-[#2A2E3A] shadow-sm text-gray-500 dark:text-[#8B8F98] hover:text-gray-900 dark:hover:text-[#F5F2EA] hover:border-gray-300 dark:hover:border-[#4A4E58] transition-colors flex items-center justify-center"
    >
      {copied ? <CheckIcon /> : <ShareIcon />}
    </button>
  );
}
