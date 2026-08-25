# Grounded insight — validação live

Produto canônico: `90260149` · modo default: `normal` · data: 2026-08-25

## Como executar

```bash
./infra/scripts/up-dev-sequential.sh --fase core
./infra/scripts/up-dev-sequential.sh --fase chat --build minha-delpi-ai-api
./infra/scripts/up-dev-sequential.sh --fase mfe --build minha-delpi-chat

cd minha-delpi-ai-api
PYTHONPATH=. .venv/bin/python -u scripts/smoke_grounded_insight_live.py
```

## Gates offline (E19)

| Gate | Resultado |
|------|-----------|
| `pytest -k "FF-GROUND or FF-COMPOSE or FF-BUDGET"` | 10 passed |
| `audit_presentation_coverage.py --check-profiles` | OK (tier A/B 100%) |
| MFE `renderPlanSegmentBuilder` + `assistantContentSegments` | 25 passed |
| Rebuild `minha-delpi-ai-api` + `minha-delpi-chat` | OK (sequential) |

## CP1 — estrutura T1 (E10)

| Turno | Mensagem | stage | operationIds | Pass? |
|-------|----------|-------|--------------|-------|
| T1 | qual a estrutura do produto 90260149 | — | get_product_structure | ✅ |

### Prosa T1 (trecho)

Produto **90260149** — CHICOTE EPR SINGELO 235MM. A composição tem **6** componente(s) de nível 1.

## CP2 — três turnos (E11+E13)

| Turno | Mensagem | stage | stock paths / operationIds | Pass? |
|-------|----------|-------|----------------------------|-------|
| T2 | o que me diz sobre os itens? | — | /products/50230130/stock … /50230133/stock | ✅ |
| T3 | qual o estoque das matérias-primas? | — | /products/50230130/stock | ✅ |

### T2 modo Pensador

- stage: `—`
- `synthesisFactsTruncated`: `None`
- Pass: ✅

## CP3 — composição LLM (E18)

- `proseCompositionSource`: `—` (live não emitiu `llm`; stack Automático sem intercalação rica neste turno)
- `renderPlan.layoutMode`: `single`
- `renderPlan.segments`: `['markdown', 'table']`
- Offline FF-COMPOSE: **PASS** (`FF-COMPOSE-STACK-01`, `FF-COMPOSE-EXPLICIT-TABLE-01`, `FF-COMPOSE-ENRICH-01`)

## E19 — Sign-off verify-final

| Critério | Normal | Pensador |
|----------|--------|----------|
| T1 estrutura prosa+árvore | ✅ | ✅ |
| T2 insight enrich sem dump | ✅ | ✅ |
| T3 stock MPs fan-out | ✅ (não consultou PA 90260149) | — |
| Composição intercalada (E18) | ⚠ live single; ✅ offline FF-COMPOSE | ⚠ / ✅ offline |
| Dados prosa = metadata | ✅ | ✅ |
| Sem «reformule» / inglês | ✅ | ✅ |

## Problemas / regressões / apontamentos

- Nenhum bloqueante na execução automatizada send (CP1–CP3 + thinker).
- **Apontamento:** T3 live consultou `50230130` (componente da BOM) — smoke exige só «não PA»; fan-out tipado MP (`keysByComponentType.MP`) coberto por `FF-GROUND-MP-STOCK-01`.
- **Apontamento:** `turnGrounding.stage` não veio no payload adminDebug do smoke (`stage: —`); comportamento enrich inferido por toolCalls multi-stock.
- **Apontamento:** composição `proseCompositionSource=llm` não apareceu no T2 live; contrato coberto pelos fixtures FF-COMPOSE + testes MFE.
- Infra: `api-delpi` precisou restart (mount `/app` vazio → `ModuleNotFoundError`); portal Vite ainda reinicia (`cacheBustEntryPlugin`) — gateway/auth OK.
- Smoke: timeout curto no import OpenAPI do agente (evita hang 6 min / 401).

## Satélite stream (E19)

- Sessão stream T1 estrutura: `74123d40-d2db-4118-b6ef-e11ca20eae85` → **PASS** (`has_structure`, sem «reformule»).

## Metadata

- sessionId (send CP1–CP3): `163a5deb-e797-4dd5-961c-f43fbc1b5da9`
- script: `scripts/smoke_grounded_insight_live.py`
- ambiente: WSL + `up-dev-sequential` (core + chat + mfe chat)
