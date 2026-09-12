import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  Calendar,
  Clock,
  ExternalLink,
  LogOut,
  Radio,
  Sparkles,
  Users,
  Video,
  AlertCircle,
} from 'lucide-react';
import { LiveSession, Course, AppView } from '../types';
import {
  fetchCourseById,
  fetchLiveSessions,
  joinLiveSession,
  leaveLiveSession,
} from '../services/api';
import { triggerHaptic } from '../services/telegram';

interface LiveSessionsViewProps {
  courseId: string | number;
  onNavigate: (view: AppView) => void;
}

export const LiveSessionsView: React.FC<LiveSessionsViewProps> = ({
  courseId,
  onNavigate,
}) => {
  const [course, setCourse] = useState<Course | null>(null);
  const [sessions, setSessions] = useState<LiveSession[]>([]);
  const [activeSession, setActiveSession] = useState<LiveSession | null>(null);
  const [joinedStreamRef, setJoinedStreamRef] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSessions();
  }, [courseId]);

  const loadSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const [courseData, sessionsData] = await Promise.all([
        fetchCourseById(courseId),
        fetchLiveSessions(courseId),
      ]);
      setCourse(courseData);
      setSessions(sessionsData);
    } catch (err: any) {
      setError(err.message || 'Jonli darslarni yuklashda xatolik');
    } finally {
      setLoading(false);
    }
  };

  const handleJoin = async (session: LiveSession) => {
    triggerHaptic('medium');
    setJoining(true);
    setError(null);
    try {
      await joinLiveSession(session.id);
      triggerHaptic('success');
      onNavigate({
        type: 'live-stream',
        sessionId: session.id,
        courseId: courseId,
      });
    } catch (err: any) {
      triggerHaptic('error');
      setError(err.message || 'Jonli darsga ulanishda xatolik');
    } finally {
      setJoining(false);
    }
  };

  const handleLeave = async () => {
    if (!activeSession) return;
    triggerHaptic('light');
    try {
      await leaveLiveSession(activeSession.id);
    } catch (err) {
      console.error('Leave error:', err);
    }
    setActiveSession(null);
    setJoinedStreamRef(null);
  };

  const formatDateTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString('uz-UZ', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  const getStatusBadge = (status: LiveSession['status']) => {
    switch (status) {
      case 'live':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-extrabold bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/20 animate-pulse">
            <Radio className="w-3 h-3 text-rose-500" />
            <span>JONLI EFIRDA</span>
          </span>
        );
      case 'scheduled':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-blue-500/15 text-blue-600 dark:text-blue-400">
            <Calendar className="w-3 h-3" />
            <span>Rejalashtirilgan</span>
          </span>
        );
      case 'ended':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-semibold bg-tg-secondary text-tg-hint">
            Tugagan
          </span>
        );
      case 'cancelled':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-500/10 text-rose-500">
            Bekor qilingan
          </span>
        );
    }
  };

  return (
    <div className="space-y-5 pb-28 max-w-3xl mx-auto px-4 pt-2 animate-in fade-in duration-200">
      {/* Active Joined Stream Screen */}
      {activeSession && joinedStreamRef && (
        <div className="bg-tg-section border-2 border-rose-500/40 rounded-3xl p-4 sm:p-5 space-y-4 shadow-xl animate-in zoom-in-95">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-rose-500 animate-ping" />
              <h3 className="font-extrabold text-sm sm:text-base text-tg-text">
                Jonli Efir Ulandi
              </h3>
            </div>
            <button
              onClick={handleLeave}
              className="py-1.5 px-3 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 text-rose-600 dark:text-rose-400 font-bold text-xs flex items-center gap-1.5 cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Tark etish</span>
            </button>
          </div>

          <div className="relative w-full aspect-video rounded-2xl bg-black overflow-hidden flex items-center justify-center">
            {joinedStreamRef.includes('meet.jit.si') ? (
              <iframe
                src={joinedStreamRef}
                allow="camera; microphone; fullscreen; display-capture"
                className="w-full h-full border-0"
                title="Live Stream"
              />
            ) : (
              <div className="text-center p-6 text-white space-y-2">
                <Video className="w-10 h-10 mx-auto text-blue-400" />
                <p className="text-xs font-semibold">WebRTC / Live Stream oqimi faol</p>
                <a
                  href={joinedStreamRef}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-blue-400 underline"
                >
                  <span>Tashqi oynada ochish</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            )}
          </div>

          <div className="text-xs text-tg-hint">
            <p className="font-semibold text-tg-text">{activeSession.title}</p>
            <p className="mt-0.5">Savollaringizni kabinet chati orqali ham yo'llashingiz mumkin.</p>
          </div>
        </div>
      )}

      {/* Header Info */}
      <div className="bg-tg-section border border-tg-secondary rounded-3xl p-4 sm:p-5 shadow-xs space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider">
            {course?.title}
          </span>
        </div>
        <h2 className="text-base sm:text-lg font-bold text-tg-text">
          Jonli Vebinarlar & Savol-Javob Sessiyalari
        </h2>
        <p className="text-xs text-tg-hint leading-relaxed">
          Kurs mentori bilan to'g'ridan-to'g'ri bog'lanib, amaliy vazifalarni muhokama qiling.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-xs text-rose-600 dark:text-rose-400 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Sessions List */}
      <div className="space-y-3">
        <h3 className="font-bold text-xs uppercase tracking-wider text-tg-hint px-1">
          Darslar jadvali ({sessions.length})
        </h3>

        {loading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="h-24 bg-tg-secondary rounded-3xl animate-pulse" />
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-8 text-center rounded-3xl bg-tg-secondary text-tg-hint space-y-2">
            <Radio className="w-8 h-8 mx-auto opacity-40" />
            <p className="text-sm font-medium">Jonli darslar mavjud emas</p>
            <p className="text-xs">Yaqin orada yangi vebinar e'lon qilinadi</p>
          </div>
        ) : (
          sessions.map((session) => {
            const isLive = session.status === 'live';

            return (
              <div
                key={session.id}
                id={`live-session-${session.id}`}
                className={`p-4 sm:p-5 rounded-3xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                  isLive
                    ? 'bg-tg-section border-rose-500/30 shadow-md ring-1 ring-rose-500/20'
                    : 'bg-tg-section border-tg-secondary shadow-xs'
                }`}
              >
                <div className="space-y-2 min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    {getStatusBadge(session.status)}
                    <span className="text-xs font-bold text-tg-text">
                      {formatDateTime(session.scheduled_at)}
                    </span>
                  </div>

                  <h4 className="font-bold text-sm sm:text-base text-tg-text">
                    {session.title || 'Mentor bilan interaktiv mashg\'ulot'}
                  </h4>

                  {session.instructor_name && (
                    <p className="text-xs text-tg-hint">
                      Boshlovchi: <span className="text-tg-text font-medium">{session.instructor_name}</span>
                    </p>
                  )}
                </div>

                <div className="shrink-0 pt-2 sm:pt-0">
                  <button
                    id={`btn-join-live-${session.id}`}
                    disabled={joining}
                    onClick={() => handleJoin(session)}
                    className={`w-full sm:w-auto py-2.5 px-5 rounded-2xl active:scale-95 text-white font-extrabold text-xs shadow-md flex items-center justify-center gap-2 transition-all cursor-pointer ${
                      isLive
                        ? 'bg-rose-600 hover:bg-rose-700 ring-2 ring-rose-500/40 animate-pulse'
                        : 'bg-blue-600 hover:bg-blue-700'
                    }`}
                  >
                    {isLive ? (
                      <>
                        <Radio className="w-4 h-4" />
                        <span>{joining ? 'Ulanmoqda...' : '🔴 Efirga kirish'}</span>
                      </>
                    ) : (
                      <>
                        <Video className="w-4 h-4" />
                        <span>{joining ? 'Ulanmoqda...' : '🎥 Efir xonasiga kirish'}</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
