# E10 — Fechar o ciclo: evidência CONSOLE

Data: 21/09/2026. Sem senha / corpo pessoal.

## Vereditos

| Capacidade | Estado | Evidência |
|---|---|---|
| Ver texto da solução na conversa | **IMPLEMENTADO** (leitura) | Timeline `Solution`/`ITILSolution` → `timeline[].kind=solution` (21/09/2026) |
| Pesquisa de satisfação | **CONSOLE** | Schema `TicketSatisfaction` sem path HLAPI (`GET` → 404). Confirmação do time GLPI: surveys «Not implemented yet» na API nova ([issue 21159](https://github.com/glpi-project/glpi/issues/21159)). |
| Aprovar / recusar solução | **CONSOLE** | Paths `…/Timeline/Solution` e `…/Validation` existem, mas a resposta do solicitante na UI clássica depende de follow-up com `add_close` / `add_reopen` — **ainda sem suporte na HLAPI** (mesmo issue). `TicketValidation` é fluxo de aprovação de pedido, não o botão «Aceitar solução». |
| Reabrir / fechar por status | **CONSOLE** | Colaborador: `PATCH` de status = **403** `ERROR_RIGHT_MISSING` (14-H1 / 14-H4). |

## O que o MFE não faz

- Sem tela de pesquisa.
- Sem botões Aprovar/Recusar solução.
- Sem PATCH de status / reabrir.
- Sem inventar payload legado (`_accepted`, `add_close`) na HLAPI.

## O que o MFE faz (leitura)

- Bolha «Solução» quando a Timeline do GLPI traz `Solution` / `ITILSolution`.

Quando a HLAPI documentar a operação do solicitante (follow-up especial ou Validation de solução), abrir **novo** plano — não reaproveitar E10.S1 como receita inventada.
