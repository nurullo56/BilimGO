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
let isConnectedToLiveBackend = false;

export function getApiBaseUrl(): string {
  return customApiBase;
}

export function setApiBaseUrl(url: string) {
  customApiBase = url.replace(/\/+$/, '');
}

export function getBackendStatus() {
  return {
    apiBase: customApiBase,
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
  
  let category = c.category || 'Amaliy Kurs';
  let thumbnail = c.thumbnail || 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800&auto=format&fit=crop&q=60';
  let instructor = c.instructor || 'Bosh Mentor';

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

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
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
    throw err;
  }
}

export async function fetchCourses(): Promise<Course[]> {
  const list = await request<Course[]>('/api/courses', { method: 'GET' });
  return (list || []).map(enhanceCourse);
}

export async function fetchCourseById(courseId: string | number): Promise<Course> {
  const cleanId = cleanNumericId(courseId);
  const course = await request<Course>(`/api/courses/${cleanId}`, { method: 'GET' });
  return enhanceCourse(course);
}

export async function fetchCourseLessons(courseId: string | number): Promise<Lesson[]> {
  const cleanId = cleanNumericId(courseId);
  const list = await request<Lesson[]>(`/api/courses/${cleanId}/lessons`, { method: 'GET' });
  return (list || []).map((item: any) => ({
    ...item,
    id: cleanNumericId(item.id),
    unlocked: Boolean(item.is_accessible ?? item.unlocked ?? item.is_free_preview),
    is_accessible: Boolean(item.is_accessible ?? item.unlocked ?? item.is_free_preview),
  }));
}

export async function fetchLessonAccessToken(lessonId: string | number): Promise<LessonAccessTokenResponse> {
  const cleanId = cleanNumericId(lessonId);
  return request<LessonAccessTokenResponse>(`/api/lessons/${cleanId}/access-token`, { method: 'POST' });
}

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
    }
  );
}

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
    { method: 'POST' }
  );
}

export async function fetchMyCabinets(): Promise<Cabinet[]> {
  return request<Cabinet[]>('/api/cabinets/me', { method: 'GET' });
}

export interface CreateCabinetPayload {
  display_name: string;
  avatar?: string;
  description?: string;
  course_id?: string | number;
  course_title?: string;
  initial_message?: string;
}

export async function createCabinet(payload: CreateCabinetPayload): Promise<Cabinet> {
  const cleanCourseId = payload.course_id ? cleanNumericId(payload.course_id) : undefined;
  return request<Cabinet>('/api/cabinets', {
    method: 'POST',
    body: JSON.stringify({ ...payload, course_id: cleanCourseId }),
  });
}

export async function updateCabinet(
  cabinetId: string | number,
  updates: Partial<Cabinet>
): Promise<Cabinet> {
  const cleanId = cleanNumericId(cabinetId);
  return request<Cabinet>(`/api/cabinets/${cleanId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
}

export async function deleteCabinet(cabinetId: string | number): Promise<{ success: boolean }> {
  const cleanId = cleanNumericId(cabinetId);
  return request<{ success: boolean }>(`/api/cabinets/${cleanId}`, { method: 'DELETE' });
}

export async function fetchCabinetStudents(cabinetId: string | number): Promise<CabinetStudent[]> {
  const cleanId = cleanNumericId(cabinetId);
  return request<CabinetStudent[]>(`/api/cabinets/${cleanId}/students`, { method: 'GET' });
}

export async function sendChatMessage(
  roomId: string | number,
  content: string,
  replyTo?: ChatReplyInfo
): Promise<ChatMessage> {
  const cleanRoomId = cleanNumericId(roomId);
  return request<ChatMessage>(`/api/chat/rooms/${cleanRoomId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ content, reply_to: replyTo }),
  });
}

export async function fetchChatMessages(
  roomId: string | number,
  afterId?: string | number | null
): Promise<ChatMessage[]> {
  const cleanRoomId = cleanNumericId(roomId);
  const cleanAfter = afterId ? cleanNumericId(afterId) : 0;
  const query = cleanAfter > 0 ? `?after_id=${cleanAfter}` : '';
  return request<ChatMessage[]>(`/api/chat/rooms/${cleanRoomId}/messages${query}`, { method: 'GET' });
}

export async function fetchLiveSessions(courseId: string | number): Promise<LiveSession[]> {
  const cleanId = cleanNumericId(courseId);
  return request<LiveSession[]>(`/api/live/courses/${cleanId}/sessions`, { method: 'GET' });
}

export async function joinLiveSession(sessionId: string | number): Promise<LiveJoinResponse> {
  const cleanId = cleanNumericId(sessionId);
  return request<LiveJoinResponse>(`/api/live/sessions/${cleanId}/join`, { method: 'POST' });
}

export async function leaveLiveSession(sessionId: string | number): Promise<{ success: boolean }> {
  const cleanId = cleanNumericId(sessionId);
  return request<{ success: boolean }>(`/api/live/sessions/${cleanId}/leave`, { method: 'POST' });
}

export async function fetchMyCourseProgress(courseId: string | number): Promise<CourseProgressItem[]> {
  const cleanId = cleanNumericId(courseId);
  return request<CourseProgressItem[]>(`/api/analytics/courses/${cleanId}/my-progress`, { method: 'GET' });
}

export async function fetchCabinetActivity(
  cabinetId?: string | number,
  mentorId?: string | number
): Promise<CabinetActivityItem[]> {
  const cleanCab = cabinetId && cabinetId !== 'all' ? cleanNumericId(cabinetId) : '';
  const cleanMentor = mentorId && mentorId !== 'all' ? cleanNumericId(mentorId) : '';
  return request<CabinetActivityItem[]>(
    `/api/analytics/cabinets/activity?cabinet_id=${cleanCab}&mentor_id=${cleanMentor}`,
    { method: 'GET' }
  );
}

export async function fetchMentorsList(): Promise<MentorInfo[]> {
  return request<MentorInfo[]>('/api/mentors', { method: 'GET' });
}

export async function fetchUserProfile(): Promise<UserProfile> {
  return request<UserProfile>('/api/users/profile', { method: 'GET' });
}

export async function updateUserProfile(updates: Partial<UserProfile>): Promise<UserProfile> {
  return request<UserProfile>('/api/users/profile', {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
}

export interface AskLessonAiPayload {
  lessonId?: string | number;
  courseTitle?: string;
  lessonTitle: string;
  lessonDescription?: string;
  question: string;
  history?: Array<{ sender: 'user' | 'assistant'; text: string }>;
}

export async function askLessonAi(payload: AskLessonAiPayload): Promise<{ answer: string }> {
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
  throw new Error('AI bilan ulanishda xatolik yuz berdi');
}
