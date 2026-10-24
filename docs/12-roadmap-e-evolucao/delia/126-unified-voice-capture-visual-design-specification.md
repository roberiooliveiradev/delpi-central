# DÉLIA — Unified Voice Capture Visual System (Batch + Live)

**Data:** 2026-10-23. **Status:** IMPLEMENTED (2026-10-23, SHA `252fa11239`). **Repositório:** roberiooliveiradev/delpi-central. **HEAD de referência:** 84306b0eb3d0b2cdd4ac50c6688fa67f02ff7fee. Reancorar antes de executar.

## 1. Objetivo e premissas

Unificar a identidade visual de **Gravar e transcrever (batch VD-F03, padrão)** e **Transcrição em tempo real (live VD-F06, opt-in)**. Ambos devem parecer membros da mesma família de controls de voz DÉLIA: azul institucional por tokens, botões circulares, movimento suave, hierarquia de ação consistente e estados inequívocos. Diferenciar os dois modos por rótulo, disposição funcional e nuance de feedback; **não** forçar os dois a um único painel operacional. Preservar a decisão da spec 123 §12, menu de configurações spec 125, batch default, live opt-in e todos os contratos.

Evidência motivadora: screenshots reais do PO (2026-10-23) mostraram batch como painel de gravação com indicador horizontal e live com botões quadrados e status fora da superfície, gerando linguagem visual inconsistente. São evidência de percepção/UX, não prova de bug backend.

## 2. Ownership / Reuse-before-design

**Owner do design compartilhável:** `plugins/plugin-ui`; **owner da composição batch/live e estados de produto:** `plugins/delia`; **owners STT, admission e AuthZ:** inalterados. Revalidar no HEAD o catálogo/export dos componentes existentes, especialmente `AudioRecorderControl`, `MessageComposer`, `IconButton`, `HelpTooltip`, estilos de controle/audio em plugin-ui, `DeliaComposer`, `useLocalAudioRecorder`, `useIncrementalDictation`. Priorizar **reutilizar/estender componentes e tokens existentes**; nova primitiva compartilhada somente se existir boundary/consumer efetivo que a justifique. Não criar paralelos para batch e live. Gate da implementação: `EXISTING_EQUIVALENT=TO_INVENTORY`, `REUSE_DECISION=TO_DECIDE` até inventário no HEAD. Não modificar backend, adapters, providers, protocolos, contratos ou captação real para fins estéticos.

## 3. Anatomia unificada

### Controles
- Botão inicial de microfone: **circular** nos dois modos, mesma dimensão/tamanho óptico de ícone e foco; idle neutro, ativo azul, hover sutil. Não manter quadrado no live.
- Pause, Retomar, Finalizar, Descartar: **botões circulares** da mesma família visual, target acessível (aprox. 40–44px segundo design system); ícones centralizados, tooltips e ARIA, sem ações perigosas ambíguas. Finalizar pode ser o comando azul de maior ênfase; Descartar é neutro e ganha aviso cromático apenas no hover/focus apropriado. Revalidar ações realmente disponíveis em cada modo, **não inventar pause onde não existe**.
- Cor: **tokens institucionais azul**; batch com aspecto azul mais estável/profundo, live ligeiramente mais luminoso, **definidos por tokens derivados legítimos**, não dois conjuntos hardcoded. Diferenciar semanticamente sem depender só da cor.
- Estado ativo: halo/glow azul de intensidade baixa, borda sutil. Não deixar outline de foco permanentemente ligado só por gravar; `:focus-visible` continua claro.

### Status e feedback
- Uma linha compartilhada: ponto de atividade + label **“Gravando”** (batch) ou **“Ouvindo…”** (live) + timer; labels reais para **Pausado**, **Processando**, **Concluído**, **Erro**. Evitar duplicar timers ou status em lugares diferentes.
- Batch: indicador de nível/waveform existente com barrinhas azuis discretas; deve derivar de captura/sinal real ou sinalização explicitamente decorativa (nunca simular amplitude “real” inexistente). Textarea cede espaço ao painel de captura existente no **mesmo** `MessageComposer` conforme implementação.
- Live: editor permanece protagonista e editável, status slim integrado visualmente à mesma família, halo delicado no composer, sem texto que pisque, salte, substitua edições humanas ou simule streaming. Respeitar layout funcional atual se a reestruturação de DOM arriscar seleção/caret.
- Informativo de finalidade (“Sua fala será enviada apenas para transcrição em texto. Revise o resultado antes de enviar.”) permanece honesto e legível, sem repetições desnecessárias.

## 4. Estados visuais

| Estado | Batch | Live | Visual comum |
|---|---|---|---|
| Idle | Mic disponível | Mic disponível após opt-in/admission | Circular neutro, tooltip e focus |
| Recording | “Gravando”, timer total/limite, waveform | “Ouvindo”, timer, texto progressivo legítimo | Azul institucional, halo sutil, ações circulares |
| Paused | Se suportado, “Pausado” | Se suportado, “Pausado” | Pulso interrompido e controle Retomar legível |
| Finalizing/processing | Status processamento do áudio | Finalização de segmentos | Feedback sem salto ou falso sucesso |
| Completed/review | Texto editável após finalizar | Texto editável após finalizar | Retorno suave, sem auto-submit |
| Error | Feedback tipado | Falha recuperável segment-scoped conforme contrato | Não apagar draft, não usar glow alarmante |

**Não** alterar semântica ou política de estado apenas para conseguir simetria estética.

## 5. Motion UX

- Hover/press: 140–180ms; entrada/saída de estado: 180–220ms; easing suave alinhado a spec 125 §11.
- Pulso de escuta/gravação lento e discreto, um pouco mais vivo no live. O pulso indica estado ativo, não precisão, amplitude ou resultado de STT; nunca piscar alarmantemente.
- Waveform/indicador de atividade suave e sem layout thrashing; dados reais quando possível.
- Mudar estado por cor/opacidade/transform, não animar height/width/editor/caret; evitar inserção animada de texto quando isso ameaçar edição humana.
- `prefers-reduced-motion: reduce`: sem pulso contínuo e sem movimentos decorativos; estado permanece evidente por texto/ícone/cor.
- Dark/light: valores por tokens e contraste AA; mobile/Dock/zoom 200%.

## 6. Contrato visual funcional

Os dois modos compartilham **a mesma linguagem**, não necessariamente o mesmo DOM de painel: batch privilegia captura e finalização; live privilegia edição simultânea. Usar o menor caminho para reaproveitar os controls de plugin-ui, adequar ícones/raio/estados e estilos com composição em `DeliaComposer`. Não introduzir novo state machine, provider, recorder, STT engine, componente gigante “VoiceControls” ou dependência cíclica. `read != write`; áudio só para transcrição; envio manual; default batch; live opt-in; regras de bloqueio de troca, cancelamento e limites permanecem.

## 7. Critérios de aceite VOX-01..VOX-20

| ID | Critério |
|---|---|
| VOX-01 | Mic dos dois modos é perfeitamente circular e possui dimensão consistente |
| VOX-02 | Botões operacionais existentes seguem mesma família circular e targets adequados |
| VOX-03 | Azul institucional por tokens nos estados ativos, não cores hardcoded |
| VOX-04 | Diferenciação batch/live é sutil e identificável por texto/comportamento |
| VOX-05 | Batch mantém painel de captura dentro do composer e waveform/timer real |
| VOX-06 | Live mantém textarea editável e status integrado à identidade visual |
| VOX-07 | Pausar/retomar/finalizar/descartar funcionam sem regressões |
| VOX-08 | Estados idle/recording/paused/processing/review/error claros e honestos |
| VOX-09 | Hover, focus-visible e pressed consistentes |
| VOX-10 | Halo/pulso elegante, sem efeito alarmante |
| VOX-11 | Reduced-motion remove animação não essencial |
| VOX-12 | Sem simulação de amplitude, transcrição ou reconhecimento |
| VOX-13 | Draft, caret, selection e prioridade de edições humanas preservados |
| VOX-14 | Batch continua default, live somente opt-in |
| VOX-15 | Sem auto-submit; finalidade e erros mantêm linguagem correta |
| VOX-16 | Full-page e Companion Dock real QA com controles completos |
| VOX-17 | Mobile 320/360/375/390/420, zoom 200%, dark/light |
| VOX-18 | Teclado, tooltip, leitor de tela (quando disponível), contraste e targets |
| VOX-19 | Reuso de owners/primitivas legítimos; nenhum backend/contrato novo |
| VOX-20 | QA com áudio pt-BR real, regressões e evidências visuais por SHA |

## 8. Implementação futura

**Task:** `DELIA-UX-UNIFIED-VOICE-CONTROLS-VISUAL-REFINEMENT-01`. Reanchor git/authorities/ledger → inventory e reuse gate → contrato visual → RED testes → menor diff plugin-ui + composição DÉLIA → regressão → QA real video/frames dos dois modos, full-page, Dock, mobile, temas, zoom, reduced-motion → rework → docs/evidence/ledger → commit/push main → deploy apenas frontend afetado → smoke → report.

**Status documental:** `SPEC_PUBLISHED`, `RUNTIME_CHANGED`, `PHASE_NOT_ADVANCED`.

**Implementação (factual):** live entrou na família circular do batch — mic e controles de sessão (Pausar/Retomar/Finalizar/Descartar) a 40px `border-radius:50%`; Finalizar `tone="primary"` e Descartar `tone="danger"` (affordance neutra+hover do `IconButton` existente). Batch: alvos 36→40px, live-dot de perigo→acento institucional, entrada 160→200ms. Halos `--capturing`/`--listening` no `MessageComposer` por tokens (`color-mix` do acento); live levemente mais luminoso; pulso no dot live parado quando pausado; tudo sob `prefers-reduced-motion`. Zero mudança de STT, contratos, state machines ou backend. Evidência: `evidence/progressive-dictation-vdf06/` (seção spec 126) — 426/426 DÉLIA, 2324/2324 plugin-ui, probe prod `vd-vox-prod.mjs` **31/31** com geometria e cores medidas.
