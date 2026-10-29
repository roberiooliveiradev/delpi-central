# DAVI-PERSONA-003 — Integração do contrato `delpi_character_profiles`

> **Status:** implementado e deployado. DAVI = primeiro consumidor real do
> contrato compartilhado de personagens. Ficção permanece UX; zero impacto
> em AuthZ, tools, contratos ou integrações.

## 1. Arquitetura aplicada

```text
shared (delpi_character_profiles, schema v1)
    ↓ import
app/persona/davi_profile.py  ← ficha DAVI (profile_version 1)
    ↓ deriva prosa de
app/content/davi_agent_intelligence.json  ← fonte única de texto
    ↓ project_persona_context
capability_surface.agent_directives.character
    ↓
discover_delpi_information / gpt_get_catalog → host
```

- **Fonte única:** a ficha *deriva* a prosa do content JSON
  (`persona`/`narrative`/`story`) — nada é duplicado em Python.
- **`story`** entrou no JSON como seção **não-projetada** (origem, missão,
  valores, interesses, eventos `davi-origin`/`davi-vista-partnership`,
  expertise narrativa) — história completa não vai a cada turno.
- **`agent_directives.character`** substitui `persona`+`narrative`:
  mesma informação em projeção compacta; 31759/32768 bytes (≤ baseline).
- **Projeção pública:** `app/content/davi_public_profile.json` — artefato
  commitado e testado contra `project_public_profile` (distribuição
  governada = git; sem serviço de sync — TARGET).

## 2. Conteúdo da ficha

- Identity: `davi`/DAVI, título especialista em dados, sem idade numérica
  (não aprovada), gênero masculino.
- Appearance: `REFERENCE_NOT_OFFICIAL_AVATAR` — jovem, cabelos escuros,
  expressão curiosa/simpática, casual-tecnológico azul.
- Personality/Communication: traços aprovados, humor leve contextual,
  pt-BR cordial objetivo.
- Expertise (narrativa, ≠ tools): dados DELPI, SQL, Protheus, investigação,
  interpretação, descoberta semântica, qualidade, sugestões.
- Story: origem no universo fictício, missão, valores, interesses; evento
  `davi-vista-partnership` sem data (cronologia romântica não definida).
- Relationship: `vista`/`romantic_partner`/public + mention_rules e
  hard_boundaries do bloco narrativo.

## 3. Empacotamento

`shared/pyproject.toml` já incluía `delpi_character_profiles*` (task
SHARED-001); `api-delpi/Dockerfile` faz `COPY shared /shared` +
`pip install -e /shared[fastapi]` → pacote disponível sem mudança de build.
Em ambientes de teste com editable strict, reinstalar `pip install -e
/shared` após bump do pyproject.

## 4. Validação

```text
CONTRACT   = import/instância/validação/round-trip/projeções — sem ERROR
SECURITY   = ficha sem campos operacionais; sem tools/AuthZ novos;
             shared continua sem fichas preenchidas (guard test)
MCP        = directives["character"] projetado; initialize com VISTA;
             31759/32768 bytes; 2 tools; read_only
REGRESSION = suites DAVI + benchmark preservados
```

## 5. Limites honrados

- `shared/` não recebeu ficha DAVI; `api-delpi` não reimplementou modelos.
- Nenhuma tool/capability/endpoint/scope/AuthZ alterado.
- Nenhuma distribuição automática de perfis; artefato commitado apenas.
- Handoff atualizado; recebimento pela VISTA não comprovado.

## Distribuição pública do avatar — DELPI-CHARACTER-AVATARS-001

- Rota owner-local: `GET /public/characters/davi/avatar/avatar-v1.png`
  (externa: `/apps/api-delpi/public/characters/davi/avatar/avatar-v1.png`).
- Prefixo `/public/characters/` liberado em `_PUBLIC_PREFIXES` do
  `jwt_middleware`; operação `get_public_character_avatar` registrada no
  `ROUTE_CONTRACTS` (`character_avatar`/`scalar`).
- Fonte única: `appearance.avatar_status` + `avatar_reference` da ficha;
  filename deve ser idêntico ao basename da referência — caso contrário 404.
- Cache `public, max-age=300`; filename versionado garante imutabilidade.
- Revogação: mudar `avatar_status` na ficha → 404 imediato.
