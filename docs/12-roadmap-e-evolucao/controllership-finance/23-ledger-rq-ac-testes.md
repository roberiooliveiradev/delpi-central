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

### GATE-017 — inventário e gate de descarte do rascunho v1 (28/10/2026)

| ID | Critério | Status | Evidência |
|----|----------|--------|-----------|
| G17-INV-01 | identidade do rascunho | PROVEN | v1 DRAFT rev1, template monthly-closing-checklist, seed 2026-10-24 |
| G17-INV-02 | proveniência | PROVEN | migration V002 seed (não cadastro administrativo); 0 eventos audit |
| G17-INV-03 | dependências | PROVEN | 0 snapshots, 0 refs competence, único FK = itens próprios |
| G17-MECH-01 | mecanismo oficial de descarte | PASS | DELETE …/versions/{v} implementado (df43536acd) |
| G17-GATE | elegibilidade p/ descarte | DECISION_REQUIRED | todos os critérios PROVEN exceto mecanismo oficial |
| G17-EXEC | encerramento governado | PASS | descarte 200 DISCARDED + VERSION_DISCARDED auditado (doc 114 §12.4) |

### UX-013 — refinamento visual do catálogo administrativo (28/10/2026)

| ID | Critério | Status | Evidência |
|----|----------|--------|-----------|
| RQ-UX013-01 | kit-first: controles de entrada como export real | PASS | `CfTextField`/`CfTextAreaField`/`CfSelectField`/`CfDateField`/`CfTimeline` boundados; zero componente paralelo (doc 30 §UX-013) |
| RQ-UX013-02 | spacing/grid responsivo, mobile sem overflow | PASS | `cf-form-grid` auto-fit 220px; overflow horizontal 0px @390px |
| RQ-UX013-03 | CTA primário + danger governado | PASS | Salvar/Adicionar/Criar versão `primary`; Descartar/Inativar/Encerrar `cf-action-btn--danger` |
| RQ-UX013-04 | eventos como timeline com tons semânticos | PASS | `CfTimeline` no modal e no histórico; `VERSION_DISCARDED` label + `DISCARDED` badge; screenshot 05 |
| RQ-UX013-05 | listagem/home estados e navegação | PASS | filtros URL/F5 preservados; CTA com ícone; deep links intactos (337 testes) |
| RQ-UX013-06 | regressão de contrato/regras | PASS | nenhum diff BFF/contrato/dados; typecheck+lint+build verde |
| RQ-UX013-07 | DoD claro/escuro/teclado/320px/zoom | PASS | screenshots 01–07 (claro, escuro, mobile); campos do kit com label/hint/focus |
| AC-UX013-PROD | deploy produção | PASS | MFE `App-B5Ynp8Kk.js` @ SHA 1b59fdc895; smoke g16: S-01..S-06 PASS (select mouse/teclado/Escape, timeline 4 eventos, edição preenchida); RBAC restaurado |
| AC-UX013-RW01 | espaçamento/hierarquia admin | PASS | causa PROVEN (__content sem regra CSS); escala 8/16/24px via tokens `--cf-*`; tsc+eslint+build ✓; 337 testes (1 flake pré-existente avatar); shots claro/escuro/tablet/390/320/zoom200 overflowX=0; deploy local ✓; prod pendente |


### UX-015 — navegação administrativa em cascata do checklist (28/10/2026)

| ID | Critério | Status | Evidência |
|----|----------|--------|-----------|
| AC-01 | admin sem expansão inferior de itens | PASS | `getVersionMock` nunca chamado; «Itens do checklist» ausente (teste admin); smoke S-01 |
| AC-02 | versão em página própria | PASS | rota `closing/admin/versions/{n}` → `checklist_version`; teste navegação + smoke S-02 |
| AC-03 | documentos da versão selecionada | PASS | `getTemplateVersion(tpl,n)` — snapshot real, não catálogo; 53 itens v1 no smoke |
| AC-04 | documento em página própria | PASS | `versions/{n}/documents/{itemKey}`; smoke S-03 |
| AC-05 | PUBLISHED/INACTIVE read-only | PASS | sem «Editar itens»/inputs (teste + smoke S-03-ro 0 inputs editáveis) |
| AC-06 | edição prospectiva governada | PASS | «Editar exigência futura» → `admin/documents/{key}` (catálogo DR-1); DRAFT edita via OCC `revision` |
| AC-07 | histórico em página contextual | PASS | `checklist_admin_events` + `?version=`; zero `[role=dialog]` no smoke S-04 |
| AC-08 | breadcrumb/retorno com contexto | PASS | `CfPagePath` por nível; back→versão, items→ancestrais |
| AC-09 | deep link e F5 | PASS | goto direto `/versions/2/documents/CK-E-01` renderiza (S-05); rotas testadas |
| AC-10 | kit reutilizado | PASS | `cf-detail-list`, `CfPagePath`, `DataTableSection`, `CfTimeline`, `ConfirmModalPanel` — zero componente novo |
| AC-11 | responsivo/espaçado | PASS | mobile 390 `overflowX=0` (S-10); stacks `--cf-*` UX-013-RW01 |
| AC-12 | teclado/foco/a11y | PASS | navegação por botões/links nativos; breadcrumb com `ariaLabel`; diálogos mantêm close/focus do kit |
| AC-13 | sem alteração de contrato/dados | PASS | diff 100% MFE; BFF/migrations/permissões intactos; zero escrita no smoke |
| AC-14 | testes frontend | PASS | 360 testes / 35 arquivos; tsc + eslint + `vite build` (`App-Cq3zaL3w.js`) |
| AC-15 | deploy produção canônico | PENDING | autorizado pelo PO — executar após commit/push |
| AC-16 | smoke prod autenticado | PENDING | não destrutivo, somente leitura |
| AC-17 | docs + Ajuda sincronizados | PASS | §28.12, doc 112 §50, ledger, doc 30, `helpTooltips` (`adminVersion*`/`adminEvents`) |
| AC-18 | evidências p/ homologação PO | PASS local | screenshots `Temp\ux015-shots` (01–09); produção pendente |
| UX-015 DEP | ator enriquecido | DECISION_REQUIRED | `actor_subject` cru mantido — depende de UX-014 |


### UX-015-RW01 — redesign visual cascata (TARGET, 28/10/2026)
| RQ/AC | Prova exigida | Status |
|---|---|---|
| UX015-RW01-01 | Cabeçalho contextual e ações no topo de versão/documento | TARGET |
| UX015-RW01-02 | Resumo compacto versão com dados reais | TARGET |
| UX015-RW01-03 | Lista documental logo após resumo e sem expansão na administração | TARGET |
| UX015-RW01-04 | Detalhe read-only em grid semântico 2–3 colunas desktop e uma mobile | TARGET |
| UX015-RW01-05 | Contexto da versão compacto + edição futura direcionada ao fluxo mestre | TARGET |
| UX015-RW01-06 | Timeline contextual em página, eventos reais e fallback ator honesto | TARGET |
| UX015-RW01-07 | Kit-first, tokens, claro/escuro, mobile, zoom200, foco/teclado | TARGET |
| UX015-RW01-08 | Regressão zero de versão histórica, DRAFT OCC, authz, F5, breadcrumbs | TARGET |
| UX015-RW01-09 | Capturas antes/depois, testes, deploy e smoke autenticado governado | PLANNED |
Nenhum teste ou deploy desta rodada foi executado ao escrever esta especificação.


### UX-015-RW01 — redesign visual da cascata administrativa (28/10/2026)

| ID | Critério | Status | Evidência |
|----|----------|--------|-----------|
| UX015-RW01-01 | cabeçalho + ações contextuais | PASS | badge no título; «Histórico da versão»/«Voltar»/«Editar exigência futura» no topo (smoke S-02/S-03, shots) |
| UX015-RW01-02 | resumo compacto da versão | PASS | `CfMetricStrip` 3 tiles do DTO + fatos secundários em grid (shot 02) |
| UX015-RW01-03 | documentos logo após resumo | PASS | `DataTableSection` banda única após tiles, sem card gigante (shot 02) |
| UX015-RW01-04 | detalhe em grid semântico | PASS | `cf-detail-list` = grid auto-fit 200px; Identificação 2 col, Exigência ~4 col (shot d-dark-document) |
| UX015-RW01-05 | contexto compacto + edição prospectiva | PASS | linha `cf-version-context`; «Editar exigência futura» no header → catálogo (S-03) |
| UX015-RW01-06 | timeline contextual acessível | PASS | página dedicada + subtítulo de escopo; `CfTimeline`, sem dialog (S-04/S-09) |
| UX015-RW01-07 | design system + responsividade | PASS | tokens `--cf-*`; 20 capturas claro/escuro/tablet/390/320/zoom200 `overflowX=0` |
| UX015-RW01-08 | navegação/regras preservadas | PASS | smoke 12/12: deep link, F5, back/forward, 404, DRAFT governado, read-only |
| UX015-RW01-09 | testes/evidências/deploy | PASS local | 360 testes, build `App-GXSC05Nq.js`, deploy canônico; smoke prod TEST_NOT_RUN se identidade smoke não autorizada |


### UX-015-RW02 — rework estrutural da Administração (28/10/2026)

| ID | Critério | Status | Evidência |
|----|----------|--------|-----------|
| UX015-RW02-01 | superfície única de listagem (fim card-em-card) | PASS | `CfSectionCard` intermediário removido; `DataTableSection` direta com ações no `headerActions` — smoke RW02-01, shot 01 |
| UX015-RW02-02 | título PT-BR sem `monthly-closing-checklist` | PASS | título «Versões · Checklist de Fechamento Mensal»; subtítulos da versão/eventos sem o código (shots 01/02/12) |
| UX015-RW02-03 | ações no topo com ícones e cores semânticas | PASS | `FilePlus2`/`History`/`FileText` no `headerActions`; Inativar/Descartar em `--danger` (shots 01/06) |
| UX015-RW02-04 | ordenação real por coluna | PASS | `sortable`+`sortValue` nas colunas de versões e itens; smoke RW02-02 asc/desc; teste RTL "sorts versions by column" |
| UX015-RW02-05 | alternância Tabela/Cards funcional | PASS | `viewLayoutPreferencesKey` + `renderCard` (`CfDataRecordCard` do kit); smoke RW02-07/RW02-09; RTL cards |
| UX015-RW02-06 | linha navega ao detalhe; sem «Abrir» redundante | PASS | `onRowClick` (clique/Enter/Espaço/foco do kit); coluna de ações removida em leitura; RTL + smoke RW02-04/RW02-06 |
| UX015-RW02-07 | destrutivas isoladas com confirmação | PASS | `rowClick:"stop"` na coluna de ações + faixa própria nos cards (anchor não aninha interativos); smoke RW02-03; RTL |
| UX015-RW02-08 | versão sem UUID como identidade | PASS | «Publicada por» → «Identidade não disponível» + subject só em `title`; trilha preserva «Ator (id):» — RTL fallback |
| UX015-RW02-09 | identidade humana via contrato autorizado | DECISION_REQUIRED | BFF só tem lookup document-scoped (`participants/lookup`); atores administrativos exigem novo contrato Core→BFF — ver UX-014 |
| UX015-RW02-10 | responsividade/temas/zoom | PASS | shots 10–15: dark/tablet820/320/390 `overflowX=0`; mobile default vira cards no kit |
| UX015-RW02-11 | regressão/navegação/estados | PASS | 365 testes; smoke RW02 13/13 (deep link, F5, back/forward, 404, DRAFT/REVIEW/PUBLISHED) |
| UX015-RW02-12 | deploy governado | PASS | `bed4993c05` → origin/main; srv-api pull + `up-prod-sequential.sh --build controllership-finance`; remoteEntry 200 servindo `__federation_expose_App-0ucqmrGp.js`/`App-D376ypA0.js`; BFF healthy; smoke prod autenticado TEST_NOT_RUN (sem identidade autorizada) |
| UX016RW01-01 | Labels informativos inventariados em todas as superfícies do Portal | PASS | Matriz: 10 superfícies — Admin, Versão, Documento, Documentos, Catálogos, Checklist, Estoque, Baixas, Minhas tarefas, formulário; exceções justificadas (colunas Ações) |
| UX016RW01-02 | Cabeçalhos de tabela com ajuda contextual | PASS | `headerHint` em ~70 colunas; RTL «renders contextual help» nas duas páginas; smoke RW01-help (6 ícones na listagem Admin) |
| UX016RW01-03 | Ajuda reutiliza componentes homologados | PASS | `HelpTooltip`/`FieldLabel`/`hintedLabel` — zero implementação paralela, zero `title` HTML como solução |
| UX016RW01-04 | Explicações respeitam os contratos | PASS | textos derivados dos hints governados já existentes em `helpTooltips.ts` + DTOs reais; «Última versão» documenta semântica de maior número (não vigência) |
| UX016RW01-05 | Acessível por mouse, teclado e toque | PASS | `HelpTooltip` do kit: trigger com foco visível, `aria-label`, portal com clamp de viewport; mesmo componente dos `headerHint`/`hint` nativos |
| UX016RW01-06 | Zero registros não exibe paginação | PASS | kit `Pagination` retorna null com `total===0` + gate `hidePaginationWhenSinglePage`; RTL kit 3 cenários |
| UX016RW01-07 | Uma página não exibe paginação | PASS | `hidePaginationWhenSinglePage` no kit + default no wrapper CF; smoke local: Admin 3 versões → «oculta (página única)» |
| UX016RW01-08 | Múltiplas páginas exibem paginação | PASS | Versão com 53 itens → «Exibindo 1–50 de 53 · Página 1 de 2» ancorada (smoke UX016-05b); RTL Stock 120 itens |
| UX016RW01-09 | Tabela e Cards seguem a mesma regra | PASS | gate aplicado ao `<Pagination>` único da seção — fora do condicional table/cards |
| UX016RW01-10 | Filtros recalculam paginação | PASS | regra usa o conjunto pós-filtro (`paginationTotal`); RTL kit «recalcula após busca reduzir a uma página» |
| UX016RW01-11 | Ordenação e navegação preservadas | PASS | smoke UX016-06-sort/search/cards/nav 20/20; sort por coluna com hint acessível |
| UX016RW01-12 | Claro/escuro e mobile funcionais | PASS | shots light/dark + 768/390/320 + zoom200 — overflowX=0 (harness UX016) |
| UX016RW01-13 | Nenhum contrato/dado alterado | PASS | diff restrito a frontend + kit; zero BFF/migrations/permissões |
| UX016RW01-14 | Testes frontend e build aprovados | PASS | MFE 371 (2 flakes transitórios conhecidos, verdes no rerun) + plugin-ui 2093/2093; build cf `App-Cq6oV9AL.js` / kit `Index-Dt9qqFyC.js` |
| UX016RW01-15 | Documentação e Ajuda sincronizadas | PASS | 112 §53.6, 113 §28.15, 30 reuse map, README e `helpTooltips.ts` no mesmo commit |


### UX-016 — Hero contextual e listagem flexível nas páginas Admin/Versão (IMPLEMENTADO)
| AC | Evidência esperada | Estado |
|---|---|---|
| UX016-01 | Admin e Versão com mesmo padrão HERO→LISTAGEM em duas superfícies irmãs | PASS | `CfPageHero` + `.cf-flex-listing` nas duas páginas; smoke UX016-01/01b; shots 01/03 desktop, dark, 768, 390, 320 |
| UX016-02 | Hero reúne métricas, ações, busca, Tabela/Cards, Colunas sem toolbar duplicada | PASS | `toolbarPortalTarget` porta a toolbar nativa (mesma instância) para `cf-hero-toolbar`; smoke UX016-02 dup=0; RTL «renders the listing toolbar inside the hero» |
| UX016-03 | Administração sem coluna Ações/Inativar; versão abre por clique na linha/card | PASS | coluna Ações removida; RTL «no actions column nor destructive controls»; smoke UX016-03 Ações=0/Inativar=0/Abrir=0 |
| UX016-04 | Inativar exclusivamente na versão, ícone danger + confirmação BFF existente | PASS | `VersionStatusActions` no hero do detalhe (`Archive` + `--danger`); RTL «inactivates the published version after confirmation, without navigating»; chamada `inactivateTemplateVersion` preservada |
| UX016-05 | Tabela ocupa altura útil flexível; paginação no fim; 0/1/50/100 linhas sem artificiais | PASS | `dashboard-page--fill` + `flex:0 0 auto` no hero + `cf-flex-listing` flex:1 + `delpi-ui-table-wrap--scroll`; smoke UX016-05/05b (bottom=876/vh=900 = padding 24; paginação ancorada); RTL empty state |
| UX016-06 | Ordenação real + paridade tabela/cards + filtros/colunas preservados | PASS | `sortable`/`sortValue` + `viewLayoutPreferencesKey` + `renderCard`; smoke UX016-06-sort asc/desc, -search 3→1→3, -cards=48, -nav; RTL sort/cards/search |
| UX016-07 | PT-BR e kit-first, light/dark, 320/390/768/desktop/zoom200, keyboard/focus | PASS | shots light+dark/768/390/320/zoom200 `overflowX=0`; hero empilha no mobile; navegação por linha mantém foco/Enter/Espaço do kit |
| UX016-08 | Snapshot, OCC, read-only PUBLISHED, back/F5/deep link, RBAC, erros, Help intactos | PASS | RTL DRAFT edit/OCC stale_revision, PUBLISHED read-only, 403/404/empty; smoke deep link v2 + histórico + F5; Help atualizado (hero/toolbar, ações só no detalhe) |
| UX016-09 | Testes, screenshots, bundle, deploy/smoke por gate com status honesto | PASS | MFE 367/367 + plugin-ui 167/167 + smoke local 19/19 + 8 capturas; commit `8389500d71` → origin/main; srv-api pull + `up-prod-sequential.sh --build plugin-ui controllership-finance`; remoteEntry 200 — cf `App-B3v-K-FL.js`/`__federation_expose_App-jOmJd2RR.js` (contém `admin-listing-toolbar`/`cf-flex-listing`), kit `__federation_expose_Index-C8jie95s.js` (contém `toolbarPortalTarget`); BFF health/ready 200, container healthy; smoke prod autenticado TEST_NOT_RUN (sem identidade autorizada) |


## Área DRE — recebimento documental (CF-PROC0072-DRE-ACCESS-018, 29/10/2026)

Inventário read-only + desenho + gate de arquitetura (Plano 113 §29, wireframes doc 112 §54). `IMPLEMENTATION_AUTHORIZED=NO` — nenhum endpoint/migration/página/deploy nesta execução. Status respeita: `PROVEN | TO_INVENTORY | PLANNED | TARGET` para capacidades; `TEST_NOT_RUN` para aceites de runtime ainda não implementáveis.

| ID | Requisito | Evidência | Status |
|---|---|---|---|
| RQ-DRE-INV-01 | Pacotes por área destinatária com snapshot imutável | `closing_package` UNIQUE(competence,recipient_area) + `closing_package_version` DRAFT→FINALIZED→SUBMITTED com `content.items[]`{document_version_id} (V008) | PROVEN |
| RQ-DRE-INV-02 | Documentos versionados + download auditado | `closing_document`/`document_version` + `resolve_download` (scope filial + `DOCUMENT_DOWNLOADED` autorizado/negado) | PROVEN |
| RQ-DRE-INV-03 | Visibilidade por assignment fail-closed | `_visible_areas`: manage→tudo, demais→só assignments ativos, sibling=404 | PROVEN |
| RQ-DRE-INV-04 | Effective permissions fail-closed | `.access`/`.manage` via middleware Core; Core down → 503; manage≠access | PROVEN |
| RQ-DRE-INV-05 | Kit UI para as 4 telas | exports verificados: `createDashboardMessageThread`/`MentionComposer`/`RoomConversationShell`/`AttachmentPreviewStrip`, `ResizableColumns`, `useFilePreviewLoader`/`FilePreview`, `DataTableSection`(+portalTarget/tableLayout/hidePaginationWhenSinglePage/headerHint), `CfTimeline`, `HelpTooltip` | PROVEN |
| RQ-DRE-INV-06 | Superfícies MFE reutilizáveis | `DocumentDetailPanel`, `DocumentConversationPanel`, `PackagesPage` existem — semântica Controladoria | PROVEN componente / TARGET contrato |
| RQ-DRE-INV-07 | Ato de liberação de documento ao destinatário | leitura de documentos (`list`/`get`/`resolve_download`) não consulta pacote/snapshot; sem campo `released` | **DECISION_REQUIRED** (D-DRE-RELEASE-01) |
| RQ-DRE-INV-08 | Vínculo «destinatário de consulta» (quem da DRE pode ver) | assignments são REVIEWER/COORDINATOR; `recipient_area` é atributo do pacote, não entitlement de pessoa | **DECISION_REQUIRED** (D-DRE-ACCESS-01) |
| RQ-DRE-INV-09 | Conversa visível ao destinatário | `document_message.audience` CHECK `('INTERNAL')` (V016) | **DECISION_REQUIRED** (D-DRE-COLLAB-01) |
| RQ-DRE-INV-10 | Solicitação de ajuste com ciclo próprio | `closing_clarification` é P5 pacote/revisor — não cobre pedido→resposta→confirmação por documento | **DECISION_REQUIRED** (D-DRE-COLLAB-01) |
| RQ-DRE-INV-11 | Permissão capability do destinatário | manifesto+teste estrutural pinam 2 permissions; Opção B do doc 91 aprovada e **deferida** | **DECISION_REQUIRED** (D-DRE-ACCESS-01 / manifest gate) |
| RQ-DRE-INV-12 | Projeção read-model restrita | `get_package`/`list_packages` expõem `content` com resumos P3/P4 internos | **DECISION_REQUIRED** (D-DRE-PROJECTION-01) |
| RQ-DRE-INV-13 | Wireframes dos 4 níveis | doc 112 §54 — listagem, detalhe da entrega, documento, solicitações | TARGET |
| RQ-DRE-INV-14 | Design V0.8 anterior + conversa inline | doc 112 §17 (PO aprovado), §18 (factories do kit), §19–§20 (complemento/notificação/realtime) | TARGET/PO_APPROVED |

| AC | Critério de aceite (futuro, pós-gate) | Status |
|---|---|---|
| AC-DRE-01 | Listagem exibe somente entregas autorizadas ao destinatário do usuário | TEST_NOT_RUN (gate pendente) |
| AC-DRE-02 | Competência sem pacote recebido → ausente da lista; pacote com 0 docs → empty state honesto | TEST_NOT_RUN |
| AC-DRE-03 | Pacote multi-PDF lista todos os documentos liberados | TEST_NOT_RUN |
| AC-DRE-04 | Somente versões liberadas acessíveis; versão não liberada = 404 | TEST_NOT_RUN |
| AC-DRE-05 | Consulta e download auditados; preview via viewer homologado autenticado | TEST_NOT_RUN |
| AC-DRE-06 | Solicitação de ajuste registra autor humano, texto, documento/versão; resposta não encerra | TEST_NOT_RUN |
| AC-DRE-07 | Encerramento só por ação de validação do destinatário; histórico imutável | TEST_NOT_RUN |
| AC-DRE-08 | 401 sem token; 403 sem capability/sem vínculo; 404 cross-recipient/IDOR period/package/document | TEST_NOT_RUN |
| AC-DRE-09 | Core indisponível → fail-closed | TEST_NOT_RUN |
| AC-DRE-10 | Desktop/tablet/mobile 320/390/768, claro/escuro, zoom 200%, teclado/leitor de tela | TEST_NOT_RUN |
| AC-DRE-11 | Filtros na URL, F5, back/forward, sort, cards, paginação inteligente | TEST_NOT_RUN |
| AC-DRE-12 | Help contextual em todas as superfícies (`feature-help-sync`) | TEST_NOT_RUN |
| AC-DRE-13 | Testes de contrato: projeção sem campos internos (p3/p4, audit internals, dados de outro destinatário) | TEST_NOT_RUN |
| AC-DRE-14 | Sem superfícies proibidas: relatórios TOTVS, divergências, estoque, admin, upload, validação P2, aceite/revisão P5 | TEST_NOT_RUN |

**Veredito do gate (não autodeclarado):** contratos existentes **insuficientes** — faltam representações de destinatário, liberação e audiência de conversa. `DECISION_REQUIRED` ×4 (ACCESS/RELEASE/PROJECTION/COLLAB) consolidado no Plano 113 §29.5 com alternativas, impactos e recomendação.

### DRE-ACCESS-019-RW02 — migração `closing-documents.read` → `access.dre` + Home DRE (2026-10-28)

| AC | Critério de aceite | Status |
|---|---|---|
| AC-RW02-01 | Manifesto declara `access`, `manage`, `access.dre` + legada DEPRECATED | PASS (contract test 4 permissions/13 rotas) |
| AC-RW02-02 | `access.dre` apenas → viewer-context 200, `accessDre: true`, `access: false` | PASS (backend test) |
| AC-RW02-03 | `access.dre` apenas → `/closing/documents` liberado no boundary documental | PASS (test_dre_authz) |
| AC-RW02-04 | `access.dre` apenas → rotas internas/admin negadas (≠ `.access`, ≠ `.manage`) | PASS (test_dre_authz) |
| AC-RW02-05 | Legada `closing-documents.read` apenas → mesma experiência via alias `received-documents` | PASS (rota+view testadas; deep links sob o entrypoint) |
| AC-RW02-06 | Sem permissions → viewer-context 403 / `/unauthorized` | PASS (backend + guard RW01) |
| AC-RW02-07 | Core indisponível → fail-closed (503) | PASS |
| AC-RW02-08 | Home DRE renderiza saudação + card «Fechamento Mensal» → Documentos e interações | PASS (route+component; smoke visual TEST_NOT_RUN) |
| AC-RW02-09 | Entrada no basePath redireciona à primeira rota visível autorizada (`/home` para DRE) | PASS (resolveAuthorizedEntryPath, convenção do launcher) |
| AC-RW02-10 | Usuário interno `.access` → Home interna e 3 áreas preservadas | PASS (redirect por capability só atua sem `access`) |
| AC-RW02-11 | Documentos filtrados por RECIPIENT+SUBMITTED+snapshot; download/mensagens/ajustes protegidos | PASS (proteção inalterada; PG suite DRE-019) |
| AC-RW02-12 | Smoke autenticado end-to-end (Home DRE → docs → bloqueios) | TEST_NOT_RUN — requer import do manifesto + grant `access.dre` pelo PO |
| AC-RW02-13 | Remoção da legada `closing-documents.read` | PENDING — gate posterior após homologação do papel |

### DRE-ACCESS-019-RW03 — Home compartilhada + top bar + remoção da legada (2026-10-28)

Evidência de migração no Core prod (PROVEN): `access.dre` importada na v0.1.3, papel «Acesso ao Portal Controladoria e Finanças — DRE» com a permission, 1 usuário provisionado, legada com zero grants.

| AC | Critério | Resultado |
|---|---|---|
| AC-RW03-01 | Home DRE usa o padrão da Home interna (hero, top bar, caminhos, busca, recents) — composição compartilhada, não duplicada | PASS (`HomePage` + `HUB_SECTIONS` por capability; `DreHomePage` removida) |
| AC-RW03-02 | Top bar DRE com «Início»; itens futuros só com rota+capability | PASS (shellNav por capability; teste DRE-only) |
| AC-RW03-03 | «Caminhos e funcionalidades» exibe «Central de Fechamento» → «Fechamento Mensal» → Documentos e interações | PASS (seção `closing_dre`; teste HomePage) |
| AC-RW03-04 | Interno não vê seção DRE; dual-cap sem Início duplicado | PASS (supressão `dreViewer`; testes) |
| AC-RW03-05 | Manifesto com exatamente `access`/`manage`/`access.dre` — 3 permissions/12 rotas | PASS (manifestContract) |
| AC-RW03-06 | Legada removida de BFF/MFE/rotas; `received-documents` → `not_found`; só-legado → 403/404 | PASS (test_dre_authz, viewer-context, pluginRoutes) |
| AC-RW03-07 | `access.dre` ≠ `access`/`manage`; endpoints internos inalterados | PASS (test_dre_authz) |
| AC-RW03-08 | Proteção documental inalterada (RECIPIENT+SUBMITTED+snapshot, 404, download auditado) | PASS (backend 491; PG suite DRE-019) |
| AC-RW03-09 | Descontinuação no Core via mecanismo oficial (sync do register v0.1.4), sem SQL direto | PENDING — registro produtivo pelo PO |
| AC-RW03-10 | Smoke autenticado DRE + interno (local/prod) | TEST_NOT_RUN — pós-import da v0.1.4 |

### DRE-ACCESS-019-RW04 — Home única no basePath (REWORK da RW03, 2026-10-28)

Decisão PO: UMA HomePage/UM basePath/UMA top bar/UM catálogo — audiência só muda o conteúdo autorizado.

| AC | Critério | Resultado |
|---|---|---|
| RW04-01 | Uma única HomePage compartilhada (sem `homeView`/`dre_home`) | PASS (`HomePage` sem modo; `dre_home` removido de view/nav/targets) |
| RW04-02 | Entrada canônica pelo basePath para ACCESS e ACCESS.DRE | PASS (`hasAuthorizedAppEntry`: mount no basePath com ≥1 rota autorizada; `/home` → redirect canônico) |
| RW04-03 | Top bar compartilhada | PASS (um «Início» `requiredCaps[access,accessDre]`; teste somente-DRE na mesma view `home`) |
| RW04-04/05 | Hero e Eventos no padrão único | PASS (mesma árvore; cópia DRE projetada por capability) |
| RW04-06/07/08 | Catálogo único filtrado; «Fechamento Mensal» → Documentos e interações | PASS (seção `closing_dre`; teste HomePage) |
| RW04-09/10 | Visão geral, relatórios, administração e endpoints internos negados à DRE | PASS (rotas guard `/unauthorized` fora do basePath; BFF inalterada — test_dre_authz) |
| RW04-11 | Downloads/mensagens com autorização documental intacta | PASS (sem mudança BFF; PG suite DRE-019) |
| RW04-12/13 | Sem novo MFE/BFF/permission; código de Home paralela removido | PASS (3 permissions; `dre_home`, `homeView`, redirects DRE→dre_home eliminados; sweep residual limpo) |
| RW04-14 | Deep links/F5/back-forward | PASS (rotas inalteradas; `/home` canonicaliza) |
| RW04-16 | Testes executados com evidência | PASS (vitest 382 c/ 1 flake isolado pré-existente; portal 9/9; estruturais; tsc; builds) |
| RW04-15/09 | QA visual claro/escuro, 320/390, zoom 200% | TEST_NOT_RUN — requer identidade autenticada |
| RW04-17 | Deploy governado e verificável | PENDING — portal + MFE rebuild via deploy canônico |
| RW04-18 | Documentação sincronizada | PASS (docs 91/112/113/115/23/30 + README) |
| RW04-smoke | Smoke autenticado interno + DRE | TEST_NOT_RUN — requer identidade autorizada (v0.1.5 pendente de registro pelo PO) |

### ANALYSIS-INVENTORY-001 — Inventário AS-IS do processo real de Joyce (2026-10-28)

Entrega documental: `117-analysis-001-inventario-processo-real-joyce.md`. Sem alteração de runtime. RQs abaixo são **candidatos PROPOSED** para ANALYSIS-002 — ainda não aceitos; dependem do gate PO/Joyce.

| RQ/AC | Critério | Estado |
|---|---|---|
| RQ-ANL-01 | Contrato canônico P7/MATR460 (competência/filial, `report_scope=all_products|mp_pi_pa` — DEC-12, excl. poder de terceiros, subtotais EM ESTOQUE/EM PROCESSO, `as_of`/emissão) — SB9 nunca servido como P7 | DESIGN_READY_CONDITIONED (escopo completo) / PENDING_SOURCE (recorte oficial — E2) |
| RQ-ANL-02 | Contratos H02/MATR989 e ENTRADAS_SAIDAS/MATR320; `UNAVAILABLE` nunca vira zero | PROPOSED — gate ANALYSIS-002 |
| RQ-ANL-03 | Motor determinístico da conciliação tripla (E/S − P7 − H02, paridade exata R$0,00, versão de regra, evidências citáveis) | PROPOSED — gate ANALYSIS-003 |
| RQ-ANL-04 | Drill-down de divergência por grupo de material (reproduzir localização MP da demo) | PROPOSED |
| RQ-ANL-05 | Kardex SD3 arm. 01/99 com filtros CF/INVENT — lista CF homologada por Joyce antes de parametrizar | PROPOSED — depende pergunta §17.2 doc 117 |
| RQ-ANL-06 | Análise SD1 por CC com expurgos/taxonomia/exceções homologadas | PROPOSED — depende §17.2/§17.3 |
| RQ-ANL-07 | Relação de baixas (5 ordenações) via SE5 com paridade às saídas oficiais | PROPOSED — decisão `_F190C` pendente |
| RQ-ANL-08 | Fat × MOD: contrato + consolidação com intervalo/soma homologados | PROPOSED — depende §17.4 |
| RQ-ANL-09 | Configuração de bancos/extratos por unidade; sem movimento exige comprovante | PROPOSED — depende E01 doc 34 |
| RQ-ANL-10 | Base de conhecimento CLARA versionada (glossário, regras, limites; fail-closed) | PROPOSED — gate ANALYSIS-005 |

### CONSOLIDATION-002 — Revisão dos RQ-ANL pela base canônica (2026-10-29)

Entrega documental: [Documento 118 — base canônica do fechamento](./118-base-canonica-processo-fechamento-mensal-proc0072.md). Sem alteração de runtime. As dependências dos RQs foram reavaliadas pela investigação cruzada (doc 118 §9); as classificações abaixo **substituem** os estados `PROPOSED` acima sem reabrir decisões:

| RQ/AC | Estado revisado | Fundamento |
|---|---|---|
| RQ-ANL-01 | `PROPOSED → DESIGN_READY_CONDITIONED` | binding de totalização P7 PROVEN (doc 84 §3); condicionado a E2 (params/produtor/RPO); SB9 nunca servido como P7 |
| RQ-ANL-01 | `escopo decidido — DEC-12` | PO (28/10): `all_products` = interno/conciliação, `mp_pi_pa` = entrega DRE; nomes canônicos preservados do exploratório (doc 49 §9); `A460UNIT.prw` localizado no acervo; recorte oficial segue `PENDING_SOURCE` (E2) — doc 118 §9.1 |
| RQ-ANL-01 | `filtro canônico reutilizado — SCOPE-CONTRACT-004` | `mp_pi_pa` oficial = `B1_TIPO IN (MP,PI,PA)` **+** exclusão poder3 (`third_party_materials=exclude`); PA/PI `PROVEN`, MP Δ quantificada; owner de tipos `protheus_product_types.py` preservado — nenhuma segunda regra; mecanismo oficial `PENDING` (E2) — doc 118 §9.1, doc 85 BR-R03-009 |
| RQ-ANL-01 | `contratos fechados — READINESS-005` | doc 119: consulta/export/doc-DRE/segurança/erros/plano executável; poder3 verificado em dados (QTNP/QTER loc01, F4_PODER3 direção, exclusão por produto); EM PROCESSO = MATR989 `as_of` PROVEN; gate `PENDING_EXTERNAL_EVIDENCE` com subconjunto implementável (`all_products` + infra completa; `mp_pi_pa` `parity_unverified` até E2) — 28/10/2026 |
| RQ-ANL-02 | `PROPOSED → DESIGN_READY` | DR-05/06 (MATR320 130/130) e DR-08 (MATR989) provadas; E5/E8 como pendências de fonte oficial |
| RQ-ANL-03 | `PROPOSED → DESIGN_READY` | regra homologada (TÉO 06.2, doc 15.1); depende dos contratos de dados RQ-ANL-01/02 |
| RQ-ANL-04 | `PROPOSED → DESIGN_READY` | decomposição por produto provada (doc 84 §4.3) |
| RQ-ANL-05 | `PROPOSED → DESIGN_READY` | dependência §17.2 **resolvida**: filtros CF/TES provados por paridade (doc 83 R06/R07) — não depende mais de homologação verbal |
| RQ-ANL-06 | `PROPOSED → DESIGN_READY_PARTIAL` | seleção R10 provada (DR-11); taxonomia Direto/Ind/Adm exige catálogo-mestre (E10) — não embutir classificação inventada |
| RQ-ANL-07 | `PROPOSED → IMPLEMENTED_PENDING_PARITY` | rotas api-delpi+BFF existem; residual = validação de paridade contra artefato oficial + fonte `DLP06R01` receber (E1); decisão `_F190C` **resolvida** (produtor pagar = `FINR190_DLP.PRX`) |
| RQ-ANL-08 | `PROPOSED → DESIGN_READY` | modelo DLP204 provado linha-a-linha (doc 84 §5.3); G5 condicionado a E9 |
| RQ-ANL-09 | `PROPOSED → DECIDED_SEED_PENDING` | lista configurável decidida (E01); seed inicial pendente (GAP-06) |
| RQ-ANL-10 | `PROPOSED → REFERENCE_READY` | doc 118 §10 é a referência de conhecimento + doc 94 |
| RQ-ANL-11 (novo) | `PROPOSED` | contrato transversal `as_of`/versionamento de emissões (DR-16) |
| RQ-ANL-12 (novo) | `BLOCKED` | consumo por OP — GAP-01 (EVIDENCE_NOT_FOUND) |
| RQ-ANL-13 (novo) | `PROPOSED` | entregáveis externos R13/R14 via P2 upload com roles configuráveis (E05) |
| RQ-ANL-14 (novo) | `PROPOSED` | `STOCK_CLOSED` canonical owner state (T03/E5) |

### IMPLEMENTATION-009 — análises independentes da gestão documental (2026-10-29)

Execução `CF-PROC0072-ANALYTICS-INDEPENDENCE-IMPLEMENTATION-009`. Registro completo: [doc 119 §12](./119-contratos-p7-implementacao-readiness.md). DEC-ANALYTICS-INDEPENDENCE: a aba «Relatórios e divergências» opera por mês de referência sem competência formal, checklist, documentos ou pacote DRE.

| RQ/AC | Critério | Estado |
|---|---|---|
| RQ-ANL-02 → IMP-09.R05 | Consulta R05 (MATR320 SD1/SD2/SD3/SF4 + SA SB9) | PASS (`/closing/stock-movements`, 200 autenticado, 401 anônimo) |
| IMP-09.R08 | Consulta R08 (motor MATR989: físico loc99 + alocado RE−DE) | PASS (`/closing/work-in-process`, composição exibida) |
| RQ-ANL-03.analítico | Conciliação analítica E/S−P7−H02 | PASS (`EXACT_PARITY` 0,00 em 2026-09; `not_persisted`, P3 intacto) |
| IMP-09.PDF | Export CSV+PDF nos 3 relatórios | PASS (R05/R08/P7 — `text/csv` + `application/pdf`, metadados+hash+watermark) |
| IMP-09.IND | Independência documental (cenários A–F) | PASS — deep links + dados + export sem acionar fluxo documental (smoke 30/30) |
| IMP-09.NEG | Sem falso zero; operando ausente → `INELIGIBLE` | PASS (testes BFF + smoke C4) |
| IMP-09.AUTH | Falha de autorização propagada | PASS (401/403/`scope_unavailable` mapeados; anônimo 401) |
| Paridade | Homologação MATR320/MATR989 oficial | `PENDING` — `officialMatr320/989=false`, watermark não-oficial |

### IMPLEMENTATION-006 — P7 na página Relatórios e divergências (2026-10-29)

Execução `CF-PROC0072-P7-IMPLEMENTATION-006`. Registro completo: [doc 119 §11](./119-contratos-p7-implementacao-readiness.md). Motor único P7 entregue (`SB9` ex-`MV_LOCPROC` + `MATR989` `as_of`); causa raiz «fonte indisponível» = flag off + provisão S2S incompleta — resolvida (client/scope/audience/token URL pelo gateway).

| RQ/AC | Critério | Estado |
|---|---|---|
| RQ-ANL-01 → IMP-01 | P7 integrado à página existente de Relatórios e divergências | PASS (rota contextual `reports/stock-inventory`, smoke S1) |
| IMP-02 | Causa «fonte indisponível» diagnosticada e corrigida | PASS (S2S cf-api provisionado; cadeia MFE→BFF→api-delpi→TOTVS 200) |
| IMP-03 | Consulta real ao Protheus via api-delpi | PASS (SB9/SB1/SD3/SC2; 7.929 itens 09/2026) |
| IMP-04/05 | `all_products` + `mp_pi_pa` por `B1_TIPO` canônico | PASS (mesmo motor; `mp_pi_pa` 6.412 vs 7.929 itens) |
| IMP-06/07 | Mesma regra de cálculo; sem SQL duplicado | PASS (motor único api-delpi; BFF proxy; MFE render-only) |
| IMP-08/09/10 | Sem permission nova; `.access` autoriza; `.access.dre` não autoriza | PASS (`cf-e2e-denied`→403 live; BFF fail-closed; 3 permissions intactas) |
| IMP-11/12 | Valores/proveniência honestos; ausência nunca vira zero | PASS (`source_missing`/`incomplete`/`no_matching_items` tipados; `parityStatus=PENDING`; `officialP7=false`) |
| IMP-13 | Exportação identificada por escopo | PASS (CSV: metadata+SHA-256+watermark; filename carrega escopo; smoke S10–S12) |
| IMP-14 | Paridade testada e classificada | PENDING — `all_products` estrutura PROVEN (PA/PI/II bit a bit; MP drift +8.182,43 STALE_EVIDENCE); `mp_pi_pa` PENDING (E2) |
| IMP-15/16 | Interface existente preservada; testes/build documentados | PASS (43+31+12 api/BFF, 33 MFE, tsc limpo, build MFE servido) |
| IMP-17 | Deploy governado | PASS — `fd1d2e02b` pushado; `srv-api` pull + `up-prod-sequential.sh --build` (api-delpi→BFF→MFE); 3 serviços healthy; `remoteEntry` 200; rollback = revert + rebuild |
| IMP-17b | Pré-condições S2S prod | PASS — checker canônico 6/6; flag ON; allowlist; token prod iss/aud/scope corretos; `ServiceTokenValidator` S2S_ACCEPT |
| IMP-18 | Smoke autenticado | PASS local — 12/12 (`cf-e2e-access`, `p7_impl006_smoke.cjs`); prod `TEST_NOT_RUN` — sem persona sancionada, reservado à homologação |
| IMP-19 | Documentação e Help | PASS (docs 119§11/118/49/85/112/113/23/README; helpTooltips) |
| IMP-20 | GATE-FINAL revisão | PASS — grandTotal fail-closed (nunca `stock+0` mascarado); CSV formula-injection sanitizado (OWASP); política monetária 6dp documentada+testada; diff 33 arquivos escopo puro |

### REWORK-008 — Integração P7 × conciliação P3 na página Relatórios e divergências (2026-10-29)

Execução `CF-PROC0072-P3-P7-INTEGRATION-REWORK-008`. Registro completo: [doc 119 §11.7](./119-contratos-p7-implementacao-readiness.md). **Causa raiz PROVEN:** o `UNAVAILABLE` por domínio no contrato P3 (`closing_reconciliation`, BFF) significa «sem fonte elegível registrada/validada» — registro governado por `PUT /{period}/p3/reconciliations/{domain}` — e não indisponibilidade da consulta operacional `/closing/stock-inventory`; o MFE colapsava ambos em «Fonte indisponível». Correção de apresentação (sem mudança de contrato): `fetched_at=null` → «Não registrada»; P7 sem `AVAILABLE` + consulta com dados → «Conciliação pendente» + «consulta disponível». Dois totais distintos reconciliados: `historicalTotal` (SB9 c/ loc99) = 14.469.584,01; `grandTotal` = historical + alocado MATR989 = 14.638.712,48.

| RQ/AC | Critério | Estado |
|---|---|---|
| RW-01 (AC-01) | Causa raiz R03 identificada em código/contrato | PASS — sintetização `UNAVAILABLE` em `get_p3_state` × consulta operacional independente |
| RW-02 (AC-02/03/09) | Consulta disponível ≠ elegível P3; estados consistentes nas duas superfícies | PASS — «Conciliação pendente»+«consulta disponível» no painel e na página P7; «Não registrada» para domínio sem registro |
| RW-03 (AC-04) | Paridade pendente visível | PASS — selo/banner `PENDING` preservado |
| RW-04 (AC-05/20) | P3 não consome valores inelegíveis; sem falso zero | PASS — células `—`; nenhum caminho alimenta P3 com o total operacional |
| RW-05 (AC-06) | Diferença dos dois totais investigada | PASS — historical (SB9 incl. loc99) × grandTotal (+alocado): Δ = 169.128,47 = EM PROCESSO alocado |
| RW-06 (AC-07) | R05/R08 classificados por evidência real | PASS — sem produtor api-delpi (RQ-ANL-02 DESIGN_READY) → «Não registrada» honesto; conciliação bloqueada |
| RW-07 (AC-08) | Indicadores consistentes | PASS — contagens derivam dos mesmos critérios dos itens |
| RW-08 (AC-10/11/12) | Sem alteração de motor/permissão; DRE restrito | PASS — zero diff em api-delpi/BFF/authz; 3 permissions intactas |
| RW-09 (AC-13/14/15) | Testes + smoke local + QA visual | PASS — MFE 49/49 arquivos afetados, suite 390/391 (flake pré-existente não relacionado), tsc/build limpos, smoke autenticado 14/14 (`cf-e2e-access`), screenshots `rework008_*.png` |
| RW-10 (AC-16) | Documentação e Help sincronizados | PASS — docs 118/119/113/112/23 + `helpTooltips.ts` |
| RW-11 (AC-17/18/19) | Commit/push/deploy/smoke prod | PASS — `4bc90151df` pushado (12 arq. escopo puro); deploy `srv-api` MFE-only via script oficial; SHA/bundle/remoteEntry/401 verificados; smoke prod usuário `TEST_NOT_RUN` (sem persona sancionada) |

### CONTRACT-GATE-014 — RQ/AC R06 (CPV/Kardex MATR910) + R07 (Inventários) (2026-10-29)

Execução `CF-PROC0072-R06-R07-CONTRACT-GATE-014`. Contratos TARGET e decisões: [doc 122](./122-gate-contratual-r06-r07-matr910-2026-10-29.md). Regras `PROVEN`: doc 85 §6/§7. Estado `TARGET` = contrato proposto aguardando aprovação do gate de implementação; implementação bloqueada (doc 122 §12).

| RQ/AC | Critério | Fonte de evidência | Estado |
|---|---|---|---|
| RQ-R06-01 | Consulta kardex: `GET /financeiro/stock-kardex` — UNION SD1(`D1_DTDIGIT`)+SD2(`D2_EMISSAO`)+SD3(`D3_EMISSAO`), `F4_ESTOQUE=S` (SD1/SD2), `D3_ESTORNO<>S`, `D*_ORIGLAN<>LF`, `B1_COD<>MV_PRODIMP`, `D*_LOCAL=warehouse` | `matr910_dlp.prx` L475–524; doc 85 BR-R06-001/002 | TARGET |
| RQ-R06-02 | Resumo kardex: totais entrada/saída por filial/armazém/`B1_TIPO`; `topProductsByCost` global sobre o conjunto autorizado (nunca sobre a página) | doc 122 §4.1; ranking §12 doc 121 | TARGET |
| RQ-R06-03 | Detalhe por produto: `…/stock-kardex/products/{code}` — cadeia de saldo linha a linha desde `B9_QINI`/`B9_VINI1` @mês anterior; ausente → `source_missing` | doc 85 BR-R06-007 (1.544/1.544) | TARGET |
| RQ-R06-04 | Grão = movimento em bloco produto×armazém×período; campos doc, data + `dateField`, TES/TM/CF, REF (`F-|P-|OP|CC`), qtd/valor entrada-saída, `unitCost`, `costAsOfSource`, `runningQty`/`runningValue` | doc 85 BR-R06-004/005/006 | TARGET |
| RQ-R06-05 | Custo `as_of`: `TTAT_OLD` quando presente, senão corrente; devoluções `TIPONF='D'` na coluna oposta ×−1 | doc 85 BR-R06-006/008 (9.357/9.357; 11/11) | TARGET |
| RQ-R06-06 | CPV vivo: `GET /financeiro/cpv` (D-O1) — semântica `SUM(D2_CUSTO1)`, `D2_CF∈{5101,5124,6101,6124}`, `D2_EMISSAO`, custo corrente por decisão PO 23/10 (`asOfConvention:"live"`); saídas kardex ≠ CPV registrado em `parityNotes` | doc 85 BR-R06-010; `cpv_query_repository.py` | TARGET |
| RQ-R07-01 | Consulta inventários: `GET /financeiro/inventory-adjustments` = SD3 `D3_DOC='INVENT'`, TES 999/RE0 saída + 499/DE0 entrada, mesma engine do kardex | doc 85 BR-R07-001/002; DR-10 | TARGET |
| RQ-R07-02 | Resumo inventários: entradas/saídas/líquido por filial/armazém; armazéns multi (evidência 01+99); `topImpacts` global | doc 85 BR-R07-003 (Σ 2.348,108 / R$185.103; líquido −28.460,098) | TARGET |
| RQ-R07-03 | Detalhe: produto, doc `INVENT`, `D3_TM`, natureza, qtd/valor, `D3_CUSTO1` `as_of`, data, proveniência (SB7 opcional não-autoridade) | doc 85 BR-R07-002; `inventory_adjustments_repository.py` | TARGET |
| RQ-X-01 | Filtros: `period` `YYYY-MM` (regex), `branch` `all|01|02`, `warehouse` multi, `product_code`, `nature`, `document_kind` — validação tipada 400 | molde `stock_inventory_router.py` | TARGET |
| RQ-X-02 | Ordenação: allowlist server-side; default data + `*_NUMSEQ`; nenhuma ordenação fora da lista | doc 85 BR-R06-004 | TARGET |
| RQ-X-03 | Paginação: tier `page_50_200`, OFFSET/FETCH, `page≥1` | `pagination_query.py` | TARGET |
| RQ-X-04 | Proveniência: `source`, `provenance{engine:"matr910_contract", officialProducer:"MATR910", snapshotDate, asOfConvention}`, `officialMatr910:false`, `parityStatus:"PENDING"` | molde R03/R05/R08 | TARGET |
| RQ-X-05 | Erros tipados: 400 validação, 401 sem Bearer, 403 `scope_unavailable`, 409 `not_exportable`, 503 indisponível; `source_missing` fail-closed — sem substituição de mês nem zero fabricado | molde `stock_inventory` + DR-16 | TARGET |
| RQ-X-06 | Monetário: `CAST(... AS DECIMAL(30,9))` por linha antes do SUM; saída `DECIMAL(28,6)` serializada como string; exibição 2dp half-up sobre soma bruta; tolerância de paridade zero | doc 84 §4.3/§5.2; doc 15.1 | TARGET |
| RQ-X-07 | Segurança: `controllership-finance.access` efetiva (Core RBAC); S2S `stock-kardex.read` + `allowed_clients=("controllership-finance-api",)`; flag `FINANCEIRO_STOCK_KARDEX_ENABLED`; delegated bearer → api-delpi; sem permission nova | doc 122 §5; `s2s_service_access.py` | TARGET |
| RQ-X-08 | Export CSV/PDF (se D-O2 aprovado): bloco de identidade, watermark «PARIDADE OFICIAL PENDENTE», SHA-256, `csv_safe_text`, timeout 120s no BFF | `report_export_common.py` | TARGET (pende D-O2) |
| RQ-X-09 | Tools CLARA READ: `get_stock_kardex`, `get_stock_kardex_summary`, `get_stock_kardex_product`, `get_inventory_adjustments`, `get_inventory_adjustments_summary`, (`get_cpv` se D-O1) — delegam às rotas BFF via `_call_route`; `MCP_TOOL_NAMES` 43→47/48 | doc 122 §4.4 | TARGET |
| RQ-X-10 | Paridade Portal×CLARA: mesmos parâmetros → mesmos valores, quantidades, classificações, proveniência e `parityStatus`; testes no padrão `test_clara_parity_016.py` | doc 121 §14 | TARGET |
| RQ-X-11 | Corpus+Help: `doc-122` autorizado no manifest (feito neste pacote); Help `reports.stockKardex`/`reports.inventoryAdjustments` na implementação; ingestão governada com versão/hash comprovados | doc 122 §7 | TARGET (manifest done; ingestão pós-impl) |
| RQ-X-12 | Não-regressão: R01/R02/R03/R05/R08, conciliação `IDENTITY_ONLY`, P3, matriz R01–R15 e as 43 tools existentes — zero alteração funcional | suites api-delpi/BFF/MFE + `test_clara_mcp_surface.py` | TARGET |
| RQ-X-13 | Paridade técnica × artefatos (etapa E8): R06 9.357 movimentos / 1.544 cadeias de saldo; R07 45/45 + totais oficiais — comparação do contrato implementado, não da reconstrução | `cpv 09 26 matriz.xlsb`, `Invent.xlsb`, doc 84 §5.1 | TEST_NOT_RUN (implementação futura) |


### IMPLEMENTATION-015 — R06 (CPV/Kardex) + R07 (Inventários) implementados (2026-10-29)

Execução `CF-PROC0072-R06-R07-IMPLEMENTATION-015`. Gate 0: **D-O1..D-O4 aprovadas pelo PO em sessão 29/10/2026** (registro: doc 122 §9). Contratos implementados conforme TARGET do doc 122 §4; motor único `stock-kardex` (UNION SD1/SD2/SD3 + TTAT `as_of` + SB9 fechamento anterior); CPV dedicado (D-O1) reusando `CpvQueryRepository`/`GetCPVUseCase`; export CSV/PDF (D-O2); R07 view dedicada (D-O3); sem filtros de saldo zero/negativo (D-O4). CLARA 43 → 48 tools READ.

| RQ/AC | Critério | Evidência de execução | Estado |
|---|---|---|---|
| RQ-R06-01 | Engine kardex UNION SD1/SD2/SD3 com filtros MATR910 | `stock_kardex_sql.py` + `_engine.py`; live f02/loc01/2026-09: 16.178 movimentos | PASS |
| RQ-R06-02 | Resumo por tipo/armazém + top produtos global | `get_stock_kardex_summary_use_case.py`; live: entry 11.889.924,464 / output 18.668.496,799 | PASS |
| RQ-R06-03 | Drill por produto com cadeia de saldo | `…/products/{code}` + `get_kardex_product`; running qty/value | PASS |
| RQ-R06-04 | Grão movimento + campos do contrato | response schema `stock_kardex_response.py`; route tests 13/13 | PASS |
| RQ-R06-05 | Custo `as_of` TTAT_OLD + devoluções sinal | `_engine.classify_movement` + TTAT por tabela-fonte; live: 8.869 movimentos com TTAT aplicada | PASS |
| RQ-R06-06 | CPV dedicado `/financeiro/cpv` (D-O1) | `get_financeiro_cpv_use_case.py` sobre `CpvQueryRepository`; live f02/2026-09: CPV 1.804.629,699 / 561 movimentos | PASS |
| RQ-R07-01 | `inventory-adjustments` = mesmo engine, INVENT | live f02/2026-09: 45 movimentos (loc01=32 + loc99=13) = universo do artefato | PASS |
| RQ-R07-02 | Resumo inventários | live: entry 2.350,667 / output 30.812,499 / net −28.461,832 | PASS |
| RQ-R07-03 | Detalhe por produto/doc/TM | mesma resposta do kardex com `document_kind=invent` | PASS |
| RQ-X-01 | Filtros tipados `YYYY-MM`, branch, warehouse multi | `stock_kardex_request.py`; 400 em período inválido | PASS |
| RQ-X-02 | Ordenação allowlist | `sort in {date,product}` + `*_NUMSEQ` interno | PASS |
| RQ-X-03 | Paginação server-side | `page/page_size` OFFSET/FETCH | PASS |
| RQ-X-04 | Proveniência + `parityStatus:PENDING` | `minha-delpi-r06-kardex-engine`, `as_of_ttat`, `sb9_previous_month_end` | PASS |
| RQ-X-05 | Erros tipados fail-closed | `source_missing` retornado p/ mês sem SB9 (live-verificado) | PASS |
| RQ-X-06 | Monetário DECIMAL(30,9)→28,6 string | SQL CAST + serialize decimal | PASS |
| RQ-X-07 | AuthZ S2S + flag + delegated user | `stock-inventory.read`, `controllership-finance-api`, flag OFF→403 testado | PASS |
| RQ-X-08 | Export CSV/PDF watermark+hash | live: CSV 140 linhas/45 itens; PDF 187.685 bytes `%PDF-1.4` | PASS |
| RQ-X-09 | CLARA tools READ 43→48 | 5 tools via `_call_route` (`get_stock_kardex(+_summary)`, `get_inventory_adjustments(+_summary)`, `get_cpv`); `test_clara_mcp_surface` 48/48 | PASS (drill via `product_code` param) |
| RQ-X-10 | Paridade Portal × CLARA | mesmas rotas BFF via `_call_route` — mesma resposta por construção | PASS estrutural; e2e autenticado pendente smoke |
| RQ-X-11 | Corpus+Help | `helpTooltips.ts` R06/R07 + docs 120/121/122 atualizados; re-ingestão pendente E9 | PASS (ingestão pendente) |
| RQ-X-12 | Não-regressão R01/R02/R03/R05/R08 | suites BFF/MFE + api-delpi (ver relatório) | PASS |
| RQ-X-13 | Paridade × artefatos XLSB | E8 executado (2026-10-29): `cpv 09 26 matriz.xlsb` × engine f02/loc01 — **1.544/1.544 produtos com contagem de movimentos idêntica; 9.357 movimentos, qtd entrada (6.209.264,643) e qtd saída (9.729.058,452) EXATAS**; 26 produtos `MOD*` (+6.821 mov, qtd+valor zero) fora do escopo da emissão; valores divergem por convenção `as_of` TTAT (entry −4,27M, output −1,28M — documentada). R07: 45/45 movimentos do doc 85. | PASS (divergências classificadas; homologação oficial = nova emissão — PENDING) |
