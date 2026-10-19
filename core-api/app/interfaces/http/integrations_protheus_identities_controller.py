"""S2S Protheus identity lookups for authorized consumers (purchase-requests, etc.)."""

from __future__ import annotations

import logging
from uuid import UUID

from flask import Blueprint, jsonify, request

from app.application.use_cases.protheus_identity.get_user_protheus_identity_use_case import (
    GetUserProtheusIdentityUseCase,
)
from app.application.use_cases.protheus_identity.upsert_user_protheus_identity_use_case import (
    UpsertUserProtheusIdentityUseCase,
)
from app.extensions.integration_rate_limit import integration_rate_limit
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.interfaces.http.security.service_token import require_service_token
from app.interfaces.http.utils.errors import api_error

logger = logging.getLogger(__name__)

integrations_protheus_identities_bp = Blueprint(
    "integrations_protheus_identities",
    __name__,
    url_prefix="/integrations/protheus-identities",
)

_LOOKUP_MAX_IDS = 50
_LOOKUP_MAX_PROTHEUS_IDS = 50


def _parse_user_id(raw: str) -> UUID:
    return UUID(str(raw).strip())


@integrations_protheus_identities_bp.route("/by-user/<user_id>", methods=["GET"])
@require_service_token()
@integration_rate_limit()
def get_protheus_identity_by_user(user_id: str):
    try:
        uid = _parse_user_id(user_id)
    except ValueError:
        return api_error("validation_error", "user_id inválido.", status=400)
    try:
        with SqlAlchemyUnitOfWork() as uow:
            mapping = GetUserProtheusIdentityUseCase(uow).execute(user_id=uid)
        return jsonify({"mapping": mapping}), 200
    except LookupError as exc:
        return api_error("not_found", str(exc), status=404)
    except Exception:
        logger.exception("get_protheus_identity_by_user_failed")
        return api_error(
            "protheus_identity_failed",
            "Erro ao carregar identidade Protheus.",
            status=500,
        )


@integrations_protheus_identities_bp.route("/by-protheus-user/<protheus_user_id>", methods=["GET"])
@require_service_token()
@integration_rate_limit()
def get_protheus_identity_by_protheus_user(protheus_user_id: str):
    normalized = (protheus_user_id or "").strip()
    if not normalized:
        return api_error("validation_error", "protheus_user_id inválido.", status=400)
    try:
        with SqlAlchemyUnitOfWork() as uow:
            identity = uow.protheus_identities.get_by_protheus_user_id(normalized)
        return jsonify({"mapping": identity.to_dict() if identity else None}), 200
    except Exception:
        logger.exception("get_protheus_identity_by_protheus_user_failed")
        return api_error(
            "protheus_identity_failed",
            "Erro ao resolver identidade Protheus.",
            status=500,
        )


@integrations_protheus_identities_bp.route("/lookup", methods=["POST"])
@require_service_token()
@integration_rate_limit()
def lookup_protheus_identities():
    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        return api_error("validation_error", "body inválido", status=400)

    raw_user_ids = body.get("user_ids")
    raw_protheus_ids = body.get("protheus_user_ids")

    if raw_user_ids is not None and not isinstance(raw_user_ids, list):
        return api_error("validation_error", "user_ids must be an array", status=400)
    if raw_protheus_ids is not None and not isinstance(raw_protheus_ids, list):
        return api_error(
            "validation_error",
            "protheus_user_ids must be an array",
            status=400,
        )
    if raw_user_ids is None and raw_protheus_ids is None:
        return api_error(
            "validation_error",
            "Informe user_ids ou protheus_user_ids.",
            status=400,
        )
    if raw_user_ids is not None and len(raw_user_ids) > _LOOKUP_MAX_IDS:
        return api_error(
            "validation_error",
            f"user_ids must contain at most {_LOOKUP_MAX_IDS} items",
            status=400,
        )
    if raw_protheus_ids is not None and len(raw_protheus_ids) > _LOOKUP_MAX_PROTHEUS_IDS:
        return api_error(
            "validation_error",
            f"protheus_user_ids must contain at most {_LOOKUP_MAX_PROTHEUS_IDS} items",
            status=400,
        )

    items: list[dict] = []
    try:
        with SqlAlchemyUnitOfWork() as uow:
            if raw_user_ids:
                uids: list[UUID] = []
                for raw in raw_user_ids:
                    try:
                        uids.append(_parse_user_id(str(raw)))
                    except ValueError:
                        continue
                for identity in uow.protheus_identities.get_by_user_ids(uids):
                    items.append(identity.to_dict())
            if raw_protheus_ids:
                seen = {item["user_id"] for item in items}
                for raw in raw_protheus_ids:
                    identity = uow.protheus_identities.get_by_protheus_user_id(
                        str(raw or "").strip()
                    )
                    if identity and str(identity.user_id) not in seen:
                        items.append(identity.to_dict())
                        seen.add(str(identity.user_id))
        return jsonify({"items": items}), 200
    except Exception:
        logger.exception("lookup_protheus_identities_failed")
        return api_error(
            "protheus_identity_lookup_failed",
            "Erro ao buscar identidades Protheus.",
            status=500,
        )


@integrations_protheus_identities_bp.route("/by-user/<user_id>", methods=["PUT"])
@require_service_token()
@integration_rate_limit()
def upsert_protheus_identity_s2s(user_id: str):
    """Compatibility write for purchase-requests admin during cutover."""
    try:
        uid = _parse_user_id(user_id)
    except ValueError:
        return api_error("validation_error", "user_id inválido.", status=400)

    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        return api_error("validation_error", "body inválido", status=400)

    try:
        with SqlAlchemyUnitOfWork() as uow:
            mapping = UpsertUserProtheusIdentityUseCase(uow).execute(
                user_id=uid,
                actor_user_id=None,
                protheus_user_id=body.get("protheus_user_id"),
                protheus_user_code=body.get("protheus_user_code"),
                mapping_status=str(body.get("mapping_status") or "mapped"),
                mapping_source=body.get("mapping_source") or "manual",
                verified=bool(body.get("verified", False)),
                ip_address=request.remote_addr,
            )
        return jsonify({"mapping": mapping}), 200
    except LookupError as exc:
        return api_error("not_found", str(exc), status=404)
    except ValueError as exc:
        return api_error("validation_error", str(exc), status=422)
    except Exception:
        logger.exception("upsert_protheus_identity_s2s_failed")
        return api_error(
            "protheus_identity_upsert_failed",
            "Erro ao atualizar identidade Protheus.",
            status=500,
        )
