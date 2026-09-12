import React, { useState } from 'react';
import { CheckCircle2, CreditCard, ShieldCheck, X, AlertCircle, Send } from 'lucide-react';
import { Course } from '../types';
import { initiatePurchase } from '../services/api';
import { triggerHaptic } from '../services/telegram';

interface PaymentModalProps {
  course: Course;
  isOpen: boolean;
  onClose: () => void;
  onSuccessEnrolled?: () => void;
}

export const PaymentModal: React.FC<PaymentModalProps> = ({
  course,
  isOpen,
  onClose,
  onSuccessEnrolled,
}) => {
  const [provider, setProvider] = useState<'click' | 'payme'>('click');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successData, setSuccessData] = useState<{ sale_id: string | number; amount: number } | null>(null);

  if (!isOpen) return null;

  const handlePurchase = async () => {
    triggerHaptic('medium');
    setLoading(true);
    setError(null);
    try {
      const res = await initiatePurchase(course.id, course.owner_node_id, provider);
      triggerHaptic('success');
      setSuccessData(res);
      if (onSuccessEnrolled) {
        onSuccessEnrolled();
      }
    } catch (err: any) {
      triggerHaptic('error');
      setError(err.message || 'To\'lov so\'rovini yuborishda xatolik yuz berdi');
    } finally {
      setLoading(false);
    }
  };

  const formattedPrice = new Intl.NumberFormat('uz-UZ').format(course.base_price);

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        className="w-full max-w-lg bg-tg-bg border border-tg-secondary rounded-t-3xl sm:rounded-3xl p-6 shadow-2xl transition-all max-h-[90vh] overflow-y-auto"
        role="dialog"
      >
        <div className="flex items-center justify-between pb-4 border-b border-tg-secondary">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-blue-500/10 text-blue-600 flex items-center justify-center">
              <CreditCard className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-base text-tg-text">Kursni xarid qilish</h3>
              <p className="text-xs text-tg-hint">Rasmiy to'lov tizimlari orqali</p>
            </div>
          </div>
          <button
            onClick={() => {
              triggerHaptic('light');
              onClose();
            }}
            className="p-2 rounded-full hover:bg-tg-secondary text-tg-hint hover:text-tg-text transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {successData ? (
          <div className="py-6 text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 mx-auto flex items-center justify-center animate-bounce">
              <CheckCircle2 className="w-8 h-8" />
            </div>

            <div className="space-y-1">
              <h4 className="text-lg font-bold text-tg-text">
                To'lov so'rovi yuborildi!
              </h4>
              <p className="text-sm text-emerald-600 dark:text-emerald-400 font-semibold">
                Iltimos, to'lovni yakunlash uchun Telegram botga qayting.
              </p>
            </div>

            <div className="bg-tg-secondary p-4 rounded-2xl text-left text-xs space-y-2 border border-tg-secondary">
              <div className="flex justify-between">
                <span className="text-tg-hint">Kurs nomi:</span>
                <span className="font-semibold text-tg-text text-right max-w-[200px] truncate">
                  {course.title}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-tg-hint">To'lov raqami (Sale ID):</span>
                <span className="font-mono font-bold text-blue-600 dark:text-blue-400">
                  {successData.sale_id}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-tg-hint">Summa:</span>
                <span className="font-bold text-tg-text">
                  {new Intl.NumberFormat('uz-UZ').format(successData.amount)} so'm
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-tg-hint">Provayder:</span>
                <span className="font-semibold uppercase text-tg-text">{provider}</span>
              </div>
            </div>

            <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl text-xs text-blue-600 dark:text-blue-300 flex items-start gap-2 text-left">
              <Send className="w-4 h-4 shrink-0 mt-0.5" />
              <span>
                Telegram botingizga to'lov havolasi va chek yuborildi. To'lov tasdiqlangach darslar avtomatik ravishda ochiladi.
              </span>
            </div>

            <button
              onClick={() => {
                triggerHaptic('light');
                onClose();
              }}
              className="w-full py-3 px-4 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm transition-all shadow-md active:scale-98 cursor-pointer"
            >
              Tushundim, davom etish
            </button>
          </div>
        ) : (
          <div className="py-4 space-y-5">
            {/* Course mini preview */}
            <div className="bg-tg-secondary p-3.5 rounded-2xl flex items-center justify-between border border-tg-secondary">
              <div className="flex-1 pr-3">
                <span className="text-[11px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider">
                  Tanlangan kurs
                </span>
                <h4 className="font-bold text-sm text-tg-text line-clamp-2 mt-0.5">
                  {course.title}
                </h4>
              </div>
              <div className="text-right shrink-0">
                <span className="text-xs text-tg-hint block">Narxi</span>
                <span className="font-black text-base text-tg-text text-blue-600 dark:text-blue-400">
                  {formattedPrice} <span className="text-xs font-normal">so'm</span>
                </span>
              </div>
            </div>

            {/* Provider selection */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-tg-text block">
                To'lov usulini tanlang:
              </label>
              <div className="grid grid-cols-2 gap-3">
                {/* Click */}
                <button
                  type="button"
                  onClick={() => {
                    triggerHaptic('selection');
                    setProvider('click');
                  }}
                  className={`p-3.5 rounded-2xl border flex flex-col items-center justify-center gap-1.5 transition-all cursor-pointer ${
                    provider === 'click'
                      ? 'border-blue-600 bg-blue-500/10 shadow-xs'
                      : 'border-tg-secondary bg-tg-secondary hover:bg-tg-secondary/80'
                  }`}
                >
                  <div className="font-black tracking-tight text-blue-500 text-lg">
                    CLICK
                  </div>
                  <span className="text-[11px] font-medium text-tg-hint">
                    Click Up / USSD / Web
                  </span>
                </button>

                {/* Payme */}
                <button
                  type="button"
                  onClick={() => {
                    triggerHaptic('selection');
                    setProvider('payme');
                  }}
                  className={`p-3.5 rounded-2xl border flex flex-col items-center justify-center gap-1.5 transition-all cursor-pointer ${
                    provider === 'payme'
                      ? 'border-teal-500 bg-teal-500/10 shadow-xs'
                      : 'border-tg-secondary bg-tg-secondary hover:bg-tg-secondary/80'
                  }`}
                >
                  <div className="font-black tracking-tight text-teal-500 text-lg">
                    Payme
                  </div>
                  <span className="text-[11px] font-medium text-tg-hint">
                    Payme Card / App
                  </span>
                </button>
              </div>
            </div>

            {error && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs text-rose-600 dark:text-rose-400 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <div className="flex items-center gap-2 text-xs text-tg-hint">
              <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0" />
              <span>Xavfsiz tranzaksiya & adaptiv dars ochilish kafolati</span>
            </div>

            <button
              id="btn-confirm-purchase"
              disabled={loading}
              onClick={handlePurchase}
              className="w-full py-3.5 px-4 rounded-2xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold text-sm transition-all shadow-md active:scale-98 cursor-pointer flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>To'lov so'rovini yuborish ({formattedPrice} so'm)</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
