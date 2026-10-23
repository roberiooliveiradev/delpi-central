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
