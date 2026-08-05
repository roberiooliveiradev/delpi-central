# Chat embarcado (`EmbeddedChat`)

Superfície exposta por Module Federation (`./EmbeddedChat`) e consumida por hosts que
embutem o chat dentro da própria tela — hoje o painel **Copiloto IA** do TV Dashboard
(`plugins/tv-dashboard/src/components/TvCopilotSidePanel.tsx`).

## Princípio

O embed é **o mesmo `ChatPage`** do portal, em `variant="embedded"`. A única diferença é
o **host**: não existe URL própria e o layout é uma coluna com a sidebar em gaveta.
Nenhuma funcionalidade do chat deve ser desligada só por estar embarcada.

## Rota interna

O portal navega por `pushState`; o embed **não pode** mexer na URL do host (senão o
AppHost sai do TV Dashboard). Por isso `ChatPage` mantém uma rota interna:

| Peça | Papel |
|---|---|
| `setChatNavigationHostMode("embedded")` | Bloqueia `pushState` em `navigateChatHref` |
| `embeddedPathname` (estado em `ChatPage`) | Rota corrente do embed |
| `activePathname` | `embeddedPathname` no embed, `pathname` do host no portal |
| `navigateToChatSurface(href)` | Atualiza a rota interna **e** aplica a rota (`applyChatRoute`) |

Consequência prática: qualquer fluxo novo deve navegar por `navigateToChatSurface` —
`navigateChatHref` puro é **no-op** no embed e deixa a tela morta.

## Seleção de conversa

Itens de conversa (`ChatConversationListItem`) mantêm `href` para acessibilidade e
ctrl+clique, mas o clique esquerdo chama `onSelectSession` (`ChatPage.handleSelectSession`),
que funciona nos dois modos: portal atualiza a URL, embed persiste a sessão em
`localStorage` (`mdc.embedded.session.v1:{surface}:{playlist}`).

## Sidebar em gaveta

`isDrawer = isEmbedded || !isDesktop`. Nesse modo a marca mostra apenas **fechar** (X) —
o rail colapsável (chevron) é do portal em desktop e não existe no embed.

## Contexto do host

`workspaceContext` (playlist, slide, blocos selecionados, data sources) chega como
`hostContext` e vai ao pipeline da API. Comandos de TV Dashboard são resolvidos pelo
BFF (`suggest-ops` → `preview-patch` / `apply-patch`); o restante do chat segue igual.

## Contrato coberto por teste

`src/embeddedChatLayout.contract.test.ts` — layout em coluna, gaveta, rota interna,
seleção de conversa sem URL e ausência de bloqueios por `isEmbedded`.
