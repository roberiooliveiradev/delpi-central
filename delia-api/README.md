# DÉLIA API — bootstrap C1

Standalone Flask API da DÉLIA. Este diretório é a pasta canônica `delia-api/`.

## Escopo atual

- C1-T1 / C1-T1R1: skeleton + `/health` + logging + smoke de processo
- C1-T2 / C1-T2R1: JWT fail-closed (shared `delpi_auth.jwt_validator`) + Core `GET /me` effective access (sem probe técnico de produção)
- C3-T2: Evidence epistemic domain model + deterministic conformance (`app/domain/evidence/`)

Não inclui: MFE, Gateway, Compose, migrations de negócio, RBAC local da DÉLIA, Domain AuthZ, Evidence store, LLM/RAG/planner/conversation.

## Run local

```bash
cd delia-api
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install -e ../shared
cp env.example .env   # configurar KEYCLOAK_* e CORE_API_URL
python -m pytest
python -m app.main
```

Health (público, sem JWT/Core): `GET http://127.0.0.1:8000/health`

Rotas de negócio autenticadas ainda não existem. Evidência JWT/Core fica nos testes (rota só de teste no harness).

Logs de processo:

```text
delia_api_started service=delia-api version=... env=...
delia_api_stopped service=delia-api version=... env=...
```

`DELIA_DEBUG` permanece `false` por default. Não logar/`persistir` Bearer tokens. Não commitar secrets.
