# G083 — Validação dos caminhos de contexto (corpus `7d3ca573` local / prod republicado)

| Caminho | Verificação | Resultado |
|---|---|---|
| `knowledge(get)` em `SUPERSEDED` | `get_item()` filtra `status='PUBLISHED'` — live: `KnowledgeNotFound` | PASS |
| `knowledge(search)` sem `report_id` | "O R04 ainda está bloqueado?" → ficha-r04 topo, zero claim superado nos hits | PASS |
| `knowledge(search)` com `report_id=R04` | ficha-r04 topo; segmentos mistos corrigidos via fix_lines | PASS |
| `knowledge(sources)` / `list_sources` | 88 fontes, 0 INTERNAL_ONLY | PASS |
| `list_top_items` / auto-contexto | `get_context` projeta só metadados do corpus (`_safe_corpus_version`), sem conteúdo | PASS |
| Acesso por `knowledge_id` antigo | SUPERSEDED → not found (fail-closed) | PASS |
| Varredura integral de padrões superados | lista `stale_patterns` Gates 080/081 + padrões G083 (`PENDING_CONTRACT` como estado, `18 tools`, `52 fontes`, bloqueios datados R04/R09/R12/R15) → 0 ocorrências em PUBLISHED | PASS |
| Escopo/autorização | `search`/`get`/`sources` filtram `status='PUBLISHED'` + `access_scope`; OR-fill herda os filtros | PASS |
| SUPERSEDED preservado | 141 itens na trilha de auditoria | PASS |

Cache/caminhos paralelos: nenhum identificado — única superfície de conhecimento é `clara_knowledge_item` via `ClaraKnowledgeRepository` (search/get/sources) consumida por `semantic_bridge` (knowledge) e `get_context` (metadados).
