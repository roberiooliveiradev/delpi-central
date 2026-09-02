# Eficiência Fabril — plugin Minha DELPI

Microfrontend (Module Federation) para dashboard de eficiência operacional e resultado MOD dos apontamentos de produção (view TOTVS `dbo.vw_Apontamentos_Eficiencia`).

Documentação completa: [docs/12-roadmap-e-evolucao/eficiencia-fabril/](../../docs/12-roadmap-e-evolucao/eficiencia-fabril/) — em especial [ESPECIFICACAO-PLUGIN.md](../../docs/12-roadmap-e-evolucao/eficiencia-fabril/ESPECIFICACAO-PLUGIN.md).  
Faixa válida e changelog jun/2026: [regras-faixa-eficiencia-producao.md](../../api-delpi/docs/api/regras-faixa-eficiencia-producao.md), [producao-eficiencia-changelog-jun2026.md](../../api-delpi/docs/api/producao-eficiencia-changelog-jun2026.md).

---

## Funcionalidades (resumo)

- Duas entradas no menu: **SC** (filial 01) e **ES** (filial 02)
- Abas internas: **Eficiência** (apontamentos produtivos) e **Horas improdutivas** (paradas PCP)
- Deep link da aba: `?tab=unproductive-hours`
- KPIs (Eficiência): eficiência (média simples das médias por CT), apontamentos na tabela, a avaliar (Verificar), resultado MOD, horas ganhas/perdidas
- KPIs (Horas improdutivas): total de horas, custo, nº de apontamentos, principal recurso/operador
- Gráficos de eficiência + rankings de parada (motivo, operador, recurso)
- Tabelas paginadas com ordenação + exportação Excel/PDF
- Clique na linha (aba Eficiência) → detalhe do apontamento (roteiro, tempos, estrutura)
- Filtros automáticos; refetch / **Atualizar** / auto-refresh a cada 5 min com a aba visível
- Regras: CTs excluídos (`CT-00`, `CT-70`, `CT-16A`, `CT-99`); eficiência fora da faixa **0–199%** fora dos indicadores (status **Verificar** na tabela)

---

## API

```http
GET /apps/api-delpi/production/eficiencia-fabril/appointments
GET /apps/api-delpi/production/eficiencia-fabril/dashboard
GET /apps/api-delpi/production/unproductive-hours/summary
GET /apps/api-delpi/production/unproductive-hours/items
GET /apps/api-delpi/production/unproductive-hours/ranking
```

A aba **Horas improdutivas** consome a família `/production/unproductive-hours/*` (view `VW_BI_RT_HORAS_IMPRODUTIVAS`, **todos** os motivos de parada). Não confundir com `/retrabalhos/*` (só motivo `RT`). Doc: [production-unproductive-hours.md](../../api-delpi/docs/api/production-unproductive-hours.md).

Parâmetros principais (eficiência): `start_date`/`end_date`, `branch` (fixo pela rota SC/ES). Filtros OP/operador/CT/turno são locais no MFE.

Parâmetros (horas improdutivas): `start_date`/`end_date`, `branch`, `stop_reason`, `operator_code`, `resource`, `cost_center`, `page`, `sort`, `rank_by`.

Rotas no Portal:

- `/apps/eficiencia-fabril/sc` — Filial SC (TOTVS `01`)
- `/apps/eficiencia-fabril/es` — Filial ES (TOTVS `02`)
- `/apps/eficiencia-fabril/{sc|es}?tab=unproductive-hours` — Aba de paradas
- `/apps/eficiencia-fabril/sc/appointment/{appointment_id}` — Detalhe (consome `GET /production/oee/appointments/{id}`)

---

## Desenvolvimento local

```bash
cd plugins/eficiencia-fabril
npm install
npm run build
```

A partir da **raiz do monorepo** (rebuild seguro):

```bash
./infra/scripts/up-dev-sequential.sh --fase mfe --build eficiencia-fabril
```

Ou local:

```bash
cd plugins/eficiencia-fabril
npm install
npm run build
```

Após mudanças só no **backend**:

```bash
docker compose -f docker-compose.dev.yml restart api-delpi
```

---

## Registro no Portal

```bash
export TOKEN="<jwt_superadmin>"
./scripts/register-manifest.sh
```

---

## Smoke

```bash
curl -sI http://localhost/apps/eficiencia-fabril/assets/remoteEntry.js

# Com JWT (opcional):
TOKEN="<jwt>" ../../scripts/homologacao/check-eficiencia-fabril.sh
```

---

## Estrutura do código

```text
src/
  api/              # HTTP + fetch bulk appointments
  components/       # FilterBar, ShiftMultiSelect, KPIs, gráficos, tabela, árvore de estrutura
  hooks/            # filtros (auto-aplicação + debounce) + dashboard (cache + agregação local) + useAutoRefresh (5 min)
  pages/            # Dashboard + detalhe do apontamento
  constants/        # regras (faixa 0–199%, turnos, cores de gráfico)
  utils/            # formatação, ordenação da tabela e export Excel
```
