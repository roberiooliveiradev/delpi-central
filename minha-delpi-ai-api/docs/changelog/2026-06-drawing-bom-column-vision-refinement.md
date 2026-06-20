# Changelog — BOM colunar, refinamento de visão e assertividade 95% (Fase 15.8)

**Data:** 20/06/2026  
**Escopo:** skill desenho orquestra visão do chat base; usuário não envia print/zoom.  
**Playbook:** [`playbook_bom_colunar_visao_skill_desenho.md`](../roadmap/melhorias/playbook_bom_colunar_visao_skill_desenho.md)

---

## Contexto

Regressão `90263149`: OCR lia QTD da **descrição** (`6,35`, `6 PINOS`, `00120` mm), gerando críticos BOM falsos. O fix jun/2026 (`ChatDrawingBomQuantityAssertivenessService`) evita crítico, mas **pending** não substitui leitura correta da coluna QTD.

## Diretriz

| Camada | Responsabilidade |
|--------|------------------|
| Chat base (`document-vision-delpi`) | OCR, regiões, `tables[]` genérico, `TableCellRefinementPort` — **sem** vocabulário BOM/QTD/SG1010 |
| Skill (`drawing-analysis-delpi`) | Interpreta tabela como BOM; compara × SG1010; orquestra refinamento; assertividade |
| Usuário | Anexa PDF uma vez — **não** participa do loop de leitura |

Fronteira detalhada: playbook § 0.

---

## Entregas

### 15.8.0–15.8.3 (commits anteriores)

Port genérico, interpretação colunar, OCR por célula, orquestração `ChatDrawingBomVisionRefinementService`, smoke E2E `scripts/smoke_drawing_90263149_chat_e2e.py`.

### 15.8.1b — Inferência de colunas (cabecalho OCR corrompido) ✅

| Artefato | Mudança |
|----------|---------|
| `ChatDrawingBomTableInterpretationService` | Resolução exato → fuzzy → inferência por perfil colunar + layout padrão |
| `drawing_stamp.json` → `bomColumnInference` | Layouts 4/5/6 colunas, edit distance, thresholds |
| `ChatDrawingPatternsService` | Loaders `bom_column_inference_rule`, `bom_column_default_layout` |
| `drawing_validation.json` | `criticalRequiresQuantitySource` inclui `column_inferred` |
| `ChatDrawingBomQuantityAssertivenessService` | Trust para `column_inferred` |
| Testes | Fixture cabeçalho corrompido + corpo legível — QTD colunar, não da descrição |

**Limitação:** PDF `90263149` live ainda tem corpo BOM fragmentado no OCR regional; inferência de colunas exige corpo legível. Próximo: refinamento célula (15.8.2) no pipeline live.

### Pendente (15.8.4–15.8.6)

Assertividade gate batch, policy follow-up, `--assertiveness-gate` — ver playbook § 5.

---

## Gates

```bash
cd minha-delpi-ai-api

.venv/bin/python -m pytest \
  tests/unit/domain/services/test_chat_drawing_bom_table_interpretation_service.py \
  tests/unit/domain/services/test_chat_drawing_bom_quantity_assertiveness_service.py \
  tests/unit/domain/services/test_chat_drawing_validation_90263149.py -q

# E2E chat (container) — gate QTD: 0 críticos bom_quantity_mismatch
docker exec -e SMOKE_BASE_URL=http://delpi-gateway -e PYTHONPATH=/app \
  delpi-minha-delpi-ai-api python /app/scripts/smoke_drawing_90263149_chat_e2e.py
```

---

## Relacionado

- Assertividade QTD jun/2026: `ChatDrawingBomQuantityAssertivenessService`
- Onda 15.7 retry confiança: `ChatDrawingExtractionQualityRetryService`
