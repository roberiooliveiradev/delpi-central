# E12 — VISTA parity

**Status:** IMPLEMENTED

- Mesmo `PresentationPatchService` / ops catalog para VISTA e editor.
- Editor persiste via `PresentationMutationCommitService`; VISTA continua PREPARE/ACT → httpCommands/WriteService.
- VERIFY: usar enrich `display*` / layout frames do nativeConfig pós-mutation (sem helpers React).
