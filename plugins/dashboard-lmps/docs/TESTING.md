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

| Área | O que validar |
|------|----------------|
| Carga inicial | KPIs e gráficos após login com permissão |
| Data inicial | Após primeira carga com dados, data inicial ajusta para a proposta mais antiga |
| Filtros | Alterar filial, status e período → dados e tabela atualizam |
| Atualizar | Botão recarrega sem perder filtros |
| Auto-refresh | Após ~2 min com aba visível, banner "Atualizando dados..." |
| Erro parcial | Simular falha de rede com dados já carregados → mantém última carga + aviso |
| Tabela | Colunas filial, proposta, nível, lead time, status classificação |
| Gráficos | Pizzas (nível/status), barras (lead por nível), linha (evolução) |
| Vazio | Período sem LMPs → mensagem na tabela e gráficos zerados |

## 7. URLs úteis

| Recurso | URL |
|---------|-----|
| Plugin | `http://localhost/apps/dashboard-lmps` |
| remoteEntry | `http://localhost/apps/dashboard-lmps/assets/remoteEntry.js` |
| API dashboard | `http://localhost/apps/api-delpi/engineering/lmps/dashboard` |
| API listagem | `http://localhost/apps/api-delpi/engineering/lmps` |

## 8. Troubleshooting

| Sintoma | Ação |
|---------|------|
| 403 na API | Verificar `dashboard-lmps.view` ou `api-delpi.access` |
| 502 em `/apps/api-delpi/*` | Reiniciar `gateway` após recreate do `api-delpi` |
| Plugin em branco | Verificar `remoteEntry.js` 200 e console do browser (federation) |
| Menu duplicado LMPs | Conferir apps `dash-lmps` vs `dashboard-lmps` na Core API |

Detalhes: [DOCUMENTACAO.md](./DOCUMENTACAO.md).
