# 78 — DÉLIA: ConversationError / Error Recovery Surface

**Status:** `IMPLEMENTED / ACCEPTED_CURRENT_SCOPE` — componente visual implementado em `plugin-ui`, integrado na DÉLIA, com testes, build, federação e browser QA comprovados; não é evidência de runtime de produção nem autorização para ampliar fase.  
**Escopo:** superfície visual compartilhável para falhas reais da interação conversacional da DÉLIA, posicionada no footer do `ConversationWorkspace`, imediatamente acima do `MessageComposer`, preservando o rascunho e permitindo recuperação honesta.  
**Reanchor:** HEAD de elaboração `f53d52fab92aa202907b295ca8f7b41f0e6251d0`; implementação deve revalidar HEAD/status e a cadeia Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → specs temáticas → ledger.  
**Referências:** [73 — identidade e anatomia](./73-chat-first-visual-identity-and-message-anatomy-specification.md), [74 — Message Composer](./74-message-composer-visual-specification.md), [75 — mensagem DÉLIA](./75-assistant-message-visual-specification.md), [77 — workspace/header](./77-conversation-workspace-and-header-visual-specification.md).

## 1. Problema e significado

A DÉLIA já possui um estado local `error: string | null` no MFE. Quando uma tentativa de interação falha antes de produzir um turno autoritativo, o runtime atual:

1. mantém o texto digitado no composer;
2. não adiciona um turno de sucesso à timeline;
3. encerra o loading;
4. mostra um aviso `role="alert"` no footer, acima do composer;
5. permite que o usuário corrija/reenvie a mensagem.

Hoje o chrome é local:

```text
plugins/delia/src/App.tsx
→ <p className="delia-interaction__error" role="alert">...</p>

plugins/delia/src/index.css
→ .delia-interaction__error
```

**ConversationError representa exatamente:** “esta interação não pôde ser concluída; o usuário continua no controle e pode se recuperar”.

Ele não representa um novo turno, uma resposta da DÉLIA, nem um outcome de negócio.

## 2. Semântica: quando aparece

`ConversationError` deve ser usado somente para falhas de interação que impedem a conclusão normal do request atual, por exemplo:

- falha de rede/transporte;
- timeout da chamada;
- resposta HTTP/runtime que o adapter converte em erro de interação;
- falha inesperada no submit;
- pré-requisito técnico local ausente para enviar (por exemplo, token de acesso indisponível no momento), quando o MFE já o trata como erro de interação;
- falha de demo/harness que representa explicitamente o mesmo caminho de erro, sempre marcada pelo contexto de demo já existente.

A fonte do erro e sua copy continuam sendo responsabilidade do consumer/DÉLIA. O componente visual **não classifica** exceções, status HTTP, códigos de provider ou mensagens de backend.

## 3. Quando NÃO aparece

Não usar `ConversationError` para estados que já têm outra semântica/owner:

| Situação | Superfície correta | Motivo |
| --- | --- | --- |
| `SOURCE_UNAVAILABLE` em `presentation.v1` | `ConversationStatus` + conteúdo da resposta | é estado semântico de uma resposta concluída, não falha do transporte UI |
| `AUTHZ_DENIED` | `ConversationStatus` + resposta autoritativa | autorização é backend/domain/Core, não erro genérico de UI |
| `WRITE_REJECTED` | `ConversationStatus` | recusa governada é outcome/estado semântico |
| `CONFIRMATION_REQUIRED` | `ConversationStatus` + `GovernedConfirmation` | confirmação ≠ erro |
| request pendente | `ActivityViewer`/loading | loading ≠ falha |
| capability/tool em execução | `ActivityViewer` | atividade ≠ erro |
| erro de campo/validação local do próprio input | primitive de form/composer apropriado | não criar alerta global se o problema é do campo |
| sucesso técnico ou business outcome | resposta/outcome correspondente | erro nunca representa sucesso |

Regra forte:

```text
transport/runtime interaction failure != semantic response state
error != authorization
error != outcome
error != activity
error != confirmation
```

## 4. Posição na experiência

A posição canônica atual é o **footer do ConversationWorkspace, imediatamente acima do composer**.

```text
┌───────────────────────────────────────────────────────┐
│ ConversationHeader                                    │
├───────────────────────────────────────────────────────┤
│                                                       │
│ timeline / reception / ActivityViewer                 │
│                                                       │
├───────────────────────────────────────────────────────┤
│ ⚠ Não foi possível concluir esta solicitação.         │
│   Sua mensagem foi preservada.   [Tentar novamente]*  │
│                                                       │
│ [ composer multiline                           Enviar ]│
└───────────────────────────────────────────────────────┘
* ação opcional; só existe com callback real
```

Motivo: no fluxo atual, o turno do usuário só é adicionado à timeline quando o submit produz resultado. Em falha, o draft permanece no composer; portanto transformar o erro em “turno” criaria uma relação causal falsa.

Se o contrato de turnos mudar no futuro e passar a registrar tentativas falhas como entidades próprias, isso exige revisão temática; não mover silenciosamente o erro para a timeline.

## 5. Aparência

Direção aprovada:

- pequeno e inline;
- subordinado à conversa;
- largura da coluna de leitura, não viewport inteira;
- fundo muito sutil com tonalidade de danger;
- borda fina de danger;
- cantos arredondados coerentes com o design system;
- ícone de alerta pequeno à esquerda;
- título curto em texto principal;
- descrição opcional em texto secundário;
- ação de recuperação opcional, visualmente secundária;
- sem sombra pesada;
- sem card corporativo grande;
- sem cabeçalho “ERRO CRÍTICO”;
- sem animação contínua;
- sem vermelho saturado dominando a conversa.

### Light

```text
surface ≈ superfície base + pequena mistura de danger
border  ≈ danger em baixa opacidade
icon    ≈ danger legível
title   ≈ text principal
detail  ≈ text-muted
```

### Dark

```text
surface ≈ superfície escura + pequena mistura de danger
border  ≈ danger discreto
icon    ≈ danger com contraste
title   ≈ texto claro
detail  ≈ texto secundário legível
```

Nunca usar fallback claro fixo que produza card branco no dark.

## 6. Densidade full-page e dock

Um único componente deve atender ambos.

### Full page
- espaçamento confortável;
- título + descrição podem ficar em duas linhas;
- ação opcional pode permanecer à direita ou abaixo quando necessário;
- largura acompanha a coluna do footer.

### Dock / narrow
- densidade `compact`;
- ícone + título continuam visíveis;
- descrição pode quebrar naturalmente;
- ação opcional vai para a linha seguinte quando necessário;
- zero overflow horizontal;
- não esconder a mensagem essencial;
- não criar variante funcional separada.

Wireframe compacto:

```text
⚠ Não foi possível concluir.
  Sua mensagem foi preservada.
  [Tentar novamente]
```

## 7. Recovery e retry

**Draft preservation é comportamento do consumer, não do componente.** A implementação atual já preserva `input` quando `sendTurn` falha.

A recuperação mínima já disponível é: usuário mantém o draft e pode pressionar `Enviar` novamente.

Por isso, um botão explícito **Tentar novamente é OPTIONAL**, não obrigatório.

Só renderizar ação de retry quando:
- a DÉLIA fornecer callback real;
- repetir a operação for semanticamente seguro naquele contexto;
- não houver risco de duplicar uma ação material de forma silenciosa;
- o callback reutilizar o fluxo normal de submit/gates;
- loading desabilitar a ação para impedir double submit.

Nunca implementar retry automático.

Para confirmation/PREPARE/ACT, retry exige preservar os mesmos gates do fluxo governado; o componente visual não pode reconstruir payload, digest, sessão ou autorização.

## 8. Reuse Gate documentado

Inventário no HEAD de elaboração:

| Candidato | EXISTING_EQUIVALENT | REUSE_DECISION | Razão |
| --- | --- | --- | --- |
| `ActionButton` | YES | REUSE | primitive canônico para ação opcional de recovery |
| `StateBox` | PARTIAL | DO_NOT_REUSE_DIRECTLY / possible composition reference | possui chrome de aviso, mas traz dismiss local e torna error tonal dismissível por default; esconder erro sem consumer limpar estado não é o contrato desejado |
| `StateBanner` | PARTIAL | DO_NOT_REUSE_DIRECTLY | usa `role="status"` inclusive em error e exige classNames do consumer; sem anatomia de recovery |
| `InfoStatePanel` | PARTIAL | DO_NOT_REUSE_DIRECTLY | painel mais pesado, heading `h3` e botão próprio; linguagem visual inadequada para aviso conversacional compacto |
| `MessageComposer.error` | PARTIAL | DO_NOT_USE_AS_FULL_EQUIVALENT | já renderiza texto `role="alert"`, mas acoplar recovery/action ao composer confundiria responsabilidade; DÉLIA hoje mantém o erro como sibling no footer |
| `ConversationError` | NO | NEW, condicionado ao Abstraction Gate | composição conversacional específica para erro + recovery, sem estado de negócio |

**EXISTING_EQUIVALENT = NO** para a composição completa.  
**REUSE_DECISION = NEW** para `ConversationError`, reutilizando `ActionButton` e tokens/primitives existentes. A implementação ainda precisa revalidar o inventário no HEAD.

## 9. Abstraction Gate

Antes de implementar, provar novamente:

1. existe consumer real? **SIM:** DÉLIA já renderiza erro local no footer;
2. existe boundary legítima? **SIM:** chrome genérico em `plugin-ui`, erro/draft/retry na DÉLIA;
3. equivalente completo existente? **NÃO no HEAD documentado**;
4. reduz duplicação/coupling? **SIM:** remove `.delia-interaction__error` genérico do produto;
5. algo mais simples basta? `MessageComposer.error` cobre texto, mas não separa recovery e owner do erro; se a implementação optar por não ter ação/recovery, deve reavaliar se extrair componente ainda é necessário;
6. provider mechanics ficam fora? **REQUIRED**;
7. read/write, PREPARE/ACT e auth permanecem preservados? **REQUIRED**.

Se o inventário futuro mostrar que `StateBox` foi evoluído para cobrir exatamente esse contrato sem os problemas acima, a decisão pode mudar para `EXTEND/REUSE`. Não duplicar por inércia.

## 10. API alvo mínima

API conceitual, não congelada até implementação:

```ts
type ConversationErrorDensity = "comfortable" | "compact";

type ConversationErrorProps = {
  title: string;
  description?: ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  actionDisabled?: boolean;
  loading?: boolean;
  density?: ConversationErrorDensity;
  className?: string;
};
```

Alternativa legítima: `action?: ReactNode` se o padrão do design system favorecer slot em vez de callback.

Regras:
- não aceitar Error object bruto;
- não aceitar HTTP status para classificar visualmente;
- não conhecer `DeliaInteractionError`;
- não aceitar token/session/JWT;
- não aceitar `message_kind`;
- não aceitar provider/tool metadata;
- não possuir retry automático;
- não persistir erro.

## 11. Ownership

### plugin-ui
OWNS:
- estrutura visual;
- ícone/chrome;
- layout;
- density;
- tokens;
- responsividade;
- semântica acessível `role="alert"`;
- apresentação da ação opcional.

DOES NOT OWN:
- detecção/classificação do erro;
- copy específica de domínio;
- draft;
- retry policy;
- API call;
- session;
- auth;
- permissions;
- PREPARE/ACT;
- idempotência;
- outcome.

### DÉLIA
OWNS:
- receber/normalizar a falha de interação;
- decidir quando existe erro;
- fornecer title/description seguros;
- preservar draft;
- decidir se retry explícito existe;
- fornecer callback;
- loading/double-submit guard;
- remover o erro quando o estado real muda.

### Authorities externas
- Keycloak continua identidade/SSO;
- Core continua permissionamento/governança;
- Domain API continua regra/authority de negócio;
- backend DÉLIA continua orchestration/presentation;
- erro visual nunca concede permissão.

## 12. Acessibilidade

Required:
- raiz com `role="alert"` para falha nova relevante;
- não duplicar outro `role="alert"` com a mesma mensagem;
- ícone decorativo `aria-hidden`;
- título textual comunica a falha sem depender de cor;
- ação usa `ActionButton`/controle nativo com nome estável;
- focus-visible;
- sem autofocus;
- sem focus trap;
- sem deslocar foco automaticamente para o erro;
- ordem DOM: erro antes do composer no footer;
- zoom 200% sem clipping;
- reduced-motion sem animação decorativa.

Se o erro persistir durante múltiplos renders, evitar reanúncios artificiais causados por remount desnecessário.

## 13. Segurança e privacidade

A superfície deve exibir somente copy já considerada adequada ao usuário.

Não renderizar:
- stack trace;
- exception repr;
- URL interna;
- bearer token;
- cookie;
- JWT;
- provider credentials;
- raw MCP payload;
- proposal handle;
- proposal digest/fingerprint/session ID;
- control-plane metadata;
- prompt/model internals.

`DeliaInteractionError.message` só pode ser exibida se o adapter já for a boundary que produz mensagem user-safe; implementação deve confirmar isso em testes. Caso contrário, mapear para copy segura no owner correto — nunca sanitizar por regex no componente visual.

## 14. Relação com MessageComposer

O erro é sibling do composer, não parte da textarea.

```text
ConversationWorkspace.footer
├── ConversationError?   ← falha/recovery
└── DeliaComposer
    └── MessageComposer  ← draft/input/submit
```

O `MessageComposer.error` existente continua útil para consumers que desejem erro estritamente pertencente ao próprio composer. Na DÉLIA, a spec prefere `ConversationError` porque a falha pertence à **interação**, não ao campo.

Não renderizar o mesmo erro nos dois lugares.

## 15. Estados visuais previstos

| Estado | Visual | Ação |
| --- | --- | --- |
| erro simples | icon + title | nenhuma |
| erro com contexto | icon + title + description | nenhuma |
| erro recuperável | icon + title + description | action opcional |
| retry pendente | mesma superfície | action disabled/loading; composer segue política do consumer |
| erro resolvido | superfície some | nenhum optimistic success |
| aborted/unmount | normalmente nenhuma superfície nova | consumer decide; abort técnico não deve virar erro falso |

Não criar variant `success` neste componente. Sucesso pertence a outras superfícies/estado real.

## 16. Copy guidance

Preferir linguagem curta, factual e recuperável.

**Título recomendado:**
```text
Não foi possível concluir esta solicitação.
```

**Descrição quando factual:**
```text
Sua mensagem foi preservada.
```

**Ação opcional:**
```text
Tentar novamente
```

Evitar:
- “Erro crítico” sem criticidade real;
- “A DÉLIA falhou”;
- “Operação cancelada” se não houver outcome;
- “Sem permissão” sem AUTHZ autoritativo;
- “Tente novamente” se repetir puder duplicar write;
- códigos técnicos como mensagem principal.

## 17. Motion

Default: nenhum movimento contínuo.

Permitido:
- entrada/fade discreto somente se padrão compartilhado já existir;
- `prefers-reduced-motion: reduce` remove transições decorativas.

Proibido:
- shake repetido;
- pulse infinito;
- piscar;
- countdown fictício;
- spinner dentro do erro se não há retry real em andamento.

## 18. Testes obrigatórios da implementação futura

### Unit/component
- title;
- description opcional;
- action opcional;
- sem action quando faltam label/callback;
- loading/disabled;
- compact;
- className;
- `role="alert"`;
- ícone decorativo;
- conteúdo hostil inerte;
- sem business types/imports.

### DÉLIA integration
- falha mantém draft;
- falha não cria turno falso;
- erro aparece acima do composer;
- novo submit limpa/atualiza erro conforme comportamento existente;
- sucesso subsequente limpa erro;
- abort não cria erro;
- no duplicate alerts;
- retry opcional, se implementado, usa fluxo real e respeita loading;
- confirmation/governed write não é convertido em erro genérico.

### Browser QA
- full page;
- dock real ou harness legítimo;
- light;
- dark;
- 420px;
- 320px;
- zoom 200%;
- mensagem curta e longa;
- conteúdo grande;
- teclado;
- focus visible da action;
- composer ancorado;
- sem horizontal overflow;
- contraste;
- leitor de tela, se disponível.

## 19. Acceptance criteria

```text
[ ] reanchor real
[ ] reuse gate revalidado
[ ] StateBox/StateBanner/InfoStatePanel/MessageComposer.error comparados
[ ] EXISTING_EQUIVALENT / REUSE_DECISION registrados
[ ] plugin-ui presentation-only
[ ] DÉLIA mantém error/draft/retry ownership
[ ] local .delia-interaction__error removido apenas após integração real
[ ] role=alert único
[ ] no duplicate error in MessageComposer
[ ] full page PASS
[ ] dock/narrow PASS
[ ] light/dark PASS
[ ] zoom 200 PASS
[ ] no overflow
[ ] draft preservation PASS
[ ] no false turn
[ ] no automatic retry
[ ] no secret/internal metadata leak
[ ] tests/build/federation PASS
[ ] catálogo plugin-ui atualizado
[ ] doc 73 atualizado com status factual
[ ] ledger somente após outcome factual, sem avanço de fase por documentação
```

## 20. Status factual desta documentação

```text
COMPONENT = ConversationError
PRODUCT_MEANING = SPECIFIED
VISUAL_DIRECTION = APPROVED_FOR_PLANNING
CURRENT_LOCAL_ERROR_SURFACE = PROVEN
PLUGIN_UI_COMPONENT = IMPLEMENTED
DELIA_INTEGRATION = IMPLEMENTED
BROWSER_QA = PASS (local harness)
BUILD/FEDERATION = PASS
DEPLOY = NOT_PERFORMED
PHASE_ADVANCEMENT = NONE
```

Esta spec autoriza apenas o planejamento bounded do componente visual. A execução deve voltar ao HEAD real, repetir reuse/abstraction gate e produzir evidência antes de declarar `IMPLEMENTED` ou `ACCEPT`.
