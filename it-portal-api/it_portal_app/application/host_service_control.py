"""#1585 - Controle remoto por agente com autorizacao default-deny.

Politica operacional fora do inventario: NENHUM servico e controlavel ate
que feature flag, allowlist de nomes exatos e binding por cliente estejam
explicitamente configurados no BFF. Favoritos/criticidade NAO dao acesso.
"""
from __future__ import annotations

import os
import uuid

from it_portal_app.application.ports import Actor
from it_portal_app.domain.errors import ConflictError, NotFoundError, ValidationError
from it_portal_app.domain.servers import normalize_hostname

_ACTIONS = frozenset({"start", "stop", "restart"})
# Protecao adicional contra configuracao acidental de servicos nucleares.
_PROTECTED = frozenset({
    "rpcss", "dcomlaunch", "eventlog", "plugplay", "schedule", "winmgmt",
    "samss", "lsass", "power", "profsvc", "bfe", "mpssvc", "lanmanserver",
    "netlogon", "wuauserv", "cryptsvc",
})


def enabled() -> bool:
    return os.environ.get("IT_PORTAL_WINDOWS_CONTROL_ENABLED", "").strip().lower() == "true"


def _service_key(value: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 200:
        raise ValidationError("invalid_control_service", "Nome de serviço inválido.")
    if value != value.strip() or any(ord(ch) < 32 or ch in "\\/ *?" for ch in value):
        raise ValidationError("invalid_control_service", "Nome técnico de serviço inválido.")
    key = value.casefold()
    if len(key) > 200:
        raise ValidationError("invalid_control_service", "Nome técnico excede o limite.")
    return key


def control_targets() -> dict[str, frozenset[str]]:
    """UUID=NomeExato1,NomeExato2;uuid2=NomeExato (sem wildcard)."""
    mapping: dict[str, frozenset[str]] = {}
    raw = os.environ.get("IT_PORTAL_WINDOWS_CONTROL_TARGETS", "")
    for block in raw.split(";"):
        if not block.strip() or "=" not in block:
            continue
        server, services = block.split("=", 1)
        try:
            sid = str(uuid.UUID(server.strip()))
            keys = frozenset(_service_key(s.strip()) for s in services.split(",") if s.strip())
        except (ValueError, ValidationError):
            continue  # invalido: negar, nunca liberar parcial no bloco
        keys = keys - _PROTECTED
        if keys:
            mapping[sid] = keys
    return mapping


def agent_bindings() -> dict[str, frozenset[str]]:
    """Configuracao diferente da ingestao de inventario Windows."""
    raw = os.environ.get("IT_PORTAL_WINDOWS_CONTROL_AGENT_BINDINGS", "")
    result: dict[str, set[str]] = {}
    for block in raw.split(";"):
        if "=" not in block:
            continue
        client, ids = block.split("=", 1)
        client = client.strip()
        if not client or len(client) > 100:
            continue
        for candidate in ids.split(","):
            try:
                sid = str(uuid.UUID(candidate.strip()))
            except ValueError:
                continue
            result.setdefault(client, set()).add(sid)
    return {client: frozenset(sids) for client, sids in result.items()}


class HostServiceControl:
    def __init__(self, repository, servers):
        self.repository = repository
        self.servers = servers

    def _server(self, server_id: str) -> dict:
        server = self.servers.get_server(server_id)
        if server is None:
            raise NotFoundError("server_not_found", "Servidor não encontrado.")
        if server.get("archived"):
            raise ConflictError("server_archived", "Servidor arquivado não pode receber ações.")
        return server

    def allowed(self, server_id: str, service_key: str) -> bool:
        return enabled() and service_key in control_targets().get(server_id, frozenset())

    def decorate(self, server_id: str, items: list[dict]) -> list[dict]:
        targets = control_targets().get(server_id, frozenset()) if enabled() else frozenset()
        return [{**item, "control_allowed": (
            item["service_key"] in targets and bool(item["is_present"])
        )} for item in items]

    def submit(self, server_id: str, service_name: str, action: str,
               request_id: str, *, confirmed: bool, actor: Actor) -> dict:
        self._server(server_id)
        key = _service_key(service_name)
        if action not in _ACTIONS:
            raise ValidationError("invalid_control_action", "Ação não permitida.")
        if not confirmed:
            raise ValidationError("control_confirmation_required", "Confirme a ação no Portal de TI.")
        if not self.allowed(server_id, key):
            raise ConflictError("control_target_blocked", "Este serviço não está liberado para controle remoto.")
        return self.repository.enqueue(
            server_id, key, action, str(uuid.UUID(request_id)), actor,
        )

    def status(self, server_id: str, action_id: str) -> dict:
        self._server(server_id)
        row = self.repository.status(server_id, action_id)
        if row is None:
            raise NotFoundError("control_action_not_found", "Solicitação não encontrada.")
        return row

    def _agent_server(self, server_id: str, client_id: str):
        server = self._server(server_id)
        if not enabled() or not control_targets().get(server_id):
            raise ConflictError("control_disabled", "Controle remoto indisponível neste servidor.")
        if server_id not in agent_bindings().get(client_id, frozenset()):
            raise ConflictError("agent_not_bound", "Agente não autorizado neste servidor.")
        return server

    def poll(self, server_id: str, client_id: str, hostname: str) -> dict | None:
        server = self._agent_server(server_id, client_id)
        if normalize_hostname(server["hostname"]) != normalize_hostname(hostname):
            raise ConflictError("control_hostname_mismatch", "Hostname do agente não confere.")
        return self.repository.claim(server_id, client_id)

    def report(self, server_id: str, client_id: str, action_id: str,
               lease: str, *, status: str, state_after: str | None,
               error_code: str | None) -> dict:
        self._agent_server(server_id, client_id)
        if status not in {"succeeded", "failed"}:
            raise ValidationError("invalid_control_result", "Resultado inválido.")
        if status == "succeeded" and state_after not in {"running", "stopped"}:
            raise ValidationError("invalid_control_state", "Estado final inválido.")
        if status == "failed" and (state_after is not None and state_after not in {"running", "stopped", "paused", "unknown"}):
            raise ValidationError("invalid_control_state", "Estado final inválido.")
        codes = {"access_denied", "service_not_found", "not_allowed", "precondition_failed",
                 "dependent_services", "timeout", "execution_failed", "disabled"}
        if status == "failed" and error_code not in codes:
            raise ValidationError("invalid_control_error", "Código de falha inválido.")
        if status == "succeeded" and error_code is not None:
            raise ValidationError("invalid_control_result", "Resultado inconsistente.")
        return self.repository.finish(server_id, action_id, client_id, lease,
                                      status=status, state_after=state_after,
                                      error_code=error_code)
