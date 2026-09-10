# E8.S2 — Skill catalog cleanup (hints neutros)

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** G (plano 08)  
**Harness:** `tests/unit/domain/services/test_e8_s2_skill_catalog_cleanup.py`

## Veredito

```text
SKILL_RUNTIME_ENDPOINT_HINT_DEPENDENCY = ZERO (catalog seed)
PATHISH_HINTS = 0
POLICY_PRESERVED = PASS
ENABLEMENT_VIA_ACTIONS_NOT_HINT = PASS
```

## Delta `executionPathHint`

| key | Antes | Depois |
|-----|-------|--------|
| `sql` | `POST /data/sql` | `sql_execution` |
| `drawing-analysis-delpi` | `GET /products/{code}/analyser` | `product_analyser` |
| `quality-action-plans-delpi` | `/quality/action-plans` | `quality_action_plans` |
| `document-vision-delpi` | `ChatDocumentVisionService` | `document_vision` |

Descriptions de `sql` / `drawing-analysis` deixam de citar path HTTP como authority; disponibilidade continua via Action Catalog + `executionDerivedKey` / tokens Python.

## KEEP

- `policyFile`, aliases, examplePrompts, labels
- `executionDerivedKey=sqlExecutionAvailable`
- Gates path em `ChatSkillRegistry` (`/data/sql`, `/analyser`, …) — runtime, não catálogo editorial

## Nota DB

Linhas já bootstrapadas em `ai_chat_skill_catalog` podem manter hint antigo até sync/admin update; seed JSON é a fonte de verdade para novas instalações.

## Próximo

**E8.S3** — help/capabilities: disponibilidade via runtime allowed actions (não path estático em `requiredActions`).
