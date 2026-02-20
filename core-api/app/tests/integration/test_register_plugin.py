import uuid

from app.infrastructure.plugins.unit_of_work import SqlAlchemyUnitOfWork
from app.application.plugins.register_plugin import RegisterPluginUseCase
from app.application.plugins.manifest_validator import ManifestValidator

from app.infrastructure.db.models import (
    App,
    Permission,
    AppRoute,
    AppManifest,
    AuditLog,
    User,
)


# ==========================================================
# UTIL
# ==========================================================

def create_test_user(db_session):
    user = User(
        id=uuid.uuid4(),
        email=f"test-{uuid.uuid4()}@delpi.com",
        name="Test User"
    )
    db_session.add(user)
    db_session.flush()  # garante persistência antes do FK
    return user


def make_manifest(version="1.0.0", extra_permissions=None, extra_routes=None):
    permissions = [
        {"code": "crm.access", "description": "Acesso", "module": "crm"}
    ]

    routes = [
        {"path": "/crm", "label": "Dashboard", "permission": "crm.access"}
    ]

    if extra_permissions:
        permissions.extend(extra_permissions)

    if extra_routes:
        routes.extend(extra_routes)

    return {
        "schemaVersion": "2.0.0",
        "id": "crm",
        "name": "CRM",
        "version": version,
        "type": "microfrontend",
        "basePath": "/crm",
        "entry": "/apps/crm/remoteEntry.js",
        "permissions": permissions,
        "routes": routes,
    }


# ==========================================================
# TESTS
# ==========================================================

def test_register_plugin_success(app, db_session):

    user = create_test_user(db_session)

    manifest = make_manifest("1.0.0")

    uow = SqlAlchemyUnitOfWork(session=db_session)
    validator = ManifestValidator()
    use_case = RegisterPluginUseCase(uow, validator)

    result = use_case.execute(
        manifest=manifest,
        user_id=str(user.id),
        user_ip="127.0.0.1"
    )

    assert result.success is True

    assert db_session.query(App).count() == 1
    assert db_session.query(Permission).count() == 1
    assert db_session.query(AppRoute).count() == 1
    assert db_session.query(AppManifest).count() == 1
    assert db_session.query(AuditLog).count() == 1


def test_upgrade_minor_add_permission(app, db_session):

    user = create_test_user(db_session)

    manifest_v1 = make_manifest("1.0.0")

    manifest_v2 = make_manifest(
        "1.1.0",
        extra_permissions=[
            {"code": "crm.leads.read", "description": "Leads", "module": "crm"}
        ],
        extra_routes=[
            {"path": "/crm/leads", "label": "Leads", "permission": "crm.leads.read"}
        ]
    )

    uow = SqlAlchemyUnitOfWork(session=db_session)
    validator = ManifestValidator()
    use_case = RegisterPluginUseCase(uow, validator)

    use_case.execute(manifest_v1, str(user.id), "127.0.0.1")
    result = use_case.execute(manifest_v2, str(user.id), "127.0.0.1")

    assert result.success is True
    assert db_session.query(Permission).count() == 2


def test_upgrade_major_blocked(app, db_session):

    user = create_test_user(db_session)

    manifest_v1 = make_manifest("1.0.0")
    manifest_v2 = make_manifest("2.0.0")

    uow = SqlAlchemyUnitOfWork(session=db_session)
    validator = ManifestValidator()
    use_case = RegisterPluginUseCase(uow, validator)

    use_case.execute(manifest_v1, str(user.id), "127.0.0.1")
    result = use_case.execute(manifest_v2, str(user.id), "127.0.0.1")

    assert result.success is False


def test_route_collision_between_apps(app, db_session):

    user = create_test_user(db_session)

    manifest_a = make_manifest("1.0.0")

    manifest_b = {
        "schemaVersion": "2.0.0",
        "id": "erp",
        "name": "ERP",
        "version": "1.0.0",
        "type": "microfrontend",
        "basePath": "/crm",  # mesma base
        "entry": "/apps/erp/remoteEntry.js",
        "permissions": [
            {"code": "erp.access", "description": "Acesso", "module": "erp"}
        ],
        "routes": [
            {"path": "/crm", "label": "ERP Dashboard", "permission": "erp.access"}
        ],
    }

    uow = SqlAlchemyUnitOfWork(session=db_session)
    validator = ManifestValidator()
    use_case = RegisterPluginUseCase(uow, validator)

    result_a = use_case.execute(manifest_a, str(user.id), "127.0.0.1")
    result_b = use_case.execute(manifest_b, str(user.id), "127.0.0.1")

    assert result_a.success is True
    assert result_b.success is False

def test_permission_code_collision_between_apps(app, db_session):

    user = create_test_user(db_session)

    manifest_a = make_manifest("1.0.0")

    manifest_b = {
        "schemaVersion": "2.0.0",
        "id": "erp",
        "name": "ERP",
        "version": "1.0.0",
        "type": "microfrontend",
        "basePath": "/erp",
        "entry": "/apps/erp/remoteEntry.js",
        "permissions": [
            {"code": "crm.access", "description": "Colisão", "module": "erp"}
        ],
        "routes": [
            {"path": "/erp", "label": "ERP", "permission": "crm.access"}
        ],
    }

    uow = SqlAlchemyUnitOfWork(session=db_session)
    validator = ManifestValidator()
    use_case = RegisterPluginUseCase(uow, validator)

    result_a = use_case.execute(manifest_a, str(user.id), "127.0.0.1")
    result_b = use_case.execute(manifest_b, str(user.id), "127.0.0.1")

    assert result_a.success is True
    assert result_b.success is False


def test_register_plugin_should_rollback_on_failure(app, db_session):

    user = create_test_user(db_session)

    manifest_valid = make_manifest("1.0.0")

    manifest_invalid = {
        "schemaVersion": "2.0.0",
        "id": "crm2",
        "name": "CRM2",
        "version": "1.0.0",
        "type": "microfrontend",
        "basePath": "/crm",
        "entry": "/apps/crm2/remoteEntry.js",
        "permissions": [
            {"code": "crm2.access", "description": "Acesso", "module": "crm2"}
        ],
        "routes": [
            {"path": "/crm", "label": "Duplicado", "permission": "crm2.access"}
        ],
    }

    uow = SqlAlchemyUnitOfWork(session=db_session)
    validator = ManifestValidator()
    use_case = RegisterPluginUseCase(uow, validator)

    result_valid = use_case.execute(manifest_valid, str(user.id), "127.0.0.1")
    result_invalid = use_case.execute(manifest_invalid, str(user.id), "127.0.0.1")

    assert result_valid.success is True
    assert result_invalid.success is False

    # Garante que CRM2 NÃO foi persistido
    assert db_session.query(App).filter_by(id="crm2").count() == 0
    assert db_session.query(Permission).filter_by(module="crm2").count() == 0


from unittest.mock import patch

def test_rbac_cache_should_be_cleared(app, db_session):

    user = create_test_user(db_session)
    manifest = make_manifest("1.0.0")

    uow = SqlAlchemyUnitOfWork(session=db_session)
    validator = ManifestValidator()
    use_case = RegisterPluginUseCase(uow, validator)

    with patch("app.infrastructure.security.rbac_cache.rbac_cache.clear") as mock_clear:
        result = use_case.execute(manifest, str(user.id), "127.0.0.1")

        assert result.success is True
        mock_clear.assert_called_once()