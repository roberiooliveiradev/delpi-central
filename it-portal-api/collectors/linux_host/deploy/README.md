# Coletor Linux — implantação piloto (srv-api)

Unidades systemd **preparadas e desabilitadas**. Não habilitar o timer em
produção sem gate operacional (Keycloak S2S aplicado + allowlist do servidor).

## Diagnóstico local (sem S2S)

```bash
cd /caminho/para/it-portal-api
PYTHONPATH=. python3 -m collectors.linux_host diagnose
```

## Submit (requer env S2S)

Arquivo `/etc/delpi/it-portal-linux-collector.env` (não versionar segredos):

```bash
IT_PORTAL_COLLECTOR_BASE_URL=https://portal.delpi.local/apps/it-portal-api
IT_PORTAL_COLLECTOR_SERVER_ID=<uuid-do-srv-api>
S2S_TOKEN_URL=https://.../realms/delpi/protocol/openid-connect/token
S2S_CLIENT_ID=it-portal-host-collector
S2S_CLIENT_SECRET=***
S2S_SCOPE=it-portal.observations.ingest
```

```bash
PYTHONPATH=. python3 -m collectors.linux_host submit
```

## Systemd

Copiar `*.service` / `*.timer` para `/etc/systemd/system/`, `daemon-reload`.
**Não** executar `systemctl enable --now` até o gate de agendamento.
