import { AppView } from '../types';
import { TelegramUser } from '../types';

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        ready: () => void;
        expand: () => void;
        close: () => void;
        enableClosingConfirmation: () => void;
        isExpanded: boolean;
        viewportHeight: number;
        viewportStableHeight: number;
        headerColor: string;
        backgroundColor: string;
        initData: string;
        initDataUnsafe?: {
          query_id?: string;
          user?: TelegramUser;
          receiver?: any;
          start_param?: string;
          auth_date?: number;
          hash?: string;
        };
        themeParams: {
          bg_color?: string;
          text_color?: string;
          hint_color?: string;
          link_color?: string;
          button_color?: string;
          button_text_color?: string;
          secondary_bg_color?: string;
          header_bg_color?: string;
          accent_text_color?: string;
          section_bg_color?: string;
          section_header_text_color?: string;
          subtitle_text_color?: string;
          destructive_text_color?: string;
        };
        BackButton: {
          isVisible: boolean;
          show: () => void;
          hide: () => void;
          onClick: (callback: () => void) => void;
          offClick: (callback: () => void) => void;
        };
        MainButton: {
          text: string;
          color: string;
          textColor: string;
          isVisible: boolean;
          isActive: boolean;
          isProgressVisible: boolean;
          setText: (text: string) => void;
          onClick: (callback: () => void) => void;
          offClick: (callback: () => void) => void;
          show: () => void;
          hide: () => void;
          enable: () => void;
          disable: () => void;
          showProgress: (leaveActive?: boolean) => void;
          hideProgress: () => void;
        };
        HapticFeedback: {
          impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void;
          notificationOccurred: (type: 'error' | 'success' | 'warning') => void;
          selectionChanged: () => void;
        };
        openTelegramLink: (url: string) => void;
        openLink: (url: string, options?: { try_instant_view?: boolean }) => void;
        showAlert: (message: string, callback?: () => void) => void;
        showConfirm: (message: string, callback?: (confirmed: boolean) => void) => void;
      };
    };
  }
}

export function initTelegramApp() {
  applyTelegramTheme();
  if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
    try {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
      if (window.Telegram.WebApp.enableClosingConfirmation) {
        window.Telegram.WebApp.enableClosingConfirmation();
      }
      applyTelegramTheme();
      if ((window.Telegram.WebApp as any).onEvent) {
        (window.Telegram.WebApp as any).onEvent('themeChanged', applyTelegramTheme);
      }
    } catch (e) {
      console.warn('Telegram WebApp init warning:', e);
    }
  }
}

function isHexColorDark(hex: string): boolean {
  if (!hex) return false;
  const clean = hex.replace('#', '').trim();
  let r = 255, g = 255, b = 255;
  if (clean.length === 3) {
    r = parseInt(clean[0] + clean[0], 16);
    g = parseInt(clean[1] + clean[1], 16);
    b = parseInt(clean[2] + clean[2], 16);
  } else if (clean.length === 6) {
    r = parseInt(clean.substring(0, 2), 16);
    g = parseInt(clean.substring(2, 4), 16);
    b = parseInt(clean.substring(4, 6), 16);
  } else {
    return false;
  }
  const yiq = (r * 299 + g * 587 + b * 114) / 1000;
  return yiq < 128;
}

export function applyTelegramTheme() {
  if (typeof window === 'undefined') return;
  const root = document.documentElement;
  const webApp = window.Telegram?.WebApp;
  const theme = webApp?.themeParams;

  let isDark = false;

  // 1. Telegram uzatgan rang eng ustuvor hisoblanadi (Telegram oq bo'lsa, 100% yorug' rejim bo'ladi)
  if (theme?.bg_color) {
    isDark = isHexColorDark(theme.bg_color);
  } else if (webApp?.colorScheme) {
    isDark = webApp.colorScheme === 'dark';
  } else {
    // 2. Agar Telegram ma'lumot bermagan bo'lsa, foydalanuvchi sozlamasi tekshiriladi
    const storedTheme = localStorage.getItem('bilimgo_theme');
    if (storedTheme === 'dark') {
      isDark = true;
    } else {
      isDark = false; // Standart holat har doim YORUG' (LIGHT) rejim! Telefon tizim qorong'iligi majburlanmaydi
    }
  }

  if (isDark) {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }

  if (!theme) return;

  if (theme.bg_color) root.style.setProperty('--tg-theme-bg-color', theme.bg_color);
  if (theme.secondary_bg_color) root.style.setProperty('--tg-theme-secondary-bg-color', theme.secondary_bg_color);
  if (theme.text_color) root.style.setProperty('--tg-theme-text-color', theme.text_color);
  if (theme.hint_color) root.style.setProperty('--tg-theme-hint-color', theme.hint_color);
  if (theme.link_color) root.style.setProperty('--tg-theme-link-color', theme.link_color);
  if (theme.button_color) root.style.setProperty('--tg-theme-button-color', theme.button_color);
  if (theme.button_text_color) root.style.setProperty('--tg-theme-button-text-color', theme.button_text_color);
  if (theme.accent_text_color) root.style.setProperty('--tg-theme-accent-text-color', theme.accent_text_color);
  if (theme.section_bg_color) root.style.setProperty('--tg-theme-section-bg-color', theme.section_bg_color);
  if (theme.destructive_text_color) root.style.setProperty('--tg-theme-destructive-text-color', theme.destructive_text_color);
}

export function getTelegramInitData(): string {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp?.initData) {
    return window.Telegram.WebApp.initData;
  }
  return '';
}

export function getTelegramUser(): TelegramUser | null {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp?.initDataUnsafe?.user) {
    return window.Telegram.WebApp.initDataUnsafe.user;
  }
  // Fallback demo user for local browser dev/testing (Admin telegram_id)
  return {
    id: 1467675358,
    first_name: 'Nurulloh',
    last_name: 'Habibullayev',
    username: 'nurulloh_bilimgo',
    language_code: 'uz'
  };
}

export function triggerHaptic(type: 'light' | 'medium' | 'heavy' | 'selection' | 'success' | 'error' = 'light') {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp?.HapticFeedback) {
    try {
      if (type === 'selection') {
        window.Telegram.WebApp.HapticFeedback.selectionChanged();
      } else if (type === 'success' || type === 'error') {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred(type);
      } else {
        window.Telegram.WebApp.HapticFeedback.impactOccurred(type);
      }
    } catch {
      // safe ignore in desktop browsers
    }
  }
}

export function parseRouteFromUrl(): AppView {
  if (typeof window === 'undefined') return { type: 'catalog' };

  // 1. Telegram WebApp start_param
  const tgStartParam = (window.Telegram?.WebApp?.initDataUnsafe?.start_param || '').toLowerCase().trim();

  // 2. URL search parameters
  const urlParams = new URLSearchParams(window.location.search);
  const viewParam = (urlParams.get('view') || urlParams.get('tab') || urlParams.get('page') || '').toLowerCase().trim();
  const startappParam = (urlParams.get('startapp') || urlParams.get('start_param') || '').toLowerCase().trim();
  const courseIdParam = urlParams.get('course_id') || urlParams.get('courseId');
  const cabinetIdParam = urlParams.get('cabinet_id') || urlParams.get('cabinetId');
  const sessionIdParam = urlParams.get('session_id') || urlParams.get('sessionId');

  // 3. URL Hash
  const rawHash = (window.location.hash || '').replace('#', '').toLowerCase().trim();

  // 4. Pathname
  const pathname = (window.location.pathname || '').toLowerCase().trim();

  // Combined string for heuristic checking
  const combined = `${tgStartParam} ${startappParam} ${viewParam} ${rawHash} ${pathname}`;

  // 1. PROFILE
  if (
    viewParam === 'profile' ||
    rawHash === 'profile' ||
    rawHash.startsWith('profile') ||
    pathname === '/profile' ||
    pathname.startsWith('/profile') ||
    tgStartParam === 'profile' ||
    startappParam === 'profile' ||
    combined.includes('profile')
  ) {
    return { type: 'profile' };
  }

  // 2. CABINET / CHAT
  if (
    viewParam === 'cabinet' ||
    viewParam === 'chat' ||
    rawHash.startsWith('cabinet') ||
    rawHash.startsWith('chat') ||
    pathname.startsWith('/cabinet') ||
    pathname.startsWith('/chat') ||
    tgStartParam.startsWith('cabinet') ||
    startappParam.startsWith('cabinet')
  ) {
    let cabId: string | number | undefined = cabinetIdParam || undefined;
    const cabMatch = combined.match(/cabinet[_-]?(\d+)/i) || pathname.match(/\/cabinet\/(\d+)/i);
    if (cabMatch && cabMatch[1]) {
      cabId = parseInt(cabMatch[1], 10);
    }
    return { type: 'cabinet', cabinetId: cabId };
  }

  // 3. MY COURSES
  if (
    viewParam === 'my-courses' ||
    viewParam === 'mycourses' ||
    rawHash === 'my-courses' ||
    rawHash === 'mycourses' ||
    pathname === '/my-courses' ||
    pathname === '/mycourses' ||
    tgStartParam === 'mycourses' ||
    tgStartParam === 'my-courses' ||
    combined.includes('my-courses') ||
    combined.includes('mycourses')
  ) {
    return { type: 'my-courses' };
  }

  // 4. MENTOR STATS / ANALYTICS
  if (
    viewParam === 'mentor-stats' ||
    viewParam === 'stats' ||
    rawHash.startsWith('stats') ||
    pathname.startsWith('/stats') ||
    tgStartParam.startsWith('stats')
  ) {
    return { type: 'mentor-stats' };
  }

  // 5. LIVE SESSION / STREAM
  if (
    viewParam === 'live' ||
    viewParam === 'live-stream' ||
    rawHash.startsWith('live') ||
    pathname.startsWith('/live') ||
    tgStartParam.startsWith('live') ||
    startappParam.startsWith('live')
  ) {
    let sessId = sessionIdParam || undefined;
    let cId = courseIdParam ? parseInt(courseIdParam, 10) : 1;
    const liveMatch = combined.match(/live[_-]?(\w+)/i) || pathname.match(/\/live\/(\w+)/i);
    if (liveMatch && liveMatch[1]) {
      sessId = liveMatch[1];
    }
    if (sessId && sessId !== 'live') {
      return { type: 'live-stream', sessionId: sessId, courseId: cId };
    }
    return { type: 'live', courseId: cId };
  }

  // 6. COURSE DETAIL
  if (
    courseIdParam ||
    viewParam === 'course' ||
    rawHash.startsWith('course') ||
    pathname.startsWith('/course') ||
    tgStartParam.includes('course') ||
    startappParam.includes('course')
  ) {
    let targetCourseId: number | null = null;
    if (courseIdParam && !isNaN(Number(courseIdParam))) {
      targetCourseId = parseInt(courseIdParam, 10);
    } else {
      const match = combined.match(/course[_-]?(\d+)/i) || pathname.match(/\/course\/(\d+)/i);
      if (match && match[1]) {
        targetCourseId = parseInt(match[1], 10);
      } else if (combined.includes('logist')) {
        targetCourseId = 1;
      } else if (combined.includes('tgads') || combined.includes('telegram')) {
        targetCourseId = 2;
      } else if (combined.includes('konkurs') || combined.includes('aksiya')) {
        targetCourseId = 3;
      } else if (combined.includes('sayt') || combined.includes('web')) {
        targetCourseId = 4;
      } else if (combined.includes('xitoy') || combined.includes('import')) {
        targetCourseId = 5;
      }
    }

    if (targetCourseId) {
      return { type: 'course', courseId: targetCourseId };
    }
  }

  return { type: 'catalog' };
}

export function getTelegramStartParam(): string | null {
  if (typeof window === 'undefined') return null;

  // 1. Telegram start_param (from WebAppInfo / Telegram link)
  const startParam = window.Telegram?.WebApp?.initDataUnsafe?.start_param;
  if (startParam) return startParam;

  // 2. URL search params (e.g. ?startapp=course_1 or ?course_id=1)
  const urlParams = new URLSearchParams(window.location.search);
  const fromQuery = urlParams.get('startapp') || urlParams.get('start_param') || urlParams.get('course_id');
  if (fromQuery) return fromQuery;

  // 3. URL hash (e.g. #course-1)
  if (window.location.hash) {
    const hash = window.location.hash.replace('#', '');
    if (hash) {
      return hash;
    }
  }

  return null;
}

