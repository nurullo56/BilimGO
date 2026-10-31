import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  User,
  Copy,
  Check,
  RotateCcw,
  Sparkles,
  X,
} from 'lucide-react';
import { Lesson, Course } from '../types';
import { askLessonAi } from '../services/api';
import { triggerHaptic } from '../services/telegram';
import { RichAiContent } from './RichAiContent';

/**
 * AI Ustoz uchun yoqimli va zamonaviy robot boshchasi belgisi (SVG).
 * UX maketidagi robot ko'rinishiga moslashtirilgan.
 */
export const AiUstozBotIcon: React.FC<{ className?: string }> = ({ className = 'w-6 h-6' }) => (
  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
    {/* Antenna */}
    <circle cx="12" cy="2.8" r="1.5" fill="currentColor" />
    <path d="M12 4.3V7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    {/* Head frame */}
    <rect x="4" y="7" width="16" height="13.2" rx="4.5" fill="currentColor" fillOpacity="0.18" stroke="currentColor" strokeWidth="1.6" />
    {/* Ears */}
    <rect x="2" y="10.5" width="2" height="6.2" rx="1" fill="currentColor" />
    <rect x="20" y="10.5" width="2" height="6.2" rx="1" fill="currentColor" />
    {/* Eyes */}
    <circle cx="9" cy="12.2" r="1.5" fill="currentColor" />
    <circle cx="15" cy="12.2" r="1.5" fill="currentColor" />
    {/* Friendly Smile */}
    <path d="M9.6 15.5C10.3 16.3 11.1 16.7 12 16.7C12.9 16.7 13.7 16.3 14.4 15.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
  </svg>
);

export const ChatGptIcon: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => (
  <AiUstozBotIcon className={className} />
);

interface LessonAiAssistantProps {
  course?: Course | null;
  lesson: Lesson;
}

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
}

export const LessonAiAssistant: React.FC<LessonAiAssistantProps> = ({
  course,
  lesson,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const chatBottomRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  // Dars mavzusiga moslashtirilgan aqlli tezkor savollar
  const quickPrompts = [
    `"${lesson.title}" darsining asosiy xulosalari nimalar?`,
    `"${lesson.title}" mavzusini oddiy tilda hayotiy misollar bilan tushuntirib ber`,
    `Ushbu dars bo'yicha eng muhim amaliy maslahatlar qanday?`,
    `Darsni qanchalik tushunganimni sinash uchun menga savol ber`,
  ];

  // Auto-scroll on new messages
  useEffect(() => {
    if (messages.length > 0 && isOpen) {
      chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading, isOpen]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [isOpen]);

  // Dars o'zgarganda xabarlarni moslash
  useEffect(() => {
    setMessages([
      {
        id: `welcome-${lesson.id}`,
        sender: 'assistant',
        text: `Salom! 🤖\n\nBu dars bo'yicha savollaring bo'lsa, men yordam berishga tayyorman.\n\nHozir **"${lesson.title}"** darsidasan.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  }, [lesson.id, lesson.title]);

  const handleSend = async (customPrompt?: string) => {
    const textToSend = customPrompt || inputQuery.trim();
    if (!textToSend || loading) return;

    triggerHaptic('medium');
    const userMsg: Message = {
      id: `u-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setInputQuery('');
    setLoading(true);

    try {
      const historyPayload = newHistory.map((m) => ({
        sender: m.sender,
        text: m.text,
      }));

      const res = await askLessonAi({
        lessonId: lesson.id,
        courseTitle: course?.title,
        lessonTitle: lesson.title,
        lessonDescription: lesson.description,
        question: textToSend,
        history: historyPayload,
      });

      triggerHaptic('light');
      const aiMsg: Message = {
        id: `ai-${Date.now()}`,
        sender: 'assistant',
        text: res.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        text: '⚠️ Kechirasiz, javob olishda xatolik yuz berdi. Iltimos, qayta urinib ko\'ring.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (id: string, text: string) => {
    triggerHaptic('light');
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleResetChat = () => {
    triggerHaptic('light');
    setMessages([
      {
        id: `welcome-${lesson.id}-${Date.now()}`,
        sender: 'assistant',
        text: `Suhbat yangilandi. 🤖\n\n**"${lesson.title}"** darsi bo'yicha yana qanday savolingiz bor?`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  const handleClose = () => {
    triggerHaptic('light');
    setIsOpen(false);
    setShowTooltip(true);
  };

  return (
    <>
      {/* ========================================================= */}
      {/* 1. & 3. SUZUVCHI TUGMA VA TOOLTIP (AI tugmasi yopiq holatda) */}
      {/* ========================================================= */}
      {!isOpen && (
        <div className="fixed bottom-6 right-5 sm:bottom-8 sm:right-8 z-40 flex items-center gap-2.5 pointer-events-auto select-none">
          {/* Savol bo'lsa chaqirish bo'yicha kichik eslatma/bulutcha (Tooltip) */}
          {showTooltip && (
            <div className="relative flex items-center gap-1.5 bg-white dark:bg-[#182234] border border-slate-200 dark:border-blue-500/30 text-tg-text text-xs px-3 py-2 rounded-2xl shadow-xl animate-in fade-in slide-in-from-right-2 duration-200">
              <span className="text-[11px] leading-tight font-medium">
                Agar yana savol bo'lsa, meni chaqiring! 🤖
              </span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowTooltip(false);
                }}
                className="w-4 h-4 rounded-full hover:bg-slate-100 dark:hover:bg-white/10 text-tg-hint hover:text-tg-text flex items-center justify-center transition-colors cursor-pointer text-xs ml-0.5"
                title="Yopish"
              >
                ×
              </button>
              {/* Bulutcha uchidagi ko'rsatkich burchagi */}
              <div className="absolute -right-1.5 top-1/2 -translate-y-1/2 w-0 h-0 border-y-4 border-y-transparent border-l-[6px] border-l-white dark:border-l-[#182234]" />
            </div>
          )}

          {/* Dumaloq suzuvchi AI tugmasi */}
          <button
            type="button"
            onClick={() => {
              triggerHaptic('medium');
              setIsOpen(true);
              setShowTooltip(false);
            }}
            title="AI Ustozni chaqirish"
            className="w-14 h-14 rounded-full bg-gradient-to-tr from-blue-600 via-indigo-600 to-blue-500 hover:from-blue-500 hover:to-indigo-500 text-white flex items-center justify-center shadow-xl shadow-blue-600/30 ring-4 ring-blue-500/20 active:scale-90 hover:scale-105 transition-all duration-200 cursor-pointer group"
          >
            <AiUstozBotIcon className="w-7 h-7 text-white transition-transform group-hover:scale-110" />
          </button>
        </div>
      )}

      {/* ========================================================= */}
      {/* 2. OCHILGAN AI CHAT - PASTKI PANEL (Bottom Sheet Modal) */}
      {/* ========================================================= */}
      {isOpen && (
        <>
          {/* Qorong'u orqa fon (Backdrop) */}
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 transition-opacity animate-in fade-in duration-200"
            onClick={handleClose}
          />

          {/* Pastki suzuvchi panel (Bottom Sheet - Kun va Tun rejimiga mos) */}
          <div className="fixed bottom-0 left-0 right-0 sm:left-auto sm:right-6 sm:bottom-6 sm:w-[440px] max-w-lg mx-auto z-50 bg-white dark:bg-[#17212b] text-tg-text rounded-t-[32px] sm:rounded-3xl border-t sm:border border-slate-200 dark:border-white/10 shadow-2xl flex flex-col h-[75vh] max-h-[640px] overflow-hidden animate-in slide-in-from-bottom duration-300">
            {/* Mobil qurilmalar uchun tortish chizig'i (Grabber) */}
            <div className="w-10 h-1 bg-slate-300 dark:bg-white/20 rounded-full mx-auto my-2.5 shrink-0 sm:hidden" />

            {/* Header: AI Ustoz, Status & Close Button */}
            <div className="px-4 py-3 border-b border-slate-200 dark:border-white/10 flex items-center justify-between bg-slate-50 dark:bg-[#1c2733] shrink-0">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center shadow-md shadow-blue-600/30 shrink-0">
                  <AiUstozBotIcon className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-sm text-tg-text leading-tight">AI Ustoz</h3>
                  <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1.5 leading-tight">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    Online
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={handleResetChat}
                  title="Suhbatni tozalash"
                  className="w-8 h-8 rounded-full hover:bg-slate-200/60 dark:hover:bg-white/10 text-tg-hint hover:text-tg-text flex items-center justify-center transition-colors cursor-pointer"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={handleClose}
                  title="Yopish"
                  className="w-8 h-8 rounded-full bg-slate-200/70 hover:bg-slate-300/70 text-slate-700 dark:bg-white/10 dark:hover:bg-white/20 dark:text-white flex items-center justify-center transition-all cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Xabarlar maydoni */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3.5 scroll-smooth bg-slate-50/50 dark:bg-[#17212b]">
              {messages.map((msg) => {
                const isAi = msg.sender === 'assistant';
                return (
                  <div
                    key={msg.id}
                    className={`flex gap-2.5 ${isAi ? 'items-start' : 'items-start flex-row-reverse'}`}
                  >
                    {/* Kichik belgi/avatar */}
                    <div
                      className={`w-7 h-7 rounded-xl flex items-center justify-center shrink-0 mt-0.5 ${
                        isAi
                          ? 'bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-xs'
                          : 'bg-slate-200 text-slate-700 dark:bg-white/10 dark:text-white'
                      }`}
                    >
                      {isAi ? <AiUstozBotIcon className="w-4 h-4" /> : <User className="w-4 h-4" />}
                    </div>

                    {/* Xabar pufakchasi (Kun va Tun rejimiga to'liq mos) */}
                    <div
                      className={`max-w-[85%] rounded-2xl p-3.5 text-xs sm:text-sm space-y-1.5 relative group ${
                        isAi
                          ? 'bg-white dark:bg-[#232e3c] border border-slate-200/80 dark:border-white/5 text-tg-text rounded-tl-xs shadow-xs'
                          : 'bg-blue-600 text-white rounded-tr-xs shadow-xs'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-4">
                        <span
                          className={`text-[10px] font-bold ${
                            isAi ? 'text-blue-600 dark:text-blue-400' : 'text-blue-100'
                          }`}
                        >
                          {isAi ? 'AI Ustoz' : 'Siz'}
                        </span>
                        <div className="flex items-center gap-1">
                          <span
                            className={`text-[9px] ${
                              isAi ? 'text-tg-hint' : 'text-blue-200'
                            }`}
                          >
                            {msg.timestamp}
                          </span>
                          {isAi && (
                            <button
                              type="button"
                              onClick={() => handleCopy(msg.id, msg.text)}
                              title="Nusxa olish"
                              className="p-1 rounded text-tg-hint hover:text-tg-text opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                            >
                              {copiedId === msg.id ? (
                                <Check className="w-3 h-3 text-emerald-500" />
                              ) : (
                                <Copy className="w-3 h-3" />
                              )}
                            </button>
                          )}
                        </div>
                      </div>

                      <div className="w-full overflow-hidden text-tg-text">
                        <RichAiContent content={msg.text} isUser={!isAi} />
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Tezkor savollar tavsiyalari (Tezkor savollar kartochkalari) */}
              {messages.length <= 2 && !loading && (
                <div className="pt-2 space-y-2 animate-in fade-in duration-300">
                  <div className="flex items-center gap-1.5 text-blue-600 dark:text-blue-400 text-xs font-bold">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Tezkor savollar</span>
                  </div>
                  <div className="grid grid-cols-1 gap-2">
                    {quickPrompts.map((prompt, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => handleSend(prompt)}
                        className="w-full text-left p-2.5 rounded-xl bg-white dark:bg-[#232e3c] hover:bg-blue-50 dark:hover:bg-blue-900/30 border border-slate-200 dark:border-white/5 hover:border-blue-300 dark:hover:border-blue-500/30 text-tg-text text-xs shadow-xs transition-all cursor-pointer active:scale-98"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* AI javob tayyorlayotgan holat (Typing indicator) */}
              {loading && (
                <div className="flex items-start gap-2.5">
                  <div className="w-7 h-7 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
                    <AiUstozBotIcon className="w-4 h-4" />
                  </div>
                  <div className="bg-white dark:bg-[#232e3c] border border-slate-200/80 dark:border-white/5 rounded-2xl rounded-tl-xs p-3 flex items-center gap-2 shadow-xs">
                    <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" />
                    <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce [animation-delay:0.2s]" />
                    <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce [animation-delay:0.4s]" />
                    <span className="text-xs text-tg-hint font-medium ml-1">
                      AI Ustoz dars bo'yicha javob tayyorlamoqda...
                    </span>
                  </div>
                </div>
              )}
              <div ref={chatBottomRef} />
            </div>

            {/* Input Bar */}
            <div className="p-3 sm:p-4 border-t border-slate-200 dark:border-white/10 bg-slate-50 dark:bg-[#1c2733] shrink-0">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSend();
                }}
                className="flex items-center gap-2"
              >
                <input
                  ref={inputRef}
                  type="text"
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  placeholder="Savolingizni yozing..."
                  disabled={loading}
                  className="flex-1 bg-white dark:bg-[#131d27] border border-slate-200 dark:border-white/10 focus:border-blue-500 text-tg-text text-xs sm:text-sm rounded-2xl px-4 py-3 outline-none transition-all placeholder:text-tg-hint"
                />
                <button
                  type="submit"
                  disabled={!inputQuery.trim() || loading}
                  className="w-11 h-11 rounded-2xl bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white flex items-center justify-center transition-all cursor-pointer active:scale-95 shadow-md shadow-blue-600/30 shrink-0"
                  title="Yuborish"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </div>
          </div>
        </>
      )}
    </>
  );
};
