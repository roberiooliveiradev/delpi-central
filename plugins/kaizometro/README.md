# Kaizômetro — plugin Minha DELPI

Microfrontend federado para **cadastro operacional** de melhorias contínuas (kaizen) no módulo qualidade. Os dados ficam em **PostgreSQL** (`quality.kaizens`); o dashboard de qualidade e a TV leem a mesma fonte (sem Google Sheets).

## Visão geral

| Camada | Responsabilidade |
|--------|------------------|
| **MFE** `kaizometro` | Listagem, ficha, dashboard, compartilhar sugestão (QR/PNG) |
| **public-hub** `/p/kaizen/sugestao/aberto` | Formulário público (wizard 2 etapas, sem login) |
| **api-delpi** `/quality/kaizens/records` | CRUD autenticado + import/export JSON |
| **api-delpi** `POST /public/kaizen/suggestions` | Cria sugestão pública (`status=recebido`) + notifica Core |
| **api-delpi** `/quality/kaizens/summary` | Leitura analítica (PostgreSQL) — dashboard-quality / TV |
| **PostgreSQL** `quality.kaizens` | Fonte de verdade do cadastro e da leitura analítica |

```text
Portal → /apps/kaizometro  (JWT)
           ↓
         api-delpi /quality/kaizens/records → Postgres

Compartilhar sugestão → QR/link → public-hub /p/kaizen/sugestao/aberto
           ↓ (sem JWT)
         POST /apps/api-delpi/public/kaizen/suggestions
           ↓
         Postgres (status recebido) + sino Core (permission notify-suggestions)

Dashboard qualidade → /quality/kaizens/summary (PostgreSQL)
```

## Rotas da UI

| Path | Tela |
|------|------|
| `/apps/kaizometro` | Listagem com filtros e tabela paginada |
| `/apps/kaizometro/novo` | Formulário de criação |
| `/apps/kaizometro/detalhe/{uuid}` | Ficha visual com edição por seção, versões, evidências e **Exportar PDF** (1 folha A4) |
| `/apps/kaizometro/editar/{uuid}` | Formulário legado de edição (redireciona ao detalhe quando aplicável) |

Navegação interna via estado do MFE (`CadastroKaizenPage`); o Portal monta o plugin em `basePath` do manifesto.

### Exportar PDF da ficha (1 folha)

Na tela de detalhe, o botão **Exportar PDF** gera uma ficha A4 (layout certificado DELPI via `@delpi/plugin-ui`) com identificação, datas, economia, narrativa (processo / problema / melhoria / resultado) e equipe da **versão selecionada**. Abre o diálogo de impressão do navegador — use **Salvar como PDF**. Não inclui fotos de evidência, changelog nem histórico completo de versões.

Arquivos: `src/utils/kaizenPdfSpec.ts`, `src/utils/exportKaizenPdf.ts`.

## Formulário público de sugestão

| Item | Detalhe |
|------|---------|
| UI | public-hub — `/p/kaizen/sugestao/aberto` (token estático `aberto`) |
| Abertura | Botão **Compartilhar sugestão** na listagem (QR + link + **Exportar PNG**) |
| Fluxo UI | Wizard **2 etapas** (Identificação → Melhoria) com **% de preenchimento** e tela de conclusão |
| API | `POST /apps/api-delpi/public/kaizen/suggestions` (**sem JWT**; liberada no `auth_middleware` por prefixo `/public/kaizen/`) |
| Status inicial | `recebido` (não conta quantidade mensal nem ganhos financeiros) |
| Pipeline | `recebido` → `aprovado` (comitê) → `implantado` |
| Notificação | Sino do portal para quem tem `kaizometro.notify-suggestions` |
| Env | `KAIZEN_NOTIFICATIONS_ENABLED` (default `true`) + `CORE_API_BASE_URL` + `CORE_API_INTEGRATIONS_SERVICE_TOKEN` |

Campos do formulário público (espelham MS Forms / planilha): nome, setor, matrícula (cadastro), CT/local, problema, solução proposta. Honeypot `website` descarta bots.

Arquivos: `plugins/public-hub/src/apps/kaizen/` · util de link/QR em `src/utils/kaizenPublicSuggestionLink.ts` · modal `KaizenShareSuggestionModal`.

### Exemplo — sugestão pública

```bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "proposer_name": "Maria Silva",
    "sector": "Produtivo",
    "employee_registration": "12345",
    "work_center_or_location": "CT-16",
    "problem_description": "Tempo excessivo na troca de resina.",
    "proposed_solution": "Kit pré-montado e check-list visual."
  }' \
  "http://localhost/apps/api-delpi/public/kaizen/suggestions" \
  | jq '.success, .data'
```

## Status e indicadores (cadastro / painel)

| Status | Quantidade mensal | Ganhos financeiros | Datas |
|--------|-------------------|--------------------|-------|
| `recebido` | Não | Não | Ideia registrada |
| `aprovado` | Sim (`date_committee_approved`, senão `date_implemented`) | Não | Exige `date_committee_approved` |
| `implantado` | Sim | Sim | Exige `date_implemented` |
| `descontinuado` / `cancelado` | — | Interrompe conforme regras de vigência | — |

Migrations: **V042** (`aprovado` + `date_committee_approved`) · **V043** (`em_andamento` → `recebido`). Domínio: `kaizen_status_date_rules`, `kaizen_indicator_eligibility`.

## API (gateway)

Base HTTP: **`/apps/api-delpi/quality/kaizens/records`**

| Método | Rota (relativa à api-delpi) | Descrição |
|--------|----------------------------|-----------|
| GET | `/quality/kaizens/records` | Lista paginada (`meta.shape`: `paged_list`) |
| POST | `/quality/kaizens/records` | Cria registro |
| GET | `/quality/kaizens/records/{id}` | Detalhe (UUID Postgres) |
| PUT | `/quality/kaizens/records/{id}` | Atualiza |
| DELETE | `/quality/kaizens/records/{id}` | Exclusão lógica (`deleted_at`) |
| POST | `/quality/kaizens/records/import` | Importa JSON exportado (backup entre ambientes) |

**Leitura analítica (PostgreSQL — mesma fonte do cadastro):**

| Método | Rota | Fonte |
|--------|------|-------|
| GET | `/quality/kaizens/summary` | PostgreSQL |
| GET | `/quality/kaizens/{kaizen_id}` | PostgreSQL (`{kaizen_id:path}` — aceita `/` no ID legado) |

| GET | `/quality/kaizens/records/{id}/revisions` | Revisões / snapshots |
| POST | `/quality/kaizens/records/{id}/versions` | Nova versão (rascunho) |
| POST | `/quality/kaizens/records/{id}/versions/{n}/implement` | Implantar versão |
| GET | `/quality/kaizens/records/{id}/evidences` | Evidências (Antes/Depois) |
| GET | `/quality/kaizens/records/{id}/savings-timeline` | Ganhos por período |

**Público (sem JWT):**

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/public/kaizen/suggestions` | Cria sugestão (`status=recebido`); honeypot `website` |

Documentação detalhada: [docs/DOCUMENTACAO.md](./docs/DOCUMENTACAO.md) · [api-delpi/docs/api/06-modulos-departamentais.md](../../api-delpi/docs/api/06-modulos-departamentais.md) (§ Cadastro operacional).

### Exemplo — listar

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"

curl -s -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: kaizometro" \
     "http://localhost/apps/api-delpi/quality/kaizens/records?page_size=50" \
  | jq '.success, .data.pagination'
```

### Exemplo — importar JSON (backup)

```bash
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Delpi-Caller-App: kaizometro" \
  -H "Content-Type: application/json" \
  -d @kaizens-export.json \
  "http://localhost/apps/api-delpi/quality/kaizens/records/import" \
  | jq '.data | {created, skipped, errors}'
```

A importação JSON é **idempotente** no que couber ao use case de import — use o export da própria API como fonte.

## Permissões

| Código | Uso |
|--------|-----|
| `kaizometro.view` | Abrir o app / listar (capacidade) |
| `kaizometro.manage` | Criar, editar, excluir e importar |
| `kaizometro.notify-suggestions` | Alerta no portal ao receber sugestão pública |
| `kaizometro.branch-01` | Escopo: unidade 01 (Santa Catarina) |
| `kaizometro.branch-02` | Escopo: unidade 02 (Espírito Santo) |

`view`/`manage` **não** liberam unidades sozinhas — atribua também `branch-01` e/ou `branch-02`. Superadmin opera ambas.

Na api-delpi, rotas de leitura aceitam também `api-delpi.quality.access` e `dashboard-quality.view`; escrita autenticada exige `kaizometro.manage` (ou `api-delpi.access` / `api-delpi.quality.access`). A rota pública de sugestão não exige JWT; o link deve levar `?unidade=01|02`.

**Janela de migração (rename `cadastro-kaizen` → `kaizometro`):** a API ainda aceita as permissões legadas `cadastro-kaizen.view` / `.manage` / `.notify-suggestions` nas mesmas listas. Remova-as após remapear os perfis RBAC (ver runbook abaixo).

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
  api/kaizenApi.ts                    # Cliente REST autenticado
  api/httpClient.ts                   # JWT + X-Delpi-Caller-App
  pages/
    CadastroKaizenPage.tsx            # Roteamento list | new | edit | dashboard | detail
    KaizenListPage.tsx                # Tabela + Compartilhar sugestão
    KaizenFormPage.tsx                # Criar
    KaizenDashboardPage.tsx           # Painel KPI + filtros
    KaizenDetailPage.tsx              # Ficha com revisões + Exportar PDF
  components/
    KaizenShareSuggestionModal.tsx    # QR + link + Exportar PNG
    KaizenListHeaderActions.tsx
    form/ … detail/ … ui/
  utils/kaizenPublicSuggestionLink.ts # URL pública + QR + download PNG
  utils/kaizenPdfSpec.ts              # DelpiDocumentSpec da ficha A4
  utils/exportKaizenPdf.ts            # printDelpiDocumentSpec
  constants/kaizen.ts
  content/helpTooltips.ts

public-hub (form público):
  plugins/public-hub/src/apps/kaizen/  # SuggestionPage (wizard), api.ts, CSS
```

UI compartilhada: [docs/UI-PLUGIN-UI.md](./docs/UI-PLUGIN-UI.md).

### UI compartilhada (`@delpi/plugin-ui`)

Primitivos de formulário, filtros, KPI, tabelas e seções foram centralizados no pacote [`@delpi/plugin-ui`](../plugin-ui/README.md). O plugin expõe wrappers em `src/components/ui/` (BEM `kz-*`).

**Documentação completa:** [docs/UI-PLUGIN-UI.md](./docs/UI-PLUGIN-UI.md)

## Desenvolvimento local

```bash
cd plugins/kaizometro
npm install
npm run dev          # Vite (porta padrão do plugin)
npm run ci           # lint + build
```

## Docker (compose dev)

Serviço `kaizometro` → container `delpi-kaizometro`.

```bash
cd infra
docker compose -f docker-compose.dev.yml --env-file .env up -d --build \
  kaizometro api-delpi gateway
```

Assets: `http://localhost/apps/kaizometro/assets/remoteEntry.js`

## Build e registro no portal

```bash
cd plugins/kaizometro
npm run build

export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
./scripts/register-manifest.sh
```

Manifesto: `kaizometro.manifest.json` (`schemaVersion` 1.0.0, `renderMode: federated`).

Após o registro, atribua `kaizometro.view` e as unidades (`kaizometro.branch-01` / `branch-02`); quem edita precisa de `kaizometro.manage`; gestores do sino precisam de `kaizometro.notify-suggestions`.

## Deploy / rename (produção)

Ordem segura após o rename do slug (`cadastro-kaizen` → `kaizometro`). Executar a partir da raiz do monorepo; preferir scripts sequenciais ([infra-sequential](../../infra/README-ambiente.md)).

1. `git pull` no `srv-api`.
2. Rebuild MFE: `./infra/scripts/up-prod-sequential.sh --fase mfe --build kaizometro` (e `plugin-ui` só se necessário).
3. Subir o serviço Compose `kaizometro` (`delpi-kaizometro`); remover o container antigo `delpi-cadastro-kaizen` só depois do novo healthy.
4. Recreate/restart **gateway** (redirect legado + upstream): `docker restart delpi-gateway` após recreate do MFE.
5. Rebuild/restart **api-delpi** (dual `kaizometro.*` + `cadastro-kaizen.*`) e **core-api** (catálogo `kaizometro` + `legacyCategoryAliases.cadastro_kaizen`).
6. **Register** do novo manifesto: `./plugins/kaizometro/scripts/register-manifest.sh` (novo `id` — não “patchar” o plugin antigo).
7. **RBAC:** nos perfis que tinham `cadastro-kaizen.*`, atribuir `kaizometro.view` | `manage` | `notify-suggestions`.
8. Smoke:
   - `curl …/apps/kaizometro/assets/remoteEntry.js`
   - `curl -I …/apps/cadastro-kaizen` → **301** para `/apps/kaizometro`
   - Listagem com JWT + `X-Delpi-Caller-App: kaizometro`
   - Sugestão pública `/p/kaizen/…` intacta
   - Sino (se token Core Integrations ok)
9. Desativar/unregister o plugin antigo `cadastro-kaizen` na Core (após validar o menu).
10. **Cleanup posterior** (PR separado, após 1–2 sprints): remover permissões legadas das listas da API e, se desejado, o redirect nginx.

**Não muda neste rename:** schema `quality.kaizens*`, paths `/quality/kaizens/*`, `/public/kaizen/*`, public-hub `/p/kaizen/…`, prefixo CSS `kz-*`.

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
| V042 | Status `aprovado` + `date_committee_approved` |
| V043 | Rename `em_andamento` → `recebido` (default + CHECKs) |

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
| Rota pública | `app/interface/http/routes/quality/kaizen_public_router.py` |
| Notificação Core | `app/application/services/kaizen_portal_notification_service.py` |
| Mapper sugestão pública | `app/domain/services/kaizen/kaizen_public_suggestion_mapper.py` |
| Repositório Postgres | `app/infrastructure/persistence/plugins/repositories/kaizen/postgres_kaizen_repository.py` |
| Composer | `app/composition/kaizen_composer.py` |

Testes: `tests/unit/test_kaizen_*.py`, `test_kaizen_public_suggestion_mapper.py`, `test_kaizen_portal_notification_service.py`, smoke `test_route_meta_smoke.py` (filtro `kaizen`).

## Relação com o dashboard de qualidade

- **Cadastro** (`kaizometro`): Postgres, CRUD completo, import/export JSON.
- **Dashboard** (`dashboard-quality`): KPIs e tabela via `/quality/kaizens/summary` (também PostgreSQL).

Cadastro e leitura analítica compartilham a mesma base — alterações no Kaizômetro refletem no dashboard.

## Homologação rápida

```bash
# MFE no ar
curl -sf -o /dev/null -w "%{http_code}\n" \
  http://localhost/apps/kaizometro/assets/remoteEntry.js

# API com token
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
curl -sf -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: kaizometro" \
     "http://localhost/apps/api-delpi/quality/kaizens/records" \
  | jq '.success'
```

## Referências

- **Roadmap completo:** [docs/12-roadmap-e-volucao/kaizometro/ROADMAP.md](../../docs/12-roadmap-e-volucao/kaizometro/ROADMAP.md)
- **Revisões temporais (design):** [ESPECIFICACAO-REVISOES.md](../../docs/12-roadmap-e-volucao/kaizometro/ESPECIFICACAO-REVISOES.md)
- **Status atual:** [docs/12-roadmap-e-volucao/kaizometro/status-atual.md](../../docs/12-roadmap-e-volucao/kaizometro/status-atual.md)
- Doc técnica: [docs/DOCUMENTACAO.md](./docs/DOCUMENTACAO.md)
- Inventário de plugins: [docs/08-plugins/README.md](../../docs/08-plugins/README.md)
- Registro de plugin: [docs/10-guias-operacionais/registrar-plugin-dev-local.md](../../docs/10-guias-operacionais/registrar-plugin-dev-local.md)
- Kaizen Sheets (testes sem TOTVS): [api-delpi/docs/api/12-testes-sem-totvs-google-sheets.md](../../api-delpi/docs/api/12-testes-sem-totvs-google-sheets.md)
