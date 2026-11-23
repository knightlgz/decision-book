import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

const el = document.getElementById('app-root') || document.getElementById('root')
if (el) {
  createRoot(el).render(
    <StrictMode>
      <App embedded={el.dataset.island === '1'} />
    </StrictMode>,
  )
}
