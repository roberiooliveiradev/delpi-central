from __future__ import annotations

from commercial_app.application.services.customer_avatar_storage import CustomerAvatarStorage
from commercial_app.application.use_cases.manage_customer_avatar import ManageCustomerAvatarUseCase
from commercial_app.application.use_cases.manage_seller_portfolio import ManageSellerPortfolioUseCase
from commercial_app.config import settings
from commercial_app.domain.ports.customer_avatar_repository_port import CustomerAvatarRepositoryPort
from commercial_app.domain.ports.seller_portfolio_repository_port import SellerPortfolioRepositoryPort
from commercial_app.infrastructure.gateways.delpi_commercial_gateway import DelpiCommercialGateway
from commercial_app.infrastructure.persistence.repositories.legacy_postgres_customer_avatar_repository import (
    LegacyPostgresCustomerAvatarRepository,
)
from commercial_app.infrastructure.persistence.repositories.legacy_postgres_seller_portfolio_repository import (
    LegacyPostgresSellerPortfolioRepository,
)
from commercial_app.infrastructure.persistence.repositories.postgres_audit_log_repository import (
    PostgresAuditLogRepository,
)
from commercial_app.infrastructure.persistence.repositories.postgres_customer_avatar_repository import (
    PostgresCustomerAvatarRepository,
)
from commercial_app.infrastructure.persistence.repositories.postgres_seller_portfolio_repository import (
    PostgresSellerPortfolioRepository,
)

_portfolio_repository: SellerPortfolioRepositoryPort | None = None
_avatar_repository: CustomerAvatarRepositoryPort | None = None
_portfolio_use_case: ManageSellerPortfolioUseCase | None = None
_avatar_use_case: ManageCustomerAvatarUseCase | None = None
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


def build_manage_seller_portfolio_use_case() -> ManageSellerPortfolioUseCase:
    global _portfolio_use_case
    if _portfolio_use_case is None:
        _portfolio_use_case = ManageSellerPortfolioUseCase(
            repository=build_seller_portfolio_repository(),
            audit_repository=build_audit_log_repository(),
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
        )
    return _avatar_use_case


def build_delpi_commercial_gateway() -> DelpiCommercialGateway:
    global _commercial_gateway
    if _commercial_gateway is None:
        _commercial_gateway = DelpiCommercialGateway()
    return _commercial_gateway
