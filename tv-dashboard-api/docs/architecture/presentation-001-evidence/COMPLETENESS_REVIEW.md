# TV-DASHBOARD-PRESENTATION-001 — Completeness Review

**BASE:** `86b2fce55c` (+ follow-up viewport materialization commit)  
**Date:** 2026-09-24  
**Evidence class:** CONFIRMADO_NO_CODIGO unless noted.

---

## 1. Persisted presentation state inventory

### A. COMPONENT (block)

| property | owner | mutation | persistence | materialized | FE consumer |
|---|---|---|---|---|---|
| frame {x,y,w,h} | BE | upsert_block / align_blocks | slide.native_config | nativeConfig.blocks[].frame | paint / transient drag |
| style (typo/chrome/z) | BE | upsert_block / reorder_block_z | native_config | blocks[].style | paint |
| chart/table/kpi options+parts | BE | upsert_block + blockDefaults | native_config | blocks[].*Options/*Parts | paint |
| shape/icon/media fields | BE | create_block / upsert | native_config | block | paint |
| projections / display* | BE | enrich bake | runtime (+specs persisted) | display*, server*Applied | PAINT only |
| create defaults | BE | create_block + blockDefaults | native_config | full block | stub FE until ack |

### B. SCREEN / CANVAS

| property | owner | mutation | persistence | materialized | FE consumer |
|---|---|---|---|---|---|
| viewportProfile | BE | PATCH playlist | playlists.viewport_profile | playlist.viewportProfile | DeckSettings / DesignViewport |
| canonical width/height | BE | resolve_effective_viewport_px | named map in BE; custom cols | playlist.viewportWidth/Height **always** | resolveViewportPixelSize prefers dims |
| aspect / orientation | BE | derived from profile/dims | via profile | width/height | VIEWPORT_TRANSFORM |
| slide background | BE | patch_native_config / upsert | native_config.background | nativeConfig.background | paint |
| master theme/logo | BE | PATCH playlist masterConfig | playlists.master_config | masterConfig | paint overlay |
| persistent grid/snap/guides | **N/A presentation** | — | localStorage `td-stage-display-preferences` | — | TRANSIENT_EDITOR_UI only (not TV paint) |
| safe area | N/A | — | not a persisted product setting | — | — |
| clipping/overflow | PAINT CSS | — | not persisted | DesignViewportStage overflow hidden | PAINT contract |

### C. SLIDE / PAGE

| property | owner | mutation | persistence | materialized | FE consumer |
|---|---|---|---|---|---|
| identity (id) | BE | create/duplicate slide | slides.id | slide.id | editor/filmstrip |
| order (sortOrder) | BE | reorder_slides / PATCH | slides.sort_order | slide.sortOrder | filmstrip |
| visibility (isActive) | BE | update_slide / section inherit | slides.is_active | slide.isActive | present filter |
| background | BE | native_config | JSON | native.background | paint |
| durationSec | BE | update_slide / update_slide op | slides.duration_sec (null=inherit) | slide.durationSec | resolveSlideDurationSec |
| transitionStyle | BE | update_slide | slides.transition_style | slide.transitionStyle | resolveSlideTransitionStyle |
| layout/settings (nativeConfig) | BE | presentation-mutations / PATCH | native_config | nativeConfig | editor + present |
| component z-order | BE | reorder_block_z / style.zIndex | native_config | style.zIndex | paint |

### D. PRESENTATION / PLAYBACK

| property | owner | mutation | persistence | materialized | FE consumer |
|---|---|---|---|---|---|
| presentation dimensions | BE | viewportProfile (+materialized px) | playlist | viewport* | DesignViewportStage |
| slide order | BE | reorder | slides.sort_order | payload.slides[] | engine |
| playbackMode | BE | PATCH playlist | playback_mode | playlist.playbackMode | isAutoAdvanceMode |
| autoplay / loop | BE via playbackMode | presentation=auto-advance cycle; meeting=manual | playback_mode | playbackMode | usePresentationEngine |
| timing (defaultDurationSec) | BE | PATCH playlist / section | default_duration_sec | defaultDurationSec | inheritance resolve |
| transition policy | BE | PATCH playlist/section/slide | transition_style | transitionStyle | present |
| globalRefreshSec | BE | PATCH playlist | global_refresh_sec | globalRefreshSec | data refresh |
| published settings / token | BE | regenerate-token / present payload | public_token | publicUrl / payload | public-hub |
| separate loop flag | N/A | not in product model | — | — | — |

---

## 5. Ribbon / persistent controls

See `E3_ribbon_controls_matrix.md` (78 controls). Persistent paths:

- geometry/create/z/duplicate → PresentationMutation ops
- style/options/frame patches → upsert_block ack (`commitUpsertBlocks`)
- slide/playlist timing/viewport/playback → updateSlide / updatePlaylist
- grid/snap/guides toggles → TRANSIENT_EDITOR_UI (localStorage), not presentation SOT

No persistent **presentation** control terminates as sole local canonical state after ack.

---

## 6. Frontend residual classification

| Hit | Class |
|---|---|
| `create*Block` / `DEFAULT_*` | TRANSIENT_EDITOR_UI (stub until mutation ack) |
| `alignComunicadoBlocks` local | TRANSIENT_EDITOR_UI (fallback) |
| `stageDisplayPreferences` localStorage | TRANSIENT_EDITOR_UI |
| `VIEWPORT_PIXEL_SIZES` map | VIEWPORT_TRANSFORM fallback only; paint prefers server dims |
| `resolveViewportPixelSize` | VIEWPORT_TRANSFORM |
| `display*` / gaugeModel paint | PAINT |
| autosave draft localStorage | NETWORK / SERVER_MODEL_CACHE coordination |
| CSS overflow clip | PAINT |
| DeckSettings → updatePlaylist | NETWORK |

**CANONICAL_FE_AUTHORITY hits for published presentation:** none after viewport materialization.

---

## 7. Final gates

| Gate | Value |
|---|---|
| ALL_COMPONENT_PRESENTATION_BACKEND_OWNED | **YES** |
| ALL_SCREEN_CONFIG_BACKEND_OWNED | **YES** (viewport px materialized; editor grid N/A) |
| ALL_SLIDE_CONFIG_BACKEND_OWNED | **YES** |
| ALL_PRESENTATION_CONFIG_BACKEND_OWNED | **YES** |
| ALL_PERSISTENT_EDITOR_CONTROLS_BACKEND_OWNED | **YES** (presentation-affecting) |
| ANY_CANONICAL_PRESENTATION_AUTHORITY_IN_FRONTEND | **NO** |
| FRONTEND_ONLY_TRANSIENT_AND_PAINT | **YES** |
| HYGIENE_COMPLETE | **YES** |

---

## 8. RQ / AC

All PRESENTATION-001 RQ (component authority + screen/slide/presentation ownership + residual allowlist + gates) → **IMPLEMENTED** / **PASS**.  
Live smoke: external optional.
