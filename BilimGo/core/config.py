from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=True)


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Majburiy environment o'zgaruvchi topilmadi: {key}")
    return value


@dataclass(frozen=True, slots=True)
class BotConfig:
    token: str
    admin_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    path: Path
    migrations_dir: Path


@dataclass(frozen=True, slots=True)
class RelayConfig:
    internal_url: str
    internal_secret: str
    chunk_size: int


@dataclass(frozen=True, slots=True)
class DeliveryConfig:
    token_ttl_seconds: int


@dataclass(frozen=True, slots=True)
class ClickConfig:
    service_id: str
    merchant_id: str
    secret_key: str

    def build_checkout_url(self, sale_id: int, amount: float, return_url: str) -> str:
        return (
            "https://my.click.uz/services/pay"
            f"?service_id={self.service_id}&merchant_id={self.merchant_id}"
            f"&amount={amount}&transaction_param={sale_id}&return_url={return_url}"
        )


@dataclass(frozen=True, slots=True)
class PaymeConfig:
    merchant_id: str
    secret_key: str

    def build_checkout_url(self, sale_id: int, amount: float) -> str:
        import base64

        amount_tiyin = int(amount * 100)
        params = f"m={self.merchant_id};ac.sale_id={sale_id};a={amount_tiyin}"
        encoded = base64.b64encode(params.encode()).decode()
        return f"https://checkout.paycom.uz/{encoded}"


@dataclass(frozen=True, slots=True)
class WebAppConfig:
    base_url: str

    def course_url(self, course_id: int) -> str:
        return f"{self.base_url}/course/{course_id}"

    def cabinet_url(self, cabinet_id: int) -> str:
        return f"{self.base_url}/cabinet/{cabinet_id}"


@dataclass(frozen=True, slots=True)
class AnthropicConfig:
    api_key: str
    model: str
    poll_interval_seconds: int


@dataclass(frozen=True, slots=True)
class PathConfig:
    userbot_db_path: Path
    downloads_dir: Path
    frontend_dist_dir: Path


@dataclass(frozen=True, slots=True)
class Settings:
    bot: BotConfig
    db: DatabaseConfig
    relay: RelayConfig
    delivery: DeliveryConfig
    click: ClickConfig
    payme: PaymeConfig
    anthropic: AnthropicConfig
    webapp: WebAppConfig
    paths: PathConfig
    debug: bool


def load_settings() -> Settings:
    admin_ids_raw = os.getenv("ADMIN_IDS", "")
    admin_ids = tuple(int(x) for x in admin_ids_raw.split(",") if x.strip())

    userbot_db_raw = os.getenv("USERBOT_DB_PATH")
    userbot_db_path = (
        Path(userbot_db_raw).resolve()
        if userbot_db_raw
        else BASE_DIR.parent / "BilimGoUserBot" / "BilimGoUserBot" / "userbot_database.db"
    )

    downloads_dir_raw = os.getenv("DOWNLOADS_DIR")
    downloads_dir = (
        Path(downloads_dir_raw).resolve()
        if downloads_dir_raw
        else BASE_DIR / "data" / "downloads"
    )

    frontend_dist_raw = os.getenv("FRONTEND_DIST_DIR")
    frontend_dist_dir = (
        Path(frontend_dist_raw).resolve()
        if frontend_dist_raw
        else BASE_DIR.parent / "frontend" / "dist"
    )

    return Settings(
        bot=BotConfig(
            token=_require("BOT_TOKEN"),
            admin_ids=admin_ids,
        ),
        db=DatabaseConfig(
            path=BASE_DIR / os.getenv("DB_PATH", "data/bilimgo.db"),
            migrations_dir=BASE_DIR / "db" / "migrations",
        ),
        relay=RelayConfig(
            internal_url=os.getenv("RELAY_INTERNAL_URL", "http://127.0.0.1:8081"),
            internal_secret=os.getenv("RELAY_INTERNAL_SECRET", "change-me"),
            chunk_size=1024 * 1024,
        ),
        delivery=DeliveryConfig(
            token_ttl_seconds=int(os.getenv("DELIVERY_TOKEN_TTL_SECONDS", "600")),
        ),
        click=ClickConfig(
            service_id=os.getenv("CLICK_SERVICE_ID", ""),
            merchant_id=os.getenv("CLICK_MERCHANT_ID", ""),
            secret_key=os.getenv("CLICK_SECRET_KEY", ""),
        ),
        payme=PaymeConfig(
            merchant_id=os.getenv("PAYME_MERCHANT_ID", ""),
            secret_key=os.getenv("PAYME_SECRET_KEY", ""),
        ),
        anthropic=AnthropicConfig(
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5"),
            poll_interval_seconds=int(os.getenv("AI_EVAL_POLL_INTERVAL_SECONDS", "15")),
        ),
        webapp=WebAppConfig(
            base_url=os.getenv("WEBAPP_BASE_URL", "https://bilimgo.example.com"),
        ),
        paths=PathConfig(
            userbot_db_path=userbot_db_path,
            downloads_dir=downloads_dir,
            frontend_dist_dir=frontend_dist_dir,
        ),
        debug=os.getenv("DEBUG", "false").lower() == "true",
    )


settings = load_settings()