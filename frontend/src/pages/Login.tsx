import { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useTranslation } from "react-i18next";
import { setAppLanguage } from "@/i18n";

const LANGUAGES = [
  { code: "pt", label: "PT", flag: "🇵🇹", name: "Português" },
  { code: "en", label: "EN", flag: "🇬🇧", name: "English" },
  { code: "es", label: "ES", flag: "🇪🇸", name: "Español" },
  { code: "fr", label: "FR", flag: "🇫🇷", name: "Français" },
  { code: "de", label: "DE", flag: "🇩🇪", name: "Deutsch" },
  { code: "cn", label: "CN", flag: "🇨🇳", name: "中文" },
  { code: "ar", label: "AR", flag: "🇸🇦", name: "العربية" },
];

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const location = useLocation();
  const from = (location.state as any)?.from?.pathname || "/";
  const { t, i18n } = useTranslation();
  const [showLangMenu, setShowLangMenu] = useState(false);
  const langMenuRef = useRef<HTMLDivElement>(null);

  const [username, setU] = useState("");
  const [password, setP] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const currentLang = LANGUAGES.find((l) => l.code === i18n.language) || LANGUAGES[0];

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (langMenuRef.current && !langMenuRef.current.contains(event.target as Node)) {
        setShowLangMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const changeLang = (code: string) => {
    setAppLanguage(code);
    setShowLangMenu(false);
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      await login(username, password);
      nav(from, { replace: true });
    } catch (e: any) {
      setErr(e?.message || t("login_error"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid place-items-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 px-4">
      <div className="w-full max-w-md">
        {/* Language Selector */}
        <div className="flex justify-end mb-4 animate-fadeIn">
          <div className="relative" ref={langMenuRef}>
            <button
              onClick={() => setShowLangMenu(!showLangMenu)}
              className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-all duration-200"
            >
              <span className="text-lg">{currentLang.flag}</span>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{currentLang.label}</span>
              <svg
                className={`w-4 h-4 text-gray-500 transition-transform duration-200 ${showLangMenu ? "rotate-180" : ""}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {showLangMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 py-1 z-50 animate-fadeIn">
                {LANGUAGES.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => changeLang(lang.code)}
                    className={`w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                      lang.code === i18n.language ? "bg-blue-50 dark:bg-blue-900/20" : ""
                    }`}
                  >
                    <span className="text-lg">{lang.flag}</span>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">{lang.name}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">{lang.label}</div>
                    </div>
                    {lang.code === i18n.language && (
                      <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Logo and Title Card */}
        <div className="text-center mb-8 animate-fadeIn">
          <div className="flex items-center justify-center gap-3 mb-4">
            <img 
              src="/assets/logos/vivae-erp-logo-main.svg" 
              alt="VIVAE ERP" 
              className="h-12 w-auto transition-transform duration-300 hover:scale-110" 
            />
            <span className="text-3xl font-bold text-gray-800 dark:text-gray-100">VIVAE ERP</span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">{t("login_subtitle")}</p>
        </div>

        {/* Login Form Card */}
        <form 
          onSubmit={onSubmit} 
          className="bg-white dark:bg-gray-900 p-8 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 transition-all duration-300 hover:shadow-3xl"
        >
          <h1 className="text-2xl font-semibold mb-6 text-gray-900 dark:text-gray-100">{t("login_title")}</h1>
          
          {err && (
            <div className="bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 p-4 rounded-lg mb-6 border border-red-200 dark:border-red-800 animate-shake">
              <div className="flex items-center gap-2">
                <span className="text-lg">⚠️</span>
                <span className="text-sm font-medium">{err}</span>
              </div>
            </div>
          )}
          
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">{t("login_username_label")}</label>
              <input 
                value={username} 
                onChange={(e) => setU(e.target.value)} 
                className="input w-full transition-all duration-200 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400" 
                placeholder={t("login_username_placeholder")}
                autoComplete="username"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">{t("login_password_label")}</label>
              <input 
                type="password" 
                value={password} 
                onChange={(e) => setP(e.target.value)} 
                className="input w-full transition-all duration-200 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400" 
                placeholder={t("login_password_placeholder")}
                autoComplete="current-password"
              />
            </div>
          </div>
          
          <button 
            disabled={loading} 
            className="btn btn-primary w-full mt-8 py-3 text-base font-semibold transition-all duration-200 hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {t("login_loading")}
              </span>
            ) : (
              t("login_button")
            )}
          </button>
        </form>

        {/* Footer */}
        <div className="text-center mt-6 text-xs text-gray-500 dark:text-gray-400">
          {t("login_footer")}
        </div>
      </div>
    </div>
  );
}
