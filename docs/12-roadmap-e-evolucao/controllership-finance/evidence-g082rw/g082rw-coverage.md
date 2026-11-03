# Gate 082-RW02 — Relatório de cobertura, método e testes

**Executor:** Devin · **Corpus:** `84e92712` local (2.207 PUBLISHED / 88 fontes — republicado com fix_lines D1/D2; baseline produtivo `1fd4c8b0`) · **Ferramenta:** `tests/clara_semantic_audit.py` (claim-level, com confronto de mecanismos) · **Adversarial:** `tests/test_clara_semantic_audit_adversarial.py` (16 cenários).

## Correções RW02 aplicadas

1. **Revisão manual verdadeira** — `MANUAL_VERDICTS` por regex removido. Regras por padrão renomeadas `CURATED_RULES` com `review_method="automático"`; decisões humanas vivem em `g082rw-manual-decisions.json` — **22 entradas**, cada uma vinculada a `knowledge_id` + `claim_hash` (SHA-256[:16]) + claim_id + texto + autoridade + evidência + resultado + justificativa. Nenhuma decisão é aplicada por fonte; sem evidência individual → `UNVERIFIED`/`PENDING`.
2. **Contratos e mecanismos** — `_verify_mechanism` confronta afirmações de comportamento implementado com `CAPABILITY_MAP`/`PRODUCER_MAP`/`CANON_FACTS`/`_CAP_TOKENS` (autoridades verificáveis no HEAD). Regra normativa/definição estável permanece `NOT_APPLICABLE`; afirmação mecânica AS-IS sem verificação externa → `UNVERIFIED`/`manter` (`source_evidence_unconfirmed`), declarada PENDING — não mascarada como aprovada.
3. **Divergências históricas** — `DIVERGENCE_REGISTRY` emite D1 (doc-100 "R01–R15 sem contrato") e D2 (doc-118 "MCP 18 tools/52 fontes/1.298 itens") com os campos exigidos (risco, decisão, ação, evidência). Disposição: `fix_lines` no `STALE_SEGMENT_FIXES` — texto reescrito com marcação temporal + estado vigente; originais SUPERSEDED preservados. Corpus republicado `84e92712`.
4. **Teste adversarial** — 16 fixtures isoladas, expectativas declaradas antes da execução. O teste expôs 3 defeitos reais, corrigidos: `no` (preposição) casando como negação; "não possui" fora do predicado de bloqueio; claims `mechanism` sem surface-token nunca chegando ao confronto. Resultado final **16/16**.

## Pipeline (EXTRACTED → CLASSIFIED → AUTHORITY_CHECKED → REVIEWED → RESOLVED)

- **EXTRACTED:** 13.418 afirmações tipadas (state/historical_state/rule/contract/plan/historical/dynamic_data/mechanism) de 2.207 itens.
- **CLASSIFIED:** itens — 88 CURRENT_VERIFIED · 1.310 HISTORICAL_ONLY · 238 NOT_APPLICABLE · **571 UNVERIFIED (PENDING)**.
- **AUTHORITY_CHECKED:** `consistent_with_authority` 260 · `historically_true_then` 1.147 · `authority_not_needed` 10.670 (regra/contrato/mecânica normativa) · `authority_not_checkable` 454 · `source_evidence_unconfirmed` 887.
- **REVIEWED:** `review_method` — automático 13.396 · **manual 22** (individuais, hash-keyed, arquivo versionado).
- **RESOLVED:** zero STALE_CONFIRMED/REVIEW/MIXED/CONFLICT residuais; 1.341 claims `UNVERIFIED` (454 itens com afirmações sem autoridade conclusiva + mecânicas AS-IS de proveniência) declarados PENDING — **não homologação universal**.

## Divergências (`g082rw-divergences.jsonl`)

D1 e D2 registrados e tratados (fix_lines + SUPERSEDED). Live divergences pós-correção: 0.

## Caminhos de contexto — re-verificados (live, plugins_hub local)

- `get(SUPERSEDED)` → `KnowledgeNotFound` (fail-closed) — PASS.
- `search "O R04 ainda está bloqueado?"` sem e com `report_id` → ficha-r04 no topo, zero claim superado — PASS.
- `list_sources` → 88 fontes, zero INTERNAL_ONLY — PASS.
- Inspeção de código: `search`/`get`/`sources` filtram `status='PUBLISHED'`+escopo — PASS.

## Testes

- `pytest tests/test_clara_semantic_audit_adversarial.py` → **16/16 PASS** (cobertura dos 15 cenários + prova de evidência por afirmação). Falsos positivos/negativos encontrados e corrigidos registrados acima.
- `pytest tests/test_pg_clara_retrieval.py` (efêmero + reingestão do manifest com fix_lines) → **15/15 PASS** — golden 105, 10 negativos, guardas SUPERSEDED/INTERNAL_ONLY/report_id.

## Limitações declaradas

- 571 itens UNVERIFIED = afirmações operacionais/mecânicas sem autoridade conclusiva — PENDING de homologação, não aprovadas.
- "Zero stale" = zero superado **identificado** na leitura claim-level; o adversarial prova detecção nos 15 cenários controlados, não prova universal.
- Corpus produtivo `1fd4c8b0` segue com D1/D2 não corrigidos — a república em produção exige deploy do manifest + ingestão no banco produtivo (pendência operacional registrada).
- Homologação conversacional: **TEST_NOT_RUN** (canal ChatGPT oficial; protocolo §14.6).
