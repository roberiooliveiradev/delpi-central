# Inspeções de Entrada — plugin Minha DELPI

Microfrontend federado para **acompanhamento operacional** de inspeções de recebimento (matéria-prima e insumos), com dados do **TOTVS Protheus** via **api-delpi**.

## Visão geral

| Camada | Responsabilidade |
|--------|------------------|
| **MFE** `inspecoes-entrada` | Dashboard por filial, histórico filtrado, detalhe com ensaios e certificado |
| **api-delpi** `/inspecoes-entrada/*` | Leitura TOTVS (views + tabelas QER/QE*) |
| **TOTVS** | Views `dbo.vw_minha_delpi_inspecoes_entrada_*` |

```text
Portal → /apps/inspecoes-entrada/filial-01|02
           ↓ Module Federation (remoteEntry.js)
         MFE inspecoes-entrada
           ↓ JWT + X-Delpi-Caller-App: inspecoes-entrada
Gateway → /apps/api-delpi/inspecoes-entrada/*
           ↓
         api-delpi → SQL Server (views + QER010)
```

## Rotas da UI

| Path | Tela |
|------|------|
| `/apps/inspecoes-entrada/filial-01` | Painel filial 01 (SC) — abas **Visão geral** e **Histórico** |
| `/apps/inspecoes-entrada/filial-02` | Painel filial 02 (ES) — mesma estrutura |

A aba ativa sincroniza com a query `?tab=historico` (Visão geral = sem parâmetro).

## API (gateway)

Base HTTP: **`/apps/api-delpi/inspecoes-entrada`**

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/resumo` | KPIs da filial (pendentes, aprovadas, taxa, tempo médio) |
| GET | `/pendentes` | Listagem paginada de inspeções aguardando laudo |
| GET | `/pendentes-fornecedor` | Ranking de fornecedores com pendências |
| GET | `/rejeitadas-ensaiador` | Rejeições agrupadas por ensaiador (API pronta; UI futura) |
| GET | `/rejeitadas-produto` | Últimas rejeições por produto (dashboard) |
| GET | `/historico` | Histórico paginado com filtros |
| GET | `/historico/detalhe` | Cabeçalho + ensaios (QER) de uma inspeção |

Todas exigem `branch=01|02`. Respostas no envelope padrão api-delpi (`success`, `data`, `meta`, `message`).

Documentação detalhada: [docs/DOCUMENTACAO.md](./docs/DOCUMENTACAO.md) · [docs/API_MAPPING.md](./docs/API_MAPPING.md) · [api-delpi/docs/api/inspecoes-entrada.md](../../api-delpi/docs/api/inspecoes-entrada.md).

### Exemplo — resumo

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"

curl -s -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: inspecoes-entrada" \
     "http://localhost/apps/api-delpi/inspecoes-entrada/resumo?branch=01" \
  | jq '.success, .meta.operationId, .data.pending_inspections'
```

## Permissões

| Código | Uso |
|--------|-----|
| `inspecoes-entrada.view.filial-01` | Menu e dados da filial 01 (SC) |
| `inspecoes-entrada.view.filial-02` | Menu e dados da filial 02 (ES) |
| `inspecoes-entrada.view` | Acesso amplo (ambas filiais) |

Na api-delpi, rotas de leitura aceitam também `api-delpi.access`. Escopo por filial é validado no router (`403` se o usuário não tiver permissão da filial solicitada).

## Estrutura do código (MFE)

```text
src/
  api/inspecoesEntradaApi.ts   # Cliente REST
  api/httpClient.ts            # JWT + X-Delpi-Caller-App
  pages/
    FilialAppPage.tsx          # Shell: header, abas, refresh
    DashboardPage.tsx          # KPIs, pendências, rejeitadas
    HistoricoPage.tsx          # Filtros + tabela + modal detalhe
  hooks/                       # useInspecoesEntradaDashboard, Historico*, Detalhe
  components/                  # KpiCard, tabelas, modal, certificado
  utils/                       # badges, impressão certificado, tabs URL
```

## Desenvolvimento local

### Standalone (Vite)

Requer gateway + api-delpi rodando em `http://localhost`. O Vite faz proxy de `/apps/api-delpi`.

```bash
cd plugins/inspecoes-entrada
npm install
export TOKEN="$(bash ../../infra/scripts/get-dev-token.sh)"
echo "VITE_DEV_ACCESS_TOKEN=$TOKEN" > .env.local
npm run dev
```

Abrir `http://localhost:5173`.

### Docker (compose dev)

```bash
cd infra
docker compose -f docker-compose.dev.yml --env-file .env up -d --build \
  inspecoes-entrada api-delpi gateway
```

Assets: `http://localhost/apps/inspecoes-entrada/assets/remoteEntry.js`

## Build e registro no portal

```bash
cd plugins/inspecoes-entrada
npm run ci

export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
./scripts/register-manifest.sh
```

Manifesto: `inspecoes-entrada.manifest.json` (`schemaVersion` 1.0.0, `renderMode: federated`).

Após o registro, atribua `inspecoes-entrada.view.filial-01|02` (ou `inspecoes-entrada.view`) aos perfis de qualidade/recebimento na Core API.

## Backend (api-delpi)

| Módulo | Arquivo |
|--------|---------|
| Rotas HTTP | `app/interface/http/routes/inspecoes_entrada/inspecoes_entrada_router.py` |
| Repository TOTVS | `app/infrastructure/persistence/totvs/inspecoes_entrada/inspecoes_entrada_repository.py` |
| Composer | `app/composition/inspecoes_entrada_composer.py` |
| Validação views (Fase 0) | `scripts/validate_inspecoes_entrada_views.py` |

Testes: `tests/test_inspecoes_entrada_*` e smoke em `tests/test_route_meta_smoke.py`.

## Homologação rápida

```bash
# MFE no ar
curl -sf -o /dev/null -w "%{http_code}\n" \
  http://localhost/apps/inspecoes-entrada/assets/remoteEntry.js

# API com token
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
curl -sf -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: inspecoes-entrada" \
     "http://localhost/apps/api-delpi/inspecoes-entrada/resumo?branch=01" \
  | jq '.success'

# Validação views TOTVS (container api-delpi)
docker exec delpi-api-delpi python scripts/validate_inspecoes_entrada_views.py
```

Ver também [docs/TESTING.md](./docs/TESTING.md).

## Referências

- **Roadmap:** [docs/12-roadmap-e-volucao/inspecoes-entrada/ROADMAP.md](../../docs/12-roadmap-e-volucao/inspecoes-entrada/ROADMAP.md)
- **Status atual:** [docs/12-roadmap-e-volucao/inspecoes-entrada/status-atual.md](../../docs/12-roadmap-e-volucao/inspecoes-entrada/status-atual.md)
- **Especificação funcional:** [ESPECIFICACAO-PLUGIN.md](../../docs/12-roadmap-e-volucao/inspecoes-entrada/ESPECIFICACAO-PLUGIN.md)
- **Views TOTVS:** [ESPECIFICACAO-VIEW.md](../../docs/12-roadmap-e-volucao/inspecoes-entrada/ESPECIFICACAO-VIEW.md)
- Doc técnica: [docs/DOCUMENTACAO.md](./docs/DOCUMENTACAO.md)
- Inventário de plugins: [docs/08-plugins/README.md](../../docs/08-plugins/README.md)
- Registro de plugin: [docs/10-guias-operacionais/registrar-plugin-dev-local.md](../../docs/10-guias-operacionais/registrar-plugin-dev-local.md)
