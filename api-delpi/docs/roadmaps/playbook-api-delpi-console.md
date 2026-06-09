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

**Fase 1 concluída** — próximo marco: Fase 2 (telemetria SQL).

### Integração com o portal (federated)

- O `bootstrap.tsx` **não** deve chamar `mount(#root)` ao carregar o remote — isso substitui o shell do portal (sidebar some). Desenvolvimento standalone usa só `src/main.tsx`.
- Navegação interna via `navigateConsole` (`pushState` + `popstate`), rota derivada de `pathname` repassado pelo `AppHost`.

### Fase 2 — Saúde SQL (3–4 sprints)

Complementa o middleware HTTP já existente (`request_observability_middleware`).

| Item | Detalhe |
|------|---------|
| **Telemetria SQL** | Hook em `BaseRepository` → `SqlQueryTelemetryService` (duração, hash, caller app) |
| **Armazenamento** | Ring buffer Redis ou tabela PostgreSQL plugins |
| **Endpoint** | `GET /system/sql-health` (superadmin) — top N queries por tempo e repetição |
| **UI Console** | Aba «SQL» com gráfico e drill-down por `operationId` |

**DoD:** query repetida de LMP/estoque aparece no painel em &lt; 1 min após reprodução.

### Fase 3 — Cache e callers (1–2 sprints)

| Item | Detalhe |
|------|---------|
| **Cache inspector** | `GET /system/query-cache/stats` — hits/miss por chave (LMP, stock-value) |
| **Caller breakdown** | Agregar `X-Delpi-Caller-App` + Core usage tracking |
| **Comparador** | Antes/depois de deploy (export CSV) |

### Fase 4 — Contrato e regressão (contínuo)

| Item | Detalhe |
|------|---------|
| **Diff OpenAPI** | Comparar spec atual vs tag Git anterior |
| **Snapshot envelope** | Golden files por rota (`meta`, shape de `data`) |
| **Integração CI** | `scripts/homologacao/check-api-delpi-console.sh` no pipeline |

Alinhar com `playbook-contrato-respostas-ia.md` e `fase-0-inventario-contrato-respostas.md`.

### Fase 5 — Alertas (opcional)

- Webhook quando smoke suite falha ou p95 &gt; limiar
- Integração com Admin Stats do portal

---

## 5. Rotas api-delpi prioritárias para testes

| Domínio | Rotas | Risco SQL / carga |
|---------|-------|-------------------|
| Engenharia | `GET /engineering/lmps`, `/engineering/lmps/dashboard/*` | Alto — paginação + cache |
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
