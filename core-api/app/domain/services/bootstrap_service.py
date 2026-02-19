# app/domain/services/bootstrap_service.py

import os
from app.infrastructure.db.models import User
from app.extensions.db import db


def seed_initial_superadmin():

    email = os.getenv("INITIAL_SUPERADMIN_EMAIL")
    name = os.getenv("INITIAL_SUPERADMIN_NAME")

    if not email or not name:
        return

    user = User.query.filter_by(email=email).first()

    if user:
        if not user.is_superadmin:
            user.is_superadmin = True
            db.session.commit()
            print("🔥 Usuário promovido a superadmin:", email)
        return

    # ⚠️ Só cria se realmente quiser
    user = User(
        email=email,
        name=name,
        is_superadmin=True
    )

    db.session.add(user)
    db.session.commit()

    print("🔥 Superadmin inicial criado:", email)
