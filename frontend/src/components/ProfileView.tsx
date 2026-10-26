import React, { useState, useEffect } from 'react';
import {
  User,
  ShieldCheck,
  BookOpen,
  Award,
  Flame,
  Clock,
  Wallet,
  Phone,
  AtSign,
  Calendar,
  Edit3,
  Check,
  X,
  Sparkles,
  ChevronRight,
  ChevronDown,
  GraduationCap,
  TrendingUp,
  RefreshCw,
  Copy,
  Info,
  Crown,
  CheckCircle2,
  PlayCircle,
  BarChart2,
  Users,
  Settings,
  ArrowRight,
  Camera,
  CreditCard,
} from 'lucide-react';
import { UserProfile, AppView, Course } from '../types';
import {
  fetchUserProfile,
  updateUserProfile,
  submitMentorApplication,
  fetchMyMentorApplication,
  MyMentorApplicationResponse,
  fetchCourses,
} from '../services/api';
import { triggerHaptic, getTelegramUser } from '../services/telegram';

interface ProfileViewProps {
  onNavigate: (view: AppView) => void;
}

export const ProfileView: React.FC<ProfileViewProps> = ({ onNavigate }) => {
  const tgUser = getTelegramUser();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [showInfoModal, setShowInfoModal] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [showSuccessToast, setShowSuccessToast] = useState(false);
  const [avatarError, setAvatarError] = useState(false);

  // Edit Form State
  const [editForm, setEditForm] = useState({
    first_name: '',
    last_name: '',
    phone: '',
    username: '',
  });

  // Mentor Application State
  const [showMentorModal, setShowMentorModal] = useState(false);
  const [mentorAppLoading, setMentorAppLoading] = useState(false);
  const [myApplication, setMyApplication] = useState<any>(null);
  const [mentorSuccessMsg, setMentorSuccessMsg] = useState<string | null>(null);
  const [mentorErrorMsg, setMentorErrorMsg] = useState<string | null>(null);
  const [availableCourses, setAvailableCourses] = useState<Course[]>([]);
  const [mentorForm, setMentorForm] = useState({
    full_name: '',
    phone: '',
    course_direction: 'Barcha kurslar (Hammasi)',
    experience_bio: '',
    telegram_username: '',
  });

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    setLoading(true);
    try {
      const data = await fetchUserProfile();
      setProfile(data);
      setEditForm({
        first_name: data.first_name || '',
        last_name: data.last_name || '',
        phone: data.phone || '',
        username: data.username ? data.username.replace(/^@/, '') : '',
      });

      try {
        const coursesData = await fetchCourses();
        setAvailableCourses(coursesData);
      } catch (cErr) {
        console.warn('Kurslarni yuklashda xatolik', cErr);
      }

      try {
        const appData: any = await fetchMyMentorApplication();
        const appObj = appData?.application ? { ...appData.application, payment_amount: appData.payment_amount } : appData;
        setMyApplication(appObj);
      } catch (err) {
        console.warn('Mentor arizasini tekshirishda xatolik', err);
      }
    } catch (e) {
      console.error('Failed to load user profile', e);
    } finally {
      setLoading(false);
    }
  };

  const openMentorModal = () => {
    triggerHaptic('light');
    const defaultName =
      (profile ? `${profile.first_name || ''} ${profile.last_name || ''}`.trim() : '') ||
      (tgUser ? `${tgUser.first_name || ''} ${tgUser.last_name || ''}`.trim() : '');
    const defaultPhone = profile?.phone || '';
    const defaultUsername = profile?.username || tgUser?.username || '';

    setMentorForm((prev) => ({
      ...prev,
      full_name: prev.full_name || defaultName,
      phone: prev.phone || defaultPhone,
      telegram_username: prev.telegram_username || (defaultUsername ? `@${defaultUsername.replace(/^@/, '')}` : ''),
    }));
    setMentorSuccessMsg(null);
    setMentorErrorMsg(null);
    setShowMentorModal(true);
  };

  const handleMentorSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mentorForm.full_name.trim() || !mentorForm.phone.trim() || !mentorForm.experience_bio.trim()) {
      setMentorErrorMsg("Iltimos, barcha majburiy maydonlarni to'ldiring!");
      return;
    }
    triggerHaptic('medium');
    setMentorAppLoading(true);
    setMentorErrorMsg(null);
    try {
      const res = await submitMentorApplication({
        full_name: mentorForm.full_name.trim(),
        phone: mentorForm.phone.trim(),
        course_direction: mentorForm.course_direction,
        experience_bio: mentorForm.experience_bio.trim(),
        telegram_username: mentorForm.telegram_username.trim() || undefined,
      });
      setMentorSuccessMsg(res.message || "Arizangiz muvaffaqiyatli qabul qilindi!");
      triggerHaptic('success');
      const appData: any = await fetchMyMentorApplication();
      const appObj = appData?.application ? { ...appData.application, payment_amount: appData.payment_amount } : appData;
      setMyApplication(appObj);
      setTimeout(() => {
        setShowMentorModal(false);
        setMentorSuccessMsg(null);
      }, 2500);
    } catch (err: any) {
      setMentorErrorMsg(err.message || "Xatolik yuz berdi. Qayta urinib ko'ring.");
      triggerHaptic('error');
    } finally {
      setMentorAppLoading(false);
    }
  };

  const handleCopy = (key: string, text: string) => {
    triggerHaptic('light');
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleSave = async () => {
    if (!profile) return;
    triggerHaptic('medium');
    setSaving(true);
    try {
      const updated = await updateUserProfile({
        first_name: editForm.first_name.trim(),
        last_name: editForm.last_name.trim(),
        phone: editForm.phone.trim(),
        username: editForm.username ? `@${editForm.username.replace(/^@/, '').trim()}` : undefined,
      });
      setProfile(updated);
      setIsEditing(false);
      setShowSuccessToast(true);
      setTimeout(() => setShowSuccessToast(false), 3000);
    } catch (e) {
      console.error('Failed to update profile', e);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4 pb-28 max-w-2xl mx-auto px-4 pt-2 animate-pulse">
        <div className="h-44 bg-tg-section border border-tg-secondary rounded-3xl" />
        <div className="grid grid-cols-2 gap-3">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="h-24 bg-tg-section border border-tg-secondary rounded-2xl" />
          ))}
        </div>
        <div className="h-36 bg-tg-section border border-tg-secondary rounded-3xl" />
        <div className="h-20 bg-tg-section border border-tg-secondary rounded-2xl" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="p-8 text-center bg-tg-section border border-tg-secondary rounded-3xl text-tg-hint max-w-md mx-auto my-6 shadow-xs">
        <p>Profil ma'lumotlarini yuklab bo'lmadi.</p>
        <button
          onClick={loadProfile}
          className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-bold shadow-xs hover:bg-blue-700 transition-colors"
        >
          Qayta yuklash
        </button>
      </div>
    );
  }

  const avatarUrl =
    profile.avatar || tgUser?.photo_url || (profile.telegram_id ? `/api/users/${profile.telegram_id}/avatar` : '');
  const displayUsername = (() => {
    const raw = (
      profile.username && !profile.username.startsWith('@id') && profile.username !== '@user'
        ? profile.username
        : tgUser?.username || profile.first_name || 'foydalanuvchi'
    )
      .replace(/^@+/, '')
      .trim();
    return `@${raw}`;
  })();

  const firstName = profile.first_name || tgUser?.first_name || 'Foydalanuvchi';
  const lastName = profile.last_name || tgUser?.last_name || '';
  const fullName = `${firstName} ${lastName}`.trim() || 'Foydalanuvchi';

  const roleBadge = (() => {
    if (profile.role === 'super_mentor') {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-full font-semibold bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/25 shrink-0">
          <Crown className="w-3 h-3 text-blue-600 dark:text-blue-400" />
          <span>Super Mentor</span>
        </span>
      );
    }
    if (profile.role === 'admin') {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-full font-semibold bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 border border-indigo-500/25 shrink-0">
          <ShieldCheck className="w-3 h-3 text-indigo-600 dark:text-indigo-400" />
          <span>Admin</span>
        </span>
      );
    }
    if (profile.role === 'mentor') {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-full font-semibold bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/25 shrink-0">
          <Crown className="w-3 h-3 text-blue-600 dark:text-blue-400" />
          <span>Mentor</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-full font-semibold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/25 shrink-0">
        <GraduationCap className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
        <span>O'quvchi</span>
      </span>
    );
  })();

  const isApprovedMentor =
    profile?.role === 'mentor' || profile?.role === 'super_mentor' || myApplication?.status === 'approved';
  const isPaymentPending = myApplication?.status === 'payment_pending';
  const isReceiptSubmitted = myApplication?.status === 'receipt_submitted';
  const isReceiptRejected = myApplication?.status === 'receipt_rejected';
  const isPending = myApplication?.status === 'pending';
  const isRejected = myApplication?.status === 'rejected';

  // Format study time: e.g. "3 soat 37 daq"
  const totalMinutes = profile.total_study_time_minutes || 0;
  const studyHours = Math.floor(totalMinutes / 60);
  const studyMins = totalMinutes % 60;
  const studyTimeFormatted =
    studyHours > 0
      ? `${studyHours} soat ${studyMins} daq`
      : studyMins > 0
      ? `${studyMins} daq`
      : '0 daq';

  // Days of week for activity chart
  const daysOfWeek = [
    { label: 'Du', active: true, height: 'h-8' },
    { label: 'Se', active: true, height: 'h-10' },
    { label: 'Ch', active: true, height: 'h-9' },
    { label: 'Pa', active: true, height: 'h-12' },
    { label: 'Ju', active: true, height: 'h-9' },
    { label: 'Sh', active: false, height: 'h-8' },
    { label: 'Ya', active: true, height: 'h-10' },
  ];

  return (
    <div className="space-y-3.5 pb-28 max-w-2xl mx-auto px-4 pt-1 animate-in fade-in duration-200">
      {/* Toast Notification */}
      {showSuccessToast && (
        <div className="fixed top-16 left-1/2 -translate-x-1/2 z-50 bg-emerald-600 text-white px-4 py-2 rounded-2xl text-xs font-bold shadow-lg flex items-center gap-2 animate-in fade-in slide-in-from-top-2">
          <Check className="w-4 h-4" />
          <span>Profil ma'lumotlari muvaffaqiyatli saqlandi!</span>
        </div>
      )}

      {/* ======================================================== */}
      {/* 1. MAIN PROFILE CARD (matching Bilim GO Dashboard UI)   */}
      {/* ======================================================== */}
      <div className="relative overflow-hidden bg-tg-section border border-tg-secondary rounded-3xl p-4 sm:p-5 shadow-xs">
        {/* Soft background blue gradient glow on the right */}
        <div className="absolute right-0 top-0 bottom-0 w-2/5 bg-gradient-to-l from-blue-500/10 via-blue-500/5 to-transparent pointer-events-none rounded-r-3xl" />

        <div className="flex items-center gap-4 sm:gap-5 relative z-10">
          {/* Avatar with small Camera icon overlay badge */}
          <div className="relative shrink-0">
            {avatarUrl && !avatarError ? (
              <img
                src={avatarUrl}
                alt={fullName}
                referrerPolicy="no-referrer"
                onError={() => setAvatarError(true)}
                className="w-18 h-18 sm:w-20 sm:h-20 rounded-full object-cover border-2 border-blue-500 shadow-sm"
              />
            ) : (
              <div className="w-18 h-18 sm:w-20 sm:h-20 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center font-black text-2xl shadow-sm border-2 border-blue-500">
                {profile.first_name ? profile.first_name.charAt(0).toUpperCase() : 'U'}
              </div>
            )}
            {/* Camera icon button overlay badge at bottom-right */}
            <button
              onClick={() => {
                triggerHaptic('light');
                setIsEditing(true);
              }}
              className="absolute -bottom-1 -right-1 w-6 h-6 sm:w-7 sm:h-7 rounded-full bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center border-2 border-tg-section shadow-xs cursor-pointer transition-transform active:scale-90"
              title="Rasmni o'zgartirish"
            >
              <Camera className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
            </button>
          </div>

          {/* User Details */}
          <div className="flex-1 min-w-0 space-y-1">
            <h2 className="text-lg sm:text-xl font-bold text-tg-text tracking-tight truncate">
              {fullName}
            </h2>

            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs sm:text-sm font-semibold text-blue-600 dark:text-blue-400 truncate">
                {displayUsername}
              </span>
              {roleBadge}
            </div>

            <button
              onClick={() => {
                triggerHaptic('light');
                setIsEditing(true);
              }}
              className="flex items-center gap-1.5 text-xs text-tg-hint hover:text-blue-600 dark:hover:text-blue-400 font-medium transition-colors pt-0.5 cursor-pointer"
            >
              <Edit3 className="w-3 h-3 text-tg-hint" />
              <span>Profilni tahrirlash</span>
            </button>
          </div>
        </div>
      </div>

      {/* ======================================================== */}
      {/* 2. 4 METRIC STATS CARDS (2x2 Grid)                      */}
      {/* ======================================================== */}
      <div className="grid grid-cols-2 gap-3">
        {/* Kurslar */}
        <div
          onClick={() => {
            triggerHaptic('light');
            onNavigate({ type: 'my-courses' });
          }}
          className="bg-tg-section border border-tg-secondary rounded-2xl p-3.5 sm:p-4 shadow-xs flex items-center justify-between cursor-pointer hover:border-blue-500/40 transition-all group"
        >
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 sm:w-11 sm:h-11 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
              <BookOpen className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <p className="text-xs text-tg-hint font-medium truncate">Kurslar</p>
              <p className="text-xl sm:text-2xl font-bold text-tg-text truncate">
                {profile.enrolled_courses_count || 0}
              </p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-tg-hint/50 group-hover:text-tg-hint group-hover:translate-x-0.5 transition-transform shrink-0" />
        </div>

        {/* Darslar */}
        <div
          onClick={() => {
            triggerHaptic('light');
            onNavigate({ type: 'my-courses' });
          }}
          className="bg-tg-section border border-tg-secondary rounded-2xl p-3.5 sm:p-4 shadow-xs flex items-center justify-between cursor-pointer hover:border-emerald-500/40 transition-all group"
        >
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 sm:w-11 sm:h-11 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
              <PlayCircle className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <p className="text-xs text-tg-hint font-medium truncate">Darslar</p>
              <p className="text-xl sm:text-2xl font-bold text-tg-text truncate">
                {profile.completed_lessons_count || 0}
              </p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-tg-hint/50 group-hover:text-tg-hint group-hover:translate-x-0.5 transition-transform shrink-0" />
        </div>

        {/* Ketma-ketlik */}
        <div className="bg-tg-section border border-tg-secondary rounded-2xl p-3.5 sm:p-4 shadow-xs flex items-center justify-between group">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 sm:w-11 sm:h-11 rounded-xl bg-orange-500/10 text-orange-500 flex items-center justify-center shrink-0">
              <Flame className="w-5 h-5 fill-orange-500" />
            </div>
            <div className="min-w-0">
              <p className="text-xs text-tg-hint font-medium truncate">Ketma-ketlik</p>
              <p className="text-xl sm:text-2xl font-bold text-tg-text truncate">
                {profile.streak_days || 1} kun
              </p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-tg-hint/50 group-hover:text-tg-hint group-hover:translate-x-0.5 transition-transform shrink-0" />
        </div>

        {/* O'qish vaqti */}
        <div className="bg-tg-section border border-tg-secondary rounded-2xl p-3.5 sm:p-4 shadow-xs flex items-center justify-between group">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 sm:w-11 sm:h-11 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center shrink-0">
              <Clock className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <p className="text-xs text-tg-hint font-medium truncate">O'qish vaqti</p>
              <p className="text-sm sm:text-base font-bold text-tg-text truncate">
                {studyTimeFormatted}
              </p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-tg-hint/50 group-hover:text-tg-hint group-hover:translate-x-0.5 transition-transform shrink-0" />
        </div>
      </div>

      {/* ======================================================== */}
      {/* 3. MENING FAOLIYATIM (Activity Streak Chart Card)       */}
      {/* ======================================================== */}
      <div className="bg-tg-section border border-tg-secondary rounded-3xl p-4 sm:p-5 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <h3 className="font-bold text-sm sm:text-base text-tg-text">Mening faoliyatim</h3>
          </div>
          <div className="flex items-center gap-1 text-xs text-tg-hint font-medium">
            <span>Bu hafta</span>
            <ChevronDown className="w-3.5 h-3.5 text-tg-hint" />
          </div>
        </div>

        <div className="flex items-center justify-between gap-3 pt-1">
          {/* 7 Days Pill Bars */}
          <div className="flex items-end gap-2.5 sm:gap-3.5">
            {daysOfWeek.map((day, idx) => (
              <div key={idx} className="flex flex-col items-center gap-2">
                <div
                  className={`w-3.5 sm:w-4 rounded-full transition-all ${
                    day.active
                      ? `${day.height} bg-blue-600 shadow-2xs`
                      : 'h-8 bg-tg-secondary'
                  }`}
                />
                <span className="text-[11px] font-medium text-tg-hint">{day.label}</span>
              </div>
            ))}
          </div>

          {/* Vertical Divider */}
          <div className="h-10 w-px bg-tg-secondary shrink-0" />

          {/* Right Status Indicator */}
          <div className="flex items-center gap-2 shrink-0">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
            <span className="text-xs font-medium text-tg-text/90">
              Faolligingiz davom etmoqda
            </span>
          </div>
        </div>
      </div>

      {/* ======================================================== */}
      {/* 4. SERTIFIKATLAR KARTASI                                */}
      {/* ======================================================== */}
      <div className="bg-tg-section border border-tg-secondary rounded-3xl p-4 shadow-xs flex items-center justify-between cursor-pointer hover:border-purple-500/30 transition-all group">
        <div className="flex items-center gap-3.5 min-w-0">
          <div className="w-12 h-12 rounded-2xl bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center shrink-0">
            <Award className="w-6 h-6" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h4 className="font-bold text-sm text-tg-text truncate">Sertifikatlar</h4>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-purple-500/15 text-purple-600 dark:text-purple-400 border border-purple-500/25 shrink-0">
                Tez kunda
              </span>
            </div>
            <p className="text-xs text-tg-hint mt-0.5 line-clamp-1">
              Kursni tugatganingizdan so'ng sertifikatlaringiz shu yerda ko'rinadi.
            </p>
          </div>
        </div>
        <ChevronRight className="w-4 h-4 text-tg-hint/50 group-hover:text-tg-hint group-hover:translate-x-0.5 transition-transform shrink-0" />
      </div>

      {/* ======================================================== */}
      {/* 5. MENTOR HOLATI BANNERI                                */}
      {/* ======================================================== */}
      {isApprovedMentor ? (
        <div className="bg-gradient-to-r from-emerald-500/10 via-teal-500/5 to-blue-500/5 border border-emerald-500/20 rounded-3xl p-4 sm:p-5 flex items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-3.5 min-w-0">
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
              <GraduationCap className="w-6 h-6" />
            </div>
            <div className="min-w-0">
              <span className="text-[9px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-700 dark:text-emerald-300">
                SUPER MENTORLIK
              </span>
              <h4 className="font-bold text-sm sm:text-base text-tg-text mt-1">
                Siz rasmiy Mentorsiz!
              </h4>
              <p className="text-xs text-tg-hint mt-0.5 line-clamp-1">
                O'quvchilar va guruhlaringizni boshqarish uchun mentor kabinetiga o'ting.
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              triggerHaptic('medium');
              onNavigate({ type: 'cabinet' });
            }}
            className="px-3.5 sm:px-4 py-2 sm:py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shrink-0 shadow-xs transition-all active:scale-95 cursor-pointer"
          >
            <span>Kabinetga o'tish</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      ) : isPaymentPending ? (
        <div className="bg-gradient-to-r from-amber-500/10 via-orange-500/5 to-yellow-500/5 border border-amber-500/25 rounded-3xl p-4 sm:p-5 flex items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-3.5 min-w-0">
            <div className="w-12 h-12 rounded-2xl bg-amber-500/20 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0">
              <CreditCard className="w-6 h-6" />
            </div>
            <div className="min-w-0">
              <span className="text-[9px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-700 dark:text-amber-300">
                SUPER MENTORLIK
              </span>
              <h4 className="font-bold text-sm text-tg-text mt-1">
                To'lov kutilmoqda 💳
              </h4>
              <p className="text-xs text-tg-hint mt-0.5 leading-relaxed">
                Arizangiz ma'qullandi! To'lov summasi: <b className="text-tg-text">{(myApplication?.payment_amount || 949000).toLocaleString()} UZS</b>. 
                Karta: <code className="bg-amber-500/15 text-amber-700 dark:text-amber-300 px-1 py-0.5 rounded text-[11px] font-mono">{myApplication?.admin_card_number || '8600 **** **** ****'}</code> ({myApplication?.admin_card_holder || 'Admin'}). To'lov qilib, chekni Telegram botga yuboring.
              </p>
            </div>
          </div>
        </div>
      ) : isReceiptSubmitted ? (
        <div className="bg-gradient-to-r from-blue-500/10 via-indigo-500/5 to-cyan-500/5 border border-blue-500/25 rounded-3xl p-4 sm:p-5 flex items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-3.5 min-w-0">
            <div className="w-12 h-12 rounded-2xl bg-blue-500/20 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
              <Clock className="w-6 h-6" />
            </div>
            <div className="min-w-0">
              <span className="text-[9px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-700 dark:text-blue-300">
                SUPER MENTORLIK
              </span>
              <h4 className="font-bold text-sm text-tg-text mt-1">
                To'lov cheki tekshirilmoqda ⏳
              </h4>
              <p className="text-xs text-tg-hint mt-0.5 line-clamp-1">
                To'lov chekingiz qabul qilingan. Admin tasdiqlashi bilan hisobingiz to'liq faollashtiriladi.
              </p>
            </div>
          </div>
        </div>
      ) : isReceiptRejected ? (
        <div className="bg-gradient-to-r from-rose-500/10 to-red-500/5 border border-rose-500/25 rounded-3xl p-4 sm:p-5 flex items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-3.5 min-w-0">
            <div className="w-12 h-12 rounded-2xl bg-rose-500/20 text-rose-600 dark:text-rose-400 flex items-center justify-center shrink-0">
              <X className="w-6 h-6" />
            </div>
            <div className="min-w-0">
              <span className="text-[9px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-700 dark:text-rose-300">
                SUPER MENTORLIK
              </span>
              <h4 className="font-bold text-sm text-tg-text mt-1">
                Chek tasdiqlanmadi ⚠️
              </h4>
              <p className="text-xs text-tg-hint mt-0.5 line-clamp-1">
                Yuborgan chekingiz qabul qilinmadi. Iltimos, qaytadan to'g'ri to'lov chekini Telegram botga yuboring.
              </p>
            </div>
          </div>
        </div>
      ) : isPending ? (
        <div className="bg-gradient-to-r from-amber-500/10 via-yellow-500/5 to-orange-500/5 border border-amber-500/25 rounded-3xl p-4 sm:p-5 flex items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-3.5 min-w-0">
            <div className="w-12 h-12 rounded-2xl bg-amber-500/20 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0">
              <GraduationCap className="w-6 h-6" />
            </div>
            <div className="min-w-0">
              <span className="text-[9px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-700 dark:text-amber-300">
                SUPER MENTORLIK
              </span>
              <h4 className="font-bold text-sm text-tg-text mt-1">
                Arizangiz ko'rib chiqilmoqda
              </h4>
              <p className="text-xs text-tg-hint mt-0.5 line-clamp-1">
                Arizangiz qabul qilingan va ma'muriyat tomonidan ko'rib chiqilmoqda.
              </p>
            </div>
          </div>
          <button
            onClick={openMentorModal}
            className="px-3.5 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-semibold shrink-0 cursor-pointer"
          >
            Arizani ko'rish
          </button>
        </div>
      ) : isRejected ? (
        <div className="bg-gradient-to-r from-rose-500/10 to-red-500/5 border border-rose-500/25 rounded-3xl p-4 sm:p-5 flex items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-3.5 min-w-0">
            <div className="w-12 h-12 rounded-2xl bg-rose-500/20 text-rose-600 dark:text-rose-400 flex items-center justify-center shrink-0">
              <GraduationCap className="w-6 h-6" />
            </div>
            <div className="min-w-0">
              <span className="text-[9px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-700 dark:text-rose-300">
                SUPER MENTORLIK
              </span>
              <h4 className="font-bold text-sm text-tg-text mt-1">
                Qayta ariza topshirish
              </h4>
              <p className="text-xs text-tg-hint mt-0.5 line-clamp-1">
                Arizangiz rad etilgan. Qayta ariza topshirishingiz mumkin.
              </p>
            </div>
          </div>
          <button
            onClick={openMentorModal}
            className="px-3.5 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-semibold shrink-0 cursor-pointer"
          >
            Qayta topshirish
          </button>
        </div>
      ) : (
        <div className="bg-gradient-to-r from-emerald-500/10 via-teal-500/5 to-blue-500/5 border border-emerald-500/25 rounded-3xl p-4 sm:p-5 flex items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-3.5 min-w-0">
            <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
              <GraduationCap className="w-6 h-6" />
            </div>
            <div className="min-w-0">
              <span className="text-[9px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-700 dark:text-emerald-300">
                SUPER MENTORLIK
              </span>
              <h4 className="font-bold text-sm sm:text-base text-tg-text mt-1">
                Mentorlikka ariza berish
              </h4>
              <p className="text-xs text-tg-hint mt-0.5 line-clamp-1">
                O'z tajribangizni boshqalar bilan bo'lishing va daromad qiling.
              </p>
            </div>
          </div>
          <button
            onClick={openMentorModal}
            className="px-3.5 sm:px-4 py-2 sm:py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shrink-0 shadow-xs transition-all active:scale-95 cursor-pointer"
          >
            <span>Ariza topshirish</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* ======================================================== */}
      {/* 6. BOSHQARUV RO'YXATI (Navigation Stack)                */}
      {/* ======================================================== */}
      <div className="space-y-2.5 pt-1">
        <div className="flex items-center justify-between px-1">
          <h3 className="text-base sm:text-lg font-bold text-tg-text">Boshqaruv</h3>
          <button
            onClick={() => setShowInfoModal(true)}
            className="text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
          >
            <Info className="w-3.5 h-3.5" />
            <span>Hisob tafsilotlari</span>
          </button>
        </div>

        <div className="space-y-2">
          {/* Mening kurslarim */}
          <button
            onClick={() => {
              triggerHaptic('light');
              onNavigate({ type: 'my-courses' });
            }}
            className="w-full bg-tg-section border border-tg-secondary rounded-2xl p-3.5 sm:p-4 flex items-center justify-between hover:border-blue-500/40 hover:bg-tg-secondary/40 transition-all text-left shadow-xs group cursor-pointer"
          >
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
                <BookOpen className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <p className="font-bold text-sm text-tg-text truncate">Mening kurslarim</p>
                <p className="text-xs text-tg-hint truncate">Darslarni davom ettirish</p>
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-tg-hint/50 group-hover:text-tg-hint group-hover:translate-x-0.5 transition-transform shrink-0" />
          </button>

          {/* Kabinet & Guruhlar */}
          <button
            onClick={() => {
              triggerHaptic('light');
              onNavigate({ type: 'cabinet' });
            }}
            className="w-full bg-tg-section border border-tg-secondary rounded-2xl p-3.5 sm:p-4 flex items-center justify-between hover:border-purple-500/40 hover:bg-tg-secondary/40 transition-all text-left shadow-xs group cursor-pointer"
          >
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center shrink-0">
                <Users className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <p className="font-bold text-sm text-tg-text truncate">Kabinet & Guruhlar</p>
                <p className="text-xs text-tg-hint truncate">Mentor va guruh chati</p>
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-tg-hint/50 group-hover:text-tg-hint group-hover:translate-x-0.5 transition-transform shrink-0" />
          </button>

          {/* Talabalar nazorati */}
          <button
            onClick={() => {
              triggerHaptic('light');
              onNavigate({ type: 'mentor-stats' });
            }}
            className="w-full bg-tg-section border border-tg-secondary rounded-2xl p-3.5 sm:p-4 flex items-center justify-between hover:border-orange-500/40 hover:bg-tg-secondary/40 transition-all text-left shadow-xs group cursor-pointer"
          >
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-xl bg-orange-500/10 text-orange-500 flex items-center justify-center shrink-0">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <p className="font-bold text-sm text-tg-text truncate">Talabalar nazorati</p>
                <p className="text-xs text-tg-hint truncate">Mentor / Super Admin</p>
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-tg-hint/50 group-hover:text-tg-hint group-hover:translate-x-0.5 transition-transform shrink-0" />
          </button>

          {/* Admin Panel */}
          <button
            onClick={() => {
              triggerHaptic('light');
              onNavigate({ type: 'admin-dashboard' });
            }}
            className="w-full bg-tg-section border border-tg-secondary rounded-2xl p-3.5 sm:p-4 flex items-center justify-between hover:border-rose-500/40 hover:bg-tg-secondary/40 transition-all text-left shadow-xs group cursor-pointer"
          >
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400 flex items-center justify-center shrink-0">
                <Settings className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <p className="font-bold text-sm text-tg-text truncate">Admin Panel</p>
                <p className="text-xs text-tg-hint truncate">Umumiy tizim nazorati</p>
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-tg-hint/50 group-hover:text-tg-hint group-hover:translate-x-0.5 transition-transform shrink-0" />
          </button>
        </div>
      </div>

      {/* ======================================================== */}
      {/* 7. EDIT PROFILE MODAL (Tahrirlash Modali)               */}
      {/* ======================================================== */}
      {isEditing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="w-full max-w-md bg-tg-bg border border-tg-secondary rounded-3xl p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-tg-secondary pb-3">
              <h3 className="font-bold text-sm text-tg-text flex items-center gap-2">
                <Edit3 className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <span>Profil ma'lumotlarini tahrirlash</span>
              </h3>
              <button
                onClick={() => setIsEditing(false)}
                className="p-1 rounded-lg text-tg-hint hover:text-tg-text hover:bg-tg-secondary cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-[11px] font-bold text-tg-hint uppercase">Ism</label>
                <input
                  type="text"
                  value={editForm.first_name}
                  onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
                  placeholder="Ismingiz"
                  className="w-full bg-tg-secondary border border-tg-secondary focus:border-blue-500 text-tg-text placeholder:text-tg-hint text-xs rounded-xl px-3.5 py-2.5 outline-none font-medium"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-bold text-tg-hint uppercase">Familiya</label>
                <input
                  type="text"
                  value={editForm.last_name}
                  onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
                  placeholder="Familiyangiz"
                  className="w-full bg-tg-secondary border border-tg-secondary focus:border-blue-500 text-tg-text placeholder:text-tg-hint text-xs rounded-xl px-3.5 py-2.5 outline-none font-medium"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-bold text-tg-hint uppercase">Telefon raqam</label>
                <input
                  type="text"
                  value={editForm.phone}
                  onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                  placeholder="+998 90 123 45 67"
                  className="w-full bg-tg-secondary border border-tg-secondary focus:border-blue-500 text-tg-text placeholder:text-tg-hint text-xs rounded-xl px-3.5 py-2.5 outline-none font-medium"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-bold text-tg-hint uppercase">Telegram Username</label>
                <input
                  type="text"
                  value={editForm.username}
                  onChange={(e) => setEditForm({ ...editForm, username: e.target.value })}
                  placeholder="username (masalan: nurulla)"
                  className="w-full bg-tg-secondary border border-tg-secondary focus:border-blue-500 text-tg-text placeholder:text-tg-hint text-xs rounded-xl px-3.5 py-2.5 outline-none font-medium"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-tg-secondary">
              <button
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 rounded-xl bg-tg-secondary text-tg-text text-xs font-bold hover:bg-tg-secondary/80 cursor-pointer"
              >
                Bekor qilish
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !editForm.first_name.trim()}
                className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-bold transition-all shadow-xs flex items-center gap-1.5 cursor-pointer"
              >
                {saving ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Saqlanmoqda...</span>
                  </>
                ) : (
                  <>
                    <Check className="w-3.5 h-3.5" />
                    <span>Saqlash</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* 8. HISOB TAFSILOTLARI MODALI (ID, Hamyon, Sana)        */}
      {/* ======================================================== */}
      {showInfoModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="w-full max-w-md bg-tg-bg border border-tg-secondary rounded-3xl p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-tg-secondary pb-3">
              <h3 className="font-bold text-sm text-tg-text flex items-center gap-2">
                <Info className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <span>Shaxsiy hisob tafsilotlari</span>
              </h3>
              <button
                onClick={() => setShowInfoModal(false)}
                className="p-1 rounded-lg text-tg-hint hover:text-tg-text hover:bg-tg-secondary cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2.5 text-xs sm:text-sm">
              {/* Telegram ID */}
              <div className="flex items-center justify-between p-3 rounded-2xl bg-tg-secondary">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-[11px] text-tg-hint font-medium">Telegram ID</p>
                    <p className="font-mono font-bold text-tg-text">{profile.telegram_id}</p>
                  </div>
                </div>
                <button
                  onClick={() => handleCopy('tg_id', String(profile.telegram_id))}
                  className="p-2 rounded-xl bg-tg-section border border-tg-secondary text-tg-hint hover:text-blue-600 dark:hover:text-blue-400 shadow-2xs cursor-pointer transition-colors"
                  title="Nusxalash"
                >
                  {copiedKey === 'tg_id' ? (
                    <Check className="w-4 h-4 text-emerald-500" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
              </div>

              {/* Phone */}
              <div className="flex items-center justify-between p-3 rounded-2xl bg-tg-secondary">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                    <Phone className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-[11px] text-tg-hint font-medium">Telefon raqami</p>
                    <p className="font-bold text-tg-text">{profile.phone || 'Biriktirilmagan'}</p>
                  </div>
                </div>
              </div>

              {/* Balance */}
              <div className="flex items-center justify-between p-3 rounded-2xl bg-tg-secondary">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center">
                    <Wallet className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-[11px] text-tg-hint font-medium">Hamyon balansi</p>
                    <p className="font-black text-tg-text text-sm">
                      {(profile.wallet_balance || 0).toLocaleString()} UZS
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    triggerHaptic('light');
                    setShowInfoModal(false);
                    onNavigate({ type: 'catalog' });
                  }}
                  className="px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-xs cursor-pointer"
                >
                  Kurs olish
                </button>
              </div>

              {/* Joined Date */}
              <div className="flex items-center justify-between p-3 rounded-2xl bg-tg-secondary">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                    <Calendar className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-[11px] text-tg-hint font-medium">Ro'yxatdan o'tgan sana</p>
                    <p className="font-bold text-tg-text">{profile.joined_date || 'Nomaʼlum'}</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-tg-secondary">
              <button
                onClick={() => setShowInfoModal(false)}
                className="px-4 py-2 rounded-xl bg-tg-secondary text-tg-text text-xs font-bold hover:bg-tg-secondary/80 cursor-pointer"
              >
                Yopish
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* 9. MENTOR APPLICATION MODAL                             */}
      {/* ======================================================== */}
      {showMentorModal && (
        <div
          onClick={() => setShowMentorModal(false)}
          className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-lg bg-tg-bg border-t sm:border border-tg-secondary rounded-t-3xl sm:rounded-3xl p-5 sm:p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto animate-in slide-in-from-bottom duration-200"
          >
            {/* Mobile Drag Indicator */}
            <div className="w-12 h-1 bg-tg-hint/30 rounded-full mx-auto -mt-1 mb-1 sm:hidden shrink-0" />

            <div className="flex items-center justify-between pb-2 border-b border-tg-secondary">
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 rounded-xl bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                  <GraduationCap className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-base text-tg-text">Mentorlikka ariza berish</h3>
                  <p className="text-[11px] text-tg-hint">Super mentorlar jamoasiga qo'shiling</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowMentorModal(false)}
                className="p-1.5 rounded-xl text-tg-hint hover:text-tg-text hover:bg-tg-secondary cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {myApplication && myApplication.status === 'pending' && (
              <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-2xl text-xs text-amber-600 dark:text-amber-400 space-y-1">
                <p className="font-bold flex items-center gap-1.5">
                  <Clock className="w-4 h-4 text-amber-500" />
                  <span>Sizning arizangiz tekshirilmoqda</span>
                </p>
                <p className="text-[11px] opacity-90 pl-5.5 text-tg-hint">
                  Yo'nalish: <b className="text-tg-text">{myApplication.course_direction}</b>. Natijasi tez orada bildiriladi.
                </p>
              </div>
            )}

            {mentorSuccessMsg && (
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>{mentorSuccessMsg}</span>
              </div>
            )}

            {mentorErrorMsg && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-xs text-rose-600 dark:text-rose-400 flex items-center gap-2">
                <X className="w-4 h-4 text-rose-500 shrink-0" />
                <span>{mentorErrorMsg}</span>
              </div>
            )}

            <form onSubmit={handleMentorSubmit} className="space-y-3.5">
              <div className="space-y-1">
                <label className="text-xs font-bold text-tg-text">
                  To'liq ism-familiyangiz <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={mentorForm.full_name}
                  onChange={(e) => setMentorForm({ ...mentorForm, full_name: e.target.value })}
                  placeholder="Masalan: Sardor Rahimov"
                  className="w-full bg-tg-secondary border border-tg-secondary focus:border-emerald-500 text-tg-text placeholder:text-tg-hint text-xs rounded-xl px-3.5 py-2.5 outline-none font-medium"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-tg-text">
                    Telefon raqam <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    required
                    value={mentorForm.phone}
                    onChange={(e) => setMentorForm({ ...mentorForm, phone: e.target.value })}
                    placeholder="+998 90 123 45 67"
                    className="w-full bg-tg-secondary border border-tg-secondary focus:border-emerald-500 text-tg-text placeholder:text-tg-hint text-xs rounded-xl px-3.5 py-2.5 outline-none font-medium"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-tg-text">
                    Telegram username
                  </label>
                  <input
                    type="text"
                    value={mentorForm.telegram_username}
                    onChange={(e) => setMentorForm({ ...mentorForm, telegram_username: e.target.value })}
                    placeholder="@username"
                    className="w-full bg-tg-secondary border border-tg-secondary focus:border-emerald-500 text-tg-text placeholder:text-tg-hint text-xs rounded-xl px-3.5 py-2.5 outline-none font-medium"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-tg-text">
                  Qaysi yo'nalish bo'yicha mentorlik qilasiz? <span className="text-red-500">*</span>
                </label>
                <select
                  value={mentorForm.course_direction}
                  onChange={(e) => setMentorForm({ ...mentorForm, course_direction: e.target.value })}
                  className="w-full bg-tg-secondary border border-tg-secondary focus:border-emerald-500 text-tg-text text-xs rounded-xl px-3.5 py-2.5 outline-none font-medium"
                >
                  <option value="Barcha kurslar (Hammasi)">Barcha kurslar (Umumiy mentorlik)</option>
                  {availableCourses.map((c) => (
                    <option key={c.id} value={c.title}>
                      {c.title}
                    </option>
                  ))}
                  <option value="Boshqa yo'nalish">Boshqa maxsus yo'nalish</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-tg-text">
                  Tajribangiz va o'zingiz haqingizda <span className="text-red-500">*</span>
                </label>
                <textarea
                  required
                  rows={3}
                  value={mentorForm.experience_bio}
                  onChange={(e) => setMentorForm({ ...mentorForm, experience_bio: e.target.value })}
                  placeholder="Qancha vaqtdan beri ushbu sohadadasiz? Shogirdlar bilan ishlash tajribangiz bormi?.."
                  className="w-full bg-tg-secondary border border-tg-secondary focus:border-emerald-500 text-tg-text placeholder:text-tg-hint text-xs rounded-xl px-3.5 py-2.5 outline-none font-medium resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-tg-secondary">
                <button
                  type="button"
                  onClick={() => setShowMentorModal(false)}
                  className="px-4 py-2 rounded-xl bg-tg-secondary text-tg-text text-xs font-bold hover:bg-tg-secondary/80 cursor-pointer"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  disabled={mentorAppLoading}
                  className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-xs font-bold shadow-xs flex items-center gap-1.5 cursor-pointer transition-all active:scale-95"
                >
                  {mentorAppLoading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Yuborilmoqda...</span>
                    </>
                  ) : (
                    <>
                      <GraduationCap className="w-3.5 h-3.5" />
                      <span>Arizani jo'natish</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
