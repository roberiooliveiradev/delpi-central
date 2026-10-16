# INTERACTION ROOMS V2 — ARCHITECTURE CONTRACT FINAL

**Repositório:** `roberiooliveiradev/delpi-central`
**HEAD analisado:** `32661f98dd08df5c276c74f28cf31b79e936feb9` (`main`)

```text
VERDICT:        ACCEPT_WITH_RESIDUAL
TARGET:         ARCHITECTURE READY FOR IMPLEMENTATION REVIEW
IMPLEMENTATION: NOT AUTHORIZED — até aprovação deste contrato final
```

```text
PRODUCT DECISION != PROVEN IMPLEMENTATION
CONFIRMATION     != AUTHORIZATION
PREPARE          != ACT
2xx              != VERIFIED OUTCOME
```

---

## 1. DECISÕES RATIFICADAS (consolidado)

| Decisão | Conteúdo |
|---|---|
| D-01 | Multi-primary: sala → N primários; objeto → ≤1 sala primária **ativa**; `open_or_locate` resolve primary; `link_role` = cardinalidade/resolução, **não** segurança |
| D-02 | Interseção fail-closed sobre **todos** os links com autoridade externa (primary e reference); sem persistir dado GLPI |
| D-03 | Standalone nasce `access_scope='members'` |
| D-04 | Exclusão lógica + restauração governada; sem purge; admin ≠ leitura de conteúdo |
| R-1 | Remoção de link restritivo só sem conteúdo histórico — inclui **tombstones** e qualquer conteúdo persistido; em dúvida, bloquear |
| R-2 | Sala restrita aparece só a participantes que **satisfazem integralmente** a interseção vigente; participação isolada não concede |
| R-3 | Autoridade administrativa (`is_owner ∨ transformometro.manage`) separada de leitura; `manage` validado contra contrato do Core |
| R-4 | `deleted_at + deleted_cause` aprovado como candidato com invariantes (atomicidade, sem hard-delete, causa explícita vs `room_deleted`) |
| R-5 | Preview administrativo = metadados seguros apenas — sem `title`, mensagens, anexos, evidências ou identificadores protegidos |
| R-6 | Reuso de `collaboration_read`/`prepare_collaboration_change`/`commit_proposal`; sem tools/proxies novos |

---

## 2. MATRIZ DE AUTORIZAÇÃO (final)

```text
can_access_room(u, R) =
    has_permission(u, transformometro.access)
    AND R.deleted_at IS NULL
    AND (R.access_scope='open' OR u=R.created_by OR u ∈ R.participants)
    AND ∀ L ∈ R.links (deleted_at IS NULL, entity_type externo):
        link_visible(u, L)

link_visible(u, L):
    'process'         → True    -- postura canônica app-level (sem ACL por processo)
    'helpdesk_ticket' → BFF GET /tickets/{entity_key} com Bearer de u
                        2xx → True; 403/404/glpi_link_required/401 → False;
                        502/503/timeout → False (fail-closed)

can_admin_room(u, R) = is_owner(u,R) OR transformometro.manage   -- SEM interseção, SEM access
manage_links = can_admin_room
manage_participants = can_admin_room (remove = admin ou self)
can_write = can_access_room
```

| Operação | Gate | Erro tipado |
|---|---|---|
| `open_or_locate` | `access` + probe do caller p/ ticket | `target_not_accessible` 403 |
| `add_link` | `can_admin_room` + probe caller (restritivo); objeto reivindicado → `primary_link_conflict` | 403/409 |
| `remove_link` | `can_admin_room` **∧** regra R-1 (§2.1) | `room_access_expansion_blocked` 409 |
| `change_role` | `can_admin_room` (não altera conjunto restritivo) | `primary_link_conflict` |
| `add/remove_participant` | `can_admin_room` / self-leave | `room_admin_denied` 403 |
| `delete_room` | `can_admin_room` + confirm; preview metadados-only (R-5) | `room_admin_denied` |
| `restore_room` | `can_admin_room` + checks §6 | `primary_link_conflict`, `linked_target_unavailable`, `room_not_deleted` |
| `get`/mensagens/anexos/reads/pins | `can_access_room`; negado = 404-equivalente (R-5/Q-11) | — |
| `list_rooms` | open-sem-link-restritivo ∪ (participante ∧ interseção completa) (R-2) | — |
| Tarefas | assignee vê tarefa sem ganhar sala; source → `room_archived` | — |

### 2.1 Regra de remoção (GATE A + R-1 — final)

```text
remove_link(L) permitido ⟺
    L.entity_type = 'process'                      -- não-restritivo
    OR NOT EXISTS conteúdo persistido na sala      -- inclui mensagens tombadas,
                                                    anexos, reações, menções
caso contrário → 409 room_access_expansion_blocked
```

Prova (§4.2 do histórico): expansão para **futuros** participantes é irrefutável sem segregação por mensagem; os únicos casos prováveis são link não-restritivo e ausência total de histórico. `change_role` nunca altera o conjunto restritivo → sempre seguro. Freeze+evict: fora do V2.

---

## 3. DDL PROPOSTO (EXPAND — nº a confirmar contra `schema_migrations` real)

```sql
-- EXPAND (provisório V053 — confirmar numeração real antes de criar arquivo)

ALTER TABLE transformometro.tm_interaction_rooms
    ADD COLUMN title TEXT,
    ADD COLUMN access_scope TEXT NOT NULL DEFAULT 'open',
    ADD COLUMN deleted_at TIMESTAMPTZ,
    ADD COLUMN deleted_by_user_id TEXT,
    ALTER COLUMN processo_id DROP NOT NULL;

ALTER TABLE transformometro.tm_interaction_rooms
    ADD CONSTRAINT tm_interaction_rooms_scope_ck
        CHECK (access_scope IN ('open','members'));

CREATE TABLE transformometro.tm_interaction_room_links (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id            UUID NOT NULL
        REFERENCES transformometro.tm_interaction_rooms (id) ON DELETE CASCADE,
    entity_type        TEXT NOT NULL
        CHECK (entity_type IN ('process','helpdesk_ticket')),
    entity_key         TEXT NOT NULL,
    link_role          TEXT NOT NULL DEFAULT 'reference'
        CHECK (link_role IN ('primary','reference')),
    created_by_user_id TEXT NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at         TIMESTAMPTZ,
    deleted_cause      TEXT
        CHECK (deleted_cause IS NULL OR deleted_cause IN ('explicit','room_deleted')),
    CONSTRAINT uq_tm_interaction_room_links_room_target
        UNIQUE (room_id, entity_type, entity_key)
);

CREATE UNIQUE INDEX uq_tm_interaction_room_links_primary_active
    ON transformometro.tm_interaction_room_links (entity_type, entity_key)
    WHERE link_role = 'primary' AND deleted_at IS NULL;

CREATE INDEX idx_tm_interaction_room_links_room
    ON transformometro.tm_interaction_room_links (room_id)
    WHERE deleted_at IS NULL;

CREATE INDEX idx_tm_interaction_room_links_target
    ON transformometro.tm_interaction_room_links (entity_type, entity_key);

CREATE TABLE transformometro.tm_interaction_room_participants (
    room_id          UUID NOT NULL
        REFERENCES transformometro.tm_interaction_rooms (id) ON DELETE CASCADE,
    user_id          TEXT NOT NULL,
    role             TEXT NOT NULL DEFAULT 'member'
        CHECK (role IN ('owner','member')),
    added_by_user_id TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (room_id, user_id)
);

CREATE INDEX idx_tm_interaction_room_participants_user
    ON transformometro.tm_interaction_room_participants (user_id);
```

**Notas de DDL:**
- Re-adição de link tombado = upsert revive a linha (`deleted_at=NULL`, `deleted_cause=NULL`, role atualizado) — o `UNIQUE(room_id, entity_type, entity_key)` não conflita com tombstones porque a linha é reutilizada, não duplicada.
- Race `open_or_locate` no mesmo objeto: `23505` no índice parcial → catch → re-resolve → retorna a sala existente.
- `MIGRATE` (arquivo seguinte): backfill idempotente `links(primary)` ← `processo_id`; `participants(owner)` ← `created_by_user_id`; ambos `ON CONFLICT DO NOTHING`.
- `VERIFY`: `count(rooms.processo_id NOT NULL) = count(links primary ativos process)`; zero órfãos em messages/attachments/reads; amostra read-path old vs new.
- `CONTRACT` (release posterior): `DROP COLUMN processo_id` + FK após soak; DTO `processo_*` derivado do link primário.
- Rollback pré-CONTRACT: código (coluna intacta); pós: SQL documentado re-derivando `processo_id`.

---

## 4. CONTRATOS HTTP (transformometro-api)

### 4.1 Criação / localização

`POST /interaction-rooms`
```json
{ "processo_id": "uuid" }                          // legado — inalterado
{ "ticket_id": 1275, "access_scope": "members" }   // novo — probe caller no BFF
{ "title": "War room NF-e", "access_scope": "members" }  // standalone
```
Response: room DTO + `links[]` + `participants[]` + `access_scope` + `title`. `processo_*` derivados do primary link (compat).

### 4.2 Leitura

`GET /interaction-rooms/{id}` → `404`-equivalente se `can_access_room` falha (sem oracle). `links[]` por viewer: `{id, entity_type, link_role, resolution:'ok'|'restricted'|'unavailable', display?}` — `display` só quando resolvido; `entity_key` nunca em `restricted`.

`GET /interaction-rooms` (`inbox_filter`: `all|unread|mentioned|process|ticket|standalone`) → regra R-2.

### 4.3 Administração

| Rota | Body / efeito |
|---|---|
| `POST /{id}/links` | `{entity_type, entity_key, role='primary'|'reference'}` |
| `DELETE /{id}/links/{link_id}` | `deleted_cause='explicit'`; expansion check |
| `POST /{id}/participants` | `{user_id}` — convite (owner/manage) |
| `DELETE /{id}/participants/{uid}` | admin ou self |
| `GET /{id}/impact` | preview metadados: `{messages, attachments, tasks, links_by_type, participants}` — sem `title`/conteúdo |
| `DELETE /{id}` | archive lógico |
| `POST /{id}/restore` | checks de restore |

Erros: `target_not_accessible` 403 · `primary_link_conflict` 409 · `target_unavailable` 502 · `room_access_expansion_blocked` 409 · `room_admin_denied` 403 · `room_archived` 410 · `room_not_deleted`/`linked_target_unavailable` 409 · sala negada = 404-equivalente.

---

## 5. CAPABILITIES MCP / EXECUTION POLICIES (R-6)

Via `prepare_collaboration_change` → `commit_proposal` — sem tools novas:

| Action → Capability | Policy | `exact_change` contém |
|---|---|---|
| `open_room` → `open_interaction_room` | `auto_act` | `{processo_id|ticket_id|title, access_scope}` — discriminador sealed |
| `add_room_link` → `add_interaction_room_link` | `confirm_before_act` | target, role, `access_shrinks:{count}` |
| `remove_room_link` → `remove_interaction_room_link` | `confirm_before_act` | target, `expansion_check` (eager `room_access_expansion_blocked` se aplicável) |
| `add_participant` → `manage_interaction_room_participants` | `auto_act` | `{user_id}` + `member_cannot_access` hint se probe falha |
| `remove_participant` → idem | `confirm_before_act` | `{user_id}` |
| `delete_room` → `delete_interaction_room` | `confirm_before_act` | impact counts (R-5 metadados-only) |
| `restore_room` → `restore_interaction_room` | `confirm_before_act` | checks §6 resultado |

Fluxo: `READ CURRENT → PREPARE (não escreve) → policy → commit (fresh authz + fingerprint) → read-back → VERIFY`. `collaboration_read` ganha `room` com links/participants e `resolution` per-viewer. OpenAPI re-import obrigatório.

---

## 6. EXCLUSÃO E RESTAURAÇÃO

**Archive (uma tx):** `rooms.deleted_at + deleted_by_user_id` + `links.deleted_at + deleted_cause='room_deleted'` → libera reivindicação primária (índice parcial), preserva relações, sem cascade física. Sala some de inbox/`get`/`resolve` (404-shape); writes = `room_archived`; tarefas intactas com source→`room_archived`.

**Restore (commit-fresh):** `can_admin_room` revalidado → room tombada (fingerprint) → actor autorizado nos targets a re-ativar → nenhum primary re-reivindicado → senão `primary_link_conflict`/`linked_target_unavailable`/`room_not_deleted` → limpa `deleted_at` só onde `cause='room_deleted'` (`'explicit'` permanece) → read-back → audit. Sem restore parcial.

---

## 7. TESTES DE SEGURANÇA (aceite ratificado + derivados)

| # | Teste |
|---|---|
| T-01 | Remoção de link não amplia acesso ao histórico (`room_access_expansion_blocked` em open e members com conteúdo) |
| T-02 | Participante convidado **sem** ACL do objeto vinculado → negado (histórico incluído) — participação isolada não concede |
| T-03 | Participante sem ACL GLPI → negado, mesmo sendo member |
| T-04 | Revogação GLPI bloqueia leitura imediata (mensagens, anexos, inclusive próprias) |
| T-05 | Gestor sem `transformometro.access` administra (delete/impact) sem ler conteúdo — preview só metadados |
| T-06 | Exclusão libera reivindicação primária (novo `open_or_locate` cria sala nova) |
| T-07 | Restore com conflito → `primary_link_conflict`; zero mutação parcial |
| T-08 | Sala primary ticket + primary process: usuário sem ACL do ticket → 404-equivalente; `open_or_locate(process)` **não** cria duplicata (resolve → nega) |
| T-09 | Todas as rotas de conteúdo (mensagens, anexos, pins, reads, tasks-source) respeitam a mesma política — sem rota que bypassa |
| T-10 | Sala com reference a ticket restrito nega a quem não tem ACL (reference ≠ bypass) |
| T-11 | `remove_link` com `content_count=0` permitido; tombstones contam como conteúdo |
| T-12 | `room_id` direto negado = indistinguível de inexistente |
| T-13 | BFF down → salas com link a ticket somem do inbox (fail-closed) |
| T-14 | `add_participant` de usuário sem ACL → permitido como membro, mas acesso negado (hint `member_cannot_access`) |
| T-15 | Regressão: sala legada de processo funciona idêntica (open, get_or_create, compat DTO) |

---

## 8. SEQUÊNCIA DE IMPLEMENTAÇÃO E1–E8

| Slice | Conteúdo | Depende de |
|---|---|---|
| E1 | Domain (entidades/ports/regras) + migration EXPAND + InMemory | Nº real `schema_migrations` (1 query) |
| E2 | AuthZ: interseção, expansion rule, participants, `TicketVisibilityPort` + negativos T-01…T-15 | E1 |
| E3 | HTTP routes + envelope de erros | E2 |
| E4 | — **elimidado**: adapter usa `GET /tickets/{id}` existente (GATE E) | — |
| E5 | TÉO: capabilities + policies + registry + OpenAPI re-import | E2 |
| E6 | Tasks: derivação por links, `room_archived` stub, inbox filters | E2 |
| E7 | Exclusão/restauração: archive cascade, restore checks, impact preview | E2, E3 |
| E8 | Docs + product guides TÉO | Todos |
| V2 UX | Portal: links panel, stubs, standalone, Meus Chamados TI | E3 |
| V2 Realtime/Notif | investigação separada | pós-Core |

---

## 9. PENDÊNCIAS QUE IMPEDE EXECUÇÃO (todas operacionais, não arquiteturais)

1. **`schema_migrations` real** — 1 query no DB antes de nomear o arquivo de migration (V052 é trabalho paralelo).
2. **Grants de `transformometro.manage` em produção** — mecanismo e contrato provados; confirmar matriz de concessão no Core na implantação.
3. **Validação do DDL** em ambiente real (índice parcial + upsert de tombstone) — primeiro passo do E1.
4. **Regressão de salas legadas** — suíte T-15 + smoke de `open_for_process` pós-EXPAND.

**Nenhum bloqueio arquitetural remanescente.** Gates A–F comprovados em desenho; prova operacional ocorre na implementação dos testes negativos.

```text
FINAL VERDICT PROPOSTO: READY_FOR_IMPLEMENTATION
aguardando apenas aprovação deste contrato + as 4 pendências operacionais acima.
```

---

# ADDENDUM — E1 PREFLIGHT EVIDENCE (executado 2026-10-16)

**BASE HEAD:** `32661f98` → **FINAL HEAD:** `0018906278` (`main`) — trabalho paralelo mergeou durante a análise.

## EXECUTION_DRIFT detectado e resolvido (favorável)

O paralelo entregou **V055__interaction_room_soft_delete** + `delete_room`/`soft_delete`/`DELETE /interaction-rooms/{id}`:
- `tm_interaction_rooms.deleted_at` **já existe** → removido do EXPAND.
- Unicidade por processo já é parcial `WHERE deleted_at IS NULL`.
- `delete_room` usa `require_manage` **sem** `require_access` — semântica `can_admin_room` já correta.
- **Gaps vs contrato D-04:** owner-authority, impact preview, restore, `deleted_by_user_id`, audit append, cascade de links (inexistente — sem links ainda), capability TÉO.
- **`created_by_user_id` é `UUID`** no schema (não `TEXT`) — links/participants ajustados para `UUID`.
- Próxima migration livre: **V056** (V053/V054 = BPMN paralelo).

## Validação em DB isolado (`delpi_e1_scratch`, Postgres 16 — schema real V002+V046+V047+V055)

| Teste | Resultado |
|---|---|
| EXPAND DDL revisado aplica sobre schema real | **PASS** |
| VERIFY paridade backfill (rooms↔primary links) | **PASS** (1=1) |
| T1 claim primária duplicada → `23505` no índice parcial; `reference` ao mesmo objeto permitido | **PASS** |
| T2 archive (room+links `room_deleted`, uma tx) libera reivindicação → nova sala primária criada | **PASS** |
| T3 restore com claim ocupada → rejeitado no link **e** no índice `processo_active` da sala (backstop duplo — achado); ordem correta funciona, `active_primaries=1` | **PASS** |
| T5 re-adição de link tombado = upsert revive sem duplicar | **PASS** (3 links, 1 revived) |
| T6 `processo_id DROP NOT NULL` → standalone criável | **PASS** (2 standalone) |
| T7 `content_count` inclui tombstones | **PASS** |
| **Concorrência real** — 2 sessões paralelas `open_or_locate(#1275)`: exatamente 1 claim, perdedor `23505`, **zero sala órfã** (CTE atômico) | **PASS** |

## Pendência E1 restante

`schema_migrations` do banco **real de produção/dev** = `PENDING` (banco local é vazio — schema `transformometro` inexistente; DB real não acessível deste ambiente). Numeração V056 confirmada em arquivos; confirmar contra a tabela real antes de criar o arquivo.

---

*Architecture Contract Final + E1 evidence — nenhum código, migration, OpenAPI ou frontend alterado. Trabalho paralelo na árvore preservado.*

---

# ADDENDUM 2 — E2 EXECUTION EVIDENCE (executado 2026-10-16)

**Escopo:** Domain + Application + Ports/Adapters + testes. Sem migration, sem frontend, sem expansão de contrato público.

## Implementado

- **Domain:** `InteractionRoomLink` (entity_type/entity_key/link_role/deleted_at/deleted_cause), `InteractionRoomParticipant` (owner/member, removed_at), `InteractionRoom.access_scope`+`title`+`deleted_by_user_id`+grafos `links`/`participants`. Entidades congeladas — `access_scope` só na criação (Q-19).
- **Serviço de decisão puro:** `check_room_access` + `deny_reason_for_state` + `is_externally_governed` — interseção de todos os links ativos; `primary`/`reference` não alteram segurança.
- **Port:** `TicketVisibilityPort` (visible/restricted/not_found/session_missing/unavailable) + adapter `HelpdeskBffGateway.check_ticket_visibility` sobre `GET /tickets/{id}` existente — Bearer do usuário, `glpi_link_required`→session_missing, forbidden→restricted, not_found→not_found, demais→unavailable.
- **Use cases:** `open_for_process` (resolve por primary claim canônico → fallback legado → dual-write), `open_for_ticket` (open_or_locate + corrida → re-resolve ao vencedor + órfã tombada), `open_standalone` (members-only), `add_link`/`remove_link` (R-1: `room_access_expansion_blocked` com histórico protegido — tombstones contam), `add/remove_participant`, `delete_impact` (só contagens — sem título/keys, R-5), `delete_room` (owner OU manage; cascade `room_deleted` atômico), `restore_room` (revive só `room_deleted`, conflito → `primary_link_conflict` sem estado parcial).
- **Repositório:** `get_raw`, `create_room`, `find_active_primary_room`, `upsert_link` (ON CONFLICT revive tombado; 23505→`PrimaryLinkConflict`), `tombstone_link`, participants, `protected_content_count` (mensagens+anexos **incluindo** tombados), `soft_delete`/`restore_room` em transação única.
- **Superfícies:** Bearer do usuário propagado em rotas HTTP, dispatch TÉO e MCP (`build_mcp_request` já encaminha `context.authorization`). Zero mudança de `operation_id`.

## Testes — 43 passando (`test_interaction_rooms.py` + `test_interaction_rooms_v2.py`)

| Gate | Evidência |
|---|---|
| T-01 ticket room nega sem ACL (get/messages/inbox) | PASS |
| T-02 `reference` restringe como `primary` | PASS |
| T-03 participante removido perde room/messages/attachments/inbox | PASS |
| T-05/T-11 remoção de link restritivo com histórico (incl. tombado) → `room_access_expansion_blocked` p/ owner **e** gestor | PASS |
| T-06 link restritivo sem conteúdo removível; link `process` removível com histórico | PASS |
| T-07 claim primária duplicada → `primary_link_conflict`; multi-primary por sala OK | PASS |
| T-08 `open_or_locate(process)` resolve sala multi-primary e nega sem criar duplicata | PASS |
| T-09 exclusão libera claim; nova sala assume | PASS |
| T-10 restore com claim ocupada → `primary_link_conflict` sem reativação parcial; link `explicit` não revive | PASS |
| T-12 gestor sem `access` administra (impact+delete) mas não lê conteúdo | PASS |
| T-13 GLPI restricted/not_found/session_missing/unavailable → fail-closed tipado | PASS |
| T-15 regressão legada: `open_for_process` idempotente, dual-write primário | PASS |
| Corrida de claim (re-resolve ao vencedor, órfã tombada) | PASS (in-memory; nível PG provado no E1) |
| Owner sem `manage` exclui; não-owner sem `manage` negado | PASS |

## TEST_NOT_RUN / PENDING

- Adapter SQL contra banco real: depende de V056 (não criada/aplicada — fora do escopo E2). Revisão manual do SQL + paridade in-memory; prova de PG já existe no E1 para as constraints.
- Integração real com Helpdesk BFF: adapter escrito e mapeado; sem sessão GLPI neste ambiente.
- TÉO open para standalone/ticket e capabilities delete/restore/link/participant: contrato de slice posterior (GATE F).
- 8 falhas pré-existentes no suite geral (dashboard/filial/sign-invite/shared-resource) — **reproduzidas em worktree limpa @HEAD**; não causadas por este diff.

---

# E2 CORRECTION EVIDENCE (review REWORK → targeted pass)

Base para a correção: HEAD `8626e874822` (E2 commit `58d53f52` é ancestral; `origin/main` avançou a `821f0cd7` com 4 commits docs/delia — sem overlap). Working tree: só 5 arquivos do escopo alterados; trabalho paralelo em `plugins/*` e `requests-api` preservado.

## P0 — administrative response leak — FIXED

- `DELETE /interaction-rooms/{id}` não serializa mais `room.to_dict()`; retorna projeção mínima `{id, deleted_at}` (read-back da exclusão apenas).
- Residual search: demais `to_dict()` nas rotas/dispatch só saem por `_authorized_room` (interseção completa). `delete_impact` já era metadata-only (contagens + `link_roles` por tipo:papel — sem `entity_key`). Dispatch/GPT não chama `delete_room`/`restore_room`/`delete_impact`. `orchestrator.py` usa `get_or_create` apenas como literal de fingerprint.
- Teste HTTP novo `test_http_delete_returns_safe_admin_projection`: gestor `manage`-sem-`access` exclui (200), payload sem `title`/`process_*`/`participants`/`last_message_preview`/`links`/`last_message_at`/`processo_id`, não-admin recebe 403, read-back = `LookupError`.

## P1 — write-before-authorization — FIXED

- `open_for_process` agora é estritamente locate → authorize → mutate: resolve a sala canônica (`find_active_primary_room` → `get_by_process` read-only), autoriza a interseção completa, e só então roda `_assert_process_link` (que também não revive remoção `explicit`). Uma tentativa negada não toca links, rooms nem cria duplicata.
- Testes: `test_open_for_process_denied_performs_no_writes` (sala process+ticket, requester sem ACL do ticket → deny, zero upsert/create, sem duplicata) e `test_open_for_process_does_not_revive_explicit_link_removal`.

## P1 — creation atomicity — FIXED

- Novo `create_room_graph` no port: room + links + participants em **uma** transação (`self.db()` + `auto_commit=False`; exceção → rollback integral — sem sala órfã, sem link solto, sem participante parcial). Conflito de claim primária (23505, `uq_tm_interaction_room_links_primary_active` / `uq_tm_interaction_rooms_processo_active`) → `PrimaryLinkConflict` antes do commit → nada persistido.
- `open_for_ticket`/`open_standalone`/`open_for_process` migrados; corrida perdedora re-resolve ao vencedor com autorização fresca. Índices canônicos continuam árbitros finais.
- Testes: `test_create_room_graph_rolls_back_on_occupied_primary` (snapshot rooms+links+participants inalterado após conflito) e `test_open_for_ticket_race_re_resolves_to_winner` (agora também prova `len(repo.rooms)` inalterado — zero órfã).

## P1 — protected historical content — FIXED

- `protected_content_count` (SQL + InMemory) cobre **todo** artefato persistido da sala: mensagens (ativas **e** tombadas), anexos, menções, reações, pins e read markers. Cobertura justificada por constraints: menções/reações/anexos são filhos de mensagens da sala (FK), pins/reads são filhos diretos da sala — não existe artefato de histórico fora dessas 6 relações no schema V046/V047/V055.
- R-1 endurecida: `test_read_marker_counts_as_protected_history` prova que até um read marker bloqueia remoção de link restritivo (block-on-doubt). `delete_impact` renomeado para `protected_content_count` (semântica correta da contagem).

## P1 — audit consistency — FIXED

- `_audit_log` usa o `AuditRepository` canônico e é best-effort **após** commit do domínio: falha de auditoria é logada via `logger.warning("interaction_room_audit_failed ...")` e o resultado do domínio permanece verdadeiro (convenção idêntica a `gpt_actions._audit`). Nenhuma infra genérica nova.
- Teste: `test_audit_failure_does_not_corrupt_write_result` — audit quebrado → criação e delete persistem, read-back confirma exclusão, warning registrado.

## Verification matrix

| Item | Resultado |
|---|---|
| T-01…T-15 regression (`test_interaction_rooms_v2.py` + `test_interaction_rooms.py`) | **49 passed** |
| Novos P0/P1 (projeção HTTP, denied-no-writes, atomicidade, R-1 read marker, audit failure, explicit-removal) | PASS — 6 testes |
| Full suite `transformometro-api/tests` | 1688 passed, 10 failed — as 10 reproduzem em worktree limpa @`8626e874` (dashboard/filial/shared-resource/sign-invite/bootstrap) → pré-existentes |
| PostgreSQL real com V056 | `PENDING` — V056 não aplicada; SQL revisado, constraints já provadas no E1 |
| Helpdesk/GLPI real | `TEST_NOT_RUN` — sem sessão GLPI neste ambiente |

Nota operacional: durante a sessão um `__pycache__` stale (skew de relógio UNC↔WSL) produziu falsos `AttributeError` — resolvido limpando caches; rerun = 49/49.

---

# E3 EVIDENCE — HTTP ROUTES, AUTHORIZATION & ERROR CONTRACT

Base: HEAD `ffc0c36c88` (== `origin/main`; E2C `b55c982f` ancestral confirmado). Escopo: `interaction_room_routes.py`, `manage_interaction_rooms.py`, `interaction_room_access_service.py`, testes. Sem frontend, MCP/GPT, realtime ou notifications.

## Endpoints adicionados (operation_ids novos; legados inalterados)

| Método | Path | operation_id | AuthZ | Resposta |
|---|---|---|---|---|
| POST | `/interaction-rooms/ticket` | `open_transformometro_interaction_room_for_ticket` | `access` + ACL GLPI (Bearer do usuário) | room `to_dict()` (interseção OK) |
| POST | `/interaction-rooms/standalone` | `create_transformometro_standalone_interaction_room` | `access` | room `to_dict()` (201) |
| GET | `/{id}/links` | `list_transformometro_interaction_room_links` | interseção completa | `items[]` |
| POST | `/{id}/links` | `add_transformometro_interaction_room_link` | owner/manage | `{id}` (201) |
| DELETE | `/{id}/links/{link_id}` | `remove_transformometro_interaction_room_link` | owner/manage | `{id}` |
| GET | `/{id}/participants` | `list_transformometro_interaction_room_participants` | interseção completa | `items[]` |
| POST | `/{id}/participants` | `add_transformometro_interaction_room_participant` | owner/manage | `{user_id}` (201) |
| DELETE | `/{id}/participants/{user_id}` | `remove_transformometro_interaction_room_participant` | owner/manage | `{user_id}` |
| GET | `/{id}/impact` | `get_transformometro_interaction_room_delete_impact` | owner/manage | metadados-only (R-5) |
| POST | `/{id}/restore` | `restore_transformometro_interaction_room` | owner/manage | `{id, deleted_at}` |

Admin ops respondem projeções mínimas (mesma disciplina do P0). Conteúdo sempre via `_authorized_room` (interseção). Erros tipados: `not_found` (404 — sem oráculo de existência), `glpi_link_required` (403), `upstream_unavailable` (503), `room_access_expansion_blocked` (409), `primary_link_conflict` (409), **`legacy_anchor_locked` (409 — novo, ver 5.3)**.

## Contratos pendentes — fechados

- **5.1 confirm_before_act:** o DELETE/REST é a superfície humana (execução direta, AuthZ reavaliada no use case). O caminho conversacional TÉO continua exclusivamente via `governed_writes` PREPARE/ACT — nenhuma Action nova criada neste slice, nenhum bypass; confirmação conversacional nunca é autorização (a autoridade é sempre `_admin_room`/`_authorized_room`).
- **5.2 auditoria:** best-effort pós-commit documentado (perda → `logger.warning interaction_room_audit_failed`; resultado do domínio permanece verdadeiro — compatível com `gpt_actions._audit`). Compatibilidade: aceita para V2 com **gate de produção mantido** — auditoria obrigatória (outbox/retentativa) é pré-condição de rollout, não deste slice.
- **5.3 anchor legado:** remoção explícita do link `primary` de processo que casa `rooms.processo_id` está **bloqueada** (`legacy_anchor_locked`, 409) — a coluna continuaria resolvendo esta sala enquanto outra reivindicasse a claim primária → duas salas canônicas. Links `reference` e primários não-âncora seguem removíveis.
- **5.4 read-back:** `_assert_process_link` verifica o link persistido após o dual-write (`list_links` fresco; divergência → `OUTCOME_VERIFICATION_FAILED`).

## Testes — 76 passando (`test_interaction_rooms*.py` + novo `test_interaction_rooms_http.py` = 23 HTTP)

TestClient/ASGI real com middleware stub honrando o contrato `request.state.user` (ausente → 401). Cobertos: 401 authN, 422 DTO, bearer forwarding ao BFF, 404 sem vazamento de existência, 403 `glpi_link_required`/admin, 503 `upstream_unavailable`, 409 `primary_link_conflict`/`room_access_expansion_blocked`/`legacy_anchor_locked`, manage-sem-access administra com projeção mínima e não lê conteúdo, owner sem manage, multi-primary, referência restritiva, restore conflitante sem estado parcial, ausência de escrita quando negado, read-back autoritativo.

Full suite: **1715 passed, 10 failed** — idênticas ao baseline limpo (pré-existentes).

## TEST_NOT_RUN / PENDING

- Keycloak real (stub honra contrato; integração de middleware é de infra)
- GLPI/Helpdesk real (double controlado; mapeamento já provado)
- PostgreSQL real com V056 (migration não aplicada — gate de deploy preservado)
- Capabilities TÉO para as novas operações (E5 — façade OpenAPI curada não as inclui)
