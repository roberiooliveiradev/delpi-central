# 05 — Workspace Context Protocol

## 1. Objetivo

Permitir que o Copilot compreenda onde o usuário está e quais entidades/filtros estão ativos sem receber o estado inteiro do frontend.

## 2. Foundation

`WorkspaceContext` e `EntityRef` são primitives compartilhados definidos/reutilizados em C0. MFE, iframe, Portal e AI usam a mesma semântica.

## 3. Contrato conceitual

```json
{
  "version": 1,
  "appId": "portal-comercial",
  "routeId": "customer-detail",
  "entityRefs": [
    {
      "entityType": "customer",
      "entityId": "000123",
      "sourceSystem": "commercial-api",
      "label": "Empresa XYZ"
    }
  ],
  "filters": {
    "branch": "01",
    "period": "2026-09"
  },
  "selection": [],
  "dateRange": null,
  "visibleDataRefs": [],
  "presentationState": {"tab":"overview"},
  "source": "mfe",
  "updatedAt": "ISO-8601"
}
```

O shape final depende do C0 inventory; não criar variante por app.

## 4. Conteúdo permitido

### App/route
Identidade lógica do workspace atual.

### EntityRefs
Referências compartilhadas, não cópias completas de objetos.

### Filters/dateRange
Apenas filtros semanticamente relevantes.

### Selection
Seleção transitória útil.

### visibleDataRefs
Referências recuperáveis a datasets/resultados, sem embutir payload grande.

### presentationState
Estado visual útil como aba/view.

### source
Provenance do contexto (`portal`, `mfe`, `iframe` ou equivalente canônico).

## 5. Publicação

```text
MFE/Iframe
→ adapter validation/sanitization
→ Portal Context Store
→ bounded WorkspaceContext
→ AI turn input
```

Portal é owner da agregação. App é owner somente do contexto que publica.

## 6. Lifecycle

Atualizar em mudanças semânticas:

- app/route;
- entity;
- filters/date range;
- selection;
- view relevante.

Não emitir por mudança irrelevante de pixel/input não confirmado.

Ao desmontar app/iframe, limpar/invalidate context conforme lifecycle.

## 7. Precedência

Contexto explícito novo na mensagem/UI prevalece sobre memória/contexto antigo.

Exemplo:

```text
Workspace: customer 000123
User: “faça isso para o cliente 000987”
→ 000987 vence para aquele objetivo
```

## 8. Segurança

Workspace Context:

- é dado não confiável para system/policy;
- não concede permission;
- não inclui JWT/token/secret;
- não inclui hidden store data só porque frontend possui;
- não substitui backend/RBAC;
- deve ser bounded/sanitizado;
- logs evitam full sensitive payload.

## 9. Persistência

Separar:

```text
live workspace context
→ efêmero/browser/Portal

bounded conversation snapshot
→ somente quando necessário para continuidade
```

Não persistir estado React/DOM.

Task/Case/Workflow usam refs compartilhadas, não snapshot ilimitado do workspace.

## 10. visibleDataRefs

Exemplo:

```json
{
  "refId":"dataset:orders:abc123",
  "kind":"table",
  "description":"Pedidos em aberto do cliente 000123"
}
```

O ref precisa owner/lifecycle/access check antes de ser recuperado.

## 11. Iframe

Iframe I1+ publica contexto pelo protocolo `26-iframe-copilot-bridge.md`; Portal converte para o mesmo `WorkspaceContext`.

O AI core não precisa conhecer tecnologia visual de origem.

## 12. Versionamento

Breaking changes exigem versão/adapters explícitos. Não criar “WorkspaceContextV2” local apenas para uma feature.

## 13. Fallback

Sem context adapter:

- chat funciona;
- open app/route funciona;
- Copilot pede required info ausente;
- não inferir entidade sensível pelo path/DOM.

## 14. Testes mínimos

- valid context;
- unknown field;
- oversize;
- secret/JWT;
- stale app/entity;
- F5/logout;
- MFE sibling;
- iframe source;
- explicit context override;
- unauthorized entity ref não vira data access.