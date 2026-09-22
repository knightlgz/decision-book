/**
 * 起卦（铜钱法 18 位抽象，2026-09-22 机制定稿）
 *
 * 三枚硬币 × 6 次 = 18 位二进制串；每 3 位一爻（自下而上：初爻→上爻）。
 * 四象映射（0＝阳面、1＝阴面）——口诀「落单的那面定阴阳；三枚全同＝该面进「老」（动）」：
 *   000 = 老阳（动，○）  100/010/001 = 少阴  110/101/011 = 少阳  111 = 老阴（动，✕）
 * 本卦 = 动前排（老阳/少阳=阳，少阴/老阴=阴）；变卦（动后排）留待变卦篇。
 *
 * 派生要素（全部非隐私项，纯前端计算、零网络依赖）：
 *   问题文本 + 地区（用户发问时所选）+ 设备系统时间（时辰粒度）+ 浏览器指纹。
 * 全流程确定性：同问同人同窗 → 同卦同局；用户动作＝揭晓，不是抽奖。
 */

// 32 位字符串哈希（FNV-1a 变体；跨端稳定，不依赖平台中文编码）
export function hash32(str) {
  let h = 0x811c9dc5;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

// 时辰（2 小时窗）：设备系统时间的粒度——窗内同问同人可复现
export function shichenOf(ms) {
  const d = new Date(ms);
  return Math.floor(((d.getHours() + 1) % 24) / 2);
}

// 浏览器指纹（不涉及隐私的四维；非浏览器环境返回空串）
export function deviceFingerprint() {
  if (typeof navigator === 'undefined') return '';
  let tz = '';
  try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch { /* noop */ }
  const w = typeof screen !== 'undefined' ? screen.width || '' : '';
  return [navigator.language || '', tz, String(w), navigator.platform || ''].join('|');
}

// 18 位 → 六爻四象（自下而上）
export function statesFromBits18(bits) {
  const states = [];
  for (let i = 0; i < 6; i++) {
    const k = bits[i * 3] + bits[i * 3 + 1] + bits[i * 3 + 2];
    states.push(k === 0 ? 'laoyang' : k === 1 ? 'shaoyin' : k === 2 ? 'shaoyang' : 'laoyin');
  }
  return states;
}

// 四象 → 本卦极性（动前）：老阳/少阳=1（阳），少阴/老阴=0（阴）
export function arrFromStates(states) {
  return states.map((s) => (s === 'laoyang' || s === 'shaoyang' ? 1 : 0));
}

// 起卦主函数（纯函数、跨端）：要素 → { bits, states, arr, moving }
export function castFromFactors({ question, region = '', fingerprint = '', shichen = 0 }) {
  const base = ['cast', String(question || '').trim(), region, String(shichen), fingerprint].join('|');
  let s = hash32(base) || 0x9e3779b9; // 兜底非零种子
  const next = () => {
    s ^= s << 13; s >>>= 0;
    s ^= s >>> 17;
    s ^= s << 5; s >>>= 0;
    return s;
  };
  const bits = [];
  for (let i = 0; i < 18; i++) bits.push(next() & 1);
  const states = statesFromBits18(bits);
  const arr = arrFromStates(states);
  const moving = states.map((st) => st === 'laoyang' || st === 'laoyin');
  return { bits, states, arr, moving };
}

// 起卦入口（纯前端）：问题 + 用户所选地区 + 当前时辰 + 本机指纹 → 本卦与动爻
export function castQuestion(question, region = '') {
  const shichen = shichenOf(Date.now());
  const fingerprint = deviceFingerprint();
  return castFromFactors({ question, region, fingerprint, shichen });
}
