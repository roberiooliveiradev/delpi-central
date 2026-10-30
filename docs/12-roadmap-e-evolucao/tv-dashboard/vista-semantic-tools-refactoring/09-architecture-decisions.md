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
  `proposal_handle?`, `idempotency_key`, `confirmation?`.
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

## D-5 — Confirmação verificável

- **Problema**: `confirmation=true` é afirmado pelo modelo — não é
  prova de humano.
- **Opções**: (a) `target_echo` no payload (host exige o humano
  redigitar o ID do alvo); (b) `ctx.elicit` quando o host suporta
  (EVA); (c) proposal echo — o commit deve repetir um campo do
  preview que só o humano que viu o diff conhece.
- **Evidência**: EVA já opera `target_echo`+elicit; MCP elicit é
  por-host (doc 08 §7); GPT Actions não têm elicit → `target_echo`
  é o único mecanismo transport-neutral disponível em ambos.
- **Recomendação**: **`target_echo` obrigatório para ops `confirm`**
  — o commit deve carregar o identificador exato do alvo
  (slideId/sectionId/blockId) que o preview exibiu; `ctx.elicit`
  adicional quando o host MCP suportar (bonus, não requisito).
  Mismatch → `CONFIRMATION_MISMATCH` 409. `confirmation=true`
  torna-se redundante e pode ser removido depois — **a prova é o
  echo, não o booleano**.
- **Status**: `RECOMMENDED` — quick win de segurança, independente
  da convergência (pode ir antes das 6 tools).

## D-6 — Escopo de expansão de capabilities (Programa B)

- **Decisão por bloco** (detalhe em doc 11 E6):
  | Bloco | Recomendação |
  |---|---|
  | `playlist.update` (name/desc/viewport/transition/duration/playback/refresh) | **INCLUIR** — typed op `patch_playlist` nova; gap real e frequente |
  | `playlist.delete` | **INCLUIR como confirm** — typed op `delete_playlist`; coerente c/ deleções existentes |
  | `playlist.activate/deactivate` | **INCLUIR** — typed ops direct; lifecycle natural |
  | `playlist.duplicate` | **ADIAR** — sem typed op; avaliar demanda |
  | `history.restore` | **DECISÃO OWNER** — surface hoje diz "never exposed" deliberadamente |
  | `media list/get` (read) | **INCLUIR read** — útil p/ contexto de assets; upload/binário fora |
  | `slide.duplicate` | **INCLUIR** — typed op `duplicate_slide` |
  | `section.reorder` | **INCLUIR** — typed op `reorder_sections` |
  | `slide-presets list` | **INCLUIR read** — presets já insumo de `add_slide_from_preset` |
  | `templates` (além de apply) | **ADIAR** — fluxo editorial complexo; avaliar após núcleo |
  | `export/import (.mdd)`, `public-url/qr`, `shares/invites` | **EXCLUIR** — gestão de acesso/exportação: decisão humana por design |
  | `validate-config`, `native-screens` | **ADIAR** — baixa demanda provável |
- **Status**: `NEEDS_APPROVAL` — cada bloco INCLUIR precisa de ok do
  owner; EXCLUIR é recomendação minha.

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

## D-8 — `delete_data_model` confirmationPolicy

- **Evidência** (doc 08 §9): `risk=mutation`+`direct` é declarado,
  mas pode órfanar bindings.
- **Recomendação**: **owner-review** — propor `confirm` **quando o
  model tem consumidores** (bindings ativos); `direct` quando órfão.
  Política condicional por estado, implementável no preview (o
  prepare já sabe contar consumidores). Sem aprovação, manter
  `direct` — não mudar unilateralmente.
- **Status**: `NEEDS_APPROVAL`.

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
| D-5 | target_echo + elicit opcional | RECOMMENDED |
| D-6 | Blocos incluir/ad iar/excluir | NEEDS_APPROVAL |
| D-7 | get_context autenticado | RECOMMENDED |
| D-8 | confirm condicional por consumidores | NEEDS_APPROVAL |
| D-9 | 6 opIds novos + deprecar gpt_* | RECOMMENDED |
| D-10 | provenance por canal | RECOMMENDED |
