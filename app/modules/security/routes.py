"""Future security support HTTP routes."""

from datetime import datetime, timedelta
from uuid import uuid4

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash

from app.modules.security import security_bp
from app.extensions import db
from app.models.users import User
from app.models.password_reset import PasswordResetToken
from app.services.audit import create_audit_log


@security_bp.post("/forgot-password")
def forgot_password():
    """Generate a password reset token."""

    data = request.get_json(silent=True) or {}

    email = data.get("email")

    user = db.session.scalar(
        db.select(User).where(User.email == email)
    )

    if user:

        token = str(uuid4())

        reset = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

        db.session.add(reset)

        create_audit_log(
            user_id=user.id,
            action="PASSWORD_RESET_REQUEST",
            status="SUCCESS"
        )

        db.session.commit()

        return jsonify({
            "message": "Password reset token generated",
            "token": token
        }), 200


    return jsonify({
        "message": "If account exists, reset instructions were sent"
    }), 200



@security_bp.post("/reset-password")
def reset_password():
    """Reset password using a valid reset token."""

    data = request.get_json(silent=True) or {}

    token = data.get("token")
    password = data.get("password")

    reset = db.session.scalar(
        db.select(PasswordResetToken)
        .where(
            PasswordResetToken.token == token
        )
    )

    if not reset or reset.used:
        return jsonify({
            "message": "Invalid token"
        }), 400


    user = db.session.get(
        User,
        reset.user_id
    )

    if user is None:
        return jsonify({
            "message": "User not found"
        }), 404


    user.password_hash = generate_password_hash(
        password
    )

    reset.used = True


    create_audit_log(
        user_id=user.id,
        action="PASSWORD_RESET",
        status="SUCCESS"
    )

    db.session.commit()


    return jsonify({
        "message": "Password changed successfully"
    }), 200



@security_bp.post("/change-password")
@jwt_required()
def change_password():
    """Change password for an authenticated user."""

    user_id = get_jwt_identity()

    data = request.get_json(silent=True) or {}

    new_password = data.get("new_password")


    user = db.session.get(
        User,
        int(user_id)
    )


    if user is None:
        return jsonify({
            "message": "User not found"
        }), 404


    user.password_hash = generate_password_hash(
        new_password
    )


    create_audit_log(
        user_id=user.id,
        action="PASSWORD_CHANGE",
        status="SUCCESS"
    )

    db.session.commit()


    return jsonify({
        "message": "Password updated"
    }), 200