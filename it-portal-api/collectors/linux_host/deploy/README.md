# Coletor Linux — implantação piloto (srv-api)

Owner da execução: infraestrutura no host. Owner do contrato: `it-portal-api`.

Unidades systemd versionadas. O **instalador não habilita o timer**. Ativação
horária só após gates operacionais e smoke manual do serviço.

## Layout canônico

| Caminho | Função |
|---|---|
| `/opt/delpi/it-portal-collector` | Artefatos + venv isolado |
| `/etc/delpi/it-portal-linux-collector.env` | Credenciais S2S (0640, fora do Git) |
| `/var/lib/it-portal-collector` | Lock/state |
| usuário `delpi-collector` | Sem login; **sem** grupo docker por padrão |

## Instalar / atualizar (idempotente)

No `srv-api`, a partir do clone Git atualizado:

```bash
cd /home/operador/projetos/delpi-central
git pull --ff-only
sudo ./it-portal-api/collectors/linux_host/deploy/install-it-portal-linux-collector.sh
```

O script:

1. cria o usuário técnico se ausente (não altera grupos existentes);
2. sincroniza `collectors/` + `shared/` para `/opt/delpi/it-portal-collector`;
3. cria/atualiza venv com `requirements-collector.txt` + `delpi_auth`;
4. instala units em `/etc/systemd/system/` e roda `systemd-analyze verify`;
5. **não** executa `systemctl enable` no timer.

## Ambiente

```bash
sudo install -m 0640 -o root -g delpi-collector \
  it-portal-api/collectors/linux_host/deploy/it-portal-linux-collector.env.example \
  /etc/delpi/it-portal-linux-collector.env
sudo -e /etc/delpi/it-portal-linux-collector.env
```

Valores canônicos do piloto:

- `IT_PORTAL_COLLECTOR_BASE_URL=http://127.0.0.1/apps/it-portal-api` (gateway local)
- `S2S_TOKEN_URL=https://…/protocol/openid-connect/token` (HTTPS)
- `IT_PORTAL_COLLECTOR_SERVER_ID=<uuid do srv-api>`
- `IT_PORTAL_COLLECTOR_HTTP_HOST` — **omitir** por padrão; só definir se o health
  local exigir Host virtual

Ausência do arquivo env → falha explícita do wrapper e do systemd (`EnvironmentFile` sem `-`).

## Validar gateway local (sem credenciais)

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1/apps/it-portal-api/health
# Se 404/400 por virtual host, testar com Host e só então setar IT_PORTAL_COLLECTOR_HTTP_HOST:
curl -fsS -H 'Host: minhadelpi.com.br' http://127.0.0.1/apps/it-portal-api/health
```

## Diagnóstico (usuário técnico)

```bash
sudo -u delpi-collector /opt/delpi/it-portal-collector/bin/run-collector diagnose
```

Espera-se JSON com `sections_status` das sete seções (`identity`, `os`, `memory`,
`volumes`, `nics`, `systemd`, `docker`). Sem grupo docker, `docker` pode ser
`unavailable`/`partial` — **não** conceder socket privilegiado sem decisão separada.

Alternativas de menor privilégio (decisão operacional, fora deste instalador):

1. manter Docker partial e aceitar inventário sem containers;
2. conceder grupo `docker` ao `delpi-collector` com revisão de risco;
3. coletar resumo Docker por outro canal read-only já autorizado.

## Smoke manual do serviço (antes do timer)

```bash
sudo systemctl start it-portal-linux-collector.service
sudo systemctl status it-portal-linux-collector.service --no-pager
journalctl -u it-portal-linux-collector.service -n 50 --no-pager
```

Aceite: exit 0, novo `run_id` em `it_portal.server_observations`, observação
visível no detalhe do servidor no Portal de TI.

## Ativar timer (somente após aceite operacional)

```bash
sudo systemctl enable --now it-portal-linux-collector.timer
systemctl is-enabled it-portal-linux-collector.timer
systemctl is-active it-portal-linux-collector.timer
systemctl list-timers it-portal-linux-collector.timer --no-pager
```

## Operação / falhas

| Cenário | Ação |
|---|---|
| Sobreposição | `flock -n` → exit ≠ 0; próxima hora tenta de novo |
| Auth S2S 401/403 | revisar secret/scope/audience; não logar token |
| API/gateway down | unit falha; Persistent=true recupera após reboot |
| Reinício do host | timer com `WantedBy=timers.target` volta se estiver enabled |
| Rollback units | `disable --now` timer; remover units; `daemon-reload` |

## Fora do escopo deste pacote

- Keycloak `--apply`
- alteração de V004 / cadastro manual / gateway Cloudflare
- `systemctl enable` automático pelo instalador
