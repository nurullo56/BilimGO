import React, { useState } from 'react';
import { submitQuizAnswer } from '../services/api';
import { triggerHaptic } from '../services/telegram';

interface LessonQuizProps {
  quizId: number;
  question: string;
  options: string[];
  onComplete?: (isCorrect: boolean) => void;
}

export const LessonQuizCard: React.FC<LessonQuizProps> = ({
  quizId,
  question,
  options,
  onComplete,
}) => {
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const [isSubmitted, setIsSubmitted] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [explanation, setExplanation] = useState<string>('');

  const handleSelect = (idx: number) => {
    if (isSubmitted) return;
    triggerHaptic('selection');
    setSelectedIdx(idx);
  };

  const handleSubmit = async () => {
    if (selectedIdx === null || isSubmitted || isSubmitting) return;
    setIsSubmitting(true);
    try {
      const data = await submitQuizAnswer(quizId, selectedIdx);
      setIsSubmitted(true);
      setIsCorrect(data.is_correct);
      setExplanation(data.explanation || '');
      if (data.is_correct) {
        triggerHaptic('success');
      } else {
        triggerHaptic('error');
      }
      if (onComplete) onComplete(data.is_correct);
    } catch (e) {
      console.error('Quiz yuborishda xatolik:', e);
      triggerHaptic('warning');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetry = () => {
    triggerHaptic('light');
    setSelectedIdx(null);
    setIsSubmitted(false);
    setIsCorrect(null);
    setExplanation('');
  };

  return (
    <div className="bg-tg-section border border-tg-secondary rounded-3xl p-4 sm:p-5 my-4 shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xl">📝</span>
        <div>
          <h4 className="text-sm sm:text-base font-bold text-tg-text">Dars Testi</h4>
          <span className="text-[11px] text-tg-hint">Mavzuni mustahkamlash uchun savolga javob bering</span>
        </div>
      </div>
      <p className="text-tg-text mb-4 text-xs sm:text-sm font-medium leading-relaxed">{question}</p>

      <div className="space-y-2 mb-4">
        {options.map((opt, idx) => {
          let btnClass = "w-full text-left p-3 rounded-2xl border text-xs sm:text-sm font-medium transition-all duration-200 cursor-pointer ";
          if (isSubmitted) {
            if (idx === selectedIdx && isCorrect) {
              btnClass += "bg-emerald-500/15 border-emerald-500 text-emerald-600 dark:text-emerald-400 font-bold";
            } else if (idx === selectedIdx && !isCorrect) {
              btnClass += "bg-rose-500/15 border-rose-500 text-rose-600 dark:text-rose-400 font-bold";
            } else {
              btnClass += "bg-tg-secondary/30 border-tg-secondary text-tg-hint opacity-60";
            }
          } else {
            if (idx === selectedIdx) {
              btnClass += "bg-blue-600/15 border-blue-600 text-blue-600 dark:text-blue-400 font-bold shadow-xs";
            } else {
              btnClass += "bg-tg-secondary/50 border-tg-secondary text-tg-text hover:border-blue-400 hover:bg-tg-secondary";
            }
          }

          return (
            <button
              key={idx}
              onClick={() => handleSelect(idx)}
              className={btnClass}
              disabled={isSubmitted || isSubmitting}
            >
              <div className="flex items-center gap-3">
                <span className="w-6 h-6 rounded-lg bg-tg-secondary border border-tg-secondary flex items-center justify-center text-xs font-bold shrink-0">
                  {String.fromCharCode(65 + idx)}
                </span>
                <span className="flex-1">{opt}</span>
              </div>
            </button>
          );
        })}
      </div>

      {!isSubmitted ? (
        <button
          onClick={handleSubmit}
          disabled={selectedIdx === null || isSubmitting}
          className="w-full py-2.5 px-4 rounded-2xl bg-blue-600 hover:bg-blue-500 active:scale-95 text-white font-bold text-xs sm:text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-blue-600/20 cursor-pointer"
        >
          {isSubmitting ? 'Tekshirilmoqda...' : 'Javobni tasdiqlash'}
        </button>
      ) : (
        <div className={`p-4 rounded-2xl border text-xs sm:text-sm mt-3 ${isCorrect ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-300' : 'bg-rose-500/10 border-rose-500/30 text-rose-700 dark:text-rose-300'}`}>
          <div className="flex items-center justify-between gap-2 font-bold mb-1">
            <span>{isCorrect ? '✅ To\'g\'ri javob! Barakalla!' : '❌ Noto\'g\'ri javob!'}</span>
            {!isCorrect && (
              <button
                onClick={handleRetry}
                className="px-2.5 py-1 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 text-rose-600 dark:text-rose-300 text-xs font-bold transition cursor-pointer"
              >
                Qayta urinish
              </button>
            )}
          </div>
          {explanation && <p className="text-xs text-tg-hint mt-1.5 leading-relaxed">{explanation}</p>}
        </div>
      )}
    </div>
  );
};
