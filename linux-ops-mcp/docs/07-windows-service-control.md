# ATLAS — Controle seguro de serviços Windows

**Atualizado:** 2026-11-19  
**Escopo:** prepare/confirm via MCP sobre o control plane #1585 do Portal de TI. Sem PowerShell arbitrário, sem WinRM, sem deploy PREPARE/ACT.

## Fluxo

```text
Usuario (ChatGPT)
  → prepare_* / start|stop|restart_windows_service
      → POST /servers/{id}/host-services/{name}/action-confirmations
  → confirmacao humana explicita
  → confirm_windows_service_action (user_confirmed=true)
      → POST /servers/{id}/host-services/{name}/actions {confirmation_id}
      → GET action status + releitura host-services
  → Agente Windows (S2S) claim/result
```

## Regras

- Allowlist + flag `IT_PORTAL_WINDOWS_CONTROL_*` no Portal (default OFF).
- Challenge one-shot (TTL ~3 min), bound a sujeito + servidor + serviço + ação + `state_before`.
- Replay/expirado/mismatch/estado alterado → fail-closed.
- `control_allowed` na listagem identifica serviços elegíveis; favoritos não liberam controle.
- Resultado só é “sucesso” com `status=succeeded` e `state_after` comprovado.

## Permissões

- MCP READ: `it-portal.access`, `it-portal.servers.view`
- MCP CONTROL: + `it-portal.host-services.control` (Core fresh)
- Portal revalida nas rotas de prepare/actions

## Testes

- `tests/test_windows_service_actions.py`
- `it-portal-api/tests/test_host_service_control.py` (prepare/confirm)
- CI inventário: 8 READ + 5 CONTROL
