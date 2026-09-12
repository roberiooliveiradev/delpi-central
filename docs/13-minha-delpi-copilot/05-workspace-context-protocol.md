# 05 — Workspace Context Protocol

## 1. Objetivo

O Workspace Context Protocol permite que o Copilot compreenda onde o usuário está e quais entidades/filtros estão ativos sem exigir que ele repita o contexto manualmente.

## 2. Princípio

Não enviar o estado completo do frontend para a IA.

Cada app publica apenas um contexto estruturado, pequeno, útil e autorizado.

## 3. Contexto mínimo sugerido

```json
{
  "version": 1,
  "appId": "portal-comercial",
  "routeId": "customer-detail",
  "title": "Cliente",
  "entityRefs": [
    {
      "type": "customer",
      "id": "000123",
      "label": "Empresa XYZ"
    }
  ],
  "filters": {
    "branch": "01",
    "period": "2026-09"
  },
  "selection": null,
  "visibleDataRefs": [],
  "presentationState": {
    "tab": "overview"
  }
}
```

## 4. Campos

### `appId`

App ativo.

### `routeId`

Identificador semântico da rota, preferível a depender do path literal.

### `entityRefs`

Entidades atualmente abertas/selecionadas.

### `filters`

Filtros relevantes de negócio ou visão.

### `selection`

Seleção transitória útil, como linha ativa de uma tabela.

### `visibleDataRefs`

Referências a datasets/resultados que o Copilot pode recuperar por ID, em vez de receber todo o payload no contexto.

### `presentationState`

Estado visual útil como aba, visão ou agrupamento.

## 5. Publicação

Fluxo recomendado:

```text
MFE
→ WorkspaceContextAdapter
→ Portal WorkspaceContextBridge
→ contexto consolidado
→ minha-delpi-ai-api
```

O Portal Shell é o owner da agregação; cada MFE é owner apenas do contexto que publica.

## 6. Atualização

Publicar somente quando houver mudança semântica relevante:

- navegação;
- entidade selecionada;
- filtro aplicado;
- período alterado;
- aba relevante alterada.

Evitar enviar eventos para cada mudança de pixel/input não confirmado.

## 7. Uso conversacional

Exemplo:

Usuário está em um cliente e pergunta:

> “Mostre os pedidos atrasados dele.”

O Copilot usa `entityRefs.customer=000123` como contexto grounded.

Se o usuário disser:

> “Agora faça isso para o cliente 000987.”

O contexto explícito da mensagem substitui o contexto anterior.

## 8. Segurança e privacidade

- contexto só contém dados que a tela/usuário já pode acessar;
- não incluir token/JWT/secrets;
- não incluir dados invisíveis ao usuário apenas porque estão no store;
- respeitar classificação de dados sensíveis;
- logs devem evitar payloads completos quando não necessários.

## 9. Persistência

Separar:

```text
live workspace context
→ estado atual do browser

conversation working memory
→ estado conversacional persistível
```

O primeiro pode expirar quando app/rota muda. O segundo guarda apenas fatos que precisam sobreviver a reload/F5.

## 10. Context References

Para dados volumosos, preferir referências:

```json
{
  "visibleDataRefs": [
    {
      "refId": "dataset:orders:abc123",
      "type": "table",
      "description": "Pedidos em aberto do cliente 000123"
    }
  ]
}
```

O Copilot recupera a referência somente se necessário.

## 11. Versionamento

O contrato deve ter `version` e evolução compatível.

Mudanças breaking exigem versão nova e adaptação explícita no Shell.

## 12. Fallback

Se um MFE não publicar contexto:

- chat continua funcionando;
- o Copilot pode pedir informação faltante;
- Platform Actions básicas de app/rota continuam disponíveis;
- nunca inferir entidade sensível apenas pelo path.
