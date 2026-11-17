# EVA × Engineering API — Matriz de paridade semântica PRC

**TASK:** `EVA-ENGINEERING-API-PRC-FULL-SEMANTIC-PARITY-01`
**Revisão:** 2026-11-17 · **Seis tools MCP preservadas:**
`get_context, read, analyze, knowledge, execute, delete`
**Mecanismo:** capabilities `entity.action` no semantic_registry +
dispatch maps → mesmo `ProductRegistrationService` das rotas REST.

## Defeito original

`read(entity="product_registration", action="list")` → `501
not_implemented`. Causa: gate deliberado em `_resolve` — entradas
`status="planned"` são honestamente inexecutáveis mesmo com handler e
dispatch registrados (comentário registry: «NUNCA executável até o
dispatch estar integrado e testado no mesmo SHA»). A correção exigiu
provas de execução (testes `tool_read`/`tool_execute` completos) antes
do flip para `proven` — não foi um mero toggle.

## Classificação

`PROVEN` = registry `proven` + dispatch + teste REST×MCP no caminho
completo (gate + AuthZ + service) neste SHA.

## Solicitações PRC — leituras

| REST | Capability | Tool | Estado |
|---|---|---|---|
| GET /requests (+view=pending) | `product_registration.list` | read | PROVEN |
| GET /requests/{id} | `product_registration.detail` | read | PROVEN (prévio) |
| GET /requests/{id}/timeline | `product_registration.timeline` | read | PROVEN |
| GET /requests/{id}/verifications | `product_registration.verifications` | read | PROVEN |
| GET /reference-data | `product_registration.reference_data` | read | PROVEN |
| outbound/result | `product_registration.outbound_result` | read | PROVEN |
| GET /requests/{id}/attachments | `product_registration.attachment_list` | read | PROVEN (novo; metadados — binário EXCLUÍDO do contrato MCP) |

## Solicitações PRC — workflow/escritas

| REST | Capability | Tool | Estado |
|---|---|---|---|
| POST /intake/requests | `product_registration.submit` | execute | PROVEN (novo flip + teste ACT) |
| POST /actions/start | `.start` | execute | PROVEN (prévio) |
| PATCH /draft | `.update_draft` | execute | PROVEN (novo flip + teste ACT) |
| POST /actions/submit-review | `.submit_review` | execute | PROVEN (novo flip + teste ACT) |
| request-information | `.request_information` | execute | PROVEN (prévio) |
| return-for-correction | `.return_for_correction` | execute | PROVEN (prévio) |
| save-returned-fields | `.save_returned_fields` | execute | PROVEN (prévio) |
| resubmit-correction | `.resubmit_correction` | execute | PROVEN (prévio) |
| resume | `.resume` | execute | PROVEN (prévio) |
| return-to-attendance | `.return_to_attendance` | execute | PROVEN (prévio) |
| reject | `.reject` | execute | PROVEN (prévio; proposta selada) |
| complete | `.complete` | execute | PROVEN (prévio; proposta selada) |
| verify-and-complete | `.verify_and_complete` | execute | PROVEN (prévio; proposta selada) |

## Esclarecimentos (rodadas)

| REST | Capability | Tool | Estado |
|---|---|---|---|
| information-rounds list/get | `.information_round_list` / `_get` | read | PROVEN (prévio) |
| question accept | `.information_question_accept` | execute | PROVEN (prévio) |
| follow-up | `.information_follow_up` | execute | PROVEN (prévio) |

## Produtos acompanhados (registros técnicos)

| REST | Capability | Tool | Estado |
|---|---|---|---|
| GET /technical-records | `product_registration.records_list` | read | PROVEN (novo) |
| GET /technical-records/{id} | `product_registration.record` | read | PROVEN |
| GET …/revisions | `product_registration.revisions` | read | PROVEN |
| GET …/revisions/{n} | `product_registration.revision` | read | PROVEN |
| GET …/comparison?from&to | `product_registration.revision_compare` | read | PROVEN (novo) |
| GET …/flags | `product_registration.record_flag_list` | read | PROVEN (novo) |

## Bandeiras e conversa (solicitação + transversal)

| REST | Capability | Tool | Estado |
|---|---|---|---|
| flags list/detail/cross-case/summary | `.flag_list` / `.flag_detail` | read | PROVEN (prévio) |
| flag create/update/resolve/reopen/delete | `.flag_*` | execute | PROVEN (prévio; delete = destructive) |
| comments list/create/update | `.comment_*` | read/execute | PROVEN (prévio) |

## Exclusões explícitas (fora do denominador elegível)

| Operação | Motivo |
|---|---|
| Download binário de anexo | Transporte MCP não suporta binário autorizado; metadados expostos via `attachment_list` |
| Upload de anexo | Idem — sem canal binário governado |
| Escrita TOTVS | Owner é a API TOTVS oficial; EVA nunca escreve no Protheus por esta superfície |
| Scan/antimalware de anexo | Pipeline interno, não é operação semântica |
| Record-flag writes via EVA | Escopo desta entrega = leitura; writes REST existem mas ainda não elegíveis (avaliação futura de risco/confirmação) |

## Evidência de execução

`engineering-api/tests/test_prc_eva_parity.py` — 38 testes:

- `TestReadParityEndToEnd`: list (=REST), view=pending exclui terminal
  + status explícito prevalece, paginação, timeline (=REST),
  verifications, reference_data, outbound_result, records_list (=REST
  + flagState), record+revisions+revision+revision_compare (=REST
  `/comparison`, byte-equal), record_flag_list, forbidden sem
  permissão, not_implemented para ação desconhecida, attachment_list
  (=REST, sem storage_key).
- `TestExecuteParityEndToEnd`: submit (cria caso real, source=eva),
  update_draft (CAS/versão), submit_review (transição), bloqueio com
  ACT desabilitado.
- Classes prévias: detail/scope/dispatch/execute/proposals.

## Métricas

- MCP tools: **6 → 6** (zero adicionadas)
- Capabilities PRC: **40** (37 prévias + `revision_compare`,
  `records_list`, `record_flag_list`, `attachment_list`)
- `planned` remanescente: **0** em product_registration
- `PARITY_CODE_COVERAGE`: 100% das 40 capacidades registradas
- `PARITY_CONTRACT_COVERAGE`: reads provados byte/função-equivalentes
  ao REST nos casos testados
- `PARITY_AUTHZ_COVERAGE`: mesmo actor/AuthZ do service (testes
  forbidden + scope)
- `PARITY_RUNTIME_VERIFIED`: HML — ver seção de deploy da task

## Deploy PRD — 2026-11-17 (EVA-PRC-SEMANTIC-PARITY-CONTROLLED-PRD-RELEASE-01)

| Item | Valor |
|---|---|
| SHA publicado | `74992dafd7` (checkout PRD `9e3445a53a` — zero diffs em `engineering-api/` após o SHA aprovado → artefato equivalente) |
| Digest anterior | `sha256:082bd86a63cd…` (retido p/ rollback) |
| Digest publicado | `sha256:380919358b64…` |
| Health | `delpi-engineering-api` healthy; `/health` 200; `/apps/.../.well-known/oauth-protected-resource` 200 com tráfego real |
| Runtime PRD | 40 caps PRC `proven`, 0 planned, 0 sem dispatch; 6 tools MCP |
| ACT | `ENG_EVA_ACT_ENABLED=true` — config PRD pré-existente, preservada (não alterada) |
| MCP live (ChatGPT) | `TEST_NOT_RUN` — requer token com aud=URL-MCP + scope `mcp:tools`; validação final pelo PO na conexão produtiva |
| Rollback | retag `082bd86a63cd` + `up-prod-sequential.sh --build engineering-api`; sem mudança de schema |
