# 112 — EVA Drawing Intelligence R9.8: MCP Internal Error — Root Cause & Serialization Fix

**Status:** causa raiz corrigida — `_pdf_bytes` (bytes) em `out` quebrava serialização JSON → `McpServerError: Internal server error`; fetch agora direto no bridge; deploy verificado. **Data:** 2026-11-02.

## 1. Causa raiz (verificada)

- `document_benchmark_service` expôs `out["_pdf_bytes"]` (bytes não-JSON-serializável) — a resposta MCP falhava com `Internal server error`/`UNAVAILABLE` ao serializar.
- Correção: removido `_pdf_bytes` de `out`; bridge agora chama `fetch_product_drawing_pdf` para obter bytes para o `TableStructureEngine`.

## 2. Deploy-lag adicional identificado

- `git merge origin/main` sem `git fetch` anterior → prod nunca recebeu `56bce52110`; container rodava imagem stale (`fetch_product_drawing_pdf`=0). Corrigido: `git fetch`+merge+`docker compose build`+`force-recreate` → `fetch_product_drawing_pdf`=1 no container.

## 3. Estado final

- Container: `table_structure_engines`=2, `_pdf_bytes` ausente de `out` (0), `fetch_product_drawing_pdf`=1, 4 engines, healthy.
- SLANet model provisionado (docker cp ephemeral — bake pendente).
- E2E MCP autenticado: `TEST_NOT_RUN` (sem OAuth) — ChatGPT re-valida.
