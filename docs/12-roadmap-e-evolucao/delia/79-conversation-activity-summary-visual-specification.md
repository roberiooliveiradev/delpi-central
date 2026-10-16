# 79 — DÉLIA: ActivityViewer / Conversation Activity Summary

**Status:** `IMPLEMENTED_EXISTING / DESIGN_ALIGNED / REUSE` — o componente compartilhado `ActivityViewer` já existe em `plugins/plugin-ui` e já é consumido pela DÉLIA. Esta especificação documenta significado, aparência e limites; não cria nova capability nem autoriza componente paralelo.
**Escopo:** resumo visual compacto e expansível da atividade observável da DÉLIA durante e após uma interação, em página completa e dock.
**Reanchor:** HEAD de elaboração `843ee2423a45275c507b7cdc10bb92f45f1827b4`; qualquer alteração futura deve revalidar HEAD/status e a cadeia canônica de authorities.
**Referências:** docs 69, 70, 73 e 75.

## 1. Decisão de reuso

Inventário factual:

- `plugins/plugin-ui/src/components/activity/ActivityViewer.tsx` — componente provider-neutral já implementado;
- `plugins/plugin-ui/src/styles/activity-viewer.css` — chrome/tokens já implementados;
- `plugins/delia/src/activity/activityView.ts` — projeção DÉLIA → props visuais;
- `plugins/delia/src/App.tsx` — uso para atividade live/pending;
- `plugins/delia/src/ui/DeliaAssistantMessage.tsx` — uso por turno concluído.

```text
ActivityViewer
EXISTING_EQUIVALENT = YES
REUSE_DECISION = REUSE

LoadingActivityCard / LoadingActivityBadge
EXISTING_EQUIVALENT = PARTIAL
REUSE_DECISION = DO_NOT_REPLACE ActivityViewer

NEW ConversationActivity
REUSE_DECISION = DO NOT CREATE
```

Não criar outro componente apenas para renomear a mesma responsabilidade.

## 2. O que representa

`ActivityViewer` representa somente atividade observável e user-facing da interação: solicitação recebida, contextualização observada, capability/fonte selecionada quando legitimamente conhecida, consulta iniciada/concluída, organização da resposta, espera por decisão governada e estados terminais observados.

Ele não representa raciocínio interno.

## 3. O que NÃO representa

- chain-of-thought;
- “pensando” como estado mental;
- confiança subjetiva do modelo;
- porcentagem de progresso inventada;
- timer artificial;
- autorização ou permissionamento;
- PREPARE/ACT;
- business outcome autoritativo;
- confirmation request;
- erro genérico de transporte do frontend;
- tool metadata como verdade.

```text
activity != chain-of-thought
activity != authorization
activity != confirmation
activity != business outcome
technical completion != business success
```

## 4. Aparência principal

Em andamento:

```text
DÉLIA

◌ Consultando informações…
  TÉO

[Ver detalhes ▾]
```

Concluído:

```text
DÉLIA

✓ Consultas concluídas
  DAVI · VISTA

[Ver detalhes ▾]

Resposta da DÉLIA…
```

Anatomia: ícone de estado + label principal + detalhe/fonte secundária + disclosure opcional.

## 5. Hierarquia visual

```text
1. resposta da DÉLIA
2. ActivityViewer
3. provenance/evidência técnica expandida
```

Durante pending, quando ainda não há resposta, o ActivityViewer pode ocupar a posição da próxima atividade. Após conclusão, permanece compacto e subordinado.

## 6. Superfície

- fundo transparente ou quase transparente;
- sem card pesado e sem sombra;
- ícone pequeno;
- tipografia pequena/muted;
- status legível por ícone + texto;
- disclosure discreto;
- detalhe expandido com spacing leve;
- tokens `--delpi-ui-*`/Portal;
- nenhuma paleta paralela.

Não mostrar painel técnico com “MCP CALL”, “TOOL EXECUTION” ou “MODEL REASONING” como etapas user-facing.

## 7. Estados visuais

O componente existente suporta:

```text
pending | running | completed | partial | blocked | denied | failed | cancelled | no_data
```

`completed` significa conclusão técnica da atividade observada, não sucesso de negócio.

## 8. Labels e fontes

Labels devem ser curtos e user-facing: “Consultando informações…”, “Reunindo informações…”, “Consulta finalizada”, “Organizando a resposta…”, “Atividade concluída”.

Fonte/owner só aparece quando legitimamente conhecido, como DAVI, TÉO, VISTA ou nome de fonte publicado.

Não expor por padrão tool name técnico, endpoint, URL interna, correlation ID, payload, token ou prompt/model internals.

Observação factual: o adapter atual pode projetar `remote_name` e `protocol` em detalhes. Isso só deve permanecer quando a disclosure for legítima; refinement futuro deve reduzir exposição se necessário, nunca inventar labels.

## 9. Disclosure

Fechado:

```text
✓ 3 consultas concluídas
  DAVI · TÉO · VISTA
Ver detalhes ▾
```

Aberto:

```text
✓ 3 consultas concluídas
  DAVI · TÉO · VISTA
Ocultar detalhes ▴

✓ Consulta concluída — DAVI
✓ Consulta concluída — TÉO
✓ Consulta concluída — VISTA
```

O componente existente usa botão com `aria-expanded` e `aria-controls`.

## 10. Pending/live activity

A DÉLIA reduz eventos observados via `buildLiveActivityView`. Regras: mostrar somente eventos recebidos; não fabricar especialista, duração, origem ou etapa; não usar timer para avançar estado; fallback genérico é permitido quando ainda não há evento suficiente.

## 11. Atividade do turno concluído

`buildDeliaActivityView` projeta atividade a partir de turno/provenance real. Pode mostrar capacidade acionada, fonte consultada, timestamp observado válido e resultado fundamentado quando suportado. Não substitui `ConversationStatus`, provenance ou limitações.

## 12. Relação com outros componentes

```text
ActivityViewer       = atividade observável
ConversationStatus  = estado semântico da resposta
GovernedConfirmation= decisão explícita governada
ConversationError   = falha da interação frontend/runtime
MessageActionBar    = ações secundárias da mensagem
```

Não fundir responsabilidades.

## 13. Falha parcial / indisponibilidade

Uma atividade pode resumir parcialidade/falha observada, mas estados de produto como `SOURCE_UNAVAILABLE`, `AUTHZ_DENIED` e `WRITE_REJECTED` continuam pertencendo a `ConversationStatus` quando fazem parte da resposta semântica.

## 14. Full page e dock

Mesma implementação. Full page permite mais espaço para detalhe; dock usa wrapping natural e disclosure inline. Zero overflow horizontal, nenhuma segunda sidebar/painel e nenhuma variante funcional paralela.

## 15. Light / dark

Usar somente tokens do Portal/plugin-ui. Running usa primary discreto; completed/success usa success discreto; warning/danger apenas quando estado real. Dark mantém mesma hierarquia, sem card branco ou saturação excessiva.

## 16. Motion

O componente atual anima o ícone de `running`. Motion só enquanto estado real estiver running, deve respeitar `prefers-reduced-motion`, nunca indicar autorização, confiança ou pensamento.

## 17. Acessibilidade

- pending/running pode usar `role=status`;
- disclosure com botão, `aria-expanded` e `aria-controls`;
- detalhe expandido como região identificável;
- ícones decorativos;
- texto comunica estado sem depender de cor;
- teclado e focus-visible;
- conteúdo hostil permanece texto inerte;
- warnings materiais não devem ficar escondidos apenas no disclosure.

## 18. Segurança e privacidade

Não renderizar bearer/JWT, credenciais, raw MCP payload, prompts, chain-of-thought, policy internals, secrets, hidden proposal handles ou control-plane metadata. Eventos/tools são untrusted data; DÉLIA projeta somente labels seguros.

## 19. Ownership

`plugin-ui/ActivityViewer` owns somente summary visual, disclosure, icon/state chrome, steps/sources/outcome presentation, acessibilidade e responsividade.

DÉLIA owns projeção dos eventos/turn data, correlação, ordem factual, labels seguros e distinção live/final. Nenhum dos dois vira authority de AuthZ/business outcome.

## 20. API existente

```ts
type ActivityViewerProps = {
  title: string;
  state: ActivityState;
  steps?: readonly ActivityStepView[];
  sources?: readonly ActivitySourceView[];
  outcome?: ActivityOutcomeView;
  durationLabel?: string;
  summaryDetail?: string;
  expandable?: boolean;
  defaultExpanded?: boolean;
  children?: ReactNode;
  className?: string;
};
```

A API existente é suficiente para o escopo atual; nova API DÉLIA-specific exige gap provado.

## 21. Evidência existente

Há testes do `ActivityViewer` para summary, running, disclosure, teclado, estados, steps, metadata, labels longos, sources, outcomes e hostile markup. Há testes de `buildLiveActivityView` para eventos reais, capability/owner apenas quando observados, start/completion, failure e ausência de especialista inventado.

Esta documentação não converte automaticamente esses testes em Browser QA para outro SHA/config.

## 22. Critérios para refinement futuro

```text
[ ] reanchor
[ ] ActivityViewer permanece componente base salvo gap provado
[ ] EXISTING_EQUIVALENT = YES
[ ] REUSE_DECISION = REUSE ou EXTEND
[ ] no ConversationActivity paralelo
[ ] no progresso inventado
[ ] no chain-of-thought
[ ] no authority conflation
[ ] full page + dock
[ ] light/dark
[ ] 320/420px
[ ] zoom 200%
[ ] teclado/focus
[ ] reduced-motion
[ ] no overflow
[ ] tests/build/federation
[ ] browser evidence
```

## 23. Estado factual

```text
COMPONENT = ActivityViewer
PLUGIN_UI = PROVEN_EXISTING
DELIA_LIVE_INTEGRATION = PROVEN_EXISTING
DELIA_TURN_INTEGRATION = PROVEN_EXISTING
EXISTING_EQUIVALENT = YES
REUSE_DECISION = REUSE
NEW_CONVERSATION_ACTIVITY_COMPONENT = NOT_JUSTIFIED
VISUAL_DIRECTION = DOCUMENTED
NEW_IMPLEMENTATION = NOT_PERFORMED_BY_THIS_DOC
PHASE_ADVANCEMENT = NONE
```

A próxima task, se desejada, deve ser tratada como visual refinement/review do `ActivityViewer` existente, não como criação de um novo componente.
