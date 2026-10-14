# TÉO — GPT Actions schema corrective (2026-10-14)

Owner `transformometro-api`. Existing `GptImprovementPackageBody` already owns typed process/instance/baseline/scenario inputs. `GptGovernedOperationBody` now reuses those schemas via deepcopy; no new catalog, action, RBAC, or runtime business rule. `instancia_contexto_v1` continues to be validated by the canonical domain validator, but is explicitly marked as an intentional opaque Builder object in both existing projections.

Consumer: Custom GPT schema importer. Change: typed OpenAPI projection, non-breaking to existing valid producer inputs, with stricter model constructibility. Tests: source parity and artifact budget in TÉO workflow, cross-repo Architecture Enforcement. Live GPT Builder import: TEST_NOT_RUN. No deploy or publication authorized.
