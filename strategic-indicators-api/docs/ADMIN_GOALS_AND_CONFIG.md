# Metas analíticas e backup administrativo

**Última atualização:** 2026-05-27

Documenta o cadastro de metas no admin, modos **Padrão** / **Curva**, exportação/importação de configuração e operações por ciclo anual.

Relacionado: [INDICATOR_GOALS_SCOPE.md](./INDICATOR_GOALS_SCOPE.md) (escopo consolidado/filial), [API.md](./API.md) (rotas HTTP), [MFE.md](./MFE.md) (telas).

---

## Modos da meta (`goal_mode`)

| Valor no banco | Rótulo na UI | Uso |
|----------------|--------------|-----|
| `standard` | **Padrão** | Um único `goal_value` por meta ativa |
| `monthly_curve` | **Curva** | Vários pontos em `indicator_goal_monthly_targets`; `goal_value` = **0** (sem consolidado) |

Helpers:

| Camada | Arquivo |
|--------|---------|
| API | `si_app/application/services/strategic_indicators/goal_value_policy.py` — `resolve_persisted_goal_value()` |
| API | `si_app/application/services/strategic_indicators/goal_curve_validation.py` — valida quantidade de pontos |
| MFE | `plugins/strategic-indicators/src/ui/utils/goalValuePolicy.ts` |
| MFE | `plugins/strategic-indicators/src/ui/utils/curveTargets.ts` — grade e rótulos dos pontos |
| MFE | `plugins/strategic-indicators/src/ui/presentation/labels.ts` — `getGoalModeLabel()` |

---

## Curva e periodicidade (`goal_periodicity`)

A **periodicidade** define quantos pontos a curva possui e como o calculador mapeia a competência para um ponto.

| `goal_periodicity` | Pontos na grade (admin) | Rótulos na UI | Mapeamento na competência mensal |
|--------------------|-------------------------|---------------|----------------------------------|
| `monthly` | 12 | Jan … Dez | Mês da competência (1–12) |
| `quarterly` | 4 | 1º trim. … 4º trim. | Trimestre do mês |
| `weekly` | 52 | Sem 1 … Sem 52 | Semana ISO do dia 15 do mês |
| `annual` | 1 | Ano | Ponto único |

Regras:

- Na API, `monthly_targets[].month_number` é o **índice do ponto** (1 … N), não necessariamente mês civil quando N ≠ 12.
- `goal_value` em metas `monthly_curve` **não** entra no cálculo; só os `target_value` dos pontos.
- Meta comparável do período = soma dos `target_value` dos pontos que caem no intervalo consultado (ex.: competência mensal → um ponto).
- Sem pontos válidos na curva → meta comparável **0** (nota sem meta).

Migration **V025** zera `goal_value` legado em metas `monthly_curve` já existentes.

---

## Cadastro no admin (MFE)

Rota: `/apps/strategic-indicators/settings` → abas **Metas**, **Visão geral**.

### Formulário de meta (`IndicatorGoalForm`)

- **Indicador** — select do catálogo (departamentos ativos).
- **Modo** — Padrão ou Curva.
- **Periodicidade** — define pontos quando o modo é Curva.
- **Escopo** — consolidado, filial `01` ou `02` ([INDICATOR_GOALS_SCOPE.md](./INDICATOR_GOALS_SCOPE.md)).
- **Valor da meta** — visível só em modo **Padrão**.
- **Curva** — grade de N campos; sem “valor consolidado”.

Listagem de metas: em modo Curva exibe apenas o `goal_label` (ex.: `Curva %`), não `goal_label · 174,24`.

### Ciclos anuais (`AdminGoalsWorkspace`)

| Ação | Comportamento |
|------|----------------|
| **Novo ano** | Ano de destino sugerido (ex.: ano anterior ao maior ciclo existente); metas iniciais em lote com select de indicador |
| **Duplicar ano** | Origem = ano imediatamente posterior ao destino (ex.: 2026 → 2025); destino editável em select |
| **Duplicar** (por linha) | Abre o formulário com cópia da meta (rótulo com sufixo `(cópia)`); permite mudar indicador, ano ou escopo antes de salvar |
| **Preencher faltantes** | Completa indicadores sem meta ativa no ano, copiando estrutura de outro ano |

Ao salvar uma cópia com o mesmo indicador, ano e escopo, a meta ativa anterior é desativada e a nova versão passa a ser a ativa.

API: `POST /admin/indicator-goals/duplicate-year` com `source_year`, `target_year`, `overwrite_existing`.

---

## Exportar / importar configuração

**Permissão:** `strategic-indicators.settings.manage`

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/admin/config/export` | JSON do catálogo administrativo |
| POST | `/admin/config/import` | Restaura/atualiza a partir do JSON |

### Conteúdo do bundle (`schema_version: 1`)

| Chave | Conteúdo |
|-------|----------|
| `departments` | Departamentos |
| `department_indicators` | Indicadores estruturais |
| `indicator_goals` | Metas **ativas** + `monthly_targets` |
| `module_settings` | `parameters.global`, `governance.notes` |

### Importação

- Departamentos e indicadores: **upsert** (merge por ID).
- Metas: cria somente se **não** existir meta ativa para `(indicator_id, goal_year, goal_scope_branch)`; não sobrescreve metas existentes (`goals_skipped`).
- Body: `include_goals` (boolean, default `true`) para ignorar metas na importação.
- Invalida cache de leitura após import.

UI: painel na aba **Visão geral** do settings (`AdminConfigImportExportPanel`).

Implementação: `postgres_admin_config_bundle_repository.py`, use cases `export_admin_config` / `import_admin_config`.

---

## Exemplo de fluxo: criar ciclo 2025 a partir de 2026

1. Garantir migration **V025** aplicada no ambiente.
2. No admin **Metas**, selecionar ou criar visão do ano **2025**.
3. **Duplicar ano** — origem **2026**, destino **2025** (ou usar **Novo ano** com destino 2025 e depois duplicar).
4. Conferir metas na lista; ajustar curvas ponto a ponto se necessário.
5. Opcional: **Exportar JSON** como backup antes de mudanças em produção.

---

## Testes automatizados

| Arquivo | Cobertura |
|---------|-----------|
| `tests/test_goal_value_policy.py` | `goal_value` zerado em curvas |
| `tests/test_goal_curve_validation.py` | Validação 4/12/52/1 pontos; calculador trimestral |
| `tests/test_commercial_production_scoring.py` | Curva sem fallback em `goal_value` |
