# 13 — Compatibility, Rollback and Risks

## 1. Classificação de mudanças por contrato

| Contrato | Mudança | Classe | Janela |
|---|---|---|---|
| MCP tools | 6 novas + 12 marcadas deprecated | ADDITIVE → DEPRECATED | ≥2 releases antes de remover |
| GPT Actions opIds | 6 `vista_*` novos + 12 `gpt_*` deprecated | ADDITIVE → DEPRECATED → BREAKING na remoção | só após migração provada do GPT externo |
| Typed ops catalog | ops novas (D-6) | ADDITIVE | imediata |
| OpenAPI gerado | schemas novos + `deprecated:true` | ADDITIVE (geração) | por release |
| `agent_directives` | vocabulário novo | BEHAVIORAL (modelo) | junto com as tools |
| Commit schema | campos `target_echo` + `consent_artifact` novos | ADDITIVE (o campo em si) | por release |
| Commit **política** | artifact exigido em ops `confirm` | **BEHAVIORAL + SECURITY-POLICY** — bloqueia fluxo antes permitido; NÃO é ADDITIVE | janela grandfather ≤1 release (`confirmation=true` aceito com warning) — **exceção de segurança pendente de aceite formal do owner, não política auto-aprovada**; flag `VISTA_CONSENT_ARTIFACT_REQUIRED` |
| Playlist history | `channel`/provenance novo | ADDITIVE | imediata |
| `confirmation` booleano | insuficiente como prova após E1 | DEPRECATED → REJECTED em ops `confirm` | após fechamento da janela grandfather |

> A adição de campo no schema é ADDITIVE; a **exigência** do
> artifact é BEHAVIORAL porque rejeita consumidor que hoje comita
> ops `confirm` com `confirmation=true`. Coexistência das 12 tools
> legadas não elimina essa mudança de comportamento.

## 2. Consumidores e impacto

| Consumidor | Superfície usada | Impacto | Ação |
|---|---|---|---|
| Custom GPT externo | 12 `gpt_*` opIds importados | nenhum na adição; quebra só na remoção | coexistir; remoção só com evidência de re-import |
| Hosts MCP | 12 tools | nenhum na adição | deprecated notices; adoção gradual |
| Chat interno | nenhum tool-call (só handoff) | nenhum | validar que handoff continua funcionando |
| Editor/preview/TV | REST/WS — não usa tools | nenhum | n/a |
| DÉLIA capability adapter | TARGET — sem código | n/a | projetar para o vocabulário novo |

## 3. Rollback por etapa

| Etapa | Rollback |
|---|---|
| E0 ADR | supersession revertida (doc) |
| E1 consent artifact | flag `VISTA_CONSENT_ARTIFACT_REQUIRED=false` — **com TTL + motivo registrado**; durante a janela grandfather volta ao estado de transição (`confirmation=true` + warning); **após a transição fechada, rollback não reintroduz `confirmation=true` como prova** — remover a tool, não rebaixar a política; política delete_data_model = metadata editável |
| E2-E5 tools | remover tools/opIds novos — legadas intactas |
| E6 typed ops | remover entries do catalog (metadata, não schema) |
| E7 depreciação | undeprecate |
| E8 directives | versão anterior das instructions |
| E9 testes | n/a |

Deploy **não é plenamente stateless**: o proposal store é
**in-process** (item 10 da ADR vigente, `ACCEPT_WITH_RESIDUAL` para
single-replica — restart descarta proposals abertas) e, se o
consent challenge backend-mediado for aprovado em D-5, uma tabela
persistida própria passa a existir no domínio (migração exigida —
o desafio **precisa** sobreviver a restart para não comprometer
planos aprovados). Provenance `channel` é additive. Conclusão:
rollback de tools/opIds = redeploy ou feature flag; rollback de
schema do consent challenge exige migração reversível, não apenas
redeploy.

## 4. Riscos de segurança

| Risco | Nível | Mitigação |
|---|---|---|
| Modelo afirma `confirmation=true` sem humano (hoje) | **resolvido por E1** | consent artifact (elicit ack ou challenge backend-mediado) vinculado a ator+proposta+alvo+plan_hash; `target_echo` só verifica identidade do alvo |
| Vocabulário aberto vira proxy genérico | baixo | Literals fechados; teste `UNKNOWN_ENTITY`/`UNKNOWN_ACTION` |
| Effective capabilities vazam escopo | baixo | derivadas de AuthZ real; só o subconjunto permitido |
| `delete` dedicada mais permissiva | não existe | mesma boundary + echo + consent artifact obrigatórios |
| Compound plan atomicidade | médio | PARTIAL_COMMIT honesto; sem rollback compensatório — documentado |
| Proposal store in-process em multi-replica | residual aceito | documentado; Postgres (CLARA) se escalar |
| `delete_data_model` direct órfana bindings | médio | D-8 política condicional — NEEDS_APPROVAL |

## 5. Riscos de contrato/runtime

| Risco | Mitigação |
|---|---|
| Divergência semântico↔legado | testes de equivalência por tool (STOP THE LINE) |
| Drift parity_map em 6↔6 | mesmo gate de cobertura (`test_surface_parity_map_*` adaptado) |
| Budget Actions com 6 schemas grandes | schemas por-verbo compactos; gate ≤100 KiB existente |
| Instruções re-declarando ops | leak-gate + budget existentes; instructions apontam para catálogo |
| Host MCP sem elicit | `CONFIRMATION_UNAVAILABLE` — bloqueio explícito em ops `confirm`; `target_echo` NÃO é prova de consentimento (só target-check) |
| ChatGPT Actions sem mecanismo de confirmação nativo | consent challenge backend-mediado (padrão CLARA: aprovação no Portal vinculada a `plan_hash`); sem canal humano verificável → `CONFIRMATION_UNAVAILABLE` |

## 6. ADR supersession — proposta

**Documento proposto**: `tv-dashboard-api/docs/architecture/adr-vista-semantic-verbs-surface.md`
— **estado atual: `PROPOSED`** (aguarda aprovação do owner em E0;
só vira `DECIDED` após aceite formal registrado na tabela §10 do
próprio ADR — não é uma decisão tomada).

**Motivo da decisão original (item 8, 2026-09-22)**: rejeitar a
superfície de entidades do TÉO (`search_records`/`prepare_record_change`)
porque ela modelava VISTA como CRUD multi-entidade genérico — errado
para um domínio cujo write canônico é `PresentationMutation` composta
sobre um boundary único.

**Diferença do modelo proposto**: o catálogo semântico de 6 verbos
não é CRUD de entidade. `execute` aceita somente
`operations[]` do **catálogo de typed ops existente** —
`entity`/`action` são vocabulário fechado de transporte, não novos
modos de mutação. O CRUD genérico seria `execute(entity=X, action=update,
payload=arbitrário)` — **proibido pelo design**: `action` é
`apply_mutation` único e `operations[]` é o subconjunto tipado
governado. A garantia original (nada de endpoint arbitrário,
nada de mutação fora do boundary) é **reforçada** pelo registry
fechado — não enfraquecida.

**Interfaces que mudam**: superfície de transporte (tools/opIds).
**Autoridades que permanecem**: `PresentationMutation` catalog,
`TvPresentationWriteService`, `GptActionsDispatchService`,
`capability_surface`, RBAC backend-first, `VISTA ≤ user capability`.
**Riscos novos**: divergência facade↔dispatch (mitigada por
equivalência), hosts sem elicit (mitigada por challenge
backend-mediado ou bloqueio `CONFIRMATION_UNAVAILABLE` — nunca por
echo), confusão de modelo entre verbos (mitigada por catalog rico +
instructions apontando para ele).

## 7. Limitações assumidas

- Proposal store in-process permanece `ACCEPT_WITH_RESIDUAL` —
  migração para persistido só se runtime virar multi-replica.
- `delete` MCP-elicit depende de suporte do host — não universal;
  host incapaz → `CONFIRMATION_UNAVAILABLE` (fail-closed), e o
  consent challenge backend-mediado é a alternativa cross-transporte.
- Consumidores externos do GPT: remoção das 12 depende de evidência
  que não está no repositório — janela de coexistência longa é o
  custo honesto.

## Expanded D-6 compatibility addendum — 2026-10-30

The [full implementation master plan](15-d6-product-direction-and-master-plan.md) now includes restore, templates, MDD and access sharing/permissions as *target scope*, replacing older DEFER/EXCLUDE recommendations. Each is a separate contract-risk family: restore must preserve history/revision semantics; template lifecycle must preserve publish/archive and consuming editor/public parity; MDD must preserve portable schema/versioning, preview!=apply, asset validation and round-trip; resource access must preserve Core RBAC, end-user context, TV resource scope and auditable grant/revoke. Do not assert these paths are ADDITIVE or implementable via typed ops before owner/consumer proof; permission changes are not generic VISTA admin operations. Product target remains unapproved for execution.
