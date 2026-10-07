import { useState } from 'react';
import { track } from '@vercel/analytics/react';

// 分享按钮（符号型悬浮，2026-09-18；2026-10-07 v2 兜底链加固）：
// 系统分享 → 剪贴板 → execCommand → 手动复制面板；复制成功 = ✓ + 气泡提示。
// payload 只含 卦名+金句（text）与链接（url）——隐私=结构性不含问题/报告任何片段。
// 设计规格见 decision-book-dev/references/share-save-design.md。定位由外层容器负责。
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
  const [toast, setToast] = useState(false);
  const [manual, setManual] = useState(false);
  const isTc = lang === "tc";

  const showCopied = () => {
    setCopied(true);
    setToast(true);
    setTimeout(() => setCopied(false), 2500);
    setTimeout(() => setToast(false), 2400);
  };

  // 传统复制（WebView/旧浏览器兜底；clipboard API 不可用时）
  const legacyCopy = (t) => {
    try {
      const ta = document.createElement('textarea');
      ta.value = t;
      ta.setAttribute('readonly', '');
      ta.style.cssText = 'position:fixed;top:-1000px;opacity:0;';
      document.body.appendChild(ta);
      ta.select();
      ta.setSelectionRange(0, ta.value.length);
      const ok = document.execCommand('copy');
      ta.remove();
      return ok;
    } catch {
      return false;
    }
  };

  const fallbackCopy = async () => {
    const payload = `${text}\n${url}`;
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(payload);
        showCopied();
        track('share_copy', { lang });
        return;
      }
    } catch {
      // 落 execCommand
    }
    if (legacyCopy(payload)) {
      showCopied();
      track('share_copy', { lang, method: 'execCommand' });
      return;
    }
    setManual(true);
    track('share_manual', { lang });
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
        // 其他失败（权限/系统中断/WebView 禁用）→ 复制兜底
      }
    }
    await fallbackCopy();
  };

  return (
    <>
      <button
        onClick={handleShare}
        title={isTc ? "分享這卦（只含卦名與金句）" : "分享这卦（只含卦名与金句）"}
        aria-label={isTc ? "分享這卦" : "分享这卦"}
        className="w-11 h-11 rounded-full bg-white dark:bg-[#171A22] border border-gray-200 dark:border-[#2A2E3A] shadow-sm text-gray-500 dark:text-[#8B8F98] hover:text-gray-900 dark:hover:text-[#F5F2EA] hover:border-gray-300 dark:hover:border-[#4A4E58] transition-colors flex items-center justify-center"
      >
        {copied ? <CheckIcon /> : <ShareIcon />}
      </button>

      {/* 复制成功气泡（2026-10-07）：✓ 单图标不自明，补一句人话 */}
      {toast && (
        <div className="fixed bottom-28 left-1/2 -translate-x-1/2 z-[60] bg-white dark:bg-[#171A22] border border-gray-200 dark:border-[#C8A96A]/40 text-gray-700 dark:text-[#E8E6E0] text-xs px-4 py-2 rounded-full shadow-lg whitespace-nowrap">
          {isTc ? "已複製，貼到 LINE／微信即可分享" : "已复制，粘贴到微信／LINE 即可分享"}
        </div>
      )}

      {/* 手动复制面板（clipboard 与 execCommand 均不可用时的最后兜底） */}
      {manual && (
        <div className="fixed left-3 right-3 bottom-[104px] z-[70] bg-white dark:bg-[#171A22] border border-gray-200 dark:border-[#C8A96A]/50 rounded-xl px-4 py-3.5 shadow-xl">
          <div className="text-xs text-[#8A6D3B] dark:text-[#C8A96A] mb-1.5">
            {isTc ? "長按選取以下文字複製，即可分享：" : "长按选取以下文字复制，即可分享："}
          </div>
          <div className="text-sm text-gray-700 dark:text-[#DCD8CF] leading-relaxed select-text whitespace-pre-wrap break-all">
            {`${text}\n${url}`}
          </div>
          <button
            onClick={() => setManual(false)}
            className="mt-2.5 text-xs text-gray-500 dark:text-[#8B8F98] border border-gray-200 dark:border-[#2A2E3A] rounded-full px-3.5 py-1"
          >
            {isTc ? "關閉" : "关闭"}
          </button>
        </div>
      )}
    </>
  );
}
