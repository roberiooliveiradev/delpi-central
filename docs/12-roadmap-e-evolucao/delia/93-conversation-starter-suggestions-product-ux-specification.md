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
