from contextlib import asynccontextmanager
import logging
from pathlib import Path

import aiosqlite

from core.config import settings
from core.exceptions import MigrationError

logger = logging.getLogger(__name__)

_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""


class Database:
    """Yagona aiosqlite connection ustidan ishlaydigan bog'lovchi qatlam."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database ulanmagan — avval connect() chaqiring")
        return self._conn

    async def connect(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self._conn.execute("PRAGMA busy_timeout=5000")
        await self._conn.commit()
        logger.info("Database ulandi: %s (WAL mode)", self._db_path)

    @asynccontextmanager
    async def transaction(self):
        try:
            yield self.conn
            await self.conn.commit()
        except Exception:
            await self.conn.rollback()
            raise

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def run_migrations(self, migrations_dir: Path) -> None:
        await self.conn.execute(_MIGRATIONS_TABLE)
        await self.conn.commit()

        applied_cursor = await self.conn.execute("SELECT filename FROM schema_migrations")
        applied = {row["filename"] for row in await applied_cursor.fetchall()}

        pending = sorted(p for p in migrations_dir.glob("*.sql") if p.name not in applied)

        for migration_file in pending:
            sql = migration_file.read_text(encoding="utf-8")
            try:
                await self.conn.executescript(sql)
                await self.conn.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (?)",
                    (migration_file.name,),
                )
                await self.conn.commit()
                logger.info("Migratsiya qo'llandi: %s", migration_file.name)
            except aiosqlite.Error as exc:
                await self.conn.rollback()
                raise MigrationError(f"{migration_file.name} bajarilmadi: {exc}") from exc


database = Database(settings.db.path)
