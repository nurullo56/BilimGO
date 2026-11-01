from pathlib import Path
import pytest
import pytest_asyncio

from db.database import Database
from db.repositories.admin_repo import AdminRepository
from db.repositories.lesson_view_repo import LessonViewRepository
from db.repositories.user_repo import UserRepository
from services.analytics_service import AnalyticsService


@pytest_asyncio.fixture
async def test_db(tmp_path: Path):
    db_file = tmp_path / "test_analytics.db"
    db = Database(db_file)
    await db.connect()
    migrations_dir = Path(__file__).resolve().parent.parent / "db" / "migrations"
    await db.run_migrations(migrations_dir)
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_analytics_clean_architecture(test_db: Database):
    conn = test_db.conn
    user_repo = UserRepository(conn)
    admin_repo = AdminRepository(conn)
    view_repo = LessonViewRepository(conn)

    service = AnalyticsService(
        lesson_view_repo=view_repo,
        admin_repo=admin_repo,
    )

    # 1. Create mentor and student
    mentor = await user_repo.get_or_create(telegram_id=99901, full_name="Super Mentor")
    await conn.execute("UPDATE users SET role = 'mentor', status = 'active' WHERE id = ?", (mentor.id,))

    student = await user_repo.get_or_create(telegram_id=99902, full_name="Talaba Rustam")

    # 2. Create courses and nodes
    await conn.execute(
        "INSERT INTO courses (id, title, base_price, status) VALUES (1, 'Frontend Kursi', 200000, 'published')"
    )
    await conn.execute(
        "INSERT INTO license_nodes (id, owner_user_id, parent_id, stage, royalty_percent) VALUES (1, ?, NULL, 'hamkorlik', 0.0)",
        (mentor.id,),
    )
    await conn.execute(
        "INSERT INTO cabinets (id, owner_node_id, display_name, branding_config) VALUES (1, 1, 'Frontend Guruhi', '{\"mentor_name\": \"Super Mentor\", \"course_title\": \"Frontend Kursi\"}')"
    )
    await conn.execute(
        "INSERT INTO cabinet_members (cabinet_id, user_id, role_in_cabinet) VALUES (1, ?, 'student')",
        (student.id,),
    )
    await conn.execute(
        "INSERT INTO sales (id, student_id, course_id, license_node_id, amount, payment_provider, payment_status) VALUES (1, ?, 1, 1, 200000, 'click', 'paid')",
        (student.id,),
    )
    await conn.commit()

    # 3. Test get_platform_overview
    overview = await service.get_platform_overview()
    assert overview["total_users"] >= 2
    assert overview["active_mentors"] >= 1
    assert overview["active_courses"] == 1
    assert overview["total_sales_count"] == 1
    assert overview["total_revenue"] == 200000
    assert overview["total_cabinets"] == 1

    # 4. Test get_cabinet_students_activity
    activity = await service.get_cabinet_students_activity(cabinet_id="cab-1")
    assert len(activity) == 1
    st = activity[0]
    assert st["full_name"] == "Talaba Rustam"
    assert st["mentor_name"] == "Super Mentor"
    assert st["course_title"] == "Frontend Kursi"
    assert st["cabinet_id"] == "cab-1"
