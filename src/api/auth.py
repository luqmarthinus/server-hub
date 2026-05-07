from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.database import get_db
from src.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from src.models.user import User
from src.schemas.user import UserCreate, UserResponse
from src.schemas.token import Token
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    email = payload.get("sub")
    if email is None:
        raise credentials_exception
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account. Email must be unique and valid format.",
    response_description="The created user object (without password)."
)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.

    - **email**: valid email address (unique)
    - **password**: plain text (will be hashed)
    - **full_name**: optional display name

    Example request:
        {
            "email": "dev@example.com",
            "password": "secure123",
            "full_name": "Developer"
        }

    Returns the created user (id, email, full_name, is_active, is_superuser, created_at).
    """
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
        is_superuser=False,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post(
    "/login",
    response_model=Token,
    summary="Login with email and password",
    description="Returns a JWT access token. Use this token in the Authorization header as `Bearer <token>`."
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate and receive an access token.

    - **username**: user's email (OAuth2 standard field)
    - **password**: user's password

    Example request (application/x-www-form-urlencoded):
        username=user@example.com&password=secure123

    Example response (200):
        {
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "token_type": "bearer"
        }

    Use the token as: `Authorization: Bearer <access_token>`
    """
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user information",
    description="Returns the profile of the authenticated user. Requires a valid Bearer token."
)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get the authenticated user's profile.

    Headers:
        Authorization: Bearer <access_token>

    Returns the user object (id, email, full_name, is_active, is_superuser, created_at).
    """
    return current_user

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.put("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change the authenticated user's password.
    Requires the current password for verification.
    """
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    new_hashed = get_password_hash(request.new_password)
    current_user.hashed_password = new_hashed
    db.add(current_user)
    await db.commit()
    return {"message": "Password updated successfully"}

@router.delete("/delete-account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete the authenticated user's account and all associated reports.
    """
    await db.delete(current_user)
    await db.commit()
    return None