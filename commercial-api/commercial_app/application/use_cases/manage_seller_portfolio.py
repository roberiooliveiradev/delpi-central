from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from commercial_app.domain.entities.portfolio_coverage import (
    CustomerOverlapWarning,
    PortfolioCoverageAudit,
)
from commercial_app.domain.entities.portfolio_load import PortfolioLoadSummary
from commercial_app.domain.entities.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
    SellerPortfolioMember,
)
from commercial_app.domain.ports.customer_avatar_repository_port import AuditLogRepositoryPort
from commercial_app.domain.ports.portal_access_port import PortalAccessPort
from commercial_app.domain.ports.seller_portfolio_repository_port import (
    SellerPortfolioRepositoryPort,
)
from commercial_app.domain.services.seller_portfolio_coverage_audit_service import (
    SellerPortfolioCoverageAuditService,
)
from commercial_app.domain.services.seller_portfolio_load_summary_service import (
    SellerPortfolioLoadSummaryService,
)

_PORTAL_ACCESS_DENIED = "Usuário sem acesso ao Portal Comercial."


def _normalize_code(value: str) -> str:
    return str(value or "").strip()


def customer_key(code: str, store: str) -> tuple[str, str]:
    return (_normalize_code(code), _normalize_code(store))


def portfolio_to_dict(portfolio: SellerPortfolio) -> dict[str, Any]:
    members = [
        {"user_id": member.user_id, "role": member.role}
        for member in portfolio.members
    ]
    member_count = len(members)
    if member_count == 0 and portfolio.user_id:
        member_count = 1
    return {
        "id": portfolio.id,
        "user_id": portfolio.user_id,
        "owner_user_id": portfolio.owner_user_id,
        "display_name": portfolio.display_name,
        "active": portfolio.active,
        "customer_count": len(portfolio.customers),
        "member_count": member_count,
        "customers": [
            {
                "customer_code": item.customer_code,
                "customer_store": item.customer_store,
                "customer_name": item.customer_name,
            }
            for item in portfolio.customers
        ],
        "members": members,
    }


def load_summary_to_dict(summary: PortfolioLoadSummary) -> dict[str, Any]:
    return {
        "portfolios": [
            {
                "id": item.id,
                "display_name": item.display_name,
                "active": item.active,
                "customer_count": item.customer_count,
                "member_count": item.member_count,
                "open_value": item.open_value,
                "attention_count": item.attention_count,
            }
            for item in summary.portfolios
        ],
        "by_person": [
            {
                "user_id": item.user_id,
                "portfolio_ids": list(item.portfolio_ids),
                "portfolio_count": item.portfolio_count,
                "customer_count": item.customer_count,
                "open_value": item.open_value,
                "attention_count": item.attention_count,
            }
            for item in summary.by_person
        ],
        "totvs_metrics": {
            "available": summary.totvs_metrics.available,
            "reason": summary.totvs_metrics.reason,
        },
    }


def parse_customer_assignments(raw: Sequence[dict[str, Any]] | None) -> list[SellerCustomerAssignment]:
    if not raw:
        return []
    parsed: list[SellerCustomerAssignment] = []
    seen: set[tuple[str, str]] = set()
    for item in raw:
        code = _normalize_code(str(item.get("customer_code") or item.get("codigo") or ""))
        store = _normalize_code(str(item.get("customer_store") or item.get("loja") or ""))
        if not code or not store:
            raise ValueError("Cada cliente precisa de customer_code e customer_store.")
        key = (code, store)
        if key in seen:
            continue
        seen.add(key)
        name_raw = item.get("customer_name") or item.get("nome")
        name = str(name_raw).strip() if name_raw else None
        parsed.append(
            SellerCustomerAssignment(
                customer_code=code,
                customer_store=store,
                customer_name=name or None,
            )
        )
    return parsed


@dataclass(frozen=True, slots=True)
class CreatePortfolioRequest:
    user_id: str = ""
    display_name: str = ""
    created_by_user_id: str | None = None
    customers: tuple[SellerCustomerAssignment, ...] = ()
    user_ids: tuple[str, ...] = ()
    owner_user_id: str | None = None


@dataclass(frozen=True, slots=True)
class AddCustomerResult:
    portfolio: SellerPortfolio
    warning: CustomerOverlapWarning | None = None


def coverage_audit_to_dict(audit: PortfolioCoverageAudit) -> dict[str, Any]:
    return {
        "overlapping_count": audit.overlapping_count,
        "overlapping": [
            {
                "customer_code": item.customer_code,
                "customer_store": item.customer_store,
                "customer_name": item.customer_name,
                "portfolio_ids": list(item.portfolio_ids),
                "portfolios": [
                    {"id": ref.id, "display_name": ref.display_name}
                    for ref in item.portfolios
                ],
            }
            for item in audit.overlapping
        ],
        "portfolios_with_overlap": [
            {
                "id": item.id,
                "display_name": item.display_name,
                "overlapping_customer_count": item.overlapping_customer_count,
            }
            for item in audit.portfolios_with_overlap
        ],
        "gap": {
            "available": audit.gap.available,
            "reason": audit.gap.reason,
        },
    }


def customer_overlap_warning_to_dict(
    warning: CustomerOverlapWarning | None,
) -> dict[str, Any] | None:
    if warning is None:
        return None
    return {
        "code": warning.code,
        "message": warning.message,
        "other_portfolios": [
            {"id": item.id, "display_name": item.display_name}
            for item in warning.other_portfolios
        ],
    }


def add_customer_result_to_dict(result: AddCustomerResult) -> dict[str, Any]:
    payload = portfolio_to_dict(result.portfolio)
    warning = customer_overlap_warning_to_dict(result.warning)
    if warning is not None:
        payload["warnings"] = [warning]
        payload["coverage_warning"] = warning
    else:
        payload["warnings"] = []
        payload["coverage_warning"] = None
    return payload


class ManageSellerPortfolioUseCase:
    def __init__(
        self,
        repository: SellerPortfolioRepositoryPort,
        audit_repository: AuditLogRepositoryPort | None = None,
        portal_access: PortalAccessPort | None = None,
        coverage_audit: SellerPortfolioCoverageAuditService | None = None,
        load_summary: SellerPortfolioLoadSummaryService | None = None,
    ):
        self._repository = repository
        self._audit = audit_repository
        # None = permissivo (mesmo efeito de PermissivePortalAccessPort).
        self._portal_access = portal_access
        self._coverage_audit = coverage_audit or SellerPortfolioCoverageAuditService()
        self._load_summary = load_summary or SellerPortfolioLoadSummaryService()

    def _ensure_portal_access(self, user_ids: Sequence[str]) -> None:
        if self._portal_access is None:
            return
        for uid in user_ids:
            if not self._portal_access.has_commercial_portal_access(uid):
                raise ValueError(_PORTAL_ACCESS_DENIED)

    def _append_audit(
        self,
        *,
        actor_user_id: str | None,
        action: str,
        entity_id: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        if self._audit is None or not actor_user_id:
            return
        self._audit.append(
            actor_user_id=actor_user_id,
            action=action,
            entity_type="seller_portfolio",
            entity_id=entity_id,
            payload=payload or {},
        )

    def get_me_portfolios(self, user_id: str) -> list[SellerPortfolio]:
        # /me só lista carteiras ativas — desativadas ficam fora do escopo do vendedor.
        return self._repository.list_by_user_id(user_id, active_only=True)

    def get_me(self, user_id: str) -> SellerPortfolio | None:
        portfolios = self.get_me_portfolios(user_id)
        return portfolios[0] if portfolios else None

    def list_portfolios(self, *, active_only: bool = False) -> list[SellerPortfolio]:
        return self._repository.list_portfolios(active_only=active_only)

    def get_portfolio(self, portfolio_id: str) -> SellerPortfolio | None:
        return self._repository.get_by_id(portfolio_id)

    def audit_customer_coverage(self) -> PortfolioCoverageAudit:
        """Relatório de overlapping entre carteiras ativas (gap só se houver universo)."""
        portfolios = self._repository.list_portfolios(active_only=True)
        return self._coverage_audit.audit_active_portfolios(portfolios)

    def summarize_portfolio_load(self, *, active_only: bool = False) -> PortfolioLoadSummary:
        """KPIs de carga (clientes/membros; TOTVS stub até wiring)."""
        portfolios = self._repository.list_portfolios(active_only=active_only)
        return self._load_summary.summarize(portfolios)

    def create_portfolio(self, request: CreatePortfolioRequest) -> SellerPortfolio:
        display_name = _normalize_code(request.display_name)
        if not display_name:
            raise ValueError("display_name é obrigatório.")

        user_ids = [
            uid
            for uid in (_normalize_code(raw) for raw in request.user_ids)
            if uid
        ]
        if not user_ids:
            sole = _normalize_code(request.user_id)
            if not sole:
                raise ValueError("Informe ao menos um usuário (user_id ou user_ids).")
            user_ids = [sole]

        owner = _normalize_code(request.owner_user_id) if request.owner_user_id else user_ids[0]
        if not owner:
            raise ValueError("owner_user_id inválido.")

        all_new = list(dict.fromkeys([owner, *user_ids]))
        self._ensure_portal_access(all_new)

        extras = [uid for uid in user_ids if uid != owner]
        portfolio = self._repository.create_portfolio(
            user_id=owner,
            display_name=display_name,
            created_by_user_id=request.created_by_user_id,
            member_user_ids=extras,
        )
        if request.customers:
            updated = self._repository.replace_customers(
                portfolio_id=portfolio.id,
                customers=request.customers,
            )
            if updated is not None:
                return updated
        return portfolio

    def update_portfolio(
        self,
        *,
        portfolio_id: str,
        display_name: str | None = None,
        active: bool | None = None,
        actor_user_id: str | None = None,
    ) -> SellerPortfolio:
        if display_name is not None and not _normalize_code(display_name):
            raise ValueError("display_name não pode ser vazio.")
        previous = self._repository.get_by_id(portfolio_id) if active is not None else None
        updated = self._repository.update_portfolio(
            portfolio_id=portfolio_id,
            display_name=_normalize_code(display_name) if display_name is not None else None,
            active=active,
        )
        if updated is None:
            raise LookupError("Vendedor não encontrado.")
        # Auditoria quando active flipa (desativa ou reativa); /me já exclui inactive.
        if previous is not None and active is not None and previous.active != updated.active:
            action = (
                "seller_portfolio.deactivate"
                if not updated.active
                else "seller_portfolio.reactivate"
            )
            self._append_audit(
                actor_user_id=actor_user_id,
                action=action,
                entity_id=portfolio_id,
                payload={"active": updated.active},
            )
        return updated

    def deactivate_portfolio(
        self,
        portfolio_id: str,
        *,
        actor_user_id: str | None = None,
    ) -> SellerPortfolio:
        updated = self._repository.deactivate_portfolio(portfolio_id)
        if updated is None:
            raise LookupError("Vendedor não encontrado.")
        self._append_audit(
            actor_user_id=actor_user_id,
            action="seller_portfolio.deactivate",
            entity_id=portfolio_id,
            payload={"active": False},
        )
        return updated

    def purge_portfolio(
        self,
        portfolio_id: str,
        *,
        actor_user_id: str | None = None,
    ) -> SellerPortfolio:
        portfolio_id = _normalize_code(portfolio_id)
        if not portfolio_id:
            raise ValueError("portfolio_id é obrigatório.")
        current = self._repository.get_by_id(portfolio_id)
        if current is None:
            raise LookupError("Vendedor não encontrado.")
        deleted = self._repository.delete_portfolio(portfolio_id)
        if deleted is None:
            raise LookupError("Vendedor não encontrado.")
        self._append_audit(
            actor_user_id=actor_user_id,
            action="seller_portfolio.purge",
            entity_id=portfolio_id,
            payload={
                "user_id": current.user_id,
                "display_name": current.display_name,
                "customer_count": len(current.customers),
            },
        )
        return deleted

    def replace_customers(
        self,
        *,
        portfolio_id: str,
        customers: Sequence[SellerCustomerAssignment],
    ) -> SellerPortfolio:
        updated = self._repository.replace_customers(
            portfolio_id=portfolio_id,
            customers=customers,
        )
        if updated is None:
            raise LookupError("Vendedor não encontrado.")
        return updated

    def add_customer(
        self,
        *,
        portfolio_id: str,
        customer: SellerCustomerAssignment,
    ) -> AddCustomerResult:
        if not customer.customer_code or not customer.customer_store:
            raise ValueError("customer_code e customer_store são obrigatórios.")
        portfolio_id = _normalize_code(portfolio_id)
        active_portfolios = self._repository.list_portfolios(active_only=True)
        other = self._coverage_audit.find_other_active_portfolios_for_customer(
            active_portfolios,
            customer_code=customer.customer_code,
            customer_store=customer.customer_store,
            exclude_portfolio_id=portfolio_id,
        )
        warning = self._coverage_audit.build_link_overlap_warning(other)
        updated = self._repository.add_customer(portfolio_id=portfolio_id, customer=customer)
        if updated is None:
            raise LookupError("Vendedor não encontrado.")
        return AddCustomerResult(portfolio=updated, warning=warning)

    def remove_customer(
        self,
        *,
        portfolio_id: str,
        customer_code: str,
        customer_store: str,
    ) -> SellerPortfolio:
        code, store = customer_key(customer_code, customer_store)
        if not code or not store:
            raise ValueError("customer_code e customer_store são obrigatórios.")
        updated = self._repository.remove_customer(
            portfolio_id=portfolio_id,
            customer_code=code,
            customer_store=store,
        )
        if updated is None:
            raise LookupError("Vendedor não encontrado.")
        return updated

    def replace_members(
        self,
        *,
        portfolio_id: str,
        members: Sequence[SellerPortfolioMember],
        actor_user_id: str | None = None,
    ) -> SellerPortfolio:
        normalized: list[SellerPortfolioMember] = []
        seen: set[str] = set()
        for member in members:
            uid = _normalize_code(member.user_id)
            if not uid or uid in seen:
                continue
            seen.add(uid)
            role = "owner" if member.role == "owner" else "member"
            normalized.append(SellerPortfolioMember(user_id=uid, role=role))
        if not normalized:
            raise ValueError("A carteira deve ter ao menos um membro.")
        owners = [item for item in normalized if item.role == "owner"]
        if len(owners) != 1:
            raise ValueError("A carteira deve ter exatamente um owner.")

        current = self._repository.get_by_id(portfolio_id)
        if current is None:
            raise LookupError("Vendedor não encontrado.")
        existing_ids = {member.user_id for member in current.members}
        if not existing_ids and current.user_id:
            existing_ids = {current.user_id}
        new_ids = [item.user_id for item in normalized if item.user_id not in existing_ids]
        self._ensure_portal_access(new_ids)

        updated = self._repository.replace_members(
            portfolio_id=portfolio_id,
            members=normalized,
        )
        if updated is None:
            raise LookupError("Vendedor não encontrado.")
        self._append_audit(
            actor_user_id=actor_user_id,
            action="seller_portfolio.replace_members",
            entity_id=portfolio_id,
            payload={
                "members": [
                    {"user_id": item.user_id, "role": item.role} for item in normalized
                ]
            },
        )
        return updated

    def add_member(
        self,
        *,
        portfolio_id: str,
        user_id: str,
        role: str = "member",
        actor_user_id: str | None = None,
    ) -> SellerPortfolio:
        uid = _normalize_code(user_id)
        if not uid:
            raise ValueError("user_id é obrigatório.")
        next_role = "owner" if role == "owner" else "member"
        self._ensure_portal_access([uid])
        updated = self._repository.add_member(
            portfolio_id=portfolio_id,
            user_id=uid,
            role=next_role,
        )
        if updated is None:
            raise LookupError("Vendedor não encontrado.")
        self._append_audit(
            actor_user_id=actor_user_id,
            action="seller_portfolio.add_member",
            entity_id=portfolio_id,
            payload={"user_id": uid, "role": next_role},
        )
        return updated

    def remove_member(
        self,
        *,
        portfolio_id: str,
        user_id: str,
        actor_user_id: str | None = None,
    ) -> SellerPortfolio:
        uid = _normalize_code(user_id)
        if not uid:
            raise ValueError("user_id é obrigatório.")
        current = self._repository.get_by_id(portfolio_id)
        if current is None:
            raise LookupError("Vendedor não encontrado.")
        members = list(current.members)
        if not members and current.user_id:
            members = [SellerPortfolioMember(user_id=current.user_id, role="owner")]
        if len(members) <= 1:
            raise ValueError("Não é possível remover o último membro da carteira.")
        target = next((item for item in members if item.user_id == uid), None)
        if target is None:
            raise LookupError("Membro não encontrado na carteira.")
        if target.role == "owner":
            raise ValueError("Não é possível remover o único owner da carteira.")
        updated = self._repository.remove_member(
            portfolio_id=portfolio_id,
            user_id=uid,
        )
        if updated is None:
            raise LookupError("Vendedor não encontrado.")
        self._append_audit(
            actor_user_id=actor_user_id,
            action="seller_portfolio.remove_member",
            entity_id=portfolio_id,
            payload={"user_id": uid},
        )
        return updated

    def set_owner(
        self,
        *,
        portfolio_id: str,
        user_id: str,
        actor_user_id: str | None = None,
    ) -> SellerPortfolio:
        uid = _normalize_code(user_id)
        if not uid:
            raise ValueError("user_id é obrigatório.")
        current = self._repository.get_by_id(portfolio_id)
        if current is None:
            raise LookupError("Vendedor não encontrado.")
        existing_ids = {member.user_id for member in current.members}
        if not existing_ids and current.user_id:
            existing_ids = {current.user_id}
        # Se o usuário ainda não for membro, o repositório o inclui como owner.
        if uid not in existing_ids:
            self._ensure_portal_access([uid])
        updated = self._repository.set_owner(
            portfolio_id=portfolio_id,
            user_id=uid,
        )
        if updated is None:
            raise LookupError("Vendedor não encontrado.")
        self._append_audit(
            actor_user_id=actor_user_id,
            action="seller_portfolio.set_owner",
            entity_id=portfolio_id,
            payload={"user_id": uid},
        )
        return updated

    def transfer_customers(
        self,
        *,
        source_portfolio_id: str,
        target_portfolio_id: str,
        customers: Sequence[SellerCustomerAssignment],
        actor_user_id: str | None = None,
        reason_note: str | None = None,
    ) -> tuple[SellerPortfolio, SellerPortfolio]:
        source_id = _normalize_code(source_portfolio_id)
        target_id = _normalize_code(target_portfolio_id)
        if not source_id or not target_id:
            raise ValueError("Origem e destino da transferência são obrigatórios.")
        if source_id == target_id:
            raise ValueError("Origem e destino devem ser vendedores diferentes.")
        if not customers:
            raise ValueError("Selecione ao menos um cliente para transferir.")
        if not (reason_note or "").strip():
            raise ValueError("reason_note é obrigatório para transferência de clientes.")

        source = self._repository.get_by_id(source_id)
        if source is None:
            raise LookupError("Vendedor de origem não encontrado.")
        target = self._repository.get_by_id(target_id)
        if target is None:
            raise LookupError("Vendedor de destino não encontrado.")
        if not target.active:
            raise ValueError("Não é possível transferir para um vendedor inativo.")

        owned = {
            (item.customer_code, item.customer_store): item for item in source.customers
        }
        to_move: list[SellerCustomerAssignment] = []
        seen: set[tuple[str, str]] = set()
        for item in customers:
            key = customer_key(item.customer_code, item.customer_store)
            if not key[0] or not key[1]:
                raise ValueError("Cada cliente precisa de customer_code e customer_store.")
            if key in seen:
                continue
            seen.add(key)
            owned_item = owned.get(key)
            if owned_item is None:
                raise ValueError(
                    f"Cliente {key[0]}/{key[1]} não pertence à carteira de origem."
                )
            to_move.append(
                SellerCustomerAssignment(
                    customer_code=owned_item.customer_code,
                    customer_store=owned_item.customer_store,
                    customer_name=item.customer_name or owned_item.customer_name,
                )
            )

        result = self._repository.transfer_customers(
            source_portfolio_id=source_id,
            target_portfolio_id=target_id,
            customers=to_move,
        )
        if result is None:
            raise LookupError("Vendedor de origem ou destino não encontrado.")

        self._append_audit(
            actor_user_id=actor_user_id,
            action="seller_portfolio.transfer_customers",
            entity_id=source_id,
            payload={
                "source_portfolio_id": source_id,
                "target_portfolio_id": target_id,
                "transferred_count": len(to_move),
                "customers": [
                    {
                        "customer_code": item.customer_code,
                        "customer_store": item.customer_store,
                    }
                    for item in to_move
                ],
                "reason_note": reason_note.strip(),
            },
        )

        return result
