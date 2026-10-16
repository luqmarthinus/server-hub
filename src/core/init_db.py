from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.security import get_password_hash, verify_password
from src.models.user import User

# Demo defaults: intentionally simple so the stack works straight after cloning.
# Override with ADMIN_EMAIL / ADMIN_PASSWORD in .env, or change the password after first login.
DEFAULT_ADMIN_EMAIL = "server_admin@example.com"
DEFAULT_ADMIN_PASSWORD = "mzansi2026"
DEFAULT_ADMIN_FULL_NAME = "Server Administrator"

DEFAULT_PASSWORD_WARNING = (
    "Super admin {} is using the default password. Change it via the Profile page "
    "or set ADMIN_PASSWORD in .env before exposing this app beyond localhost."
)


async def create_default_admin(db: AsyncSession) -> None:
    """Create the super admin if it doesn't exist. The password is never logged."""
    email = settings.ADMIN_EMAIL or DEFAULT_ADMIN_EMAIL
    password = settings.ADMIN_PASSWORD or DEFAULT_ADMIN_PASSWORD

    result = await db.execute(select(User).where(User.email == email))
    admin = result.scalar_one_or_none()

    if admin:
        if verify_password(DEFAULT_ADMIN_PASSWORD, admin.hashed_password):
            logger.warning(DEFAULT_PASSWORD_WARNING, email)
        else:
            logger.info("Super admin already exists: {}", email)
        return

    db.add(
        User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=DEFAULT_ADMIN_FULL_NAME,
            is_active=True,
            is_superuser=True,
        )
    )
    await db.commit()
    logger.info("Super admin created: {}", email)
    if password == DEFAULT_ADMIN_PASSWORD:
        logger.warning(DEFAULT_PASSWORD_WARNING, email)
