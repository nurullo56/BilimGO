import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  CreditCard,
  Lock,
  Play,
  Radio,
  ShieldAlert,
  Sparkles,
  Trophy,
  User,
  Video,
} from 'lucide-react';
import { Course, Lesson, AppView } from '../types';
import { fetchCourseById, fetchCourseLessons, fetchLiveSessions } from '../services/api';
import { PaymentModal } from './PaymentModal';
import { triggerHaptic } from '../services/telegram';
import { TgText } from './TgEmoji';

interface CourseDetailViewProps {
  courseId: string | number;
  onNavigate: (view: AppView) => void;
  onSelectLesson: (courseId: string | number, lessonId: string | number) => void;
}

export const CourseDetailView: React.FC<CourseDetailViewProps> = ({
  courseId,
  onNavigate,
  onSelectLesson,
}) => {
  const [course, setCourse] = useState<Course | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [liveCount, setLiveCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [paymentModalOpen, setPaymentModalOpen] = useState(false);

  useEffect(() => {
    loadCourseDetails();
  }, [courseId]);

  const loadCourseDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const [courseData, lessonsData, liveData] = await Promise.all([
        fetchCourseById(courseId),
        fetchCourseLessons(courseId),
        fetchLiveSessions(courseId).catch(() => []),
      ]);
      setCourse(courseData);
      setLessons(lessonsData);
      setLiveCount(liveData.length);
    } catch (err: any) {
      setError(err.message || 'Kurs ma\'lumotlarini yuklashda xatolik');
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  if (loading) {
    return (
      <div className="space-y-4 max-w-3xl mx-auto px-4 py-4 animate-pulse">
        <div className="h-48 bg-tg-secondary rounded-3xl" />
        <div className="h-6 bg-tg-secondary rounded w-3/4" />
        <div className="h-4 bg-tg-secondary rounded w-1/2" />
        <div className="space-y-2 pt-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 bg-tg-secondary rounded-2xl" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="max-w-md mx-auto px-4 py-12 text-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-rose-500/10 text-rose-500 mx-auto flex items-center justify-center">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <h3 className="text-base font-bold text-tg-text">{error || 'Kurs topilmadi'}</h3>
        <button
          onClick={() => onNavigate({ type: 'catalog' })}
          className="px-4 py-2.5 rounded-xl bg-blue-600 text-white font-bold text-xs"
        >
          Katalogga qaytish
        </button>
      </div>
    );
  }

  const unlockedCount = lessons.filter((l) => l.unlocked || l.is_free_preview).length;
  const formattedPrice = new Intl.NumberFormat('uz-UZ').format(course.base_price);
  const isEnrolled = Boolean(course.is_enrolled);

  return (
    <div className="space-y-5 pb-28 max-w-3xl mx-auto px-4 pt-2 animate-in fade-in duration-200">
      {/* Course Hero Banner */}
      <div className="bg-tg-section border border-tg-secondary rounded-3xl overflow-hidden shadow-xs">
        {course.thumbnail && (
          <div className="relative w-full h-44 sm:h-56 bg-tg-secondary">
            <img
              src={course.thumbnail}
              alt={course.title}
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
            <div className="absolute bottom-4 left-4 right-4 text-white">
              {course.category && (
                <span className="px-2.5 py-0.5 rounded-md bg-blue-600 text-[10px] font-bold uppercase tracking-wider mb-1.5 inline-block">
                  {course.category}
                </span>
              )}
              <h2 className="text-base sm:text-xl font-black leading-tight drop-shadow-xs">
                <TgText>{course.title}</TgText>
              </h2>
            </div>
          </div>
        )}

        <div className="p-4 sm:p-5 space-y-4">
          {course.description && (
            <p className="text-xs sm:text-sm text-tg-text/90 leading-relaxed">
              <TgText>{course.description}</TgText>
            </p>
          )}

          {/* Instructor & stats chips */}
          <div className="flex flex-wrap items-center gap-2 text-xs text-tg-hint">
            {course.instructor && (
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-tg-secondary">
                <User className="w-3.5 h-3.5 text-blue-500" />
                <span className="font-medium text-tg-text">{course.instructor}</span>
              </div>
            )}
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-tg-secondary">
              <Video className="w-3.5 h-3.5 text-blue-500" />
              <span className="font-medium text-tg-text">
                {lessons.length} ta dars ({unlockedCount} ta ochiq)
              </span>
            </div>
          </div>

          {/* Action Bar: Purchase / Live sessions */}
          <div className="pt-2 flex flex-col sm:flex-row gap-2.5">
            {isEnrolled ? (
              <div
                id="badge-course-enrolled"
                className="flex-1 py-3 px-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-600 dark:text-emerald-400 font-bold text-xs sm:text-sm flex items-center justify-center gap-2 shadow-xs"
              >
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>Sotib olingan (To'liq dostup ochiq)</span>
              </div>
            ) : (
              <button
                id="btn-buy-course"
                onClick={() => {
                  triggerHaptic('medium');
                  setPaymentModalOpen(true);
                }}
                className="flex-1 py-3 px-4 rounded-2xl bg-blue-600 hover:bg-blue-700 active:scale-98 text-white font-bold text-sm shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <CreditCard className="w-4 h-4" />
                <span>Sotib olish ({formattedPrice} so'm)</span>
              </button>
            )}

            {liveCount > 0 && (
              <button
                id="btn-view-live-sessions"
                onClick={() => {
                  triggerHaptic('light');
                  onNavigate({ type: 'live', courseId: course.id });
                }}
                className="py-3 px-4 rounded-2xl bg-rose-500/10 hover:bg-rose-500/20 active:scale-98 text-rose-600 dark:text-rose-400 font-bold text-xs border border-rose-500/20 transition-all flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <Radio className="w-4 h-4 text-rose-500 animate-pulse" />
                <span>Jonli efirlar ({liveCount})</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Adaptive Unlock Notice */}
      <div className="p-3.5 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-start gap-3">
        <Sparkles className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
        <div className="text-xs space-y-0.5">
          <span className="font-bold text-blue-700 dark:text-blue-300 block">
            Adaptiv unlock mexanizmi
          </span>
          <p className="text-blue-600/90 dark:text-blue-200/80">
            Darslar kunlik bilim hajmingizga qarab backend tomonidan ochiladi. Bepul darslar har doim ochiq!
          </p>
        </div>
      </div>

      {/* Course Overall Progress Tracker */}
      {lessons.length > 0 && (
        <div className="bg-tg-section border border-tg-secondary rounded-3xl p-4 sm:p-5 space-y-3 shadow-xs">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-tg-text flex items-center gap-1.5">
              <Trophy className="w-4 h-4 text-amber-500" />
              Kursni o'zlashtirish darajasi
            </span>
            <span className="font-extrabold text-blue-600 dark:text-blue-400 font-mono text-xs sm:text-sm">
              {lessons.length > 0
                ? Math.round(lessons.reduce((acc, l) => acc + (l.completion_percent || 0), 0) / lessons.length)
                : 0}
              % ({lessons.filter((l) => (l.completion_percent || 0) >= 90).length} / {lessons.length} tugatildi)
            </span>
          </div>
          <div className="w-full h-2.5 bg-tg-secondary rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-600 via-indigo-500 to-emerald-500 rounded-full transition-all duration-500"
              style={{
                width: `${Math.max(
                  lessons.some((l) => (l.completion_percent || 0) > 0) ? 3 : 0,
                  Math.round(lessons.reduce((acc, l) => acc + (l.completion_percent || 0), 0) / Math.max(lessons.length, 1))
                )}%`,
              }}
            />
          </div>
        </div>
      )}

      {/* Resume Learning Hero Banner */}
      {(() => {
        const inProgressLesson =
          lessons.find((l) => (l.completion_percent || 0) > 0 && (l.completion_percent || 0) < 90) ||
          lessons.find((l) => (l.completion_percent || 0) === 0 && (l.unlocked || l.is_free_preview)) ||
          lessons[0];

        if (!inProgressLesson) return null;

        const p = inProgressLesson.completion_percent || 0;

        return (
          <div className="p-4 sm:p-5 rounded-3xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white flex items-center justify-between gap-3 shadow-lg shadow-blue-600/20 animate-in fade-in duration-300">
            <div className="min-w-0 flex-1 space-y-1">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-blue-200 block">
                {p > 0 ? "Qolgan joyidan davom etish" : "O'rganishni boshlash"}
              </span>
              <h4 className="font-bold text-sm sm:text-base truncate">
                {inProgressLesson.order_index}-dars: <TgText>{inProgressLesson.title}</TgText>
              </h4>
              <div className="flex items-center gap-2 text-[11px] text-blue-100/90">
                <span>{p > 0 ? `${p}% ko'rilgan (To'xtagan joyingiz)` : 'Tayyor'}</span>
              </div>
            </div>
            <button
              onClick={() => {
                triggerHaptic('medium');
                onSelectLesson(course.id, inProgressLesson.id);
                onNavigate({ type: 'lesson', courseId: course.id, lessonId: inProgressLesson.id });
              }}
              className="px-4 py-2.5 rounded-2xl bg-white hover:bg-blue-50 text-blue-600 font-extrabold text-xs flex items-center gap-1.5 shadow-md active:scale-95 transition-all cursor-pointer shrink-0"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{p > 0 ? 'Davom etish' : 'Boshlash'}</span>
            </button>
          </div>
        );
      })()}

      {/* Lessons List */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-sm text-tg-text">
            Darslar ro'yxati ({lessons.length})
          </h3>
          <span className="text-xs text-tg-hint">
            {unlockedCount} / {lessons.length} ochiq
          </span>
        </div>

        <div className="space-y-2">
          {lessons.map((lesson, idx) => {
            const isAccessible = lesson.unlocked || lesson.is_free_preview;
            const percent = lesson.completion_percent || 0;
            const isDone = percent >= 90;

            return (
              <div
                key={lesson.id}
                id={`lesson-item-${lesson.id}`}
                className={`p-3.5 rounded-2xl border transition-all flex items-center justify-between gap-3 ${
                  isAccessible
                    ? isDone
                      ? 'bg-emerald-500/5 border-emerald-500/30 hover:border-emerald-500/50 shadow-xs'
                      : 'bg-tg-section border-tg-secondary hover:border-blue-500/40 shadow-xs'
                    : 'bg-tg-secondary/60 border-tg-secondary opacity-75'
                }`}
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div
                    className={`w-9 h-9 rounded-xl shrink-0 flex items-center justify-center font-bold text-xs ${
                      isDone
                        ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
                        : isAccessible
                        ? 'bg-blue-500/15 text-blue-600 dark:text-blue-400'
                        : 'bg-tg-secondary text-tg-hint'
                    }`}
                  >
                    {isDone ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                    ) : (
                      lesson.order_index || idx + 1
                    )}
                  </div>

                  <div className="min-w-0 flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-bold text-xs sm:text-sm text-tg-text truncate">
                        <TgText>{lesson.title}</TgText>
                      </h4>
                      {lesson.is_free_preview && (
                        <span className="shrink-0 px-1.5 py-0.5 rounded text-[9px] font-extrabold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">
                          Bepul
                        </span>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-2 text-[11px] text-tg-hint">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDuration(lesson.duration_sec)}
                      </span>

                      {percent > 0 && (
                        <span
                          className={`px-1.5 py-0.2 rounded font-mono font-bold text-[10px] ${
                            isDone
                              ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
                              : 'bg-blue-500/15 text-blue-600 dark:text-blue-400'
                          }`}
                        >
                          {isDone ? '✅ 100% tugatildi' : `⏱️ ${percent}% ko'rildi`}
                        </span>
                      )}
                    </div>

                    {percent > 0 && !isDone && (
                      <div className="w-full max-w-xs h-1 bg-tg-secondary rounded-full overflow-hidden mt-0.5">
                        <div
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${percent}%` }}
                        />
                      </div>
                    )}
                  </div>
                </div>

                <div className="shrink-0">
                  {isAccessible ? (
                    <button
                      id={`btn-watch-lesson-${lesson.id}`}
                      onClick={() => {
                        triggerHaptic('light');
                        onSelectLesson(course.id, lesson.id);
                        onNavigate({
                          type: 'lesson',
                          courseId: course.id,
                          lessonId: lesson.id,
                        });
                      }}
                      className={`py-1.5 px-3.5 rounded-xl font-bold text-xs flex items-center gap-1.5 shadow-xs cursor-pointer active:scale-95 transition-all ${
                        isDone
                          ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                          : percent > 0
                          ? 'bg-indigo-600 hover:bg-indigo-700 text-white'
                          : 'bg-blue-600 hover:bg-blue-700 text-white'
                      }`}
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                      <span>{isDone ? 'Qayta ko\'rish' : percent > 0 ? 'Davom etish' : 'Ko\'rish'}</span>
                    </button>
                  ) : (
                    <div
                      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-tg-secondary text-tg-hint text-xs font-semibold"
                      title="Ushbu dars kunlik limitga ko'ra hali ochilmagan"
                    >
                      <Lock className="w-3.5 h-3.5 text-amber-500" />
                      <span className="hidden sm:inline">Hali ochilmagan</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Payment Modal */}
      <PaymentModal
        course={course}
        isOpen={paymentModalOpen}
        onClose={() => setPaymentModalOpen(false)}
        onSuccessEnrolled={() => {
          loadCourseDetails();
        }}
      />
    </div>
  );
};
