# 120 — DÉLIA | Voice Dictation Composer — refinamento visual, motion e microinterações (VD-F04)

**Data da decisão:** 2026-10-19  
**Tipo:** `PRODUCT_UX_DECISION / IMPLEMENTATION_REFERENCE` — especificação visual, **não** evidência de implementação.  
**Status:** `PRODUCT_DIRECTION_APPROVED / VISUAL_REWORK_PLANNED / NO_CODE_CHANGE`  
**Owner:** UX/Frontend DÉLIA + `plugin-ui` (componentes visuais compartilhados).  
**Fonte funcional:** [119 — Voice Dictation Composer](./119-conversation-audio-recorder-composer-product-ux-specification.md) §0; contrato [dictation.transcription.v1](./contracts/dictation-transcription-contract-v1.md).  
**Fundação existente:** `MessageComposer.bodyOverride`, `AudioRecorderControl`, `useLocalAudioRecorder`, `DeliaComposer`, `dictationClient`; alterações visuais devem preservar STT e segurança.  
**Evidência de produto:** capturas de produção fornecidas pelo Product Master em 2026-10-19: escrita; gravação 00:00; gravação 00:07 com waveform; transcrição; texto editável “Testando o som, testando.” Não importar screenshots do chat como arquivos GitHub sem fonte autorizada.  
**Reancoragem:** Git status/HEAD → instruções de projeto/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → 119 → ledger. Em conflito, STOP/EXECUTION_DRIFT ou ARCHITECTURE_DECISION_REQUIRED.

## 1. Decisão do Product Master — escopo congelado

Refinar o componente **de ditado** existente para uma interface limpa, moderna, de cantos e controles arredondados, consistente com os componentes já existentes da DÉLIA e do design system compartilhado `plugin-ui`. A gravação já substitui a escrita funcionalmente; agora os estados devem parecer a **mesma superfície** com mudanças coerentes de conteúdo, geometria e feedback. Reutilizar componentes e tokens atuais em vez de inventar um novo design system.

**Função inalterada:** `escrita → iniciar ditado → captura consentida → finalizar → STT real → texto editável → envio manual`. O áudio da captura é usado apenas para STT; **não** é uma mensagem de áudio enviada à DÉLIA para análise multimodal. Envio de áudio para análise e Live Voice são capacidades futuras separadas. Sem auto-submit, sem nova permissão de áudio, sem alteração de autoridade, provider ou contrato STT por estética.

**Não incluir:** novo composer, outro gravador, novo runtime, troca de provider, backend, alterações no contrato de transcrição, reformulação de layout da DÉLIA, redesenho de Dock/Portal, novas cores/tokens globais sem gate, efeitos de áudio falsos, porcentagem fictícia de transcrição, confusão entre ditado e mensagem multimodal.

## 2. Diagnóstico visual fundamentado nas capturas de produção

| Estado visto | Evidência positiva | Gap de UX que VD-F04 resolve |
|---|---|---|
| Escrita | botão mic no toolbar, campo de texto e Enviar | mic tem forma/peso isolado; harmonizar com ações compartilhadas e estados hover/focus |
| Gravando (00:00) | `Gravando`, contador, waveform, X e finalizar | controles parecem quadrados/heterogêneos; waveform pequena, amplo vazio; distribuir pesos |
| Gravando (00:07) | amplitude reage à voz, texto substituído por captura | espaço/ritmo visual do sinal e alinhamento do cronômetro precisam consistência |
| Transcrevendo | texto honesto e X | caixa aninhada dentro do composer; hierarquia/posicionamento fracos; falta indicador de atividade real |
| Texto transcrito | texto reconhecido editável, caret, envio manual | retorno sem feedback contextual; o X pode ser confundido com cancelar captura, embora seja limpar draft |
| Cabeçalho | aviso de destino/finalidade do áudio | faixa amarela global persistente e chamativa em contexto de não gravação |

**Não afirmar** que captura prova velocidade, suporte cross-browser, acessibilidade ou qualidade semântica do STT; são critérios a testar.

## 3. Composição visual comum (invariantes)

1. **Uma só surface**: `MessageComposer` permanece como moldura única. `bodyOverride` apresenta gravação/processamento dentro da surface. Nenhum segundo cartão, borda dupla ou painel flutuante acima. `AudioRecorderControl` é reutilizado, não refeito em outro componente.
2. **Geometria**: mesmo raio, fundo, borda, densidade visual, tipografia e tokens do composer normal; containers internos sem borda/sombra duplicada. Não fixar novos hexadecimais, pixels, fontes ou breakpoints se tokens canônicos equivalentes existirem. Espacamento estável horizontal e vertical; sem saltos perceptíveis nas transições.
3. **Ações**: botões de ícone **circulares** (mesmo diâmetro e área hit target acessível), com padrão `IconButton` compartilhado, estados default/hover/active/focus-visible/disabled e tooltip/aria-label; ação primária com maior destaque, cancelamento secundário (tom destrutivo somente quando semântico). Não usar ícones soltos como controles.
4. **Cores**: azul institucional/tokens de ação para completar; vermelho discreto só para gravação ativa e semântica destrutiva; fundo/contraste consistentes com light/dark. Cor nunca é o único identificador do estado.
5. **Motion**: transição curta sugerida ~150–250 ms, condicionada aos tokens atuais e `prefers-reduced-motion`; não introduzir pulso excessivo, animação decorativa permanente, mudanças de largura do botão ou movimento da toolbar. Reduced motion mantém estado compreensível.
6. **Texto**: microcopy concisa em pt-BR, sem rótulo de `mensagem de áudio`. Sem percentuais, estimativas de segundos ou status de sucesso que o backend não confirme.
7. **Mesma identidade no Dock e full page**: preservar single-surface, hierarquia, sem overflow/scroll horizontal, inclusive em largura compacta; não reinventar Dock global.

## 4. Estados e composição detalhada

### 4.1 `writing / idle`
- Área de texto e toolbar como hoje; mic à esquerda como ação circular icon-only alinhada aos demais controles, com `aria-label="Ditar mensagem"` ou nomenclatura equivalente aprovada. Tooltip curto “Ditar mensagem”.
- Enviar mantém comportamento original (texto apenas); limpar draft, se presente, conserva owner `ComposerClearDraftButton` e significado textual; não o estilizar como cancelar captura.
- Hover/focus claros no mic; feedback tátil visual sutil do clique, sem pulso de gravação antes de permissão. Mic indisponível: disabled com motivo acessível; não simular disponibilidade.
- O helper genérico do composer permanece discreto; aviso específico de STT não fica fixo no cabeçalho global.

### 4.2 `requesting_permission`
- Substituir textarea/toolbar pela área de ditado dentro da mesma surface, sem piscada nem altura abrupta.
- Ícone discreto + “Aguardando acesso ao microfone…”; botão circular Cancelar; sem waveform ativa, contador de gravação ou dot vermelho enquanto não existir captura.
- Se negado/indisponível: feedback de erro contextual, retornar escrita preservando draft e foco; não dizer que está gravando.

### 4.3 `recording`
- Linha visual: [mic/pequeno indicador vivo] [“Gravando” e contador estável] [waveform real flexível] [Cancelar] [Finalizar primário].
- Botões X e Finalizar com borda e raio **circulares**; tamanho e hit area idênticos, hierarquia distinta. Ação de finalizar usa ícone consistente com o design system (square/check conforme semântica legível), nome acessível “Finalizar ditado”.
- Waveform usa amplitude real de `useLocalAudioRecorder`, barras finas/arredondadas, espaçamento regular, suavização visual sem falsificar amostras, tamanho proporcional ao espaço; amplitude mínima em silêncio, nunca loop decorativo que sugira fala.
- Contador real `mm:ss` com dígitos tabulares/fixed width e sem layout shift. Não anunciar a cada segundo por screen reader.
- Estado de gravação distinguível também por rótulo e indicador, não apenas vermelho.
- O campo de texto **não renderiza** e nenhum Enter/envio textual é possível; foco permanece em controles ativos.

### 4.4 `stopping / finalizing`
- Ao finalizar, responder ao gesto imediatamente; desabilitar double-click/reentrada, manter estrutura estável. Liberar tracks conforme ciclo real.
- Passar ao processamento quando STT contratado estiver realmente ativo; se STT indisponível, manter fluxo de prévia local honesto conforme contrato existente, **não** prometer transcrição.
- Sem barra de progresso percentual inventada.

### 4.5 `transcribing`
- Dentro da mesma surface, **sem segundo card/borda interna**; [indicador sutil de processamento não-percentual] [“Transcrevendo sua fala…”] [Cancelar circular].
- Indicador elegante compatível com reduced motion, sem shimmer agressivo; o estado visual expressa operação real em andamento, não velocidade falsa.
- Em latência prolongada, mensagem discreta contextual se houver base real; não prometer tempo restante.
- Cancelamento é **local abort** quando provider não oferece cancelamento autoritativo: ignorar resposta tardia e preservar draft, sem alegar que processamento remoto foi revogado.
- Sem textarea e sem Enviar durante processamento.

### 4.6 `review / writing após STT`
- Composer textual volta na mesma posição, com texto transcrito editável e caret/foco na posição definida pelo merge do VD-F03.
- Feedback transitório *discreto* e acessível “Texto transcrito, revise antes de enviar”, sem toast global nem sucesso exuberante; anunciar conclusão uma única vez por região `aria-live` apropriada, evitando duplicidade.
- Enviar permanece exclusivamente manual; mic disponível para novo ditado quando idle. Botão X no toolbar é **limpar rascunho**, não cancelar gravação: reutilizar componente compartilhado, tooltip/aria-label “Limpar texto” e styling coerente; não alterar semântica de limpeza.
- Respeitar texto anterior, seleção/cursor e invalidação de sessão tardia já implementados.

### 4.7 `error / cancelled / unavailable`
- Erros recuperáveis aparecem em contexto na área própria do composer: mensagem clara + opção de tentar novamente quando legítima; erro não apaga draft e não ocupa página inteira.
- Cancelar durante gravação/solicitação/processamento libera recursos locais e retorna escrita; sem confirmação destrutiva desnecessária para a captura não enviada. Quando houver transcrição já aplicada ao draft, limpar texto continua ato distinto.
- Diferenciar permissão negada, dispositivo ausente, duração/tamanho limite, STT indisponível, timeout, rate limit e falha de rede por mensagem compatível com contrato; não vazar detalhes internos ou provider.

## 5. Matriz de transições, foco e anúncios

| Origem → destino | Gatilho real | Feedback/foco | Dados |
|---|---|---|---|
| writing → requesting | clique Ditar | surface muda, foco em cancelar | draft preservado |
| requesting → recording | permissão efetiva | mic ativo, waveform real; foco em Finalizar/controle alcançável | áudio capturado |
| requesting → error/writing | bloqueio/cancel | mensagem contextual e retorno foco textarea | draft intacto |
| recording → stopping | Finalizar | botão imediatamente protegido de double-submit | fecha stream |
| recording → writing | Cancelar | volta ao textarea com foco | descarta captura |
| stopping → transcribing | request STT real admitido | indicador sem progresso falso, cancelar | resposta correlacionada |
| stopping → preview | sem STT configurado | player local honesto; não chamar isso de ditado concluído | áudio local |
| transcribing → review | texto não vazio validado | retorna textarea, texto/edit + anúncio único | merge existente, sem envio |
| transcribing → writing/error | cancelar, timeout, provider failure | retorno seguro e aviso | descartar resposta tardia, draft preservado |
| review → writing | edição/novo ditado/limpar | segue fluxo textual normal | não auto-submit |

**Foco:** sem `autoFocus` indiscriminado em cada render; testar mudanças condicionadas a transições, teclado e componente desmontado. Foco visível e ordem lógica; evitar `document.getElementById` indiscriminado que alcance outro composer se houver IDs não exclusivos — analisar necessidade real antes de mudar.

## 6. Privacy notice — mudança de posicionamento, não remoção de consentimento

Remover como **alvo visual** a faixa amarela permanente do topo da página, **depois** de confirmar onde ela nasce e quais outros avisos compartilham o mesmo componente. Não ocultar ou apagar informação de finalidade. Exibir informação contextual e legível ao iniciar ditado/na primeira utilização e oferecer acesso posterior por tooltip/ajuda informativa do mic, sem presumir persistência da escolha ou consentimento global.

Texto-base permitido: “Sua fala será enviada apenas para transcrição em texto. Revise o resultado antes de enviar.” Ajustar copy à capacidade real (STT remoto ou indisponível) e à política de privacidade vigente. A permissão do browser é distinta da transparência sobre envio ao STT; ambas se preservam. Evitar banners permanentes ocupando o cabeçalho da DÉLIA.

## 7. Responsividade, temas e acessibilidade

- Conferir página completa e Companion Dock em larguras **320, 360 e 420 px**, além de zoom 200%; tratar wrapping/compactação da waveform e dos botões, sem truncar ações críticas ou forçar scroll horizontal.
- Mobile/touch: área de toque acessível conforme design system; controles principais distinguíveis mesmo com dedo/sem hover.
- Light/dark/high contrast: usar tokens atuais e testar contraste de status, foco e controles; nunca confiar só em cor ou pulso.
- `prefers-reduced-motion`: desabilitar animações ornamentais, preservar ícone/rótulo/estado. Waveform continua fiel ao sinal se mostrada, mas sem interpolação decorativa inadequada.
- Leitor de tela: rótulos pt-BR corretos (Ditar, Cancelar, Finalizar, Transcrevendo, Limpar texto), `aria-live` somente em mudanças semânticas, duração não anunciada continuamente, estados busy/disabled claros, foco restaurado.
- Browser support e secure context continuam fail-closed pelo primitive existente; não gerar CTA de gravação ativa se browser não suporta.

## 8. Reuse/Abstraction Gates (obrigatórios antes de editar)

| Responsabilidade | Equivalente | Decisão |
|---|---|---|
| composer/padrão de toolbar e limpeza | `MessageComposer`, `ComposerClearDraftButton` | `YES / REUSE` ou `EXTEND` bounded |
| gravação, timer, waveform, controles | `AudioRecorderControl`, `useLocalAudioRecorder` | `YES / EXTEND` **somente visual** |
| ações arredondadas | `IconButton`, tokens `plugin-ui` e CSS local | `YES / REUSE` |
| coordenação de estados + rascunho | `DeliaComposer` | `YES / REUSE` |
| STT/AuthZ/backend | `dictation.transcription.v1`, `delia-api` | `YES / PRESERVE, NO DIFF` |

Documentar estado real no HEAD. Sem import cross-bounded-context, sem novo componente compartilhado de aplicação específica por conveniência, sem alterar API de props em vários consumers sem caracterização de regressão.

## 9. Acceptance Gate visual VD-F04 (novos identificadores locais, não CP/RQ canônicos)

| ID | Aceite | Verificação |
|---|---|---|
| VD-V01 | Uma única surface no idle/recording/transcribing/review | screenshot full + Dock; nenhum card aninhado |
| VD-V02 | Mic, Cancelar, Finalizar e Limpar com botões circulares e semânticas distintas | screenshot e teste de controle |
| VD-V03 | Waveform proporcional, arredondada e alimentada por amplitude real | mic real + silêncio/voz; sem dados fabricados |
| VD-V04 | Cronômetro real `mm:ss`, largura estável, sem SR spam | teste fake clock + a11y |
| VD-V05 | Transição de superfície sem layout shift perceptível e reduced motion respeitado | Playwright + inspeção visual |
| VD-V06 | Processamento real em estado limpo sem borda dupla nem percentual falso | screenshot e falha/latência |
| VD-V07 | Retorno do texto editável e foco/caret corretos, feedback discreto | E2E STT, sem auto-submit |
| VD-V08 | Captura, permissão, erro, cancelar e timeout preservam draft | regressão |
| VD-V09 | Aviso STT contextual substitui faixa global após verificar owner/copy e preservar transparência | screenshot com/sem ditado |
| VD-V10 | 320/360/420px, zoom 200%, full-page e Dock sem overflow | browser QA |
| VD-V11 | Light/dark, touch, teclado, screen reader, contraste e focus-visible | QA acessibilidade |
| VD-V12 | Nenhum diff funcional em `delia-api`, provider, RBAC ou upload multimodal | diff review |
| VD-V13 | Playwright, Vitest, TypeScript/build/federation, revisão independente com SHA/config | evidence |
| VD-V14 | Teste produção com mic físico e transcrição real pt-BR, texto editável e envio manual | validação pós-deploy |

Status de VD-V01…V14: `PLANNED` até execução/evidência. Screenshots de produto fornecidos para discovery **não** constituem aceite visual da solução futura.

## 10. Sequência bounded de implementação — para Cursor, sem autorização automática de código

`VD-F04-A`: reanchor + inventário focado de `plugin-ui` (IconButton, MessageComposer, CSS/tokens), DÉLIA e screenshots de referência; contrato visual/owner; diffs mínimos.

`VD-F04-B`: implementar estados compartilhados e CSS local: geometric alignment, botões circulares, waveform e processing, foco; preservar interface single-surface. Sem alterar STT.

`VD-F04-C`: mover aviso persistente para contexto após verificar dono do banner, consentimento e cópia; não remover disclosure da transmissão ao STT.

`VD-F04-D`: Vitest, builds, Module Federation, Playwright full page/Dock, acessibilidade, QA real em produção, evidência e revisão. Não declarar PASS se só testado em synthetic mic.

Separação em subetapas serve para **entregar**, não para prolongar inventários. Implementar o menor diff correto; nenhuma nova abstração sem owner/consumer real.

## 11. Regras de evidência, entrega e anti-drift

Antes de alterar código: reanchor canônico e ledger; confirmar `EXISTING_EQUIVALENT=YES/NO/TO_INVENTORY` e `REUSE_DECISION=REUSE/EXTEND/NEW`; checar compatibilidade dos consumers de `plugin-ui`. Depois: testes e screenshot na versão de SHA/config, residual search, commit/push para `main` conforme protocolo do projeto e atualização factual do ledger.

**Estados aceitos:** `PROVEN | TO_INVENTORY | PLANNED | TARGET`; testes `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`; review `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`. Não tratar documentação como runtime, nem screenshot de conceito como aprovação do código. VD-F04 não progride fase e não autoriza novas capacidades de áudio.
