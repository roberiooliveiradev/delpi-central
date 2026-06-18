# Como testar — Inspeções de Entrada

## 1. Build local

```bash
cd plugins/inspecoes-entrada
npm install
npm run ci
```

Saída esperada: `dist/assets/remoteEntry.js`.

## 2. Stack Docker (recomendado)

```bash
cd infra
docker compose -f docker-compose.dev.yml --env-file .env up -d --build \
  gateway core-api api-delpi inspecoes-entrada
```

Aguarde os containers. Acesse:

```text
http://localhost/apps/inspecoes-entrada/filial-01
http://localhost/apps/inspecoes-entrada/filial-02?tab=historico
```

## 3. Registrar o plugin (primeira vez)

Com JWT de usuário com `apps.manage`:

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
bash plugins/inspecoes-entrada/scripts/register-manifest.sh
```

Conceda `inspecoes-entrada.view.filial-01` e/ou `inspecoes-entrada.view.filial-02` ao perfil de Qualidade no admin RBAC.

## 4. Permissões

O usuário precisa de **uma** das permissões:

- `inspecoes-entrada.view.filial-01` (filial 01)
- `inspecoes-entrada.view.filial-02` (filial 02)
- `inspecoes-entrada.view` (ambas)
- `api-delpi.access` (legado)

Consulta a filial sem permissão específica retorna **403** (exceto superadmin ou `inspecoes-entrada.view`).

## 5. Smoke test HTTP

### Assets (sem token)

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  http://localhost/apps/inspecoes-entrada/assets/remoteEntry.js
# esperado: 200
```

### API (com token)

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"

curl -sf -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: inspecoes-entrada" \
     "http://localhost/apps/api-delpi/inspecoes-entrada/resumo?branch=01" \
  | jq '.success, .meta.operationId'

curl -sf -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: inspecoes-entrada" \
     "http://localhost/apps/api-delpi/inspecoes-entrada/historico?branch=01&page=1&page_size=5" \
  | jq '.data.pagination'
```

## 6. Validação views TOTVS (Fase 0)

Requer container `delpi-api-delpi` com conectividade SQL Server:

```bash
docker exec delpi-api-delpi python scripts/validate_inspecoes_entrada_views.py
```

Relatório JSON opcional:

```bash
docker exec delpi-api-delpi python scripts/validate_inspecoes_entrada_views.py \
  --json /tmp/inspecoes-entrada-fase0.json
```

Ver [FASE0-VALIDACAO.md](../../../docs/12-roadmap-e-volucao/inspecoes-entrada/FASE0-VALIDACAO.md).

## 7. Testes automatizados (api-delpi)

```bash
cd api-delpi
PYTHONPATH="../shared:.:." pytest tests/test_inspecoes_entrada_* -q
PYTHONPATH="../shared:.:." pytest tests/test_route_meta_smoke.py -k inspecoes_entrada -q
```

## 8. Checklist manual de UI

- [ ] Visão geral carrega KPIs e três blocos analíticos
- [ ] Tabela de pendências exibe status e quantidade
- [ ] Aba Histórico respeita `?tab=historico` na URL
- [ ] Filtros de histórico disparam nova consulta (paginação reset)
- [ ] Clique em linha abre modal com ensaios
- [ ] Impressão de certificado abre janela (inspeção aprovada)
- [ ] Botão Atualizar recarrega dados da aba ativa
- [ ] Tema claro e escuro legíveis (tokens do portal)
- [ ] Layout responsivo em viewport ≤ 768px
