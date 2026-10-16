# 80 — DÉLIA: EvidenceDetails / Provenance Details

**Status:** `DESIGN_SPECIFIED / NOT_IMPLEMENTED` — aparência, semântica e boundary documentadas; não é evidência de runtime, não avança fase e não congela API antes da execução.  
**Escopo:** superfície conversacional secundária para apresentar fonte, provenance, classificação epistêmica, freshness/observed_at e limitações da resposta DÉLIA.  
**Reanchor:** HEAD de elaboração `7ff31715f4b0eb3b5531510bfce7a6f4e794cd36`; implementação futura deve revalidar HEAD/status e a cadeia Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → specs temáticas → ledger.  
**Referências:** [38 — Evidence/Provenance/Epistemic UX](./38-evidence-provenance-and-epistemic-ux.md), [73 — identidade/anatomia](./73-chat-first-visual-identity-and-message-anatomy-specification.md), [75 — mensagem DÉLIA](./75-assistant-message-visual-specification.md), [79 — ActivityViewer](./79-conversation-activity-summary-visual-specification.md).

## 1. Problema e significado

Hoje `DeliaAssistantMessage.tsx` apresenta localmente:

```text
Fonte · <source_system> · Consultado em <data>

Detalhes da evidência ▾
  classificação: <epistemicClass>
  fonte: <source> · <specialist>/<protocol> · <observed_at>
  limitações: ...
```

A responsabilidade visual ainda não está encapsulada em um componente compartilhado. O objetivo desta spec é definir a experiência antes de qualquer extração.

`EvidenceDetails` representa: **por que e com que contexto esta resposta pode ser verificada**.

Ele não representa: “quão certa a DÉLIA acha que está”.

## 2. Semântica epistêmica

As classes canônicas preservadas pelo doc 38 são:

```text
OBSERVATION
FACT
CALCULATION
HYPOTHESIS
CONCLUSION
RECOMMENDATION
```

Elas são tipos semânticos, não níveis ordinais de força ou qualidade.

```text
OBSERVATION != FACT
FACT != permission
RECOMMENDATION != authorization
epistemic class != confidence score
evidence != business outcome
```

A UI não transforma essas classes em badges de sucesso/perigo ou rankings implícitos.

## 3. Aparência fechada

```text
Fonte · Cadastro DELPI · consultado em 16/10/2026 14:32

Detalhes da evidência ▾
```

Características:

- linha de fonte pequena e legível;
- texto `text-muted`, com fonte/origem material claramente identificável;
- disclosure abaixo, discreto;
- sem card pesado;
- sem sombra;
- sem grande título “EVIDÊNCIA”;
- sem badge de confiança;
- sem duplicar `ActivityViewer`.

## 4. Aparência expandida

```text
Fonte · Cadastro DELPI · consultado em 16/10/2026 14:32

Detalhes da evidência ▴

Classificação   OBSERVATION
Fonte           Cadastro DELPI
Especialista    DAVI
Observado em    16/10/2026 14:32

Limitações
Dados sujeitos ao horário da última atualização.
```

Preferir estrutura semântica de pares label/valor (`dl/dt/dd`) e spacing leve. Não usar várias caixas aninhadas.

## 5. Hierarquia na mensagem

```text
DÉLIA / avatar
ActivityViewer               ← atividade observável
ConversationStatus?          ← estado semântico
Resposta                     ← conteúdo principal
Owner hint?                  ← notice quando real
GovernedConfirmation?        ← decisão governada
EvidenceDetails              ← provenance / classe / limitações
MessageActionBar             ← ações secundárias
```

`EvidenceDetails` deve ter peso visual menor que o texto da resposta e menor ou equivalente ao `ActivityViewer`.

## 6. Fonte resumida sempre visível

Quando a resposta é grounded e existe `source_system`, a fonte material deve ser legível sem abrir o disclosure.

```text
Fonte · Cadastro DELPI
```

Quando `observed_at` válido existir:

```text
Fonte · Cadastro DELPI · consultado em 16/10/2026 14:32
```

Não inventar timestamp, freshness ou source label.

## 7. Limitações materiais

Limitações materiais não devem ficar escondidas exclusivamente no disclosure fechado.

```text
Fonte · Cadastro DELPI
⚠ Há limitações nesta resposta
Detalhes da evidência ▾
```

A versão expandida pode listar as limitações completas.

A UI não decide sozinha se uma limitação é material; essa decisão deve vir da projeção/contrato legítimo ou de regra determinística autorizada. Até existir tal classificação, não inventar severidade.

## 8. NON_GROUNDED

Quando `groundingStatus === NON_GROUNDED`, a superfície pode informar de forma neutra:

```text
Sem fonte vinculada
```

Não transformar isso automaticamente em erro, warning ou baixa confiança.

## 9. Full page e dock

Mesma implementação.

### Full page

- linha de fonte pode permanecer em uma linha quando houver espaço;
- detalhes em grid leve de duas colunas label/value;
- limitações ocupam largura completa;
- alinhamento com o eixo da resposta DÉLIA.

### Dock/narrow

- fonte e data quebram naturalmente;
- detalhes migram para uma coluna vertical;
- labels ficam acima ou à esquerda conforme largura;
- zero overflow horizontal;
- disclosure permanece acessível;
- nenhuma segunda sidebar/painel.

## 10. Light / dark

Light:

```text
background = transparent
text = text
metadata = text-muted
divider = border sutil, somente se necessário
```

Dark:

- mesma hierarquia;
- fundo transparente;
- sem superfície branca;
- muted continua legível;
- nada de badge saturado para classe epistêmica.

## 11. Epistemic class visual

Preferência:

```text
Classificação   OBSERVATION
```

Evitar:

```text
[ OBSERVATION ✓ ]
[ FACT verde ]
[ HYPOTHESIS amarelo ]
```

Cor/ícone de sucesso ou warning pode sugerir força, aprovação, confiança ou qualidade que o contrato não declara.

## 12. Reuse Gate

Inventário no HEAD de elaboração:

| Candidato | EXISTING_EQUIVALENT | REUSE_DECISION | Evidência |
| --- | --- | --- | --- |
| Local `DeliaAssistantMessage` evidence block | YES, local | EXTEND/EXTRACT candidate | já renderiza fonte, classe e limitações |
| `DetailFieldGrid` | PARTIAL | REUSE_CANDIDATE | fornece `dl/dt/dd` acessível, mas não possui disclosure/provenance semantics |
| `DetailCard` | PARTIAL | DO_NOT_REUSE_AS_SURFACE | card/heading pesado para experiência chat-first |
| `InfoStatePanel` | PARTIAL | DO_NOT_REUSE_AS_SURFACE | semântica de estado/ação, não evidence disclosure |
| HTML `<details>/<summary>` | YES, primitive nativa | REUSE/REFERENCE | disclosure nativo já usado localmente |
| `EvidenceDetails` | NO full equivalent | NEW candidate after revalidation | composição específica ainda não existe no plugin-ui |

```text
EXISTING_EQUIVALENT = NO
REUSE_DECISION = NEW_CANDIDATE
REUSE DetailFieldGrid = PARTIAL_CANDIDATE
```

A implementação futura deve revalidar o HEAD. Se um equivalente compartilhado surgir, mudar para REUSE/EXTEND; não duplicar.

## 13. Abstraction Gate

Antes de criar componente compartilhado, provar novamente:

1. consumer real = DÉLIA;
2. owner visual = `plugin-ui` se a composição for genérica e reutilizável;
3. owner dos dados/projeção = DÉLIA/backend contracts;
4. equivalente completo = inexistente no HEAD de elaboração;
5. shared extraction reduz markup/CSS local sem transportar regra de domínio;
6. primitive simples não basta para fonte + disclosure + limitações de forma consistente;
7. nenhuma authority nova é criada.

Se só a DÉLIA continuar sendo consumer e nenhuma reutilização legítima adicional existir, avaliar se manter a composição local é mais correto que criar abstração compartilhada.

## 14. Ownership

### plugin-ui, se `EvidenceDetails` for criado

OWNS:

- estrutura visual;
- disclosure;
- layout de pares label/value;
- responsividade;
- acessibilidade;
- tokens;
- apresentação de notice de limitação quando explicitamente fornecido.

DOES NOT OWN:

- classificação epistêmica;
- promoção OBSERVATION→FACT;
- source truth;
- freshness;
- AuthZ;
- definição de materialidade;
- geração de limitations;
- provider parsing;
- business outcome.

### DÉLIA

OWNS:

- projeção de provenance para props user-facing;
- formatação de timestamps quando legitimamente disponível;
- labels seguros;
- decisão de quais campos podem ser expostos;
- dados de classe epistêmica recebidos do contrato;
- limitações recebidas/projetadas.

## 15. Segurança e privacidade

Não renderizar na superfície comum:

- bearer/JWT/cookie;
- credenciais;
- raw MCP payload;
- prompt/model internals;
- chain-of-thought;
- proposal handle/digest/fingerprint/session id;
- stack trace;
- internal URL;
- control-plane metadata desnecessário.

Observação factual: o bloco local atual ainda mostra `specialist_id/protocol` nos detalhes técnicos. A implementação futura deve revisar se isso é user-facing legítimo ou se deve ser reduzido, sem apagar provenance exigida pelo contrato.

## 16. Acessibilidade

Required:

- disclosure com semântica nativa ou `button` + `aria-expanded/aria-controls`;
- estrutura `dl/dt/dd` preferencial para pares;
- não depender de cor;
- focus-visible;
- sem autofocus/focus trap;
- conteúdo hostil como texto inerte;
- zoom 200% sem clipping;
- 320px sem overflow;
- limitações materiais perceptíveis com disclosure fechado;
- fonte resumida não deve ser repetida desnecessariamente por live regions.

## 17. Motion

Default: nenhum motion.

Permitido apenas disclosure transition sutil se já houver padrão compartilhado e com `prefers-reduced-motion`.

Não animar classes epistêmicas, fonte ou limitações.

## 18. Copy guidance

Preferir:

```text
Fonte · Cadastro DELPI
Consultado em 16/10/2026 14:32
Detalhes da evidência
Classificação
Especialista
Observado em
Limitações
Sem fonte vinculada
```

Evitar:

- “100% confiável”;
- “certeza alta”;
- “fonte aprovada” sem contrato que diga isso;
- “FACT” como selo verde de qualidade;
- “sem evidência” como erro automático;
- linguagem que converta provenance em autorização.

## 19. API alvo conceitual

Não congelada:

```ts
type EvidenceDetailItem = {
  label: string;
  value: ReactNode;
  wide?: boolean;
};

type EvidenceDetailsProps = {
  sourceSummary?: ReactNode;
  items?: readonly EvidenceDetailItem[];
  limitations?: readonly ReactNode[];
  materialLimitationLabel?: ReactNode;
  expanded?: boolean;
  defaultExpanded?: boolean;
  onExpandedChange?: (expanded: boolean) => void;
  className?: string;
};
```

Regras:

- não aceitar objeto bruto de backend/provider;
- não aceitar JWT/session/token;
- não interpretar epistemic class;
- não calcular confidence;
- não transformar source em link sem href legítimo;
- não promover limitação para severity sem sinal explícito.

## 20. Testes obrigatórios de implementação futura

### plugin-ui

- source summary;
- detail items;
- disclosure open/closed;
- limitations;
- material limitation summary quando explicitamente fornecido;
- no badge semantics;
- hostile text inert;
- keyboard/focus;
- 320px/long labels;
- className/tokens/dark;
- sem business imports.

### DÉLIA

- grounded source summary;
- observed_at válido formatado;
- timestamp inválido omitido;
- NON_GROUNDED neutro;
- epistemic class renderizada literalmente;
- limitations preservadas;
- ausência de provenance não inventa fonte;
- sem duplicação com ActivityViewer;
- sem transformação de classe em confidence;
- revisão de `specialist_id/protocol` disclosure.

### Browser QA

- full page;
- dock real ou harness legítimo;
- light/dark;
- closed/open;
- sem provenance;
- grounded;
- non-grounded;
- múltiplas limitações;
- long source;
- 420px/320px;
- zoom 200%;
- teclado/focus;
- no overflow.

## 21. Acceptance criteria

```text
[ ] reanchor real
[ ] reuse gate revalidado
[ ] abstraction gate revalidado
[ ] local block inventoried
[ ] DetailFieldGrid assessed
[ ] no heavy card
[ ] no epistemic confidence badges
[ ] source summary visible when material
[ ] limitations material visibility governed explicitly
[ ] full-page/dock same component
[ ] light/dark
[ ] keyboard/focus
[ ] 320/420/zoom 200
[ ] no technical/secret leak
[ ] no authority inference
[ ] tests/build/federation
[ ] browser evidence
[ ] docs/catalog updated after factual implementation
[ ] no phase advancement
```

## 22. Estado factual

```text
CURRENT_LOCAL_EVIDENCE_UI = PROVEN
SHARED_EVIDENCE_COMPONENT = NOT_IMPLEMENTED
PRODUCT_MEANING = SPECIFIED
VISUAL_DIRECTION = SPECIFIED
EXISTING_FULL_EQUIVALENT = NO
DETAIL_FIELD_GRID = PARTIAL_REUSE_CANDIDATE
REUSE_DECISION = NEW_CANDIDATE_AFTER_REVALIDATION
BROWSER_QA_FOR_NEW_COMPONENT = TEST_NOT_RUN
BUILD_FOR_NEW_COMPONENT = TEST_NOT_RUN
PHASE_ADVANCEMENT = NONE
```

Esta spec define o próximo bounded design target. Ela não obriga a extração para `plugin-ui` se a revalidação futura provar que a abstração compartilhada não se justifica.
