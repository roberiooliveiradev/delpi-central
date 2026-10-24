from __future__ import annotations

from uuid import UUID

from app.application.security.supplies_permissions import can_administer, can_enter_shell
from app.application.services.authorization_service import AuthorizationService
from app.application.services.capability_resolution_service import (
    CapabilityResolutionService,
)
from app.application.services.preferences_service import PreferencesService
from app.application.services.requester_identity_service import (
    RequesterIdentityService,
)
from app.domain.entities import EffectiveUser
from app.domain.exceptions import AuthorizationError
from app.infrastructure.gateways.core_api_http_gateway import CoreApiHttpGateway
from app.infrastructure.gateways.purchase_requests_gateway import (
    PurchaseRequestsGateway,
)
from app.infrastructure.persistence.preferences_repository import PreferencesRepository

_RELATED_REQUESTS_MAX_PAGE_SIZE = 20
# Explicit "authorized history" semantics: the producer applies a silent
# 90-day lookback when date_from is absent, so the profile section pins a
# floor date instead of inheriting an implicit window.
_RELATED_REQUESTS_DATE_FROM = "2000-01-01"


class UserProfileService:
    """Compose Core identity + supplies preferences for WF-USER."""

    def __init__(
        self,
        *,
        preferences: PreferencesService | None = None,
        capabilities: CapabilityResolutionService | None = None,
        authorization: AuthorizationService | None = None,
        core_gateway: CoreApiHttpGateway | None = None,
        preferences_repository: PreferencesRepository | None = None,
        purchase_requests_gateway: PurchaseRequestsGateway | None = None,
        requester_identity: RequesterIdentityService | None = None,
    ) -> None:
        self.preferences = preferences or PreferencesService()
        self.capabilities = capabilities or CapabilityResolutionService()
        self.authorization = authorization or AuthorizationService()
        self.core_gateway = core_gateway or CoreApiHttpGateway()
        self.preferences_repository = (
            preferences_repository or PreferencesRepository()
        )
        self.purchase_requests_gateway = (
            purchase_requests_gateway or PurchaseRequestsGateway()
        )
        self.requester_identity = requester_identity or RequesterIdentityService()

    def _assert_can_view(self, actor: EffectiveUser, target_user_id: str) -> None:
        target = (target_user_id or "").strip()
        if not target:
            raise AuthorizationError("Forbidden")
        if actor.id == target:
            if not can_enter_shell(actor):
                raise AuthorizationError("Forbidden")
            return
        if not can_administer(actor):
            raise AuthorizationError("Forbidden")

    def _assert_can_edit(self, actor: EffectiveUser, target_user_id: str) -> None:
        target = (target_user_id or "").strip()
        if not target or actor.id != target:
            raise AuthorizationError("Forbidden")
        if not can_enter_shell(actor):
            raise AuthorizationError("Forbidden")

    def _identity_for(
        self,
        actor: EffectiveUser,
        target_user_id: str,
    ) -> dict[str, str]:
        target = target_user_id.strip()
        if actor.id == target:
            return {
                "userId": actor.id,
                "name": (actor.name or "").strip() or actor.email or actor.id,
                "email": actor.email or "",
            }

        token = actor.access_token or ""
        if token:
            try:
                found = self.core_gateway.lookup_directory_users(
                    access_token=token,
                    user_ids=[target],
                    reveal_email=True,
                )
                hit = found.get(target)
                if hit:
                    return {
                        "userId": str(hit.get("id") or target),
                        "name": str(hit.get("name") or target),
                        "email": str(hit.get("email") or ""),
                    }
            except Exception:
                pass

        return {"userId": target, "name": target, "email": ""}

    def _preferences_for(self, user_id: str) -> dict:
        try:
            uid = UUID(user_id)
        except ValueError as exc:
            raise AuthorizationError("Forbidden") from exc
        row = self.preferences_repository.get(uid)
        if not row:
            return {
                "userId": user_id,
                "defaultBranch": None,
                "tableDensity": "comfortable",
            }
        return {
            "userId": str(row["user_id"]),
            "defaultBranch": row.get("default_branch"),
            "tableDensity": row.get("table_density") or "comfortable",
        }

    def _person_identity_fields(self, target_user_id: str) -> dict:
        """Campos transversais Minha DELPI (Core). Ausência → null (UI: Não informado)."""
        empty = {
            "jobTitle": None,
            "phone": None,
            "mobile": None,
            "whatsapp": None,
            "hasPhoto": False,
        }
        try:
            raw = self.core_gateway.get_person_profile(target_user_id)
        except Exception:
            return empty
        if not isinstance(raw, dict):
            return empty

        def text(key: str) -> str | None:
            value = raw.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
            return None

        return {
            "jobTitle": text("job_title"),
            "phone": text("phone_e164"),
            "mobile": text("mobile_e164"),
            "whatsapp": text("whatsapp_e164"),
            "hasPhoto": bool(raw.get("has_photo")),
        }

    def _self_access_block(self, actor: EffectiveUser) -> dict:
        from app.application.security.supplies_permissions import (
            SUPPLIES_ACCESS,
            SUPPLIES_MANAGE,
        )

        codes = sorted(
            code
            for code in actor.permissions
            if isinstance(code, str) and code in {SUPPLIES_ACCESS, SUPPLIES_MANAGE}
        )
        return {
            "isSuperadmin": bool(actor.is_superadmin),
            "permissions": codes,
        }

    def get(self, actor: EffectiveUser, target_user_id: str) -> dict:
        target = (target_user_id or "").strip()
        self._assert_can_view(actor, target)
        is_self = actor.id == target
        identity = self._identity_for(actor, target)
        preferences = (
            self.preferences.get(actor) if is_self else self._preferences_for(target)
        )
        person = self._person_identity_fields(target)

        payload: dict = {
            "userId": identity["userId"],
            "name": identity["name"],
            "email": identity["email"],
            "jobTitle": person["jobTitle"],
            "phone": person["phone"],
            "mobile": person["mobile"],
            "whatsapp": person["whatsapp"],
            "hasPhoto": person["hasPhoto"],
            "isSelf": is_self,
            "preferences": preferences,
            "capabilities": None,
            "allowedUnits": [],
            "isSuperadmin": None,
            "permissions": None,
        }
        if is_self:
            caps = self.capabilities.resolve(actor)
            payload["capabilities"] = caps["capabilities"]
            payload["allowedUnits"] = caps["allowedUnits"]
            access = self._self_access_block(actor)
            payload["isSuperadmin"] = access["isSuperadmin"]
            payload["permissions"] = access["permissions"]
        return payload

    def _protheus_ids_for(self, target_user_id: str) -> list[str] | None:
        """Core user id → mapped Protheus user ids (deterministic join).

        Returns None when the Core lookup is unavailable — an integration
        failure is not the same as "user has no TOTVS link".
        """
        try:
            mappings = self.core_gateway.lookup_protheus_identities(
                user_ids=[target_user_id]
            )
        except Exception:
            return None
        if mappings is None:
            return None
        pids = {
            str(item.get("protheus_user_id") or "").strip()
            for item in mappings.values()
            if str(item.get("mapping_status") or "").strip() == "mapped"
        }
        pids.discard("")
        return sorted(pids)

    def related_purchase_requests(
        self,
        actor: EffectiveUser,
        target_user_id: str,
        *,
        branches: list[str] | None = None,
        page: int = 1,
        page_size: int = 5,
    ) -> dict:
        """SCs do vínculo Core↔Protheus do usuário — mesma política self|admin.

        O filtro do cliente só restringe as unidades do actor (validado pelo
        decorator `require_units`); a resolução do requester sempre usa o
        `protheus_user_id` mapeado do *target*, nunca o actor.
        """
        target = (target_user_id or "").strip()
        self._assert_can_view(actor, target)
        cleaned_branches = [
            str(branch or "").strip() for branch in branches or []
        ]
        cleaned_branches = [branch for branch in cleaned_branches if branch]
        if cleaned_branches:
            # Optional restriction — every requested unit must belong to the actor.
            self.authorization.require_units(actor, cleaned_branches)
        # The producer contract requires at least one branch; without an
        # explicit filter the universe is the actor's own authorized units —
        # never wider than the caller's scope.
        effective_branches = cleaned_branches or self.authorization.allowed_units(
            actor
        )
        pids = self._protheus_ids_for(target)
        empty = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": page_size,
            "protheus_user_ids": pids or [],
            "requester_unmapped": pids == [],
            "date_from": _RELATED_REQUESTS_DATE_FROM,
        }
        if pids is None:
            return {**empty, "error": "identity_lookup_unavailable"}
        if not pids:
            return empty
        if not effective_branches:
            return empty

        page = max(1, int(page or 1))
        page_size = min(max(1, int(page_size or 5)), _RELATED_REQUESTS_MAX_PAGE_SIZE)
        params: list[tuple[str, str]] = [("requester_user_id", pid) for pid in pids]
        for branch in effective_branches:
            params.append(("branch", branch))
        params += [
            ("date_from", _RELATED_REQUESTS_DATE_FROM),
            ("page", str(page)),
            ("page_size", str(page_size)),
            ("sort_by", "issue_date"),
            ("sort_dir", "desc"),
        ]
        try:
            payload = self.purchase_requests_gateway.list_purchase_requests(
                access_token=actor.access_token or "",
                params=params,
            )
        except Exception as exc:
            return {**empty, "error": "related_requests_unavailable", "detail": str(exc)}
        data = payload if isinstance(payload, dict) else {}
        if isinstance(data.get("data"), dict):
            data = data["data"]
        data = self.requester_identity.enrich_payload(
            data, access_token=actor.access_token or ""
        )
        if not isinstance(data, dict):
            data = {}
        return {
            "items": data.get("items") if isinstance(data.get("items"), list) else [],
            "total": data.get("total") if isinstance(data.get("total"), int) else 0,
            "page": data.get("page") or page,
            "page_size": data.get("page_size") or page_size,
            "protheus_user_ids": pids,
            "requester_unmapped": False,
            "date_from": _RELATED_REQUESTS_DATE_FROM,
        }

    def photo(
        self, actor: EffectiveUser, target_user_id: str
    ) -> tuple[bytes, str, str] | None:
        """Photo bytes for the profile avatar — self|admin, fail-closed."""
        target = (target_user_id or "").strip()
        self._assert_can_view(actor, target)
        try:
            return self.core_gateway.get_person_profile_photo(target)
        except Exception:
            return None

    def patch(self, actor: EffectiveUser, target_user_id: str, payload: dict) -> dict:
        target = (target_user_id or "").strip()
        self._assert_can_edit(actor, target)
        prefs_patch = payload.get("preferences") if isinstance(payload, dict) else None
        if prefs_patch is None and isinstance(payload, dict):
            prefs_patch = {
                key: payload[key]
                for key in ("defaultBranch", "tableDensity")
                if key in payload
            }
        if not isinstance(prefs_patch, dict):
            prefs_patch = {}
        self.preferences.patch(actor, prefs_patch)
        return self.get(actor, target)
