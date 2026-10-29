# EVA — ficha narrativa (EVA-CHARACTER-PROFILE-001)

Implementação da identidade narrativa aprovada da EVA sobre o contrato
compartilhado `shared/delpi_character_profiles`.
**Shared owns the structure; o MCP owns the character.** Conteúdo
exclusivamente ficcional (`FICTION_IDENTITY_ONLY`) — nenhum campo libera
tool, permissão, capability ou operação.

## Arquivos

| Artefato | Caminho |
|---|---|
| Camada de conteúdo (fonte única da prosa narrativa) | `engineering_app/content/eva_agent_intelligence.json` |
| Ficha estruturada (`build_eva_profile` / `get_eva_profile`) | `engineering_app/persona/eva_profile.py` |
| Serviço de projeção (`agent_directives` → `get_catalog`) | `engineering_app/application/eva/agent_intelligence_service.py` |
| Avatar oficial aprovado (JPEG 1024×1024) | `engineering_app/assets/characters/eva/avatar-v1.jpg` |
| Projeção pública commitada | `engineering_app/content/eva_public_profile.json` |
| Testes | `tests/test_eva_character_profile.py` |

## Integração MCP

`tool_get_catalog` (interface/mcp/tool_bridge.py) publica
`agent_directives` via `EvaAgentIntelligenceService.agent_directives()`:
diretivas operacionais (`read_first`, `provenance`, `boundaries`) +
`character` = `project_persona_context(ficha)` — identidade,
personalidade, comunicação, aparência, relações públicas e regras de
coexistência/conduta. A história completa e os eventos ficam fora do
contexto por orçamento; a ficha local é a fonte.

## Avatar

`avatar_status = OFFICIAL_AVATAR_APPROVED` somente enquanto o asset
referenciado existir no pacote (`persona/eva_profile.py` degrada para
`REFERENCE_NOT_OFFICIAL_AVATAR` se o arquivo estiver ausente). Integridade
fixada por SHA-256 no teste. **Regra visual aprovada: EVA não usa
óculos** — o campo `glasses` permanece vazio em todas as projeções.

## Relacionamentos

EVA declara (visibility `public`):

- `teo` → `family` — TÉO é o irmão mais novo; ligação fraternal
  carinhosa e protetora, sem rivalidade nem passado inventado.
- `delia` → `narrative_partnership` — parceria narrativa e profissional
  (não romântica, sem delegação técnica automática).
- `davi` → `friendship`; `vista` → `friendship`.
- `clara` → `colleagues`.

`validate_relationship_consistency` sobre as projeções públicas
commitadas reporta apenas `WARNING`s esperados: as fichas de
TÉO/DAVI/VISTA/CLARA não declaram a aresta de volta e DÉLIA ainda não
possui projeção pública no repositório (handoffs aos owners:
`transformometro-api`, `api-delpi`, `tv-dashboard-api`,
`controllership-finance-api`, `delia-api`). Nenhuma contradição
(`ERROR`).

## Distribuição pública do avatar — DELPI-CHARACTER-AVATARS-001-R01

- Publicação pública **ratificada pelo PO** (R01) — gate
  `_PUBLIC_DISTRIBUTION_ENABLED = True`.
- Rota owner-local: `GET /public/characters/eva/avatar/avatar-v1.jpg`
  (externa: `/apps/engineering-api/public/characters/eva/avatar/avatar-v1.jpg`).
- `jwt_middleware`: allowlist **exata** — apenas o path do asset e sua
  variante `/apps/engineering-api/…` foram adicionados a `_PUBLIC_PATHS`.
  Nenhum prefixo genérico (`/public/`, `/public/characters/`) é liberado.
- Fonte única: `appearance.avatar_status` + `avatar_reference` da ficha;
  filename deve ser idêntico ao basename da referência — caso contrário 404.
- Asset: `engineering_app/assets/characters/eva/avatar-v1.jpg`,
  1024×1024, sha256 `18d9e05f…e6fc`, status `OFFICIAL_AVATAR_APPROVED`.
- Cache `public, max-age=300`; `X-Content-Type-Options: nosniff`.
- Revogação: mudar `avatar_status` na ficha → 404 imediato.

## Descoberta MCP — DELPI-CHARACTER-AVATARS-002

`EvaAgentIntelligenceService.persona_context()` projeta
`avatar_distribution` (kind/url/version/mime_type/sha256) como chave
aditiva quando `avatar_status == OFFICIAL_AVATAR_APPROVED`. A URL compõe
`PUBLIC_BASE_URL` + root path + basename de `avatar_reference`; o sha256
é calculado do asset servido. Chave ausente quando o avatar não está
aprovado (safe-fail).
