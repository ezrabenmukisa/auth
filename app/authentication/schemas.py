"""Authentication request validation schemas."""


class ValidationError(Exception):
    """Raised when authentication input fails validation."""

    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        super().__init__(str(errors))


def validate_registration_data(data: dict) -> dict:
    """Validate and normalize an account-registration payload."""
    if not isinstance(data, dict):
        raise ValidationError({"body": "A JSON object is required."})

    errors = {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    full_name = (data.get("full_name") or "").strip() or None

    if not username or len(username) < 3:
        errors["username"] = (
            "Username is required and must be at least 3 characters."
        )
    if not email or "@" not in email:
        errors["email"] = "A valid email address is required."
    if not isinstance(password, str) or len(password) < 8:
        errors["password"] = (
            "Password is required and must be at least 8 characters."
        )
    if full_name is not None and len(full_name) > 150:
        errors["full_name"] = "Full name must not exceed 150 characters."

    if errors:
        raise ValidationError(errors)

    return {
        "username": username,
        "email": email,
        "password": password,
        "full_name": full_name,
    }


def validate_login_data(data: dict) -> dict[str, str]:
    """Validate and normalize a login request."""
    if not isinstance(data, dict):
        raise ValidationError({"body": "A JSON object is required."})

    errors = {}
    identifier = (data.get("identifier") or "").strip()
    password = data.get("password") or ""

    if not identifier:
        errors["identifier"] = "Username or email is required."
    if not isinstance(password, str) or not password:
        errors["password"] = "Password is required."

    if errors:
        raise ValidationError(errors)

    return {"identifier": identifier, "password": password}
