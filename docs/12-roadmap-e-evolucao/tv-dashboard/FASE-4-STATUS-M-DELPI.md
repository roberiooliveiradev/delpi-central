# Fase 4 — Workbench M no frontend

**Status:** concluída em 2026-07-16
**Baseline:** `deb172a94`

## Resultado

O editor **Preparar dados** agora possui uma arquitetura M server-driven em
`plugins/tv-dashboard/src/features/data-query/{domain,data,state,ui}`. O
`DataPrepareModal` público é um compositor de rollout: só ativa o workbench M
quando a API entrega `enabled=true` e `writeV2Enabled=true`; caso contrário,
mantém a experiência v1 sem escrita acidental de v2.

## Contratos

- `GET /data/m/capabilities`: capabilities e flags efetivas.
- `POST /data/m/mutate`: `convert_legacy`, `insert_step`,
  `replace_step_expression`, `rename_step`, `move_step`, `remove_step`,
  `rename_query` e `format_script`.
- `POST /data/m/compile`: fórmulas M reais por etapa, diagnósticos com range.
- `POST /data/preview-block`: `targetStepName`, schema tipado, nulabilidade e
  metadados de amostra.
- contexto do editor `updateBlocksAtomically`: patches de várias consultas em
  um único `nativeConfig`, snapshot de histórico, autosave e evento WS.

O frontend não concatena nem interpreta M. `dataTransformFormula.ts` permanece
somente como fixture/compatibilidade da biblioteca; saiu do caminho runtime do
MFE. A barra v1 fica somente leitura e a barra v2 envia texto ao endpoint de
mutação.

## Transação

Ao abrir, cada `sourceId` recebe um draft independente. Mutação e preview só
alteram o draft. Cancelar, X e Escape do modal descartam o estado sem chamar o
contexto editorial. **Fechar e aplicar** valida todas as consultas dirty e
envia uma única lista de patches ao comando atômico.

Seleção de etapa é sempre `selectedStepName`; índices existem apenas como
posição transitória do comando de reorder.

## UI compartilhada

`DataTable` ganhou modo genérico `grid-preview`, índice opcional, prefixo de
cabeçalho, seleção de coluna e eventos de header/célula com teclado. A grade do
workbench usa o componente; não foi criado `DataGrid`. CSS visual permanece em
`plugin-ui`, com dual-class e tokens.

## Testes

- backend compile/mutate/API e execução Fase 3;
- transação multi-consulta com commit único e bloqueio em diagnóstico;
- resposta concorrente ignorada e `AbortController`;
- seleção por nome após alteração;
- barra fx Enter/Escape e diagnóstico linha/coluna/código;
- eventos, seleção, índice, ARIA e teclado do `DataTable`;
- build do `plugin-ui`.

O typecheck global do TV Dashboard continua bloqueado por erros anteriores à
Fase 4 em `plugin-ui`, `tv-dashboard-presentation` e componentes legados. Os
testes direcionados da fase estão verdes; esse passivo está fora do contrato M
e deve ser tratado antes de tornar o gate global obrigatório.

## Rollout e riscos

- As flags seguem `false` por padrão; não há escrita v2 em produção sem
  ativação explícita.
- `move_step` preserva referências e é rejeitado pelo compilador se a nova
  ordem violar o DAG.
- O editor avançado e novas operações de coluna permanecem na Fase 5/6.
- A UX v1 fica disponível durante a janela dual-read; sua barra pseudo-M não é
  mais editável.
