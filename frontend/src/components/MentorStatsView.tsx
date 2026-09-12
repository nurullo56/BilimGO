import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  BarChart3,
  CheckCircle2,
  Clock,
  ExternalLink,
  Filter,
  GraduationCap,
  MessageSquare,
  Search,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  UserCheck,
  Users,
  Award,
  BookOpen,
  ChevronRight,
  Layers,
  Send,
  Crown,
  Globe,
} from 'lucide-react';
import { CabinetActivityItem, AppView, MentorInfo, UserProfile, UserRole } from '../types';
import {
  fetchCabinetActivity,
  fetchMentorsList,
  fetchUserProfile,
  updateUserProfile,
} from '../services/api';
import { triggerHaptic } from '../services/telegram';

interface MentorStatsViewProps {
  cabinetId?: string | number;
  mentorId?: string | number;
  onNavigate: (view: AppView) => void;
}

export const MentorStatsView: React.FC<MentorStatsViewProps> = ({
  cabinetId,
  mentorId: initialMentorId,
  onNavigate,
}) => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [mentors, setMentors] = useState<MentorInfo[]>([]);
  const [activity, setActivity] = useState<CabinetActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters state
  const [selectedMentorId, setSelectedMentorId] = useState<string>(
    initialMentorId ? String(initialMentorId) : 'all'
  );
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'graduated' | 'inactive'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showRoleSwitcher, setShowRoleSwitcher] = useState(false);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (profile) {
      loadStudentsActivity();
    }
  }, [profile?.role, selectedMentorId, cabinetId]);

  const loadInitialData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [userProf, mentorsList] = await Promise.all([
        fetchUserProfile(),
        fetchMentorsList(),
      ]);
      setProfile(userProf);
      setMentors(mentorsList);

      const data = await fetchCabinetActivity(cabinetId, selectedMentorId);
      setActivity(data);
    } catch (err: any) {
      setError(err.message || 'Statistikani yuklashda xatolik yuz berdi');
    } finally {
      setLoading(false);
    }
  };

  const loadStudentsActivity = async () => {
    try {
      const data = await fetchCabinetActivity(
        cabinetId,
        selectedMentorId !== 'all' ? selectedMentorId : undefined
      );
      setActivity(data);
    } catch (err: any) {
      console.error('Error fetching students activity:', err);
    }
  };

  const handleRoleChange = async (newRole: UserRole) => {
    triggerHaptic('medium');
    try {
      const updated = await updateUserProfile({ role: newRole });
      setProfile(updated);
      setShowRoleSwitcher(false);
    } catch (e) {
      console.error('Failed to change role', e);
    }
  };

  const isSuperAdmin = profile?.role === 'super_mentor' || profile?.role === 'admin';

  // Filter students based on search and status
  const filteredStudents = activity.filter((student) => {
    // Search query filter
    const matchesSearch =
      searchQuery.trim() === '' ||
      student.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (student.username && student.username.toLowerCase().includes(searchQuery.toLowerCase())) ||
      String(student.telegram_id).includes(searchQuery.trim());

    // Status filter
    const matchesStatus =
      statusFilter === 'all' || student.status === statusFilter;

    // Mentor filter (for super admin)
    const matchesMentor =
      !isSuperAdmin ||
      selectedMentorId === 'all' ||
      String(student.mentor_id) === String(selectedMentorId);

    return matchesSearch && matchesStatus && matchesMentor;
  });

  const totalLessonsWatched = filteredStudents.reduce((acc, curr) => acc + curr.lessons_watched, 0);
  const graduatedCount = filteredStudents.filter((s) => s.status === 'graduated' || s.progress_percent === 100).length;
  const avgProgress =
    filteredStudents.length > 0
      ? Math.round(
          filteredStudents.reduce((acc, s) => acc + (s.progress_percent || 0), 0) /
            filteredStudents.length
        )
      : 0;

  return (
    <div className="space-y-4 pb-28 max-w-3xl mx-auto px-3 sm:px-4 pt-1 animate-in fade-in duration-200">
      {/* Role Banner & Switcher */}
      <div className="bg-tg-section border border-tg-secondary rounded-2xl p-3.5 shadow-xs space-y-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-sm shrink-0 ${
                isSuperAdmin
                  ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400 ring-1 ring-amber-500/30'
                  : 'bg-blue-500/15 text-blue-600 dark:text-blue-400 ring-1 ring-blue-500/30'
              }`}
            >
              {isSuperAdmin ? <ShieldCheck className="w-5 h-5" /> : <Users className="w-5 h-5" />}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h2 className="font-extrabold text-sm sm:text-base text-tg-text truncate">
                  {isSuperAdmin ? 'Super Mentor & Admin Paneli' : 'Mentor Paneli'}
                </h2>
                <span
                  className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-tight ${
                    isSuperAdmin
                      ? 'bg-amber-500/20 text-amber-700 dark:text-amber-300'
                      : 'bg-blue-500/20 text-blue-700 dark:text-blue-300'
                  }`}
                >
                  {isSuperAdmin ? 'Barcha Mentorlar' : 'Mening O\'quvchilarim'}
                </span>
              </div>
              <p className="text-[11px] text-tg-hint truncate">
                {isSuperAdmin
                  ? 'Platformadagi barcha mentorlar, guruhlar va o\'quvchilar monitoringi'
                  : 'Faqat sizning guruhlaringiz va biriktirilgan talabalaringiz ro\'yxati'}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => {
              triggerHaptic('light');
              setShowRoleSwitcher((prev) => !prev);
            }}
            className="px-2.5 py-1.5 rounded-xl bg-tg-secondary hover:bg-tg-secondary/80 text-tg-text text-[11px] font-bold transition-all shrink-0 cursor-pointer"
          >
            Rolni almashtirish
          </button>
        </div>

        {/* Quick Role Switcher Tray */}
        {showRoleSwitcher && (
          <div className="p-3 bg-tg-secondary/60 rounded-xl border border-tg-secondary space-y-2 animate-in fade-in slide-in-from-top-1">
            <p className="text-[11px] font-bold text-tg-hint">
              Ko'rish rejimini tanlang (Test & Boshqaruv uchun):
            </p>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleRoleChange('mentor')}
                className={`p-2.5 rounded-xl text-left border transition-all cursor-pointer ${
                  profile?.role === 'mentor'
                    ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                    : 'bg-tg-section text-tg-text border-tg-secondary hover:border-blue-500/40'
                }`}
              >
                <div className="font-extrabold text-xs flex items-center gap-1.5">
                  <GraduationCap className="w-3.5 h-3.5" />
                  <span>Kichik/Katta Mentor</span>
                </div>
                <div className={`text-[10px] mt-0.5 ${profile?.role === 'mentor' ? 'text-blue-100' : 'text-tg-hint'}`}>
                  Faqat o'ziga biriktirilgan o'quvchilarni ko'radi
                </div>
              </button>

              <button
                type="button"
                onClick={() => handleRoleChange('super_mentor')}
                className={`p-2.5 rounded-xl text-left border transition-all cursor-pointer ${
                  isSuperAdmin
                    ? 'bg-amber-600 text-white border-amber-600 shadow-xs'
                    : 'bg-tg-section text-tg-text border-tg-secondary hover:border-amber-500/40'
                }`}
              >
                <div className="font-extrabold text-xs flex items-center gap-1.5">
                  <Crown className="w-3.5 h-3.5 fill-current" />
                  <span>Super Mentor / Admin</span>
                </div>
                <div className={`text-[10px] mt-0.5 ${isSuperAdmin ? 'text-amber-100' : 'text-tg-hint'}`}>
                  Barcha mentorlar va hamma o'quvchilarni ko'radi
                </div>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Super Mentor - Mentor Filter Tabs */}
      {isSuperAdmin && (
        <div className="bg-tg-section border border-tg-secondary rounded-2xl p-3 shadow-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-extrabold text-tg-hint uppercase tracking-wider flex items-center gap-1.5">
              <Filter className="w-3 h-3 text-amber-500" />
              <span>Mentor bo'yicha filtrlash:</span>
            </span>
            <span className="text-[11px] font-bold text-amber-600 dark:text-amber-400">
              {mentors.length} ta mentor mavjud
            </span>
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
            <button
              type="button"
              onClick={() => {
                triggerHaptic('selection');
                setSelectedMentorId('all');
              }}
              className={`px-3 py-1.5 rounded-xl text-xs font-extrabold whitespace-nowrap transition-all cursor-pointer shrink-0 inline-flex items-center gap-1.5 ${
                selectedMentorId === 'all'
                  ? 'bg-gradient-to-r from-amber-600 to-orange-600 text-white shadow-xs'
                  : 'bg-tg-secondary text-tg-hint hover:text-tg-text'
              }`}
            >
              <Globe className="w-3.5 h-3.5" />
              <span>Barcha Mentorlar ({activity.length})</span>
            </button>

            {mentors.map((m) => {
              const count = activity.filter((s) => String(s.mentor_id) === String(m.id)).length;
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => {
                    triggerHaptic('selection');
                    setSelectedMentorId(String(m.id));
                  }}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer flex items-center gap-1.5 shrink-0 ${
                    selectedMentorId === String(m.id)
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'bg-tg-secondary text-tg-hint hover:text-tg-text'
                  }`}
                >
                  <span>{m.avatar || '👨‍🏫'}</span>
                  <span>{m.name}</span>
                  <span className="opacity-80 text-[10px]">({count})</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Header Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        <div className="bg-tg-section border border-tg-secondary p-3.5 rounded-2xl shadow-xs space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-tg-hint">
            <Users className="w-3.5 h-3.5 text-blue-500" />
            <span>O'quvchilar</span>
          </div>
          <p className="text-xl sm:text-2xl font-black text-tg-text">
            {filteredStudents.length} nafar
          </p>
        </div>

        <div className="bg-tg-section border border-tg-secondary p-3.5 rounded-2xl shadow-xs space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-tg-hint">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
            <span>Darslar soni</span>
          </div>
          <p className="text-xl sm:text-2xl font-black text-tg-text">
            {totalLessonsWatched} ta
          </p>
        </div>

        <div className="bg-tg-section border border-tg-secondary p-3.5 rounded-2xl shadow-xs space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-tg-hint">
            <UserCheck className="w-3.5 h-3.5 text-indigo-500" />
            <span>O'rtacha o'zlashtirish</span>
          </div>
          <p className="text-xl sm:text-2xl font-black text-tg-text">
            {avgProgress}%
          </p>
        </div>

        <div className="bg-tg-section border border-tg-secondary p-3.5 rounded-2xl shadow-xs space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-tg-hint">
            <GraduationCap className="w-3.5 h-3.5 text-amber-500" />
            <span>Tugatganlar</span>
          </div>
          <p className="text-xl sm:text-2xl font-black text-tg-text">
            {graduatedCount} ta
          </p>
        </div>
      </div>

      {/* Search & Status Filter Controls */}
      <div className="bg-tg-section border border-tg-secondary rounded-2xl p-3 shadow-xs space-y-2.5">
        {/* Search Bar */}
        <div className="relative">
          <Search className="w-4 h-4 text-tg-hint absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="O'quvchi ismi, username yoki Telegram ID..."
            className="w-full pl-9.5 pr-4 py-2.5 bg-tg-secondary rounded-xl text-xs sm:text-sm text-tg-text placeholder-tg-hint border border-tg-secondary focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-tg-hint hover:text-tg-text font-bold"
            >
              Tozalash
            </button>
          )}
        </div>

        {/* Status Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar">
          <button
            type="button"
            onClick={() => {
              triggerHaptic('selection');
              setStatusFilter('all');
            }}
            className={`px-3 py-1 rounded-xl text-[11px] font-bold whitespace-nowrap transition-all cursor-pointer ${
              statusFilter === 'all'
                ? 'bg-tg-text text-tg-bg font-extrabold'
                : 'bg-tg-secondary text-tg-hint hover:text-tg-text'
            }`}
          >
            Barchasi ({activity.length})
          </button>

          <button
            type="button"
            onClick={() => {
              triggerHaptic('selection');
              setStatusFilter('active');
            }}
            className={`px-3 py-1 rounded-xl text-[11px] font-bold whitespace-nowrap transition-all cursor-pointer flex items-center gap-1 ${
              statusFilter === 'active'
                ? 'bg-emerald-600 text-white font-extrabold shadow-xs'
                : 'bg-tg-secondary text-tg-hint hover:text-tg-text'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span>Faol ({activity.filter((s) => s.status === 'active').length})</span>
          </button>

          <button
            type="button"
            onClick={() => {
              triggerHaptic('selection');
              setStatusFilter('graduated');
            }}
            className={`px-3 py-1 rounded-xl text-[11px] font-bold whitespace-nowrap transition-all cursor-pointer flex items-center gap-1 ${
              statusFilter === 'graduated'
                ? 'bg-amber-600 text-white font-extrabold shadow-xs'
                : 'bg-tg-secondary text-tg-hint hover:text-tg-text'
            }`}
          >
            <span>🏆</span>
            <span>Bitirgan ({activity.filter((s) => s.status === 'graduated').length})</span>
          </button>

          <button
            type="button"
            onClick={() => {
              triggerHaptic('selection');
              setStatusFilter('inactive');
            }}
            className={`px-3 py-1 rounded-xl text-[11px] font-bold whitespace-nowrap transition-all cursor-pointer flex items-center gap-1 ${
              statusFilter === 'inactive'
                ? 'bg-rose-600 text-white font-extrabold shadow-xs'
                : 'bg-tg-secondary text-tg-hint hover:text-tg-text'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-rose-400"></span>
            <span>Passiv ({activity.filter((s) => s.status === 'inactive').length})</span>
          </button>
        </div>
      </div>

      {/* Activity Table & Student Cards */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between px-1">
          <h3 className="font-extrabold text-xs sm:text-sm text-tg-text flex items-center gap-1.5">
            <BarChart3 className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <span>O'quvchilar monitoringi ({filteredStudents.length} ta)</span>
          </h3>
        </div>

        {loading ? (
          <div className="space-y-2.5">
            {[1, 2, 3].map((n) => (
              <div key={n} className="h-24 rounded-2xl bg-tg-secondary animate-pulse" />
            ))}
          </div>
        ) : error ? (
          <div className="p-6 text-center rounded-3xl bg-tg-secondary text-rose-500 font-bold text-xs">
            {error}
          </div>
        ) : filteredStudents.length === 0 ? (
          <div className="p-8 text-center rounded-3xl bg-tg-section border border-tg-secondary text-tg-hint space-y-2">
            <Users className="w-8 h-8 mx-auto opacity-40 text-blue-500" />
            <p className="font-bold text-xs">Belgilangan filtrlarga mos keluvchi o'quvchilar topilmadi</p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {filteredStudents.map((item) => {
              const statusBadge =
                item.status === 'graduated'
                  ? { label: 'Tugatgan 🏆', color: 'bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30' }
                  : item.status === 'inactive'
                  ? { label: 'Yordam kerak ⚠️', color: 'bg-rose-500/15 text-rose-700 dark:text-rose-300 border-rose-500/30' }
                  : { label: 'Faol 🟢', color: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/30' };

              return (
                <div
                  key={item.user_id}
                  className="bg-tg-section border border-tg-secondary rounded-2xl p-3.5 sm:p-4 shadow-xs space-y-3 hover:border-blue-500/40 transition-all"
                >
                  <div className="flex items-start justify-between gap-2.5">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-10 h-10 rounded-2xl bg-blue-500/15 text-blue-600 dark:text-blue-400 flex items-center justify-center font-black text-sm shrink-0 border border-blue-500/20">
                        {item.full_name.charAt(0)}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="font-black text-xs sm:text-sm text-tg-text truncate">
                            {item.full_name}
                          </h4>
                          <span
                            className={`px-2 py-0.5 rounded-full text-[9.5px] font-extrabold border ${statusBadge.color}`}
                          >
                            {statusBadge.label}
                          </span>
                        </div>

                        <div className="flex items-center gap-2 mt-0.5 text-[11px] text-tg-hint flex-wrap font-mono">
                          {item.username && (
                            <span className="text-blue-600 dark:text-blue-400 font-bold">
                              {item.username}
                            </span>
                          )}
                          <span>ID: {item.telegram_id}</span>
                        </div>
                      </div>
                    </div>

                    <div className="text-right shrink-0">
                      <span className="text-xs font-black text-blue-600 dark:text-blue-400 block">
                        {item.lessons_watched} ta dars
                      </span>
                      <span className="text-[10px] text-tg-hint flex items-center justify-end gap-1 mt-0.5">
                        <Clock className="w-2.5 h-2.5" />
                        {item.last_activity}
                      </span>
                    </div>
                  </div>

                  {/* Mentor & Group Information */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 border-t border-tg-secondary/60 text-[11px]">
                    {item.mentor_name && (
                      <div className="flex items-center gap-1.5 text-tg-text">
                        <span className="text-tg-hint">Mentor:</span>
                        <span className="font-bold text-amber-700 dark:text-amber-300">
                          👨‍🏫 {item.mentor_name}
                        </span>
                      </div>
                    )}
                    {item.cabinet_name && (
                      <div className="flex items-center gap-1.5 text-tg-text truncate">
                        <span className="text-tg-hint">Guruh:</span>
                        <span className="font-semibold text-tg-text truncate">
                          {item.cabinet_name}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Progress Bar */}
                  {item.progress_percent !== undefined && (
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-[10px] font-bold text-tg-hint">
                        <span>Kurs o'zlashtirish darajasi:</span>
                        <span className="text-blue-600 dark:text-blue-400">{item.progress_percent}%</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-tg-secondary overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            item.progress_percent === 100
                              ? 'bg-gradient-to-r from-amber-500 to-emerald-500'
                              : 'bg-gradient-to-r from-blue-500 to-indigo-500'
                          }`}
                          style={{ width: `${item.progress_percent}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Direct Contact Button */}
                  {item.username && (
                    <div className="pt-1 flex items-center justify-end">
                      <a
                        href={`https://t.me/${item.username.replace(/^@/, '')}`}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-blue-600/10 hover:bg-blue-600/20 text-blue-600 dark:text-blue-400 text-[11px] font-bold transition-all"
                      >
                        <Send className="w-3 h-3" />
                        <span>Telegramda yozish</span>
                      </a>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Back Button */}
      <div className="pt-2">
        <button
          onClick={() => {
            triggerHaptic('light');
            if (cabinetId) {
              onNavigate({ type: 'cabinet', cabinetId });
            } else {
              onNavigate({ type: 'cabinet' });
            }
          }}
          className="w-full py-3 rounded-2xl bg-tg-secondary hover:bg-tg-secondary/80 text-tg-text font-bold text-xs transition-all flex items-center justify-center gap-1.5 cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Guruh chatiga qaytish</span>
        </button>
      </div>
    </div>
  );
};
