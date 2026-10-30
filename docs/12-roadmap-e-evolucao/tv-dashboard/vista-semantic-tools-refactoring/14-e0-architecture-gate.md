# 14 — E0 Architecture Decision Gate (approval package)

Pacote de decisão preparado para o gate E0. **Este documento não
aprova nada** — recommendation ≠ approval. O executor não aprova a
própria proposta. Estados usados (não são equivalentes):

| Estado | Significado |
|---|---|
| `ARCHITECTURE_APPROVED` | owner de arquitetura aceitou a forma da decisão |
| `SECURITY_APPROVED` | owner de segurança aceitou o mecanismo (ex.: consent, grandfather) |
| `PRODUCT_SCOPE_APPROVED` | owner de produto aceitou escopo de capability |
| `READY_FOR_EXECUTION` | todos os gates da etapa satisfeitos + pré-condições técnicas verdes |

Baseline: HEAD `f646363133`, branch `docs/vista-semantic-tools-phase1`,
12 commits atrás de `origin/main` (divergência documental — upstream
avançou fora de tv-dashboard-api; sem conflito material conhecido).

## 1. Pacote de decisão — D-1..D-10

| Decisão | Proposta | Gate exigido | Status de aprovação |
|---|---|---|---|
| D-1 coexistência 6+12 | 6 semantic ADDITIVE; 12 legadas deprecated; remoção só com evidência | ARCHITECTURE | `PENDING` |
| D-2 capability_surface estendido | campos `semantic_mapping`+`status` no modelo neutro — sem registry paralelo | ARCHITECTURE | `PENDING` |
| D-3 execute phase+operations[] | facade fina sobre preview/commit; `operations[]` não reenviado no commit | ARCHITECTURE | `PENDING` |
| D-4 delete dedicada | tool `delete` delegando ao mesmo envelope | ARCHITECTURE | `PENDING` |
| D-5 consent model | consent artifact por transporte + echo como target-check | SECURITY | `PENDING` — ver §2 |
| D-6 capability expansion | Programa B por classificação | PRODUCT_SCOPE | `PENDING` — ver §3 |
| D-7 get_context AuthZ | effective capabilities derivadas de AuthZ real | ARCHITECTURE | `PENDING` |
| D-8 delete_data_model | política condicional por consumidores | ARCHITECTURE+PRODUCT_SCOPE (domínio) | `PENDING` — ver §4 |
| D-9 opIds vista_* | 6 novos + deprecar 12 gpt_* | ARCHITECTURE | `PENDING` |
| D-10 provenance canal | `channel` em history respeitando owner | ARCHITECTURE | `PENDING` |
| ADR supersession item 8 | `adr-vista-semantic-verbs-surface.md` | ARCHITECTURE | `PROPOSED` — ver §5 |

## 2. D-5 — human consent (condicionada)

Perguntas que a autoridade decisória precisa responder **antes** de
aprovar — nenhuma foi presumida:

| Pergunta | Evidência atual | Pendente |
|---|---|---|
| Elicitation é confirmação confiável nos hosts MCP reais da VISTA? | FastMCP `ctx.elicit` existe; suporte é **por-host** (EVA usa com fallback honesto); delpi_mcp não expõe | Confirmar quais hosts MCP produtivos suportam elicitation; sem lista, assumir indisponível |
| Reuso do mecanismo CLARA sem acoplamento? | Padrão provado: `clara_consent_challenge` (V014), `step_up_consent.py`, rotas BFF `clara_consent_routes.py`, `iat>=created_at`, `consent_record` atômico | Decidir: (a) serviço de consentimento de plataforma (owner segurança), (b) implementação VISTA-local seguindo o padrão (owner tv-dashboard-api). Import de `controllership_finance_app` = **proibido** (boundary) |
| Owner da superfície confiável? | CLARA tem página Portal `…/clara-consent` + rotas BFF próprias | VISTA precisa de equivalente: página Portal TV ou superfície genérica — owner não definido |
| Spec do artifact | vinculado a `(actor_sub, proposal_handle, target_ref, plan_hash)`, `challenge_id`, status, `created_at`/`expires_at`/`approved_at`, single-use, consumido no commit, `consent_record` auditável | Congelar contrato em E1 com owner segurança |
| Transição de consumidores legados | janela grandfather ≤1 release proposta | **Exceção de segurança pendente de aceite formal** — não é política aprovada; ver §6 |
| `target_echo` | é target-check, nunca prova de consentimento | nenhum downgrade via flag |

## 3. D-6 — capability expansion (condicionada)

Cada capability requer aceite do owner de produto individualmente:

| Capability | Classificação proposta | Pré-condição |
|---|---|---|
| `patch_playlist` | INCLUIR | typed op sobre `UpdatePlaylistBody` |
| `activate/deactivate_playlist` | INCLUIR | endpoints existentes |
| `duplicate_slide` | INCLUIR | typed op |
| `reorder_sections` | INCLUIR | typed op |
| `slide_preset.list`/`media_asset.list` | INCLUIR | reads somente |
| `delete_playlist` | CONDICIONADO | E1+E5 com consent artifact em produção |
| `history_restore`, templates, `.mdd`, `public-url/qr` | ADIAR | decisão própria |
| shares/invites/ACL | EXCLUIR | — |

Nenhum item é executável nesta entrega.

## 4. D-8 — delete_data_model (condicionada)

Decisão efetiva do domínio pendente. Proposta entregue (doc 09 D-8):
sem consumidores → `direct`; com consumidores → `confirm` + consent
artifact + preview do blast radius; dependências indetermináveis →
`DEPENDENCY_UNRESOLVED` (fail-closed). O owner decide: aprovar a
condicional OU declarar `direct` intencional com aceite documentado
do risco de órfãos.

## 5. ADR

[`tv-dashboard-api/docs/architecture/adr-vista-semantic-verbs-surface.md`](../../../../tv-dashboard-api/docs/architecture/adr-vista-semantic-verbs-surface.md)
— estado `PROPOSED`, tabela de aprovação vazia aguardando autoridade
competente. Item 8 da ADR vigente permanece em vigor até supersession
aprovada.

## 6. Correções documentais aplicadas nesta revisão

- **"Deploy é stateless"** (doc 13) era incompatível com o proposal
  store in-process (item 10 da ADR vigente, `ACCEPT_WITH_RESIDUAL`)
  e com o consent challenge persistido proposto. Corrigido: o write
  boundary já carrega estado de propostas em memória, e o consent
  mechanism, se aprovado, adiciona tabela própria → rollback exige
  migração reversível, não apenas redeploy.
- **Janela grandfather** reclassificada como **exceção de segurança
  pendente de aceite formal** (doc 11 E1, doc 13) — não é política
  automaticamente aprovada.

## 7. Implementation readiness matrix

| Etapa | ARCHITECTURE | SECURITY | PRODUCT_SCOPE | READY_FOR_EXECUTION | Pré-condições | Contratos afetados | Testes exigidos | STOP CONDITION |
|---|---|---|---|---|---|---|---|---|
| E0 ADR/decisões | `PENDING` | n/a | n/a | `NO` | aprovações D-1..D-10 | nenhum (docs) | doc-gate: links+refs | owner rejeita supersession |
| E1 consent model | `PENDING` | `PENDING` | `PENDING`(D-8) | `NO` | E0 + D-5 mechanism owner + D-8 | commit schema (ADDITIVE), política (BEHAVIORAL) | contrato/negativa/equivalência per doc 12 | caminho que comita op confirm sem artifact |
| E2 surface+get_context | `PENDING` | n/a | n/a | `NO` | E0 | tools/list, OpenAPI, surface entries (ADDITIVE) | contexto A/B, parity gate, catalog | capabilities exigirem mudança no Core |
| E3 read/analyze/knowledge | `PENDING` | n/a | `PENDING`(preset/media reads) | `NO` | E2 | 3 tools novas (ADDITIVE) | equivalência byte-level + negativa | handler sem cobertura de teste |
| E4 execute | `PENDING` | `PENDING`(herda E1) | n/a | `NO` | E1,E2 | tool nova (ADDITIVE) | equivalência prepare/commit + PLAN_MISMATCH | divergência facade↔dispatch |
| E5 delete | `PENDING` | `PENDING`(herda E1) | n/a | `NO` | E1,E4 | tool nova (ADDITIVE) | artifact+echo+replay+CONFIRMATION_UNAVAILABLE | delete sem artifact |
| E6 capability expansion | `PENDING` | `PENDING`(ops confirm) | `PENDING` | `NO` | E0 por bloco + E1+E5 p/ delete_playlist | typed ops catalog (ADDITIVE) | positive/sibling/negative por op | op exigir mudança em PatchService |
| E7 depreciação legadas | `PENDING` | n/a | n/a | `NO` | E3-E5 adotadas + evidência de migração | OpenAPI deprecated → BREAKING na remoção | OpenAPI diff + uso | consumidor ativo detectado |
| E8 directives/provenance | `PENDING` | n/a | n/a | `NO` | E2-E5 | instructions + history channel (ADDITIVE) | budget + leak-gate | instructions re-declarando ops |
| E9 certificação E2E | `PENDING` | `PENDING`(veredicto final) | n/a | `NO` | E3-E5 | n/a | E2E+unit+conformance+wire | divergência semântico↔legado |

**Nenhuma etapa está `READY_FOR_EXECUTION`.** O pacote inteiro
aguarda aprovações externas.

## 8. Primeiro bounded step executável

Quando (e somente quando) a ADR for aprovada:

**Step candidato: E0.S1 — publicação da supersession**
- Escopo: marcar item 8 da ADR vigente como `superseded-by` +
  referência cruzada + capability-matrix ref. Somente docs.
- Pré-condição: tabela de aprovação §5 preenchida para o escopo
  arquitetural (D-1..D-4, D-7, D-9, D-10 + supersession).
- Evidência a retornar: diff da ADR vigente + link no README.

## 9. Condições explícitas para iniciar E1

1. `SECURITY_APPROVED` para o mecanismo de consent artifact
   (owner do mecanismo definido + spec congelada: binding, TTL,
   single-use, auditoria, fail-closed).
2. `SECURITY_APPROVED` ou rejeição registrada da janela grandfather
   como exceção de segurança.
3. Decisão D-8 registrada pelo owner do domínio.
4. Ownership da superfície confiável de consentimento definido.

## 10. Condições explícitas para iniciar E2

1. `ARCHITECTURE_APPROVED` da ADR (supersession + D-2, D-7).
2. Verificação de que derivação de effective capabilities usa apenas
   contratos existentes de `PlaylistAccessService`/Core — se exigir
   mudança no Core, escalar antes de E2.

## 11. Riscos residuais do gate

- Aprovação parcial (D-5 rejeitado) invalida E1/E4/E5/E6 —
  replanejar mantendo o booleano legado **sem** chamá-lo de prova.
- `origin/main` 12 commits à frente — rebased docs podem divergir;
  verificar antes de qualquer implementação futura.
- PR não aberto; o pacote de aprovação vive na branch documental —
  abrir PR quando o owner estiver pronto para decidir.

## D-6 product-direction amendment — 2026-10-30

The §3 D-6 INCLUIR/ADIAR/EXCLUIR classification reflects an earlier recommendation, **not the latest requester scope**. All eight blocks are now desired as INCLUDED, including playlist delete, restore/templates/MDD and shares/invites/permissions. See [15 — product decision and master plan](15-d6-product-direction-and-master-plan.md). Approval status remains `PRODUCT_DIRECTION_RECORDED / OWNER_APPROVAL_PENDING`, **NOT** `PRODUCT_SCOPE_APPROVED` and **NOT** `READY_FOR_EXECUTION`. Resolve individual TV-domain, Core-RBAC and security gates before respective waves. E2/E3's existing read-only projections do not depend on Program B media/preset expansion. ADR supersession remains PROPOSED.
