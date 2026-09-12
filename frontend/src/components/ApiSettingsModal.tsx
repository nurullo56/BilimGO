import React, { useState } from 'react';
import { Check, Globe, RefreshCw, Shield, X, AlertCircle } from 'lucide-react';
import { getApiBaseUrl, setApiBaseUrl, getBackendStatus } from '../services/api';
import { getTelegramInitData, triggerHaptic } from '../services/telegram';

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
  const status = getBackendStatus();
  const initData = getTelegramInitData();

  if (!isOpen) return null;

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
      <div className="w-full max-w-md bg-tg-bg border border-tg-secondary rounded-3xl p-6 shadow-2xl transition-all max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between pb-3 border-b border-tg-secondary">
          <div className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <h3 className="font-bold text-base text-tg-text">API & Backend Sozlamalari</h3>
          </div>
          <button
            onClick={() => {
              triggerHaptic('light');
              onClose();
            }}
            className="p-1.5 rounded-full hover:bg-tg-secondary text-tg-hint hover:text-tg-text transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="py-4 space-y-4 text-xs">
          <div>
            <label className="font-bold text-tg-text block mb-1">
              FastAPI Server URL (API_BASE):
            </label>
            <input
              type="text"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="http://localhost:8000 yoki https://api.domain.uz"
              className="w-full px-3.5 py-2.5 rounded-xl bg-tg-secondary border border-tg-secondary text-tg-text font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs"
            />
            <p className="text-[11px] text-tg-hint mt-1">
              Default qiymat: <code className="text-blue-600 dark:text-blue-400">http://localhost:8000</code>. Istalgan vaqtda o'zgartirishingiz mumkin.
            </p>
          </div>

          <div className="bg-tg-secondary p-3 rounded-2xl space-y-2 border border-tg-secondary">
            <div className="flex items-center gap-2 font-bold text-tg-text">
              <Shield className="w-4 h-4 text-emerald-500" />
              <span>Telegram Auth Holati:</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-tg-hint">X-Telegram-Init-Data:</span>
              <span className={`font-semibold px-2 py-0.5 rounded-full text-[10px] ${
                initData ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400' : 'bg-amber-500/15 text-amber-600 dark:text-amber-400'
              }`}>
                {initData ? 'Mavjud (Telegram WebApp)' : 'Lokal / Browser Dev'}
              </span>
            </div>
            {initData && (
              <div className="p-2 bg-tg-bg rounded-lg font-mono text-[10px] text-tg-hint truncate">
                {initData.slice(0, 60)}...
              </div>
            )}
          </div>

          <div className="flex items-center justify-between p-3 rounded-2xl bg-tg-secondary border border-tg-secondary">
            <div>
              <span className="font-bold text-tg-text block">Lokal / Demo rejim</span>
              <span className="text-[11px] text-tg-hint">
                Backend ulanmagan bo'lsa to'liq o'quv namunalarini ko'rsatish
              </span>
            </div>
            <input
              type="checkbox"
              checked={status.useMockFallback}
              onChange={(e) => handleToggleMock(e.target.checked)}
              className="w-4 h-4 text-blue-600 rounded cursor-pointer accent-blue-600"
            />
          </div>

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
              className="px-3 py-2.5 rounded-xl bg-tg-secondary hover:bg-tg-secondary/80 text-tg-text font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer text-[11px]"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Keshni tozalash</span>
            </button>
            <button
              onClick={handleSave}
              className="flex-1 py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold transition-all flex items-center justify-center gap-1.5 cursor-pointer"
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
