# 106 — DÉLIA | ConversationNavigation — Conteúdo da categoria Conversas

**Data:** 2026-10-16  
**Status:** `PRODUCT_UX_SPEC / PLANNED / NOT_IMPLEMENTED`. **Documentação somente**: sem frontend, backend, dados mock de produção, deploy, mudança de fase ou aceite.  
**Produto:** DÉLIA standalone. `plugin-ui` é owner de apresentação compartilhada; `plugins/delia` compõe o produto e seu estado. O Portal continua host/navegação global; Core resolve autorização; APIs de domínio são autoridade final; MCP/A2A não conferem permissão.  
**Reancoragem obrigatória antes de executar:** HEAD/git status e .cursor/Project Instructions → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → documentos temáticos → ledger; evidência conflitante exige `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`.  
**Base verificada nesta documentação:** GitHub `main` `e7159c86756ba05f885cf0ccdbfe6fb2faecb54b`. Não presumir que será o HEAD de implementação.  
**Gates universais:** `read != write`, `draft != send`, `PREPARE != ACT`, `discovery != approval`, `model output != FACT`, `JWT != live AuthZ`; layout não concede authority.  

**Master:** [103](./103-delia-navigation-sidebar-master-product-ux-specification.md). **Dependências essenciais:** [97 — busca backend](./97-conversation-search-backend-first-future-ux-specification.md), [99 — sidebar atual](./99-conversation-sidebar-left-product-ux-specification.md), [107 — item](./107-conversation-history-item-product-ux-specification.md), [108 — fixadas](./108-pinned-conversations-group-product-ux-specification.md), [112 — ações](./112-navigation-actions-toggles-search-product-ux-specification.md).

## Aparência de categoria

```text
Conversas                            [recolher]
[+] Nova conversa
[⌕] Pesquisar conversas
  Fixadas        [itens reais ou seção omitida]
  Recentes       [itens autorizados]
  Anteriores     [paginação/cursor quando disponíveis]
  Opções         [se autorizadas]
```

Cabeçalho e toolbar possuem alinhamento de uma coluna e affordances discretas, sem botões de formulário pesados. Separar grupos por ritmo vertical e heading pequeno, sem banners ou repetição de “sem contrato” em cada grupo. Em runtime sem persistência, manter uma única mensagem curta de indisponibilidade; não dizer que não existem conversas porque nenhuma API foi consultada.

## Comportamento de listas

**Fixadas:** prioridade no topo, ordenação contratada; grupo pode estar ausente se vazio. **Recentes:** ordem temporal fornecida pela API, agrupada opcionalmente por período com timezone correto. **Anteriores:** paginação ou carregar mais por cursor real, never fake pagination. Se item ativo consta fora do segmento carregado, deve permanecer identificável/recuperável via contrato de navegação.

Menu por item não executa writes sem Core live AuthZ, Domain authority, Policy/Decision, confirmação quando necessária, idempotência, audit e postcondition. Selecionar conversa existente não é criar sessão: exige validação de acesso e recuperação autorizada, preservando draft quando houver decisão de troca.

## Estados

`history_unavailable`, `loading`, `list`, `empty_confirmed`, `forbidden`, `error`, `pagination_loading`, `selection_pending`. Empty confirmado só após consulta; pending não se apresenta como seleção concluída; erro não descarta o contexto ativo. Busca mantém apenas entrypoint desabilitado até [97](./97-conversation-search-backend-first-future-ux-specification.md).

## Contratos backend antes da ativação

List/get/create conversation, list turns, search, pinned state, paginação e lifecycle, com owner, OpenAPI/operationId estável, authz, retenção, exclusão, erro, idempotência writes e observabilidade. Os verbos são **capacidades semânticas ilustrativas**, não endpoints aprovados. Não usar `localStorage` ou import de tabelas Minha DELPI Chat.

## Densidade e QA

Linha de item ~40–48px, ícone 16px, texto 13–14px, truncamento seguro + tooltip acessível; títulos de grupos 11–12px. Scroll próprio, paginação não perde foco/seleção, títulos longos e Unicode, vários milhares de itens (virtualização conforme contrato), teclado e mobile. A opção “Nova conversa” é intenção sem efeito fake e requer guards para pending ACT/draft conforme doc 99.

**Reuse gate:** `EXISTING_EQUIVALENT=YES` para `ConversationSidebar`, `ConversationSidebarSearch`; `REUSE_DECISION=EXTEND`. Serviço de histórico `TO_INVENTORY` — não criado por esta spec.

## Critérios transversais de qualidade

- **Design system:** usar tokens, typografia, `IconButton`, feedback e superfícies do `plugin-ui`; ícones Lucide, sem cores hardcoded como identidade; no claro e escuro, ícone ghost transparente em repouso, hover tonal, foco visível, estados pressed/selected distinguíveis.
- **Responsividade:** medir container do Portal, não assumir viewport global. Cobrir página ≥1440, 1280, 1024, 768, 420, 375, 320px, zoom 200%, além do Companion Dock; não renderizar lista legível em rail estreito.
- **Movimento:** transição curta 180–240ms conforme tokens existentes; `prefers-reduced-motion` instantâneo; nunca remount do `ConversationWorkspace` nem perda de draft ao selecionar categoria.
- **Acessibilidade:** landmarks únicos, labels de ícones e hints por teclado, `aria-current` para navegação, `aria-expanded`/`aria-controls` para expansão, ordem de Tab previsível, Escape apenas em overlays, restauração de foco, contraste e screen reader.
- **Sem falso runtime:** nada de nomes de conversas, projetos, agentes, plugins, datas, métricas ou permissão inferidos. Loading só com requisição real; vazio = resultado autorizado real, indisponível = contrato inexistente, proibido = sem revelação de recursos.
- **Segurança:** nenhum item visual executa domínio, MCP, ferramenta, automação ou write por clique sem fluxo autorizado. Dados externos são não confiáveis; labels/snippets renderizados como texto inerte.
- **Validação:** testes de props/callbacks/estados e negativos de AuthZ, QA page/dock light/dark, check de exports/federação, prova de generalização em cenários de navegação e revisão independente no SHA executado. `TEST_NOT_RUN` não equivale a PASS.



## Rework R1 — estados e atos backend por grupo

O grupo de Conversas só pode distinguir `unavailable` (persistência ausente), `loading_real` (API em curso), `authorized_empty` (API respondeu vazio autorizado), `forbidden` (omitir) e `stale` (não navegar sem revalidação). Não declarar “zero conversas” baseado em memória React. “Fixadas”, “Recentes” e “Anteriores” serão renderizados com **itens reais** e ordenação/publicação do owner; sem sessão persistida, apenas orientação geral única.

Selecionar = read + alteração de contexto sujeita a ACL live e guardas de draft/turnos em andamento. Nova conversa = criação persistida e exige idempotência/outcome; Fixar, Renomear, Arquivar, Excluir são writes **separados**, com audit, permissão live e postcondition. Pesquisar remete ao doc 97 (backend-first), nunca busca efêmera no array React. Nomes no wireframe são exemplos, não fixture de produção. Matriz vinculante de classificação/owner está no [103 — Rework R1](./103-delia-navigation-sidebar-master-product-ux-specification.md).

## Implementação bounded 03 — ConversationNavigation (2026-10-17)

**Autorização:** Product Master pediu “Continue implementando, próximo”, dando continuidade à sequência de um componente por vez. O único novo componente público desta task é `ConversationNavigation`, que **reutiliza e estende `ConversationSidebar`**; não cria item de histórico separado, menu contextual, registry, API, serviço ou backend.

**HEAD de início:** `bc0d5b92bacb2835edc856a5b1d41b7078685edd`. Reancoragem técnica realizada por consulta de arquivos GitHub e specs 103/106; reancoragem completa das authorities 16/50/17/49/51/52/21/20/25, .cursor e ledger continua **INCONCLUSIVE** (não alegar comprovada). Nenhuma fase/CP avançou.

### Reuse Gate

- `EXISTING_EQUIVALENT=YES`: `ConversationSidebar`, `ConversationSidebarSearch`, `NavigationCategoryPanel` e linha de histórico existente.
- `REUSE_DECISION=EXTEND`: `ConversationSidebar` suporta agora projeções reais `pinnedHistory`, `history` (recentes), `olderHistory` e `historyStatus`; `ConversationNavigation` é wrapper de categoria com props explícitas `pinned`, `recent`, `older`, `status` e callbacks já existentes.
- `EXISTING_EQUIVALENT=TO_INVENTORY`: persistência, paginação, ACL de seleção, fixação e search backend; **nenhum desses mecanismos foi implementado ou substituído por storage frontend**.

### Comportamento visual e funcional implementado

1. Nova conversa, Pesquisar e Opções **reutilizam controles atuais**; permanecem desabilitados quando host não fornece callbacks.
2. Quando o consumer fornece **status ready + listas autorizadas + callback de seleção**, renderiza grupos não vazios na ordem **Fixadas, Recentes, Anteriores**. Todos os itens usam o botão/lista já existente, seleção e `aria-current=page` quando aplicável. A UI não altera ordenação da API; o owner deve fornecer os grupos já classificados.
3. Com `unavailable`, mostra **uma orientação única** explicando ausência de persistência, sem nomes fictícios, sem listagens de grupos “vazios confirmados”.
4. `loading` só aparece quando explicitamente informado, `authorized_empty` apenas após confirmação do owner, `error` exibe erro honesto; estes são **estados visuais**, não evidência de API.
5. O `ConversationSidebar` conserva compatibilidade de legado para um host que já passe array real + `onSelectConversation`. `ConversationNavigation` é opt-in explícito com `status=unavailable` padrão. Sem callback de seleção a lista não é apresentada como navegável.
6. DÉLIA `DeliaConversationPage` usa `ConversationNavigation` dentro do `NavigationCategoryPanel` existente, preservando `NavigationRail`, a mesma sidebar, único toggle e `ConversationWorkspace` montado.

### Arquivos/validação

Criado `plugins/plugin-ui/src/components/conversation/ConversationNavigation.tsx` e `ConversationNavigation.test.tsx`. Alterados `ConversationSidebar.tsx` (grupos e estados), `ConversationSidePanels.css` (espaçamento de grupos), exports em `components/conversation/index.ts` e `src/index.ts`, `scripts/verify-host-exports.mjs`, e consumer `plugins/delia/src/ui/DeliaConversationPage.tsx`.

Testes especificados: sem backend não inventa histórico, ordem de grupos e callbacks, grupos vazios omitidos, nenhum item sem callback, status loading/empty/error. **TESTS_CREATED=YES**, `VITEST=TEST_NOT_RUN`, `TSC=TEST_NOT_RUN`, `FEDERATION_BUILD=TEST_NOT_RUN`, `BROWSER_QA=TEST_NOT_RUN`, `INDEPENDENT_ACCEPTANCE=PENDING`.

**Fora do escopo:** `ConversationHistoryItem` separado, fixar/desafixar, rename/archive/delete, paginação e cursor backend, criação de sessão, pesquisa backend, projeto/agentes/plugins, contratos de autorização. `CODE_COMMITTED_CANDIDATE` não é PASS de produção.
