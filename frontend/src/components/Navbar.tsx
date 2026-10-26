import React from 'react';
import { ArrowLeft, Bell, Settings } from 'lucide-react';
import { AppView, TelegramUser } from '../types';
import { triggerHaptic } from '../services/telegram';

interface NavbarProps {
  currentView: AppView;
  onNavigate: (view: AppView) => void;
  user: TelegramUser | null;
  onOpenSettings: () => void;
  onOpenNotifications?: () => void;
  hasUnreadNotifications?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentView,
  onNavigate,
  user: _user,
  onOpenSettings,
  onOpenNotifications,
  hasUnreadNotifications = true,
}) => {
  const isHome =
    currentView.type === 'catalog' ||
    currentView.type === 'my-courses' ||
    currentView.type === 'profile' ||
    (currentView.type === 'cabinet' && !currentView.cabinetId);
  const showBack = !isHome;

  const handleBack = () => {
    triggerHaptic('light');
    if (currentView.type === 'lesson') {
      onNavigate({ type: 'course', courseId: currentView.courseId });
    } else if (currentView.type === 'live' || currentView.type === 'live-stream') {
      onNavigate({ type: 'course', courseId: currentView.courseId });
    } else if (currentView.type === 'mentor-stats') {
      onNavigate({ type: 'cabinet', cabinetId: currentView.cabinetId });
    } else if (currentView.type === 'course') {
      onNavigate({ type: 'catalog' });
    } else {
      onNavigate({ type: 'catalog' });
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full bg-transparent transition-all duration-200 px-4 pt-3 pb-2 sm:px-6">
      <div className="max-w-4xl mx-auto flex items-center justify-between">
        {/* Left Section: Back Button (if deep view) + Bilim GO Logo (compact & elegant) */}
        <div className="flex items-center gap-2">
          {showBack && (
            <button
              id="btn-nav-back"
              onClick={handleBack}
              className="w-9 h-9 rounded-full flex items-center justify-center bg-slate-100/80 hover:bg-slate-200/90 dark:bg-white/10 dark:hover:bg-white/15 text-slate-700 dark:text-white transition-all active:scale-90 cursor-pointer shrink-0"
              title="Orqaga"
            >
              <ArrowLeft className="w-4.5 h-4.5 stroke-[2.2]" />
            </button>
          )}

          <button
            onClick={() => {
              triggerHaptic('light');
              onNavigate({ type: 'catalog' });
            }}
            className="flex items-center gap-1 cursor-pointer select-none text-left focus:outline-none active:opacity-85 transition-opacity"
            title="Bilim GO"
          >
            <span className="text-xl sm:text-[22px] font-black tracking-tight leading-none text-slate-900 dark:text-white transition-colors">
              Bilim <span className="text-[#2481cc] dark:text-[#3390ec]">GO</span>
            </span>
          </button>
        </div>

        {/* Right Section: Notification Bell + Settings Gear (compact, sleek circular buttons) */}
        <div className="flex items-center gap-2">
          {/* Notification Button with Blue Indicator Dot */}
          <button
            id="btn-nav-notifications"
            onClick={() => {
              triggerHaptic('light');
              if (onOpenNotifications) {
                onOpenNotifications();
              }
            }}
            className="w-9 h-9 rounded-full flex items-center justify-center relative bg-slate-100/80 hover:bg-slate-200/90 dark:bg-white/10 dark:hover:bg-white/15 text-slate-700 dark:text-white transition-all duration-200 active:scale-95 cursor-pointer"
            title="Bildirishnomalar"
          >
            <Bell className="w-4.5 h-4.5 stroke-[2]" />
            {hasUnreadNotifications && (
              <span
                className="absolute top-0.5 right-0.5 w-2.5 h-2.5 rounded-full bg-[#2481cc] dark:bg-[#3390ec] ring-2 ring-white dark:ring-[#17212b]"
                aria-hidden="true"
              />
            )}
          </button>

          {/* Settings Button */}
          <button
            id="btn-nav-settings"
            onClick={() => {
              triggerHaptic('light');
              onOpenSettings();
            }}
            className="w-9 h-9 rounded-full flex items-center justify-center bg-slate-100/80 hover:bg-slate-200/90 dark:bg-white/10 dark:hover:bg-white/15 text-slate-700 dark:text-white transition-all duration-200 active:scale-95 cursor-pointer"
            title="Sozlamalar"
          >
            <Settings className="w-4.5 h-4.5 stroke-[2]" />
          </button>
        </div>
      </div>
    </header>
  );
};
