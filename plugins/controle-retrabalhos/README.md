# Controle de Retrabalhos — plugin Minha DELPI

Microfrontend (Module Federation) para dashboard de **horas improdutivas de retrabalho** (motivo `RT`), alimentado pela view TOTVS `dbo.VW_BI_RT_HORAS_IMPRODUTIVAS` via **api-delpi**.

Documentação de roadmap: [docs/12-roadmap-e-evolucao/controle-retrabalhos/](../../docs/12-roadmap-e-evolucao/controle-retrabalhos/) · API: [controle-retrabalhos.md](../../api-delpi/docs/api/controle-retrabalhos.md).

---

## Visão geral

| Camada | Responsabilidade |
|--------|------------------|
| **MFE** `controle-retrabalhos` | KPIs, gráficos mensais, rankings, tabela paginada, export Excel |
| **api-delpi** `/retrabalhos/*` | Leitura TOTVS (view BI) + RBAC por filial |
| **TOTVS** | View `dbo.VW_BI_RT_HORAS_IMPRODUTIVAS` |

```text
Portal → /apps/controle-retrabalhos/sc|es
           ↓ Module Federation (remoteEntry.js)
         MFE controle-retrabalhos
           ↓ JWT + X-Delpi-Caller-App: controle-retrabalhos
Gateway → /apps/api-delpi/retrabalhos/*
           ↓
         api-delpi → SQL Server (WITH NOLOCK)
```

---

## Funcionalidades

- Duas entradas no menu: **SC** (filial `01`) e **ES** (filial `02`)
- Filtro de período (padrão últimos 12 meses) com atalhos 6m / 12m / mês atual
- KPIs: apontamentos, horas, custo, custo médio/hora, horas sem custo
- Gráficos: evolução mensal (custo e horas), ranking top 10 recursos e colaboradores
- Tabela de detalhes paginada + exportação Excel (todas as páginas)

---

## Rotas da UI

| Path | Filial TOTVS |
|------|----------------|
| `/apps/controle-retrabalhos/sc` | `01` |
| `/apps/controle-retrabalhos/es` | `02` |

---

## API (gateway)

Base HTTP: **`/apps/api-delpi/retrabalhos`**

| Método | Rota | Uso no MFE |
|--------|------|------------|
| GET | `/resumo` | KPIs |
| GET | `/mensal` | Gráficos mensais |
| GET | `/recursos` | Ranking recursos |
| GET | `/colaboradores` | Ranking colaboradores |
| GET | `/detalhes` | Tabela paginada |
| GET | `/filtros` | Opções de filtro (API pronta; UI futura) |
| GET | `/health` | Health check da view |

Parâmetros comuns: `filial` (obrigatório), `dataInicio`, `dataFim` (YYYY-MM-DD). Respostas no envelope padrão api-delpi.

### Exemplo — resumo

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"

curl -s -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: controle-retrabalhos" \
     "http://localhost/apps/api-delpi/retrabalhos/resumo?filial=01&dataInicio=2025-07-01&dataFim=2026-07-07" \
  | jq '.success, .meta.operationId, .data.totalHoras'
```

---

## Permissões (Portal / Keycloak)

| Código | Escopo |
|--------|--------|
| `controle-retrabalhos.access` | Abrir o app |
| `controle-retrabalhos.view.filial-sc` | Dados filial SC (`01`) |
| `controle-retrabalhos.view.filial-es` | Dados filial ES (`02`) |
| `controle-retrabalhos.view` | Ambas filiais (legado) |
| `controle-retrabalhos.export` | Export Excel (UI) |

A **api-delpi** valida filial no router: usuário só com `.view.filial-sc` recebe `403` ao consultar `filial=02`.

---

## Desenvolvimento local

```bash
cd plugins/controle-retrabalhos
npm install
npm run build
```

A partir de `infra/`:

```bash
docker compose -f docker-compose.dev.yml --profile plugins up -d controle-retrabalhos gateway api-delpi
```

Após mudanças só no **backend**:

```bash
docker compose -f docker-compose.dev.yml restart api-delpi
```

---

## Registro no Portal

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
./plugins/controle-retrabalhos/scripts/register-manifest.sh
```

Atribuir permissões no RBAC conforme perfil (filial SC, ES ou ambas).

---

## Smoke

```bash
curl -sI http://localhost/apps/controle-retrabalhos/assets/remoteEntry.js

# Com JWT:
TOKEN="$(bash infra/scripts/get-dev-token.sh)" \
  curl -s -H "Authorization: Bearer $TOKEN" \
       -H "X-Delpi-Caller-App: controle-retrabalhos" \
       "http://localhost/apps/api-delpi/retrabalhos/health" | jq .
```

Validação da view TOTVS (Fase 0):

```bash
docker exec delpi-api-delpi python scripts/validate_retrabalho_horas_improdutivas_view.py
```

---

## Estrutura do código

```text
src/
  api/              # retrabalhoApi.ts, httpClient, export bulk
  components/       # KPIs, gráficos, filtros, tabela, modal
  hooks/            # dashboard (parallel fetch) + detalhes paginados
  pages/            # ControleRetrabalhosPage
  constants/        # filiais, tema de gráficos
  utils/            # datas, formatação, export Excel
```
