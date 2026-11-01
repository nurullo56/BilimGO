from pathlib import Path
import pytest
import pytest_asyncio

from db.database import Database
from db.repositories.cabinet_repo import CabinetRepository
from db.repositories.chat_repo import ChatRepository
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.user_repo import UserRepository
from services.cabinet_service import CabinetService


@pytest_asyncio.fixture
async def test_db(tmp_path: Path):
    db_file = tmp_path / "test_cabinet.db"
    db = Database(db_file)
    await db.connect()
    migrations_dir = Path(__file__).resolve().parent.parent / "db" / "migrations"
    await db.run_migrations(migrations_dir)
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_cabinet_flow_and_clean_architecture(test_db: Database):
    conn = test_db.conn
    user_repo = UserRepository(conn)
    cabinet_repo = CabinetRepository(conn)
    chat_repo = ChatRepository(conn)
    node_repo = LicenseNodeRepository(conn)

    service = CabinetService(
        cabinet_repo=cabinet_repo,
        chat_repo=chat_repo,
        license_node_repo=node_repo,
        user_repo=user_repo,
    )

    # 1. Create a user, root node, and course
    user = await user_repo.get_or_create(telegram_id=123456, full_name="Ali Valiyev")
    assert user.id is not None
    await conn.execute(
        "INSERT INTO courses (id, title, base_price, status) VALUES (1, 'Python Asoslari', 100000, 'published')"
    )
    await conn.execute(
        "INSERT INTO license_nodes (id, owner_user_id, parent_id, stage, royalty_percent) VALUES (1, ?, NULL, 'hamkorlik', 0.0)",
        (user.id,),
    )
    await conn.commit()

    # 2. Create cabinet flow
    res = await service.create_cabinet_flow(
        creator_user_id=user.id,
        display_name="Python Darslari",
        avatar="🐍",
        description="Boshlang'ich dasturlash",
        course_id=1,
        course_title="Python Asoslari",
        initial_message="Xush kelibsiz!",
    )

    assert res["display_name"] == "Python Darslari"
    assert res["avatar"] == "🐍"
    assert res["role_in_cabinet"] == "mentor"
    cab_id = int(res["id"].replace("cab-", ""))

    # 3. Check get_user_cabinets
    cabinets = await service.get_user_cabinets(user.id, is_admin=False)
    assert len(cabinets) == 1
    assert cabinets[0]["id"] == f"cab-{cab_id}"
    assert cabinets[0]["display_name"] == "Python Darslari"
    assert cabinets[0]["role_in_cabinet"] == "mentor"

    # 4. Update cabinet branding
    updated = await service.update_cabinet_branding(
        cabinet_id=cab_id,
        display_name="Python Pro Darslari",
        avatar="🚀",
        description="Mukammal Python",
    )
    assert updated["display_name"] == "Python Pro Darslari"
    assert updated["avatar"] == "🚀"
    assert updated["description"] == "Mukammal Python"

    # 5. Delete cabinet
    await service.delete_cabinet(cab_id)
    remaining = await service.get_user_cabinets(user.id, is_admin=False)
    assert len(remaining) == 0
