import React, { useState } from 'react';
import { submitQuizAnswer } from '../services/api';
import { triggerHaptic } from '../services/telegram';
import { LessonQuiz } from '../services/api';

interface LessonQuizCardProps {
  quizzes: LessonQuiz[];
  onAllComplete?: () => void;
}

export const LessonQuizCard: React.FC<LessonQuizCardProps> = ({
  quizzes,
  onAllComplete,
}) => {
  const [currentIdx, setCurrentIdx] = useState<number>(0);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const [isSubmitted, setIsSubmitted] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [explanation, setExplanation] = useState<string>('');
  const [isAllCompleted, setIsAllCompleted] = useState<boolean>(false);

  if (!quizzes || quizzes.length === 0) {
    return null;
  }

  const currentQuiz = quizzes[currentIdx];
  const total = quizzes.length;
  const progressPercent = Math.round(((currentIdx + (isSubmitted && isCorrect ? 1 : 0)) / total) * 100);

  const handleSelect = (idx: number) => {
    if (isSubmitted) return;
    triggerHaptic('selection');
    setSelectedIdx(idx);
  };

  const handleSubmit = async () => {
    if (selectedIdx === null || isSubmitted || isSubmitting || !currentQuiz) return;
    setIsSubmitting(true);
    try {
      const data = await submitQuizAnswer(currentQuiz.id, selectedIdx);
      setIsSubmitted(true);
      setIsCorrect(data.is_correct);
      setExplanation(data.explanation || '');
      if (data.is_correct) {
        triggerHaptic('success');
      } else {
        triggerHaptic('error');
      }
    } catch (e) {
      console.error('Quiz tekshirishda xatolik:', e);
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

  const handleNext = () => {
    triggerHaptic('selection');
    if (currentIdx + 1 < total) {
      setCurrentIdx((prev) => prev + 1);
      setSelectedIdx(null);
      setIsSubmitted(false);
      setIsCorrect(null);
      setExplanation('');
    } else {
      setIsAllCompleted(true);
      triggerHaptic('success');
      if (onAllComplete) {
        onAllComplete();
      }
    }
  };

  if (isAllCompleted) {
    return (
      <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-3xl p-5 sm:p-6 my-4 text-center space-y-3 shadow-md animate-in zoom-in-95 duration-300">
        <div className="w-14 h-14 mx-auto rounded-2xl bg-emerald-500/20 text-emerald-500 flex items-center justify-center text-3xl shadow-inner">
          🎉
        </div>
        <div>
          <h4 className="text-base sm:text-lg font-black text-emerald-600 dark:text-emerald-400">
            Barakalla! Barcha testlarni yakunladingiz!
          </h4>
          <p className="text-xs sm:text-sm text-tg-hint mt-1">
            Dars 100% muvaffaqiyatli o'zlashtirildi. Keyingi darsga bemalol o'tishingiz mumkin!
          </p>
        </div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-bold">
          <span>✅ Barcha javoblar to'g'ri ({total}/{total})</span>
        </div>
      </div>
    );
  }

  return (
    <div
      key={currentQuiz.id}
      className="bg-tg-section border border-tg-secondary rounded-3xl p-4 sm:p-5 my-4 shadow-sm animate-in fade-in duration-300"
    >
      {/* Header: Title and Progress */}
      <div className="flex items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">📝</span>
          <div>
            <h4 className="text-sm sm:text-base font-bold text-tg-text">Dars Testi</h4>
            <span className="text-[11px] text-tg-hint">To'g'ri javobni tanlang</span>
          </div>
        </div>

        <div className="text-right">
          <span className="inline-block px-2.5 py-1 rounded-xl bg-blue-600/15 border border-blue-500/30 text-blue-600 dark:text-blue-400 font-extrabold text-xs">
            Savol: {currentIdx + 1} / {total}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-tg-secondary/60 h-1.5 rounded-full overflow-hidden mb-4">
        <div
          className="bg-blue-600 h-full rounded-full transition-all duration-300 ease-out"
          style={{ width: `${Math.max(5, progressPercent)}%` }}
        />
      </div>

      {/* Question */}
      <p className="text-tg-text mb-4 text-xs sm:text-sm font-semibold leading-relaxed">
        {currentQuiz.question}
      </p>

      {/* Options */}
      <div className="space-y-2 mb-4">
        {currentQuiz.options.map((opt, idx) => {
          let btnClass = "w-full text-left p-3 rounded-2xl border text-xs sm:text-sm font-medium transition-all duration-200 cursor-pointer ";
          if (isSubmitted) {
            if (idx === selectedIdx && isCorrect) {
              btnClass += "bg-emerald-500/15 border-emerald-500 text-emerald-600 dark:text-emerald-400 font-bold shadow-xs";
            } else if (idx === selectedIdx && !isCorrect) {
              btnClass += "bg-rose-500/15 border-rose-500 text-rose-600 dark:text-rose-400 font-bold shadow-xs";
            } else {
              btnClass += "bg-tg-secondary/30 border-tg-secondary text-tg-hint opacity-50";
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
                <span className="flex-1 leading-snug">{opt}</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Submit or Result Action */}
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
            <span>{isCorrect ? "✅ To'g'ri javob! Barakalla!" : "❌ Noto'g'ri javob!"}</span>
            {!isCorrect ? (
              <button
                onClick={handleRetry}
                className="px-3 py-1.5 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 text-rose-600 dark:text-rose-300 text-xs font-bold transition cursor-pointer"
              >
                Qayta urinish
              </button>
            ) : (
              <button
                onClick={handleNext}
                className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-extrabold shadow-md shadow-emerald-600/20 active:scale-95 transition cursor-pointer flex items-center gap-1.5"
              >
                <span>{currentIdx + 1 < total ? 'Keyingi savol' : 'Yakunlash'}</span>
                <span>➡️</span>
              </button>
            )}
          </div>
          {explanation && <p className="text-xs text-tg-hint mt-2 leading-relaxed">{explanation}</p>}
        </div>
      )}
    </div>
  );
};
