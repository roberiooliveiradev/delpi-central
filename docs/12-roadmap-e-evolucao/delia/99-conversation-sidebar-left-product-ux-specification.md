# 99 — DÉLIA | ConversationSidebar — Navegação esquerda de conversas

**Data:** 2026-10-16  
**Natureza:** especificação de produto, UX e contrato visual **somente documental**. Não autoriza runtime, migração, backend, deploy, CP ou avanço de fase.  
**Produto:** DÉLIA standalone (não é Minha DELPI Chat).  
**Base factual:** `main` no SHA `395bd45012f8b45899f07e226b6525df9e0a0c66`. Revalidar HEAD antes de implementar.  
**Autoridade:** HEAD/git status → Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → specs temáticas → ledger. Conflito = `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`; não reconciliar silenciosamente.  
**Propriedade:** `plugin-ui` hospeda componentes visuais reutilizáveis; `plugins/delia` compõe produto, decide estados de interface e integra contratos autorizados. Portal hospeda/navega; Core valida AuthZ; Domain APIs têm autoridade de regras/dados; DÉLIA não cria autoridade paralela.


**Posicionamento:** região **esquerda** do layout completo [doc 98](./98-delia-full-page-three-region-layout-product-ux-specification.md). **Painel direito independente:** [doc 100](./100-conversation-context-panel-right-product-ux-specification.md). **Busca no histórico:** [doc 97](./97-conversation-search-backend-first-future-ux-specification.md).

## 1. Responsabilidade e hierarquia

`ConversationSidebar` oferece navegação conversacional (não navegação global de apps, não catálogo de capabilities). Contém affordances para iniciar uma conversa, localizar histórico **quando real**, selecionar conversa autorizada, identificar sessão ativa e exibir ações contextuais legitimamente contratadas.

```text
+--------------------------------+
| [☰ recolher]      Conversas    |
| [+ Nova conversa]              |
| [🔍 Pesquisar conversas]*      |
|                                |
| Recentes*                      |
| [• Indicadores de produção]    |
| [  Análise de capacidade] [···]|
| Ontem*                         |
| [  Pendências operacionais]    |
|                                |
| [opções pertinentes]*          |
+--------------------------------+
* não renderizar em produção sem contrato, dados ou função reais
```

Não inventar títulos, data, agrupamento temporal ou seleção de conversas persistidas antes do backend. A sidebar **não** deve apresentar lista de sessões React transitórias como histórico real.

## 2. Aparência e estrutura

- Largura expandida alvo ~260–300px; border-right fina, fundo ligeiramente distinto do centro, altura do shell interno. Ajustar ao Portal e tokens existentes; valores são candidatos, não freeze de CSS.
- Header superior compacto com rótulo “Conversas”, ícone e toggle “Recolher barra lateral”. Não duplicar título principal da DÉLIA nem logo institucional em excesso.
- Ação “Nova conversa” prioritária, de alto reconhecimento visual (ícone `SquarePen`/Lucide ou equivalente), com label expandido; no rail, ícone acompanhado de `aria-label`/tooltip.
- Busca posicionada abaixo de Nova conversa, mas **não ativa** até que persistence/search backend sejam contratados (doc 97); preferir omitir a affordance em runtime a abrir busca local de fachada.
- Lista ocupa o espaço flexível e rola de modo independente; entradas leves e densidade confortável; títulos truncados com elipse, mantendo label completo por mecanismo acessível e sem fuga de dados.
- Agrupamentos (“Recentes”, “Ontem”, “Esta semana”) são alvos UX futuros e exigem timestamps/ordenação/fuso de fonte autoritativa.
- Item selecionado com fundo/tom do kit e indicador além de cor; hover/active/focus-visible; menu de reticências somente com operações implementadas (ex.: renomear, arquivar/excluir quando contratos existirem).
- Rodapé reservado para opções de **conversa** legitimadas pelo produto. Não duplicar settings globais, perfil Portal, Keycloak, área de aplicações ou funcionalidades do painel direito.

## 3. Estados visuais

| Estado | Aparência/funcionalidade |
|---|---|
| `expanded` | Barra completa com labels, itens e regiões válidas |
| `rail` | Faixa estreita com ícones de toggle/nova conversa e affordances realmente ativas; sem truncamento enganoso |
| `closed` | Região oculta, toggle acessível disponível no centro |
| `drawer` | Overlay em mobile/dock, com backdrop, close, focus trap e restore focus |
| `empty_unpersisted` | Não alegar “Você não tem conversas”; mostrar apenas controles seguros e texto neutro sobre histórico não disponível, quando fizer sentido |
| `loading_history` | Skeleton/estado honesto após API autorizada; nunca spinner permanente fictício |
| `empty_history` | Mensagem clara somente após consulta real bem-sucedida ao escopo autorizado |
| `history_error` | Falha tipada; opção de tentar novamente quando existir callback/contrato |
| `permission_denied` | Sem vazamento de nomes/snippets; informação neutra |
| `selected` | Item autorizado ativo, realçado sem depender só de cor |

Não implementar lista do futuro para dar aparência de feature pronta. Layout/chrome pode existir antes de backend, com área de histórico omitida.

## 4. Funcionalidades completas esperadas

### 4.1 Recolher e expandir

- Toggle persistente e descobrível; expandida ↔ rail ↔ fechada conforme responsive. Sem remount do `ConversationWorkspace` ou perda de draft.
- `aria-expanded`, `aria-controls`, keyboard Enter/Space, foco visível e retorno ao toggle quando sidebar fecha. No mobile, a barra é drawer acessível, não coluna fixa estreita.
- Preferência de expansão opcional somente por owner/capability existente de preferências; proibido criar `localStorage` ad hoc.

### 4.2 Nova conversa (dependências)

- Objetivo futuro: solicitar nova sessão DÉLIA persistida a um contrato legítimo e navegar somente após resposta autoritativa. Não confundir com limpar `turns` da memória React.
- O botão pode aparecer como affordance visual em uma entrega frontend bounded, mas **não pode ser clicável sem callback seguro real**; preferir desabilitado com tratamento honesto até contrato/guardas.
- Ao haver rascunho não enviado: proteção contra descarte, confirmar intenção com UI legítima. Em turnos em curso: interromper **somente espera local** quando permitido, nunca afirmar rollback de backend. Havendo proposta de operação governada, preservar/reconciliar estado; não navegar para contornar decisão.
- Quando existir sessão persistida: criar/selecionar pelo backend, não gerar ID autoritativo no frontend; idempotência para duplo clique, tratamento de falhas sem perder conversa anterior.

### 4.3 Lista de conversas e ações

- História e títulos fornecidos pelo owner; IDs estáveis e opacos; paginação/cursor, carga progressiva e limites. Não derivar título “inteligente” por LLM sem contrato/revisão.
- Ordem/agrupamentos por dados de publicação, observando timezone; restrições e exclusões governadas.
- Seleção deve recuperar/validar acesso **live**, preservar foco e rolagem por mensagem, sem restaurar conteúdo de cache não autorizado.
- Item poderá exibir menu contextual de “Renomear / Arquivar / Excluir” **apenas após** contratos write, AuthZ live, idempotência, audit e postcondition; não habilitar menu por conveniência.
- Distinção visual entre item ativo, hover, indisponível, arquivado, sem acesso e carregando; não vazar existência de conversas restritas.
- Pesquisa deve utilizar backend conforme doc 97, não indexação no array React. Não simular resultados.

### 4.4 Acessibilidade e microinterações

- Landmark `nav` nomeado “Conversas”, se não conflitar com navegação Portal; lista semântica; controles action `button` e navegação `a` apenas para rotas autorizadas.
- Tab order: toggle, Nova conversa, busca autorizada, itens, menu contextual, sem trap fora de modal. Menu por item com semântica própria e keyboard Escape/Arrow quando adotado.
- Labels completos em rail via `aria-label`/tooltip acessível; indicadores selected/pending não dependem exclusivamente de cor; responsividade 320/420px e zoom 200%.
- No Dock, preferir não renderizar rail permanentemente; drawer sob demanda para não sufocar o composer.
- Transições contidas, reduced motion respeitado; não emitir anúncios massivos a screen readers quando histórico atualiza.

## 5. Reuse, owners e contratos

**PROVEN:** `ConversationHeader` aceita `actions`, `ConversationWorkspace` permanece central, existem botões e chrome no `plugin-ui`. `plugins/delia/src/App.tsx` mantém conversa transitória em React, não histórica persistida.

`EXISTING_EQUIVALENT=YES` para botões/layout base; `EXISTING_EQUIVALENT=TO_INVENTORY` para sidebar/drawer/lista de conversas concreta e serviços de history. `REUSE_DECISION=REUSE` primitives; `EXTEND/NEW_PENDING_GATE` para composição de sidebar. Validar kit de navegação, menus, drawer, empty state e virtualized list antes de criar novo.

Contrato backend **futuro**, não definido aqui: `createConversation`, `listConversations`, `getConversation`, `listTurns`, `searchConversations`, ações de manutenção conforme owner — estes são **nomes ilustrativos**, não `operationId` nem endpoints congelados. Especificar owner/consumers, schemas/version, AuthN, Core live AuthZ, Domain rules, erros, paginação, idempotência, limites, retention, compatibilidade, observabilidade e postconditions antes de integrar.

## 6. Separação de subcomponentes (proposta sujeita a gate)

- `ConversationSidebar` — composição e estados de abertura.
- `ConversationSidebarToggle` — controle de expandir/recolher.
- `ConversationNewSession` — intenção de criar nova conversa, sem política backend no UI kit.
- `ConversationHistoryList` + `ConversationHistoryItem` — itens e grupos de histórico real, após contrato.
- `ConversationSidebarSearch` — entrada para a busca backend futura, não componente de busca local.
- `ConversationItemActions` — menu de ações apenas com owner write/policy.
- Não tratar essa enumeração como autorização para gerar todos os componentes. Reuse-before-design em cada slice.

## 7. Testes/aceite futuros

1. Expansão/rail/fechamento/drawer não afetam conversa ou draft.
2. Sidebar navega por conversas reais com autenticação/Autorização e sem acesso a terceiros.
3. Nenhum item fake, search local ou persistência frontend temporária em produção.
4. Seleção, paginação, stale cursor, loading/error/ACL e remoção de itens funcionam via contratos.
5. Guardas de rascunho, requisição em andamento e PREPARE/ACT pendente comprovados.
6. Ações write não existem sem owner/Policy/AuthZ live e postcondition.
7. Page full + Dock/mobile com browser QA, teclado, screen reader, tema e zoom 200%.
8. Testes independentes de componente, integração, build e Module Federation com SHA/config.

## 8. Estado documental

```text
SPEC_STATUS = DOCUMENTED_PRODUCT_TARGET
CONVERSATION_SIDEBAR = NOT_IMPLEMENTED
HISTORY_LIST_RUNTIME = NOT_AUTHORIZED_WITHOUT_BACKEND
NEW_PERSISTED_SESSION = CONTRACT_PENDING
CONVERSATION_SEARCH = DEFERRED_DOC_97
VISUAL_PRIMITIVES = REUSE
BACKEND_CONTRACTS = TO_INVENTORY
TESTS = TEST_NOT_RUN
PHASE_PROGRESSION = NONE
```

## Registro de implementação visual bounded — 2026-10-16

A pedido do Product Master, foram adicionadas ao `plugin-ui` as superfícies reais `ConversationSidebar` e `ConversationSidebarSearch`, importadas pelo wrapper `plugins/delia/src/ui/DeliaConversationPage.tsx`, mantendo o layout único do doc 98. Estão posicionados: botão **Nova conversa**, entrada **Pesquisar conversas**, grupo **Recentes**, botão **Opções** e toggle de recolhimento no shell compartilhado. Sem contratos de sessões e pesquisa, ações `onNewConversation`, `onSearch`, `onOptions` permanecem desabilitadas; nenhuma conversa mock é inserida em Recentes. A busca é somente entrypoint visual, não indexação em estado React. O componente tem props explícitas para ativação **somente** após validação backend. `EXISTING_EQUIVALENT=YES` (primitives do kit); `REUSE_DECISION=EXTEND` (composição). Testes/build/browser ainda `TEST_NOT_RUN`; review independente `PENDING`; fase inalterada.

## 9. Revisão visual R1 — sidebar de navegação clean (2026-10-16)

**Evidência:** capturas reais fornecidas pelo Product Master e comparação com `ConversationSidebar` e CSS no `plugin-ui` (HEAD `18583359972f22ff76041859740307f401628933`). A implementação possui áreas corretas, mas visual de formulário provisório, fundo pesado, mensagens longas e duplicação dos toggles. Este capítulo **substitui os alvos de aparência conflitantes** acima, não altera os registros históricos nem implementa código. Ver [98 §12](./98-delia-full-page-three-region-layout-product-ux-specification.md).

### 9.1 Composição refinada

```text
  Conversas                             [recolher ‹]
  [+]  Nova conversa
  [⌕]  Pesquisar conversas

  Recentes
  [item de conversa autorizado quando existir]
  [mensagem curta de estado vazio, somente se necessário]

  (flex space)

  [sliders] Opções
```

- **Cabeçalho:** título discreto com hierarquia do design system, ícone de colapso único no canto direito **somente quando sidebar aberta**. Não exibir simultaneamente um segundo toggle no topo central.
- **Nova conversa:** botão primário de navegação, aparência **tonal discreta** e ícone `SquarePen`; não usar retângulo preto opaco, borda grossa nem aparência de input. Altura alvo 40–44px, radius do kit, largura alinhada à lista. Quando não disponível, disabled visual refinado sem fingir click.
- **Pesquisar:** linha de navegação leve com lupa à esquerda; até existir contrato pode ficar desabilitada. Não parecer um campo de pesquisa escuro e vazio: **não renderizar fake input**. Após contrato, poderá abrir a busca backend do doc 97; somente então um input real será exibido.
- **Recentes:** heading sutil (menor, muted e com respiro), itens futuros com ícone discreto, título de linha única e `aria-current` no ativo. Sem chips ou bordas em todos os itens; destaque ativo por superfície tonal suave e indicador legível no tema.
- **Sem histórico persistido:** apresentar no máximo uma frase curta e neutra, como “As conversas aparecerão aqui quando o histórico estiver disponível.” Em contextos muito compactos, **ocultar texto** em vez de preencher grande área com explicação de backend. Nunca inventar dados e nunca dizer que a lista foi consultada se não foi.
- **Opções:** rodapé sticky visualmente leve, separação tênue opcional, ícone `Settings2`, não usar segundo menu global de perfil/settings Portal. Se `onOptions` ausente, botão disabled com hint conciso; nenhum menu falso.
- **Espaçamento:** padding horizontal ~16–20px, gap vertical ~8px entre ações e ~16–20px entre grupos; texto 13–14px para navegação, label de grupo 11–12px conforme tokens existentes. Sem borda em cada linha e sem alta densidade.
- **Fundo:** herdar superfície compartilhada do shell (ligeira diferença tonal, sem “painel azul opaco”). Border-right hairline como separação suficiente; sem cartão interno para todas as seções.
- **Hover/selected/focus:** hover sutil, foco visível consistente, selected distinto do hover. Não reduzir contraste de disabled a ponto de ficar ilegível no dark mode.

### 9.2 Estados e colapso

- **Expandida:** contém título, toggle único, Nova conversa, Pesquisar, Recentes e Opções. A barra central **não repete** o botão de recolhimento.
- **Fechada:** ocupa largura zero e libera espaço ao centro. O botão **Abrir conversas** aparece no header central, posicionado no começo de forma harmoniosa.
- **Rail:** apenas como variante **futura opt-in** se houver espaço/teste justificando; não introduzir automaticamente uma terceira forma de sidebar ao corrigir esta entrega. Se implementado, ícones devem ter labels acessíveis e sem controles duplicados.
- **Dock/mobile:** sidebar como drawer com backdrop; aberta apenas por comando e única drawer simultânea. Escape/restauração de foco e rolagem independentemente; não deixar um rail fixo espremendo o composer.
- **Preferência:** sem localStorage ad hoc; preservar a decisão de responsividade e o estado de interação independentemente da abertura.
- O header da sidebar é **o único** local do botão de fechar enquanto a barra estiver visível. Quando fecha, o controle migra para o header central; essa regra vale também no drawer.

### 9.3 Dependências e contrato visual

O componente `ConversationSidebar` deve permanecer render-only e aceitar callbacks e itens autorizados fornecidos pela DÉLIA; não conhece armazenamento, indexação, autorização ou APIs. `ConversationSidebarSearch` continua affordance de busca contratual, sem digitação local sobre `turns`. A barra de header/toggles é responsabilidade da composição shell/header, nunca duplicada pela própria sidebar.

Revisar primeiro `IconButton`, botões e menu/navigation existentes em `plugin-ui`, `RoomSidePanel` para surface e os tokens Portal. `EXISTING_EQUIVALENT=YES` (primitives de botão/navegação); `REUSE_DECISION=EXTEND` para sidebar. Nada de primitive com branding DÉLIA dentro do kit.

### 9.4 Gates de aceite visual

- Screenshot desktop da sidebar aberta com **um** toggle; com sidebar fechada, apenas toggle central.
- Botões não se parecem com textareas/inputs; ações apresentam estado disabled sem false affordance.
- Grupo Recentes tem hierarquia sutil e empty state mínimo, sem resultado fake.
- Opções fica ao final sem segunda navegação institucional.
- Page e Dock preservam a largura, foco, tema dark/light, teclado, zoom e transições reduzidas.
- Não criar callbacks backend nesta correção de UI. `UX_REVIEW=REWORK`; `RUNTIME_TESTS=TEST_NOT_RUN` até execução.

## 10. Implementação visual R1 — registro

`ConversationSidebar` permanece render-only com Nova conversa, Pesquisar, Recentes e Opções bounded, desabilitados quando faltam callbacks contratuais; não existe história inventada nem pesquisa local. O shell removeu a duplicação: quando aberta, sidebar tem **um** botão de recolher no próprio header e **nenhum** toggle equivalente no centro; quando fechada, botão de abrir aparece no `ConversationHeader.leading`. O CSS recebe refinamento tonal discreto, sem bordas pesadas nas ações. Testes de conduta atualizados; `TEST_NOT_RUN` para runner/QA no ambiente desta task. Aceite visual independente pendente. 

## 11. Direção R2 — rail de ícones persistente (2026-10-16)

Decisão superior do Product Master: `Recolher conversas` transforma a largura expandida em **rail**, não remove a região. Alvo: ~64px desktop e ~52px em containers compactos, adaptado aos tokens reais; botão superior passa para `Expandir conversas`. Permanecem em rail os ícones de **Nova conversa**, **Pesquisar conversas** e **Opções**, com `aria-label` e tooltip. Grupo Recentes/histórico e seus labels somem apenas visualmente quando colapsado; zero perda de estado da conversa. Nenhum botão sem backend recebe handler artificial. Não duplicar controle no header central. `ConversationSidebar.collapsed` é propriedade render-only de layout; persistência de preferência não implementada. Implementação candidata no Plugin UI, testes criados/atualizados `TEST_NOT_RUN`, QA navegador `TEST_NOT_RUN`, fase inalterada.
