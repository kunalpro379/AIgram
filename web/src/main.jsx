import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import aigramIco from './assets/aigram.png'
import './index.css'
import App from './App.jsx'

function setLinkIcon(rel, href) {
  let el = document.querySelector(`link[rel="${rel}"]`)
  if (!el) {
    el = document.createElement('link')
    el.rel = rel
    document.head.appendChild(el)
  }
  el.href = href
  if (rel === 'icon') el.type = 'image/png'
}

setLinkIcon('icon', aigramIco)
setLinkIcon('apple-touch-icon', aigramIco)

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
