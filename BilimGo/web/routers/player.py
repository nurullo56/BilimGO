import logging
import time
from pathlib import Path
import aiofiles
import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

from core.config import settings
from core.exceptions import AccessDeniedError, NotFoundError
from db.database import database
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.completion_notification_repo import CompletionNotificationRepository
from db.repositories.comprehension_check_repo import ComprehensionCheckRepository
from db.repositories.course_repo import CourseRepository
from db.repositories.course_tariff_repo import CourseTariffRepository
from services.course_service import CourseService
from services.cohort_service import format_course_title_with_cohort
from db.repositories.daily_unlock_plan_repo import DailyUnlockPlanRepository
from db.repositories.delivery_token_repo import DeliveryTokenRepository
from db.repositories.engagement_repo import EngagementRepository, NudgeRepository
from db.repositories.lesson_repo import Lesson, LessonRepository
from db.repositories.lesson_view_repo import LessonViewRepository
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.unlock_tier_repo import UnlockTierRuleRepository
from db.repositories.user_repo import UserRepository
from services.access_control_service import AccessControlService
from services.adaptive_unlock_service import AdaptiveUnlockService
from services.analytics_service import AnalyticsService
from services.delivery_token_service import DeliveryTokenService
from services.engagement_monitor_service import EngagementMonitorService
from services.lesson_completion_service import LessonCompletionService
from web.dependencies.auth import get_current_telegram_id

router = APIRouter(prefix="/api", tags=["player"])


class LessonProgressPayload(BaseModel):
    watch_duration_sec: int = Field(default=0, ge=0)
    completion_percent: int = Field(default=0, ge=0, le=100)


def _build_access_control() -> AccessControlService:
    conn = database.conn
    adaptive_unlock = AdaptiveUnlockService(
        plan_repo=DailyUnlockPlanRepository(conn),
        tier_repo=UnlockTierRuleRepository(conn),
        comprehension_repo=ComprehensionCheckRepository(conn),
    )
    return AccessControlService(
        lesson_repo=LessonRepository(conn),
        access_grant_repo=AccessGrantRepository(conn),
        adaptive_unlock_service=adaptive_unlock,
        user_repo=UserRepository(conn),
    )


def _build_token_service() -> DeliveryTokenService:
    conn = database.conn
    return DeliveryTokenService(
        access_control=_build_access_control(),
        token_repo=DeliveryTokenRepository(conn),
        lesson_repo=LessonRepository(conn),
    )


@router.get("/courses")
async def list_courses(
    telegram_id: int = Depends(get_current_telegram_id),
) -> list[dict]:
    conn = database.conn
    user_repo = UserRepository(conn)
    user = await user_repo.get_or_create(telegram_id=telegram_id)

    course_repo = CourseRepository(conn)
    lesson_repo = LessonRepository(conn)
    access_grant_repo = AccessGrantRepository(conn)
    views_repo = LessonViewRepository(conn)

    is_admin = user.role in ("admin", "super_mentor") or user.telegram_id in settings.bot.admin_ids
    is_mentor = user.role == "mentor"
    courses = await course_repo.list_published()
    results = []
    for c in courses:
        lessons = await lesson_repo.list_by_course(c.id)
        progress_list = await views_repo.student_progress_for_course(user.id, c.id)

        # Foydalanuvchi aynan shu kursni sotib olganmi yoki yo'qligini tekshirish
        is_enrolled = False
        try:
            is_enrolled = await access_grant_repo.has_active_access(
                user_id=user.id, lesson_id=0, course_id=c.id
            )
        except Exception:
            is_enrolled = False

        has_access = is_admin or is_mentor or is_enrolled

        total_lessons = len(lessons)
        completed_lessons = sum(
            1 for p in progress_list if (p.get("completion_percent") or 0) >= 90
        )
        total_duration = sum(l.duration_sec or 0 for l in lessons)

        course_service = CourseService(course_repo=course_repo)
        cohort = await course_service.get_course_cohort(c, user_id=user.id)
        formatted_title = format_course_title_with_cohort(c.title, cohort)

        results.append(
            {
                "id": c.id,
                "title": formatted_title,
                "raw_title": c.title,
                "cohort": cohort,
                "description": c.description,
                "base_price": c.base_price,
                "is_waitlist": bool(c.is_waitlist),
                "owner_node_id": c.owner_node_id or 1,
                "has_access": has_access,
                "is_enrolled": is_enrolled,
                "total_lessons": total_lessons,
                "completed_lessons": completed_lessons,
                "total_duration_sec": total_duration,
                "total_duration_minutes": round(total_duration / 60),
                "tariffs": await CourseTariffRepository(conn).get_by_course_id(c.id),
            }
        )
    return results


@router.get("/courses/{course_id}")
async def get_course_by_id(
    course_id: int,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    conn = database.conn
    user_repo = UserRepository(conn)
    user = await user_repo.get_or_create(telegram_id=telegram_id)

    course_repo = CourseRepository(conn)
    lesson_repo = LessonRepository(conn)
    access_grant_repo = AccessGrantRepository(conn)
    views_repo = LessonViewRepository(conn)

    c = await course_repo.get_by_id(course_id)
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Kurs topilmadi")

    lessons = await lesson_repo.list_by_course(c.id)
    progress_list = await views_repo.student_progress_for_course(user.id, c.id)

    is_admin = user.role in ("admin", "super_mentor") or user.telegram_id in settings.bot.admin_ids
    is_mentor = user.role == "mentor"
    
    # Aynan shu kurs uchun sotib olinganlik holati
    is_enrolled = False
    try:
        is_enrolled = await access_grant_repo.has_active_access(
            user_id=user.id, lesson_id=0, course_id=c.id
        )
    except Exception:
        is_enrolled = False

    has_access = is_admin or is_mentor or is_enrolled

    total_lessons = len(lessons)
    completed_lessons = sum(
        1 for p in progress_list if (p.get("completion_percent") or 0) >= 90
    )
    total_duration = sum(l.duration_sec or 0 for l in lessons)

    course_service = CourseService(course_repo=course_repo)
    cohort = await course_service.get_course_cohort(c, user_id=user.id)
    formatted_title = format_course_title_with_cohort(c.title, cohort)

    return {
        "id": c.id,
        "title": formatted_title,
        "raw_title": c.title,
        "cohort": cohort,
        "description": c.description,
        "base_price": c.base_price,
        "is_waitlist": bool(c.is_waitlist),
        "owner_node_id": c.owner_node_id,
        "has_access": has_access,
        "is_enrolled": is_enrolled,
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "total_duration_sec": total_duration,
        "total_duration_minutes": round(total_duration / 60),
        "tariffs": await CourseTariffRepository(conn).get_by_course_id(c.id),
    }


@router.get("/courses/{course_id}/lessons")
async def list_course_lessons(
    course_id: int,
    telegram_id: int = Depends(get_current_telegram_id),
) -> list[dict]:
    conn = database.conn
    user_repo = UserRepository(conn)
    user = await user_repo.get_or_create(telegram_id=telegram_id)

    lesson_repo = LessonRepository(conn)
    lessons = await lesson_repo.list_by_course(course_id)
    if not lessons:
        return []

    access_control = _build_access_control()
    access_grant_repo = AccessGrantRepository(conn)
    views_repo = LessonViewRepository(conn)
    progress_list = await views_repo.student_progress_for_course(user.id, course_id)
    progress_map = {p["lesson_id"]: p for p in progress_list}

    is_admin = user.role in ("admin", "super_mentor") or user.telegram_id in settings.bot.admin_ids
    has_course_access = is_admin or await access_grant_repo.has_active_access(
        user_id=user.id, lesson_id=lessons[0].id if lessons else 0, course_id=course_id
    )

    results = []
    for lesson in lessons:
        is_accessible = False
        if is_admin or has_course_access or lesson.is_free_preview:
            is_accessible = True
        else:
            try:
                await access_control.ensure_can_watch(user.id, lesson.id)
                is_accessible = True
            except Exception:
                is_accessible = False

        view_data = progress_map.get(lesson.id, {})
        results.append(
            {
                "id": lesson.id,
                "title": lesson.title,
                "order_index": lesson.order_index,
                "duration_sec": lesson.duration_sec,
                "is_free_preview": lesson.is_free_preview,
                "is_accessible": is_accessible,
                "completion_percent": view_data.get("completion_percent") or 0,
                "watch_duration_sec": view_data.get("watch_duration_sec") or 0,
            }
        )

    return results


def _get_candidate_download_folders(channel_id: str | int | None = None) -> list[Path]:
    base_dirs = [
        Path("C:/Users/Acer/Downloads/BilimGoUserBot/BilimGoUserBot/downloads"),
        Path("C:/Users/Acer/Downloads/BilimGoUserBot/downloads"),
        settings.paths.downloads_dir,
        Path(__file__).resolve().parents[3] / "BilimGoUserBot" / "BilimGoUserBot" / "downloads",
        Path(__file__).resolve().parents[4] / "BilimGoUserBot" / "BilimGoUserBot" / "downloads",
        Path(__file__).resolve().parents[2] / "data" / "downloads",
    ]
    if not channel_id:
        return [b for b in base_dirs if b.exists()]
    
    ch_str = str(channel_id).strip()
    variations = [ch_str]
    if ch_str.startswith("-100"):
        variations.append(ch_str.replace("-100", ""))
    else:
        variations.append(f"-100{ch_str}")

    res = []
    for b in base_dirs:
        if b.exists():
            for v in variations:
                cand = b / v
                if cand.exists() and cand not in res:
                    res.append(cand)
            if b not in res:
                res.append(b)
    return res


def _find_local_media(lesson: Lesson) -> Path | None:
    if not lesson or not lesson.source_channel_id or not lesson.source_message_id:
        return None
    candidate_dirs = _get_candidate_download_folders(lesson.source_channel_id)
    extensions = [".mp4", ".oga", ".ogg", ".mp3", ".m4a", ".webm", ".mkv", ".mov"]
    msg_id = lesson.source_message_id
    for folder in candidate_dirs:
        for ext in extensions:
            p = folder / f"msg_{msg_id}{ext}"
            if p.exists():
                return p
    return None


def _find_lesson_images(lesson: Lesson) -> list[str]:
    if not lesson or not lesson.source_channel_id or not lesson.source_message_id:
        return []
    # Matnli shablon darsiga rasm biriktirilmaydi
    if lesson.source_message_id == 149:
        return []
    candidate_dirs = _get_candidate_download_folders(lesson.source_channel_id)
    media_exts = [".mp4", ".oga", ".ogg", ".mp3", ".m4a", ".webm", ".mkv", ".mov"]
    img_exts = [".jpg", ".jpeg", ".png", ".webp"]

    img_urls = []
    msg_id = lesson.source_message_id

    for folder in candidate_dirs:
        # Faqat ushbu darsdan oldin kelgan va oldingi darsgacha bo'lgan rasmlarni qidiramiz
        curr = msg_id - 1
        matched_files = []
        while curr >= max(1, msg_id - 10):
            # Agar boshqa audio/video darsga duch kelsa, darhol to'xtaydi
            has_media = any((folder / f"msg_{curr}{ext}").exists() for ext in media_exts)
            if has_media:
                break
            # Matnli dars chegarasidan o'tib ketmaslik
            if curr == 149 and msg_id > 149:
                break
            for ext in img_exts:
                p = folder / f"msg_{curr}{ext}"
                if p.exists():
                    matched_files.insert(0, p.name)
            curr -= 1

        for fname in matched_files:
            rel_url = f"/api/media/{lesson.source_channel_id}/{fname}"
            if rel_url not in img_urls:
                img_urls.append(rel_url)
        if img_urls:
            break
    return img_urls


def _find_lesson_text_material(lesson: Lesson) -> str | None:
    """Telegram kanalidagi ushbu darsga tegishli matnli dars/shablonni oladi."""
    if not lesson or not lesson.source_channel_id or not lesson.source_message_id:
        return None
    try:
        import sqlite3
        candidate_userbot_dbs = [
            settings.paths.userbot_db_path,
            Path("C:/Users/Acer/Downloads/BilimGoUserBot/BilimGoUserBot/userbot_database.db"),
            Path(__file__).resolve().parents[4] / "BilimGoUserBot" / "BilimGoUserBot" / "userbot_database.db",
            Path(__file__).resolve().parents[3] / "BilimGoUserBot" / "BilimGoUserBot" / "userbot_database.db",
        ]
        userbot_db_path = None
        for db_p in candidate_userbot_dbs:
            if db_p and db_p.exists():
                userbot_db_path = db_p
                break
        if not userbot_db_path:
            return None
        with sqlite3.connect(userbot_db_path) as conn:
            conn.row_factory = sqlite3.Row
            # Faqat aynan shu dars xabaridagi matn
            row = conn.execute(
                "SELECT text FROM posts WHERE channel_id = ? AND message_id = ?",
                (lesson.source_channel_id, lesson.source_message_id),
            ).fetchone()
            if row and row["text"] and len(row["text"].strip()) > 20:
                return row["text"].strip()
    except Exception as e:
        logger.warning(f"Error fetching lesson text material: {e}")
    return None


def _get_media_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in [".oga", ".ogg"]:
        return "audio/ogg"
    if ext == ".mp3":
        return "audio/mpeg"
    if ext == ".m4a":
        return "audio/mp4"
    if ext == ".webm":
        return "video/webm"
    if ext in [".jpg", ".jpeg"]:
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    return "video/mp4"


@router.get("/media/{channel_id}/{filename}")
async def serve_media_image(channel_id: str, filename: str):
    candidate_dirs = _get_candidate_download_folders(channel_id)
    for d in candidate_dirs:
        target = d / filename
        if target.exists():
            ext = target.suffix.lower()
            media_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
            return FileResponse(target, media_type=media_type)
    raise HTTPException(status_code=404, detail="Rasm topilmadi")


@router.post("/lessons/{lesson_id}/access-token")
async def create_access_token(
    lesson_id: int,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    user_repo = UserRepository(database.conn)
    user = await user_repo.get_or_create(telegram_id=telegram_id)

    token_service = _build_token_service()
    try:
        issued = await token_service.issue(user_id=user.id, lesson_id=lesson_id)
    except AccessDeniedError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    analytics = AnalyticsService(LessonViewRepository(database.conn))
    await analytics.record_view_start(user_id=user.id, lesson_id=lesson_id)

    engagement = EngagementMonitorService(
        EngagementRepository(database.conn), NudgeRepository(database.conn)
    )
    await engagement.touch_activity(user.id)

    lesson_repo = LessonRepository(database.conn)
    lesson = await lesson_repo.get_by_id(lesson_id)
    local_file = _find_local_media(lesson) if lesson else None
    text_content = _find_lesson_text_material(lesson) if lesson else None

    media_type = "video/mp4"
    is_audio = False
    is_text = False
    stream_url = f"/api/stream/{issued.raw_token}"

    if text_content and not local_file:
        # Standalone Text / Template lesson
        media_type = "text/plain"
        is_text = True
        stream_url = ""
    elif local_file:
        media_type = _get_media_type(local_file)
        is_audio = media_type.startswith("audio/")
    elif lesson:
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                resp = await client.get(
                    f"{settings.relay.internal_url}/meta",
                    params={
                        "channel_id": lesson.source_channel_id,
                        "message_id": lesson.source_message_id,
                    },
                    headers={"X-Internal-Secret": settings.relay.internal_secret},
                )
                if resp.is_success:
                    meta_info = resp.json()
                    mime = meta_info.get("mime_type", "")
                    if mime:
                        media_type = mime
                        is_audio = mime.startswith("audio/") or mime in ("application/ogg", "audio/ogg", "audio/opus")
        except Exception as exc:
            import logging
            logging.exception("Jim xatolik (Swallowed Exception): %s", exc)

    images = _find_lesson_images(lesson) if lesson else []

    return {
        "stream_url": stream_url,
        "expires_at": issued.expires_at,
        "media_type": media_type,
        "is_audio": is_audio,
        "is_text": is_text,
        "images": images,
        "text_content": text_content,
    }


@router.post("/lessons/{lesson_id}/progress")
async def update_lesson_progress(
    lesson_id: int,
    payload: LessonProgressPayload,
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    conn = database.conn
    user_repo = UserRepository(conn)
    user = await user_repo.get_or_create(telegram_id=telegram_id)

    lesson_completion_service = LessonCompletionService(
        lesson_repo=LessonRepository(conn),
        course_repo=CourseRepository(conn),
        user_repo=user_repo,
        license_node_repo=LicenseNodeRepository(conn),
        lesson_view_repo=LessonViewRepository(conn),
        notification_repo=CompletionNotificationRepository(conn),
        engagement_repo=EngagementRepository(conn),
        nudge_repo=NudgeRepository(conn),
    )

    is_completed = await lesson_completion_service.handle_lesson_progress(
        user_id=user.id,
        lesson_id=lesson_id,
        watch_duration_sec=payload.watch_duration_sec,
        completion_percent=payload.completion_percent,
    )

    if payload.watch_duration_sec > 0:
        try:
            from db.repositories.server_expense_repo import ServerExpenseRepository
            from services.server_expense_service import ServerExpenseService

            server_service = ServerExpenseService(ServerExpenseRepository(conn))
            await server_service.track_video_stream(
                student_id=user.id,
                lesson_id=lesson_id,
                duration_sec=payload.watch_duration_sec,
            )
        except Exception as exc:
            import logging
            logging.exception("Jim xatolik (Swallowed Exception): %s", exc)

    return {
        "status": "ok",
        "lesson_id": lesson_id,
        "is_completed": is_completed,
        "completion_percent": payload.completion_percent,
    }


@router.post("/lessons/{lesson_id}/voice-report")
async def submit_voice_report(
    lesson_id: int,
    voice_file: UploadFile = File(...),
    duration_sec: int = Form(0),
    telegram_id: int = Depends(get_current_telegram_id),
) -> dict:
    conn = database.conn
    user_repo = UserRepository(conn)
    user = await user_repo.get_or_create(telegram_id=telegram_id)
    lesson_repo = LessonRepository(conn)
    course_repo = CourseRepository(conn)
    node_repo = LicenseNodeRepository(conn)

    lesson = await lesson_repo.get_by_id(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Dars topilmadi")

    course = await course_repo.get_by_id(lesson.course_id)
    course_title = course.title if course else "Kurs"
    lesson_title = lesson.title

    # 1. Audio faylni diskda saqlash
    audio_bytes = await voice_file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Bo'sh audio fayl yuborildi")

    voices_dir = Path("data/voice_reports")
    voices_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(voice_file.filename or "voice.ogg").suffix or ".ogg"
    saved_filename = f"voice_{user.id}_{lesson_id}_{int(time.time())}{ext}"
    saved_path = voices_dir / saved_filename
    async with aiofiles.open(saved_path, "wb") as f:
        await f.write(audio_bytes)

    # 2. Ushbu dars bo'yicha biriktirilgan Mentorni aniqlash
    mentor_tg_id = None
    if course and course.owner_node_id:
        node = await node_repo.get_by_id(course.owner_node_id)
        if node:
            mentor_user = await user_repo.get_by_id(node.owner_user_id)
            if mentor_user:
                mentor_tg_id = mentor_user.telegram_id

    # Agar shaxsiy mentor topilmasa yoki o'quvchining o'zi bo'lsa, super mentor / admin guruhiga yuboriladi
    if not mentor_tg_id or mentor_tg_id == user.telegram_id:
        mentor_tg_id = getattr(settings, "super_mentor_group_id", None) or (
            settings.bot.admin_ids[0] if settings.bot.admin_ids else None
        )

    # 3. Telegram orqali Mentorga OVOZLI XABAR qilib yetkazish (sendVoice)
    duration_mins = duration_sec // 60
    duration_rem = duration_sec % 60
    duration_str = f"{duration_mins}:{duration_rem:02d}" if duration_sec > 0 else "Noma'lum"

    student_name = user.full_name or "Talaba"
    caption = (
        f"🎙 <b>Yangi dars bo'yicha ovozli hisobot!</b>\n\n"
        f"👤 <b>O'quvchi:</b> {student_name} (ID: <code>{user.telegram_id}</code>)\n"
        f"📚 <b>Kurs:</b> {course_title}\n"
        f"📖 <b>Dars:</b> {lesson_title}\n"
        f"⏱ <b>Davomiyligi:</b> {duration_str}\n\n"
        f"✅ O'quvchi dars tushunchasi bo'yicha hisobot topshirdi."
    )

    sent_to_mentor = False
    if mentor_tg_id:
        try:
            bot_token = settings.bot.token
            url = f"https://api.telegram.org/bot{bot_token}/sendVoice"
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    url,
                    data={"chat_id": mentor_tg_id, "caption": caption, "parse_mode": "HTML"},
                    files={"voice": (saved_filename, audio_bytes, voice_file.content_type or "audio/ogg")},
                )
                if resp.status_code == 200:
                    sent_to_mentor = True
                else:
                    # Agar Telegram sendVoice formatini qabul qilmasa, sendAudio orqali yuborish
                    audio_url = f"https://api.telegram.org/bot{bot_token}/sendAudio"
                    resp2 = await client.post(
                        audio_url,
                        data={"chat_id": mentor_tg_id, "caption": caption, "parse_mode": "HTML"},
                        files={"audio": (saved_filename, audio_bytes, voice_file.content_type or "audio/mpeg")},
                    )
                    sent_to_mentor = resp2.status_code == 200
        except Exception as err:
            logger.error("Mentorga ovoz yuborishda xatolik: %s", err)

    # 4. Ovoz topshirilgach darsni to'liq yakunlangan deb hisoblash
    lesson_completion_service = LessonCompletionService(
        lesson_repo=lesson_repo,
        course_repo=course_repo,
        user_repo=user_repo,
        license_node_repo=node_repo,
        lesson_view_repo=LessonViewRepository(conn),
        notification_repo=CompletionNotificationRepository(conn),
        engagement_repo=EngagementRepository(conn),
        nudge_repo=NudgeRepository(conn),
    )
    await lesson_completion_service.handle_lesson_completed(user_id=user.id, lesson_id=lesson_id)

    return {
        "status": "success",
        "sent_to_mentor": sent_to_mentor,
        "message": "Ovozli hisobotingiz qabul qilindi va mentoringizga yetkazildi! Dars muvaffaqiyatli yakunlandi.",
    }


async def _stream_local_file(file_path: Path, range_header: str | None) -> StreamingResponse:
    file_size = file_path.stat().st_size
    media_type = _get_media_type(file_path)
    
    start = 0
    end = file_size - 1
    
    if range_header:
        parts = range_header.replace("bytes=", "").split("-")
        start = int(parts[0]) if parts[0] else 0
        if len(parts) > 1 and parts[1]:
            end = int(parts[1])
            
    content_length = end - start + 1
    
    async def file_iterator():
        async with aiofiles.open(file_path, mode="rb") as f:
            await f.seek(start)
            remaining = content_length
            chunk_size = 1024 * 512  # 512KB chunks
            while remaining > 0:
                read_size = min(remaining, chunk_size)
                data = await f.read(read_size)
                if not data:
                    break
                remaining -= len(data)
                yield data
                
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
    }
    
    status_code = status.HTTP_200_OK
    if range_header:
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        status_code = status.HTTP_206_PARTIAL_CONTENT
        
    return StreamingResponse(
        file_iterator(),
        status_code=status_code,
        media_type=media_type,
        headers=headers,
    )


async def _fetch_meta(lesson: Lesson) -> int:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.relay.internal_url}/meta",
            params={
                "channel_id": lesson.source_channel_id,
                "message_id": lesson.source_message_id,
            },
            headers={"X-Internal-Secret": settings.relay.internal_secret},
        )
        resp.raise_for_status()
        return resp.json()["file_size"]


async def _relay_chunks(lesson: Lesson, offset_chunk: int):
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "GET",
            f"{settings.relay.internal_url}/relay",
            params={
                "channel_id": lesson.source_channel_id,
                "message_id": lesson.source_message_id,
                "offset_chunk": offset_chunk,
            },
            headers={"X-Internal-Secret": settings.relay.internal_secret},
        ) as resp:
            resp.raise_for_status()
            async for chunk in resp.aiter_bytes():
                yield chunk


@router.get("/stream/{raw_token}")
async def stream_lesson(
    raw_token: str,
    request: Request,
    range: str | None = Header(default=None),
) -> StreamingResponse:
    conn = database.conn
    token_service = DeliveryTokenService(
        access_control=_build_access_control(),
        token_repo=DeliveryTokenRepository(conn),
        lesson_repo=LessonRepository(conn),
    )

    try:
        lesson = await token_service.resolve(raw_token)
    except AccessDeniedError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    # 1. First check if local file is already available
    local_file = _find_local_media(lesson)
    if local_file and local_file.exists():
        return await _stream_local_file(local_file, range)

    # 2. Otherwise relay live from Userbot
    try:
        file_size = await _fetch_meta(lesson)
    except Exception as exc:
        logger.error(f"Relay serverga ulanishda xatolik: {exc}")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail="Relay Userbot server ishlamayapti yoki manba topilmadi"
        ) from exc

    chunk_size = settings.relay.chunk_size

    start = 0
    if range:
        start = int(range.replace("bytes=", "").split("-")[0] or 0)

    offset_chunk = start // chunk_size
    leading_trim = start - offset_chunk * chunk_size

    async def body():
        skipped = 0
        async for chunk in _relay_chunks(lesson, offset_chunk):
            if skipped < leading_trim:
                to_skip = min(leading_trim - skipped, len(chunk))
                chunk = chunk[to_skip:]
                skipped += to_skip
            if chunk:
                yield chunk

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size - start),
    }
    status_code = status.HTTP_200_OK
    if range:
        headers["Content-Range"] = f"bytes {start}-{file_size - 1}/{file_size}"
        status_code = status.HTTP_206_PARTIAL_CONTENT

    return StreamingResponse(
        body(), status_code=status_code, media_type="video/mp4", headers=headers
    )
