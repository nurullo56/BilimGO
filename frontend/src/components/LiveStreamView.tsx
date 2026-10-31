import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  ThumbsUp,
  Heart,
  Flame,
  PartyPopper,
  Hand,
  Mic,
  MicOff,
  Video,
  VideoOff,
  Users,
  MessageSquare,
  X,
  Check,
  BarChart2,
  Crown,
  Radio,
  Monitor,
  User,
  Volume2,
  PlusCircle,
  Pin,
  PinOff,
  Smile,
  Sparkles,
  ChevronLeft,
  Share2,
} from 'lucide-react';
import { AppView } from '../types';
import { getTelegramUser, triggerHaptic } from '../services/telegram';
import { getApiBaseUrl } from '../services/api';
import { TgText } from './TgEmoji';

interface LiveStreamViewProps {
  sessionId: string | number;
  courseId: string | number;
  onNavigate: (view: AppView) => void;
  onLeave: () => void;
}

interface LiveMessage {
  id: string;
  user_id: number;
  username: string;
  type: 'chat' | 'reaction' | 'question' | 'poll' | 'poll_vote' | 'raise_hand' | 'join' | 'leave';
  content: any;
  timestamp: string;
}

interface Poll {
  id: string;
  question: string;
  options: string[];
  votes: Record<number, number>;
  total_votes?: number;
  is_ended?: boolean;
}

interface RaisedHandUser {
  user_id: number;
  username: string;
  timestamp: string;
}

interface PinnedMessage {
  id: string;
  content: string;
  author_name: string;
  pinned_by: number;
  timestamp: string;
}

interface FloatingReaction {
  id: number;
  emoji: string;
  left: number;
}

export const LiveStreamView: React.FC<LiveStreamViewProps> = ({
  sessionId,
  courseId,
  onNavigate,
  onLeave,
}) => {
  const user = getTelegramUser();
  const [messages, setMessages] = useState<LiveMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [viewerCount, setViewerCount] = useState(1);
  const [likesCount, setLikesCount] = useState(12);
  const [hasLiked, setHasLiked] = useState(false);
  const [floatingReactions, setFloatingReactions] = useState<FloatingReaction[]>([]);

  // Host & Stream State
  const [isHost, setIsHost] = useState(false);
  const [isBroadcasting, setIsBroadcasting] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(false);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [streamStatus, setStreamStatus] = useState<'scheduled' | 'live' | 'ended'>('live');
  const [sessionTitle, setSessionTitle] = useState('Jonli Efir: Amaliy Dars');

  // Student Microphone State
  const [isHandRaised, setIsHandRaised] = useState(false);
  const [canSpeak, setCanSpeak] = useState(false);
  const [isStudentMicActive, setIsStudentMicActive] = useState(false);
  const [activeSpeakerName, setActiveSpeakerName] = useState<string | null>(null);

  // Pinned Message State
  const [pinnedMessage, setPinnedMessage] = useState<PinnedMessage | null>(null);
  const [showPinModal, setShowPinModal] = useState(false);
  const [customPinText, setCustomPinText] = useState('');

  // Modals & Bottom Sheets
  const [showPollModal, setShowPollModal] = useState(false);
  const [showHandsSheet, setShowHandsSheet] = useState(false);
  const [showPollSheet, setShowPollSheet] = useState(false);
  const [pollQuestion, setPollQuestion] = useState('');
  const [pollOptions, setPollOptions] = useState(['Ha', "Yo'q"]);
  const [polls, setPolls] = useState<Record<string, Poll>>({});
  const [raisedHands, setRaisedHands] = useState<RaisedHandUser[]>([]);

  // Media References
  const wsRef = useRef<WebSocket | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const pipVideoRef = useRef<HTMLVideoElement | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const pipStreamRef = useRef<MediaStream | null>(null);
  const studentAudioStreamRef = useRef<MediaStream | null>(null);
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const chatScrollRef = useRef<HTMLDivElement | null>(null);
  const [isPipCamActive, setIsPipCamActive] = useState(false);

  const RTC_CONFIG: RTCConfiguration = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' },
    ],
  };

  const createPeerConnection = (remoteUserId?: number) => {
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
    }

    const pc = new RTCPeerConnection(RTC_CONFIG);
    peerConnectionRef.current = pc;

    pc.onicecandidate = (event) => {
      if (event.candidate && wsRef.current) {
        wsRef.current.send(
          JSON.stringify({
            type: 'webrtc_ice_candidate',
            candidate: event.candidate,
            target_user_id: remoteUserId,
          })
        );
      }
    };

    pc.ontrack = (event) => {
      console.log('Live stream remote track received:', event.streams);
      if (videoRef.current && event.streams[0]) {
        videoRef.current.srcObject = event.streams[0];
        videoRef.current.play().catch((err) => console.warn('Video play warning:', err));
      }
    };

    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((track) => {
        pc.addTrack(track, localStreamRef.current!);
      });
    }

    return pc;
  };

  // 1. Establish WebSocket Connection to Backend
  useEffect(() => {
    const apiBase = getApiBaseUrl();
    const wsProto = apiBase.startsWith('https') ? 'wss:' : 'ws:';
    const host = apiBase.replace(/^https?:\/\//, '');
    const cleanSessionId = String(sessionId).replace('live-', '').replace('live_', '');
    const tgUser = user || getTelegramUser();
    const userId = tgUser?.id || 0;
    const wsUrl = `${wsProto}//${host}/live/ws/${cleanSessionId}?user_id=${userId}`;

    let socket: WebSocket | null = null;
    try {
      socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        console.log('Live WebSocket connected successfully');
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleServerMessage(data);
        } catch (e) {
          console.error('Failed to parse WS message:', e);
        }
      };

      socket.onerror = (err) => {
        console.warn('Live WebSocket error:', err);
      };

      socket.onclose = () => {
        console.log('Live WebSocket connection closed');
      };
    } catch (e) {
      console.error('Could not create WebSocket:', e);
    }

    return () => {
      stopAllMediaTracks();
      if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
        socket.close();
      }
      wsRef.current = null;
    };
  }, [sessionId]);

  useEffect(() => {
    if (isPipCamActive && pipVideoRef.current && pipStreamRef.current) {
      pipVideoRef.current.srcObject = pipStreamRef.current;
      pipVideoRef.current.play().catch(console.error);
    }
  }, [isPipCamActive]);

  const stopPipCamera = () => {
    if (pipStreamRef.current) {
      pipStreamRef.current.getTracks().forEach((t) => t.stop());
      pipStreamRef.current = null;
    }
    setIsPipCamActive(false);
  };

  const stopAllMediaTracks = () => {
    stopPipCamera();
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((t) => t.stop());
      localStreamRef.current = null;
    }
    if (studentAudioStreamRef.current) {
      studentAudioStreamRef.current.getTracks().forEach((t) => t.stop());
      studentAudioStreamRef.current = null;
    }
  };

  const handleServerMessage = (data: any) => {
    const { type, ...rest } = data;

    switch (type) {
      case 'init_session':
        setIsHost(Boolean(data.is_host));
        setSessionTitle(data.title || 'Jonli Efir: Amaliy Dars');
        setStreamStatus(data.status || 'live');
        setViewerCount(data.viewer_count || 1);
        if (data.raised_hands) setRaisedHands(data.raised_hands);
        if (data.pinned_message) setPinnedMessage(data.pinned_message);
        if (data.active_broadcaster) setIsBroadcasting(true);
        break;

      case 'pinned_message':
        setPinnedMessage(data.pinned_message);
        triggerHaptic('medium');
        break;

      case 'unpinned_message':
        setPinnedMessage(null);
        triggerHaptic('light');
        break;

      case 'join':
        setViewerCount(rest.viewer_count || 1);
        addMessage({
          id: `join_${Date.now()}`,
          type: 'join',
          user_id: rest.user_id,
          username: rest.username,
          content: 'efirga qo‘shildi',
          timestamp: new Date().toISOString(),
        });
        break;

      case 'leave':
        setViewerCount(rest.viewer_count || 1);
        break;

      case 'chat':
        addMessage({
          id: rest.id || `chat_${Date.now()}`,
          type: 'chat',
          user_id: rest.user_id,
          username: rest.username,
          content: rest.content,
          timestamp: rest.timestamp || new Date().toISOString(),
        });
        break;

      case 'reaction':
        if (rest.reaction === '👍' || rest.reaction === 'like') {
          setLikesCount((prev) => prev + 1);
        }
        spawnFloatingReaction(rest.reaction || '❤️');
        break;

      case 'poll':
        setPolls((prev) => ({
          ...prev,
          [rest.data.id]: {
            id: rest.data.id,
            question: rest.data.question,
            options: rest.data.options,
            votes: rest.data.votes || {},
            total_votes: 0,
          },
        }));
        setShowPollSheet(true);
        triggerHaptic('medium');
        break;

      case 'poll_update':
        setPolls((prev) => {
          const poll = prev[rest.poll_id];
          if (poll) {
            return {
              ...prev,
              [rest.poll_id]: {
                ...poll,
                votes: rest.votes || {},
                total_votes: rest.total_votes || 0,
              },
            };
          }
          return prev;
        });
        break;

      case 'raise_hand':
        if (rest.raised_hands) setRaisedHands(rest.raised_hands);
        addMessage({
          id: `hand_${Date.now()}`,
          type: 'raise_hand',
          user_id: rest.user_id,
          username: rest.username,
          content: 'qo‘l ko‘tardi ✋',
          timestamp: new Date().toISOString(),
        });
        triggerHaptic('light');
        break;

      case 'lower_hand':
        if (rest.raised_hands) setRaisedHands(rest.raised_hands);
        break;

      case 'grant_mic':
        setCanSpeak(true);
        triggerHaptic('success');
        startStudentMicrophone();
        break;

      case 'revoke_mic':
        setCanSpeak(false);
        stopStudentMicrophone();
        triggerHaptic('medium');
        break;

      case 'speaker_joined':
        setActiveSpeakerName(rest.username);
        if (rest.raised_hands) setRaisedHands(rest.raised_hands);
        break;

      case 'speaker_left':
        setActiveSpeakerName(null);
        break;

      case 'broadcast_active':
      case 'start_broadcast':
        setIsBroadcasting(true);
        setStreamStatus('live');
        if (!isHost) {
          createPeerConnection(rest.broadcaster?.user_id || rest.user_id);
        }
        break;

      case 'stop_broadcast':
        setIsBroadcasting(false);
        if (!isHost && videoRef.current) {
          videoRef.current.srcObject = null;
        }
        break;

      case 'webrtc_offer':
        if (!isHost && rest.data) {
          (async () => {
            try {
              const pc = peerConnectionRef.current || createPeerConnection(rest.sender_id);
              await pc.setRemoteDescription(new RTCSessionDescription(rest.data));
              const answer = await pc.createAnswer();
              await pc.setLocalDescription(answer);
              if (wsRef.current) {
                wsRef.current.send(
                  JSON.stringify({
                    type: 'webrtc_answer',
                    target_user_id: rest.sender_id,
                    data: answer,
                  })
                );
              }
            } catch (err) {
              console.warn('WebRTC offer handling warning:', err);
            }
          })();
        }
        break;

      case 'webrtc_answer':
        if (isHost && rest.data && peerConnectionRef.current) {
          (async () => {
            try {
              await peerConnectionRef.current.setRemoteDescription(
                new RTCSessionDescription(rest.data)
              );
            } catch (err) {
              console.warn('WebRTC answer handling warning:', err);
            }
          })();
        }
        break;

      case 'webrtc_ice_candidate':
        if (rest.data && peerConnectionRef.current) {
          (async () => {
            try {
              await peerConnectionRef.current.addIceCandidate(
                new RTCIceCandidate(rest.data)
              );
            } catch (err) {
              console.warn('WebRTC candidate handling warning:', err);
            }
          })();
        }
        break;

      case 'stream_status':
        setStreamStatus(rest.status);
        break;

      default:
        break;
    }
  };

  const addMessage = (msg: LiveMessage) => {
    setMessages((prev) => [...prev.slice(-60), msg]);
    setTimeout(() => {
      if (chatScrollRef.current) {
        chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
      }
    }, 40);
  };

  const spawnFloatingReaction = (emoji: string) => {
    const id = Date.now() + Math.random();
    const left = Math.floor(Math.random() * 50) + 40; // over the video/chat
    setFloatingReactions((prev) => [...prev.slice(-12), { id, emoji, left }]);
    setTimeout(() => {
      setFloatingReactions((prev) => prev.filter((r) => r.id !== id));
    }, 2000);
  };

  // 2. Broadcaster Host Engine
  const startBroadcasting = async (mode: 'camera' | 'screen' = 'camera') => {
    try {
      triggerHaptic('medium');
      let stream: MediaStream;

      if (mode === 'screen') {
        stream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: true,
        });
        setIsScreenSharing(true);

        // Auto activate webcam overlay (PiP) when screen sharing
        try {
          const camStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
            audio: false,
          });
          pipStreamRef.current = camStream;
          setIsPipCamActive(true);
        } catch (camErr) {
          console.warn('PiP Camera startup skipped:', camErr);
        }
      } else {
        stopPipCamera();
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: true,
        });
        setIsScreenSharing(false);
      }

      localStreamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(console.error);
      }

      setIsBroadcasting(true);
      setIsMuted(false);
      setIsVideoOff(false);

      if (wsRef.current) {
        wsRef.current.send(
          JSON.stringify({
            type: 'start_broadcast',
            has_video: true,
            has_audio: true,
            mode,
          })
        );

        try {
          const pc = createPeerConnection();
          const offer = await pc.createOffer();
          await pc.setLocalDescription(offer);
          wsRef.current.send(
            JSON.stringify({
              type: 'webrtc_offer',
              data: offer,
            })
          );
        } catch (offerErr) {
          console.warn('Host WebRTC offer warning:', offerErr);
        }
      }
      triggerHaptic('success');
    } catch (err: any) {
      console.error('Camera/Mic permission error:', err);
      alert('Kamera yoki mikrofonga ruxsat berilmadi.');
    }
  };

  const stopBroadcasting = () => {
    triggerHaptic('light');
    stopAllMediaTracks();
    if (videoRef.current) videoRef.current.srcObject = null;
    setIsBroadcasting(false);
    setIsScreenSharing(false);
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: 'stop_broadcast' }));
    }
  };

  const toggleMic = () => {
    if (!localStreamRef.current) return;
    const audioTrack = localStreamRef.current.getAudioTracks()[0];
    if (audioTrack) {
      audioTrack.enabled = !audioTrack.enabled;
      setIsMuted(!audioTrack.enabled);
      triggerHaptic('light');
    }
  };

  const toggleVideo = () => {
    if (!localStreamRef.current) return;
    const videoTrack = localStreamRef.current.getVideoTracks()[0];
    if (videoTrack) {
      videoTrack.enabled = !videoTrack.enabled;
      setIsVideoOff(!videoTrack.enabled);
      triggerHaptic('light');
    }
  };

  const togglePipCam = async () => {
    if (isPipCamActive) {
      stopPipCamera();
      triggerHaptic('light');
    } else {
      try {
        const camStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
          audio: false,
        });
        pipStreamRef.current = camStream;
        setIsPipCamActive(true);
        triggerHaptic('success');
      } catch (err) {
        console.error('PiP camera permission error:', err);
        alert('Kameraga ruxsat berilmadi.');
      }
    }
  };

  // 3. Student Voice Q&A
  const startStudentMicrophone = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      studentAudioStreamRef.current = stream;
      setIsStudentMicActive(true);
      triggerHaptic('success');
    } catch (err) {
      console.error('Student mic permission error:', err);
    }
  };

  const stopStudentMicrophone = () => {
    if (studentAudioStreamRef.current) {
      studentAudioStreamRef.current.getTracks().forEach((t) => t.stop());
      studentAudioStreamRef.current = null;
    }
    setIsStudentMicActive(false);
    setCanSpeak(false);
    setIsHandRaised(false);
  };

  const toggleRaiseHand = () => {
    if (!wsRef.current) return;
    const newHandState = !isHandRaised;
    setIsHandRaised(newHandState);
    wsRef.current.send(
      JSON.stringify({
        type: newHandState ? 'raise_hand' : 'lower_hand',
      })
    );
    triggerHaptic('light');
  };

  const handleGrantMic = (targetUserId: number) => {
    if (!wsRef.current || !isHost) return;
    triggerHaptic('medium');
    wsRef.current.send(
      JSON.stringify({
        type: 'grant_mic',
        target_user_id: targetUserId,
      })
    );
  };

  const handleRevokeMic = (targetUserId: number) => {
    if (!wsRef.current || !isHost) return;
    triggerHaptic('light');
    wsRef.current.send(
      JSON.stringify({
        type: 'revoke_mic',
        target_user_id: targetUserId,
      })
    );
  };

  // 4. Pin / Unpin
  const handlePinMessage = (content: string, authorName: string = 'Spiker', messageId?: string) => {
    if (!wsRef.current || !isHost || !content.trim()) return;
    wsRef.current.send(
      JSON.stringify({
        type: 'pin_message',
        content: content.trim(),
        author_name: authorName,
        message_id: messageId,
      })
    );
    setShowPinModal(false);
    setCustomPinText('');
    triggerHaptic('success');
  };

  const handleUnpinMessage = () => {
    if (!wsRef.current || !isHost) return;
    wsRef.current.send(JSON.stringify({ type: 'unpin_message' }));
    triggerHaptic('light');
  };

  // 5. Send Chat / Like / Reactions
  const sendMessage = () => {
    if (!inputText.trim() || !wsRef.current) return;
    wsRef.current.send(
      JSON.stringify({
        type: 'chat',
        content: inputText.trim(),
      })
    );
    setInputText('');
    triggerHaptic('light');
  };

  const handleLike = () => {
    if (!hasLiked) {
      setLikesCount((prev) => prev + 1);
      setHasLiked(true);
    }
    sendReaction('👍');
  };

  const sendReaction = (reaction: string) => {
    if (!wsRef.current) return;
    wsRef.current.send(JSON.stringify({ type: 'reaction', reaction }));
    spawnFloatingReaction(reaction);
    triggerHaptic('medium');
  };

  const votePoll = (pollId: string, optionIndex: number) => {
    if (!wsRef.current) return;
    wsRef.current.send(
      JSON.stringify({
        type: 'poll_vote',
        poll_id: pollId,
        option_index: optionIndex,
      })
    );
    triggerHaptic('light');
  };

  const createPoll = () => {
    if (!pollQuestion.trim() || pollOptions.length < 2 || !wsRef.current) return;
    wsRef.current.send(
      JSON.stringify({
        type: 'create_poll',
        question: pollQuestion.trim(),
        options: pollOptions.filter((o) => o.trim().length > 0),
      })
    );
    setShowPollModal(false);
    setPollQuestion('');
    setPollOptions(['Ha', "Yo'q"]);
    triggerHaptic('success');
  };

  return (
    <div className="flex flex-col h-[100dvh] bg-[#0f0f0f] text-white font-sans overflow-hidden select-none">
      {/* 1. TOP 16:9 YOUTUBE STYLE VIDEO PLAYER CONTAINER */}
      <div className="relative w-full aspect-video sm:max-h-[380px] bg-black shrink-0 flex items-center justify-center overflow-hidden border-b border-[#272727]">
        {/* Main Video Viewport */}
        <video
          ref={videoRef}
          className={`w-full h-full object-contain ${isVideoOff ? 'hidden' : 'block'}`}
          autoPlay
          playsInline
          muted={isHost}
        />

        {/* Video Off or Stream Waiting Placeholder */}
        {(!isBroadcasting || isVideoOff) && (
          <div className="text-center p-4 space-y-2 z-10 animate-in fade-in">
            <div className="w-16 h-16 sm:w-20 sm:h-20 mx-auto rounded-full bg-gradient-to-tr from-rose-600 via-indigo-600 to-amber-500 p-0.5 shadow-2xl flex items-center justify-center">
              <div className="w-full h-full rounded-full bg-[#181818] flex items-center justify-center">
                <Radio className="w-8 h-8 sm:w-9 sm:h-9 text-rose-500 animate-pulse" />
              </div>
            </div>
            <h3 className="font-extrabold text-sm sm:text-base text-white">
              {isHost
                ? 'Efir Studiyasi'
                : isBroadcasting
                ? 'Spiker kamerasi o‘chirilgan'
                : 'Jonli efir boshlanishi kutilmoqda...'}
            </h3>
            {isHost && !isBroadcasting && (
              <button
                onClick={() => startBroadcasting('camera')}
                className="mt-2 px-5 py-2 rounded-full bg-rose-600 hover:bg-rose-700 active:scale-95 text-white font-black text-xs shadow-lg flex items-center gap-1.5 mx-auto cursor-pointer"
              >
                <Video className="w-3.5 h-3.5" />
                <span>Kamera & Mikrofonni Yoqish</span>
              </button>
            )}
          </div>
        )}

        {/* Player Top Navigation Overlay */}
        <div className="absolute top-2 left-2 right-2 z-20 flex items-center justify-between pointer-events-auto">
          <button
            onClick={() => {
              triggerHaptic('light');
              stopAllMediaTracks();
              onLeave();
            }}
            className="p-1.5 rounded-full bg-black/60 backdrop-blur-md text-white hover:bg-black/80 transition cursor-pointer"
            title="Orqaga"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-600 text-[11px] font-black tracking-wider uppercase shadow-md">
              <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
              <span>LIVE</span>
            </div>
            <div className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-md text-xs font-bold text-gray-200">
              <Users className="w-3.5 h-3.5 text-blue-400" />
              <span>{viewerCount}</span>
            </div>
          </div>
        </div>

        {/* Picture-in-Picture Floating Camera Overlay during Screen Share */}
        {isScreenSharing && isPipCamActive && (
          <div className="absolute bottom-12 right-3 z-30 group cursor-grab active:cursor-grabbing animate-in fade-in zoom-in-95">
            <div className="relative w-28 h-20 sm:w-40 sm:h-28 rounded-2xl overflow-hidden border-2 border-blue-500 shadow-2xl bg-black">
              <video
                ref={pipVideoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover scale-x-[-1]"
              />
              <div className="absolute top-1 left-1 px-1.5 py-0.5 rounded bg-black/60 backdrop-blur-md text-[9px] font-bold text-white flex items-center gap-1">
                <Video className="w-2.5 h-2.5 text-rose-400 animate-pulse" />
                <span>Spiker</span>
              </div>
              <button
                onClick={togglePipCam}
                className="absolute top-1 right-1 p-1 rounded-full bg-black/60 hover:bg-rose-600 text-white/80 hover:text-white opacity-0 group-hover:opacity-100 transition cursor-pointer"
                title="Kamerani yopish"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          </div>
        )}

        {/* Host Control Pills Inside Player (Bottom-Right of Video) */}
        {isHost && isBroadcasting && (
          <div className="absolute bottom-2 right-2 z-20 flex items-center gap-1 bg-black/70 backdrop-blur-md p-1 rounded-full border border-white/10">
            <button
              onClick={toggleMic}
              className={`p-1.5 rounded-full transition cursor-pointer ${
                isMuted ? 'bg-rose-600 text-white' : 'bg-white/10 hover:bg-white/20 text-white'
              }`}
              title="Mikrofon"
            >
              {isMuted ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />}
            </button>

            <button
              onClick={toggleVideo}
              className={`p-1.5 rounded-full transition cursor-pointer ${
                isVideoOff ? 'bg-rose-600 text-white' : 'bg-white/10 hover:bg-white/20 text-white'
              }`}
              title="Kamera"
            >
              {isVideoOff ? <VideoOff className="w-3.5 h-3.5" /> : <Video className="w-3.5 h-3.5" />}
            </button>

            <button
              onClick={() =>
                isScreenSharing
                  ? startBroadcasting('camera')
                  : startBroadcasting('screen')
              }
              className={`p-1.5 rounded-full transition cursor-pointer ${
                isScreenSharing ? 'bg-blue-600 text-white' : 'bg-white/10 hover:bg-white/20 text-gray-300'
              }`}
              title="Ekran ulashish"
            >
              <Monitor className="w-3.5 h-3.5" />
            </button>

            {isScreenSharing && (
              <button
                onClick={togglePipCam}
                className={`p-1.5 rounded-full transition cursor-pointer ${
                  isPipCamActive ? 'bg-indigo-600 text-white' : 'bg-white/10 hover:bg-white/20 text-gray-400'
                }`}
                title={isPipCamActive ? "Mini kamerani yopish" : "Mini kamerani (PiP) yoqish"}
              >
                <User className="w-3.5 h-3.5" />
              </button>
            )}

            <button
              onClick={stopBroadcasting}
              className="px-2 py-1 rounded-full bg-rose-600 hover:bg-rose-700 text-white text-[10px] font-black uppercase cursor-pointer"
            >
              Tugatish
            </button>
          </div>
        )}

        {/* Floating Heart Reactions Animation Over Video */}
        <div className="absolute inset-0 pointer-events-none z-30 overflow-hidden">
          {floatingReactions.map((r) => (
            <div
              key={r.id}
              className="absolute bottom-4 text-3xl animate-float-up opacity-90 drop-shadow-md"
              style={{ left: `${r.left}%` }}
            >
              {r.emoji}
            </div>
          ))}
        </div>
      </div>

      {/* 2. MIDDLE META BAR: STREAM TITLE, LIKE & ACTION BUTTONS */}
      <div className="px-3.5 py-2.5 bg-[#181818] border-b border-[#272727] space-y-2 shrink-0">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="font-extrabold text-sm text-white truncate">{sessionTitle}</h1>
            <p className="text-[11px] text-gray-400 mt-0.5 flex items-center gap-1.5">
              <span>BilimGo Jonli Efir</span>
              <span>•</span>
              <span className="text-emerald-400 font-bold">Faol efir</span>
            </p>
          </div>

          {/* Quick Action Buttons (YouTube Style Pill Buttons) */}
          <div className="flex items-center gap-1.5 shrink-0">
            {/* Like Button */}
            <button
              onClick={handleLike}
              className={`px-3 py-1.5 rounded-full text-xs font-bold flex items-center gap-1.5 transition cursor-pointer ${
                hasLiked
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-[#272727] hover:bg-[#333333] text-gray-200'
              }`}
            >
              <ThumbsUp className={`w-3.5 h-3.5 ${hasLiked ? 'fill-current' : ''}`} />
              <span>{likesCount}</span>
            </button>

            {/* Student Raise Hand (Voice Q&A) */}
            {!isHost && (
              <button
                onClick={toggleRaiseHand}
                className={`px-3 py-1.5 rounded-full text-xs font-bold flex items-center gap-1.5 transition cursor-pointer ${
                  isHandRaised
                    ? 'bg-amber-500 text-black ring-1 ring-amber-300'
                    : 'bg-[#272727] hover:bg-[#333333] text-amber-400'
                }`}
              >
                <Hand className={`w-3.5 h-3.5 ${isHandRaised ? 'animate-bounce' : ''}`} />
                <span>{isHandRaised ? 'Qo‘l tushirish' : 'Savol berish'}</span>
              </button>
            )}

            {/* Host Quick Toolbar */}
            {isHost && (
              <>
                <button
                  onClick={() => setShowHandsSheet(true)}
                  className="px-2.5 py-1.5 rounded-full bg-[#272727] hover:bg-[#333333] text-amber-400 text-xs font-bold flex items-center gap-1 cursor-pointer"
                  title="Qo'l ko'targanlar"
                >
                  <Hand className="w-3.5 h-3.5" />
                  {raisedHands.length > 0 && (
                    <span className="w-4 h-4 rounded-full bg-amber-500 text-black text-[10px] font-black flex items-center justify-center">
                      {raisedHands.length}
                    </span>
                  )}
                </button>

                <button
                  onClick={() => setShowPollModal(true)}
                  className="px-2.5 py-1.5 rounded-full bg-[#272727] hover:bg-[#333333] text-indigo-400 text-xs font-bold flex items-center gap-1 cursor-pointer"
                  title="So'rovnoma"
                >
                  <BarChart2 className="w-3.5 h-3.5" />
                </button>

                <button
                  onClick={() => setShowPinModal(true)}
                  className="px-2.5 py-1.5 rounded-full bg-[#272727] hover:bg-[#333333] text-amber-400 text-xs font-bold flex items-center gap-1 cursor-pointer"
                  title="E'lon qadash"
                >
                  <Pin className="w-3.5 h-3.5" />
                </button>
              </>
            )}
          </div>
        </div>

        {/* Active Speaking Student Voice Banner */}
        {activeSpeakerName && (
          <div className="px-3 py-1 rounded-xl bg-emerald-950/80 border border-emerald-500/40 text-emerald-300 text-xs font-bold flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <Volume2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>{activeSpeakerName} ovozli savol bermoqda...</span>
          </div>
        )}

        {/* Student Mic Active Card */}
        {isStudentMicActive && (
          <div className="p-2 rounded-xl bg-emerald-950/90 border border-emerald-500/60 text-emerald-200 text-xs flex items-center justify-between gap-2 animate-in zoom-in-95">
            <div className="flex items-center gap-2 font-black">
              <Mic className="w-4 h-4 text-emerald-400 animate-pulse" />
              <span>Mikrofoningiz faol!</span>
            </div>
            <button
              onClick={stopStudentMicrophone}
              className="px-2.5 py-1 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-bold text-[10px] cursor-pointer"
            >
              Tugatish
            </button>
          </div>
        )}
      </div>

      {/* 3. YOUTUBE STYLE PINNED COMMENT (RIGHT ABOVE THE CHAT) */}
      {pinnedMessage && (
        <div className="mx-3.5 mt-2.5 p-2.5 px-3 rounded-xl bg-[#222222] border-l-4 border-amber-400 shadow-md flex items-start justify-between gap-2 shrink-0 animate-in slide-in-from-top-1">
          <div className="flex items-start gap-2 min-w-0">
            <Pin className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] font-black uppercase text-amber-400">
                  Qadalgan xabar
                </span>
                <span className="text-[10px] text-gray-400 font-bold truncate">
                  • {pinnedMessage.author_name}
                </span>
              </div>
              <p className="text-xs text-gray-100 font-medium leading-snug mt-0.5 break-words">
                <TgText>{pinnedMessage.content}</TgText>
              </p>
            </div>
          </div>

          {isHost && (
            <button
              onClick={handleUnpinMessage}
              className="p-1 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white shrink-0 cursor-pointer"
              title="Qadashni bekor qilish"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      )}

      {/* 4. YOUTUBE STYLE LIVE CHAT / KOMMENTARIYALAR SECTION */}
      <div className="flex-1 flex flex-col min-h-0 bg-[#0f0f0f] mt-1">
        {/* Chat Section Header */}
        <div className="px-3.5 py-1.5 flex items-center justify-between border-b border-[#222222] text-xs font-bold text-gray-400">
          <div className="flex items-center gap-1.5">
            <MessageSquare className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-white">Jonli chat</span>
          </div>
          <span className="text-[11px] text-gray-500">Barcha xabarlar</span>
        </div>

        {/* Scrollable Comments Stream */}
        <div
          ref={chatScrollRef}
          className="flex-1 overflow-y-auto px-3.5 py-2 space-y-2.5 scrollbar-thin scrollbar-thumb-[#333333]"
        >
          {messages.length === 0 && (
            <p className="text-xs text-gray-500 text-center py-6">
              Chatga birinchi bo'lib fikringizni yozing! 👇
            </p>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className="flex items-start gap-2 text-xs group">
              {msg.type === 'join' && (
                <div className="text-[11px] text-emerald-400/80 font-medium">
                  👋 <b>{msg.username}</b> {msg.content}
                </div>
              )}
              {msg.type === 'raise_hand' && (
                <div className="text-[11px] text-amber-400 font-bold">
                  ✋ <b>{msg.username}</b> {msg.content}
                </div>
              )}
              {msg.type === 'chat' && (
                <div className="flex items-start justify-between gap-2 w-full leading-relaxed">
                  <div className="min-w-0">
                    <span className="font-extrabold text-blue-400 text-xs mr-1.5">
                      {msg.username}:
                    </span>
                    <span className="text-gray-200 text-xs break-words">
                      <TgText>{msg.content}</TgText>
                    </span>
                  </div>

                  {/* Host Pin Button on Hover */}
                  {isHost && (
                    <button
                      onClick={() => handlePinMessage(msg.content, msg.username, msg.id)}
                      className="opacity-0 group-hover:opacity-100 p-1 rounded-md bg-[#222222] hover:bg-amber-500/20 text-gray-400 hover:text-amber-400 transition cursor-pointer shrink-0"
                      title="Qadab qo'yish (Pin)"
                    >
                      <Pin className="w-3 h-3" />
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* 5. BOTTOM COMMENT INPUT BAR (YOUTUBE LIVE STYLE) */}
        <div className="p-2.5 bg-[#181818] border-t border-[#272727] flex items-center gap-2 shrink-0">
          <div className="flex-1 flex items-center bg-[#222222] border border-[#333333] rounded-full pl-3.5 pr-1 py-1">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Fikr yoki savolingizni yozing..."
              className="flex-1 bg-transparent text-white text-xs placeholder-gray-500 outline-none"
            />
            <button
              onClick={sendMessage}
              disabled={!inputText.trim()}
              className="w-8 h-8 rounded-full bg-blue-600 hover:bg-blue-700 disabled:opacity-30 text-white flex items-center justify-center transition cursor-pointer shadow-md"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Quick Floating Reaction Emojis */}
          <div className="flex items-center gap-1 bg-[#222222] p-1 rounded-full border border-[#333333] shrink-0">
            {['❤️', '🔥', '👏'].map((emoji) => (
              <button
                key={emoji}
                onClick={() => sendReaction(emoji)}
                className="w-7 h-7 rounded-full hover:bg-white/10 active:scale-125 transition flex items-center justify-center text-sm cursor-pointer"
              >
                {emoji}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* MODAL: CUSTOM PIN ANNOUNCEMENT */}
      {showPinModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-sm bg-[#1c1c1c] border border-[#333333] rounded-3xl p-5 space-y-4 shadow-2xl animate-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-[#2c2c2c] pb-3">
              <h3 className="font-bold text-sm text-white flex items-center gap-2">
                <Pin className="w-4 h-4 text-amber-400" />
                <span>Efirga Xabar / E'lon Qadash</span>
              </h3>
              <button
                onClick={() => setShowPinModal(false)}
                className="p-1 rounded-lg text-gray-400 hover:text-white cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2">
              <textarea
                rows={3}
                value={customPinText}
                onChange={(e) => setCustomPinText(e.target.value)}
                placeholder="Masalan: Dars boshlandi! Barcha savollaringizni chatda qoldiring..."
                className="w-full bg-[#272727] border border-[#333333] rounded-xl p-3 text-white text-xs outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#2c2c2c]">
              <button
                onClick={() => setShowPinModal(false)}
                className="px-4 py-2 rounded-xl bg-[#272727] text-white text-xs font-bold cursor-pointer"
              >
                Bekor qilish
              </button>
              <button
                onClick={() => handlePinMessage(customPinText, user?.first_name || 'Spiker')}
                disabled={!customPinText.trim()}
                className="px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-black font-extrabold text-xs transition shadow-md cursor-pointer"
              >
                📌 Qadash
              </button>
            </div>
          </div>
        </div>
      )}

      {/* BOTTOM SHEET: RAISED HANDS QUEUE (HOST ONLY) */}
      {showHandsSheet && isHost && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-end sm:items-center justify-center p-0 sm:p-4">
          <div className="w-full max-w-sm bg-[#1c1c1c] border border-[#333333] rounded-t-3xl sm:rounded-3xl p-5 space-y-4 shadow-2xl max-h-[75vh] flex flex-col animate-in slide-in-from-bottom-5">
            <div className="flex items-center justify-between border-b border-[#2c2c2c] pb-3">
              <h3 className="font-bold text-sm text-amber-400 flex items-center gap-2">
                <Hand className="w-4 h-4" />
                <span>Qo‘l Ko‘targanlar ({raisedHands.length})</span>
              </h3>
              <button
                onClick={() => setShowHandsSheet(false)}
                className="p-1 rounded-lg text-gray-400 hover:text-white cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2">
              {raisedHands.length === 0 ? (
                <p className="text-xs text-gray-500 text-center py-6">
                  Hozircha hech kim qo‘l ko‘tarmagan.
                </p>
              ) : (
                raisedHands.map((h) => (
                  <div
                    key={h.user_id}
                    className="p-3 rounded-2xl bg-[#272727] border border-[#333333] flex items-center justify-between gap-2"
                  >
                    <div className="min-w-0">
                      <p className="font-bold text-xs text-white truncate">{h.username}</p>
                      <p className="text-[10px] text-amber-400">Mikrofon so‘ramoqda</p>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <button
                        onClick={() => {
                          handleGrantMic(h.user_id);
                          setShowHandsSheet(false);
                        }}
                        className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-black text-xs flex items-center gap-1 cursor-pointer"
                      >
                        <Mic className="w-3.5 h-3.5" />
                        <span>Ruxsat</span>
                      </button>
                      <button
                        onClick={() => handleRevokeMic(h.user_id)}
                        className="p-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-gray-400 cursor-pointer"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* MODAL: CREATE POLL */}
      {showPollModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-sm bg-[#1c1c1c] border border-[#333333] rounded-3xl p-5 space-y-4 shadow-2xl animate-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-[#2c2c2c] pb-3">
              <h3 className="font-bold text-sm text-white flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-indigo-400" />
                <span>Yangi Tezkor So‘rovnoma</span>
              </h3>
              <button
                onClick={() => setShowPollModal(false)}
                className="p-1 rounded-lg text-gray-400 hover:text-white cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3">
              <input
                type="text"
                value={pollQuestion}
                onChange={(e) => setPollQuestion(e.target.value)}
                placeholder="Savolni kiriting..."
                className="w-full bg-[#272727] border border-[#333333] rounded-xl px-3 py-2 text-white text-xs outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <div className="space-y-1.5">
                {pollOptions.map((opt, idx) => (
                  <input
                    key={idx}
                    type="text"
                    value={opt}
                    onChange={(e) => {
                      const updated = [...pollOptions];
                      updated[idx] = e.target.value;
                      setPollOptions(updated);
                    }}
                    placeholder={`Variant ${idx + 1}`}
                    className="w-full bg-[#272727] border border-[#333333] rounded-xl px-3 py-1.5 text-white text-xs outline-none"
                  />
                ))}
                {pollOptions.length < 4 && (
                  <button
                    onClick={() => setPollOptions([...pollOptions, ''])}
                    className="text-[11px] text-indigo-400 font-bold hover:underline cursor-pointer"
                  >
                    + Variant qo‘shish
                  </button>
                )}
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#2c2c2c]">
              <button
                onClick={() => setShowPollModal(false)}
                className="px-4 py-2 rounded-xl bg-[#272727] text-white text-xs font-bold cursor-pointer"
              >
                Bekor qilish
              </button>
              <button
                onClick={createPoll}
                disabled={!pollQuestion.trim()}
                className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-bold transition shadow-md cursor-pointer"
              >
                Efirga chiqarish
              </button>
            </div>
          </div>
        </div>
      )}

      {/* FLOATING KEYFRAMES */}
      <style>{`
        @keyframes floatUp {
          0% { opacity: 1; transform: translateY(0) scale(1); }
          100% { opacity: 0; transform: translateY(-130px) scale(1.5); }
        }
        .animate-float-up {
          animation: floatUp 2s ease-out forwards;
        }
      `}</style>
    </div>
  );
};
