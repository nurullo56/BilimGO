import pytest
import pytest_asyncio
from pathlib import Path

from db.database import Database
from db.repositories.license_node_repo import LicenseNodeRepository
from db.repositories.royalty_repo import RoyaltyLedgerRepository
from db.repositories.sale_repo import Sale, SaleRepository
from db.repositories.course_repo import CourseRepository
from db.repositories.tariff_quota_repo import TariffQuotaRepository
from db.repositories.click_transaction_repo import ClickTransactionRepository
from db.repositories.access_grant_repo import AccessGrantRepository
from db.repositories.cabinet_repo import CabinetRepository
from db.repositories.chat_repo import ChatRepository
from db.repositories.user_repo import UserRepository
from services.royalty_service import RoyaltyService
from services.click_service import ClickService, ClickError
from services.payment_service import PaymentService
from services.cabinet_service import CabinetService


@pytest_asyncio.fixture
async def test_db(tmp_path: Path):
    db_file = tmp_path / "test.db"
    db = Database(db_file)
    await db.connect()
    
    # Run migrations
    migrations_dir = Path(__file__).resolve().parent.parent / "db" / "migrations"
    await db.run_migrations(migrations_dir)
    
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_royalty_service_limit_stage(test_db: Database):
    conn = test_db.conn
    node_repo = LicenseNodeRepository(conn)
    royalty_repo = RoyaltyLedgerRepository(conn)
    course_repo = CourseRepository(conn)
    quota_repo = TariffQuotaRepository(conn)

    # 1. Create root user & mentor in limit stage
    await conn.execute("INSERT INTO users (id, telegram_id, full_name) VALUES (1, 99999, 'Super Admin')")
    await conn.execute("INSERT INTO users (id, telegram_id, full_name) VALUES (10, 11111, 'Mentor Test')")
    await conn.execute("INSERT INTO license_nodes (id, owner_user_id, parent_id, stage, royalty_percent) VALUES (1, 1, NULL, 'hamkorlik', 0.0)")
    await conn.execute("INSERT INTO license_nodes (id, owner_user_id, parent_id, stage, royalty_percent) VALUES (2, 10, 1, 'limit', 20.0)")
    await conn.execute("INSERT INTO courses (id, title, base_price, status) VALUES (1, 'Logistika', 500000, 'published')")
    await conn.execute("INSERT INTO sales (id, student_id, course_id, license_node_id, amount, payment_provider, payment_status) VALUES (101, 10, 1, 2, 500000, 'click', 'paid')")
    await conn.commit()

    # Initialize quota
    await quota_repo.initialize_quotas_for_tariff(node_id=2, tariff_name="standart")
    
    royalty_service = RoyaltyService(
        license_node_repo=node_repo,
        royalty_repo=royalty_repo,
        tariff_quota_repo=quota_repo,
        course_repo=course_repo,
    )

    sale = Sale(
        id=101,
        student_id=10,
        course_id=1,
        license_node_id=2,
        amount=500000,
        payment_provider="click",
        payment_status="paid",
        external_txn_id="ext_101",
    )

    await royalty_service.distribute_for_sale(sale)

    # In limit stage within 15 days, 0 royalty ledger entries should be created for parent
    cursor = await conn.execute("SELECT * FROM royalty_ledger WHERE sale_id = 101")
    rows = await cursor.fetchall()
    assert len(rows) == 0, "Limit davrida ota tugunga royalti ajratilmasligi kerak"

    # Quota should be consumed by 1
    quota = await quota_repo.get_quota_for_course(2, "Logistika")
    assert quota is not None
    assert quota.used_quota == 1
    assert quota.remaining == 19


@pytest.mark.asyncio
async def test_royalty_service_hamkorlik_stage_cascade(test_db: Database):
    conn = test_db.conn
    node_repo = LicenseNodeRepository(conn)
    royalty_repo = RoyaltyLedgerRepository(conn)
    course_repo = CourseRepository(conn)
    quota_repo = TariffQuotaRepository(conn)

    # Create root node #1 and child node #2 in hamkorlik stage
    await conn.execute("INSERT INTO users (id, telegram_id, full_name) VALUES (1, 99999, 'Super Admin')")
    await conn.execute("INSERT INTO users (id, telegram_id, full_name) VALUES (10, 11111, 'Mentor Test')")
    await conn.execute("INSERT INTO license_nodes (id, owner_user_id, parent_id, stage, royalty_percent) VALUES (1, 1, NULL, 'hamkorlik', 0.0)")
    await conn.execute("INSERT INTO license_nodes (id, owner_user_id, parent_id, stage, royalty_percent) VALUES (2, 10, 1, 'hamkorlik', 20.0)")
    await conn.execute("INSERT INTO courses (id, title, base_price, status) VALUES (1, 'Logistika', 1000000, 'published')")
    await conn.execute("INSERT INTO sales (id, student_id, course_id, license_node_id, amount, payment_provider, payment_status) VALUES (202, 10, 1, 2, 1000000, 'click', 'paid')")
    await conn.commit()

    royalty_service = RoyaltyService(
        license_node_repo=node_repo,
        royalty_repo=royalty_repo,
        tariff_quota_repo=quota_repo,
        course_repo=course_repo,
    )

    sale = Sale(
        id=202,
        student_id=10,
        course_id=1,
        license_node_id=2,
        amount=1000000,
        payment_provider="click",
        payment_status="paid",
        external_txn_id="ext_202",
    )

    await royalty_service.distribute_for_sale(sale)

    # In hamkorlik stage, parent node 1 should receive 20% of 1,000,000 = 200,000 UZS
    cursor = await conn.execute("SELECT * FROM royalty_ledger WHERE sale_id = 202")
    rows = await cursor.fetchall()
    assert len(rows) == 1
    assert rows[0]["node_id"] == 1
    assert rows[0]["amount"] == 200000.0


@pytest.mark.asyncio
async def test_click_service_invalid_sign(test_db: Database):
    conn = test_db.conn
    sale_repo = SaleRepository(conn)
    click_repo = ClickTransactionRepository(conn)
    node_repo = LicenseNodeRepository(conn)
    royalty_repo = RoyaltyLedgerRepository(conn)
    course_repo = CourseRepository(conn)
    access_grant_repo = AccessGrantRepository(conn)
    cabinet_repo = CabinetRepository(conn)
    chat_repo = ChatRepository(conn)
    user_repo = UserRepository(conn)

    cabinet_service = CabinetService(cabinet_repo, chat_repo, node_repo, user_repo)
    royalty_service = RoyaltyService(node_repo, royalty_repo)
    payment_service = PaymentService(
        course_repo=course_repo,
        sale_repo=sale_repo,
        access_grant_repo=access_grant_repo,
        royalty_service=royalty_service,
        cabinet_service=cabinet_service,
        user_repo=user_repo,
    )
    click_service = ClickService(sale_repo, click_repo, payment_service)

    params = {
        "click_trans_id": "12345",
        "service_id": "1",
        "merchant_trans_id": "1",
        "amount": "100000",
        "action": "0",
        "sign_time": "2026-08-28 12:00:00",
        "sign_string": "invalid_signature_hash",
    }

    res = await click_service.prepare(params)
    assert res.error == ClickError.SIGN_FAILED


@pytest.mark.asyncio
async def test_live_session_lifecycle(test_db: Database):
    from db.repositories.live_session_repo import LiveSessionRepository
    from services.live_stream_service import LiveStreamManager

    conn = test_db.conn
    await conn.execute("INSERT INTO users (id, telegram_id, full_name) VALUES (1, 99999, 'Super Admin')")
    await conn.execute("INSERT INTO courses (id, title, base_price, status) VALUES (1, 'Logistika', 1000000, 'published')")
    await conn.commit()

    repo = LiveSessionRepository(conn)
    session_id = await repo.create(
        course_id=1,
        mentor_id=1,
        scheduled_at="2026-08-28 20:00",
        title="Jonli Efir Test",
        description="Amaliy savol-javob",
    )
    assert session_id is not None

    session = await repo.get_by_id(session_id)
    assert session is not None
    assert session.title == "Jonli Efir Test"
    assert session.status == "scheduled"

    # Start session
    await repo.set_status(session_id, "live", stream_key="stream_key_123")
    started = await repo.get_by_id(session_id)
    assert started.status == "live"
    assert started.stream_key == "stream_key_123"

    # End session
    await repo.set_status(session_id, "ended")
    ended = await repo.get_by_id(session_id)
    assert ended.status == "ended"

