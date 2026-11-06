# MyWEG Necessidades — UI/UX refinement

> **TASK_ID:** `MYWEG-NEEDS-UI-UX-REFINEMENT`  
> **BASE_HEAD (origin/main ao iniciar):** `7c8440a4e711f0cf3e943eab24b181b0746bc85e`  
> **Escopo:** frontend do plugin `production-control` (MyWEG) — visual/copy/layout apenas

## Reuse

| Campo | Valor |
|---|---|
| EXISTING_EQUIVALENT | YES |
| REUSE_DECISION | REUSE |

Owners preservados:

- `plugins/production-control` — UI
- `production-control-api` — contratos e comparação (sem alteração)
- `api-delpi` — integrações fiscais / SB1 (sem alteração)

## Objetivo

Deixar a tela **Necessidades WEG** mais minimalista, escaneável e executiva para o PCP, sem mudar contratos nem lógica de comparação/reprogramação.

## O que mudou (UI)

- Hub de entrada (dois cards) com menos texto, CTA alinhado ao título e hierarquia mais limpa.
- Textos longos da comparação movidos/encurtados; disclaimers essenciais em linha curta + tooltips.
- Filtros da comparação agrupados (par de coletas · filtro de produto · faturamento).
- Busca duplicada removida: filtro de produto fica na barra de análise; `hideSearch` nas `DataTableSection` MyWEG.
- Análise por produto com título mais claro, chips de resumo e colunas enxutas.
- Detalhe do produto abre em modal central (`HostContainedWideDialog`), sem expandir na lista.
- Percentuais via `formatPercentDisplay` (máx. 2 casas, pt-BR).
- Semântica visual verde/vermelho para aumentos/reduções (badges, deltas, KPIs).
- KPIs de comparação com mais respiro e número em destaque.
- Ajustes responsivos (≤1100px e ≤768px) nos filtros/hub.

## O que não mudou

- Contratos OpenAPI / rotas backend
- Motor de comparação E5 e algoritmo de reprogramação
- RBAC, cron/publisher Linux, E1/E2/E4/E5 de domínio
- Manifesto / subplugin

## Evidência de testes

| Comando | Resultado |
|---|---|
| `vitest` MyWEG (page + shifts + `formatPercentDisplay` + `mywegSemanticTone`) | 5 files / 18 tests PASS |
| `vite build --outDir /tmp/ppc-myweg-build-check` | PASS (build padrão bloqueado por `dist/` root-owned no workspace) |
| `tsc -b` | Falhas pré-existentes fora do escopo (LineFeeder / deps markdown plugin-ui / EACCES tsbuildinfo) |
| eslint focado nos arquivos MyWEG | warnings pré-existentes `react-hooks/set-state-in-effect` (sem errors novos) |

Homologação visual em produção / smoke no portal **não** executada neste documento.
