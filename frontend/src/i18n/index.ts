import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import pt from '@/i18n/locales/pt/common.json';
import en from '@/i18n/locales/en/common.json';
import es from '@/i18n/locales/es/common.json';
import fr from '@/i18n/locales/fr/common.json';
import cn from '@/i18n/locales/cn/common.json';
import de from '@/i18n/locales/de/common.json';
// Determine initial language from persisted preference or browser
const persisted = (typeof window !== 'undefined' ? localStorage.getItem('lang') : null) || ''
const browserLang = (typeof navigator !== 'undefined' ? (navigator.language || (navigator as any).userLanguage || '') : '').split('-')[0]
const initialLang = (persisted || '').trim() || (browserLang || '').trim() || 'pt'

i18n.use(initReactI18next).init({
  resources: { pt: { translation: pt }, en: { translation: en }, es: { translation: es }, fr: { translation: fr }, cn: { translation: cn }, de: { translation: de } },
  lng: initialLang, fallbackLng: 'en', interpolation: { escapeValue: false },
});

// Persist changes to language and expose helper
export function setAppLanguage(lang: string){
  try{ if (typeof window !== 'undefined') localStorage.setItem('lang', lang) }catch{}
  i18n.changeLanguage(lang)
}
export default i18n;
