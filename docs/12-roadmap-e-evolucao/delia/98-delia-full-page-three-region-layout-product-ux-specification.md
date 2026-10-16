# 98 — DÉLIA | Página completa — layout de três regiões e experiência de produto

**Data:** 2026-10-16  
**Natureza:** especificação de produto, UX e contrato visual **somente documental**. Não autoriza runtime, migração, backend, deploy, CP ou avanço de fase.  
**Produto:** DÉLIA standalone (não é Minha DELPI Chat).  
**Base factual:** `main` no SHA `395bd45012f8b45899f07e226b6525df9e0a0c66`. Revalidar HEAD antes de implementar.  
**Autoridade:** HEAD/git status → Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → specs temáticas → ledger. Conflito = `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`; não reconciliar silenciosamente.  
**Propriedade:** `plugin-ui` hospeda componentes visuais reutilizáveis; `plugins/delia` compõe produto, decide estados de interface e integra contratos autorizados. Portal hospeda/navega; Core valida AuthZ; Domain APIs têm autoridade de regras/dados; DÉLIA não cria autoridade paralela.


**Dependências documentais:** [99 — Sidebar esquerda](./99-conversation-sidebar-left-product-ux-specification.md), [100 — Contexto direito](./100-conversation-context-panel-right-product-ux-specification.md), [97 — ConversationSearch adiada](./97-conversation-search-backend-first-future-ux-specification.md), [95 — StopResponse](./95-conversation-stop-response-product-ux-specification.md).

## 1. Decisão visual de produto

A **página completa** da DÉLIA utiliza três regiões coordenadas: **navegação de conversas à esquerda**, **conversa central como protagonista** e **funcionalidades contextuais opcionais à direita**. Sidebar e painel contextual são independentes, colapsáveis e não deslocam o conteúdo principal para fora da viewport. No Companion Dock ou em largura reduzida, não comprimir as três colunas: somente a conversa fica visível, com laterais sob demanda.

A proposta não transforma DÉLIA em dashboard nem substitui a página, menu, roteamento e SSO do Portal. Não duplicar topbar, menu global ou autenticação do host. **A página completa** tem layout interno próprio; **o Dock** usa o mesmo `ConversationWorkspace`, adaptando chrome e acessos laterais, sem runtime/fluxo conversacional paralelo.

## 2. Hierarquia e wireframes

```text
[Portal host chrome quando presente — fora do layout interno DÉLIA]
+-----------------------------------------------------------------------+
| DÉLIA — surface interna                                                |
| +-----------------+---------------------------------+-----------------+ |
| | Sidebar left    | ConversationWorkspace           | Context right   | |
| | [≡] Conversas   | DÉLIA            [context ⊞]    | Detalhes [×]    | |
| | [+] Nova        |                                 |                 | |
| | [🔎] Pesquisar  | [mensagens/respostas]            | [evidências]    | |
| | Recentes*       | [estado/activity]               | [atividades]    | |
| | [...]           |                                 | [contexto]      | |
| |                 | [ir ao final]                   |                 | |
| |                 | [composer ancorado]             |                 | |
| +-----------------+---------------------------------+-----------------+ |
+-----------------------------------------------------------------------+
* histórico real somente após contrato backend/persistência.
```

Colapso à esquerda: `[≡][+]` rail estreito ou sidebar inteiramente ocultável conforme espaço; o **toggle permanece descobrível** no header central. Direita fechada: largura zero (não reservar coluna vazia). O centro se expande naturalmente para o espaço liberado. Nenhum ícone representa capability funcional ausente.

## 3. Geometria, alinhamento e design system

- Layout externo: flex/grid responsivo com `min-width:0` nas regiões flexíveis, `min-height:0` nas superfícies com scroll, full height **do container efetivo**, nunca `100vh` cego dentro do Portal.
- Valores de design **propostos, não tokens congelados**: sidebar aberta ~260–300px; rail ~48–60px; painel direito aberto ~300–380px; área de leitura central ideal ~760px (reutilizar o limite do `ConversationWorkspace`), com respiro lateral elástico.
- Não obrigar painel direito aberto por padrão; **page default**: sidebar esquerda expandida, painel direito fechado; **Dock/mobile**: laterais fechadas.
- Divisórias verticais sutis por borda do kit; superfície central menos ornamentada; fundos diferenciados discretamente, sem cartões grossos nem sombras permanentes entre as três regiões.
- Tipografia, cores, estados, avatar e iconografia herdam `plugin-ui` e Portal (light/dark). Não introduzir tema DÉLIA paralelo.
- Cabeçalho local leve, sticky quando adequado; compositor fixo no rodapé da coluna central; corpo da conversa possui scroll próprio. Sidebar e painel contextual **rolam independentemente**, sem rolagem global indesejada.
- As áreas de foco e leitura permanecem estáveis ao expandir/recolher regiões; nenhuma perda de draft, reset de conversa, reenvio de requisição ou remount da timeline causado apenas por layout.

## 4. Composição canônica alvo

```text
DeliaConversationLayout (composição DÉLIA sobre shell compartilhado)
├── left: ConversationSidebar (doc 99)
├── center: ConversationWorkspace (REUSE do plugin-ui)
│   ├── ConversationHeader (REUSE; ações/toggles aprovados)
│   ├── ConversationReception | ConversationTimeline
│   ├── ActivityViewer / ConversationStatus / EvidenceDetails
│   ├── ConversationScrollNavigator
│   ├── GovernedConfirmation (quando houver proposal válida)
│   └── MessageComposer + ComposerStopButton
└── right: ConversationContextPanel (doc 100)
```

O nome `DeliaConversationLayout` é conceitual e **não** exige novo componente genérico sem verificar shells/drawers e layouts compartilhados existentes no `plugin-ui`. O layout visual compartilhado (caso necessário) pertence ao kit; o wrapper DÉLIA só compõe props e estado. Não mover o runtime de interação para o layout.

## 5. Responsividade e modalidades

| Contexto | Esquerda | Centro | Direita |
|---|---|---|---|
| Página ampla | Aberta inicialmente, recolhível | Sempre presente | Fechada inicialmente, abre por necessidade |
| Largura intermediária | Rail ou fechada automaticamente com toggle | Ocupa maior espaço | Drawer/sobreposição contextual |
| Mobile | Drawer modal sob demanda | Ocupa toda a largura | Drawer modal sob demanda |
| Companion Dock | Fechada; eventual acesso pelo menu contextual | Componente existente com density compacta | Fechada; conteúdo via drawer se aprovado |

Breakpoints dependem **da largura do container** e não apenas da viewport global; não fixar valores definitivos sem QA visual do Portal e Dock. Se overlays abrirem, trap de foco apenas no modal correto, scroll lock apenas na superfície efetivamente modal, fechamento por Escape quando não destruir confirmação governada, restore de foco ao botão disparador. Evitar duas drawers abertas simultaneamente em telas compactas.

## 6. Máquina de estados de layout

- `left=expanded|rail|closed` e `right=expanded|closed`, controlados independentemente pelo consumer.
- `view=full|compact|dock` derivado do espaço real do host. Adaptação pode sobrepor estado visual sem apagar a preferência, desde que não cause surpresa ao voltar à página ampla.
- Estado da interface é transitório; preferências persistidas só se houver padrão de settings/owner existente e autorização. Não usar `localStorage` ad hoc.
- Ao colapsar esquerda: manter affordance “Abrir conversas”. Ao fechar direita: manter affordance “Abrir contexto” apenas quando existe conteúdo contextual legítimo.
- Layout transitions rápidas/contidas, respeitando `prefers-reduced-motion`; não animar a timeline inteira.
- Sidebars vazias/indisponíveis devem ter copy honesta e não renderizar histórico/recursos falsos.

## 7. Fluxos de usuário

1. **Entrar na DÉLIA:** página completa inicia na experiência de recepção ou conversa real disponível, com sidebar visual adequada e contexto direito fechado; não inventar histórico.
2. **Ler/responder:** usuário mantém foco central e composer ancorado; aberturas laterais não fazem nova chamada de interação.
3. **Nova conversa:** affordance na esquerda, mas reset/seleção de sessão só com guardas apropriados; não vender como “nova sessão persistida” antes do contrato backend. Operações PREPARE/ACT pendentes não podem ser esquecidas/desvinculadas por simples reset de UI.
4. **Abrir contexto:** painel direito mostra somente projections/evidence concretas da conversa/turno atual, sem extrações especulativas de dados operacionais.
5. **Pesquisar histórico:** entrada visual/funcional somente quando busca backend e persistência autorizadas conforme doc 97; não substituir por busca no array React.
6. **Conversa em andamento:** preservar controles já existentes de stop, scroll e governança, sem efeito colateral de painel.

## 8. Reuse Gate, limites de arquitetura e contratos

**PROVEN no código:** `ConversationWorkspace` implementa header/body/footer/scrollNavigator; `ConversationHeader` já oferece `actions`; `App.tsx` renderiza um único shell e estado React transitório sem persistência conversacional no backend.  
`EXISTING_EQUIVALENT=YES` para o workspace central e chrome; `TO_INVENTORY` para layout de três regiões/drawers/toggles equivalentes no kit; `REUSE_DECISION=REUSE` o centro + `EXTEND/NEW_PENDING_GATE` para shell de composição. Não duplicar serviços, tabelas ou routers.

A composição nunca executa Domain writes, não interpreta JWT como permissão, não deriva autorização de provider metadata, não presume persistência. Os contratos de conversas, contexto e actions serão definidos antes de conexões funcionais. `discovery != approval`; `read != write`; `PREPARE != ACT`; `technical success != business outcome`.

## 9. Acessibilidade, qualidade e critérios futuros

- Regiões landmark nomeadas de modo único (navegação à esquerda, main central, complementary à direita somente quando aberto); heading hierarchy sem vários `h1` redundantes.
- Toggles `aria-expanded`/`aria-controls`, nomes claros, keyboard/focus visible, foco restaurado após drawer; não criar regiões `aria-live` sobrepostas.
- Estados loading/error/empty do centro e laterais independentes; quem lê não perde a posição ao mudar largura.
- QA: desktop amplo, intermediário, 320/375/420px, zoom 200%, Portal embedded e Companion Dock, dark/light, reduced motion, tab order, screen reader; sem horizontal overflow global.
- Regressão: composer, scroll, activity, provenance, confirmação governada, docs 92–97; build plugin-ui/DÉLIA, gate federado, browser QA sobre SHA efetivo; `TEST_NOT_RUN` até executar.
- Critério de aceite do shell: UI pode ser implementada antes de backend, mas históricos e recursos não contratados ficam ocultos/indisponíveis, sem mocks em produção.

## 10. Execução futura e status

Definir contratos visuais/props somente depois de inventário de layout primitives e revisão dos owners. Implementação em slices: (A) shell e responsive sem alterar runtime, (B) sidebar visual e toggles, (C) contexto direito visual e toggles, (D) backend/estado persistido em outra autorização. Registrar commit, SHA, build/test/QA e review reais; documentação não promove fase.

```text
SPEC_STATUS = DOCUMENTED_PRODUCT_TARGET
FULL_PAGE_THREE_REGION_SHELL = NOT_IMPLEMENTED
CENTRAL_CONVERSATION_WORKSPACE = PROVEN_EXISTING
SIDEBAR_CONVERSATION_HISTORY = BACKEND_DEPENDENT
RIGHT_CONTEXT_CONTENT = CONTRACT_DEPENDENT
REUSE_DECISION = REUSE_CENTER + FUTURE_GATE_FOR_SHELL
TESTS = TEST_NOT_RUN
PHASE_PROGRESSION = NONE
```

## 11. Registro da implementação frontend bounded — 2026-10-16

**Autorização de produto:** shell visual de três regiões em `plugin-ui` e importação como página composta da DÉLIA, preservando componentes conversacionais existentes.

**Arquivos implementados:**
- `plugins/plugin-ui/src/components/conversation/ConversationThreeRegionLayout.tsx`: layout render-only, left nav, centro sempre montado, aside direito opcional; toggles de abertura/fechamento e affordances acessíveis; regiões de conteúdo via props.
- `plugins/plugin-ui/src/components/conversation/ConversationThreeRegionLayout.css`: três colunas flexíveis; sob largura do container `delia-page` de 920px, laterais como overlays sobre o centro, com backdrop.
- `plugins/plugin-ui/src/components/conversation/index.ts` + `src/index.ts`: export público e nomeado Federation; `scripts/verify-host-exports.mjs`: gate requerido.
- `plugins/delia/src/ui/DeliaConversationPage.tsx`: composição única da página, importando layout do kit; esquerda/direita contêm somente mensagens neutras de indisponibilidade; histórico persistido e detalhes não são simulados.
- `plugins/delia/src/App.tsx`: mantém as instâncias existentes de `ConversationWorkspace`, `ConversationHeader`, `ConversationTimeline`/`Reception`, `ActivityViewer`, `ConversationScrollNavigator`, `DeliaComposer` e governança, incorporadas no slot central da página única.
- Testes criados para shell e wrapper; CSS/tokens compartilhados com Portal.

**Limite de escopo:** histórico, busca, criação persistida de conversa, seleção de turnos no painel direito, menus e dados contextuais reais **não foram implementados**; seu slot visual existe, mas não representa capabilities de backend existentes. Layout central continua com runtime/state próprios. Sidebar da DÉLIA não substitui navegação global do Portal.

**Evidência:** commit(s) em `main` via API GitHub; fetch de conteúdo/HEAD confirma persistência. Não há runner de build ou navegador autenticado disponível nesta execução, portanto `TESTS=TEST_NOT_RUN`, `TYPECHECK=TEST_NOT_RUN`, `FEDERATION_BUILD=TEST_NOT_RUN`, `BROWSER_QA=TEST_NOT_RUN`. Revisão independente `PENDING`. Não inferir PASS de arquivo criado.

```text
SHELL_IMPLEMENTATION = CODE_COMMITTED_CANDIDATE
CENTRAL_WORKSPACE_REUSE = YES
SIDEBAR_HISTORY = NOT_IMPLEMENTED
RIGHT_CONTEXT_BACKEND = NOT_IMPLEMENTED
RUNTIME_TESTS = TEST_NOT_RUN
INDEPENDENT_REVIEW = PENDING
PHASE_PROGRESSION = NONE
```

## 12. Revisão visual R1 — alinhamento ao design system DELPI (2026-10-16)

**Origem da evidência:** duas capturas reais da página `/apps/delia` fornecidas pelo Product Master. Na primeira o shell tinha apenas mensagens neutras nas laterais; na segunda os controles e grupos básicos já estavam renderizados. A estrutura de três colunas está coerente com os docs 98–100, mas a execução visual **não** corresponde ao padrão moderno/clean desejado. **Status:** `UX_REVIEW=REWORK`; esta seção atualiza o **alvo de aparência** e substitui, em conflitos visuais, as propostas anteriores destes três documentos. Os registros de implementação anteriores continuam históricos; **nenhum código foi alterado por esta revisão documental**.

### 12.1 Diagnóstico verificável nas capturas

1. **Duplicação de affordance de colapso:** botão no cabeçalho de cada lateral **e** botão no topo do centro. Isso cria ambiguidade, retrabalho cognitivo e aparência de controle técnico.
2. **Segunda barra horizontal no topo do centro:** há uma faixa para toggles, separada do `ConversationHeader`, seguida de cabeçalho interno “DÉLIA”. Duas camadas visuais sem necessidade. O centro deve ter **um único header conversacional**, e as ações de painel devem compor seu slot `actions`/posições de extremidade apropriadas.
3. **Laterais como blocos de cor pesada:** esquerda e direita aparecem densas, com fundos sólidos azulados e separação forte do canvas escuro, quebrando continuidade da experiência clean.
4. **Sidebar com controle primário excessivamente encaixotado:** Nova conversa e Pesquisar parecem campos/botões de formulário administrativo e não navegação conversacional.
5. **Painel direito poluído por mensagens repetidas de indisponibilidade:** Detalhes, Evidências e Atividades repetem textos longos, divisórias e vazios, apesar de não existirem projeções válidas.
6. **Hierarquia espacial ainda sem refinamento:** títulos/paddings, ícones e seções das laterais não acompanham a leveza da recepção central.
7. **Responsividade não evidenciada nessas imagens:** capturas de desktop não constituem aceite de Dock, zoom ou drawers.

### 12.2 Direção visual aprovada como alvo — uma superfície coesa

- **Três regiões, mas uma página só**: canvas contínuo com sutis diferenças de tom e divisores hairline. Na ausência de tokens exatos de tema, derivar exclusivamente de `--delpi-ui-*` e fallbacks Portal; sem cores hardcoded como identidade nova. Área central continua predominante.
- **Larguras-alvo para QA, não valores congelados:** esquerda 248–288px, centro flexível com leitura centrada conforme `ConversationWorkspace` (~760px de medida interna existente), direita 296–344px quando aberta. Abaixo de largura útil apropriada, laterais viram drawers e o centro ocupa 100%; não comprimir três colunas simultâneas no Dock.
- **Ritmo de 8px e tipografia compartilhada:** gap entre ícone e rótulo ~10–12px, padding horizontal de painel ~16–20px, cabeçalho de painel ~52–60px, raio de controles ~10–12px, hit target preferencial ≥40–44px. Ajustar tokens ao kit real, não inventar escala CSS paralela.
- **Hierarquia:** DÉLIA/recepção/timeline/composer no centro; textos periféricos menos contrastantes e mais compactos; peso e tamanho coerentes com o `ConversationHeader`. Títulos laterais ≠ títulos de página.
- **Superfícies:** painéis não são cartões autônomos grossos. De preferência, mesma família de surface da conversa, com leve gradação de contraste e bordas de baixa opacidade, como `RoomSidePanel` compartilhado. Sem shadow permanente desktop, exceto drawer overlay.
- **Microinterações:** hover por fundo sutil, selected por tom/acento discreto e indicador não dependente só de cor, `focus-visible` consistente, transições discretas e `prefers-reduced-motion`.
- **Central sem chrome extra:** nenhuma barra vazia de 42px para dois toggles. Integrar o botão **Abrir conversas** no início do header central **apenas quando esquerda estiver recolhida**; botão **Abrir contexto** no final do mesmo header **apenas quando painel direito estiver fechado** e a affordance for pertinente. O `ConversationHeader` atual já suporta `leading` e `actions`; **REUSE**, não substituição. Alternativamente, integrar a gestão visual pelo shell com slots do header, se o contrato do consumer exigir; não criar dois headers.
- **Único owner de cada estado e toggle:** o shell coordena `left/right open`, mas expõe um único controle efetivo por região, na região visível correta. Esquerda aberta: botão de recolher no cabeçalho da sidebar; esquerda fechada: abrir no header central. Direita aberta: fechar no cabeçalho de contexto; direita fechada: abrir no header central. Nenhum par de controles duplicado e simultâneo.
- **No desktop:** ambas as laterais podem coexistir abertas sem desfocar o centro. No Dock/mobile: uma única drawer por vez, backdrop e gerenciamento de foco, sem barra técnica superior persistente. O host Portal não deve receber uma segunda navegação global.

### 12.3 Wireframe visual corrigido

```text
+--------------------------+----------------------------------+---------------------------+
| Conversas           [‹] |  DÉLIA                  [› ctx] | Contexto              [×] |
|                          |  Inteligência operacional        |                           |
| [+] Nova conversa        |                                  | Detalhes (quando houver)   |
| [⌕] Pesquisar             |     Recepção ou timeline         | Evidências (quando houver) |
|                          |                                  | Atividades (quando houver) |
| Recentes                 |                                  |                           |
|  estado vazio discreto   |                                  |   texto de orientação      |
|                          |                                  |   único, se vazio         |
|                          |   Composer ancorado              |                           |
| Opções                   |                                  |                           |
+--------------------------+----------------------------------+---------------------------+
```

**O desenho representa regiões abertas para revisão. Estado inicial da página:** esquerda aberta e direita fechada; sem sobreposição fixa. Se a direita estiver aberta, o botão `[› ctx]` central não aparece; se esquerda aberta, não duplicar “abrir/recolher” no centro. Em telas estreitas, as duas laterais ficam fechadas e seus controles de abertura são colocados no header central.

### 12.4 Contrato visual de composição (antes do próximo código)

- `ConversationThreeRegionLayout`: exclusivamente geometria, abertura, fechamento, drawer/foco, breakpoints de container; **não renderiza uma nova topbar visual independente**. O centro é o `ConversationWorkspace` existente, preservado sem remount.
- `ConversationHeader`: owner da única barra de identidade DÉLIA; seus `leading/actions` acomodam toggles de painéis **sem duplicar**. Propor uma interface com slots/callbacks controlados se necessário após inventário.
- `ConversationSidebar` (doc 99): owner visual de Nova conversa, Pesquisar, Recentes, Opções e sua composição de header.
- `ConversationContextPanel` (doc 100): owner visual de Detalhes, Evidências e Atividades, junto a uma apresentação neutra honesta.
- `DeliaConversationPage`: wrapper de produto integra shell e widgets; `App.tsx` continua dono da conversa, do transporte, dos turnos e dos gates.
- `EXISTING_EQUIVALENT=YES` para `ConversationHeader`, `ConversationWorkspace`, `IconButton` e `RoomSidePanel` como referência de superfícies. `REUSE_DECISION=REUSE` para primitives; `EXTEND` para os composites. Nenhum framework de layout novo.
- Ausência de contrato backend não é motivo para UI com três mensagens idênticas de indisponibilidade. A UI pode reservar espaços, mostrar controles desabilitados *honestamente*, e apresentar **um** empty state conciso por painel.

### 12.5 Critérios objetivos de revisão visual e funcional

1. **EXATAMENTE UM** controle de recolher/abrir por região conforme estado; zero barra técnica adicional no topo central.
2. Sidebar e painel direito parecem parte da mesma aplicação do centro, com tokens e densidade consistentes; não têm “azul pesado” apartado nem molduras administrativas.
3. Largura do centro e largura efetiva da coluna de leitura preservadas ao alternar painéis; nenhum shift de recepção/composer além do redimensionamento natural.
4. Ações não contratadas não disparam buscas, sessões, evidências ou opções fictícias. Um empty state contextual por painel, sem spam em três seções.
5. Desktop com esquerda aberta/direita fechada por default; desktop suporta direita aberta; Dock/mobile com drawers fechadas por default e apenas uma drawer aberta.
6. Keyboard/foco/restauração, contraste, light/dark, 320/375/420px, zoom 200%, reduced motion e visual QA em Portal/Dock.
7. Criar comparação *antes/depois* no mesmo viewport, capturas do navegador reais e review independente. Não inferir PASS de mockup, documentação ou commit.
8. Testes comportamentais de toggle, remount, estado do composer, drawer, ausência de backend e export federado no HEAD/config efetivo.

```text
UX_R1 = DOCUMENTED_CORRECTION_TARGET
VISUAL_REVIEW = REWORK
SHELL_THREE_REGION_GEOMETRY = PRESERVE
DUPLICATE_TOGGLES = REMOVE_IN_FUTURE_CODE
CENTER_EXTRA_TOOLBAR = REMOVE_IN_FUTURE_CODE
DOCUMENTATION_UPDATE != RUNTIME_CORRECTION
IMPLEMENTATION = PENDING
TESTS_AND_BROWSER_QA = TEST_NOT_RUN
PHASE_PROGRESSION = NONE
```

## 13. Execução do rework UX R1 — evidência e comparativo

**Task:** `DELIA-UX-THREE-REGION-SHELL-VISUAL-REWORK-R1` (2026-10-16). **Autorização:** pedido explícito do Product Master de corrigir duplicações e aparência; sem novos contratos backend.

**Diff de apresentação no GitHub:** `ConversationThreeRegionLayout.tsx` removeu a topbar `__controls`; agora o slot `center` aceita uma função de render com `leftToggle` e `rightToggle` para compor o `ConversationHeader.leading/actions` existente. Um único controle de fechamento fica no header da lateral aberta; botão de abertura surge no header central somente enquanto a lateral está fechada. `plugins/delia/src/App.tsx` fornece os slots sem alterar runtime de mensagens, composer, activity e governança. `DeliaConversationPage` mantém uma composição única. CSS remove barra horizontal, reduz tratamento cromático pesado e reutiliza surfaces/tokens do kit. Em contêiner estreito, laterais são drawers mutuamente exclusivas, com backdrop e Escape; callbacks do layout não invocam backend.

**Comparativo por evidência:**

| Observação nas capturas ANTES | Direção implementada no código DEPOIS | Evidência e limite |
|---|---|---|
| Topbar separada sobre o header DÉLIA | Topbar removida; toggles integram `ConversationHeader` | Confirmado por diff/source; browser pós-change não capturado |
| Duplicidade dos botões de recolher | Controle de fechar exclusivo da lateral aberta e de abrir no centro quando fechada | Confirmado por render condicional; teste criado, ainda não executado |
| Painéis com cor sólida e divisores fortes | Surfaces do Portal e divisórias hairline de baixo contraste | Confirmado por CSS; contraste real requer browser |
| Vários avisos de vazio no contexto | Um estado vazio curto após as três seções | Confirmado pelo componente; QA visual não executado |
| Navegação com controles encaixotados | Tratamento tonal leve e ações com foco/hover de kit | Confirmado por CSS; screenshot pós-change pendente |

**QA comparativo de navegador:** as **capturas anteriores** são evidência real de BEFORE; não foi possível abrir uma sessão autenticada no Portal nem gerar screenshot AFTER do runtime/deploy neste ambiente. Classificação obrigatória `BROWSER_QA_AFTER=TEST_NOT_RUN`, `PIXEL_COMPARISON=INCONCLUSIVE`; nunca reportar PASS. Acesso GitHub via plugin permite atualizar arquivos e verificar HEAD, **não** executa o build, TypeScript ou Vitest. `TESTS_CREATED=YES`, `TESTS_EXECUTED=NO`, `BUILD=TEST_NOT_RUN`, `FEDERATION=TEST_NOT_RUN`. Publicação de código na main **não é deploy**.

**Gate de aceite**: reexecutar testes de `plugin-ui` e `delia`, verificar export federado e testar em Browser full-page/Dock light/dark e 320/375/420px, incluindo zoom 200%, teclado, Escape, foco, ausência de overflow, nenhuma duplicação, teste do composer/turnos e reversibilidade do painel. Comparar novas capturas do mesmo viewport com as fornecidas antes. Review independente ainda `PENDING`; fase canônica não avança.

```text
UX_R1_CODE = COMMITTED_CANDIDATE
CENTER_EXTRA_TOOLBAR = REMOVED_IN_SOURCE
DUPLICATE_TOGGLE = ADDRESSED_IN_SOURCE
CONTEXT_EMPTY_STATE = SINGLE
VISUAL_BROWSER_QA = TEST_NOT_RUN
COMPARATIVE_BROWSER_RESULT = INCONCLUSIVE
INDEPENDENT_ACCEPTANCE = PENDING
PHASE_PROGRESSION = NONE
```
