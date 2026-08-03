# Playbook — Relatório Gerencial (Faturamento)

> **Branch:** `feat/reports-relatorio-gerencial`  
> **Provider key:** `management_revenue_monthly`  
> **Nome na UI:** Relatório Gerencial — Faturamento  
> **Agenda:** mensal, dia 1 (timezone `America/Sao_Paulo`)

## Objetivo

E-mail mensal à Direção com visão gerencial do **faturamento (ROL com IPI)** do mês civil anterior, comparativo MoM, divisão SC × ES, distribuição por cliente e **IGD / IDDs** do mês (Indicadores Estratégicos).

## Glossário

| Termo | Significado |
|-------|-------------|
| **ROL (`rol_with_ipi`)** | Receita operacional líquida canônica Delpi (SD2 − devoluções SD1), mesma fórmula do dashboard comercial / financeiro |
| **Mês do relatório** | Mês civil imediatamente anterior à data de envio (`as_of`) |
| **Comparativo** | Mês civil imediatamente anterior ao mês do relatório |
| **Filial 01** | Jaraguá do Sul (SC) |
| **Filial 02** | Rio Bananal (ES) |
| **Consolidado** | Soma das filiais (branch omitido em `get_rol`) |
| **Top 20 + Demais** | Maiores clientes por ROL no mês; restante agregado em «Demais» |
| **IGD** | Índice Geral de Desempenho (às vezes chamado “IDG”) — nota consolidada SI |
| **IDD** | Indicador de Desempenho Departamental (0–10) por departamento SI |

## Wireframe do e-mail

1. **Cabeçalho marca** — logo CID + título «Relatório Gerencial» + subtítulo «Faturamento — {Mês/Ano}»
2. **Resumo executivo** — 3–4 bullets (consolidado, Δ%, participação SC vs ES)
3. **Cards KPI** — Consolidado | SC | ES (valor do mês, Δ R$, Δ %)
4. **Tabela filiais** — mês / anterior / Δ %
5. **Desempenho — IGD e IDDs** — card IGD (nota, classificação, tendência) + tabela IDDs por departamento
6. **Evolução consolidada do ano** — gráfico linha (R$ mi), jan → mês do relatório
7. **Tabela Top 20 clientes** — nome fantasia (`A1_NREDUZ`), ROL mês, share %, ROL ant., Δ % (sem código)
8. **Rodapé institucional** — brand layout Delpi Reports

Seções futuras (shell): meta ROL SI, WEG vs novos negócios, OTD — fora do MVP.

## Subject

`Relatório Gerencial — Faturamento | {mês/ano}`  
Ex.: `Relatório Gerencial — Faturamento | jun/2026`

## Params do provider

| Param | Default | Uso |
|-------|---------|-----|
| `asOfDate` | hoje (SP) | Preview / backfill; agenda usa data do run |
| `customerLimit` | 20 | Top N clientes |

## Fontes de dados

| Bloco | Fonte |
|-------|--------|
| ROL consolidado / 01 / 02 | `FinancialRepository.get_rol` |
| Ranking clientes | `GET /commercial/rol/by-customer` (nome fantasia `A1_NREDUZ`) |
| MoM | `CommercialRolMomComparisonService` |
| Evolução anual | `year_evolution` (jan→mês, consolidado) + PNG CID no e-mail |
| IGD | SI S2S `tv-dashboard-hero` via `DashboardIgdService` (`competence=YYYY-MM`) |
| IDDs | SI S2S `dashboard-departments-indicators` via `DashboardDepartmentIndicatorsService` |

Se a SI estiver indisponível, o bloco de faturamento segue e a seção IGD/IDDs é omitida.

## Checklist homologação

- [ ] Preview HTML no Outlook/Gmail
- [ ] Números batem com dashboard-commercial / financial no mesmo período
- [ ] Agenda `monthly` dia 1 → `next_run_at` correto
- [ ] Envio piloto → lista Direção

## Ops

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin reports
./infra/scripts/up-*-sequential.sh --fase mfe --build reports
```

Em produção: **somente** `up` — nunca `reset --plugin reports`.
