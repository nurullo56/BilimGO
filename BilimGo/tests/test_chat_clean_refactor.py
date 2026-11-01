from pathlib import Path
import pytest
import pytest_asyncio

from db.database import Database
from db.repositories.chat_repo import ChatRepository
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.user_repo import UserRepository
from services.messaging_service import MessagingService


@pytest_asyncio.fixture
async def test_db(tmp_path: Path):
    db_file = tmp_path / "test_chat.db"
    db = Database(db_file)
    await db.connect()
    migrations_dir = Path(__file__).resolve().parent.parent / "db" / "migrations"
    await db.run_migrations(migrations_dir)
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_chat_messaging_clean_architecture(test_db: Database):
    conn = test_db.conn
    user_repo = UserRepository(conn)
    chat_repo = ChatRepository(conn)
    service = MessagingService(chat_repo)

    # 1. Create 2 users and dependencies
    sender = await user_repo.get_or_create(telegram_id=11111, full_name="Mentor Bek")
    student = await user_repo.get_or_create(telegram_id=22222, full_name="Talaba Jon")

    await conn.execute(
        "INSERT INTO courses (id, title, base_price, status) VALUES (1, 'Test Kurs', 10000, 'published')"
    )
    await conn.execute(
        "INSERT INTO license_nodes (id, owner_user_id, parent_id, stage, royalty_percent) VALUES (1, ?, NULL, 'hamkorlik', 0.0)",
        (sender.id,),
    )
    await conn.execute(
        "INSERT INTO cabinets (id, owner_node_id, display_name) VALUES (1, 1, 'Test Kabinet')"
    )
    await conn.commit()

    # 2. Send message from sender (mentor)
    msg_out = await service.send_room_message(
        raw_id="cab-1",
        user_id=sender.id,
        user_name=sender.full_name,
        user_role="mentor",
        content="Salom talabalar!",
    )
    assert msg_out["content"] == "Salom talabalar!"
    assert msg_out["is_me"] is True
    assert msg_out["sender_name"] == "Mentor Bek"

    # 3. Poll messages from student's perspective
    messages = await service.get_room_messages(
        raw_id="cab-1",
        user_id=student.id,
        user_tg_id=student.telegram_id,
        after_id=0,
    )
    assert len(messages) == 1
    assert messages[0]["content"] == "Salom talabalar!"
    assert messages[0]["is_me"] is False  # From student perspective, it's not me
    assert messages[0]["sender_name"] == "Mentor Bek"

    # 4. Student replies
    msg_reply = await service.send_room_message(
        raw_id="cab-1",
        user_id=student.id,
        user_name=student.full_name,
        user_role="student",
        content="Va alaykum assalom ustoz!",
    )
    assert msg_reply["is_me"] is True

    # 5. Check all messages in room
    all_msgs = await service.get_room_messages(
        raw_id="cab-1",
        user_id=student.id,
        user_tg_id=student.telegram_id,
        after_id=0,
    )
    assert len(all_msgs) == 2
    assert all_msgs[1]["is_me"] is True
