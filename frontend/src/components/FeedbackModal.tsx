import React, { useState } from 'react';
import {
  X,
  MessageSquare,
  Star,
  Send,
  CheckCircle2,
  Sparkles,
  Lightbulb,
  AlertTriangle,
  HeartHandshake,
} from 'lucide-react';
import { triggerHaptic } from '../services/telegram';
import { submitStudentFeedback } from '../services/api';

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  courseId?: number | string | null;
  lessonId?: number | string | null;
  courseTitle?: string | null;
  lessonTitle?: string | null;
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
  isOpen,
  onClose,
  courseId,
  lessonId,
  courseTitle,
  lessonTitle,
}) => {
  const [rating, setRating] = useState<number>(5);
  const [hoverRating, setHoverRating] = useState<number>(0);
  const [category, setCategory] = useState<'general' | 'lesson' | 'suggestion' | 'bug'>('general');
  const [comment, setComment] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isSuccess, setIsSuccess] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleStarClick = (selectedStar: number) => {
    triggerHaptic('selection');
    setRating(selectedStar);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (comment.trim().length < 3) {
      setError('Iltimos, fikringizni kamida bir necha so‘z bilan yozing.');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    triggerHaptic('medium');

    try {
      await submitStudentFeedback({
        rating,
        comment: comment.trim(),
        category,
        course_id: courseId,
        lesson_id: lessonId,
      });

      triggerHaptic('success');
      setIsSuccess(true);
      setTimeout(() => {
        setIsSuccess(false);
        setComment('');
        setRating(5);
        onClose();
      }, 2000);
    } catch (err: any) {
      console.error('Feedback yuborishda xatolik:', err);
      setError(err.message || 'Xatolik yuz berdi. Iltimos qaytadan urinib ko‘ring.');
      triggerHaptic('warning');
    } finally {
      setIsSubmitting(false);
    }
  };

  const categories = [
    { id: 'general', label: 'Umumiy fikr', icon: HeartHandshake },
    { id: 'lesson', label: 'Dars sifati', icon: Sparkles },
    { id: 'suggestion', label: 'Taklif', icon: Lightbulb },
    { id: 'bug', label: 'Muammo', icon: AlertTriangle },
  ] as const;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-md bg-white dark:bg-slate-900 rounded-3xl p-6 shadow-2xl border border-slate-100 dark:border-slate-800 transition-all">
        {/* Yopish tugmasi */}
        <button
          onClick={() => {
            triggerHaptic('light');
            onClose();
          }}
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {isSuccess ? (
          <div className="py-8 text-center flex flex-col items-center justify-center space-y-3">
            <div className="w-16 h-16 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-500 flex items-center justify-center animate-bounce">
              <CheckCircle2 className="w-10 h-10" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white">
              Fikringiz qabul qilindi! 🎉
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-xs">
              Platformamizni yaxshilashga qo‘shgan hissangiz uchun katta rahmat!
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Header */}
            <div className="text-center space-y-1">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 mb-1">
                <MessageSquare className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                Fikr-mulohaza bildirish
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {lessonTitle
                  ? `«${lessonTitle}» darsi bo‘yicha`
                  : courseTitle
                  ? `«${courseTitle}» kursi bo‘yicha`
                  : 'BilimGo platformasi bo‘yicha fikr va takliflaringiz'}
              </p>
            </div>

            {/* Yulduzchalar (Rating) */}
            <div className="flex flex-col items-center justify-center py-2 space-y-1">
              <div className="flex items-center space-x-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => handleStarClick(star)}
                    onMouseEnter={() => setHoverRating(star)}
                    onMouseLeave={() => setHoverRating(0)}
                    className="p-1 transition-transform hover:scale-125 active:scale-95 focus:outline-none"
                  >
                    <Star
                      className={`w-8 h-8 transition-colors ${
                        (hoverRating || rating) >= star
                          ? 'fill-amber-400 text-amber-400'
                          : 'text-slate-300 dark:text-slate-600'
                      }`}
                    />
                  </button>
                ))}
              </div>
              <span className="text-xs font-semibold text-amber-500 dark:text-amber-400">
                {rating === 5 && '⭐️⭐️⭐️⭐️⭐️ Ajoyib!'}
                {rating === 4 && '⭐️⭐️⭐️⭐️ Yaxshi'}
                {rating === 3 && '⭐️⭐️⭐️ Qoniqarli'}
                {rating === 2 && '⭐️⭐️ Kamchiliklar bor'}
                {rating === 1 && '⭐️ Qoniqarsiz'}
              </span>
            </div>

            {/* Kategoriya tanlash */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                Mavzu turi:
              </label>
              <div className="grid grid-cols-2 gap-2">
                {categories.map((c) => {
                  const Icon = c.icon;
                  const isSelected = category === c.id;
                  return (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => {
                        triggerHaptic('selection');
                        setCategory(c.id);
                      }}
                      className={`flex items-center space-x-2 px-3 py-2 rounded-xl text-xs font-medium border transition-all ${
                        isSelected
                          ? 'bg-indigo-50 border-indigo-500 text-indigo-700 dark:bg-indigo-950/50 dark:border-indigo-500 dark:text-indigo-300 shadow-sm'
                          : 'border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50'
                      }`}
                    >
                      <Icon className="w-4 h-4 shrink-0" />
                      <span className="truncate">{c.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Fikr matni */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                Sizning fikringiz yoki taklifingiz:
              </label>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Dars yoki ta'lim jarayoni sizga ma'qul bo'ldimi? Nimalarni yaxshilashimiz mumkin?..."
                rows={4}
                className="w-full px-3.5 py-2.5 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 text-sm text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all resize-none"
              />
            </div>

            {error && (
              <p className="text-xs font-medium text-rose-500 dark:text-rose-400">
                {error}
              </p>
            )}

            {/* Yuborish tugmasi */}
            <button
              type="submit"
              disabled={isSubmitting || comment.trim().length < 3}
              className="w-full py-3.5 px-4 rounded-2xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white font-semibold text-sm shadow-lg shadow-indigo-500/25 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-all active:scale-[0.98]"
            >
              {isSubmitting ? (
                <span>Yuborilmoqda...</span>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Fikrni yuborish</span>
                </>
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
