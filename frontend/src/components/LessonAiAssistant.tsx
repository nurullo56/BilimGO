import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  User,
  Copy,
  Check,
  RotateCcw,
  HelpCircle,
  Code,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Bot,
} from 'lucide-react';
import { Lesson, Course } from '../types';
import { askLessonAi } from '../services/api';
import { triggerHaptic } from '../services/telegram';
import { RichAiContent } from './RichAiContent';

export const ChatGptIcon: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.8956zm16.0993 3.8558L12.5973 8.3829l2.02-1.1638a.0804.0804 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.402-.686zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L8.907 9.2297V6.8974a.0662.0662 0 0 1 .0331-.0615L13.765 3.9997a4.4992 4.4992 0 0 1 6.676 4.7277zm-10.59 4.1444l-2.2713-1.3096 2.2713-1.3096 2.2713 1.3096z" />
  </svg>
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
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(true);
  const chatBottomRef = useRef<HTMLDivElement | null>(null);

  // Quick preset questions tailored to lesson
  const quickPrompts = [
    {
      icon: BookOpen,
      label: 'Dars xulosasi',
      prompt: `Ushbu "${lesson.title}" darsining eng muhim 3 ta xulosasini qisqa qilib tushuntirib ber.`,
    },
    {
      icon: HelpCircle,
      label: 'Oddiy tilda tushuntir',
      prompt: `"${lesson.title}" mavzusidagi asosiy tushunchalarni yangi boshlovchi uchun eng sodda tilda va hayotiy misollar bilan tushuntirib ber.`,
    },
    {
      icon: Code,
      label: 'Amaliy misol',
      prompt: `Ushbu dars mavzusiga oid eng amaliy kod yoki real loyihadagi misol ko'rsat.`,
    },
    {
      icon: CheckCircle2,
      label: 'Meni sinab ko\'r',
      prompt: `Ushbu darsni qanchalik tushunganimni tekshirish uchun menga 3 ta qiziqarli savol ber.`,
    },
  ];

  // Auto-scroll on new messages
  useEffect(() => {
    if (messages.length > 0 && isExpanded) {
      chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading, isExpanded]);

  // Reset or initialize on lesson change
  useEffect(() => {
    setMessages([
      {
        id: `welcome-${lesson.id}`,
        sender: 'assistant',
        text: `Salom! Men sizning shaxsiy **AI Ustozingizman**. \n\n**"${lesson.title}"** darsi davomida tushunmagan har qanday savolingizni so'rashingiz mumkin. Quyidagi tezkor tugmalardan foydalaning yoki savolingizni yozing!`,
        timestamp: 'Hozir',
      },
    ]);
  }, [lesson.id]);

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
        text: `Suhbat yangilandi. **"${lesson.title}"** darsi bo'yicha yana nimalarni tushuntirib beray?`,
        timestamp: 'Hozir',
      },
    ]);
  };

  return (
    <div className="bg-tg-section border border-tg-secondary rounded-3xl overflow-hidden shadow-xs transition-all">
      {/* Header Bar */}
      <div className="p-4 sm:p-5 flex items-center justify-between border-b border-tg-secondary bg-gradient-to-r from-blue-500/10 via-indigo-500/5 to-transparent">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-2xl bg-[#10a37f] text-white flex items-center justify-center shadow-sm">
            <ChatGptIcon className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-sm sm:text-base text-tg-text">
                AI Ustozdan so'rash
              </h3>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Faol
              </span>
            </div>
            <p className="text-[11px] text-tg-hint line-clamp-1">
              Darsda tushunmagan joylaringizni darhol so'rab o'rganing
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handleResetChat}
            title="Suhbatni tozalash"
            className="p-2 rounded-xl text-tg-hint hover:text-tg-text hover:bg-tg-secondary transition-all cursor-pointer"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              triggerHaptic('light');
              setIsExpanded(!isExpanded);
            }}
            className="p-2 rounded-xl text-tg-hint hover:text-tg-text hover:bg-tg-secondary transition-all cursor-pointer"
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="p-4 sm:p-5 space-y-4">
          {/* Quick Prompts Carousel/Grid */}
          <div className="space-y-1.5">
            <span className="text-[11px] font-bold uppercase tracking-wider text-tg-hint">
              Tezkor savollar:
            </span>
            <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar scroll-smooth">
              {quickPrompts.map((item, idx) => {
                const IconComponent = item.icon;
                return (
                  <button
                    key={idx}
                    disabled={loading}
                    onClick={() => handleSend(item.prompt)}
                    className="shrink-0 px-3 py-2 rounded-xl bg-tg-secondary hover:bg-blue-500/15 hover:border-blue-500/30 border border-transparent text-tg-text text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer active:scale-95 disabled:opacity-50"
                  >
                    <IconComponent className="w-3.5 h-3.5 text-blue-500" />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Messages Flow */}
          <div className="space-y-3 max-h-[360px] overflow-y-auto pr-1">
            {messages.map((msg) => {
              const isAi = msg.sender === 'assistant';
              return (
                <div
                  key={msg.id}
                  className={`flex gap-2.5 ${isAi ? 'items-start' : 'items-start flex-row-reverse'}`}
                >
                  {/* Avatar */}
                  <div
                    className={`w-7 h-7 rounded-xl flex items-center justify-center shrink-0 mt-0.5 ${
                      isAi
                        ? 'bg-[#10a37f] text-white shadow-2xs'
                        : 'bg-tg-secondary text-tg-text'
                    }`}
                  >
                    {isAi ? <ChatGptIcon className="w-4 h-4" /> : <User className="w-4 h-4" />}
                  </div>

                  {/* Message Bubble */}
                  <div
                    className={`max-w-[85%] rounded-2xl p-3.5 sm:p-4 text-xs sm:text-sm space-y-2 relative group ${
                      isAi
                        ? 'bg-tg-secondary/70 border border-tg-secondary text-tg-text rounded-tl-sm'
                        : 'bg-blue-600 text-white rounded-tr-sm'
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

                    <div className="w-full overflow-hidden">
                      <RichAiContent content={msg.text} isUser={!isAi} />
                    </div>
                  </div>
                </div>
              );
            })}

            {loading && (
              <div className="flex items-start gap-2.5">
                <div className="w-7 h-7 rounded-xl bg-blue-500/15 text-blue-600 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-tg-secondary/70 border border-tg-secondary rounded-2xl rounded-tl-sm p-3.5 flex items-center gap-2">
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

          {/* Input Box */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="pt-2 border-t border-tg-secondary flex items-center gap-2"
          >
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Dars bo'yicha tushunmagan savolingizni yozing..."
              disabled={loading}
              className="flex-1 bg-tg-secondary border border-transparent focus:border-blue-500 text-tg-text text-xs sm:text-sm rounded-2xl px-4 py-3 outline-none transition-all placeholder:text-tg-hint"
            />
            <button
              type="submit"
              disabled={!inputQuery.trim() || loading}
              className="p-3 rounded-2xl bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-all cursor-pointer active:scale-95 shadow-xs shrink-0"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}
    </div>
  );
};
