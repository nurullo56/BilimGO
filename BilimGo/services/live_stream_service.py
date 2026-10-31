from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

from core.cache import cache_service
from core.config import settings
from db.database import database
from db.repositories.live_session_repo import LiveSessionRepository
from db.repositories.user_repo import UserRepository
from services.userbot_client import UserbotClient

logger = logging.getLogger(__name__)


class LiveEventType(str, Enum):
    """Live event turlari"""
    JOIN = "join"
    LEAVE = "leave"
    CHAT = "chat"
    REACTION = "reaction"
    QUESTION = "question"
    ANSWER = "answer"
    POLL = "poll"
    POLL_UPDATE = "poll_update"
    POLL_ENDED = "poll_ended"
    POLL_VOTE = "poll_vote"
    RAISE_HAND = "raise_hand"
    LOWER_HAND = "lower_hand"
    GRANT_MIC = "grant_mic"
    REVOKE_MIC = "revoke_mic"
    START_BROADCAST = "start_broadcast"
    STOP_BROADCAST = "stop_broadcast"
    WEBRTC_OFFER = "webrtc_offer"
    WEBRTC_ANSWER = "webrtc_answer"
    WEBRTC_ICE_CANDIDATE = "webrtc_ice_candidate"
    STREAM_STATUS = "stream_status"
    VIEWER_COUNT = "viewer_count"
    MODERATION = "moderation"


@dataclass
class LiveMessage:
    """Live xabar"""
    id: str
    session_id: str
    user_id: int
    username: str
    type: LiveEventType
    content: Any
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "username": self.username,
            "type": self.type.value,
            "content": self.content,
            "timestamp": self.timestamp,
        }


@dataclass
class LiveViewer:
    """Live tomoshabin"""
    user_id: int
    username: str
    joined_at: str
    is_hand_raised: bool = False
    is_moderator: bool = False
    is_host: bool = False
    can_speak: bool = False


@dataclass
class LivePoll:
    """Live so'rovnoma"""
    id: str
    question: str
    options: List[str]
    votes: Dict[int, int] = field(default_factory=dict)
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class LiveStreamManager:
    """Live stream boshqaruvi (WebRTC Signaling + WebSocket + Real-time Audio/Video)"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._user_sockets: Dict[str, Dict[int, WebSocket]] = {}
        self._viewers: Dict[str, Dict[int, LiveViewer]] = {}
        self._polls: Dict[str, Dict[str, LivePoll]] = {}
        self._questions: Dict[str, List[Dict]] = {}
        self._chat_history: Dict[str, List[LiveMessage]] = {}
        self._active_broadcasters: Dict[str, Dict[str, Any]] = {}
        self._raised_hands: Dict[str, List[Dict[str, Any]]] = {}
        self._pinned_messages: Dict[str, Optional[Dict[str, Any]]] = {}
        self._userbot = UserbotClient()

        logger.info("LiveStreamManager initialized")

    # ========== SESSION MANAGEMENT ==========

    async def create_session(
        self,
        course_id: int,
        mentor_id: int,
        title: str,
        description: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Yangi live session yaratish"""
        session_id = f"live_{uuid.uuid4().hex[:10]}"
        stream_key = f"sk_{uuid.uuid4().hex[:16]}"

        session_data = {
            "id": session_id,
            "course_id": course_id,
            "mentor_id": mentor_id,
            "title": title,
            "description": description or "",
            "stream_key": stream_key,
            "status": "scheduled",
            "viewer_count": 0,
            "total_viewers": 0,
            "scheduled_at": scheduled_at.isoformat() if scheduled_at else datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "stream_url": f"{settings.webapp.base_url}/live/{session_id}",
        }

        # DB ga yozish
        repo = LiveSessionRepository(database.conn)
        db_id = await repo.create(
            course_id=course_id,
            mentor_id=mentor_id,
            scheduled_at=session_data["scheduled_at"],
            title=title,
            description=description,
        )

        session_id = str(db_id)
        session_data["id"] = session_id
        session_data["stream_url"] = f"{settings.webapp.base_url}/live/{session_id}"

        # Xotirada saqlash
        self._sessions[session_id] = session_data
        await cache_service.set(f"live:session:{session_id}", session_data, ttl=86400)

        logger.info(f"Live session created: {session_id} by mentor {mentor_id}")
        return session_data

    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Session ma'lumotlarini olish"""
        if session_id in self._sessions:
            return self._sessions[session_id]

        cached = await cache_service.get(f"live:session:{session_id}")
        if cached:
            self._sessions[session_id] = cached
            return cached

        repo = LiveSessionRepository(database.conn)
        session = await repo.get_by_id(session_id)
        if not session:
            return None

        data = {
            "id": str(session.id),
            "course_id": session.course_id,
            "mentor_id": session.mentor_id,
            "title": getattr(session, "title", "Jonli dars") or "Jonli dars",
            "description": getattr(session, "description", "") or "",
            "stream_key": getattr(session, "stream_key", "") or "",
            "status": getattr(session, "status", "live") or "live",
            "viewer_count": getattr(session, "viewer_count", 0) or 0,
            "total_viewers": getattr(session, "total_viewers", 0) or 0,
            "scheduled_at": str(session.scheduled_at) if session.scheduled_at else None,
            "stream_url": f"{settings.webapp.base_url}/live/{session_id}",
        }
        self._sessions[session_id] = data
        return data

    async def start_session(self, session_id: str, stream_key: Optional[str] = None) -> Dict[str, Any]:
        """Live session ni 'live' holatga o'tkazish"""
        session = await self.get_session_info(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        session["status"] = "live"
        session["started_at"] = datetime.now().isoformat()
        if stream_key:
            session["stream_key"] = stream_key

        repo = LiveSessionRepository(database.conn)
        await repo.set_status(session_id, "live", session.get("stream_key"))
        await cache_service.set(f"live:session:{session_id}", session, ttl=86400)

        await self.broadcast(session_id, {
            "type": "stream_status",
            "status": "live",
            "started_at": session["started_at"],
        })
        return session

    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """Live session ni tugatish"""
        session = await self.get_session_info(session_id)
        if not session:
            return {}

        session["status"] = "ended"
        session["ended_at"] = datetime.now().isoformat()

        repo = LiveSessionRepository(database.conn)
        await repo.set_status(session_id, "ended")
        await cache_service.delete(f"live:session:{session_id}")

        await self.broadcast(session_id, {
            "type": "stream_status",
            "status": "ended",
            "ended_at": session["ended_at"],
        })

        if session_id in self._active_broadcasters:
            del self._active_broadcasters[session_id]

        if session_id in self._connections:
            for ws in list(self._connections[session_id]):
                try:
                    await ws.close()
                except Exception as exc:
                    import logging
                    logging.exception("Jim xatolik (Swallowed Exception): %s", exc)
            self._connections[session_id].clear()

        if session_id in self._user_sockets:
            self._user_sockets[session_id].clear()

        logger.info(f"Live session ended: {session_id}")
        return session

    # ========== WEBSOCKET CONNECTION ==========

    async def connect(self, session_id: str, websocket: WebSocket, user_id: int):
        """WebSocket ulanish"""
        await websocket.accept()

        if session_id not in self._connections:
            self._connections[session_id] = set()
        self._connections[session_id].add(websocket)

        if session_id not in self._user_sockets:
            self._user_sockets[session_id] = {}
        self._user_sockets[session_id][user_id] = websocket

        user_repo = UserRepository(database.conn)
        user = await user_repo.get_by_id(user_id)
        username = user.full_name if user and user.full_name else f"Foydalanuvchi_{user_id}"
        session_info = await self.get_session_info(session_id) or {}

        # Is user host/moderator?
        admin_ids = getattr(settings.bot, "admin_ids", [])
        is_host = bool(
            user_id == session_info.get("mentor_id")
            or (user and user.role in ("admin", "super_mentor", "mentor"))
            or (user and user.telegram_id in admin_ids)
        )
        is_moderator = is_host or (user and user.role in ("admin", "super_mentor"))

        viewer = LiveViewer(
            user_id=user_id,
            username=username,
            joined_at=datetime.now().isoformat(),
            is_host=is_host,
            is_moderator=is_moderator,
        )

        if session_id not in self._viewers:
            self._viewers[session_id] = {}
        self._viewers[session_id][user_id] = viewer

        if session_id in self._sessions:
            self._sessions[session_id]["viewer_count"] = len(self._viewers[session_id])

        # 1. Send initial session state to the newly connected client
        await websocket.send_text(json.dumps({
            "type": "init_session",
            "session_id": session_id,
            "title": session_info.get("title", "Jonli efir"),
            "status": session_info.get("status", "live"),
            "is_host": is_host,
            "is_moderator": is_moderator,
            "viewer_count": len(self._viewers[session_id]),
            "active_broadcaster": self._active_broadcasters.get(session_id),
            "raised_hands": self._raised_hands.get(session_id, []),
            "pinned_message": self._pinned_messages.get(session_id),
        }))

        # 2. Broadcast join event to everyone
        await self.broadcast(session_id, {
            "type": "join",
            "user_id": user_id,
            "username": viewer.username,
            "is_host": is_host,
            "viewer_count": len(self._viewers[session_id]),
            "timestamp": datetime.now().isoformat(),
        })

        # 3. Send recent chat history
        if session_id in self._chat_history:
            for msg in self._chat_history[session_id][-30:]:
                await websocket.send_text(json.dumps(msg.to_dict()))

        # 4. Send active polls
        if session_id in self._polls:
            for poll in self._polls[session_id].values():
                if poll.is_active:
                    await websocket.send_text(json.dumps({
                        "type": "poll",
                        "data": {
                            "id": poll.id,
                            "question": poll.question,
                            "options": poll.options,
                            "votes": poll.votes,
                        },
                    }))

        # 5. If there's an active broadcast, notify the viewer to request WebRTC stream
        if session_id in self._active_broadcasters:
            await websocket.send_text(json.dumps({
                "type": "broadcast_active",
                "broadcaster": self._active_broadcasters[session_id],
            }))

    async def disconnect(self, session_id: str, websocket: WebSocket, user_id: int):
        """WebSocket uzilish"""
        if session_id in self._connections:
            self._connections[session_id].discard(websocket)

        if session_id in self._user_sockets and user_id in self._user_sockets[session_id]:
            del self._user_sockets[session_id][user_id]

        viewer = self._viewers.get(session_id, {}).get(user_id)
        if session_id in self._viewers and user_id in self._viewers[session_id]:
            del self._viewers[session_id][user_id]

        # If broadcaster disconnected
        if session_id in self._active_broadcasters and self._active_broadcasters[session_id].get("user_id") == user_id:
            del self._active_broadcasters[session_id]
            await self.broadcast(session_id, {
                "type": "stop_broadcast",
                "user_id": user_id,
            })

        # Remove from raised hands if any
        if session_id in self._raised_hands:
            self._raised_hands[session_id] = [h for h in self._raised_hands[session_id] if h.get("user_id") != user_id]

        await self.broadcast(session_id, {
            "type": "leave",
            "user_id": user_id,
            "username": viewer.username if viewer else "Foydalanuvchi",
            "viewer_count": len(self._viewers.get(session_id, {})),
            "timestamp": datetime.now().isoformat(),
        })

    # ========== MESSAGE DISPATCHER ==========

    async def handle_message(
        self,
        session_id: str,
        websocket: WebSocket,
        user_id: int,
        data: Dict[str, Any],
    ):
        """Xabarlarni qayta ishlash"""
        msg_type = data.get("type")

        if msg_type == "chat":
            await self._handle_chat(session_id, user_id, data, websocket)
        elif msg_type == "reaction":
            await self._handle_reaction(session_id, user_id, data)
        elif msg_type == "question":
            await self._handle_question(session_id, user_id, data)
        elif msg_type == "poll_vote":
            await self._handle_poll_vote(session_id, user_id, data)
        elif msg_type == "raise_hand":
            await self._handle_raise_hand(session_id, user_id)
        elif msg_type == "lower_hand":
            await self._handle_lower_hand(session_id, user_id)
        elif msg_type == "grant_mic":
            await self._handle_grant_mic(session_id, user_id, data)
        elif msg_type == "revoke_mic":
            await self._handle_revoke_mic(session_id, user_id, data)
        elif msg_type == "start_broadcast":
            await self._handle_start_broadcast(session_id, user_id, data)
        elif msg_type == "stop_broadcast":
            await self._handle_stop_broadcast(session_id, user_id)
        elif msg_type in ("webrtc_offer", "webrtc_answer", "webrtc_ice_candidate"):
            await self._handle_webrtc_signal(session_id, user_id, data)
        elif msg_type == "create_poll":
            await self._handle_create_poll(session_id, user_id, data)
        elif msg_type == "pin_message":
            await self._handle_pin_message(session_id, user_id, data)
        elif msg_type == "unpin_message":
            await self._handle_unpin_message(session_id, user_id)
        elif msg_type == "moderation":
            await self._handle_moderation(session_id, user_id, data)

    # ========== EVENT HANDLERS ==========

    async def _handle_pin_message(self, session_id: str, user_id: int, data: Dict):
        """Spiker / Moderator xabarni pin qilganda"""
        content = str(data.get("content", "")).strip()
        if not content:
            return
        author_name = str(data.get("author_name", "Spiker")).strip()
        message_id = data.get("message_id") or f"pin_{uuid.uuid4().hex[:8]}"

        pinned = {
            "id": message_id,
            "content": content,
            "author_name": author_name,
            "pinned_by": user_id,
            "timestamp": datetime.now().isoformat(),
        }
        self._pinned_messages[session_id] = pinned

        await self.broadcast(session_id, {
            "type": "pinned_message",
            "pinned_message": pinned,
        })
        logger.info(f"Message pinned in session {session_id} by user {user_id}")

    async def _handle_unpin_message(self, session_id: str, user_id: int):
        """Qadalgan xabarni olib tashlash"""
        self._pinned_messages[session_id] = None
        await self.broadcast(session_id, {
            "type": "unpinned_message",
        })
        logger.info(f"Message unpinned in session {session_id} by user {user_id}")

    async def _handle_start_broadcast(self, session_id: str, user_id: int, data: Dict):
        """Mentor jonli efirni (video/audio/ekran) boshlaganda"""
        viewer = self._viewers.get(session_id, {}).get(user_id)
        username = viewer.username if viewer else f"Mentor_{user_id}"

        broadcaster_info = {
            "user_id": user_id,
            "username": username,
            "has_video": data.get("has_video", True),
            "has_audio": data.get("has_audio", True),
            "mode": data.get("mode", "camera"),  # camera | screen
            "started_at": datetime.now().isoformat(),
        }
        self._active_broadcasters[session_id] = broadcaster_info

        # Update session status
        if session_id in self._sessions:
            self._sessions[session_id]["status"] = "live"

        await self.broadcast(session_id, {
            "type": "start_broadcast",
            "broadcaster": broadcaster_info,
        })
        logger.info(f"Broadcast started in session {session_id} by user {user_id}")

    async def _handle_stop_broadcast(self, session_id: str, user_id: int):
        """Mentor efirni to'xtatganda"""
        if session_id in self._active_broadcasters:
            del self._active_broadcasters[session_id]

        await self.broadcast(session_id, {
            "type": "stop_broadcast",
            "user_id": user_id,
        })
        logger.info(f"Broadcast stopped in session {session_id}")

    async def _handle_webrtc_signal(self, session_id: str, sender_id: int, data: Dict):
        """WebRTC signallarini (offer, answer, candidate) to'g'ridan-to'g'ri peerlarga uzatish"""
        target_user_id = data.get("target_user_id")
        msg_type = data.get("type")

        payload = {
            "type": msg_type,
            "sender_id": sender_id,
            "data": data.get("data") or data.get("sdp") or data.get("candidate"),
            "target_user_id": target_user_id,
        }

        if target_user_id:
            # Muayyan foydalanuvchiga to'g'ridan-to'g'ri uzatish
            await self.send_to_user(session_id, int(target_user_id), payload)
        else:
            # Broadcaster barcha tomoshabinlarga uzatishi
            await self.broadcast(session_id, payload, exclude_user_id=sender_id)

    async def _handle_raise_hand(self, session_id: str, user_id: int):
        """Talaba qo'l ko'targanda"""
        viewer = self._viewers.get(session_id, {}).get(user_id)
        if not viewer:
            return

        viewer.is_hand_raised = True
        hand_item = {
            "user_id": user_id,
            "username": viewer.username,
            "timestamp": datetime.now().isoformat(),
        }

        if session_id not in self._raised_hands:
            self._raised_hands[session_id] = []

        # Remove duplicate if exists
        self._raised_hands[session_id] = [h for h in self._raised_hands[session_id] if h.get("user_id") != user_id]
        self._raised_hands[session_id].append(hand_item)

        await self.broadcast(session_id, {
            "type": "raise_hand",
            "user_id": user_id,
            "username": viewer.username,
            "raised_hands": self._raised_hands[session_id],
        })

    async def _handle_lower_hand(self, session_id: str, user_id: int):
        """Qo'lni tushirish"""
        viewer = self._viewers.get(session_id, {}).get(user_id)
        if viewer:
            viewer.is_hand_raised = False

        if session_id in self._raised_hands:
            self._raised_hands[session_id] = [h for h in self._raised_hands[session_id] if h.get("user_id") != user_id]

        await self.broadcast(session_id, {
            "type": "lower_hand",
            "user_id": user_id,
            "raised_hands": self._raised_hands.get(session_id, []),
        })

    async def _handle_grant_mic(self, session_id: str, host_id: int, data: Dict):
        """Mentor talabaga mikrofon ruxsatini berganda"""
        target_user_id = data.get("target_user_id")
        if not target_user_id:
            return

        target_user_id = int(target_user_id)
        viewer = self._viewers.get(session_id, {}).get(target_user_id)
        if viewer:
            viewer.can_speak = True
            viewer.is_hand_raised = False

        if session_id in self._raised_hands:
            self._raised_hands[session_id] = [h for h in self._raised_hands[session_id] if h.get("user_id") != target_user_id]

        # Notify target student to enable their microphone
        await self.send_to_user(session_id, target_user_id, {
            "type": "grant_mic",
            "granted_by": host_id,
        })

        # Broadcast to all viewers that this student is speaking
        await self.broadcast(session_id, {
            "type": "speaker_joined",
            "user_id": target_user_id,
            "username": viewer.username if viewer else f"User_{target_user_id}",
            "raised_hands": self._raised_hands.get(session_id, []),
        })

    async def _handle_revoke_mic(self, session_id: str, host_id: int, data: Dict):
        """Mentor talabaning mikrofonini o'chirganda"""
        target_user_id = data.get("target_user_id")
        if not target_user_id:
            return

        target_user_id = int(target_user_id)
        viewer = self._viewers.get(session_id, {}).get(target_user_id)
        if viewer:
            viewer.can_speak = False

        await self.send_to_user(session_id, target_user_id, {
            "type": "revoke_mic",
            "revoked_by": host_id,
        })

        await self.broadcast(session_id, {
            "type": "speaker_left",
            "user_id": target_user_id,
        })

    async def _handle_create_poll(self, session_id: str, user_id: int, data: Dict):
        """Mentor yangi so'rovnoma yaratganda"""
        question = data.get("question", "")
        options = data.get("options", [])
        if not question or not options:
            return

        poll_id = f"poll_{uuid.uuid4().hex[:8]}"
        poll = LivePoll(
            id=poll_id,
            question=question,
            options=options,
        )

        if session_id not in self._polls:
            self._polls[session_id] = {}
        self._polls[session_id][poll_id] = poll

        await self.broadcast(session_id, {
            "type": "poll",
            "data": {
                "id": poll.id,
                "question": poll.question,
                "options": poll.options,
                "votes": {},
            },
        })

    async def _handle_chat(self, session_id: str, user_id: int, data: Dict, websocket: WebSocket):
        """Chat xabar"""
        content = str(data.get("content", "")).strip()
        if not content:
            return

        viewer = self._viewers.get(session_id, {}).get(user_id)
        username = viewer.username if viewer else f"Foydalanuvchi_{user_id}"

        message = LiveMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            user_id=user_id,
            username=username,
            type=LiveEventType.CHAT,
            content=content,
        )

        if session_id not in self._chat_history:
            self._chat_history[session_id] = []
        self._chat_history[session_id].append(message)

        await self.broadcast(session_id, message.to_dict())

    async def _handle_reaction(self, session_id: str, user_id: int, data: Dict):
        """Reaksiya (❤️🔥👍)"""
        reaction = data.get("reaction", "❤️")
        await self.broadcast(session_id, {
            "type": "reaction",
            "user_id": user_id,
            "reaction": reaction,
            "timestamp": datetime.now().isoformat(),
        })

    async def _handle_question(self, session_id: str, user_id: int, data: Dict):
        """Savol berish"""
        question = str(data.get("question", "")).strip()
        if not question:
            return

        viewer = self._viewers.get(session_id, {}).get(user_id)
        username = viewer.username if viewer else f"Foydalanuvchi_{user_id}"

        question_data = {
            "id": f"q_{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "username": username,
            "question": question,
            "created_at": datetime.now().isoformat(),
        }

        if session_id not in self._questions:
            self._questions[session_id] = []
        self._questions[session_id].append(question_data)

        await self.broadcast(session_id, {
            "type": "question",
            "data": question_data,
        })

    async def _handle_poll_vote(self, session_id: str, user_id: int, data: Dict):
        """Poll ovoz berish"""
        poll_id = data.get("poll_id")
        option_index = data.get("option_index")

        if session_id not in self._polls or poll_id not in self._polls[session_id]:
            return

        poll = self._polls[session_id][poll_id]
        if not poll.is_active:
            return

        poll.votes[user_id] = int(option_index)

        await self.broadcast(session_id, {
            "type": "poll_update",
            "poll_id": poll_id,
            "votes": poll.votes,
            "total_votes": len(poll.votes),
        })

    async def _handle_moderation(self, session_id: str, user_id: int, data: Dict):
        """Moderatsiya buyrug'i"""
        action = data.get("action")
        target_user_id = data.get("target_user_id")

        if action == "kick" and target_user_id:
            target_ws = self._user_sockets.get(session_id, {}).get(int(target_user_id))
            if target_ws:
                try:
                    await target_ws.send_text(json.dumps({
                        "type": "moderation",
                        "action": "kicked",
                        "message": "Siz efirdan chetlashtirildingiz.",
                    }))
                    await target_ws.close()
                except Exception as exc:
                    import logging
                    logging.exception("Jim xatolik (Swallowed Exception): %s", exc)

    # ========== UTILITIES ==========

    async def send_to_user(self, session_id: str, target_user_id: int, data: dict):
        """Muayyan foydalanuvchiga xabar yuborish"""
        ws = self._user_sockets.get(session_id, {}).get(target_user_id)
        if ws:
            try:
                await ws.send_text(json.dumps(data))
            except Exception as e:
                logger.debug(f"Send to user {target_user_id} failed: {e}")

    async def broadcast(self, session_id: str, message: dict, exclude_user_id: Optional[int] = None):
        """Barcha ulanganlarga xabar tarqatish"""
        connections = self._connections.get(session_id, set())
        if not connections:
            return

        exclude_ws = None
        if exclude_user_id and session_id in self._user_sockets:
            exclude_ws = self._user_sockets[session_id].get(exclude_user_id)

        msg_str = json.dumps(message)
        dead = []
        for ws in connections:
            if exclude_ws and ws == exclude_ws:
                continue
            try:
                await ws.send_text(msg_str)
            except Exception:
                dead.append(ws)

        for ws in dead:
            connections.discard(ws)


live_manager = LiveStreamManager()
