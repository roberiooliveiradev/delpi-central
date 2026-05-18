# Como testar — Dashboard Qualidade

## 1. Build local (sem Docker)

```bash
cd plugins/dashboard-quality
npm install
npm run ci
```

Equivalente na raiz do monorepo:

```bash
./scripts/ci/build-dashboard-quality.sh
```

## 2. Stack completa (recomendado)

Na pasta `infra/`:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build \
  gateway core-api api-delpi dashboard-quality
```

Aguarde os containers ficarem healthy. A UI fica em:

```text
http://localhost/apps/dashboard-quality
```

## 3. Registrar o plugin na Core API (primeira vez)

Com usuário **superadmin** ou permissão `apps.manage`:

```bash
export TOKEN="<jwt do portal>"
./plugins/dashboard-quality/scripts/register-manifest.sh
```

Depois, no admin RBAC, conceda `dashboard-quality.view` ao grupo/perfil de Qualidade.

## 4. Permissões

O usuário precisa de **uma** das permissões:

- `dashboard-quality.view` (plugin)
- `api-delpi.quality.access` (API legada)

## 5. Smoke test HTTP

Sem token (só assets):

```bash
./scripts/homologacao/check-dashboard-quality.sh
```

Com token (API + assets):

```bash
export TOKEN="<jwt>"
export DATE_START="2025-01-01"
export DATE_END="2025-12-31"
./scripts/homologacao/check-dashboard-quality.sh
```

## 6. Checklist manual na UI

| Área | O que validar |
|------|----------------|
| Home | KPIs PPM, sparklines, resumos Kaizen/5S; filtros na URL |
| PPM | Toggle interno/externo; gráfico linha (PPM); granularidade; clique no ponto filtra datas; export CSV |
| NC | Gráfico devoluções; debounce em texto; drill-down e export |
| Kaizen | Série por período; pie status; barras setor |
| 5S | Nota média por período; drill-down |
| Erros | Período muito grande → mensagem sugerindo intervalo menor |
| Mobile | Largura ≤768px: toolbar empilhada, grids em 1 coluna |
| PPM comparativo | Toggle **Comparar** → duas linhas (interno/externo), export CSV com duas colunas |
| Metas PPM | Definir `target`/`limit` em `src/constants/ppmReferenceLines.ts` ou `VITE_DQ_PPM_TARGET` / `VITE_DQ_PPM_LIMIT` |
| Impressão | **Imprimir** em qualquer aba: cabeçalho com período/filial; sem nav/filtros; gráficos visíveis; só conteúdo do dashboard (não sidebar do portal) |

## 7. Impressão

1. Abra qualquer aba (ex.: 5S) com dados ou período válido.
2. Clique em **Imprimir** → pré-visualização do navegador.
3. Validar: resumo com período/filial no topo; sem menu lateral do portal; KPIs e gráficos legíveis; sem filtros nem paginação da tabela.

Detalhes: [DOCUMENTACAO.md](./DOCUMENTACAO.md#5-impressão).

## 8. URLs úteis

| Recurso | URL |
|---------|-----|
| Plugin | `http://localhost/apps/dashboard-quality` |
| remoteEntry | `http://localhost/apps/dashboard-quality/assets/remoteEntry.js` |
| API qualidade | `http://localhost/apps/api-delpi/quality/` |
