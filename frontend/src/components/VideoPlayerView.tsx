import React, { useState, useEffect, useRef } from 'react';
import {
  ArrowLeft,
  Award,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  Copy,
  FileText,
  Headphones,
  Home,
  ImageIcon,
  Lock,
  Pause,
  Play,
  RotateCcw,
  RotateCw,
  Sparkles,
  Video as VideoIcon,
  X,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  Mic,
} from 'lucide-react';
import { Lesson, Course, AppView } from '../types';
import {
  fetchCourseById,
  fetchCourseLessons,
  fetchLessonAccessToken,
  fetchLessonQuizzes,
  LessonQuiz,
  fetchUserProfile,
  getApiBaseUrl,
  updateLessonProgress,
} from '../services/api';
import { triggerHaptic, getTelegramUser } from '../services/telegram';
import { LessonAiAssistant } from './LessonAiAssistant';
import { LessonQuizCard } from './LessonQuizCard';
import { FeedbackModal } from './FeedbackModal';
import { VoiceReportModal } from './VoiceReportModal';
import { TgText } from './TgEmoji';

interface VideoPlayerViewProps {
  courseId: string | number;
  lessonId: string | number;
  onNavigate: (view: AppView) => void;
  onSelectLesson: (courseId: string | number, lessonId: string | number) => void;
}

export const VideoPlayerView: React.FC<VideoPlayerViewProps> = ({
  courseId,
  lessonId,
  onNavigate,
  onSelectLesson,
}) => {
  const [course, setCourse] = useState<Course | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [currentLesson, setCurrentLesson] = useState<Lesson | null>(null);
  const [streamUrl, setStreamUrl] = useState<string | null>(null);
  const [lessonImages, setLessonImages] = useState<string[]>([]);
  const [activeImageIdx, setActiveImageIdx] = useState<number>(0);
  const [isAudio, setIsAudio] = useState(false);
  const [forceMode, setForceMode] = useState<'auto' | 'video' | 'audio'>('auto');
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [progressPercent, setProgressPercent] = useState<number>(0);
  const [isCompleted, setIsCompleted] = useState<boolean>(false);
  const [quizzes, setQuizzes] = useState<LessonQuiz[]>([]);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [textContent, setTextContent] = useState<string | null>(null);
  const [isTextLesson, setIsTextLesson] = useState(false);
  const [copiedTemplate, setCopiedTemplate] = useState(false);
  const [showCourseCompletedModal, setShowCourseCompletedModal] = useState(false);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [showVoiceModal, setShowVoiceModal] = useState(false);
  const [feedbackReaction, setFeedbackReaction] = useState<'like' | 'dislike' | null>(null);
  const [watermarkPos, setWatermarkPos] = useState({ top: '25%', left: '20%' });
  const [studentProfile, setStudentProfile] = useState<any>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const lastReportedTimeRef = useRef<number>(0);
  const quizSectionRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    fetchUserProfile().then((p) => setStudentProfile(p)).catch(() => {});
    // Anti-Piracy: Har 6 soniyada vatermarka joylashuvini tasodifiy o'zgartirib turish
    const timer = setInterval(() => {
      const randomTop = Math.floor(15 + Math.random() * 65) + '%';
      const randomLeft = Math.floor(10 + Math.random() * 55) + '%';
      setWatermarkPos({ top: randomTop, left: randomLeft });
    }, 6000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    loadPlayerContext();
  }, [courseId, lessonId]);

  const loadPlayerContext = async () => {
    setLoading(true);
    setError(null);
    setStreamUrl(null);
    setLessonImages([]);
    setTextContent(null);
    setIsTextLesson(false);
    setCopiedTemplate(false);
    setShowCourseCompletedModal(false);
    setActiveImageIdx(0);
    setIsPlaying(false);
    setCurrentTime(0);
    setDuration(0);
    setProgressPercent(0);
    setIsCompleted(false);
    setQuizzes([]);
    lastReportedTimeRef.current = 0;

    try {
      const [courseData, lessonsData] = await Promise.all([
        fetchCourseById(courseId),
        fetchCourseLessons(courseId),
      ]);
      setCourse(courseData);
      setLessons(lessonsData);

      const target = lessonsData.find((l) => String(l.id) === String(lessonId));
      if (!target) {
        throw new Error('Dars topilmadi');
      }
      setCurrentLesson(target);
      if (target.completion_percent) {
        setProgressPercent(target.completion_percent);
        setIsCompleted(target.completion_percent >= 90);
      }

      fetchLessonQuizzes(lessonId)
        .then((q) => setQuizzes(q || []))
        .catch(() => setQuizzes([]));

      // Fetch Access Token & Media metadata
      const tokenRes = await fetchLessonAccessToken(lessonId);
      
      const isText = Boolean(
        tokenRes.is_text ||
        (tokenRes.text_content && (!tokenRes.stream_url || tokenRes.media_type === 'text/plain'))
      );
      setIsTextLesson(isText);

      let fullUrl = tokenRes.stream_url || '';
      if (fullUrl && !fullUrl.startsWith('http://') && !fullUrl.startsWith('https://')) {
        fullUrl = `${getApiBaseUrl()}${fullUrl.startsWith('/') ? '' : '/'}${fullUrl}`;
      }
      setStreamUrl(isText ? '' : fullUrl);
      
      if (tokenRes.images && Array.isArray(tokenRes.images)) {
        setLessonImages(tokenRes.images);
      }

      if (tokenRes.text_content) {
        setTextContent(tokenRes.text_content);
      } else if (target.description) {
        setTextContent(target.description);
      }

      if (isText) {
        setProgressPercent(100);
        setIsCompleted(true);
      }

      const isAudioDetected = Boolean(
        tokenRes.is_audio ||
        tokenRes.media_type?.startsWith('audio/') ||
        tokenRes.media_type === 'application/ogg' ||
        tokenRes.media_type === 'audio/ogg' ||
        tokenRes.media_type === 'audio/opus' ||
        fullUrl.endsWith('.ogg') ||
        fullUrl.endsWith('.oga') ||
        fullUrl.endsWith('.mp3')
      );
      setIsAudio(isAudioDetected);
    } catch (err: any) {
      if (err.message && (err.message.includes('403') || err.message.includes('ruxsatingiz yo\'q'))) {
        setError('403: Bu darsga hali ruxsatingiz yo\'q. Kunlik o\'quv limitingizga muvofiq keyinroq ochiladi.');
      } else {
        setError(err.message || 'Video stream yuklanishida xatolik yuz berdi');
      }
    } finally {
      setLoading(false);
    }
  };

  // Real-time backend progress reporter (throttled every 4 seconds or on pause/finish)
  const reportProgress = (curTime: number, dur: number, force = false) => {
    if (dur <= 0 && (!currentLesson?.duration_sec || currentLesson.duration_sec <= 0)) return;
    const totalSecs = dur > 0 ? dur : (currentLesson?.duration_sec || 60);
    const calculatedPercent = Math.min(100, Math.max(0, Math.round((curTime / totalSecs) * 100)));

    setProgressPercent((prev) => Math.max(prev, calculatedPercent));

    if (calculatedPercent >= 90 && !isCompleted) {
      setIsCompleted(true);
      triggerHaptic('success');
      if (quizzes.length > 0) {
        setTimeout(() => {
          quizSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 400);
      } else {
        const currIdx = lessons.findIndex((l) => String(l.id) === String(lessonId));
        if (currIdx !== -1 && currIdx === lessons.length - 1 && lessons.length > 0) {
          setShowCourseCompletedModal(true);
        }
      }
    }

    if (force || Math.abs(curTime - lastReportedTimeRef.current) >= 4) {
      lastReportedTimeRef.current = curTime;
      updateLessonProgress(lessonId, {
        watch_duration_sec: Math.round(curTime),
        completion_percent: calculatedPercent,
      }).catch(console.warn);
    }
  };

  const toggleAudioPlay = () => {
    if (!audioRef.current) return;
    triggerHaptic('light');
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch(console.error);
    }
  };

  const handleAudioSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value);
    setCurrentTime(val);
    if (audioRef.current) {
      audioRef.current.currentTime = val;
      reportProgress(val, duration, true);
    }
  };

  const handleRateChange = () => {
    triggerHaptic('selection');
    const rates = [1, 1.25, 1.5, 2];
    const nextRate = rates[(rates.indexOf(playbackRate) + 1) % rates.length];
    setPlaybackRate(nextRate);
    if (audioRef.current) {
      audioRef.current.playbackRate = nextRate;
    }
    if (videoRef.current) {
      videoRef.current.playbackRate = nextRate;
    }
  };

  const skipAudio = (seconds: number) => {
    triggerHaptic('light');
    if (audioRef.current) {
      const targetTime = Math.max(0, Math.min(duration, audioRef.current.currentTime + seconds));
      audioRef.current.currentTime = targetTime;
      setCurrentTime(targetTime);
      reportProgress(targetTime, duration, true);
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const currentIndex = lessons.findIndex((l) => String(l.id) === String(lessonId));
  const prevLesson = currentIndex > 0 ? lessons[currentIndex - 1] : null;
  const nextLesson = currentIndex !== -1 && currentIndex < lessons.length - 1 ? lessons[currentIndex + 1] : null;
  const isLastLesson = lessons.length > 0 && (currentIndex === lessons.length - 1 || !nextLesson);

  const activeIsAudio = forceMode === 'audio' ? true : forceMode === 'video' ? false : isAudio;

  return (
    <div className="space-y-3.5 pb-28 max-w-3xl mx-auto px-4 pt-1 animate-in fade-in duration-200">
      {/* Course Completed Celebration Modal */}
      {showCourseCompletedModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-300">
          <div className="bg-tg-section border border-tg-secondary rounded-3xl p-6 max-w-sm w-full shadow-2xl text-center space-y-4 animate-in zoom-in-95 duration-200 relative overflow-hidden">
            {/* Background Glow */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-48 h-48 bg-gradient-to-b from-amber-500/20 via-emerald-500/10 to-transparent rounded-full blur-2xl pointer-events-none" />

            {/* Close Button */}
            <button
              onClick={() => setShowCourseCompletedModal(false)}
              className="absolute top-4 right-4 p-1.5 rounded-full bg-tg-secondary text-tg-hint hover:text-tg-text transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Trophy / Award Icon */}
            <div className="relative inline-flex items-center justify-center pt-2">
              <div className="w-20 h-20 rounded-3xl bg-gradient-to-tr from-amber-500 to-emerald-500 p-0.5 shadow-xl shadow-amber-500/20">
                <div className="w-full h-full bg-tg-section rounded-[22px] flex items-center justify-center text-amber-500">
                  <Award className="w-10 h-10 stroke-[2.2]" />
                </div>
              </div>
              <span className="absolute -top-0 -right-1 text-2xl">✨</span>
            </div>

            {/* Title & Congratulations */}
            <div className="space-y-1.5 relative z-10">
              <span className="text-[11px] font-extrabold uppercase tracking-widest text-emerald-500 block">
                Kurs to'liq yakunlandi!
              </span>
              <h2 className="text-xl font-black text-tg-text tracking-tight">
                Tabriklaymiz! 🎉
              </h2>
              <p className="text-xs text-tg-hint leading-relaxed px-1">
                Siz <strong className="text-tg-text font-bold">"{course?.title || 'Kurs'}"</strong> kursining barcha darslarini muvaffaqiyatli tugatdingiz!
              </p>
            </div>

            {/* Stats Summary Pill */}
            <div className="grid grid-cols-2 gap-2 p-3 bg-tg-secondary/60 rounded-2xl border border-tg-secondary relative z-10">
              <div className="text-center">
                <span className="text-[10px] text-tg-hint font-semibold block">Darslar</span>
                <span className="text-sm font-black text-tg-text">{lessons.length} ta dars</span>
              </div>
              <div className="text-center border-l border-tg-secondary">
                <span className="text-[10px] text-tg-hint font-semibold block">Natija</span>
                <span className="text-sm font-black text-emerald-500">100% Tugallandi</span>
              </div>
            </div>

            {/* Action Navigation Buttons */}
            <div className="space-y-2 pt-1 relative z-10">
              <button
                onClick={() => {
                  triggerHaptic('medium');
                  setShowCourseCompletedModal(false);
                  onNavigate({ type: 'catalog' });
                }}
                className="w-full py-3 px-4 rounded-2xl bg-blue-600 hover:bg-blue-500 active:scale-98 text-white font-extrabold text-xs sm:text-sm shadow-lg shadow-blue-600/30 flex items-center justify-center gap-2 cursor-pointer transition-all"
              >
                <Home className="w-4 h-4" />
                <span>Bosh sahifaga qaytish</span>
              </button>

              <button
                onClick={() => {
                  triggerHaptic('light');
                  setShowCourseCompletedModal(false);
                  onNavigate({ type: 'my-courses' });
                }}
                className="w-full py-2.5 px-4 rounded-2xl bg-tg-secondary hover:bg-tg-secondary/80 text-tg-text font-bold text-xs flex items-center justify-center gap-2 cursor-pointer transition-all"
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>Mening kurslarim</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Navigation & Mode Selector Bar */}
      <div className="flex items-center justify-between px-1">
        <button
          onClick={() => onNavigate({ type: 'course', courseId })}
          className="flex items-center gap-1.5 text-xs font-semibold text-tg-hint hover:text-tg-text transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Kursga qaytish</span>
        </button>

        {/* Video / Audio Mode Toggle */}
        {!isTextLesson ? (
          <div className="flex items-center bg-tg-secondary p-0.5 rounded-xl border border-tg-secondary">
            <button
              onClick={() => {
                triggerHaptic('selection');
                setForceMode('video');
              }}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                !activeIsAudio
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-tg-hint hover:text-tg-text'
              }`}
            >
              <VideoIcon className="w-3.5 h-3.5" />
              <span>Video</span>
            </button>
            <button
              onClick={() => {
                triggerHaptic('selection');
                setForceMode('audio');
              }}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                activeIsAudio
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-tg-hint hover:text-tg-text'
              }`}
            >
              <Headphones className="w-3.5 h-3.5" />
              <span>Ovozli</span>
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-blue-500/15 text-blue-600 dark:text-blue-400 text-xs font-bold border border-blue-500/20">
            <FileText className="w-3.5 h-3.5" />
            <span>Matnli dars</span>
          </div>
        )}
      </div>

      {/* Player Stage */}
      <div className="relative w-full rounded-[28px] overflow-hidden shadow-2xl border border-blue-900/30 flex items-center justify-center bg-gradient-to-b from-[#0e1626] to-[#080d1a]">
        {loading ? (
          <div className="flex flex-col items-center justify-center gap-3 py-16 text-white aspect-video">
            <div className="w-8 h-8 border-3 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
            <span className="text-xs font-medium text-white/80">
              Dars oqimi ulanmoqda...
            </span>
          </div>
        ) : error ? (
          <div className="p-6 text-center text-white space-y-3 max-w-sm py-12 aspect-video flex flex-col justify-center items-center">
            <div className="w-12 h-12 rounded-full bg-rose-500/20 text-rose-400 mx-auto flex items-center justify-center">
              <Lock className="w-6 h-6" />
            </div>
            <p className="text-xs sm:text-sm font-semibold text-rose-300">
              {error}
            </p>
            <button
              onClick={() => onNavigate({ type: 'course', courseId })}
              className="px-4 py-2 rounded-xl bg-white/20 hover:bg-white/30 text-white text-xs font-bold transition-all cursor-pointer"
            >
              Kursga qaytish
            </button>
          </div>
        ) : isTextLesson && textContent ? (
          /* Dedicated Full Text / Template Lesson View in Main Stage */
          <div className="w-full p-4 sm:p-6 text-white space-y-4 max-h-[75vh] overflow-y-auto">
            <div className="flex items-center justify-between gap-3 border-b border-white/10 pb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-blue-600/30 border border-blue-500/30 flex items-center justify-center text-blue-400">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] font-extrabold uppercase tracking-widest text-blue-400 block">
                    MATNLI DARS & AMALIY QO'LLANMA
                  </span>
                  <h3 className="text-sm sm:text-base font-bold text-white truncate">
                    <TgText>{currentLesson?.title}</TgText>
                  </h3>
                </div>
              </div>

              <button
                onClick={() => {
                  triggerHaptic('light');
                  navigator.clipboard.writeText(textContent);
                  setCopiedTemplate(true);
                  setTimeout(() => setCopiedTemplate(false), 2500);
                  reportProgress(100, 100, true);
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 active:scale-95 text-white text-xs font-bold transition-all cursor-pointer shadow-md shrink-0"
                title="Shablonni nusxalash"
              >
                {copiedTemplate ? (
                  <>
                    <Check className="w-3.5 h-3.5" />
                    <span>Nusxalandi!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Nusxalash</span>
                  </>
                )}
              </button>
            </div>

            {lessonImages.length > 0 && (
              <div className="relative w-full rounded-2xl overflow-hidden bg-black/60 border border-white/10 shadow-lg my-2">
                <img
                  src={
                    lessonImages[activeImageIdx].startsWith('http')
                      ? lessonImages[activeImageIdx]
                      : `${getApiBaseUrl()}${lessonImages[activeImageIdx].startsWith('/') ? '' : '/'}${lessonImages[activeImageIdx]}`
                  }
                  alt={currentLesson?.title || 'Dars rasmi'}
                  className="w-full max-h-64 object-contain mx-auto"
                />
              </div>
            )}

            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 text-xs sm:text-sm text-white/95 leading-relaxed whitespace-pre-line font-sans select-text shadow-inner">
              {textContent}
            </div>
          </div>
        ) : streamUrl && activeIsAudio ? (
          /* Dedicated Audio Voice Player with Attached Infographic Image */
          <div className="w-full p-4 sm:p-6 space-y-4 text-white">
            <audio
              ref={audioRef}
              src={streamUrl}
              autoPlay
              onPlay={() => setIsPlaying(true)}
              onPause={() => {
                setIsPlaying(false);
                if (audioRef.current) {
                  reportProgress(audioRef.current.currentTime, duration, true);
                }
              }}
              onTimeUpdate={() => {
                if (audioRef.current) {
                  const cur = audioRef.current.currentTime;
                  setCurrentTime(cur);
                  reportProgress(cur, duration);
                }
              }}
              onLoadedMetadata={() => {
                if (audioRef.current) {
                  const dur = audioRef.current.duration || 0;
                  setDuration(dur);
                  audioRef.current.playbackRate = playbackRate;
                  if (currentLesson?.watch_duration_sec && currentLesson.watch_duration_sec > 0 && currentLesson.watch_duration_sec < dur) {
                    audioRef.current.currentTime = currentLesson.watch_duration_sec;
                    setCurrentTime(currentLesson.watch_duration_sec);
                  }
                }
              }}
              onEnded={() => {
                setIsPlaying(false);
                if (audioRef.current) {
                  reportProgress(duration, duration, true);
                }
                if (quizzes.length > 0) {
                  triggerHaptic('notification');
                  setTimeout(() => {
                    quizSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                  }, 400);
                }
              }}
            />

            {/* Audio Header & Title */}
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-10 h-10 rounded-2xl bg-blue-600/30 border border-blue-500/30 flex items-center justify-center shadow-lg shadow-blue-500/20 shrink-0">
                  <Headphones className="w-5 h-5 text-blue-400" />
                </div>
                <div className="min-w-0">
                  <span className="text-[10px] font-extrabold uppercase tracking-widest text-blue-400 block">
                    OVOZLI DARS & INFOGRAFIKA
                  </span>
                  <h3 className="text-sm sm:text-base font-bold text-white truncate">
                    <TgText>{currentLesson?.title}</TgText>
                  </h3>
                </div>
              </div>

              <button
                onClick={handleRateChange}
                className="px-2.5 py-1 rounded-xl bg-white/10 hover:bg-white/20 active:scale-95 text-xs font-bold text-white border border-white/10 transition-all cursor-pointer shrink-0"
              >
                {playbackRate}x
              </button>
            </div>

            {/* Attached Lesson Images / Infographics (if available) */}
            {lessonImages.length > 0 && (
              <div className="relative w-full rounded-2xl overflow-hidden bg-black/60 border border-white/10 shadow-lg group">
                <img
                  src={
                    lessonImages[activeImageIdx].startsWith('http')
                      ? lessonImages[activeImageIdx]
                      : `${getApiBaseUrl()}${lessonImages[activeImageIdx].startsWith('/') ? '' : '/'}${lessonImages[activeImageIdx]}`
                  }
                  alt={currentLesson?.title || 'Dars rasmi'}
                  className="w-full max-h-64 sm:max-h-80 object-contain mx-auto transition-transform duration-300 group-hover:scale-[1.02]"
                />
                
                {/* Multi-image thumbnail switcher dots */}
                {lessonImages.length > 1 && (
                  <div className="absolute bottom-2.5 inset-x-0 flex items-center justify-center gap-1.5 p-1 bg-black/60 backdrop-blur-xs rounded-full max-w-fit mx-auto border border-white/10">
                    {lessonImages.map((_, idx) => (
                      <button
                        key={idx}
                        onClick={() => setActiveImageIdx(idx)}
                        className={`h-2 rounded-full transition-all cursor-pointer ${
                          activeImageIdx === idx ? 'bg-blue-500 w-5' : 'bg-white/40 w-2 hover:bg-white/70'
                        }`}
                        title={`${idx + 1}-rasm`}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Glowing Equalizer Waveform */}
            <div className="flex items-center justify-center gap-1 sm:gap-1.5 h-12 py-1.5 px-3 bg-black/40 rounded-2xl border border-white/5 overflow-hidden shadow-inner">
              {[35, 60, 85, 45, 95, 55, 75, 40, 100, 65, 80, 30, 90, 70, 50, 85, 40, 95, 60, 75, 35, 80, 100, 45, 90, 65, 55, 85, 40, 70, 90, 50].map((height, i) => (
                <div
                  key={i}
                  className={`w-1 sm:w-1.5 rounded-full transition-all duration-150 ${
                    isPlaying
                      ? 'bg-gradient-to-t from-blue-600 to-blue-400 shadow-[0_0_8px_rgba(59,130,246,0.6)] animate-pulse'
                      : 'bg-white/20'
                  }`}
                  style={{
                    height: isPlaying ? `${Math.max(18, (height * (0.4 + Math.random() * 0.6)))}%` : `${height * 0.35}%`,
                    animationDelay: `${i * 35}ms`,
                  }}
                />
              ))}
            </div>

            {/* Progress Slider */}
            <div className="space-y-1.5">
              <input
                type="range"
                min={0}
                max={duration || 100}
                value={currentTime}
                onChange={handleAudioSeek}
                className="w-full h-1.5 bg-white/20 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
              <div className="flex justify-between text-[11px] font-mono text-white/60">
                <span>{formatTime(currentTime)}</span>
                <span>{formatTime(duration)}</span>
              </div>
            </div>

            {/* Playback Controls */}
            <div className="flex items-center justify-center gap-6 pt-1">
              <button
                onClick={() => skipAudio(-10)}
                className="w-10 h-10 rounded-full flex items-center justify-center hover:bg-white/10 active:scale-95 text-white/80 transition-all cursor-pointer"
                title="-10 soniya"
              >
                <RotateCcw className="w-5 h-5" />
              </button>

              <button
                onClick={toggleAudioPlay}
                className="w-14 h-14 rounded-full bg-blue-600 hover:bg-blue-500 active:scale-95 text-white flex items-center justify-center shadow-[0_0_25px_rgba(37,99,235,0.7)] transition-all cursor-pointer ring-4 ring-blue-500/20"
              >
                {isPlaying ? (
                  <Pause className="w-6 h-6 fill-current" />
                ) : (
                  <Play className="w-6 h-6 fill-current ml-0.5" />
                )}
              </button>

              <button
                onClick={() => skipAudio(10)}
                className="w-10 h-10 rounded-full flex items-center justify-center hover:bg-white/10 active:scale-95 text-white/80 transition-all cursor-pointer"
                title="+10 soniya"
              >
                <RotateCw className="w-5 h-5" />
              </button>
            </div>
          </div>
        ) : streamUrl ? (
          /* Standard Video Player */
          <video
            ref={videoRef}
            src={streamUrl}
            controls
            playsInline
            controlsList="nodownload"
            className="w-full h-full aspect-video object-contain"
            autoPlay
            onPlay={() => setIsPlaying(true)}
            onPause={() => {
              setIsPlaying(false);
              if (videoRef.current) {
                reportProgress(videoRef.current.currentTime, videoRef.current.duration || duration, true);
              }
            }}
            onTimeUpdate={() => {
              if (videoRef.current) {
                const cur = videoRef.current.currentTime;
                const dur = videoRef.current.duration || duration;
                setCurrentTime(cur);
                reportProgress(cur, dur);
              }
            }}
            onLoadedMetadata={(e) => {
              const vid = e.currentTarget;
              const dur = vid.duration || 0;
              setDuration(dur);
              vid.playbackRate = playbackRate;
              if (currentLesson?.watch_duration_sec && currentLesson.watch_duration_sec > 0 && currentLesson.watch_duration_sec < dur) {
                vid.currentTime = currentLesson.watch_duration_sec;
                setCurrentTime(currentLesson.watch_duration_sec);
              }
            }}
            onEnded={() => {
              setIsPlaying(false);
              if (videoRef.current) {
                const dur = videoRef.current.duration || duration;
                reportProgress(dur, dur, true);
              }
              if (quizzes.length > 0) {
                triggerHaptic('notification');
                setTimeout(() => {
                  quizSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 400);
              } else {
                const currIdx = lessons.findIndex((l) => String(l.id) === String(lessonId));
                if (currIdx !== -1 && currIdx === lessons.length - 1 && lessons.length > 0) {
                  setShowCourseCompletedModal(true);
                  triggerHaptic('success');
                }
              }
            }}
          >
            Sizning brauzeringiz HTML5 videoni qo'llab-quvvatlamaydi.
          </video>
        ) : textContent && (!streamUrl || !activeIsAudio) ? (
          /* Dedicated Full Text / Template Lesson View in Main Stage */
          <div className="w-full p-4 sm:p-6 text-white space-y-4 max-h-[75vh] overflow-y-auto">
            <div className="flex items-center justify-between gap-3 border-b border-white/10 pb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-blue-600/30 border border-blue-500/30 flex items-center justify-center text-blue-400">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] font-extrabold uppercase tracking-widest text-blue-400 block">
                    MATNLI DARS & AMALIY QO'LLANMA
                  </span>
                  <h3 className="text-sm sm:text-base font-bold text-white truncate">
                    <TgText>{currentLesson?.title}</TgText>
                  </h3>
                </div>
              </div>

              <button
                onClick={() => {
                  triggerHaptic('light');
                  navigator.clipboard.writeText(textContent);
                  setCopiedTemplate(true);
                  setTimeout(() => setCopiedTemplate(false), 2500);
                  reportProgress(100, 100, true);
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 active:scale-95 text-white text-xs font-bold transition-all cursor-pointer shadow-md shrink-0"
                title="Shablonni nusxalash"
              >
                {copiedTemplate ? (
                  <>
                    <Check className="w-3.5 h-3.5" />
                    <span>Nusxalandi!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Nusxalash</span>
                  </>
                )}
              </button>
            </div>

            {lessonImages.length > 0 && (
              <div className="relative w-full rounded-2xl overflow-hidden bg-black/60 border border-white/10 shadow-lg my-2">
                <img
                  src={
                    lessonImages[activeImageIdx].startsWith('http')
                      ? lessonImages[activeImageIdx]
                      : `${getApiBaseUrl()}${lessonImages[activeImageIdx].startsWith('/') ? '' : '/'}${lessonImages[activeImageIdx]}`
                  }
                  alt={currentLesson?.title || 'Dars rasmi'}
                  className="w-full max-h-64 object-contain mx-auto"
                />
              </div>
            )}

            <div className="p-4 rounded-2xl bg-white/5 border border-white/10 text-xs sm:text-sm text-white/95 leading-relaxed whitespace-pre-line font-sans select-text shadow-inner">
              {textContent}
            </div>
          </div>
        ) : null}

        {/* Anti-Piracy Floating Watermark (Identity Stamp on Screen Recording / External Camera) */}
        {!studentProfile?.is_admin && (
          <div
            className="pointer-events-none absolute z-30 transition-all duration-1000 ease-in-out select-none bg-black/65 backdrop-blur-xs border border-white/20 px-3 py-1.5 rounded-xl text-white/85 font-mono text-[11px] sm:text-xs font-black tracking-wider shadow-xl flex items-center gap-2"
            style={{ top: watermarkPos.top, left: watermarkPos.left }}
          >
            <span className="w-2 h-2 rounded-full bg-red-500 animate-ping shrink-0" />
            <span>
              {studentProfile?.first_name || getTelegramUser()?.first_name || 'Talaba'} • ID: {studentProfile?.telegram_id || getTelegramUser()?.id || '7293959501'}
            </span>
          </div>
        )}
      </div>

      {/* Lesson Details & Navigation */}
      {currentLesson && (
        <div className="bg-tg-section border border-tg-secondary rounded-3xl p-4 sm:p-5 space-y-4 shadow-xs">
          {/* Real-time Learning Progress Bar Card */}
          <div className="p-3.5 bg-tg-secondary/60 border border-tg-secondary rounded-2xl space-y-2">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-1.5 font-bold">
                {isCompleted ? (
                  <span className="flex items-center gap-1.5 text-emerald-500 font-extrabold">
                    <CheckCircle2 className="w-4 h-4" />
                    Dars to'liq o'zlashtirildi! (100%)
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 text-blue-600 dark:text-blue-400">
                    <Clock className="w-4 h-4" />
                    O'zlashtirish: {progressPercent}%
                  </span>
                )}
              </div>
              <span className="text-[11px] font-mono text-tg-hint">
                {formatTime(currentTime)} / {formatTime(duration || currentLesson.duration_sec || 0)}
              </span>
            </div>
            <div className="w-full h-2 bg-tg-secondary rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-300 rounded-full ${
                  isCompleted ? 'bg-emerald-500' : 'bg-blue-500'
                }`}
                style={{ width: `${Math.max(3, progressPercent)}%` }}
              />
            </div>
          </div>

          <div className="flex items-start justify-between gap-3">
            <div>
              <span className="text-[11px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider">
                <TgText>{course?.title}</TgText>
              </span>
              <h2 className="text-base sm:text-lg font-bold text-tg-text mt-0.5">
                <TgText>{currentLesson.title}</TgText>
              </h2>
            </div>
          </div>

          {currentLesson.description && (
            <p className="text-xs sm:text-sm text-tg-hint leading-relaxed">
              {currentLesson.description}
            </p>
          )}

          {/* Dars sizga ma'qul bo'ldimi? (Modern ThumbsUp / ThumbsDown vector reaction widget) */}
          <div className="p-3.5 bg-tg-secondary/40 border border-tg-secondary rounded-2xl flex items-center justify-between gap-3">
            <span className="text-xs font-semibold text-tg-text">
              Dars sizga ma'qul bo'ldimi?
            </span>
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={() => {
                  triggerHaptic('medium');
                  setFeedbackReaction('like');
                  setShowFeedbackModal(true);
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-bold transition-all active:scale-95 cursor-pointer"
                title="Ha, yoqdi"
              >
                <ThumbsUp className="w-3.5 h-3.5 stroke-[2.2]" />
                <span>Yoqdi</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  triggerHaptic('medium');
                  setFeedbackReaction('dislike');
                  setShowFeedbackModal(true);
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 dark:text-rose-400 text-xs font-bold transition-all active:scale-95 cursor-pointer"
                title="Yoqmadi"
              >
                <ThumbsDown className="w-3.5 h-3.5 stroke-[2.2]" />
                <span>Yoqmadi</span>
              </button>
            </div>
          </div>

          {/* Ovozli hisobot yuborish (Voice Report to Mentor) - Faqat kursning oxirgi darsida */}
          {isLastLesson && (
            <div className="p-4 bg-gradient-to-r from-indigo-500/15 via-purple-500/15 to-blue-500/15 border-2 border-indigo-500/40 rounded-3xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-md animate-in fade-in duration-300">
              <div className="flex items-center gap-3.5 min-w-0">
                <div className="w-11 h-11 rounded-2xl bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-lg shadow-indigo-600/30">
                  <Mic className="w-5 h-5" />
                </div>
                <div className="min-w-0 space-y-0.5">
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-bold text-tg-text truncate">
                      Kurs yakuni bo'yicha umumiy ovozli hisobot
                    </h4>
                    <span className="text-[9px] font-black uppercase px-2 py-0.5 rounded-full bg-indigo-600 text-white shadow-xs shrink-0">
                      Yakuniy
                    </span>
                  </div>
                  <p className="text-xs text-tg-hint leading-relaxed">
                    Barcha darslardan olgan umumiy xulosangizni 1-3 daqiqalik ovozda mentorga so'zlab bering.
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => {
                  triggerHaptic('medium');
                  setShowVoiceModal(true);
                }}
                className="w-full sm:w-auto px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 active:scale-95 text-white text-xs sm:text-sm font-bold rounded-2xl shadow-lg shadow-indigo-600/25 transition-all flex items-center justify-center gap-2 shrink-0 cursor-pointer"
              >
                <Mic className="w-4 h-4" />
                <span>Ovoz yozish</span>
              </button>
            </div>
          )}

          {/* Prev / Next Lesson Navigation Buttons */}
          <div className="flex items-center justify-between gap-2 pt-2 border-t border-tg-secondary">
            {prevLesson ? (
              <button
                onClick={() => {
                  triggerHaptic('selection');
                  onSelectLesson(courseId, prevLesson.id);
                }}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-tg-secondary hover:bg-tg-secondary/80 text-xs font-semibold text-tg-text transition-all cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" />
                <span className="truncate max-w-[110px] sm:max-w-[160px]">
                  {prevLesson.title}
                </span>
              </button>
            ) : <div />}

            {nextLesson ? (
              <button
                onClick={() => {
                  triggerHaptic('selection');
                  onSelectLesson(courseId, nextLesson.id);
                }}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 active:scale-95 text-xs font-bold text-white shadow-md shadow-blue-600/20 transition-all cursor-pointer ml-auto"
              >
                <span className="truncate max-w-[110px] sm:max-w-[160px]">
                  {nextLesson.title}
                </span>
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={() => {
                  triggerHaptic('success');
                  setShowCourseCompletedModal(true);
                }}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-xs font-extrabold text-white shadow-lg shadow-emerald-600/25 transition-all cursor-pointer ml-auto"
              >
                <Award className="w-4 h-4" />
                <span>Kursni tugatish 🎉</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Lesson Quizzes Section */}
      {quizzes.length > 0 && (
        <div ref={quizSectionRef} className="space-y-3 transition-all duration-300">
          {!isCompleted && progressPercent < 90 ? (
            <div className="bg-tg-section border border-dashed border-amber-500/30 rounded-3xl p-5 text-center space-y-2 my-4 shadow-sm">
              <div className="w-12 h-12 mx-auto rounded-2xl bg-amber-500/10 flex items-center justify-center text-amber-500 text-2xl">
                🔒
              </div>
              <h4 className="text-sm font-bold text-tg-text">Dars Testi Qulflangan</h4>
              <p className="text-xs text-tg-hint max-w-xs mx-auto">
                Test savollariga javob berish uchun darsni 100% ko'rib chiqing. Video yoki audio tugashi bilan test avtomatik ochiladi!
              </p>
            </div>
          ) : (
            <div className="space-y-3 animate-in fade-in slide-in-from-bottom-3 duration-300">
              <div className="bg-gradient-to-r from-blue-600/15 via-emerald-600/15 to-transparent border border-blue-500/30 rounded-2xl p-3.5 flex items-center gap-3 shadow-xs">
                <span className="text-2xl animate-bounce">🎯</span>
                <div>
                  <h4 className="text-xs sm:text-sm font-bold text-tg-text">
                    Dars yakunlandi! Bilimingizni sinab ko'ring
                  </h4>
                  <p className="text-[11px] text-tg-hint">
                    Quyidagi test savoliga to'g'ri javob berib, darsni muvaffaqiyatli yakunlang
                  </p>
                </div>
              </div>

              <LessonQuizCard
                quizzes={quizzes}
                onAllComplete={() => {
                  reportProgress(100, 100, true);
                  const currIdx = lessons.findIndex((l) => String(l.id) === String(lessonId));
                  if (currIdx !== -1 && currIdx === lessons.length - 1 && lessons.length > 0) {
                    setShowCourseCompletedModal(true);
                  }
                }}
              />
            </div>
          )}
        </div>
      )}

      {/* AI Tutor Assistant Embedded Widget */}
      {currentLesson && (
        <LessonAiAssistant
          course={course}
          lesson={currentLesson}
        />
      )}

      {/* Lesson Feedback Modal */}
      <FeedbackModal
        isOpen={showFeedbackModal}
        onClose={() => setShowFeedbackModal(false)}
        courseId={courseId}
        lessonId={lessonId}
        courseTitle={course?.title}
        lessonTitle={currentLesson?.title}
        initialReaction={feedbackReaction}
      />

      {/* Voice Report to Mentor Modal */}
      <VoiceReportModal
        isOpen={showVoiceModal}
        onClose={() => setShowVoiceModal(false)}
        lessonId={lessonId}
        lessonTitle={currentLesson?.title}
        courseTitle={course?.title}
        onSuccess={() => {
          setIsCompleted(true);
          reportProgress(100, 100, true);
        }}
      />
    </div>
  );
};
