# 06 — Refactoring Gap Analysis

Formato: `SYMPTOM → EVIDENCE → ROOT_CAUSE (PROVEN|INCONCLUSIVE) → OWNER →
CONTRACT → EXISTING_EQUIVALENT → REUSE_DECISION → RISK`.

## G-01 — Crescimento por tool: cardinalidade 1:1 tool↔operação

- **SINTOMA**: cada nova capability VISTA exige nova MCP tool + novo
  GPT Action + entrada no parity_map + schema próprio; 12 tools hoje.
- **EVIDÊNCIA**: `tool_bridge.py` (12 métodos), `server.py` (12
  `@mcp.tool()`), `GPT_ACTIONS_OPERATION_IDS` (12 ids), parity_map em
  `vista_agent_intelligence.json`.
- **ROOT_CAUSE**: **PROVEN — decisão arquitetural registrada**
  (ADR item 8 recusa superfície CRUD de entidades; item 4 separa
  typed ops de Actions). Não é acidente; é trade-off deliberado de
  discoverability por tool vs. estabilidade de superfície.
- **OWNER**: tv-dashboard-api (architecture authority: ADR +
  capability matrix).
- **CONTRACT**: `capability_surface.py` (neutral model) +
  `GptActionsDispatchService` (dispatch único).
- **EXISTING_EQUIVALENT**: YES — CAIO/EVA `SemanticAction` registry
  + `delpi_mcp` substrate comprovam o padrão alternativo no mesmo
  monorepo.
- **REUSE_DECISION**: EXTEND — adicionar projeção semântica sobre o
  dispatch existente, não engine nova.
- **RISCO**: supersession do ADR item 8 precisa mostrar que o registry
  fechado preserva a razão da decisão original (anti generic-CRUD).

## G-02 — `delete_data_model` com `confirmationPolicy=direct`

- **SINTOMA**: uma deleção de recurso (data model) não exige
  confirmação enquanto delete_block/section/slide exigem `confirm`.
- **EVIDÊNCIA**: `presentation_ops_content.json` — 3 ops `confirm`
  (`delete_block`, `delete_section`, `delete_slide`);
  `delete_data_model` não consta entre elas.
- **ROOT_CAUSE**: **PROVEN (revisado)** — decisão **declarada** no
  catálogo: `risk:"mutation"` + `confirmationPolicy:"direct"` (não é
  omissão nem drift). Porém pode órfanar bindings; recomendada
  revisão do owner — política condicional por consumidores (D-8).
- **OWNER**: tv-dashboard-api (typed op catalog authority).
- **CONTRACT**: `confirmationPolicy` por op no catálogo canônico.
- **EXISTING_EQUIVALENT**: — (não é gap de implementação).
- **REUSE_DECISION**: — (decisão de política do owner — D-8
  `NEEDS_APPROVAL`; mudança = 1 linha de metadata).
- **RISCO**: MEDIO — deleção silenciosa via proposal direta pode
  órfanar bindings; mitigação atual = envelope prepare/commit ainda
  mostra diff.

## G-03 — Confirmação declarada pelo modelo, não provada pelo humano

- **SINTOMA**: `confirmation=true` no commit é afirmado pelo
  LLM/host; não há prova verificável de ação humana.
- **EVIDÊNCIA**: `commit_service.py` (campo `confirmation` booleano);
  comparação: EVA `_DestructiveConfirmation{confirm, target_echo}`
  via `ctx.elicit()` (`engineering_app/interface/mcp/semantic_bridge.py:115-198`);
  CAIO sealed prepare→commit com claim atômico.
- **ROOT_CAUSE**: **PROVEN** — o mecanismo foi desenhado antes do
  padrão de elicitation/echo; o envelope (proposal opaco, single-use,
  actor-bound) já garante que *alguém* preparou e revisou, mas a
  prova não vincula *humano→commit*.
- **OWNER**: tv-dashboard-api; substrato `delpi_mcp` suporta
  elicitation (EVA já usa no mesmo shared transport).
- **CONTRACT**: `commit_proposal` input schema (`confirmation`).
- **EXISTING_EQUIVALENT**: YES — EVA elicitation; CAIO
  `claim_valid_proposal`.
- **REUSE_DECISION**: REUSE (padrão EVA) — aditivo no schema de
  commit para ops `confirm`; não quebra envelope existente.
- **RISCO**: hosts MCP sem suporte a elicitation → resposta honesta
  `confirmation_unavailable` (comportamento EVA) em vez de fallback
  silencioso; precisa avaliar consumidores (ver 07).

## G-04 — Proposal store in-process (single-replica only)

- **SINTOMA**: handles opacos vivem em memória; restart/replica
  múltipla invalida proposals em voo.
- **EVIDÊNCIA**: `proposal_store.py` + documentação
  `ACCEPT_WITH_RESIDUAL` (single-replica assumido).
- **ROOT_CAUSE**: **PROVEN — residual aceito e documentado.**
- **OWNER**: tv-dashboard-api.
- **CONTRACT**: proposal lifecycle (mint/validate/claim/consume).
- **EXISTING_EQUIVALENT**: YES — `ClaraProposalRepository` (Postgres,
  controllership-finance-api); CAIO lock+store (mesmo modelo
  in-process).
- **REUSE_DECISION**: EXTEND — abstrair store atrás de interface e
  oferecer implementação persistida quando runtime crescer para
  multi-replica. Não urgente hoje.
- **RISCO**: BAIXO no runtime atual (documentado); ALTO se escalar
  réplicas sem migrar antes.

## G-05 — VISTA não responde "quem sou eu / o que posso"

- **SINTOMA**: nenhuma tool devolve identidade + capabilities
  efetivas do usuário autenticado; `get_catalog` devolve o catálogo
  *estático* (mesmo para todos, módulo AuthZ no backend).
- **EVIDÊNCIA**: `get_catalog` → `build_capability_surface` (estático);
  SURI `get_context` inclui contexto do usuário; CAIO `get_context`
  inclui `commercial_capabilities` do usuário.
- **ROOT_CAUSE**: **PROVEN** — capability surface é declarativo;
  user-parity é enforcement backend, nunca foi projetada para
  *informar* o usuário do seu escopo efetivo.
- **OWNER**: tv-dashboard-api + Core (fonte de permissões).
- **CONTRACT**: catálogo (capability surface projection).
- **EXISTING_EQUIVALENT**: YES — SURI `tool_get_my_context` /
  `get_context`; CAIO `commercial_capabilities`.
- **REUSE_DECISION**: EXTEND — adicionar bloco opcional
  `principal_capabilities` na projeção (AuthZ-derived, nunca
  auto-declarado) ou tool/contexto dedicado em refatoração semântica.
- **RISCO**: BAIXO (read-only, aditivo) — mas dados de permissão
  passam a vazar no payload; verificar política de exposição
  (fail-closed já protege no backend independentemente).

## G-06 — Capabilities backend fora do alcance da VISTA

- **SINTOMA**: ~15 grupos de endpoints REST sem caminho semântico:
  playlist update/delete/activate/duplicate/export/import/shares/
  invites, history restore, slide duplicate, section reorder, media,
  templates CRUD/publish, presets listing, validate-config,
  native-screens.
- **EVIDÊNCIA**: matriz em `03-capability-mapping.md`.
- **ROOT_CAUSE**: **PROVEN — escopo deliberado histórico**:
  capability surface foi construída para "criar/editar painel via
  typed ops"; lifecycle administrativo ficou no editor humano.
- **OWNER**: tv-dashboard-api.
- **CONTRACT**: REST routes (já existentes) + typed ops catalog.
- **EXISTING_EQUIVALENT**: YES para cada item (o backend já executa
  via REST/editor); NÃO existe equivalente *semântico*.
- **REUSE_DECISION**: EXTEND — cada gap é aditivo: novo typed op ou
  novo handler read no dispatch, com ADR por item. Nenhum precisa de
  engine nova.
- **RISCO**: expandir semântica para shares/invites/ACL toca gestão
  de permissões — candidato a exclusão deliberada (manter humano).

## G-07 — `data_model_lifecycle` como analysis entry com 5 write ops

- **SINTOMA**: 5 typed ops de data-model estão descritos dentro de
  uma entrada `ANALYSIS` do capability surface, não no workflow
  `presentation_change`.
- **EVIDÊNCIA**: `capability_surface.py` — entry
  `data_model_lifecycle` class ANALYSIS com `typed_ops` write.
- **ROOT_CAUSE**: **INCONCLUSIVE** — provavelmente decisão de
  agrupamento (data-model ops são destrutivas/técnicas, separadas do
  fluxo de conteúdo), mas a classificação ANALYSIS com write_ops é
  semanticamente ambígua — `CONTRACT_DRIFT` leve.
- **OWNER**: tv-dashboard-api.
- **CONTRACT**: capability surface classification.
- **EXISTING_EQUIVALENT**: —.
- **REUSE_DECISION**: EXTEND — reclassificar ou documentar a
  exceção na refatoração semântica (registry `SemanticAction` resolve
  isso naturalmente com `risk`/`kind` por entrada).
- **RISCO**: BAIXO (metadado).

## G-08 — Ausência de execução de data route como análise

- **SINTOMA**: VISTA não oferece análise/insight sobre dados — o
  que existe é execução crua de rota via preview de bloco.
- **EVIDÊNCIA**: `TvDataPreviewService.preview_block`
  (`tv_data_preview_service.py:44`) delega a
  `SlideDataResolutionService` — o mesmo pipeline de resolução do
  player, com `authorization`/`force_refresh`/defaults propagados.
  Preview **executa a rota real** e devolve dados resolvidos.
  Rotas `/m/*` e `validate-config` existem fora da superfície.
- **ROOT_CAUSE**: **PROVEN (revisado)** — o acesso ao dado existe;
  a limitação real é ausência de camada de análise homologada
  (agregações, KPIs, facts rotulados), não de execução de rota.
- **OWNER**: tv-dashboard-api.
- **CONTRACT**: data routes allowlist (`tv_data_routes.json`, 545).
- **EXISTING_EQUIVALENT**: YES — `preview_data_block` cobre "ver os
  dados"; análise/insight tipo SURI `analyze` não existe.
- **REUSE_DECISION**: EXTEND — se fase 2 quiser `analyze`, modelar
  como analysis homologada sobre o preview existente (facts
  FACT/CALCULATION/RECOMMENDATION, padrão SURI).
- **RISCO**: MEDIO — análise de dados operacionais por IA pede
  rótulos de evidência (padrão SURI knowledge/analyze).

## G-09 — Sem status honesto de capability não-implementada

- **SINTOMA**: catálogo VISTA não expõe `planned`/`not_implemented`;
  consumidor descobre pela ausência ou por erro.
- **EVIDÊNCIA**: capability_surface não tem campo status; CAIO
  `SemanticAction.status` = proven|planned|not_implemented (501
  honesto no dispatch).
- **ROOT_CAUSE**: **PROVEN** — modelo de superfície não prevê
  estado de implementação.
- **OWNER**: tv-dashboard-api.
- **CONTRACT**: capability surface projection.
- **EXISTING_EQUIVALENT**: YES — CAIO/EVA registry.
- **REUSE_DECISION**: REUSE — campo `status` por capability no
  modelo neutral; barato e evita descoberta por erro.
- **RISCO**: BAIXO (aditivo).

## G-10 — Auditoria/observabilidade de commits MCP não comprovada

- **SINTOMA**: não há evidência de trilha de auditoria dedicada a
  writes via MCP/Actions comparável a CLARA (`mcp/clara` audit +
  consent challenges persistidos).
- **EVIDÊNCIA**: inspeção de `commit_service.py`/`dispatch_service.py`
  não revelou audit trail dedicado (há eval telemetry
  `test_vista_eval_telemetry.py`, que é quality harness, não audit).
- **ROOT_CAUSE**: **PROVEN (revisado, doc 08 §3)** — auditoria de
  domínio **existe**: playlist history persiste `authorName` +
  `reason` (proveniência allowlisted) + revision por mutação, e
  `gpt_commit.verify` emite logs estruturados com actor/client/op/
  revisions. Gap residual real: **sem atribuição de canal**
  (`presentation_mutation` não distingue editor vs MCP vs Actions).
- **OWNER**: tv-dashboard-api + platform observability.
- **CONTRACT**: `TECHNICAL_PROVENANCE_CODES` + history schema.
- **EXISTING_EQUIVALENT**: YES — CLARA audit_trail (mais rica).
- **REUSE_DECISION**: EXTEND — adicionar `channel` à provenance
  (D-10, barato: o write já recebe contexto de transporte).
- **RISCO**: BAIXO-MEDIO — forense por canal indisponível hoje;
  conteúdo e ator já são auditados.

## Duplicações identificadas

| Duplicação | Natureza | Avaliação |
|---|---|---|
| parity_map (intelligence JSON) ↔ capability_surface (código) | metadado repetido | **mantida por design** — map é a ponte declarativa; surface é a fonte; drift possível → gate de teste existe? TO_INVENTORY |
| `suggest_change` (determinístico) ↔ `builder/sessions` (NL REST) | dois caminhos NL→ops | boundary conhecida: builder é UI wizard; suggest é tool. Não duplicam execução — ambos convergem ao typed ops. **OK** |
| `gpt_*` opIds ↔ MCP tool names | nomes paralelos | por design (transport projection); convergência semântica pode unificar nomes |
| EVA: domain tools + semantic tools coexistindo | mesmo consumidor, duas surfaces | **precedente para migração progressiva VISTA** — não é problema, é padrão de transição |
