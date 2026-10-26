import React, { useState } from 'react';
import { CreditCard, KeyRound, ShieldCheck, X } from 'lucide-react';
import { initiateCardBind, verifyCardBind } from '../services/api';
import { triggerHaptic } from '../services/telegram';

interface CardBindingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const CardBindingModal: React.FC<CardBindingModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [step, setStep] = useState<'input' | 'otp'>('input');
  const [provider, setProvider] = useState<'click' | 'payme'>('click');
  const [cardNumber, setCardNumber] = useState('');
  const [cardExpire, setCardExpire] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [cardToken, setCardToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleCardNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value.replace(/\D/g, '').slice(0, 16);
    // Format 4x4
    const formatted = val.replace(/(\d{4})(?=\d)/g, '$1 ');
    setCardNumber(formatted);
  };

  const handleExpireChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value.replace(/\D/g, '').slice(0, 4);
    if (val.length >= 2) {
      setCardExpire(`${val.slice(0, 2)}/${val.slice(2)}`);
    } else {
      setCardExpire(val);
    }
  };

  const cleanNum = cardNumber.replace(/\s/g, '');
  const cleanExp = cardExpire.replace(/\D/g, '');

  const handleSendCode = async () => {
    if (cleanNum.length !== 16) {
      setError("Karta raqami 16 ta raqamdan iborat bo'lishi kerak");
      return;
    }
    if (cleanExp.length !== 4) {
      setError("Amal qilish muddati to'liq kiritilishi kerak (MM/YY)");
      return;
    }

    setLoading(true);
    setError(null);
    triggerHaptic('light');

    try {
      const res = await initiateCardBind({
        provider,
        card_number: cleanNum,
        card_expire: cleanExp,
      });

      setCardToken(res.card_token);
      setStep('otp');
      triggerHaptic('selection');
    } catch (err: any) {
      setError(err.message || 'SMS kod yuborishda xatolik yuz berdi');
      triggerHaptic('error');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!otpCode || otpCode.length < 4) {
      setError("SMS orqali kelgan kodni to'liq kiriting");
      return;
    }

    setLoading(true);
    setError(null);
    triggerHaptic('light');

    try {
      const masked = `${cleanNum.slice(0, 4)} **** **** ${cleanNum.slice(-4)}`;
      await verifyCardBind({
        provider,
        card_token: cardToken,
        code: otpCode,
        card_number_masked: masked,
        card_expire: cleanExp,
      });

      triggerHaptic('success');
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || "SMS kod noto'g'ri yoki muddati o'tgan");
      triggerHaptic('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="w-full max-w-md bg-white dark:bg-[#17212b] border border-slate-200 dark:border-[#243343] rounded-3xl p-5 shadow-2xl transition-all">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-[#243343]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-blue-50 dark:bg-[#233447] text-[#2481cc] flex items-center justify-center">
              <CreditCard className="w-4 h-4 stroke-[2.2]" />
            </div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Bank Kartasini Ulash
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
        <div className="py-4 space-y-4">
          {error && (
            <div className="p-3 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs font-semibold">
              {error}
            </div>
          )}

          {step === 'input' ? (
            <>
              {/* Provider Selection */}
              <div>
                <label className="text-xs font-bold text-slate-500 dark:text-slate-400 mb-1.5 block">
                  To'lov tizimi:
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      triggerHaptic('selection');
                      setProvider('click');
                    }}
                    className={`py-2.5 px-3 rounded-2xl border text-xs font-bold flex items-center justify-center gap-2 transition cursor-pointer ${
                      provider === 'click'
                        ? 'bg-blue-600/15 border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    <span>Click</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      triggerHaptic('selection');
                      setProvider('payme');
                    }}
                    className={`py-2.5 px-3 rounded-2xl border text-xs font-bold flex items-center justify-center gap-2 transition cursor-pointer ${
                      provider === 'payme'
                        ? 'bg-emerald-600/15 border-emerald-500 text-emerald-600 dark:text-emerald-400'
                        : 'border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    <span>Payme</span>
                  </button>
                </div>
              </div>

              {/* Card Number */}
              <div>
                <label className="text-xs font-bold text-slate-500 dark:text-slate-400 mb-1.5 block">
                  Karta raqami (16 ta raqam):
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="8600 0000 0000 0000"
                  value={cardNumber}
                  onChange={handleCardNumberChange}
                  className="w-full px-3.5 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 text-slate-900 dark:text-white font-mono text-sm tracking-wider focus:outline-hidden focus:border-blue-500"
                />
              </div>

              {/* Expiry Date */}
              <div>
                <label className="text-xs font-bold text-slate-500 dark:text-slate-400 mb-1.5 block">
                  Amal qilish muddati (OO/YY):
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="12/28"
                  value={cardExpire}
                  onChange={handleExpireChange}
                  className="w-full px-3.5 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 text-slate-900 dark:text-white font-mono text-sm tracking-wider focus:outline-hidden focus:border-blue-500"
                />
              </div>

              <div className="flex items-center gap-2 text-[11px] text-slate-500 dark:text-slate-400 pt-1">
                <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>Karta ma'lumotlari xavfsiz shifrlangan holda saqlanadi</span>
              </div>

              <button
                type="button"
                onClick={handleSendCode}
                disabled={loading || cleanNum.length !== 16 || cleanExp.length !== 4}
                className="w-full py-3 rounded-2xl bg-blue-600 hover:bg-blue-500 active:scale-95 text-white font-bold text-xs sm:text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-blue-600/20 cursor-pointer"
              >
                {loading ? 'Yuborilmoqda...' : 'SMS Kod Olish'}
              </button>
            </>
          ) : (
            <>
              {/* OTP Step */}
              <div className="text-center py-2">
                <div className="w-12 h-12 rounded-full bg-blue-50 dark:bg-[#233447] text-[#2481cc] flex items-center justify-center mx-auto mb-2">
                  <KeyRound className="w-6 h-6 stroke-[2]" />
                </div>
                <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                  SMS Tasdiqlash Kodi
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Telefoningizga yuborilgan tasdiqlash kodini kiriting
                </p>
              </div>

              <div>
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="000000"
                  maxLength={6}
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                  className="w-full text-center px-4 py-3 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 text-slate-900 dark:text-white font-mono text-lg font-bold tracking-widest focus:outline-hidden focus:border-blue-500"
                />
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setStep('input')}
                  className="flex-1 py-2.5 rounded-2xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-bold text-xs transition cursor-pointer"
                >
                  Orqaga
                </button>
                <button
                  type="button"
                  onClick={handleVerify}
                  disabled={loading || otpCode.length < 4}
                  className="flex-2 py-2.5 rounded-2xl bg-blue-600 hover:bg-blue-500 active:scale-95 text-white font-bold text-xs transition disabled:opacity-50 cursor-pointer shadow-md shadow-blue-600/20"
                >
                  {loading ? 'Tekshirilmoqda...' : 'Ulashni Yakunlash'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
