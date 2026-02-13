from flask import request, g
from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.db.models import User
from app.extensions import db
from datetime import datetime

jwt_service = JWTService()


def authenticate():
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]
    claims = jwt_service.verify_token(token)

    user_id = claims.get("sub")
    email = claims.get("email")
    name = claims.get("name")

    user = User.query.filter_by(email=email).first()

    if not user:
        user = User(
            id=user_id,
            email=email,
            name=name
        )
        db.session.add(user)

    user.last_login_at = datetime.utcnow()
    db.session.commit()

    g.current_user = user
    return user
