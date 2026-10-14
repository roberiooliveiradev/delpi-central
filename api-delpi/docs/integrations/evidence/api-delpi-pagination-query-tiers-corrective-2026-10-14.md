# API DELPI pagination factory corrective — 2026-10-14

Owner: `api-delpi` HTTP interface pagination. Root cause: two literal `page_size=Query(...)` declarations bypassed the centralized `PAGE_SIZE_QUERY` tier policy and failed the existing integration gate.

Contracts preserved:
- Legacy `gpt_search_products` remains default `page_size=50`, min 1, max 50; only the declaration now references canonical tier `page_50_50`.
- `list_lancamento_notas_fiscais_received_invoices` remains default `page_size=25`, min 1, max 100; the existing explicit HTTP 422 error check stays in place as defense in depth, although out-of-range requests are now rejected early by FastAPI Query validation. That error-body difference is a **BEHAVIORAL** risk requiring HTTP consumer smoke before deployment.

Two new tiers were added to `pagination_tiers.json`, with two corresponding entries in `pagination_inbound_inventory.json` (118→120). Existing policies, data outputs, AuthZ decorators, openapi operation IDs, and owner gateways unchanged. New tests assert defaults and caps and preserve the existing no-literal-Query gate.

Evidence: local pytest **TEST_NOT_RUN** due container DNS, GH Actions API tests **PENDING** at commit; deploy and HTTP integration **TEST_NOT_RUN**. No authorization to merge/deploy production.
