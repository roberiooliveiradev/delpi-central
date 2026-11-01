# 26 — VISTA/TV B5 list_shares ROOT-CAUSE & HOTFIX EXECUTION REPORT

**Data:** 2026-10-31 · **Commit:** `2e4aef7ceb` · **Deploy:** `srv-api`
imagem `sha256:79df6c0f3f55`

## Root cause

`PlaylistAccess.can_manage`/`can_read`/`can_edit` são **`@property`**
(`playlist_access_service.py:19-27`). `playlist_share_service.
assert_can_manage` chamava `access.can_manage()` → `TypeError:
'bool' object is not callable` → `INTERNAL_ERROR` 500 em todos os
cenários (playlist inexistente, viewer, editor, manager).

Os testes B5 originais passavam porque mockavam `can_manage=lambda: True`
(tornando o atributo chamável por acidente) — o bug escapou para
produção.

## Fix

`access.can_manage` (sem parênteses) — único call site em
`playlist_share_service.py`. Contrato inalterado:

- `level != "owner"` → `PermissionError` → 403 (fail-closed, anti-enum
  — não distingue "playlist inexistente" de "sem permissão", igual à
  rota REST `require_playlist_access`).
- `level == "owner"` → lista real.
- Sem bypass de manage, sem lista vazia para esconder erro.

## Regressão

- Mocks corrigidos para property (`can_manage=True` não lambda).
- Novo `test_list_shares_real_access_property` — `PlaylistAccess`
  **real**: editor→deny, owner→allow, none→deny.
- **2358/2358 PASS** no HEAD (foi 2357 + 1 novo teste).
- 6 tools/6 opIds preservados.

## Vereditos

`ROOT_CAUSE_PROVEN` · `INTEGRATION_PASS` · `SECURITY_PASS` ·
`DEPLOY_VERIFIED` · **`HOTFIX_COMPLETE`**

Pendências externas de homologação preservadas (doc 25):
`EXTERNAL_HUMAN_CHANNEL_PENDING` + `GPT_BUILDER_SYNC_PENDING_OPERATOR`.
