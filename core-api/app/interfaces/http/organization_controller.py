"""GLPI #887 — RH hierarchy lookup and verified Core identity bindings.

S2S team reads use a dedicated capability secret. Admin mapping writes require
rbac.manage + users.manage and an explicit human identity confirmation.
"""

from __future__ import annotations

import logging
from uuid import UUID

from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.application.services.organization_identity_review_service import (
    OrganizationIdentityReviewService,
)
from app.application.services.organization_team_service import OrganizationTeamService
from app.application.services.organization_weekly_usage_service import (
    OrganizationWeeklyUsageService,
)
from app.extensions.integration_rate_limit import integration_rate_limit
from app.infrastructure.gateways.portal_rh_organization_gateway import (
    PortalRhManagerNotFound,
    PortalRhOrganizationContractError,
    PortalRhOrganizationGateway,
    PortalRhOrganizationUnauthorized,
    PortalRhOrganizationUnavailable,
)
from app.infrastructure.persistence.sqlalchemy.organization_weekly_usage_repository import (
    SqlAlchemyOrganizationWeeklyUsageRepository,
)
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.interfaces.http.security.authorization import require_all_permissions
from app.interfaces.http.security.service_token import (
    require_organization_read_service_token,
    require_reports_direct_usage_service_token,
)
from app.interfaces.http.utils.errors import api_error

logger = logging.getLogger(__name__)

integrations_organization_bp = Blueprint(
    "integrations_organization", __name__, url_prefix="/integrations/organization"
)
admin_hr_identity_bp = Blueprint(
    "admin_hr_identity", __name__, url_prefix="/admin/organization"
)


def _bool_query(name: str, default: bool = False) -> bool:
    raw = request.args.get(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"true", "1", "yes", "sim"}:
        return True
    if normalized in {"false", "0", "no", "nao"}:
        return False
    raise ValueError(name + " deve ser true ou false.")


def _uuid(value: str) -> UUID:
    try:
        return UUID(str(value).strip())
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("user_id inválido.") from exc


@integrations_organization_bp.route(
    "/managers/<registration>/team",
    methods=["GET"],
    endpoint="get_manager_team",
)
@require_organization_read_service_token()
@integration_rate_limit(max_requests=30, per_seconds=60, key_prefix="org-team")
def get_manager_team(registration: str):
    """Read the current HR hierarchy; only mapped, active Core users get UUIDs."""
    try:
        include_indirect = _bool_query("include_indirect")
        include_inactive = _bool_query("include_inactive")
        registration = PortalRhOrganizationGateway.validate_registration(registration)
    except ValueError as exc:
        return api_error("validation_error", str(exc), status=400)

    try:
        with SqlAlchemyUnitOfWork() as uow:
            service = OrganizationTeamService(
                PortalRhOrganizationGateway(), uow.hr_registrations
            )
            result = service.get_team(
                registration,
                include_indirect=include_indirect,
                include_inactive=include_inactive,
            )
        logger.info(
            "organization_team_read count=%s unmapped=%s indirect=%s",
            result["count"], result["unmappedCount"], include_indirect,
        )
        return jsonify(result), 200
    except PortalRhManagerNotFound:
        return api_error("manager_not_found", "Gestor não localizado no RH.", status=404)
    except PortalRhOrganizationUnauthorized:
        logger.warning("organization_team_rh_credentials_rejected")
        return api_error("rh_unavailable", "Integração RH não autorizada.", status=503)
    except PortalRhOrganizationContractError:
        logger.warning("organization_team_rh_contract_invalid")
        return api_error("rh_contract_error", "Contrato de equipe RH inválido.", status=502)
    except PortalRhOrganizationUnavailable:
        logger.warning("organization_team_rh_unavailable")
        return api_error("rh_unavailable", "Portal RH indisponível.", status=503)
    except Exception:
        logger.exception("organization_team_unexpected_failure")
        return api_error("organization_team_failed", "Erro ao consultar equipe.", status=500)


@admin_hr_identity_bp.route(
    "/users/<user_id>/hr-registration", methods=["GET"]
)
@require_all_permissions(["rbac.manage", "users.manage"])
def get_user_hr_registration(user_id: str):
    try:
        uid = _uuid(user_id)
        with SqlAlchemyUnitOfWork() as uow:
            if uow.users.get_by_id(uid) is None:
                return api_error("user_not_found", "Usuário não encontrado.", status=404)
            return jsonify({
                "mapping": uow.hr_registrations.serialize(
                    uow.hr_registrations.get_by_user(uid)
                )
            }), 200
    except ValueError as exc:
        return api_error("validation_error", str(exc), status=400)
    except Exception:
        logger.exception("hr_registration_get_failed")
        return api_error("internal_error", "Falha ao consultar vínculo RH.", status=500)


@admin_hr_identity_bp.route(
    "/users/<user_id>/hr-registration", methods=["PUT"]
)
@require_all_permissions(["rbac.manage", "users.manage"])
def put_user_hr_registration(user_id: str):
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or body.get("confirmIdentity") is not True:
        return api_error(
            "validation_error",
            "É obrigatória a confirmação manual da identidade (confirmIdentity=true).",
            status=422,
        )
    verification_reference = body.get("verificationReference")
    if verification_reference is not None:
        if (
            not isinstance(verification_reference, str)
            or not 5 <= len(verification_reference.strip()) <= 120
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in verification_reference)
        ):
            return api_error(
                "validation_error",
                "verificationReference deve ter de 5 a 120 caracteres, sem controles ou quebras de linha.",
                status=422,
            )
        verification_reference = verification_reference.strip()

    try:
        uid = _uuid(user_id)
        registration = PortalRhOrganizationGateway.validate_registration(
            body.get("registration")
        )
        actor = _uuid(g.current_user.id)
    except ValueError as exc:
        return api_error("validation_error", str(exc), status=400)

    try:
        # Validate the registration against the RH source before touching the Core DB.
        person = PortalRhOrganizationGateway().get_collaborator(registration)
        if not person["active"]:
            return api_error(
                "inactive_collaborator", "Colaborador RH está inativo.", status=422
            )
        with SqlAlchemyUnitOfWork() as uow:
            user = uow.users.get_by_id(uid)
            if user is None:
                return api_error("user_not_found", "Usuário não encontrado.", status=404)
            if not user.active:
                return api_error("inactive_user", "Usuário Core está inativo.", status=422)
            before = uow.hr_registrations.get_by_user(uid)
            before_registration = before.registration if before else None
            mapping = uow.hr_registrations.upsert(
                user_id=uid, registration=registration, verified_by_user_id=actor
            )
            uow.audits.log({
                "user_id": actor,
                "action": "hr_registration.verified_upsert",
                "entity_type": "user_hr_registration",
                "entity_id": str(uid),
                "payload": {
                    "before_registration": before_registration,
                    "after_registration": registration,
                    "identity_confirmed": True,
                    "verification_reference": verification_reference,
                },
                "ip_address": request.remote_addr,
            })
            result = uow.hr_registrations.serialize(mapping)
        return jsonify({"mapping": result}), 200
    except PortalRhManagerNotFound:
        return api_error(
            "collaborator_not_found", "Matrícula não localizada no RH.", status=404
        )
    except (PortalRhOrganizationUnauthorized, PortalRhOrganizationUnavailable):
        return api_error("rh_unavailable", "Portal RH indisponível.", status=503)
    except PortalRhOrganizationContractError:
        return api_error("rh_contract_error", "Contrato RH inválido.", status=502)
    except ValueError as exc:
        return api_error("identity_conflict", str(exc), status=409)
    except IntegrityError:
        return api_error(
            "identity_conflict", "Matrícula já vinculada a outro usuário.", status=409
        )
    except Exception:
        logger.exception("hr_registration_put_failed")
        return api_error("internal_error", "Falha ao salvar vínculo RH.", status=500)


@admin_hr_identity_bp.route(
    "/users/<user_id>/hr-registration", methods=["DELETE"]
)
@require_all_permissions(["rbac.manage", "users.manage"])
def delete_user_hr_registration(user_id: str):
    try:
        uid = _uuid(user_id)
        actor = _uuid(g.current_user.id)
        with SqlAlchemyUnitOfWork() as uow:
            row = uow.hr_registrations.get_by_user(uid)
            if row is not None:
                old_registration = row.registration
                uow.hr_registrations.delete(uid)
                uow.audits.log({
                    "user_id": actor,
                    "action": "hr_registration.delete",
                    "entity_type": "user_hr_registration",
                    "entity_id": str(uid),
                    "payload": {"registration": old_registration},
                    "ip_address": request.remote_addr,
                })
        return "", 204
    except ValueError as exc:
        return api_error("validation_error", str(exc), status=400)
    except Exception:
        logger.exception("hr_registration_delete_failed")
        return api_error("internal_error", "Falha ao remover vínculo RH.", status=500)


@admin_hr_identity_bp.route(
    "/managers/<registration>/identity-review", methods=["GET"]
)
@require_all_permissions(["rbac.manage", "users.manage"])
@integration_rate_limit(max_requests=10, per_seconds=60, key_prefix="org-identity-review")
def get_manager_identity_review(registration: str):
    """Administrative, read-only identity suggestions. Not an identity verification."""
    try:
        registration = PortalRhOrganizationGateway.validate_registration(registration)
        include_indirect = _bool_query("include_indirect", default=True)
        details = _bool_query("details", default=False)
    except ValueError as exc:
        return api_error("validation_error", str(exc), status=400)

    try:
        with SqlAlchemyUnitOfWork() as uow:
            review = OrganizationIdentityReviewService(
                OrganizationTeamService(PortalRhOrganizationGateway(), uow.hr_registrations),
                uow.users,
                uow.hr_registrations,
            ).get_review(
                registration, include_indirect=include_indirect, details=details
            )
        logger.info(
            "organization_identity_review team=%s verified=%s suggestions=%s details=%s",
            review["teamCount"], review["verifiedCount"], review["suggestionCount"], details,
        )
        return jsonify(review), 200
    except ValueError as exc:
        return api_error("validation_error", str(exc), status=422)
    except PortalRhManagerNotFound:
        return api_error("manager_not_found", "Gestor não localizado no RH.", status=404)
    except PortalRhOrganizationUnauthorized:
        return api_error("rh_unavailable", "Credencial RH inválida.", status=503)
    except PortalRhOrganizationContractError:
        return api_error("rh_contract_error", "Contrato RH inválido.", status=502)
    except PortalRhOrganizationUnavailable:
        return api_error("rh_unavailable", "Portal RH indisponível.", status=503)
    except Exception:
        logger.exception("organization_identity_review_failed")
        return api_error("internal_error", "Falha na prévia de identidade.", status=500)


@admin_hr_identity_bp.route(
    "/managers/<registration>/weekly-app-opens", methods=["GET"]
)
@require_all_permissions(["rbac.manage", "users.manage"])
@integration_rate_limit(max_requests=10, per_seconds=60, key_prefix="org-weekly-opens")
def get_manager_weekly_app_opens(registration: str):
    """GLPI #887: admin-only view of one completed week, no sending/scheduling."""
    try:
        registration = PortalRhOrganizationGateway.validate_registration(registration)
        include_indirect = _bool_query("include_indirect", default=True)
        details = _bool_query("details", default=False)
        week_start = request.args.get("week_start")
    except ValueError as exc:
        return api_error("validation_error", str(exc), status=400)

    try:
        with SqlAlchemyUnitOfWork() as uow:
            report = OrganizationWeeklyUsageService(
                OrganizationTeamService(PortalRhOrganizationGateway(), uow.hr_registrations),
                SqlAlchemyOrganizationWeeklyUsageRepository(uow.session),
            ).get_weekly_report(
                registration,
                week_start=week_start,
                include_indirect=include_indirect,
                details=details,
            )
        logger.info(
            "organization_weekly_app_opens team=%s mapped=%s consented=%s details=%s",
            report["teamCount"], report["verifiedMapped"],
            report["consentGranted"], details,
        )
        return jsonify(report), 200
    except ValueError as exc:
        return api_error("validation_error", str(exc), status=422)
    except PortalRhManagerNotFound:
        return api_error("manager_not_found", "Gestor não localizado no RH.", status=404)
    except PortalRhOrganizationUnauthorized:
        return api_error("rh_unavailable", "Credencial RH inválida.", status=503)
    except PortalRhOrganizationContractError:
        return api_error("rh_contract_error", "Contrato RH inválido.", status=502)
    except PortalRhOrganizationUnavailable:
        return api_error("rh_unavailable", "Portal RH indisponível.", status=503)
    except Exception:
        logger.exception("organization_weekly_app_opens_failed")
        return api_error("internal_error", "Falha na apuração semanal.", status=500)


@integrations_organization_bp.route(
    "/managers/<registration>/reports/direct-weekly-opens", methods=["GET"]
)
@require_reports_direct_usage_service_token()
@integration_rate_limit(max_requests=90, per_seconds=60, key_prefix="reports-direct-week")
def get_manager_reports_direct_weekly_opens(registration: str):
    """S2S: one manager's direct RH employees only, with verified recipient.

    This report never accepts include_indirect, manager email or recipient ID
    from the caller. All inputs are resolved from RH + verified Core mapping.
    """
    try:
        registration = PortalRhOrganizationGateway.validate_registration(registration)
        week_start = request.args.get("week_start")
        # Forbid the possibility that a caller supplies a broader team flag.
        if "include_indirect" in request.args or "include_inactive" in request.args:
            return api_error("validation_error", "Escopo da equipe é fixo: apenas diretos ativos.", status=400)
    except ValueError as exc:
        return api_error("validation_error", str(exc), status=400)

    try:
        with SqlAlchemyUnitOfWork() as uow:
            team_service = OrganizationTeamService(
                PortalRhOrganizationGateway(), uow.hr_registrations,
            )
            report = OrganizationWeeklyUsageService(
                team_service,
                SqlAlchemyOrganizationWeeklyUsageRepository(uow.session),
            ).get_weekly_report(
                registration, week_start=week_start, include_indirect=False, details=True,
            )
            # Defensive check against a broken upstream relationship contract:
            # none of the indirect members may enter the delivery.
            members = report.get("members") or []
            if report.get("includeIndirect") is not False or any(
                row.get("relationship") != "direct" for row in members
            ):
                raise ValueError("Hierarquia RH não retornou somente subordinados diretos.")
            snapshot = team_service.get_team(
                registration, include_indirect=False, include_inactive=False,
            )
            manager = snapshot["manager"]
            if (
                not manager.get("active")
                or manager.get("identityStatus") != "mapped"
                or not manager.get("coreUserId")
            ):
                return api_error(
                    "manager_identity_missing",
                    "Gestor sem identidade Core verificada e ativa.",
                    status=422,
                )
            core_user = uow.users.get_by_id(_uuid(manager["coreUserId"]))
            email = (getattr(core_user, "email", "") or "").strip().lower()
            if (
                core_user is None
                or not getattr(core_user, "active", False)
                or not email
                or "@" not in email
                or "***" in email
            ):
                return api_error(
                    "manager_email_missing",
                    "Gestor sem conta Core ativa e e-mail válido.",
                    status=422,
                )
            core_user_id = str(core_user.id)

        result = {
            **report,
            "directOnly": True,
            "manager": {
                "registration": manager["registration"],
                "fullName": manager["fullName"],
            },
            "recipient": {
                "userId": core_user_id,
                "email": email,
            },
        }
        logger.info(
            "reports_direct_team_weekly_read team=%s mapped=%s consented=%s",
            report["teamCount"], report["verifiedMapped"], report["consentGranted"],
        )
        return jsonify(result), 200
    except ValueError as exc:
        return api_error("validation_error", str(exc), status=422)
    except PortalRhManagerNotFound:
        return api_error("manager_not_found", "Gestor não localizado no RH.", status=404)
    except PortalRhOrganizationUnauthorized:
        return api_error("rh_unavailable", "Credencial RH recusada.", status=503)
    except PortalRhOrganizationContractError:
        return api_error("rh_contract_error", "Hierarquia RH inválida.", status=502)
    except PortalRhOrganizationUnavailable:
        return api_error("rh_unavailable", "Portal RH indisponível.", status=503)
    except Exception:
        logger.exception("reports_direct_team_weekly_failed")
        return api_error("internal_error", "Falha na consulta semanal direta.", status=500)
