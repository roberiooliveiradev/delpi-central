# E4.S1 — Verify-final assignee (live)

**Data:** 2026-09-22

## Live (HttpxGlpiClient no container `delpi-helpdesk-api`)

Base interna `http://172.19.0.36`. OAuth via legado `user_token` → authorize PKCE.

| Perfil | Ticket | `can_assign` | `list_users` | assign + reassign |
|---|---|---|---|---|
| Technician (`minha-delpi-upload`) | **1133** | true | ids 2,3,4… | ok |
| Colaborador (Brenda id 19) | **1134** | true | ids 2,3,4… | ok |

## Testes

- helpdesk-api: **48 passed** (`test_helpdesk_api` + `test_glpi_client`) no container
- MFE helpdesk: **116 passed** (incl. structural assignee + help)

## M-23

Catálogo por id (G-A4) **PROVEN** — desbloqueia herança para menções `@` em onda **separada** (fora deste entrega).

## Publish

Rebuild/restart `helpdesk-api` + MFE `helpdesk` para expor UI/rotas no portal.
