// 卦象结果卡（2026-10-07）：纯 Canvas 绘制 1080×1920 分享图，零第三方依赖。
// 隐私红线：卡面结构性不含问题/报告片段——只含 品牌行 / 卦象 / 卦名 / 金句 / 二维码。
// 品牌行措辞：曾師的AI學徒（2026-10-07 Kyson 定，替代已弃用的“AI 弟子”）。
const W = 1080;
const H = 1920;

const C = {
  bg: '#16130E',
  frame: '#C8A96A',
  gold: '#C8A96A',
  goldLight: '#E6D3A3',
  white: '#F0EAD9',
  body: '#D8CDB8',
  muted: '#8A8172',
};

function font(weight, size, lang) {
  const fam = lang === 'tc'
    ? '"PingFang TC","Noto Sans TC","Microsoft JhengHei",serif'
    : '"PingFang SC","Noto Sans SC","Microsoft YaHei",serif';
  return `${weight} ${size}px ${fam}`;
}

function wrap(ctx, text, maxWidth) {
  const lines = [];
  let line = '';
  for (const ch of text) {
    if (ctx.measureText(line + ch).width > maxWidth && line) {
      lines.push(line);
      line = ch;
    } else {
      line += ch;
    }
  }
  if (line) lines.push(line);
  return lines;
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}

/**
 * 在 canvas 上绘制卦象卡（并设为 1080×1920 画布）。
 * @param {HTMLCanvasElement} canvas
 * @param {{hexagram: object, orig: object, cast: object|null, insight: string, lang: string}} opts
 */
export async function renderCard(canvas, { hexagram, orig, cast, insight, lang }) {
  const isTc = lang === 'tc';
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext('2d');

  // 底
  ctx.fillStyle = C.bg;
  ctx.fillRect(0, 0, W, H);

  // 双线画框
  ctx.strokeStyle = C.frame;
  ctx.globalAlpha = 0.9;
  ctx.lineWidth = 2;
  ctx.strokeRect(44, 44, W - 88, H - 88);
  ctx.globalAlpha = 0.45;
  ctx.lineWidth = 1;
  ctx.strokeRect(58, 58, W - 116, H - 116);
  ctx.globalAlpha = 1;

  // 品牌行
  ctx.fillStyle = C.gold;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.font = font(500, 30, lang);
  if ('letterSpacing' in ctx) ctx.letterSpacing = '6px';
  ctx.fillText(isTc ? '決策之書 · 曾師的AI學徒' : '决策之书 · 曾师的AI学徒', W / 2, 150);
  if ('letterSpacing' in ctx) ctx.letterSpacing = '0px';

  // 六爻图（arr 自下而上：arr[0]=初爻；显示时上爻在最上）
  const arr = orig.array;
  const barW = 420;
  const barH = 20;
  const gap = 62;
  const cx = W / 2;
  const left = cx - barW / 2;
  const topY = 380;
  ctx.fillStyle = C.goldLight;
  for (let i = 0; i < 6; i += 1) {
    const row = 5 - i; // 显示行（0=最上）
    const y = topY + row * gap;
    const yang = arr[i] === 1;
    const moving = !!(cast && cast.moving && cast.moving[i]);
    if (yang) {
      ctx.fillRect(left, y, barW, barH);
    } else {
      const seg = (barW - 60) / 2;
      ctx.fillRect(left, y, seg, barH);
      ctx.fillRect(left + barW - seg, y, seg, barH);
    }
    if (moving) {
      const mx = left + barW + 46;
      const my = y + barH / 2;
      ctx.strokeStyle = C.gold;
      ctx.lineWidth = 3;
      if (yang) {
        ctx.beginPath();
        ctx.arc(mx, my, 15, 0, Math.PI * 2);
        ctx.stroke();
      } else {
        const r = 15;
        ctx.beginPath();
        ctx.moveTo(mx - r, my - r);
        ctx.lineTo(mx + r, my + r);
        ctx.moveTo(mx + r, my - r);
        ctx.lineTo(mx - r, my + r);
        ctx.stroke();
      }
    }
  }

  // 卦名
  const name = hexagram[lang].name;
  ctx.fillStyle = C.white;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'alphabetic';
  ctx.font = font(700, 96, lang);
  ctx.fillText(name, cx, 872);

  // 第 N 卦
  ctx.fillStyle = C.gold;
  ctx.font = font(500, 32, lang);
  ctx.fillText(`第 ${Number(hexagram.number)} 卦`, cx, 928);

  // 上/下卦
  if (orig.upper_tc && orig.lower_tc) {
    ctx.fillStyle = C.muted;
    ctx.font = font(400, 26, lang);
    const tri = isTc
      ? `上${orig.upper_tc.name}${orig.upper_tc.nature} · 下${orig.lower_tc.name}${orig.lower_tc.nature}`
      : `上${orig.upper_sc.name}${orig.upper_sc.nature} · 下${orig.lower_sc.name}${orig.lower_sc.nature}`;
    ctx.fillText(tri, cx, 972);
  }

  // 分隔线 + 菱形
  ctx.strokeStyle = C.gold;
  ctx.globalAlpha = 0.5;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(cx - 200, 1048);
  ctx.lineTo(cx - 40, 1048);
  ctx.moveTo(cx + 40, 1048);
  ctx.lineTo(cx + 200, 1048);
  ctx.stroke();
  ctx.globalAlpha = 1;
  ctx.save();
  ctx.translate(cx, 1048);
  ctx.rotate(Math.PI / 4);
  ctx.fillStyle = C.gold;
  ctx.fillRect(-6, -6, 12, 12);
  ctx.restore();

  // 金句
  ctx.fillStyle = C.body;
  ctx.font = font(400, 38, lang);
  ctx.textAlign = 'center';
  const lines = wrap(ctx, insight || '', 840);
  let ty = 1146;
  for (const ln of lines.slice(0, 4)) {
    ctx.fillText(ln, cx, ty);
    ty += 62;
  }

  // 底部分隔线
  ctx.strokeStyle = C.frame;
  ctx.globalAlpha = 0.35;
  ctx.beginPath();
  ctx.moveTo(130, 1546);
  ctx.lineTo(W - 130, 1546);
  ctx.stroke();
  ctx.globalAlpha = 1;

  // 二维码（构建期静态资产；加载失败则留空不阻断）
  try {
    const qr = await loadImage('/qr-home.png');
    ctx.drawImage(qr, 130, 1600, 240, 240);
  } catch {
    /* 忽略 */
  }

  // 底部文案
  ctx.textAlign = 'left';
  ctx.fillStyle = C.goldLight;
  ctx.font = font(500, 34, lang);
  ctx.fillText(isTc ? '掃碼起一卦，看看你的處境' : '扫码起一卦，看看你的处境', 430, 1662);
  ctx.fillStyle = C.muted;
  ctx.font = font(400, 30, lang);
  ctx.fillText('decision-book.vercel.app', 430, 1716);
  ctx.font = font(400, 24, lang);
  ctx.fillText(isTc ? '卦不預測吉凶，只幫你理清處境' : '卦不预测吉凶，只帮你理清处境', 430, 1766);
}
