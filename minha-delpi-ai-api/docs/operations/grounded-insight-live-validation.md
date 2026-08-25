# Grounded insight — validação live (gaps E20–E24)

Produto canônico: `90260149` · data: 2026-08-25

## Asserções de qualidade (E23)

O smoke falha se:
- **T2** prosa = template de um único estoque («Saldo disponível…» + «próximos passos… negativo») sem cruzar códigos
- **T3** stock paths só `5023…` (PI) em vez de MPs (`1008…` / `1038…`) ou incluir o PA

## E24 — Verify-final gaps

### Offline (2026-08-25)

| Gate | Resultado |
|------|-----------|
| `pytest -k "FF-QUALITY or FF-GROUND or FF-COMPOSE or brief_direct_skips or preserving_structure or mp_referent"` | **15 passed** |
| E20 brief-direct skip enrich multi-tool | PASS |
| E21 excerpt preserve BOM + planner MP sem PI | PASS |
| E22 composição Normal facts/reminder | PASS |

### Live

| Critério | Normal | Pensador |
|----------|--------|----------|
| T1 estrutura prosa+árvore | _pendente — Docker Desktop off_ | — |
| T2 insight enrich (não template) | _pendente live_ | _pendente live_ |
| T3 stock MPs tipadas | _pendente live_ | — |
| Composição intercalada | _pendente live_ | — |

**Ambiente:** WSL sem Docker (`docker.sock` ausente). Reexecutar:

```bash
# Docker Desktop ligado
./infra/scripts/up-dev-sequential.sh --fase core
./infra/scripts/up-dev-sequential.sh --fase chat --build minha-delpi-ai-api
cd minha-delpi-ai-api && PYTHONPATH=. .venv/bin/python -u scripts/smoke_grounded_insight_live.py
```

## Commits desta rodada (gaps)

- E20.S1–S3 — Normal enrich → LLM; fallback multi-tool; FF-QUALITY-T2
- E21.S1–S2 — Excerpt BOM tipado preservado; planner MP sem fallback PI
- E22.S1 — Reminder composição enrich Normal
- E23.S1 — Smoke qualidade T2/T3

## Metadata

- script: `scripts/smoke_grounded_insight_live.py`
- plano: `gaps_insights_normal_7f86b666`
