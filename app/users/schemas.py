
"""User request validation schemas."""


class ValidationError(Exception):
    """Raised when incoming user data fails validation."""

    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__(str(errors))


def validate_user_creation_data(data: dict) -> dict:
    """Validate non-password fields used to create a user."""
    errors = {}

    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    full_name = (data.get("full_name") or "").strip() or None

    if not username or len(username) < 3:
        errors["username"] = "Username is required and must be at least 3 characters."

    if not email or "@" not in email:
        errors["email"] = "A valid email address is required."

    if errors:
        raise ValidationError(errors)

    return {
        "username": username,
        "email": email,
        "full_name": full_name,
    }


def validate_profile_update(data: dict) -> dict:
    """Validate and clean fields accepted by profile updates."""
    errors = {}
    allowed_fields = {"full_name"}
    unknown_fields = set(data) - allowed_fields

    if unknown_fields:
        errors["fields"] = (
            "Unsupported fields: " + ", ".join(sorted(unknown_fields))
        )

    if "full_name" in data:
        full_name = data["full_name"]
        if full_name is not None and not isinstance(full_name, str):
            errors["full_name"] = "Full name must be a string or null."
        elif isinstance(full_name, str) and len(full_name.strip()) > 150:
            errors["full_name"] = "Full name must not exceed 150 characters."

    if errors:
        raise ValidationError(errors)

    if "full_name" not in data:
        return {}

    return {"full_name": (data["full_name"] or "").strip() or None}


def parse_list_query(args) -> dict:
    """Parse and validate query params for listing/searching users.

    Supports ?search=<text>&page=<n>&per_page=<n>

    """
    search = (args.get("search") or "").strip() or None

    errors = {}
    page = _parse_positive_integer(args.get("page", 1), "page", errors)
    per_page = _parse_positive_integer(
        args.get("per_page", 10), "per_page", errors
    )

    if per_page is not None and per_page > 100:
        errors["per_page"] = "per_page must not exceed 100."

    if errors:
        raise ValidationError(errors)

    return {"search": search, "page": page, "per_page": per_page}


def _parse_positive_integer(value, field: str, errors: dict) -> int | None:
    """Parse a positive integer query parameter into an integer."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        errors[field] = f"{field} must be a positive integer."
        return None

    if parsed < 1:
        errors[field] = f"{field} must be a positive integer."
        return None

    return parsed
