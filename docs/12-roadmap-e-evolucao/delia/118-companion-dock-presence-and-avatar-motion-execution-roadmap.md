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
| D02 | Motion State binding do pending request DÉLIA | `EXISTING_EQUIVALENT=YES`: UnifiedAvatar + ActivityViewer + App loading real; `REUSE_DECISION=REUSE/EXTEND_COMPOSITION` | **Primeira task bounded autorizada**: exibir avatar `processing` somente com request pendente e remover visual duplicado no resumo; teste, build/QA, code review e evidence no SHA; `IMPLEMENTATION_CANDIDATE` até provas |
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
