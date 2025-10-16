import fs from 'fs'
import path from 'path'

const localesDir = path.resolve(process.cwd(), 'src/i18n/locales')
const baseLang = 'pt'
const baseFile = path.join(localesDir, baseLang, 'common.json')

function flatKeys(obj, prefix=''){
  const out = []
  for (const [k,v] of Object.entries(obj||{})){
    const key = prefix ? `${prefix}.${k}` : k
    if (v && typeof v === 'object' && !Array.isArray(v)) out.push(...flatKeys(v, key))
    else out.push(key)
  }
  return out
}

function readJSON(p){ return JSON.parse(fs.readFileSync(p, 'utf-8')) }

const base = readJSON(baseFile)
const baseKeys = new Set(flatKeys(base))
const langs = fs.readdirSync(localesDir).filter(d=>fs.statSync(path.join(localesDir,d)).isDirectory())
let missing = []
for (const lang of langs){
  if (lang === baseLang) continue
  const f = path.join(localesDir, lang, 'common.json')
  const data = readJSON(f)
  const keys = new Set(flatKeys(data))
  for (const k of baseKeys){ if (!keys.has(k)) missing.push({ lang, key: k }) }
}

if (missing.length){
  console.error('[i18n] Missing keys:')
  for (const m of missing){ console.error(` - ${m.lang}: ${m.key}`) }
  process.exit(1)
} else {
  console.log('[i18n] All locales in sync with base.')
}
