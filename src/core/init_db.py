from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.user import User
from src.core.security import get_password_hash

DEFAULT_ADMIN_EMAIL = "server_admin@example.com"
DEFAULT_ADMIN_PASSWORD = "mzansi2026"
DEFAULT_ADMIN_FULL_NAME = "Server Administrator"


async def create_default_admin(db: AsyncSession):
    """Create default super admin if it doesn't exist."""
    result = await db.execute(select(User).where(User.email == DEFAULT_ADMIN_EMAIL))
    admin = result.scalar_one_or_none()
    if not admin:
        hashed = get_password_hash(DEFAULT_ADMIN_PASSWORD)
        new_admin = User(
            email=DEFAULT_ADMIN_EMAIL,
            hashed_password=hashed,
            full_name=DEFAULT_ADMIN_FULL_NAME,
            is_active=True,
            is_superuser=True,
        )
        db.add(new_admin)
        await db.commit()
        print(
            f"Default super admin created: {DEFAULT_ADMIN_EMAIL} / {DEFAULT_ADMIN_PASSWORD}"
        )
    else:
        print("Default super admin already exists")
