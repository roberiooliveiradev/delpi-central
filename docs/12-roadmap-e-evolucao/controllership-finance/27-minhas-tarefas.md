# 27 — Minhas Tarefas

## Estado

**TARGET / PROJECTION_CONTRACT_REQUIRED**

## Objetivo

**Minhas tarefas** é a projeção pessoal das responsabilidades do usuário dentro do Portal Controladoria & Finanças.

```text
Minhas tarefas
= projection of existing work
!= new workflow
!= new business owner
```

## Rota lógica

```text
/apps/controllership-finance/my-tasks
```

Permission: `controllership-finance.access`.


## Reuso obrigatório de `@delpi/plugin-ui`

O chrome de Minhas tarefas já existe no kit e deve ser reutilizado.

Import canônico:

```ts
import {
  TaskWorkspacePage,
  TaskWorklistSection,
  TaskItemsTable,
  TaskSearchField,
  TaskEmptyState,
  TaskEditorFrame,
  buildTaskWorkspaceHighlights,
} from "@delpi/plugin-ui/index";
```

Estilos/runtime:

```ts
await import("@delpi/plugin-ui/styles");
```

Responsabilidade do Portal:
- produzir o `TaskProjection`;
- mapear os itens para a apresentação esperada pelo kit;
- preservar deep links;
- chamar o use case/owner correto ao agir;
- controlar AuthZ e estados parciais.

Responsabilidade do kit:
- workspace/chrome;
- busca;
- lista/tabela;
- seção de worklist;
- empty state;
- editor frame/presentation helpers.

**DO NOT RECREATE:** task workspace, task table, task search, worklist chrome ou empty state de tarefas.

## Fontes de tarefas

A página deve compor trabalho já existente nas páginas owners, por exemplo:
- checklist/documento que depende do usuário;
- validação atribuída;
- pendência atribuída;
- correção estrutural que requer atuação;
- esclarecimento ligado a pacote;
- futuras responsabilidades aprovadas do Portal.

Cada item deve preservar o owner original.

## Modelo conceitual

```text
TaskProjection
├── sourceType
├── sourceId
├── title
├── status
├── responsibility
├── context
├── pendingSince
├── sourceFreshness
└── deepLink
```

`TaskProjection` é read-model/projeção; não é necessariamente entidade persistida.

## Invariantes

- concluir item em Minhas tarefas deve executar o caso de uso do owner, não criar estado paralelo;
- remover item da lista sem mudar o owner não significa conclusão;
- source indisponível não vira lista vazia silenciosamente;
- `PENDING_SINCE` pode existir como idade factual;
- sem SLA/due/overdue enquanto não houver decisão formal;
- permission permanece `access`, sem código por tipo de tarefa.

## Composição lógica

```text
TaskHeader
→ TaskFilters
→ TaskSummary
→ TaskList
→ TaskDetailOrDeepLink
→ ContextualHelp
```

## Filtros

Podem existir quando suportados: tipo, status, período, contexto e responsabilidade.

Não criar filtro de filial como permission.

## Ação

Preferência: deep link para a página owner com contexto preservado.

A página pode oferecer ação inline somente quando o mesmo caso de uso/contract do owner é reutilizado, AuthZ server-side permanece no owner/BFF e a UX não mascara requisitos do processo.

## Estados

Cobrir `LOADING`, `EMPTY` real, `PARTIAL`, `UNAVAILABLE_SOURCE`, `ERROR`, `FORBIDDEN` e `NOT_FOUND` no deep link.

`EMPTY` só pode significar ausência real de tarefas quando todas as fontes necessárias foram avaliadas com sucesso.

## Freshness

Cada projeção deve permitir saber quando foi calculada/recebida quando o dado puder ficar defasado.

## Help

Explicar origem das tarefas, por que algo aparece, como concluir no contexto correto, diferença entre pendência e tarefa, ausência de SLA formal e estados parciais/indisponíveis.

## Inventário obrigatório

Antes de implementar:
- identificar producers de tarefas em P2/P4/P5;
- definir contract de projeção;
- definir se composição é on-read, materialized read-model ou evento;
- verificar padrão de Minhas tarefas em Comercial/Suprimentos;
- evitar duplicação de estado ou regra.

A estratégia física é decisão de arquitetura após inventário.
