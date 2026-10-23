# DÉLIA — Composer Settings e Dictation Mode Settings — Especificação UX

**Data:** 2026-10-23. **Status:** IMPLEMENTED_AND_HOMOLOGATED (2026-10-23, commit `77f1aa67c5`, deploy prod + QA 36/36). **Owner de composição:** plugins/delia; **primitivas compartilhadas:** plugins/plugin-ui. **Consumers:** full-page e Companion Dock da DÉLIA. **Fontes:** docs 119, 120, 123 §12, 124, contratos dictation.transcription.v1 e dictation.incremental.v1. **HEAD na elaboração:** 668034de3d0ede27b2f3348cdd934727b807a9e9. Reancorar no HEAD antes de executar.

## 1. Decisão de produto

O seletor horizontal e permanente `SegmentToggle` de modo de ditado, atualmente acima do campo de pergunta, **deixa de ser o elemento principal da composição visual**. A escolha passa para um **menu de configurações do composer** aberto por controle discreto na própria barra de ações, preferencialmente próximo ao microfone. O editor recupera espaço vertical e mantém a superfície única. Esta é uma proposta de alteração **visual/interativa**, sem modificar contratos de STT ou backend.

**Extensibilidade futura:** o menu **poderá abrigar outras configurações do composer** (não somente ditado). Esta decisão não autoriza criar um framework de settings, registry, persistence layer, Core settings, feature flags ou opções fictícias antecipadamente. Adicionar futuras seções apenas quando houver owner, consumer, contrato e demanda concreta (Abstraction Gate). Nome público do invólucro: **Configurações do campo de pergunta**, não “Configurações do ditado”; “Ditado” é a primeira seção/subcomponente.

## 2. Estrutura e ownership

- **Composer atual:** `MessageComposer` em `plugin-ui`, composição em `DeliaComposer` de `plugins/delia`. Reutilizar controles, menu/popover, radio/segmented choice, tooltip, ícones e tokens existentes após inventário.
- **Subcomponente funcional alvo:** `DictationModeSettings` (nome candidato, sujeito à convenção existente) — apresenta escolhas `batch | live` e estados de disponibilidade, sem chamar STT; controlado pelo host via `value/onChange/disabled/liveAvailable` ou props equivalentes.
- **Contêiner do menu:** `ComposerSettingsMenu` (nome candidato), somente se nenhum componente de menu/popover existente já oferecer composição suficiente. Preferir composição de primitives com um wrapper fino em vez de nova abstração de settings.
- **Owner da decisão de modo:** `DeliaComposer` mantém `DEFAULT_DICTATION_MODE="batch"` e controla sessão/captureBusy. Nenhum subcomponente pode mudar modo ignorando a máquina de estados.
- **Futuras opções:** novas seções de conteúdo devem ser componentes pertencentes aos respectivos owners, encaixados no menu sem acoplar a lógica de STT ou fazer o composer depender de capacidades não implementadas. Não criar API de plugin/registry genérico sem consumidores efetivos.

## 3. Anatomia visual

**Idle padrão:** composer de superfície única, texto e ações na configuração de hoje. Retirar a faixa `SegmentToggle` persistente de cima. Barra inferior: microfone, controle discreto `Configurações do campo de pergunta` (ícone `settings-2` ou equivalente existente), ações já existentes e Enviar. Respeitar foco azul e tokens atuais.

**Menu aberto:** popover/popmenu ancorado na barra de ações, com cabeçalho **Configurações do campo de pergunta**, seção **Ditado** e duas escolhas exclusivas:

1. **Gravar e transcrever** — “Grave primeiro; o texto aparece quando finalizar.” **Padrão**.
2. **Transcrição em tempo real** — “O texto aparece durante a fala; pode exigir revisões.” **Opcional**.

Estado selecionado evidenciado por marca/radio e texto, não só cor. Se live indisponível, item desabilitado com descrição honesta; batch permanece selecionado. Quando só batch estiver disponível, o menu pode conservar a seção explicativa, sem oferecer ação não funcional; não esconder o único controle de configurações quando houver outras seções futuras.

**Indicador compacto:** modo do microfone disponível via tooltip e/ou label acessível (“Microfone — Gravar e transcrever” / “Microfone — Transcrição em tempo real”), sem faixa textual permanente. Não transformar microfone em controle de troca involuntária.

**Posição:** menu acima da barra, alinhamento lateral adaptativo, com borda/radius/tokens do `plugin-ui`. Respeitar viewport, largura nativa do Dock e teclado mobile. Não cobrir texto digitado, Enviar ou controles essenciais. Não criar overlay persistente fora da superfície.

**Tamanhos:** largura intrínseca com máximo responsivo; texto de duas linhas quando necessário; área clicável e foco adequados; sem scroll horizontal global. Descrições curtas, sem ajustes de typography locais arbitrários.

## 4. Interações e transições

- Botão de settings abre/fecha por clique, Enter ou Space; Escape fecha e devolve foco ao trigger; clique externo fecha conforme primitive; Tab/Shift+Tab navegam itens em ordem previsível.
- Seleção só pode ser alterada **idle/review**. Durante gravação, pause, transcribing, finalizing ou captura pendente, os itens de mudança ficam disabled com explicação; não remonta editor nem perde draft.
- Escolha em idle atualiza `DictationMode` local mount-scoped; microfone seguinte usa batch ou live; não abre sessão nem inicia gravação no ato da escolha.
- Ao selecionar live, só habilitar quando admission incremental vigente permitir; `incremental.available=true` **não auto-seleciona**. Se capability cair, bloquear início live e comunicar; não mudar modo durante sessão.
- Após escolher, fechar menu e devolver foco ao editor ou trigger conforme padrão acessível do componente; preservar caret e seleção exatamente para próximo ditado.
- Em nova montagem, default batch. Sem LocalStorage, cookies, Personal Memory, configuração organizacional ou backend apenas para preferência.
- Nenhuma alteração de `dictation.transcription.v1`, `dictation.incremental.v1`, reconciler, gravação ou envio. **No auto-submit**.
- Se menu aberto enquanto gravação começar por outro caminho, sincronizar `disabled` imediatamente; nunca trocar protocolo no meio de uma sessão.
- Quando futuras opções forem adicionadas, mudança de uma seção não pode atualizar estado de outra silenciosamente.

## 5. Estados e microcopy

| Estado | Exibição |
|---|---|
| Idle + batch | settings acessível; batch marcado; tooltip mic indica batch |
| Idle + live admitido | live pode ser escolhido; marcar seleção e nota de revisão |
| Live indisponível | escolha live disabled com razão textual; sem promessa de uso |
| Recording/paused | configuração visível mas seleção bloqueada; status de mic na UI original |
| Transcribing/finalizing | seleção bloqueada até liberação efetiva |
| Erro de STT | draft preservado; menu não vira superfície de erro |
| Dock/mobile | popover contido na área visível; botão permanece acessível |

## 6. Acessibilidade e segurança

Trigger com `type=button`, `aria-label="Configurações do campo de pergunta"`, `aria-expanded`/popup conforme primitive. Grupo `Ditado` acessível, opções mutuamente exclusivas com checked/selected comunicado; focus ring visível, contraste WCAG AA, zoom 200%, prefers-reduced-motion. Não duplicar anúncios nem roubar foco em resposta STT. Testar leitor de tela real quando ambiente disponível; ausência = `TEST_NOT_RUN`.

Menu é apenas configuração de apresentação/input; não permite a criação de permissão nem AuthZ. STT remoto continua governado pela admissão do backend, permissão do navegador e informação contextual de finalidade.

## 7. QA e critérios CS-01 a CS-18

| ID | Critério |
|---|---|
| CS-01 | Faixa permanente de modos removida; composer permanece única superfície |
| CS-02 | Controle settings dentro da barra de ações, discreto e identificável |
| CS-03 | Menu “Configurações do campo de pergunta” e seção “Ditado” |
| CS-04 | Batch selecionado por default em nova montagem |
| CS-05 | Live selecionável apenas por gesto explícito e admission vigente |
| CS-06 | Item live indisponível tratado honestamente |
| CS-07 | Escolha não inicia gravação/transcrição |
| CS-08 | Troca bloqueada durante captura, pausa e processamento |
| CS-09 | Draft e caret/seleção preservados na abertura, escolha e fechamento |
| CS-10 | Teclado, Escape, foco, nomes acessíveis e ARIA |
| CS-11 | Full-page e Dock real equivalentes |
| CS-12 | Mobile 320/360/375/420, zoom 200%, dark/light/reduced-motion |
| CS-13 | Tooltip/estado do mic acompanha modo sem faixa permanente |
| CS-14 | Fluxo batch v1 intacto; áudio real e texto pós-finalização |
| CS-15 | Live opt-in v1 intacto, sem auto seleção |
| CS-16 | No auto-submit; erros e cancel preservam draft |
| CS-17 | Não cria settings engine/registry/store ou backend |
| CS-18 | Futura seção isolada pode ser adicionada por composição, sem reescrever ditado |

**Testes:** unit/interaction `DeliaComposer`, primitive compartilhada, Compose/Queue/DraftRecovery/Voice/STT, Playwright full-page/Dock nativo, regressões, a11y, production smoke se houver código implantado. States `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN`. Histórico não basta; evidência por SHA.

## 8. Gate de implementação

`EXISTING_EQUIVALENT=TO_INVENTORY` para menu/popover reutilizável e `REUSE_DECISION=TO_DECIDE` até examinar HEAD; a preferência é `REUSE/EXTEND`. Prioridade: menor diff no `DeliaComposer`, primitive compartilhada somente se houver necessidade legítima e reutilização. Reancorar authorities 16→50→17→49→51→52→21→20→25, contratos e ledger; testes RED/GREEN, QA, docs/evidence, commit/push main, deploy frontend scoped e validação.

**Status do documento:** implementado, deployado e homologado em produção (36/27 checks — ver evidência VD-F06, seção Composer Settings). Futuras configurações são `PLANNED_AS_EXTENSION_POINT`, não funcionalidades anunciadas. Futuras configurações são `PLANNED_AS_EXTENSION_POINT`, não funcionalidades anunciadas.


## 9. Decisão visual posterior — Clean Select Menu (2026-10-23)

**Status:** IMPLEMENTED_AND_HOMOLOGATED (2026-10-23, commit `678f373ae0`, deploy prod + QA visual 21/21 + transcrição real); substitui apenas o tratamento visual da seção Ditado na especificação anterior. **Não** reabre seleção batch default, opt-in live, portais, contratos STT ou runtime. **Referência aprovada pelo Product Owner:** imagem de interface clara com menus compactos, linhas leves, tipografia hierárquica, seleção de linha inteira e check discreto à direita. A referência é de linguagem visual, **não** de tema claro obrigatório e **não** autoriza implementar as opções ilustrativas “Tone of voice”/“Answer length”. A DÉLIA permanece compatível com dark/light e tokens compartilhados.

### 9.1 Princípios visuais

- **Clean/minimal:** abandonar aparência de formulário/radios expostos ou cards dentro de cards. O menu é um único painel flutuante, radius e sombra leves do design system; itens são **linhas/list-items selecionáveis** de altura confortável, com bordas sutis ou fundo hover. Sem outline azul permanente em cards, sem gradientes decorativos, blur extravagante, glassmorphism obrigatória ou excesso de ícones.
- **Cabeçalho compacto:** título **“Configurações”**; descrição opcional breve **“Campo de pergunta”**, sem repetir longamente o título. A seção **“Ditado”** pode ter pequeno ícone de microfone. Hierarquia clara entre título do menu, nome de seção, label da opção e auxílio.
- **Opções:** duas linhas com label semibold e descrição pequena: **“Gravar e transcrever”** — “Grave primeiro; o texto aparece ao finalizar.”; **“Transcrição em tempo real”** — “Veja o texto aparecer durante a fala.”. Seleção demonstrada por **check à direita**, mais destaque leve de fundo da linha; hover distinto, desabilitado distinguível por texto+semântica. Toda a linha é clicável, sem rádio circular visual obrigatório. Preservar **inputs radio nativos ou semântica equivalente real** para a11y e teclado, não construir pressables sem suporte a teclado.
- **Espaçamento:** utilizar tokens de `plugin-ui`, padding uniforme, gaps consistentes e área de toque confortável. Largura intrínseca aproximada 300–340px apenas como referência, **clamped** ao viewport/Dock. Não fixar dimensões que causem clipping. Evitar truncar descrições.
- **Estados:** hover/focus-visible/selected/disabled, menu aberto/fechado, toggle em gravação bloqueado, prefers-reduced-motion, dark/light, contraste AA, zoom 200% e teclado. Animações opcionais curtas apenas se já houver token/padrão.
- **Toolbar:** preservar `[microfone] [configurações] ... [Enviar]` compacta. Ícone do trigger com estado aberto discreto, sem novo badge/label fixo e sem mexer no foco azul do composer.
- **Extensível:** futuras seções podem ser adicionadas por `children`, sem mostrar placeholders nem adicionar settings engine. **Não** criar componente universal novo se uma estilização de `DictationModeSettings` e `ComposerSettingsMenu` resolver.

### 9.2 Componentes e limites

**PROVEN a partir do rework anterior (revalidar HEAD):** `ComposerSettingsMenu` e `DictationModeSettings` em `plugins/delia`, `AnchoredPanelPortal`, `IconButton`, `HelpTooltip` de `plugin-ui`; `DeliaComposer` coordena modo `batch|live` e `captureBusy`. **EXISTING_EQUIVALENT=YES; REUSE_DECISION=EXTEND** sujeito a reancoragem. Alteração alvo é somente apresentação/estilos/semântica acessível dos elementos atuais. Sem provider, backend, contrato, novo store ou nova capability.

### 9.3 Critérios de aceite visual CL-01 a CL-14

| ID | Critério |
|---|---|
| CL-01 | Um único painel flutuante clean, sem segundo card por opção |
| CL-02 | Cabeçalho compacto “Configurações” e seção “Ditado” |
| CL-03 | Duas linhas de seleção com título e descrição, sem aparência de formulário |
| CL-04 | Estado selecionado por check discreto à direita + fundo sutil |
| CL-05 | Toda a linha selecionável e radio/semântica acessível mantida |
| CL-06 | Hover/focus-visible/disabled distintos, contraste AA |
| CL-07 | Dark/light por tokens reais, sem hardcode de palette |
| CL-08 | Viewport/Dock sem clipping, mobile 320/360/375/390/420 e zoom 200% |
| CL-09 | Escape/click-outside/foco restaurados; menu abre/fecha sem mudar draft |
| CL-10 | Batch default, live opt-in, indisponibilidade e bloqueio durante gravação intactos |
| CL-11 | Nenhum auto-submit, caret/seleção preservados |
| CL-12 | Full-page + Companion Dock nativo + áudio pt-BR batch/live sem regressão |
| CL-13 | Sem nova primitiva ou settings engine se reuse existente suficiente |
| CL-14 | Sem implementar opções fictícias da imagem de referência; extensibilidade via composição intacta |

**Implementação:** task bounded `DELIA-UX-COMPOSER-SETTINGS-CLEAN-VISUAL-REFINEMENT-01`: reanchor HEAD/authorities/ledger → reuse/abstraction gate → alterar menor diff dos dois componentes e CSS → RED/GREEN + regressões → browser screenshot/QA light+dark/full-page/Dock/mobile/zoom → rework → docs/evidence/ledger → commit/push main → deploy frontend scoped → smoke/relatório. **VISUAL_RUNTIME_STATUS=IMPLEMENTED** — ver evidência VD-F06, seção Clean Select Menu. Não considerar a task concluída por mockup ou apenas CSS sem QA.


## 10. Ajuste de interação aprovado pelo Product Owner — manter menu aberto após seleção (2026-10-23)

**Status:** PRODUCT_UX_DECISION / IMPLEMENTATION_PENDING. Substitui a regra anterior de fechar o popover depois de escolher modo, sem alterar a estética clean (§9), default batch, live opt-in, contratos ou admission.

- Escolher **Gravar e transcrever** ou **Transcrição em tempo real** atualiza a opção imediatamente **e mantém o menu aberto**, inclusive após múltiplas alterações. Não há botão Salvar/Aplicar.
- O menu fecha por **clique fora**, **novo clique no botão de configurações** ou **Escape**. Também pode fechar quando o usuário inicia outra interação no composer, desde que isso decorra do dismiss externo governado pelo `AnchoredPanelPortal` e não dispare perda de foco/draft ou cancelamento de captura.
- Escape restaura foco no trigger. Clique externo não deve **roubar foco** da ação/elemento escolhido; preservar caret e seleção para edição e ditado.
- Enquanto grava/processa, itens de mudança seguem desabilitados; o menu pode ser consultado. Nenhuma seleção dispara gravação ou auto-submit.
- Não usar o fechamento como efeito genérico de `onChange` nem `data-close-on-change` na seção Ditado. A possibilidade de outras seções futuras não justifica construir mecanismo genérico agora; ações explícitas com semântica diferente poderão usar contrato de fechamento quando especificadas.
- No HEAD examinado, `ComposerSettingsMenu` possui listener `onChange` que chama `dismiss()` quando o alvo é descendente de `[data-close-on-change]`. O executor deve verificar o uso real dessa marcação e aplicar o menor diff para que a troca de rádio não feche o painel, preservando comportamento de Escape/outside/trigger e compatibilidade de outras seções existentes.

**Critérios de aceite adicionais:** `CM-01` selecionar batch→live mantém painel aberto; `CM-02` live→batch idem; `CM-03` clique fora fecha sem roubar foco da interação externa; `CM-04` trigger fecha ao segundo clique; `CM-05` Escape fecha e restaura foco; `CM-06` múltiplas seleções sem remount/perda de draft/caret; `CM-07` opção bloqueada durante captura; `CM-08` full-page/Dock/mobile e regressões de dictation/queue sem auto-submit. Evidenciar SHA, testes e QA; docs-only não altera runtime.
