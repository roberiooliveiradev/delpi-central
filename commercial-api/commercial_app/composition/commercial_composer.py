from __future__ import annotations

from commercial_app.application.services.attachment_storage import AttachmentStorage
from commercial_app.application.services.customer_avatar_storage import CustomerAvatarStorage
from commercial_app.application.services.user_profile_storage import UserProfileStorage
from commercial_app.application.use_cases.manage_account_contacts import (
    ManageAccountContactsUseCase,
)
from commercial_app.application.use_cases.manage_attachments import ManageAttachmentsUseCase
from commercial_app.application.use_cases.manage_customer_avatar import ManageCustomerAvatarUseCase
from commercial_app.application.use_cases.manage_seller_portfolio import ManageSellerPortfolioUseCase
from commercial_app.application.use_cases.manage_user_profile import ManageUserProfileUseCase
from commercial_app.application.use_cases.manage_worklist import ManageWorklistUseCase
from commercial_app.config import settings
from commercial_app.domain.ports.attachment_repository_port import AttachmentRepositoryPort
from commercial_app.domain.ports.account_contact_repository_port import (
    AccountContactRepositoryPort,
)
from commercial_app.domain.ports.customer_avatar_repository_port import CustomerAvatarRepositoryPort
from commercial_app.domain.ports.seller_portfolio_repository_port import SellerPortfolioRepositoryPort
from commercial_app.domain.ports.task_repository_port import (
    ActivityRepositoryPort,
    TaskRepositoryPort,
)
from commercial_app.domain.ports.user_profile_repository_port import UserProfileRepositoryPort
from commercial_app.infrastructure.gateways.core_api_portal_access import (
    CoreApiPortalAccessPort,
)
from commercial_app.infrastructure.gateways.delpi_commercial_gateway import DelpiCommercialGateway
from commercial_app.infrastructure.gateways.delpi_open_orders_metrics_adapter import (
    DelpiOpenOrdersMetricsAdapter,
)
from commercial_app.infrastructure.persistence.repositories.legacy_postgres_customer_avatar_repository import (
    LegacyPostgresCustomerAvatarRepository,
)
from commercial_app.infrastructure.persistence.repositories.legacy_postgres_seller_portfolio_repository import (
    LegacyPostgresSellerPortfolioRepository,
)
from commercial_app.infrastructure.persistence.repositories.postgres_attachment_repository import (
    PostgresAttachmentRepository,
)
from commercial_app.infrastructure.persistence.repositories.postgres_account_contact_repository import (
    PostgresAccountContactRepository,
)
from commercial_app.infrastructure.persistence.repositories.postgres_audit_log_repository import (
    PostgresAuditLogRepository,
)
from commercial_app.infrastructure.security.permissive_portal_access import (
    PermissivePortalAccessPort,
)
from commercial_app.domain.ports.portal_access_port import PortalAccessPort
from commercial_app.infrastructure.persistence.repositories.postgres_customer_avatar_repository import (
    PostgresCustomerAvatarRepository,
)
from commercial_app.infrastructure.persistence.repositories.postgres_seller_portfolio_repository import (
    PostgresSellerPortfolioRepository,
)
from commercial_app.infrastructure.persistence.repositories.postgres_task_repository import (
    PostgresActivityRepository,
    PostgresTaskRepository,
)
from commercial_app.infrastructure.persistence.repositories.postgres_user_profile_repository import (
    PostgresUserProfileRepository,
)

_portfolio_repository: SellerPortfolioRepositoryPort | None = None
_avatar_repository: CustomerAvatarRepositoryPort | None = None
_attachment_repository: AttachmentRepositoryPort | None = None
_task_repository: TaskRepositoryPort | None = None
_activity_repository: ActivityRepositoryPort | None = None
_account_contact_repository: AccountContactRepositoryPort | None = None
_user_profile_repository: UserProfileRepositoryPort | None = None
_portfolio_use_case: ManageSellerPortfolioUseCase | None = None
_avatar_use_case: ManageCustomerAvatarUseCase | None = None
_attachment_use_case: ManageAttachmentsUseCase | None = None
_worklist_use_case: ManageWorklistUseCase | None = None
_account_contacts_use_case: ManageAccountContactsUseCase | None = None
_user_profile_use_case: ManageUserProfileUseCase | None = None
_commercial_gateway: DelpiCommercialGateway | None = None


def _portfolio_source() -> str:
    return (settings.COMMERCIAL_PORTFOLIO_SOURCE or "legacy").lower()


def build_seller_portfolio_repository() -> SellerPortfolioRepositoryPort:
    global _portfolio_repository
    if _portfolio_repository is None:
        if _portfolio_source() == "commercial":
            _portfolio_repository = PostgresSellerPortfolioRepository()
        else:
            _portfolio_repository = LegacyPostgresSellerPortfolioRepository()
    return _portfolio_repository


def build_audit_log_repository() -> PostgresAuditLogRepository:
    return PostgresAuditLogRepository()


def build_portal_access_port() -> PortalAccessPort:
    port = CoreApiPortalAccessPort()
    if port.configured():
        return port
    return PermissivePortalAccessPort()


def build_manage_seller_portfolio_use_case() -> ManageSellerPortfolioUseCase:
    global _portfolio_use_case
    if _portfolio_use_case is None:
        _portfolio_use_case = ManageSellerPortfolioUseCase(
            repository=build_seller_portfolio_repository(),
            audit_repository=build_audit_log_repository(),
            portal_access=build_portal_access_port(),
            open_orders_metrics=DelpiOpenOrdersMetricsAdapter(
                gateway=build_delpi_commercial_gateway(),
            ),
        )
    return _portfolio_use_case


def build_customer_avatar_repository() -> CustomerAvatarRepositoryPort:
    global _avatar_repository
    if _avatar_repository is None:
        if _portfolio_source() == "commercial":
            _avatar_repository = PostgresCustomerAvatarRepository()
        else:
            _avatar_repository = LegacyPostgresCustomerAvatarRepository()
    return _avatar_repository


def build_avatar_storage() -> CustomerAvatarStorage:
    if _portfolio_source() == "commercial":
        return CustomerAvatarStorage()
    legacy_dir = settings.PEDIDOS_VENDA_ABERTOS_AVATAR_UPLOAD_DIR
    return CustomerAvatarStorage(base_dir=legacy_dir or settings.COMMERCIAL_AVATAR_UPLOAD_DIR)


def build_manage_customer_avatar_use_case() -> ManageCustomerAvatarUseCase:
    global _avatar_use_case
    if _avatar_use_case is None:
        _avatar_use_case = ManageCustomerAvatarUseCase(
            repository=build_customer_avatar_repository(),
            storage=build_avatar_storage(),
            audit_repository=build_audit_log_repository(),
        )
    return _avatar_use_case


def build_resolve_commercial_customer_scope_service():
    from commercial_app.application.services.resolve_commercial_customer_scope_service import (
        ResolveCommercialCustomerScopeService,
    )

    return ResolveCommercialCustomerScopeService(build_seller_portfolio_repository())


def build_delpi_commercial_gateway() -> DelpiCommercialGateway:
    global _commercial_gateway
    if _commercial_gateway is None:
        _commercial_gateway = DelpiCommercialGateway()
    return _commercial_gateway


def build_task_repository() -> TaskRepositoryPort:
    global _task_repository
    if _task_repository is None:
        _task_repository = PostgresTaskRepository()
    return _task_repository


def build_activity_repository() -> ActivityRepositoryPort:
    global _activity_repository
    if _activity_repository is None:
        _activity_repository = PostgresActivityRepository()
    return _activity_repository


def build_manage_worklist_use_case() -> ManageWorklistUseCase:
    global _worklist_use_case
    if _worklist_use_case is None:
        _worklist_use_case = ManageWorklistUseCase(
            task_repository=build_task_repository(),
            activity_repository=build_activity_repository(),
            audit_repository=build_audit_log_repository(),
            portfolio_repository=build_seller_portfolio_repository(),
            attachment_repository=build_attachment_repository(),
        )
    return _worklist_use_case


def build_account_contact_repository() -> AccountContactRepositoryPort:
    global _account_contact_repository
    if _account_contact_repository is None:
        _account_contact_repository = PostgresAccountContactRepository()
    return _account_contact_repository


def build_manage_account_contacts_use_case() -> ManageAccountContactsUseCase:
    global _account_contacts_use_case
    if _account_contacts_use_case is None:
        _account_contacts_use_case = ManageAccountContactsUseCase(
            repository=build_account_contact_repository(),
            audit_repository=build_audit_log_repository(),
        )
    return _account_contacts_use_case


def build_attachment_repository() -> AttachmentRepositoryPort:
    global _attachment_repository
    if _attachment_repository is None:
        _attachment_repository = PostgresAttachmentRepository()
    return _attachment_repository


def build_attachment_storage() -> AttachmentStorage:
    return AttachmentStorage()


def build_manage_attachments_use_case() -> ManageAttachmentsUseCase:
    global _attachment_use_case
    if _attachment_use_case is None:
        _attachment_use_case = ManageAttachmentsUseCase(
            repository=build_attachment_repository(),
            storage=build_attachment_storage(),
            task_repository=build_task_repository(),
            portfolio_repository=build_seller_portfolio_repository(),
        )
    return _attachment_use_case


def build_user_profile_repository() -> UserProfileRepositoryPort:
    global _user_profile_repository
    if _user_profile_repository is None:
        _user_profile_repository = PostgresUserProfileRepository()
    return _user_profile_repository


def build_user_profile_storage() -> UserProfileStorage:
    return UserProfileStorage()


def build_manage_user_profile_use_case() -> ManageUserProfileUseCase:
    global _user_profile_use_case
    if _user_profile_use_case is None:
        directory = CoreApiPortalAccessPort()
        _user_profile_use_case = ManageUserProfileUseCase(
            repository=build_user_profile_repository(),
            storage=build_user_profile_storage(),
            portfolio_repository=build_seller_portfolio_repository(),
            portal_access=directory,
            directory_gateway=directory,
        )
    return _user_profile_use_case
