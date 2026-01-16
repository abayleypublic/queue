from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from src import context

router = APIRouter(prefix="/user")


class UserResponse(BaseModel):
    """User information extracted from authentication headers."""
    username: Optional[str] = None
    email: Optional[str] = None
    groups: Optional[str] = None


@router.get("/me", response_model=UserResponse)
async def get_current_user() -> UserResponse:
    """
    Get the current authenticated user's information from request headers.
    
    Returns user details that were propagated from the authentication gateway.
    """
    return UserResponse(
        username=context.get_auth_user(),
        email=context.get_auth_email(),
        groups=context.get_auth_groups()
    )
