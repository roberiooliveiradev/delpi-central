# CLARA — ficha narrativa (CHARACTER-PROFILE-CLARA-001)

Implementação da identidade narrativa aprovada (V0.2) da CLARA sobre o
contrato compartilhado `shared/delpi_character_profiles`.
**Shared owns the structure; o MCP owns the character.** Conteúdo
exclusivamente ficcional (`FICTION_IDENTITY_ONLY`) — nenhum campo libera
tool, permissão, capability ou operação.

## Arquivos

| Artefato | Caminho |
|---|---|
| Camada de conteúdo (fonte única da prosa narrativa) | `controllership_finance_app/content/clara_agent_intelligence.json` |
| Ficha estruturada (`build_clara_profile` / `get_clara_profile`) | `controllership_finance_app/persona/clara_profile.py` |
| Serviço de projeção (`agent_directives` → `get_catalog`) | `controllership_finance_app/application/clara/agent_intelligence_service.py` |
| Avatar oficial aprovado (JPEG 1024×1024) | `controllership_finance_app/assets/characters/clara/avatar-v1.jpg` |
| Projeção pública commitada | `controllership_finance_app/content/clara_public_profile.json` |
| Testes | `tests/test_clara_character_profile.py` |

## Integração MCP

`tool_get_catalog` (interface/mcp/tool_bridge.py) publica
`agent_directives` via `ClaraAgentIntelligenceService.agent_directives()`:
as diretivas operacionais existentes (`read_first`, `citations`,
`confirmation`) + `character` = `project_persona_context(ficha)`
(~4,9 KB — identidade, personalidade, comunicação, aparência, relações
públicas, regras de coexistência/conduta). A história completa e os
eventos ficam fora do contexto por orçamento; a ficha local é a fonte.

## Relacionamentos

CLARA declara `colleagues` (visibility `public`) para `davi`, `vista` e
`teo`. `validate_relationship_consistency` sobre as projeções públicas
commitadas reporta apenas `WARNING` de reciprocidade ausente — as fichas
de DAVI/VISTA/TÉO ainda não declaram a aresta de volta (handoff aos
owners: `api-delpi`, `tv-dashboard-api`, `transformometro-api`). Nenhuma
contradição (`ERROR`).

- EVA: sem ficha ou projeção pública no repositório — aresta `TO_INVENTORY`,
  não declarada nesta versão.
- Romance ficcional DAVI–VISTA preservado; CLARA não possui
  relacionamento romântico.

## Invariantes preservadas

- 18 tools MCP congeladas; nenhuma tool/permission/scope nova.
- AuthN/AuthZ, PREPARE/ACT, consentimento, idempotência e auditoria
  inalterados — narrativa nunca é autorização.
- Avatar versionado no contexto da API (não em `shared/`, sem base64 em
  prompts/contexto); `avatar_status = OFFICIAL_AVATAR_APPROVED` após
  verificação de integridade (sha256 pinado em teste).

## Regenerar a projeção pública

```bash
PYTHONPATH=controllership-finance-api:shared python - <<'EOF'
import json
from controllership_finance_app.application.clara.agent_intelligence_service import ClaraAgentIntelligenceService as S  # noqa: E501
from delpi_character_profiles import public_profile_to_dict
with open('controllership-finance-api/controllership_finance_app/content/clara_public_profile.json', 'w', encoding='utf-8') as f:  # noqa: E501
    json.dump(public_profile_to_dict(S.public_profile()), f,
              ensure_ascii=False, indent=2, sort_keys=True)
    f.write('\n')
EOF
```

O teste `test_public_profile_excludes_internals_and_operational_data`
falha se o artefato divergir da projeção viva — regenerar ao revisar a
ficha e incrementar `PROFILE_VERSION`.

## Distribuição pública do avatar — DELPI-CHARACTER-AVATARS-001

- Rota owner-local: `GET /public/characters/clara/avatar/avatar-v1.jpg`
  (externa: `/apps/controllership-finance-api/public/characters/clara/avatar/avatar-v1.jpg`).
- Prefixo `/public/` liberado no `_is_controllership_finance_public_path`
  do `jwt_middleware` local.
- Fonte única: `appearance.avatar_status` + `avatar_reference` da ficha;
  filename deve ser idêntico ao basename da referência — caso contrário 404.
- Cache `public, max-age=300`; `X-Content-Type-Options: nosniff`.
- Revogação: mudar `avatar_status` na ficha → 404 imediato.
