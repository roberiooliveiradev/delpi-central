# 113 — EVA Drawing Intelligence R9.8: MCP Internal Error — numpy Serialization Root Cause

**Status:** causa raiz final identificada e corrigida — `numpy.float32`/`ndarray` nos resultados SLANet quebrava `PydanticSerializationError` no serializer MCP → `McpServerError: Internal server error`; deploy verificado. **Data:** 2026-11-02.

## 1. Causa raiz (verificada via logs sanitizados)

`docker logs` mostrou: `PydanticSerializationError: Unable to serialize unknown type: numpy.float32` — `structure_score`/`bbox` do SLANet chegam como tipos numpy; `result.model_dump(mode="json")` falha. Duas serializações separadas já corrigidas: `_pdf_bytes` (bytes em `out`) + esta (`numpy.float32` nas células/tables).

## 2. Correção

`_to_native(obj)` em `engine_adapters` — converte `np.generic→.item()`, `np.ndarray→list`, recursivo em dict/list. Aplicado em `structure_score` e `bounding_box_px` do `TableStructureEngine`. 11/11 testes.

## 3. Deploy

fetch+merge+`docker compose build`+`force-recreate` → container tem `_to_native`=5, código baked correto, healthy.

## 4. Estado MCP

`analyze(product.drawing_understanding)` agora produz `table_structure_engines` serializável (tipos nativos Python). E2E autenticado: `TEST_NOT_RUN` — ChatGPT re-valida.
