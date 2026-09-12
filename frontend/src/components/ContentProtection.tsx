import React, { useEffect, useState } from 'react';
import { Lock } from 'lucide-react';
import { TelegramUser } from '../types';
import { fetchUserProfile } from '../services/api';

interface ContentProtectionProps {
  user: TelegramUser | null;
  children: React.ReactNode;
}

export const ContentProtection: React.FC<ContentProtectionProps> = ({ user, children }) => {
  const [isAdmin, setIsAdmin] = useState<boolean>(false);
  const [isScreenProtected, setIsScreenProtected] = useState<boolean>(false);

  useEffect(() => {
    // Check if user is in .env admin list or has admin role
    fetchUserProfile()
      .then((profile) => {
        if (profile?.is_admin || profile?.role === 'admin' || profile?.role === 'super_mentor') {
          setIsAdmin(true);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    // If admin (in .env), completely bypass all screenshot and recording protection
    if (isAdmin) return;

    // 1. Anti-Screen Recording & App Switcher Blackout Protection
    const handleBlur = () => {
      setIsScreenProtected(true);
      // Pause any playing media
      const videos = document.querySelectorAll('video');
      videos.forEach((v) => v.pause());
      const audios = document.querySelectorAll('audio');
      audios.forEach((a) => a.pause());
    };

    const handleFocus = () => {
      setTimeout(() => {
        setIsScreenProtected(false);
      }, 150);
    };

    const handleVisibilityChange = () => {
      if (document.hidden) {
        handleBlur();
      } else {
        handleFocus();
      }
    };

    // 2. Anti-Screenshot / DevTools Keydown Blocking
    const handleKeyDown = (e: KeyboardEvent) => {
      // PrintScreen
      if (e.key === 'PrintScreen') {
        e.preventDefault();
        setIsScreenProtected(true);
        try {
          navigator.clipboard?.writeText?.('');
        } catch {}
        setTimeout(() => setIsScreenProtected(false), 800);
        return false;
      }

      // Ctrl+P (Print), Ctrl+S (Save), Ctrl+U (View Source)
      if ((e.ctrlKey || e.metaKey) && ['p', 's', 'u'].includes(e.key.toLowerCase())) {
        e.preventDefault();
        return false;
      }

      // F12 or Ctrl+Shift+I / C / J (DevTools)
      if (
        e.key === 'F12' ||
        ((e.ctrlKey || e.metaKey) && e.shiftKey && ['i', 'c', 'j'].includes(e.key.toLowerCase()))
      ) {
        e.preventDefault();
        return false;
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.key === 'PrintScreen') {
        try {
          navigator.clipboard?.writeText?.('');
        } catch {}
      }
    };

    // 3. Anti-Copy Context Menu
    const handleContextMenu = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (target?.tagName === 'INPUT' || target?.tagName === 'TEXTAREA') {
        return;
      }
      e.preventDefault();
    };

    window.addEventListener('blur', handleBlur);
    window.addEventListener('focus', handleFocus);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('keydown', handleKeyDown, { capture: true });
    window.addEventListener('keyup', handleKeyUp, { capture: true });
    document.addEventListener('contextmenu', handleContextMenu);

    return () => {
      window.removeEventListener('blur', handleBlur);
      window.removeEventListener('focus', handleFocus);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('keydown', handleKeyDown, { capture: true });
      window.removeEventListener('keyup', handleKeyUp, { capture: true });
      document.removeEventListener('contextmenu', handleContextMenu);
    };
  }, [isAdmin]);

  return (
    <div className="relative select-none">
      {children}

      {/* Screen Recording / Screenshot Protective Blackout Shield (Only for non-admins) */}
      {!isAdmin && isScreenProtected && (
        <div className="fixed inset-0 z-[99999] bg-[#070b14] flex flex-col items-center justify-center p-6 text-center animate-in fade-in duration-100">
          <div className="w-16 h-16 rounded-3xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 mb-4 shadow-xl shadow-blue-600/20">
            <Lock className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-black text-white tracking-tight mb-2">
            🔒 Himoyalangan Kontent
          </h3>
          <p className="text-xs text-white/70 max-w-xs leading-relaxed">
            Ekran tasvirini yozib olish (Screen recording) yoki skrinshot olish taqiqlangan. Ilovaga qaytganingizda dars davom etadi.
          </p>
        </div>
      )}
    </div>
  );
};
