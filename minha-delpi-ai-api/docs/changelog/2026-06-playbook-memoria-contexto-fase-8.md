# Changelog — Playbook memória e contexto (Fase 8)

**Data:** 03/06/2026

## UX de memória

- `ChatMemoryUxService`: chips assunto/tarefa/anexo, `metadata.memoryUx`, resumo da barra, vista de uso.
- Resposta direta «quais informações você está usando?» e edição de preferência via `ChatSessionMemoryDirectAnswerService`.
- Pins: `ChatSessionMemoryPinsUseCase` retorna `summary` + `usage`.
- MFE: `ChatContextBar` (ver memória, fixar, menu), `ChatMemoryUsedDialog`, ações em `chatContextChipActions.ts`.
- Regressão **M20**.

## Validação

```bash
./scripts/run_memory_context_validation.sh
cd plugins/minha-delpi-chat && npm run build
```
