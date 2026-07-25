"""Authorization request validation schemas."""


class ValidationError(Exception):
    """Raised when incoming authorization data fails validation."""

    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__(str(errors))


def validate_role_data(data: dict) -> dict:
    """Validate role creation/update data."""
    errors = {}

    allowed_fields = {"name", "description"}
    unknown_fields = set(data) - allowed_fields

    if unknown_fields:
        errors["fields"] = (
            "Unsupported fields: " + ", ".join(sorted(unknown_fields))
        )

    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip() or None

    if not name:
        errors["name"] = "Role name is required."
    elif len(name) > 100:
        errors["name"] = "Role name must not exceed 100 characters."

    if (
        description is not None
        and not isinstance(description, str)
    ):
        errors["description"] = "Description must be a string or null."
    elif description is not None and len(description) > 255:
        errors["description"] = (
            "Description must not exceed 255 characters."
        )

    if errors:
        raise ValidationError(errors)

    return {
        "name": name,
        "description": description,
    }


def validate_permission_data(data: dict) -> dict:
    """Validate permission creation/update data."""
    errors = {}

    allowed_fields = {"name", "description"}
    unknown_fields = set(data) - allowed_fields

    if unknown_fields:
        errors["fields"] = (
            "Unsupported fields: " + ", ".join(sorted(unknown_fields))
        )

    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip() or None

    if not name:
        errors["name"] = "Permission name is required."
    elif len(name) > 100:
        errors["name"] = (
            "Permission name must not exceed 100 characters."
        )

    if (
        description is not None
        and not isinstance(description, str)
    ):
        errors["description"] = "Description must be a string or null."
    elif description is not None and len(description) > 255:
        errors["description"] = (
            "Description must not exceed 255 characters."
        )

    if errors:
        raise ValidationError(errors)

    return {
        "name": name,
        "description": description,
    }


def validate_user_role_data(data: dict) -> dict:
    """Validate role assignment data."""
    errors = {}

    allowed_fields = {"role_id"}
    unknown_fields = set(data) - allowed_fields

    if unknown_fields:
        errors["fields"] = (
            "Unsupported fields: " + ", ".join(sorted(unknown_fields))
        )

    role_id = _parse_positive_integer(
        data.get("role_id"),
        "role_id",
        errors,
    )

    if errors:
        raise ValidationError(errors)

    return {
        "role_id": role_id,
    }


def _parse_positive_integer(value, field: str, errors: dict) -> int | None:
    """Parse a positive integer into an integer."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        errors[field] = f"{field} must be a positive integer."
        return None

    if parsed < 1:
        errors[field] = f"{field} must be a positive integer."
        return None

    return parsed