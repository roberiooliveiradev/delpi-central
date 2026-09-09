# OTA production-grade — contratos e drifts congelados (F0)

Documento de evidência para o plano hub OTA. Não substitui SCHEMA.md / API-ROUTES.

## Modelo

| Conceito | Realidade `main` |
|---|---|
| Família | `firmware_key` (sem tabela própria) |
| Versão | linha `production_pulse.firmwares` (`id` UUID) |
| Source snapshot | `firmwares.source_text` (TEXT, cap 256 KiB) — owner da versão |
| Artifact | volume + `artifact_*` na versão (nullable em draft) |
| Lifecycle | draft (`published_at` NULL) · published · archived |
| Device link | `devices.firmware_key` → família |
| Installed sketch | resolução **exact-version** `(firmwareKey, installedFirmwareVersion)` |
| Legacy sketch | `devices.firmware_source` — fallback explícito; MFE não grava mais |
| Job | `firmware_id` → versão |

## Drifts doc × código

| Spec / UI | Código |
|---|---|
| Token one-time | TTL + re-check regenera token |
| Semver / anti-downgrade | igualdade string + `onlyOutdated` |
| `min_compatible_version` | persistido, não lido na elegibilidade |
| Job `completed` | CHECK existe; writer `maybe_finish_job` |
| Progresso `authorized = 5%` | removido — fase sem % fake |

## Invariantes P0

1. Artifact publicado imutável (`firmware_key`,`version` unique; sem PATCH de bytes).
2. Target/job terminal monotônico (report não ressuscita cancel).
3. Cancel limpa `artifact_token`.
4. Archive (`archived_at` / V012) bloqueia novos jobs.
5. MFE só via factories `Pp*` / `production-pulse-api`.

## Inventário P0 entregue × P1/P2 (F10)

| Item | Fase | Notas |
|---|---|---|
| PATCH metadata + archive | P0 | `PATCH /firmwares/{id}`, `POST …/archive` |
| Draft/create + attach + publish | P0 | V013; `POST publish=false`; `POST …/artifact`; `POST …/publish` |
| List vs detail DTO | P0 | list sem `sourceText`; detail com |
| Device source resolution | P0 | `GET /devices/{id}/firmware-sources` exact-version |
| Soft-disable IoT UI | P0 | `DELETE` → `enabled=false` |
| TopBar admin (`PpTopBar`) | P0 | `ProductionPulseShell`; operador sem TopBar admin |
| Upload só `.bin` + orphan delete | P0 | storage + publish rollback |
| Job finish `completed`/`failed` | P0 | `maybe_finish_job` |
| Cancel token + late report 409 | P0 | `deviceOtaInvalidTransition` |
| Hub `/firmware-links` + redirect jobs | P0 | soft poll; PpDataTable |
| TopBar 3 áreas (Painel / Hub / Operador) | P0 | Firmwares fora da TopBar |
| Create `/firmwares/new` + source/bin fields | P0 | progressive disclosure |
| Hub KPIs client-side | P0 | publicados/vinculados/updating/failed |
| Progress PHASE vs % | P0 | `formatOtaProgressDisplay` |
| Canvas Desvincular / Delete+Backspace | P0 | |
| Logs transição job/target / archive | P0 | sem token/bin |
| `source_sha256` provenance ino↔bin | **P1** | |
| Reject write `devices.firmware_source` | **P1** | API DEPRECATED write |
| Migrate legado source → catálogo | **P1** | EXPAND→MIGRATE→CONTRACT |
| SHA verify no ESP | **P1** | |
| Stuck target timeout | **P1** | |
| Admin download artifact | **P1** | |
| RBAC `firmware.*` fino | **P1** | hoje `devices.*` |
| Secret scan / redaction sketch | **P2** | |
| Semver / anti-downgrade policy | **P1** | |
| Métricas Prometheus OTA | **P1** | |
| Signed artifacts / anti-rollback HW | **P2** | |
| Abort/canary staged | **P2** | |
| Un-archive policy | **P2** | |

## Checklist lab L4 (F11)

- [ ] Publish versão → amarrar → disparar → ESP baixa → `updated` → job `completed`
- [ ] Cancel mid-download → late `updated` rejeitado; token inválido
- [ ] Job parcial (1 ok / 1 fail) → lifecycle `failed` ou `completed` conforme counts
- [ ] Archive versão → não cria job; histórico permanece
- [ ] `/firmware-jobs?branch=` redireciona preservando filial
- [ ] UI: authorized sem barra %; downloading com % real
