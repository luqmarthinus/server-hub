from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.core.database import get_db
from src.api.auth import get_current_user
from src.core.security import get_password_hash
from src.models.user import User
from src.models.report import ServerReport
from src.schemas.user import UserCreate

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


async def require_superuser(current_user: User = Depends(get_current_user)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/users")
async def list_users(
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    List all users with their report counts.
    Admin only.
    """
    stmt = (
        select(
            User.id,
            User.email,
            User.full_name,
            User.is_active,
            User.is_superuser,
            User.created_at,
            func.count(ServerReport.id).label("report_count"),
        )
        .outerjoin(ServerReport, User.id == ServerReport.user_id)
        .group_by(User.id)
    )
    result = await db.execute(stmt)
    users = result.mappings().all()
    return {"users": users}


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new user (admin only). Password is provided in plain text, hashed automatically.
    """
    existing = await db.execute(select(User).where(User.email == user_data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists")
    hashed = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed,
        full_name=user_data.full_name,
        is_active=True,
        is_superuser=False,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {"id": new_user.id, "email": new_user.email, "full_name": new_user.full_name}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a user by ID. Cannot delete yourself or the only remaining super admin.
    """
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_superuser:
        super_count = await db.execute(
            select(func.count()).select_from(User).where(User.is_superuser)
        )
        if super_count.scalar() <= 1:
            raise HTTPException(
                status_code=400, detail="Cannot delete the only super admin account"
            )
    await db.delete(user)
    await db.commit()
    return None


@router.put("/users/{user_id}/role")
async def toggle_superuser(
    user_id: int,
    admin: User = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Toggle is_superuser flag for a user. Cannot change your own role.
    """
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_superuser = not user.is_superuser
    await db.commit()
    return {"id": user.id, "is_superuser": user.is_superuser}
