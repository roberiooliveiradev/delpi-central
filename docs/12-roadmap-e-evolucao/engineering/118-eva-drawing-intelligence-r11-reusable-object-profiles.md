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
