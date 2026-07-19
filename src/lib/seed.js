/**
 * 时辰起卦法：时辰 + 问题哈希 + 匿名四维指纹 → 同时同问不同人得不同卦
 * 指纹维度均无需用户授权，不涉及个人隐私，同设备稳定一致
 */
export function generateHexagramIndex(question) {
  const now = new Date();
  const shichen = Math.floor(((now.getHours() + 1) % 24) / 2);

  const hash = (s) => {
    let h = 0;
    for (let i = 0; i < s.length; i++) {
      h = ((h << 5) - h) + s.charCodeAt(i);
      h |= 0;
    }
    return Math.abs(h);
  };

  const fingerprint = [
    navigator.language,
    Intl.DateTimeFormat().resolvedOptions().timeZone || "",
    screen.width,
    navigator.platform || "",
  ].join("|");

  const seed = shichen * 100000 + hash(question) + hash(fingerprint);
  return seed % 64;
}
