# 03 — Capability Mapping (domínio TV Dashboard vs VISTA)

HEAD de inspeção: `28943d4d9b` · Legenda de disponibilidade:
**REST** = endpoint backend existe · **TYPED** = covered por typed op
(via prepare/commit) · **TOOL** = VISTA expõe operação dedicada ·
**—** = não acessível à VISTA.

## 1. Matriz domínio → VISTA

| CAPABILITY_ID | REST endpoint(s) | VISTA hoje | Via | Limitações |
|---|---|---|---|---|
| `playlist.list` | `GET /playlists` | **TOOL** | `list_playlists` | paging apenas |
| `playlist.get/context` | `GET /playlists/{id}` | **TOOL** | `get_playlist_context` | contexto rico (slides, blocks, revision) |
| `playlist.history.list/get` | `GET /playlists/{id}/history*` | **TOOL** | `get_playlist_history` | digest bounded ≤500; sem diff de block |
| `playlist.history.restore` | `POST .../history/{hid}/restore` | **—** | — | **gap**: restore existe no backend; VISTA não alcança |
| `playlist.create` | `POST /playlists` | **TYPED** | `create_playlist` op (direct) | via governed envelope apenas |
| `playlist.update` | `PATCH /playlists/{id}` | **TYPED parcial** | `update_slide`/defaults ops | sem typed op de playlist-level fields (nome/desc?) — **TO_INVENTORY** |
| `playlist.delete` | `DELETE /playlists/{id}` | **—** | — | **gap**: sem typed op de delete playlist |
| `playlist.activate/deactivate` | `POST .../activate\|deactivate` | **—** | — | **gap** |
| `playlist.duplicate` | `POST .../duplicate` | **—** | — | **gap** |
| `playlist.export (.mdd)` | `GET .../export` | **—** | — | **gap**: exportação MDD indisponível |
| `playlist.import` | `POST /playlists/import/{preview,apply}` | **—** | — | **gap** |
| `playlist.public-url/qr/token` | `GET .../public-url`, `/qr`, `POST .../regenerate-token` | **—** | — | **gap**: compartilhamento indisponível |
| `playlist.shares` | `GET/POST/DELETE .../shares*` | **—** | — | **gap** (deliberado? ACL é admin, não IA — TO_INVENTORY) |
| `playlist.edit-invites` | `POST .../edit-invites*` | **—** | — | **gap** (mesma nota) |
| `slide.add` | `POST /slides`, `/from-preset` | **TYPED** | `add_blank_slide`, `add_slide_from_preset` | ✓ |
| `slide.update` | `PATCH /slides/{id}` | **TYPED** | `update_slide` | ✓ |
| `slide.delete` | `DELETE /slides/{id}` | **TYPED confirm** | `delete_slide` | confirmação = boolean declarado (ver 05) |
| `slide.duplicate` | `POST /slides/{id}/duplicate` | **—** | — | **gap** |
| `slide.reorder` | `POST /slides/reorder` | **TYPED** | `reorder_slides` | ✓ |
| `slide.move-to-section` | (via PATCH) | **TYPED** | `move_slide_to_section` | ✓ |
| `slide.rendered-preview` | `PUT /slides/{id}/rendered-preview` | **—** | — | render do host; não-AI |
| `slide.preview-data-block` | `POST /slides/{id}/preview-data-block` | **TOOL** | `preview_data_block` | executa rota real via SlideDataResolutionService |
| `section.crud/reorder` | `POST/GET/PATCH/DELETE /sections`, `/reorder`, `/ensure-main` | **TYPED parcial** | `upsert_section`, `delete_section`(confirm), `move_slide_to_section` | **gap**: sem reorder_sections typed op — **TO_INVENTORY** |
| `block.create/upsert` | (via slide mutations) | **TYPED** | `create_block`, `upsert_block`, `duplicate_blocks` | ✓ |
| `block.delete` | — | **TYPED confirm** | `delete_block` | ✓ |
| `block.align/z/transform` | — | **TYPED** | `align_blocks`, `reorder_block_z`, `transform_text_case`, `bump_font_size` | ✓ |
| `datablock.route.discovery` | `GET /data/routes`, `POST /routes/suggest` | **TOOL** | `search_data_routes` | 545 rotas allowlisted (`tv_data_routes.json`) |
| `datablock.preview` | `POST /data/preview-block` | **TOOL** | `preview_data_block` | executa resolução real (05 §Caso C) |
| `datasource.upsert/patch` | — | **TYPED** | `upsert_data_source`, `patch_data_source_params`, `patch_playlist_data_defaults` | ✓ |
| `datamodel.crud/migrate` | `POST /data/data-model-*`, `/preview-model`, `GET /data-models/inspect` | **TOOL+TYPED** | `preview_data_model`, `inspect_data_model` + 5 typed ops | `delete_data_model` é **direct** (ver 05/G-02) |
| `data.transform` | `POST /m/*`, `/data/transform` | **TYPED** | `set_data_transform` | M DELPI implementado, flags off (playbook) |
| `display.format` | `POST /data/display-format/previews` | **TYPED** | `set_display_format` + designIntelligence no catálogo | ✓ |
| `native.config` | — | **TYPED** | `patch_native_config`, `re_layer_playlist_filters` | ✓ |
| `media.upload/list/get/delete` | `POST /media`, `/uploads`, `GET/DELETE /media*` | **—** | — | **gap**: mídia indisponível à VISTA (upload binário não-semântico é esperado; list/get seriam read) |
| `media.optimize/poster` | `POST .../optimize*`, `GET .../poster` | **—** | — | **gap** |
| `brand.logo.ensure` | — | **TYPED** | `ensure_brand_logo_on_slide` | ✓ |
| `template.crud` | `POST/GET/PATCH/DELETE /slide-templates*` | **—** | — | **gap**: só `apply_published_slide_template` existe |
| `template.publish/archive/clone` | `POST .../publish\|unpublish\|archive\|clone` | **—** | — | **gap** |
| `template.import/export` | `POST /slide-templates/{import,export}*` | **—** | — | **gap** |
| `slide.preset.list/get/export` | `GET /slide-presets*` | **—** | — | **gap**: presets listáveis via REST, não via VISTA (só uso indireto em `add_slide_from_preset`) |
| `content.ui/branch-scope` | `GET /content/ui`, `/branch-scope` | **—** | — | **TO_INVENTORY** (conteúdo estático; branch-scope pode ser relevante a read) |
| `guide.product` | `GET /product-guides` | **TOOL** | `get_product_guide` (MCP-primary no taxonomy) | GUIDANCE_NOT_DOMAIN_TRUTH |
| `character.avatar.public` | `GET /characters/{id}/avatar/{fn}` | público | rota pública | asset oficial servido |
| `catalog.capability` | `GET /gpt-actions/v1/catalog` | **TOOL** | `get_catalog` (ambas projeções) | ✓ |
| `change.suggest` | `POST /changes/suggest` | **TOOL** | `suggest_change` (determinístico) | ✓ |
| `change.prepare/commit` | `POST /changes/{preview,commit}` | **TOOL** | `prepare_change`+`commit_proposal` | PREPARE→COMMIT + commit_now (Actions) |
| `present.public` | `GET/POST /present/{token}*` | público | — | TV/player; não-AI por design |
| `realtime.ws` | WS `/presentation` | — | — | editor concurrency; não-AI |
| `native.screen.list` | `GET /native-screens` | **—** | — | **TO_INVENTORY** |
| `builder.sessions` | `POST /builder/sessions*` | — | — | UI builder NL; **não expor à VISTA** (seria caminho paralelo ao suggest_change) |
| `openapi.sync` | `POST /data/openapi/sync` | S2S | — | INTERNAL ADMIN apenas |
| `validate-config` | `POST /data/validate-config` | **—** | — | **TO_INVENTORY** — possível read/analysis útil |
| `copilot.*` | `/data/copilot/*` | **410 Gone** | — | retired — não reativar |

## 2. Resumo quantitativo

- **12 tools MCP** / **12 GPT Actions** (paridade total via parity_map).
- **32 typed ops** (29 direct + 3 confirm).
- **~90 REST endpoints**; ~40+ capabilities de produto catalogadas
  acima; a VISTA alcança diretamente ~15 (tools) + tudo que os 32
  typed ops cobrem dentro do envelope governado.
- Gaps materiais à VISTA: playlist lifecycle fora de create
  (update/delete/activate/duplicate/export/import/sharing), history
  restore, media, templates (exceto apply), slide duplicate,
  section reorder, presets listing, validate-config.

## 3. Observações de ownership

- `get_playlist_history` já documenta limite intencional:
  restore/rollback "never exposed" — decisão registrada em
  capability_surface; expor restore exigiria decisão explícita.
- Shares/invites/branch ACL: candidatos a exclusão deliberada do
  escopo IA (admin de acesso humano) — classificar em Fase 2 como
  `TO_INVENTORY` com decisão do owner.
- `builder/sessions/*` e `/data/copilot/*`: caminho NL alternativo —
  manter fora da VISTA evita segunda trilha de materialização
  (o canônico é `suggest_change` + typed ops).
