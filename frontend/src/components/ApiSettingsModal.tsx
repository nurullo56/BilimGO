import React, { useState, useEffect } from 'react';
import { Check, Globe, Moon, RefreshCw, Shield, Sun, X } from 'lucide-react';
import { getApiBaseUrl, setApiBaseUrl, getBackendStatus, setMockFallback } from '../services/api';
import { getTelegramInitData, triggerHaptic, applyTelegramTheme } from '../services/telegram';

interface ApiSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRefresh?: () => void;
}

export const ApiSettingsModal: React.FC<ApiSettingsModalProps> = ({
  isOpen,
  onClose,
  onRefresh,
}) => {
  const [urlInput, setUrlInput] = useState(getApiBaseUrl());
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [currentTheme, setCurrentTheme] = useState<'light' | 'dark' | 'auto'>('auto');

  useEffect(() => {
    const saved = localStorage.getItem('bilimgo_theme') as 'light' | 'dark' | null;
    if (saved) {
      setCurrentTheme(saved);
    } else {
      setCurrentTheme('auto');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const status = getBackendStatus();
  const initData = getTelegramInitData();

  const handleSetTheme = (mode: 'light' | 'dark' | 'auto') => {
    triggerHaptic('selection');
    setCurrentTheme(mode);
    if (mode === 'auto') {
      localStorage.removeItem('bilimgo_theme');
    } else if (mode === 'dark') {
      localStorage.setItem('bilimgo_theme', 'dark');
    } else {
      localStorage.setItem('bilimgo_theme', 'light');
    }
    applyTelegramTheme();
  };

  const handleSave = () => {
    triggerHaptic('success');
    setApiBaseUrl(urlInput);
    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      onClose();
      if (onRefresh) onRefresh();
    }, 600);
  };

  const handleToggleMock = (checked: boolean) => {
    triggerHaptic('selection');
    setMockFallback(checked);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="w-full max-w-md bg-white dark:bg-[#17212b] border border-slate-200 dark:border-[#243343] rounded-3xl p-5 shadow-2xl transition-all max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-3.5 border-b border-slate-100 dark:border-[#243343]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-blue-50 dark:bg-[#233447] text-[#2481cc] flex items-center justify-center">
              <Globe className="w-4 h-4 stroke-[2.2]" />
            </div>
            <h3 className="font-bold text-base text-slate-900 dark:text-white">
              Platforma Sozlamalari
            </h3>
          </div>
          <button
            onClick={() => {
              triggerHaptic('light');
              onClose();
            }}
            className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 dark:bg-[#1c2733] dark:hover:bg-[#253241] text-slate-600 dark:text-slate-300 flex items-center justify-center transition cursor-pointer"
          >
            <X className="w-4 h-4 stroke-[2.2]" />
          </button>
        </div>

        <div className="py-4 space-y-4 text-xs">
          {/* Theme switcher (Tungi / Kunduzgi / Avto) */}
          <div>
            <label className="font-bold text-slate-800 dark:text-slate-200 block mb-2">
              Ko'rinish rejimi (Mavzu):
            </label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleSetTheme('light')}
                className={`py-2 px-3 rounded-xl border flex items-center justify-center gap-1.5 font-semibold transition cursor-pointer ${
                  currentTheme === 'light'
                    ? 'bg-blue-50 border-[#2481cc] text-[#2481cc] dark:bg-blue-500/10'
                    : 'bg-slate-50 dark:bg-[#1c2733] border-slate-200 dark:border-[#243343] text-slate-700 dark:text-slate-300'
                }`}
              >
                <Sun className="w-3.5 h-3.5" />
                <span>Kunduzgi</span>
              </button>

              <button
                type="button"
                onClick={() => handleSetTheme('dark')}
                className={`py-2 px-3 rounded-xl border flex items-center justify-center gap-1.5 font-semibold transition cursor-pointer ${
                  currentTheme === 'dark'
                    ? 'bg-blue-50 border-[#2481cc] text-[#2481cc] dark:bg-blue-500/10'
                    : 'bg-slate-50 dark:bg-[#1c2733] border-slate-200 dark:border-[#243343] text-slate-700 dark:text-slate-300'
                }`}
              >
                <Moon className="w-3.5 h-3.5" />
                <span>Tungi</span>
              </button>

              <button
                type="button"
                onClick={() => handleSetTheme('auto')}
                className={`py-2 px-3 rounded-xl border flex items-center justify-center gap-1.5 font-semibold transition cursor-pointer ${
                  currentTheme === 'auto'
                    ? 'bg-blue-50 border-[#2481cc] text-[#2481cc] dark:bg-blue-500/10'
                    : 'bg-slate-50 dark:bg-[#1c2733] border-slate-200 dark:border-[#243343] text-slate-700 dark:text-slate-300'
                }`}
              >
                <span>Avto (TG)</span>
              </button>
            </div>
          </div>

          {/* FastAPI Server URL */}
          <div>
            <label className="font-bold text-slate-800 dark:text-slate-200 block mb-1">
              Backend Server URL:
            </label>
            <input
              type="text"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="http://localhost:8000 yoki https://api.domain.uz"
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-[#1c2733] border border-slate-200 dark:border-[#243343] text-slate-900 dark:text-white font-mono focus:outline-none focus:ring-2 focus:ring-[#2481cc] text-xs"
            />
          </div>

          {/* Telegram Auth status */}
          <div className="bg-slate-50 dark:bg-[#1c2733] p-3 rounded-2xl space-y-2 border border-slate-200 dark:border-[#243343]">
            <div className="flex items-center gap-2 font-bold text-slate-800 dark:text-slate-200">
              <Shield className="w-4 h-4 text-emerald-500" />
              <span>Telegram Auth Holati:</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500 dark:text-slate-400">X-Telegram-Init-Data:</span>
              <span
                className={`font-semibold px-2 py-0.5 rounded-full text-[10px] ${
                  initData
                    ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
                    : 'bg-amber-500/15 text-amber-600 dark:text-amber-400'
                }`}
              >
                {initData ? 'Mavjud (Telegram WebApp)' : 'Lokal / Browser Dev'}
              </span>
            </div>
          </div>

          {/* Mock toggle */}
          <div className="flex items-center justify-between p-3 rounded-2xl bg-slate-50 dark:bg-[#1c2733] border border-slate-200 dark:border-[#243343]">
            <div>
              <span className="font-bold text-slate-800 dark:text-slate-200 block">Lokal / Demo rejim</span>
              <span className="text-[11px] text-slate-500 dark:text-slate-400">
                Backend ulanmagan bo'lsa lokal ma'lumotlar bilan ishlash
              </span>
            </div>
            <input
              type="checkbox"
              checked={status.useMockFallback}
              onChange={(e) => handleToggleMock(e.target.checked)}
              className="w-4 h-4 text-[#2481cc] rounded cursor-pointer accent-[#2481cc]"
            />
          </div>

          {/* Actions */}
          <div className="flex gap-2 pt-2">
            <button
              onClick={() => {
                triggerHaptic('light');
                localStorage.removeItem('bilimgo_cabinets');
                localStorage.removeItem('bilimgo_user_profile');
                localStorage.removeItem('bilimgo_last_lesson');
                setSavedSuccess(true);
                setTimeout(() => {
                  setSavedSuccess(false);
                  onClose();
                  if (onRefresh) onRefresh();
                }, 600);
              }}
              className="px-3 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-[#243343] dark:hover:bg-[#2b3e52] text-slate-700 dark:text-slate-200 font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer text-[11px]"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Keshni tozalash</span>
            </button>
            <button
              onClick={handleSave}
              className="flex-1 py-2.5 px-4 rounded-xl bg-[#2481cc] hover:bg-blue-600 text-white font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer"
            >
              {savedSuccess ? (
                <>
                  <Check className="w-4 h-4" />
                  <span>Saqlandi!</span>
                </>
              ) : (
                <span>Saqlash</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
