import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import fs from 'fs'
import path from 'path'

// dev 环境：目录 URL（如 /hexagram/01/）命中 public 下对应的 index.html
// 对齐 Vercel 生产行为（Vercel 自带目录索引；vite dev 默认会 fallback 到 SPA）
function devDirIndexPlugin() {
  return {
    name: 'dev-dir-index',
    configureServer(server) {
      const publicDir = server.config.publicDir
      server.middlewares.use((req, res, next) => {
        const urlPath = (req.url || '').split('?')[0]
        if (urlPath.endsWith('/')) {
          const candidate = path.join(publicDir, decodeURIComponent(urlPath), 'index.html')
          if (fs.existsSync(candidate)) {
            req.url = urlPath + 'index.html'
          }
        }
        next()
      })
    },
  }
}

// SPA 入口 index.html 的 canonical / JSON-LD url：单一数据源注入（site_components.json）
function siteUrlPlugin() {
  return {
    name: 'site-url',
    transformIndexHtml(html) {
      const data = JSON.parse(fs.readFileSync(path.resolve('src/data/site_components.json'), 'utf-8'))
      return html.replaceAll('__SITE_URL__', data.site_url)
    },
  }
}

export default defineConfig({
  plugins: [
    devDirIndexPlugin(),
    siteUrlPlugin(),
    react(),
    tailwindcss(),
  ],
  // dev 代理：本地 npm run dev 没有 /api 函数，转发到线上 Vercel（dev-only，仅本地联调用）
  // 注：起卦为纯前端计算（src/lib/seed.js），不经过 /api；此代理仅供报告生成 /api/dify 联调
  server: {
    proxy: {
      '/api': { target: 'https://kysonsbook.com', changeOrigin: true },
    },
  },
})
