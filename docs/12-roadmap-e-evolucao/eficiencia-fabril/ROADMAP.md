# Roadmap — Plugin Eficiência Fabril

> **Arquivo:** `docs/12-roadmap-e-evolucao/eficiencia-fabril/ROADMAP.md`  
> **Status:** MVP implementado em dev (documentação alinhada em 2026-05-28)  
> **Produto:** Minha DELPI  
> **Escopo:** plano de entrega do plugin `eficiencia-fabril` + rotas em `api-delpi`

---

## 1. Objetivo

Disponibilizar no Portal uma **tela única de dashboard gerencial** para líderes de produção acompanharem:

- **eficiência operacional** dos apontamentos (`EFICIENCIA_PERCENTUAL`);
- **tempo previsto vs real** e **horas ganhas/perdidas**;
- **resultado financeiro de MOD** (`RESULTADO_MOD`, `LUCRO_MOD`, `PREJUIZO_MOD`);
- filtros por **período**, **filial**, **operador (nome)**, **OP** (parcial) e **centro de trabalho**.

**Fonte de dados:** view TOTVS `dbo.vw_Apontamentos_Eficiencia`. Na aplicação, centros **CT-00, CT-70, CT-16A e CT-99** são sempre excluídos.

**Especificação do que está implementado:** [ESPECIFICACAO-PLUGIN.md](./ESPECIFICACAO-PLUGIN.md).

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
  → GET /apps/api-delpi/production/eficiencia-fabril/appointments  (carga do período)
  → agregação e filtros no navegador
  → EficienciaFabrilQueryRepository → dbo.vw_Apontamentos_Eficiencia

Alternativa (smoke/legado): GET .../eficiencia-fabril/dashboard (SQL agregado + paginação)
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

**Agregação implementada (KPI e gráficos):** média simples de `EFICIENCIA_PERCENTUAL` nos registros OK com eficiência ≤ 250%.

**Tabela:** registros OK; eficiência &gt; 250% com status **Verificar** (fora dos indicadores).

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
| Rota bulk | `GET /production/eficiencia-fabril/appointments` | ✅ |
| Composer | dashboard + appointments use cases | ✅ |
| Permissões | `eficiencia-fabril.view`, `api-delpi.access`, `dashboard-production.view` | ✅ |
| Testes unitários | `tests/test_get_eficiencia_fabril_dashboard_use_case.py` | ✅ |
| CTs excluídos | `CT-00`, `CT-70`, `CT-16A`, `CT-99` | ✅ |
| Teto indicadores | eficiência &gt; 250% (`max_efficiency_indicator_pct`) | ✅ |

**Query params:**

```text
date_start, date_end     (obrigatórios)
branch                   (opcional)
employee                 (busca parcial em NOME_OPERADOR)
op                       (busca parcial em OP)
work_center              (CENTRO_TRABALHO)
status_ok_only           (dashboard: default true; appointments MFE: false na carga)
page, page_size          (somente /dashboard)
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

### Fase 3 — Dashboard gerencial (UI completa MVP) ✅

**Objetivo:** experiência analítica para líderes na tela única.

| Entrega | Detalhe | Status |
|---------|---------|--------|
| FilterBar | datas, filial, operador (nome), OP, centro de trabalho; aplicar sem refetch | ✅ |
| Carga bulk + cache | `GET /appointments`; filtros locais; **Atualizar** recarrega período | ✅ |
| KPIs | eficiência (&lt;95% vermelho), apontamentos + Verificar, MOD, horas | ✅ |
| Gráficos (3+2) | dia, MOD, operadores, eficiência por CT (cores), horas por CT | ✅ |
| Modal expandido | tamanho padrão 1320×700px; labels CT no expandido | ✅ |
| Tabela | início/fim, qtd apontada; paginação local; linha Verificar | ✅ |
| Export Excel | dados filtrados em memória | ✅ |
| UX | aviso 250%; sem grade nos gráficos; layout 3+2 | ✅ |

Detalhe funcional: [ESPECIFICACAO-PLUGIN.md](./ESPECIFICACAO-PLUGIN.md).

**Critério de pronto:** líder filtra por mês + operador sem nova API; KPIs/gráficos/tabela coerentes; export Excel; `npm run build` OK.

---

### Fase 4 — RBAC, homologação e CI

**Objetivo:** entrega segura para usuários não superadmin e pipeline mínimo.

| Entrega | Detalhe | Status |
|---------|---------|--------|
| Role “Líder Produção” (ou equivalente) | `eficiencia-fabril.view` associada | Pendente |
| README do plugin | `plugins/eficiencia-fabril/README.md` | ✅ |
| Docs módulo | `docs/12-roadmap-e-evolucao/eficiencia-fabril/*` | ✅ |
| Script CI build | `scripts/ci/build-eficiencia-fabril.sh` | ✅ |
| Smoke homologação | `scripts/homologacao/check-eficiencia-fabril.sh` | ✅ |
| Documentação OpenAPI | entrada em `api-delpi/docs/api/` | Pendente |

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
| Export CSV/Excel | — | ✅ Excel na tabela (dados em memória) |
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
| Outliers de eficiência (ex.: &gt; 250%) | excluídos dos indicadores; tabela com status &quot;Verificar&quot; |
| `TEMPO_REAL_HORAS = 0` | respeitar `STATUS_REGISTRO`; excluir na agregação |
| `STATUS_MOD` incompleto | aviso no summary; excluir MOD do total ou flag |
| Performance | índices na view (DBA); cache fase 6 |
| Confusão UX eficiência \> 100% | aviso 250% + status Verificar na tabela |

---

## 7. Checklist de implantação (dev)

- [x] Fase 0: view validada no TOTVS
- [x] Fase 1: endpoints dashboard + appointments na api-delpi
- [x] Fase 2: plugin no compose + manifesto registrado
- [x] Fase 3: UI dashboard completa (ver ESPECIFICACAO-PLUGIN.md)
- [x] Documentação revisada (2026-05-28)
- [ ] `npm run build` OK no ambiente do time
- [ ] RBAC para usuário piloto (não superadmin)
- [ ] PR / merge para homologação
- [ ] Fase 5: produção

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
- [ESPECIFICACAO-PLUGIN.md](./ESPECIFICACAO-PLUGIN.md) — funcionalidades implementadas
- [../../08-plugins/README.md](../../08-plugins/README.md) — inventário plugins
- [../../05-plugin-system/manifesto-plugin.md](../../05-plugin-system/manifesto-plugin.md) — contrato JSON
- [../../10-guias-operacionais/registrar-plugin.md](../../10-guias-operacionais/registrar-plugin.md) — registro
- [../transformometro-app/ROADMAP.md](../transformometro-app/ROADMAP.md) — exemplo de roadmap por fases

---

## 10. Histórico

| Data | Autor | Nota |
|------|-------|------|
| 2026-05-27 | Planejamento inicial | Roadmap criado a partir da view `vw_Apontamentos_Eficiencia` e alinhamento com padrão dashboard-lmps |
| 2026-05-28 | Revisão MVP | ESPECIFICACAO-PLUGIN.md; fases 1–3 alinhadas ao código (filtros locais, CT-99, 250%, export Excel) |
