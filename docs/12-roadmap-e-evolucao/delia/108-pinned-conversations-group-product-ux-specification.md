# 108 — DÉLIA | PinnedConversations — Grupo Fixadas

**Data:** 2026-10-16  
**Status:** `PRODUCT_UX_SPEC / PLANNED / NOT_IMPLEMENTED`. **Documentação somente**: sem frontend, backend, dados mock de produção, deploy, mudança de fase ou aceite.  
**Produto:** DÉLIA standalone. `plugin-ui` é owner de apresentação compartilhada; `plugins/delia` compõe o produto e seu estado. O Portal continua host/navegação global; Core resolve autorização; APIs de domínio são autoridade final; MCP/A2A não conferem permissão.  
**Reancoragem obrigatória antes de executar:** HEAD/git status e .cursor/Project Instructions → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → documentos temáticos → ledger; evidência conflitante exige `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`.  
**Base verificada nesta documentação:** GitHub `main` `e7159c86756ba05f885cf0ccdbfe6fb2faecb54b`. Não presumir que será o HEAD de implementação.  
**Gates universais:** `read != write`, `draft != send`, `PREPARE != ACT`, `discovery != approval`, `model output != FACT`, `JWT != live AuthZ`; layout não concede authority.  

**Master:** [103](./103-delia-navigation-sidebar-master-product-ux-specification.md). **Usa:** [107 — item](./107-conversation-history-item-product-ux-specification.md).

## Objetivo e visual

Agrupar conversas **explicitamente fixadas pelo usuário e confirmadas pelo owner** no topo do painel de Conversas. Título secundário “Fixadas” (11–12px), opcional ícone `Pin` pequeno, lista comum de conversation items, sem duplicar estilos e sem outra fonte de histórico.

```text
Fixadas
  [▢] Conversa real fixada                 [⋯]
  [▢] Outra conversa fixada                [⋯]
Recentes
  ...
```

Sem pinned real? Preferir omitir o grupo ou apresentar estado vazio apenas se a seção tiver sido explicitamente aberta e backend comprovou vazio; nunca criar exemplos de chats fixados em produção.

## Estados e operações

`collapsed` (se disclosure aprovado), `expanded`, `empty_confirmed`, `loading`, `error`, `forbidden`. A fixação é **write de preferência/metadata**, não mera mudança de array local: owner, OpenAPI, AuthZ live, idempotência, auditoria e postcondition, rollback/retry definidos antes de habilitar ícone `Pin`.

Ao fixar/desafixar, backend autoritativo confirma e só então o agrupamento muda, ou usar optimistic UI apenas se a política autorizar e rollback for comprovado; evitar piscar/reordenar enquanto request pendente. Não exibir limite numérico, ordering, timestamp de fixação ou drag sort sem contrato. Fixar não concede acesso nem impede revogação/exclusão.

## Acessibilidade, responsividade, QA

Headings e listas semânticas, status legível por screen reader após postcondition, teclado menu/confirmation, 320–1440px, dark/light, selected e hover, titles muito longos; impedir que a seção consuma altura ilimitada se houver milhares de itens (scroll/paginação conforme API). No rail apenas ícone de categoria Conversas, nunca pinned chats individuais.

**Reuse:** `EXISTING_EQUIVALENT=YES` para estrutura de lista/tokens; `TO_INVENTORY` para API de fixação; `REUSE_DECISION=EXTEND` visual, backend pending owner/contract.

## Critérios transversais de qualidade

- **Design system:** usar tokens, typografia, `IconButton`, feedback e superfícies do `plugin-ui`; ícones Lucide, sem cores hardcoded como identidade; no claro e escuro, ícone ghost transparente em repouso, hover tonal, foco visível, estados pressed/selected distinguíveis.
- **Responsividade:** medir container do Portal, não assumir viewport global. Cobrir página ≥1440, 1280, 1024, 768, 420, 375, 320px, zoom 200%, além do Companion Dock; não renderizar lista legível em rail estreito.
- **Movimento:** transição curta 180–240ms conforme tokens existentes; `prefers-reduced-motion` instantâneo; nunca remount do `ConversationWorkspace` nem perda de draft ao selecionar categoria.
- **Acessibilidade:** landmarks únicos, labels de ícones e hints por teclado, `aria-current` para navegação, `aria-expanded`/`aria-controls` para expansão, ordem de Tab previsível, Escape apenas em overlays, restauração de foco, contraste e screen reader.
- **Sem falso runtime:** nada de nomes de conversas, projetos, agentes, plugins, datas, métricas ou permissão inferidos. Loading só com requisição real; vazio = resultado autorizado real, indisponível = contrato inexistente, proibido = sem revelação de recursos.
- **Segurança:** nenhum item visual executa domínio, MCP, ferramenta, automação ou write por clique sem fluxo autorizado. Dados externos são não confiáveis; labels/snippets renderizados como texto inerte.
- **Validação:** testes de props/callbacks/estados e negativos de AuthZ, QA page/dock light/dark, check de exports/federação, prova de generalização em cenários de navegação e revisão independente no SHA executado. `TEST_NOT_RUN` não equivale a PASS.



## Rework R1 — fixação não é estado local autoritativo

Renderizar “Fixadas” **somente** com dados publicados e autorizados pelo owner; ausência de contrato não permite lista exemplificativa. A ação fixar/desafixar é write de metadados: identity → Core live AuthZ → Domain owner → Policy/Decision quando aplicável → idempotência → audit → execution → authoritative postcondition. Em falha/revogação, a conversa mantém posição autoritativa. Se pinned vazio foi confirmado pelo backend, grupo pode ser omitido; `empty_confirmed` é diferente de `unavailable`. Nenhum drag-sort ou favoritar local sem contrato.

## Implementação bounded 05 — PinnedConversations (2026-10-17)

**Autorização:** Product Master solicitou “Ok, implementar” para o componente seguinte à entrega do `ConversationHistoryItem`. **Base HEAD consultada:** `d4913798c07f975956457e30cb690532990518a1`.

**Reuse gate:** `EXISTING_EQUIVALENT=YES` — grupo Fixadas já estava representado em `ConversationSidebar`, com linha `ConversationHistoryItem` e CSS compartilhado; `REUSE_DECISION=EXTEND`. Extraiu-se apenas o grupo visual para `plugins/plugin-ui/src/components/conversation/PinnedConversations.tsx`, sem segunda fonte de dados, shell ou navegação. `EXISTING_EQUIVALENT=TO_INVENTORY` para contrato/backend de fixação; **não foi criado**.

**Contrato visual:** `items: readonly ConversationHistoryItemData[]`, `onSelectConversation?(id)`, `className?`. Grupo semanticamente rotulado Fixadas, `h2` e `ul/li`, cada linha reutiliza `ConversationHistoryItem`. A ordem é **exatamente a projeção recebida**, não uma ordenação local inferida. Se a lista estiver vazia ou não houver callback de seleção autorizado fornecido pelo consumer, retorna `null` (não declara falso zero nem apresenta controle inválido). Só é usado por `ConversationSidebar` dentro de `historyStatus=ready`.

**Segurança:** nenhuma função `pin`, `unpin`, `rename`, `delete`, drag-and-drop, escrita de preferências ou persistência local. A presença de um item não autentica nem autoriza o usuário; a callback apenas sinaliza intenção, e o owner backend precisa validar a sessão antes de carregar. MCP/provider/model não é autoridade. Fixação futura permanece sob identity → Core live AuthZ → Domain authority → Policy/Decision → idempotência → audit → postcondition.

**Arquivos alterados:** componente e teste `PinnedConversations.tsx` / `PinnedConversations.test.tsx`; `ConversationSidebar.tsx` troca grupo inline existente pelo componente; exports em `components/conversation/index.ts` e `src/index.ts`, gate de Federation `scripts/verify-host-exports.mjs`. DÉLIA continua a consumi-lo **indiretamente** via `DeliaConversationPage → NavigationCategoryPanel → ConversationNavigation → ConversationSidebar`, sem novo import nem sessão fictícia.

**Testes criados:** grupo omitido com zero itens / callback ausente, foco em reaproveitamento de item, seleção, ausência de menu e integração ordenada com Recentes/Anteriores. **TESTS=TEST_NOT_RUN**, **TSC=TEST_NOT_RUN**, **FEDERATION_BUILD=TEST_NOT_RUN**, **BROWSER_QA=TEST_NOT_RUN** até execução real em SHA/config verificados. `CODE_COMMITTED_CANDIDATE` após confirmação de HEAD, `INDEPENDENT_REVIEW=PENDING`, `PHASE_PROGRESSION=NONE`. Reancoragem integral de autoridades e ledger não demonstrada neste ambiente: `INCONCLUSIVE`; este registro não aceita o runtime.
