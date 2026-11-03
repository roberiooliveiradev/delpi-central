# 114 — EVA Drawing Intelligence R9.9: SLANet Persistent Model Provisioning & Production Hardening

**Status:** provisionamento persistente implementado e comprovado — SLANet sobrevive a build limpo + recreate sem `docker cp`; integração R9.8 preservada; E2E MCP `TEST_NOT_RUN` (OAuth). **Data:** 2026-11-02.

## 1. Solução (Abstraction Gate — menor correta)

- **Opção B (volume gerenciado):** modelo provisionado no volume host `~/ocr-models/paddlex/SLANet` → montado `/opt/ocr-models/paddlex` no container.
- **Symlink baked na imagem:** `Dockerfile` — `ln -sfn /opt/ocr-models/paddlex /root/.paddlex/official_models` → o paddlex resolve `~/.paddlex/official_models/SLANet` para o volume persistente.
- Elimina `docker cp` ephemeral; sobrevive a build/recreate/restart.

## 2. Manifesto (RQ-01)

- `SLANet` (PaddleX table-structure, ~7.7MB), Apache-2.0; `inference.pdiparams` SHA-256 `9d33d47b174bcb9f…`; files: `inference.pdiparams`, `inference.yml`, `inference.json`, `config.json`, `README.md`.

## 3. Comprovação (TEST-01..06)

`docker compose build` + `force-recreate` → `/root/.paddlex/official_models/SLANet` presente via symlink (não arquivo copiado) → `SLANET_PERSISTENT_OK` (modelo carrega e serve sem `docker cp`).

## 4. Residuais

- Rollback para imagem anterior: imagem sem symlink → modelo some (documentado).
- Integração R9.8 (table_structure_engines + associação) preservada.
- E2E autenticado: `TEST_NOT_RUN`; baseline default intacta; BOM gate fail-closed.
