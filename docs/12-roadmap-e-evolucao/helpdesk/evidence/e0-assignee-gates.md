# E0.S1 — HLAPI gates: TeamMember `assigned` + catálogo de usuários

**Data:** 2026-09-22  
**Ambiente:** GLPI interno `http://172.19.0.36` (container `inventario-ti-glpi-1`), OAuth client da helpdesk-api.  
**Método:** `user_token` legado → cookie web = `session_token` → `GET /api.php/authorize?accept=1` + PKCE → Bearer HLAPI 2.2.  
**Script:** `helpdesk-api/scripts/probe_assignee_gates_e0.py` (não imprime tokens).

## Perfis

| Label | Usuário GLPI | Perfil | Resultado |
|---|---|---|---|
| technician | `minha-delpi-upload` (legado `GLPI_LEGACY_USER_TOKEN`) | Technician (6) | PROVEN |
| colaborador | Brenda (id 19) via `api_token` cifrado | Colaborador - Chamados (1) | PROVEN |

Chamados de prova: **1131** (tech), **1132** (colab).

## Gates

| Gate | Critério | Tech | Colaborador |
|---|---|---|---|
| G-A1 / G-A2 | `POST …/Ticket/{id}/TeamMember` `{type:User, role:assigned, id}` → 201 | **201** (id=2) | **201** (id=2) |
| G-A3 | DELETE TeamMember (body type/role/id) → 200; segundo POST assigned → 201; um único ator | DELETE **200**, reassign **201**, `assigned_ids=[3]`, sem duplicata | idem |
| G-A4 | `GET /Administration/User?filter=is_active==true` devolve itens com **id** + nome | **206**, sample ids 2.. | **206**, mesmos ids |
| G-A5 | assigned id inexistente | **400** `ERROR_INVALID_PARAMETER` | **400** |
| RQ-07 | observer ainda 201 | **201** | **201** |

## Notas

- WAF no host público (`helpdesk.centraldelpi.com.br`) bloqueia User-Agent de script; prova usou rede interna Docker.
- `GET /Administration/User/Me` retornou **403** nos tokens de prova; o catálogo por lista/filtro com **id** está disponível (G-A4).
- Body HD-011-safe: só `{type, role, id}` — sem requester/entity.
- Reatribuição: `DELETE …/TeamMember` **com** body `{type, role, id}` funciona neste GLPI 11 / HLAPI 2.2 (OpenAPI omite requestBody, mas o runtime aceita).

## Decisão

**E0 PROVEN** — liberar E1 (contrato BFF) e UI. Não há STOP-THE-LINE em G-A1 nem G-A4 neste ambiente.  
M-23 (menções) herda o catálogo por id em onda **separada** após assignee estável.
