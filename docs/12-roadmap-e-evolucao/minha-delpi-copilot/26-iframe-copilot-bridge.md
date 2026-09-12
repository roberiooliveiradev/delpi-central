# Minha DELPI Copilot — Iframe Copilot Bridge

**Status:** arquitetura planejada / execução a partir de C0  
**Escopo:** integração segura do Copilot com apps `iframe` registrados na Minha DELPI  
**Princípio:** iframe não é exceção arquitetural; é um adapter de experiência com capacidades graduais.

## 1. Objetivo

Permitir que o Minha DELPI Copilot interaja com aplicações carregadas por `iframe` sem automação frágil de DOM, sem bypass de origem/RBAC e sem duplicar Business Actions que deveriam utilizar APIs/use cases.

A integração deve permitir, conforme maturidade do app:

- abrir o app/rota pelo Portal;
- receber contexto estruturado do iframe;
- navegar/focar views internas por comandos tipados;
- aplicar filtros/seleções suportados;
- abrir entidades por contrato;
- receber observations/resultados de comandos visuais;
- utilizar Business Actions por OpenAPI/API, não por clique no iframe.

## 2. Regra arquitetural principal

```text
NÃO:
Copilot
→ localizar DOM do iframe
→ preencher input
→ clicar botão

SIM:
Copilot
→ Platform Capability
→ CopilotBridge
→ IframeBridge
→ comando visual tipado
→ app iframe executa a experiência

E para negócio:
Copilot
→ Business Capability
→ OpenAPI / Action Catalog
→ policy / RBAC / confirmation
→ API / Use Case
```

O iframe bridge é para **experiência/contexto**, não para substituir APIs de negócio.

## 3. Classes de integração

Todo app `iframe` deve ser classificado em uma destas classes:

| Classe | Nome | Capacidade mínima |
|---|---|---|
| I0 | `PORTAL_ONLY` | Copilot descobre/abre app ou rota no Shell |
| I1 | `CONTEXTUAL` | I0 + iframe publica `WorkspaceContext` normalizado |
| I2 | `INTERACTIVE` | I1 + recebe comandos visuais tipados e retorna observations |
| I3 | `AI_READY` | I2 + Business Actions relevantes existem por API/OpenAPI governada |

A progressão não é automática. Cada nível exige evidence e testes.

## 4. Arquitetura

```text
                         Minha DELPI
┌────────────────────────────────────────────────────────┐
│ Copilot                                                │
│   │                                                    │
│   ▼                                                    │
│ Capability Projection / Planner                        │
│   │                                                    │
│   ▼                                                    │
│ PlatformCommand                                        │
│   │                                                    │
│   ▼                                                    │
│ CopilotBridge ────────────────┐                        │
│   │                           │                        │
│   ▼                           ▼                        │
│ Portal Router              IframeBridge                │
│                               │ postMessage            │
│                               ▼                        │
│                        ┌──────────────────┐             │
│                        │ app em iframe    │             │
│                        │ bridge adapter   │             │
│                        │ context/events   │             │
│                        └──────────────────┘             │
│                               │                        │
│                               ▼                        │
│                      WorkspaceContext Store            │
└────────────────────────────────────────────────────────┘

Business operation:
Copilot → Action Catalog/OpenAPI → policy → API/use case
```

## 5. Responsabilidades

### Portal `IframeBridge`

Responsável por:

- handshake;
- validação de `origin`;
- validação de `event.source`;
- associação iframe ↔ app registrado;
- validação de versão do protocolo;
- envio de comandos permitidos;
- recebimento/sanitização de contexto;
- correlação `requestId`;
- timeout;
- observabilidade;
- revogação da sessão do bridge quando iframe/app/rota deixa de ser válido.

Não deve:

- receber/entregar JWT como mensagem de integração;
- executar JavaScript recebido do iframe;
- aceitar `targetOrigin='*'` para mensagens sensíveis;
- transformar payload arbitrário em capability;
- conceder permissão de negócio.

### App iframe

Responsável por:

- implementar adapter/SDK do protocolo quando quiser I1+;
- declarar capacidades visuais suportadas;
- publicar apenas contexto bounded;
- validar comandos recebidos;
- executar somente commands suportados;
- retornar observation tipada;
- não tratar o bridge como autenticação/autorização de negócio.

### Copilot/AI API

Responsável por:

- selecionar apenas Platform Capabilities autorizadas/descobertas;
- trabalhar sobre contrato genérico, não sobre DOM/app específico;
- não inventar comando que o iframe não declarou;
- usar OpenAPI/Action Catalog para operações de negócio.

## 6. Handshake v1

O protocolo deve ter handshake explícito.

### 6.1 `HELLO`

Iframe → Portal:

```json
{
  "protocol": "delpi-iframe-copilot",
  "version": 1,
  "type": "hello",
  "appId": "app-canonic-id",
  "capabilities": [
    "context.publish",
    "view.open_entity",
    "view.set_filters"
  ]
}
```

### 6.2 Validação do Portal

O Portal deve comprovar:

```text
origin ∈ origins permitidas para o app
+ event.source === iframe.contentWindow esperado
+ appId corresponde ao iframe/rota carregado
+ app está autorizado em /me/apps
+ protocolo/version suportados
+ capabilities declaradas pertencem ao schema permitido
```

### 6.3 `BRIDGE_READY`

Portal → iframe:

```json
{
  "protocol": "delpi-iframe-copilot",
  "version": 1,
  "type": "bridge.ready",
  "sessionId": "opaque-id",
  "acceptedCapabilities": [
    "context.publish",
    "view.open_entity",
    "view.set_filters"
  ]
}
```

`sessionId` é correlação do bridge, não credencial de negócio.

## 7. Envelope de mensagem

Todas as mensagens após handshake usam envelope tipado:

```json
{
  "protocol": "delpi-iframe-copilot",
  "version": 1,
  "sessionId": "opaque-id",
  "requestId": "uuid",
  "type": "context.changed",
  "payload": {}
}
```

Campos obrigatórios:

```text
protocol
version
sessionId
requestId quando request/response
message type
payload schema validado
```

## 8. Publicação de contexto

Iframe I1+ pode publicar contexto visual bounded:

```json
{
  "protocol": "delpi-iframe-copilot",
  "version": 1,
  "sessionId": "opaque-id",
  "type": "context.changed",
  "payload": {
    "viewId": "production-order-detail",
    "entityRefs": [
      {
        "type": "productionOrder",
        "id": "OP123456",
        "label": "OP123456"
      }
    ],
    "filters": {
      "branch": "01"
    },
    "selection": []
  }
}
```

O Portal converte/sanitiza isso para `WorkspaceContextV1`.

O Copilot não precisa saber se o contexto veio de MFE nativo ou iframe.

## 9. Comandos visuais v1

O protocolo deve priorizar comandos genéricos:

```text
view.open_entity
view.set_view
view.set_filters
view.set_selection
view.focus_entity
view.refresh
```

Não criar comandos como:

```text
open_commercial_customer
click_totvs_approve_button
select_supplier_screen_x
```

### Exemplo

Portal → iframe:

```json
{
  "protocol": "delpi-iframe-copilot",
  "version": 1,
  "sessionId": "opaque-id",
  "requestId": "uuid",
  "type": "command",
  "payload": {
    "command": "view.set_view",
    "arguments": {
      "viewId": "operations"
    }
  }
}
```

Iframe → Portal:

```json
{
  "protocol": "delpi-iframe-copilot",
  "version": 1,
  "sessionId": "opaque-id",
  "requestId": "uuid",
  "type": "command.result",
  "payload": {
    "status": "succeeded",
    "observation": {
      "viewId": "operations"
    }
  }
}
```

## 10. Capability discovery

A capability de iframe deve resultar da combinação de fontes canônicas:

```text
Core /me/apps
→ app/rota autorizados

manifest/registration metadata
→ render type = iframe
→ origin/entry metadata aplicável

runtime handshake
→ capabilities visuais realmente suportadas

OpenAPI/Action Catalog
→ Business Actions
```

O handshake não concede acesso a app/rota. Ele apenas negocia integração visual para um app já autorizado.

## 11. Autenticação e SSO

O protocolo não deve transmitir token como solução de SSO.

Preferência:

```text
Portal autentica em Keycloak
Iframe/app autentica em Keycloak/SSO compatível
Bridge troca somente contexto/comandos de experiência
```

Proibido por padrão:

- token em query string;
- JWT no `postMessage`;
- refresh token no bridge;
- credencial técnica compartilhada com o iframe.

Se um legado exigir mecanismo diferente, deve existir análise de segurança explícita fora do protocolo genérico.

## 12. Segurança

Obrigatório:

- allowlist de origins por app;
- `event.source` validation;
- schema validation;
- versioning;
- capability allowlist;
- bounded payload;
- timeout;
- correlation IDs;
- rate limiting/throttling no bridge quando necessário;
- sanitização de contexto;
- não persistir secret/token;
- logs sem payload sensível;
- revalidação quando app/rota/permissão mudar;
- CSP/frame policies coerentes com os apps permitidos.

### Threats mínimos

Testar:

- mensagem de origin maliciosa;
- `appId` falso;
- iframe não autorizado tentando handshake;
- replay de `requestId`;
- payload oversize;
- comando não declarado;
- comando desconhecido;
- context injection;
- tentativa de enviar token;
- bridge session antiga após navegação/logout;
- iframe substituído/reciclado;
- permission revogada depois do handshake.

## 13. Apps externos/legados sem integração

Quando não for possível modificar o iframe:

```text
Classe = PORTAL_ONLY
```

O Copilot pode:

- descobrir app autorizado;
- abrir app/rota;
- explicar dados obtidos por fontes/API disponíveis fora do iframe.

Não prometer:

- leitura do DOM cross-origin;
- identificação da entidade interna atual;
- filtros internos;
- preenchimento de formulários;
- clique em botões.

Não criar hacks para contornar isolamento do navegador.

## 14. Apps `external`

Se o app abre fora do Shell/aba controlada, a integração padrão fica limitada a Platform Actions de abertura/navegação. Integração contextual/interactive exige canal explicitamente implementado e auditado pelo sistema externo.

## 15. Business Actions em apps iframe

Mesmo para I3/`AI_READY`:

```text
UI do iframe ─────────────┐
                          ▼
                     API / Use Case
                          ▲
Copilot ──────────────────┘
```

Exemplos de aprovar/cancelar/criar/editar devem usar Business Actions reais, com:

- OpenAPI;
- Action Catalog;
- RBAC;
- sensitivity;
- confirmation;
- idempotency quando aplicável;
- audit.

Nunca usar `view.click_button` como substituto de operação de negócio.

## 16. SDK planejado

Em C5, se C0 provar que não existe equivalente reutilizável, criar SDK/helper compartilhado conceitualmente como:

```text
@delpi/iframe-copilot-bridge
```

Responsabilidades do SDK:

- handshake;
- envelope/versioning;
- publisher de contexto;
- command handler registration;
- result/observation;
- schema/type helpers;
- lifecycle cleanup;
- test fixtures.

Não incluir business logic nem autorização de domínio.

## 17. Implantação no plano C0–C7

### C0

- inventariar todos apps `iframe` e `external`;
- mapear origins/SSO/ownership;
- congelar contrato `IframeBridgeV1`;
- incluir testes de origin/source/schema.

### C1

- `PORTAL_ONLY` para todos os iframes autorizados;
- `IframeBridge` no Portal para handshake básico;
- navegação segura.

### C2

- piloto `CONTEXTUAL`;
- iframe → `WorkspaceContextV1`;
- piloto `INTERACTIVE` com comando visual genérico;
- stale/logout/F5 tests.

### C3

- garantir que Business Actions do piloto não dependem de clique/DOM;
- paridade API/use case.

### C5

- SDK/template;
- scanner de readiness;
- unknown iframe test;
- onboarding em waves.

### C6/C7

- policies/observability/rollout e coverage final.

## 18. Readiness de iframe

A matriz de apps deve registrar adicionalmente:

```text
renderMode
iframeIntegrationClass
origin(s)
SSO mode
bridge protocol/version
context publish support
visual command support
declared capabilities
Business API/OpenAPI support
security owner
last bridge verification
```

## 19. Testes obrigatórios

### Positive

- handshake válido;
- contexto válido atualiza Workspace Context;
- comando declarado executa;
- observation correlacionada retorna;
- navegação `PORTAL_ONLY` funciona sem SDK.

### Sibling

- segundo iframe com outra origin/capabilities funciona sem patch central;
- app muda de `CONTEXTUAL` para `INTERACTIVE` por contrato, não hardcode.

### Negative

- origin inválida;
- source inválido;
- app não autorizado;
- capability não declarada;
- payload inválido/oversize;
- session expirada;
- permission revogada;
- command replay indevido;
- tentativa de business write por comando visual.

### Generalization

Cadastrar iframe fictício/novo no Core, com origin e capabilities compatíveis, e provar onboarding sem adicionar selector específico no planner/bridge.

## 20. Critérios de aceite

Um app iframe só pode ser declarado:

```text
PORTAL_ONLY
→ app/rota autorizados abrem de forma segura

CONTEXTUAL
→ PORTAL_ONLY + contexto tipado/seguro + lifecycle provado

INTERACTIVE
→ CONTEXTUAL + commands declarados + observations + negative security gates

AI_READY
→ INTERACTIVE + Business Actions via API/OpenAPI + RBAC/policy/confirmation + evals
```

`postMessage` funcionando não é suficiente para `AI_READY`.

## 21. Proibições

- DOM automation como arquitetura padrão;
- leitura cross-origin por workaround;
- `eval`/script execution recebido do iframe;
- `targetOrigin='*'` em integração sensível;
- JWT/refresh token em mensagens;
- command names por aplicativo no core genérico;
- Business Action implementada como clique;
- handshake usado como RBAC;
- contexto do iframe tratado como trusted instruction;
- capability declarada pelo iframe automaticamente autorizada sem Core/Portal validation.
