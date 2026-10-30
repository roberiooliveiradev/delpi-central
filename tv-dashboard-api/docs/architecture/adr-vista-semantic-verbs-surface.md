# ADR — VISTA semantic verbs surface (proposal)

**Status:** PROPOSED — aguarda aprovação formal do owner (architecture
governance). **Não é `DECIDED`**: este documento é o pacote de decisão
preparado pela fase 2 de planejamento; a implementação só inicia após
aceite registrado.  
**Date:** 2026-10-30  
**Supersedes:** item 8 de [`adr-vista-specialist-capability-surfaces.md`](adr-vista-specialist-capability-surfaces.md) (2026-09-22), **se aprovado**  
**Evidence baseline:** `docs/12-roadmap-e-evolucao/tv-dashboard/vista-semantic-tools-refactoring/` (docs 01–14, commits `edfe69c361`, `34754a6495`, `f646363133`)

## 1. Contexto

A decisão original (item 8, 2026-09-22) rejeitou a superfície de
entidades do TÉO (`search_records`/`prepare_record_change`) porque
ela modelava VISTA como CRUD multi-entidade genérico — errado para um
domínio cujo write canônico é `PresentationMutation` composta sobre um
boundary único (`GptActionsDispatchService` + `TvPresentationWriteService`).

Desde então, quatro fatos mudaram o custo-benefício:

1. A superfície VISTA cresceu para **12 MCP tools + 12 GPT Actions**
   (paridade via `surface_parity.parity_map`, com gate de drift
   testado) — o problema que item 8 evitava (explosão de endpoints
   por entidade) se manifestou como explosão de tools por operação.
2. SURI (5 tools), CAIO (6 tools/123 SemanticActions), EVA (6+23
   coexistentes) e CLARA (6 tools + consent challenge persistido)
   provaram o padrão de **vocabulário semântico fechado** — verbos,
   não entidades CRUD.
3. Os gaps inventariados (G-03 confirmação fraca, G-05 sem
   auto-descrição de capability, G-09 sem status honesto) são de
   *forma de superfície*, não de capacidade de domínio.
4. O mecanismo de consentimento confiável necessário (challenge
   persistido vinculado a plano — CLARA V014) não existia quando o
   item 8 foi decidido.

## 2. Decisão proposta

Adotar uma superfície semântica de **seis verbos** —
`get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete` —
projetada do **mesmo** `capability_surface` neutro estendido, em
**coexistência** com as 12 tools/opIds legados, sobre o **mesmo**
write boundary. Nenhum orquestrador, registry, autorização ou
mutation engine paralelo é criado.

### Por que isto não é o CRUD que o item 8 proibiu

O modelo rejeitado era `execute(entity=X, action=update,
payload=arbitrário)` — dispatch aberto por nome de entidade. O modelo
proposto é:

- `entity`/`action` são **Literals fechados** por verbo — allowlist,
  nunca dispatch por URL, método, nome de função, SQL ou código.
- `execute` aceita apenas `operations[]` do **catálogo de typed ops
  existente** (`presentation_ops_content.json`) — `entity`/`action`
  são vocabulário de transporte, não novos modos de mutação.
- `delete` cobre somente as 3 typed ops `confirm` existentes
  (`delete_block|delete_section|delete_slide`) — a separação é de
  política de confirmação, não de executor.

A garantia original (nada de endpoint arbitrário, nada de mutação
fora do boundary) é **reforçada** pelo fechamento do vocabulário.

### Modelo

| Tool | Delega a | Natureza |
|---|---|---|
| `get_context` | `build_capability_surface` + AuthZ efetiva (novo) | read-only, aditivo |
| `read` | handlers read existentes (9 mapeamentos) | projeção |
| `analyze` | `preview_*` + `suggest_change` | projeção |
| `knowledge` | `get_product_guide` + content estático | projeção |
| `execute` | `preview_change`/`commit_change` (PREPARE/COMMIT) | facade fina |
| `delete` | mesmo envelope PREPARE/COMMIT | facade fina |

### Contrato execute (fidelidade à proposal)

- `phase=prepare` exige `entity`/`action`/`operations[]`/
  `idempotency_key`; devolve `proposal_handle` + `plan_fingerprint`
  + `base_revision` + `required_confirmation` + `consent_challenge`
  (quando há op `confirm`).
- `phase=commit` exige `proposal_handle` + `idempotency_key`;
  `target_echo` e `consent_artifact` conforme política.
- **`operations[]` não é reenviado no commit** — o handle vincula o
  plano selado; reenvio divergente → `PLAN_MISMATCH`.
- Idempotência por `idempotency_key` + handle single-use; CAS por op
  (`REVISION_CONFLICT`); `PARTIAL_COMMIT` honesto; resultado
  desconhecido → `OUTCOME_NOT_VERIFIED` (read-back, nunca retry cego).
- Single-shot (`commit_now`, Actions-only) somente sem op `confirm`.

## 3. Modelo de confirmação — decisão condicionada (D-5)

**Não aprovado nesta ADR** — depende de evidência de autoridade
decisória. Proposta técnica:

Separação formal: `target_echo` = verificação de identidade do alvo
(anti wrong-object); consentimento humano = artifact cuja **emissão
depende de ação humana verificável**:

| Transporte | Mecanismo proposto | Prova |
|---|---|---|
| MCP + host com elicitation | `ctx.elicit` (padrão EVA) | ação humana no protocolo — **suporte por-host, não universal** |
| MCP host sem elicitation | nenhum confiável | `CONFIRMATION_UNAVAILABLE` — bloqueio explícito |
| GPT Actions / qualquer transporte | consent challenge backend-mediado (padrão CLARA V014) | aprovação humana em superfície confiável, fora do modelo |

Requisitos do artifact (do padrão CLARA `clara_consent_challenge` +
`step_up_consent.py`): persistido, vinculado a `(actor_sub,
proposal_handle, target_ref, plan_hash)`, `challenge_id` emitido no
prepare, aprovação exige token fresco (`iat >= challenge.created_at`)
em superfície confiável, single-use, TTL, consumido no commit,
auditoria via `consent_record`. Sem mecanismo → fail-closed.

**Pendências de decisão (não presumir aprovado):**
- Ownership do mecanismo: serviço de consentimento de plataforma
  (owner segurança) vs implementação VISTA-local seguindo o padrão
  (owner tv-dashboard-api). Import direto de
  `controllership_finance_app` é **proibido** (boundary).
- Ownership da superfície confiável de consentimento (página Portal /
  endpoint BFF).
- Confiança efetiva de elicitation nos hosts MCP reais da VISTA.
- Política de transição dos consumidores legados (janela grandfather
  = exceção de segurança que exige aceite formal, ver §6).

## 4. Capability expansion — decisão condicionada (D-6)

Programa A (refactoring semântico, E0–E5/E7–E9) e Programa B
(expansão, E6) são programas separados. Classificação proposta,
cada item `NEEDS_APPROVAL` do owner:

INCLUIR: `patch_playlist`, `activate/deactivate_playlist`,
`duplicate_slide`, `reorder_sections`, reads `slide_preset.list`/
`media_asset.list` · CONDICIONADO: `delete_playlist` (só após
E1+E5 provarem consent artifact em produção) · ADIAR:
`history_restore`, templates admin, import/export `.mdd`,
`public-url/qr` · EXCLUIR: shares/invites/ACL.

## 5. delete_data_model — decisão condicionada (D-8)

Política proposta ao owner do domínio: sem consumidores → `direct`
(atual); com ≥1 binding consumidor → `confirm` + consent artifact +
preview do blast radius; dependências indetermináveis → bloqueio
`DEPENDENCY_UNRESOLVED`. `NEEDS_APPROVAL`.

## 6. Compatibilidade e transição

- 6 tools/opIds novos = ADDITIVE; 12 legados `deprecated`,
  remoção só após evidência de migração (janela ≥2 releases).
- Campos `target_echo`/`consent_artifact` no schema = ADDITIVE.
- **Exigência** de consent artifact em ops `confirm` =
  **BEHAVIORAL + SECURITY-POLICY** — rejeita fluxo hoje permitido.
  Mitigação proposta: flag `VISTA_CONSENT_ARTIFACT_REQUIRED` +
  janela grandfather ≤1 release (`confirmation=true` aceito com
  warning logado). **A janela é uma exceção de segurança pendente
  de aceite formal — não é política automaticamente aprovada.**
- Rollback nunca reintroduz `confirmation=true` como prova após a
  transição fechar — remover a tool, não rebaixar a política.

## 7. Autoridades preservadas

`PresentationMutation`/`presentation_ops_content.json` (typed ops),
`TvPresentationWriteService` (escritor canônico),
`GptActionsDispatchService` (boundary), `capability_surface` (fonte
única de projeção MCP↔Actions), RBAC backend-first
(`PlaylistAccessService`, fresh Core RBAC, `principal_type==user`),
`VISTA capability ≤ user capability`, proposal store canônico.

## 8. Consequências e riscos

- Divergência facade↔dispatch → testes de equivalência STOP THE LINE.
- Proposal store in-process (item 10 da ADR anterior) permanece
  `ACCEPT_WITH_RESIDUAL`; consent challenge persistido **adiciona
  estado novo** ao domínio — deploy deixa de ser puramente stateless
  se o mecanismo for aprovado (migração própria).
- Hosts MCP sem elicitation não executam ops `confirm` até o
  challenge existir — degradação honesta documentada.
- Custom GPT externo: remoção dos 12 opIds depende de evidência de
  re-import — `INCONCLUSIVE` até lá.
- Auditoria de canal (D-10): `channel` na provenance, respeitando o
  owner do history/digest.

## 9. Referências

- Docs 01–07 (fase 1, inventário); 08 (pendências fechadas);
  09 (D-1..D-10 + matriz de decisões); 10 (contratos); 11 (E0–E9);
  12 (testes); 13 (compatibilidade/riscos); 14 (gate E0).
- `controllership-finance-api/.../clara/step_up_consent.py`,
  `clara_consent_challenge_repository.py`,
  `clara_consent_routes.py`, `migrations/V014`.
- `engineering-api` EVA `semantic_bridge.py` (`ctx.elicit`).

## 10. Aprovação

| Aprovador | Escopo | Status | Data |
|---|---|---|---|
| _(owner arquitetura — nome)_ | supersession item 8 + D-1..D-4, D-7, D-9, D-10 | `PENDING` | — |
| _(owner segurança — nome)_ | D-5 consent mechanism + janela grandfather | `PENDING` | — |
| _(owner produto TV — nome)_ | D-6 capability expansion por bloco | `PENDING` | — |
| _(owner domínio TV — nome)_ | D-8 delete_data_model | `PENDING` | — |

**Esta ADR permanece `PROPOSED` até que a tabela acima esteja
preenchida por autoridade competente. O executor não aprova a
própria proposta.**
