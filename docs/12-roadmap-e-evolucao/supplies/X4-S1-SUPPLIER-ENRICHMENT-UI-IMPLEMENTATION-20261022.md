# X4.S1 — Supplier Enrichment UI — Implementação (2026-10-22)

> Escopo: seção `#enrichment` na ficha E14 (`/apps/supplies/suppliers/:code/:store`),
> módulo `plugins/supplies/src/features/suppliers/enrichment/`. Incremento de E14 —
> sem rota, manifest, permission ou escrita ERP novos. Contrato UX: X4.P0.

## 1. Sequencing gate — decisão

| Frente | Estado em HEAD |
|---|---|
| E10 / WF-15 | `IN_PROGRESS` — gate federado `INCONCLUSIVE`; **preservado, não promovido** |
| E13 / WF-09 | `PROVEN` — SuppliersPage real |
| E14 / WF-10 | `PROVEN` — SupplierDetailPage real (alvo do incremento) |
| X3.E2E | `ACCEPT` (evidência `X3-RUNTIME-EVIDENCE-20261022.md` + addendum) |
| X4.P0 | `ACCEPT` — contrato UX congelado |
| X4.S1 | **Implementado nesta execução** |

Gate de execução satisfeito: E14 implementada + X4.P0 aceito + autorização explícita
da etapa («PORTAL SUPRIMENTOS — X4.S1») + nenhum conflito material com a fila
(E10 é frente independente). **Decisão: READY_TO_EXECUTE → executado.**

## 2. Implementação — menor diff

```
plugins/supplies/src/features/suppliers/enrichment/
  types.ts                          DTOs espelhados do BFF (0 campos inventados)
  api.ts                            7 endpoints via httpClient canônico
  stateMachine.ts                   gates puros: elegibilidade, seleção, bulk, resumo
  content.ts                        copy PT-BR + labels dos enums + error map
  EnrichmentSection.tsx             orquestração: consulta, decisões, draft, histórico
  EnrichmentComparisonTable.tsx     tabela Protheus × BrasilAPI por campo
  EnrichmentHistoryTable.tsx        revisões do ator, paginação server-side
  enrichment.test.ts                28 testes unitários
  EnrichmentSection.structural.test.ts  7 testes de boundary/contrato
```

Integração: `SupplierDetailPage` renderiza `<EnrichmentSection>` somente fora de
edição; `id="enrichment"` + `scrollIntoView` quando `#enrichment` está na URL.

### Regras de decisão (fiéis ao contrato S2)

- `ACCEPT` só quando `decision_state=PENDING` **e** `eligibility_state=ELIGIBLE_TO_APPLY`.
- `REJECT` para qualquer proposta `PENDING`.
- Revisão acionável: `IN_REVIEW` ou `DECIDED` (mesmo `_ACTIONABLE` do backend).
- Bulk: seleção múltipla → confirmação modal → payload atômico; aceite em lote
  desabilitado se qualquer selecionado for inelegível (evita 422 em massa).
- Idempotência: `idempotency_key` estável por tentativa (uuid v4, ≤128 chars);
  retry de falha recuperável reusa **a mesma chave** (replay idêntico real);
  operação nova = chave nova. `expected_revision` sempre enviado.
- `idempotent_replay=true` na resposta → banner «já registrada, sem duplicação».
- Conflito de revisão / 410 / already-decided → reload automático da revisão.
- `prepare-update`: exibe `draft_fields` como rascunho; mensagem fixa
  «Rascunho preparado. Nenhum dado foi gravado no Protheus.» / draft vazio =
  «Nenhum campo aceito…». `write_gate_enabled=false` respeitado — nenhum
  botão de escrita ERP existe.
- Histórico: paginação server-side (10/página), ownership delegado ao backend,
  falha parcial do histórico não derruba a revisão ativa.
- `429`: `ApiRequestError.retryAfter` agora é propagado do header `Retry-After`.

## 3. Segurança — comprovado estruturalmente

- MFE → `supplies-api` somente (`suppliesApiUrl`); zero `api-delpi`/BrasilAPI/fetch.
- Sem token S2S no frontend; `X-Delpi-Caller-App: supplies` + Bearer do usuário.
- Sem permission nova: `supplies.access` + ownership no BFF; UI não decide AuthZ.
- Sem QSA/CPF/contatos excluídos renderizados — só `proposals` do contrato.
- Zero `PUT/POST/PATCH` fora dos 7 endpoints de revisão (structural test).

## 4. UI kit reuse

`SuppliesSectionCard`, `SuppliesDataTable`, `SuppliesStatusBadge`,
`SuppliesModal`, `SuppliesEmptyState`, `SuppliesStateBanner`,
`SuppliesLoadingCard`, `SuppliesCompactPagination`, `SuppliesActionButton`,
`SP_HELP` — **zero componentes novos no kit**; composição local com CSS
`.sp-enrichment__*` isolado em `.dashboard-supplies-portal` (tokens `--sp-*`).

## 5. Help sync (feature-help-sync)

- `helpTooltips.ts`: `suppliersEnrichment` (fonte externa, elegibilidade, lote,
  draft-only, expiração 24h).
- `userManualContent.ts`: passo-a-passo «Comparar cadastro com fonte externa».
- `glossaryContent.ts`: termo «Enriquecimento cadastral» + correção do termo
  «Fornecedor» (ficha agora abre pela lista).

## 6. Matriz de estados implementada

Loading (consulta/histórico/decisão) · Empty (sem revisão / sem histórico) ·
Partial (histórico falha, revisão ativa preservada) · Error genérico ·
Forbidden/NotFound · Expirada/STALE/Cancelled (somente leitura) ·
Revision conflict (reload automático) · Idempotency conflict (409) ·
Rate limit (429 + Retry-After) · Fonte externa indisponível · Resposta inválida ·
CNPJ não localizado/inválido · Documento não suportado · Sem divergência
(summary 0 divergências) · Nenhum elegível (bulk accept bloqueado) ·
Todas decididas (somente leitura + DECIDED acionável para prepare) ·
Draft vazio · Draft preparado. 16 códigos reais → mensagens PT-BR em `content.ts`.

## 7. Verificação

| Gate | Resultado |
|---|---|
| Unit/structural tests | `PASS` 35/35 no módulo |
| Suíte MFE completa | `PASS` 279/279 (38 arquivos) |
| Typecheck `tsc -b` | `PASS` 0 erros |
| Build federado `vite build` | `PASS` (warning pré-existente de chunk) |
| Lint (escopo) | 0 erros, 2 warnings idênticos ao padrão pré-existente de `SupplierDetailPage` |
| Smoke federado / visual QA | `INCONCLUSIVE` — sem runtime Portal nesta execução |
| Escrita ERP | `PROVEN` ausente — nenhum endpoint de write chamado |

## 8. Residuais

1. Smoke federado + screenshots pendentes (AC-21 `INCONCLUSIVE`).
2. Ação opcional na lista E13 **não** adicionada — ampliaria escopo sem ganho
   material; deep link `#enrichment` já cobre navegação direta.
3. Registro ROPA formal → DPO (herdado de X3/X4.P0).

**Conclusão: `ACCEPT_WITH_RESIDUAL`** — menor diff, contrato íntegro, zero escrita
ERP; residual = evidência visual federada.
