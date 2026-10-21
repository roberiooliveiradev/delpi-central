# 93 — DÉLIA | Conversation Starter Suggestions — Especificação de produto, aparência e comportamento

**Status:** `PRODUCT_UX_PROPOSAL / FUTURE_CANDIDATE / IMPLEMENTATION_DEFERRED`  
**Data:** 2026-10-16  
**Natureza:** documentação do estado-alvo; **nenhuma autorização** de implementação, schema, integração, deploy ou progressão de fase.  
**Owner de apresentação compartilhada:** `plugins/plugin-ui`. **Consumer:** `plugins/delia` (DÉLIA standalone).  
**Fontes de precedência:** 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → specs de conversa pertinentes → ledger. Em conflito, prevalece authority superior; não criar fase/CP por inferência.  
**Referências diretas:** specs 69/73/75/82 conforme paths canônicos a localizar na reancoragem futura; doc [92](./92-conversation-assistant-actions-ux-functional-spec.md), sobre ações em respostas (**componente diferente**).  
**Snapshot de consulta GitHub:** `main` observado em `17e61331faef05cf99a534e601a0ac2f64bba457` na elaboração documental; novo HEAD deve ser revalidado antes de qualquer implementação.

## 1. Visão e propósito

`ConversationStarterSuggestions` é um conjunto opcional de sugestões de perguntas **na recepção de uma conversa vazia**, abaixo da saudação e antes do compositor. Sua função é ajudar a pessoa a descobrir como começar a conversar com a DÉLIA sem converter exemplos em promessa de capability ou em execução automática.

Princípio de interação: **selecionar sugestão = preencher rascunho editável; nunca enviar**. O usuário continua decidindo o texto e o momento do envio. A interface é chat-first, leve, sem visual de dashboard, sem um catálogo paralelo de capacidades.

Este registro descreve aparência e funcionalidades *esperadas no futuro*. O usuário decidiu explicitamente **não implementar agora**.

## 2. Estado existente, reuse e owners

Evidências pontuais consultadas no código de `main` em 2026-10-16:

- `plugins/plugin-ui/src/components/conversation/ConversationReception.tsx`: recepção render-only com avatar, greeting, title, description, note e density default/compact; não busca identidade ou capabilities.
- `plugins/delia/src/ui/DeliaReception.tsx`: thin wrapper sobre `ConversationReception`, `UnifiedAvatar` e projeção existente de saudação. A copy atual explicitamente **não promete capabilities**.
- `plugins/plugin-ui/src/components/composer/MessageComposer.tsx`: textarea controlada por `value/onChange`, envio explícito por `onSubmit`, loading, Enter/Shift+Enter e secondaryActions; não envia por conta própria.
- `plugins/delia/src/ui/DeliaComposer.tsx`: thin wrapper do `MessageComposer`, recebe estado e callbacks do consumidor.

`EXISTING_EQUIVALENT = YES` **para primitives/superfícies-base**; `EXISTING_EQUIVALENT = TO_INVENTORY` **para o conjunto específico de starter suggestions**.  
`REUSE_DECISION = REUSE` para `ConversationReception`, `MessageComposer` e demais primitives aprovados; **EXTEND ou NEW para uma composição de sugestões só após inventário breve, gate de abstração e aprovação bounded**. Não duplicar recepção, cards/buttons ou composer.

**Ownership obrigatório no futuro:**
- `plugin-ui`: layout, subcomponentes visuais, estilos/tokens, interações sem efeito externo, states, a11y e contrato visual de `ConversationStarterSuggestions`.
- DÉLIA MFE: compor/importar o kit, fornecer sugestões admitidas, contexto de sessão, callbacks e rascunho. Não criar primitives visuais locais.
- Core / Domain APIs / contracts legítimos: governança de acesso e de capability conforme owner; DÉLIA não produz autorização pela UI.
- DÉLIA Application: quando houver superfície admitida, seleciona/ordena sugestões de modo governado, sem usar rótulos do provider/modelo como permissão.

## 3. Anatomia da recepção — alvo

```text
                   [avatar DÉLIA / Sparkles]
                   [saudação opcional]
             Como posso ajudar você hoje?
       [descrição honesta: capacidades dependem de acesso]

          Explore algumas possibilidades para começar

  +--------------------------------+  +--------------------------------+
  | [ícone] Analisar indicadores   |  | [ícone] Investigar informações |
  | Explorar dados operacionais    |  | Consultar fontes disponíveis   |
  +--------------------------------+  +--------------------------------+
  | [ícone] Acompanhar atividades  |  | [ícone] Explorar possibilidades|
  | Consultar situações           |  | Descobrir por onde começar     |
  +--------------------------------+  +--------------------------------+

                  [MessageComposer existente]
```

Os textos são **exemplos de design**, não capability claims, não dados de produção e não devem ser exibidos a usuários reais sem lastro admitido. A redação final pode variar conforme contratos/objetivos.

**Composição:** preservar a recepção atual, seu avatar institucional, a saudação condicional e a nota de privacidade. Não adicionar segundo título principal, uma segunda área de input nem uma superfície de onboarding intrusiva.

## 4. Aparência visual esperada

- **Estilo:** minimalista, institucional e acolhedor; superfícies discretas com borda leve/radius dos tokens do `plugin-ui`, sem sombras pesadas, brilho excessivo, cores semânticas inventadas ou aparência de dashboards.
- **Título da seção:** texto curto e subordinado ao `h2` de recepção; preferir “Explore algumas possibilidades para começar”, ocultável sem gerar espaço vazio.
- **Cards/sugestões:** no máximo uma frase principal clara e opcional descrição curta. Ícone Lucide decorativo quando útil; texto continua suficiente sem ícone. Cada item é um controle acionável com hit target adequado.
- **Hierarquia:** rótulo com maior ênfase que descrição; evita poluição visual. Tokens de tema (light/dark) e contraste real, não cores fixas específicas da DÉLIA.
- **Espaçamento:** distância regular da saudação e do composer; densidade compacta no dock. Transições discretas e compatíveis com `prefers-reduced-motion`.
- **Hover/focus/press:** hover leve, `focus-visible` nítido, pressed momentâneo; seleção de sugestão não deve insinuar que a pergunta foi enviada.
- **Layout:** desktop tipicamente grade de 2 colunas; dock/mobile 1 coluna, com adaptação por espaço disponível e sem scroll horizontal. A quantidade é bounded, dinâmica e pode ser zero; não preencher lacunas com itens fictícios.
- **Text overflow:** truncamento visual somente se acessibilidade preservar o texto integral; preferir quebra de linha limitada e não cortar semântica importante.
- **Sem dependência de avatar individual, biometria ou atributos pessoais sensíveis.**

## 5. Catálogo semântico de exemplos — não é um catálogo de capabilities

Exemplos de temas ilustrativos, sempre sujeitos ao filtro de disponibilidade real:

| Tema UX | Exemplo de título | Exemplo editável de texto inserido no composer | Gate de exibição |
|---|---|---|---|
| Indicadores | Analisar indicadores | “Quais indicadores operacionais posso consultar?” | Superfície de consulta legítima disponível e autorizada |
| Informações | Investigar informações | “Que fontes de informação estão disponíveis para minha consulta?” | Discovery/consulta permitida para o contexto |
| Atividades | Acompanhar atividades | “Quais situações ou pendências posso acompanhar?” | Contrato real de consulta; não presumir tarefas pessoais |
| Orientação | Explorar possibilidades | “Em que tipos de análise você pode me ajudar agora?” | Pergunta de orientação segura; não prometer ações inexistentes |

Não exibir uma sugestão porque determinado texto/capability apareceu em metadata não confiável de MCP, ferramenta, modelo ou memória. Uma capability apenas descoberta não é necessariamente permitida; `discovery != approval`.

As sugestões reais podem ser estáticas **somente** se forem perguntas genéricas honestas e não representarem capacidades inexistentes. Se dependerem de ação/capability específica, exigem projeção legitimamente publicada, governança atual e checagem de autorização no backend na execução.

## 6. Comportamento funcional esperado

### 6.1 Visibilidade e ciclo de vida
- Componente aparece **somente em conversa vazia**, como parte da recepção, se houver sugestões elegíveis e a feature estiver liberada.
- Assim que a conversa tiver turnos, a recepção e as sugestões desaparecem conforme o fluxo existente.
- Em ausência de sugestões ou erro de obtenção, não exibir skeleton eterno, menu vazio, cards falsos ou erro alarmista; conservar recepção/composer utilizáveis.
- Carregamento opcional só com contrato/estado real; nunca simular descoberta.

### 6.2 Seleção
- Clique, Enter ou Space no item → invocar callback explícito `onSelect(suggestion)`.
- O consumidor recebe um identificador opaco/estável e um `draftText` **pré-validado/limitado**, coloca o texto no draft controlado do `MessageComposer`, move o foco de modo acessível ao campo e posiciona cursor quando viável.
- **Proibido auto-submit** e proibido simular que a DÉLIA já iniciou consulta ou executou a tarefa.
- O usuário pode editar, completar, apagar ou não enviar. O editor continua sujeito ao limite de caracteres contratado; suggestion `draftText` não pode ultrapassá-lo.
- Se o composer estiver desabilitado/loading, a sugestão deve estar indisponível ou não agir; evitar sobrescrever draft existente por engano.
- Se já houver texto digitado, estratégia de confirmação/não sobrescrita deve ser definida no contrato de integração; **default fail-safe: não sobrescrever silenciosamente**.
- Clique repetido não duplica texto nem gera várias solicitações.

### 6.3 Origem, ordenação e personalização
- Direção futura: sugestões podem depender de capacidades **efetivamente permitidas**, propósito da página, módulo/contexto legítimo e intenção explícita do usuário. A seleção é uma **projeção governada**, não autorização.
- Ordem preferencial: relevância/contexto → utilidade → diversidade; não inventar scores nem exibir rankings sem evidência.
- Caso não haja fonte contratada para personalização contextual, trabalhar com estado vazio ou exemplos estritamente genéricos aprovados, sem alegar integração já existente.
- Não inferir personalidade, saúde, honestidade, emoção, desempenho laboral ou atributos sensíveis.
- Não usar Personal Memory como fonte de autorização ou fato operacional. Não vazar nomes de apps, informações de outros usuários ou resources sem permissão.
- Não persistir cliques, histórico ou preferências sem contrato de observabilidade/privacidade.

### 6.4 Erros e estados
- Estados-alvo: `hidden`, `ready`, `loading` (somente quando verdadeiro), `disabled` (contexto não elegível), `empty`, `error-neutral`.
- Conteúdo e ícones não devem parecer clicáveis quando não existe callback autorizado.
- Erros não impedem digitar no composer.
- Conteúdo externo e rótulos são tratados como dados não confiáveis; sem HTML arbitrário, `dangerouslySetInnerHTML` ou URLs automáticas.

## 7. Contrato visual alvo (conceitual, não API congelada)

Uma futura composição compartilhada pode receber:

```ts
type StarterSuggestion = {
  id: string;                  // identidade UI estável
  title: string;               // rótulo admitido e limitado
  description?: string;        // detalhe curto opcional
  draftText: string;           // texto a inserir; nunca executar
  iconKey?: string;            // allowlist semântico-visual do kit
  disabled?: boolean;
};

type ConversationStarterSuggestionsProps = {
  items: readonly StarterSuggestion[];
  onSelect?: (item: StarterSuggestion) => void;
  density?: "default" | "compact";
  disabled?: boolean;
  loading?: boolean;
  label?: string;
  className?: string;
};
```

Esse shape é **ilustrativo**. Na task futura, validar semântica, limites, acessibilidade, versionamento, consumer e compatibilidade, reusando padrões presentes no `plugin-ui`. Não converter `iconKey` em carregamento dinâmico arbitrário e não aceitar metadata externa como instrução.

**Integração pretendida:** `plugin-ui` publica componente e CSS; `plugins/delia` importa pelo entrypoint público `@delpi/plugin-ui/index`. A DÉLIA fornece itens admitidos e liga `onSelect` ao draft controlado existente do composer. `MessageComposer` continua proprietário da apresentação do campo; DÉLIA é proprietária do estado e do envio explícito.

## 8. Acessibilidade e responsividade

- WCAG/ARIA: controles reais (`button`), nomes acessíveis por item, descrição associada quando relevante, tab order natural, `focus-visible`, Enter/Space, target adequado e ausência de anúncios indevidos.
- Ao preencher composer, comunicar o resultado de forma discreta; foco no campo sem forçar submit. Sem `aria-live` duplicado ou anúncios repetidos por atualização de lista.
- Paridade full-page/Companion Dock, desktop/mobile, 320/420px, zoom 200%, fontes grandes, light/dark, `prefers-reduced-motion` e leitores de tela.
- Grid responsiva sem rolagem horizontal ou sobreposição ao dock e sem deslocamento excessivo da área de escrita.

## 9. Restrições de segurança, autoridade e UX

- DÉLIA é standalone; não importar runtime/frontend/services/migrations de Minha DELPI Chat.
- `plugin-ui` não busca Core/Keycloak/Domain, não chama MCP, não descobre tools, não persiste drafts e não envia requests.
- A DÉLIA não duplica primitives nem cria catálogo local de capabilities por conveniência.
- JWT/contexto de página/metadata/provider output não concedem permissão. Core e Domain APIs resolvem autoridade conforme contratos legítimos.
- `read != write`; `recommendation != authorization`; `PREPARE != ACT`; `simulate != apply`.
- Sugestão de consulta, diagnóstico ou preparo não pode implicitamente disparar ACT, confirmação ou operação industrial.

## 10. Critérios futuros de aceite — NÃO EXECUTADOS

1. Gate de reuse fechado com owner/consumer/contrato comprovados; nenhum primitive visual duplicado em DÉLIA.
2. Componente compartilhado em `plugin-ui` e importação pública validada via federation.
3. Seleção só altera draft e foca composer; **nenhum envio automático** ou mutação material.
4. Não sobrescreve draft existente sem política explícita e não permite seleção durante submit/loading.
5. Não exibe capability indisponível/não admitida; safe empty-state preserva conversa normal.
6. Paridade full-page/dock, mobile, keyboard, screen-reader, dark/light, zoom e reduced-motion.
7. Testes unitários, de integração, de segurança, builds, federation e browser QA registrados por SHA/config.
8. Sem phase progression ou CP PASS inferido de componente visual.

## 11. Não escopo, pendências e decisão de postergação

**NÃO implementar nesta rodada:** JSX, CSS, alterações de exports, integração DÉLIA, backend, endpoints, schemas, telemetry, feature flags, migrations, testes de runtime ou deploy. **Não habilitar** sugestões reais nem adicionar cards na recepção existente apenas por causa desta especificação.

Pontos a decidir **quando a implementação for autorizada**: contrato de origem das sugestões, autorização/capability binding e refresh, política de não sobrescrita de drafts, limites de caracteres/cards, affordance opcional de personalização, ordering, validações e RQ/AC/CP aplicáveis. Qualquer decisão que conflite com authority canônica retorna à coordenação.

```text
SPEC = DOCUMENTED_FUTURE_TARGET
IMPLEMENTATION = NOT_AUTHORIZED_NOW
RUNTIME = UNCHANGED
EXISTING_EQUIVALENT_SHARED_BASE = YES
EXISTING_EQUIVALENT_SUGGESTION_SET = TO_INVENTORY
REUSE_DECISION_SHARED_BASE = REUSE
REUSE_DECISION_SUGGESTION_COMPOSITION = PENDING_GATE
BACKEND_CAPABILITY_BINDING = TO_INVENTORY
TESTS = TEST_NOT_RUN
PHASE_PROGRESSION = NONE
NEXT = DEFERRED_UNTIL_PRODUCT_AND_COORDINATION_AUTHORIZATION
```

## 12. Inventário dirigido de interações visuais e gates de capacidade real (2026-10-20)

**Tipo:** `PRODUCT_DIRECTION_APPROVED / VISUAL_INVENTORY / DOCUMENTATION_ONLY`. O Product Master determina: **somente sugerir funcionalidades que a DÉLIA realmente consegue executar para o usuário e contexto atuais**. Nunca mostrar exemplos fictícios do wireframe §3 como capacidades habilitadas. Contrato backend de catálogo/projeção de sugestões **não será criado nem congelado nesta etapa**; `IMPLEMENTATION_DEFERRED` continua até autorização futura específica. Esta seção complementa os conceitos anteriores, sem promover targets a runtime.

**HEAD observado nesta revisão documental:** `ca8b1d0d4a5a796c949a6e3bcb1ed765f8036395`. Fontes conferidas: specs 93, 116, 117, `ConversationReception.tsx`, `DeliaReception.tsx`, `DeliaConversationPage.tsx`, `HelpTooltip.tsx`. Git local/status, authorities completas, consumidores de capabilities e infraestrutura de autorização **não** foram inventariados integralmente; revalidar na task futura. `TEST_NOT_RUN`.

### 12.1 Gate epistemológico de conteúdo

| Situação | Estado visual admitido | Regra |
|---|---|---|
| Capacidade comprovadamente existente, contextual, operacional e autorizada no owner legítimo | `ready` com sugestão clicável | provar responsabilidade → owner → fonte → consumidor → contrato → implementação → teste/outcome |
| Implementação identificada, mas permissão efetiva não comprovada | `hidden`/não ofertar | não deduzir de metadata, JWT, memória ou import frontend |
| Capability `PLANNED/TARGET` | `hidden` | não transformar roadmap em promessa |
| Descoberta MCP/provedor sem aprovação/AuthZ | `hidden` | `discovery != approval` |
| Capability temporariamente indisponível | omitir por padrão; `disabled` apenas se a visibilidade tiver justificativa real aprovada | nunca parece acionável |
| Nenhum item elegível / sem contrato legítimo de fornecimento | `empty` invisível, preservar recepção/composer | não popular fallback inventado |
| Falha do provedor da projeção futura | `error-neutral` sem erro global | não bloquear texto |
| `loading` apenas de fluxo real | indicação discreta, sem skeleton eterno | sem simular integração inexistente |

**Capacidades atualmente sugeríveis:** `TO_INVENTORY`. As consultas sobre DAVI/VISTA/TÉO, roteamento, STT e outros componentes em execuções anteriores **não** provam elegibilidade geral nem AuthZ atual de cada sugestão; a próxima task deverá colher evidência por capability/usuário antes de disponibilizar textos concretos. Exemplos “Analisar indicadores”, “Investigar informações”, “Acompanhar atividades” e “Explorar possibilidades” do §5 são **placeholders de design**, nunca allowlist automática.

### 12.2 Inventário de estados/interações visuais

| Estado / evento | Apresentação | Resposta e invariantes |
|---|---|---|
| `hidden`, conversa com turnos | não renderizar sugestões | recepção desaparece pelo ciclo existente |
| `empty`, nenhum item autorizado | renderizar recepção sem grid e sem título de sugestões | não criar espaços vazios nem fallback fictício |
| `loading` real, antes da admissão | skeleton leve opcional abaixo da descrição | não bloquear composer nem sugerir autorização |
| `ready`, conversa vazia | seção secundária com título discreto + conjunto limitado de cards | avatar/greeting/title/note existentes preservados |
| Card `default` | borda discreta, cantos/tokens `plugin-ui`, ícone semântico opcional, título + descrição curta | título suficiente sem ícone; uma só superfície clicável |
| Card hover | realce leve de borda/fundo; help contextual padronizado | sem salto de layout, sem executar ação |
| Card focus-visible | outline acessível, tooltip `HelpTooltip` existente | tab order natural; não atualizar draft no foco |
| Card pressed | feedback visual curto | invocar intenção uma vez, sem prometer ação material |
| Card selecionado | aplicar `draftText` admissível e focar `MessageComposer` | não enviar; permitir edição e desfazer edição manual |
| Seleção com draft não vazio | por default não sobrescrever; proteção explícita | decidir no contrato de integração se perguntar, inserir ou bloquear; até lá fail-safe |
| Repetição de click/Enter | não duplicar prompt nem disparar múltiplos efeitos | callback idempotente no consumidor |
| Composer loading/disabled | cards desabilitados ou ocultos | nenhum clique efetivo |
| Turno criado | seção some conforme recepção existente | sem animação que reordene mensagens |
| Items atualizados por projeção legítima futura | atualizar itens com keys estáveis, sem piscar | não depender de LLM para autorização; foco não some sem aviso |
| `error-neutral` | omitir sugestões, manter composer | erro não vira banner global |
| Dock compact | uma coluna, cards densos, altura contida | sem clipping/overflow; priorizar campo de texto |
| Desktop | preferir duas colunas, no máximo bounded conforme evidência | não inferir número fixo de capacidades |
| Touch e zoom | hit area adequada, tooltips não exclusivamente por hover | legibilidade 320/360/420px, 200% zoom |
| Tema/motion | light/dark, reduced motion, contraste | tokens, foco, transições curtas, sem brilho ornamental |

### 12.3 Estrutura visual e detalhamento

- Ordem na recepção: avatar institucional → saudação condicional → `h2` atual → descrição honesta → título secundário de sugestões se houver itens → grid responsiva → composer preexistente no layout do host. Nota de privacidade/persistência permanece; não duplicar títulos.
- Cards são botões inteiros, não links de navegação; ícone Lucide somente de allowlist; título de uma linha preferencial, descrição curta com wrapping acessível; textos variáveis sem cortar informação decisiva.
- Usar primitives de `plugin-ui` antes de novo card/componente; `HelpTooltip` comprovadamente existente com `wrap`, trigger hover/focus, portal/viewport; não usar `title` nativo como única ajuda. Tooltip fornece descrição factual da **pergunta que será inserida**, não promessa de execução nem da competência de outra API.
- Feedback de seleção: foco retorna ao textarea com caret apropriado e conteúdo editável; feedback de `draft populated` sem toast global ou `aria-live` duplicada. Não executar o prompt.
- Compatibilidade de 320/360/420px, Companion Dock, zoom 200%, light/dark, teclado, leitor de tela e `prefers-reduced-motion`.
- No backend contract / autorização nesta etapa. Em implementação visual futura, componente pode ser render-only com `items=[]` e `disabled`/empty honestos; integração de sugestões reais só após admissibilidade comprovada por owner legítimo.

### 12.4 Inventário de reuso e limites

| Responsabilidade | Evidência de código no HEAD consultado | Decisão |
|---|---|---|
| Recepção | `plugins/plugin-ui/src/components/conversation/ConversationReception.tsx` | `EXISTING_EQUIVALENT=YES; REUSE` |
| Consumer/reception DÉLIA | `plugins/delia/src/ui/DeliaReception.tsx` | `YES; REUSE/EXTEND` para composição apenas |
| Composer/draft | `MessageComposer` e `DeliaComposer` (inventário 117) | `YES; REUSE` |
| Tooltip/help | `plugins/plugin-ui/src/components/help/HelpTooltip.tsx` | `YES; REUSE` |
| Estrutura de página/Dock | `DeliaConversationPage.tsx` + superfícies do Portal | `YES; REUSE` |
| Composição específica de starter suggestions | não provada no inventário dirigido 117 | `TO_INVENTORY`; decidir EXTEND/NEW depois |
| Catálogo/admissão de sugestões | owner/contrato específico não validado | `TO_INVENTORY`, **não criar neste ciclo** |

### 12.5 Critérios de aceite futuros do frontend (não executados)

- `SS-V01`: recepção existente sem duplicação ou mudanças quando items vazios.
- `SS-V02`: nenhuma sugestão não comprovada é exibida como ação disponível.
- `SS-V03`: cards/tokens/ícones/help padronizados; hover/focus/pressed distinguíveis.
- `SS-V04`: seleção preenche **só o draft** e restaura foco; sem auto-submit.
- `SS-V05`: draft existente protegido; comportamento repetido não duplica texto.
- `SS-V06`: conversa iniciada oculta sugestões; ausência de contratos não bloqueia escrita.
- `SS-V07`: full-page/Dock, 320/360/420, 200%, light/dark/reduced motion.
- `SS-V08`: teclado/Enter/Space/SR/tooltip/a11y validados.
- `SS-V09`: componentes visuais compartilhados `plugin-ui`, sem catálogo ou autorização implementada no frontend.
- `SS-V10`: integração futura com capabilities somente após evidência runtime/AuthZ contratada; backend/provedor/feature não inventados.

**Decisões a fechar quando autorizar implementação:** quantidade máxima simultânea, política explícita de clique sobre draft não vazio, contrato UI tipado final, integração com fonte autorizada e UX de eventual refresh. Não fechar backend neste inventário; não presumir que design mock autoriza uma capability.

```text
TASK=CONVERSATION_STARTER_SUGGESTIONS_VISUAL_INVENTORY
STATUS=DOCUMENTED_VISUAL_SCOPE_ONLY
PRODUCT_RULE=ONLY_REAL_EXECUTABLE_AUTHORIZED_CAPABILITIES
BACKEND_CONTRACT=NOT_DEFINED_BY_DESIGN_TASK
ACTUAL_ELIGIBLE_SUGGESTIONS=TO_INVENTORY
REUSE_RECEPTION=YES_REUSE
REUSE_COMPOSER=YES_REUSE
REUSE_HELP_TOOLTIP=YES_REUSE
DEDICATED_SUGGESTION_COMPOSITION=TO_INVENTORY
IMPLEMENTATION=DEFERRED_UNCHANGED
RUNTIME=UNCHANGED
TESTS=TEST_NOT_RUN
PHASE_PROGRESSION=NONE
```

## 13. Limite responsivo de sugestões e variantes de apresentação (decisão de produto de 2026-10-20)

**Decisão aprovada:** o número de sugestões visíveis deve respeitar **o espaço útil real da superfície**, preservando a saudação e, principalmente, o `MessageComposer`. Cards possuem variantes de densidade/tamanho adequadas a **diferentes tamanhos de viewport e modos de apresentação**. Não impor uma grade fixa de quatro itens em qualquer tela, não causar scroll horizontal nem esconder o composer atrás de sugestões. Esta é uma decisão de UX/visual; **não** aprova novas capacidades nem contrato backend.

### 13.1 Orçamento visual e regra de quantidade

- Ordenar apenas sugestões **efetivamente elegíveis**; `visibleCount = min(eligibleCount, presentationCap, slotsThatFit)`. `slotsThatFit` depende da largura e da altura disponíveis **após** reservar espaço para cabeçalho, recepção, composer e margens/touch-safe area.
- **Teto inicial de design, não promessa de exibir itens:** `full/desktop ≤ 4`; `compact/tablet ≤ 3`; `mobile estreito ≤ 2`; `Companion Dock ≤ 2`. Quando a altura não permitir, mostrar 1 ou **0**. Não preencher espaços com sugestões falsas.
- Um item continua útil; não criar placeholders. Se nada couber com segurança, esconder a seção e manter a entrada textual sempre acessível.
- O máximo visual **não** exige que a DÉLIA tenha quatro capacidades. Uma só sugestão comprovada significa uma só sugestão visível.
- Não utilizar paginação ou carrossel automático por padrão; o custo de esconder o campo de escrita ou criar descoberta extra não se justifica. Um futuro “Ver mais” só poderá existir se houver requisitos e fonte legítima de mais sugestões, fora deste escopo.
- Calcular a apresentação pelo **container de conteúdo** (não apenas `window.innerWidth`), porque o Dock pode ocupar pouco espaço em um monitor grande; preferir container queries/tokens existentes. Avoid observers/engines próprios se CSS e composição resolverem.
- Evitar layout shift, loops de `ResizeObserver` e flicker quando teclado virtual abrir ou sugestão desaparecer. Preservar estabilidade quando a conversa começa.

### 13.2 Variantes visuais por espaço disponível

| Modo | Variante de card | Layout preferencial | Limite inicial | Conteúdo |
|---|---|---|---|---|
| Página completa larga | `regular` | grade 2 colunas × até 2 linhas | 4 | ícone opcional, título e descrição curta |
| Página completa média | `compact` | 1 ou 2 colunas conforme container | 3 | título e descrição curta somente se houver espaço |
| Tela estreita (320–420px) | `compact` / `minimal` | 1 coluna | 2 | título legível; ícone opcional; descrição omitida visualmente se necessário, acessível via help |
| Companion Dock | `minimal` | 1 coluna, ações horizontais/stack compacto conforme espaço | 2 | preferência a título curto e help contextual; não disputar altura do composer |
| Altura muito reduzida / zoom 200% | `minimal` ou `hidden` | no máximo 1 card se houver espaço | 1 ou 0 | não ocultar título/área de escrita para exibir sugestão |

Essas variantes são um **contrato de apresentação conceitual**, não nomes obrigatórios de props. Inventariar variantes já existentes do kit antes de criar novas. Usar tokens `plugin-ui` de radius, gaps, text, breakpoints e focus. Não fixar alturas em px que cortem títulos com fonte ampliada.

### 13.3 Microcomportamentos

1. **Hover/focus:** destaque sutil + `HelpTooltip` do kit, com explicação da pergunta que será inserida; não descrever capacidade não comprovada.
2. **Card compacto:** componente inteiro é área clicável; sem controles aninhados ou ellipsis que esconda informação crítica. Quando a descrição não for visível, manter texto integral acessível por descrição/tooltip sem duplicar anúncios.
3. **Mudança de apresentação:** preservar identidade, ordem relativa e conteúdo dos itens; nunca fazer submit nem perder draft em resize. Reduzir primeiro descrição, depois número de cards; preservar leitura e foco.
4. **Quando a altura faltar:** prioridade `composer > recepção principal > sugestões`; esconder cards excedentes sem rolagem interna e sem forçar a página a perder funcionalidades.
5. **Semântica de exibição:** o teto é aplicado **depois** do filtro de elegibilidade; frontend nunca decide permissão com base no tamanho.
6. **Acessibilidade:** teclado, touch targets, leitor de tela, contraste, zoom 200%, reduced motion; se um card desaparecer durante foco, tratamento previsível (não mover foco ao body).
7. **Estados vazios/loading:** nenhum skeleton mais alto do que o espaço reservado; sem cards fictícios para completar grade.
8. **Full page e Dock:** mesmos significados, mas densidades próprias; nenhuma variante promete capability diferente.

### 13.4 Acceptance Gate adicional (não executado)

- `SS-V11`: nunca mais sugestões visíveis do que cabem com composer permanentemente utilizável.
- `SS-V12`: teto inicial full ≤4, médio ≤3, narrow ≤2, Dock ≤2, com redução adicional por altura.
- `SS-V13`: variantes `regular/compact/minimal` coerentes com design system e com altura/fonte responsiva.
- `SS-V14`: container/Dock, 320/360/420px, 200% zoom, orientação/teclado virtual sem overflow horizontal ou clipping.
- `SS-V15`: reflow/resize sem sobrescrever draft, duplicar sugestão, auto-submit, flicker ou foco perdido.
- `SS-V16`: cards ocultos por falta de espaço não viram sugestões não elegíveis e nenhum fallback inventado é inserido.

`SS-V11…SS-V16=PLANNED`. Testar com 0/1/2/3/4/6 itens **fictícios somente em fixtures de teste visual**, nunca como capacidades oferecidas a usuários em produção. O conteúdo real continua condicionado à elegibilidade e ao futuro owner/contrato legítimo.

**Gate de reuso:** `EXISTING_EQUIVALENT=TO_INVENTORY` para composição/variantes específicas, `REUSE_DECISION=REUSE/EXTEND` dos primitives `plugin-ui` quando comprovados; nenhuma nova engine/layout service. `BACKEND_CONTRACT=NOT_DEFINED`, `IMPLEMENTATION=DEFERRED`, `PHASE_PROGRESSION=NONE`.

## 14. Autorização bounded do Product Master — frontend com quatro perguntas iniciais (2026-10-20)

**Decisão:** `F02-A_FRONTEND_IMPLEMENTATION_AUTHORIZED` para construir o componente compartilhado e integrá-lo à recepção da DÉLIA, **sem contrato backend de sugestão e sem inferir autorização de capabilities**. Esta decisão substitui `IMPLEMENTATION_DEFERRED` **apenas para o slice render-only e a composição do draft**, sem alterar a proibição de anunciar funções não comprovadas. Não autoriza avançar fase, modificar MCP/LLM, criar catálogo backend ou liberar ações materiais.

**Quatro perguntas padrão para QA visual e funcional (copy inicial, sujeita a revalidação de execução por sessão antes de produção):**
1. `Quais formatos de dados estão disponíveis?` — evidência de pergunta respondida em execução real via VISTA catalog, porém disponibilidade contextual sempre revalidada.
2. `O que é SIPOC?` — pergunta explicativa compatível com especialização de processos TÉO e com exemplos já avaliados; não prometer consulta específica sem prova live.
3. `Quais fontes de informação posso consultar com meu acesso?` — pergunta de discovery, não afirma que certa fonte está autorizada.
4. `Que tipos de análise operacional você consegue realizar agora?` — pergunta de orientação baseada em capabilities, não promessa de ação.

**Gate de visibilidade em produção:** perguntas 1–4 são **fixtures de apresentação**, não allowlist de permissions. Apenas montar sugestões cujo fluxo de resposta esteja comprovadamente admitido para a sessão/ambiente; sem projeção de admissibilidade, não exibir como quatro capabilities disponíveis para todos. Se não houver evidência de elegibilidade por contexto, manter `items=[]` em produção ou habilitar as quatro opções somente em modo QA explicitamente controlado já existente e aprovado, sem inventar nova permissão ou feature backend. O deploy do render-only pode ocorrer disabled/hidden honestamente. Não codificar owner names, tools ou metadata MCP como fonte de autorização.

**Reuso:** `ConversationReception`, `MessageComposer`, botões/cards e `HelpTooltip` do `plugin-ui`; composição das opções fornecida pela DÉLIA MFE; callback somente `setInput(draftText)` e foco; **nunca `handleSubmit()`**. Implementar variants regular/compact/minimal e caps responsivos §13, com item count abaixo de quatro quando contexto/tela exigir. Texto já digitado não pode ser sobrescrito: por default, não aplicar sugestão, com feedback leve ou seleção desabilitada, até política definida.

**Critérios do slice:** `SS-F01` render-only em `plugin-ui`; `SS-F02` quatro fixtures de perguntas definidos somente no consumer DÉLIA/QA com elegibilidade honesta; `SS-F03` clique/Enter/Space preenche draft com foco sem submit; `SS-F04` preserva draft existente; `SS-F05` zero sugestões se não houver fonte/gate legítimos; `SS-F06` layout 0–4 em fullpage/Dock/mobile; `SS-F07` tooltips, keyboard/a11y/theme/reduced-motion; `SS-F08` Vitest/TypeScript/build/federation/browser/evidence no SHA; `SS-F09` rollout não modifica STT, Keycloak, Core, API nem MCP; `SS-F10` registro de implantação distingue fixtures QA de capabilities admitidas. Todos `PLANNED` até execução.

`BACKEND_SUGGESTIONS_CONTRACT=DEFERRED`; `FRONTEND_SLICE=AUTHORIZED`; `PRODUCTION_FOUR_CAPABILITIES=NOT_AUTHORIZED_WITHOUT_RUNTIME_EVIDENCE`; `PHASE_PROGRESSION=NONE`.

## 15. Registro de execução F02-A (2026-10-21)

**TASK:** `DELIA-UX-F02A-STARTER-SUGGESTIONS-FRONTEND-01`. `ConversationStarterSuggestions` implementado em `plugins/plugin-ui` (render-only, `NEW` — sem equivalente no inventário), integrado como sibling de `DeliaReception` no estado vazio (`turns.length === 0`) do `plugins/delia/src/App.tsx`. Quatro fixtures de QA do §14 em `plugins/delia/src/suggestions/starterSuggestions.ts`, admitidos **somente** pelo modo QA governado existente (`isDemoAllowed()` + `?delia-demo=<scenario>` explícito); em produção `items=[]` e a seção não renderiza. Dockerfile da DÉLIA ganhou `ARG VITE_DELIA_DEMO` (QA-only, default off) no padrão do `VITE_DELIA_AUDIO_QA`. Seleção = `setInput` + foco no composer, nunca submit; draft preenchido preservado com nota leve (`role=status`).

**Resultado:** `SS-V01…SS-V16=PASS`; `SS-F01…SS-F10=PASS`. Vitest plugin-ui 2269/2269, delia 276/276; typecheck/build/federation OK; browser QA 42/42 (página 1440px, 420/360/320px, viewport curto, zoom 200%, Dock, dark, reduced-motion, zero `POST /interaction/turns` em seleções). Evidência: `evidence/starter-suggestions-f02a/starter-suggestions-f02a-evidence.md`. Ledger §6.351.

`BACKEND_SUGGESTIONS_CONTRACT=DEFERRED` (inalterado); `PRODUCTION_FOUR_CAPABILITIES=NOT_AUTHORIZED_WITHOUT_RUNTIME_EVIDENCE` (inalterado — fixtures seguem invisíveis em produção); `PHASE_PROGRESSION=NONE`.

## 16. Decisão de produto F02-A-R1 — quatro perguntas visíveis na produção (2026-10-21)

**AUTORIZAÇÃO EXPLÍCITA DO PRODUCT MASTER:** exibir **por padrão** na recepção vazia da DÉLIA as quatro **perguntas de início de conversa** do §14 para usuários que já tenham acesso legítimo à aplicação, sem exigir `VITE_DELIA_DEMO` nem `?delia-demo=`. Substitui, **somente para esta lista fechada de perguntas de orientação/consulta**, a decisão anterior de ocultar todas as fixtures fora do QA. Não equivale à autorização de executar determinada ferramenta MCP ou operação de negócio, nem certifica que toda consulta terá dados acessíveis. Tratar os rótulos como **perguntas editáveis**, não afirmações de disponibilidade ou promessas de resultado. Se uma pergunta depender de recursos não disponíveis, a resposta deve ser honesta, segundo os controles existentes de Core/Domain/DÉLIA.

**Lista congelada para esta etapa (sem extrapolar):** (1) “Quais formatos de dados estão disponíveis?”; (2) “O que é SIPOC?”; (3) “Quais fontes de informação posso consultar com meu acesso?”; (4) “Que tipos de análise operacional você consegue realizar agora?”. Preservar textos no consumer existente `plugins/delia/src/suggestions/starterSuggestions.ts`, sem criar catálogo backend de sugestões. São prompts de consulta/orientação, não chamadas diretas aos MCPs.

**Escopo `DELIA-UX-F02A-R1-PRODUCTION-DEFAULT-STARTERS-01`:** reutilizar `ConversationStarterSuggestions` já criado; remover **somente** o gate de demo para o conjunto padrão na recepção, mantendo o modo demo para suas funções próprias e preservando auth/application admission preexistentes. Cards aparecem apenas enquanto não há turnos, seguem limites responsivos §13 (até 4 desktop, 2 Dock e reduções por espaço), callback apenas preenche o draft e foca textarea, sem submit nem sobrescrita silenciosa de rascunho. Sem nova API, RBAC, provider, tool, planner, permissão ou chamada MCP direta.

**Gates de implementação e deploy:** reanchor no HEAD/authorities/ledger, inspecionar gate efetivo e testes, menor diff; testar usuário já autorizado na DÉLIA e não disponibilizar a público fora da app. Testar quatro cards página completa, até dois Dock, foco, acessibilidade, edição, ausência de auto-submit, draft preservado, nenhum impacto VD-F05. Build/federation e QA autenticado. Deploy de frontends somente após testes, verificação de SHA servido e rollback disponível. Não divulgar as sugestões como quatro `capabilities autorizadas`. Sem mudança de fase nem aceite automático a partir desta decisão.

`PRODUCT_DECISION=APPROVED`; `FRONTEND_PRODUCTION_DEFAULT_QUESTIONS=AUTHORIZED`; `BACKEND_SUGGESTIONS_CONTRACT=DEFERRED`; `MCP_AUTHORITY_OR_EXECUTION=UNCHANGED`; `IMPLEMENTATION=EXECUTED`; `DEPLOYMENT=EXECUTED`; `PRODUCTION_BROWSER_QA=PENDING_USER_VERIFICATION`.

**Registro de execução F02-A-R1 (2026-10-21):** menor diff em `starterSuggestions.ts` + `App.tsx` — `resolveStarterSuggestions()` retorna a lista congelada sem depender de demo flag, query param ou cenário; seam preservado para futura projeção de elegibilidade por sessão. Demais gates de demo intactos (`demoMode.ts` inalterado; suíte demo-mode verde). Evidência: `evidence/starter-suggestions-f02a/starter-suggestions-f02a-r1-evidence.md`; ledger §6.352. Vitest delia 276/276, typecheck + build PASS, browser QA local produção-paridade 40/40 (URL limpa, página + Dock + mobile + zoom 200%, draft-only, zero auto-submit, VD-F05 smoke). Deploy canônico do MFE `delia` em `192.168.1.237` (`up-prod-sequential.sh --cpu --build delia`, SHA `4191b65649`); bundle servido verificado (resolver incondicional, 4 ids, guard demo intacto). QA autenticado de produção pendente de sessão real — Keycloak não modificado (fora de escopo).

## 17. F02-A-R2 — Companion Dock: aproveitar altura disponivel e apresentar ate quatro sugestoes (2026-10-21)

**Observacao de producao reportada pelo Product Master:** duas capturas do Companion Dock em viewport alto apresentam somente as sugestoes “Formatos de dados” e “O que e SIPOC?”, deixando grande espaco vertical entre recepcao, sugestoes e composer. As outras duas perguntas padrao ja publicadas no frontend nao sao exibidas. **Causa identificada no codigo:** `plugins/plugin-ui/src/styles/conversation-starter-suggestions.css` aplica `.global-delia-dock .delpi-ui-starter-suggestions__item:nth-child(n + 3) { display: none; }`, teto rigido de 2 independente da altura. Esta era regra de §13; a decisao atual **substitui especificamente** aquele teto rigido no Companion Dock, preservando os demais gates.

**Direcao de melhoria:** o Companion Dock pode apresentar **ate quatro** sugestoes ja admitidas quando couberem sem prejudicar saudacao, composer e foco. Priorizar compactacao visual e espacamento antes de cortar itens. Nao transformar quantidade maxima em obrigacao; `visibleCount <= eligibleCount`. O numero efetivo considera **largura e altura util do container do Dock** (nao somente viewport global), reservando header, recepcao, composer, safe areas e margem. Nao usar tamanho de viewport global como proxy suficiente para altura do Dock.

**Variantes alvo:** dock largo/alto = 2 colunas x ate 2 linhas; dock estreito/alto = 1 coluna x ate 4 linhas, cards minimal; altura intermediaria = 2–3; altura critica = 0–1 (composer prioritario). Nao usar scroll interno no grid, carrossel automatico ou badges de contagem para esconder itens. Evitar excesso de vazios entre saudacao/grid/composer, sem transformar a area de recepcao em dashboard. Ajustar gap, density, max-width e composicao por tokens do `plugin-ui`/Portal, com layout sem saltos e sem observer/engine se CSS de container resolver.

**Regras preservadas:** quatro perguntas congeladas §16, capacidade real nao inferida da UI, clique apenas preenche draft editavel, nao auto-submit, nao sobrescrever draft, tooltips existentes, responsividade 320/360/420, 200% zoom, light/dark, reduced motion e keyboard/focus. Sem backend, Core, MCP, STT, novo permission gate ou substituicao de `ConversationStarterSuggestions`.

**Aceite especifico F02-A-R2 (PLANNED):** `SS-R2-01` quarto card aparece em Dock alto que suporte 4, `SS-R2-02` dock estreito/alto comporta 4 compactos, `SS-R2-03` quantidade diminui somente quando altura realmente critica, `SS-R2-04` composer nao some nem sofre overlap/scroll horizontal, `SS-R2-05` recepcao/grid/composer ficam visualmente proximos e consistentes, `SS-R2-06` todos cards continuam teclado/foco/tooltip/draft-only, `SS-R2-07` full page 4 cards e VD-F05 sem regressao. QA fullpage e Dock em mais de uma largura/altura, com capturas reais e evidence SHA.

**Status:** `PRODUCT_UX_ADJUSTMENT_REQUESTED`; `IMPLEMENTATION_PENDING`; `TESTS=TEST_NOT_RUN`. Reancorar authorities/ledger antes de modificar codigo e registrar fato vs simulado. Esta decisao nao avanca fase.
