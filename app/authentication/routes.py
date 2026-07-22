"""Authentication HTTP routes."""

from flask import jsonify, request

from app.authentication import authentication_bp
from app.authentication.schemas import ValidationError, validate_registration_data
from app.authentication.services import (
    PasswordHashingNotImplementedError,
    register_user_account,
)


@authentication_bp.post("/register")
def register():
    """Validate registration input before authentication orchestration."""
    payload = request.get_json(silent=True) or {}

    try:
        clean_data = validate_registration_data(payload)
    except ValidationError as exc:
        return jsonify(errors=exc.errors), 400

    try:
        register_user_account(clean_data)
    except PasswordHashingNotImplementedError:
        return (
            jsonify(
                error="Password hashing is not yet implemented",
                status="registration_pending",
            ),
            501,
        )

    raise RuntimeError("Registration service returned without a response.")
