# Changelog — apresentação delivered puro (jun/2026)

## Resumo

Corte definitivo do pipeline rico legado. Toda metadata de `execute_external_action` passa por **schema-first as-delivered**.

## Código

- `ChatPresentationMetadataPipelineService` — delegação única a `ChatPresentationApiDeliveredMetadataService` (~35 linhas).
- `ChatDataInsightEnrichmentService` re-ligado no caminho as-delivered (`dataAnswer` / `dataCommentary`).
- `ChatToolContextFormatService` e `ChatPresentationPrimaryViewService` — `ChatSchemaDrivenPresentationService.build_bundle` (sem visual bundle).
- **Removidos** 12 módulos: visual bundle, table assembly, humanized narrative, composite visual, entity route dispatch, hierarchy tree, story, prose quality, dashboard assembly, profile text/visual builders.

## Presenters

Pasta `external_actions/presenters/` reduzida a hosts utilitários (SQL, KPI, operational table, content). Sem presenters por entidade.

## Documentação

- Novo: `docs/architecture/presentation-delivered-pure-jun2026.md`
- Atualizados: playbook-22, chat-assistant-content-presentation, chat-intelligence-base, guia-desenvolvimento, índices
- Regra Cursor: `.cursor/rules/schema-first-presentation-delivered.mdc`

## Testes

- Casos de qualidade operacional alinhados ao contrato as-delivered.
- `test_chat_presentation_data_only_pipeline.py` — skipped (flags legacy; revalidar no turn completion).

## Pendente (Fase 2+)

- Limpar `visualBuilders` / `tableAssembly` / `richStackProfiles` de `presentation_profiles.json`.
- Slim `ChatPresentationDecisionService` e `tailVisualPolicy` no render.
- `dataAnswer` para `structure_exclusivity` e demais perfis sem commentary.
