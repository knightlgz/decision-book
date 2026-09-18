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

export default defineConfig({
  plugins: [
    devDirIndexPlugin(),
    react(),
    tailwindcss(),
  ],
  // dev 代理：本地 npm run dev 没有 /api 函数，转发到线上 Vercel（dev-only，仅本地联调用）
  server: {
    proxy: {
      '/api': { target: 'https://decision-book.vercel.app', changeOrigin: true },
    },
  },
})