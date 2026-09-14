# Core — S2S effective access by Keycloak subject

Owner: `core-api`  
Consumer (future): `tv-dashboard-api` MCP boundary  
Introduced: TV-GPI-004B4

## Capability

Resolve **Core-authoritative** effective platform permissions for a Keycloak
subject, for an authenticated **internal** service.

```text
trusted service
→ subject (Keycloak sub / UUID)
→ Core user by id == sub (no email fallback)
→ PermissionResolver
→ { userId, keycloakSubject, permissions, isSuperadmin }
```

## Endpoint

| Field | Value |
|---|---|
| Method / path | `GET /integrations/effective-access/subjects/{keycloak_sub}` |
| operationId | `get_effective_access_by_subject` |
| Auth | `CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN` via `Authorization: Bearer` **or** `X-Delpi-Service-Token` |

`keycloak_sub` must be a UUID. It is the same identifier Core already uses as
`users.id` (Keycloak `sub`).

### Auth model (CALLER_BINDING)

This endpoint **does not** accept `CORE_API_INTEGRATIONS_SERVICE_TOKEN`.

That shared integrations secret is held by multiple plugins. Full effective
permission dumps for arbitrary subjects require a **dedicated** secret so ops
can issue the capability only to the intended consumer (e.g. TV MCP).

### Response `200`

```json
{
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "keycloakSubject": "550e8400-e29b-41d4-a716-446655440000",
  "permissions": ["tv-dashboard.read", "tv-dashboard.write"],
  "isSuperadmin": false
}
```

Empty `permissions` with `200` means the subject is known and has no grants —
**not** an auth failure and **not** “Core unavailable”.

### Errors

| HTTP | code | Meaning |
|---|---|---|
| 401 | `unauthorized` | Missing service token |
| 403 | `forbidden` | Invalid token **or** dedicated token not configured |
| 400 | `validation_error` | Malformed `keycloak_sub` |
| 404 | `identity_not_found` | Subject not linked to a Core user |
| 503 | `authorization_unavailable` | PermissionResolver / backend failure |
| 500 | `effective_access_failed` | Unexpected internal error |

## Non-goals

- Not a substitute for end-user `GET /me`
- Does not accept caller-supplied permissions/roles/email as authority
- Does not create users
- Does not implement MCP / TV AuthZ

## Future MCP ACT

```text
no authoritative Core decision (503 / transport failure)
→ NO ACT
```

Distinguish `permissions: []` (deny) from `authorization_unavailable` (fail closed).
