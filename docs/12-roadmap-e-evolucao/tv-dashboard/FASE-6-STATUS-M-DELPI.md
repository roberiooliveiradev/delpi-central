# Fase 6 — Editor avançado e produtividade M DELPI

**Status:** concluída em 2026-07-17
**Baseline:** `f26302751`

## Resultado

O workbench ganhou um editor multiline local baseado em
`NativeTextAreaControl`, sem Monaco, CodeMirror ou novo componente no
`plugin-ui`. O backend continua sendo a única autoridade da linguagem: compile
devolve tokens de realce e contexto de completions; o catálogo
`GET /data/m/functions` fornece assinatura, descrição, parâmetros e exemplos;
formatter e renames percorrem `POST /data/m/mutate`.

O editor só aparece quando `enabled`, `writeV2Enabled` e
`advancedEditorEnabled` estão ativos nas capabilities. As flags continuam
desligadas por padrão.

## Produtividade entregue

- realce lexical classificado pelo parser/lexer do backend;
- autocomplete de funções, etapas, colunas e consultas, sem parser M no browser;
- ajuda de assinatura, descrição e exemplo;
- formatação server-driven e idempotente;
- navegação de diagnostics por offsets/range, linha e coluna;
- rename de etapa e consulta com atualização de referências via AST no backend;
- DAG textual simples `consulta → dependência`, alimentado por
  `referencedQueries` do compile;
- busca de etapas;
- undo/redo limitado ao draft local; nenhum atalho chama histórico persistido;
- copiar/colar nativo do textarea;
- atalhos Ctrl/Cmd+Space, Ctrl/Cmd+Z, Ctrl/Cmd+Shift+Z, Ctrl/Cmd+Y,
  Ctrl/Cmd+Enter e Escape;
- foco, listbox/option, `aria-activedescendant`, navegação de diagnostics e
  fallback responsivo.

## Concorrência e persistência

Compile, preview e catálogo preservam `AbortController` e sequência de request.
Respostas antigas não sobrescrevem o draft atual. O script só alcança o bloco
persistido em **Fechar e aplicar**, pelo commit atômico já existente; Cancelar
continua descartando tudo.

## Testes

- backend: contexto de completion, tokens, formatter idempotente e rename por AST;
- frontend: autocomplete, assinatura, formatter, diagnostics, busca/rename de
  etapa, undo/redo, teclado, foco/ARIA, flag e CSS responsivo;
- gates locais: Vitest focado, CSS scope e Vite build direto.

O ambiente local desta execução não possui `pytest` nem `lark` globais e não
possui venv existente. Conforme a restrição da tarefa, nenhuma dependência ou
venv foi criada; os testes Python ficaram registrados para execução no CI.
