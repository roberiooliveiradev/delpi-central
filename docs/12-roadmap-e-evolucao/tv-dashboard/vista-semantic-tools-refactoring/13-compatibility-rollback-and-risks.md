# 13 — Compatibility, Rollback and Risks

## 1. Classificação de mudanças por contrato

| Contrato | Mudança | Classe | Janela |
|---|---|---|---|
| MCP tools | 6 novas + 12 marcadas deprecated | ADDITIVE → DEPRECATED | ≥2 releases antes de remover |
| GPT Actions opIds | 6 `vista_*` novos + 12 `gpt_*` deprecated | ADDITIVE → DEPRECATED → BREAKING na remoção | só após migração provada do GPT externo |
| Typed ops catalog | ops novas (D-6) | ADDITIVE | imediata |
| OpenAPI gerado | schemas novos + `deprecated:true` | ADDITIVE (geração) | por release |
| `agent_directives` | vocabulário novo | BEHAVIORAL (modelo) | junto com as tools |
| Commit schema | `target_echo` novo | ADDITIVE → obrigatório em ops confirm | flag `VISTA_TARGET_ECHO_REQUIRED` |
| Playlist history | `channel`/provenance novo | ADDITIVE | imediata |
| `confirmation` booleano | redundante após echo | DEPRECATED | após adoção do echo |

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
| E1 echo | flag `VISTA_TARGET_ECHO_REQUIRED=false` (volta a `confirmation` booleano); política delete_data_model = metadata editável |
| E2-E5 tools | remover tools/opIds novos — legadas intactas |
| E6 typed ops | remover entries do catalog (metadata, não schema) |
| E7 depreciação | undeprecate |
| E8 directives | versão anterior das instructions |
| E9 testes | n/a |

Deploy é **stateless** — nenhuma mudança de schema de dados
(exceto provenance `channel`, additive); rollback = redeploy da
imagem anterior ou feature flag.

## 4. Riscos de segurança

| Risco | Nível | Mitigação |
|---|---|---|
| Modelo afirma `confirmation=true` sem humano (hoje) | **resolvido por E1** | `target_echo` vinculado ao alvo |
| Vocabulário aberto vira proxy genérico | baixo | Literals fechados; teste `UNKNOWN_ENTITY`/`UNKNOWN_ACTION` |
| Effective capabilities vazam escopo | baixo | derivadas de AuthZ real; só o subconjunto permitido |
| `delete` dedicada mais permissiva | não existe | mesma boundary + echo obrigatório |
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
| Host MCP sem elicit | `confirmation_unavailable` honesto; `target_echo` é a prova transport-neutral |
| ChatGPT Actions sem mecanismo de confirmação nativo | `target_echo` no payload — funciona em HTTP puro |

## 6. ADR supersession — proposta

**Documento proposto**: `adr-vista-semantic-verbs-surface.md`
(DECIDED após aprovação em E0).

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
equivalência), hosts sem elicit (mitigada por target_echo),
confusão de modelo entre verbos (mitigada por catalog rico +
instructions apontando para ele).

## 7. Limitações assumidas

- Proposal store in-process permanece `ACCEPT_WITH_RESIDUAL` —
  migração para persistido só se runtime virar multi-replica.
- `delete` MCP-elicit depende de suporte do host — não universal.
- Consumidores externos do GPT: remoção das 12 depende de evidência
  que não está no repositório — janela de coexistência longa é o
  custo honesto.
