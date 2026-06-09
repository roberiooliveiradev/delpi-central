# Playbook — Console API DELPI

> **Plugin:** `plugins/api-delpi-console`  
> **Manifesto:** `api-delpi-console.manifest.json`  
> **Público:** engenharia, ops, suporte avançado  
> **Status:** Fase 0 concluída · Fase 1 iniciada (verificações + tema portal)

---

## 1. Objetivo

Centralizar **testes manuais e semi-automatizados** da `api-delpi` sem depender de curl/Postman dispersos:

- Validar rotas após deploy ou mudança de contrato
- Inspecionar envelope (`data` + `meta.operationId`, paginação, erros)
- Correlacionar latência HTTP (`X-Response-Time-Ms`) com logs do middleware
- Evoluir para painel de **saúde SQL** e smoke suites das rotas críticas

O console **não substitui** testes automatizados (`pytest`, homologação CI); complementa diagnóstico interativo.

---

## 2. Arquitetura

```text
Portal (AppHost federado)
  → GET /apps/api-delpi-console/assets/remoteEntry.js
  → Console MFE (React + Module Federation)
       → GET /apps/api-delpi/openapi.json
       → GET|POST /apps/api-delpi/<rota>
            headers: Authorization, X-Delpi-Caller-App: api-delpi-console
            resposta: envelope + X-Operation-Id + X-Response-Time-Ms
```

| Camada | Responsabilidade |
|--------|------------------|
| **MFE** | UI explorador, formulário de params, painel de resposta, histórico localStorage |
| **api-delpi** | OpenAPI, rotas de negócio, middleware de observabilidade HTTP |
| **Core API** | Registro do app, permissão `api-delpi-console.view` |
| **Gateway** | Proxy `/apps/api-delpi-console/*` → container `delpi-api-delpi-console` |

---

## 3. Fase 0 — MVP (entregue)

### Funcionalidades

| Tela | Descrição |
|------|-----------|
| **Início** | `GET /health` com status e latência |
| **Documentação da API** | Iframe `/apps/api-delpi/docs` com bridge `DELPI_AUTH` / `DELPI_REFRESH_REQUEST` |
| **Explorador** | Lista operações do OpenAPI por tag; exemplos de schema; respostas documentadas; executor HTTP |
| **OpenAPI / Spec** | Resumo da spec (tags, versão), inventário e download `openapi.json` |
| **Verificações** | Smoke suite «Rotas essenciais» (health, LMP summary, stock-value, quality branches) |
| **Histórico** | Últimas 50 chamadas (status, ms cliente/servidor, `operationId`) |

### Critérios de aceite

- [x] Build Vite + federation (`remoteEntry.js`)
- [x] Manifesto com `basePath` `/apps/api-delpi-console`
- [x] Header `X-Delpi-Caller-App: api-delpi-console`
- [x] Exibição de `meta` quando presente no envelope
- [x] Documentação interativa embutida com autorização JWT automática
- [x] Página de especificação OpenAPI (inventário + download)
- [x] Serviço Docker `api-delpi-console`
- [x] Tema alinhado ao portal (`--primary`, `--secundary`, `data-theme` light/dark)
- [x] Smoke suite inicial em `plugins/api-delpi-console/src/content/smokeSuites.ts`

### Registro na plataforma

```bash
# Após build e subir o container
curl -X POST "$CORE_API/admin/apps/register" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @plugins/api-delpi-console/api-delpi-console.manifest.json
```

Conceder `api-delpi-console.view` a perfis de engenharia/ops (ou `api-delpi.access` como alias futuro).

### Homologação rápida

```bash
cd plugins/api-delpi-console && npm run build
curl -sI http://localhost/apps/api-delpi-console/assets/remoteEntry.js
curl -s http://localhost/apps/api-delpi/health | jq .
```

---

## 4. Roadmap

### Fase 1 — Smoke suites (em andamento)

| Item | Detalhe | Status |
|------|---------|--------|
| **Coleções fixas** | Rotas críticas: health, LMP summary, stock-value, quality branches | [x] MVP |
| **Execução em lote** | Rodar N requests sequenciais; tabela pass/fail + latência | [x] MVP |
| **Persistência** | Último resultado no localStorage | [x] MVP |
| **Mais suites** | PPM, scheduling, transforma-mais | [x] |
| **Exportação** | CSV/JSON do último resultado na UI | [x] |
| **Homologação** | `scripts/homologacao/check-api-delpi-console.sh` | [x] |
| **API backend** | `GET /system/smoke-definitions` (`app/content/smoke_definitions.json`) | [x] |

**DoD:** suite «Rotas essenciais» roda em homologação; falha exibe `operationId` e motivo (status ou timeout).

**Fases 1–4 (MVP) concluídas** — evolução contínua: ampliar golden files e homologação HTTP com `TOKEN` no CI.

### Integração com o portal (federated)

- O `bootstrap.tsx` **não** deve chamar `mount(#root)` ao carregar o remote — isso substitui o shell do portal (sidebar some). Desenvolvimento standalone usa só `src/main.tsx`.
- Navegação interna via `navigateConsole` (`pushState` + `popstate`), rota derivada de `pathname` repassado pelo `AppHost`.

### Fase 2 — Saúde SQL (concluída)

Complementa o middleware HTTP já existente (`request_observability_middleware`).

| Item | Detalhe | Status |
|------|---------|--------|
| **Telemetria SQL** | Hook em `BaseRepository` → `SqlQueryTelemetryService` (duração, hash, caller app) | [x] MVP |
| **Contexto HTTP** | `request_context` — `operationId` + `X-Delpi-Caller-App` | [x] MVP |
| **Armazenamento** | Ring buffer em memória (800 amostras) | [x] MVP |
| **Endpoint** | `GET /system/sql-health` — top N por tempo e repetição | [x] MVP |
| **UI Console** | Aba «SQL» com tabelas agregadas | [x] MVP |
| **Persistência** | Ring buffer Redis (`SQL_TELEMETRY_BACKEND=redis`) com fallback memória | [x] |
| **Gráficos** | Barras por `operationId`, linha do tempo e drill-down (`?operation_id=`) | [x] |

**DoD:** query repetida de LMP/estoque aparece no painel em &lt; 1 min após reprodução.

#### Validação — `get_lmps_dashboard_summary` (jun/2026)

| Sintoma | Causa provável | Ação |
|---------|----------------|------|
| P95 &gt; 2500 ms, caller `strategic-indicators-api` | Cold path sem `listing_type=lmp` ou cache miss | Confirmar deploy SI + api-delpi; segunda chamada no mesmo período deve cair para &lt; 500 ms |
| Mesma query hash, duração variável (300 ms–5 s) | Contenção TOTVS ou cold cache | Aba Cache: hit rate `lmp-dashboard`; aguardar TTL 300s entre comparações |
| Caller anônimo | Cliente sem `X-Delpi-Caller-App` | SI e dashboards devem enviar header; ver aba Callers |

Teste manual pós-deploy:

```bash
# 1ª chamada (cold) — esperado &lt; 2 s com listing_type=lmp
curl -s -H "Authorization: Bearer $TOKEN" \
  "$API/engineering/lmps/dashboard/summary?date_start=20260401&date_end=20260430&listing_type=lmp" \
  -D - -o /dev/null | grep -i x-response-time

# 2ª chamada — esperado cache hit (&lt; 100 ms)
curl -s -H "Authorization: Bearer $TOKEN" \
  "$API/engineering/lmps/dashboard/summary?date_start=20260401&date_end=20260430&listing_type=lmp" \
  -D - -o /dev/null | grep -i x-response-time
```

Testes automatizados: `pytest tests/test_lmp_query_repository_sql.py tests/test_list_lmp_dashboard_use_case.py`.

### Fase 3 — Cache e callers (concluída)

| Item | Detalhe | Status |
|------|---------|--------|
| **Cache inspector** | `GET /system/query-cache/stats` — hits/miss por namespace (LMP, estoque, lmp-summary) | [x] |
| **Caller breakdown** | `GET /system/caller-stats` — agrega `X-Delpi-Caller-App` por request | [x] |
| **Comparador** | `GET /system/observability-snapshot` + UI «antes/depois» com export CSV | [x] |
| **UI Console** | Aba «Cache» com tabelas e comparador | [x] |

### Fase 4 — Contrato e regressão (MVP concluído)

| Item | Detalhe | Status |
|------|---------|--------|
| **Diff OpenAPI** | `GET /system/openapi-diff` vs `app/content/openapi_baseline.json` | [x] |
| **Snapshot envelope** | `envelope_contract_golden.json` + `GET /system/envelope-contracts` | [x] |
| **UI Console** | Painel de diff na aba OpenAPI | [x] |
| **Baseline sync** | `python scripts/sync_openapi_baseline.py` | [x] |
| **Integração CI** | `.github/workflows/api-delpi-console.yml` (pytest + build MFE) | [x] |

Alinhar com `playbook-contrato-respostas-ia.md` e `fase-0-inventario-contrato-respostas.md`.

### Fase 5 — Alertas (concluída)

| Item | Detalhe | Status |
|------|---------|--------|
| **Avaliação** | `evaluate_console_alerts` — smoke, p95 caller e SQL lento | [x] |
| **Webhook** | `POST` opcional com debounce 5 min (`CONSOLE_ALERT_WEBHOOK_URL`) | [x] |
| **Endpoints** | `GET /system/console-health`, `GET /system/console-alerts`, `POST /system/console-alerts/evaluate`, `POST /system/console-alerts/smoke` | [x] |
| **UI Console** | Aba «Alertas» com detalhes acionáveis + link para SQL | [x] |
| **Admin Stats** | Card «Console API DELPI» na visão geral do portal | [x] |
| **Sino Minha DELPI** | `POST /integrations/notifications` (`CONSOLE_ALERT_PORTAL_ENABLED`) | [x] |
| **Monitoramento** | Polling 30 s (SQL, Cache, Alertas, Início) com aba visível | [x] |

**DoD:** falha na suite smoke dispara alerta crítico; p95 acima do limiar gera warning; card no Admin Stats reflete status em tempo real.

**Monitoramento:** não é WebSocket — telemetria alimentada pelo tráfego HTTP/SQL real; o console atualiza a cada 30 s enquanto a aba está aberta. Reavaliação automática de alertas a cada 5 min na aba Alertas.

---

## 5. Rotas api-delpi prioritárias para testes

| Domínio | Rotas | Risco SQL / carga |
|---------|-------|-------------------|
| Engenharia | `GET /engineering/lmps`, `/engineering/lmps/dashboard/*` | Alto — paginação + cache |
| Engenharia (summary) | `GET /engineering/lmps/dashboard/summary` | Alto — batch AIJ + engenharia; otimizado com `listing_type=lmp` e cache `|summary-response` |
| Suprimentos | `GET /supplies/stock-value` | Alto — bundle histórico |
| Qualidade | `GET /quality/ppm/*` | Médio |
| Produção | `GET /production/eficiencia-fabril/*` | Médio |
| Sistema | `GET /health`, futuro `/system/sql-health` | Baixo |

---

## 6. Permissões e segurança

- Console é ferramenta **interna**; não expor rotas de escrita destrutiva sem confirmação (Fase 1+).
- JWT do portal repassado automaticamente (`Authorization: Bearer`).
- Logs de uso rastreiam `api-delpi-console` via `X-Delpi-Caller-App`.
- Endpoints `/system/*` devem exigir role superadmin na api-delpi.

---

## 7. Operação

```bash
# Dev local
cd plugins/api-delpi-console
npm install && npm run dev

# Docker (stack completa)
cd infra
docker compose -f docker-compose.dev.yml up -d --build api-delpi-console api-delpi gateway
```

Documentação do plugin: `plugins/api-delpi-console/README.md`.

**Telemetria SQL persistente:** defina `REDIS_URL` e `SQL_TELEMETRY_BACKEND=redis` no `.env` da stack. Sem Redis, o ring buffer permanece em memória (por processo).

---

## 8. Métricas de sucesso

| Métrica | Meta |
|---------|------|
| Tempo para testar rota nova pós-deploy | &lt; 2 min (vs. montar curl) |
| Correlação incidente → `operationId` | 100% dos requests do console |
| Redução chamadas repetidas LMP/estoque | Monitorar via Fase 2 + dashboards existentes |
| Cobertura smoke suite rotas críticas | ≥ 10 rotas na Fase 1 |

---

## 9. Referências

- Middleware HTTP: `api-delpi/app/middleware/request_observability_middleware.py`
- Cache compartilhado: `api-delpi/app/composition/query_cache_composer.py`
- Plugins: `docs/08-plugins/README.md`
- Contrato respostas: `api-delpi/docs/roadmaps/playbook-contrato-respostas-ia.md`
