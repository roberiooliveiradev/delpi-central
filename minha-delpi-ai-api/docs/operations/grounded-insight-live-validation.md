# Grounded insight — validação live

Produto canônico: `90260149` · modo default: `normal` · data: 2026-08-25

## CP1 — estrutura T1 (E10)

| Turno | Mensagem | stage | operationIds | Pass? |
|-------|----------|-------|--------------|-------|
| T1 | qual a estrutura do produto 90260149 | — | get_product_structure | ✅ |

### Prosa T1 (trecho)

Produto **90260149** — CHICOTE EPR SINGELO 235MM. A composição tem **6** componente(s) de nível 1.

## CP2 — três turnos (E11+E13)

| Turno | Mensagem | stage | stock paths / operationIds | Pass? |
|-------|----------|-------|----------------------------|-------|
| T2 | o que me diz sobre os itens? | — | /products/50230130/stock, /products/50230131/stock, /products/50230132/stock, /products/50230133/stock | ✅ |
| T3 | qual o estoque das matérias-primas? | — | /products/50230130/stock | ✅ |

### T2 modo Pensador

- stage: `—`
- `synthesisFactsTruncated`: `None`
- Pass: ✅

## CP3 — composição LLM (E18)

- `proseCompositionSource`: `—`
- `renderPlan.layoutMode`: `single`
- `renderPlan.segments`: `['markdown', 'table']`
- Offline FF-COMPOSE: ver pytest (`FF-COMPOSE-STACK/EXPLICIT-TABLE/ENRICH`)

## E19 — Sign-off verify-final

| Critério | Normal | Pensador |
|----------|--------|----------|
| T1 estrutura prosa+árvore | ✅ | ✅ |
| T2 insight enrich sem dump | ✅ | ✅ |
| T3 stock MPs fan-out | ✅ | — |
| Composição intercalada (E18) | ⚠ offline FF-COMPOSE | ⚠ offline FF-COMPOSE |
| Dados prosa = metadata | ✅ | ✅ |
| Sem «reformule» / inglês | ✅ | ✅ |

## Problemas / regressões

- Nenhum na execução automatizada.

## Metadata

- sessionId: `7769f922-5561-423e-b359-5d289702939d`
- script: `scripts/smoke_grounded_insight_live.py`
- ambiente: WSL + `up-dev-sequential` (core + chat)
