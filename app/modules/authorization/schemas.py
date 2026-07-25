"""Authorization request validation schemas."""


class ValidationError(Exception):
    """Raised when incoming authorization data fails validation."""

    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__(str(errors))


def validate_role_data(data: dict) -> dict:
    """Validate role creation/update data."""
    if not isinstance(data, dict):
        raise ValidationError({"body": "A JSON object is required."})

    errors = {}

    allowed_fields = {"name", "description"}
    unknown_fields = set(data) - allowed_fields

    if unknown_fields:
        errors["fields"] = "Unsupported fields: " + ", ".join(sorted(unknown_fields))

    name = _validate_name(data.get("name"), "Role", errors)
    description = _validate_description(data.get("description"), errors)

    if errors:
        raise ValidationError(errors)

    return {
        "name": name,
        "description": description,
    }


def validate_permission_data(data: dict) -> dict:
    """Validate permission creation/update data."""
    if not isinstance(data, dict):
        raise ValidationError({"body": "A JSON object is required."})

    errors = {}

    allowed_fields = {"name", "description"}
    unknown_fields = set(data) - allowed_fields

    if unknown_fields:
        errors["fields"] = "Unsupported fields: " + ", ".join(sorted(unknown_fields))

    name = _validate_name(data.get("name"), "Permission", errors)
    description = _validate_description(data.get("description"), errors)

    if errors:
        raise ValidationError(errors)

    return {
        "name": name,
        "description": description,
    }


def validate_user_role_data(data: dict) -> dict:
    """Validate role assignment data."""
    if not isinstance(data, dict):
        raise ValidationError({"body": "A JSON object is required."})

    errors = {}

    allowed_fields = {"role_id"}
    unknown_fields = set(data) - allowed_fields

    if unknown_fields:
        errors["fields"] = "Unsupported fields: " + ", ".join(sorted(unknown_fields))

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


def _validate_name(value, label: str, errors: dict) -> str:
    """Validate a role or permission name."""
    if not isinstance(value, str) or not value.strip():
        errors["name"] = f"{label} name is required."
        return ""

    name = value.strip()
    if len(name) > 100:
        errors["name"] = f"{label} name must not exceed 100 characters."
    return name


def _validate_description(value, errors: dict) -> str | None:
    """Validate an optional description."""
    if value is None:
        return None
    if not isinstance(value, str):
        errors["description"] = "Description must be a string or null."
        return None

    description = value.strip() or None
    if description is not None and len(description) > 255:
        errors["description"] = "Description must not exceed 255 characters."
    return description
