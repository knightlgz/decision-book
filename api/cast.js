// api/cast.js (Vercel Serverless Function) —— 起卦：服务端注入 IP 因子（仅入哈希，不落地存储）
// 机制：铜钱法 18 位抽象（见 decision-book-dev/references/variation-design.md）
// 兼容两种运行环境：Vercel（req.body 已解析）/ vite dev 中间件（connect 原始流）
import { castFromFactors } from '../src/lib/seed.js';

function send(res, code, obj) {
  res.statusCode = code;
  if (typeof res.setHeader === 'function') res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.end(JSON.stringify(obj));
}

async function readBody(req) {
  if (req.body && typeof req.body === 'object') return req.body; // Vercel 自动解析
  const chunks = [];
  for await (const c of req) chunks.push(c); // dev（connect）手动收集
  try { return JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}'); } catch { return {}; }
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return send(res, 405, { ok: false, error: 'Method not allowed' });
  try {
    const body = await readBody(req);
    const question = String(body.question || '').slice(0, 256);
    const fingerprint = String(body.fingerprint || '').slice(0, 256);
    const shichen = Number.isFinite(+body.shichen) ? Math.abs(Math.floor(+body.shichen)) % 12 : 0;
    // IP 仅参与哈希：取链路首段；不返回、不写日志、不存储
    const ipSalt = String((req.headers && req.headers['x-forwarded-for']) || '').split(',')[0].trim() || 'local';
    const cast = castFromFactors({ question, fingerprint, shichen, ipSalt });
    send(res, 200, { ok: true, arr: cast.arr, states: cast.states, moving: cast.moving, bits: cast.bits });
  } catch (error) {
    console.error('[cast] failed:', (error && error.message) || String(error));
    send(res, 502, { ok: false, error: 'cast failed' });
  }
}
