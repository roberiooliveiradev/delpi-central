# Como testar — Dashboard LMPs

## 1. Build local

```bash
cd plugins/dashboard-lmps
npm install
npm run build
npm run lint
```

Saída esperada: `dist/assets/remoteEntry.js`.

## 2. Stack Docker (recomendado)

```bash
cd infra
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build \
  gateway core-api dashboard-lmps
```

Aguarde os containers. Acesse:

```text
http://localhost/apps/dashboard-lmps
```

## 3. Registrar o plugin (primeira vez)

Com JWT de usuário com `apps.manage`:

```bash
export TOKEN="<jwt>"
curl -s -X POST "http://localhost/core-api/admin/apps/register" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @plugins/dashboard-lmps/dash-lmps-microfrontend.manifest.json
```

Conceda `dashboard-lmps.view` ao perfil de Engenharia no admin RBAC.

> Se já existir app legado `dash-lmps` (iframe), avalie desativar a versão antiga para evitar duplicidade no menu.

## 4. Permissões

O usuário precisa de **uma** das permissões:

- `dashboard-lmps.view`
- `api-delpi.access`

## 5. Smoke test HTTP

### Assets (sem token)

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  http://localhost/apps/dashboard-lmps/assets/remoteEntry.js
# esperado: 200
```

### API dashboard (com token)

```bash
export TOKEN="<jwt>"
export BASE="http://localhost/apps/api-delpi/engineering"

curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE/lmps/dashboard?date_start=2025-01-01&date_end=2026-12-31&status=Todos" | jq .
```

## 6. Checklist manual na UI

### Lista (`/apps/dashboard-lmps`)

| Área | O que validar |
|------|----------------|
| Carga inicial | KPIs e gráficos após login com permissão |
| Data inicial | Após primeira carga com dados, data inicial ajusta para a proposta mais antiga |
| Filtros | Alterar filial, status e período → dados e tabela atualizam |
| URL | Alterar filtros atualiza query string; recarregar a página mantém filtros |
| Atualizar | Botão recarrega sem perder filtros |
| Auto-refresh | Após ~2 min com aba visível, banner "Atualizando dados..." |
| Erro parcial | Simular falha de rede com dados já carregados → mantém última carga + aviso |
| Tabela | Colunas filial, proposta, nível, lead time, status classificação; ⓘ em todos os cabeçalhos |
| Lead time | Período curto (ex. 01–15/06/2026): `lead_time_util` coerente com `Data Início`/`Data Fim` da linha (dias úteis, tipicamente poucos dias — não centenas por OV antiga reentrante) |
| KPI lead time | `avg_lead_time` próximo da média manual das linhas com `lead_time_util` preenchido |
| Gráficos | Pizzas (nível/status), barras (lead por nível), linha (evolução); multi-select nos filtros |
| Vazio | Período sem LMPs → mensagem na tabela e gráficos zerados |
| Exportar CSV | Download com filtros atuais |

### Detalhe OV (`/apps/dashboard-lmps/ov/{sale_number}`)

| Área | O que validar |
|------|----------------|
| Navegação | Clique na linha abre detalhe; **Voltar** retorna à lista **sem** esvaziar tabela/KPIs e **sem** perder filtros da URL |
| Cards / KPIs | Proposta, Engenharia, Cliente; tooltips nos campos |
| Produtos + BOM | Tabela de produtos; árvore de estrutura expandível; legenda e tooltips nos nós |
| Histórico | Toggle Linha do tempo / Tabela; filtros Todos / Engenharia / Em aberto / Revisão atual |
| Gantt | Mini-Gantt por evento na timeline; Gantt global no topo |
| Preferências | View e filtro do histórico persistem após F5 (`localStorage`) |
| Tooltips tabela | ⓘ em todas as colunas do histórico (incl. Situação); balões não cortados em scroll horizontal |
| Impressão | Ctrl+P oculta chrome desnecessário (`@media print`) |

### API (detalhe + histórico)

```bash
# Cabeçalho e produtos (sem histórico)
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE/lmps/000123?date_start=2025-01-01&date_end=2026-12-31&branch=01" \
  | jq '.data | {sale_number, reference_revision, list_history}'

# Eventos AIJ010
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE/lmps/000123/history/events?date_start=2025-01-01&date_end=2026-12-31&branch=01" \
  | jq '.data.items[0] | {process_label, status_label, is_open, duration_display, is_current}'

# Fluxo engenharia (idas/voltas)
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE/lmps/000123/history/flow?branch=01" \
  | jq '.data.items[0] | {flow_transition, flow_transition_label, is_engineering_entry}'
```

Esperado: detalhe com `list_history: []`; eventos e fluxo enriquecidos quando a OV tem histórico AIJ010.

## 7. URLs úteis

| Recurso | URL |
|---------|-----|
| Plugin | `http://localhost/apps/dashboard-lmps` |
| remoteEntry | `http://localhost/apps/dashboard-lmps/assets/remoteEntry.js` |
| API dashboard | `http://localhost/apps/api-delpi/engineering/lmps/dashboard` |
| API listagem | `http://localhost/apps/api-delpi/engineering/lmps` |
| Detalhe OV (ex.) | `http://localhost/apps/dashboard-lmps/ov/000123` |
| API detalhe OV | `http://localhost/apps/api-delpi/engineering/lmps/{sale_number}` |
| API histórico eventos | `http://localhost/apps/api-delpi/engineering/lmps/{sale_number}/history/events` |
| API histórico fluxo | `http://localhost/apps/api-delpi/engineering/lmps/{sale_number}/history/flow` |

## 8. Troubleshooting

| Sintoma | Ação |
|---------|------|
| 403 na API | Verificar `dashboard-lmps.view` ou `api-delpi.access` |
| 502 em `/apps/api-delpi/*` | Reiniciar `gateway` após recreate do `api-delpi` |
| Plugin em branco | Verificar `remoteEntry.js` 200 e console do browser (federation) |
| Menu duplicado LMPs | Conferir apps `dash-lmps` vs `dashboard-lmps` na Core API |

Detalhes: [DOCUMENTACAO.md](./DOCUMENTACAO.md).
