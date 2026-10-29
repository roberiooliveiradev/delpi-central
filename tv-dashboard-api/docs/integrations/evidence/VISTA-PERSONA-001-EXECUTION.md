# VISTA-PERSONA-001 — Ficha oficial VISTA via `delpi_character_profiles`

**Status:** EXECUTED · `validate_profile` zero ERROR/zero WARNING  
**Owner:** `tv-dashboard-api` (TV Dashboard domain — VISTA owns the character)  
**Origem:** handoff DAVI → VISTA (`api-delpi/docs/integrations/evidence/DAVI-PERSONA-003-VISTA-HANDOFF.md`)  
**Decisão congelada:** *Shared owns the structure. MCP owns the character.*

## Arquitetura

```text
vista_agent_intelligence.json (persona/narrative/story — fonte única de prosa)
  → tv_app/persona/vista_profile.py (CharacterProfile do contrato shared)
    → project_persona_context → agent_directives.character  (MCP-primary)
    → project_public_profile  → tv_app/content/vista_public_profile.json
```

- Ficha local no bounded context — nenhum modelo copiado para `shared/` nem para o domínio.
- `narrative_age="20"` (str), `gender_identity="feminino"`, `avatar_status=REFERENCE_NOT_OFFICIAL_AVATAR`.
- Relacionamento público `romantic_partner` → `davi`, evento canônico compartilhado `davi-vista-partnership` referenciado (não inventado).
- Reciprocidade com `api-delpi/app/content/davi_public_profile.json`: zero ERROR via `validate_relationship_consistency`.

## Superfícies

| Superfície | Entrega |
|---|---|
| MCP (`/mcp` → `get_catalog`) | `agent_directives.character` completo (`project_persona_context`) |
| GPT Actions (`gpt_get_catalog`) | `character` **não projetado** — envelope ~100 KiB sem margem (mesmo precedente de `surface_parity`/`write_flow_mcp`/`param_expressions`); persona estável nas Instructions do Builder (`specialist-instructions.md`, bloco «Identidade fictícia») |

## Segurança

- `FICTION_IDENTITY_ONLY` — ficção nunca é autorização, capability, tool ou dependência entre MCPs.
- Sem comunicação MCP-to-MCP, sem import da ficha DAVI, sem novas tools (12 GPT Actions inalteradas).
- Backend continua autoridade de AuthZ; nada no perfil contém credenciais/permissões/dados operacionais.

## Evidência

- `pytest tests/test_vista_persona_001_character_integration.py` — 24 testes (A contrato, B personalidade, C história+reciprocidade, D contexto MCP, E segurança, F prontidão conversacional).
- Budget gates verdes: `test_gpt_actions_catalog_budget.py` (envelope HTTP ≤ 100 KiB preservado), `test_vista_builder_instructions_budget.py` (sem vazamento de chaves JSON nas Instructions).
- Regressão MCP/GPT: `test_mcp_*`, `test_vista_mcp_*`, `test_gpt_actions_*` verdes.
