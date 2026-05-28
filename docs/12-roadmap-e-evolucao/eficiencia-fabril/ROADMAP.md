# Roadmap — Plugin Eficiência Fabril

> **Arquivo:** `docs/12-roadmap-e-evolucao/eficiencia-fabril/ROADMAP.md`  
> **Status:** documentação oficial (rascunho de implantação)  
> **Produto:** Minha DELPI  
> **Escopo:** plano de entrega do plugin `eficiencia-fabril` + rotas em `api-delpi`

---

## 1. Objetivo

Disponibilizar no Portal uma **tela única de dashboard gerencial** para líderes de produção acompanharem:

- **eficiência operacional** dos apontamentos (`EFICIENCIA_PERCENTUAL`);
- **tempo previsto vs real** e **horas ganhas/perdidas**;
- **resultado financeiro de MOD** (`RESULTADO_MOD`, `LUCRO_MOD`, `PREJUIZO_MOD`);
- filtros dinâmicos por **período**, **filial**, **colaborador**, **centro de trabalho** e **centro de custo**.

**Fonte de dados:** view TOTVS `dbo.vw_Apontamentos_Eficiencia` (1 linha por apontamento de `SH6010`, excluindo recurso `CT-00`).

---

## 2. Decisões de arquitetura

| Decisão | Escolha | Motivo |
|---------|---------|--------|
| Tipo de plugin | `microfrontend` + `renderMode: federated` | Padrão dashboards analíticos no monorepo |
| API dedicada (`*-api`) | **Não** | Domínio operacional TOTVS já pertence à **api-delpi** |
| Backend de dados | Rotas em `api-delpi` módulo **Produção** | Mesmo padrão de `dashboard-lmps` → `/engineering/lmps/*` |
| Persistência própria | **Não** (MVP) | Leitura direta da view; sem `postgres-plugins` no MVP |
| Referência de UI | `plugins/dashboard-lmps` | Dashboard único, filtros, Recharts, JWT |
| Referência de backend | `lmp_repositories` + `production_router` | Repository TOTVS + permissões FastAPI |

Fluxo:

```text
Portal → MFE eficiencia-fabril
  → GET /apps/api-delpi/production/eficiencia-fabril/dashboard
  → EficienciaFabrilQueryRepository
  → dbo.vw_Apontamentos_Eficiencia
```

---

## 3. Fonte de dados — resumo da view

**View:** `dbo.vw_Apontamentos_Eficiencia`

| Grupo | Colunas principais |
|-------|-------------------|
| Identificação | `FILIAL`, `OP`, `PRODUTO`, `CENTRO_TRABALHO`, `OPERACAO` |
| Operador | `COD_OPERADOR`, `LOGIN_OPERADOR`, `NOME_OPERADOR` |
| Tempo | `DATA_PRODUCAO`, `HORA_INICIO`, `HORA_FINAL`, `TEMPO_REAL_HORAS`, `TEMPO_PREVISTO_HORAS`, `TEMPO_GANHO_PERDIDO_HORAS` |
| Eficiência | `EFICIENCIA_INDICE`, `EFICIENCIA_PERCENTUAL` |
| MOD | `VALOR_MOD_HORA`, `RESULTADO_MOD`, `LUCRO_MOD`, `PREJUIZO_MOD`, `STATUS_MOD`, `STATUS_RESULTADO_MOD` |
| Qualidade | `STATUS_REGISTRO` |

**Fórmula de eficiência (UI deve documentar):**

```text
EFICIENCIA_PERCENTUAL = (TEMPO_PREVISTO_HORAS / TEMPO_REAL_HORAS) × 100
```

| Valor | Significado |
|-------|-------------|
| \> 100% | Mais rápido que o previsto |
| = 100% | No previsto |
| < 100% | Mais lento que o previsto |

**Agregação recomendada (KPI global):** eficiência ponderada por tempo real:

```text
SUM(TEMPO_PREVISTO_HORAS) / SUM(TEMPO_REAL_HORAS) × 100
```

**Filtro default sugerido no dashboard:** `STATUS_REGISTRO = 'OK'` (registros com problema em contador separado ou toggle).

---

## 4. Permissões

| Camada | Código | Observação |
|--------|--------|------------|
| Manifesto (Core API) | `eficiencia-fabril.view` | Entrada no menu do Portal |
| api-delpi | `eficiencia-fabril.view` | Decorator nas rotas |
| Legado | `api-delpi.access` | Compatibilidade perfis amplos |
| Opcional | `dashboard-production.view` | Se líderes já usam dashboard Produção |

Registro: `POST /core-api/admin/apps/register` com permissão `apps.manage` ou superadmin.

---

## 5. Fases de entrega

### Fase 0 — Especificação e validação TOTVS (pré-código) ✅

**Objetivo:** confirmar view e volume antes de implementar repository.

| Entrega | Detalhe | Status |
|---------|---------|--------|
| Validar view no ambiente dev/homolog | `SELECT TOP 100` via `delpi-api-delpi` (2026-05-27) | ✅ |
| Confirmar literais de status | 7 + 3 + 7 valores distintos — ver [ESPECIFICACAO-VIEW.md](./ESPECIFICACAO-VIEW.md) | ✅ |
| Confirmar filiais | `01`, `02` (+ 2 linhas órfãs sem filial) | ✅ |
| Estimar volume | ~8,4k linhas/dia (30d); ~373k histórico | ✅ |
| Documentar SQL de referência | `api-delpi/.../eficiencia_fabril/EFICIENCIA_FABRIL_VIEW.sql` | ✅ |
| Script validação | `api-delpi/scripts/validate_eficiencia_fabril_view.py` | ✅ |
| Relatório | [FASE0-VALIDACAO.md](./FASE0-VALIDACAO.md) | ✅ |

**Critério de pronto:** query de amostra retorna dados coerentes; statuses documentados; mesma conexão `TOTVS_DB_*` dos LMPs confirmada. **`ready_for_phase_1: true`** (10/10 checks).

---

### Fase 1 — Backend api-delpi (MVP leitura) ✅

**Objetivo:** endpoint agregado pronto para consumo pelo MFE.

| Entrega | Detalhe | Status |
|---------|---------|--------|
| Port + settings | `EficienciaFabrilQueryRepositoryPort`, `EficienciaFabrilQuerySettings` | ✅ |
| Repository TOTVS | `EficienciaFabrilQueryRepository` extends `BaseRepository` | ✅ |
| DTOs | request (filtros), summary, charts, item paginado | ✅ |
| Use case | `GetEficienciaFabrilDashboardUseCase` | ✅ |
| Rota | `GET /production/eficiencia-fabril/dashboard` | ✅ |
| Composer | `build_get_eficiencia_fabril_dashboard_use_case` | ✅ |
| Permissões | `eficiencia-fabril.view`, `api-delpi.access`, `dashboard-production.view` | ✅ |
| Testes unitários | `tests/test_get_eficiencia_fabril_dashboard_use_case.py` | ✅ |

**Query params previstos:**

```text
date_start, date_end     (obrigatórios)
branch                   (opcional)
employee                 (COD_OPERADOR ou LOGIN_OPERADOR)
work_center              (CENTRO_TRABALHO)
cost_center              (CENTRO_CUSTO_RECURSO)
status_ok_only           (default true)
page, page_size          (tabela de items)
```

**Resposta JSON (contrato alvo):**

```json
{
  "summary": {
    "weighted_efficiency_pct": 0,
    "total_mod_result": 0,
    "total_mod_profit": 0,
    "total_mod_loss": 0,
    "total_hours_gained_lost": 0,
    "appointment_count": 0,
    "invalid_record_count": 0
  },
  "charts": {
    "efficiency_by_day": [],
    "mod_result_by_day": [],
    "efficiency_by_operator": [],
    "hours_by_work_center": []
  },
  "items": [],
  "pagination": { "page": 1, "page_size": 50, "total": 0 }
}
```

**Critério de pronto:** `curl` autenticado contra gateway retorna 200 com summary + charts + items paginados; testes unitários passando.

---

### Fase 2 — Plugin MFE (esqueleto deployável) ✅

**Objetivo:** plugin visível no Portal com página mínima consumindo a API.

| Entrega | Detalhe | Status |
|---------|---------|--------|
| Pasta `plugins/eficiencia-fabril/` | Scaffold a partir de `dashboard-production` | ✅ |
| Vite + Federation | `base: /apps/eficiencia-fabril/`, `remoteEntry.js` | ✅ |
| `bootstrap.tsx` | `mount` / `unmount` / `updateRoute` | ✅ |
| `httpClient.ts` | JWT via `getAccessToken` | ✅ |
| `eficienciaFabrilApi.ts` | cliente do endpoint dashboard | ✅ |
| Manifesto | `eficiencia-fabril.manifest.json` v `0.1.0` | ✅ |
| Dockerfile | build nginx (padrão dashboards) | ✅ |
| Compose dev | serviço `eficiencia-fabril`, container `delpi-eficiencia-fabril` | ✅ |
| Script registro | `plugins/eficiencia-fabril/scripts/register-manifest.sh` | ✅ |
| CI / homologação | `scripts/ci/build-eficiencia-fabril.sh`, `check-eficiencia-fabril.sh` | ✅ |

**Critério de pronto:**

- `curl -sI http://localhost/apps/eficiencia-fabril/assets/remoteEntry.js` → 200
- `POST /core-api/admin/apps/register` → 201
- Superadmin vê item no menu; tela carrega JSON da API (mesmo que UI básica)

---

### Fase 3 — Dashboard gerencial (UI completa MVP)

**Objetivo:** experiência analítica para líderes na tela única.

| Entrega | Detalhe | Status |
|---------|---------|--------|
| FilterBar | datas, filial, operador, centro de trabalho, CC, toggle “somente OK” | Pendente |
| KPI cards | eficiência ponderada, resultado MOD, lucro, prejuízo, horas ganhas/perdidas, qtd apontamentos | Pendente |
| Gráfico linha | eficiência por dia | Pendente |
| Gráfico barras | top operadores (eficiência ou MOD) | Pendente |
| Gráfico empilhado | lucro vs prejuízo MOD por dia | Pendente |
| Tabela detalhada | colunas principais da view, paginação server-side | Pendente |
| Estados UX | loading, erro, empty, legenda eficiência \>100% | Pendente |
| CSS | prefixo `.dashboard-eficiencia-fabril` | Pendente |

**Critério de pronto:** líder filtra por mês + operador; KPIs e gráficos atualizam; tabela lista apontamentos; build `npm run build` sem erro.

---

### Fase 4 — RBAC, homologação e CI

**Objetivo:** entrega segura para usuários não superadmin e pipeline mínimo.

| Entrega | Detalhe | Status |
|---------|---------|--------|
| Role “Líder Produção” (ou equivalente) | `eficiencia-fabril.view` associada | Pendente |
| README do plugin | `plugins/eficiencia-fabril/README.md` | Pendente |
| Script CI build | `scripts/ci/build-eficiencia-fabril.sh` | Pendente |
| Smoke homologação | `scripts/homologacao/check-eficiencia-fabril.sh` | Pendente |
| Documentação OpenAPI | entrada em `api-delpi/docs/api/` (se aplicável) | Pendente |

**Critério de pronto:** usuário com role (não superadmin) acessa dashboard; CI build passa no PR.

---

### Fase 5 — Produção

**Objetivo:** deploy na VM de produção sem regressão.

| Entrega | Detalhe | Status |
|---------|---------|--------|
| Build imagens | `eficiencia-fabril` + deploy `api-delpi` com novas rotas | Pendente |
| Registro manifesto prod | `issuer`/`audience` do backend no manifesto com domínio real | Pendente |
| RBAC produção | perfis operacionais | Pendente |
| Validação VPN/TOTVS | endpoint responde no servidor | Pendente |
| Monitoramento | logs api-delpi sem timeout; alerta volume alto | Pendente |

**Critério de pronto:** líderes em produção acessam via Portal; números conferidos com amostra SQL manual na view.

---

### Fase 6 — Evoluções (pós-MVP)

| Entrega | Prioridade | Detalhe |
|---------|------------|---------|
| Export CSV/Excel | Alta | botão na tabela |
| Cache TTL dashboard | Média | padrão `lmp_dashboard_cache` |
| Filtro por OP/produto/operação | Média | query params extras |
| Drill-down operador | Média | clique no gráfico filtra tabela |
| Painel “registros com problema” | Média | `STATUS_REGISTRO <> OK` |
| Metas de eficiência (linha 100%) | Baixa | referência visual |
| Segunda rota / tela admin | Baixa | somente se necessário |

---

## 6. Dependências e riscos

| Dependência | Impacto |
|-------------|---------|
| VPN / rede TOTVS | api-delpi falha sem SQL Server |
| View `vw_Apontamentos_Eficiencia` em homolog/prod | repository vazio ou erro |
| Keycloak + audience `delpi-central` | login Portal |
| `TOTVS_DB_*` no `.env` | mesma config dos LMPs |
| Volume de linhas | necessidade de paginação e agregação no servidor |

| Risco | Mitigação |
|-------|-----------|
| Outliers de eficiência (ex.: 500%) | agregação ponderada; cap visual opcional |
| `TEMPO_REAL_HORAS = 0` | respeitar `STATUS_REGISTRO`; excluir na agregação |
| `STATUS_MOD` incompleto | aviso no summary; excluir MOD do total ou flag |
| Performance | índices na view (DBA); cache fase 6 |
| Confusão UX eficiência \> 100% | legenda e tooltips na Fase 3 |

---

## 7. Checklist de implantação (dev)

- [ ] Fase 0: view validada no TOTVS
- [ ] Fase 1: endpoint dashboard na api-delpi
- [ ] Fase 2: plugin no compose + manifesto registrado
- [ ] Fase 3: UI dashboard completa
- [ ] `npm run build` OK
- [ ] RBAC para usuário piloto
- [ ] PR com `plugins/eficiencia-fabril/` + `api-delpi/` + compose

---

## 8. O que reaproveitar do monorepo

| Peça existente | Uso |
|----------------|-----|
| `plugins/dashboard-lmps/` | Estrutura MFE, FilterBar, hooks, Recharts |
| `plugins/dashboard-production/` | Manifesto domínio Produção |
| `api-delpi/.../lmp_query_repository.py` | Padrão repository + QueryBuilder TOTVS |
| `api-delpi/.../production_router.py` | Onde registrar rotas |
| `plugins/dashboard-lmps/scripts/register-manifest.sh` | Template script registro |
| `docs/10-guias-operacionais/registrar-plugin.md` | Runbook operacional |

---

## 9. Documentos relacionados

- [README.md](./README.md) — índice do módulo
- [../../08-plugins/README.md](../../08-plugins/README.md) — inventário plugins
- [../../05-plugin-system/manifesto-plugin.md](../../05-plugin-system/manifesto-plugin.md) — contrato JSON
- [../../10-guias-operacionais/registrar-plugin.md](../../10-guias-operacionais/registrar-plugin.md) — registro
- [../transformometro-app/ROADMAP.md](../transformometro-app/ROADMAP.md) — exemplo de roadmap por fases

---

## 10. Histórico

| Data | Autor | Nota |
|------|-------|------|
| 2026-05-27 | Planejamento inicial | Roadmap criado a partir da view `vw_Apontamentos_Eficiencia` e alinhamento com padrão dashboard-lmps |
