# OVERVIEW.R2 — Diagnóstico e recuperação de metas LMP

> **Status:** implementado e deployado.  
> **Missão:** recuperar metas oficiais no card `% LMP dentro do prazo`.  
> **Baseline:** `origin/main` em `da291bba20` (rebase sobre `321484aa44`).  
> **Autoridades:** docs 18/19/20, `KPI-FICHAS.md`, seed SI V009.

## 1. Sintoma

Captura produtiva (01–28/10/2026): `% LMP dentro do prazo` exibia valor
`100,00` sem Meta parcial, Meta mês e Nota IDD, enquanto `Ganhos brutos
TRANSFORMA+` exibia metas corretamente.

## 2. Causa raiz (boundary: api-delpi → SI)

Cadeia rastreada end-to-end:

```text
BFF overview_api_delpi.py — _lmp_date() serializa YYYYMMDD
  → GET /engineering/lmps/dashboard/summary?start_date=20261001&end_date=20261028
  → resolve_period_dates() devolve as strings cruas (sem reformatar)
  → enrich_dashboard_metric(start_date="20261001")
  → normalize_si_period_date() só convertia ISO YYYY-MM-DD → DD-MM-YYYY;
    "20261001" passava inalterado
  → SI resolve_period() → parse_period_date("20261001") = None
  → _require_valid_period_date → ValueError → HTTP 400
  → StrategicIndicatorsApiClient → StrategicIndicatorsApiError
  → _load_goals_map captura e retorna {} (degradação honesta)
  → attach_goal_fields retorna o resumo sem goal_*
  → BFF sem metas → card elegível renderiza sem meta
```

TRANSFORMA+ funcionava porque seu endpoint recebe datas **ISO**
(`YYYY-MM-DD`), convertidas corretamente para `DD-MM-YYYY`. A mesma falha
latente afetava o Dashboard Engenharia legado, que também serializa
`YYYYMMDD` via `inputDateToLmpApi` — o bug era do contrato da api-delpi,
não do Portal Engenharia.

## 3. Matriz de evidências

| Boundary | Meta LMP | Evidência |
|---|---|---|
| Strategic Indicators | **Existe** | Seed V009: `source_key='lmp'` → `engineering-projects-on-time`, meta `95%` mensal 2026 (`higher_is_better`, `percent`) |
| api-delpi (enriquecimento) | **Perdia** | `normalize_si_period_date` rejeitava `YYYYMMDD` → SI 400 → `{}` |
| Adapter Engineering API | Correto | `GOAL_ELIGIBLE_INDICATORS` inclui `lmp_on_time`; `_goal_fields` espelha o contrato |
| `/v1/overview` | Ausente | consequência do boundary acima |
| View model | Correto | `showGoal` reage a `has_goal`/`goal_value` do contrato |

Associação oficial comprovada pelo catálogo SI (V009), não por similaridade
de nome: `lmp` → `engineering-projects-on-time` ("% de Projetos Concluídos
no Prazo").

## 4. Correção

`api-delpi/.../strategic_indicators/dashboard_goal_dates.py`:
`normalize_si_period_date` agora converte `YYYYMMDD` → `DD-MM-YYYY`
(com validação de mês/dia). Boundary correto: o helper existe justamente
para normalizar datas de query dos dashboards para a SI. Nenhum formato
anterior suportado foi alterado; formatos inválidos continuam passando
cruos (comportamento preservado — falha explícita no SI).

**Não revertida** a proteção da OVERVIEW.R1: elegibilidade por indicador
canônico permanece; a correção está no contrato de datas, não na
elegibilidade.

## 5. IDD

A Nota IDD segue trilha separada (`/dashboard/department-indicators`,
`DASHBOARD_IDD_ACCESS` no owner). Com ISO já normalizado, o único bloqueio
conhecido é o grant efetivo — sem ele, `idd: null` (honesto), conforme
residual já documentado no doc 19. Nenhum grant criado.

## 6. Testes

- `test_dashboard_goal_dates.py` (+3): `YYYYMMDD` → `DD-MM-YYYY`,
  inválidos preservados.
- `test_dashboard_goal_enrichment.py` (+1): `enrich_dashboard_metric`
  com datas compactas chama `list_dashboard_goals` com `01-10-2026`/
  `28-10-2026` — prova do contrato na borda.
- Suítes de metas/contrato: **126 passed**.
- api-delpi completa: **6210 passed**, 21 failed pré-existentes
  ambientais (`PermissionError: /app` em `planejamento_orcamentario` —
  assumem layout de container; não relacionadas ao diff).
- engineering-api: 195 passed (inalterada — nenhum diff).
- plugins/engineering: 90 passed (inalterado — nenhum diff).

## 7. Efeito esperado em produção

Com a meta `95%` (monthly/standard, 2026) do indicador
`engineering-projects-on-time`, o SI resolve `comparable_goal`
(Meta parcial) e `reference_goal` (Meta do mês) para o recorte
01–28/10 → o card `% LMP dentro do prazo` exibe Meta parcial, Meta mês
e badges oficiais; IDD aparece quando `DASHBOARD_IDD_ACCESS` efetivo.

Se em algum recorte o SI não possuir meta cadastrada, a ausência
permanece honesta — nenhum valor é fabricado.

## 8. Deploy e smoke

- Push `main` (ff-only): SHA `da8cfa9ee7`.
- Deploy canônico: rebuild de `api-delpi` apenas
  (`up-prod-sequential.sh --build api-delpi`) → `delpi-api-delpi`
  Up/healthy. Engineering-api e MFE inalterados — sem rebuild.
- Smoke público (edge `http://192.168.1.237`): `200`
  `/apps/engineering/overview`, `200` `/apps/api-delpi/health`,
  `401` `/apps/engineering-api/v1/overview` sem JWT.
- Smoke autenticado (meta LMP visível com usuário autorizado):
  `PENDING_GRANT_APPROVAL`.

## 9. Residuais

- QA visual autenticado pendente (gate administrativo).
- O mesmo fix beneficia o Dashboard Engenharia legado (mesma serialização
  `YYYYMMDD`) — efeito colateral positivo, sem alteração nele.

## 10. SHA final

`da8cfa9ee7ec938d5d59a741d2566a97399d91c4` — código + documentação.
