# E8 / WF-06 — smoke federado live

- Data: 2026-09-21
- Ambiente: Portal de produção `https://minhadelpi.com.br` (jornada no shell, MFE federado)
- Artefato MFE: `App-DF39uenx.js`, `Last-Modified: Mon, 21 Sep 2026 14:45:50 GMT`
- Código de Suprimentos nesse artefato: contido em `e8afa67ab`, ancestral de `24ee4ad48`. Commits posteriores a `38fd8c097` não alteram `plugins/supplies` nem `supplies-api`.
- O bundle local `App-omdSFLt9.js` (`Last-Modified: Fri, 18 Sep 2026 17:35:18 GMT`) não foi o ambiente deste gate.

## Rota e chave

- Lista: `/apps/supplies/purchase-orders`
- Detalhe: `/apps/supplies/purchase-orders/01/****175` (pedido aberto real da lista; número mascarado)
- Inexistente: `/apps/supplies/purchase-orders/01/ZZZNOTEXIST`

## Happy path

Portal autenticado por SSO, shell íntegro, MFE Suprimentos carregado. A lista chamou `GET /apps/supplies-api/purchase-orders` com 200. A seleção abriu a ficha: cabeçalho, filial, fornecedor, item, emissão, data prometida, SC de origem e seção de recebimentos. Um item. Sem erro material de console e sem `is not a function` do kit compartilhado.

## URL / histórico

- F5 na ficha manteve o path e voltou a renderizar o detalhe, com novo `GET` do BFF 200.
- Back retornou a `/apps/supplies/purchase-orders`.
- Forward, após um único back, retornou à ficha.

## Negativos

| Caso | Resultado |
|---|---|
| Chave inexistente | BFF 404, corpo `detail = Not Found`. UI: «Pedido não encontrado ou fora do universo em aberto…». Shell permanece. |
| Unidade fora do escopo | `INCONCLUSIVE`. Só havia uma identidade autorizada; não foi fabricado usuário nem permission. |
| Sem sessão | Deep link sem cookie termina em `/login` e não renderiza a ficha. `GET /apps/supplies-api/purchase-orders/01/000001` sem sessão responde 401. |

## Rede

Chamadas de dados da jornada: somente `/apps/supplies-api/purchase-orders` e `/apps/supplies-api/purchase-orders/01/…`. Nenhuma chamada do browser a `/apps/api-delpi`.

## Residuais

- 403 de unidade não executado.
- Tema e teclado não reexecutados; o desktop claro não mostrou regressão de federation.
- Viewport 390px: o card permaneceu no DOM; o frame capturado mostrou a sidebar do Portal ocupando a largura. Não é falha da ficha no desktop.

## Classificação

`GATE-FEATURE WF-06 = PASS`, com os residuais acima. Isso não autoriza E9 / WF-07.
