import React, { useState, useRef, useEffect } from 'react';
import {
  Mic,
  Square,
  Play,
  Pause,
  RotateCcw,
  Send,
  X,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
} from 'lucide-react';
import { triggerHaptic } from '../services/telegram';
import { submitVoiceReport } from '../services/api';

interface VoiceReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  lessonId: string | number;
  lessonTitle?: string;
  courseTitle?: string;
  onSuccess?: () => void;
}

export const VoiceReportModal: React.FC<VoiceReportModalProps> = ({
  isOpen,
  onClose,
  lessonId,
  lessonTitle,
  courseTitle,
  onSuccess,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordDuration, setRecordDuration] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackTime, setPlaybackTime] = useState(0);
  const [totalAudioDuration, setTotalAudioDuration] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerIntervalRef = useRef<any>(null);
  const previewAudioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (!isOpen) {
      resetRecording();
    }
  }, [isOpen]);

  const resetRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {
        // ignore
      }
    }
    clearInterval(timerIntervalRef.current);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    setIsRecording(false);
    setRecordDuration(0);
    setAudioBlob(null);
    setAudioUrl(null);
    setIsPlaying(false);
    setPlaybackTime(0);
    setTotalAudioDuration(0);
    setError(null);
    setIsSuccess(false);
    audioChunksRef.current = [];
  };

  const startRecording = async () => {
    setError(null);
    triggerHaptic('medium');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];

      let mimeType = 'audio/webm';
      if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
        mimeType = 'audio/ogg;codecs=opus';
      } else if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus';
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mimeType = 'audio/mp4';
      }

      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
        const blob = new Blob(audioChunksRef.current, { type: mimeType });
        setAudioBlob(blob);
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        setIsRecording(false);
        clearInterval(timerIntervalRef.current);
        triggerHaptic('success');
      };

      recorder.start(250); // har 250ms da chunk
      setIsRecording(true);
      setRecordDuration(0);

      timerIntervalRef.current = setInterval(() => {
        setRecordDuration((prev) => {
          if (prev >= 180) {
            // Maksimal 3 daqiqa
            stopRecording();
            return 180;
          }
          return prev + 1;
        });
      }, 1000);
    } catch (err: any) {
      console.error('Mikrofon xatosi:', err);
      setError("Mikrofondan foydalanishga ruxsat berilmadi yoki qurilmada mikrofon topilmadi.");
      triggerHaptic('warning');
    }
  };

  const stopRecording = () => {
    triggerHaptic('light');
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    clearInterval(timerIntervalRef.current);
    setIsRecording(false);
  };

  const handleTogglePlay = () => {
    if (!previewAudioRef.current) return;
    triggerHaptic('light');
    if (isPlaying) {
      previewAudioRef.current.pause();
      setIsPlaying(false);
    } else {
      previewAudioRef.current.play().catch(console.error);
      setIsPlaying(true);
    }
  };

  const handleSubmit = async () => {
    if (!audioBlob) {
      setError("Iltimos, avval ovozingizni yozib oling.");
      return;
    }

    if (recordDuration < 15) {
      setError("Ovozli hisobot kamida 15-20 soniya bo'lishi kerak. Iltimos darsdan nimalarni tushunganingizni to'liqroq so'zlab bering.");
      triggerHaptic('warning');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    triggerHaptic('medium');

    try {
      await submitVoiceReport(lessonId, audioBlob, recordDuration);
      triggerHaptic('success');
      setIsSuccess(true);
      if (onSuccess) {
        onSuccess();
      }
      setTimeout(() => {
        setIsSuccess(false);
        onClose();
      }, 2200);
    } catch (err: any) {
      console.error('Ovoz yuborishda xatolik:', err);
      setError(err.message || "Ovozli hisobotni yuborishda xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.");
      triggerHaptic('warning');
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/65 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-md bg-white dark:bg-slate-900 rounded-3xl p-6 shadow-2xl border border-slate-100 dark:border-slate-800 transition-all">
        {/* Yopish tugmasi */}
        <button
          onClick={() => {
            triggerHaptic('light');
            resetRecording();
            onClose();
          }}
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {isSuccess ? (
          <div className="py-8 text-center flex flex-col items-center justify-center space-y-3">
            <div className="w-16 h-16 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center animate-bounce">
              <CheckCircle2 className="w-10 h-10" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white">
              Ovozli hisobot yuborildi!
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-xs leading-relaxed">
              Ovozli xabaringiz shaxsiy mentoringizga Telegram orqali muvaffaqiyatli yetkazildi. Dars qabul qilindi!
            </p>
          </div>
        ) : (
          <div className="space-y-5">
            {/* Sarlavha */}
            <div className="text-center space-y-1">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 mb-1">
                <Mic className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Kurs Yakuni Bo'yicha Ovozli Hisobot
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-xs mx-auto">
                {courseTitle ? `«${courseTitle}» kursi bo'yicha` : "Butun kurs davomida"} olgan umumiy xulosangizni 1-3 daqiqalik ovozda mentorga so'zlab bering.
              </p>
            </div>

            {/* Ovoz yozish zonasi */}
            <div className="flex flex-col items-center justify-center py-4 bg-slate-50 dark:bg-slate-800/40 rounded-2xl border border-slate-100 dark:border-slate-800 space-y-3">
              {/* Taymer */}
              <div className="flex items-center gap-2 font-mono text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">
                {isRecording && (
                  <span className="w-3 h-3 rounded-full bg-rose-500 animate-ping" />
                )}
                <span>{formatTimer(recordDuration)}</span>
                <span className="text-xs font-sans text-slate-400 font-normal">/ 03:00</span>
              </div>

              {/* Asosiy Mikrofon / To'xtatish Tugmasi */}
              {!audioBlob ? (
                isRecording ? (
                  <button
                    type="button"
                    onClick={stopRecording}
                    className="w-20 h-20 rounded-full bg-rose-600 hover:bg-rose-700 active:scale-95 text-white flex flex-col items-center justify-center shadow-lg shadow-rose-600/30 transition-all cursor-pointer ring-4 ring-rose-500/20"
                  >
                    <Square className="w-8 h-8 fill-current" />
                    <span className="text-[10px] font-bold mt-1 uppercase">To'xtatish</span>
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={startRecording}
                    className="w-20 h-20 rounded-full bg-indigo-600 hover:bg-indigo-700 active:scale-95 text-white flex flex-col items-center justify-center shadow-lg shadow-indigo-600/30 transition-all cursor-pointer ring-4 ring-indigo-500/20 hover:scale-105"
                  >
                    <Mic className="w-8 h-8" />
                    <span className="text-[10px] font-bold mt-1 uppercase tracking-wider">Yozish</span>
                  </button>
                )
              ) : (
                /* Yozilgan Ovozni Eshitib Ko'rish (Preview Player) */
                <div className="w-full px-4 space-y-3">
                  {audioUrl && (
                    <audio
                      ref={previewAudioRef}
                      src={audioUrl}
                      onTimeUpdate={() => {
                        if (previewAudioRef.current) {
                          setPlaybackTime(previewAudioRef.current.currentTime);
                        }
                      }}
                      onLoadedMetadata={() => {
                        if (previewAudioRef.current) {
                          setTotalAudioDuration(previewAudioRef.current.duration || recordDuration);
                        }
                      }}
                      onEnded={() => setIsPlaying(false)}
                    />
                  )}

                  <div className="flex items-center justify-between gap-3 p-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700">
                    <button
                      type="button"
                      onClick={handleTogglePlay}
                      className="w-10 h-10 rounded-full bg-indigo-600 text-white flex items-center justify-center shrink-0 active:scale-95 cursor-pointer"
                    >
                      {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-0.5" />}
                    </button>

                    <div className="flex-1 min-w-0">
                      <div className="h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-600 transition-all"
                          style={{
                            width: `${
                              totalAudioDuration > 0
                                ? (playbackTime / totalAudioDuration) * 100
                                : 0
                            }%`,
                          }}
                        />
                      </div>
                      <div className="flex justify-between text-[10px] text-slate-400 font-mono mt-1">
                        <span>{formatTimer(Math.round(playbackTime))}</span>
                        <span>{formatTimer(Math.round(totalAudioDuration || recordDuration))}</span>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={resetRecording}
                      className="p-2 text-rose-500 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-xl transition cursor-pointer"
                      title="Qayta yozish"
                    >
                      <RotateCcw className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}

              <p className="text-[11px] text-slate-400 text-center max-w-xs">
                {isRecording
                  ? "Ovoz yozilmoqda... Tugatgach qizil to'xtatish tugmasini bosing."
                  : audioBlob
                  ? "Ovozingizni eshitib ko'rishingiz yoki qaytadan yozishingiz mumkin."
                  : "Mikrofon tugmasini bosing va darsdan tushunganlaringizni so'zlang."}
              </p>
            </div>

            {error && (
              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 text-xs">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Yuborish tugmasi */}
            <button
              type="button"
              onClick={handleSubmit}
              disabled={isSubmitting || !audioBlob || isRecording}
              className="w-full py-3.5 px-4 rounded-2xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white font-bold text-xs sm:text-sm shadow-lg shadow-indigo-600/25 transition-all active:scale-[0.98] flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <span>Mentorga yetkazilmoqda...</span>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Mentorga yuborish</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
