# Product Usage Knowledge — `product_guide_v1`

Fundação governada de conhecimento vivo de uso do Transformômetro /
Portal Transforma+. Uma única authority de orientação de produto para
TÉO hoje e para a Ajuda do Portal no futuro.

## Ownership

| Conceito | Owner | Fonte |
|---|---|---|
| Product Usage Guidance | transformometro-api | `tm_app/content/product_guides/*.json` |
| Contrato vivo (capabilities, execution_policy) | transformometro-api | `get_catalog` / `capability_descriptors` |
| Estado de domínio | transformometro-api | leituras autoritativas (`get_process_context` etc.) |
| Metodologia | transformometro-api | `teo-method-playbooks` / `get_methodology_guide` |

`product_guide_v1` é **PRODUCT_USAGE_GUIDANCE** — `authority` fixa
`GUIDANCE_NOT_DOMAIN_TRUTH`. Em conflito com schema/policy o contrato
vivo vence; o guide nunca autoriza, nunca prova estado e nunca redefine
execution_policy.

## Arquitetura

```text
content/product_guides/*.json   (versioned files — a única fonte)
        │
        ▼
ProductGuideRegistry            (load + schema validation + cross-refs)
        │
        ▼
ProductGuideService             (application service — read-only)
        │
        ├─ gpt_get_product_guide  (GET /gpt-actions/v1/product-guide)
        └─ get_product_guide      (MCP tool, READ)
```

Sem banco, sem embeddings, sem busca vetorial — arquivos versionados +
loader + validação (Abstraction Gate).

## Contrato `product_guide_v1`

Campos: `schema`, `id` (== filename), `title`, `summary`,
`authority: GUIDANCE_NOT_DOMAIN_TRUTH`, `purpose`, `use_when[]`,
`do_not_use_when[]`, `how_to_use[]`, `field_guidance[]`
(`field` + `guidance` + `contract_ref?`), `quality_rules[]`,
`common_mistakes[]`, `related_topics[]`, `capability_refs[]`,
`contract_refs[]`, `source_refs[]` (`ref` + `classification`
PROVEN|INFERRED|PROPOSED), `agent_guidance?`.

Sections no read: `overview` | `when_to_use` | `how_to_use` |
`field_guidance` | `quality` | `relationships` | `all`.
`topic` omitido → índice. Unknown topic/section → erro tipado
(404/400), nunca fallback silencioso.

## Relação com a Help do Portal

- CURRENT HELP SOURCE: copy espalhada em componentes (tooltips,
  empty states, `emptyStateUi.ts`) — HARDCODED/MULTIPLE.
- TARGET SHARED AUTHORITY: este registry → TÉO (hoje) e Portal Help
  (futuro). MIGRATION REQUIRED: LATER — sem migração de UI nesta fase.

## Relação com methodology e catalog

`get_product_guide` = como usar o produto. `get_methodology_guide` =
método/análise. `get_catalog` = contrato técnico. São autoridades
disjuntas; o guide referencia capabilities por `capability_refs`
(ids do catálogo), nunca duplica schemas/enums/policies.

## Drift rules

- `related_topics` devem existir no registry (validado em load).
- `capability_refs` devem existir no catálogo vivo — drift quebra o
  load (fail-closed) e o teste de contrato.
- `source_refs` exigem classificação PROVEN|INFERRED|PROPOSED —
  hipótese não vira regra oficial sem revisão.

## Como adicionar um tópico

```text
ADD GUIDE  → novo tm_app/content/product_guides/<id>.json
VALIDATE   → schema + registry (pytest tests/test_teo_product_guide.py)
TEST       → topic aparece no index; sections corretas
REVIEW     → source_refs/classification revisados
DEPLOY     → restart transformometro-api
VERIFY     → get_product_guide(topic=<id>) no MCP/Actions
```

Novo tópico = conteúdo + validação; sem código novo.
