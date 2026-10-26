import React from 'react';
import { Bell, CheckCheck, X } from 'lucide-react';
import { triggerHaptic } from '../services/telegram';

interface NotificationsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const NotificationsModal: React.FC<NotificationsModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="w-full max-w-md bg-white dark:bg-[#17212b] border border-slate-200 dark:border-[#243343] rounded-3xl p-5 shadow-2xl transition-all">
        {/* Header */}
        <div className="flex items-center justify-between pb-3.5 border-b border-slate-100 dark:border-[#243343]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-blue-50 dark:bg-[#233447] text-[#2481cc] flex items-center justify-center">
              <Bell className="w-4 h-4 stroke-[2.2]" />
            </div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Bildirishnomalar
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

        {/* Content */}
        <div className="py-6 text-center">
          <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-slate-100 dark:bg-[#1c2733] flex items-center justify-center text-slate-400 dark:text-slate-500">
            <Bell className="w-7 h-7 stroke-[1.8]" />
          </div>
          <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-1">
            Yangi xabarnomalar yo'q
          </h4>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-xs mx-auto">
            Kurs yangiliklari, guruh e'lonlari va dars eslatmalari shu yerda ko'rinadi.
          </p>
        </div>

        {/* Action Button */}
        <button
          onClick={() => {
            triggerHaptic('light');
            onClose();
          }}
          className="w-full py-2.5 rounded-2xl bg-slate-100 hover:bg-slate-200 dark:bg-[#243343] dark:hover:bg-[#2b3e52] text-slate-800 dark:text-white font-semibold text-xs transition cursor-pointer flex items-center justify-center gap-1.5"
        >
          <CheckCheck className="w-4 h-4 text-[#2481cc]" />
          <span>Tushundim</span>
        </button>
      </div>
    </div>
  );
};
