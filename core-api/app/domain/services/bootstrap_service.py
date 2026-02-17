# app/domain/services/bootstrap_service.py


import os
from app.infrastructure.db.models import User
from app.extensions.db import db


def seed_initial_superadmin():
    """
    Cria superadmin inicial apenas se:
    - Variáveis de ambiente estiverem definidas
    - Usuário ainda não existir
    """

    email = os.getenv("INITIAL_SUPERADMIN_EMAIL")
    name = os.getenv("INITIAL_SUPERADMIN_NAME")

    # 🔒 Não faz nada se não estiver configurado
    if not email or not name:
        return

    existing = User.query.filter_by(email=email).first()

    if existing:
        # Se já existir, apenas garante que seja superadmin
        if not existing.is_superadmin:
            existing.is_superadmin = True
            db.session.commit()
        return

    # Criar usuário superadmin
    user = User(
        email=email,
        name=name,
        is_superadmin=True
    )

    db.session.add(user)
    db.session.commit()

    print("🔥 Superadmin inicial criado:", email)
