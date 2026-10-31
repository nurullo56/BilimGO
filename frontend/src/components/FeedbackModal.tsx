import React, { useState, useEffect } from 'react';
import {
  X,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  Send,
  CheckCircle2,
  Sparkles,
  AlertCircle,
  Check,
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
  initialReaction?: 'like' | 'dislike' | null;
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
  isOpen,
  onClose,
  courseId,
  lessonId,
  courseTitle,
  lessonTitle,
  initialReaction = null,
}) => {
  const [reaction, setReaction] = useState<'like' | 'dislike' | null>(initialReaction);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [comment, setComment] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isSuccess, setIsSuccess] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setReaction(initialReaction || null);
      setSelectedTags([]);
      setComment('');
      setError(null);
      setIsSuccess(false);
    }
  }, [isOpen, initialReaction]);

  if (!isOpen) return null;

  const likeTags = [
    "Tushunarli tushuntirilgan",
    "Foydali amaliy misollar",
    "Mavzu to'liq ochilgan",
    "A'lo darajadagi dars",
  ];

  const dislikeTags = [
    "Ovoz yoki video sifati past",
    "Tushuntirish murakkab",
    "Juda tez yoki sekin",
    "Amaliy mashqlar kam",
  ];

  const handleTagToggle = (tag: string) => {
    triggerHaptic('selection');
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const handleReactionSelect = (type: 'like' | 'dislike') => {
    triggerHaptic('medium');
    setReaction(type);
    setSelectedTags([]);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reaction) {
      setError("Iltimos, dars ma'qul bo'lgan yoki bo'lmaganini tanlang.");
      return;
    }

    // Dislike bo'lsa kamida tag yoki matn tanlash tavsiya qilinadi
    if (reaction === 'dislike' && selectedTags.length === 0 && comment.trim().length === 0) {
      setError("Iltimos, darsda nima yoqmaganini belgilang yoki qisqacha izoh yozing.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    triggerHaptic('medium');

    const combinedComment = [
      selectedTags.length > 0 ? `[Belgilangan sabablar: ${selectedTags.join(', ')}]` : '',
      comment.trim(),
    ]
      .filter(Boolean)
      .join('\n\n') || (reaction === 'like' ? "Dars ma'qul bo'ldi." : "Dars ma'qul bo'lmadi.");

    try {
      await submitStudentFeedback({
        rating: reaction === 'like' ? 5 : 1,
        comment: combinedComment,
        category: reaction === 'like' ? 'lesson' : 'suggestion',
        course_id: courseId,
        lesson_id: lessonId,
      });

      triggerHaptic('success');
      setIsSuccess(true);
      setTimeout(() => {
        setIsSuccess(false);
        onClose();
      }, 1800);
    } catch (err: any) {
      console.error('Feedback yuborishda xatolik:', err);
      setError(err.message || "Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.");
      triggerHaptic('warning');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-md bg-white dark:bg-slate-900 rounded-3xl p-6 shadow-2xl border border-slate-100 dark:border-slate-800 transition-all max-h-[90vh] overflow-y-auto">
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
            <div className="w-16 h-16 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center animate-bounce">
              <CheckCircle2 className="w-10 h-10" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white">
              Fikringiz qabul qilindi!
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-xs leading-relaxed">
              Darslarimiz sifatini yanada oshirishga qo'shgan hissangiz uchun rahmat.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Sarlavha */}
            <div className="text-center space-y-1">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Dars sizga ma'qul bo'ldimi?
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {lessonTitle
                  ? `«${lessonTitle}» darsi yuzasidan baholang`
                  : courseTitle
                  ? `«${courseTitle}» kursi yuzasidan baholang`
                  : "Dars haqida o'z bahongizni qoldiring"}
              </p>
            </div>

            {/* Asosiy Yoqdi / Yoqmadi Vektor Kartalari */}
            <div className="grid grid-cols-2 gap-3 pt-1">
              {/* Yoqdi (ThumbsUp) */}
              <button
                type="button"
                onClick={() => handleReactionSelect('like')}
                className={`relative flex flex-col items-center justify-center p-4 rounded-2xl border-2 transition-all cursor-pointer ${
                  reaction === 'like'
                    ? 'border-emerald-500 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 shadow-md shadow-emerald-500/10 scale-[1.02]'
                    : 'border-slate-200 dark:border-slate-800 hover:border-emerald-400/50 bg-slate-50/50 dark:bg-slate-800/40 text-slate-600 dark:text-slate-300'
                }`}
              >
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all ${
                    reaction === 'like'
                      ? 'bg-emerald-500 text-white shadow-sm'
                      : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                  }`}
                >
                  <ThumbsUp className="w-6 h-6 stroke-[2.2]" />
                </div>
                <span className="mt-2 text-xs font-bold tracking-wide">
                  Ha, yoqdi
                </span>
                {reaction === 'like' && (
                  <span className="absolute top-2 right-2 w-4 h-4 rounded-full bg-emerald-500 text-white flex items-center justify-center">
                    <Check className="w-2.5 h-2.5 stroke-[3]" />
                  </span>
                )}
              </button>

              {/* Yoqmadi (ThumbsDown) */}
              <button
                type="button"
                onClick={() => handleReactionSelect('dislike')}
                className={`relative flex flex-col items-center justify-center p-4 rounded-2xl border-2 transition-all cursor-pointer ${
                  reaction === 'dislike'
                    ? 'border-rose-500 bg-rose-500/10 text-rose-600 dark:text-rose-400 shadow-md shadow-rose-500/10 scale-[1.02]'
                    : 'border-slate-200 dark:border-slate-800 hover:border-rose-400/50 bg-slate-50/50 dark:bg-slate-800/40 text-slate-600 dark:text-slate-300'
                }`}
              >
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all ${
                    reaction === 'dislike'
                      ? 'bg-rose-500 text-white shadow-sm'
                      : 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                  }`}
                >
                  <ThumbsDown className="w-6 h-6 stroke-[2.2]" />
                </div>
                <span className="mt-2 text-xs font-bold tracking-wide">
                  Yoqmadi
                </span>
                {reaction === 'dislike' && (
                  <span className="absolute top-2 right-2 w-4 h-4 rounded-full bg-rose-500 text-white flex items-center justify-center">
                    <Check className="w-2.5 h-2.5 stroke-[3]" />
                  </span>
                )}
              </button>
            </div>

            {/* Tanlangan reaksiyaga mos dinamik savollar va teglar */}
            {reaction && (
              <div className="space-y-3 pt-2 animate-in fade-in duration-200">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    {reaction === 'like'
                      ? "Nima ayniqsa ma'qul bo'ldi? (ixtiyoriy):"
                      : "Darsda nima sizga yoqmadi yoki nimani yaxshilash kerak?:"}
                  </label>

                  <div className="flex flex-wrap gap-1.5">
                    {(reaction === 'like' ? likeTags : dislikeTags).map((tag) => {
                      const isSelected = selectedTags.includes(tag);
                      return (
                        <button
                          key={tag}
                          type="button"
                          onClick={() => handleTagToggle(tag)}
                          className={`text-xs px-2.5 py-1.5 rounded-xl border transition-all cursor-pointer font-medium ${
                            isSelected
                              ? reaction === 'like'
                                ? 'bg-emerald-500 text-white border-emerald-500 shadow-xs'
                                : 'bg-rose-500 text-white border-rose-500 shadow-xs'
                              : 'bg-slate-50 dark:bg-slate-800/60 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-300'
                          }`}
                        >
                          {tag}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Qo'shimcha fikr matni */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    {reaction === 'like'
                      ? "Qo'shimcha fikringiz bo'lsa yozing (ixtiyoriy):"
                      : "Fikr yoki taklifingizni yozib qoldiring:"}
                  </label>
                  <textarea
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder={
                      reaction === 'like'
                        ? "Dars haqida iliq fikringiz..."
                        : "Kamchiliklar yoki yaxshilash bo'yicha taklifingiz..."
                    }
                    rows={3}
                    className="w-full px-3.5 py-2.5 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 text-xs sm:text-sm text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all resize-none"
                  />
                </div>
              </div>
            )}

            {error && (
              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 text-xs">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Yuborish tugmasi */}
            <button
              type="submit"
              disabled={isSubmitting || !reaction}
              className={`w-full py-3 px-4 rounded-2xl text-white font-semibold text-xs sm:text-sm shadow-md transition-all active:scale-[0.98] flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${
                reaction === 'dislike'
                  ? 'bg-rose-600 hover:bg-rose-700 shadow-rose-600/20'
                  : 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-600/20'
              }`}
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
