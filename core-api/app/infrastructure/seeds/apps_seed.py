from app.extensions.db import db
from app.infrastructure.db.models import App, AppRoute

def seed_crm_app():

    # 🔎 Verifica se CRM já existe
    crm = App.query.get("crm")

    if not crm:
        crm = App(
            id="crm",
            name="CRM",
            base_path="/crm",
            icon="briefcase",
            type="module",
            version="1.0.0",
            active=True,
        )
        db.session.add(crm)
        db.session.commit()

    # ----------------------------
    # Rotas padrão CRM
    # ----------------------------

    default_routes = [
        {
            "path": "/crm/dashboard",
            "label": "Dashboard",
            "icon": "layout-dashboard",
            "order": 1,
            "show_in_menu": True,
        },
        {
            "path": "/crm/leads",
            "label": "Leads",
            "icon": "users",
            "order": 2,
            "show_in_menu": True,
        },
    ]

    for r in default_routes:

        exists = AppRoute.query.filter_by(
            app_id="crm",
            path=r["path"]
        ).first()

        if exists:
            continue

        route = AppRoute(
            app_id="crm",
            path=r["path"],
            label=r["label"],
            icon=r["icon"],
            order=r["order"],
            show_in_menu=r["show_in_menu"],
            active=True,
        )

        db.session.add(route)

    db.session.commit()
