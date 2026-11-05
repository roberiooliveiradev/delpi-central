# 244 — Remoção integral de paginated_result_semantics.py e correção dos consumidores

**TASK_ID:** DELIA-C3-PAGINATED-RESULT-SEMANTICS-FULL-REMOVAL-AND-CONSUMERS-01
**DATE:** 2026-11-05
**STATUS:** IMPLEMENTATION_REQUIRED / NOT_EXECUTED
**SOURCE HEAD INSPECTED:** 19b2a4b74e18915352a341d475b4540e56b1b287
**TARGET:** remover integralmente `delia-api/app/application/capability_provision/paginated_result_semantics.py` (802 linhas), sem copiar o módulo nem manter classificadores locais de intenção por regex.
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED.

## 1. Reancoragem

Antes de qualquer diff: git status/HEAD/origin, Project Instructions/.cursor, 16→50→17→49→51→52→21→20→25, arquitetura, product spec, specs temáticas, doc 239–243 e ledger. Documentação de arquitetura não basta para declarar consumidores mortos. Revalidar fase/CP/RQ, owner, contracts, tests.

**EXISTING_EQUIVALENT:** YES para Agent/typed tool/semantic interpretation (Pydantic AI); YES para EvidenceFacts/Outcome, source/provenance and owner pagination contract; TO_INVENTORY para projeção de paginação já existente fora deste módulo. **REUSE_DECISION:** REUSE Pydantic AI para intenção; EXTEND mínimo existente de outcome/Evidence para paginação factual; REMOVE módulo e todas as heurísticas proprietárias.

## 2. Mapa de uso comprovado no HEAD

- `orchestration.py` importa `PersonalTicketScope, ResultIntent, arguments_include_personal_assignee, arguments_include_requester_filter, classify_personal_ticket_scope, classify_result_intent, count_message_for_visible_query, extract_pagination_envelope, personal_scope_response, resolve_count_semantics, unique_structural_ticket_list_capability` (linhas ~158–170).
- `orchestration.py::_project_paginated_personal_or_count` (~1046–1099) invoca os classificadores por regex para decidir escopo pessoal/COUNT/LIST e resposta, e `render_specialist_outcome_rich` chama essa projeção (~3038).
- `orchestration.py::_activity_outcome_summary` (~3576) chama `extract_pagination_envelope` para não mentir sobre contagem de página parcial.
- `outcome_assessment.py` importa `extract_pagination_envelope` (~30) e usa dentro de `outcome_facts` (~1644) para `coverage_complete`, `total_count`, `has_business_evidence`, `explicit_empty`.
- `unique_structural_ticket_list_capability` foi reexportada por compatibilidade em doc 242, mas não foi localizada chamada dentro de `orchestration.py`; verificar testes/consumidores externos antes de remover.
- `pydantic_ai_investigation.py` não importa diretamente este módulo no HEAD inspecionado; recebe os resultados através das gates e Outcome existentes.
- Outros usos dinâmicos/testes/imports fora desses arquivos: **TO_INVENTORY**, executar `rg`+AST/trace local; 0 matches não prova ausência.

## 3. Remoção obrigatória por responsabilidade

### REMOVE

- Apagar arquivo inteiro, import e todas as referências, sem alias/reexport residual.
- Eliminar `classify_result_intent`, `classify_personal_ticket_scope`, `is_ticket_domain_inquiry`, `schema_supports_ticket_list_action`, `unique_structural_ticket_list_capability` e respectivas regex/listas de palavras para reconhecer perguntas. Pydantic AI Agent e tool schemas decidem semântica e capability, não Application regex.
- Remover `_project_paginated_personal_or_count` como classificador de linguagem/escopo, e substituir somente os controles factuais que realmente forem necessários para composição.
- Remover funções de strings e textos artificiais de resposta a contagens, preservando renderer atual e evidências autoritativas.
- Remover `DEFAULT_MAX_PAGES` e rotinas de page-walk locais com consumers inexistentes; quando houver paginação necessária, preferir API de owner fornecer total ou Pydantic AI invocar READs governadas com schema normal; nenhuma paginação que extrapole deadline/budget.

### KEEP BUSINESS CONTRACT, NOT THIS FILE

- Total de página retornado **nunca** é `total_count` quando `has_more=true`.
- `total_count` só é FACT quando explicitamente publicado pelo owner autorizado, ou agregação completa, auditável e bounded em rota autorizada.
- `coverage_complete` deve ser false para página incompleta, unknown quando não houver prova.
- `explicit_empty` somente quando o owner comprovar vazio, não por página vazia sem total/has_more autoritativo.
- "Meus chamados", "atribuídos a mim", "abertos por mim": modelo pode propor escopo, mas backend/domain owner valida identidade e filtro, nunca inventa ou aplica scope derivado de modelo como autorização.
- Payload de metadata, page_size, returned_count, HTTP 200 não comprova total.
- Honest partial/insufficient outcome, SourceRef and no false GROUNDED.

A projeção factual tipada mínima deve usar owners/contratos existentes; preferir `outcome_assessment.py` / `EvidenceFacts` ou Domain contract atual ao invés de criar outro serviço `pagination_semantics`. **Não transferir todo o arquivo para outro módulo**. Separar dados de owner de interpretação de usuário.

## 4. Execução bounded

1. Reanchor e mapear import/calls com AST + grep em App, adapters e tests; capturar baseline.
2. RED tests para `has_more=true`, `total_count`, page_size-vs-total, aggregation completeness, scope pessoal wrong filter, empty result, negative fake count, JSON/NDJSON, session context.
3. Apagar o arquivo; atualizar `outcome_assessment.py` para extrair envelope factual pelo contrato legítimo existente, evitando nova biblioteca genérica se um parser já existir.
4. Corrigir `orchestration.py` e o renderer para não chamar classificação por regex; usar proposta tipada do Agent somente onde necessária, com owner filter verification e honest insufficient if no scope proof.
5. Atualizar imports, tests, fixture aliases, plugin contracts; nenhum remanescente de `paginated_result_semantics`, `classify_personal_ticket_scope`, `classify_result_intent`, `unique_structural_ticket_list_capability` no runtime.
6. Testar E01–E10 local reconstruído, mais casos pessoais e listas paginadas; full delia-api tests/ --ignore=tests/live **após último diff** e import/architecture tests; nenhum teste apagado sem equivalência comportamental.
7. Documentar LOC removida líquida, contracts, testes/eval, evidence/outcome, SHA; atualizar docs 239/243, ledger e relatório de execução no próximo número disponível; commit/push main após testes. Sem deploy produtivo.

**GATE:** se a remoção comprometer escopo de identidade, total correto, a proveniência ou a autorização de owner, resultado REWORK/INCONCLUSIVE, não PASS. HTTP 200 != business outcome.

## 5. Relatório

TASK_ID, BASE_HEAD, FINAL_SHA, PUSH_VERIFIED, FILE_DELETED, CONSUMER_IMPORTS_REMOVED, SEMANTIC_REGEX_REMOVED, EQUIVALENT_EXISTING_OWNER, CONTRACT_PROOFS, LINES_BEFORE_AFTER, RED_GREEN, FULL_BACKEND_SUITE, PERSONAL_TICKET_SCOPE_NEGATIVES, COUNT_TOTAL_PAGINATION_NEGATIVES, E01_E10, EVALUATED_SHA, LOCAL_RUNTIME_SHA, SOURCE_REF, FALSE_GROUNDED, RESIDUAL_SEARCH, DOCS_LEDGER, VERDICT, PRODUCTION_DEPLOY=NOT_AUTHORIZED.

**No source code changed in this planning record.**
