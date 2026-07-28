from flask import request

from app.extensions import db
from app.models.audit_logs import AuditLog


def create_audit_log(
    action,
    status,
    user_id=None,
    ip=None
):

    log = AuditLog(
        user_id=user_id,
        action=action,
        status=status,
        ip_address=ip or request.remote_addr
    )

    db.session.add(log)
    db.session.commit()

    return log