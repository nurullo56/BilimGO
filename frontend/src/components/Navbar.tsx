import React from 'react';
import { ArrowLeft, Settings, Sparkles, User } from 'lucide-react';
import { AppView, TelegramUser } from '../types';
import { triggerHaptic } from '../services/telegram';

interface NavbarProps {
  currentView: AppView;
  onNavigate: (view: AppView) => void;
  user: TelegramUser | null;
  onOpenSettings: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentView,
  onNavigate,
  user,
  onOpenSettings,
}) => {
  const isHome = currentView.type === 'catalog' || currentView.type === 'my-courses' || currentView.type === 'profile' || (currentView.type === 'cabinet' && !currentView.cabinetId);
  const showBack = !isHome;

  const handleBack = () => {
    triggerHaptic('light');
    if (currentView.type === 'lesson') {
      onNavigate({ type: 'course', courseId: currentView.courseId });
    } else if (currentView.type === 'live') {
      onNavigate({ type: 'course', courseId: currentView.courseId });
    } else if (currentView.type === 'mentor-stats') {
      onNavigate({ type: 'cabinet', cabinetId: currentView.cabinetId });
    } else if (currentView.type === 'course') {
      onNavigate({ type: 'catalog' });
    } else {
      onNavigate({ type: 'catalog' });
    }
  };

  const getTitle = () => {
    switch (currentView.type) {
      case 'catalog':
        return 'BilimGo';
      case 'my-courses':
        return 'Mening kurslarim';
      case 'cabinet':
        return 'Kabinet & Muloqot';
      case 'profile':
        return 'Mening Profilim';
      case 'course':
        return 'Kurs tafsilotlari';
      case 'lesson':
        return 'Video Dars';
      case 'live':
        return 'Jonli Darslar';
      case 'mentor-stats':
        return 'Mentor Statistikasi';
      default:
        return 'BilimGo';
    }
  };

  const [navAvatarError, setNavAvatarError] = React.useState(false);
  const navAvatarUrl = (!navAvatarError && (user?.photo_url || (user?.id ? `/api/users/${user.id}/avatar` : ''))) || '';

  const getSubtitle = () => {
    switch (currentView.type) {
      case 'catalog':
        return 'Adaptiv o\'quv platformasi';
      case 'my-courses':
        return 'Shaxsiy o\'zlashtirish jarayoni';
      case 'cabinet':
        return 'Mentor va guruh bilan chat';
      case 'profile':
        return 'Shaxsiy profil va yutuqlar';
      case 'course':
        return 'Darslar va materiallar';
      case 'lesson':
        return 'Video Dars';
      case 'live':
        return 'Jonli vebinarlar & savol-javob';
      case 'mentor-stats':
        return 'Talabalar faolligi & ko\'rsatkichlar';
      default:
        return '';
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full bg-tg-bg/95 backdrop-blur border-b border-tg-secondary px-4 py-3 transition-colors">
      <div className="max-w-3xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          {showBack ? (
            <button
              id="btn-nav-back"
              onClick={handleBack}
              className="p-1.5 rounded-xl bg-tg-secondary hover:bg-blue-500/15 hover:text-blue-500 text-tg-text transition-all active:scale-90 cursor-pointer shadow-2xs"
              title="Orqaga"
            >
              <ArrowLeft className="w-4 h-4 sm:w-5 sm:h-5" />
            </button>
          ) : (
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20 shrink-0">
              <Sparkles className="w-4 h-4" />
            </div>
          )}

          <div className="min-w-0">
            <h1 className="text-sm sm:text-base font-extrabold text-tg-text tracking-tight truncate">
              {getTitle()}
            </h1>
            {getSubtitle() && (
              <p className="text-[10px] sm:text-xs text-tg-hint truncate leading-none mt-0.5">
                {getSubtitle()}
              </p>
            )}
          </div>
        </div>

        {/* Right Section: User Pill & Dev API Button */}
        <div className="flex items-center gap-2">
          {/* User profile quick toggle button */}
          <button
            id="btn-navbar-profile"
            onClick={() => {
              triggerHaptic('light');
              onNavigate({ type: 'profile' });
            }}
            className={`flex items-center gap-1.5 pl-2 pr-2.5 py-1 rounded-full border text-xs cursor-pointer active:scale-95 transition-all ${
              currentView.type === 'profile'
                ? 'bg-blue-600/15 border-blue-500 text-blue-600 dark:text-blue-400'
                : 'bg-tg-secondary border-tg-secondary text-tg-text hover:border-blue-500/40'
            }`}
            title="Profilga o'tish"
          >
            <div className="w-5 h-5 rounded-full bg-blue-600/20 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-[10px] overflow-hidden">
              {navAvatarUrl ? (
                <img
                  src={navAvatarUrl}
                  alt={user?.first_name || 'Profil'}
                  referrerPolicy="no-referrer"
                  onError={() => setNavAvatarError(true)}
                  className="w-full h-full rounded-full object-cover"
                />
              ) : (
                user?.first_name?.charAt(0) || <User className="w-3 h-3" />
              )}
            </div>
            <span className="font-semibold max-w-[80px] sm:max-w-[120px] truncate text-xs">
              {user?.first_name || 'Profil'}
            </span>
          </button>

          {/* API settings button (Faqat DEV rejimida) */}
          {import.meta.env.DEV && (
            <button
              id="btn-open-settings"
              onClick={() => {
                triggerHaptic('light');
                onOpenSettings();
              }}
              className="p-2 rounded-xl bg-tg-secondary text-tg-hint hover:text-tg-text active:scale-95 transition-all cursor-pointer"
              title="API Sozlamalari"
            >
              <Settings className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
