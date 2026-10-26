import {
  Course,
  Lesson,
  LessonAccessTokenResponse,
  PurchaseInitiateResponse,
  Cabinet,
  CabinetStudent,
  ChatMessage,
  ChatReplyInfo,
  LiveSession,
  LiveJoinResponse,
  CourseProgressItem,
  CabinetActivityItem,
  UserProfile,
  UserRole,
  MentorInfo,
} from '../types';
import { getTelegramInitData, getTelegramUser } from './telegram';

// In-memory configuration store
const getInitialApiBase = (): string => {
  if (typeof process !== 'undefined' && (process.env as any)?.VITE_API_URL) {
    return (process.env as any).VITE_API_URL.replace(/\/+$/, '');
  }
  if (typeof window !== 'undefined' && window.location) {
    const origin = window.location.origin;
    const port = window.location.port;
    if (port && ['3000', '5173', '5174', '5175', '4173', '8080'].includes(port)) {
      return 'http://localhost:8000';
    }
    if (origin.startsWith('http://') || origin.startsWith('https://')) {
      return origin;
    }
  }
  return 'http://localhost:8000';
};

let customApiBase = getInitialApiBase();
let useMockFallbackWhenOffline = false;
let isConnectedToLiveBackend = false;

export function getApiBaseUrl(): string {
  return customApiBase;
}

export function setApiBaseUrl(url: string) {
  customApiBase = url.replace(/\/+$/, '');
}

export function setMockFallback(enabled: boolean) {
  useMockFallbackWhenOffline = enabled;
}

export function getBackendStatus() {
  return {
    apiBase: customApiBase,
    useMockFallback: useMockFallbackWhenOffline,
    isConnected: isConnectedToLiveBackend,
  };
}

export function cleanNumericId(id: string | number | undefined | null): number {
  if (id === undefined || id === null) return 1;
  if (typeof id === 'number') return id;
  const str = String(id).trim();
  const digitsOnly = str.replace(/^(course-|l-|cab-|msg-|st-|room-|live-|u-)/, '');
  const parsed = parseInt(digitsOnly, 10);
  return isNaN(parsed) ? 1 : parsed;
}

export function enhanceCourse(c: any): Course {
  const idNum = cleanNumericId(c.id);
  const title = c.title || 'Nomsiz kurs';
  
  let category = c.category;
  let thumbnail = c.thumbnail;
  let instructor = c.instructor || 'Nurulloh Habibullayev (Bosh Mentor)';

  if (!category) {
    const t = title.toLowerCase();
    if (t.includes('logist')) category = 'Logistika & Dispetcherlik';
    else if (t.includes('ads') || t.includes('reklama')) category = 'Telegram Marketing';
    else if (t.includes('konkurs') || t.includes('aksiya')) category = 'Biznes & Konkurs';
    else if (t.includes('sayt') || t.includes('daromad')) category = 'Web & Monetizatsiya';
    else if (t.includes('xitoy') || t.includes('import')) category = 'Savdo & Import';
    else if (t.includes('python') || t.includes('backend')) category = 'Backend Dasturlash';
    else if (t.includes('react') || t.includes('mini app')) category = 'Frontend & TMA';
    else category = 'Amaliy Kurs';
  }

  if (!thumbnail) {
    const t = title.toLowerCase();
    if (t.includes('logist')) {
      thumbnail = 'https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=800&auto=format&fit=crop&q=60';
    } else if (t.includes('ads') || t.includes('reklama')) {
      thumbnail = 'https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=800&auto=format&fit=crop&q=60';
    } else if (t.includes('konkurs') || t.includes('aksiya')) {
      thumbnail = 'https://images.unsplash.com/photo-1513151233558-d860c5398176?w=800&auto=format&fit=crop&q=60';
    } else if (t.includes('sayt') || t.includes('daromad')) {
      thumbnail = 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&auto=format&fit=crop&q=60';
    } else if (t.includes('xitoy') || t.includes('import')) {
      thumbnail = 'https://images.unsplash.com/photo-1578575437130-527eed3abbec?w=800&auto=format&fit=crop&q=60';
    } else {
      thumbnail = 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800&auto=format&fit=crop&q=60';
    }
  }

  return {
    ...c,
    id: idNum,
    title,
    category,
    thumbnail,
    instructor,
    base_price: Number(c.base_price) || 0,
    owner_node_id: c.owner_node_id || 1,
    is_enrolled: Boolean(c.is_enrolled || c.has_access),
    has_access: Boolean(c.has_access || c.is_enrolled),
    total_lessons: c.total_lessons || 0,
    total_duration_minutes: c.total_duration_minutes || (c.total_duration_sec ? Math.round(c.total_duration_sec / 60) : 0),
  };
}

// Common headers generator with X-Telegram-Init-Data & X-Telegram-User-Id
function getHeaders(customHeaders: Record<string, string> = {}): HeadersInit {
  const initData = getTelegramInitData();
  const user = getTelegramUser();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...customHeaders,
  };

  if (initData) {
    headers['X-Telegram-Init-Data'] = initData;
  }
  if (user?.id) {
    headers['X-Telegram-User-Id'] = String(user.id);
  }

  return headers;
}

// Fetch helper with graceful fallback
async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  fallbackGenerator?: () => Promise<T> | T
): Promise<T> {
  const url = `${customApiBase}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: getHeaders(options.headers as Record<string, string>),
    });

    if (!res.ok) {
      if (res.status === 403) {
        throw new Error('403: Bu darsga hali ruxsatingiz yo\'q (Adaptive Unlock)');
      }
      if (res.status === 404) {
        throw new Error('404: Ma\'lumot topilmadi');
      }
      if (res.status === 401) {
        throw new Error('401: Autentifikatsiya talab qilinadi');
      }
      throw new Error(`Xatolik: ${res.status} ${res.statusText}`);
    }

    isConnectedToLiveBackend = true;
    return (await res.json()) as T;
  } catch (err: any) {
    console.warn(`[BilimGo API] Error calling ${endpoint}:`, err.message);
    if (useMockFallbackWhenOffline && fallbackGenerator) {
      return fallbackGenerator();
    }
    throw err;
  }
}

/* =========================================================================
   API Endpoints implementation
========================================================================= */

// 1. GET /api/courses
export async function fetchCourses(): Promise<Course[]> {
  const list = await request<Course[]>(
    '/api/courses',
    { method: 'GET' },
    () => mockCourses
  );
  return (list || []).map(enhanceCourse);
}

// 2. GET /api/courses/{course_id}
export async function fetchCourseById(courseId: string | number): Promise<Course> {
  const cleanId = cleanNumericId(courseId);
  const course = await request<Course>(
    `/api/courses/${cleanId}`,
    { method: 'GET' },
    () => {
      const found = mockCourses.find((c) => String(c.id) === String(courseId) || String(c.id) === `course-${cleanId}`);
      if (!found) throw new Error('Kurs topilmadi');
      return found;
    }
  );
  return enhanceCourse(course);
}

// 3. GET /api/courses/{course_id}/lessons (header: X-Telegram-Init-Data)
export async function fetchCourseLessons(courseId: string | number): Promise<Lesson[]> {
  const cleanId = cleanNumericId(courseId);
  const list = await request<Lesson[]>(
    `/api/courses/${cleanId}/lessons`,
    { method: 'GET' },
    () => {
      return mockLessons[String(courseId)] || mockLessons[`course-${cleanId}`] || defaultMockLessons(courseId);
    }
  );
  return (list || []).map((item: any) => ({
    ...item,
    id: cleanNumericId(item.id),
    unlocked: Boolean(item.is_accessible ?? item.unlocked ?? item.is_free_preview),
    is_accessible: Boolean(item.is_accessible ?? item.unlocked ?? item.is_free_preview),
  }));
}

// 4. POST /api/lessons/{lesson_id}/access-token (header: X-Telegram-Init-Data)
export async function fetchLessonAccessToken(lessonId: string | number): Promise<LessonAccessTokenResponse> {
  const cleanId = cleanNumericId(lessonId);
  return request<LessonAccessTokenResponse>(
    `/api/lessons/${cleanId}/access-token`,
    { method: 'POST' },
    () => {
      // Find lesson across all mock lists
      let targetLesson: Lesson | undefined;
      for (const list of Object.values(mockLessons)) {
        const item = list.find((l) => String(l.id) === String(lessonId) || cleanNumericId(l.id) === cleanId);
        if (item) {
          targetLesson = item;
          break;
        }
      }

      if (targetLesson && !targetLesson.unlocked && !targetLesson.is_free_preview) {
        const error = new Error('Bu darsga hali ruxsatingiz yo\'q');
        (error as any).status = 403;
        throw error;
      }

      // Sample playable MP4 video for native player verification & range seek
      return {
        stream_url: targetLesson?.video_url_sample || 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
        expires_at: new Date(Date.now() + 3600 * 1000).toISOString(),
      };
    }
  );
}

// 4.1 POST /api/lessons/{lesson_id}/progress
export interface LessonProgressPayload {
  watch_duration_sec: number;
  completion_percent: number;
}

export async function updateLessonProgress(
  lessonId: string | number,
  payload: LessonProgressPayload
): Promise<{ status: string; lesson_id: number; is_completed: boolean; completion_percent: number }> {
  const cleanId = cleanNumericId(lessonId);
  return request<{ status: string; lesson_id: number; is_completed: boolean; completion_percent: number }>(
    `/api/lessons/${cleanId}/progress`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
    () => ({
      status: 'ok',
      lesson_id: cleanId,
      is_completed: payload.completion_percent >= 90,
      completion_percent: payload.completion_percent,
    })
  );
}

// 5. POST /api/payments/purchase/initiate?course_id={id}&license_node_id={owner_node_id}&provider={click|payme}
export async function initiatePurchase(
  courseId: string | number,
  ownerNodeId: string | number,
  provider: 'click' | 'payme'
): Promise<PurchaseInitiateResponse> {
  const cleanCourseId = cleanNumericId(courseId);
  const cleanNodeId = cleanNumericId(ownerNodeId);
  const query = new URLSearchParams({
    course_id: String(cleanCourseId),
    license_node_id: String(cleanNodeId),
    provider,
  });

  return request<PurchaseInitiateResponse>(
    `/api/payments/purchase/initiate?${query.toString()}`,
    { method: 'POST' },
    () => {
      // Mock successful initiation
      const course = mockCourses.find((c) => String(c.id) === String(courseId) || cleanNumericId(c.id) === cleanCourseId);
      return {
        sale_id: `SALE-${Date.now().toString().slice(-6)}`,
        amount: course?.base_price || 180000,
      };
    }
  );
}

// 6. GET /api/cabinets/me (header: X-Telegram-Init-Data)
export function getSavedCabinets(): Cabinet[] {
  const cached = localStorage.getItem('bilimgo_cabinets');
  if (cached) {
    try {
      return JSON.parse(cached);
    } catch {
      return mockCabinets;
    }
  }
  return mockCabinets;
}

export function saveCabinetsToStorage(cabinets: Cabinet[]) {
  localStorage.setItem('bilimgo_cabinets', JSON.stringify(cabinets));
}

export async function fetchMyCabinets(): Promise<Cabinet[]> {
  const realList = await request<Cabinet[]>(
    '/api/cabinets/me',
    { method: 'GET' },
    () => getSavedCabinets()
  );
  if (realList && Array.isArray(realList) && realList.length > 0) {
    saveCabinetsToStorage(realList);
  }
  return realList;
}

// 6.1 POST /api/cabinets (Mentor creates new group chat)
export interface CreateCabinetPayload {
  display_name: string;
  avatar?: string;
  description?: string;
  course_id?: string | number;
  course_title?: string;
  initial_message?: string;
}

export async function createCabinet(payload: CreateCabinetPayload): Promise<Cabinet> {
  const user = getTelegramUser();
  const mentorName = user ? `${user.first_name} ${user.last_name || ''}`.trim() : 'Mentor';
  const cleanCourseId = payload.course_id ? cleanNumericId(payload.course_id) : undefined;

  const newCabinet: Cabinet = {
    id: `cab-${Date.now()}`,
    display_name: payload.display_name.trim(),
    role_in_cabinet: 'mentor',
    avatar: payload.avatar || '💬',
    unread_count: 0,
    course_id: cleanCourseId,
    course_title: payload.course_title,
    description: payload.description,
    mentor_name: mentorName,
    created_at: new Date().toISOString(),
    students_count: 1,
  };

  return request<Cabinet>(
    '/api/cabinets',
    {
      method: 'POST',
      body: JSON.stringify({
        ...payload,
        course_id: cleanCourseId,
      }),
    },
    () => {
      const current = getSavedCabinets();
      const updated = [newCabinet, ...current];
      saveCabinetsToStorage(updated);

      // Seed initial welcome message if given or default
      const welcomeMsg: ChatMessage = {
        id: `msg-${Date.now()}`,
        sender_id: user?.id || 999111,
        sender_name: mentorName,
        content:
          payload.initial_message?.trim() ||
          `Assalomu alaykum! Ushbu "${newCabinet.display_name}" guruh chatiga xush kelibsiz. Savollaringiz bo'lsa bemalol yozishingiz mumkin.`,
        sent_at: new Date().toISOString(),
        is_me: true,
        role: 'mentor',
      };
      mockChatStore[String(newCabinet.id)] = [welcomeMsg];

      return newCabinet;
    }
  );
}

// 6.2 PUT /api/cabinets/{cabinet_id} (Update cabinet details)
export async function updateCabinet(
  cabinetId: string | number,
  updates: Partial<Cabinet>
): Promise<Cabinet> {
  const cleanId = cleanNumericId(cabinetId);
  return request<Cabinet>(
    `/api/cabinets/${cleanId}`,
    {
      method: 'PUT',
      body: JSON.stringify(updates),
    },
    () => {
      const current = getSavedCabinets();
      const idx = current.findIndex((c) => String(c.id) === String(cabinetId) || cleanNumericId(c.id) === cleanId);
      if (idx !== -1) {
        current[idx] = { ...current[idx], ...updates };
        saveCabinetsToStorage(current);
        return current[idx];
      }
      throw new Error('Cabinet topilmadi');
    }
  );
}

// 6.3 DELETE /api/cabinets/{cabinet_id}
export async function deleteCabinet(cabinetId: string | number): Promise<{ success: boolean }> {
  const cleanId = cleanNumericId(cabinetId);
  return request<{ success: boolean }>(
    `/api/cabinets/${cleanId}`,
    { method: 'DELETE' },
    () => {
      const current = getSavedCabinets();
      const filtered = current.filter((c) => String(c.id) !== String(cabinetId) && cleanNumericId(c.id) !== cleanId);
      saveCabinetsToStorage(filtered);
      delete mockChatStore[String(cabinetId)];
      delete mockChatStore[String(cleanId)];
      return { success: true };
    }
  );
}

// 7. GET /api/cabinets/{cabinet_id}/students (header: X-Telegram-Init-Data)
export async function fetchCabinetStudents(cabinetId: string | number): Promise<CabinetStudent[]> {
  const cleanId = cleanNumericId(cabinetId);
  return request<CabinetStudent[]>(
    `/api/cabinets/${cleanId}/students`,
    { method: 'GET' },
    () => mockStudents
  );
}

// 8. POST /api/chat/rooms/{room_id}/messages (header: X-Telegram-Init-Data, body: {content, reply_to})
export async function sendChatMessage(
  roomId: string | number,
  content: string,
  replyTo?: ChatReplyInfo
): Promise<ChatMessage> {
  const cleanRoomId = cleanNumericId(roomId);
  return request<ChatMessage>(
    `/api/chat/rooms/${cleanRoomId}/messages`,
    {
      method: 'POST',
      body: JSON.stringify({ content, reply_to: replyTo }),
    },
    () => {
      const user = getTelegramUser();
      const currentRoomMsgs = mockChatStore[String(roomId)] || defaultMockMessages();
      mockChatStore[String(roomId)] = currentRoomMsgs;

      // Deduplicate immediate rapid spam clicks (< 1.5s identical message)
      const lastMsg = currentRoomMsgs[currentRoomMsgs.length - 1];
      if (
        lastMsg &&
        lastMsg.content === content &&
        String(lastMsg.sender_id) === String(user?.id || 123456789) &&
        Date.now() - new Date(lastMsg.sent_at).getTime() < 1500
      ) {
        return lastMsg;
      }

      const newMsg: ChatMessage = {
        id: `msg-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
        sender_id: user?.id || 123456789,
        sender_name: user?.first_name || 'Men',
        content,
        sent_at: new Date().toISOString(),
        is_me: true,
        reply_to: replyTo,
      };

      currentRoomMsgs.push(newMsg);
      return newMsg;
    }
  );
}

// 9. GET /api/chat/rooms/{room_id}/messages?after_id={last_id} (header: X-Telegram-Init-Data)
export async function fetchChatMessages(
  roomId: string | number,
  afterId?: string | number | null
): Promise<ChatMessage[]> {
  const cleanRoomId = cleanNumericId(roomId);
  const cleanAfter = afterId ? cleanNumericId(afterId) : 0;
  const query = cleanAfter > 0 ? `?after_id=${cleanAfter}` : '';
  return request<ChatMessage[]>(
    `/api/chat/rooms/${cleanRoomId}/messages${query}`,
    { method: 'GET' },
    () => {
      const roomMsgs = mockChatStore[String(roomId)] || defaultMockMessages();
      mockChatStore[String(roomId)] = roomMsgs;

      if (!afterId) {
        return [...roomMsgs];
      }

      const idx = roomMsgs.findIndex((m) => String(m.id) === String(afterId));
      if (idx === -1) {
        // If afterId is not found, return empty array to prevent appending entire history again
        return [];
      }
      return roomMsgs.slice(idx + 1);
    }
  );
}

// 10. GET /api/live/courses/{course_id}/sessions
export async function fetchLiveSessions(courseId: string | number): Promise<LiveSession[]> {
  const cleanId = cleanNumericId(courseId);
  return request<LiveSession[]>(
    `/api/live/courses/${cleanId}/sessions`,
    { method: 'GET' },
    () => mockLiveSessions[String(courseId)] || defaultLiveSessions(courseId)
  );
}

// 11. POST /api/live/sessions/{session_id}/join (header: X-Telegram-Init-Data)
export async function joinLiveSession(sessionId: string | number): Promise<LiveJoinResponse> {
  const cleanId = cleanNumericId(sessionId);
  return request<LiveJoinResponse>(
    `/api/live/sessions/${cleanId}/join`,
    { method: 'POST' },
    () => {
      return {
        stream_ref: `https://meet.jit.si/BilimGo-LiveSession-${sessionId}`,
        join_method: 'webrtc_stream',
      };
    }
  );
}

// 12. POST /api/live/sessions/{session_id}/leave (header: X-Telegram-Init-Data)
export async function leaveLiveSession(sessionId: string | number): Promise<{ success: boolean }> {
  const cleanId = cleanNumericId(sessionId);
  return request<{ success: boolean }>(
    `/api/live/sessions/${cleanId}/leave`,
    { method: 'POST' },
    () => ({ success: true })
  );
}

// 13. GET /api/analytics/courses/{course_id}/my-progress (header: X-Telegram-Init-Data)
export async function fetchMyCourseProgress(courseId: string | number): Promise<CourseProgressItem[]> {
  const cleanId = cleanNumericId(courseId);
  return request<CourseProgressItem[]>(
    `/api/analytics/courses/${cleanId}/my-progress`,
    { method: 'GET' },
    () => mockCourseProgress[String(courseId)] || defaultCourseProgress(courseId)
  );
}

// 14. GET /api/analytics/cabinets/activity & multi-mentor student tracking
export async function fetchCabinetActivity(
  cabinetId?: string | number,
  mentorId?: string | number
): Promise<CabinetActivityItem[]> {
  const cleanCab = cabinetId && cabinetId !== 'all' ? cleanNumericId(cabinetId) : '';
  const cleanMentor = mentorId && mentorId !== 'all' ? cleanNumericId(mentorId) : '';
  return request<CabinetActivityItem[]>(
    `/api/analytics/cabinets/activity?cabinet_id=${cleanCab}&mentor_id=${cleanMentor}`,
    { method: 'GET' },
    () => {
      const userProfile = getCachedUserProfile();
      const role = userProfile?.role || 'mentor';

      let list = [...mockAllStudentsActivity];

      // If mentor role, strictly show their own students
      if (role === 'mentor') {
        const myMentorId = userProfile?.assigned_mentor_id || 'mentor-1';
        list = list.filter((st) => st.mentor_id === myMentorId || (cabinetId && String(st.cabinet_id) === String(cabinetId)));
      } else if (role === 'super_mentor' || role === 'admin') {
        // Super mentor or admin can filter by mentor or see all
        if (mentorId && mentorId !== 'all') {
          list = list.filter((st) => String(st.mentor_id) === String(mentorId));
        }
      }

      // Filter by cabinet if specified
      if (cabinetId && cabinetId !== 'all') {
        list = list.filter((st) => String(st.cabinet_id) === String(cabinetId));
      }

      return list;
    }
  );
}

// 15. GET /api/mentors - List all mentors on the platform (Super Mentor / Admin)
export async function fetchMentorsList(): Promise<MentorInfo[]> {
  return request<MentorInfo[]>(
    '/api/mentors',
    { method: 'GET' },
    () => mockMentors
  );
}

// Helper to get cached user profile synchronously
export function getCachedUserProfile(): UserProfile | null {
  const cached = localStorage.getItem('bilimgo_user_profile');
  if (cached) {
    try {
      return JSON.parse(cached);
    } catch {
      return null;
    }
  }
  return null;
}

// 16. GET /api/users/profile & PUT /api/users/profile
export async function fetchUserProfile(): Promise<UserProfile> {
  const tgUser = getTelegramUser();
  const profile = await request<UserProfile>(
    '/api/users/profile',
    { method: 'GET' },
    () => getDefaultUserProfile(tgUser)
  );

  // Merge live Telegram user information (photo_url, username, first_name, last_name)
  if (tgUser) {
    if (tgUser.photo_url) {
      profile.avatar = tgUser.photo_url;
    } else if (!profile.avatar && (profile.telegram_id || tgUser.id)) {
      profile.avatar = `/api/users/${profile.telegram_id || tgUser.id}/avatar`;
    }
    if (tgUser.username) {
      profile.username = `@${tgUser.username.replace(/^@/, '')}`;
    }
    if (tgUser.first_name) {
      profile.first_name = tgUser.first_name;
    }
    if (tgUser.last_name) {
      profile.last_name = tgUser.last_name;
    }
  }

  localStorage.setItem('bilimgo_user_profile', JSON.stringify(profile));
  return profile;
}

export async function updateUserProfile(updates: Partial<UserProfile>): Promise<UserProfile> {
  const current = await fetchUserProfile();
  const updated: UserProfile = { ...current, ...updates };
  localStorage.setItem('bilimgo_user_profile', JSON.stringify(updated));

  return request<UserProfile>(
    '/api/users/profile',
    {
      method: 'PUT',
      body: JSON.stringify(updates),
    },
    () => updated
  );
}

function getDefaultUserProfile(tgUser: any): UserProfile {
  return {
    id: tgUser?.id ? `u-${tgUser.id}` : 'u-774912',
    telegram_id: tgUser?.id || 774912384,
    first_name: tgUser?.first_name || 'Habibullayev',
    last_name: tgUser?.last_name || 'Nurulla',
    username: tgUser?.username ? `@${tgUser.username}` : '@habibullayev_n',
    phone: '+998 90 123 45 67',
    avatar: tgUser?.photo_url || '',
    role: 'super_mentor', // Default to super_mentor so user can immediately view all mentor students and toggle
    assigned_mentor_id: 'mentor-1',
    enrolled_courses_count: 3,
    completed_lessons_count: 14,
    total_study_time_minutes: 380,
    streak_days: 7,
    joined_date: '12 Yanvar, 2026',
    wallet_balance: 150000,
    certificate_count: 1,
  };
}

// 17. POST /api/ai/ask-lesson & /api/ai/lesson-chat (AI Lesson Assistant)
export interface AskLessonAiPayload {
  lessonId?: string | number;
  courseTitle?: string;
  lessonTitle: string;
  lessonDescription?: string;
  question: string;
  history?: Array<{ sender: 'user' | 'assistant'; text: string }>;
}

export async function askLessonAi(payload: AskLessonAiPayload): Promise<{ answer: string }> {
  try {
    const rawLessonId = payload.lessonId || (payload.lessonTitle ? parseInt(payload.lessonTitle.replace(/\D/g, '')) || 1 : 1);
    const body = {
      lesson_id: rawLessonId,
      message: payload.question,
      question: payload.question,
      courseTitle: payload.courseTitle,
      lessonTitle: payload.lessonTitle,
      lessonDescription: payload.lessonDescription,
      history: (payload.history || []).map((h) => ({
        role: h.sender === 'assistant' ? 'assistant' : 'user',
        content: h.text,
        sender: h.sender,
        text: h.text,
      })),
    };

    const res = await fetch(`${customApiBase}/api/ai/lesson-chat`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(body),
    });

    if (res.ok) {
      const data = await res.json();
      const answer = data.answer || data.reply || '';
      if (answer) {
        return { answer };
      }
    }
  } catch (e) {
    console.warn('Direct server AI call failed, falling back to contextual generator', e);
  }

  // Graceful client-side fallback if server route is in offline mode
  return generateContextualFallbackAiAnswer(payload);
}

function generateContextualFallbackAiAnswer(payload: AskLessonAiPayload): { answer: string } {
  const { lessonTitle, question } = payload;
  const q = question.toLowerCase();

  if (q.includes('xulosa') || q.includes('umumiy') || q.includes('haqida')) {
    return {
      answer: `📌 **"${lessonTitle}" darsining qisqacha xulosasi:**\n\n1. **Asosiy maqsad:** Darsda mavzuning fundamental tamoyillari va amaliy qo'llanilishi bosqichma-bosqich yoritilgan.\n2. **Muhim nuqtalar:** Xavfsizlik, to'g'ri sintaksis va optimallashtirish usullari.\n3. **Amaliyot:** O'rgangan bilimlaringizni mustahkamlash uchun mini topshiriqni bajarib ko'ring.\n\n*Yana qaysi qismiga tushunmadingiz? Bemalol so'rang!*`,
    };
  }

  if (q.includes('misol') || q.includes('kod') || q.includes('namuna')) {
    return {
      answer: `💡 **"${lessonTitle}" mavzusi bo'yicha amaliy namuna:**\n\n\`\`\`python\n# Mavzuga oid namunaviy kod\ndef handle_lesson_flow(lesson_id: str):\n    print(f"Dars {lesson_id} muvaffaqiyatli ishga tushirildi")\n    return {"status": "success", "unlocked": True}\n\`\`\`\n\nUshbu kod parchasi darsda ko'rsatilgan asosiy mantiqni ifodalaydi. Uni o'z loyihangizda sinab ko'rishingiz mumkin!`,
    };
  }

  if (q.includes('savol') || q.includes('sinash') || q.includes('test')) {
    return {
      answer: `🎯 **O'zingizni sinash uchun 3 ta savol:**\n\n1. **1-Savol:** Ushbu darsda ko'rilgan asosiy tushunchaning asosiy vazifasi nima?\n2. **2-Savol:** Qanday holatlarda ushbu yondashuvdan foydalanish xavfsizlikni oshiradi?\n3. **3-Savol:** Amaliyotda eng ko'p uchraydigan 2 ta xatoni ayta olasizmi?\n\n*Javoblaringizni shu yerga yozing, to'g'riligini tekshirib beraman!*`,
    };
  }

  return {
    answer: `🤖 **AI Ustoz javobi:**\n\nSiz **"${lessonTitle}"** mavzusi yuzasidan juda yaxshi savol berdingiz:\n> "${question}"\n\nUshbu mavzuni tushunish uchun eng asosiy qoida — nazariyani darhol amalda qo'llab ko'rishdir. Darsdagi videoni kerakli vaqtiga qaytarib ko'rishingiz yoki yuqoridagi tezkor tugmalardan foydalanib qo'shimcha misollar olishingiz mumkin.`,
  };
}

/* =========================================================================
   Mock In-Memory Data (Clean Uzbek Language Educational Mock Data)
========================================================================= */

export const mockCourses: Course[] = [
  {
    id: 'course-1',
    title: 'Python va FastAPI: Noldan Mutaxassisgacha',
    base_price: 350000,
    owner_node_id: 'node_py_01',
    description: "Backend dasturlash asoslari, asinxron FastAPI arxitekturasi, PostgreSQL ma'lumotlar bazasi va Telegram botlar bilan integratsiya qilish bo'yicha to'liq amaliy kurs.",
    category: 'Backend Dasturlash',
    instructor: 'Javohir Toshpo\'latov (Senior Backend Engineer)',
    thumbnail: 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=800&auto=format&fit=crop&q=60',
    total_lessons: 12,
    total_duration_minutes: 240,
    is_enrolled: true,
  },
  {
    id: 'course-2',
    title: 'React & Telegram Mini Apps (TMA) Ishlab Chiqish',
    base_price: 290000,
    owner_node_id: 'node_react_02',
    description: "Zamonaviy React 19, Tailwind CSS va Telegram WebApp SDK orqali to'liq ishlovchi interaktiv bot-ilovalar yaratish kursi.",
    category: 'Frontend & WebApp',
    instructor: 'Madina Karimova (Lead Frontend Developer)',
    thumbnail: 'https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=800&auto=format&fit=crop&q=60',
    total_lessons: 8,
    total_duration_minutes: 180,
    is_enrolled: true,
  },
  {
    id: 'course-3',
    title: 'Sun\'iy Intellekt va Prompt Engineering Asoslari',
    base_price: 190000,
    owner_node_id: 'node_ai_03',
    description: "Gemini API, LLM modellar bilan ishlash, biznes jarayonlarni avtomatlashtirish va amaliy sun'iy intellekt botlari.",
    category: 'Sun\'iy Intellekt',
    instructor: 'Farrux Ergashev (AI Research Fellow)',
    thumbnail: 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800&auto=format&fit=crop&q=60',
    total_lessons: 6,
    total_duration_minutes: 130,
    is_enrolled: false,
  },
  {
    id: 'course-4',
    title: 'UI/UX Dizayn: Figma orqali Mobil Ilovalar',
    base_price: 220000,
    owner_node_id: 'node_design_04',
    description: "Figma komponentlari, Auto-layout, dizayn tizimlari va Telegram Mini App foydalanuvchi tajribasini loyihalash.",
    category: 'Dizayn',
    instructor: 'Sevara Alimova (Product Designer)',
    thumbnail: 'https://images.unsplash.com/photo-1581291518857-4e27b48ff24e?w=800&auto=format&fit=crop&q=60',
    total_lessons: 10,
    total_duration_minutes: 200,
    is_enrolled: false,
  },
];

export const mockLessons: Record<string, Lesson[]> = {
  'course-1': [
    {
      id: 'l-101',
      course_id: 'course-1',
      title: '1. Kirish: Python va FastAPI nima uchun kerak?',
      order_index: 1,
      duration_sec: 480,
      is_free_preview: true,
      unlocked: true,
      description: "FastAPI afzalliklari, Python 3.12 tiplar tizimi va virtual muhitni o'rnatish.",
      video_url_sample: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
    },
    {
      id: 'l-102',
      course_id: 'course-1',
      title: '2. Pydantic modellari va Request Validatsiyasi',
      order_index: 2,
      duration_sec: 720,
      is_free_preview: false,
      unlocked: true, // Adaptive unlock: open today
      description: "Sxemalarni loyihalash, ma'lumotlarni tekshirish va response modellar bilan ishlash.",
      video_url_sample: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4',
    },
    {
      id: 'l-103',
      course_id: 'course-1',
      title: '3. Dependency Injection va Telegram Auth Headers',
      order_index: 3,
      duration_sec: 900,
      is_free_preview: false,
      unlocked: true,
      description: "Depends() mexanizmi orqali X-Telegram-Init-Data tekshirish va xavfsiz autentifikatsiya.",
      video_url_sample: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4',
    },
    {
      id: 'l-104',
      course_id: 'course-1',
      title: '4. Asinxron SQLAlchemy 2.0 va PostgreSQL',
      order_index: 4,
      duration_sec: 1100,
      is_free_preview: false,
      unlocked: false, // Adaptive lock (not yet unlocked for user)
      description: "Ma'lumotlar bazasi jadvallari, migratsiyalar va tezkor so'rovlar.",
      video_url_sample: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyBlazes.mp4',
    },
    {
      id: 'l-105',
      course_id: 'course-1',
      title: '5. HTTP Video Streaming va Range So\'rovlari',
      order_index: 5,
      duration_sec: 840,
      is_free_preview: false,
      unlocked: false,
      description: "Video oqimlarini qismlarga bo'lib uzatish, bufferlash va optimizatsiya.",
      video_url_sample: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4',
    },
    {
      id: 'l-106',
      course_id: 'course-1',
      title: '6. Click va Payme To\'lov Tizimlari Integratsiyasi',
      order_index: 6,
      duration_sec: 1250,
      is_free_preview: false,
      unlocked: false,
      description: "To'lov cheklarini generatsiya qilish va webhook xavfsizligi.",
      video_url_sample: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4',
    },
  ],
  'course-2': [
    {
      id: 'l-201',
      course_id: 'course-2',
      title: '1. Telegram WebApp SDK ga kirish',
      order_index: 1,
      duration_sec: 540,
      is_free_preview: true,
      unlocked: true,
      description: 'WebApp muhiti, MainButton, BackButton va HapticFeedback sozlamalari.',
      video_url_sample: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4',
    },
    {
      id: 'l-202',
      course_id: 'course-2',
      title: '2. InitData orqali xavfsiz API so\'rovlar',
      order_index: 2,
      duration_sec: 680,
      is_free_preview: false,
      unlocked: true,
      description: 'X-Telegram-Init-Data bilan foydalanuvchi ma\'lumotlarini tasdiqlash.',
      video_url_sample: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WhatCarCanYouGetForAGrand.mp4',
    },
    {
      id: 'l-203',
      course_id: 'course-2',
      title: '3. Tailwind CSS & Telegram ThemeParams',
      order_index: 3,
      duration_sec: 760,
      is_free_preview: false,
      unlocked: false,
      description: 'Mavzularni sinxronlashtirish va toza mobil interfeys yaratish.',
      video_url_sample: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
    },
  ],
};

function defaultMockLessons(courseId: string | number): Lesson[] {
  return [
    {
      id: `l-${courseId}-1`,
      course_id: courseId,
      title: '1. Kursga kirish va asosiy tushunchalar',
      order_index: 1,
      duration_sec: 600,
      is_free_preview: true,
      unlocked: true,
      description: 'Kurs dasturi va talab qilinadigan vositalar bilan tanishuv.',
      video_url_sample: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
    },
    {
      id: `l-${courseId}-2`,
      course_id: courseId,
      title: '2. Dastlabki amaliy mashg\'ulot',
      order_index: 2,
      duration_sec: 900,
      is_free_preview: false,
      unlocked: false,
      description: 'Nazariy bilimlarni mustahkamlash uchun amaliy topshiriqlar.',
      video_url_sample: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4',
    },
  ];
}

export const mockCabinets: Cabinet[] = [
  {
    id: 'cab-1',
    display_name: 'Python Guruhi (Kuz-2026)',
    role_in_cabinet: 'mentor',
    avatar: '🐍',
    unread_count: 2,
  },
  {
    id: 'cab-2',
    display_name: 'Frontend Mini Apps Jamiyati',
    role_in_cabinet: 'student',
    avatar: '⚡',
    unread_count: 0,
  },
];

export const mockStudents: CabinetStudent[] = [
  {
    id: 'st-1',
    full_name: 'Sardorbek Olimov',
    telegram_id: 987654321,
    joined_at: '2026-08-01T10:00:00Z',
    username: 'sardor_dev',
  },
  {
    id: 'st-2',
    full_name: 'Nilufar Yusupova',
    telegram_id: 876543210,
    joined_at: '2026-08-03T14:30:00Z',
    username: 'nilufar_y',
  },
  {
    id: 'st-3',
    full_name: 'Rustam Qodirov',
    telegram_id: 765432109,
    joined_at: '2026-08-05T09:15:00Z',
    username: 'rustam_q',
  },
];

const mockChatStore: Record<string, ChatMessage[]> = {};

function defaultMockMessages(): ChatMessage[] {
  return [
    {
      id: 'msg-1',
      sender_id: 999111,
      sender_name: 'Javohir Mentor',
      content: 'Assalomu alaykum talabalar! Bugungi dars bo\'yicha savollaringiz bo\'lsa bemalol yozishingiz mumkin.',
      sent_at: '2026-08-15T08:00:00Z',
      is_me: false,
      role: 'mentor',
    },
    {
      id: 'msg-2',
      sender_id: 987654321,
      sender_name: 'Sardorbek Olimov',
      content: 'Ustoz, 3-darsdagi dependency injection qismida token muddati qanday tekshiriladi?',
      sent_at: '2026-08-15T08:15:00Z',
      is_me: false,
      role: 'student',
    },
    {
      id: 'msg-3',
      sender_id: 999111,
      sender_name: 'Javohir Mentor',
      content: 'FastAPI Depends() ichida decode_token orqali payload exp tekshiriladi. Dars materiallariga misol kodi ilova qilingan!',
      sent_at: '2026-08-15T08:18:00Z',
      is_me: false,
      role: 'mentor',
      reply_to: {
        message_id: 'msg-2',
        sender_name: 'Sardorbek Olimov',
        content: 'Ustoz, 3-darsdagi dependency injection qismida token muddati qanday tekshiriladi?',
      },
    },
  ];
}

export const mockLiveSessions: Record<string, LiveSession[]> = {
  'course-1': [
    {
      id: 'live-101',
      course_id: 'course-1',
      title: 'FastAPI va Real-world Microservices Savol-Javob',
      scheduled_at: '2026-08-15T19:00:00+05:00',
      status: 'live', // Currently LIVE
      join_method: 'webrtc_stream',
      instructor_name: 'Javohir Toshpo\'latov',
    },
    {
      id: 'live-102',
      course_id: 'course-1',
      title: 'Telegram Bot Webhook xavfsizligi va SSL',
      scheduled_at: '2026-08-18T20:00:00+05:00',
      status: 'scheduled',
      join_method: 'webrtc_stream',
      instructor_name: 'Javohir Toshpo\'latov',
    },
    {
      id: 'live-103',
      course_id: 'course-1',
      title: 'PostgreSQL Optimizatsiya va Indekslar',
      scheduled_at: '2026-08-10T19:00:00+05:00',
      status: 'ended',
      join_method: 'webrtc_stream',
      instructor_name: 'Javohir Toshpo\'latov',
    },
  ],
  'course-2': [
    {
      id: 'live-201',
      course_id: 'course-2',
      title: 'Telegram Mini Apps UI UX masterclass',
      scheduled_at: '2026-08-16T18:00:00+05:00',
      status: 'scheduled',
      join_method: 'webrtc_stream',
      instructor_name: 'Madina Karimova',
    },
  ],
};

function defaultLiveSessions(courseId: string | number): LiveSession[] {
  return [
    {
      id: `live-${courseId}-1`,
      course_id: courseId,
      title: 'Mentor bilan jonli savol-javob sessiyasi',
      scheduled_at: '2026-08-17T19:00:00+05:00',
      status: 'scheduled',
      join_method: 'webrtc_stream',
      instructor_name: 'Kurs Mentori',
    },
  ];
}

export const mockCourseProgress: Record<string, CourseProgressItem[]> = {
  'course-1': [
    {
      lesson_id: 'l-101',
      title: '1. Kirish: Python va FastAPI nima uchun kerak?',
      completion_percent: 100,
      watch_duration_sec: 480,
      started_at: '2026-08-14T10:00:00Z',
    },
    {
      lesson_id: 'l-102',
      title: '2. Pydantic modellari va Request Validatsiyasi',
      completion_percent: 100,
      watch_duration_sec: 720,
      started_at: '2026-08-14T15:30:00Z',
    },
    {
      lesson_id: 'l-103',
      title: '3. Dependency Injection va Telegram Auth Headers',
      completion_percent: 45,
      watch_duration_sec: 405,
      started_at: '2026-08-15T07:10:00Z',
    },
  ],
  'course-2': [
    {
      lesson_id: 'l-201',
      title: '1. Telegram WebApp SDK ga kirish',
      completion_percent: 100,
      watch_duration_sec: 540,
      started_at: '2026-08-12T09:00:00Z',
    },
  ],
};

function defaultCourseProgress(courseId: string | number): CourseProgressItem[] {
  return [
    {
      lesson_id: `l-${courseId}-1`,
      title: '1. Kursga kirish va asosiy tushunchalar',
      completion_percent: 100,
      watch_duration_sec: 600,
      started_at: '2026-08-15T06:00:00Z',
    },
  ];
}

export const mockMentors: MentorInfo[] = [
  {
    id: 'mentor-1',
    name: 'Javohir Toshpo\'latov',
    username: '@javohir_dev',
    avatar: '🐍',
    specialty: 'Python & FastAPI Backend',
    total_students: 4,
    active_groups: 2,
    rating: 4.9,
  },
  {
    id: 'mentor-2',
    name: 'Madina Karimova',
    username: '@madina_ui',
    avatar: '🎨',
    specialty: 'Telegram Mini Apps & React',
    total_students: 3,
    active_groups: 1,
    rating: 4.8,
  },
  {
    id: 'mentor-3',
    name: 'Bobur Ismoilov',
    username: '@bobur_mobile',
    avatar: '📱',
    specialty: 'Flutter & Dart Mobile',
    total_students: 3,
    active_groups: 1,
    rating: 4.9,
  },
];

export const mockAllStudentsActivity: CabinetActivityItem[] = [
  // Javohir Toshpo'latov (mentor-1) o'quvchilari
  {
    user_id: 'st-1',
    full_name: 'Sardorbek Olimov',
    telegram_id: 987654321,
    username: '@sardor_dev',
    lessons_watched: 5,
    last_activity: '10 daqiqa oldin',
    progress_percent: 83,
    cabinet_id: 'cab-1',
    cabinet_name: 'Python Guruhi (Kuz-2026)',
    mentor_id: 'mentor-1',
    mentor_name: 'Javohir Toshpo\'latov',
    course_title: 'Python Backend: FastAPI & Microservices',
    status: 'active',
  },
  {
    user_id: 'st-2',
    full_name: 'Nilufar Yusupova',
    telegram_id: 876543210,
    username: '@nilufar_y',
    lessons_watched: 3,
    last_activity: '1 soat oldin',
    progress_percent: 50,
    cabinet_id: 'cab-1',
    cabinet_name: 'Python Guruhi (Kuz-2026)',
    mentor_id: 'mentor-1',
    mentor_name: 'Javohir Toshpo\'latov',
    course_title: 'Python Backend: FastAPI & Microservices',
    status: 'active',
  },
  {
    user_id: 'st-3',
    full_name: 'Rustam Qodirov',
    telegram_id: 765432109,
    username: '@rustam_q',
    lessons_watched: 2,
    last_activity: 'Kecha 18:45',
    progress_percent: 33,
    cabinet_id: 'cab-1',
    cabinet_name: 'Python Guruhi (Kuz-2026)',
    mentor_id: 'mentor-1',
    mentor_name: 'Javohir Toshpo\'latov',
    course_title: 'Python Backend: FastAPI & Microservices',
    status: 'active',
  },
  {
    user_id: 'st-4',
    full_name: 'Diyorbek Mahmudov',
    telegram_id: 654321098,
    username: '@diyor_m',
    lessons_watched: 6,
    last_activity: 'Bugun 11:20',
    progress_percent: 100,
    cabinet_id: 'cab-1',
    cabinet_name: 'Python Guruhi (Kuz-2026)',
    mentor_id: 'mentor-1',
    mentor_name: 'Javohir Toshpo\'latov',
    course_title: 'Python Backend: FastAPI & Microservices',
    status: 'graduated',
  },

  // Madina Karimova (mentor-2) o'quvchilari
  {
    user_id: 'st-5',
    full_name: 'Shahzod Aliyev',
    telegram_id: 543210987,
    username: '@shahzod_al',
    lessons_watched: 4,
    last_activity: '25 daqiqa oldin',
    progress_percent: 75,
    cabinet_id: 'cab-2',
    cabinet_name: 'Frontend Mini Apps Jamiyati',
    mentor_id: 'mentor-2',
    mentor_name: 'Madina Karimova',
    course_title: 'Telegram Mini Apps: React & Tailwind Pro',
    status: 'active',
  },
  {
    user_id: 'st-6',
    full_name: 'Malika Sobirova',
    telegram_id: 432109876,
    username: '@malika_s',
    lessons_watched: 5,
    last_activity: 'Bugun 14:00',
    progress_percent: 100,
    cabinet_id: 'cab-2',
    cabinet_name: 'Frontend Mini Apps Jamiyati',
    mentor_id: 'mentor-2',
    mentor_name: 'Madina Karimova',
    course_title: 'Telegram Mini Apps: React & Tailwind Pro',
    status: 'graduated',
  },
  {
    user_id: 'st-7',
    full_name: 'Azizbek Rahmonov',
    telegram_id: 321098765,
    username: '@aziz_rahmon',
    lessons_watched: 1,
    last_activity: '3 kun oldin',
    progress_percent: 20,
    cabinet_id: 'cab-2',
    cabinet_name: 'Frontend Mini Apps Jamiyati',
    mentor_id: 'mentor-2',
    mentor_name: 'Madina Karimova',
    course_title: 'Telegram Mini Apps: React & Tailwind Pro',
    status: 'inactive',
  },

  // Bobur Ismoilov (mentor-3) o'quvchilari
  {
    user_id: 'st-8',
    full_name: 'Jasur Ergashev',
    telegram_id: 210987654,
    username: '@jasur_erg',
    lessons_watched: 3,
    last_activity: '45 daqiqa oldin',
    progress_percent: 60,
    cabinet_id: 'cab-3',
    cabinet_name: 'Flutter Pro Mobilchilar',
    mentor_id: 'mentor-3',
    mentor_name: 'Bobur Ismoilov',
    course_title: 'Flutter & Dart: Cross-Platform Dasturlash',
    status: 'active',
  },
  {
    user_id: 'st-9',
    full_name: 'Farrux Toirov',
    telegram_id: 109876543,
    username: '@farrux_t',
    lessons_watched: 4,
    last_activity: 'Bugun 09:30',
    progress_percent: 80,
    cabinet_id: 'cab-3',
    cabinet_name: 'Flutter Pro Mobilchilar',
    mentor_id: 'mentor-3',
    mentor_name: 'Bobur Ismoilov',
    course_title: 'Flutter & Dart: Cross-Platform Dasturlash',
    status: 'active',
  },
  {
    user_id: 'st-10',
    full_name: 'Ziyoda Nurmatova',
    telegram_id: 998877665,
    username: '@ziyoda_n',
    lessons_watched: 5,
    last_activity: 'Kecha 20:10',
    progress_percent: 100,
    cabinet_id: 'cab-3',
    cabinet_name: 'Flutter Pro Mobilchilar',
    mentor_id: 'mentor-3',
    mentor_name: 'Bobur Ismoilov',
    course_title: 'Flutter & Dart: Cross-Platform Dasturlash',
    status: 'graduated',
  },
];

export const mockActivity: CabinetActivityItem[] = mockAllStudentsActivity;

export interface MentorApplicationPayload {
  full_name: string;
  phone: string;
  course_direction: string;
  experience_bio: string;
  telegram_username?: string;
}

export interface MyMentorApplicationResponse {
  application: {
    id: number;
    full_name: string;
    phone: string;
    course_direction: string;
    experience_bio: string;
    status: 'pending' | 'approved' | 'rejected';
    payment_amount: number;
    receipt_photo_id?: string;
    created_at: string;
  } | null;
  payment_amount?: number;
}

export async function submitMentorApplication(payload: MentorApplicationPayload): Promise<{ success: boolean; message: string }> {
  return request<{ success: boolean; message: string }>('/api/users/mentor-application', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchMyMentorApplication(): Promise<MyMentorApplicationResponse> {
  return request<MyMentorApplicationResponse>(
    '/api/users/mentor-application/my',
    { method: 'GET' },
    () => ({ application: null })
  );
}

// ==========================================
// 22. LESSON QUIZZES (Dars testlari)
// ==========================================

export interface MentorCardInfo {
  has_card: boolean;
  provider?: string;
  card_number_masked?: string;
  card_expire?: string;
  created_at?: string;
}

export interface CardBindInitiateResponse {
  status: string;
  card_token: string;
  provider?: string;
  message?: string;
}

export interface CardBindVerifyResponse {
  status: string;
  message: string;
  card_number?: string;
}

export async function fetchMyCard(): Promise<MentorCardInfo> {
  return request<MentorCardInfo>(
    '/api/cards/my-card',
    { method: 'GET' },
    () => ({ has_card: false })
  );
}

export async function initiateCardBind(payload: {
  provider: 'click' | 'payme';
  card_number: string;
  card_expire: string;
}): Promise<CardBindInitiateResponse> {
  return request<CardBindInitiateResponse>(
    '/api/cards/bind/initiate',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    }
  );
}

export async function verifyCardBind(payload: {
  provider: 'click' | 'payme';
  card_token: string;
  code: string;
  card_number_masked?: string;
  card_expire?: string;
}): Promise<CardBindVerifyResponse> {
  return request<CardBindVerifyResponse>(
    '/api/cards/bind/verify',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    }
  );
}

export async function unbindCard(): Promise<{ status: string; message: string }> {
  return request<{ status: string; message: string }>(
    '/api/cards/unbind',
    { method: 'POST' }
  );
}

export interface AdminOverviewStats {
  total_users: number;
  active_mentors: number;
  active_courses: number;
  total_sales_count: number;
  total_revenue: number;
  total_cabinets: number;
  total_views: number;
}

export async function fetchAdminOverview(): Promise<AdminOverviewStats> {
  return request<AdminOverviewStats>(
    '/api/analytics/overview',
    { method: 'GET' },
    () => ({
      total_users: 0,
      active_mentors: 0,
      active_courses: 0,
      total_sales_count: 0,
      total_revenue: 0,
      total_cabinets: 0,
      total_views: 0,
    })
  );
}

export interface LessonQuiz {
  id: number;
  lesson_id: number;
  question: string;
  options: string[];
}

export interface QuizSubmitResult {
  quiz_id: number;
  is_correct: boolean;
  correct_option_index: number;
  explanation: string;
  lesson_passed?: boolean;
}

export interface LessonQuizStatus {
  lesson_id: number;
  total_quizzes: number;
  passed_quizzes?: number;
  passed: boolean;
  has_quizzes?: boolean;
  attempts_count: number;
}

export async function fetchLessonQuizzes(lessonId: string | number): Promise<LessonQuiz[]> {
  const cleanId = cleanNumericId(lessonId);
  return request<LessonQuiz[]>(
    `/api/quizzes/lesson/${cleanId}`,
    { method: 'GET' },
    () => []
  );
}

export async function submitQuizAnswer(
  quizId: number,
  selectedOptionIndex: number
): Promise<QuizSubmitResult> {
  return request<QuizSubmitResult>(
    `/api/quizzes/${quizId}/submit`,
    {
      method: 'POST',
      body: JSON.stringify({ selected_option_index: selectedOptionIndex }),
    }
  );
}

export async function fetchLessonQuizStatus(
  lessonId: string | number
): Promise<LessonQuizStatus> {
  const cleanId = cleanNumericId(lessonId);
  return request<LessonQuizStatus>(
    `/api/quizzes/lesson/${cleanId}/status`,
    { method: 'GET' },
    () => ({ lesson_id: Number(cleanId), total_quizzes: 0, passed: true, attempts_count: 0 })
  );
}
