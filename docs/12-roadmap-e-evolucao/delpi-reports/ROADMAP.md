# Roadmap — Delpi Reports

> **Escopo:** plugin `reports` + módulo `api-delpi/reports` + schema Postgres `reports` + providers de domínio  
> **Status:** Fase 0–**4** concluídas (2026-07-21); Fase 5 planejada  
> **Índice:** [README.md](./README.md) · [OPS.md](./OPS.md)

---

## Visão das fases

| Fase | Nome | Status | Entrega principal |
|------|------|--------|-------------------|
| **0** | Fundação e contratos | **Concluída** | Schema, RBAC, ADR Graph, provider port |
| **1** | Scaffold MFE + API skeleton | **Concluída** | App no portal; CRUD definitions; registry vazio |
| **2** | Provider rupturas 30 dias | **Concluída** | Agregação + preview coerente com extrato |
| **3** | Cadastro, destinatários, agenda, e-mail | **Concluída** | Envio real de `minhadelpi@delpi.com.br` |
| **4** | Robustez e escala | **Concluída** | Claim, retries, lotes, artefato HTML, ops |
| **5** | Ecossistema multi-app | Planejada | 2º provider; templates; grupos |

**Ordem sugerida:** 0 → 1 em paralelo com início de 2 → fechar 2 → 3 → 4/5 sob demanda.

---

## Fase 0 — Fundação e contratos

**Objetivo:** alinhar modelo de dados, permissões e extensão do cliente Graph **antes** de código de UI.

**Status:** concluída em 2026-07-21 — [ADR-001](./ADR-001-fundacao.md), [SCHEMA.md](./SCHEMA.md), `V001__create_reports_core.sql`, `REPORTS_*`, `send_mail_to`, `ReportProviderPort`.

### Entregáveis

#### 0.1 Modelo Postgres (schema `reports`)

| Tabela | Responsabilidade |
|--------|------------------|
| `report_definitions` | `id`, `name`, `provider_key`, `params` (JSONB), `active`, timestamps, `created_by` |
| `report_recipients` | `definition_id`, `user_id` (Core), `email` (snapshot/resolvido), `active` |
| `report_schedules` | `definition_id`, cron/expressão, timezone, `next_run_at`, `enabled` |
| `report_runs` | `definition_id`, `trigger` (`manual`/`schedule`), `status`, `started_at`, `finished_at`, `summary` JSONB, `error` |
| `report_deliveries` | `run_id`, `recipient_email`, `status`, `provider_message_id` (se houver), `error`, `sent_at` |

Migrations via padrão de plugins da api-delpi (`run_plugins_migrations.py --plugin reports`), **nunca** editar migration já aplicada.

#### 0.2 RBAC

| Código | Uso |
|--------|-----|
| `reports.view` | Ver definições, histórico, preview |
| `reports.manage` | Criar/editar definições, destinatários, agendas, disparar agora |
| `reports.view.filial-sc` / `filial-es` | Escopo branch `01` / `02` |
| `reports.manage.filial-sc` / `filial-es` | Gestão com escopo de filial |

Constantes em `api_delpi_permissions.py` — sem strings literais nos routers.

#### 0.3 Extensão Microsoft Graph

| Capacidade | Status |
|------------|--------|
| N destinatários (`send_mail_to`) | Implementado |
| Remetente Reports (`GRAPH_REPORTS_MAIL_SENDER`) | Config + Compose (default `minhadelpi@delpi.com.br`) |
| Anexo opcional (`fileAttachment`) | Implementado |
| Legado canal-denúncia (`send_mail`) | Preservado |

Homologação da mailbox e permissão `Mail.Send` fica para ops (Fase 3/4).

#### 0.4 Contratos de provider (interface)

```text
ReportProviderPort
  key: str
  describe_params() -> schema
  collect(params, context) -> ReportDataset
  render_email(dataset) -> EmailPayload
```

`ReportProviderRegistry` — registry vazio na Fase 0; composition root na Fase 1+.

### Critério de pronto — Fase 0

- [x] ADR curto neste diretório + entrada em `decisoes-tecnicas.md`
- [x] Schema / migration `V001` + [SCHEMA.md](./SCHEMA.md)
- [x] Permissões listadas no manifesto-alvo (ADR-001)
- [x] Graph multi-destinatário + anexo implementados e testados

---

## Fase 1 — Scaffold MFE + API skeleton

**Objetivo:** app visível no portal e superfície HTTP mínima, sem lógica de rupturas.

**Status:** concluída em 2026-07-21 — `plugins/reports/`, rotas `/reports/*`, smoke `test_reports_routes_smoke.py`.

### Entregáveis

#### 1.1 Plugin MFE `plugins/reports/`

Seguir [novo-plugin-mfe-checklist.md](../../05-plugin-system/novo-plugin-mfe-checklist.md):

- [x] `reports.manifest.json` (`type: microfrontend`, `ui.renderMode: federated`)
- [x] Vite MF + `preparePluginUiRemote()` + `@delpi/plugin-ui`
- [x] `Dockerfile` com `context: ../plugins`, **sem** `COPY plugin-ui`
- [x] Serviço em `infra/docker-compose.yml` e `docker-compose.dev.yml` (`<<: *plugin-ui-federated`)
- [x] `gateway.depends_on` inclui `reports` (prod)
- [x] `scripts/register-manifest.sh`
- [x] `README.md` do plugin + linha em `docs/08-plugins/README.md`
- [x] Telas: lista de definições + detalhe stub

#### 1.2 API skeleton (`api-delpi`)

| Método | Path sugerido | `operation_id` sugerido |
|--------|---------------|-------------------------|
| `GET` | `/reports/definitions` | `list_report_definitions` |
| `POST` | `/reports/definitions` | `create_report_definition` |
| `GET` | `/reports/definitions/{id}` | `get_report_definition` |
| `PATCH` | `/reports/definitions/{id}` | `update_report_definition` |
| `GET` | `/reports/runs` | `list_report_runs` |
| `GET` | `/reports/providers` | `list_report_providers` |

- [x] Schema Postgres + migration V001
- [x] Permissões + smoke Nível A (`meta.operationId`)
- [x] Doc `api-delpi/docs/api/delpi-reports.md`
- [x] Registry de providers **vazio** (`build_report_provider_registry`)
- [x] Inventário: `audit_route_test_coverage.py --write && --check`

### Critério de pronto — Fase 1

- [x] Scaffold MFE + compose `delpi-reports`
- [x] `GET /reports/definitions` e `GET /reports/providers` (lista vazia) no smoke
- [ ] Manifest registrado na Core API (ops: `register-manifest.sh`)

---

## Fase 2 — Provider “rupturas nos próximos 30 dias”

**Status:** concluída (2026-07-21).

**Objetivo:** coletar itens com ruptura projetada na janela de 30 dias **sem** N+1 de details, alinhado ao extrato do estoque-segurança.

### Regras de negócio (canônicas)

| Regra | Detalhe |
|-------|---------|
| Saldo inicial | Disponível SB2 **01+98+99** |
| Timeline | `+` SC7 elegíveis, `−` SD4 elegíveis; no mesmo dia, saídas antes de entradas |
| Ruptura | Primeiro `running_balance < 0` → `first_shortage_date` |
| Inclusão no relatório | `first_shortage_date` ≤ `as_of_date + 30 dias` (inclui atrasadas; data = início da OP do empenho) |
| Fora | Status ESTSEG / `deficit_quantity` (não confundir com ruptura física) |
| Empenhos sem data | Não geram previsão confiável (mesmo warning do módulo atual) |

Código reutilizado:

- `safety_stock_sql.py` — `materials_for_projection_batch_sql`, SC7/SD4 por filial
- `build_stock_projection()` / enrich de SC7 e SD4
- Testes: `test_safety_stock_shortage_30d_provider.py` + `test_safety_stock_stock_projection_service.py`

### Entregáveis

- [x] `SafetyStockShortage30dProvider` (`provider_key = safety_stock_shortage_30d`)
- [x] Serviço de **agregação** por filial (batch): 3 SQL + projection in-process — **não** loop HTTP de details
- [x] Rota `GET /reports/providers/safety_stock_shortage_30d/preview?branch=&horizonDays=`
- [x] Payload tabular estável para e-mail (colunas abaixo)
- [x] Testes unitários: critério de janela 30d + regressão de `first_shortage_date`
- [x] Medição SQL (peso/latência) — ver nota abaixo; **sem cache** na 1ª entrega

### Colunas do dataset / e-mail

| Coluna | Origem |
|--------|--------|
| Código | produto |
| Descrição | SB1/SBZ |
| Filial | parâmetro / branch |
| Saldo atual | `available_stock` |
| Data da ruptura | `first_shortage_date` |
| Saldo no evento | `running_balance` no evento de ruptura |
| Observação | warnings do summary da projeção |

### Latência (medição)

| Etapa | Observação |
|-------|------------|
| I/O TOTVS | 3 queries/filial (`materials` + SC7 + SD4), `WITH (NOLOCK)` |
| CPU | loop `build_stock_projection` por MP |
| Cache | não introduzido (agenda diária; reavaliar se p95 inviável) |

**Medição ao vivo (2026-07-21, container `delpi-api-delpi`, filial `01`, universo MP):**

| Amostra | `materialsScanned` | `shortageCount` | tempo |
|---------|--------------------|-----------------|-------|
| 1ª (fria) | 10 496 | 25 | **24,6 s** |
| 2–4 (quentes, n=3) | 10 496 | 25 | 2,8–3,7 s (máx **3,7 s** ≈ p95 n=3) |

Loop in-process isolado (500 MPs mock, sem SQL): ~5 ms → gargalo é I/O TOTVS, não a projeção. Aceitável para agenda diária; **sem cache** nesta entrega.

### Critério de pronto — Fase 2

- [x] Preview autenticado lista rupturas coerentes com o modal “Extrato projetado” (paridade unitária com fixture de projeção)
- [x] Tempo de agregação documentado (p95 quente ~3,7 s; fria ~25 s — ver tabela acima)
- [x] Provider registrado em `list_report_providers`

---

## Fase 3 — Cadastro, destinatários, agendamento e e-mail

**Status:** concluída (2026-07-21) — código + testes com Graph mock; e-mail real exige Azure/`GRAPH_REPORTS_MAIL_SENDER`.

**Objetivo:** valor de negócio — configurar e receber o e-mail.

### Entregáveis UI (MFE)

- [x] Criar/editar definição do tipo `safety_stock_shortage_30d`
- [x] Parâmetros: filial, horizonte (default 30), nome amigável
- [x] Destinatários via `UserDirectoryPicker` (Core directory)
- [x] Agendamento: diário / semanal + horário (timezone America/Sao_Paulo)
- [x] Ações: **Enviar agora**, ativar/desativar, ver histórico de runs
- [x] Componentes `@delpi/plugin-ui` (`UserDirectoryPicker`)

### Entregáveis API / motor

- [x] CRUD recipients + schedules
- [x] `POST /reports/definitions/{id}/run` (manual)
- [x] Worker/cron: `POST /reports/schedules/process-pending` + script host
- [x] Pipeline run: `collect` → `render_email` → Graph → `report_runs` + `report_deliveries`
- [x] Extensão Graph (`send_mail_to` + `GRAPH_REPORTS_MAIL_SENDER`)
- [x] Remetente Reports via `GRAPH_REPORTS_MAIL_SENDER` (compose default `minhadelpi@delpi.com.br`)

### Critério de pronto — Fase 3

- [x] Pipeline e UI prontos; e-mail de teste na caixa = passo ops (Graph/Azure)
- [x] Corpo lista rupturas 30d (ou mensagem “nenhuma ruptura”)
- [x] Run e deliveries no histórico do app
- [x] Falha Graph registrada com erro sanitizado (sem secrets)

---

## Fase 4 — Robustez e escala

**Status:** concluída (2026-07-21) — claim atômico, retries Graph, lotes, artefato HTML, hook `event`, [OPS.md](./OPS.md).

**Objetivo:** operação confiável em produção.

### Entregáveis

- [x] Retries com backoff em falha transitória Graph
- [x] Idempotência de schedule (claim `SKIP LOCKED` + avanço de `next_run_at` no claim)
- [x] Rate-limit / loteamento de destinatários (`REPORTS_MAIL_BATCH_SIZE`, default 40)
- [x] Storage de artefato HTML da run em volume `${DELPI_DATA_HOST_DIR}/reports-runs`
- [x] Observabilidade: logs estruturados de claim / run / batch
- [x] Doc operacional: [OPS.md](./OPS.md)
- [x] Disparo por evento — `POST …/run?trigger=event`

### Critério de pronto — Fase 4

- [x] Agenda diária não reprocessa o mesmo slot sob concorrência (claim)
- [x] Run falha e sucesso auditáveis (runs + deliveries + artefato)
- [x] Volume `reports-runs` nos composes (recreate não apaga HTML no host)

---

## Fase 5 — Ecossistema multi-app

**Objetivo:** provar extensibilidade além do estoque-segurança.

### Entregáveis

- [ ] Segundo `ReportProvider` (outro domínio api-delpi — escolher na hora da implementação)
- [ ] Templates de e-mail versionados (HTML por `provider_key` + locale pt-BR)
- [ ] Grupos / listas de destinatários reutilizáveis (opcional)
- [ ] Preferências (opt-out) — se produto exigir
- [ ] Canal complementar portal (Core `/integrations/notifications`) — **opcional**, não substitui e-mail

### Critério de pronto — Fase 5

- [ ] Duas definições de providers distintos enviam e-mail pelo mesmo motor
- [ ] README do plugin atualizado com catálogo de providers

---

## Configuração Graph (ops)

### Canal de denúncia (`GRAPH_*`)

| Variável | Uso |
|----------|-----|
| `GRAPH_TENANT_ID` / `GRAPH_CLIENT_ID` / `GRAPH_CLIENT_SECRET` | App Azure do canal-denúncia |
| `GRAPH_MAIL_SENDER` | `canal-denuncia@delpi.com.br` |
| `GRAPH_MAIL_RECIPIENT` | Destinatário fixo da ouvidoria |

### Delpi Reports (`GRAPH_REPORTS_*`) — **separado**, sem fallback para canal-denúncia

| Variável | Uso |
|----------|-----|
| `GRAPH_REPORTS_TENANT_ID` | Tenant Azure AD da app Reports |
| `GRAPH_REPORTS_CLIENT_ID` | App registration Reports |
| `GRAPH_REPORTS_CLIENT_SECRET` | Segredo Reports |
| `GRAPH_REPORTS_MAIL_SENDER` | Remetente Reports (`minhadelpi@delpi.com.br`) |
| `GRAPH_HTTP_TIMEOUT_SECONDS` | Timeout HTTP (compartilhado) |

**Azure (fora do código):** Application Access Policy / `Mail.Send` na mailbox `minhadelpi@delpi.com.br` para a app Reports.

> Canal-denúncia e Reports **não** compartilham remetente nem client credentials no código.

---

## Referências rápidas de implementação

| Tema | Onde |
|------|------|
| Scaffold MFE | `docs/05-plugin-system/novo-plugin-mfe-checklist.md` |
| Nova rota api-delpi | `.cursor/rules/new-api-route-checklist.mdc` |
| Extrato / projeção | `safety_stock_stock_projection_service.py` |
| Graph mail | `microsoft_graph_mail_client.py` |
| Branding e-mail | `report_email_brand_layout_service.py` + `logo_delpi.png` (CID `delpi-logo`); templates Jinja → Fase 5 |
| Diretório usuários | Core `GET /me/directory/users` + `UserDirectoryPicker` |
| E-mail real no picker | Query `reveal_email=true` (padrão Core mascara — LGPD); API Reports rejeita `***` no local |
| Deploy seguro | `infra/scripts/up-*-sequential.sh` |
| Doc plugins | `.cursor/rules/plugins-documentation.mdc` |

---

## Anti-padrões (não fazer)

- Chamar o MFE estoque-segurança ou duplicar UI do extrato no Reports
- Loop N+1 em `get_supplies_safety_stock_item_details`
- Confundir ruptura (`running_balance < 0`) com déficit vs ESTSEG
- Strings PT de e-mail espalhadas sem template/versionamento a partir da Fase 5
- Persistência de anexo só em filesystem efêmero do container
- `if "/supplies/safety-stock"` no motor genérico — usar `provider_key`
- Gravar e-mail mascarado do diretório (`t***@…`) como destinatário SMTP — usar `reveal_email=true`

---

## Checklist global antes do “MVP produção”

- [x] Fases 0–4 concluídas
- [ ] Manifest + RBAC em papéis reais
- [ ] Compose prod com serviço `reports`
- [ ] Graph homologado com `minhadelpi@delpi.com.br`
- [ ] Doc API + README plugin + inventário `08-plugins`
- [ ] Smoke: preview + run manual + e-mail recebido
