from contextvars import ContextVar
from typing import Optional

auth_user: ContextVar[Optional[str]] = ContextVar('auth_user', default=None)
auth_email: ContextVar[Optional[str]] = ContextVar('auth_email', default=None)
auth_groups: ContextVar[Optional[str]] = ContextVar('auth_groups', default=None)
auth_name: ContextVar[Optional[str]] = ContextVar('auth_name', default=None)

def get_auth_user() -> Optional[str]:
    """Get the authenticated user from context."""
    return auth_user.get()


def get_auth_email() -> Optional[str]:
    """Get the authenticated user's email from context."""
    return auth_email.get()


def get_auth_groups() -> Optional[str]:
    """Get the authenticated user's groups from context."""
    return auth_groups.get()


def get_auth_name() -> Optional[str]:
    """Get the authenticated user's name from context."""
    return auth_name.get()


def set_auth_context(user: Optional[str], email: Optional[str], groups: Optional[str], name: Optional[str] = None) -> None:
    """
    Set all auth context variables at once.
    Used by workflows to propagate auth to activities.
    """
    auth_name.set(name)
    auth_user.set(user)
    auth_email.set(email)
    auth_groups.set(groups)
