// api/dify.js (Vercel Serverless Function)
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const response = await fetch('https://api.dify.ai/v1/workflows/run', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.DIFY_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(req.body)
    });

    const data = await response.json();
    // 上游非 200 时附带状态码，便于前端/日志定位
    if (!response.ok) {
      console.error('[dify-proxy] upstream status', response.status, JSON.stringify(data).slice(0, 500));
    }
    res.status(200).json(data);
  } catch (error) {
    // 关键：把真实错误写进 Vercel Functions 日志 + 返回给前端
    console.error('[dify-proxy] fetch failed:', error?.message || String(error));
    res.status(502).json({ error: error?.message || 'Failed to fetch Dify API' });
  }
}
