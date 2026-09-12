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
  ExternalLink,
  GraduationCap,
  TrendingUp,
  RefreshCw,
  Copy,
  Info,
  Crown,
  CheckCircle2,
  UserCheck,
} from 'lucide-react';
import { UserProfile, AppView } from '../types';
import { fetchUserProfile, updateUserProfile } from '../services/api';
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
    } catch (e) {
      console.error('Failed to load user profile', e);
    } finally {
      setLoading(false);
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
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="h-24 bg-tg-section border border-tg-secondary rounded-2xl" />
          ))}
        </div>
        <div className="h-40 bg-tg-section border border-tg-secondary rounded-3xl" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="p-8 text-center bg-tg-section border border-tg-secondary rounded-3xl text-tg-hint max-w-md mx-auto my-6">
        <p>Profil ma'lumotlarini yuklab bo'lmadi.</p>
        <button
          onClick={loadProfile}
          className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-bold"
        >
          Qayta yuklash
        </button>
      </div>
    );
  }

  const avatarUrl = profile.avatar || tgUser?.photo_url || (profile.telegram_id ? `/api/users/${profile.telegram_id}/avatar` : '');
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
        <span className="inline-flex items-center gap-1 text-[10px] sm:text-[11px] px-2.5 py-0.5 rounded-full font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 shrink-0">
          <Crown className="w-3 h-3 fill-amber-500/30" />
          <span>Super Mentor</span>
        </span>
      );
    }
    if (profile.role === 'admin') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] sm:text-[11px] px-2.5 py-0.5 rounded-full font-bold bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 shrink-0">
          <ShieldCheck className="w-3 h-3" />
          <span>Admin</span>
        </span>
      );
    }
    if (profile.role === 'mentor') {
      return (
        <span className="inline-flex items-center gap-1 text-[10px] sm:text-[11px] px-2.5 py-0.5 rounded-full font-bold bg-blue-500/15 text-blue-600 dark:text-blue-400 shrink-0">
          <GraduationCap className="w-3 h-3" />
          <span>Mentor</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 text-[10px] sm:text-[11px] px-2.5 py-0.5 rounded-full font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 shrink-0">
        <BookOpen className="w-3 h-3" />
        <span>O'quvchi</span>
      </span>
    );
  })();

  const handleRoleQuickChange = async (newRole: any) => {
    triggerHaptic('medium');
    try {
      const updated = await updateUserProfile({ role: newRole });
      setProfile(updated);
      setShowSuccessToast(true);
      setTimeout(() => setShowSuccessToast(false), 2500);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-3.5 pb-28 max-w-2xl mx-auto px-3 sm:px-4 pt-1 animate-in fade-in duration-200">
      {/* Toast Notification */}
      {showSuccessToast && (
        <div className="fixed top-16 left-1/2 -translate-x-1/2 z-50 bg-emerald-600 text-white px-4 py-2 rounded-2xl text-xs font-bold shadow-lg flex items-center gap-2 animate-in fade-in slide-in-from-top-2">
          <Check className="w-4 h-4" />
          <span>Profil ma'lumotlari muvaffaqiyatli saqlandi!</span>
        </div>
      )}

      {/* Main Profile Header Card */}
      <div className="relative overflow-hidden bg-tg-section border border-tg-secondary rounded-2xl sm:rounded-3xl p-4 sm:p-6 shadow-xs">
        {/* Background Decorative Gradient */}
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-52 h-52 bg-gradient-to-br from-blue-500/20 to-indigo-500/0 rounded-full blur-2xl pointer-events-none" />

        <div className="flex items-center gap-3.5 sm:gap-5 relative z-10">
          {/* Avatar Container */}
          <div className="relative shrink-0">
            {avatarUrl && !avatarError ? (
              <img
                src={avatarUrl}
                alt={fullName}
                referrerPolicy="no-referrer"
                onError={() => setAvatarError(true)}
                className="w-14 h-14 sm:w-20 sm:h-20 rounded-2xl sm:rounded-3xl object-cover border-2 border-blue-500 shadow-md"
              />
            ) : (
              <div className="w-14 h-14 sm:w-20 sm:h-20 rounded-2xl sm:rounded-3xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center font-black text-xl sm:text-2xl shadow-md">
                {profile.first_name ? profile.first_name.charAt(0).toUpperCase() : 'U'}
              </div>
            )}
            <div className="absolute -bottom-1 -right-1 bg-blue-600 text-white p-0.5 sm:p-1 rounded-lg sm:rounded-xl shadow-xs">
              <ShieldCheck className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
            </div>
          </div>

          {/* User Details & Action */}
          <div className="flex-1 min-w-0 space-y-1">
            <div className="flex items-center justify-between gap-2">
              <div className="min-w-0">
                <h2 className="text-base sm:text-xl font-black text-tg-text tracking-tight truncate">
                  {fullName}
                </h2>
                <div className="flex items-center gap-1.5 flex-wrap mt-0.5">
                  <span className="text-xs font-semibold text-blue-600 dark:text-blue-400 truncate">
                    {displayUsername}
                  </span>
                  {roleBadge}
                </div>
              </div>

              {!isEditing && (
                <button
                  onClick={() => {
                    triggerHaptic('light');
                    setIsEditing(true);
                  }}
                  className="px-2.5 sm:px-3 py-1.5 rounded-xl bg-tg-secondary hover:bg-blue-500/15 hover:text-blue-500 text-tg-text text-[11px] sm:text-xs font-bold transition-all flex items-center gap-1 cursor-pointer shadow-2xs shrink-0"
                >
                  <Edit3 className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
                  <span className="hidden xs:inline sm:inline">Tahrirlash</span>
                </button>
              )}
            </div>

            <p className="text-[11px] sm:text-xs text-tg-hint flex items-center gap-1 font-medium pt-0.5">
              <Calendar className="w-3 h-3 text-tg-hint/80" />
              <span>A'zo bo'lingan: {profile.joined_date}</span>
            </p>
          </div>
        </div>
      </div>

      {/* Edit Form Modal/Card (if active) */}
      {isEditing && (
        <div className="bg-tg-section border-2 border-blue-500/40 rounded-3xl p-5 shadow-sm space-y-4 animate-in slide-in-from-top-3">
          <div className="flex items-center justify-between border-b border-tg-secondary pb-3">
            <h3 className="font-bold text-sm text-tg-text flex items-center gap-1.5">
              <Edit3 className="w-4 h-4 text-blue-500" />
              <span>Profil ma'lumotlarini o'zgartirish</span>
            </h3>
            <button
              onClick={() => setIsEditing(false)}
              className="p-1 rounded-lg text-tg-hint hover:text-tg-text hover:bg-tg-secondary cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] font-bold text-tg-hint uppercase">Ism</label>
              <input
                type="text"
                value={editForm.first_name}
                onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
                placeholder="Ismingiz"
                className="w-full bg-tg-secondary border border-transparent focus:border-blue-500 text-tg-text text-xs rounded-xl px-3.5 py-2.5 outline-none font-medium"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold text-tg-hint uppercase">Familiya</label>
              <input
                type="text"
                value={editForm.last_name}
                onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
                placeholder="Familiyangiz"
                className="w-full bg-tg-secondary border border-transparent focus:border-blue-500 text-tg-text text-xs rounded-xl px-3.5 py-2.5 outline-none font-medium"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold text-tg-hint uppercase">Telefon raqam</label>
              <input
                type="text"
                value={editForm.phone}
                onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                placeholder="+998 90 123 45 67"
                className="w-full bg-tg-secondary border border-transparent focus:border-blue-500 text-tg-text text-xs rounded-xl px-3.5 py-2.5 outline-none font-medium"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold text-tg-hint uppercase">Telegram Username</label>
              <input
                type="text"
                value={editForm.username}
                onChange={(e) => setEditForm({ ...editForm, username: e.target.value })}
                placeholder="username (masalan: nurulla)"
                className="w-full bg-tg-secondary border border-transparent focus:border-blue-500 text-tg-text text-xs rounded-xl px-3.5 py-2.5 outline-none font-medium"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-tg-secondary">
            <button
              onClick={() => setIsEditing(false)}
              className="px-4 py-2 rounded-xl bg-tg-secondary text-tg-text text-xs font-bold hover:opacity-80 cursor-pointer"
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
      )}

      {/* Metric & Achievement Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        <div className="bg-tg-section border border-tg-secondary rounded-2xl p-3.5 space-y-1 shadow-2xs">
          <div className="flex items-center gap-1.5 text-xs text-tg-hint">
            <BookOpen className="w-3.5 h-3.5 text-blue-500" />
            <span>Kurslar</span>
          </div>
          <p className="text-lg sm:text-xl font-black text-tg-text">
            {profile.enrolled_courses_count || 0} ta
          </p>
        </div>

        <div className="bg-tg-section border border-tg-secondary rounded-2xl p-3.5 space-y-1 shadow-2xs">
          <div className="flex items-center gap-1.5 text-xs text-tg-hint">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            <span>Tugallangan</span>
          </div>
          <p className="text-lg sm:text-xl font-black text-tg-text">
            {profile.completed_lessons_count || 0} dars
          </p>
        </div>

        <div className="bg-tg-section border border-tg-secondary rounded-2xl p-3.5 space-y-1 shadow-2xs">
          <div className="flex items-center gap-1.5 text-xs text-tg-hint">
            <Flame className="w-3.5 h-3.5 text-orange-500 fill-orange-500" />
            <span>Ketma-ketlik</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-lg sm:text-xl font-black text-tg-text">
              {profile.streak_days || 1} kun
            </span>
            <span className="inline-flex items-center justify-center w-5 h-5 rounded-lg bg-orange-500/15 text-orange-500">
              <Flame className="w-3.5 h-3.5 fill-orange-500" />
            </span>
          </div>
        </div>

        <div className="bg-tg-section border border-tg-secondary rounded-2xl p-3.5 space-y-1 shadow-2xs">
          <div className="flex items-center gap-1.5 text-xs text-tg-hint">
            <Clock className="w-3.5 h-3.5 text-indigo-500" />
            <span>O'qish vaqti</span>
          </div>
          <p className="text-lg sm:text-xl font-black text-tg-text">
            {Math.floor((profile.total_study_time_minutes || 0) / 60)}s {(profile.total_study_time_minutes || 0) % 60}m
          </p>
        </div>
      </div>

      {/* Account Info Details List */}
      <div className="bg-tg-section border border-tg-secondary rounded-3xl p-4 sm:p-5 space-y-3.5 shadow-xs">
        <h3 className="font-bold text-xs uppercase tracking-wider text-tg-hint px-1 flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5 text-blue-500" />
          <span>Shaxsiy Ma'lumotlar</span>
        </h3>

        <div className="space-y-2 text-xs sm:text-sm">
          {/* Telegram ID */}
          <div className="flex items-center justify-between p-3 rounded-2xl bg-tg-secondary/60 hover:bg-tg-secondary transition-colors">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-xl bg-blue-500/10 text-blue-600 flex items-center justify-center">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <p className="text-[11px] text-tg-hint font-medium">Telegram ID</p>
                <p className="font-mono font-bold text-tg-text">{profile.telegram_id}</p>
              </div>
            </div>
            <button
              onClick={() => handleCopy('tg_id', String(profile.telegram_id))}
              className="p-1.5 rounded-xl bg-tg-secondary text-tg-hint hover:text-tg-text transition-colors cursor-pointer"
              title="Nusxalash"
            >
              {copiedKey === 'tg_id' ? (
                <Check className="w-3.5 h-3.5 text-emerald-500" />
              ) : (
                <Copy className="w-3.5 h-3.5" />
              )}
            </button>
          </div>

          {/* Phone */}
          <div className="flex items-center justify-between p-3 rounded-2xl bg-tg-secondary/60 hover:bg-tg-secondary transition-colors">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-xl bg-emerald-500/10 text-emerald-600 flex items-center justify-center">
                <Phone className="w-4 h-4" />
              </div>
              <div>
                <p className="text-[11px] text-tg-hint font-medium">Telefon raqami</p>
                <p className="font-bold text-tg-text">{profile.phone || 'Biriktirilmagan'}</p>
              </div>
            </div>
          </div>

          {/* Balance / Wallet */}
          <div className="flex items-center justify-between p-3 rounded-2xl bg-tg-secondary/60 hover:bg-tg-secondary transition-colors">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-xl bg-amber-500/10 text-amber-600 flex items-center justify-center">
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
                onNavigate({ type: 'catalog' });
              }}
              className="px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs transition-all cursor-pointer shadow-2xs"
            >
              Kurs olish
            </button>
          </div>

          {/* Certificates */}
          <div className="p-3.5 rounded-2xl bg-tg-secondary/60 border border-purple-500/20 hover:bg-tg-secondary transition-all space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-xl bg-purple-500/15 text-purple-600 dark:text-purple-400 flex items-center justify-center">
                  <Award className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <p className="text-[11px] text-tg-hint font-bold uppercase tracking-wider">Sertifikatlar</p>
                    <span className="px-1.5 py-0.5 rounded-md text-[9px] font-extrabold bg-purple-500/15 text-purple-600 dark:text-purple-300">
                      Tez kunda
                    </span>
                  </div>
                  <p className="font-bold text-xs text-tg-text">
                    Hali joriy etilmagan
                  </p>
                </div>
              </div>
            </div>
            <p className="text-[11px] text-tg-hint pl-9.5 leading-relaxed">
              💡 Kurslarni tamomlash bo'yicha rasmiy sertifikatlar moduli tez kunda ishga tushiriladi. Joriy etilishi bilan sizga Telegram bot orqali xabar beramiz!
            </p>
          </div>
        </div>
      </div>

      {/* Quick Navigation Action Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        <button
          onClick={() => {
            triggerHaptic('light');
            onNavigate({ type: 'my-courses' });
          }}
          className="p-3.5 rounded-2xl bg-tg-section border border-tg-secondary hover:border-blue-500/40 text-left transition-all flex items-center justify-between group cursor-pointer shadow-2xs"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-xl bg-blue-500/15 text-blue-600 flex items-center justify-center shrink-0">
              <BookOpen className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <p className="font-bold text-xs text-tg-text truncate">Mening kurslarim</p>
              <p className="text-[10px] text-tg-hint truncate">Darslarni davom ettirish</p>
            </div>
          </div>
          <ChevronRight className="w-3.5 h-3.5 text-tg-hint group-hover:translate-x-0.5 transition-transform shrink-0" />
        </button>

        <button
          onClick={() => {
            triggerHaptic('light');
            onNavigate({ type: 'cabinet' });
          }}
          className="p-3.5 rounded-2xl bg-tg-section border border-tg-secondary hover:border-blue-500/40 text-left transition-all flex items-center justify-between group cursor-pointer shadow-2xs"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-xl bg-indigo-500/15 text-indigo-600 flex items-center justify-center shrink-0">
              <GraduationCap className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <p className="font-bold text-xs text-tg-text truncate">Kabinet & Guruhlar</p>
              <p className="text-[10px] text-tg-hint truncate">Mentor va guruh chati</p>
            </div>
          </div>
          <ChevronRight className="w-3.5 h-3.5 text-tg-hint group-hover:translate-x-0.5 transition-transform shrink-0" />
        </button>

        <button
          onClick={() => {
            triggerHaptic('light');
            onNavigate({ type: 'mentor-stats' });
          }}
          className="p-3.5 rounded-2xl bg-tg-section border border-tg-secondary hover:border-amber-500/40 text-left transition-all flex items-center justify-between group cursor-pointer shadow-2xs"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-xl bg-amber-500/15 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <p className="font-bold text-xs text-tg-text truncate">Talabalar Nazorati</p>
              <p className="text-[10px] text-tg-hint truncate">Mentor / Super Admin</p>
            </div>
          </div>
          <ChevronRight className="w-3.5 h-3.5 text-tg-hint group-hover:translate-x-0.5 transition-transform shrink-0" />
        </button>
      </div>
    </div>
  );
};
