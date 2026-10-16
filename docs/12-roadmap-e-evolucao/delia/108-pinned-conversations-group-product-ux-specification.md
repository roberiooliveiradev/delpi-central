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


