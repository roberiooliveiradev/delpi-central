# E10 / H10 — Ciclo do solicitante

Data: 22/09/2026. Sem senha / corpo pessoal.

## Vereditos

| Capacidade | Estado | Evidência |
|---|---|---|
| Ver texto da solução na conversa | **PROVEN** (leitura) | Timeline `Solution`/`ITILSolution` → `timeline[].kind=solution` |
| Pesquisa de satisfação | **PROVEN** (Branch B legado) | `apirest.php/TicketSatisfaction` POST/GET; HLAPI continua 404 |
| Aprovar / recusar solução | **PROVEN** (Branch B legado) | `apirest.php/ITILFollowup` com `add_close` / `add_reopen` após ACL OAuth |
| Reabrir / fechar por status (Colaborador PATCH HLAPI) | **CONSOLE** | Colaborador: `PATCH` de status = **403** `ERROR_RIGHT_MISSING` (14-H1) |

## Re-gate HLAPI (22/09/2026)

| Gate | Resultado |
|---|---|
| `GET …/TicketSatisfaction` | **404** |
| Schema `Followup` | sem `add_close` / `add_reopen` |
| `POST …/Timeline/Followup` com `add_close` | cria follow-up; **não** fecha o ciclo |
| `Timeline/Solution` / `TicketValidation` | ≠ botão «Aceitar solução» do solicitante |
| Upstream | GLPI [#21159](https://github.com/glpi-project/glpi/issues/21159) — surveys ainda incompletos na API nova |

## Branch B — legado autorizado (produto)

Mesmo padrão H12 Document: OAuth Bearer prova ACL no ticket; write via App-Token + User-Token técnico (`GLPI_LEGACY_*`).

| Operação BFF | Legado | Prova live |
|---|---|---|
| `POST /tickets/{id}/solution/accept` | `ITILFollowup` + `add_close:1` | ticket **1139**/**1141** status 5→6 |
| `POST /tickets/{id}/solution/reject` | `ITILFollowup` + `add_reopen:1` | status 5→1 / 6→1 |
| `PUT /tickets/{id}/satisfaction` | `TicketSatisfaction` | ticket **1141** score 3; duplicate → 400 |
| `GET /tickets/{id}/satisfaction` | `Ticket/{id}/TicketSatisfaction` | lista com score/comment |

Flags no detalhe (backend-first): `can_accept_solution`, `can_reject_solution`, `can_submit_satisfaction` — só com `requester_mine` + status coerente + legado ligado.

## O que o MFE faz

- Botões Aceitar / Recusar quando `can_*` (status 5, solicitante).
- Formulário de satisfação 1–5 quando `can_submit_satisfaction` (status 6).
- CTA «Abrir no helpdesk» permanece para aprovação (status 10) e fallback sem capability.

## Fora

Bancada / Change / Problem / `helpdesk.console` / HD-011.
