from __future__ import annotations

import asyncio
import logging

from core.config import settings
from db.database import Database
from db.repositories.assessment_criteria_repo import AssessmentCriteriaRepository
from db.repositories.completion_notification_repo import CompletionNotificationRepository
from db.repositories.comprehension_check_repo import ComprehensionCheckRepository
from db.repositories.course_repo import CourseRepository
from db.repositories.engagement_repo import EngagementRepository, NudgeRepository
from db.repositories.lesson_repo import LessonRepository
from db.repositories.lesson_view_repo import LessonViewRepository
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.user_repo import UserRepository
from services.ai_evaluation_service import AIEvaluationService
from services.lesson_completion_service import LessonCompletionService

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def run_forever() -> None:
    db = Database(settings.db.path)
    await db.connect()
    await db.run_migrations(settings.db.migrations_dir)

    user_repo = UserRepository(db.conn)
    lesson_repo = LessonRepository(db.conn)

    lesson_completion_service = LessonCompletionService(
        lesson_repo=lesson_repo,
        course_repo=CourseRepository(db.conn),
        user_repo=user_repo,
        license_node_repo=LicenseNodeRepository(db.conn),
        lesson_view_repo=LessonViewRepository(db.conn),
        notification_repo=CompletionNotificationRepository(db.conn),
        engagement_repo=EngagementRepository(db.conn),
        nudge_repo=NudgeRepository(db.conn),
    )

    service = AIEvaluationService(
        comprehension_repo=ComprehensionCheckRepository(db.conn),
        criteria_repo=AssessmentCriteriaRepository(db.conn),
        user_repo=user_repo,
        lesson_repo=lesson_repo,
        lesson_completion_service=lesson_completion_service,
    )

    logger.info(
        "AI evaluation worker ishga tushdi (poll_interval=%ss)",
        settings.anthropic.poll_interval_seconds,
    )
    try:
        while True:
            processed = await service.evaluate_pending_batch(limit=10)
            if processed:
                logger.info("%s ta comprehension_check baholandi", processed)
            await asyncio.sleep(settings.anthropic.poll_interval_seconds)
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(run_forever())
