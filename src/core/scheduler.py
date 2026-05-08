from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from src.api.reports import generate_report
from src.core.database import AsyncSessionLocal
from src.models.user import User
from loguru import logger


async def scheduled_report():
    """Generate a report every minute using a system user."""
    async with AsyncSessionLocal() as db:
        # Find a user to own the report (first superuser, else first user)
        result = await db.execute(select(User).where(User.is_superuser))
        user = result.scalar_one_or_none()
        if not user:
            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
        if not user:
            logger.warning("No user found in database; skipping scheduled report.")
            return
        try:
            await generate_report(user, db)
            logger.debug("Scheduled report generated successfully.")
        except Exception as e:
            logger.error(f"Failed to generate scheduled report: {e}")


scheduler = AsyncIOScheduler()
scheduler.add_job(
    scheduled_report, trigger=IntervalTrigger(minutes=1), id="auto_report"
)
