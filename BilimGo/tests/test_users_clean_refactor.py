from pathlib import Path
import pytest
import pytest_asyncio

from db.database import Database
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.lesson_view_repo import LessonViewRepository
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.mentor_application_repo import MentorApplicationRepository
from db.repositories.user_repo import UserRepository
from services.user_service import UserService


@pytest_asyncio.fixture
async def test_db(tmp_path: Path):
    db_file = tmp_path / "test_users.db"
    db = Database(db_file)
    await db.connect()
    migrations_dir = Path(__file__).resolve().parent.parent / "db" / "migrations"
    await db.run_migrations(migrations_dir)
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_user_service_clean_architecture(test_db: Database):
    conn = test_db.conn
    user_repo = UserRepository(conn)
    access_grant_repo = AccessGrantRepository(conn)
    lesson_view_repo = LessonViewRepository(conn)
    license_node_repo = LicenseNodeRepository(conn)
    mentor_app_repo = MentorApplicationRepository(conn)

    service = UserService(
        user_repo=user_repo,
        access_grant_repo=access_grant_repo,
        lesson_view_repo=lesson_view_repo,
        license_node_repo=license_node_repo,
        mentor_app_repo=mentor_app_repo,
    )

    # 1. Create a user and get full profile
    profile = await service.get_full_profile(
        telegram_id=77701,
        tg_info={"username": "test_user", "first_name": "Test", "last_name": "User"},
    )
    assert profile["telegram_id"] == 77701
    assert profile["username"] == "@test_user"
    assert "daily_activity" in profile
    assert len(profile["daily_activity"]) == 14

    # 2. Update profile info
    await service.update_profile_info(
        telegram_id=77701,
        first_name="Ulugbek",
        last_name="Samadov",
        phone="+998901234567",
    )
    user = await user_repo.get_by_telegram_id(77701)
    assert user.full_name == "Ulugbek Samadov"
    assert user.phone == "+998901234567"

    # 3. List mentors
    mentors = await service.list_mentors_directory()
    assert len(mentors) >= 1

    # 4. Create mentor application
    app_res = await service.create_mentor_application(
        telegram_id=77701,
        full_name="Ulugbek Samadov",
        phone="+998901234567",
        course_direction="Backend Python",
        experience_bio="5 yillik dasturchiman",
    )
    assert app_res["success"] is True
    app_id = app_res["application_id"]

    # 5. Get my mentor application
    my_app = await service.get_my_mentor_application(77701)
    assert my_app["application"]["id"] == app_id
    assert my_app["application"]["status"] == "pending"

    # 6. Submit receipt
    receipt_res = await service.submit_mentor_application_receipt(
        telegram_id=77701,
        application_id=app_id,
        receipt_photo_id="photo_file_123",
    )
    assert receipt_res["success"] is True

    updated_app = await mentor_app_repo.get_by_id(app_id)
    assert updated_app.status == "receipt_submitted"
    assert updated_app.receipt_photo_id == "photo_file_123"
