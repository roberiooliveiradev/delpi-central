# DÉLIA API — bootstrap C1-T1

Standalone Flask API da DÉLIA. Este diretório é a pasta canônica `delia-api/`.

C1-T1 cobre somente skeleton + `/health` + config + logging mínimo + testes. Não inclui JWT, Core, MFE, Gateway, Compose, migrations de negócio nem runtime de IA.

## Run local

```bash
cd delia-api
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp env.example .env   # opcional; defaults já são seguros
python -m pytest
python -m app.main
```

Health: `GET http://127.0.0.1:8000/health`

Logs de processo (liveness operacional):

```text
delia_api_started service=delia-api version=... env=...
delia_api_stopped service=delia-api version=... env=...
```

Smoke de processo real (TCP/HTTP, não `test_client`):

```bash
python -m pytest tests/test_runtime_smoke.py -q
```

`DELIA_DEBUG` permanece `false` por default. Não commitar secrets.
