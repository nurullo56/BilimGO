import React, { useState, useEffect } from 'react';
import {
  Bell,
  CheckCheck,
  X,
  Sparkles,
  GraduationCap,
  PlayCircle,
  Award,
  Info,
  Clock,
  ChevronRight,
  RefreshCw,
} from 'lucide-react';
import { triggerHaptic } from '../services/telegram';
import {
  fetchNotifications,
  markNotificationAsRead,
  markAllNotificationsAsRead,
  AppNotification,
} from '../services/api';

interface NotificationsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUnreadCountChange?: (count: number) => void;
}

export const NotificationsModal: React.FC<NotificationsModalProps> = ({
  isOpen,
  onClose,
  onUnreadCountChange,
}) => {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'all' | 'unread'>('all');
  const [markingAll, setMarkingAll] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadNotifications();
    }
  }, [isOpen]);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const res = await fetchNotifications();
      setNotifications(res.notifications || []);
      setUnreadCount(res.unread_count || 0);
      if (onUnreadCountChange) {
        onUnreadCountChange(res.unread_count || 0);
      }
    } catch (err) {
      console.warn("Bildirishnomalarni yuklashda xatolik:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (item: AppNotification) => {
    if (item.is_read) return;
    triggerHaptic('light');

    // Optimistic update
    setNotifications((prev) =>
      prev.map((n) => (n.id === item.id ? { ...n, is_read: true } : n))
    );
    const newCount = Math.max(0, unreadCount - 1);
    setUnreadCount(newCount);
    if (onUnreadCountChange) {
      onUnreadCountChange(newCount);
    }

    try {
      const res = await markNotificationAsRead(item.id);
      if (res && typeof res.unread_count === 'number') {
        setUnreadCount(res.unread_count);
        if (onUnreadCountChange) {
          onUnreadCountChange(res.unread_count);
        }
      }
    } catch (err) {
      console.warn("Xabarni o'qildi deb belgilashda xato:", err);
    }
  };

  const handleMarkAllAsRead = async () => {
    if (unreadCount === 0 || markingAll) return;
    triggerHaptic('medium');
    setMarkingAll(true);

    // Optimistic update
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnreadCount(0);
    if (onUnreadCountChange) {
      onUnreadCountChange(0);
    }

    try {
      await markAllNotificationsAsRead();
      triggerHaptic('success');
    } catch (err) {
      console.warn("Barchasini o'qilgan qilishda xato:", err);
    } finally {
      setMarkingAll(false);
    }
  };

  const formatTime = (dateStr: string) => {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return dateStr;

      const now = new Date();
      const diffSec = Math.floor((now.getTime() - d.getTime()) / 1000);

      if (diffSec < 60) return 'Hozirgina';
      if (diffSec < 3600) return `${Math.floor(diffSec / 60)} daqiqa oldin`;
      if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} soat oldin`;
      if (diffSec < 172800) return 'Kecha';

      return `${d.getDate()}.${String(d.getMonth() + 1).padStart(2, '0')}.${d.getFullYear()}`;
    } catch {
      return dateStr;
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'ai_evaluation':
        return (
          <div className="w-10 h-10 rounded-2xl bg-purple-500/15 text-purple-600 dark:text-purple-400 flex items-center justify-center shrink-0">
            <Sparkles className="w-5 h-5 stroke-[2]" />
          </div>
        );
      case 'mentor':
        return (
          <div className="w-10 h-10 rounded-2xl bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
            <GraduationCap className="w-5 h-5 stroke-[2]" />
          </div>
        );
      case 'lesson':
        return (
          <div className="w-10 h-10 rounded-2xl bg-blue-500/15 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
            <PlayCircle className="w-5 h-5 stroke-[2]" />
          </div>
        );
      case 'course':
        return (
          <div className="w-10 h-10 rounded-2xl bg-amber-500/15 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0">
            <Award className="w-5 h-5 stroke-[2]" />
          </div>
        );
      default:
        return (
          <div className="w-10 h-10 rounded-2xl bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0">
            <Bell className="w-5 h-5 stroke-[2]" />
          </div>
        );
    }
  };

  if (!isOpen) return null;

  const filteredNotifications =
    activeTab === 'unread' ? notifications.filter((n) => !n.is_read) : notifications;

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-lg bg-tg-bg border-t sm:border border-tg-secondary rounded-t-3xl sm:rounded-3xl p-5 sm:p-6 shadow-2xl space-y-4 max-h-[88vh] flex flex-col animate-in slide-in-from-bottom duration-200"
      >
        {/* Mobile Drag Handle Indicator */}
        <div className="w-12 h-1 bg-tg-hint/30 rounded-full mx-auto -mt-1 mb-1 sm:hidden shrink-0" />

        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-tg-secondary shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-2xl bg-blue-500/15 text-blue-600 dark:text-blue-400 flex items-center justify-center relative">
              <Bell className="w-5 h-5 stroke-[2.2]" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center ring-2 ring-tg-bg">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </div>
            <div>
              <h3 className="font-bold text-base text-tg-text">Bildirishnomalar</h3>
              <p className="text-[11px] text-tg-hint">Yangiliklar, baholar va eslatmalar</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={handleMarkAllAsRead}
                disabled={markingAll}
                className="px-2.5 py-1.5 rounded-xl bg-blue-500/10 hover:bg-blue-500/20 text-blue-600 dark:text-blue-400 text-xs font-semibold flex items-center gap-1 transition cursor-pointer"
                title="Barchasini o'qilgan qilish"
              >
                <CheckCheck className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Barchasini o'qish</span>
              </button>
            )}

            <button
              type="button"
              onClick={() => {
                triggerHaptic('light');
                onClose();
              }}
              className="p-1.5 rounded-xl text-tg-hint hover:text-tg-text hover:bg-tg-secondary cursor-pointer transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => {
              triggerHaptic('selection');
              setActiveTab('all');
            }}
            className={`flex-1 py-1.5 rounded-xl text-xs font-bold transition-colors cursor-pointer ${
              activeTab === 'all'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'bg-tg-secondary/60 text-tg-hint hover:text-tg-text'
            }`}
          >
            Barchasi ({notifications.length})
          </button>
          <button
            type="button"
            onClick={() => {
              triggerHaptic('selection');
              setActiveTab('unread');
            }}
            className={`flex-1 py-1.5 rounded-xl text-xs font-bold transition-colors cursor-pointer ${
              activeTab === 'unread'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'bg-tg-secondary/60 text-tg-hint hover:text-tg-text'
            }`}
          >
            O'qilmaganlar {unreadCount > 0 ? `(${unreadCount})` : ''}
          </button>
        </div>

        {/* Notifications List (Scrollable) */}
        <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 py-1">
          {loading ? (
            <div className="space-y-3 py-4 animate-pulse">
              {[1, 2, 3].map((n) => (
                <div key={n} className="h-18 bg-tg-secondary/50 rounded-2xl" />
              ))}
            </div>
          ) : filteredNotifications.length === 0 ? (
            <div className="py-10 text-center space-y-2">
              <div className="w-14 h-14 mx-auto rounded-3xl bg-tg-secondary/60 flex items-center justify-center text-tg-hint">
                <Bell className="w-7 h-7 stroke-[1.8]" />
              </div>
              <h4 className="text-sm font-semibold text-tg-text">
                {activeTab === 'unread' ? "O'qilmagan xabarnomalar yo'q" : "Hozircha xabarnomalar yo'q"}
              </h4>
              <p className="text-xs text-tg-hint max-w-xs mx-auto">
                Yangi darslar, AI baholash natijalari va mentor e'lonlari shu yerda chiqadi.
              </p>
            </div>
          ) : (
            filteredNotifications.map((item) => (
              <div
                key={item.id}
                onClick={() => handleMarkAsRead(item)}
                className={`p-3.5 rounded-2xl border transition-all cursor-pointer flex items-start gap-3 relative ${
                  item.is_read
                    ? 'bg-tg-secondary/20 border-tg-secondary/40 text-tg-hint hover:bg-tg-secondary/40'
                    : 'bg-blue-500/5 dark:bg-blue-500/10 border-blue-500/30 text-tg-text hover:border-blue-500/50 shadow-xs'
                }`}
              >
                {getNotificationIcon(item.type)}

                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-center justify-between gap-2">
                    <h4
                      className={`text-xs font-bold truncate ${
                        item.is_read ? 'text-tg-text/80' : 'text-tg-text font-extrabold'
                      }`}
                    >
                      {item.title}
                    </h4>
                    <span className="text-[10px] text-tg-hint font-medium shrink-0 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatTime(item.created_at)}
                    </span>
                  </div>

                  <p className="text-xs text-tg-hint leading-relaxed line-clamp-2">
                    {item.message}
                  </p>
                </div>

                {!item.is_read && (
                  <span className="w-2 h-2 rounded-full bg-blue-600 shrink-0 self-center animate-pulse" />
                )}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="pt-2 border-t border-tg-secondary shrink-0">
          <button
            type="button"
            onClick={() => {
              triggerHaptic('light');
              onClose();
            }}
            className="w-full py-2.5 rounded-xl bg-tg-secondary text-tg-text text-xs font-bold hover:bg-tg-secondary/80 transition-colors cursor-pointer"
          >
            Yopish
          </button>
        </div>
      </div>
    </div>
  );
};
