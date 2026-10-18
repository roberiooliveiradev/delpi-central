# 118 — DÉLIA | Companion Dock, presença e Avatar Motion — roadmap bounded

**Data:** 2026-10-17  
**Natureza:** execução frontend complementar ao [116](./116-delia-frontend-capability-surface-and-component-execution-map.md)/[117](./117-frontend-f01-component-export-consumer-and-gap-inventory.md), sem alterar as authorities ou C0–C7.  
**BASE_HEAD observado:** `453daa26958f4f0730efb012619e4dbef4e96fc9` (GitHub main); `git status` local não disponível neste conector.  
**Owners:** Portal = host/abertura/posição do GlobalDeliaDock; plugin-ui = apresentação `UnifiedAvatar`, `ActivityViewer` e design tokens; DÉLIA = estado de interação e composição da conversa; Domain/Core/Keycloak não são derivados de animação.

## 1. Decisões já documentadas

- [69](./69-conversation-experience-ux-wireframes-and-activity-plan.md) WF-03, §14: o Companion Dock é superfície compacta do mesmo produto, sem sidebar persistente nem segunda sessão de backend; microinterações curtas, interrompíveis, acessíveis e não invasivas.
- [76](./76-unified-avatar-delia-motion-and-user-profile-visual-specification.md) §§1–5: conservar círculo azul e Sparkles; `processing` **somente enquanto POST de interação realmente pendente**, halo externo 1600–2200 ms; `idle` estático; `responding` one-shot; `attention` por evento semântico; `prefers-reduced-motion` remove movimento. Não apresentar “pensando”, MCP ou atividade do provider a partir de duração.
- [70](./70-tool-activity-and-source-transparency-ux-specification.md)/[79](./79-conversation-activity-summary-visual-specification.md): `ActivityViewer` relata estado observado sem eventos inventados; evitar indicadores duplicados concorrentes.
- `portal/src/ui/GlobalDeliaDock.tsx` já hospeda DÉLIA por Module Federation. `plugins/plugin-ui/src/components/layout/UnifiedAvatar.tsx` possui `motionState`; `plugins/plugin-ui/src/styles/unified-avatar.css` possui `processing` com pulso CSS de 1900 ms e reduced motion; `plugins/delia/src/App.tsx` apresenta `ActivityViewer` durante `loading`, mas sem `UnifiedAvatar(processing)` naquele estado. `DeliaAssistantMessage` usa `attention/responding/idle` para turnos concluídos, corretamente diferente de turno pendente.

## 2. Trilhas bounded

| ID | Responsabilidade | Reuse gate | Implementação / aceite |
|---|---|---|---|
| D01 | UX de host do Companion Dock: cabeçalho, viewport, drag/resize, chrome, focus, scroll, composer | `EXISTING_EQUIVALENT=YES`: Portal GlobalDeliaDock + shell conversacional; `REUSE_DECISION=EXTEND` somente após QA e owner review | `PLANNED`; não duplicar Dock nem shell |
| D02 | Motion State binding do pending request DÉLIA | `EXISTING_EQUIVALENT=YES`: UnifiedAvatar + ActivityViewer + App loading real; `REUSE_DECISION=REUSE/EXTEND_COMPOSITION` | **IMPLEMENTED + VALIDATION EVIDENCE** (§5–§6); recomendação executor `ACCEPT_WITH_RESIDUAL`; aceite formal GPT; residual Portal/Dock auth + cancel demo |
| D03 | Presença/interações e cópia honesta em espera/resposta/erro/atenção, com opções da personalidade | `EXISTING_EQUIVALENT=YES` para status/evidence/avatars; novos dados `TO_INVENTORY` | `PLANNED`; não inventar eventos, características pessoais ou fontes |
| D04 | Paridade Dock/full-page, mobile, focus, theme, clipped halo, reduced motion, browser & federation | `EXISTING_EQUIVALENT=YES` para harness/tests e host; `REUSE_DECISION=REUSE` | `PLANNED` gate E09 relacionado e review independente; Dock autenticado ainda `TEST_NOT_RUN` no §115 |

## 3. D02 — contrato preciso

**Prova/owner:** `App.loading` já é estado de requisição pendente (real ou explicitamente marcado demo). O avatar `processing` não é projeção de owner MCP, status de ferramenta ou business outcome. Deve aparecer ao lado da atividade de pending já existente, sem segundo spinner; enquanto não há resposta/pending não há pulso. `DeliaReception` idle e avatars de respostas concluídas não ganham loop.

**Acessibilidade:** um único aviso de atividade `role=status` via ActivityViewer, avatar decorativo na composição (`aria-hidden`); reduções de movimento respeitadas pelo CSS `plugin-ui`; não interromper foco/composer. Para Dock estreito, conservar halo dentro do container, sem alterar hierarquia Portal. Evitar segundo rótulo live ou indicador redundante de progresso.

**Accept gates:** teste de elemento condicional e reuso; Vitest DÉLIA; TypeScript, build/federation; inspeção browser real full-page/Companion Dock sob identity authorized, reduced motion e host 320–420px. Se sem executor, `TEST_NOT_RUN`, `INCONCLUSIVE`; sem autoaceite.

## 4. Residuais e trilha de continuidade

- O roadmap [115](./115-navigation-ux-rework-execution-roadmap.md) continua com E09/E10 formais abertos; o 118 não os encerra e não promove fase.
- Novo código de frontend não habilita capabilities backend, MCP/A2A, SSO, memory ou ACT.
- A spec 93 Starter Suggestions continua `IMPLEMENTATION_DEFERRED`; prioridade candidata da F-01 foi revista pelo Product Master em favor de presença/Dock, sem revogar specs de produto.
- Implementações D01/D03/D04 exigem novas tasks delimitadas e aceite baseado em evidência.

```text
TASK_ID=DELIA-UX-COMPANION-D02-PENDING-AVATAR-MOTION-BINDING-01
OWNER_UI=plugin-ui
OWNER_COMPOSITION=plugins/delia
OWNER_DOCK_HOST=Portal
EXISTING_EQUIVALENT=YES
REUSE_DECISION=REUSE_AND_EXTEND_COMPOSITION
CODE_STATUS=PENDING_EVIDENCE
PHASE_PROGRESSION=NONE
NEXT=D02_MINIMAL_UI_DIFF_TEST_BUILD_AND_REVIEW
```


## 5. D02 — implementação publicada, QA pendente (2026-10-17)

**TASK_ID:** `DELIA-UX-COMPANION-D02-PENDING-AVATAR-MOTION-BINDING-01`. **BASE_HEAD:** `453daa26958f4f0730efb012619e4dbef4e96fc9`. **Autorização:** Product Master pediu verificar documentação e iniciar a implementação de presença/Dock. **Reuse:** `EXISTING_EQUIVALENT=YES` (`UnifiedAvatar`, `ActivityViewer`, `App.loading`); `REUSE_DECISION=REUSE_AND_EXTEND_COMPOSITION`. **Owners preservados:** UI = plugin-ui; estado/composição = DÉLIA; host = Portal.

**Alteração mínima efetiva:**
- `plugins/delia/src/App.tsx` insere `UnifiedAvatar(kind="assistant", size="sm", motionState="processing")` **somente quando `loading` for true**, ao lado do `ActivityViewer` já existente; avatar decorativo com `aria-hidden`. Os estados da resposta final e da recepção não foram alterados; o mesmo App serve full-page e Dock.
- `plugins/delia/src/index.css` organiza ícone e atividade em linha compacta, oculta apenas o ícone decorativo do viewer dentro do pending row (evita segunda animação concorrente), mantém texto de status/disclosure e não muda o halo tokenizado de `plugin-ui`.
- `plugins/delia/src/App.test.tsx` registra um teste de início/fim do halo usando o demo gate existente `?delia-demo=loading`, sem chamadas de produção; verifica o estado `processing` somente entre submit e resposta simulada.

**Resultado factual (implementação):** código e teste demo publicados; gates de execução na época = `TEST_NOT_RUN`. **D02_ACCEPTED=NO / IMPLEMENTED_CANDIDATE** até a passagem §6.

## 6. D02 — validação automatizada + browser QA (2026-10-17)

**TASK_ID:** `DELIA-UX-COMPANION-D02-MOTION-VALIDATION-AND-ACCEPTANCE-01`  
**TESTED_SHA:** `a7869a5d4527d251a3f99ef549aa81979ed6d535`  
**Evidence:** [`evidence/companion-d02-motion-validation/d02-motion-validation-and-acceptance-01.md`](./evidence/companion-d02-motion-validation/d02-motion-validation-and-acceptance-01.md)

### Gates executados

| Gate | Resultado |
|---|---|
| Vitest DÉLIA (App/demo/shell) | **44 PASS** |
| Vitest UnifiedAvatar + ActivityViewer | **32 PASS** |
| Vitest MessageComposer (stop) | **23 PASS** |
| delia typecheck | **PASS** |
| plugin-ui full tsc | **FAIL_PREEXISTING 29** (avatar scoped PASS) |
| delia build + federation | **PASS** |
| plugin-ui build + host-exports (`UnifiedAvatar`) | **PASS** |
| Dock unit (`tsx --test`) | **23 PASS** |
| CSS bundle `1.9s` processing + reduced-motion | **PROVEN** |
| Playwright standalone demo LIVE | **AC-01…04,06,08…13,15,16 PASS**; AC-05 PARTIAL; AC-07/14 TEST_NOT_RUN |
| Portal autenticado / Dock live | **TEST_NOT_RUN** |

### Decisão do executor

```text
D02_IMPLEMENTATION_VERIFIED=YES
D02_ACCEPTED=NO
D02_ACCEPTANCE_RECOMMENDATION=ACCEPT_WITH_RESIDUAL
EXECUTION_STATUS=IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW
TASK_VERIFIED_COVERAGE_PCT=81.25
FIXES_APPLIED=NONE
RESIDUALS=demo cancel path; Portal/Dock auth live; real POST pending; AC-05 respond capture timing
PHASE_PROGRESSION=NONE
NEXT=D01_COMPANION_DOCK_UX_IF_ACCEPTED
```

Aceite formal permanece com o review GPT. **D01/D03/D04 e roadmap 115 E09/E10 não avançados.**

## 7. D01 — decisão de produto e implementação bounded: Contexto compacto no Dock (2026-10-17)

**Decisão do Product Master:** no Companion Dock, manter o Contexto como superfície flutuante sobre a conversa, mas menor que a área útil, deixando parte da conversa visível; em tamanhos pequenos, adaptar sem passar por baixo do rail, sem cortar conteúdo e sem cobrir integralmente o composer. Não criar outra coluna, outro painel ou outra sessão. A página completa mantém a geometria existente.

**OWNER:** `plugin-ui` (geometria de `ConversationThreeRegionLayout`); **HOST:** Portal `GlobalDeliaDock`; **CONSUMER:** DÉLIA. **EXISTING_EQUIVALENT=YES**; **REUSE_DECISION=EXTEND**. Evidência inicial: screenshots fornecidos pelo Product Master; CSS E05 utilizava `left: rail + 8px` e `right: 8px`, ocupando quase toda a faixa de conversa no modo compacto.

**Diff de implementação:** regra CSS estritamente sob `.global-delia-dock` para o popover compacto com `right:12px`, `width:min(292px,78%)`, `max-width:calc(100% - rail - 24px)`, `max-height:min(55%,calc(100% - 140px))` e `left:auto`. Valores são hipótese inicial sujeita a QA geométrico; preservados trigger, Escape, foco, leitura, reduced motion, scroll interno e comportamento da página completa.

**Gates pendentes:** Vitest de layout, `plugin-ui` build/exports, DÉLIA build, Browser QA no Dock autenticado (320/360/420 px de largura interna, light/dark, zoom, abertura, foco, scroll, clipping, composer). **TEST_NOT_RUN nesta edição GitHub-only**; CSS publicado não constitui aceite runtime. Após QA, corrigir apenas defeitos reproduzidos e atualizar evidence/ledger com SHA testado. Roadmap 115 E09/E10 permanece aberto. **D01_IMPLEMENTATION=CANDIDATE; D01_ACCEPTED=NO**.

## 8. D01 — ajuste incremental do drawer Conversas no Companion Dock (2026-10-17)

**Evidência de produto:** screenshot do Dock com drawer Conversas aberto mostrou painel lateral largo, deixando pouco espaço visual para a conversa. **Decisão de execução bounded:** preservar drawer, backdrop e semântica de fechamento já implementados e reduzir apenas sua largura no host Portal; não criar segunda navegação ou alterar o comportamento da página completa. **EXISTING_EQUIVALENT=YES; REUSE_DECISION=EXTEND**; owner CSS `plugin-ui`, host Portal, consumer DÉLIA.

**Diff:** override CSS condicionado a `.global-delia-dock` + layout compacto `--with-rail` + `[data-drawer=true]`, com largura `min(252px, calc(100% - rail - 40px))`. A regra genérica E04 continua válida fora do Dock. Mantidos lifecycle, foco, Escape, backdrop, renderização e draft existentes; os valores estão sujeitos a QA visual e geométrico em 320/360/420px, teclado, light/dark, zoom 200% e reduced motion.

**Status:** `IMPLEMENTED_CANDIDATE` no GitHub; `VITEST/BUILD/BROWSER_QA=TEST_NOT_RUN` neste acesso GitHub-only; `D01_ACCEPTED=NO`. A validação integrada foi intencionalmente postergada por orientação do Product Master, sem alterar E09/E10, D02 residuals ou fase.

## 9. D01 — densidade da recepção no Companion Dock (2026-10-17)

**Fonte:** screenshots do Product Master mostram saudação/receptivo no centro da região conversacional e composer no rodapé. **Objetivo bounded:** melhorar a hierarquia e compactar o bloco de recepção sem alterar seus textos, identidade, motion, lógica de estado, scroll, composer ou a página completa. **EXISTING_EQUIVALENT=YES** (`ConversationReception`, `DeliaReception`, CSS compartilhado); **REUSE_DECISION=EXTEND**; owner visual `plugin-ui`, consumidor DÉLIA, host Portal.

**Diff publicado:** CSS de `plugins/plugin-ui/src/styles/conversation-reception.css` escopado à classe real `.global-delia-dock`, limitando largura a 28rem e reduzindo padding (16px/12px), margem do avatar (12px), título (1.125rem), margens da descrição (10px) e nota (8px). Nenhuma lógica/componente duplicado; a página completa retém os valores existentes.

**Validação ainda necessária:** inspeção no Portal real para 320/360/420px do Dock, página completa sem regressão, altura curta, zoom 200%, light/dark, acessibilidade e composer não coberto; verificar CSS federado no asset efetivamente servido. `VITEST/BUILD/BROWSER_QA=TEST_NOT_RUN` nesta edição GitHub-only. `D01_IMPLEMENTED_CANDIDATE`; `D01_ACCEPTED=NO`; não avançar E09/E10 nem C0–C7. Verificação integrada postergada a pedido do Product Master.
