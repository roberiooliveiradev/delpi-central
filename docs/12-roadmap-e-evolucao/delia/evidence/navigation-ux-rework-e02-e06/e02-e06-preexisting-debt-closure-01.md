# E02–E06 — Fechamento da dívida TypeScript pré-existente (tríade)

**TASK_ID:** `DELIA-UX-NAV-REWORK-E02-E06-PREEXISTING-DEBT-CLOSURE-01`  
**DATE:** 2026-10-17  
**BASE_HEAD:** `85dbfee824bae1d1c1313c2562e220fdf8174743`  
**RELATED:** validação técnica E02–E06 (`DELIA-UX-NAV-REWORK-E02-E06-TECHNICAL-VALIDATION-01`)  
**DEPLOY:** NOT_RUN  
**PHASE_PROGRESSION:** NONE  

## 1. Problemas corrigidos

| Erro | Causa | Correção |
|---|---|---|
| `InitialsAvatar.tsx:198` `src` `string \| null \| undefined` → `string` | Lightbox recebia `src` bruto | Passar `resolvedSrc` (já narrowed no ramo previewable) |
| `layout/index.ts` export `PublishedAvatarProfile` | Tipo removido de `UnifiedAvatar`; reexport órfão | Remover reexport; nenhum consumidor no monorepo |
| `TaskDetailCard.tsx:136` `hint` ReactNode → string | Prop local mais larga que `DetailCard.hint` | Alinhar `hint?: string` ao contrato do `DetailCard` |

## 2. Comandos pós-fix

| Comando | EXIT | Resultado |
|---|---|---|
| `plugins/delia` `npm run typecheck` | **0** | PASS (tríade eliminada) |
| InitialsAvatar + UnifiedAvatar + TaskDetailCard Vitest | **0** | 31 PASS |
| plugin-ui nav Vitest (E02–E06) | **0** | 24 PASS |
| DeliaConversationPage Vitest | **0** | 8 PASS |

Builds/federation: reexecutados na mesma sessão (ver report final).

## 3. Residual

- `npx tsc -p tsconfig.json --noEmit` no **plugin-ui completo** ainda pode reportar dívida em catalog/bpmn/charts/tests **fora** desta tríade e **fora** do gate delia `tsconfig.app.json`.
- Browser QA E09 / review E10 inalterados.

## 4. Decisão

```text
DELIA_TYPECHECK=PASS
TRIAD_PREEXISTING_DEBT=CLOSED
E02_E06_VERDICTS_UNCHANGED
ROADMAP_PROGRESS=6/10 ACCEPTED
NEXT=E07_VISUAL_MOTION_POLISH_IF_GATES_SATISFIED
```
