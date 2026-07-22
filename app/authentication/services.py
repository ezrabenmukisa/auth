"""Authentication business logic."""


class PasswordHashingNotImplementedError(Exception):
    """Raised until Authentication implements secure password hashing."""


def register_user_account(data: dict):
    """Temporarily stop registration before any database insertion."""
    raise PasswordHashingNotImplementedError
