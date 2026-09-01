# Production Pulse API

BFF dedicado ao plugin **Production Pulse** (IoT industrial). O MFE consome apenas esta API — nunca a api-delpi diretamente.

## Desenvolvimento local

```bash
cd production-pulse-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ../shared[fastapi]
pytest -q
```

## Endpoints (E1.S1)

| Método | Path | Auth |
|--------|------|------|
| GET | `/health` | público |

Documentação completa: `docs/12-roadmap-e-evolucao/production-pulse/`.
