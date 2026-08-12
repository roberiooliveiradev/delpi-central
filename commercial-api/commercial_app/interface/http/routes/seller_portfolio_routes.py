from __future__ import annotations

import logging

from fastapi import APIRouter, Body, Path, Query, Request

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_AUDIT_PERMISSIONS,
    COMMERCIAL_LIST_PORTFOLIOS_PERMISSIONS,
    COMMERCIAL_MANAGE_PERMISSIONS,
    COMMERCIAL_READ_PERMISSIONS,
    can_export_proposals,
    can_manage_followups,
    can_manage_portfolios,
    can_use_team_scope,
    can_view_accounts_team,
    can_view_analytics,
    can_view_proposals,
    can_view_worklist,
    can_view_worklist_team,
)
from commercial_app.application.use_cases.manage_seller_portfolio import (
    CreatePortfolioRequest,
    ManageSellerPortfolioUseCase,
    add_customer_result_to_dict,
    coverage_audit_to_dict,
    customer_shared_coverage_to_dict,
    load_summary_to_dict,
    parse_customer_assignments,
    portfolio_to_dict,
)
from commercial_app.composition.commercial_composer import build_manage_seller_portfolio_use_case
from commercial_app.core.auth_actor import actor_sub_from_request, current_user_from_request
from commercial_app.core.responses import fail, ok
from commercial_app.domain.entities.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
    SellerPortfolioMember,
)
from commercial_app.interface.http.schemas.portfolio_schemas import (
    AddCustomerBody,
    AddMemberBody,
    CreatePortfolioBody,
    CustomerCoverageLookupBody,
    ReplaceCustomersBody,
    ReplaceMembersBody,
    SetOwnerBody,
    TransferCustomersBody,
    UpdatePortfolioBody,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/seller-portfolios", tags=["Seller portfolios"])


def _use_case() -> ManageSellerPortfolioUseCase:
    return build_manage_seller_portfolio_use_case()


def _current_user_id(request: Request) -> str | None:
    return actor_sub_from_request(request)


def _can_access_portfolio(request: Request, portfolio: SellerPortfolio | str) -> bool:
    user = current_user_from_request(request)
    if can_manage_portfolios(user):
        return True
    current_id = _current_user_id(request)
    if not current_id:
        return False
    if isinstance(portfolio, SellerPortfolio):
        member_ids = {member.user_id for member in portfolio.members}
        if current_id in member_ids:
            return True
        return current_id in {portfolio.owner_user_id, portfolio.user_id}
    return current_id == portfolio


@router.get("/me", operation_id="get_my_seller_portfolio")
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS)
def get_my_seller_portfolio(request: Request):
    try:
        user_id = _current_user_id(request)
        if not user_id:
            return fail("Usuário não identificado.", 401, operation_id="get_my_seller_portfolio")
        portfolios = _use_case().get_me_portfolios(user_id)
        first = portfolios[0] if portfolios else None
        user = current_user_from_request(request)
        return ok(
            {
                "user_id": user_id,
                "portfolio": portfolio_to_dict(first) if first else None,
                "portfolios": [portfolio_to_dict(item) for item in portfolios],
                # is_admin = somente manage (CRUD). Filtro equipe = team_scope no MFE.
                "is_admin": can_manage_portfolios(user),
                "capabilities": {
                    "worklist_view": can_view_worklist(user),
                    "followups_manage": can_manage_followups(user),
                    "seller_portfolios_manage": can_manage_portfolios(user),
                    "analytics_view": can_view_analytics(user),
                    "proposals_view": can_view_proposals(user),
                    "proposals_export": can_export_proposals(user),
                    "accounts_team_view": can_view_accounts_team(user),
                    "worklist_team_view": can_view_worklist_team(user),
                    "team_scope": can_use_team_scope(user),
                },
            },
            message="Carteira do usuário carregada.",
            operation_id="get_my_seller_portfolio",
        )
    except Exception:
        logger.exception("get_my_seller_portfolio_failed")
        return fail(
            "Erro interno ao carregar carteira.",
            500,
            operation_id="get_my_seller_portfolio",
        )


@router.get("/coverage-audit", operation_id="get_seller_portfolios_coverage_audit")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def get_seller_portfolios_coverage_audit(_request: Request):
    """Auditoria de cobertura: clientes em 2+ carteiras ativas (overlapping)."""
    try:
        audit = _use_case().audit_customer_coverage()
        return ok(
            coverage_audit_to_dict(audit),
            message="Auditoria de cobertura carregada.",
            operation_id="get_seller_portfolios_coverage_audit",
        )
    except Exception:
        logger.exception("get_seller_portfolios_coverage_audit_failed")
        return fail(
            "Erro interno ao auditar cobertura de carteiras.",
            500,
            operation_id="get_seller_portfolios_coverage_audit",
        )


@router.post(
    "/customer-coverage",
    operation_id="lookup_seller_portfolios_customer_coverage",
)
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS)
def lookup_seller_portfolios_customer_coverage(
    request: Request,
    body: CustomerCoverageLookupBody = Body(...),
):
    """Batch: quais clientes do lote estão em 2+ carteiras do escopo (E6.4)."""
    try:
        user = current_user_from_request(request)
        team_scope = can_use_team_scope(user) or can_manage_portfolios(user)
        keys = [
            (item.customer_code, item.customer_store)
            for item in body.customers
        ]
        items = _use_case().lookup_customer_shared_coverage(
            customers=keys,
            portfolio_ids=body.portfolio_ids,
            actor_user_id=_current_user_id(request),
            team_scope=team_scope,
        )
        return ok(
            customer_shared_coverage_to_dict(items),
            message="Cobertura compartilhada dos clientes carregada.",
            operation_id="lookup_seller_portfolios_customer_coverage",
        )
    except Exception:
        logger.exception("lookup_seller_portfolios_customer_coverage_failed")
        return fail(
            "Erro interno ao consultar cobertura compartilhada.",
            500,
            operation_id="lookup_seller_portfolios_customer_coverage",
        )


@router.get("/load-summary", operation_id="get_seller_portfolios_load_summary")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def get_seller_portfolios_load_summary(
    _request: Request,
    active_only: bool = Query(False, description="Se true, resume apenas ativas."),
):
    """KPIs de carga por carteira/pessoa (clientes, membros; TOTVS stub)."""
    try:
        summary = _use_case().summarize_portfolio_load(active_only=active_only)
        return ok(
            load_summary_to_dict(summary),
            message="Resumo de carga das carteiras carregado.",
            operation_id="get_seller_portfolios_load_summary",
        )
    except Exception:
        logger.exception("get_seller_portfolios_load_summary_failed")
        return fail(
            "Erro interno ao resumir carga das carteiras.",
            500,
            operation_id="get_seller_portfolios_load_summary",
        )


@router.get("", operation_id="list_seller_portfolios")
@require_any_permission(*COMMERCIAL_LIST_PORTFOLIOS_PERMISSIONS)
def list_seller_portfolios(
    request: Request,
    active_only: bool = Query(False, description="Se true, lista apenas ativos."),
):
    """Lista carteiras para admin (CRUD) ou team.view (filtro / Gestão Equipe)."""
    try:
        user = current_user_from_request(request)
        # Só team (sem manage): força ativos — universo G4.
        force_active = active_only or (
            can_use_team_scope(user) and not can_manage_portfolios(user)
        )
        portfolios = _use_case().list_portfolios(active_only=force_active)
        return ok(
            {"items": [portfolio_to_dict(item) for item in portfolios]},
            message="Carteiras carregadas com sucesso.",
            operation_id="list_seller_portfolios",
        )
    except Exception:
        logger.exception("list_seller_portfolios_failed")
        return fail(
            "Erro interno ao listar carteiras.",
            500,
            operation_id="list_seller_portfolios",
        )


@router.post("", operation_id="create_seller_portfolio")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def create_seller_portfolio(request: Request, body: CreatePortfolioBody = Body(...)):
    try:
        customers = parse_customer_assignments(
            [item.model_dump() for item in body.customers]
        )
        portfolio = _use_case().create_portfolio(
            CreatePortfolioRequest(
                user_id=body.user_id or "",
                display_name=body.display_name,
                created_by_user_id=_current_user_id(request),
                customers=tuple(customers),
                user_ids=tuple(body.user_ids or ()),
                owner_user_id=body.owner_user_id,
            )
        )
        return ok(
            portfolio_to_dict(portfolio),
            message="Carteira cadastrada com sucesso.",
            status_code=201,
            operation_id="create_seller_portfolio",
        )
    except ValueError as exc:
        return fail(str(exc), 400, operation_id="create_seller_portfolio")
    except Exception:
        logger.exception("create_seller_portfolio_failed")
        return fail(
            "Erro interno ao cadastrar carteira.",
            500,
            operation_id="create_seller_portfolio",
        )


@router.get("/{portfolio_id}", operation_id="get_seller_portfolio")
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS)
def get_seller_portfolio(
    request: Request,
    portfolio_id: str = Path(..., min_length=1),
):
    try:
        portfolio = _use_case().get_portfolio(portfolio_id)
        if portfolio is None:
            return fail("Carteira não encontrada.", 404, operation_id="get_seller_portfolio")
        if not _can_access_portfolio(request, portfolio):
            return fail("Sem permissão para esta carteira.", 403, operation_id="get_seller_portfolio")
        return ok(
            portfolio_to_dict(portfolio),
            message="Carteira carregada com sucesso.",
            operation_id="get_seller_portfolio",
        )
    except Exception:
        logger.exception("get_seller_portfolio_failed")
        return fail(
            "Erro interno ao carregar carteira.",
            500,
            operation_id="get_seller_portfolio",
        )


@router.get("/{portfolio_id}/audit", operation_id="list_seller_portfolio_audit")
@require_any_permission(*COMMERCIAL_AUDIT_PERMISSIONS)
def list_seller_portfolio_audit(
    request: Request,
    portfolio_id: str = Path(..., min_length=1),
    page: int = Query(1, ge=1, description="Página (1-based)."),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página."),
):
    """Timeline de audit_log da carteira (membros, owner, transfer, ativo)."""
    try:
        portfolio = _use_case().get_portfolio(portfolio_id)
        if portfolio is None:
            return fail(
                "Carteira não encontrada.",
                404,
                operation_id="list_seller_portfolio_audit",
            )
        if not _can_access_portfolio(request, portfolio):
            return fail(
                "Sem permissão para esta carteira.",
                403,
                operation_id="list_seller_portfolio_audit",
            )
        payload = _use_case().list_portfolio_audit(
            portfolio_id,
            page=page,
            page_size=page_size,
        )
        return ok(
            payload,
            message="Auditoria da carteira carregada.",
            operation_id="list_seller_portfolio_audit",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="list_seller_portfolio_audit")
    except ValueError as exc:
        return fail(str(exc), 400, operation_id="list_seller_portfolio_audit")
    except Exception:
        logger.exception("list_seller_portfolio_audit_failed")
        return fail(
            "Erro interno ao listar auditoria da carteira.",
            500,
            operation_id="list_seller_portfolio_audit",
        )


@router.patch("/{portfolio_id}", operation_id="update_seller_portfolio")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def update_seller_portfolio(
    request: Request,
    portfolio_id: str = Path(..., min_length=1),
    body: UpdatePortfolioBody = Body(...),
):
    try:
        portfolio = _use_case().update_portfolio(
            portfolio_id=portfolio_id,
            display_name=body.display_name,
            active=body.active,
            actor_user_id=_current_user_id(request),
        )
        return ok(
            portfolio_to_dict(portfolio),
            message="Carteira atualizada com sucesso.",
            operation_id="update_seller_portfolio",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="update_seller_portfolio")
    except ValueError as exc:
        return fail(str(exc), 400, operation_id="update_seller_portfolio")
    except Exception:
        logger.exception("update_seller_portfolio_failed")
        return fail(
            "Erro interno ao atualizar carteira.",
            500,
            operation_id="update_seller_portfolio",
        )


@router.delete("/{portfolio_id}", operation_id="deactivate_seller_portfolio")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def deactivate_seller_portfolio(
    request: Request,
    portfolio_id: str = Path(..., min_length=1),
):
    try:
        portfolio = _use_case().deactivate_portfolio(
            portfolio_id,
            actor_user_id=_current_user_id(request),
        )
        return ok(
            portfolio_to_dict(portfolio),
            message="Carteira desativada com sucesso.",
            operation_id="deactivate_seller_portfolio",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="deactivate_seller_portfolio")
    except Exception:
        logger.exception("deactivate_seller_portfolio_failed")
        return fail(
            "Erro interno ao desativar carteira.",
            500,
            operation_id="deactivate_seller_portfolio",
        )


@router.delete("/{portfolio_id}/permanent", operation_id="purge_seller_portfolio")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def purge_seller_portfolio(
    request: Request,
    portfolio_id: str = Path(..., min_length=1),
):
    try:
        portfolio = _use_case().purge_portfolio(
            portfolio_id,
            actor_user_id=_current_user_id(request),
        )
        return ok(
            portfolio_to_dict(portfolio),
            message="Carteira excluída em definitivo.",
            operation_id="purge_seller_portfolio",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="purge_seller_portfolio")
    except ValueError as exc:
        return fail(str(exc), 400, operation_id="purge_seller_portfolio")
    except Exception:
        logger.exception("purge_seller_portfolio_failed")
        return fail(
            "Erro interno ao excluir carteira.",
            500,
            operation_id="purge_seller_portfolio",
        )


@router.put("/{portfolio_id}/customers", operation_id="replace_seller_customers")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def replace_seller_customers(
    _request: Request,
    portfolio_id: str = Path(..., min_length=1),
    body: ReplaceCustomersBody = Body(...),
):
    try:
        customers = parse_customer_assignments(
            [item.model_dump() for item in body.customers]
        )
        portfolio = _use_case().replace_customers(
            portfolio_id=portfolio_id,
            customers=customers,
        )
        return ok(
            portfolio_to_dict(portfolio),
            message="Carteira de clientes atualizada.",
            operation_id="replace_seller_customers",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="replace_seller_customers")
    except ValueError as exc:
        return fail(str(exc), 400, operation_id="replace_seller_customers")
    except Exception:
        logger.exception("replace_seller_customers_failed")
        return fail(
            "Erro interno ao atualizar clientes.",
            500,
            operation_id="replace_seller_customers",
        )


@router.post("/{portfolio_id}/customers", operation_id="add_seller_customer")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def add_seller_customer(
    _request: Request,
    portfolio_id: str = Path(..., min_length=1),
    body: AddCustomerBody = Body(...),
):
    try:
        result = _use_case().add_customer(
            portfolio_id=portfolio_id,
            customer=SellerCustomerAssignment(
                customer_code=body.customer_code.strip(),
                customer_store=body.customer_store.strip(),
                customer_name=(body.customer_name or "").strip() or None,
            ),
        )
        message = (
            "Cliente adicionado à carteira (já estava em outra carteira ativa)."
            if result.warning is not None
            else "Cliente adicionado à carteira."
        )
        return ok(
            add_customer_result_to_dict(result),
            message=message,
            operation_id="add_seller_customer",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="add_seller_customer")
    except ValueError as exc:
        return fail(str(exc), 400, operation_id="add_seller_customer")
    except Exception:
        logger.exception("add_seller_customer_failed")
        return fail(
            "Erro interno ao adicionar cliente.",
            500,
            operation_id="add_seller_customer",
        )


@router.delete(
    "/{portfolio_id}/customers/{customer_code}/{customer_store}",
    operation_id="remove_seller_customer",
)
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def remove_seller_customer(
    _request: Request,
    portfolio_id: str = Path(..., min_length=1),
    customer_code: str = Path(..., min_length=1),
    customer_store: str = Path(..., min_length=1),
):
    try:
        portfolio = _use_case().remove_customer(
            portfolio_id=portfolio_id,
            customer_code=customer_code,
            customer_store=customer_store,
        )
        return ok(
            portfolio_to_dict(portfolio),
            message="Cliente removido da carteira.",
            operation_id="remove_seller_customer",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="remove_seller_customer")
    except ValueError as exc:
        return fail(str(exc), 400, operation_id="remove_seller_customer")
    except Exception:
        logger.exception("remove_seller_customer_failed")
        return fail(
            "Erro interno ao remover cliente.",
            500,
            operation_id="remove_seller_customer",
        )


@router.put("/{portfolio_id}/members", operation_id="replace_seller_portfolio_members")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def replace_seller_portfolio_members(
    request: Request,
    portfolio_id: str = Path(..., min_length=1),
    body: ReplaceMembersBody = Body(...),
):
    try:
        portfolio = _use_case().replace_members(
            portfolio_id=portfolio_id,
            members=[
                SellerPortfolioMember(user_id=item.user_id, role=item.role)
                for item in body.members
            ],
            actor_user_id=_current_user_id(request),
        )
        return ok(
            portfolio_to_dict(portfolio),
            message="Membros da carteira atualizados.",
            operation_id="replace_seller_portfolio_members",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="replace_seller_portfolio_members")
    except ValueError as exc:
        return fail(str(exc), 422, operation_id="replace_seller_portfolio_members")
    except Exception:
        logger.exception("replace_seller_portfolio_members_failed")
        return fail(
            "Erro interno ao atualizar membros.",
            500,
            operation_id="replace_seller_portfolio_members",
        )


@router.post("/{portfolio_id}/members", operation_id="add_seller_portfolio_member")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def add_seller_portfolio_member(
    request: Request,
    portfolio_id: str = Path(..., min_length=1),
    body: AddMemberBody = Body(...),
):
    try:
        portfolio = _use_case().add_member(
            portfolio_id=portfolio_id,
            user_id=body.user_id,
            role=body.role,
            actor_user_id=_current_user_id(request),
        )
        return ok(
            portfolio_to_dict(portfolio),
            message="Membro adicionado à carteira.",
            operation_id="add_seller_portfolio_member",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="add_seller_portfolio_member")
    except ValueError as exc:
        return fail(str(exc), 422, operation_id="add_seller_portfolio_member")
    except Exception:
        logger.exception("add_seller_portfolio_member_failed")
        return fail(
            "Erro interno ao adicionar membro.",
            500,
            operation_id="add_seller_portfolio_member",
        )


@router.delete(
    "/{portfolio_id}/members/{user_id}",
    operation_id="remove_seller_portfolio_member",
)
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def remove_seller_portfolio_member(
    request: Request,
    portfolio_id: str = Path(..., min_length=1),
    user_id: str = Path(..., min_length=1),
):
    try:
        portfolio = _use_case().remove_member(
            portfolio_id=portfolio_id,
            user_id=user_id,
            actor_user_id=_current_user_id(request),
        )
        return ok(
            portfolio_to_dict(portfolio),
            message="Membro removido da carteira.",
            operation_id="remove_seller_portfolio_member",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="remove_seller_portfolio_member")
    except ValueError as exc:
        return fail(str(exc), 422, operation_id="remove_seller_portfolio_member")
    except Exception:
        logger.exception("remove_seller_portfolio_member_failed")
        return fail(
            "Erro interno ao remover membro.",
            500,
            operation_id="remove_seller_portfolio_member",
        )


@router.post("/{portfolio_id}/owner", operation_id="set_seller_portfolio_owner")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def set_seller_portfolio_owner(
    request: Request,
    portfolio_id: str = Path(..., min_length=1),
    body: SetOwnerBody = Body(...),
):
    try:
        portfolio = _use_case().set_owner(
            portfolio_id=portfolio_id,
            user_id=body.user_id,
            actor_user_id=_current_user_id(request),
        )
        return ok(
            portfolio_to_dict(portfolio),
            message="Owner da carteira atualizado.",
            operation_id="set_seller_portfolio_owner",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="set_seller_portfolio_owner")
    except ValueError as exc:
        return fail(str(exc), 422, operation_id="set_seller_portfolio_owner")
    except Exception:
        logger.exception("set_seller_portfolio_owner_failed")
        return fail(
            "Erro interno ao definir owner.",
            500,
            operation_id="set_seller_portfolio_owner",
        )


@router.post("/transfer", operation_id="transfer_seller_customers")
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def transfer_seller_customers(request: Request, body: TransferCustomersBody = Body(...)):
    try:
        customers = parse_customer_assignments(
            [item.model_dump() for item in body.customers]
        )
        source, target = _use_case().transfer_customers(
            source_portfolio_id=body.source_portfolio_id,
            target_portfolio_id=body.target_portfolio_id,
            customers=customers,
            actor_user_id=_current_user_id(request),
            reason_note=body.reason_note,
        )
        return ok(
            {
                "source": portfolio_to_dict(source),
                "target": portfolio_to_dict(target),
                "transferred_count": len(customers),
            },
            message="Clientes transferidos com sucesso.",
            operation_id="transfer_seller_customers",
        )
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="transfer_seller_customers")
    except ValueError as exc:
        return fail(str(exc), 400, operation_id="transfer_seller_customers")
    except Exception:
        logger.exception("transfer_seller_customers_failed")
        return fail(
            "Erro interno ao transferir clientes.",
            500,
            operation_id="transfer_seller_customers",
        )
