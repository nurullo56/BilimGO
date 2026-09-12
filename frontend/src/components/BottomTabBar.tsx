import React from 'react';
import { BookOpen, Compass, MessageSquare, User } from 'lucide-react';
import { AppView } from '../types';
import { triggerHaptic } from '../services/telegram';

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
    if (currentView.type === 'catalog' || currentView.type === 'course' || currentView.type === 'lesson' || currentView.type === 'live') {
      return 'catalog';
    }
    if (currentView.type === 'my-courses') return 'my-courses';
    if (currentView.type === 'cabinet' || currentView.type === 'mentor-stats') return 'cabinet';
    if (currentView.type === 'profile') return 'profile';
    return 'catalog';
  })();

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
    },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-tg-bg/95 backdrop-blur-md border-t border-tg-secondary pb-[calc(env(safe-area-inset-bottom,12px)+6px)] pt-2 px-3 transition-colors">
      <div className="max-w-md mx-auto grid grid-cols-4 gap-1">
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
              className={`relative flex flex-col items-center justify-center py-1.5 px-1 rounded-2xl transition-all cursor-pointer select-none ${
                isActive
                  ? 'text-blue-600 dark:text-blue-400 font-bold'
                  : 'text-tg-hint hover:text-tg-text font-medium'
              }`}
            >
              <div className="relative">
                <Icon className={`w-5 h-5 transition-transform ${isActive ? 'scale-110' : ''}`} />
                {tab.badge && (
                  <span className="absolute -top-1.5 -right-2.5 min-w-4 h-4 px-1 rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center">
                    {tab.badge}
                  </span>
                )}
              </div>
              <span className="text-[11px] mt-1 tracking-tight truncate max-w-full">
                {tab.label}
              </span>
              {isActive && (
                <div className="w-1.5 h-1.5 rounded-full bg-blue-600 dark:bg-blue-400 mt-0.5" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};
