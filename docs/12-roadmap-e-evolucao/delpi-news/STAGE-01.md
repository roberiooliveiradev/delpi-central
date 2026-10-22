# DELPI News — Etapa 1 (fechamento)

**Commit original E1:** `e26d8ade783661c503fe84872b78e92dc4055e81`  
**HEAD de início desta correção (local):** `a34fbdf62e3998604e65e2f6ed7ebd592526bdee`  
**HEAD final (commit de fechamento):** `6ae6ea799e847ed66d75ed4dffa37e703907821c`  
**Branch:** `main`

## Ledger de requisitos

| ID | Requisito | Estado |
|---|---|---|
| RQ-01 | Reancorar git/regras/docs | ATENDIDO |
| RQ-02 | Inventário de reuso | ATENDIDO |
| RQ-03 | Ownership admin × público × API × TV (API como PLANNED) | ATENDIDO |
| RQ-04 | Contratos conceituais sem ops prematuras | ATENDIDO |
| RQ-05 | Prova visual navegável | ATENDIDO |
| RQ-06 | Sem Android/APK | FORA_DO_ESCOPO_COM_JUSTIFICATIVA |
| RQ-07 | Não ampliar `external-data-api` | ATENDIDO |
| RQ-08 | Preservar trabalho alheio | ATENDIDO |
| RQ-09 | Bloquear demo em produção por padrão | ATENDIDO |
| RQ-10 | Textos neutros + identificação de demonstração | ATENDIDO |
| RQ-11 | Imagem opcional / vazio / 16:9 / clamp / TV | ATENDIDO |
| RQ-12 | Testes ampliados (timer, teclado, wrap, prod gate) | ATENDIDO |
| RQ-13 | Homologação Adeus documentada | ATENDIDO (execução em aparelho PENDENTE) |
| RQ-14 | `delpi-news-api` não apresentado como aprovado | ATENDIDO |

## Impacto da mudança de rota demo

| Antes | Depois |
|---|---|
| `/p/delpi-news/board/aberto` servia fixture em qualquer build | Token `aberto` rejeitado; demo só em DEV ou `VITE_DELPI_NEWS_DEMO=1` via `/p/delpi-news/board/demo` |

Não havia consumidor legítimo de canal real — apenas a prova visual E1. Produção padrão passa a 404 (comportamento desejado).

## Evidência de validação

| Prova | Resultado |
|---|---|
| Vitest `src/apps/delpi-news` (Docker node:22) | **16/16 PASS** |
| `npx vite build` do `public-hub` (produção, sem `VITE_DELPI_NEWS_DEMO`) | **PASS** (`VITE_BUILD_OK`) — demo gate embutido no bundle |
| `npm run build` (`tsc -b && vite build`) no sandbox com symlinks de irmãos | **não reexecutado como fonte de verdade**; vite build isolado prova o app. Falhas históricas de `tsc -b` vinham de pacotes irmãos/ambiente, não de `delpi-news` |
| Demo em produção sem flag | **bloqueada** (testes de `loadBoard` + build prod) |
| Homologação Adeus | **HOMOLOGACAO_PENDENTE** (checklist em `HOMOLOGACAO-ADEUS-PENDRIVE.md`) |

## Pendências para Etapa 2

- Decisão arquitetural formal sobre criar `delpi-news-api`
- Scaffold API + schema + coleta (somente após decisão)
- Admin MFE + RBAC
- Token opaco de board real
- Homologação Adeus presencial
