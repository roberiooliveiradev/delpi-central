# ADR 003 — Textos de UI em JSON

**Status:** Aceito (jun/2026)

## Contexto

Strings PT-BR espalhadas em presenter, selection e turn prep dificultavam edição sem deploy e geravam inconsistência entre send/stream e MFE.

## Decisão

Textos exibidos ao usuário ficam em `app/content/pt-BR/assistant/*.json`, carregados por serviços de conteúdo (`ChatAssistantContentService`, `ExternalActionResponseContentService`, `ChatTurnPreparationContentService`, …). Regex, heurísticas e formatação numérica permanecem em Python.

Gate CI (ADR 006) bloqueia **novas** strings em caminhos protegidos (presenters, selection, content services).

## Consequências

- Catálogo: [`assistant-content-catalog.md`](../assistant-content-catalog.md).
- Presenter fatiado consome `presenter_content.json`, `column_labels.json`, `external_action_responses.json`.
- PRs que alteram copy devem atualizar bundle + baseline quando aplicável.
