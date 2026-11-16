# Root cause — entity sufficiency

## Defect

Presentation aggregation could mark an obligation SATISFIED when an
authoritative metric shared material filters (e.g. `status=ativo`) but the
owner vocabulary belonged to a different business entity (orders/products
vs processes).

## Causal chain

```text
MaterialObligation (delivery=aggregation, evidence_source=summary|analysis|view)
  → _attempt_demonstrates_anchored presentation bypass
  → matched filter/metric without entity congruence
  → FALSE SATISFIED / COMPLETE risk
```

## Fix (canonical owner)

In `semantic_capability_support.py`, under aggregation presentation path,
require `_attempt_business_entity_congruent` using mechanical
`entity=` / `entity_kind=` tokens from `required_scope` intersected with
attempt anchor tokens. Empty declared entity set fails closed.

## Evidence

- Directed S2/S3 entity negatives + G2 positive live
  `or-qwen14b-aca443baae46`: SATISFIED with `entity=process`, `teo.read`, 109.
