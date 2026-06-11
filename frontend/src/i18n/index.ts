import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import en from './locales/en.json';
import ur from './locales/ur.json';

const resources = {
  en: {
    translation: en,
  },
  ur: {
    translation: ur,
  },
};

const normalizeLanguage = (lng: string) => (lng?.startsWith('ur') ? 'ur' : 'en');

const applyDocumentLanguage = (lng: string) => {
  const normalized = normalizeLanguage(lng);
  document.documentElement.lang = normalized;
  document.documentElement.dir = normalized === 'ur' ? 'rtl' : 'ltr';
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false, // react already safes from xss
    },
  });

i18n.on('languageChanged', applyDocumentLanguage);
applyDocumentLanguage(i18n.language || 'en');

export default i18n;
