"""Validation schemas for security requests."""


class ValidationError(Exception):
    """Raised when security request data is invalid."""

    def __init__(self, errors: dict[str, str]):
        super().__init__("Invalid security request.")
        self.errors = errors


def _validate_password(value, field, errors):
    if not isinstance(value, str) or len(value) < 8:
        errors[field] = "Must be a string containing at least 8 characters."


def validate_forgot_password_data(data: dict) -> dict:
    """Validate and normalize a password-reset request."""
    errors = {}
    email = data.get("email")
    if not isinstance(email, str) or "@" not in email:
        errors["email"] = "A valid email address is required."
    if errors:
        raise ValidationError(errors)
    return {"email": email.strip().lower()}


def validate_reset_password_data(data: dict) -> dict:
    """Validate a reset token and replacement password."""
    errors = {}
    token = data.get("token")
    if not isinstance(token, str) or not token.strip():
        errors["token"] = "A reset token is required."
    _validate_password(data.get("password"), "password", errors)
    if errors:
        raise ValidationError(errors)
    return {"token": token.strip(), "password": data["password"]}


def parse_audit_query(args) -> dict:
    """Validate audit pagination query parameters."""
    errors = {}
    values = {}
    for field, default in (("page", 1), ("per_page", 20)):
        raw_value = args.get(field, default)
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            errors[field] = "Must be a positive integer."
            continue
        if value < 1 or (field == "per_page" and value > 100):
            errors[field] = (
                "Must be between 1 and 100."
                if field == "per_page"
                else "Must be a positive integer."
            )
        values[field] = value
    if errors:
        raise ValidationError(errors)
    return values
