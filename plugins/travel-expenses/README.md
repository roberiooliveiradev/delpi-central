# Plugin Despesas de Viagem

Prestação de contas de viagem: o colaborador abre um rascunho, lança despesas com foto do cupom e monta o pacote imprimível. Envio ao financeiro e aprovação ficam fora deste P0.

## Fluxo

```text
Portal → plugins/travel-expenses (MFE) → /apps/travel-expenses-api → schema travel_expenses (postgres-plugins)
```

O MFE **não** chama a api-delpi.

## Rotas UI

| Path | Descrição |
|------|-----------|
| `/apps/travel-expenses` | Hub — KPIs, atalhos e recentes |
| `/apps/travel-expenses/reports` | Lista (filtros na URL: `scope`, `unit`, `q`, `from`, `to`) |
| `/apps/travel-expenses/reports/new` | Nova prestação |
| `/apps/travel-expenses/reports/{id}` | Workspace (cabeçalho, despesas, cupons, prontidão) |
| `/apps/travel-expenses/reports/{id}/package` | Pacote A4 (`DocumentReader`) + download PDF |

## API

Base: `/apps/travel-expenses-api` — ver [travel-expenses-api/README.md](../../travel-expenses-api/README.md).

## Permissões

| Código | Escopo |
|--------|--------|
| `travel-expenses.view` | Abrir e ver os próprios rascunhos |
| `travel-expenses.write` | Criar/editar rascunho próprio e anexar cupom |
| `travel-expenses.manage` | Ver todas as prestações da unidade |
| `travel-expenses.admin` | Todas as unidades |
| `travel-expenses.unit.filial-01` | Dados da filial 01 (SC) |
| `travel-expenses.unit.filial-02` | Dados da filial 02 (ES) |

Combine **uma ação** (`view`, `write` ou `manage`) com **a unidade**. `travel-expenses.admin` dispensa o restante.

## Dev

```bash
cd plugins/travel-expenses && npm install && npm test && npm run build
TOKEN=… bash scripts/register-manifest.sh
./infra/scripts/up-dev-sequential.sh --fase api --build travel-expenses-api
./infra/scripts/up-dev-sequential.sh --fase mfe --build travel-expenses
```

O P0 não exige rebuild de `plugin-ui` (nenhum primitivo novo no kit).

## Smoke

```bash
curl -fsS http://localhost/apps/travel-expenses/assets/remoteEntry.js | head -c 80
curl -fsS http://localhost/apps/travel-expenses-api/health
```
