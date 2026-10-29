# VISTA-AVATAR-001 — Avatar oficial VISTA e identidade visual

**Status:** EXECUTED · `validate_profile`/`validate_public_profile` zero ERROR/zero WARNING  
**Owner:** `tv-dashboard-api` (VISTA bounded context)  
**Dependência:** `VISTA-PERSONA-001` (ficha existente reutilizada — nenhuma segunda fonte de persona)  
**Decisão congelada:** *Shared owns the structure. MCP owns the character — e seus assets.*

## Asset original preservado

Fonte: imagem fornecida pelo usuário (referência visual aprovada — não recriada, não reinterpretada, não substituída). **v2** — o usuário aprovou nova imagem após a v1; a v1 permanece no histórico do git.

| Propriedade | Valor |
|---|---|
| Caminho canônico | `tv_app/content/characters/vista/avatar-v2.jpg` |
| Formato | JPEG (JFIF), 1024×1024 |
| Tamanho | 340.944 bytes |
| SHA-256 | `8d4879cc395361619d6b4c2623a04c029faaa41714283c76dec3e82ddc39d155` |
| v1 (superseded) | `avatar-v1.png` — PNG 1024×1024, SHA-256 `740f772b…42b6` |

- Byte-idêntico ao original (checksum verificado após cópia); nenhuma alteração visual, nenhum derivado gerado.
- Convenção reutilizada: assets versionados em `tv_app/content/` (mesmo mecanismo de `content/brand/`); estrutura `characters/<character_id>/avatar-v1.png` espelha a convenção cross-MCP de DAVI-AVATAR-001 (`app/assets/characters/davi/`); nenhum sistema de storage novo criado.
- **Não** armazenado em `shared/delpi_character_profiles/` — o asset pertence ao bounded context da VISTA.
- Nenhum base64 em MCP, JSON de inteligência ou prompts; `avatar_reference` é o path estável do repo, resolvível no pacote deployado (Dockerfile copia `tv_app/` integralmente).

## Identidade visual oficial (Appearance)

Campos atualizados na ficha conforme imagem aprovada v2: `skin`, `hair` (pretos, lisos e longos), `eyes` (grandes, expressivos e castanhos), `face`, `glasses` (armação escura retangular — segurado na mão), `clothing` (blazer cinza sobre blusa clara), `visual_style` (3D estilizado), `color_palette` (cinza/branco/preto/bege quente), `avatar_reference`, `avatar_status=OFFICIAL_AVATAR_APPROVED` (aplicado só após validar+persistir o asset). `age_appearance` preservado ("jovem — 20 anos").

`profile_version` 1 → 3 (v1: ficha inicial; v2: avatar PNG v1; v3: avatar JPEG v2 — content version do owner; `SCHEMA_VERSION` e `PUBLIC_PROJECTION_VERSION` inalterados — mudança aditiva).

## Contrato shared — evolução mínima

`project_persona_context` passa a emitir `avatar_reference` **condicional** (somente quando preenchido — mesmo padrão de `narrative_age`). Aditivo e retrocompatível: perfis sem avatar (ex.: DAVI) não emitem a chave. Nenhum campo removido ou renomeado.

## Preservação

- Personalidade, expertise, história, `narrative_age="20"`, estilo de comunicação: **inalterados**.
- Relacionamento `romantic_partner` → `davi` e evento `davi-vista-partnership`: **inalterados**; ficha DAVI intocada.
- Características visuais não viram instruções repetitivas: `appearance.rule` mantém «não se repete em respostas operacionais».
- `specialist-instructions.md`: descrição visual dos blocos «Identidade fictícia» atualizada (cabelo longo, óculos na mão, blazer cinza); edição do usuário («identidade fictícia») preservada.

## Segurança

- `FICTION_IDENTITY_ONLY` inalterado — avatar não é capability, tool, permissão ou dependência.
- Zero tools/rotas/AuthZ novas; 12 GPT Actions inalteradas; backend segue autoridade.
- `avatar_reference` é path de pacote interno — não URL, não endpoint, não superfície de acesso.

## Evidência

- `test_vista_persona_001_character_integration.py` — 25 testes: novo `test_avatar_asset_persisted_and_resolvable` (existência + magic PNG + SHA-256 pinado), contexto projeta `avatar_status`/`avatar_reference`, artefato público regenerado e igual à projeção, reciprocidade DAVI mantida.
- Shared `delpi_character_profiles/tests/` — 39/40 (1 baseline: `test_import_has_no_side_effects` falha por `sitecustomize` injetado pelo venv — artefato de ambiente, pré-existente).
- Regressão MCP/GPT/budgets: 119 testes verdes (catalog ≤ 100 KiB, instructions budget, wire/conformance, read/write surfaces).
- Round-trip `profile_to_dict`/`profile_from_dict` igual; `validate_relationship_consistency` com artefato real do DAVI: zero ERROR.

## Deploy/runtime

- Asset empacotado via `COPY tv_app/` do Dockerfile — presença no container verificada pós-deploy: `/app/tv_app/content/characters/vista/avatar-v2.jpg`, 340.944 bytes, SHA-256 `8d4879cc…d155` (idêntico ao commit).
- Runtime in-container: `vista 20 3 OFFICIAL_AVATAR_APPROVED tv_app/content/characters/vista/avatar-v2.jpg`.
- Smoke via gateway: `/apps/tv-dashboard-api/health` 200; catalog sem auth 401 (fail-closed); `/.well-known/oauth-protected-resource` 200; portal `/` 200.
- Validação conversacional live ChatGPT: TEST_NOT_RUN (sem acesso ao host nesta sessão).

## Distribuição pública do avatar — DELPI-CHARACTER-AVATARS-001

- Rota owner-local: `GET /public/characters/vista/avatar/avatar-v2.jpg`
  (externa: `/apps/tv-dashboard-api/public/characters/vista/avatar/avatar-v2.jpg`).
- `PUBLIC_PREFIXES` já cobre `/public/` — sem mudança de middleware.
- Fonte única: `appearance.avatar_status` + `avatar_reference` da ficha;
  filename deve ser idêntico ao basename da referência — caso contrário 404.
- Resposta via `build_media_file_response` (helper canônico); cache
  `public, max-age=300`.
- Revogação: mudar `avatar_status` na ficha → 404 imediato.
