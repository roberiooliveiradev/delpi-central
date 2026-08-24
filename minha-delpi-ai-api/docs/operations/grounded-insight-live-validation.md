# Grounded insight — validação live

Produto canônico: `90260149` · modos: **Normal** (CP1/CP2) e **Pensador** (T2 repetido).

## Como executar

```bash
# 1. Subir stack (raiz do repo)
./infra/scripts/up-dev-sequential.sh --fase core
./infra/scripts/up-dev-sequential.sh --fase chat --build minha-delpi-ai-api

# 2. Smoke automatizado CP1+CP2 (atualiza este arquivo)
cd minha-delpi-ai-api
PYTHONPATH=. .venv/bin/python scripts/smoke_grounded_insight_live.py
```

Variáveis opcionais: `SMOKE_BASE_URL`, `SMOKE_USER`, `SMOKE_PASSWORD`, `SMOKE_PRODUCT_CODE`, `SMOKE_RESPONSE_MODE`, `SMOKE_SKIP_THINKER=1`.

## CP1 — estrutura T1 (E10)

**Objetivo:** árvore OK; prosa com insight BOM; zero «reformule».

| Turno | Mensagem | stage | operationIds | Pass? |
|-------|----------|-------|--------------|-------|
| T1 | qual a estrutura do produto 90260149 | _pendente live_ | _pendente_ | ⏳ |

### Validação de dados (prosa vs artefato)

| Afirmação na prosa | Fonte (tool/path) | Valor API/tabela | Bate? |
|--------------------|-------------------|------------------|-------|
| _preencher após smoke_ | | | |

## CP2 — três turnos (E11+E13)

**Objetivo:** enrich insight; fan-out MP; prosa T2 sem dump `Código:/Tipo:`.

| Turno | Mensagem | stage | stock paths / operationIds | Pass? |
|-------|----------|-------|----------------------------|-------|
| T1 | qual a estrutura do produto 90260149 | — | structure | ⏳ |
| T2 | o que me diz sobre os itens? | `grounded_enrich_insight` | stock+profile | ⏳ |
| T3 | qual o estoque das matérias-primas? | — | MPs (não 90260149) | ⏳ |

### T2 modo Pensador

- stage: _pendente_
- `synthesisFactsTruncated`: _pendente (validar após E17)_
- Pass: ⏳

## CP3 — composição LLM (E18)

_Pendente — executar após E18 (marcadores `[[table]]` / `renderPlan` intercalado)._

## Última execução automatizada

| Campo | Valor |
|-------|-------|
| Data | 2026-08-24 |
| Ambiente | WSL — **Docker daemon indisponível** |
| Proxy offline | `pytest tests/unit/ -k FF-GROUND -q` → 6 passed |
| Script | `scripts/smoke_grounded_insight_live.py` (criado; aguarda stack) |

## Problemas / regressões

- Live bloqueado: `Cannot connect to the Docker daemon` — subir Docker Desktop / `sudo service docker start` e repetir o smoke.

## Metadata (preencher após smoke)

- sessionId: _
- messageIds: _
- synthesisFactsTruncated: _
- renderPlan.segments: _ (CP3)_
