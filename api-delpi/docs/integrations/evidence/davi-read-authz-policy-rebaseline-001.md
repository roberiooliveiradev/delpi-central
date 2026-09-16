# DAVI READ Authorization Policy

> **Decision ID:** `DAVI-READ-AUTHZ-REBASELINE-001`
> **Status:** `RATIFIED` (Architecture / Governance rebaseline)
> **Owner surface:** DAVI × API DELPI external capabilities
> **Does not weaken backend AuthZ.**

```text
Documentation ≠ runtime proof of a specific deploy SHA
```

## Invariants

1. **DAVI capability ≤ authenticated user capability**
2. DAVI has **no** independent business permissions (`DAVI_LOCAL_RBAC = FORBIDDEN`)
3. Authenticated end-user identity is propagated to the canonical backend
4. Canonical backend AuthZ is the **final** authority
5. Query attributes (`branch`, `code`, `warehouse`, …) are **filters** unless the backend itself uses them in its policy
6. DAVI must not invent branch / object / department / role / customer / supplier AuthZ
7. Backend-authorized internal READ may be processed by DAVI unless an **explicit** canonical prohibition exists
8. Model-safe projection / minimization remains mandatory
9. READ policy does **not** authorize WRITE

## Forbidden DAVI AuthZ modes

```text
DAVI_BRANCH_AUTHZ = FORBIDDEN
DAVI_OBJECT_LEVEL_AUTHZ = FORBIDDEN
DAVI_PRODUCT_AUTHZ = FORBIDDEN
DAVI_DEPARTMENT_AUTHZ = FORBIDDEN
DAVI_ROLE_TITLE_AUTHZ = FORBIDDEN
DAVI_CUSTOMER_AUTHZ = FORBIDDEN
DAVI_SUPPLIER_AUTHZ = FORBIDDEN
DAVI_CONTEXT_BASED_PERMISSION_INFERENCE = FORBIDDEN
```

## Stock semantics

```text
branch = query filter
authorized user may query stock across branches
available_quantity is domain-provided (not recomputed by DAVI)
```

## EXECUTION_DRIFT (invalidated)

Prior DAVI assumptions requiring `NEEDS_BRANCH_AUTHZ_EVIDENCE` / `DAVI-GOV-STOCK-001` branch permission families for DAVI eligibility are **invalidated**.

Supersedes family-only external-processing and taxonomy-absence universal blockers from `DAVI-DYNAMIC-READ-005` / `DAVI-GOV-READ-001` when those were the sole reason for quarantine.

## Flow

```text
Authenticated end user
  → DAVI Agent
  → DAVI App / MCP (3 tools)
  → API DELPI / canonical use case
  → canonical backend AuthZ
  → authoritative source
  → model-safe projection
```
