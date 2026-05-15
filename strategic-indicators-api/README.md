# Strategic Indicators API

Serviço FastAPI dedicado a **`/strategic-indicators/*`** (código derivado da api-delpi, pacote `si_app` com imports `from si_app...`).

O **`si_app/main.py`** expõe **`/health`**, **`/docs`** e o router **`/strategic-indicators/*`**.

O repositório `si_app/` foi **poado**: mantêm-se só módulos alcançáveis a partir de `main.py` → `strategic_indicators_routes` → `strategic_indicators_composer` → composers departamentais (comercial, produção, qualidade, engenharia, financeiro, suprimentos, RH) e respetiva infra (TOTVS, Google Sheets, Portal RH, Postgres plugins para catálogo/metas/settings).

## Variáveis de ambiente

Igual à api-delpi para dados operacionais: `PLUGINS_*`, TOTVS, Google Sheets, Portal RH, Keycloak/JWT, etc. (ver `si_app/config.py`).

| Variável | Descrição |
|----------|-----------|
| `SI_API_ROOT_PATH` | Prefixo atrás do gateway (predefinição `/apps/strategic-indicators-api`). |
| `STRATEGIC_INDICATORS_API_PORT` | Porta do processo (fallback para `PORT`). |

## Desenvolvimento local

Na raiz do monorepo:

```bash
export PYTHONPATH="$(pwd)/strategic-indicators-api:$(pwd)/shared"
pip install -r strategic-indicators-api/requirements.txt
pip install -e ./shared[fastapi]
python -m uvicorn si_app.main:app --reload --app-dir strategic-indicators-api --port 8010
```

Docker (contexto = raiz do monorepo):

```bash
docker build -f strategic-indicators-api/Dockerfile -t strategic-indicators-api:dev .
```

## Integração

O MFE chama **`/apps/strategic-indicators-api/strategic-indicators`** através do gateway; a **api-delpi** já não monta estas rotas.
