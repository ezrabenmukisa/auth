
"""Registration and profile validation schemas."""


class ValidationError(Exception):
    """Raised when incoming user data fails validation."""

    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__(str(errors))


def validate_registration_data(data: dict) -> dict:
    """Validate registration payload.

    Rejects missing/invalid fields before the service layer runs,
    per PROPOSAL.md §9.1 ("validate registration data").
    Returns a cleaned dict of the fields the service layer needs.
    """
    errors = {}

    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    full_name = (data.get("full_name") or "").strip() or None

    if not username or len(username) < 3:
        errors["username"] = "Username is required and must be at least 3 characters."

    if not email or "@" not in email:
        errors["email"] = "A valid email address is required."

    if not password or len(password) < 8:
        errors["password"] = "Password is required and must be at least 8 characters."

    if errors:
        raise ValidationError(errors)

    return {
        "username": username,
        "email": email,
        "password": password,
        "full_name": full_name,
    }


def parse_list_query(args) -> dict:
    """Parse and validate query params for listing/searching users.

    Supports ?search=<text>&page=<n>&per_page=<n>

    """
    search = (args.get("search") or "").strip() or None

    try:
        page = int(args.get("page", 1))
    except (TypeError, ValueError):
        page = 1

    try:
        per_page = int(args.get("per_page", 10))
    except (TypeError, ValueError):
        per_page = 10

    page = max(page, 1)
    per_page = min(max(per_page, 1), 100)  # cap to avoid huge queries

    return {"search": search, "page": page, "per_page": per_page}
