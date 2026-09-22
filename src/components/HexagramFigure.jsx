// 六爻图（古朴风）：阳爻=横实线、阴爻=两短线；动爻右侧加标记——老阳 ○ / 老阴 ✕
// 规格（variation-design.md 显示规范）：等线宽；✕ 两线段交点与 ○ 的圆心共线；✕ 视觉体量 ≈ ○ 的 91%
// 入参 lines：自下而上（初爻→上爻）[{ yang: boolean, moving: boolean }]
export default function HexagramFigure({ lines, ariaLabel }) {
  const rows = [...lines].reverse(); // 展示自上而下（上爻在最上）
  return (
    <div className="flex flex-col gap-[5px] shrink-0 text-[#3A352E] dark:text-[#DCD8CF]" role="img" aria-label={ariaLabel}>
      {rows.map((ln, i) => (
        <div key={i} className="flex items-center gap-[6px] h-[10px]">
          {ln.yang ? (
            <div className="w-12 h-[5px] rounded-[2px] bg-current" />
          ) : (
            <div className="w-12 h-[5px] flex justify-between" aria-hidden="true">
              <div className="w-[43.75%] h-[5px] rounded-[2px] bg-current" />
              <div className="w-[43.75%] h-[5px] rounded-[2px] bg-current" />
            </div>
          )}
          {ln.moving && (
            <svg className="w-[11px] h-[11px]" viewBox="0 0 17 17" aria-hidden="true">
              {ln.yang ? (
                <circle cx="8.5" cy="8.5" r="6" fill="none" stroke="currentColor" strokeWidth="2.7" />
              ) : (
                <path d="M2.8 2.8 L14.2 14.2 M14.2 2.8 L2.8 14.2" fill="none" stroke="currentColor" strokeWidth="2.7" strokeLinecap="round" />
              )}
            </svg>
          )}
        </div>
      ))}
    </div>
  );
}
