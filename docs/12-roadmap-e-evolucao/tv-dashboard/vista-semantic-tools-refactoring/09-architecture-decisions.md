# 09 — Architecture Decisions (D-1 a D-10)

Cada decisão: contexto → opções → evidência → **recomendação** →
status. Status `RECOMMENDED` = pronto para aprovação; `NEEDS_APPROVAL`
= decisão de produto/segurança do owner; `READY` = pode implementar.

## D-1 — Superfície: 6 verbos substituindo, coexistindo ou mantendo 12?

- **Contexto**: ADR item 8 decidiu contra superfície de entidades
  (TÉO CRUD). A convergência semântica muda a *forma*, não o poder.
- **Opções**: (a) 6 substituem 12; (b) coexistência EVA-style
  (6 novas + 12 legadas até migração provada); (c) manter 12.
- **Evidência**: EVA opera 23+6 tools coexistindo sem quebra; os 12
  gpt_* opIds estão importados num Custom GPT externo — remoção é
  BREAKING para consumidor fora do repositório (doc 08 §5).
- **Recomendação**: **(b) coexistência** — 6 semantic tools ADDITIVE,
  12 legadas mantidas com `deprecated` no catálogo/OpenAPI, remoção
  somente após evidência de migração. Não há benefício em quebrar
  consumidores para ganhar elegância de superfície.
- **Status**: `RECOMMENDED` (precisa supersession ADR item 8 — doc 11 E0).

## D-2 — Onde mora o catálogo semântico?

- **Opções**: (a) `vista_semantic_registry.py` novo tipo
  `SemanticAction`; (b) campos `semantic`/`status` no
  `capability_surface` neutral existente.
- **Evidência**: `capability_surface.py` já é a única fonte que
  projeta MCP↔Actions (gate testado, doc 08 §4). CAIO/EVA usam
  registry dataclass — mas eles *não* tinham um capability_surface
  neutro prévio; VISTA tem.
- **Recomendação**: **(b) estender o modelo neutral** — adicionar
  `semantic_mapping` (entidade/ação → operação) + `status`
  (proven/planned/not_implemented) às entries existentes e derivar
  as 6 tools por projeção. Um novo registry paralelo criaria a
  segunda fonte que a própria ADR proíbe.
- **Status**: `RECOMMENDED`.

## D-3 — Forma do `execute`

- **Opções**: (a) `execute(entity, action, operations[])` estilo
  SURI — operations = typed ops; (b) `phase: prepare|commit` dentro
  do mesmo tool (estilo CAIO delete); (c) manter prepare/commit
  separados como tools.
- **Evidência**: PlanCompiler já aceita `ops[]` ordenado com
  `as`/`*Ref` (compound plans provados, doc 05 Caso A/D); CAIO
  prova que `phase` num único tool é legível para hosts; SURI prova
  que `operations[]` resolve multi-op.
- **Recomendação**: **(a)+(b)** — `execute` com
  `entity: "presentation"`, `action: "apply_mutation"`,
  `operations: [{op, args, as?}]`, `phase: "prepare"|"commit"`,
  `proposal_handle?`, `idempotency_key`, `target_echo?`,
  `consent_artifact?` (ver D-5 — `confirmation` booleano nunca é
  prova suficiente em ops `confirm`).
  `phase=prepare` → delega a `preview_change`; `phase=commit` →
  `commit_change`. **Fachada fina, zero lógica nova**: o dispatch
  existente faz tudo. Nenhum orquestrador paralelo.
- **Status**: `RECOMMENDED`.

## D-4 — `delete` dedicada ou dentro de `execute`?

- **Opções**: (A) tool `delete` sobre o mesmo PREPARE/COMMIT;
  (B) exclusões dentro de `execute` com confirmação governada;
  (C) híbrido — `delete` existe como alias semântico para
  `execute(entity, action=delete_*)` mas delega ao mesmo mecanismo.
- **Comparação**:
  | Critério | A: delete dedicada | B: delete via execute | C: alias semântico |
  |---|---|---|---|
  | Clareza pro modelo/host | alta (verbo explícito) | média | alta |
  | Duplicação de mecanismo | nenhuma (reusa) | nenhuma | nenhuma |
  | Paridade c/ padrão alvo (6 tools) | exata | 5 tools | exata |
  | Política especial de deleção | isolável por tool | misturada | isolável no registry |
- **Evidência**: CAIO/CLARA/EVA têm `delete` dedicada com política
  própria (sealed/elicitation); VISTA tem só 3 ops `confirm` —
  volume pequeno, mas a *separação de política* (deleção sempre
  exige prova) é o motivo do verbo dedicado no benchmark.
- **Recomendação**: **(A) `delete` dedicada** delegando ao mesmo
  envelope PREPARE/COMMIT — com `entity ∈ {block, section, slide}`
  (os 3 ops confirm existentes), `phase`, e confirmação verificável.
  A interface separa a política; a execução não duplica.
- **Status**: `RECOMMENDED` (mantém as 6 tools do padrão-alvo).

## D-5 — Confirmação: separação formal de conceitos (CORRIGIDO)

**Correção ao plano anterior**: `target_echo` sozinho **não é prova
de consentimento humano** — um modelo pode observar o target ID no
preview e reproduzi-lo no commit sem intervenção humana. O plano
anterior classificava o echo como "a prova"; isso estava errado.
As responsabilidades são separadas:

| Conceito | O que prova | Mecanismo VISTA |
|---|---|---|
| Target identity verification | o commit atinge o objeto exibido no preview, não outro | `target_echo` (id exato do alvo) |
| Proposal integrity | o plano comitado é o plano preparado, não outro | `proposal_handle` opaco HMAC + plan fingerprint selado server-side |
| Actor binding | quem comita é quem preparou | handle actor-bound + `principal_type==user` + re-authz por op |
| Authorization | o ator pode executar aquela operação naquele recurso | Core RBAC + `PlaylistAccessService` no commit |
| **Human consent** | um humano aprovou conscientemente | **só vale se a emissão depender de ação humana verificável** — ver mecanismos abaixo |
| Commit permission | política permite comitar neste transporte/estado | `confirmationPolicy` + consent artifact válido |

### Mecanismos de consentimento por transporte/host

| Transporte/host | Mecanismo | Prova | Disponibilidade |
|---|---|---|---|
| MCP + host com elicitation (Claude Code/Desktop) | `ctx.elicit` schema `{confirm, target_echo}` (padrão EVA) | ação humana no protocolo | por-host |
| MCP host sem elicitation | nenhum confiável | — | `CONFIRMATION_UNAVAILABLE` → **bloqueio explícito** |
| GPT Actions (HTTP/OpenAPI) | **backend-mediated consent challenge** (padrão CLARA step-up): prepare emite `consent_challenge_id` + URL do Portal; humano autenticado aprova o plano selado no Portal; commit exige `consent_token` emitido pelo backend **após** aprovação registrada | ação humana em canal autenticado, fora do modelo | requer Portal consent endpoint (reuso do padrão CLARA `step_up_consent.py`/`clara_consent_challenge` V014: challenge persistido, `plan_hash` vinculado, `iat>=created_at`) |
| Ambos (fallback político) | nenhum | — | `CONFIRMATION_UNAVAILABLE` explícito; **nunca downgrade silencioso para echo** |

### Resistência a replay/reuso (obrigatória no desenho)

- Consent challenge/token vinculado a `(actor, proposal_handle,
  target_ref, action, plan_hash)` — reuso entre atores, alvos ou
  propostas → `CONSENT_MISMATCH`.
- Single-use: consumido no primeiro commit (mesmo se falhar).
- TTL curto + invalidado se a proposal expirar/for consumida.
- `iat >= challenge.created_at` (padrão CLARA) — credenciais
  anteriores ao desafio não valem.
- `target_echo` permanece como **verificação de identidade do alvo**
  (anti wrong-object), nunca como consent proof.

### Decisão

`confirmation=true` booleano **não satisfaz** consentimento humano
para ops `confirm`. Transições:
1. `target_echo` entra como target-identity check (corrige
   wrong-object; não é consent).
2. Consent artifact por transporte: elicit (MCP-capable) ou
   consent challenge backend-mediado (Actions/qualquer host).
3. Sem mecanismo confiável no transporte → bloqueio explícito
   `CONFIRMATION_UNAVAILABLE` — fail-closed.

- **Status**: `RECOMMENDED` — mecanismo consent-challenge precisa
  de aprovação de segurança (reuso do padrão CLARA vs. implementação
  nova no tv-dashboard-api; owner decide).

## D-6 — Dois programas separados (CORRIGIDO)

**Programa A — Semantic Surface Refactoring**: padronizar *como* a
VISTA descobre/consulta/analisa/executa o que já existe. Escopo:
E0-E5, E7-E9. Não adiciona capability de produto.

**Programa B — Capability Expansion**: ampliar *o que* a VISTA
alcança. Escopo: E6 (e somente ele). Cada item abaixo é decisão de
produto do owner, não consequência da refatoração:

| Capability | Classificação | Rationale |
|---|---|---|
| `playlist.update` (patch_playlist: name/desc/viewport/transition/duration/playback/refresh) | **INCLUIR** | gap real provado (doc 08 §6); typed op nova sobre `UpdatePlaylistBody` |
| `playlist.activate/deactivate` | **INCLUIR** | lifecycle natural; endpoints existem |
| `slide.duplicate` | **INCLUIR** | REST existe; typed op `duplicate_slide` |
| `section.reorder` | **INCLUIR** | REST existe; typed op `reorder_sections` |
| `media.list/get` + `slide_presets.list` (reads) | **INCLUIR** | leitura de contexto; binário/upload fora |
| `playlist.delete` | **CONDICIONADO À GOVERNANÇA DE EXCLUSÃO** | só entra após E1/E5 provarem consent artifact + echo; delete de recurso-topo é a operação mais destrutiva do domínio |
| `history.restore` | **ADIAR** | surface diz "never exposed" deliberadamente; precisa decisão própria com análise de blast radius |
| `templates` administrativos | **ADIAR** | fluxo editorial complexo (publish/archive/clone) |
| `import/export .mdd` | **ADIAR** | boundary de pacote, validação de payload — sub-projeto próprio |
| `public-url/qr/token`, `native-screens`, `validate-config` | **ADIAR** | baixa demanda provável; reavaliar depois |
| `shares/invites/ACL` | **EXCLUIR DO ESCOPO** | gestão de acesso é decisão humana por design; IA operando ACL cria superfície de escalada |

- **Status**: `NEEDS_APPROVAL` — cada INCLUIR precisa de ok do
  owner; CONDICIONADO depende de E1/E5; EXCLUIR é recomendação
  final da análise.

## D-7 — `get_context` com capabilities do usuário

- **Evidência**: SURI `get_my_context` + CAIO `commercial_capabilities`
  informam o escopo efetivo pós-AuthZ. VISTA hoje devolve catálogo
  estático igual para todos.
- **Recomendação**: **INCLUIR** — `get_context` devolve
  `principal` (tipo, não segredos), `effective_capabilities`
  (subset do catálogo permitido pelo RBAC do usuário — derivado de
  `PlaylistAccessService`/Core, nunca auto-declarado),
  `confirmation_model` e `agent_directives`. Read-only, aditivo.
- **Status**: `RECOMMENDED` — risco baixo; dados de permissão já são
  enforcement backend, expor o *subconjunto permitido* não vaza nada
  que o backend não vá negar.

## D-8 — `delete_data_model`: proposta de decisão ao owner (REVISADO)

- **Owner/contrato**: `presentation_ops_content.json` —
  `delete_data_model` declara `risk:"mutation"` +
  `confirmationPolicy:"direct"` (decisão registrada, doc 08 §9).
  O delete real executa no `PresentationPatchService` sobre
  `nativeConfig.dataModels[]`.
- **Análise de órfãos**: data models são alvo de bindings —
  `dataBinding.modelId` em blocks e referências `modelId` em
  visuals/cells (`binding_target_id` dual-read). Deletar um model
  com consumidores **órfa os bindings**: os blocos ficam sem
  resolução de dados (estado degradado, não erro visível imediato).
- **Estado/dependências a consultar no prepare**: (a) o model
  existe; (b) `blockIndex[]`/`dataBinding` consumers do `modelId`;
  (c) data_sources/transforms dependentes do `modelId`;
  (d) contagem de consumidores exposta no preview.
- **Autorização**: `require_playlist_access(edit)` — mesma dos
  demais ops; nenhuma política extra necessária.
- **Política de confirmação proposta**:
  | Condição | Política proposta |
  |---|---|
  | model sem consumidores | `direct` (atual — baixo risco real) |
  | model com ≥1 binding consumidor | `confirm` + preview lista consumidores + consent artifact obrigatório (D-5) |
  | consumidores indetermináveis | **bloqueio fail-closed** (`DEPENDENCY_UNRESOLVED`) — sem evidência, sem execução |
- **Efeito sobre consumidores**: o preview do prepare **deve
  enumerar** os bindings afetados (blockIds/slideIds) — o humano
  consentidor precisa ver o blast radius.
- **Testes negativos**: delete com consumidores sem consent →
  `CONFIRMATION_REQUIRED`; consent para model errado →
  `CONSENT_MISMATCH`; bindings resolvidos parcialmente → bloqueio.
- **Decisão para o owner**: aprovar política condicional acima
  (recomendado) OU declarar `direct` intencional e documentar
  aceitação do risco de órfãos. **Não implementar confirmação
  condicional por conveniência sem essa aprovação.**
- **Status**: `NEEDS_APPROVAL` — proposta entregue, decisão do
  owner pendente.

## D-9 — GPT Actions: novos opIds ou projeção sobre os existentes?

- **Opções**: (a) 6 opIds novos (`vista_get_context`, `vista_read`,
  `vista_analyze`, `vista_knowledge`, `vista_execute`,
  `vista_delete`) + deprecar 12 `gpt_*`; (b) manter 12 e não levar
  verbos ao Actions; (c) mapear verbos dentro dos opIds existentes.
- **Evidência**: parity gate prova 1:1 atual; orçamento de opIds
  importáveis (30) e envelope (100 KiB) favorecem 6; hosts GPT já
  entendem vocabulário fechado.
- **Recomendação**: **(a)** — 6 opIds semantic novos +
  12 `gpt_*` marcados `deprecated: true` no OpenAPI gerado.
  Actions e MCP convergem para o mesmo vocabulário — parity_map
  vira mapa 6↔6 (ou desaparece, se nomes MCP = opIds sem prefixo).
- **Status**: `RECOMMENDED`.

## D-10 — Auditoria por canal

- **Evidência** (doc 08 §3): história persiste actor+provenance+
  revision; `gpt_commit.verify` logs estruturados; **falta
  atribuição de canal** (editor/MCP/Actions).
- **Recomendação**: **INCLUIR na fase 2** — estender
  `TECHNICAL_PROVENANCE_CODES` ou campo `channel` no registro de
  história (valores: `editor`/`mcp`/`gpt_actions`); o write service
  já recebe contexto — propagar transporte até o reason. Barato,
  fecha forense por canal.
- **Status**: `RECOMMENDED`.

## Matriz de status

| Decisão | Recomendação | Status |
|---|---|---|
| D-1 | Coexistência 6+12 | RECOMMENDED |
| D-2 | Estender capability_surface | RECOMMENDED |
| D-3 | execute phase+operations[] | RECOMMENDED |
| D-4 | delete dedicada (mesmo mecanismo) | RECOMMENDED |
| D-5 | Consent artifact por transporte + echo como target-check | RECOMMENDED* |
| D-6 | Programa A/B; blocos por classificação | NEEDS_APPROVAL |
| D-7 | get_context autenticado | RECOMMENDED |
| D-8 | confirm condicional por consumidores | NEEDS_APPROVAL |
| D-9 | 6 opIds novos + deprecar gpt_* | RECOMMENDED |
| D-10 | provenance por canal | RECOMMENDED |

\* D-5 RECOMMENDED condicionado à aprovação do mecanismo de
consent challenge backend-mediado (reuso padrão CLARA) — decisão
de segurança do owner.

## Tabela de decisões (owner gates)

| DECISION | CURRENT STATUS | REQUIRED EVIDENCE | OWNER | PROPOSED RESOLUTION | IMPLEMENTATION GATE |
|---|---|---|---|---|---|
| D-1 coexistência | RECOMMENDED | ADR supersession aprovada | tv-dashboard-api arch | 6 novas + 12 deprecated | E0 |
| D-2 surface estendido | RECOMMENDED | — | tv-dashboard-api | campos semantic no modelo neutro | E2 |
| D-3 execute contract | RECOMMENDED | contrato revisado doc 10 §5 | tv-dashboard-api | phase+operations[] facade | E4 |
| D-4 delete dedicada | RECOMMENDED | — | tv-dashboard-api | tool delegando ao envelope | E5 |
| D-5 consent model | RECOMMENDED* | aprovação de segurança do consent challenge | security + tv-dashboard-api | consent artifact (elicit/challenge) + echo | E1 — **bloqueia E5** |
| D-6 expansão | NEEDS_APPROVAL | ok do owner por bloco | tv-dashboard-api product | tabela Programa B | E6 |
| D-7 get_context | RECOMMENDED | — | tv-dashboard-api | caps derivadas AuthZ | E2 |
| D-8 delete_data_model | NEEDS_APPROVAL | decisão do owner sobre política condicional | tv-dashboard-api domain | confirm c/ consumidores | E1 |
| D-9 opIds novos | RECOMMENDED | — | tv-dashboard-api | 6 vista_* + deprecar | E3-E5 |
| D-10 audit canal | RECOMMENDED | — | tv-dashboard-api | channel na provenance | E8 |
| ADR supersession | **PROPOSED** | aprovação formal | architecture board | doc 13 §6 texto-proposta | E0 — **bloqueia tudo** |
