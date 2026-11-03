# 51 — VISTA/TV — ISSUE #129 EXISTING SLIDE VISION CAPABILITY AUDIT

Data: 2026-11-03 | HEAD: 2f5d2eaa05 | Audit forense, sem patch.

## B. Inventario — CAPABILITY_EXISTS = YES

### RENDERED_PREVIEW — PROVEN (domain-owned)
- SlidePreviewRenderService.render_png(native) — renderer
  server-side de esquema do slide (fills/frames/labels).
- get_or_render / read_rendered_png / store_rendered_png.
- Endpoint: PUT /{slide_id}/rendered-preview — o editor sobe
  PNG do palco real (source=editor_live|editor_stage_capture).

### IMAGE_TRANSPORT — PROVEN
- slide_preview_token.py — mint/parse signed tokens
  (playlistId/slideId/revision/cacheKey/artifact) — AuthZ.
- GET /gpt-actions/slide-previews/{token} (routes:311) — serve
  PNG bytes; Bearer opcional + token assinado.
- get_playlist_context(include_preview=True) →
  slidePreview.previewUrl + rendered.previewUrl — a VISTA
  recebe URLs assinadas no read/get_context.
- previewUrl tambem sai no resultado de execute (line 4930).

### LIVE CAPTURE — PROVEN
- presentation_realtime_hub.request_visual_capture — realtime
  pede ao EDITOR focado renderizar e subir PNG.
- _apply_live_editor_visual_policy (VISTA-LIVE-EDITOR-VISUAL-
  VERIFICATION-003): artifact canonico so conta quando
  source=editor_live + fresh(300s); senao EDITOR_CAPTURE_PENDING.

### VISUAL_EVALUATION — PARTIAL
- VisualVerificationService: design_audit diff + layoutGate +
  rendered flag — avaliacao ESTRUTURAL deterministica (Q1-Q10,
  overlaps, contraste, hierarquia por coordenadas).
- Avaliacao por PIXEL/VLM: ausente no dominio TV; existe so em
  minha-delpi-ai-api (outro bounded context — nao assumir).

## D. Comparativo — backend vs MCP vs consumo

| Camada | Estado |
|---|---|
| Backend render+capture+serve | EXISTE e esta exposto |
| MCP tool_bridge | lê PNG renderizado (bridge:128) |
| read/get_context | retorna previewUrl assinada |
| VISTA consumo | GAP — previewUrl nao solicitada (includePreview
  default False) e instrucao nao orienta fetch+avaliacao |

## F. Diagnostico

Sintoma: "VISTA nao ve o dashboard". Causa: NAO e ausencia de
capability — e RUNTIME_INSTRUCTION_GAP + RESULT_CONSUMPTION_GAP:
a imagem esta acessivel via previewUrl (read com includePreview)
mas o fluxo de uma interacao nunca a solicita nem a avalia.
Avaliacao visual por pixels (VLM) = unica peca realmente
inexistente no dominio; structural QA ja cobre findings
deterministicos.

## G. Plano — menor correcao

1. REUSE: no fluxo de composicao, apos proposal/preview, ler o
   slide com include_preview=true e propagar previewUrl +
   rendered status + issues do design_audit no suggest result.
2. VISTA instrucao: fetch da previewUrl (signed, bearer-opt)
   como evidencia visual — sem novo Action, sem contrato novo.
3. VLM eval = decisao arquitetural separada (ADR); structural
   QA ja alimenta findings hoje.

## H. Veredito — PROVEN

CAPABILITY_EXISTS_AND_EXPOSED — o gap e consumo/instrucao
(includePreview + fetch guidance), nao transporte nem capture.
Minima correcao: propagar previewUrl no resultado de composicao.
