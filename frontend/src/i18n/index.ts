
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import pt from '@/i18n/locales/pt/common.json';
import en from '@/i18n/locales/en/common.json';
import es from '@/i18n/locales/es/common.json';
import fr from '@/i18n/locales/fr/common.json';
import cn from '@/i18n/locales/cn/common.json';
i18n.use(initReactI18next).init({
  resources: { pt: { translation: pt }, en: { translation: en }, es: { translation: es }, fr: { translation: fr }, cn: { translation: cn } },
  lng: 'pt', fallbackLng: 'en', interpolation: { escapeValue: false },
});
export default i18n;
