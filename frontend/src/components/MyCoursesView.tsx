import React, { useState, useEffect } from 'react';
import { BookOpen, CheckCircle, Clock, Compass, Play, Sparkles, Trophy, Award } from 'lucide-react';
import { Course, CourseProgressItem, AppView } from '../types';
import { fetchCourses, fetchMyCourseProgress } from '../services/api';
import { triggerHaptic } from '../services/telegram';
import { TgText } from './TgEmoji';

interface MyCoursesViewProps {
  onNavigate: (view: AppView) => void;
  onSelectCourse: (course: Course) => void;
  onSelectLesson: (courseId: string | number, lessonId: string | number) => void;
}

export const MyCoursesView: React.FC<MyCoursesViewProps> = ({
  onNavigate,
  onSelectCourse,
  onSelectLesson,
}) => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [progressMap, setProgressMap] = useState<Record<string, CourseProgressItem[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMyCourses();
  }, []);

  const loadMyCourses = async () => {
    setLoading(true);
    setError(null);
    try {
      const allCourses = await fetchCourses();
      // Enrolled or accessible courses
      const myCourses = allCourses.filter((c) => Boolean(c.is_enrolled || c.has_access));
      setCourses(myCourses);

      // Load progress for each enrolled course
      const progressPromises = myCourses.map(async (c) => {
        try {
          const progressList = await fetchMyCourseProgress(c.id);
          return { courseId: String(c.id), progressList };
        } catch {
          return { courseId: String(c.id), progressList: [] };
        }
      });

      const progressResults = await Promise.all(progressPromises);
      const map: Record<string, CourseProgressItem[]> = {};
      for (const res of progressResults) {
        map[res.courseId] = res.progressList;
      }
      setProgressMap(map);
    } catch (err: any) {
      setError(err.message || 'Mening kurslarimni yuklashda xatolik');
    } finally {
      setLoading(false);
    }
  };

  const calculateCourseCompletion = (courseId: string | number, totalLessons = 6) => {
    const items = progressMap[String(courseId)] || [];
    if (items.length === 0) return 0;
    const completedCount = items.filter((p) => p.completion_percent >= 90).length;
    const ratio = Math.round((completedCount / Math.max(totalLessons, items.length)) * 100);
    return Math.min(100, Math.max(0, ratio));
  };

  return (
    <div className="space-y-5 pb-28 max-w-3xl mx-auto px-4 pt-2 animate-in fade-in duration-200">
      {/* Learning stats banner */}
      <div className="bg-tg-section border border-tg-secondary rounded-3xl p-4.5 shadow-xs flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-amber-500/15 text-amber-500 flex items-center justify-center">
            <Trophy className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-tg-hint uppercase tracking-wider block">
              O'quv yutuqlaringiz
            </span>
            <h3 className="font-extrabold text-sm sm:text-base text-tg-text">
              {courses.length} ta faol kurs
            </h3>
          </div>
        </div>
        <div className="px-3 py-1 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 text-xs font-bold">
          Adaptiv faol
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="font-bold text-sm text-tg-text flex items-center gap-1.5">
          <BookOpen className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          <span>Mening o'rganayotgan kurslarim</span>
        </h3>

        {loading ? (
          <div className="space-y-3">
            {[1, 2].map((n) => (
              <div key={n} className="p-5 rounded-3xl bg-tg-secondary animate-pulse space-y-3">
                <div className="h-4 bg-tg-hint/20 rounded w-1/2" />
                <div className="h-2 bg-tg-hint/20 rounded-full w-full" />
                <div className="h-8 bg-tg-hint/20 rounded-xl w-32" />
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="p-6 text-center rounded-3xl bg-tg-secondary space-y-3">
            <p className="text-sm text-rose-500">{error}</p>
            <button
              onClick={loadMyCourses}
              className="px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-bold"
            >
              Qayta yuklash
            </button>
          </div>
        ) : courses.length === 0 ? (
          <div className="p-8 text-center rounded-3xl bg-tg-secondary text-tg-hint space-y-3">
            <div className="w-12 h-12 rounded-full bg-blue-500/10 text-blue-600 mx-auto flex items-center justify-center">
              <BookOpen className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <h4 className="font-bold text-sm text-tg-text">Hozircha kurslarga yozilmagansiz</h4>
              <p className="text-xs">Katalogdan o'zingizga qiziq kursni tanlang va o'rganishni boshlang!</p>
            </div>
            <button
              onClick={() => {
                triggerHaptic('light');
                onNavigate({ type: 'catalog' });
              }}
              className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs inline-flex items-center gap-1.5 shadow-xs cursor-pointer"
            >
              <Compass className="w-4 h-4" />
              <span>Katalogga o'tish</span>
            </button>
          </div>
        ) : (
          <div className="space-y-3.5">
            {courses.map((course) => {
              const progressPercent = calculateCourseCompletion(course.id, course.total_lessons || 6);
              const progressItems = progressMap[String(course.id)] || [];
              const lastStarted = progressItems[progressItems.length - 1];

              return (
                <div
                  key={course.id}
                  id={`my-course-card-${course.id}`}
                  className="bg-tg-section border border-tg-secondary rounded-3xl p-4 sm:p-5 shadow-xs space-y-4 hover:border-blue-500/30 transition-all"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      {course.category && (
                        <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400 mb-1 inline-block">
                          {course.category}
                        </span>
                      )}
                      <h4 className="font-bold text-sm sm:text-base text-tg-text truncate">
                        <TgText>{course.title}</TgText>
                      </h4>
                      {course.instructor && (
                        <p className="text-xs text-tg-hint mt-0.5 truncate">
                          {course.instructor}
                        </p>
                      )}
                    </div>

                    <div className="text-right shrink-0">
                      <span className="font-extrabold text-base text-blue-600 dark:text-blue-400">
                        {progressPercent}%
                      </span>
                      <span className="text-[10px] text-tg-hint block">bajarildi</span>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="space-y-1.5">
                    <div className="w-full h-2.5 rounded-full bg-tg-secondary overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-600 to-indigo-500 rounded-full transition-all duration-500"
                        style={{ width: `${progressPercent}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[11px] text-tg-hint">
                      <span>{progressItems.length} ta dars ko'rildi</span>
                      <span>Jami {course.total_lessons || 6} ta dars</span>
                    </div>
                  </div>

                  {/* Action buttons */}
                  <div className="pt-2 border-t border-tg-secondary flex items-center justify-between gap-2">
                    <button
                      id={`btn-continue-learning-${course.id}`}
                      onClick={() => {
                        triggerHaptic('medium');
                        onSelectCourse(course);
                        if (lastStarted) {
                          onSelectLesson(course.id, lastStarted.lesson_id);
                          onNavigate({
                            type: 'lesson',
                            courseId: course.id,
                            lessonId: lastStarted.lesson_id,
                          });
                        } else {
                          onNavigate({ type: 'course', courseId: course.id });
                        }
                      }}
                      className="py-2 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 active:scale-95 text-white font-bold text-xs flex items-center gap-1.5 shadow-xs cursor-pointer"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                      <span>Darsni davom ettirish</span>
                    </button>

                    <button
                      onClick={() => {
                        triggerHaptic('light');
                        onSelectCourse(course);
                        onNavigate({ type: 'course', courseId: course.id });
                      }}
                      className="py-2 px-3 rounded-xl bg-tg-secondary hover:bg-tg-secondary/80 text-tg-text font-semibold text-xs cursor-pointer"
                    >
                      Barcha darslar
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
