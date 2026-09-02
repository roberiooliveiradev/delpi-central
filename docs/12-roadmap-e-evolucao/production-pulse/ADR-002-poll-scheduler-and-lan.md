# ADR-002 — Scheduler de poll e rede LAN (container → ESP)

**Status:** aceito (set/2026)  
**Contexto:** devices na VLAN industrial (`192.168.x.x`); API roda em Docker (dev WSL / prod srv-api). Padrão de mercado: **edge poll** (BFF puxa device), não push MQTT no MVP.

**Referências de mercado:** ThingsBoard device connectivity (last activity + grace); AWS IoT Core **last connectivity**; Home Assistant **unavailable** após `2× update_interval`; scrape Prometheus **up** com `2–3× scrape_interval`.

---

## Decisão 1 — Scheduler (aplicação)

**Um** `DevicePollSchedulerService` no lifecycle da API (FastAPI `lifespan`), **sem** Celery/Redis no MVP.

| Aspecto | Regra |
|---------|--------|
| Modelo | **Per-device** `next_poll_at` (não cron global) |
| Tick | Loop a cada **1 s** — seleciona devices com `enabled=true`, binding vigente, `next_poll_at <= now()` |
| Intervalo | `devices.poll_interval_ms` (clamp 500–300000) |
| **Jitter** | ±10% no intervalo — evita thundering herd (padrão Kubernetes / IoT hubs) |
| Concorrência | Semáforo asyncio **`max_concurrent_polls=10`** (env `PP_POLL_MAX_CONCURRENT`, default 10) |
| Overlap | Se poll do mesmo device **em flight** → pula tick (idempotência por device) |
| Startup | Distribuir `next_poll_at` aleatoriamente nos primeiros `interval` segundos |
| Falha | Não grava reading; atualiza `last_error` + `last_poll_attempt_at` (R13) |
| Sucesso | R14 — reading `source=poll` |

Implementação alvo: `production_pulse_app/application/services/device_poll_scheduler_service.py`.

---

## Decisão 2 — Status online/offline (grace window)

Alinhado a **2× intervalo de poll** com piso/teto (mesmo espírito Prometheus/Grafana):

```text
grace_seconds(device) = clamp((poll_interval_ms / 1000) × 2, min=60, max=600)

online  ⇔  enabled AND last_seen_at NOT NULL AND (now - last_seen_at) <= grace_seconds
offline ⇔  enabled AND NOT online
disabled ⇔  NOT enabled
no_binding ⇔  sem binding vigente (rascunho)
```

Constantes configuráveis via env (defaults acima):

| Env | Default |
|-----|---------|
| `PP_ONLINE_GRACE_MIN_SECONDS` | `60` |
| `PP_ONLINE_GRACE_MAX_SECONDS` | `600` |
| `PP_ONLINE_GRACE_MULTIPLIER` | `2` |

Cálculo exposto em `DeviceConnectivityStatusService` — **único** módulo; painel, `/live`, hub operador consomem o mesmo `status` derivado.

---

## Decisão 3 — Rede Docker → LAN industrial

**Problema:** bridge Docker nem sempre alcança `192.168.20.0/24` (WSL2, NAT).

| Ambiente | Decisão |
|----------|---------|
| **Dev (WSL/local)** | `production-pulse-api` no `docker-compose.dev.yml` com **`network_mode: host`** para o serviço que faz poll HTTP LAN. Documentar em `infra/README-ambiente.md` § Production Pulse. |
| **Prod (srv-api)** | Container na mesma VLAN/rota que os ESPs **ou** host network se firewall permitir — operação valida `curl http://192.168.20.2/api/contador` **de dentro do container** antes do go-live. |
| **MFE / browser** | **Nunca** chama IP LAN — só BFF. |

Fallback dev sem host network: poll manual via script no host (homologação only) — **não** produção.

Timeout HTTP por driver: `device_drivers.json` → `poll.timeoutMs` (default **3000** ms, padrão Modbus/TCP industrial).

---

## Decisão 4 — Teste de conexão antes do save

**Padrão mercado:** AWS IoT test connectivity / ThingsBoard **Test device** antes de ativar.

| Rota | Uso |
|------|-----|
| **`POST /devices/test-probe`** | Cadastro **novo** — body `{ branch, ip_address, driver_key }` — **sem** persistir device |
| `POST /devices/{id}/test` | Edição — mesmo driver HTTP, device já existe |

Ambas: não gravam `readings`; retornam `{ metrics, latencyMs, online, driverKey }`.  
Rate limit: **10 req/min** por usuário (middleware BFF).

---

## Consequências

- E3.S2 implementa scheduler + connectivity service + test-probe.
- E1.S2 Compose dev: `network_mode: host` no serviço API.
- Testes unitários: grace window, jitter bounds, skip in-flight.
- Homologação: checklist `curl` LAN from container documentado no ROADMAP E6.

---

## Referências

- [ESPECIFICACAO-PLUGIN.md §6–7.2](./ESPECIFICACAO-PLUGIN.md)
- [ADR-003-rbac-mvp.md](./ADR-003-rbac-mvp.md)
