"""HTTP routes for password security and account controls."""

from flask import current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.modules.authorization.services import require_permission
from app.modules.security import security_bp
from app.modules.security.schemas import (
    ValidationError,
    parse_audit_query,
    validate_forgot_password_data,
    validate_reset_password_data,
)
from app.modules.security.services import (
    SecurityError,
    SecurityPersistenceError,
    list_audit_logs,
    request_password_reset,
    send_password_reset_email,
    set_account_suspension,
)
from app.modules.security.services import (
    reset_password as reset_password_service,
)


@security_bp.post("/forgot-password")
def forgot_password():
    """Accept a password-reset request without disclosing account existence."""
    try:
        data = validate_forgot_password_data(request.get_json(silent=True) or {})
        token = request_password_reset(data["email"], request.remote_addr)
        if token is not None:
            send_password_reset_email(data["email"], token)
    except ValidationError as exc:
        return jsonify(errors=exc.errors), 400
    except SecurityPersistenceError as exc:
        return jsonify(error=str(exc)), 500

    response = {
        "message": "If the account exists, password-reset instructions were created."
    }
    if current_app.testing and token is not None:
        response["reset_token"] = token
    return jsonify(response), 200


@security_bp.post("/reset-password")
def reset_password():
    """Reset a password with an unused, unexpired reset token."""
    try:
        data = validate_reset_password_data(request.get_json(silent=True) or {})
        reset_password_service(**data, ip_address=request.remote_addr)
    except ValidationError as exc:
        return jsonify(errors=exc.errors), 400
    except SecurityError as exc:
        status = 500 if isinstance(exc, SecurityPersistenceError) else 400
        return jsonify(error=str(exc)), status
    return jsonify(message="Password changed successfully."), 200


@security_bp.post("/users/<int:user_id>/suspend")
@jwt_required()
@require_permission("users.suspend")
def suspend_user(user_id):
    """Suspend another user's account."""
    try:
        set_account_suspension(
            user_id,
            suspended=True,
            actor_id=int(get_jwt_identity()),
            ip_address=request.remote_addr,
        )
    except SecurityError as exc:
        status = 500 if isinstance(exc, SecurityPersistenceError) else 400
        return jsonify(error=str(exc)), status
    return jsonify(message="User suspended."), 200


@security_bp.post("/users/<int:user_id>/activate")
@jwt_required()
@require_permission("users.suspend")
def activate_user(user_id):
    """Reactivate another user's account."""
    try:
        set_account_suspension(
            user_id,
            suspended=False,
            actor_id=int(get_jwt_identity()),
            ip_address=request.remote_addr,
        )
    except SecurityError as exc:
        status = 500 if isinstance(exc, SecurityPersistenceError) else 400
        return jsonify(error=str(exc)), status
    return jsonify(message="User activated."), 200


@security_bp.get("/audit-logs")
@jwt_required()
@require_permission("audit.read")
def get_audit_logs():
    """Return paginated security events to authorized administrators."""
    try:
        query = parse_audit_query(request.args)
    except ValidationError as exc:
        return jsonify(errors=exc.errors), 400

    pagination = list_audit_logs(**query)
    return (
        jsonify(
            events=[
                {
                    "id": event.id,
                    "user_id": event.user_id,
                    "action": event.action,
                    "status": event.status,
                    "ip_address": event.ip_address,
                    "created_at": event.created_at.isoformat(),
                }
                for event in pagination.items
            ],
            page=pagination.page,
            per_page=pagination.per_page,
            total=pagination.total,
            total_pages=pagination.pages,
        ),
        200,
    )
