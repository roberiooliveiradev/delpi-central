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
