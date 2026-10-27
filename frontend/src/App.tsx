import React, { useState, useEffect } from 'react';
import { AppView, Course, TelegramUser } from './types';
import {
  initTelegramApp,
  getTelegramUser,
  getTelegramStartParam,
  parseRouteFromUrl,
  triggerHaptic,
} from './services/telegram';
import { Navbar } from './components/Navbar';
import { BottomTabBar } from './components/BottomTabBar';
import { CatalogView } from './components/CatalogView';
import { CourseDetailView } from './components/CourseDetailView';
import { VideoPlayerView } from './components/VideoPlayerView';
import { MyCoursesView } from './components/MyCoursesView';
import { CabinetChatView } from './components/CabinetChatView';
import { LiveSessionsView } from './components/LiveSessionsView';
import { LiveStreamView } from './components/LiveStreamView';
import { MentorStatsView } from './components/MentorStatsView';
import { ProfileView } from './components/ProfileView';
import { AdminDashboardView } from './components/AdminDashboardView';
import { ApiSettingsModal } from './components/ApiSettingsModal';
import { NotificationsModal } from './components/NotificationsModal';
import { FeedbackModal } from './components/FeedbackModal';
import { fetchNotifications } from './services/api';
import { ContentProtection } from './components/ContentProtection';

export default function App() {
  const [currentView, setCurrentView] = useState<AppView>(() => parseRouteFromUrl());
  const [user, setUser] = useState<TelegramUser | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [unreadNotifCount, setUnreadNotifCount] = useState<number>(0);
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);

  // Initialize Telegram WebApp on mount & handle deep link
  useEffect(() => {
    initTelegramApp();
    const tgUser = getTelegramUser();
    setUser(tgUser);

    const initialView = parseRouteFromUrl();
    setCurrentView(initialView);

    // Initial unread notifications check
    fetchNotifications()
      .then((res) => {
        if (res && typeof res.unread_count === 'number') {
          setUnreadNotifCount(res.unread_count);
        }
      })
      .catch((e) => console.warn('Notif count fetch error:', e));

    const handleRouteSync = () => {
      const parsed = parseRouteFromUrl();
      setCurrentView(parsed);
    };

    window.addEventListener('hashchange', handleRouteSync);
    window.addEventListener('popstate', handleRouteSync);

    return () => {
      window.removeEventListener('hashchange', handleRouteSync);
      window.removeEventListener('popstate', handleRouteSync);
    };
  }, []);

  // Sync Telegram WebApp native BackButton
  useEffect(() => {
    if (typeof window === 'undefined' || !window.Telegram?.WebApp?.BackButton) return;

    const backButton = window.Telegram.WebApp.BackButton;
    const isRoot =
      currentView.type === 'catalog' ||
      currentView.type === 'my-courses' ||
      currentView.type === 'profile' ||
      (currentView.type === 'cabinet' && !currentView.cabinetId);

    const handleBackClick = () => {
      triggerHaptic('light');
      if (currentView.type === 'admin-dashboard') {
        setCurrentView({ type: 'profile' });
      } else if (currentView.type === 'lesson') {
        setCurrentView({ type: 'course', courseId: currentView.courseId });
      } else if (currentView.type === 'live' || currentView.type === 'live-stream') {
        setCurrentView({ type: 'course', courseId: currentView.courseId });
      } else if (currentView.type === 'mentor-stats') {
        setCurrentView({ type: 'cabinet', cabinetId: currentView.cabinetId });
      } else if (currentView.type === 'course') {
        setCurrentView({ type: 'catalog' });
      } else {
        setCurrentView({ type: 'catalog' });
      }
    };

    if (!isRoot) {
      backButton.show();
      backButton.onClick(handleBackClick);
    } else {
      backButton.hide();
    }

    return () => {
      backButton.offClick(handleBackClick);
    };
  }, [currentView]);

  const handleNavigate = (view: AppView) => {
    setCurrentView(view);
    if (typeof window !== 'undefined') {
      if (view.type === 'admin-dashboard') {
        window.location.hash = 'admin';
      } else if (view.type === 'profile') {
        window.location.hash = 'profile';
      } else if (view.type === 'cabinet') {
        window.location.hash = view.cabinetId ? `cabinet-${view.cabinetId}` : 'cabinet';
      } else if (view.type === 'my-courses') {
        window.location.hash = 'my-courses';
      } else if (view.type === 'catalog') {
        window.location.hash = 'catalog';
      } else if (view.type === 'course') {
        window.location.hash = `course-${view.courseId}`;
      } else if (view.type === 'live') {
        window.location.hash = `live-${view.courseId}`;
      } else if (view.type === 'mentor-stats') {
        window.location.hash = 'stats';
      }
    }
  };

  const handleSelectCourse = (course: Course) => {
    setSelectedCourse(course);
  };

  const handleSelectLesson = (courseId: string | number, lessonId: string | number) => {
    try {
      localStorage.setItem(
        'bilimgo_last_lesson',
        JSON.stringify({ courseId, lessonId, timestamp: Date.now() })
      );
    } catch {
      // safe ignore
    }
    setCurrentView({
      type: 'lesson',
      courseId,
      lessonId,
    });
  };

  return (
    <ContentProtection user={user}>
      <div className="min-h-screen bg-tg-bg text-tg-text flex flex-col font-sans transition-colors selection:bg-blue-500 selection:text-white">
        {/* Top Navbar */}
        <Navbar
          currentView={currentView}
          onNavigate={handleNavigate}
          user={user}
          onOpenSettings={() => setSettingsOpen(true)}
          onOpenNotifications={() => setNotificationsOpen(true)}
          onOpenFeedback={() => setFeedbackOpen(true)}
          hasUnreadNotifications={unreadNotifCount > 0}
        />

        {/* Main View Router */}
        <main className="flex-1 w-full max-w-4xl mx-auto pt-3">
          {currentView.type === 'catalog' && (
            <CatalogView
              onNavigate={handleNavigate}
              onSelectCourse={handleSelectCourse}
            />
          )}

          {currentView.type === 'course' && (
            <CourseDetailView
              courseId={currentView.courseId}
              onNavigate={handleNavigate}
              onSelectLesson={handleSelectLesson}
            />
          )}

          {currentView.type === 'lesson' && (
            <VideoPlayerView
              courseId={currentView.courseId}
              lessonId={currentView.lessonId}
              onNavigate={handleNavigate}
              onSelectLesson={handleSelectLesson}
            />
          )}

          {currentView.type === 'my-courses' && (
            <MyCoursesView
              onNavigate={handleNavigate}
              onSelectCourse={handleSelectCourse}
              onSelectLesson={handleSelectLesson}
            />
          )}

          {currentView.type === 'cabinet' && (
            <CabinetChatView
              initialCabinetId={currentView.cabinetId}
              onNavigate={handleNavigate}
            />
          )}

          {currentView.type === 'live' && (
            <LiveSessionsView
              courseId={currentView.courseId}
              onNavigate={handleNavigate}
            />
          )}

          {currentView.type === 'live-stream' && (
            <LiveStreamView
              sessionId={currentView.sessionId}
              courseId={currentView.courseId}
              onNavigate={handleNavigate}
              onLeave={() => setCurrentView({ type: 'live', courseId: currentView.courseId })}
            />
          )}

          {currentView.type === 'mentor-stats' && (
            <MentorStatsView
              cabinetId={currentView.cabinetId}
              mentorId={currentView.mentorId}
              onNavigate={handleNavigate}
            />
          )}

          {currentView.type === 'admin-dashboard' && (
            <AdminDashboardView onNavigate={handleNavigate} />
          )}

          {currentView.type === 'profile' && (
            <ProfileView onNavigate={handleNavigate} />
          )}
        </main>

        {/* Bottom Tab Bar (shown on primary pages) */}
        <BottomTabBar
          currentView={currentView}
          onNavigate={handleNavigate}
          unreadCount={0}
        />

        {/* Notifications Modal */}
        <NotificationsModal
          isOpen={notificationsOpen}
          onClose={() => setNotificationsOpen(false)}
          onUnreadCountChange={(cnt) => setUnreadNotifCount(cnt)}
        />

        {/* Feedback Modal */}
        <FeedbackModal
          isOpen={feedbackOpen}
          onClose={() => setFeedbackOpen(false)}
        />

        {/* Settings Modal (Theme, API, Cache) */}
        <ApiSettingsModal
          isOpen={settingsOpen}
          onClose={() => setSettingsOpen(false)}
          onRefresh={() => {
            setCurrentView({ ...currentView });
          }}
        />
      </div>
    </ContentProtection>
  );
}
