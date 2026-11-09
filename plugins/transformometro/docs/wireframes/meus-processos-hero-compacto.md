# Meus processos — Hero compacto e área de resultados

**Tipo:** wireframe funcional + contrato de UX para implementação
**Estado:** IMPLEMENTED_IN_CODE — composição do hero compacto no MFE (`ProcessesPage` + `PageHeader.children`); **aceitação visual runtime = TEST_NOT_RUN** (sem smoke autenticado nesta entrega documental)
**Owner:** `plugins/transformometro` (MFE Portal Transforma+)
**Rota:** `/apps/transformometro/processes`
**Referência existente:** [Blueprint do Portal Transforma+](../../../../docs/12-roadmap-e-evolucao/transformometro-app/PORTAL-TRANSFORMA-BLUEPRINT.md)
**Fonte de comportamento vigente (código):** `src/ui/pages/ProcessesPage.tsx`, `src/ui/processes/ProcessFolderBrowser.tsx`, `src/ui/processes/ProcessListPresentationControls.tsx`

## 1. Problema e objetivo

Na situação observada, a página possui breadcrumb, hero de título/ações, um grande card separado de controles de listagem e, só então, os resultados. Isso consome espaço vertical e empurra a tabela para baixo.

**Objetivo aprovado:** concentrar no **mesmo hero** todas as ações e os controles de consulta/apresentação que ficam acima da área de resultados. A lista/tabela/pastas deve começar imediatamente abaixo do hero, sem card intermediário de filtros. Preservar a semântica, os modos e a fonte de dados existentes.

Não redesenhar a tabela, o workspace de processo nem o formulário de criação. Não criar novos filtros ou métricas.

## 2. Wireframe desktop — TARGET

```text
[← Início] / Meus processos                         (breadcrumb atual; acima do hero)

┌─────────────────────────────────────────────────────────────────────────────┐
│ PROCESSOS                                                                   │
│ Meus processos                            [Atualizar] [+ Novo processo]      │
│ Processos disponíveis no Portal Transforma+.                                │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Buscar processo                        Status                 Ordenar por    │
│ [Nome ou código…____________________]   [Todos_________v]      [Campo____v]   │
│ ─────────────────────────────────────────────────────────────────────────── │
│ [Processos | Departamentos]        [Ordem: Maior/Menor] [Grandes Médios Lista Detalhes] │
└─────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────┐
│ Resultados / contexto do agrupamento                      [N registros]    │
│ Código       Processo                Status       Preenchimento    Atualizado│
│ ...         ...                      ...          ...              ...      │
│ ...         ...                      ...          ...              ...      │
│ [Paginação existente + estados existentes]                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

O wireframe é **esquemático**, não uma especificação de largura fixa. O componente `ProcessListPresentationControls` preserva a escolha independente de campo de ordenação e direção ascendente/descendente; **“Maior” é direção de ordenação, não um novo modo de visualização**. Os quatro modos atuais são **Grandes, Médios, Lista e Detalhes**.

### Composição

- **Fora do hero:** breadcrumb canônico `TmPagePath` acima do cabeçalho.
- **Faixa 1 (identidade):** eyebrow PROCESSOS, título Meus processos, descrição curta; ações Atualizar e Novo processo alinhadas à direita (quebra responsiva).
- **Faixa 2 (consulta):** Buscar por nome/código, Status, Ordenar por. Preservar rótulos, tooltips e componentes `FieldLabel`, `NativeTextControl`, `SelectField`.
- **Faixa 3 (apresentação):** Processos/Departamentos; direção de ordenação (Maior/Menor); modos Grandes/Médios/Lista/Detalhes; agrupados com clareza e acessibilidade.
- **Abaixo:** somente região de resultados, drilldown de departamento, tabela/pastas/cards, contagem, paginação, loading/erro/vazio e ajuda contextual quando necessárias. O formulário de **Novo processo** continua como seção própria quando aberto, sem comprimir ou misturar o formulário no hero.

## 3. Comportamento existente a preservar (PROVEN em código, não prova de runtime)

| Elemento | Origem/contrato atual | Requisito |
|---|---|---|
| Busca e status | `ProcessesPage`: `searchQ`, `statusFilter`, `buildProcessListQuery` → `fetchProcessos` | Preservar params `q`/`status`, sem nova API |
| Processos/Departamentos | `processListBrowseMode` + `ProcessFolderBrowser` | Preservar agrupamento e drilldown; processo pode aparecer em mais de um departamento |
| Ordenação | `processListSort` + `ProcessListPresentationControls` | Preservar campos nome/código/status/preenchimento/atualizado e asc/desc |
| Modos | `processListViewMode` | Preservar `icons-lg`, `icons-md`, `list`, `details` |
| Preferências | `read*/write*` de browse/sort/view | Manter persistência no navegador e defaults canônicos |
| Detalhes | `detailColumns` | Preservar Código, Processo, Status, Preenchimento, Atualizado em |
| Resultados | `ProcessFolderBrowser`, `DataTable`, `Pagination` | Sem alteração de semântica, paginação, clique ou caminho |
| Novo processo | `startCreate`, `ProcessFormFields`, `ProcessScopeFields` | Preservar scroll, criação e validação de escopo |
| Atualizar/realtime | `load`, `useTransformometroCatalogWatch` | Preservar refetch e invalidation |
| Segurança | backend `list_processos` e AuthZ corrente | Nenhum efeito de UI implica permissão nova |

**Cuidado:** `ProcessFolderBrowser` já possui `hideBrowseToggle` e `hideListToolbar`, além de `filters` e callbacks controlados. Usar o caminho mais curto para delegar os controles ao hero e desabilitar a duplicação na região de resultados. Manter o breadcrumb interno de drilldown **Departamentos / nome** quando houver seleção.

## 4. Estados e responsividade

- **Desktop largo:** faixas compactas, controles em uma linha onde couber, sem overflow horizontal.
- **Tablet:** filtros e controles quebram em linhas responsivas; nenhuma sobreposição ou texto cortado.
- **Mobile (e zoom 200%):** empilhamento lógico, alvos tocáveis, rolagem da tabela conforme padrão existente; NÃO ocultar funcionalidades.
- **Loading:** manter status de carregamento; evitar deslocamentos grandes da tabela.
- **Erro/403:** `StatusAlerts` continua distinto de lista vazia; manter retry e mensagens atuais.
- **Vazio:** manter mensagem atual, inclusive sem resultados após filtro.
- **Departamento selecionado:** breadcrumb de drilldown na área de resultados; os controles de ordenação respeitam a política do componente existente (nome de departamento no nível raiz).
- **Teclado/a11y:** labels associados, grupos rotulados, estados `aria-pressed`, tab order e foco após mudança/retorno.

## 5. Aceite verificável

1. Breadcrumb `Início / Meus processos` permanece funcional acima do hero.
2. Hero contém título, descrição, Atualizar, Novo processo, busca, status, campo e direção de ordenação, agrupamento e modos de visualização.
3. Nenhum controle duplicado fora do hero; nenhum grande card intermediário entre hero e resultados.
4. Resultados começam imediatamente após hero (ressalvado o formulário de criação aberto e mensagens de estado).
5. Busca/status retornam os mesmos registros que antes sob a mesma consulta; 403 continua erro, não lista vazia.
6. Ordenação e modo exibem estados corretos e mantêm preferências.
7. Alternar Processos/Departamentos e navegar para dentro/fora de um departamento preserva contagem e paginação.
8. Modos Grandes/Médios/Lista/Detalhes e ordenação de colunas continuam funcionais.
9. Novo processo abre formulário completo, cancela e cria sem regressão; navegação para o workspace intacta.
10. Refresh manual e WebSocket de catálogo continuam atualizando a lista.
11. Desktop, tablet, mobile, zoom 200%, F5, Back/Forward e tema visual do Portal sem clipping ou overflow.
12. Testes de UI/componentes e smoke visual autenticado no Portal; capturas antes/depois e evidência do ganho de espaço vertical (comparar viewport equivalente, sem inventar métrica).

## 6. Limites e execução

**Escopo:** refatoração frontend de `ProcessesPage`, `PageHeader`/composição de `PageHero` se necessário, `ProcessFolderBrowser` e CSS pontual. Primeiro inspecionar API real de slots/children no `PageHeader` e evitar alterar a semântica compartilhada para outras páginas.

**Fora de escopo:** backend, tabelas/colunas, OpenAPI, MCP/Actions, Keycloak/Core, novos filtros, métricas ou design system paralelo.

Implementação somente após `git status`, HEAD seguro, testes e validação de contratos. Deploy produtivo do **MFE transformometro** pelo comando canônico, após gates de qualidade. Documentação `TARGET` não comprova runtime; atualizar seu status apenas após evidência de implementação e browser acceptance.
