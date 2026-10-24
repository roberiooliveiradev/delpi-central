# DAVI — Endereçamento semântico de seções do corpus governado (R7 dependency)

**TASK_ID:** `DAVI-GOVERNED-KNOWLEDGE-SEMANTIC-SECTION-ADDRESSABILITY-R7-01`
**OWNER:** `api-delpi` / DAVI — **CONSUMER:** DÉLIA (Trilha B, revisão R7 `e29beded`)
**ESTADO:** implementação local completa; `DEPLOY_AUTHORIZED=NO` — aguarda revisão independente (gate da task).

## 1. Lacuna (evidência R7)

A capability `read_governed_technical_knowledge` só endereçava trechos por identificadores internos (`sNNNN`) descobertos via paginação. A DÉLIA não conseguia transformar um assunto ("nomenclatura de terminal bala") na seção normativa `TERM. BALA` sem conhecer a estrutura interna do documento. Não havia falha de conteúdo — a norma MP V2 documenta `TERM. BALA` (s0054/s0055) — a falha era de **endereçamento**.

## 2. Reuse gate (provado pelo HEAD)

`RESPONSIBILITY=api-delpi governed knowledge READ`; `OWNER=ReadGovernedTechnicalKnowledgeUseCase + GovernedKnowledgeRepository + rota OpenAPI existente`; `SOURCE_OF_TRUTH=corpus publicado + manifesto + topic index (imutáveis)`; `EXISTING_EQUIVALENT=YES_PARTIAL — excerpt splitting, paginação, tokens/phrase-fillers do retrieval, argumentConstraints, candidate tokens`; `REUSE_DECISION=EXTEND — mesmo use case, mesma rota, mesmos erros tipados`.

Não criados: nova tool MCP, índice vetorial/full-text, embeddings, planner, tabela assunto→seção, dependência de provider. Nenhum ID de seção está codificado no algoritmo.

## 3. Contrato estendido (compatível)

`subject` opcional (string 1–240) em `GET /knowledge/technical-guides/{topic}`:

```json
{ "topic": "mp_description_standards", "subject": "nomenclatura de terminal bala", "corpus_version": 2, "page_size": 3 }
```

- Ranking **determinístico e lexical** sobre conteúdo verificado do documento: tokens do assunto × tokens do `heading_path` (peso 3×) e do corpo da seção, ponderados por **IDF document-local** (`log((N+1)/(df+1))` — mesmo perfil do action catalog). Termo ubíquo que casa nunca contribui zero (`_TERM_MIN_WEIGHT=0.10`) — fix causal para `df=N` ⇒ idf=0 ⇒ falso `NO_MATCH`.
- `heading_path`: hierarquia `##`/`###` reconstruída; headings repetidos ("Objetivo", "Estrutura", "Exemplo") herdam o último heading **único** do mesmo nível e mesmos ancestrais — heurística derivada do próprio documento, sem tabela de domínio. Seções cujo corpo é só o próprio heading não elegíveis para assunto (não carregam conteúdo).
- `subject` combinável com `section` (ranking dentro do escopo). Compatível: `section`, `page`, `page_size`, `corpus_version` inalterados; chamadas sem `subject` idênticas.
- Zero match → `items=[]`, `coverage=NO_MATCH`, `matched_terms`/`unmatched_terms` (insuficiência documental honesta — nunca fabrica seção).
- `selection ∈ {document, section, subject, subject+section}`; `items[].relevance` e `items[].heading_path` expõem a fundamentação da escolha.
- Classificações preservadas: `GUIDANCE_NOT_DOMAIN_TRUTH`, `UNTRUSTED_DOCUMENT_CONTENT`.
- Allowlist: `subject` em `approvedInputFields` + `argumentConstraints {minLength:1, maxLength:240}`; `heading_path`, `relevance`, `selection`, `subject`, `matched_terms`, `unmatched_terms` em `approvedResponseFields`. Constraints continuam vindas do allowlist (`argumentConstraints` é a fonte governada).

## 4. Fluxo MCP preservado

```
consumer → discover_delpi_information → read_governed_technical_knowledge
→ candidate_token → execute_delpi_information → rota real (ASGI executor)
→ GovernedKnowledgeRepository → excerpts ranqueados
```

`NEW_MCP_TOOLS=0`; `NEW_KNOWLEDGE_ENGINES=0`; `NEW_REGISTRIES=0`; `operationId` estável; `responseContract=governed_document_guidance` inalterado.

## 5. Resultados medidos (offline, corpus publicado real)

| Assunto | Top | Nota |
|---|---|---|
| `terminais tipo bala` | s0054 "Terminais (Genérico) / Estrutura" (0.332) | `TIPO DE TERMINAL — ex.: BALA`; s0055 exemplo `TERM. BALA ...` é o #2 (0.232) |
| `term. bala` / `TERM. BALA` | s0054 + s0055 empatados (0.222) | trecho `TERM. BALA` dentro da janela page_size=3 |
| `nomenclatura de terminal bala` | s0054 → s0055 | designação + regra |
| `terminais genericos` | família "Terminais (Genérico)" | assunto de família sem designação |
| `revestimentos e cores` | s0124 (1016 · Resistores) | outra família MP |
| `furo e sobra de inventário` (V1) | seções do playbook de ajustes | prova do piso de especificidade |
| `protocolo de irrigação` | `items=[]`, `NO_MATCH` | insuficiência honesta |

Metamórficos: caixa alta/baixa, ordem de tokens, pontuação, termo inserido → mesma seção top.

## 6. Testes

- `tests/test_davi_knowledge_subject_addressability.py`: **30 testes** — MP/PI positivos, NO_MATCH honesto, compatibilidade (V1/V2 sem `subject`, `section`, paginação, versão inválida, tópico inexistente, limites), segurança (injeção no assunto tratada como texto), metamórficos, e **execute path real**: discover → candidate_token → `execute_delpi_information` → `AsgiCatalogActionExecutor` → rota → `BALA` no corpo retornado.
- Regressão: `test_davi_live_governed_knowledge` + `_v2` + `test_davi_discovery_knowledge_selection` = 80 PASS; slice DAVI (`davi|discovery|governed|allowlist|openapi`) = **1506 PASS / 0 FAIL**.

## 7. Segurança / limites

- AuthZ backend inalterada (`api-delpi.access`, fail-closed); rota READ idempotente, sem efeito material.
- `subject` é texto puro tokenizado — injeção/paths maliciosos viram tokens sem efeito; sanitização de saída (`html.escape`, 4 KiB/excerpt) inalterada.
- Bounded: scoring O(seções × termos) sobre UM documento já carregado; `page_size ≤ 3`; sem scan ilimitado; sem chamadas externas.

## 8. DÉLIA / R7

A dependência DAVI-side identificada na R7 está endereçada: o consumidor localiza a seção por assunto sem conhecer `sNNNN`. **Não** resolve automaticamente O2/R7 — a homologação integrada ("Me dê dois exemplos de terminal bala" retornando dois registros verificáveis) pertence à Trilha B. `DÉLIA_O2=INCONCLUSIVE`; `R4_AUTHORIZED=NO`; status R7 inalterado.


## 9. Revisão independente da coordenação — 2026-10-24

**REVIEW_VERDICT=ACCEPT_WITH_RESIDUAL (implementação/contrato local)**; **RELEASE_READINESS=CONDITIONAL**; **PRODUCTION_DEPLOY_AUTHORIZED=NO**. Revisados no GitHub o commit `6542b384796400c36052c4f241d2dc3599e18d89`, esta evidência e o caso de uso `read_governed_technical_knowledge`. Não houve reexecução independente de testes/SSH nesta sessão; os resultados de testes são `EXECUTOR_REPORTED_PASS`.

**Aceito:** extensão opcional `subject` (1–240) mantendo `topic/section/corpus_version/page/page_size`, operação `read_governed_technical_knowledge` e duas tools MCP, corpus V1/V2 e proveniência; scoring bounded por documento e sem mapeamento hardcoded `assunto→sNNNN`; `NO_MATCH` tipado como cobertura; 30/30 RED→GREEN, suite focada 1506/1506 segundo executor, fluxo candidate-token→ASGI→READ reportado.

**Condições antes da autorização operacional específica:** (1) executar **suíte DAVI completa aplicável** ou apresentar matriz objetiva das 4619 exclusões da slice e provar que não encobrem regressão; (2) caracterizar contrato `matched_terms/unmatched_terms`: atualmente os termos são calculados sobre **todos os itens ranqueados**, e não necessariamente os `selected_items` da página; provar que a semântica é de cobertura do conjunto ou ajustar contrato/testes para impedir interpretação incorreta de cobertura dos trechos entregues; (3) obter prova de generalização com subjects ambíguos, e confirmação de respostas/erros da rota OpenAPI além do caminho in-process; (4) assegurar imagem/SHA/config sob os gates de release canônicos. Nenhuma dessas condições autoriza nova arquitetura, RAG ou tool.

**Delimitação:** a dependência `api-delpi` fica **localmente implementada**, não implantada nem homologada em runtime produtivo. `DELIA_O2=INCONCLUSIVE` — a disponibilidade da norma não garante sequenciamento semântico de knowledge→search na DÉLIA. Próximo passo: evidência de regressão/contrato → revisão de fechamento → **autorização operacional específica** → deploy `api-delpi` → smoke mínimo → teste R7 da DÉLIA no SHA/model/config real. Não realizar deploy em resposta a este review condicional.


## 10. Fechamento das condições — `DAVI-…-FINAL-ACCEPTANCE-01` (2026-10-24)

### C1 — Full regression

`TEST_COMMAND=pytest tests -q` (suíte completa `api-delpi`, sem seleção):
`TOTAL_COLLECTED=6125`; `TOTAL_PASSED=6093`; `TOTAL_FAILED=2`; `TOTAL_SKIPPED=30`; `TOTAL_DESELECTED=0`.

- 2 falhas = **ambientais pré-existentes**: `test_pac_plan_revision_retention…` e `test_route_phase2_products_production_smoke…` abortam em `PluginsDatabaseConfigError: PLUGINS_DB_HOST ausente` — dependência de Postgres de plugins fora do container de validação; domínios PAC/supplies, sem nenhum acoplamento ao diff.
- 30 skips = skips condicionais pré-existentes (marcadores de infra/fixture).
- `SHARED_NORMALIZATION_REGRESSION=CLEAN`: `text_normalize` é compartilhado com `retrieval.py` (import único, sem duplicação); todos os testes de retrieval/discovery passam na suíte completa.

### C2 — Semântica de cobertura (contrato fixado)

Decisão contratual preservada e documentada: **`matched_terms`/`unmatched_terms` descrevem o conjunto ranqueado inteiro** ("o documento cobre o assunto?"), enquanto **`coverage` descreve a página entregue** (`PARTIAL`/`COMPLETE_SELECTION`/`NO_MATCH`) e `items` é só a fatia da página. `unmatched_terms` reporta termos ausentes do documento — nunca declara correspondência total com cobertura parcial. Página além do último item retorna `items=[]` com `coverage=PARTIAL` (o conjunto existe); `NO_MATCH` só quando nenhuma seção pontua. Fixado por 13 testes novos (`test_terms_describe_full_selection_not_page`, `test_term_coverage_is_stable_across_pages`, `test_partial_subject_coverage_is_honest`, `test_page_beyond_last_is_empty_not_no_match`, …).

### C3 — Generalização ampliada

Casos novos aprovados: stopwords-only → `VALIDATION_ERROR`; subject >240 → `VALIDATION_ERROR`; subject ubíquo (`descrição`) → página bounded; ambíguo (`terminais`) → 3 itens, ordem estável; headings estruturais repetidos em famílias distintas mantêm o contexto da **família correta** (`estrutura … terminais pino` → path "Pino", sem "Genérico"); itens empatados → ordem documental determinística entre execuções; correspondência parcial honesta (`vulcao` → `unmatched_terms`).

### C4 — Contrato real OpenAPI/rota/MCP

Provas no caminho real adicionadas: `subject` publicado no schema OpenAPI (`string, minLength 1, maxLength 240`, `operationId` estável); rota real responde subject + subject&section (`selection=subject+section`, `NO_MATCH` honesto em seção estranha); 422 (vazio/oversized), 409 (versão inválida), 404/422 (tópico inexistente); leitura sem `subject` idêntica ao comportamento anterior (`selection=document`); permissão insuficiente levanta `Forbidden` no decorator (mapeamento de status no `jwt_middleware` do app real — já provado 401 sem Bearer no smoke produtivo); execute path completo `discover → candidate_token → execute → ASGI → rota → use case` retorna `BALA` + proveniência.

`TOTAL=test_davi_knowledge_subject_addressability.py: 43 PASS / 0 FAIL`. `CODE_CHANGE_REQUIRED=NO` — nenhuma alteração produtiva nesta task; apenas testes de fixação de contrato + documentação.
