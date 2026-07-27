from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token
from flask import request
from app.utils.audit import log_event  # if you implemented audit logging


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json

    user = User.query.filter_by(email=data["email"]).first()

    # ✅ Step 1: Check credentials
    if not user or not check_password_hash(user.password_hash, data["password"]):
        log_event(None, "LOGIN", "FAILED", request.remote_addr)
        return {"error": "Invalid credentials"}, 401

    # 🔴 Step 2: Account status checks (THIS IS WHAT YOU ASKED ABOUT)
    if not user.is_active:
        log_event(user.id, "LOGIN", "BLOCKED_INACTIVE", request.remote_addr)
        return {"error": "Account not activated"}, 403

    if user.is_suspended:
        log_event(user.id, "LOGIN", "BLOCKED_SUSPENDED", request.remote_addr)
        return {"error": "Account suspended"}, 403

    # ✅ Step 3: Generate token
    access_token = create_access_token(identity=user.id)

    log_event(user.id, "LOGIN", "SUCCESS", request.remote_addr)

    return {"access_token": access_token}, 200