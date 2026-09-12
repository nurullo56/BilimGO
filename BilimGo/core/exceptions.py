class BilimGoError(Exception):
    """Barcha domen xatoliklari uchun bazaviy klass."""


class AccessDeniedError(BilimGoError):
    """Foydalanuvchida kerakli ruxsat yo'q."""


class NotFoundError(BilimGoError):
    """So'ralgan yozuv topilmadi."""


class MigrationError(BilimGoError):
    """Migratsiya bajarilishida xatolik."""
