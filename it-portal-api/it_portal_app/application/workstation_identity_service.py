"""G2-S4-S1: provisionamento governado de identidades de inventario (sem remoto).

A preparacao cria SOMENTE client Keycloak DESABILITADO. Nao le/retorna secrets,
nao concede escopos, nao habilita ingestao e nao instala agentes Windows.
"""
from __future__ import annotations

import uuid
from typing import Protocol

from it_portal_app.application.ports import Actor
from it_portal_app.config import settings
from it_portal_app.domain.errors import ConflictError, PersistenceUnavailableError

PREFIX = "itp-ws-"


def device_client_id(workstation_id: str) -> str:
    uid = uuid.UUID(workstation_id)
    if uid.int == 0:
        raise ValueError("Workstation UUID nao pode ser zero.")
    return PREFIX + uid.hex


class IdentityStore(Protocol):
    def get(self, workstation_id: str) -> dict | None: ...
    def reserve(self, workstation_id: str, client_id: str, actor: Actor) -> dict: ...
    def prepared(self, workstation_id: str, keycloak_uuid: str, actor: Actor) -> dict: ...
    def failed(self, workstation_id: str, actor: Actor) -> None: ...
    def request_revocation(self, workstation_id: str, actor: Actor) -> dict | None: ...
    def complete_revocation(self, workstation_id: str, actor: Actor) -> None: ...
    def fail_revocation(self, workstation_id: str, actor: Actor) -> None: ...


class DisabledClientProvisioner(Protocol):
    def create_disabled(self, client_id: str, workstation_id: str) -> str: ...
    def disable_client(
        self, *, keycloak_uuid: str, client_id: str, workstation_id: str
    ) -> None: ...


class WorkstationIdentityService:
    def __init__(self, store: IdentityStore, provisioner: DisabledClientProvisioner) -> None:
        self.store = store
        self.provisioner = provisioner

    def status(self, workstation_id: str) -> dict:
        found = self.store.get(workstation_id)
        revocation = found.get("revocation_status", "none") if found else "none"
        collector = bool(
            settings.WORKSTATION_INGEST_ENABLED
            and settings.WORKSTATION_DB_BINDINGS_ENABLED
            and found
            and found.get("ingest_authorized") is True
            and found["state"] == "prepared"
            and revocation == "none"
        )
        return {
            "workstation_id": workstation_id,
            "client_id": found["client_id"] if found else None,
            "state": found["state"] if found else "not_prepared",
            "prepared_at": found["updated_at"] if found and found["state"] == "prepared" else None,
            "revocation_status": revocation,
            "can_prepare": bool(settings.WORKSTATION_PROVISIONING_ENABLED and not found),
            "can_revoke": bool(
                settings.WORKSTATION_DB_BINDINGS_ENABLED
                and settings.WORKSTATION_REVOKE_ENABLED
                and found and found["state"] == "prepared" and revocation == "none"
            ),
            "credentials_issued": False,
            "collector_enabled": collector,
            "remote_access_enabled": False,
        }

    def prepare(self, workstation_id: str, actor: Actor, *, confirmed: bool) -> dict:
        if not confirmed:
            raise ConflictError("workstation_identity_confirmation_required", "Confirme o preparo.")
        if not settings.WORKSTATION_PROVISIONING_ENABLED:
            raise ConflictError(
                "workstation_provisioning_disabled",
                "Preparacao automatica ainda nao habilitada neste ambiente.",
            )
        client_id = device_client_id(workstation_id)
        existing = self.store.reserve(workstation_id, client_id, actor)
        if existing["state"] == "prepared":
            return self.status(workstation_id)
        try:
            uuid_created = self.provisioner.create_disabled(client_id, workstation_id)
            self.store.prepared(workstation_id, uuid_created, actor)
        except Exception:
            # Se o Keycloak respondeu parcialmente, o client precisa permanecer
            # desabilitado; sem retry automatico/adocao silenciosa.
            try:
                self.store.failed(workstation_id, actor)
            except Exception:
                pass
            raise PersistenceUnavailableError(
                "workstation_provisioning_unavailable",
                "Nao foi possivel concluir o preparo. Revise o Keycloak e o cadastro antes de repetir.",
            ) from None
        return self.status(workstation_id)

    def revoke(self, workstation_id: str, actor: Actor, *, confirmed: bool) -> dict:
        """DB cutoff first, then Keycloak disable; no automatic retry on failures."""
        if not confirmed:
            raise ConflictError(
                "workstation_identity_revocation_confirmation_required",
                "Confirme a revogacao individual.",
            )
        if not (settings.WORKSTATION_DB_BINDINGS_ENABLED and settings.WORKSTATION_REVOKE_ENABLED):
            raise ConflictError(
                "workstation_revocation_disabled",
                "Revogacao automatica disponivel apenas apos homologacao do modo banco.",
            )
        client = self.store.request_revocation(workstation_id, actor)
        if client is None:
            return self.status(workstation_id)
        try:
            self.provisioner.disable_client(
                keycloak_uuid=client["keycloak_client_uuid"],
                client_id=client["client_id"],
                workstation_id=workstation_id,
            )
            self.store.complete_revocation(workstation_id, actor)
        except Exception:
            # Mesmo se Keycloak estiver inacessivel, o banco ja revogou o grant.
            # Nao reabrir binding automaticamente nem anunciar sucesso.
            try:
                self.store.fail_revocation(workstation_id, actor)
            except Exception:
                pass
            raise PersistenceUnavailableError(
                "workstation_revocation_requires_review",
                "Revogacao pendente de verificacao manual no Keycloak.",
            ) from None
        return self.status(workstation_id)
