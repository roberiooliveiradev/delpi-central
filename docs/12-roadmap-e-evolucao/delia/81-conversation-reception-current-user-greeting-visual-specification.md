# 81 — DÉLIA: Conversation Reception + Current User Greeting

**Status:** `IMPLEMENTED / INTEGRATED_IN_DELIA` — `ConversationReception` implementado em `plugin-ui` e consumido por `DeliaReception` com greeting nominal via identidade Core já publicada; não é evidência de produção, não avança fase e não autoriza personalização além dos contratos atuais.  
**Implementado em:** task `DELIA-UX-CONVERSATION-RECEPTION-CURRENT-USER-GREETING-01` sobre HEAD `8786b605ae2ca3b108c31d64cc1cf32748a13c5f`.  
**Escopo:** recepção da conversa antes do primeiro turno, com greeting opcional baseado na identidade legítima já publicada pela plataforma.  
**Reanchor:** HEAD de elaboração `96e877cea61d6c4fe9260e1873b6ef0283d50f5c`; implementação futura deve revalidar HEAD/status e a cadeia Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → specs temáticas → ledger.  
**Referências:** [50 — arquitetura standalone](./50-standalone-copilot-application-architecture.md), [73 — identidade/anatomia chat-first](./73-chat-first-visual-identity-and-message-anatomy-specification.md), [76 — Unified Avatar](./76-unified-avatar-visual-specification.md).

## 1. Estado factual atual

No HEAD de elaboração existe:

```text
plugins/delia/src/identity/currentUser.ts
```

com consumo já implementado de contratos Core existentes:

```text
GET /core-api/me
→ { name }

GET /core-api/me/person-profile
→ { has_photo }

GET /core-api/me/person-profile/photo
→ image blob
```

A DÉLIA já usa essa identidade para apresentação do avatar do usuário na conversa.

Também existe a recepção local:

```text
plugins/delia/src/ui/DeliaReception.tsx
```

com copy genérica:

```text
Como posso ajudar você hoje?

Converse com a inteligência operacional da DELPI.
As respostas dependem das informações e permissões disponíveis no momento.

A conversa é mantida apenas nesta tela e não é salva.
```

## 2. Decisão de produto

A recepção deve poder reconhecer o usuário nominalmente quando `displayName` legítimo estiver disponível.

Exemplo:

```text
        [avatar DÉLIA]

Bom dia, Robério.

Como posso ajudar você hoje?

Converse com a inteligência operacional da DELPI.
As respostas consideram as informações e permissões
disponíveis para você neste momento.

A conversa é mantida apenas nesta tela e não é salva.
```

Fallback quando nome não estiver disponível:

```text
        [avatar DÉLIA]

Como posso ajudar você hoje?
```

Nenhum nome deve ser inferido, inventado ou derivado de claims não aprovadas para apresentação.

## 3. Três níveis de conhecimento sobre o usuário

### 3.1 Identidade

Já há evidência de identidade de apresentação:

```text
displayName
profile photo when available
current authenticated user context
```

Isso permite greeting e avatar.

### 3.2 Contexto operacional

Pode ser usado somente quando publicado por contratos legítimos, por exemplo:

```text
app atual
rota/tela atual
entidade em foco
unidade/contexto operacional
permissões efetivas
Work/Task atribuídos
```

Esse contexto é separado da identidade.

Exemplo futuro permitido somente com contexto real:

```text
Bom dia, Robério.

Vi que você está na OP 12345.
Posso ajudá-lo a analisar esta ordem ou responder outra pergunta.
```

Não inventar contexto a partir de rota parcial, JWT, memória ou heurística.

### 3.3 Personalização / Personal Memory

Futura e governada.

Pode eventualmente suportar preferências como:

```text
respostas mais objetivas
mais ou menos proatividade
formato preferido de apresentação
```

Mas:

```text
Personal Memory != autorização
Personal Memory != live domain fact
Personal Memory != cargo oficial
Personal Memory != permissão
```

Esta spec não implementa Personal Memory.

## 4. Limites de autoridade

Reconhecer o usuário visualmente não autoriza nada.

Preservar:

```text
nome != autorização
foto != autenticação adicional
cargo conhecido != permissão atual
JWT != permissão final
memória != verdade operacional
frontend identity != AuthZ
```

Fluxo de autoridade continua:

```text
Keycloak
→ identidade/SSO

Core
→ apps/rotas/RBAC/governança

Domain APIs
→ regra final de negócio

DÉLIA
→ inteligência/contexto/orquestração dentro dos gates
```

## 5. Aparência esperada

Direção principal:

```text
             [avatar DÉLIA]

          Bom dia, Robério.

     Como posso ajudar você hoje?

Converse com a inteligência operacional da DELPI.

As respostas dependem das informações e permissões
disponíveis para você neste momento.

A conversa é mantida apenas nesta tela e não é salva.
```

Características:

- centralizada no eixo de leitura;
- sem card externo;
- sem sombra;
- sem painel de dashboard;
- avatar DÉLIA como identidade principal;
- greeting menor que o título;
- título curto e claro;
- descrição discreta;
- nota de persistência ainda mais subordinada;
- mesmo componente full-page/dock com densidade adaptada.

## 6. Greeting

O greeting pode ser:

```text
Olá, Robério.
Bom dia, Robério.
Boa tarde, Robério.
Boa noite, Robério.
```

A definição de saudação temporal deve ser determinística e local à apresentação, usando horário confiável do cliente apenas para copy, sem efeito em regra de negócio.

Fallback:

```text
Olá.
```

ou simplesmente omitir greeting se o nome não estiver disponível.

Não usar apelido, primeiro nome derivado ou tratamento informal se o contrato atual só fornece um nome completo e não houver regra explícita de apresentação.

## 7. Reconhecimento do usuário

A recepção pode receber dados já resolvidos:

```ts
displayName?: string | null
imageUrl?: string | null
```

Mas o componente de chrome não deve fazer fetch.

Regra:

```text
Core → current user identity
DÉLIA → projection/greeting
ConversationReception → render
```

## 8. Reuse Gate

Inventariar no HEAD de implementação:

```text
DeliaReception
EmptyState
EmptyGuidance
UnifiedAvatar
ConversationReception
```

Estado no HEAD de elaboração:

```text
DeliaReception
EXISTING_EQUIVALENT = YES_LOCAL

UnifiedAvatar
EXISTING_EQUIVALENT = YES
REUSE_DECISION = REUSE

EmptyState
EXISTING_EQUIVALENT = TO_INVENTORY

EmptyGuidance
EXISTING_EQUIVALENT = TO_INVENTORY

ConversationReception
EXISTING_EQUIVALENT = NO_FULL_EQUIVALENT
REUSE_DECISION = TO_DECIDE_AFTER_INVENTORY
```

Não criar componente novo antes de provar que `EmptyState`/`EmptyGuidance` não cobrem a necessidade sem acoplamento ou chrome inadequado.

## 9. Abstraction Gate

Antes de extrair para `plugin-ui`, provar:

1. necessidade real de chrome conversacional próprio;
2. owner visual correto;
3. consumer real;
4. equivalente existente;
5. benefício de consistência com `ConversationWorkspace`, `ConversationUserMessage`, `ConversationError`, `GovernedConfirmation`, `EvidenceDetails`;
6. que a extração não carrega identidade/Core para dentro do kit.

Resultado aceitável:

```text
REUSE
EXTEND
NEW
KEEP_LOCAL
```

Não forçar `NEW`.

## 10. Ownership

### plugin-ui, se ConversationReception for criado

OWNS:

- layout;
- avatar slot;
- greeting slot/text;
- title;
- description;
- note;
- density;
- responsiveness;
- light/dark;
- accessibility.

DOES NOT OWN:

- fetch de usuário;
- Core;
- Keycloak;
- AuthZ;
- escolha de contexto operacional;
- memória;
- capability suggestions;
- permissão;
- greeting business semantics.

### DÉLIA

OWNS:

- quando a recepção aparece;
- copy;
- nome user-facing já resolvido;
- greeting;
- identidade visual já obtida;
- contexto adicional explicitamente publicado;
- desaparecimento após primeiro turno.

## 11. O que NÃO deve aparecer por default

Não mostrar sem contrato real:

- cargo;
- unidade;
- departamento;
- permissões;
- role;
- lista de capabilities;
- suggestions/chips;
- histórico;
- memória;
- tarefas;
- favoritos;
- contexto inferido;
- "você pode executar X".

A recepção não é um painel de perfil.

## 12. Relação com autorização

Mesmo que a recepção diga:

```text
Bom dia, Robério.
```

isso não altera:

```text
identity → live Core AuthZ → Domain authority → Policy/Decision
```

Nenhuma ação é autorizada pelo greeting.

## 13. Full page e dock

Mesma implementação.

### Full page

- avatar maior;
- maior respiro vertical;
- title e greeting separados;
- largura confortável.

### Dock

- avatar menor;
- spacing compacto;
- greeting pode quebrar em uma linha;
- descrição reduz densidade sem perder significado;
- note permanece legível;
- zero overflow horizontal.

## 14. Light / dark

Usar apenas tokens existentes do Portal/plugin-ui.

Sem fundos fixos, sem card branco em dark mode, sem cor especial por usuário.

## 15. Acessibilidade

Required:

- section com label ou heading claro;
- avatar decorativo quando o texto adjacente já identifica DÉLIA;
- nome do usuário como texto, não somente avatar;
- sem live region;
- sem autofocus;
- zoom 200%;
- 320px sem overflow;
- greeting não deve duplicar nome em leitores de tela de forma desnecessária;
- contraste adequado.

## 16. Privacidade

A recepção usa apenas identidade necessária à apresentação.

Não:

- persistir nome/foto na DÉLIA;
- logar bearer/token;
- colocar token em prompt;
- guardar foto em storage da DÉLIA;
- inferir atributos pessoais;
- inferir cargo, senioridade, personalidade ou preferência.

A foto continua como object URL transitória com cleanup, conforme implementação atual.

## 17. Segurança

A identidade visual é untrusted para autorização.

```text
displayName != actor permission
imageUrl != identity proof
profile photo != biometric authentication
```

Fallback neutro deve funcionar quando Core/profile estiver indisponível.

## 18. Context-aware greeting futuro

A arquitetura pode futuramente permitir:

```text
Olá, Robério.
Você está em Produção > OP 12345.
```

somente se o Portal publicar esse contexto por contrato legítimo.

O chrome deve aceitar contexto já projetado; não deve ler rota arbitrária ou consultar Domain APIs por conta própria.

## 19. API alvo conceitual

Não congelada:

```ts
type ConversationReceptionProps = {
  avatar?: ReactNode;
  greeting?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  note?: ReactNode;
  className?: string;
  density?: "default" | "compact";
};
```

O componente não deve receber:

```text
JWT
permissions
raw user object
Core response
WorkspaceContext raw
memory object
capability registry
```

## 20. Testes obrigatórios futuros

### plugin-ui, se extraído

- greeting presente;
- greeting ausente;
- avatar slot;
- title only;
- description/note opcionais;
- compact/default;
- long display name;
- hostile text inert;
- dark/light;
- 320px;
- zoom 200%;
- sem roles desnecessárias.

### DÉLIA

- displayName real recebido → greeting;
- ausência de displayName → fallback honesto;
- foto existente → avatar;
- sem foto → fallback;
- Core falha → recepção continua funcional;
- nenhum nome inventado;
- greeting desaparece com a recepção após primeiro turno;
- nenhuma permissão derivada do nome;
- nenhum capability suggestion inventado.

## 21. Estado factual

```text
CURRENT_USER_NAME_SOURCE = PROVEN (GET /core-api/me → name)
CURRENT_USER_PHOTO_SOURCE = PROVEN_WHEN_AVAILABLE
CURRENT_USER_IDENTITY_OWNER = CORE
DELIA_CURRENT_USER_PRESENTATION = PROVEN
DELIA_RECEPTION_LOCAL = REPLACED_BY_SHARED_COMPONENT
PERSONALIZED_GREETING = IMPLEMENTED — primeiro nome via projeção
  canônica `firstNameFromDisplay` (regra de apresentação já existente
  no kit/Portal, não heurística nova); período via `portalDayPeriodGreeting`
  com relógio injetável — LOCAL_BROWSER_TIME = PRESENTATION_ONLY;
  sem nome → greeting omitido (nada inventado)
CONVERSATION_RECEPTION_SHARED = IMPLEMENTED (plugin-ui)
  EMPTY_STATE = DO_NOT_REUSE (state/card semantics, role status/alert)
  EMPTY_GUIDANCE = DO_NOT_REUSE (role=status default obrigatório,
    sem slots greeting/note/avatar, TitleTag=p em canvas — semântica
    de "empty guidance" ≠ reception)
  SECOND_REAL_CONSUMER = NO (decisão arquitetural de consolidar
    chrome conversacional no kit — mesma família de
    ConversationWorkspace/GovernedConfirmation/EvidenceDetails)
AUTHORITY_CHANGE = NONE
MEMORY_CHANGE = NONE
BACKEND_CHANGE = NONE
PHASE_ADVANCEMENT = NONE

PLUGIN_UI_TESTS = 9/9 (ConversationReception.test.tsx)
DELIA_TESTS = 187/187 (inclui DeliaReception.test.tsx 8/8 — greeting
  determinístico com setSystemTime, fallback, hostile inert, sem
  live region, avatar decorativo)
PLUGIN_UI_BUILD + HOST_EXPORTS = PASS (ConversationReception exportado)
DELIA_BUILD + FEDERATION = PASS
BROWSER_QA = PASS (harness dev: com/sem nome, nome longo, dark tokens,
  320/420, zoom 200, composer ancorado, recepção some após 1º turno,
  avatar decorativo, sem leak de campos de identidade)
LOCAL_CSS_REMOVED = YES (delia-reception* removidas; residual limpo)
```

## 22. Próximo bounded step

```text
DELIA-UX-CONVERSATION-RECEPTION-CURRENT-USER-GREETING-01
```

Mode:

```text
REANCHOR
→ INVENTORY
→ REUSE GATE
→ ABSTRACTION GATE
→ IMPLEMENT OR KEEP LOCAL
→ INTEGRATE CURRENT USER
→ TEST
→ BROWSER QA
→ DOCUMENT
→ COMMIT
→ PUSH
→ REPORT
```

A implementação não deve transformar reconhecimento nominal em autorização, memória ou inferência sobre o usuário.
