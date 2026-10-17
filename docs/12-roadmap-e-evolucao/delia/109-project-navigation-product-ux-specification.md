# 109 — DÉLIA | ProjectNavigation — Projetos na navegação

**Data:** 2026-10-16  
**Status:** `PRODUCT_UX_SPEC / PLANNED / NOT_IMPLEMENTED`; **documentação somente**.  
**Master:** [103 — DeliaNavigationSidebar](./103-delia-navigation-sidebar-master-product-ux-specification.md).  
**Base verificada:** `main` `e7159c86756ba05f885cf0ccdbfe6fb2faecb54b` antes dos commits desta série. Documentação não é runtime nem autorização de execução.  
**Autoridades para reancoragem antes de código:** HEAD/git status + Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura → product spec → temática → ledger. `EXECUTION_DRIFT`/`ARCHITECTURE_DECISION_REQUIRED` em conflito.  
**Owner de apresentação:** `plugin-ui`; **consumer/estado:** DÉLIA; Core/Portal/Domain APIs preservam seus boundaries.  


## Propósito, fronteira e descoberta

Um **projeto** pode agrupar trabalho/contexto relacionado a um objetivo, mas a UI não deve criar modelo, tabela ou API próprios só porque a categoria existe. Antes de listar/criar/editar, inventariar: (a) projetos/workspaces do Portal/Core/Domain APIs; (b) eventual conceito de projeto da DÉLIA congelado em spec; (c) owner, RBAC, recurso persistido, vínculo legítimo entre conversa e projeto, permission scopes, ciclo de vida (retenção/exclusão) e consumidores.

`EXISTING_EQUIVALENT=TO_INVENTORY` para projeto/contrato; `REUSE_DECISION=PENDING_GATE`. `EXISTING_EQUIVALENT=YES` apenas para rail, painel, lista e primitives; `REUSE_DECISION=EXTEND` visual.

## Aparência detalhada

```text
Projetos                             [recolher]
[+ Novo projeto] * somente se autorizado
[⌕ Encontrar projeto] * busca real contratada
Meus projetos
  [▣] Projeto autorizado A      [⋯]
  [▣] Projeto autorizado B      [⋯]
Compartilhados * apenas se owner publicar essa categoria
  [▣] Projeto autorizado C
```

Cabeçalho 13–15px, ícone `FolderKanban`/folder 17–18px, items ~44px, title truncado numa linha e tooltip contextual; seção 11–12px, padding 16px, gap 8–12px, superfície clean, selected tonal distinto do hover. Ícones de projeto podem ser fornecidos pelo catálogo legítimo, mas URLs externas não confiáveis devem ser validadas. Não usar avatars de pessoas para inventar autoria/ownership.

## Estados de listagem e seleção

`unavailable` se não há contrato; `loading` apenas consulta real; `empty_confirmed` se API autorizada retornou vazio; `forbidden` oculta nomes e resultados; `partial` quando paginação incompleta; `error` com retry; `selected` somente após navegação real. Selecionar projeto não cria sessão conversacional nem injeta memória/fato; antes de trocar contexto, contrato precisa definir o que acontece com draft, turns, evidence, proposta governada e contexto do Portal.

## Funcionalidades previstas por gatilho de contrato

- **Listar/abrir:** query paginada por owner, permissão live Core e regras Domain; abertura usa rota/ID estável aceito.
- **Criar:** formulário bounded (nome, descrição opcional, owner definido), idempotência e confirmação de postcondition real. Sem callback, ação omitida/disabled honesto.
- **Renomear/arquivar/excluir:** menu por item quando `allowedActions` backend autoritativo; write gates e proteção contra perda de contexto.
- **Associar/desassociar conversa:** recurso apenas se owner publicá-lo; não arrastar card nem alterar array React como prova de vínculo persistido.
- **Projetos compartilhados:** visibilidade e membresia provadas no owner; nunca enumerar projetos de outros usuários por metadata.
- **Pesquisa de projeto:** read-only backend aprovada; não indexar título local para simular busca global.

## Contrato/API antes do código

Owner, consumers, schema OpenAPI, operationId, request/response/errors, list cursor/order/search, identity, tenant boundary, Core AuthZ, Domain final authority, idempotency writes, limites, retenção/exclusão, observabilidade, compatibilidade e audit/postcondition. Metadados do Portal não autorizam write na DÉLIA.

## QA e anti-casos

Validar 0/1/1000 projetos, nomes longos, erros, ACL revogada após listagem, mudanças de organização, projetos compartilhados, empty vs unavailable, seleção enquanto resposta DÉLIA em andamento e operação PREPARE/ACT pendente. Sem compartilhar estados por banco alheio ou runtime do Chat.

## Contrato de qualidade transversal

Usar cores/tokens do kit em light/dark, sem tons cinzas permanentes em botões ghost de repouso. Ícones 16–20px, hit target 40–44px, foco 2px, labels reais, keyboard e tooltip acessível; movimento 180–240ms ou nulo em `prefers-reduced-motion`. Validar container 1440/1280/1024/768/420/375/320px, zoom 200% e Companion Dock; sem overflow horizontal, remount de conversa ou perda de draft. Snapshots ou exemplos de UI nunca substituem dados/permission reais. Testes e browser QA permanecem `TEST_NOT_RUN`; independente `PENDING`.



## Rework R1 — projeto condicionado a owner legítimo

A categoria Projetos é **TARGET de navegação**, não uma implementação de workspace DÉLIA nem autorização para nova entidade. Antes de qualquer listagem real, `EXISTING_EQUIVALENT=TO_INVENTORY` de Core/Portal/Domain APIs/projetos existentes, seus owners, consumers, contratos de leitura/write e entidade persistida. `REUSE_DECISION=PENDING_GATE` para feed e comandos. Se houver projeto legítimo, acessar via boundary autorizado; se não houver evidência, manter categoria `contract_unavailable` **somente** se produto a aprovar como affordance visual, sem fake “Meus projetos”.

Propostas de Novo projeto, mover conversa, renomear/arquivar/excluir não estão aprovadas. Exigem decisão de produto e contracts antes de callbacks enabled. A seleção de projeto não pode mudar contexto de conversas silenciosamente nem substituir Domain authority.

## Implementação bounded 06 — ProjectNavigation (2026-10-17)

**Autorização:** Product Master solicitou implementar o próximo componente após `PinnedConversations`. Esta task implementa **apenas `ProjectNavigation` como frontend render-only**, integrada como prévia visual da categoria Projetos na DÉLIA. **BASE_HEAD** observado: `ce2a5533ce3c5e109b5aaaf4848efda6e050e06a`.

**Reuse Gate:** `EXISTING_EQUIVALENT=YES` para composição de `ConversationThreeRegionLayout`, `NavigationRail`, `NavigationCategoryPanel` e tokens/CSS compartilhados; `REUSE_DECISION=EXTEND` a apresentação via novo componente de categoria, sem segundo shell. `EXISTING_EQUIVALENT=TO_INVENTORY` para entidade/catálogo/owner/API de projetos no Portal/Core/Domain; `REUSE_DECISION=PENDING_GATE` para data source, operações, links e qualquer adapter. Busca GitHub sem resultados não elimina equivalente.

**Contrato visual implementado:** `status="contract_unavailable"|"ready"|"loading"|"authorized_empty"|"error"`; `projects?: {id,title,selected?}[]`; `onSelectProject?(id)`; `onRetry?;` `className?`. O estado default é `contract_unavailable`. Em `ready`, apenas itens fornecidos por consumer autorizado e com callback explícito de seleção são exibidos (ícone FolderKanban, título uma linha/truncado, foco, hover e indicação da seleção recebida). `loading`/empty/error são estados de apresentação, não evidência real de backend. `onRetry` só aparece quando fornecido. `forbidden` deve ser omitido pelo consumer e nunca pode ser inferido deste componente. Sem `create/update/delete`, associação de conversa ou pesquisa.

**Integração DÉLIA:** `DeliaConversationPage` mantém `selectedCategory` transitório `conversations|projects`, preservando o `ConversationWorkspace`. O `NavigationRail` permite selecionar Projetos como **prévia visual aprovada, não autorização de catálogo**. Ao selecionar, expande a sidebar existente e renderiza `NavigationCategoryPanel category="projects"` contendo `ProjectNavigation status="contract_unavailable"`. Para voltar a Conversas, recolher a barra e selecioná-las pelo rail (interação provisória, a melhorar quando existir rail lateral persistente ao painel). Agentes e Plugins continuam indisponíveis, sem fake callback. O shell mantém apenas um toggle e usa `leftTitle` apropriado. Nenhum endpoint ou rota foi introduzido.

**Arquivos:** `plugins/plugin-ui/src/components/conversation/ProjectNavigation.tsx`, `ProjectNavigation.css`, `ProjectNavigation.test.tsx`, exports `components/conversation/index.ts`/`src/index.ts`, import CSS em `src/styles.css`, gate `scripts/verify-host-exports.mjs`, `plugins/delia/src/ui/DeliaConversationPage.tsx` e teste da página.

**Status factual:** código/testes publicados em GitHub. `VITEST=TEST_NOT_RUN`, `TSC=TEST_NOT_RUN`, `FEDERATION_BUILD=TEST_NOT_RUN`, `PORTAL_DOCK_QA=TEST_NOT_RUN`; `INDEPENDENT_REVIEW=PENDING`; `PHASE_PROGRESSION=NONE`; `CODE_COMMITTED_CANDIDATE` sujeito a revisão. Reancoragem integral .cursor → 16/50/17/49/51/52/21/20/25 → arquitetura/ledger não foi comprovada nesta execução via conector: `INCONCLUSIVE`; não declarar aceite/fase nem tratar UI de projetos como backend autorizado. Próximo subcomponente apenas por nova autorização.
