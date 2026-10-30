# 04 — Semantic Tools Target Assessment

Avaliação do catálogo-alvo de 6 verbos como **hipótese de arquitetura
futura** — nada implementado.

## 1. Mapeamento tools atuais → verbos-alvo

| Verbo-alvo | Tools VISTA absorvidas | Comentário |
|---|---|---|
| `get_context` | `get_catalog` (+ novo: identity/capabilities do usuário) | VISTA hoje não devolve "quem sou eu / o que posso" — SURI/CAIO devolvem |
| `read` | `list_playlists`, `get_playlist_context`, `get_playlist_history`, `search_data_routes`, `inspect_data_model` | `(entity, action, ref, filters)` cobre todos |
| `analyze` | `preview_data_block`, `preview_data_model`, `suggest_change` | "análise" VISTA = preview/simulação de dados e materialização NL |
| `knowledge` | `get_product_guide` | mapping direto; corpus VISTA precisa de citações verificáveis (padrão SURI) para paridade |
| `execute` | `prepare_change` + `commit_proposal` (e `commit_now` no Actions) | **não é 1:1** — ver §3 |
| `delete` | (não existe como tool; 3 typed ops `confirm`) | precisaria nascer como tool dedicada ou ficar dentro de execute/prepare |

## 2. Avaliação por verbo

### `get_context`
- **Agruparia**: get_catalog; identity/effective capabilities (ausente
  hoje); agent_directives; honest status de capabilities planned.
- **Contrato recomendado**: `{action: context|catalog}`, retornando
  identidade do assistente, catalog_version, semantic_tools,
  entities/actions disponíveis, capabilities efetivas do usuário
  (pós-AuthZ), confirmation_model, planned/not_implemented honestos.
- **Reuse**: `GptActionsDispatchService.get_catalog` +
  `capability_surface.build_capability_surface` já produzem ~80% do
  payload; falta bloco `user capabilities` (SURI `tool_get_my_context`
  é o modelo) e `status` por capability (padrão `SemanticAction`).
- **REUSE_DECISION: EXTEND**.

### `read`
- **Agruparia**: as 6 tools READ atuais.
- **Contrato recomendado**: `entity` ∈ {playlist, playlist_history,
  data_route, data_model, product_guide?}; `action` ∈
  {list, get, context, history, search, inspect}; `ref`, `filters`,
  `pagination`, `projection`.
- **Registry**: cada (entity,action) → handler existente no
  dispatch_service — os métodos já existem; o registry seria
  metadado declarativo, não código novo.
- **Risco**: `get_playlist_context` tem contrato rico (contexto do
  slide/bloco selecionado) — modelar como `playlist.context` com
  `ref`+`filters` é natural.
- **REUSE_DECISION: REUSE** (handlers) + **EXTEND** (registry).

### `analyze`
- **Agruparia**: preview_data_block, preview_data_model,
  suggest_change; futuras análises de playlist (saúde do painel,
  cobertura de dados).
- **Contrato recomendado**: `analysis_type` ∈
  {data_block_preview, data_model_preview, intent_materialization}
  (+ espaço para `playlist.summary`/`playlist.quality` futuros);
  `subject_refs`, `parameters`.
- **Particularidade VISTA**: previews **executam a rota real**
  (SlideDataResolutionService — ver 05 Caso C) — são análises
  "what-if" sobre dados vivos, não leituras.
- **REUSE_DECISION: REUSE**.

### `knowledge`
- **Agruparia**: `get_product_guide` + conteúdo estático
  (`/content/ui`, presets docs).
- **Gap**: corpus VISTA (`ProductGuideRegistry`) retorna bodies sem
  citação de fonte/locator; SURI `suri_knowledge.json` tem
  `source+locator+evidence_class`. Para paridade, o registry
  precisaria de campos de citação.
- **REUSE_DECISION: EXTEND**.

### `execute` — o ponto delicado
- VISTA **já é** um executor composto governado: `ops[]` de typed
  ops + PlanCompiler dentro de um envelope PREPARE→COMMIT.
  O modelo semântico `execute(entity, action, payload)` (CAIO) ou
  `execute(entity, action, operations[])` (SURI) cobriria isso como:
  - `execute(entity=presentation, action=apply_mutation,
    operations=[typed_ops...])` — 1 entrada de registry com o
    vocabulário de 32 ops no payload; ou
  - `execute(entity=slide, action=create/delete/...)` — 1 entrada por
    typed op (32 entradas) com `target_ref`/`payload` unificados.
- **Decisão arquitetural pendente** (P2): manter envelope
  PREPARE→COMMIT interno (governed) e expor `execute` como facade
  que roda PREPARE internamente + COMMIT quando política=direct.
  CAIO prova que "executa direto quando autorizado" convive com
  AuthZ backend — para VISTA a fronteira não é AuthZ simples: o
  PREPARE também produz diff/preview/risk que o usuário pode querer
  ver antes. Manter o two-phase **dentro** de `execute` via
  `phase: prepare|commit` (padrão CAIO delete) preserva a semântica
  sem expor duas tools.
- **REUSE_DECISION: EXTEND** (facade sobre o fluxo governado real).

### `delete`
- VISTA hoje **não tem** tool delete dedicada — deleções são typed
  ops `confirm` dentro do envelope comum.
- Opções: (a) tool `delete` dedicada com sealed prepare→commit
  (padrão CAIO) + elicitation (padrão EVA) para os 3 ops confirm;
  (b) manter dentro de `execute`/`prepare` com `phase` e
  confirmação verificável.
- O modelo VISTA atual (confirmação via `confirmation=true`
  declarado) é **mais fraco** que CAIO/EVA — converge à prova
  verificável independentemente da forma da superfície.
- **REUSE_DECISION: NEW tool + REUSE do mecanismo** (ou EXTEND do
  prepare/commit existente — decisão P2).

## 3. Restrições de transporte (avaliadas separadamente)

- **MCP**: 6 tools são viáveis — CAIO/EVA provam. Schemas por-tool
  com Literals fechados funcionam.
- **GPT Actions**: o orçamento de ~100 KiB do envelope e o limite de
  operationIds importáveis (`platform_prefer_max: 30`) favorecem 6
  ops *também* no Actions — mas `commit_now` é mecânica Actions-only
  (capability_surface injeta só na projeção actions); no modelo de
  6 verbos, o single-shot seria `phase`/`commit_now` dentro do mesmo
  `execute` op. Viável.
- **Coexistência**: EVA prova que 6 semantic tools podem coexistir
  com domain tools legadas durante migração progressiva.
- **Contrato OpenAPI**: nomes novos = deprecar 12 `gpt_*` opIds →
  transição `ADDITIVE` primeiro (6 novas + 12 antigas marcadas
  deprecated) e `BREAKING` na remoção — ver 06.

## 4. O que NÃO muda (invariantes que o target deve preservar)

- Typed ops em `presentation_ops_content.json` = autoridade de
  mutação; `PresentationPatchService` = engine; `TvPresentationWriteService`
  = boundary. O verbo `execute` **despacha para**, não substitui.
- PlanCompiler + proposal opaque handles + read-back VERIFIED.
- Catalog informa; backend autoriza; `VISTA capability ≤ user capability`.
- `agent_directives` MCP-primary; Actions budget ≤100 KiB.
- Sem proxy genérico, SQL, HTTP arbitrário (ADR item 6) — o
  `(entity,action)` registry reforça exatamente isso.

## 5. Riscos do target

- **R-1**: esconder o PREPARE dentro de `execute` pode remover do
  host a etapa de revisão do diff — mitigar mantendo `phase=prepare`
  como saída de primeira classe com proposal + preview.
- **R-2**: `suggest_change` é um planner NL determinístico, não uma
  análise de dados — agrupar em `analyze` pode confundir hosts
  (classification `domain_intent_materialization` já é ANALYSIS no
  surface atual — coerente).
- **R-3**: ADR item 8 ("não adotar superfície de entidade tipo CRUD")
  — a convergência precisa de supersession documentada mostrando que
  o motivo de 2026 (anti generic-CRUD) é preservado pelo registry
  fechado + typed ops, não traído.
- **R-4**: compound plan (ops[] ordenado) não cabe naturalmente em
  `execute(entity, action)` singular — o modelo `operations[]` da
  SURI resolve; exige schema `operations: [{op, args, as, refs}]`.
