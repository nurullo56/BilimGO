import React from 'react';
import { BookOpen, Compass, MessageSquare, User } from 'lucide-react';
import { AppView } from '../types';
import { triggerHaptic, getTelegramUser } from '../services/telegram';

interface BottomTabBarProps {
  currentView: AppView;
  onNavigate: (view: AppView) => void;
  unreadCount?: number;
}

export const BottomTabBar: React.FC<BottomTabBarProps> = ({
  currentView,
  onNavigate,
  unreadCount = 0,
}) => {
  if (currentView.type === 'live-stream' || currentView.type === 'lesson') {
    return null;
  }

  const currentTab = (() => {
    if (
      currentView.type === 'catalog' ||
      currentView.type === 'course' ||
      currentView.type === 'lesson' ||
      currentView.type === 'live'
    ) {
      return 'catalog';
    }
    if (currentView.type === 'my-courses') return 'my-courses';
    if (currentView.type === 'cabinet' || currentView.type === 'mentor-stats') return 'cabinet';
    if (currentView.type === 'profile') return 'profile';
    return 'catalog';
  })();

  const tgUser = getTelegramUser();

  const tabs = [
    {
      id: 'catalog',
      label: 'Katalog',
      icon: Compass,
      view: { type: 'catalog' } as AppView,
    },
    {
      id: 'my-courses',
      label: 'Kurslarim',
      icon: BookOpen,
      view: { type: 'my-courses' } as AppView,
    },
    {
      id: 'cabinet',
      label: 'Kabinet',
      icon: MessageSquare,
      view: { type: 'cabinet' } as AppView,
      badge: unreadCount > 0 ? unreadCount : undefined,
    },
    {
      id: 'profile',
      label: 'Profil',
      icon: User,
      view: { type: 'profile' } as AppView,
      avatarUrl: (tgUser as any)?.photo_url,
    },
  ];

  return (
    <div className="fixed bottom-4 left-0 right-0 z-40 pointer-events-none flex justify-center px-4 pb-[env(safe-area-inset-bottom,0px)]">
      <nav
        className="pointer-events-auto bg-white/95 dark:bg-[#17212b]/95 backdrop-blur-2xl border border-slate-200/90 dark:border-white/10 shadow-[0_12px_32px_-4px_rgba(0,0,0,0.08),0_4px_12px_-2px_rgba(0,0,0,0.04)] dark:shadow-[0_16px_36px_-6px_rgba(0,0,0,0.6)] rounded-full p-1.5 flex items-center justify-between gap-1 max-w-[360px] w-full transition-all duration-300"
      >
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = currentTab === tab.id;

          return (
            <button
              key={tab.id}
              id={`tab-btn-${tab.id}`}
              onClick={() => {
                triggerHaptic('selection');
                onNavigate(tab.view);
              }}
              className={`relative flex-1 flex flex-col items-center justify-center py-1.5 px-3 rounded-full transition-all duration-200 cursor-pointer select-none active:scale-95 ${
                isActive
                  ? 'bg-[#2481cc]/12 dark:bg-[#233447] text-[#2481cc] dark:text-[#3390ec]'
                  : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100/70 dark:text-slate-400 dark:hover:text-white dark:hover:bg-white/5'
              }`}
            >
              <div className="relative flex items-center justify-center">
                {tab.id === 'profile' && tab.avatarUrl ? (
                  <img
                    src={tab.avatarUrl}
                    alt="Avatar"
                    className={`w-5 h-5 rounded-full object-cover transition-transform ${
                      isActive
                        ? 'ring-2 ring-[#2481cc] dark:ring-[#3390ec] scale-105'
                        : 'opacity-85'
                    }`}
                    onError={(e) => {
                      (e.target as HTMLElement).style.display = 'none';
                    }}
                  />
                ) : (
                  <Icon
                    className={`w-5 h-5 transition-transform duration-200 ${
                      isActive
                        ? 'stroke-[#2481cc] dark:stroke-[#3390ec] scale-105'
                        : 'stroke-slate-500 dark:stroke-slate-400'
                    }`}
                    strokeWidth={isActive ? 2.3 : 1.9}
                  />
                )}

                {tab.badge && (
                  <span className="absolute -top-1 -right-2 min-w-4 h-4 px-1 rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center shadow-xs">
                    {tab.badge}
                  </span>
                )}
              </div>

              <span
                className={`text-[11px] mt-0.5 tracking-tight ${
                  isActive
                    ? 'text-[#2481cc] dark:text-[#3390ec] font-bold'
                    : 'text-slate-500 dark:text-slate-400 font-medium'
                }`}
              >
                {tab.label}
              </span>
            </button>
          );
        })}
      </nav>
    </div>
  );
};
