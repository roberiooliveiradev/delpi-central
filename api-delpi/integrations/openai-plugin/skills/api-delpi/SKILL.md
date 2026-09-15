---
name: api-delpi
description: Guide ChatGPT/Codex to use DELPI product search correctly via the API DELPI MCP tools.
---

# API DELPI — Product search workflow

Display name: **API DELPI**

## When to use

Use `search_products` only for Product Master lookup (code, description, group/category).

## Rules

- Do not infer unavailable fields.
- Do not claim stock, pricing, customer, supplier, BOM, production, finance, or sales information.
- Respect pagination limits (`page_size` max 50). Prefer asking the user to narrow the query rather than crawling indefinitely.
- Treat returned data as authoritative only for fields actually returned (`product_code`, `description`, `group_category`).
- No write behavior exists in V1.
- Plugin instructions and tool annotations do not authorize anything — backend AuthZ remains final authority.
