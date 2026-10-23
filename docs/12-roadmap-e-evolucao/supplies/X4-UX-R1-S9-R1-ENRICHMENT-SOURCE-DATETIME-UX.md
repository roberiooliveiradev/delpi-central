# X4.UX-R1.S9.R1 — Fonte e data/hora padronizadas no enriquecimento E14

**Status:** `ACCEPT_WITH_RESIDUAL` — código/testes/docs verdes; residual = validação visual em browser autenticado (mesma pendência de S9/S9.D1).

| Item | Valor |
|---|---|
| BASE HEAD | `c666e96af0` → rebase `f7c899fffe` |
| ORIGIN MAIN | `f7c899fffe` (pré-push) |
| Evidência PO | E14 `002469/01` exibia `brasilapi-cnpj-v1` + ISO UTC brutos |

## 1. Causa raiz

Dois pontos renderizavam valores crus do contrato de enriquecimento (mesmo contrato temporal de S9 — `source_id` ≡ `provider_id`, `source_retrieved_at` ≡ `retrieved_at`, ISO com offset — confirmado em `enrichment/types.ts`):

- `EnrichmentSection.tsx` — meta da revisão ativa interpolava `source_id` e `source_retrieved_at` brutos (ISO UTC visível).
- `EnrichmentHistoryTable.tsx` — coluna Fonte exibia `source_id` cru; `formatDateTime` local usava `toLocaleString("pt-BR")` (fuso do relógio da máquina, não o padrão S9 `America/Sao_Paulo`).

`EXECUTION_DRIFT`: nenhum — semântica temporal idêntica; reuso do formatador era a decisão correta.

## 2. Correção (menor diff, frontend-only)

| Arquivo | Mudança |
|---|---|
| `externalSourceFormat.ts` (novo) | `PORTAL_TIME_ZONE`, `PORTAL_TIME_ZONE_LABEL`, `formatRetrievedAt`, `providerDisplayName` extraídos de `creation/content.ts` — fonte canônica única no bounded context suppliers |
| `creation/content.ts` | re-export do módulo compartilhado (consumidores/testes S9 intactos) |
| `EnrichmentSection.tsx` | meta exibe nome amigável + `formatRetrievedAt`; proveniência técnica (`source_id` + ISO original) preservada via `title` |
| `EnrichmentHistoryTable.tsx` | coluna Fonte → `providerDisplayName` + `title={r.source_id}`; datas → `formatRetrievedAt` (sem dupla conversão) |
| `EnrichmentSection.structural.test.ts` | +2 testes S9.R1 (formatadores compartilhados, proveniência via title, sem `toLocaleString`, fonte única) |
| `creation/creation.structural.test.ts` | asserções S9 apontam para a nova casa canônica |
| `helpTooltips.ts` | tooltip de enriquecimento menciona formato amigável/Brasília |

Fallback honesto preservado: provedor desconhecido exibe o próprio identificador; timestamp inválido retorna o valor original. Controles aceitar/rejeitar, decisões, histórico e contratos **inalterados** — zero backend, zero permissão, zero escrita.

## 3. Validação

- **365 testes MFE PASS** (43 arquivos) · `tsc -b` PASS · `vite build` PASS · ESLint escopado limpo (1 warning pré-existente não relacionado).
- Browser/visual: `TEST_NOT_RUN` — aceite visual pendente de sessão autenticada (gate S9 permanece `INCONCLUSIVE`).

## 4. AC

- ISO bruto fora do texto principal `PASS` (código + estrutural; visual pendente)
- Nome humanizado `PASS` · horários equivalentes criação/enriquecimento `PASS` (mesma função) · sem dupla conversão `PASS` · fallback honesto `PASS` · controles inalterados `PASS` · help sincronizado `PASS`
