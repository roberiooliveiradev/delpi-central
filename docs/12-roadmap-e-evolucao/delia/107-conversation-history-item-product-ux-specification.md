# 107 — DÉLIA | ConversationHistoryItem — Item de conversa persistida

**Data:** 2026-10-16  
**Status:** `PRODUCT_UX_SPEC / PLANNED / NOT_IMPLEMENTED`. **Documentação somente**: sem frontend, backend, dados mock de produção, deploy, mudança de fase ou aceite.  
**Produto:** DÉLIA standalone. `plugin-ui` é owner de apresentação compartilhada; `plugins/delia` compõe o produto e seu estado. O Portal continua host/navegação global; Core resolve autorização; APIs de domínio são autoridade final; MCP/A2A não conferem permissão.  
**Reancoragem obrigatória antes de executar:** HEAD/git status e .cursor/Project Instructions → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → documentos temáticos → ledger; evidência conflitante exige `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`.  
**Base verificada nesta documentação:** GitHub `main` `e7159c86756ba05f885cf0ccdbfe6fb2faecb54b`. Não presumir que será o HEAD de implementação.  
**Gates universais:** `read != write`, `draft != send`, `PREPARE != ACT`, `discovery != approval`, `model output != FACT`, `JWT != live AuthZ`; layout não concede authority.  

**Master:** [103](./103-delia-navigation-sidebar-master-product-ux-specification.md). **Usado por:** [106](./106-conversation-navigation-groups-product-ux-specification.md), [108](./108-pinned-conversations-group-product-ux-specification.md).

## Modelo visual

```text
[▢] Análise de capacidade           [⋯]
[▢] Indicadores de produção           • selected
```

Exemplo apenas conceitual. Um único item mostra título publicado pelo owner, indicação de seleção e menu overflow quando houver operações reais. Ícone de conversa `MessageSquareText`/Lucide, tamanho ~16px; altura mínima 40–44px, padding 8–12px, radius 8–10px, texto 13–14px em linha única com ellipsis. Tooltip acessível para título truncado; não exibir ID interno nem texto privado de snippets em tooltip por padrão. Sem cartão pesado por item.

## Estados completos

| Estado | Tratamento |
|---|---|
| `idle` | fundo transparente |
| `hover` | tonal sutil; menu aparece se existir |
| `focus-visible` | outline sem apagar seleção |
| `selected` | `aria-current=page` ou equivalente para navegação, indicação não só por cor |
| `loading` | item verdadeiro sendo recuperado, sem sessão fictícia |
| `unavailable` | indisponível com semântica correta, sem ação |
| `forbidden/revoked` | item removido/redacted, sem disclosure de dados |
| `stale` | sem navegação até reconciliação com owner |
| `menu_open` | menu semântico ancorado e teclado correto |

## Interações

Selecionar dispara callback de intenção com ID opaco validado pelo backend. UI não define authz; não inicia conversa simplesmente por selecionar. Duplo clique não deve duplicar requests. Menus futuros: Fixar/Desafixar, Renomear, Arquivar, Excluir, somente após contratos write. A ação Excluir segue confirmação e postcondition; “Renomear” recebe form com validação bounds no backend. Ordem e timestamp publicadas por owner; não criar títulos via model inferido.

## Component contract proposto

`item: {id,title,selected,availability,...authorizedMetadata}`, `onSelect(id)`, `actions?: [{id,label,enabled,reason}]`, `onAction(intent)`; tipos finais sujeitos ao contrato Domain/backend. Ausência de `actions` significa menu omitido, não botão desabilitado sem utilidade.

## Safety/QA

Teste titles UTF-8/RTL, longa string, HTML literal inerte, XSS, truncamento, screen reader, selecionado, menu por teclado, selecionar item de outro tenant (negação server), revogação após listagem, stale cursor, scroll position e dock. Sem drag-and-drop/mover conversa entre projetos sem contrato governado.

**Reuse:** `EXISTING_EQUIVALENT=YES` para item básico `ConversationSidebar`; `REUSE_DECISION=EXTEND`. Menus/tooltip compartilhados `TO_INVENTORY` antes de inventar.

## Critérios transversais de qualidade

- **Design system:** usar tokens, typografia, `IconButton`, feedback e superfícies do `plugin-ui`; ícones Lucide, sem cores hardcoded como identidade; no claro e escuro, ícone ghost transparente em repouso, hover tonal, foco visível, estados pressed/selected distinguíveis.
- **Responsividade:** medir container do Portal, não assumir viewport global. Cobrir página ≥1440, 1280, 1024, 768, 420, 375, 320px, zoom 200%, além do Companion Dock; não renderizar lista legível em rail estreito.
- **Movimento:** transição curta 180–240ms conforme tokens existentes; `prefers-reduced-motion` instantâneo; nunca remount do `ConversationWorkspace` nem perda de draft ao selecionar categoria.
- **Acessibilidade:** landmarks únicos, labels de ícones e hints por teclado, `aria-current` para navegação, `aria-expanded`/`aria-controls` para expansão, ordem de Tab previsível, Escape apenas em overlays, restauração de foco, contraste e screen reader.
- **Sem falso runtime:** nada de nomes de conversas, projetos, agentes, plugins, datas, métricas ou permissão inferidos. Loading só com requisição real; vazio = resultado autorizado real, indisponível = contrato inexistente, proibido = sem revelação de recursos.
- **Segurança:** nenhum item visual executa domínio, MCP, ferramenta, automação ou write por clique sem fluxo autorizado. Dados externos são não confiáveis; labels/snippets renderizados como texto inerte.
- **Validação:** testes de props/callbacks/estados e negativos de AuthZ, QA page/dock light/dark, check de exports/federação, prova de generalização em cenários de navegação e revisão independente no SHA executado. `TEST_NOT_RUN` não equivale a PASS.



## Rework R1 — item e ações sem autoridade implícita

Item somente renderiza dados autorizados e recebe `onSelect` do consumer. O menu de reticências **não aparece** quando não existem ações com contrato válido; disabled não implica permissão concedida. Estados de `pending selection`, `forbidden`, `revoked`, `stale` e `authorized_empty` devem ser distintos. Ao selecionar, apenas indicar sucesso visual depois de confirmação de acesso e recuperação do owner; resultados expirados invalidam a seleção.

Ações de menu são intents distintas de navegação: `pin|unpin|rename|archive|delete` não podem ser deduzidas de metadata de UI/agent/tool nem habilitadas sem live AuthZ, Domain rule, idempotência/audit/postcondition. Não usar optimistic update que antecipe aceite material sem rollback aprovado. Reusar primitives de list item, menu e tooltip existentes; `TO_INVENTORY` para equivalentes não conferidos.
