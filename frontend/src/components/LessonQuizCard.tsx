import React, { useState } from 'react';

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
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [explanation, setExplanation] = useState<string>('');

  const handleSelect = (idx: number) => {
    if (isSubmitted) return;
    setSelectedIdx(idx);
  };

  const handleSubmit = async () => {
    if (selectedIdx === null || isSubmitted) return;
    try {
      const res = await fetch(`/api/quizzes/${quizId}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ selected_option_index: selectedIdx }),
      });
      const data = await res.json();
      setIsSubmitted(true);
      setIsCorrect(data.is_correct);
      setExplanation(data.explanation || '');
      if (onComplete) onComplete(data.is_correct);
    } catch (e) {
      console.error('Quiz yuborishda xatolik:', e);
    }
  };

  return (
    <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-5 my-4 shadow-lg backdrop-blur-sm">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xl">📝</span>
        <h4 className="text-base font-semibold text-white">Dars Testi</h4>
      </div>
      <p className="text-slate-200 mb-4 text-sm leading-relaxed">{question}</p>

      <div className="space-y-2 mb-4">
        {options.map((opt, idx) => {
          let btnClass = "w-full text-left p-3 rounded-xl border text-sm transition-all duration-200 ";
          if (isSubmitted) {
            if (idx === selectedIdx && isCorrect) {
              btnClass += "bg-emerald-500/20 border-emerald-500 text-emerald-300";
            } else if (idx === selectedIdx && !isCorrect) {
              btnClass += "bg-rose-500/20 border-rose-500 text-rose-300";
            } else {
              btnClass += "bg-slate-900/40 border-slate-700/40 text-slate-400 opacity-60";
            }
          } else {
            if (idx === selectedIdx) {
              btnClass += "bg-blue-600/30 border-blue-500 text-blue-200 shadow-md";
            } else {
              btnClass += "bg-slate-900/60 border-slate-700/60 text-slate-300 hover:border-slate-500 hover:bg-slate-800";
            }
          }

          return (
            <button
              key={idx}
              onClick={() => handleSelect(idx)}
              className={btnClass}
              disabled={isSubmitted}
            >
              <div className="flex items-center gap-3">
                <span className="w-6 h-6 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-semibold">
                  {String.fromCharCode(65 + idx)}
                </span>
                <span>{opt}</span>
              </div>
            </button>
          );
        })}
      </div>

      {!isSubmitted ? (
        <button
          onClick={handleSubmit}
          disabled={selectedIdx === null}
          className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium text-sm hover:from-blue-500 hover:to-indigo-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
        >
          Javobni tasdiqlash
        </button>
      ) : (
        <div className={`p-3 rounded-xl border text-sm mt-3 ${isCorrect ? 'bg-emerald-950/40 border-emerald-800/50 text-emerald-300' : 'bg-rose-950/40 border-rose-800/50 text-rose-300'}`}>
          <div className="flex items-center gap-2 font-semibold mb-1">
            <span>{isCorrect ? '✅ To\'g\'ri javob!' : '❌ Noto\'g\'ri javob!'}</span>
          </div>
          {explanation && <p className="text-xs text-slate-300 mt-1">{explanation}</p>}
        </div>
      )}
    </div>
  );
};
