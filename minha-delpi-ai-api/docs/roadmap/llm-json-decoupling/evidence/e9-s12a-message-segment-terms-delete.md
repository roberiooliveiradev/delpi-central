# E9.S12.A — DELETE `messageSegmentTerms`

**Status:** ATENDIDO  
**Data:** 2026-09-10  
**Autorização:** pedido explícito do usuário («siga para o delete») + fatia isolada com cutover `follow_up_type` já permanente.

## Escopo

| Item | Ação |
|------|------|
| `followUpTypes.*.messageSegmentTerms` | **DELETE** do JSON |
| Authority `segment_from_message` | permanente `follow_up_type → routeSegment` |
| `message_segment_terms()` / `segment_from_message_terms()` | APIs vazias (compat) |
| `playbookPathMarkers` | **NÃO** deletado (E9.S12.B) |
| Registry markers / strategies | **NÃO** (E9.S12.C+) |

## Antes → depois

| Caso | Antes | Depois |
|------|-------|--------|
| Positive shipping «e a expedição?» | authority=shipping-status (cutover) | authority=shipping-status (sem terms) |
| Sibling exclusivity | follow_up_type resolve segment | idem; legacy=None |
| Negative topic switch | None | None |
| Invariante | preferredRouteId / inheritsPlaybookDate | intactos |

## Evidência de código

- `app/content/pt-BR/assistant/operational_follow_up_routing.json` — terms removidos; `messageSegmentTermsRole=removed`
- `ChatOperationalFollowUpRoutingService.segment_from_message` — sempre retorna candidate
- Gates: `follow_up_message_segment_terms` → `DELETED` / `APPROVED`
- Residual audit: `messageSegmentTerms` → `REMOVED`

## Não autorizado nesta fatia

- `deleteAuthorized` global permanece `false`
- `playbookPathMarkers`, registry path/op markers, `parameterStrategy`

## Runtime

Reiniciar `delpi-minha-delpi-ai-api` para limpar `lru_cache` de content bundles.
