@admin_bp.route("/users/<int:user_id>/suspend", methods=["POST"])
@jwt_required()
def suspend_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_suspended = True
    db.session.commit()

    return {"message": "User suspended"}, 200


@admin_bp.route("/users/<int:user_id>/activate", methods=["POST"])
@jwt_required()
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = True
    user.is_suspended = False
    db.session.commit()

    return {"message": "User activated"}, 200