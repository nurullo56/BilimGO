import React, { useState, useEffect } from 'react';
import { BookOpen, Clock, Lock, Play, Search, Sparkles, User, Layers, ArrowRight, CheckCircle2 } from 'lucide-react';
import { Course, AppView } from '../types';
import { fetchCourses } from '../services/api';
import { triggerHaptic } from '../services/telegram';
import { TgText } from './TgEmoji';

interface CatalogViewProps {
  onNavigate: (view: AppView) => void;
  onSelectCourse: (course: Course) => void;
}

export const CatalogView: React.FC<CatalogViewProps> = ({
  onNavigate,
  onSelectCourse,
}) => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('Barchasi');

  useEffect(() => {
    loadCourses();
  }, []);

  const loadCourses = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCourses();
      setCourses(data);
    } catch (err: any) {
      setError(err.message || 'Kurslarni yuklashda xatolik yuz berdi');
    } finally {
      setLoading(false);
    }
  };

  const categories = React.useMemo(() => {
    const list = ['Barchasi'];
    courses.forEach((c) => {
      if (c.category && !list.includes(c.category)) {
        list.push(c.category);
      }
    });
    return list;
  }, [courses]);

  const filteredCourses = courses.filter((course) => {
    const matchesSearch =
      course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (course.description && course.description.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (course.category && course.category.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesCategory =
      selectedCategory === 'Barchasi' || course.category === selectedCategory;

    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-5 pb-24 animate-in fade-in duration-200 max-w-3xl mx-auto px-4 pt-2">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-tg-hint" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Kurs nomi yoki mavzuni qidiring..."
          className="w-full pl-10 pr-4 py-3 rounded-2xl bg-tg-secondary border border-tg-secondary text-tg-text placeholder-tg-hint text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
        />
      </div>

      {/* Category Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar text-xs">
        {categories.map((cat) => {
          const isSelected = selectedCategory === cat;
          return (
            <button
              key={cat}
              onClick={() => {
                triggerHaptic('selection');
                setSelectedCategory(cat);
              }}
              className={`px-3.5 py-2 rounded-xl whitespace-nowrap font-semibold transition-all cursor-pointer ${
                isSelected
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'bg-tg-secondary text-tg-hint hover:text-tg-text'
              }`}
            >
              {cat}
            </button>
          );
        })}
      </div>

      {/* Courses List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-sm text-tg-text flex items-center gap-1.5">
            <BookOpen className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <span>Nashr qilingan kurslar ({filteredCourses.length})</span>
          </h3>
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((n) => (
              <div
                key={n}
                className="p-4 rounded-3xl bg-tg-secondary animate-pulse space-y-3"
              >
                <div className="h-4 bg-tg-hint/20 rounded-md w-3/4" />
                <div className="h-3 bg-tg-hint/15 rounded-md w-1/2" />
                <div className="h-8 bg-tg-hint/20 rounded-xl w-full" />
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="p-6 text-center rounded-3xl bg-tg-secondary space-y-3">
            <p className="text-sm text-rose-500 font-medium">{error}</p>
            <button
              onClick={loadCourses}
              className="px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-bold"
            >
              Qayta urinish
            </button>
          </div>
        ) : filteredCourses.length === 0 ? (
          <div className="p-8 text-center rounded-3xl bg-tg-secondary text-tg-hint space-y-2">
            <Layers className="w-8 h-8 mx-auto opacity-40" />
            <p className="text-sm font-medium">Bunday kurs topilmadi</p>
            <p className="text-xs">Boshqa kalit so'z yoki toifani tanlab ko'ring</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredCourses.map((course) => {
              const formattedPrice = new Intl.NumberFormat('uz-UZ').format(course.base_price);
              return (
                <div
                  key={course.id}
                  id={`course-card-${course.id}`}
                  className="group bg-tg-section border border-tg-secondary rounded-3xl p-4.5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    {course.thumbnail && (
                      <div className="relative w-full h-36 rounded-2xl overflow-hidden bg-tg-secondary">
                        <img
                          src={course.thumbnail}
                          alt={course.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                        {course.category && (
                          <span className="absolute top-2.5 left-2.5 px-2.5 py-1 rounded-lg bg-black/60 backdrop-blur-md text-[11px] font-bold text-white">
                            {course.category}
                          </span>
                        )}
                        {course.is_enrolled && (
                          <span className="absolute top-2.5 right-2.5 px-2.5 py-1 rounded-lg bg-emerald-600 text-[11px] font-bold text-white shadow-xs flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" />
                            Sotib olingan
                          </span>
                        )}
                      </div>
                    )}

                    <div className="space-y-1.5">
                      <h4 className="font-bold text-base text-tg-text line-clamp-2 leading-snug group-hover:text-blue-600 transition-colors">
                        <TgText>{course.title}</TgText>
                      </h4>
                      {course.description && (
                        <p className="text-xs text-tg-hint line-clamp-2 leading-relaxed">
                          <TgText>{course.description}</TgText>
                        </p>
                      )}
                    </div>

                    {course.instructor && (
                      <div className="flex items-center gap-1.5 text-xs text-tg-hint">
                        <User className="w-3.5 h-3.5 text-blue-500" />
                        <span className="truncate">{course.instructor}</span>
                      </div>
                    )}
                  </div>

                  <div className="pt-4 mt-3 border-t border-tg-secondary flex items-center justify-between">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-tg-hint block">
                        {course.is_waitlist ? 'Kutilmoqda' : course.is_enrolled ? 'Holat' : 'Kurs narxi'}
                      </span>
                      {course.is_waitlist ? (
                        <span className="text-xs font-bold text-amber-500 flex items-center gap-1">
                          <Sparkles className="w-3 h-3 text-amber-500" />
                          Tez kunda (Waitlist)
                        </span>
                      ) : course.is_enrolled ? (
                        <span className="text-xs sm:text-sm font-extrabold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Sotib olingan
                        </span>
                      ) : (
                        <span className="text-base font-extrabold text-tg-text text-blue-600 dark:text-blue-400">
                          {formattedPrice}{' '}
                          <span className="text-xs font-normal text-tg-hint">so'm</span>
                        </span>
                      )}
                    </div>

                    <button
                      id={`btn-course-details-${course.id}`}
                      onClick={() => {
                        triggerHaptic('light');
                        onSelectCourse(course);
                        onNavigate({ type: 'course', courseId: course.id });
                      }}
                      className={`py-2 px-4 rounded-xl active:scale-95 text-white font-bold text-xs transition-all shadow-xs flex items-center gap-1.5 cursor-pointer ${
                        course.is_waitlist
                          ? 'bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 shadow-amber-500/20'
                          : 'bg-blue-600 hover:bg-blue-700 shadow-blue-500/20'
                      }`}
                    >
                      <span>{course.is_waitlist ? 'Navbatga yozilish' : 'Batafsil'}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
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
