# Engineering NC — T7: Production Handoff, Deployment & Runtime Evidence

Data: 2026-10-29 · Executor: Devin · Missão: `ENGINEERING.NC.T7` (Plano Mestre 48)
Ambiente: produção — `https://minhadelpi.com.br` (`srv-api` / `192.168.1.237`)

## 1. Âncoras

| Item | Valor |
|---|---|
| BASE_HEAD | `160faa2e53` |
| TARGET_SHA | `0a60c3a576` — hardening writer único + wiring prod |
| HEAD produtivo (`srv-api`) | `0a60c3a57` — idêntico em código funcional |
| Deploy | canônico `up-prod-sequential.sh --build` (engineering-api, api-delpi, engineering MFE) |
| DATABASE_STATE | **EXISTING_COMPATIBLE** — V001–V009 com checksums idênticos; V010–V011 de outro domínio intactas |

## 2. Inventário produtivo (T7-A — READ-only)

| Item | Estado |
|---|---|
| Cluster/database | `delpi-postgres-plugins` / `plugins_hub` |
| Schema | `engineering` — 5 tabelas NC + `lmp_problem_tags` + `schema_migrations` |
| Migrations | V001–V009 aplicadas 2026-07-27, checksums = arquivos do repo |
| Trigger append-only | `trg_lmp_nc_history_no_mutation` + `prevent_lmp_nc_history_mutation()` ativas |
| Principais | apenas `plugins_user` (compartilhado) antes do T7 |
| Baseline dataset | 53 NC · 63 histórico · 53 produtos · 50 vínculos tag · 10 tags catálogo · todas `done` · max(updated_at) 2026-10-27 · md5(ids) `3e7cd61c…` |
| Consumidores legados | api-delpi (`ENGINEERING_LMP_NC_WRITE`), dashboard-lmps MFE |
| Backup pré-handoff | `plugins-hub-nc-pre-t7-20261029232637.dump` em `~/backups` |

## 3. Ownership e aprovação operacional (T7-B)

- Owner funcional alvo: Engineering API — ratificado por ADR-NC-OWNERSHIP (doc 47)
  e decisão de Coordenação (missões T6.R1/T7).
- Aprovação operacional: execução pelo operador/Product Master via mecanismo
  canônico de deploy (`AGENTS.md` — local → push → pull → build sequencial em
  srv-api); ACT condicionado a pacote PREPARE completo, que foi verificado:
  schema compatível, backup consistente, grants mínimos, sequência de writer
  único sem janela dual, rollback ensaiável.
- Grants/roles: `engineering.access` (4 usuários legítimos) já existia na Core
  prod; `engineering.manage` inexistente e não utilizada.

## 4. Principal dedicado e grants (T7-C)

| Item | Implementação |
|---|---|
| Role | `eng_nc` — criada por `engineering-api/db/eng_nc_grants.sql` (senha gerada no servidor, armazenada só em `infra/.env` prod — nunca no repo) |
| Grants | USAGE no schema; SELECT/INSERT/UPDATE/DELETE nas 4 tabelas NC; SELECT/INSERT no catálogo de tags; EXECUTE na função da trigger |
| Revogações explícitas | TRUNCATE/TRIGGER/REFERENCES e UPDATE/DELETE no catálogo |
| Negativas provadas | `metallographic_reports` (mesmo schema) → permission denied; `quality.*` → denied; TRUNCATE → denied; SELECT NC → 53 |
| Guarda de credencial | `nc_composer` rejeita `ENG_NC_DB_USER == PLUGINS_DB_USER` |

## 5. Handoff writer único (T7-D)

Sequência executada 2026-10-29 ~23:35 UTC:

1. Baseline consistente capturado (md5 de IDs, contagens, max updated_at).
2. Backup `pg_dump -Fc` das 5 tabelas NC.
3. Grants aplicados (aditivo, sem risco).
4. `LMP_NC_WRITE_MODE=frozen` + recreate api-delpi → **writer legado
   congelado primeiro** (sem janela de dois writers).
5. `ENG_NC_*` em `infra/.env` + recreate engineering-api → novo writer.
6. Correção de senha divergente (escaping de `psql -v` → `format()` na role).
7. Smoke controlado: CREATE → UPDATE (`expected_updated_at`, status→in_progress)
   → HISTORY (diff real old/new) → DELETE — registro sintético autorizado,
   totalmente revertido.
8. Integridade pós-handoff: **idêntica ao baseline** (53/63/53/50/10, md5 igual,
   max(updated_at) inalterado). Tag de teste removida do catálogo.

## 6. Hardening WRITE legado (T7-E)

- `ENGINEERING_LMP_NC_WRITE`: `api-delpi.access` removida — antes, **14
  usuários** podiam escrever NC; agora apenas `dashboard-lmps.nc.write` (4,
  os mesmos que possuem `engineering.access`).
- `LMP_NC_WRITE_MODE=frozen`: CREATE/UPDATE/DELETE/IMPORT legados retornam
  **409 explícito** apontando a Engineering API — verificado em prod.
- Legacy READ intacto (200) — dashboard LMP e contratos de leitura preservados.

## 7. Validação produtiva

### 7.1 API (token humano real, identidade smoke autorizada)

| Verificação | Resultado |
|---|---|
| `GET /v1/nonconformities` | 200 — dados reais (53 registros) |
| `GET /v1/nonconformities/indicators` | 200 — streak 8 dias, max 55 |
| `GET /v1/nonconformities/{id}/context` | 200 — facts OV/produto via api-delpi |
| `POST /v1/nonconformities/prepare` | 200 — "nada foi gravado" (zero side effects) |
| CREATE/UPDATE/HISTORY/DELETE smoke | ciclo completo + diff de auditoria |
| Legacy `GET lmps/nonconformities` | 200 |
| Legacy `POST` (WRITE) | **409 frozen** |
| Sem token | 401 |
| Token sem `engineering.access` | 403 (eng-api) e 403 (legado) |

### 7.2 Browser real (Playwright, SSO prod, identidade `deploy01.smoke`)

5/5 desktop: hero+filtros+indicadores, filtros reagem, detalhe via tabela,
formulário com validação de ocorrência, bridge legado `/lmps/nonconformities`.

### 7.3 EVA/MCP

- Endpoint `/apps/engineering-api/mcp` live e enforcement RFC 9728 correto
  (401 + `resource_metadata` + audience exigida).
- 6 tools READ + PREPARE registradas no mesmo artifact testado (dev: 83 testes
  MCP, live dev). `DESTRUCTIVE_ACT_TOOLS` vazio — **ACT desabilitada**.
- Chamada tool-level em prod requer fluxo OAuth MCP completo (client
  `mcp-engineering` + consentimento humano) — evidência parcial, registro
  honesto; tools já PROVEN em dev e o enforcement de audience está ativo.

## 8. Rollback

- Imagens anteriores: tags Docker anteriores ao rebuild (registry local).
- `.env` backup: `infra/.env.pre-t7-*.bak` no servidor.
- Reversão: remover `LMP_NC_WRITE_MODE`/`ENG_NC_*` do `.env` + recreate
  api-delpi/eng-api → writer volta ao legado; dados preservados (mesmo schema,
  nenhuma migration aplicada); dataset NC intacto (md5 verificado).
- Writes do novo writer: todos compatíveis com o schema legado — sem replay
  necessário ao reverter (o histórico do smoke foi removido com o registro).
- `eng_nc` pode permanecer sem uso ou ser dropped (`DROP ROLE eng_nc`).

## 9. Riscos e pendências

| Item | Estado |
|---|---|
| Consumidores de escrita legada | 4 usuários `dashboard-lmps.nc.write` redirecionados ao Portal NC — botões legados recebem 409 explícito (comportamento desenhado) |
| Telemetria de chamadas NC WRITE legadas | monitorar logs api-delpi 30–60d (TO_INVENTORY) |
| `deploy01.smoke` na Core | usuário Core sem KC login permanece (precedente doc 44) |
| `nc-t7.neg` | nunca provisionada na Core — removida do KC |
| Role Core grant de smoke | mantida (sem usuário KC — inerte) |
| EVA tool-call em prod | pendente de fluxo OAuth MCP interativo |
| Import replace-total | `ENG_NC_IMPORT_REPLACE_ENABLED=false` em prod — protegido |
| Collation mismatch plugins_hub | aviso pré-existente do cluster — fora de escopo |

## 10. Critérios de aceite T7

| ID | Status | ID | Status |
|---|---|---|---|
| T7-01 reancoragem | PASS | T7-16 import protegida | PASS |
| T7-02 inventário prod | PASS | T7-17 EVA READ | PASS (endpoint+registro; call pendente OAuth) |
| T7-03 ownership | PASS | T7-18 EVA PREPARE s/ writes | PASS |
| T7-04 schema/migrations | PASS | T7-19 EVA ACT off | PASS |
| T7-05 dados preservados | PASS | T7-20 integridade dataset | PASS (md5 idêntico) |
| T7-06 principal dedicado | PASS | T7-21 LMP dashboard | PASS |
| T7-07 grants mínimos | PASS | T7-22 consumidores legados | PASS |
| T7-08 writer único | PASS | T7-23 browser real | PASS (5/5 prod) |
| T7-09 hardening WRITE legado | PASS | T7-24 negativas segurança | PASS (401/403/409/credencial) |
| T7-10 eng-api NC prod | PASS | T7-25 rollback | PASS (preparado+reversível) |
| T7-11 Core AuthZ | PASS | T7-26 monitoramento | PASS (baseline+telemetria doc.) |
| T7-12 S2S facts | PASS (context 200) | T7-27 documentação | PASS (este doc) |
| T7-13 Portal NC prod | PASS | T7-28 evidências↔SHA | PASS |
| T7-14 CRUD validado | PASS | T7-29 ACT autorizado | PASS (canônico+pacote verificado) |
| T7-15 histórico/auditoria | PASS | T7-30 postconditions | PASS |

## 11. Commits

| SHA | Conteúdo |
|---|---|
| `0a60c3a576` | Hardening writer único + wiring compose prod + grants + testes |
| (doc commit) | Este documento + fix `format()` no script de grants |

**SHA funcional em produção:** `0a60c3a57` (srv-api checkout).
