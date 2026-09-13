# 05 — Workspace Context Protocol

## 1. Objetivo

Permitir que a DÉLIA compreenda onde o usuário está e quais entidades/filtros estão ativos sem receber o estado inteiro do frontend.

## 2. Foundation

`WorkspaceContext` e `EntityRef` são **primitives TARGET** a confirmar/reutilizar/criar no owner correto em C0. MFE, iframe, Portal e DÉLIA devem convergir para a mesma semântica somente após o contract ser congelado.

A presença desses nomes na documentação não prova implementação atual.

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
Identidade lógica do workspace atual publicada pelo host/app conforme contrato.

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

## 5. Publicação e ownership

Target flow:

```text
MFE/Iframe
→ adapter validation/sanitization
→ Portal host/context transport
→ bounded WorkspaceContext
→ DÉLIA contextualization
```

Ownership deve permanecer separado:

```text
Portal = host/navigation/published app context transport
App/MFE = owner dos fatos de view/context que publica
Domain/source = owner dos fatos de negócio referenciados
DÉLIA = owner da contextualização/intelligence state derivada sobre refs autorizadas
```

Portal não vira source of truth de fatos operacionais apenas por agregar/publicar contexto. DÉLIA não ganha permission pelo contexto recebido.

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

Contexto explícito novo na mensagem/UI prevalece sobre memória/contexto antigo, sem substituir validação autoritativa.

Exemplo:

```text
Workspace: customer 000123
User: “faça isso para o cliente 000987”
→ 000987 vence como referência para aquele objetivo
→ acesso/estado real ainda é revalidado no owner autoritativo
```

## 8. Segurança

Workspace Context:

- é dado não confiável para system/policy;
- não concede permission;
- não inclui JWT/token/secret;
- não inclui hidden store data só porque frontend possui;
- não substitui backend/RBAC/domain validation;
- deve ser bounded/sanitizado;
- logs evitam full sensitive payload;
- device/provider/tool metadata dentro do contexto não amplia authority.

## 9. Persistência

Separar:

```text
live workspace context
→ efêmero/browser/host transport

bounded DÉLIA conversation/work snapshot
→ somente quando necessário para continuidade e com refs apropriadas
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

O ref precisa owner/lifecycle/access check antes de ser recuperado. Ref metadata nunca é permission proof.

## 11. Iframe

Iframe I1+ pode publicar contexto pelo protocolo histórico/técnico `26-iframe-copilot-bridge.md` se esse contract for confirmado/aprovado. Portal normaliza para o mesmo `WorkspaceContext` target.

O core da DÉLIA não precisa conhecer tecnologia visual de origem.

## 12. Versionamento

Breaking changes exigem versão/adapters explícitos. Não criar “WorkspaceContextV2” local apenas para uma feature.

## 13. Fallback

Sem context adapter:

- experiência conversacional pode continuar;
- open app/route pode continuar se o platform contract existir;
- DÉLIA pede required info ausente;
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
- unauthorized entity ref não vira data access;
- provider/device/tool metadata não vira permission;
- Portal context aggregation não substitui source truth.
