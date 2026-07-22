"""User registration and profile business logic."""

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.users import User


class DuplicateUserError(Exception):
    """Raised when a username or email is already registered."""

    def __init__(self, field: str):
        self.field = field
        super().__init__(f"{field} is already taken.")


class UserNotFoundError(Exception):
    """Raised when a requested user does not exist."""


def register_user(data: dict) -> User:
    """Create a new user account.

    Rejects duplicate usernames/emails and hashes the password before
    storage
    """
    if User.query.filter_by(username=data["username"]).first():
        raise DuplicateUserError("username")

    if User.query.filter_by(email=data["email"]).first():
        raise DuplicateUserError("email")

    user = User(
        username=data["username"],
        email=data["email"],
        password_hash=generate_password_hash(data["password"]),
        full_name=data["full_name"],
    )

    db.session.add(user)
    db.session.commit()

    return user


def get_user_by_id(user_id: int) -> User:
    """Fetch a single user by id, or raise if not found."""
    user = db.session.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"No user with id {user_id}")
    return user


def update_profile(user_id: int, data: dict) -> User:
    """Update a user's profile fields (full_name only, for now)."""
    user = get_user_by_id(user_id)

    if "full_name" in data:
        user.full_name = (data.get("full_name") or "").strip() or None

    db.session.commit()
    return user


def verify_password(user: User, password: str) -> bool:
    """Check a plaintext password against the stored hash."""
    return check_password_hash(user.password_hash, password)


def list_users(search: str | None, page: int, per_page: int):
    """Return a paginated, optionally-searched list of users."""
    stmt = db.select(User)

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            db.or_(User.username.ilike(pattern), User.email.ilike(pattern))
        )

    stmt = stmt.order_by(User.id)
    pagination = db.paginate(
        stmt, page=page, per_page=per_page, error_out=False)

    return pagination
