import React, { useState, useEffect, useRef } from 'react';
import {
  BarChart2,
  ChevronDown,
  MessageSquare,
  Send,
  Sparkles,
  Users,
  Smile,
  Shield,
  Plus,
  Edit3,
  Check,
  Copy,
  X,
  Info,
  BookOpen,
  Link,
  MoreVertical,
  CheckCircle2,
  Reply,
  CornerDownRight,
} from 'lucide-react';
import { Cabinet, ChatMessage, CabinetStudent, AppView, Course, ChatReplyInfo } from '../types';
import {
  fetchMyCabinets,
  fetchChatMessages,
  sendChatMessage,
  fetchCabinetStudents,
  createCabinet,
  updateCabinet,
  fetchCourses,
} from '../services/api';
import { getTelegramUser, triggerHaptic } from '../services/telegram';
import { TgText, TgEmoji, TELEGRAM_ANIMATED_EMOJIS, TgAnimatedEmoji } from './TgEmoji';

interface CabinetChatViewProps {
  initialCabinetId?: string | number;
  onNavigate: (view: AppView) => void;
}

const EMOJI_OPTIONS = [
  '💬', '🐍', '⚡', '🚀', '💻', '🎯', '💡', '🌐',
  '📱', '🎨', '🤖', '📚', '🏆', '🛠️', '🎓', '🔥'
];

const CHAT_EMOJIS_CATEGORIES = [
  {
    category: '✨ Premium Animated',
    emojis: Object.keys(TELEGRAM_ANIMATED_EMOJIS),
  },
  {
    category: '🔥 Ommabop',
    emojis: ['👍', '🔥', '❤️', '🎉', '👏', '🚀', '💡', '🎯', '✨', '⚡', '💯', '👀', '💪', '👌', '🤝'],
  },
  {
    category: '😂 Kayfiyat',
    emojis: ['😊', '😂', '😎', '🤔', '😍', '🥳', '🤩', '🫡', '🙌', '🤓', '😴', '😇', '🙏', '🤯', '😭'],
  },
  {
    category: '💻 Dasturlash & Ta\'lim',
    emojis: ['💻', '🐍', '🤖', '📚', '🎓', '✍️', '🔑', '📊', '🛠️', '🌐', '📱', '⚙️', '📝', '⚡', '🖥️'],
  },
  {
    category: '📌 Belgilar',
    emojis: ['✅', '❌', '⚠️', '📌', '⏳', '🔔', '📢', '💎', '🟢', '🔴', '⭐', '🏆', '🎯', '🚀', '💬'],
  },
];


function isPureEmojiMessage(text: string): boolean {
  if (!text) return false;
  const trimmed = text.trim();
  const emojiRegex = /^(\p{Extended_Pictographic}|\p{Emoji_Presentation}|\p{Emoji_Modifier_Base}|\p{Emoji_Modifier}|\p{Emoji_Component}|\s)+$/u;
  if (!emojiRegex.test(trimmed)) return false;
  const chars = Array.from(trimmed.replace(/\s+/g, ''));
  return chars.length >= 1 && chars.length <= 4;
}

const SUGGESTED_NAMES = [
  'Python Backend Pro Guruhi',
  'Frontend Mini Apps Amaliyot',
  'Telegram Bot Muhandislari',
  'Algoritmlar & Data Structures',
  'Fullstack Dasturchilar Hamjamiyati',
];

export const CabinetChatView: React.FC<CabinetChatViewProps> = ({
  initialCabinetId,
  onNavigate,
}) => {
  const [cabinets, setCabinets] = useState<Cabinet[]>([]);
  const [selectedCabinet, setSelectedCabinet] = useState<Cabinet | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [students, setStudents] = useState<CabinetStudent[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);

  // Modals state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showStudentsModal, setShowStudentsModal] = useState(false);
  const [showSuccessToast, setShowSuccessToast] = useState<string | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);

  // Form states for creating a new cabinet
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupAvatar, setNewGroupAvatar] = useState('🚀');
  const [newGroupDescription, setNewGroupDescription] = useState('');
  const [newGroupCourseId, setNewGroupCourseId] = useState<string>('');
  const [newGroupInitialMsg, setNewGroupInitialMsg] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  // Form states for editing current cabinet
  const [editGroupName, setEditGroupName] = useState('');
  const [editGroupAvatar, setEditGroupAvatar] = useState('💬');
  const [editGroupDescription, setEditGroupDescription] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  // Reply message state
  const [replyingTo, setReplyingTo] = useState<ChatMessage | null>(null);
  const [highlightedMsgId, setHighlightedMsgId] = useState<string | number | null>(null);

  // Emoji picker state
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [activeEmojiCategoryIdx, setActiveEmojiCategoryIdx] = useState(0);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const lastMessageIdRef = useRef<string | number | null>(null);
  const isSendingRef = useRef(false);
  const currentUser = getTelegramUser();

  // Load Cabinets & Courses list
  useEffect(() => {
    loadCabinets();
    loadCourses();
  }, []);

  const loadCourses = async () => {
    try {
      const data = await fetchCourses();
      setCourses(data);
    } catch (err) {
      console.error('Courses load error:', err);
    }
  };

  const loadCabinets = async (preferCabinetId?: string | number) => {
    try {
      setLoading(true);
      const data = await fetchMyCabinets();
      setCabinets(data);
      if (data.length > 0) {
        const targetId = preferCabinetId || initialCabinetId;
        const target = targetId
          ? data.find((c) => String(c.id) === String(targetId)) || data[0]
          : data[0];
        setSelectedCabinet(target);
      }
    } catch (err) {
      console.error('Cabinets error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Load and start polling for selected Cabinet
  useEffect(() => {
    if (!selectedCabinet) return;

    // Reset messages and load initial
    setMessages([]);
    lastMessageIdRef.current = null;
    loadInitialChat(selectedCabinet.id);
    loadStudents(selectedCabinet.id);

    // Setup 3.5s interval polling
    if (pollingRef.current) clearInterval(pollingRef.current);
    pollingRef.current = setInterval(() => {
      pollNewMessages(selectedCabinet.id);
    }, 3500);

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [selectedCabinet?.id]);

  const loadInitialChat = async (cabinetId: string | number) => {
    try {
      const msgs = await fetchChatMessages(cabinetId);
      setMessages(msgs);
      if (msgs.length > 0) {
        lastMessageIdRef.current = msgs[msgs.length - 1].id;
      }
      scrollToBottom();
    } catch (err) {
      console.error('Chat initial load error:', err);
    }
  };

  const pollNewMessages = async (cabinetId: string | number) => {
    try {
      const newMsgs = await fetchChatMessages(cabinetId, lastMessageIdRef.current);
      if (newMsgs && newMsgs.length > 0) {
        setMessages((prev) => {
          const existingIds = new Set(prev.map((m) => String(m.id)));
          const uniqueNew = newMsgs.filter((m) => !existingIds.has(String(m.id)));
          if (uniqueNew.length === 0) return prev;
          return [...prev, ...uniqueNew];
        });
        lastMessageIdRef.current = newMsgs[newMsgs.length - 1].id;
        scrollToBottom();
      }
    } catch (err) {
      // silent fail in polling
    }
  };

  const loadStudents = async (cabinetId: string | number) => {
    try {
      const data = await fetchCabinetStudents(cabinetId);
      setStudents(data);
    } catch (err) {
      console.error('Students load error:', err);
    }
  };

  const scrollToBottom = () => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const handleReplyTo = (msg: ChatMessage) => {
    triggerHaptic('light');
    setReplyingTo(msg);
    setTimeout(() => {
      inputRef.current?.focus();
    }, 50);
  };

  const handleCancelReply = () => {
    triggerHaptic('selection');
    setReplyingTo(null);
  };

  const scrollToMessage = (messageId: string | number) => {
    triggerHaptic('light');
    setHighlightedMsgId(messageId);
    const el = document.getElementById(`chat-bubble-${messageId}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    setTimeout(() => {
      setHighlightedMsgId((prev) => (prev === messageId ? null : prev));
    }, 2000);
  };

  const handleInsertEmoji = (emoji: string) => {
    triggerHaptic('light');
    setInputText((prev) => prev + emoji);
    setTimeout(() => {
      inputRef.current?.focus();
    }, 20);
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (!inputText.trim() || !selectedCabinet || isSendingRef.current) return;

    triggerHaptic('medium');
    isSendingRef.current = true;
    setSending(true);

    const content = inputText.trim();
    const currentReply = replyingTo
      ? {
          message_id: replyingTo.id,
          sender_name:
            replyingTo.sender_name ||
            (replyingTo.is_me || String(replyingTo.sender_id) === String(currentUser?.id)
              ? 'Siz'
              : 'Foydalanuvchi'),
          content: replyingTo.content,
        }
      : undefined;

    setInputText('');
    setReplyingTo(null);

    try {
      const sentMsg = await sendChatMessage(selectedCabinet.id, content, currentReply);
      setMessages((prev) => {
        if (prev.some((m) => String(m.id) === String(sentMsg.id))) return prev;
        return [...prev, sentMsg];
      });
      lastMessageIdRef.current = sentMsg.id;
      scrollToBottom();
    } catch (err) {
      console.error('Send error:', err);
    } finally {
      isSendingRef.current = false;
      setSending(false);
    }
  };

  // Mentor creates a new group chat
  const handleCreateCabinet = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGroupName.trim() || isCreating) return;

    triggerHaptic('medium');
    setIsCreating(true);

    try {
      const selectedCourse = courses.find((c) => String(c.id) === String(newGroupCourseId));

      const created = await createCabinet({
        display_name: newGroupName.trim(),
        avatar: newGroupAvatar || '🚀',
        description: newGroupDescription.trim() || undefined,
        course_id: selectedCourse?.id,
        course_title: selectedCourse?.title,
        initial_message: newGroupInitialMsg.trim() || undefined,
      });

      // Update state
      setCabinets((prev) => [created, ...prev]);
      setSelectedCabinet(created);
      setShowCreateModal(false);

      // Reset form
      setNewGroupName('');
      setNewGroupAvatar('🚀');
      setNewGroupDescription('');
      setNewGroupCourseId('');
      setNewGroupInitialMsg('');

      // Show toast
      setShowSuccessToast(`"${created.display_name}" guruh chati muvaffaqiyatli ochildi!`);
      setTimeout(() => setShowSuccessToast(null), 3000);
    } catch (err) {
      console.error('Failed to create cabinet', err);
    } finally {
      setIsCreating(false);
    }
  };

  // Mentor edits current group chat
  const handleSaveEditCabinet = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCabinet || !editGroupName.trim() || isEditing) return;

    triggerHaptic('medium');
    setIsEditing(true);

    try {
      const updated = await updateCabinet(selectedCabinet.id, {
        display_name: editGroupName.trim(),
        avatar: editGroupAvatar || '💬',
        description: editGroupDescription.trim() || undefined,
      });

      setSelectedCabinet(updated);
      setCabinets((prev) =>
        prev.map((c) => (String(c.id) === String(updated.id) ? updated : c))
      );
      setShowEditModal(false);

      setShowSuccessToast('Guruh ma\'lumotlari yangilandi!');
      setTimeout(() => setShowSuccessToast(null), 3000);
    } catch (err) {
      console.error('Failed to update cabinet', err);
    } finally {
      setIsEditing(false);
    }
  };

  const handleOpenEditModal = () => {
    if (!selectedCabinet) return;
    triggerHaptic('light');
    setEditGroupName(selectedCabinet.display_name);
    setEditGroupAvatar(selectedCabinet.avatar || '💬');
    setEditGroupDescription(selectedCabinet.description || '');
    setShowEditModal(true);
  };

  const handleCopyInviteLink = () => {
    if (!selectedCabinet) return;
    triggerHaptic('light');
    const link = `https://t.me/BilimGoBot?start=group_${selectedCabinet.id}`;
    navigator.clipboard.writeText(link);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  const isMentor = selectedCabinet?.role_in_cabinet === 'mentor';

  return (
    <div className="flex flex-col h-[calc(100vh-130px)] max-w-3xl mx-auto px-3 sm:px-4 pb-10 animate-in fade-in duration-200">
      {/* Toast Notification */}
      {showSuccessToast && (
        <div className="fixed top-16 left-1/2 -translate-x-1/2 z-50 bg-emerald-600 text-white px-4 py-2 rounded-2xl text-xs font-bold shadow-lg flex items-center gap-2 animate-in fade-in slide-in-from-top-2 max-w-[90%] text-center">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{showSuccessToast}</span>
        </div>
      )}

      {/* Top Header & Group Selector / Creator */}
      <div className="bg-tg-section border border-tg-secondary rounded-2xl p-3 mb-2.5 shadow-xs shrink-0 space-y-2.5">
        <div className="flex items-center justify-between gap-2">
          {/* Active Group Details */}
          <div className="flex items-center gap-2.5 min-w-0 flex-1">
            <button
              onClick={handleOpenEditModal}
              disabled={!isMentor}
              title={isMentor ? 'Guruhni tahrirlash' : ''}
              className={`w-10 h-10 rounded-xl bg-blue-500/15 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-lg shrink-0 transition-transform ${
                isMentor ? 'hover:scale-105 active:scale-95 cursor-pointer ring-1 ring-blue-500/30' : ''
              }`}
            >
              {selectedCabinet?.avatar || '💬'}
            </button>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5 flex-wrap">
                <h3 className="font-black text-xs sm:text-sm text-tg-text truncate max-w-[170px] sm:max-w-[280px]">
                  {selectedCabinet?.display_name || 'Guruh chati'}
                </h3>
                {isMentor ? (
                  <span className="px-1.5 py-0.5 rounded-full text-[9px] font-extrabold bg-amber-500/15 text-amber-600 dark:text-amber-400 uppercase tracking-tight">
                    Siz Mentorsiz
                  </span>
                ) : (
                  <span className="px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-blue-500/15 text-blue-600 dark:text-blue-400 uppercase">
                    O'quvchi
                  </span>
                )}
              </div>
              <p className="text-[11px] text-tg-hint truncate flex items-center gap-1.5">
                <span>{students.length} a'zo</span>
                {selectedCabinet?.course_title && (
                  <>
                    <span>•</span>
                    <span className="text-blue-500 font-medium truncate">{selectedCabinet.course_title}</span>
                  </>
                )}
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-1.5 shrink-0">
            {/* Create New Group Button (Mentor) */}
            <button
              id="btn-create-group-chat"
              onClick={() => {
                triggerHaptic('light');
                setShowCreateModal(true);
              }}
              className="py-1.5 px-2.5 sm:px-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold text-[11px] sm:text-xs flex items-center gap-1 shadow-xs cursor-pointer active:scale-95 transition-all"
              title="Yangi guruh ochish"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Guruh ochish</span>
            </button>

            {/* Members info button */}
            <button
              onClick={() => {
                triggerHaptic('light');
                setShowStudentsModal(true);
              }}
              className="p-2 rounded-xl bg-tg-secondary hover:bg-tg-secondary/80 text-tg-text transition-all cursor-pointer"
              title="A'zolar"
            >
              <Users className="w-4 h-4" />
            </button>

            {/* Mentor stats & monitoring button */}
            <button
              id="btn-mentor-stats"
              onClick={() => {
                triggerHaptic('light');
                onNavigate({ type: 'mentor-stats', cabinetId: selectedCabinet?.id });
              }}
              className="px-2.5 py-1.5 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 text-amber-700 dark:text-amber-300 transition-all cursor-pointer flex items-center gap-1 shrink-0"
              title="Mentor & Talabalar Nazorati"
            >
              <BarChart2 className="w-4 h-4" />
              <span className="text-[11px] font-bold hidden xs:inline sm:inline">Statistika</span>
            </button>
          </div>
        </div>

        {/* Group Switcher Horizontal Tabs */}
        {cabinets.length > 1 && (
          <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5 pt-1 scrollbar-none border-t border-tg-secondary/40">
            <span className="text-[10px] font-bold text-tg-hint uppercase tracking-wider shrink-0 mr-1">
              Guruhlar:
            </span>
            {cabinets.map((c) => {
              const isSelected = selectedCabinet?.id === c.id;
              return (
                <button
                  key={c.id}
                  onClick={() => {
                    triggerHaptic('selection');
                    setSelectedCabinet(c);
                  }}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'bg-tg-secondary text-tg-text hover:bg-tg-secondary/70'
                  }`}
                >
                  <TgEmoji emoji={c.avatar || '💬'} size={15} />
                  <span className="max-w-[120px] truncate">{c.display_name}</span>
                  {c.role_in_cabinet === 'mentor' && (
                    <span
                      className={`text-[8px] px-1 py-0.2 rounded font-extrabold ${
                        isSelected ? 'bg-white/20 text-white' : 'bg-amber-500/20 text-amber-600 dark:text-amber-400'
                      }`}
                    >
                      MENTOR
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-tg-secondary/30 rounded-3xl border border-tg-secondary">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-tg-hint space-y-3">
            <div className="w-14 h-14 rounded-2xl bg-blue-500/10 text-blue-500 flex items-center justify-center text-2xl">
              <TgEmoji emoji={selectedCabinet?.avatar || '💬'} size={32} />
            </div>
            <div>
              <p className="text-sm font-bold text-tg-text">{selectedCabinet?.display_name}</p>
              <p className="text-xs text-tg-hint mt-0.5">
                {isMentor ? 'Siz ushbu guruh mentorsiz. Birinchi e\'lon yoki ko\'rsatmani yuboring!' : 'Guruhga birinchi bo\'lib savol yoki xabar qoldiring!'}
              </p>
            </div>
          </div>
        ) : (
          messages.map((msg) => {
            const isMe =
              msg.is_me ||
              String(msg.sender_id) === String(currentUser?.id) ||
              msg.sender_name === 'Men';
            const isHighlighted = String(highlightedMsgId) === String(msg.id);
            const isPureEmoji = isPureEmojiMessage(msg.content);

            return (
              <div
                key={msg.id}
                id={`chat-bubble-${msg.id}`}
                className={`group flex flex-col transition-all duration-300 ${
                  isMe ? 'items-end' : 'items-start'
                }`}
              >
                {!isMe && msg.sender_name && (
                  <span className="text-[10px] font-bold text-tg-hint mb-0.5 px-2 flex items-center gap-1">
                    {msg.sender_name}
                    {msg.role === 'mentor' && (
                      <span className="text-[8px] bg-blue-500/20 text-blue-600 px-1 py-0.2 rounded font-extrabold">
                        MENTOR
                      </span>
                    )}
                  </span>
                )}

                <div className={`flex items-end gap-1.5 max-w-[88%] sm:max-w-[75%] ${isMe ? 'flex-row' : 'flex-row-reverse'}`}>
                  {/* Quick Reply Trigger Button */}
                  <button
                    type="button"
                    onClick={() => handleReplyTo(msg)}
                    title="Javob berish (Reply)"
                    className="opacity-0 group-hover:opacity-100 focus:opacity-100 hover:opacity-100 p-1.5 rounded-full bg-tg-section hover:bg-tg-secondary text-tg-hint hover:text-blue-500 border border-tg-secondary/60 shadow-xs transition-all cursor-pointer shrink-0 active:scale-90"
                  >
                    <Reply className="w-3.5 h-3.5" />
                  </button>

                  {/* Message Bubble or Big Sticker Emoji */}
                  {isPureEmoji && !msg.reply_to ? (
                    <div
                      className={`relative select-text transition-all p-1 ${
                        isHighlighted ? 'ring-2 ring-blue-500 rounded-2xl scale-105' : ''
                      }`}
                    >
                      <span className="text-3xl sm:text-4xl select-text drop-shadow-xs block py-0.5">
                        <TgText>{msg.content}</TgText>
                      </span>
                      <div className="flex items-center justify-end gap-2 mt-0.5 px-1">
                        <button
                          type="button"
                          onClick={() => handleReplyTo(msg)}
                          className={`text-[9px] font-bold sm:hidden flex items-center gap-0.5 opacity-75 hover:opacity-100 ${
                            isMe ? 'text-blue-500' : 'text-blue-500'
                          }`}
                        >
                          <Reply className="w-2.5 h-2.5" />
                          <span>Javob</span>
                        </button>
                        <span className="text-[9px] font-semibold text-tg-hint/80">
                          {formatTime(msg.sent_at)}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div
                      className={`p-3 rounded-2xl text-xs sm:text-sm shadow-xs break-words relative leading-relaxed transition-all ${
                        isHighlighted ? 'ring-2 ring-blue-500 scale-[1.02] shadow-md' : ''
                      } ${
                        isMe
                          ? 'bg-blue-600 text-white rounded-br-xs'
                          : 'bg-tg-section text-tg-text border border-tg-secondary rounded-bl-xs'
                      }`}
                    >
                      {/* Quoted / Replied-to Message Preview */}
                      {msg.reply_to && (
                        <div
                          onClick={() => scrollToMessage(msg.reply_to!.message_id)}
                          className={`mb-2 p-1.5 pl-2.5 rounded-xl text-xs cursor-pointer border-l-3 transition-all ${
                            isMe
                              ? 'bg-black/20 hover:bg-black/30 border-white text-blue-100'
                              : 'bg-tg-secondary/80 hover:bg-tg-secondary border-blue-500 text-tg-text'
                          }`}
                        >
                          <div className="flex items-center gap-1 font-bold text-[10.5px]">
                            <CornerDownRight className="w-2.5 h-2.5 shrink-0 opacity-80" />
                            <span className={isMe ? 'text-white' : 'text-blue-600 dark:text-blue-400'}>
                              {msg.reply_to.sender_name}
                            </span>
                          </div>
                          <p className="text-[11px] truncate opacity-90 mt-0.5">
                            <TgText>{msg.reply_to.content}</TgText>
                          </p>
                        </div>
                      )}

                      <p className={`whitespace-pre-wrap select-text ${isPureEmoji ? 'text-xl py-0.5' : ''}`}>
                        <TgText>{msg.content}</TgText>
                      </p>

                      <div className="flex items-center justify-between gap-3 mt-1">
                        {/* Mobile-friendly tap to reply button link */}
                        <button
                          type="button"
                          onClick={() => handleReplyTo(msg)}
                          className={`text-[9px] font-bold sm:hidden flex items-center gap-0.5 transition-opacity opacity-75 hover:opacity-100 ${
                            isMe ? 'text-blue-200' : 'text-blue-500'
                          }`}
                        >
                          <Reply className="w-2.5 h-2.5" />
                          <span>Javob</span>
                        </button>

                        <span
                          className={`text-[9px] ml-auto font-medium ${
                            isMe ? 'text-blue-200' : 'text-tg-hint'
                          }`}
                        >
                          {formatTime(msg.sent_at)}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Reply Preview Bar & Message Input Box */}
      <div className="pt-2 space-y-1.5">
        {/* Active Reply Banner (Telegram Style) */}
        {replyingTo && (
          <div className="flex items-center justify-between gap-2 p-2 px-3 bg-tg-section border border-blue-500/30 rounded-2xl shadow-xs animate-in slide-in-from-bottom-2 fade-in">
            <div className="flex items-center gap-2.5 min-w-0 flex-1">
              <div className="w-1 self-stretch bg-blue-500 rounded-full shrink-0" />
              <div className="w-6 h-6 rounded-lg bg-blue-500/15 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
                <Reply className="w-3.5 h-3.5" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-bold text-blue-600 dark:text-blue-400 truncate">
                  {replyingTo.sender_name || (replyingTo.is_me ? 'Siz' : 'Foydalanuvchi')}ga javob berish
                </p>
                <p className="text-[11px] text-tg-hint truncate">
                  {replyingTo.content}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleCancelReply}
              className="p-1.5 rounded-full hover:bg-tg-secondary text-tg-hint hover:text-tg-text transition-colors shrink-0 cursor-pointer"
              title="Javobni bekor qilish"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Telegram Emoji Drawer */}
        {showEmojiPicker && (
          <div className="p-3 bg-tg-section border border-tg-secondary rounded-2xl shadow-lg space-y-2.5 animate-in slide-in-from-bottom-2 fade-in">
            {/* Category Tabs */}
            <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pb-1 border-b border-tg-secondary/60">
              {CHAT_EMOJIS_CATEGORIES.map((cat, idx) => (
                <button
                  key={cat.category}
                  type="button"
                  onClick={() => {
                    triggerHaptic('selection');
                    setActiveEmojiCategoryIdx(idx);
                  }}
                  className={`px-2.5 py-1 rounded-xl text-[11px] font-bold whitespace-nowrap transition-all cursor-pointer ${
                    activeEmojiCategoryIdx === idx
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'bg-tg-secondary/80 text-tg-hint hover:text-tg-text'
                  }`}
                >
                  {cat.category}
                </button>
              ))}
            </div>

            {/* Emojis Grid */}
            <div className="grid grid-cols-8 sm:grid-cols-10 gap-1.5 max-h-36 overflow-y-auto pr-1">
              {CHAT_EMOJIS_CATEGORIES[activeEmojiCategoryIdx].emojis.map((emoji) => (
                <button
                  key={emoji}
                  type="button"
                  onClick={() => handleInsertEmoji(emoji)}
                  className="h-9 flex items-center justify-center text-lg sm:text-xl rounded-xl hover:bg-tg-secondary active:scale-125 transition-all cursor-pointer emoji-font"
                >
                  {emoji.startsWith(':anim_') ? (
                    <TgAnimatedEmoji code={emoji} size="1.6em" />
                  ) : (
                    emoji
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Form */}
        <form onSubmit={handleSendMessage} className="flex items-center gap-2">
          {/* Emoji Drawer Toggle Button */}
          <button
            type="button"
            onClick={() => {
              triggerHaptic('light');
              setShowEmojiPicker((prev) => !prev);
            }}
            className={`p-3 rounded-2xl border transition-all cursor-pointer flex items-center justify-center active:scale-95 shrink-0 ${
              showEmojiPicker
                ? 'bg-blue-600/15 border-blue-500 text-blue-600 dark:text-blue-400'
                : 'bg-tg-secondary border-tg-secondary text-tg-hint hover:text-tg-text'
            }`}
            title="Stiker va Emojilar"
          >
            <Smile className="w-4 h-4" />
          </button>

          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={
              replyingTo
                ? `${replyingTo.sender_name || 'Ushbu xabar'}ga javobingizni yozing...`
                : isMentor
                ? "Mentor sifatida xabar yoki ko'rsatma yozing..."
                : "Guruhga savol yoki xabar yozing..."
            }
            className="flex-1 px-4 py-3 rounded-2xl bg-tg-secondary border border-tg-secondary text-tg-text placeholder-tg-hint text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all emoji-font"
          />
          <button
            type="submit"
            id="btn-send-chat-message"
            disabled={!inputText.trim() || sending}
            className="p-3 rounded-2xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold transition-all shadow-xs cursor-pointer flex items-center justify-center active:scale-95 shrink-0"
            aria-label="Yuborish"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>

      {/* Modal: Create New Group Chat (Mentor) */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-tg-section border border-tg-secondary rounded-3xl p-5 sm:p-6 w-full max-w-md shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-tg-secondary pb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-blue-500/15 text-blue-600 flex items-center justify-center font-bold">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-black text-tg-text">Yangi Guruh Chat Ochish</h3>
                  <p className="text-[11px] text-tg-hint">Mentor sifatida yangi o'quv guruhi yaratish</p>
                </div>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1.5 rounded-full hover:bg-tg-secondary text-tg-hint transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateCabinet} className="space-y-3.5">
              {/* Group Name */}
              <div>
                <label className="block text-xs font-bold text-tg-text mb-1">
                  Guruh Nomi <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={newGroupName}
                  onChange={(e) => setNewGroupName(e.target.value)}
                  placeholder="Masalan: Python Backend Pro #4"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-tg-secondary border border-tg-secondary text-tg-text placeholder-tg-hint text-xs font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                
                {/* Suggestions */}
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {SUGGESTED_NAMES.map((name) => (
                    <button
                      key={name}
                      type="button"
                      onClick={() => setNewGroupName(name)}
                      className="text-[10px] px-2 py-0.5 rounded-lg bg-tg-secondary/70 hover:bg-blue-500/15 hover:text-blue-600 text-tg-hint transition-all cursor-pointer"
                    >
                      + {name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Choose Emoji / Avatar */}
              <div>
                <label className="block text-xs font-bold text-tg-text mb-1">
                  Guruh Belgisi (Emoji Avatar)
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {EMOJI_OPTIONS.map((emoji) => (
                    <button
                      key={emoji}
                      type="button"
                      onClick={() => setNewGroupAvatar(emoji)}
                      className={`w-9 h-9 rounded-xl text-base flex items-center justify-center transition-all cursor-pointer ${
                        newGroupAvatar === emoji
                          ? 'bg-blue-600 text-white scale-110 shadow-sm'
                          : 'bg-tg-secondary hover:bg-tg-secondary/80 text-tg-text'
                      }`}
                    >
                      {emoji}
                    </button>
                  ))}
                </div>
              </div>

              {/* Linked Course (Optional) */}
              <div>
                <label className="block text-xs font-bold text-tg-text mb-1">
                  Bog'langan Kurs (Ixtiyoriy)
                </label>
                <select
                  value={newGroupCourseId}
                  onChange={(e) => setNewGroupCourseId(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-tg-secondary border border-tg-secondary text-tg-text text-xs font-medium cursor-pointer"
                >
                  <option value="">-- Umumiy mentorlik guruhi (Kursga bog'lanmagan) --</option>
                  {courses.map((course) => (
                    <option key={course.id} value={course.id}>
                      {course.title}
                    </option>
                  ))}
                </select>
              </div>

              {/* Description */}
              <div>
                <label className="block text-xs font-bold text-tg-text mb-1">
                  Guruh Tavsifi / Maqsadi
                </label>
                <textarea
                  rows={2}
                  value={newGroupDescription}
                  onChange={(e) => setNewGroupDescription(e.target.value)}
                  placeholder="Masalan: Ushbu guruhda o'quvchilar bilan amaliy vazifalarni va kodlarni tahlil qilamiz..."
                  className="w-full px-3.5 py-2 rounded-xl bg-tg-secondary border border-tg-secondary text-tg-text placeholder-tg-hint text-xs font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* First message */}
              <div>
                <label className="block text-xs font-bold text-tg-text mb-1">
                  Ilk Salomlashish Xabari (Mentor e'loni)
                </label>
                <input
                  type="text"
                  value={newGroupInitialMsg}
                  onChange={(e) => setNewGroupInitialMsg(e.target.value)}
                  placeholder="Masalan: Assalomu alaykum talabalar! Guruhimizga xush kelibsiz."
                  className="w-full px-3.5 py-2 rounded-xl bg-tg-secondary border border-tg-secondary text-tg-text placeholder-tg-hint text-xs font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="pt-2 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 py-2.5 rounded-xl bg-tg-secondary hover:bg-tg-secondary/80 text-tg-text text-xs font-bold cursor-pointer transition-all"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  disabled={!newGroupName.trim() || isCreating}
                  className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 text-white text-xs font-bold cursor-pointer shadow-md transition-all flex items-center justify-center gap-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{isCreating ? 'Ochilmoqda...' : 'Guruhni Ochish'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Edit Group Chat (Mentor) */}
      {showEditModal && selectedCabinet && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-tg-section border border-tg-secondary rounded-3xl p-5 sm:p-6 w-full max-w-md shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-tg-secondary pb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-amber-500/15 text-amber-600 flex items-center justify-center font-bold">
                  <Edit3 className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-black text-tg-text">Guruhni Tahrirlash</h3>
                  <p className="text-[11px] text-tg-hint">Guruh nomi va sozlamalarini yangilash</p>
                </div>
              </div>
              <button
                onClick={() => setShowEditModal(false)}
                className="p-1.5 rounded-full hover:bg-tg-secondary text-tg-hint transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveEditCabinet} className="space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-tg-text mb-1">
                  Guruh Nomi <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={editGroupName}
                  onChange={(e) => setEditGroupName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-tg-secondary border border-tg-secondary text-tg-text text-xs font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-tg-text mb-1">
                  Guruh Belgisi (Emoji Avatar)
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {EMOJI_OPTIONS.map((emoji) => (
                    <button
                      key={emoji}
                      type="button"
                      onClick={() => setEditGroupAvatar(emoji)}
                      className={`w-9 h-9 rounded-xl text-base flex items-center justify-center transition-all cursor-pointer ${
                        editGroupAvatar === emoji
                          ? 'bg-blue-600 text-white scale-110 shadow-sm'
                          : 'bg-tg-secondary hover:bg-tg-secondary/80 text-tg-text'
                      }`}
                    >
                      {emoji}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-tg-text mb-1">
                  Guruh Tavsifi
                </label>
                <textarea
                  rows={2}
                  value={editGroupDescription}
                  onChange={(e) => setEditGroupDescription(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl bg-tg-secondary border border-tg-secondary text-tg-text text-xs font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="pt-2 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="flex-1 py-2.5 rounded-xl bg-tg-secondary hover:bg-tg-secondary/80 text-tg-text text-xs font-bold cursor-pointer transition-all"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  disabled={!editGroupName.trim() || isEditing}
                  className="flex-1 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-bold cursor-pointer shadow-md transition-all flex items-center justify-center gap-1.5"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>{isEditing ? 'Saqlanmoqda...' : 'Saqlash'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Group Members & Info */}
      {showStudentsModal && selectedCabinet && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-tg-section border border-tg-secondary rounded-3xl p-5 sm:p-6 w-full max-w-md shadow-2xl space-y-4 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-tg-secondary pb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-blue-500/15 text-blue-600 flex items-center justify-center font-bold">
                  <Users className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-black text-tg-text">Guruh A'zolari</h3>
                  <p className="text-[11px] text-tg-hint">{students.length} ta faol a'zo</p>
                </div>
              </div>
              <button
                onClick={() => setShowStudentsModal(false)}
                className="p-1.5 rounded-full hover:bg-tg-secondary text-tg-hint transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Group details card */}
            <div className="p-3 bg-tg-secondary/50 rounded-2xl border border-tg-secondary space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="text-xl">{selectedCabinet.avatar || '💬'}</span>
                <span className="text-xs font-bold text-tg-text">{selectedCabinet.display_name}</span>
              </div>
              {selectedCabinet.description && (
                <p className="text-[11px] text-tg-hint">{selectedCabinet.description}</p>
              )}
            </div>

            {/* Invite link copy */}
            <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-2xl flex items-center justify-between gap-2">
              <div className="min-w-0">
                <p className="text-[11px] font-bold text-blue-600 dark:text-blue-400">Guruhga taklif havolasi</p>
                <p className="text-[10px] text-tg-hint truncate">t.me/BilimGoBot?start=group_{selectedCabinet.id}</p>
              </div>
              <button
                onClick={handleCopyInviteLink}
                className="px-2.5 py-1.5 rounded-xl bg-blue-600 text-white font-bold text-[11px] flex items-center gap-1 shrink-0 cursor-pointer active:scale-95 transition-all"
              >
                {copiedLink ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedLink ? 'Nusxalandi' : 'Nusxa'}</span>
              </button>
            </div>

            {/* Students list */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-tg-text">A'zolar Ro'yxati</h4>
              {students.map((student) => (
                <div
                  key={student.id}
                  className="flex items-center justify-between p-2.5 rounded-2xl bg-tg-secondary/40 border border-tg-secondary/50 text-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-full bg-blue-600/20 text-blue-600 flex items-center justify-center font-bold text-xs">
                      {student.full_name.charAt(0)}
                    </div>
                    <div>
                      <p className="font-bold text-tg-text">{student.full_name}</p>
                      <p className="text-[10px] text-tg-hint">@{student.username || 'user'}</p>
                    </div>
                  </div>
                  <span className="text-[10px] text-tg-hint">
                    {new Date(student.joined_at).toLocaleDateString('uz-UZ')}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

