# E9.S16 — F5 / session reload (API)

**Status:** `ATENDIDO` (2026-09-11)  
**Onda:** H (encerramento de débitos)  
**Harness:** `scripts/smoke_e9_s16_f5_session_reload_live.py`  
**JSON:** `evidence/e9-s16-f5-session-reload-live.json`

## Escopo

Medição da superfície de **reload de sessão** no backend (equivalente F5):

1. SEND estoque
2. GET `/sessions/{id}/messages` — histórico persistido com toolCalls
3. FOLLOW-UP reconsulta o mesmo produto na mesma sessão

Browser/MFE Playwright permanece fora do escopo da AI API; o contrato de persistência que o F5 consome é este.

## Veredito

```text
API_SESSION_RELOAD = PASS
HISTORY_TOOLCALLS_PERSISTED = PASS
SAME_PRODUCT_FOLLOWUP_AFTER_RELOAD = PASS
```
