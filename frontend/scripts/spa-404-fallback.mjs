// Create 404.html as a copy of index.html for static hosts/CDNs that serve 404 directly
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs'
import { resolve } from 'node:path'

const dist = resolve(process.cwd(), 'dist')
const indexHtml = resolve(dist, 'index.html')
const target = resolve(dist, '404.html')

try {
  if (!existsSync(dist)) {
    console.warn('[spa-404-fallback] dist folder not found; skipping')
    process.exit(0)
  }
  if (!existsSync(indexHtml)) {
    console.warn('[spa-404-fallback] index.html not found; skipping')
    process.exit(0)
  }
  const html = readFileSync(indexHtml, 'utf-8')
  writeFileSync(target, html)
  console.log('[spa-404-fallback] Created 404.html for SPA fallback')
} catch (e) {
  console.warn('[spa-404-fallback] failed:', e?.message || e)
}
