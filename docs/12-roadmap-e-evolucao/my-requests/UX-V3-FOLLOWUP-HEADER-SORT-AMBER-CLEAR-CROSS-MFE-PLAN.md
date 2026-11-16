# UX V3 — Follow-up P0: Header Sort + Clear Filters âmbar — My Requests × Helpdesk

**TASK_ID:** `CROSS-MFE-LIST-UXV3-HEADER-SORT-AMBER-CLEAR-PLUGIN-UI-HML-01`  
**Decisão PO:** APPROVED_VISUAL / IMPLEMENTATION_PLANNED em 16/11/2026.  
**Estado factual:** **IMPLEMENTED + HML_DEPLOYED em 16/11/2026** — implementação `30fba42e82` (+ spec `929291374a`) deployada em HML (plugin-ui `236faeb98152`, my-requests `5cda269028f3`); E2E autenticado 36/36 em 4 viewports. Helpdesk sem E2E visual (serviço ausente do compose HML + RBAC). **PRD: NOT_AUTHORIZED_THIS_PACKAGE** — gate devolvido à Coordination (ver relatório de execução).  
**Escopo de três telas em dois MFEs:** `/apps/my-requests/mine`, `/apps/my-requests/work-queue`, `/apps/helpdesk`. Owner de UI compartilhada: `@delpi/plugin-ui`; owners de ordenação são Requests API/PRC Engineering API e Helpdesk API conforme a fonte.

## 1. Fontes e decisão visual

- [UX V3 base](./UX-V3-CROSS-MFE-HERO-LOWER-RIGHT-TOOLBAR-WIREFRAME-AND-ROLLOUT.md) — hero compacto, busca → chips → toolbar inferior direita, page size na região da tabela.
- Prints PO de 16/11/2026 (Mine, Fila, Helpdesk, closeup do Helpdesk): **usar exatamente o ícone `FilterX` já existente no Helpdesk**, em **tom amarelo/âmbar** para destaque; não substituir por ícone genérico diferente.
- Implementação de referência identificada no repositório: `plugins/helpdesk/src/pages/HelpdeskPage.tsx` — `<HelpdeskIconButton aria-label="Limpar filtros" onClick={clearListFilters}><FilterX size={16} ... /></HelpdeskIconButton>` em `TicketListToolbar.trailing`. Está ao lado dos chips hoje; **mover para imediatamente à esquerda do botão Filtros da toolbar inferior direita**.
- My Requests: `plugins/my-requests/src/components/RequestListShell.tsx` dispõe de `columnSortMap`/sortableColumns e `headerSortDirection`; alcance real do sort é restrito pelo contrato da consulta (Mine combinada Requests + PRC; Work Queue requests-api). Não apresentar ícone clicável para campo sem suporte server-side.

## 2. Composição final (obrigatória) — três telas

```text
┌ HERO ───────────────────────────────────────────────────────────────────────┐
│ Título e ações autorizadas                                                  │
│ [ Busca dominante                                                       ]   │
│ Chips rápidos de status/escopo                                              │
│                     [FilterX âmbar] [Filtros] [Ordenar] [Colunas] [Tabela|Cards]│
└─────────────────────────────────────────────────────────────────────────────┘
┌ REGIÃO DA TABELA ───────────────────────────────────────────────────────────┐
│                                                  Itens por página [20 ▾]   │
│ Cabeçalhos ordenáveis (somente whitelisted, ícone, foco, aria-sort)         │
│ Linhas/cards reais, sem ordenação local de página paginada                  │
│ Resumo e navegação por páginas                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Ordem sem negociação:** `FilterX (Limpar filtros)` → `Filtros` → `Ordenar` → `Colunas` → `Tabela/Cards`. Ícone de limpeza **à esquerda do botão Filtros**, dentro da linha inferior direita do Hero, **não** na linha dos chips, **não** à direita da busca, **não** em uma segunda toolbar. Responsividade deve preservar ordem DOM/teclado e row-major. Remover link textual "Limpar tudo". Se Helpdesk ainda exibir chip "Meus chamados" repetido, investigar origem/scope e remover duplicação visual sem mudar filtro.

### 2.1 Componente canônico — Plugin UI

**Começar por inventário e Abstraction Gate:** verificar se já existe clear-filter action pública no Plugin UI, `IconButton`/factory e suporte à cor semântica. Se existir, estender/reusar; se faltar contrato neutro, generalizar a **ação visual** no owner Plugin UI com API pública reutilizável, exemplos/catálogo/testes. Nunca importar componente interno do Helpdesk em My Requests ou duplicar CSS. O ícone é `FilterX` (Lucide) como no Helpdesk, tamanho equivalente, botão quadrado/compacto, tema claro/escuro, foco/hover/disabled, `aria-label="Limpar filtros"`, hint/tooltip de controle (não `?` ornamental).

**Cor:** amarelo/âmbar semântico do design system; não fixar hex em MFE. Foco e contraste WCAG 2.2 AA; não comunicar perigo/destruição (limpar recorte é operação reversível). Com filtros ativos, destaque âmbar claramente visível; sem filtros, preferir disabled visual/accessibility **ou** omitir de acordo com padrão compartilhado, mas preservar geometria/consistência. Registrar escolha e testar. Não criar novo primitivo por conveniência.

**Semântica de limpeza:** limpar busca (`q`), chips status, regras AND avançadas e demais filtros ativos relevantes à página, resetar `page=1` e sincronizar URL/history, mantendo ordenação, page size, colunas, modo Tabela/Cards e preferências. Verificar no Helpdesk contrato exato `clearListFilters`: preservar a semântica pretendida sem apagar preferências ou auth scope de forma insegura; `Meus chamados` é escopo de requisição, avaliar com owner antes de alterá-lo. Refletir tooltip com mensagem legível: "Limpa os filtros e a busca; mantém ordenação, colunas e quantidade por página" (adaptar ao comportamento verificado).

## 3. Ordenação por clique no cabeçalho — três telas

- Cabeçalho clicável **apenas** quando o campo mapeia para sort válido na API de todas as fontes da consulta. Primeiro clique aplica uma direção determinística (documentada); segundo alterna ASC ↔ DESC; foco por teclado Enter/Space.
- Ícone/sinalização `aria-sort`, destaque do campo ativo, sentido e atualização do botão Ordenar; `sort=` sincroniza URL, F5, back/forward, page=1, page size e paginação; order antes de LIMIT/OFFSET, tie-break determinístico; sem sorting em memória apenas da página atual.
- My Requests Mine (Requests + PRC): inventariar `columnSortMap` + catálogo shared sort; comprovar quais dos campos Número/Tipo/Assunto/Status/Filial/Data têm equivalência real em ambas as fontes. Quando necessário, propor ampliação de contrato **aditiva** pelos owners e testes de paridade (sort + null + collation + id tiebreak + paginação), sem inventar equivalência; campo não compatível permanece sem affordance e é documentado como residual.
- My Requests Work Queue (Requests-only): mapear Número/Tipo/Assunto/Solicitante/Status/Filial/Concluída por/Data; habilitar todas as colunas cujo sort server-side é implementável e autorizado. Não usar client sort de página.
- Helpdesk: preservar ordenação GLPI por header e até três níveis no painel quando suportado; sincronizar/confirmar affordance, query e backend; não regredir behavior pré-existente; distinguir "multi-sort via popup" de "header click" e definir se clique substitui primeiro nível ou lista completa de forma previsível.
- Todos os campos realmente suportados devem funcionar; os outros exigem decisão explícita, não seta decorativa.

## 4. Gates de implementação e aceite

| Gate | Evidência obrigatória |
|---|---|
| G0 | HEAD/origin/main/status/WIP; inventário Helpdesk `FilterX`, kit e coluna sorts; contratos API e regras |
| G1 | Plugin UI generalizado (se necessário), export público, tokens âmbar, testes, documentação e nenhum componente duplicado |
| G2 | Mine e Fila consomem o mesmo controle; limpar filtros completo, link "Limpar tudo" removido |
| G3 | Helpdesk consome o mesmo controle, ícone migrado para **esquerda de Filtros** no footer do Hero, sem chip repetido |
| G4 | Matriz colunas 3 telas × ASC/DESC, server-side, URL/F5/back, 3 níveis Helpdesk, sem sort local pós-paginação |
| G5 | Unit/integration/typecheck/build Plugin UI + ambos MFEs; APIs somente se realmente alteradas |
| G6 | Chromium desktop1440/tablet768/mobile390/mobile320/zoom200, light/dark; geometria/ordem, tooltips, keyboard, headers, limpar, paginação/URLs, screenshots versionados |
| G7 | Verificação independente: matriz AC, refutações, findings/OCs, corrigir e reverificar até zero bloqueadores |
| G8 | Deploy HML controlado na ordem contratos/kit→consumers, saúde, remotes, E2E side-by-side **três telas** autenticado |
| G9 | Se Helpdesk HML ainda sem RBAC/compose, `TEST_NOT_RUN` e **STOP antes do GO PRD**; concessão/provisionamento só por owner autorizado |
| G10 | Gate PRD: SHA único, delta, backup/rollback, AuthZ, compat, métricas, saúde, mudanças concorrentes; produção requer autorização explícita da Coordination para este pacote **(não inferir da autorização UX V3 anterior)** |
| G11 | Deploy PRD somente depois do GO autorizado; monitoramento, smoke autenticado real read-only, rollback se gatilho |
| G12 | Atualizar docs dos MFEs e Plugin UI + ledger; evidências e relatório honesto |

### Critérios de aceite

- **AC01**: três telas mostram `FilterX` do Helpdesk com tom âmbar e mesma implementação pública do kit.
- **AC02**: controle está imediatamente à **esquerda** de Filtros na faixa inferior direita do Hero; depois Ordenar, Colunas e Tabela/Cards.
- **AC03**: remove "Limpar tudo", zera recortes/busca conforme contrato, mantém sort, page size, colunas e layout; página=1.
- **AC04**: sem `?` duplicado; tooltip/aria-label/foco e controle nested OK.
- **AC05**: cabeçalhos sortáveis executam ASC/DESC no backend; colunas não suportadas sem falsa affordance.
- **AC06**: estado do botão Ordenar, header `aria-sort`, URL e histórico sincronizados.
- **AC07**: Tabela/Cards, paginação, status chips e filtros avançados intactos.
- **AC08**: nenhuma regressão de AuthN/AuthZ, contratos, identidade de fontes ou consumer.
- **AC09**: 4 viewports, zoom200 e temas, popovers ancorados, sem clipping/overflow.
- **AC10**: testes e verificador independentes executados com evidências, findings tratados.
- **AC11**: HML realmente verificado nas três telas ou classificado bloqueado sem false PASS.
- **AC12**: PRD só após gate/autorização dedicada; rollback+observabilidade e validação autenticada.
- **AC13**: sem writes de negócio PRD/TOTVS, grants RBAC não autorizados, migrations incidentais, imports entre MFEs ou perda de WIP.

## 5. Invariantes e não objetivos

- Manter quatro abas My Requests, breadcrumbs, ações principais, PRC merge bounded honesto, paginação/colunas/preferences.
- Não alterar produtos, revisão, BOM, desenhos ou processos de Engenharia.
- `plugin-ui` é owner da UI; `requests-api`/`engineering-api`/`helpdesk-api` são owners de seus dados/ordenação. JWT/MCP/frontend não outorgam autoridade.
- `PRD_DEPLOY=NOT_AUTHORIZED_THIS_PACKAGE` até autorização separada depois de predeploy; implementação/HML são autorizados como escopo de execução planejada do agente, sob gates.
- Baseline UX V3 implantado não deve ser reescrito: este é um follow-up corretivo, com novos commits e ledger.

## 6. Output exigido

```text
TASK_ID, BASE_SHA, IMPLEMENTATION_SHA, FINAL_MAIN_SHA
PLUGIN_UI_INVENTORY, ABSTRACTION_GATE, PUBLIC_EXPORT, AMBER_TOKEN
MINE_CLEAR, QUEUE_CLEAR, HELPDESK_CLEAR, POSITION_RECT
SORT_MATRIX_BY_SOURCE, SORT_HEADER_ASC_DESC, SORT_POPUP_SYNC
URL_STATE, PAGE_SIZE, PAGINATION, COLUMN_PREFS, CARDS
TESTS_UNIT_INTEGRATION, TYPECHECK, BUILD, E2E_3_SURFACES
VERIFIER_ROUNDS, FINDINGS, CORRECTIONS, POST_FIX_E2E
HML_SHA_DIGEST_HEALTH, HML_AUTHORIZED_SMOKE, HML_ROLLBACK
PRD_PREDEPLOY, PRD_AUTHORIZATION, PRD_DEPLOY, PRD_SMOKE
AC01_AC13, TEST_NOT_RUN, INCONCLUSIVE, RESIDUAL_RISKS
ARCHITECTURE_DECISION_REQUIRED, EXECUTION_DRIFT, NEXT_ACTION
```
