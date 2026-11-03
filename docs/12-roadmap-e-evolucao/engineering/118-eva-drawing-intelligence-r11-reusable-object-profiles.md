# 118 — EVA Drawing Intelligence R11: Reusable Object Profiles & Relationships v1

**Status:** perfis de objetos implementados em `domain/drawing/object_profiles.py` + builder Application + integração aditiva em `analyze_product_drawing`; testes 4/4; deploy verificado (`R11_LOADED`). **Data:** 2026-11-03.

## 1. Modelos (domain puro, dataclasses)

`DrawingObject` (`object_id/type/attributes/document_identity/location/evidence_refs/relations/observation_state/verification_state/limitations/official`), `DrawingObjectRef`, `DrawingRelation` (`source/target/type/evidence/state/uncertainty`), `VerificationSpec`, `DrawingObjectSet` (identidade única + integridade referencial — `ValueError` em id duplicado/dangling ref).

## 2. Perfis

- **A BOM_OCCURRENCE** — `component_code/parent/bom_level/bom_path/consumption_quantity+unit` (oficial, EXPECTED);
- **B DRAWING_TABLE_ITEM** — `item_label/assembly_quantity/component_code_candidate/description/table_region` (observado, CANDIDATE);
- **C BALLOON**, **D DIMENSION** (`raw/numeric/unit/kind/geometry_linked:false`), **E GEOMETRY** — modelados;
- Separação explícita **consumo≠montagem≠cota** (cabo 500mm BOM ≠ qty 1).

## 3. Relações + verificações

`REPRESENTED_BY/REFERENCED_BY/POINTS_TO/DIMENSIONS/REPRESENTS` com `verification_state` — code_match nunca verifica (NOT_CHECKED+uncertainty). `PENDING_RULE_VALIDATION` p/ regras não aprovadas.

## 4. Integração

`payload["object_profiles"]` (v1, DRAFT, not_official) via `build_object_profiles(bom_occurrences, visual_observations)` — aditivo a `analyze_product_drawing`, sem segunda superfície.

## 5. Residuais

`component_rows=None` (tabela tipada do `understanding` ainda não alimenta a superfície — mapper pendente); balões/geometria modelados mas **não reconhecidos** pela pipeline atual (honesto).

## 6. R11.1 — integração das evidências visuais (2026-11-03)

- **Identidade**: `object_profiles.document_sha` agora recebe `extraction.document_hash` (= `audit.document_hash_sha256`); `document_identity` por objeto separa proveniência oficial (`official_source_ref` = `api-delpi:/products/{code}/structure` para BOM_OCCURRENCE) da identidade do PDF (objetos visuais).
- **Mapper**: `application/drawing/understanding_object_mapper.py` converte `drawing_understanding.v1` → `DrawingObjectSet` (linhas tipadas→DRAWING_TABLE_ITEM, `dimension_candidates`→DIMENSION, regiões `drawing_area/geometry/figure/view`→DRAWING_GEOMETRY, `balloons[]`→BALLOON só quando identificados). Ambiguidades (`quantity_not_numeric`, `component_code_not_code_shaped`, `association_unresolved`, `ambiguous_cells`) preservam evidência bruta e nunca geram relação.
- **Relações**: `REPRESENTED_BY` (BOM→item, code_match NOT_CHECKED), `REFERENCED_BY` (item→balão), `POINTS_TO` (balão→geometria, vínculo declarado), `DIMENSIONS` (cota→geometria, contenção espacial). Zero relações quando não há evidência, com limitações explícitas.
- **Wiring**: `product.drawing_understanding` alimenta `understanding["object_profiles"]` + `report["object_profiles"]` com a execução real (sem reprocessar OCR/SLANet); `product.drawing_analysis` aceita `parameters.understanding` (drawing_understanding.v1) — conflito de identidade documental exposto em `document_identity.match`.
- **Testes**: `test_drawing_object_profiles_r11_1.py` 16/16 + R11 4/4; regressão 635 pass / 1 fail pré-existente ambiental (`test_visual_perception_r7::test_normalize_box_json_safe` — numpy ausente no container, fora do diff).

## 7. R12 — investigação guiada pela estrutura oficial (2026-11-03)

- **`application/drawing/drawing_investigation.py`**: planner determinístico (`plan_investigations` — INV por BOM_OCCURRENCE com identidade/fonte/contexto) + executor (`execute_investigations` — I-01 código com MATCH_CANDIDATE/AMBIGUOUS/NOT_LOCATED, código só em carimbo não é componente, similares sem prova; I-02 atributos da linha com qty não-numérica→AMBIGUOUS; I-03 relações preservando todas as ocorrências repetidas; I-04 EXPECTED_COMPONENT_NOT_LOCATED/INCONCLUSIVE; I-05 UNMATCHED_DRAWING_CANDIDATE sem declarar erro de BOM).
- **Identidade**: sha incompatível → NOT_COMPARABLE fail-closed; `is_component_code`/`COMPONENT_CODE_RE` movidos ao domínio (fonte única, `_CODE_RE` de understanding virou alias).
- **Wiring**: `build_object_profiles(include_investigations=True)` no mesmo DrawingObjectSet; `payload["guided_investigations"]` versionado `guided_investigations.v1` em `product.drawing_analysis` e `product.drawing_understanding`.
- **Testes**: `test_drawing_investigation_r12.py` 15/15; suite 651 pass / 1 fail ambiental pré-existente.
