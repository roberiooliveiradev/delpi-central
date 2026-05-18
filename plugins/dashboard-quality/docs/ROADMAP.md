# Roadmap — Dashboard Qualidade

Plugin: `dashboard-quality`  
Backend: **api-delpi** (`/apps/api-delpi/quality/*`)  
Referência de UX/arquitetura: `plugins/dashboard-lmps`

---

## Objetivo

Oferecer um painel unificado para a área de Qualidade consumir indicadores já disponíveis na api-delpi (TOTVS), sem duplicar regras de negócio no frontend:

- **PPM** interno e externo (KPI + séries/detalhes)
- **Kaizens** (resumo)
- **Auditoria 5S** (resumo)
- **Não conformidades** listadas do Protheus (consulta analítica)

> **Não é escopo deste plugin** o sistema de registro/gestão de NC em PostgreSQL documentado em `api-delpi/docs/api/07-qualidade-nc.md` (rotas ainda não montadas em `main.py`). Integração futura em fase opcional.

---

## Princípios

1. **Thin client:** gráficos, tabelas e filtros no MFE; agregações permanecem na api-delpi.
2. **Mesmo contrato HTTP** que outros consumidores: envelope `{ success, message, data }`.
3. **Permissões:** usuário do portal com permissão do plugin; API aceita `api-delpi.quality.access` **ou** `dashboard-quality.view` (ajuste na api-delpi, espelhando engenharia/LMPs).
4. **Uma base de código** por domínio (abas ou sub-rotas internas), não microfrontends separados por indicador.

---

## Fase 0 — Fundação (infra + scaffold) ✅

**Entregáveis**

- [x] `package.json`, Vite + Module Federation (`name: dashboard-quality`, `base: /apps/dashboard-quality/`)
- [x] `Dockerfile` (build Node → nginx), serviço `dashboard-quality` em `infra/docker-compose.yml` e `docker-compose.dev.yml`
- [x] Gateway: rota genérica `/apps/dashboard-quality/assets/*` → serviço `dashboard-quality` (dev) / `delpi-dashboard-quality` (prod)
- [ ] `dashboard-quality.manifest.json` registrado na Core API (`POST /core-api/admin/apps/register`) — **manual**
- [x] Permissão `dashboard-quality.view` no manifesto
- [x] **api-delpi:** `require_any_permission(["api-delpi.quality.access", "dashboard-quality.view"])` em `quality_router.py`
- [x] Shell mínimo: `App.tsx` + `bootstrap.tsx` + página placeholder
- [x] `httpClient.ts` + `configureHttpClient` + esboço `qualityApi.ts`

**Critério de pronto:** plugin aparece no menu do portal; abre sem erro 404 nos assets; chamada de teste `GET /quality/ppm/internal/summary` retorna 200 para usuário com permissão.

**Registro na Core API (operacional):**

```bash
# A partir do manifesto em plugins/dashboard-quality/
curl -X POST "$CORE_API_URL/core-api/admin/apps/register" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d @dashboard-quality.manifest.json
```

Depois, atribuir `dashboard-quality.view` ao perfil/grupo desejado no Keycloak ou admin de permissões.

---

## Fase 1 — Camada de API e tipos

**Entregáveis**

- [ ] `src/api/qualityApi.ts` — funções para cada endpoint (ver [API_MAPPING.md](./API_MAPPING.md))
- [ ] `src/types/` — DTOs alinhados aos `to_dict()` dos use cases (PPM, kaizen, 5S, NC)
- [ ] `src/api/query.ts` — helper `buildQuery` (filial, datas, paginação)
- [ ] Tratamento uniforme de erro (`message` do envelope)
- [ ] Testes manuais documentados no README (curl ou coleção)

**Critério de pronto:** hooks conseguem buscar os 7 endpoints sem adaptação ad hoc por tela.

---

## Fase 2 — Visão executiva (home do dashboard)

**UX sugerida** (similar ao dashboard LMPs):

- Barra de filtros global: filial, `date_start`, `date_end`
- **Cards KPI:** PPM interno, PPM externo (valores do `/summary`)
- **Cards/resumos:** Kaizen e 5S (totais, status, tendência se a API expuser)
- Atalhos para abas detalhadas

**Entregáveis**

- [ ] `FilterBar` compartilhada
- [ ] `KpiCard` / `ChartCard` (reutilizar padrão visual de `dashboard-lmps` ou design system Delpi)
- [ ] `useQualityDashboard` — paraleliza fetches de summary com `AbortController`
- [ ] Loading / empty / error states

**Critério de pronto:** alterar período reflete em todos os KPIs; cancelamento de request ao trocar filtro rapidamente.

---

## Fase 3 — PPM (interno e externo)

**Entregáveis**

- [ ] Aba ou rota `/ppm` com toggle interno | externo
- [ ] Gráfico de evolução a partir de `/ppm/{type}/summary` (se série temporal no payload; senão derivar de lista paginada — validar contrato com backend)
- [ ] Tabela paginada: `/ppm/internal` e `/ppm/external` (`page`, `page_size`)
- [ ] Exportação CSV opcional (client-side) — nice-to-have

**Critério de pronto:** paginação estável; mesmos filtros da home aplicados.

---

## Fase 4 — Não conformidades (TOTVS)

**Entregáveis**

- [ ] Aba NC: tabela com colunas principais (tipo, filial, datas, status, item, descrição)
- [ ] Filtros: `type` (`internal` | `external` | `all`), `status`, `item_code`, `description`
- [ ] Paginação server-side
- [ ] Link ou tooltip “origem TOTVS” (deixar claro que não é o módulo de gestão PostgreSQL)

**Critério de pronto:** listagem de NC Protheus utilizável pela equipe de qualidade no dia a dia analítico.

---

## Fase 5 — Kaizen e Auditoria 5S

**Entregáveis**

- [ ] Aba Kaizen: resumo + filtros (`title`, `status`, `branch`, datas)
- [ ] Aba 5S: resumo + filtros (`start_date`, `end_date`, `branch`)
- [ ] Visualizações adequadas ao payload (barras, pizza, tabela — definir após inspecionar `to_dict()`)

**Critério de pronto:** paridade funcional com o que a API já retorna; sem campos inventados no front.

---

## Fase 6 — Polimento e operação

**Entregáveis**

- [ ] Acessibilidade básica (labels, contraste, foco)
- [ ] Responsivo (tablet+)
- [ ] Documentação de deploy em `docs/08-plugins/README.md` (linha na tabela de inventário)
- [ ] Cache leve no cliente (SWR / stale-while-revalidate) se latência TOTVS for alta
- [ ] Logs de erro amigáveis + telemetria opcional

**Critério de pronto:** aceite da área de Qualidade + revisão de segurança (somente leitura).

---

## Fase opcional — NC PostgreSQL (gestão)

Somente quando rotas `internal-nc` / `external-nc` forem montadas em `api-delpi/main.py`:

- [ ] Nova permissão `quality-nc.view` no manifesto ou plugin irmão
- [ ] Telas de workflow separadas do dashboard analítico (evitar misturar com TOTVS)

**Fora do roadmap imediato** a pedido do produto.

---

## Dependências e riscos

| Item | Impacto | Mitigação |
|---|---|---|
| Latência TOTVS | Dashboard lento | Paralelismo + loading por seção; cache HTTP se API expuser |
| Contrato `data` instável | Quebra de gráficos | Tipos gerados ou validação Zod na Fase 1 |
| Permissão só `api-delpi.quality.access` | Usuários do portal sem acesso | Fase 0: `require_any_permission` + seed Core API |
| Confusão NC TOTVS vs PostgreSQL | Suporte | Copy na UI + docs |

---

## Ordem sugerida de PRs

1. Fase 0 (scaffold + infra + permissões API)
2. Fase 1 (API client + types)
3. Fase 2 (home KPI)
4. Fase 3 + 4 (PPM + NC) — podem ser PRs separados
5. Fase 5 (Kaizen + 5S)
6. Fase 6 (polish)

---

## Checklist de registro no monorepo

- [ ] Entrada em `docs/08-plugins/README.md` (tabela inventário + backend)
- [ ] CI: build do plugin no pipeline (quando existir job de plugins)
- [ ] Ícone e label no manifesto para menu do portal
