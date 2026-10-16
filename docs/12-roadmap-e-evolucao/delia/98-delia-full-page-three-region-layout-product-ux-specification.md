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
