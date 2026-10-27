# 23 — Ledger de Requisitos, Critérios de Aceite e Testes

> **DELTA RQ/AC APROVADO PELO PO EM 26/10/2026 — TARGET, GATE DE CONTRATOS PENDENTE:** `RQ-P1-01` deve aceitar seleção de **mês de referência** sem exigir `monthly_competence` aberta, template publicado ou documento anexado; GET de relatórios por mês continua sob owner e AuthZ, com estado ausente/erro explícito. `RQ-P2-01` na tabela abaixo registra o **contrato AS-IS de snapshot na abertura**, não é mais precondição de **consulta**. O cadastro mestre de tipos/entregáveis é versionado por vigência efetiva desde a referência escolhida, sem recadastro mensal; itens/evidências históricos de fechamentos finalizados não sofrem mutação retroativa. **AC a detalhar antes de execução:** seleção e deep link YYYY-MM; mês sem abertura; sem lista/sem anexos; relatórios com fonte disponível/indisponível; mudança futura no cadastro mestre; competência finalizada; mês em andamento; autorização de cadastro/anexo; testes de regressão P2/P5. Status de implementação desta decisão: `PARTIAL_IMPLEMENTED` — 26/10/2026 (CF-PROC0072-MONTHLY-REFERENCE-CATALOG-001): seleção de mês de referência, deep link YYYY-MM, mês sem abertura com estado honesto + abertura autorizada, lista de competências como atalhos; relatórios P2/R01–R15 por mês **sem** competência e cadastro mestre de entregáveis seguem `DECISION_REQUIRED`/`TO_INVENTORY` até contrato/GO. Detalhamento do acoplamento e opções de reconciliação em [doc 112 §32](./112-design-visual-fechamento-mensal-wireframes.md) (DR-C1 abertura sem template / DR-C2 relatórios sem competência / DR-C3 propagação a competência aberta). **Execução — CF-PROC0072-MONTHLY-OPEN-003:** DR-C1 implementado — `POST /closing/competences` sem template PUBLISHED cria competência com `template_version_id` NULL e checklist legitimamente vazio (V015, audit `opened_without_template`, idempotente); RQ-P2-01 passa a ter dois modos: com template vigente (snapshot AS-IS) e sem template (lista vazia). Deploy produtivo da migration **executado** (CF-PROC0072-MONTHLY-OPEN-PROD-CLARA-004, @`052d344d90`): V015 aplicada, `2026-09` aberto em produção sem template com audit `opened_without_template`. DR-C2/DR-C3 seguem `DECISION_REQUIRED`. [Doc 112](./112-design-visual-fechamento-mensal-wireframes.md).


## Objetivo

Fornecer rastreabilidade executável entre requisito funcional, página, critério de aceite, teste e dependência de implementação.

Este ledger complementa:
- [15-requisitos-criterios-de-aceite-e-testes.md](./15-requisitos-criterios-de-aceite-e-testes.md);
- [15.1-p3-criterios-paridade-monetaria.md](./15.1-p3-criterios-paridade-monetaria.md);
- [22-handoff-implementacao-p1-p6.md](./22-handoff-implementacao-p1-p6.md).

`READY` neste documento significa requisito funcional fechado; não prova runtime nem libera gate de página sozinho.

## P1 — Cockpit da Competência

| RQ | Requisito | Aceite mínimo | Teste mínimo | Dependência | Estado |
|---|---|---|---|---|---|
| RQ-P1-01 | selecionar/identificar competência e contexto de empresa/unidade quando aplicável | contexto exibido e preservado em navegação/deep link sem criar permission por filial | positive + contexto alternativo + F5 | T05 | TARGET |
| RQ-P1-02 | mostrar eixos Estoque/Documentos/Pacote independentemente | mudança em um eixo não falsifica estado dos demais | positive + sibling | P2/P3/P5 | TARGET |
| RQ-P1-03 | mostrar blockers com motivo/source/ação | blocker material aparece sem percentual mascarando causa | positive + partial source | T01 | TARGET |
| RQ-P1-04 | source indisponível não pode virar zero/sucesso | estado PARTIAL/UNAVAILABLE_SOURCE explícito | negative | T01 | TARGET |
| RQ-P1-05 | P1 é leitura/composição, sem sacramentar/validar/enviar | ações proibidas não existem como authority de P1 | negative | boundaries | TARGET |
| RQ-P1-06 | histórico do fechamento navegável | eventos materiais aparecem com contexto | positive | P2–P5 audit | TARGET |
| RQ-P1-07 | Help explica eixos, freshness e conclusão | usuário acessa Help contextual da página | UI/help check | feature help | TARGET |

## P2 — Checklist e Documentos

| RQ | Requisito | Aceite mínimo | Teste mínimo | Dependência | Estado |
|---|---|---|---|---|---|
| RQ-P2-01 | competência usa snapshot do template vigente na abertura | publicação nova não altera competência aberta | positive + sibling | P6 | PROVEN (CP03-P2, doc 100) |
| RQ-P2-02 | REQUIRED nunca pode N/A; CONDITIONAL pode conforme regra | tentativa inválida é rejeitada server-side | positive + negative | business rule | PROVEN (A2/Upload, doc 100) |
| RQ-P2-03 | ATTACHED != VALIDATED quando validation required | upload não produz ACCEPTED automaticamente | positive + negative | validator | PROVEN (A2/Upload, doc 100) |
| RQ-P2-04 | rejeição preserva versão e exige motivo estruturado | evidência rejeitada permanece histórica | positive + audit | E06 seed | PROVEN (A2/Upload, doc 100) |
| RQ-P2-05 | replacement cria nova validação | nova evidência não herda aceite antigo | positive + negative | — | PROVEN (A2/Upload, doc 100) |
| RQ-P2-06 | PER_ATTACHMENT e WHOLE_SET obedecem escopo de validação | rejeição parcial/conjunto seguem regra configurada | positive + sibling | config | PROVEN (A2/Upload, doc 100) |
| RQ-P2-07 | item excepcional é somente da competência | criação não altera template mestre | positive + sibling | T05 | PROVEN (A2/Upload, doc 100) |
| RQ-P2-08 | CANCELLED não é delete nem NOT_APPLICABLE | item cancelado sai da completude ativa e histórico permanece | positive + negative | — | PROVEN (A2/Upload, doc 100) |
| RQ-P2-09 | correção estrutural pós-execução cria nova revisão | request/review/audit separados; histórico preservado | positive + stale negative | MANAGE | PROVEN (A2/Upload, doc 100) |
| RQ-P2-10 | reversão de rejeição respeita nova versão | reversão é bloqueada quando replacement já existe | positive + negative | notification | PROVEN (A2/Upload, doc 100) |
| RQ-P2-11 | notificações seguem targets efetivos e histórico | reversão não apaga notificação anterior | positive | T02 | TARGET |
| RQ-P2-12 | Help explica requirement, validação, N/A, replacement e correção | conteúdo contextual disponível | UI/help check | feature help | PROVEN (A2/Upload, doc 100) |
| RQ-P2-13 | item `EXPECTED` não é documento entregue nem validado | UI/API nunca apresentam item esperado como entregue; estado inicial do snapshot é sempre `EXPECTED` | positive + negative + UI check | schema snapshot | PROVEN (CP03-P2/CP03-UX, doc 100) |
| RQ-P2-14 | item sem R-ID não ganha automação fictícia | `totvs_report_ref` nulo permanece nulo; proveniência honesta sem relatório inventado | negative + UI check | seed doc 59 | PROVEN (CP03-P2/CP03-UX, doc 100) |
| RQ-P2-15 | upload cria evidência `ATTACHED` vinculada a `(competence, item?)`, nunca valida | item permanece `EXPECTED`; estado criado é `ATTACHED`; sem autoaceite | positive + negative | doc 103 §4 | PROVEN (A2/Upload, doc 100) |
| RQ-P2-16 | metadado no Postgres e binário em volume persistente são par indissociável | arquivo sobrevive a recreate/mudança controlada; falha de persistência faz rollback do binário | integration + fault-injection | persistent-upload-storage.mdc | PROVEN (A2/Upload, doc 100) |
| RQ-P2-17 | substituição cria nova versão e preserva a anterior | versão substituída fica `SUPERSEDED` e referenciável; nunca deletada silenciosamente | positive + version history | doc 103 §4.2 | PROVEN (A2/Upload, doc 100) |
| RQ-P2-18 | download exige `access` efetivo + scope, sem URL pública | streaming autenticado; recurso fora do scope/competência retorna 404/403 | negative + cross-competence + cross-branch | doc 103 §5 | PROVEN (A2/Upload, doc 100) |
| RQ-P2-19 | `CANCELLED` preserva histórico e sai da listagem ativa | cancelamento não deleta arquivo/versões; documento cancelado permanece consultável no histórico | positive + negative | doc 103 §4.2 | PROVEN (A2/Upload, doc 100) |
| RQ-P2-20 | tipo/tamanho de arquivo é allowlist com conferência de conteúdo | MIME+extensão+magic bytes; `file_too_large`/`unsupported_media_type` tipados | negative por tipo | D-U2 doc 103 | PROVEN (A2/Upload, doc 100) |
| RQ-P2-21 | evidência em pacote submetido é imutável | `version_locked` em substituição/cancelamento após submissão P5 | negative + P5 sibling | doc 12/37 | TARGET |
| RQ-P2-22 | upload idempotente e concorrência segura | `idempotency_key`+`request_hash`+`UNIQUE` (padrão supplies-api; transporte/escopo = D-U7); `version_no` UNIQUE + OCC `revision`; replay não duplica evidência | idempotency + concurrent | doc 103 §4.1 + Adendo §B | PROVEN (A2/Upload, doc 100) |

### P2-Upload — critérios de aceite (AC) e escopo por slice

Contrato consolidado no doc 103, Adendo §B–§E (`CF-C3-P2-UPLOAD-DECISIONS-CONTRACT-CLOSURE-001`). SLICE-1 executado sob `CF-C3-P2-UPLOAD-IMPL-GO-001` (evidência por AC abaixo); SLICE-2 permanece `TARGET`.

**SLICE-1** (candidato ao primeiro GO de implementação: U1 upload, U2 list, U3 get, U4 download+audit):

| AC | Cobre RQ | Caso | Pós-condição verificável |
|---|---|---|---|
| AC-P2-UP-01 | RQ-P2-15 | happy: upload válido em item e em competência (D-U6) | documento `ATTACHED`, `version_no=1`, `link_kind` correto, item permanece `EXPECTED` |
| AC-P2-UP-02 | RQ-P2-15 | sibling: mesmo binário anexado a dois itens | dois documentos distintos (sem dedup por hash) |
| AC-P2-UP-03 | RQ-P2-15 | negative: `snapshot_item_id` de outra competência | 404; nenhuma gravação |
| AC-P2-UP-04 | RQ-P2-16 | happy: arquivo sobrevive a recreate do serviço | download retorna bytes idênticos ao sha256 registrado |
| AC-P2-UP-05 | RQ-P2-16 | negative: falha de persistência após write | binário removido (compensação); `persistence_unavailable` 503; zero metadado |
| AC-P2-UP-06 | RQ-P2-16 | negative: metadado sem binário | download `file_missing` 503 — nunca sucesso falso |
| AC-P2-UP-07 | RQ-P2-18 | happy: download autorizado emite `DOCUMENT_DOWNLOADED` | evento com ator UUID, versão, competência, `result=AUTHORIZED` (D-U3) |
| AC-P2-UP-08 | RQ-P2-18 | negative: sem `access` / cross-competence / cross-branch | 401/403/404 sem vazamento de existência; `result=DENIED` quando auditável |
| AC-P2-UP-09 | RQ-P2-20 | negative por tipo: ZIP-renomeado-xlsx, PDF truncado, arquivo vazio, extensão divergente do conteúdo, >25 MB mid-stream | `invalid_file_content`/`empty_file`/`content_type_mismatch`/`file_too_large`/`unsupported_media_type` tipados |
| AC-P2-UP-10 | RQ-P2-20 | negative: `original_name` com separadores/`..`/NUL | nome sanitizado; stored name UUID; traversal impossível |
| AC-P2-UP-11 | RQ-P2-22 | idempotency: replay idêntico com mesma `idempotency_key` (transporte = D-U7) | mesmo `document_id`, `deduplicated: true`, zero novo arquivo |
| AC-P2-UP-12 | RQ-P2-22 | negative: mesma key com payload divergente | `idempotency_conflict` 409 |
| AC-P2-UP-13 | RQ-P2-22 | concurrency: dois uploads com a mesma key | um vencedor; perdedor lê registro ou `idempotency_conflict` — nunca duplicata |
| AC-P2-UP-14 | segurança | service principal / Core indisponível | 403 / `rbac_unavailable` 503 — fail-closed |
| AC-P2-UP-15 | auditoria | mutações e download auditável | `actor_subject` UUID-only (hardening R2 preservado) |
| AC-P2-UP-23 | boundary | MFE consome só a BFF; sem URL pública/storage direto | structural test; download sempre stream autenticado |
| AC-P2-UP-24 | invariante | upload nunca produz `VALIDATED`/`ACCEPTED` | estados persistidos limitados a `ATTACHED\|SUPERSEDED\|CANCELLED`; item segue `EXPECTED` |

Cobertura SLICE-1 por requisito (positive/sibling/negative/security/postcondition conforme aplicabilidade): RQ-P2-15 → AC-01/02/03 · RQ-P2-16 → AC-04/05/06 · RQ-P2-18 → AC-07/08 · RQ-P2-20 → AC-09/10 · RQ-P2-22 → AC-11/12/13 · transversais segurança/auditoria/boundary/invariante → AC-14/15/23/24.

**Execução SLICE-1 (`CF-C3-P2-UPLOAD-IMPL-GO-001`)** — resultados reais de suíte; `TEST_NOT_RUN` explícito onde aplicável:

| AC | Estado | Evidência executada |
|---|---|---|
| AC-P2-UP-01 | PASS | `test_pg_closing_documents.py` (competence+item docs ATTACHED v1); item `EXPECTED` inalterado — nenhum caminho de mutação de estado do item existe |
| AC-P2-UP-02 | PASS | `test_same_binary_two_documents_no_collapse` — mesmo checksum em dois documentos distintos |
| AC-P2-UP-03 | PASS | service/PG `ItemNotFound` + route 404 — cross-competence nunca revela |
| AC-P2-UP-04 | TEST_NOT_RUN parcial | publish→resolve provado em `test_closing_document_storage.py`; recreate literal de container não executado — durabilidade = volume host mapeado (`docker-compose*.yml`) |
| AC-P2-UP-05 | PASS | `test_persistence_failure_compensates_binary` — binário removido, exceção propagada |
| AC-P2-UP-06 | PASS | `test_download_missing_binary_audits_failed_never_success` — `file_missing` 503 com `result=FAILED`/`phase=delivery`, nunca sucesso |
| AC-P2-UP-07 | PASS | `test_audit_upload_and_download_append_only` + `test_audit_download_denied_phase_classification` — `result` + `phase` distinguem autorização de entrega; sem claim de transferência concluída |
| AC-P2-UP-08 | PASS | routes: sem token 401, sem permissão 403, cross-competence 404 (`test_document_scoped_to_competence`); cross-branch: `branch_scope` do request × escopo herdado do item = 404 (`test_*outside_declared_scope*`, PG `test_list_documents_filters_by_request_scope`, `test_document_inherits_item_branch_scope`); DENIED auditável registrado |
| AC-P2-UP-09 | PASS | `test_closing_file_validation.py` — ZIP-renomeado, PDF truncado, vazio, divergência, oversize |
| AC-P2-UP-10 | PASS | `test_sanitize_original_name` + traversal guard em `test_resolve_and_traversal_guard` |
| AC-P2-UP-11 | PASS | routes replay `deduplicated` + PG `test_idempotent_replay_same_hash` — zero segundo documento |
| AC-P2-UP-12 | PASS | `test_same_key_divergent_hash_conflict` — `idempotency_conflict` 409 |
| AC-P2-UP-13 | PASS | `test_concurrent_same_key_single_winner` — 4 threads, um vencedor, UNIQUE no banco |
| AC-P2-UP-14 | PASS | routes: service principal 403, `rbac_unavailable` 503 — fail-closed |
| AC-P2-UP-15 | PASS | routes: ator não-UUID 401; `actor_subject` UUID nas colunas PG |
| AC-P2-UP-23 | PASS | `apiBoundary.structural.test.mjs` + MFE consome só `documentsApi`/`httpClient` da BFF; download sempre stream autenticado |
| AC-P2-UP-24 | PASS | CHECK constraint `state IN (ATTACHED\|SUPERSEDED\|CANCELLED)`; MFE afirma «anexado ≠ validado»; zero mutação de item |

**SLICE-2** (U5 substituição, **U6 histórico de versões**, U7 cancelamento, U8 eventos de auditoria; depende do aceite do slice 1):

| AC | Cobre RQ | Caso | Pós-condição verificável |
|---|---|---|---|
| AC-P2-UP-16 | RQ-P2-17 | happy: replace cria v2 | v1 `SUPERSEDED` e referenciável; v2 `ATTACHED`; histórico íntegro |
| AC-P2-UP-17 | RQ-P2-17 | negative: replace por não-uploader sem `manage` (D-U1) | 403 — nem `access` genérico substitui |
| AC-P2-UP-18 | RQ-P2-17 | sibling: `manage` elegível substitui | permitido; evento registra ator distinto do uploader |
| AC-P2-UP-19 | RQ-P2-19 | happy: cancel | `CANCELLED`, sai da listagem ativa, histórico/arquivos preservados (`CANCELLED != DELETED`) |
| AC-P2-UP-20 | RQ-P2-21 | negative: replace/cancel após submissão P5 | `version_locked`/`document_locked` 409; pacote imutável |
| AC-P2-UP-21 | RQ-P2-22 | concurrency: replaces simultâneos | um vencedor por OCC `revision`; perdedor `stale_revision` 409 — nenhuma versão perdida |
| AC-P2-UP-22 | retenção | D-U4: v1 não deleta nada | housekeeping só atinge `.part`/órfãos sem metadado, nunca evidências registradas |

**Execução SLICE-2 (`CF-C3-P2-UPLOAD-SLICE2-IMPL-GO-001`)** — resultados reais de suíte; `TEST_NOT_RUN` explícito onde aplicável:

| AC | Estado | Evidência executada |
|---|---|---|
| AC-P2-UP-16 | PASS | PG `test_add_version_supersedes_previous` + `test_version_rows_never_updated` — v2 `ATTACHED`, v1 `SUPERSEDED` derivada (linha jamais UPDATEada — V004) e baixável, `current_version_no=2`, `VERSION_ADDED` append-only; binário anterior intocado |
| AC-P2-UP-17 | PASS | service `test_replace_by_non_uploader_without_manage_forbidden` (`Forbidden` 403, sem escrita) + route `test_replace_typed_errors`; `access` genérico não substitui |
| AC-P2-UP-18 | PASS | service `test_replace_by_eligible_manage_allowed` + route `test_replace_manage_user_gets_can_manage` — ator gestor registrado no `VERSION_ADDED`; `manage` sem `access` 403 (`test_replace_without_access_is_403`) |
| AC-P2-UP-19 | PASS | PG `test_cancel_preserves_history_and_exits_active_list` — sai da listagem ativa (filtro padrão), consultável via U3/U6, `document_file`/`document_version` intactos, `DOCUMENT_CANCELLED` único (`test_cancel_twice_is_typed_conflict`) |
| AC-P2-UP-20 | TEST_NOT_RUN | Nenhum runtime P5 existe no HEAD — não há estado de submissão canônico a consultar; `version_locked`/`document_locked` permanecem reservados no contrato e a trava ativa quando a fonte P5 existir (boundary documentado, sem permissividade inventada) |
| AC-P2-UP-21 | PASS | PG `test_concurrent_replace_single_winner` (4 threads, `FOR UPDATE`+`revision`: 1 vencedor, 3 `stale_revision`) + `test_concurrent_same_key_replace_deduplicates` (mesma key: 1 criador + 3 dedup, zero stale, um `VERSION_ADDED`); service `test_replace_stale_revision_fails_before_write` + `test_replace_idempotent_replay_deduplicates` (dedup resolve antes do OCC — replay com revision obsoleta ⇒ 200) |
| AC-P2-UP-22 | PASS | Sem `DELETE` nem UPDATE em `document_version` (V004 — estado derivado); cancel é UPDATE só no documento; compensação remove binário novo órfão inclusive em dedup de corrida (`test_replace_race_lost_compensates_published_binary`); `.part` descartado em toda rejeição |


**A2 — validação humana P2** (`CF-PROC0072-E2E-MASTER-EXECUTION-001`, Pacote A; decisões append-only em `evidence_decision`, V005; rotas `validations_routes.py`):

| AC | Cobre RQ | Estado | Evidência executada |
|---|---|---|---|
| AC-P2-VAL-01 | RQ-P2-02 | PASS | PG `test_na_required_item_blocked` + `test_na_conditional_and_revert` + route `test_mark_na_required_item_409`/`test_mark_na_conditional_200` — `not_applicable_not_allowed` 409; `ITEM_MARKED_NA`/`ITEM_NA_REVERTED` auditados |
| AC-P2-VAL-02 | RQ-P2-03 | PASS | upload nunca cria decisão; `evidence_decision` só existe via rota de decisão — item permanece `EXPECTED` após anexar (invariante preservada de AC-P2-UP-24) |
| AC-P2-VAL-03 | RQ-P2-04 | PASS | PG `test_decisions_are_append_only` + `test_reject_requires_structured_reason_db` — decisões crescem append-only; versão rejeitada permanece referenciável; `EVIDENCE_REJECTED` com `reason_code`/`comment`; `test_decide_version_other_reason_requires_comment` |
| AC-P2-VAL-04 | RQ-P2-05 | PASS | PG `test_reject_then_replace_requires_new_validation` + `test_replace_on_accepted_item_reopens_validation` + `test_whole_set_accept_then_replace_reopens` — substituição/cancelamento rebaixa `ACCEPTED`→`EXPECTED` e decisão antiga não cobre `version_no` novo |
| AC-P2-VAL-05 | RQ-P2-06 | PASS | PG `test_accept_attachment_derives_item_accepted` + `test_whole_set_accept_then_replace_reopens`/`test_whole_set_reject_with_reason` + route `test_per_attachment_route_on_whole_set_item_mismatch`/`test_decide_version_scope_mismatch_409` — PER_ATTACHMENT decide por versão; WHOLE_SET compara composição `document_id:version_no` exata |
| AC-P2-VAL-06 | RQ-P2-07 | PASS | PG `test_exceptional_item_only_in_competence` + route `test_create_exceptional_item_201`/`test_create_exceptional_item_access_only` — `snapshot` ganha item `exceptional` sem tocar template mestre; outra competência não vê o item |
| AC-P2-VAL-07 | RQ-P2-08 | PASS | PG `test_cancel_item_without_evidence` + route `test_cancel_item_200`/`test_cancel_item_with_evidence_409` — `CANCELLED` sai da completude ativa, decisões/documentos íntegros, `item_cancelled` 409 em decisão posterior; `CANCELLED != DELETED` |
| AC-P2-VAL-08 | RQ-P2-09 | PASS | PG `test_correction_request_approve_new_revision`/`test_correction_reject_requires_reason`/`test_correction_stale_after_another_approval` + route `test_request_correction_201`/`test_review_correction_approve_200`/`test_review_correction_stale_revision_409` — request ACCESS → review MANAGE → APPROVE gera `revision` nova; request/review são eventos distintos; revisão de correção inexistente `no_correction_pending` 409 |
| AC-P2-VAL-09 | RQ-P2-10 | PASS | PG `test_reversal_blocked_by_newer_version` + route `test_reverse_blocked_by_newer_version` — `replacement_requires_revalidation` 409; reversão só do mesmo validador (`test_reversal_same_validator_only`/`test_reverse_requires_same_validator`) com justificativa → `UNDER_REVIEW`/`ACCEPTED` |
| AC-P2-VAL-10 | segurança | PASS | route: sem token 401, sem `access` 403, cross-competence/cross-branch 404 (`test_decide_version_item_out_of_scope_404`, PG `test_item_out_of_declared_scope_404`); MANAGE para revisão de correção; ator não-UUID 401 |
| AC-P2-VAL-11 | auditoria | PASS | `EVIDENCE_ACCEPTED`/`EVIDENCE_REJECTED`/`DECISION_REVERSED`/`ITEM_MARKED_NA`/`ITEM_CANCELLED`/`CORRECTION_*` append-only em `closing_audit_event` (PG `test_validation_events_in_audit`) + `evidence_decision` sem UPDATE (`test_decisions_are_append_only`) |
| AC-P2-VAL-12 | frontend | PASS | `ItemValidationPanel.test.tsx` (10) — badges de decisão, rejeição com motivo+comentário «Outro», WHOLE_SET decide conjunto, reversão, N/A condicional, correção request/review, erro tipado 403; `ClosingDocumentsPanel` valida evidência de competência sem item |
| AC-P2-VAL-13 | RQ-P2-12 | PASS | `helpTooltips.ts` — `checklist.validation` (anexado≠validado, motivos, reversão, revalidação pós-substituição), `checklist.state` (novos estados), `checklist.exceptionalItem` |

Cobertura A2 por requisito: RQ-P2-02 → VAL-01 · RQ-P2-03 → VAL-02 · RQ-P2-04 → VAL-03 · RQ-P2-05 → VAL-04 · RQ-P2-06 → VAL-05 · RQ-P2-07 → VAL-06 · RQ-P2-08 → VAL-07 · RQ-P2-09 → VAL-08 · RQ-P2-10 → VAL-09 · RQ-P2-12 → VAL-13. RQ-P2-11 (notificações) permanece `TARGET` — dependência T02 fora do escopo A2.

## P3 — Estoque, Cutoff e Conciliação

| RQ | Requisito | Aceite mínimo | Teste mínimo | Dependência | Estado |
|---|---|---|---|---|---|
| RQ-P3-01 | cutoff requer confirmação humana autorizada | estabilidade aparente não confirma cutoff automaticamente | positive + negative | T05 | TARGET |
| RQ-P3-02 | pós-cutoff revalida P7, Entradas/Saídas, H02 e conciliação | readiness usa resultado revalidado | positive | T01 | TARGET |
| RQ-P3-03 | paridade monetária é exatamente R$ 0,00 | qualquer valor não zero bloqueia READY_TO_CLOSE | AC-P3-PARITY-01..07 | T01 | TARGET |
| RQ-P3-04 | zero pré-cutoff não é final | permanece PRELIMINARY/WAITING conforme state | negative | — | TARGET |
| RQ-P3-05 | source obrigatório indisponível não vira zero | readiness bloqueada e indisponibilidade explícita | negative | T01 | TARGET |
| RQ-P3-06 | input alterado após revalidação invalida prontidão aplicável | estado volta a requerer revalidação | positive + sibling | source version/freshness | TARGET |
| RQ-P3-07 | V1 não grava sacramentação no ERP | nenhuma action de escrita ERP é criada | architecture negative | E03/T03 | TARGET |
| RQ-P3-08 | STOCK_CLOSED usa estado canônico do owner se existir | sem fallback manual silencioso | integration/contract | T03 | TARGET / STOP_CONDITION |
| RQ-P3-08A | STOCK_CLOSED é terminal no lifecycle P3 do Portal V1 | sem reabrir/desfazer/retificar localmente; correção posterior pertence ao owner e não reescreve histórico | negative + lifecycle + P5 sibling | E02 CLOSED | TARGET / PRODUCT_DECISION |
| RQ-P3-09 | freshness/proveniência acompanham resultado | source/time/competência/unidade/finality/rule version disponíveis | contract/UI | T01 | TARGET |
| RQ-P3-10 | Help explica cutoff, revalidação, paridade e estado canônico | conteúdo contextual disponível | UI/help check | feature help | TARGET |

## P4 — Classificações e Pendências

| RQ | Requisito | Aceite mínimo | Teste mínimo | Dependência | Estado |
|---|---|---|---|---|---|
| RQ-P4-01 | regra determinística/IA pode sugerir classificação | sugestão não altera ERP nem conclui decisão | positive + AI negative | T01 | TARGET |
| RQ-P4-02 | humano autorizado confirma classificação | decisão confirmada registra ator/evidência | positive + permission negative | T05 | TARGET |
| RQ-P4-03 | pendência usa state machine fechada | estado livre/inválido rejeitado | positive + negative | — | TARGET |
| RQ-P4-04 | claim/reassign preserva ownership history | responsável anterior/atual e timestamps auditados | positive + sibling | T05 | TARGET |
| RQ-P4-05 | DISMISSED exige justificativa e não substitui N/A | blocker real não pode ser ocultado por dismiss indevido | positive + negative | business rule | TARGET |
| RQ-P4-06 | sem SLA/overdue no target | UI mostra pending_since/idade factual sem atraso formal | UI negative | — | TARGET |
| RQ-P4-07 | boundary com Portal Financeiro P0 é preservado | P4 não reutiliza despesas CC como authority automática | architecture review | 21-boundaries | TARGET |
| RQ-P4-08 | Help explica sugestão, owner, states e dismiss | conteúdo contextual disponível | UI/help check | feature help | TARGET |

## P5 — Pacote, Finalização e Envio

| RQ | Requisito | Aceite mínimo | Teste mínimo | Dependência | Estado |
|---|---|---|---|---|---|
| RQ-P5-01 | PACKAGE_INCOMPLETE só avança quando requisitos aplicáveis permitirem | blockers impedem READY_TO_FINALIZE | positive + negative | P2/P3 | TARGET |
| RQ-P5-02 | Finalizar cria versão/snapshot e não submete | PACKAGE_FINALIZED sem reviewer access/task | positive | — | TARGET |
| RQ-P5-03 | reabrir antes da submissão preserva versão anterior | V1 histórica + working copy + V2 | positive + audit | — | TARGET |
| RQ-P5-04 | pacotes são por destinatário dentro da mesma competência | submit/review de um destinatário não avança sibling | positive + sibling | recipients config | TARGET |
| RQ-P5-05 | Enviar significa submeter dentro da Minha DELPI | PACKAGE_SUBMITTED_FOR_REVIEW; nenhum package attachment por e-mail | positive + architecture negative | doc 37 | TARGET |
| RQ-P5-06 | reviewer autenticado é autorizado por Core e P5 | ACCESS efetivo via Core AND elegibilidade por área/função AND PackageVersion atual AND assignment/resource scope AND regra de negócio; MANAGE isolado não basta | authz positive + sibling + negative | Core/T05 / P5-C / doc 37 | TARGET / T05_TO_INVENTORY |
| RQ-P5-07 | notifications não são business state | in-app + e-mail opcional; falha de e-mail não reverte submission | integration + sibling | T02/Core | TARGET |
| RQ-P5-08 | reviewer work pode projetar em Minhas tarefas | self-only projection; deep link abre P5 owner | projection + authz | TSK | TARGET |
| RQ-P5-09 | versão submetida/histórico de review são imutáveis | nova versão não apaga review anterior | positive + audit | — | TARGET |
| RQ-P5-10 | clarification/correction preserva history | request/response/version ficam auditáveis | positive + sibling | — | TARGET |
| RQ-P5-11 | Help explica finalize/submit/notify/review | conteúdo contextual coerente | UI/help check | feature help | TARGET |
| RQ-P5-12 | conclusão mensal C2 depende de aceites humanos reais por pacote/área/versão | todos os pacotes aplicáveis submetidos; cada pacote tem aceite humano real, válido e auditado na PackageVersion atual; cada área obrigatória existente está aceita; nenhuma clarification aberta; competência rejeitada nunca é concluída; sem reviewers => pendente, sem bloqueio extra de envio | positive + sibling + negative + zero-area/zero-reviewer + version | C2 / P5-A / P5-E / D-FINAL-02 | TARGET / PO_APPROVED / TEST_NOT_RUN |
| RQ-P5-AREA-01 | quorum por área e não por pessoa | dois usuários elegíveis da mesma área não exigem dois aceites; área não aceita bloqueia C2 | positive + sibling + concurrency | P5-A/C / Core T05 | TARGET / PHYSICAL_BINDING_TO_INVENTORY |
| RQ-P5-AREA-02 | nova versão não herda aceites | nova PackageVersion exige novos aceites de todas as áreas e preserva histórico de versão anterior | positive + sibling + negative | P5-E / D-P5-02 | TARGET / PO_APPROVED |
| RQ-P5-AREA-03 | reatribuição preserva aceite válido e autoria | substituição de usuário não altera/atribui retroativamente aceite já dado; substituto só age depois da atribuição autorizada | positive + sibling + audit | P5-F/B / DEC-03 | TARGET / PO_APPROVED |
| RQ-P5-AREA-04 | eligibility e AuthZ fail-closed | ACCESS efetivo + grupo/função elegível + scope + regra da ação; ACCESS isolado, MANAGE isolado e Core indisponível não autorizam aceite | positive + sibling + negative | P5-C / Core T05 | TARGET / CORE_ATTRIBUTE_CONTRACT_TO_INVENTORY |
| RQ-P5-AREA-05 | ausência de revisor ou de áreas não cria aceite automático nem bloqueio extra de envio | pacote segue para revisão mesmo sem pessoa elegível; fica pendente até existir aceite humano real da versão atual; configuração vazia nunca completa C2 por vacuidade; respeitar quorum por área existente | positive + sibling + negative (zero área; zero revisor; ausência temporária; aceite posterior; nova versão) | D-FINAL-02 PO 19/10/2026 / C2 / P5-A/H | TARGET / PO_APPROVED / TEST_NOT_RUN |
| RQ-P5-AREA-06 | identidade/permissões e vínculo de revisor têm owner Core | Core API gerencia RBAC/effective permissions; Portal CF não cria/revoga permission; BFF usa contrato S2S autorizado para eligibility + business scope, falhando fechado; sem associação corporativa tipada provada no S2S atual | S2S producer/consumer positive+sibling+negative após inventory | D-FINAL-01 / P5-C / Core T05 | TO_INVENTORY / CONTRACT_PENDING |
| RQ-P5-TERM-01 | rejeição de área não rejeita competência automaticamente | resultado da área gera proposta pendente; somente coordenador formal com ACCESS e vínculo/scope confirma com motivo | positive + negative + audit | P5-I / DEC-01/02 | TARGET / PHYSICAL_BINDING_TO_INVENTORY |
| RQ-P5-TERM-02 | rejeição terminal interrompe ações pendentes | competência rejeitada não conclui C2; TaskProjection deixa de ser acionável, histórico/auditoria preservados | positive + sibling + negative | P5-D/J | TARGET / PO_APPROVED |
| RQ-P5-TERM-03 | aceite P5 irreversível na V1 | não há API nem botão de reversão/retificação; P2 validação de evidência tem fluxo independente | negative + boundary + audit | P5-G / DEC-03 | TARGET / PO_APPROVED |
| RQ-P5-F | Reatribuição preserva aceite por área/versão | aceite original continua válido; autoria não muda; novo elegível assume ações futuras | positive + sibling + audit | P5-F / Core T05 | TARGET |
| RQ-P5-G | Aceite P5 irreversível pela UI **e pela API** V1 | nem autor nem substituto conseguem editar/reverter por endpoint ou tela; incidentes fora do Portal V1 | negative endpoint + UI + audit | P5-G / DEC-03 | TARGET / PO_APPROVED |
| RQ-P5-H | P6 versiona áreas obrigatórias por tipo e P5 congela na submissão | mudança P6 posterior não muda revisão aberta | snapshot + sibling + negative | P5-H / ADM / T05 | TARGET / CONTRACT_PENDING |
| RQ-P5-I | Rejeição do pacote e confirmação terminal da competência separadas | rejeição por área não conclui nem encerra automaticamente; coordenador formal com ACCESS/vínculo/scope confirma com motivo; sem confirmação mantém pendência | positive + sibling + transitions + authz negative | P5-I / DEC-01/02 / Core T05 | TARGET / PO_APPROVED / PHYSICAL_BINDING_TO_INVENTORY |
| RQ-P5-J | Rejeição terminal remove acionabilidade das tasks | projections deixam de ser acionáveis, histórico não é apagado | positive + sibling + negative | P5-J / TSK | TARGET |

## P6 — Administração e Configuração

| RQ | Requisito | Aceite mínimo | Teste mínimo | Dependência | Estado |
|---|---|---|---|---|---|
| RQ-P6-01 | template segue DRAFT→REVIEW→PUBLISH→EFFECTIVE_FROM | salvar draft não publica | positive + negative | MANAGE | PROVEN (A3, doc 100 — ciclo atual DRAFT→PUBLISHED sem etapa REVIEW separada) |
| RQ-P6-02 | publicação não altera snapshot de competência aberta | competência continua na versão original | positive + sibling | P2 snapshot | PROVEN (CP03-P2 + A3, doc 100) |
| RQ-P6-03 | inativação é prospectiva e sem delete físico | histórico continua referenciável | positive + negative | audit | PROVEN (A3, doc 100) |
| RQ-P6-04 | ACCESS usa opções; MANAGE administra catálogos | ACCESS não altera mestre | permission negative | T05 | PROVEN (A3 — ACCESS→403 em todas as rotas admin, doc 100) |
| RQ-P6-05 | bancos/contas são configuráveis, não hardcoded | seed pode mudar sem diff de regra | config test | E01 | TARGET |
| RQ-P6-06 | motivos de rejeição = núcleo + extensões | inativação preserva códigos históricos | positive + sibling | E06 | TARGET |
| RQ-P6-07 | attachment roles são catalogados com genérico quando permitido | role obrigatório/configurado respeitado | positive + negative | E05 | TARGET |
| RQ-P6-08 | notification targets usam opções governadas | targets inválidos não são free-form | positive + negative | T02 | TARGET |
| RQ-P6-09 | MANAGE efetivo **AND** escopo administrativo publica configuração versionada | um publicador autorizado, motivo/audit e vigência prospectiva; segundo MANAGE não é requisito; ACCESS isolado e MANAGE sem scope falham | positive + sibling + permission/scope negative | T05 / DEC-04 / P5-H | PROVEN (A3, doc 100) |
| RQ-P6-10 | Help explica draft/publish/effective_from/snapshot/inativação | conteúdo contextual disponível | UI/help check | feature help | PROVEN (A3 — `CF_HELP.admin.*`) |

## Superfícies da topbar

| RQ | Requisito | Aceite mínimo | Teste mínimo | Dependência | Estado |
|---|---|---|---|---|---|
Fonte detalhada do Início: [32-inicio-home.md](./32-inicio-home.md).

| RQ-NAV-01 | topbar contém exatamente Início, Visão geral, Sala de interação, Minhas tarefas, Administração e Ajuda | ordem/conjunto canônico sem item de P1–P5 na topbar | navigation + mobile + keyboard | 24 | TARGET |
| RQ-HOME-01 | Início usa Home family comum dos Portais | TopBar + Hero + Eventos + launcher/recentes; zero redesign local | visual/component + mobile/dark | plugin-ui + 32 | TARGET |
| RQ-HOME-02 | Hero é operacional, não analítico | Competência ativa + Minhas tarefas + Blockers; indicadores financeiros ficam na Visão geral | positive + source partial | H02/H03/H04 | TARGET |
| RQ-HOME-03 | Eventos degradam independentemente | tasks/alerts podem falhar sem derrubar catálogo; sem SLA inventado | positive + partial + negative | H02/H04 | TARGET |
| RQ-HOME-04 | catálogo mostra somente runtime implementado + autorizado | P1–P5 entram page-by-page; Administração só MANAGE; profile fora do launcher | positive + route/permission negative | router/Core | TARGET |
| RQ-HOME-05 | busca local usa catálogo e deep link ?q= | F5 preserva query; rota sem acesso não aparece | search + F5 + permission negative | router/catalog | TARGET |
| RQ-HOME-06 | recentes são efêmeros e seguros | máx. 5; stale/unauthorized filtrado; sem dado financeiro/PII | storage + corruption negative | local UI state | TARGET |
| RQ-HOME-07 | favoritos sincronizam estrela e TopBar | falha save faz rollback; persistência física somente após H01 | positive + backend failure + stale | H01 | TO_INVENTORY |
| RQ-HOME-08 | Home preserva light/dark/mobile/a11y | mesmos componentes/tokens; teclado/foco; estado não só por cor | visual/a11y | plugin-ui | TARGET |
| RQ-HOME-09 | Help explica Home | Home vs Overview, eventos, busca, recentes e favoritos documentados quando runtime existir | help sync | feature-help-sync | TARGET |
| RQ-TASK-01 | Minhas tarefas usa workspace comum | `TaskWorkspacePage` + task primitives; zero clone/CSS local | visual/component + mobile/dark | plugin-ui + 27 | TARGET |
| RQ-TASK-02 | TaskProjection não é task entity | sem create/edit/complete/cancel/defer/reassign genérico; owner state não é copiado | architecture + negative | D-TASK-01/02 | TARGET |
| RQ-TASK-03 | worklist é self-only | `/me/tasks`; sem user selector/team scope; MANAGE não implica team | permission/privacy negative | Core + D-TASK-03 | TARGET |
| RQ-TASK-04 | producer exige obrigação governada | P2/P4 conforme owner; P5 gera projection self-only por área para cada usuário elegível quando review acionável; blocker/mention não cria task | positive + sibling + negative | TSK01 / doc 37 / P5-A/C | TARGET / PHYSICAL_BINDING_TO_INVENTORY |
| RQ-TASK-05 | ação V1 abre owner | deep link seguro; owner reautoriza; nenhuma ação de negócio local | navigation + stale item | TSK03 | TARGET |
| RQ-TASK-06 | sem SLA global | sem Atrasadas/Hoje/Depois; due/overdue só owner-provided; pendingSince factual | negative due/SLA | D-TASK-04 | TARGET |
| RQ-TASK-07 | partial coverage é honesta | source failure preserva siblings; count não parece total; empty só COMPLETE | partial + source failure | TSK04 | TARGET |
| RQ-TASK-08 | filtros são shareable | source/competence/q em URL; F5; sem user override/open redirect | URL roundtrip + negative | TSK03 | TARGET |
| RQ-TASK-09 | Home reusa a mesma projeção | summary/count seguem coverage; nenhuma regra duplicada | contract sibling | Home H02 | TARGET |
| RQ-TASK-10 | Sala não cria task na V1 | `onCreateTask` oculto; message/mention não geram TaskProjection | interaction negative | D-TASK-07 | TARGET |
| RQ-TASK-11 | light/dark/mobile/a11y seguem kit | mesmos componentes/tokens; teclado/foco; tabela responsiva | visual/a11y | plugin-ui/TSK05 | TARGET |
| RQ-TASK-12 | Help sincronizada | explica projection/owner/no-SLA/no-free-task e só producers implementados | help sync | feature-help-sync | TARGET |

| RQ-ROOM-01 | Sala usa full-page comum | `InteractionRoomPage` como canvas; zero clone local | visual/component + mobile/dark | plugin-ui + 26 | TARGET |
| RQ-ROOM-02 | Sala é sempre contextual | sem wall/global room/criação livre; somente context registry | positive + invalid context negative | context registry | TARGET |
| RQ-ROOM-03 | uma sala por contexto | resolve idempotente; concorrência não duplica; título derivado | concurrency + contract | persistence future | TARGET |
| RQ-ROOM-04 | AuthZ depende do contexto | ACCESS + context access; member/mention não concede acesso | permission/resource negative | Core + owners | TARGET |
| RQ-ROOM-05 | conversa não muda business state | comment/reaction/pin não validam, aprovam, fecham ou enviam | negative business-state | P1–P5 | TARGET |
| RQ-ROOM-06 | edit/delete preservam histórico | autor edita própria text; delete é soft; system imutável | positive + negative author | message policy | TARGET |
| RQ-ROOM-07 | attachment de chat não é evidência P2 | evidence exige ação owner explícita | boundary negative | P2 | TARGET |
| RQ-ROOM-08 | mentions respeitam acesso | suggestion server-side; target permitido; mention não concede scope | privacy/resource negative | Core directory + context | TARGET |
| RQ-ROOM-09 | realtime é degradável | transport failure vira banner/partial, não perda total de chat | degraded/reconnect | R03 | TARGET |
| RQ-ROOM-10 | notifications usam capability canônica | mention notifica; sem SMTP/preferences local | integration negative | R04/T02 | TARGET |
| RQ-ROOM-11 | criar tarefa não existe na V1 | `onCreateTask` oculto; message/mention não geram TaskProjection | interaction negative | Item 5 / D-TASK-07 | TARGET |
| RQ-ROOM-12 | Help sincronizada | contexto, mensagem vs ação, attachments, mentions, edit/delete explicados no runtime | help sync | feature-help-sync | TARGET |

| RQ-OVW-01 | Visão geral usa Overview family comum | Hero compacto + período/filtros + KPI grid + charts | visual/component + mobile/dark | plugin-ui + 25 | TARGET |
| RQ-OVW-02 | indicador é governado por owner/source/fórmula | nenhum KPI sem metadata mínima; indisponível != zero | positive + source failure | D-OVW-01=C + O04 | TARGET |
| RQ-OVW-03 | filtros são shareable por URL | F5 reconstrói recorte; unidade é dimensão de dado | URL roundtrip + F5 | D-OVW-02=A + D-OVW-03=A | TARGET |
| RQ-OVW-04 | blocos degradam isoladamente | source failure de um indicador não derruba siblings | partial + sibling | contracts físicos | TARGET |
| RQ-OVW-05 | gráfico segue semântica do indicador | sem baseline/fórmula inventada; chart do kit | component + negative | indicator contract | TARGET |
| RQ-OVW-06 | drilldown é rastreável | preserva filtros e explica o número pelo mesmo owner/source | positive + deep link | route/contract | TARGET |
| RQ-OVW-07 | strategic scores vêm do owner | IDD/IGD não são recalculados no Portal; partial explícito | contract + negative | D-OVW-01=C / strategic-indicators-api | TARGET |
| RQ-OVW-08 | AuthZ usa ACCESS/MANAGE sem proliferation | ACCESS necessário; MANAGE não implica ACCESS; sem permission por indicador/unidade | permission negative | Core | TARGET |
| RQ-OVW-09 | light/dark/mobile/a11y seguem padrão comum | mesma ordem/DOM conceitual, tokens e teclado/foco | visual/a11y | plugin-ui | TARGET |
| RQ-OVW-10 | Ajuda acompanha indicadores aprovados | significado/fórmula/source/freshness/deep links sincronizados | help sync | feature-help-sync | TARGET |
| RQ-INT-01 | Sala de interação é contextual e não muda estado de negócio por mensagem | mensagem/comentário não valida, aprova, fecha estoque ou envia pacote | positive + resource negative | interaction contract inventory | CONTRACT_INVENTORY_REQUIRED |
| RQ-ADM-01 | Administração exige somente MANAGE | ACCESS sozinho não altera mestre; nenhum permission code adicional | positive + permission negative | Core effective permissions | TARGET |
| RQ-ADM-02 | IA administrativa é Painel/Templates/Catálogos/Histórico | catálogos não viram topbar/permission; deep links preservados | navigation + F5 | router + 28 | TARGET |
| RQ-ADM-03 | template segue lifecycle canônico | DRAFT→REVIEW→PUBLISH→EFFECTIVE_FROM; save != publish; published immutable | positive + transition negative | P6 | PROVEN (A3 — publicada imutável; REVIEW não modelado neste ciclo) |
| RQ-ADM-04 | snapshot não sofre retroatividade | nova publicação não altera competência aberta/histórico | positive + sibling | P2 snapshot | PROVEN (CP03-P2 + A3) |
| RQ-ADM-05 | catálogos são tipados | registry explicita schema/validation; sem free-form generic CRUD | contract + invalid field negative | ADM01 | TARGET |
| RQ-ADM-06 | inativação é prospectiva | sem hard delete; reason/actor/time/effective date; histórico interpretável | positive + delete negative | audit | PROVEN (A3) |
| RQ-ADM-07 | identidades permanecem no Core | selectors usam referências elegíveis; nenhum user/role/permission write | integration + security negative | ADM06/Core | TARGET |
| RQ-ADM-08 | notification target não é delivery engine | targets lógicos; Minha DELPI entrega; sem SMTP/preferences local | integration negative | ADM05/T02 | TARGET |
| RQ-ADM-09 | writes tratam concorrência | stale revision rejeitada; sem overwrite silencioso | stale/concurrency negative | ADM07 | PROVEN (A3 — OCC `revision`, `stale_revision` 409; teste PG `test_stale_revision_rejected`) |
| RQ-ADM-10 | histórico administrativo é auditável/read-only | actor/time/entity/action/before-after/reason/effective/version | positive + immutable negative | audit store | PROVEN (A3 — `GET …/events` append-only) |
| RQ-ADM-11 | Administração é plugin-ui first | primitives públicos; zero design-system local; mobile/dark/a11y | component + visual/a11y | plugin-ui | PROVEN (A3 — página usa kit/compartilhados `cf*`) |
| RQ-ADM-12 | Help acompanha P6 | lifecycle/snapshot/inativação/catálogos ensinados somente quando implementados | help sync | feature-help-sync | PROVEN (A3) |
| RQ-ADM-13 | base de publicação é o vencedor do boundary | versão de maior número não pode ser base; desempate eff/version igual ao backend | positive + out-of-order negative | resolve_published_version | PROVEN (UX-012-RW01 — winnerAt + planDocumentSave) |
| RQ-ADM-14 | alteração de exigência propaga a boundaries futuros | item inserido/editado no meio da timeline não morre no boundary seguinte | positive + overlap sibling | planDocumentSave | PROVEN (UX-012-RW01 — teste multi-boundary) |
| RQ-ADM-15 | publicação multi-passo é idempotente e honesta | retry não duplica; falha intermediária nunca informa sucesso; rascunho igual retomado, divergente é conflito | retry + failure negative | ensurePublishedVersion | PROVEN (UX-012-RW01 — testes de resume/conflito/no-op) |
| RQ-ADM-16 | encerrar última exigência tem semântica explícita | sem versão vazia fictícia nem documento sentinela; conflito com TARGET registrado | negative + decision | doc 114 (DR-2) | DECISION_REQUIRED (comparativo A vs B no doc 114 — recomendação A, aguarda PO) |
| RQ-ADM-17 | configuração documental início+fim é atômica | uma transação para janela completa | atomicity | doc 114 §10 | PASS — PUT requirement implementado; smoke local + PG tests |
| RQ-ADM-DR1-01 | configuração documental em transação única | falha em qualquer passo → rollback integral; zero versão parcial | atomicity + failure injection | doc 114 §10.3 | PASS — teste A (rollback) PG |
| RQ-ADM-DR1-02 | propagação server-side a boundaries | winner@b + item em cada boundary; remoção em until+1 | positive + overlap | doc 114 §10.3 | PASS — planner unit + PG |
| RQ-ADM-DR1-03 | concorrência serializada + idempotência | FOR UPDATE; base_version OCC; retry → replayed sem duplicar | concurrency + retry | doc 114 §10.3 | PASS — PG concurrency + smoke |
| RQ-ADM-DR1-04 | autorização e auditoria completas | MANAGE; evento por versão + DOCUMENT_CONFIG_APPLIED; retro ativo 422 | permission negative + audit | doc 114 §10.3 | PASS — rotas 403/401 + auditoria |
| RQ-ADM-DR2-01 | ausência de exigências sem documento fictício | sem-template (NULL) ≠ checklist vazio (versão publicada 0 itens); distinção auditável | decision + negative | doc 114 §10.3 | PASS — alternativa A aprovada (PO D2) e implementada |
| RQ-ADM-DR2-02 | consumers de snapshot inalterados | abertura, P2/P5, validações, pacotes, CLARA, histórico | compat suite | doc 114 §10.5 | PASS — suíte backend 689 verde |
| RQ-ADM-DR2-03 | versão vazia exige intenção explícita | publish/update com itens vazios só via `allow_empty`; sem documento-sentinela | contract negative | doc 114 §10 | PASS — 422 empty_resulting_checklist sem flag |
| RQ-ADM-DR1-05 | operação idempotente por chave | Idempotency-Key + request_hash; replay retorna resultado sem duplicar versão/auditoria; mesma chave + payload divergente → 409 | positive + conflict negative | doc 114 §10.2/§10.3 | PASS — V017 + smoke replay |
| RQ-ADM-DR1-06 | serialização de publicações | lock FOR UPDATE no template em writers novos e legados; ordem fixa; lock_timeout → 409 busy | concurrency + legacy interleave | doc 114 §10.3 | PASS — locks em publish/inactivate/create_draft/open_competence + testes |
| RQ-ADM-DR1-07 | janela nunca cobre competência aberta | window intersecting open competence → 422 window_covers_open_competence; correção via item excepcional | negative + sibling | doc 114 §10.3 | PASS — PG window_covers_open_competence |
| RQ-ADM-DR1-08 | trilha de auditoria equivalente ao lifecycle | DRAFT_CREATED→SUBMITTED→PUBLISHED por versão + DOCUMENT_CONFIG_APPLIED resumo dentro da transação | audit positive | doc 114 §10.3 | PASS — audit rows conferidas no banco |
| RQ-ADM-DR1-09 | `base_version` exigido e 409 no stale; replay da mesma operação concluída é determinístico sem duplicar | positive + conflict | doc 114 §10.1/§10.3 | PASS — smoke stale_revision + replayed |
| RQ-ADM-DR1-10 | publicação e abertura concorrentes não escapam de D3; 422 quando a competência já abriu, ou snapshot novo coerente quando abertura vem depois da publicação | concurrency | doc 114 §10.3 | PASS — open_competence trava templates + teste D PG |
| RQ-ADM-DR2-04 | `allow_empty` é intencional e auditado; último item pode terminar sem documento-sentinela, sem modificar snapshots anteriores | positive + audit | doc 114 §10.3 | PASS — smoke último item + audit DOCUMENT_CONFIG_APPLIED |
| RQ-ADM-DR1-11 | etapa REVIEW audita transições na mesma transação; rollback elimina também eventos de auditoria em falha | atomicity + audit | doc 114 §10.3 | PASS — eventos na tx única + teste A |
| RQ-HELP-01 | Ajuda usa manual canônico | `createDashboardUserManual` + PageHero/Path/SectionCard; zero chrome local | component + structural | plugin-ui + 29 | TARGET |
| RQ-HELP-02 | Ajuda é rota de topbar com ACCESS | `/help` funciona em F5; sem ACCESS = 403 | navigation + permission negative | router/manifest/Core | TARGET |
| RQ-HELP-03 | manual publica somente runtime real | feature/route futura não aparece nem vira link | route-disabled negative | feature catalog | TARGET |
| RQ-HELP-04 | conteúdo respeita capability | Administração só com MANAGE; sem permission nova | positive + permission sibling | Core effective permissions | TARGET |
| RQ-HELP-05 | Help contextual usa hash seguro | página abre seção correta; inválido não quebra; MANAGE hash não vaza conteúdo | deep-link + negative | HELP03 | TARGET |
| RQ-HELP-06 | guide table navega por registry tipado | Quero/Onde/Como; destinos existentes/autorizados; sem arbitrary URL | structural + navigation negative | HELP01 | TARGET |
| RQ-HELP-07 | conceitos preservam invariantes | ATTACHED!=VALIDATED, BLOCKER!=MY_TASK, Finalizar!=Enviar, ACCESS!=MANAGE, source error!=zero | content assertions | business contracts | TARGET |
| RQ-HELP-08 | Central de Fechamento acompanha slices reais | P1–P5 publicados somente com runtime autorizado; P5 explica submissão/revisão no Portal somente quando feature ativa; P3 zero tolerance | feature sibling + content negative | P1–P5 contracts | TARGET |
| RQ-HELP-09 | FAQ/glossário seguem terminologia vigente | nenhum termo stale; exemplos não viram regra | structural/content | terminology catalog | TARGET |
| RQ-HELP-10 | Help V1 não cria backend/CMS | conteúdo versionado no MFE; sem endpoint/table/editor | architecture negative | D-HELP-02 | TARGET |
| RQ-HELP-11 | light/dark/mobile/a11y seguem kit | mesmo conteúdo; TOC/nav semântico; teclado/foco | visual/a11y | plugin-ui | TARGET |
| RQ-HELP-12 | feature-help-sync é gate | mudança user-facing avalia/atualiza Help no mesmo slice | help sync + link check | feature-help-sync | TARGET |
| RQ-AUTHZ-01 | permissions do Portal são somente access e manage | nenhum permission code por página, CRUD, filial, unidade ou indicador | manifest/contract review | Core | TARGET |


## Página do usuário

| RQ | Requisito | Aceite mínimo | Teste mínimo | Dependência | Estado |
|---|---|---|---|---|---|
| RQ-USER-01 | perfil é deep route transversal, sem item novo de topbar | `/users/{userId}` funciona em deep link/F5; topbar permanece com 6 itens | navigation + F5 + mobile | foundation/router | TARGET |
| RQ-USER-02 | identidade corporativa vem do Core | Directory + Person Profile; zero tabela/migration/storage de perfil no Portal | contract + architecture negative | Core directory/person-profile | TARGET |
| RQ-USER-03 | viewer com ACCESS pode ver outro usuário do mesmo Portal | ACCESS positivo; target sem app access = 404; sem ACCESS = 403; nenhuma permission nova | positive + sibling + permission negative | Core app membership/effective permissions | TARGET |
| RQ-USER-04 | access/capabilities são self-only e D2 mostra label + código técnico | próprio perfil mostra somente `controllership-finance.access/manage` efetivos; outro perfil não expõe RBAC | positive + privacy negative | Core effective permissions | TARGET |
| RQ-USER-05 | edição de identidade pertence ao Meu Perfil | self CTA navega ao Meu Perfil da Minha DELPI; cargo/contatos e foto são editados pela Core API; BFF/MFE de Controladoria permanecem read-only e não criam proxy/form de write | navigation + architecture negative | host profile + Core person profile | TARGET |
| RQ-USER-06 | indisponibilidade de source não vira "Não informado" | Person Profile unavailable = PARTIAL; null real só quando source AVAILABLE; Directory failure = ERROR | partial + downstream negative | Core integrations | TARGET |
| RQ-USER-07 | perfil reutiliza full-page do `@delpi/plugin-ui` | `createDashboardPortalUserProfilePage`; zero clone/CSS do kit; tema/mobile/teclado | component/build + visual/a11y | plugin-ui | TARGET |
| RQ-USER-08 | atalhos refletem runtime + acesso do viewer, não roadmap | somente rota implementada e autorizada; Administração apenas com MANAGE | positive + route-not-implemented negative | manifest/router/effective permissions | TARGET |
| RQ-USER-09 | Ajuda acompanha a página | conteúdo só fica disponível quando a feature estiver implementada; deep links válidos | help sync + link check | feature-help-sync | TARGET |

Fonte detalhada: [31-pagina-do-usuario.md](./31-pagina-do-usuario.md).

## Requisitos transversais de segurança

| RQ | Requisito | Aceite mínimo | Teste mínimo | Dependência | Estado |
|---|---|---|---|---|---|
| RQ-SEC-01 | backend autoriza fail-closed | UI ocultar ação não concede autorização | negative: chamada direta sem capability/scope + Core unavailable | Core + BFF AuthZ | TARGET |
| RQ-SEC-02 | effective permissions vêm do Core | JWT sozinho não é authority final | contract/integration: JWT válido sem effective access não autoriza | Core PermissionResolver | TARGET |
| RQ-SEC-03 | resource ownership/context access sempre aplicados quando houver recurso restrito | URL direta para recurso não autorizado é rejeitada | sibling + negative: resource A/B + direct URL | owner adapter | TARGET |
| RQ-SEC-04 | MANAGE não apaga histórico | delete/overwrite material rejeitado | negative: hard delete/overwrite histórico | audit/version rules | TARGET |
| RQ-SEC-05 | IA respeita acesso/ownership e não muda estado | tool/prompt não contorna business rule | AI negative + permission negative | governed AI adapter | TARGET |
| RQ-SEC-06 | secrets/tokens não entram em frontend state/logs/prompts comuns | scanner/review sem exposição | secret/log/frontend-state scan | platform security | TARGET |

## Requisitos transversais de experiência

| RQ | Requisito | Aceite mínimo | Teste mínimo | Dependência | Estado |
|---|---|---|---|---|---|
| RQ-UX-01 | estados LOADING/SUCCESS/EMPTY/PARTIAL/UNAVAILABLE/ERROR/403/404 | página não colapsa estados distintos em erro genérico | state matrix + source unavailable negative | page contracts | TARGET |
| RQ-UX-02 | desktop/mobile e claro/escuro | conteúdo e ações materiais permanecem utilizáveis | visual/responsive: desktop + mobile + light + dark | plugin-ui/theme | TARGET |
| RQ-UX-03 | teclado/foco | fluxo principal operável por teclado com foco visível | keyboard-only + focus order/modal trap | plugin-ui/a11y | TARGET |
| RQ-UX-04 | deep link/F5 | contexto aplicável é preservado/reconstruído sem bypass de auth | deep-link roundtrip + F5 + unauthorized URL negative | router/BFF | TARGET |
| RQ-UX-05 | status não depende apenas de cor | labels/texto acessíveis | a11y/status semantics | plugin-ui | TARGET |
| RQ-UX-06 | Help sincronizada | mudança user-facing material atualiza ajuda antes do aceite | structural Help link/section + capability gating | 29/help registry | TARGET |

## Regra de evidência para implementação

Cada RQ material da página em execução deve aparecer no report do Cursor com:
- status;
- arquivo/contrato que implementa;
- teste positive;
- sibling quando aplicável;
- negative;
- evidência do HEAD final;
- residual/unresolved.

Nenhum RQ pode ser marcado PASS apenas porque outro RQ da mesma página passou.

**Decisões P5 vigentes:** [37 — contrato canônico de revisão, C2, P5-A..J e DEC-01..04](./37-p5-submissao-e-revisao-no-portal.md). RQ/AC em [23](./23-ledger-rq-ac-testes.md); histórico de gates não é contrato ativo. `IMPLEMENTATION_AUTHORIZED=NO`.


## Visão geral V0.2 — execução CF-PROC0072-OVERVIEW-UX-004 (26/10/2026)

Fonte: [Plano 113 §§12–13](./113-plano-canonico-fluxo-fechamento-controladoria-dre-vigencia-documental.md) e [doc 112 §36](./112-design-visual-fechamento-mensal-wireframes.md). Testes em `plugins/controllership-finance/src/features/closing/MonthlyClosingPage.test.tsx` (29 casos; suíte do plugin 211/211 PASS; tsc + ESLint + build federado PASS).

| RQ | Requisito | Aceite mínimo | Teste mínimo | Estado |
|---|---|---|---|---|
| RQ-OVR-01 | Três abas preservadas, sem quarta aba | deep link ?tab + troca preserva período | troca de aba mantém /YYYY-MM; deep link período+aba | PASS |
| RQ-OVR-02 | Atenção é o bloco dominante com itens reais | blocking_reasons + P4 abertas + EXPECTED, máx. 4, ações para destinos reais | tradução de códigos; itens P4/checklist; navegação relatórios/pacotes/pendências | PASS |
| RQ-OVR-03 | Sem código técnico cru na interface | blocking_reasons traduzidos por mapa auditável | `package_not_submitted:FISCAL` → texto PT-BR; código ausente do DOM | PASS |
| RQ-OVR-04 | Sem falso zero de divergência | fonte UNAVAILABLE ⇒ «—» | fixture UNAVAILABLE ⇒ «—»; fixture disponível ⇒ contagem real | PASS |
| RQ-OVR-05 | Documentos a tratar honesto | sem contrato P2 ⇒ «—» explicado | indicador «—» + hint do owner pendente | PASS |
| RQ-OVR-06 | Eixos independentes | Estoque/Documentos/Pacote com estados próprios | três cartões com fatos reais por eixo | PASS |
| RQ-OVR-07 | Atividade só com eventos reais | feed P3 real; vazio/erro honesto; sem sintético | vazio + evento real (tipo/ator/data); keyed por período | PASS |
| RQ-OVR-08 | Conclusão ≠ envio | blocos separados; sem botão de concluir; envio via página de pacotes | bloco de conclusão mostra estado/impeditivos; «Gerenciar pacotes» navega | PASS |
| RQ-OVR-09 | Isolamento por período | resposta fora de ordem nunca vaza entre meses | rerender A→B com promise lenta + mês sem abertura | PASS |
| RQ-OVR-10 | Fail-closed | 403 sem conteúdo inventado | banner de restrição; atenção ausente | PASS |
| RQ-OVR-11 | Checklist vazio = estado normal | «Sem exigências cadastradas», sem erro | checklist {} + template_version_id null | PASS |
| RQ-OVR-12 | Acessibilidade da seção de atenção | foco programático ao ativar Bloqueios | activeElement = #cf-monthly-attention | PASS |
| RQ-OVR-13 | Mobile/temas/QA visual | layout responsivo e temas do kit | media queries implementadas; homologação visual PO | PENDING (QA visual pelo PO) |

## Visão geral V0.3 — refinamento de linguagem (CF-PROC0072-OVERVIEW-UX-REWORK-005, 26/10/2026)

| ID | Requisito | Critério de aceite | Evidência | Status |
|---|---|---|---|---|
| RQ-V03-01 | Copy primária em PT-BR simples | sem `cutoff`/`P3`/`checklist`/`pacote`/`template`/`source` em texto visível | grep sobre `MonthlyOverviewPanel.tsx` + tabela Plano 113 §15 | PASS |
| RQ-V03-02 | Tradução de bloqueios conhecidos | mensagens humanas por código real | testes «traduz códigos», «fonte P3 indisponível» | PASS |
| RQ-V03-03 | Fallback sem código cru | código desconhecido → mensagem genérica | teste «código de bloqueio desconhecido» | PASS |
| RQ-V03-04 | Expansão da atenção in-place | `Mostrar todas as N situações`/`Mostrar menos`; sem link enganoso para P4 | teste «expande todas as situações» | PASS |
| RQ-V03-05 | `no_applicable_packages` honesto | «Não há um conjunto de documentos para envio definido neste mês» | assert em «eixos independentes» | PASS |
| RQ-V03-06 | `—` sem falso zero | fonte indisponível/sem contrato → `—` | regressivos V0.2 mantidos | PASS |
| RQ-V03-07 | Eixos renomeados | «Conferência do estoque», «Documentos do mês», «Documentos para a Contabilidade» | teste «eixos independentes» | PASS |
| RQ-V03-08 | Conclusão ≠ envio preservado | «Concluir fechamento» + «Enviar documentos à Contabilidade» separados | teste «conclusão e envio separados» | PASS |
| RQ-V03-09 | Atividades = escopo conferências | subtítulo e vazio honestos («nesta conferência») | teste «atividade recente» | PASS |
| RQ-V03-10 | Regressões V0.2 | isolamento por período, deep link, fail-closed, foco | suíte 213/213 do plugin | PASS |
| RQ-V03-11 | QA visual desktop/mobile/temas | homologação do PO no navegador | — | PENDING (QA visual pelo PO) |

## Documentos e interações V0.2 — aba + detalhe contextual (CF-PROC0072-DOCUMENTS-UX-006, 26/10/2026)

| ID | Requisito | Critério de aceite | Evidência | Status |
|---|---|---|---|---|
| RQ-DOC-01 | Cartões por documento, sem tabela | cartão por exigência e por adicional com nome/situação/versão | MonthlyDocumentsPanel: «cartões», «aguardo», «adicional» | PASS |
| RQ-DOC-02 | Pesquisa e filtro de situação | restringem cartões; preservados na URL | testes «pesquisa por nome», «filtro de situação» | PASS |
| RQ-DOC-03 | Resumo de solicitações real | só decisões REJECTED correntes; motivo/autor/data | teste «solicitações reais» + «Abrir conversa» → `item:{key}` | PASS |
| RQ-DOC-04 | Vazio honesto | sem exigências/arquivos → «Nenhum documento exigido», sem erro | teste «estado vazio»; CANCELLED fora da lista | PASS |
| RQ-DOC-05 | Deep route do detalhe | `documents/{ref}` preserva período; ref `item:`/`uuid`/`new` | pluginRoutes: deep link + período inválido → not_found | PASS |
| RQ-DOC-06 | Detalhe com prévia/download/versões | FilePreviewView por download autenticado; versões e histórico reais | testes «decisões e histórico», «download e nova versão» | PASS |
| RQ-DOC-07 | Anexação contextual | upload no detalhe com `snapshot_item_id`; `new` sem vínculo | testes «anexo contextual», «novo adicional» | PASS |
| RQ-DOC-08 | Nova versão preserva anterior | replace com revision+idempotency_key; SUPERSEDED | teste «nova versão preserva revisão» | PASS |
| RQ-DOC-09 | Sem conversa fictícia | sem contrato de comentário → estado honesto declarado | teste «interações honestas» no modo adicional | PASS |
| RQ-DOC-10 | Fail-closed | 403 → banner, sem conteúdo inventado | testes «autorização» painel e «document_not_found» detalhe | PASS |
| RQ-DOC-11 | Três abas preservadas | detalhe esconde abas; voltar restaura filtros | teste de página «deep link de documento» | PASS |
| RQ-DOC-12 | QA visual mobile/temas | homologação do PO no navegador | — | PENDING (QA visual pelo PO) |



> **REWORK DOC V0.3 — 26/10/2026 — TARGET/RQ a verificar:** `RQ-DOC-RW-01` download/preview autenticado com pós-condição real e sem loading infinito; `RQ-DOC-RW-02` menu três pontos no card e operação U7 de cancelamento lógico devidamente autorizada + confirmação/OCC; `RQ-DOC-RW-03` U5 nova versão sem perda do histórico; `RQ-DOC-RW-04` histórico operacional sem eventos de download repetitivos ou UUID cru (preservar trilha obrigatória backend, sujeito owner/gate); `RQ-DOC-RW-05` eliminar navegação obrigatória ao checklist legado da composição nova sem perder validação P2; `RQ-DOC-RW-06` testes positivo/negativo/sibling, temas/mobile/foco, Ajuda, CLARA, local/prod e smoke autenticado. Capturas PO comprovam falha visível, não causa raiz da BFF. Referência [Plano 113 §19](./113-plano-canonico-fluxo-fechamento-controladoria-dre-vigencia-documental.md). Resultado: executado — ver tabela abaixo.

## Rework Documentos V0.3 — resultado (CF-PROC0072-DOCUMENTS-REWORK-007, 26/10/2026)

Causa raiz comprovada: `source` do `useFilePreviewLoader` com identidade nova a cada render → loop render→fetch U4→`DOCUMENT_DOWNLOADED`→render (spinner infinito + histórico inundado). Backend U4 íntegro.

| ID | Requisito | Evidência | Status |
|---|---|---|---|
| RQ-DOC-RW-01 | Download/preview autenticado, sem loading infinito, erro+retry | testes «fetch único por documento» (regressão), «falha na prévia oferece retry» | PASS |
| RQ-DOC-RW-02 | Menu três pontos + U7 autorizado, confirmação, OCC | testes «menu acessível», «sem ação impossível», «remoção confirma e chama U7», «cancelamento não chama U7», «exigência permanece» | PASS |
| RQ-DOC-RW-03 | U5 preserva histórico/versão anterior | testes «nova versão pelo cartão» (revision+idempotency), «selecionar versão anterior» | PASS |
| RQ-DOC-RW-04 | Timeline sem downloads repetidos; trilha backend preservada | filtro `DOCUMENT_DOWNLOADED` na UI + nota de auditoria; nenhum evento apagado; emissão na origem `PLANNED` (gate auditoria) | PASS (UI) / PLANNED (producer) |
| RQ-DOC-RW-05 | Sem navegação obrigatória ao checklist legado | `ItemValidationPanel` embutido no detalhe; bloco removido da aba; rota legada intacta | PASS |
| RQ-DOC-RW-06 | Testes, Ajuda, CLARA, deploy | plugin 244/244, tsc/eslint/estruturais/build PASS; Ajuda atualizada; CLARA reindexada | PASS / smoke autenticado PO PENDING |

## Conversa documental U9 — resultado (CF-PROC0072-DOCUMENT-INTERACTIONS-008, 27/10/2026)

Decisão PO ([Plano 113 §21](./113-plano-canonico-fluxo-fechamento-controladoria-dre-vigencia-documental.md), doc-112 §42): a Controladoria inicia conversa persistida por documento sem solicitação DRE prévia. Owner: `controllership-finance-api` (aggregate `closing_document`, migration V016).

| ID | Requisito | Evidência | Status |
|---|---|---|---|
| RQ-MSG-01 | Início proativo sem mensagem/solicitação prévia | composer ativo na thread vazia; `POST …/messages` 201 sem dependência de correção/validação | PASS |
| RQ-MSG-02 | Persistência backend, sobrevive a refresh/contexto | `document_message` V016 + `GET …/messages`; testes PG de persistência e cronologia | PASS |
| RQ-MSG-03 | Autor/data do servidor; sem UUID visual | `author_subject` UUID + `author_name` snapshot do claim; NULL → «Participante»; `uploaded_by` UUID removido da UI | PASS |
| RQ-MSG-04 | Sem duplicidade em retry | `UNIQUE(document_id,idempotency_key)`+`request_hash`; replay → `deduplicated`; divergente → 409; frontend reutiliza a chave no retry do mesmo texto | PASS |
| RQ-MSG-05 | Falha preserva rascunho; erro acessível | teste «falha no envio preserva o texto»; `CfFeedbackMessage` | PASS |
| RQ-MSG-06 | Escopo: competência/documento/filial | cross-competence/scope = 404 (positivo+sibling+negativo em rotas e PG) | PASS |
| RQ-MSG-07 | Mensagem não valida/conclui/libera/envia | nenhum efeito colateral no service; U5/U7/P2/P5 intactos (regressão 175 PG) | PASS |
| RQ-MSG-08 | Audiência governada | `audience='INTERNAL'` CHECK; documento não liberado nunca expõe fio à DRE | PASS / DRE TARGET (gate futuro) |
| RQ-MSG-09 | Documento cancelado: regra de negócio | conversa permitida em CANCELLED (não é mutação); registrado no Plano 113 §22.1 | PASS |
| RQ-MSG-10 | Auditoria obrigatória | `DOCUMENT_MESSAGE_POSTED` na mesma transação; incluso em U8; fora da timeline operacional | PASS |
| RQ-MSG-11 | Sem anexos/tempo real/notificação inventados | fora de escopo declarado; nenhum código criado | PASS (ausente por contrato) |
| RQ-MSG-12 | Testes, Ajuda, CLARA, deploy | backend 110/110+30/30+175/175 · frontend detalhe 18/18, closing 176/176, plugin 249/249 · tsc/eslint/build PASS · help+docs atualizados | PASS / homologação visual PO PENDING |


## Refinamento do detalhe UX-009 — resultado (CF-PROC0072-DOCUMENT-DETAIL-UX-009, 26/10/2026)

Decisão PO ([Plano 113 §23](./113-plano-canonico-fluxo-fechamento-controladoria-dre-vigencia-documental.md), doc-112 §44): conversa com altura mínima, histórico em linha do tempo compartilhada e avatar autorizado dos participantes. U9/U1–U8, permissões e lifecycle preservados.

| ID | Requisito | Evidência | Status |
|---|---|---|---|
| RQ-UX-01 | Altura mínima da conversa no desktop (faixa 480–560) | `.cf-document-conversation min-height: 520px`; thread `flex:1` rola até 560px; composer no rodapé com 0/1/N mensagens | PASS |
| RQ-UX-02 | Rolagem interna + composer acessível | `fill`/`overflow-y` do kit; `submitOnEnter=false`, `rows=3`; mobile `60vh` sem aprisionar | PASS |
| RQ-UX-03 | Histórico como timeline compartilhada | `CfTimeline = createTimeline` do kit (mesmo da CIPA); `EventsSection` confirmado como alertas e rejeitado | PASS |
| RQ-UX-04 | Somente eventos materiais ordenados | U8: upload/versão/cancelamento/EVIDENCE_* com tom; `DOCUMENT_DOWNLOADED`+`DOCUMENT_MESSAGE_POSTED` fora; auditoria íntegra | PASS |
| RQ-UX-05 | Sem UUID/enums na UI | labels PT por evento; responsável = display_name do diretório ou «Participante»; teste asserta ausência do UUID | PASS |
| RQ-UX-06 | Empty state honesto | «Ainda não há alterações registradas neste documento.»; nenhum evento artificial | PASS |
| RQ-UX-07 | Avatar oficial ou fallback legítimo | `UnifiedAvatar`/`InitialsAvatar`; foto via proxy S2S Core person-profile; sem foto → iniciais; nunca foto do viewer para terceiros | PASS |
| RQ-UX-08 | Nome oficial autorizado | `POST /closing/participants/lookup` → diretório Core com bearer do caller; `display_name=null` → neutro | PASS |
| RQ-UX-09 | Permissões congeladas | ambos endpoints exigem `access`; sem token/sem access → 401/403; nenhuma permission nova | PASS |
| RQ-UX-10 | U9 preservada | mensagens/idempotência/auditoria/escopo inalterados; regressão detalhe 23/23, plugin 254/254 | PASS |
| RQ-UX-11 | Falhas honestas de perfil | Core fora → lookup `{}`→fallback; avatar 404→iniciais; gateway 503; UUID inválido 422; lote>50 rejeitado | PASS |
| RQ-UX-12 | Testes + docs + CLARA | rotas 10/10 · gateway 10/10 · detalhe 23/23 · plugin 254/254 · tsc/ESLint/estruturais PASS · help atualizado | PASS / homologação visual PO PENDING |


## Rework UX-009-RW01 — isolamento de participantes (CF-PROC0072-DOCUMENT-DETAIL-UX-009-RW01, 26/10/2026)

REWORK do GPT Arquiteto sobre o contrato de participantes da UX-009:
lookup/avatar exigiam só `access` e aceitavam ids arbitrários — risco
de enumeração/exposição de perfis fora do escopo documental. Correção:
contrato contextual por documento+competência; visual aprovado
inalterado. Plano 113 §23.6 / doc-112 §44.2.

| ID | Requisito | Evidência | Status |
|---|---|---|---|
| RQ-RW01-01 | Lookup exige contexto documental autorizado | `POST /closing/competences/{period}/documents/{id}/participants/lookup`; `_document_in_scope` precede Core | PASS |
| RQ-RW01-02 | Avatar exige o mesmo contexto | `GET …/participants/{user_id}/avatar`; `branch_scope` opcional igual às rotas U3–U9 | PASS |
| RQ-RW01-03 | Vínculo canônico é a prova | `list_document_participant_ids`: autor U9 + ator U8 + uploader; id do frontend só filtra | PASS |
| RQ-RW01-04 | Cross-documento fail-closed | id sem vínculo omitido do lookup; avatar 404 sem consultar Core | PASS |
| RQ-RW01-05 | Cross-competência fail-closed | competência do path resolve o documento; divergente → `DocumentNotFound` 404 | PASS |
| RQ-RW01-06 | Resource scope preservado | `branch_scope` MATRIX/BRANCH/BOTH no mesmo `_document_in_scope` de U3/U4/U9 | PASS |
| RQ-RW01-07 | Sem enumeração | resposta omite ids fora do vínculo; ausência não confirma nem nega existência | PASS |
| RQ-RW01-08 | Rotas antigas removidas | `/closing/participants/lookup` + `/{user_id}/avatar` fora do router; busca residual: zero consumidores CF | PASS |
| RQ-RW01-09 | Core segue owner do perfil | diretório (bearer do caller) + person-profile S2S inalterados; sem storage/duplicação local | PASS |
| RQ-RW01-10 | Sem permission nova | `controllership-finance.access` apenas; sem token 401, sem access 403 | PASS |
| RQ-RW01-11 | Isolamento de perfis no frontend | hook recebe `{period, documentId}`; estado etiquetado por chave completa; troca de contexto nunca exibe perfil stale | PASS |
| RQ-RW01-12 | UX aprovada preservada | conversa 520px + composer rodapé, `CfTimeline`, `UnifiedAvatar`/`authorSrc`, fallback de iniciais, histórico/versões intactos | PASS |
| RQ-RW01-13 | Testes negativos executados | rotas 19/19 (cross-doc, cross-competence, não-participante, sem access, sem token, UUID inválido, >50, Core fora); hook 6/6; detalhe 23/23; plugin; gateway 10/10 | PASS |
| RQ-RW01-14 | Fallback honesto | sem foto → iniciais; sem perfil → «Participante»; UUID nunca visível | PASS |


## Relatórios e divergências V0.2 — resultado (CF-PROC0072-REPORTS-UX-010, 27/10/2026)

Decisões PO congeladas ([Plano 113 §25](./113-plano-canonico-fluxo-fechamento-controladoria-dre-vigencia-documental.md), doc-112 §45): atenção antes do catálogo, cartões por família, resultados inline, PDF inline. Implementação sobre contratos canônicos existentes — sem endpoint novo, sem permission nova, sem cálculo no navegador.

| ID | Requisito | Evidência | Status |
|---|---|---|---|
| RQ-REP-01 | Atenção antes do catálogo | `MonthlyReportsPanel`: «O que precisa de atenção» é a primeira seção operacional | PASS |
| RQ-REP-02 | Três categorias de apresentação | `divergence` / `source_unavailable` / `check_pending` derivadas dos contratos (P3, quality flags, status estoque, matriz) — nenhum enum persistido | PASS |
| RQ-REP-03 | Sem falso zero | erro de fonte → indicador `—`; `source_missing`/`UNAVAILABLE` nunca viram «0 divergências»; teste «erro de consulta não é ausência» | PASS |
| RQ-REP-04 | Valor/origem/data/ação nos itens | cada item mostra diferença formatada, origem, `fetched_at` real e próxima ação; expansão com fatos | PASS |
| RQ-REP-05 | Causa honesta | «A causa ainda não foi identificada» nas divergências; sem instrução TOTVS inventada, sem escrita ERP | PASS |
| RQ-REP-06 | Cartões por família | `CfInteractiveDataCard` ×2 (Baixas financeiras, Estoque e conciliação) com situação real + seleção visual; matriz subordinada | PASS |
| RQ-REP-07 | Resultados inline + progressivo | `?tab=reports&report=…`; total → grupos → linhas sob demanda (`nature_code`/`movement_type`, itens do snapshot paginados) | PASS |
| RQ-REP-08 | Divergência canônica | P3 `reported − expected` do backend; nenhum cálculo financeiro no MFE; `R$ 0,00` exato = sem divergência | PASS |
| RQ-REP-09 | Competência não aberta honesta | P3/matriz 404 → «Conferência não realizada» + cobertura não gerada; baixas/estoque period-keyed seguem consultáveis | PASS |
| RQ-REP-10 | URL/F5/back-forward | `report` na query; painel recebe `selectedReport` da página; teste de troca de período refaz as 4 consultas | PASS |
| RQ-REP-11 | Isolamento de período | resultados keyed `period:nonce`; AbortController + request-id; nunca dado de outro mês | PASS |
| RQ-REP-12 | PDF contextual honesto | slot sempre presente; «ainda não está disponível para este relatório» sem produtor; nenhum PDF fictício/evidência reutilizada | PASS |
| RQ-REP-13 | Plugin-ui real, sem duplicatas | inventário Doc 30: `CfInteractiveDataCard`, `CfSectionCard`, `CfStatusBadge`, `CfMetricStrip`, `DataTableSection`, `CfEmptyState`, `CfFeedbackMessage`, `CfActionButton` | PASS |
| RQ-REP-14 | Rotas legadas compatíveis | `closing/financial-settlements` e `closing/stock-inventory` intactas; nenhum consumer removido | PASS |
| RQ-REP-15 | Testes e gates | painel 15/15 + página 32/32 + plugin 275/275 + estruturais 8/8 · tsc · ESLint escopo · build federado `App-C7-aX4Lo.js` | PASS / homologação visual PO PENDING |


### Relatórios e divergências V0.3 — páginas contextuais (UX-011, 27/10/2026)

| ID | Requisito | Evidência | Status |
|---|---|---|---|
| RQ-REP-16 | Rota contextual por relatório | `closing/monthly-closing/{p}/reports/{key}` em `resolvePluginRoute`; `financial-settlements`/`stock-inventory`; chave desconhecida → estado honesto; testes de rota 149+ | PASS |
| RQ-REP-17 | Reuso das páginas legadas | `reportContext` em `FinancialSettlementsPage`/`StockInventoryPage` — competência travada da rota, filtros/tabela/paginação intactos; rotas legadas preservadas | PASS |
| RQ-REP-18 | Tabelas organizadas por colunas | agrupamentos SE5 em `DataTableSection` (Natureza/Tipo/Baixas/Valor/Moeda/Ação, sem concatenação); estoque mantém Resumo por tipo/armazém em tabelas do kit | PASS |
| RQ-REP-19 | Contexto preservado no retorno | «Voltar» → `?tab=reports&report={família}`; navegação, deep link e F5 testados na página (4 casos) | PASS |
| RQ-REP-20 | Hub compacto sem detalhe inline | cartões com slot `children`; matriz R01–R15 em `<details>` técnico; sem «RELATÓRIO/DESCRIÇÃO» repetidos; PDF saiu do hub | PASS |
| RQ-REP-21 | PDF contextual honesto | `ReportPdfSlot` nas duas páginas; «ainda não está disponível» sem produtor; zero PDF fictício | PASS |
| RQ-REP-22 | Sem fonte/cálculo inventado | nenhum endpoint/permission/migration novo; divergência P3 vem do backend; «Ver registros» aplica filtros reais do contrato | PASS |


### Persistência de filtros nas páginas contextuais (UX-011-RW01, 28/10/2026)

| ID | Requisito | Evidência | Status |
|---|---|---|---|
| RQ-REP-23 | URL é a fonte recuperável | `reportQueryParams.ts` serializa filtros na query da rota (`replace: true`); parse na montagem + `popstate`; mesmo padrão `location.search`/`popstate` do portal (`useConsoleSearchParams`) | PASS |
| RQ-REP-24 | Baixas — filtros completos | `side|start|end|nature|movement|sort|dir|page` restaurados de F5/deep link e reconsultados; datas fora da competência descartadas como par | PASS |
| RQ-REP-25 | Estoque — filtros completos | `branch|scope|warehouse|page` restaurados e reconsultados; `period` nunca serializado — competência travada na rota | PASS |
| RQ-REP-26 | Back/forward do navegador | `popstate` reidrata o estado da entrada e refaz a consulta com os valores dela (casos de página 3 e filtros alterados) | PASS |
| RQ-REP-27 | Retorno e reabertura | `backToReports` → `?tab=reports&report={família}&{filtros}`; `openReport` repassa somente quando `report=` é a família aberta — família diferente abre limpa | PASS |
| RQ-REP-28 | Validação e isolamento | allowlists de enums, `page` ≥ 1, datas `YYYY-MM-DD`/`start ≤ end`/dentro do mês; `pickFamilyParams` prova ausência de vazamento entre famílias; sem `localStorage`/dados financeiros na URL | PASS |
| RQ-REP-29 | UX V0.3 preservada | zero mudança visual; modo legado (`reportContext` ausente) não sincroniza — comportamento idêntico; sem novo endpoint/permissão/cálculo | PASS |

### Catálogo mestre de documentos — administração (UX-012, 28/10/2026)

| ID | Requisito | Evidência | Status |
|---|---|---|---|
| RQ-ADM-01 | Listagem derivada do contrato | `documentCatalog.deriveDocumentCatalog` agrega `item_key` da timeline publicada; janelas de vigência por versão vencedora — testado (contínuo, futuro, descontínuo, só-rascunho) | PASS |
| RQ-ADM-02 | Cadastro em página completa | `closing/admin/documents/new` — `DocumentConfigFormPage`; validação nome/competência/intervalo/key antes do backend; slug automático; sem modal | PASS |
| RQ-ADM-03 | Edição em página completa | `closing/admin/documents/{itemKey}` — carrega configuração publicada mais recente, situação, janelas e histórico de eventos; não encontra → estado honesto | PASS |
| RQ-ADM-04 | Vigência prospectiva | `saveDocumentConfig` publica versão com `effective_from_period`; «até» agenda versão de remoção em `nextPeriod`; snapshots congelados; `effective_from ≥` competência atual | PASS |
| RQ-ADM-05 | Encerrar exigência | `publishRemovalVersion` — confirmação `ConfirmModalPanel`; último item recusado (`CatalogSaveError`); histórico preservado | PASS |
| RQ-ADM-06 | Filtros persistentes | `q`, `status`, `dest` na URL via `useReportQuerySync`; deep link/F5 restauram; retorno do formulário devolve a query | PASS |
| RQ-ADM-07 | Isolamento de escrita | orquestração draft→update→review→publish nos endpoints existentes; `draft_already_open` → banner honesto; nenhum endpoint/permissão/migration novo; 403 seguro | PASS |
| RQ-ADM-08 | Sem premissas inventadas | destino `CONTABIL`/`FISCAL`/uso-interno conforme contrato; excepcional-por-competência não exposto aqui (conceito distinto); página DRE fora de escopo | PASS |

### GATE-016 — deploy produtivo e homologação (28/10/2026)

| ID | Critério | Status | Evidência |
|----|----------|--------|-----------|
| RQ-ADM-DR1-12 | writers legados respeitam D3 (janela cobrindo competência aberta → 422) | PASS | PG: publish/inactivate bloqueados + publish prospectivo permitido; suíte 692 |
| AC-01 | BFF em produção com endpoint documental | PASS | PUT …/requirement → 401 sem token (rota registrada); health 200 |
| AC-02 | V017 aplicada | PASS | startup log migration_applied V017; tabela existe (0 linhas) |
| AC-03 | Frontend atualizado e integrado | PASS | bundle prod contém Idempotency-Key/empty_resulting_checklist |
| AC-04 | Catálogo administrativo abre | PASS | GET admin/checklist-templates 200 MANAGE (template real retornado) |
| AC-05/06 | Cadastro/edição página completa | PENDING | homologação do PO (primeiro cadastro real) |
| AC-07 | Filtros e navegação preservados | PASS | UX-012 inalterado neste gate (escopo backend) |
| AC-08 | Backend protege MANAGE | PASS | 403 autenticado sem permissão CF; 401 sem token |
| AC-09 | Operação transacional validada localmente | PASS | GATE-015 smoke + PG (13 casos) |
| AC-10 | Checklist vazio intencional | PASS | allow_empty smoke local + empty guard 422 |
| AC-11 | Auditoria funcional | PASS | trilha conferida no banco local; audit prod 4.511 eventos intactos |
| AC-12 | Publicação legada compatível | PASS | D3 guard + suíte legada verde |
| AC-13 | Snapshots preservados | PASS | competência 2026-09 OPEN template_version_id=NULL intacta |
| AC-14 | Health/readiness produção | PASS | containers healthy pós-deploy |
| AC-15 | Smoke autenticado prod não destrutivo | PASS | GET templates/versions 200; zero escrita |
| AC-16 | Cadastro manual preparado para o PO | PENDING | draft v1 (53 itens) bloqueia via catalog_draft_conflict até publicação prospectiva — ver doc 114 §11.4 |
| AC-17 | Documentação atualizada | PASS | doc 114 §11, plano 113 §28.6, ledger 23 |
| AC-18 | Nenhuma regressão material | PASS | backend 692 + frontend 337 verde; sem overlapping remote diffs |
