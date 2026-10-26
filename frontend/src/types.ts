export interface Course {
  id: string | number;
  title: string;
  base_price: number;
  owner_node_id: string | number;
  description?: string;
  category?: string;
  instructor?: string;
  thumbnail?: string;
  total_lessons?: number;
  total_duration_minutes?: number;
  is_enrolled?: boolean;
  has_access?: boolean;
}

export interface Lesson {
  id: string | number;
  course_id?: string | number;
  title: string;
  order_index: number;
  duration_sec: number;
  is_free_preview: boolean;
  is_accessible?: boolean;
  unlocked?: boolean;
  description?: string;
  video_url_sample?: string;
  completion_percent?: number;
  watch_duration_sec?: number;
}

export interface LessonAccessTokenResponse {
  stream_url: string;
  expires_at: string;
  media_type?: string;
  is_audio?: boolean;
  is_text?: boolean;
  slide_url?: string;
  images?: string[];
  text_content?: string;
}

export interface PurchaseInitiateResponse {
  sale_id: string | number;
  amount: number;
}

export interface Cabinet {
  id: string | number;
  display_name: string;
  role_in_cabinet: 'mentor' | 'student' | string;
  avatar?: string;
  unread_count?: number;
  course_id?: string | number;
  course_title?: string;
  description?: string;
  created_at?: string;
  mentor_name?: string;
  students_count?: number;
}

export interface CabinetStudent {
  id: string | number;
  full_name: string;
  telegram_id: number | string;
  joined_at: string;
  username?: string;
  avatar?: string;
}

export interface ChatReplyInfo {
  message_id: string | number;
  sender_name: string;
  content: string;
}

export interface ChatMessage {
  id: string | number;
  sender_id: string | number;
  sender_name?: string;
  content: string;
  sent_at: string;
  is_me?: boolean;
  role?: string;
  reply_to?: ChatReplyInfo;
}

export type LiveSessionStatus = 'scheduled' | 'live' | 'ended' | 'cancelled';

export interface LiveSession {
  id: string | number;
  course_id?: string | number;
  title?: string;
  scheduled_at: string;
  status: LiveSessionStatus;
  join_method: string;
  stream_ref?: string;
  instructor_name?: string;
}

export interface LiveJoinResponse {
  stream_ref: string;
  join_method: string;
}

export interface CourseProgressItem {
  lesson_id: string | number;
  title: string;
  completion_percent: number;
  watch_duration_sec: number;
  started_at: string;
}

export interface CabinetActivityItem {
  user_id: string | number;
  full_name: string;
  telegram_id: number | string;
  username?: string;
  avatar?: string;
  lessons_watched: number;
  last_activity: string;
  progress_percent?: number;
  cabinet_id?: string | number;
  cabinet_name?: string;
  mentor_id?: string | number;
  mentor_name?: string;
  course_title?: string;
  status?: 'active' | 'graduated' | 'inactive';
}

export type UserRole = 'student' | 'mentor' | 'super_mentor' | 'admin';

export interface MentorInfo {
  id: string | number;
  name: string;
  username?: string;
  avatar?: string;
  specialty: string;
  total_students: number;
  active_groups: number;
  rating?: number;
}

export interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  language_code?: string;
}

export interface UserProfile {
  id: string | number;
  telegram_id: number | string;
  first_name: string;
  last_name?: string;
  username?: string;
  phone?: string;
  avatar?: string;
  role: UserRole;
  is_admin?: boolean;
  assigned_mentor_id?: string | number;
  enrolled_courses_count: number;
  completed_lessons_count: number;
  total_study_time_minutes: number;
  streak_days: number;
  joined_date: string;
  wallet_balance?: number;
  certificate_count?: number;
}

export type AppView = 
  | { type: 'catalog' }
  | { type: 'course'; courseId: string | number }
  | { type: 'lesson'; courseId: string | number; lessonId: string | number }
  | { type: 'my-courses' }
  | { type: 'cabinet'; cabinetId?: string | number }
  | { type: 'live'; courseId: string | number }
  | { type: 'live-stream'; sessionId: string | number; courseId: string | number }
  | { type: 'mentor-stats'; cabinetId?: string | number; mentorId?: string | number }
  | { type: 'admin-dashboard' }
  | { type: 'profile' };
