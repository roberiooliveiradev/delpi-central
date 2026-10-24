# USERS.PROFILE.S2 — E-mail completo e solicitações relacionadas na ficha

Status: **CONCLUÍDO** · Escopo: `supplies-api` + `plugins/supplies` · Sem permission nova, sem escrita ERP, sem bypass de mascaramento Core.

## Frente A — E-mail mascarado (`p***@delpi.com.br`)

**Causa-raiz (provada em código):** `Core /me/directory/users/lookup` mascara `email` por padrão (`LookupDirectoryUsersUseCase(mask_email=True)` → `_mask_email`). O BFF `UserProfileService._identity_for` chamava o endpoint sem a flag de revelação — a máscara era produzida **pela Core**, não pelo BFF/MFE.

**Contrato Core:** o mesmo endpoint aceita `reveal_email=true` (query/body) — a própria Core documenta «Perfis de portal / SMTP precisam do endereço real (paridade com search)». **Fix:** gateway `lookup_directory_users` ganhou `reveal_email: bool = False`; `_identity_for` passa `True` (perfil já é self|admin — escopo mais restrito que o typeahead); `RequesterIdentityService` segue mascarado (minimização — só precisa do nome). Self já vinha completo via JWT (`actor.email`).

## Frente B — Lista vazia de solicitações relacionadas

**Causa-raiz primária (provada):** o produtor exige `branch` (`purchase-requests-api` rota `Query(...)`, e `authorize_portal_branches([])` → `ValueError`). O BFF só enviava `branch` com filtro explícito → **422 → `except` → `{error:"related_requests_unavailable"}` → o MFE ignorava `data.error` e renderizava `relatedEmpty`** («Nenhuma solicitação…»). Degradação era indistinguível de universo vazio.

**Causa-raiz secundária (período implícito):** sem `date_from`, `api-delpi` aplica `DEFAULT_LOOKBACK_DAYS=90` — a seção herdaria um recorte silencioso de 90 dias.

**Evidência de correlação (runtime):**
- Core `user_protheus_identities`: `c8ef4b53-a743-4180-8556-3a957ad1ecf7` ↔ `protheus_user_id='000304'`, `mapping_status=mapped`.
- TOTVS `SC1010`: SC `178764` → `C1_USER='000304'`, `C1_FILIAL='01'`, `C1_EMISSAO='20261023'`. Vínculo exato confirmado — a SC pertence à pessoa da ficha.

**Fixes (`UserProfileService.related_purchase_requests`):**
1. Sem filtro explícito, `branch` = `allowed_units(actor)` — exigência do contrato do produtor; **nunca amplia** o universo (é o próprio recorte autorizado do caller). Filtro explícito segue fail-closed via `require_units`.
2. `date_from="2000-01-01"` explícito — semântica de histórico autorizado, ecoada na resposta (`date_from`); sem `date_to` (o produtor fecha em hoje). Paginação server-side preservada (máx 20).
3. `_protheus_ids_for` → `list | None`: `None` = lookup Core indisponível → `error:"identity_lookup_unavailable"` (antes `except`→`[]`=`requester_unmapped` — indisponibilidade era mascarada como ausência de vínculo). Gateway `lookup_protheus_identities` agora retorna `None` quando **toda** chamada falha (callers antigos já guardavam `if not mappings`; `resolve_mapped_user_id` ganhou guarda).
4. MFE: `related.data.error` → estado de erro distinto (`relatedIdentityUnavailable` para falha de vínculo, `relatedError` genérico) + retry. «Ver todas» agora inclui `date_from` ecoado — mesma semântica da seção.

## Testes

- `supplies-api`: **455 pass** — +4 novos: expansão do escopo autorizado + `date_from`, lookup indisponível ≠ unmapped, filial não autorizada → `AuthorizationError`, e-mail `reveal_email=True` com endereço completo.
- MFE: **390 pass** · `tsc -b` limpo · lint 0 erros (1 warning preexistente) · `vite build` OK.

## Estados da seção (contrato)

| Estado | Indicador |
|---|---|
| loading | `relatedLoading` |
| erro fonte | `error:"related_requests_unavailable"` → banner + retry |
| falha vínculo Core | `error:"identity_lookup_unavailable"` → `relatedIdentityUnavailable` |
| sem vínculo TOTVS | `requester_unmapped:true` → `relatedUnmapped` |
| zero SCs no universo | `items:[]` → `relatedEmpty` |
| acesso negado | 403 (HTTP) |

## Deploy / rollback

`git revert <sha>` + redeploy `supplies` + `supplies-api`. Sem flag, sem migração, sem contrato removido (campos aditivos apenas).
