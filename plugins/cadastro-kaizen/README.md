# Cadastro de Kaizens — plugin Minha DELPI

Microfrontend federado para **cadastro operacional** de melhorias contínuas (kaizen) no módulo qualidade. Os dados ficam em **PostgreSQL** (`quality.kaizens`); o **dashboard de qualidade** continua lendo KPIs da **planilha Google Sheets** até migração futura da leitura analítica.

## Visão geral

| Camada | Responsabilidade |
|--------|------------------|
| **MFE** `cadastro-kaizen` | Listagem, formulário, filtros, importação da planilha |
| **api-delpi** `/quality/kaizens/records` | CRUD + importação Sheets → Postgres |
| **api-delpi** `/quality/kaizens/summary` | Leitura analítica (Sheets) — dashboard |
| **PostgreSQL** `quality.kaizens` | Fonte de verdade do cadastro operacional |

```text
Portal → /apps/cadastro-kaizen
           ↓ Module Federation (remoteEntry.js)
         MFE cadastro-kaizen
           ↓ JWT + X-Delpi-Caller-App
Gateway → /apps/api-delpi/quality/kaizens/records
           ↓
         api-delpi → Postgres (quality.kaizens)

Dashboard qualidade → /apps/api-delpi/quality/kaizens/summary (Google Sheets)
```

## Rotas da UI

| Path | Tela |
|------|------|
| `/apps/cadastro-kaizen` | Listagem com filtros e tabela paginada |
| `/apps/cadastro-kaizen/novo` | Formulário de criação |
| `/apps/cadastro-kaizen/detalhe/{uuid}` | Ficha visual com edição por seção, versões, evidências |
| `/apps/cadastro-kaizen/editar/{uuid}` | Formulário legado de edição (redireciona ao detalhe quando aplicável) |

Navegação interna via estado do MFE (`CadastroKaizenPage`); o Portal monta o plugin em `basePath` do manifesto.

## Formulário público de sugestão

- Link compartilhado (botão **Compartilhar** na listagem): `/p/kaizen/sugestao/aberto` (public-hub)
- API: `POST /apps/api-delpi/public/kaizen/suggestions` (sem JWT)
- Status inicial: `recebido`
- Permissão de alerta: `cadastro-kaizen.notify-suggestions` (sino do portal)
- Env API: `KAIZEN_NOTIFICATIONS_ENABLED` (default true) + token Core Integrations

## API (gateway)

Base HTTP: **`/apps/api-delpi/quality/kaizens/records`**

| Método | Rota (relativa à api-delpi) | Descrição |
|--------|----------------------------|-----------|
| GET | `/quality/kaizens/records` | Lista paginada (`meta.shape`: `paged_list`) |
| POST | `/quality/kaizens/records` | Cria registro |
| GET | `/quality/kaizens/records/{id}` | Detalhe (UUID Postgres) |
| PUT | `/quality/kaizens/records/{id}` | Atualiza |
| DELETE | `/quality/kaizens/records/{id}` | Exclusão lógica (`deleted_at`) |
| POST | `/quality/kaizens/records/import-from-sheet` | Importa linhas ativas da planilha |

**Leitura analítica (Sheets, dashboard):**

| Método | Rota | Fonte |
|--------|------|-------|
| GET | `/quality/kaizens/summary` | Google Sheets |
| GET | `/quality/kaizens/{kaizen_id}` | Google Sheets (`{kaizen_id:path}` — aceita `/` no ID) |

| GET | `/quality/kaizens/records/{id}/revisions` | Revisões / snapshots |
| POST | `/quality/kaizens/records/{id}/versions` | Nova versão (rascunho) |
| POST | `/quality/kaizens/records/{id}/versions/{n}/implement` | Implantar versão |
| GET | `/quality/kaizens/records/{id}/evidences` | Evidências (Antes/Depois) |
| GET | `/quality/kaizens/records/{id}/savings-timeline` | Ganhos por período |

Documentação detalhada: [docs/DOCUMENTACAO.md](./docs/DOCUMENTACAO.md) · [api-delpi/docs/api/06-modulos-departamentais.md](../../api-delpi/docs/api/06-modulos-departamentais.md) (§ Cadastro operacional).

### Exemplo — listar

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"

curl -s -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: cadastro-kaizen" \
     "http://localhost/apps/api-delpi/quality/kaizens/records?page_size=50" \
  | jq '.success, .data.pagination'
```

### Exemplo — importar da planilha

```bash
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Delpi-Caller-App: cadastro-kaizen" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}' \
  "http://localhost/apps/api-delpi/quality/kaizens/records/import-from-sheet" \
  | jq '.data | {created, skipped, errors}'
```

A importação é **idempotente**: ignora duplicatas (mesma filial + título + data de implantação). Use `dry_run: true` para simular.

## Permissões

| Código | Uso |
|--------|-----|
| `cadastro-kaizen.view` | Listar e consultar registros |
| `cadastro-kaizen.manage` | Criar, editar, excluir e importar |
| `cadastro-kaizen.notify-suggestions` | Alerta no portal ao receber sugestão pública |

Na api-delpi, rotas de leitura aceitam também `api-delpi.quality.access` e `dashboard-quality.view`; escrita autenticada exige `cadastro-kaizen.manage` (ou `api-delpi.access` / `api-delpi.quality.access`). A rota pública de sugestão não exige JWT.

## Modelo de dados

Tabela: `quality.kaizens` (migration `V027__create_kaizens.sql`).

| Campo | Tipo / valores | Observação |
|-------|----------------|------------|
| `branch_code` | `01`, `02` | Obrigatório |
| `title` | string | Obrigatório |
| `status` | `recebido`, `aprovado`, `implantado`, `descontinuado`, `cancelado` | Default `recebido` |
| `date_idea_received` | date | Recebimento da ideia (V035) |
| `date_committee_approved` | date | Aprovação no comitê (V042); obrigatória se status = aprovado |
| `date_implemented` | date | Implantação — vigência da revisão + validade 1 ano da economia |
| `date_discontinued` | date | Fim da operação |
| `categories` | `TEXT[]` | Multi-categoria (V036); `category` = primeiro item |
| `savings_type` | `tempo`, `material`, `financeiro`, `qualitativo`, `misto` | Inferido se omitido no POST |
| `seconds_per_occurrence`, `occurrences_per_day`, `hourly_cost` | numérico | Tipo **tempo** |
| `quantity_saved_per_day`, `unit_material_cost` | numérico | Tipo **material** |
| `fixed_daily_savings` | numérico | Tipo **financeiro** |
| `daily_savings`, `annual_savings` | calculados | `KaizenSavingsCalculator` na API |
| `realized_daily_savings`, `realized_annual_savings` | numérico | V032; fallback = estimativa calculada se omitido |

Tabelas relacionadas: `kaizen_revisions`, `kaizen_participants`, `kaizen_evidences`, `kaizen_history`, `kaizen_audit_log` (V029–V034).

Cálculo de economia (domínio): `api-delpi/app/domain/services/kaizen/kaizen_savings_calculator.py`.

## Estrutura do código (MFE)

```text
src/
  api/kaizenApi.ts          # Cliente REST (base /apps/api-delpi/...)
  api/httpClient.ts         # JWT + X-Delpi-Caller-App
  pages/
    CadastroKaizenPage.tsx  # Roteamento list | new | edit | dashboard | detail
    KaizenListPage.tsx      # Tabela + importar planilha
    KaizenFormPage.tsx      # Criar / editar
    KaizenDashboardPage.tsx # Painel KPI + filtros
    KaizenDetailPage.tsx    # Ficha com revisões
  components/ui/            # Wrappers finos @delpi/plugin-ui (prefixo kz)
  components/form/          # KaizenFormFields, CategoryMultiSelect, domínio
  constants/kaizen.ts       # Status, filiais, payload do formulário
  content/helpTooltips.ts   # Textos PT-BR (balões de ajuda)
```

UI compartilhada: [docs/UI-PLUGIN-UI.md](./docs/UI-PLUGIN-UI.md).

### UI compartilhada (`@delpi/plugin-ui`)

Primitivos de formulário, filtros, KPI, tabelas e seções foram centralizados no pacote [`@delpi/plugin-ui`](../plugin-ui/README.md). O plugin expõe wrappers em `src/components/ui/` (BEM `kz-*`).

**Documentação completa:** [docs/UI-PLUGIN-UI.md](./docs/UI-PLUGIN-UI.md)

## Desenvolvimento local

```bash
cd plugins/cadastro-kaizen
npm install
npm run dev          # Vite (porta padrão do plugin)
npm run ci           # lint + build
```

## Docker (compose dev)

Serviço `cadastro-kaizen` → container `delpi-cadastro-kaizen`.

```bash
cd infra
docker compose -f docker-compose.dev.yml --env-file .env up -d --build \
  cadastro-kaizen api-delpi gateway
```

Assets: `http://localhost/apps/cadastro-kaizen/assets/remoteEntry.js`

## Build e registro no portal

```bash
cd plugins/cadastro-kaizen
npm run build

export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
./scripts/register-manifest.sh
```

Manifesto: `cadastro-kaizen.manifest.json` (`schemaVersion` 1.0.0, `renderMode: federated`).

Após o registro, atribua `cadastro-kaizen.view` e `cadastro-kaizen.manage` aos perfis de qualidade na Core API.

## Migrations

Pasta: `api-delpi/migrations/plugins/quality/` — principais:

| Migration | Conteúdo |
|-----------|----------|
| V026 | `quality.submodules` |
| V027 | `quality.kaizens` |
| V029–V031 | Revisões, evidências, campos ricos, participantes |
| V032 | Economia realizada |
| V033–V034 | Auditoria, ciclo de vida de versões |
| V035 | `date_idea_received` |
| V036 | `categories TEXT[]` |

```bash
# Status (container)
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin quality

# Local
cd api-delpi
python scripts/run_plugins_migrations.py --plugin quality
```

Com `RUN_PLUGINS_MIGRATIONS_ON_STARTUP=true` (default no compose), migrations rodam no boot da api-delpi.

## Backend (api-delpi)

| Módulo | Arquivo |
|--------|---------|
| Rotas CRUD + import | `app/interface/http/routes/quality/kaizen_records_router.py` |
| Repositório Postgres | `app/infrastructure/persistence/plugins/repositories/kaizen/postgres_kaizen_repository.py` |
| Importação Sheets | `app/application/use_cases/kaizen/import_kaizens_from_sheet_use_case.py` |
| Mapper planilha → POST | `app/domain/services/kaizen/kaizen_sheet_import_mapper.py` |
| Composer | `app/composition/kaizen_composer.py` |

Testes: `tests/unit/test_kaizen_savings_calculator.py`, `tests/unit/test_import_kaizens_from_sheet_use_case.py`, smoke em `tests/test_route_meta_smoke.py` (filtro `kaizen`).

## Relação com o dashboard de qualidade

- **Cadastro** (`cadastro-kaizen`): Postgres, CRUD completo, importação one-shot da planilha.
- **Dashboard** (`dashboard-quality`): KPIs e tabela via `/quality/kaizens/summary` (Sheets).

Até unificar a leitura analítica no Postgres, alterações no cadastro **não** refletem automaticamente no dashboard — planeje sincronização ou migração da rota `summary`.

## Homologação rápida

```bash
# MFE no ar
curl -sf -o /dev/null -w "%{http_code}\n" \
  http://localhost/apps/cadastro-kaizen/assets/remoteEntry.js

# API com token
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
curl -sf -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: cadastro-kaizen" \
     "http://localhost/apps/api-delpi/quality/kaizens/records" \
  | jq '.success'
```

## Referências

- **Roadmap completo:** [docs/12-roadmap-e-volucao/cadastro-kaizen/ROADMAP.md](../../docs/12-roadmap-e-volucao/cadastro-kaizen/ROADMAP.md)
- **Revisões temporais (design):** [ESPECIFICACAO-REVISOES.md](../../docs/12-roadmap-e-volucao/cadastro-kaizen/ESPECIFICACAO-REVISOES.md)
- **Status atual:** [docs/12-roadmap-e-volucao/cadastro-kaizen/status-atual.md](../../docs/12-roadmap-e-volucao/cadastro-kaizen/status-atual.md)
- Doc técnica: [docs/DOCUMENTACAO.md](./docs/DOCUMENTACAO.md)
- Inventário de plugins: [docs/08-plugins/README.md](../../docs/08-plugins/README.md)
- Registro de plugin: [docs/10-guias-operacionais/registrar-plugin-dev-local.md](../../docs/10-guias-operacionais/registrar-plugin-dev-local.md)
- Kaizen Sheets (testes sem TOTVS): [api-delpi/docs/api/12-testes-sem-totvs-google-sheets.md](../../api-delpi/docs/api/12-testes-sem-totvs-google-sheets.md)
