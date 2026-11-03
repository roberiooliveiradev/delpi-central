# Gate 082-RW01 — Relatório de cobertura e método

**Executor:** Devin · **Corpus auditado:** `5c48899a` local (2.207 PUBLISHED / 88 fontes — mesmo conjunto do produtivo `1fd4c8b0`) · **Ferramenta:** `controllership-finance-api/tests/clara_semantic_audit.py` (reescrita claim-level; reproduz o baseline G082 com `--prior`).

## Método (READ → VERIFY → CLASSIFY → DECIDE)

1. **Extração por statement** — cada item tem cada linha inspecionada; fora de fenced code, cada statement é tipado `state | historical_state | rule | contract | plan | historical | dynamic_data | mechanism`. 13.416 afirmações extraídas.
2. **Perfil estrutural** — % código/SQL, % tabela, % prosa por item; a justificativa de NOT_APPLICABLE cita o conteúdo inspecionado, não "ausência de match".
3. **Confronto com a verdade vigente** — afirmações de estado são confrontadas com `REPORT_STATE` (matriz GATE A vigente: R01–R12/R15 IMPLEMENTED, R13/R14 SOURCE_UNAVAILABLE), `STILL_MISSING` (E1/E8/E9 + fontes externas) e `PARITY_PENDING` (G6 = 0/15). Afirmações datadas **também** são confrontadas — narrativa datada não imuniza estado superado.
4. **Decisões manuais curadas** — 190 afirmações que a tabela não resolve receberam decisão individual registrada em `MANUAL_VERDICTS` (review_method=manual, justificativa + autoridade por claim).

## Contagens (reconciliadas, 2.207 itens)

| Classe final | Itens |
|---|---|
| NOT_APPLICABLE | 578 |
| HISTORICAL_ONLY | 1.569 |
| CURRENT_VERIFIED | 60 |
| STALE_CONFIRMED / MIXED / CONFLICT / REVIEW / UNVERIFIED residuais | **0** |

### Reconciliação G082 → RW01

| G082 | → CURRENT_VERIFIED | → HISTORICAL_ONLY | → NOT_APPLICABLE |
|---|---|---|---|
| NOT_APPLICABLE (2.045) | 34 | 1.452 | 559 |
| UNVERIFIED (117) | 19 | 85 | 13 |
| REVIEW (16) | 1 | 11 | 4 |
| CURRENT_VERIFIED (13) | 3 | 9 | 1 |
| HISTORICAL_ONLY (16) | 3 | 12 | 1 |

Os 2.045 NOT_APPLICABLE foram efetivamente reexaminados: 1.486 continham afirmações que a regex original não via (datadas, mecânicas, regras, plano) — 34 continham afirmações de estado corrente verificadas contra autoridade. Os 117 UNVERIFIED (valores monetários) tiveram decisão individual: 85 datados com competência explícita → HISTORICAL_ONLY; 19 consistentes com regra vigente → CURRENT_VERIFIED; 13 são regra/exemplo de paridade → NOT_APPLICABLE. Os 45 restantes (REVIEW/CURRENT_VERIFIED/HISTORICAL_ONLY) foram revalidados claim a claim.

## Afirmações (matriz `g082rw-claims.jsonl`)

13.416 claims com `knowledge_id, source_id, citation_locator, claim_id, claim_text, claim_type, temporal_scope, authority, authority_reference, verified_state, classification, decision, rationale, review_method, review_status`.

- `verified_state=consistent_with_authority`: 80 · `historically_true_then`: 1.183 · `historical_evidence`: 31 · `authority_not_needed` (regra/contrato/mecânica/plano): 12.122.
- `review_method`: automático 13.226 · manual 190.
- Verificação adversarial: 16 claims contendo R04/R09/R12/R15 + predicado de bloqueio — **todas** com decisão individual (linhas corrigidas G080-RW01, registros datados, DR-C2, specs, negações). Nenhuma afirmação superada sem confronto.

## Divergências (`g082rw-divergences.jsonl`)

Zero STALE_CONFIRMED novo. Dois registros datados contradizem a verdade atual e foram mantidos como histórico — anotados para o GPT: doc-100 "R01–R15 sem contrato (PENDING_CONTRACT)" e doc-118 "MCP 18 tools / corpus 52 fontes / 1.298 itens".

## Caminhos de contexto — re-verificados (live, plugins_hub local)

- `get_item(SUPERSEDED)` → `KnowledgeNotFound` (fail-closed PUBLISHED) — PASS.
- `search("O R04 ainda está bloqueado?")` sem `report_id` → ficha-r04 no topo, nenhum claim superado nos 12 hits — PASS.
- `search(..., report_id="R04")` → ficha-r04 topo — PASS.
- `list_sources` → 88 fontes, zero INTERNAL_ONLY; filtro PUBLISHED no join — PASS.
- `get_context` só projeta `catalog["knowledge"]=_safe_corpus_version()` (metadados), sem conteúdo — PASS.
- Code inspection: `search`/`get_item`/`list_sources` filtram `status='PUBLISHED'` + escopo; OR-fill herda os mesmos filtros — PASS.

## Testes

`pytest tests/test_pg_clara_retrieval.py` (efêmero, reingestão do manifest): **15/15 PASS** — golden 105 + 10 negativos + guardas SUPERSEDED/INTERNAL_ONLY/report_id + invariantes do corpus.

## Limitações declaradas

- A extração/verificação é determinística + decisões manuais curadas; não foi usado LLM no loop de classificação. Cada afirmação carrega evidência reconstruível (claim_id → locator → autoridade).
- "Zero stale" significa: zero afirmação comprovadamente superada **identificada** na leitura integral claim-level — não prova universal de ausência.
- Homologação conversacional (115 respostas do host): **TEST_NOT_RUN** — dependência externa (canal ChatGPT oficial); protocolo §14.6 do doc 152.
