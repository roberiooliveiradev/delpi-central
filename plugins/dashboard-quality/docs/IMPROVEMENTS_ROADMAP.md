# Roadmap de melhorias — Dashboard Qualidade

Complementa [ROADMAP.md](./ROADMAP.md) (fases 0–6). Entregas em **ondas** com critério de pronto por item.

---

## Onda 1 — Fundação UX e API ✅

| # | Item | Status | Critério de pronto |
|---|------|--------|-------------------|
| 1.1 | `GET /quality/branches` — filiais do período | ✅ | Combo de filial populado dinamicamente |
| 1.2 | Filtros sincronizados na URL (`date_start`, `date_end`, `branch`) | ✅ | Link compartilhável; atalhos preservam filtros |
| 1.3 | Debounce em filtros de texto (NC) | ✅ | Sem request a cada tecla |
| 1.4 | Cache leve no cliente (stale-while-revalidate) | ✅ | Voltar à tela não refaz fetch imediato |

---

## Onda 2 — Performance de gráficos (parcial ✅)

| # | Item | Status | Critério de pronto |
|---|------|--------|-------------------|
| 2.1 | `GET /quality/ppm/{type}/series?granularity=` | ✅ | Uma HTTP call para evolução PPM |
| 2.2 | Home: KPIs com loading independente | ✅ | Falha em Kaizen não derruba PPM |
| 2.3 | Mini-sparklines na home (PPM) | 📋 | Tendência visual no card |

---

## Onda 3 — Análise e exportação

| # | Item | Status | Critério de pronto |
|---|------|--------|-------------------|
| 3.1 | Granularidade dia/semana/mês/ano em Kaizen e 5S | 📋 | Mesmo padrão PPM/NC |
| 3.2 | Drill-down gráfico → tabela filtrada | 📋 | Clique no ponto aplica filtro de data |
| 3.3 | Export CSV da série do gráfico | 📋 | PPM e devoluções NC |
| 3.4 | `GET /quality/nonconformities/series` (agregado server-side) | 📋 | Gráfico NC sem limite de amostra |

---

## Onda 4 — Polimento (Fase 6 estendida)

| # | Item | Status | Critério de pronto |
|---|------|--------|-------------------|
| 4.1 | Responsivo tablet+ | 📋 | Gráficos legíveis em 768px |
| 4.2 | Acessibilidade (labels, foco, contraste) | 📋 | Revisão axe/Lighthouse |
| 4.3 | Validação Zod das respostas API | 📋 | Erro claro em contrato quebrado |
| 4.4 | Registro Core API + CI build plugin | 📋 | Checklist monorepo |
| 4.5 | Mensagens de erro acionáveis (timeout TOTVS) | 📋 | Copy orientando período menor |

---

## Onda 5 — Produto avançado (opcional)

| # | Item | Status |
|---|------|--------|
| 5.1 | PPM interno + externo no mesmo gráfico | 📋 |
| 5.2 | Linhas de meta / limite no gráfico | 📋 |
| 5.3 | NC PostgreSQL (gestão) — plugin separado | 📋 |
| 5.4 | Relatório PDF / impressão | 📋 |

**Legenda:** ✅ concluído · 🚧 em andamento · 📋 planejado

---

## Ordem de PRs sugerida

1. Onda 1 (API branches + URL + debounce + cache)
2. Onda 2.1–2.2 (série PPM + home resiliente)
3. Onda 2.3 + Onda 3 (sparklines, drill-down, exports)
4. Onda 4 (polish operacional)
