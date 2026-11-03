# 54 — VISTA/TV — ISSUE #129 PREVIEW ROOT-CAUSE CORRECTION

Data: 2026-11-03 | Commit: 72a8fc9644 | Deploy: srv-api a2b567f7510b

## Root cause — PROVEN

NameError: get_slide_preview_render_service era importado
localmente em get_playlist_context (2347), get_slide_preview_png
(2678) e build_candidate_preview (4970), mas NAO em
suggest_change (4346). O NameError caia no except generico ->
PREVIEW_UNAVAILABLE: defeito de programacao mascarado como
indisponibilidade operacional.

## Correcao — REUSE

Import local na convencao existente do arquivo (3 linhas).
EXISTING_EQUIVALENT=YES; REUSE_DECISION=REUSE.

## Validacao

- py_compile + 2455/2455 (97/97 DI).
- visualEvidence agora emite available (previewUrl+rendered+
  designAudit+basisRevision) quando slide resolve;
  SLIDE_NOT_FOUND/PREVIEW_UNAVAILABLE seguem tipados para falhas
  reais — nao para excecoes de programacao.

## Residuos

- Editor conectado (capture real): TEST_NOT_RUN — exige MFE do
  usuario no LAB; bloqueador externo, nao codigo.
- Pixel-VLM: ADR pendente.

## Veredito — ACCEPT (escopo desta task)

Excecao comprovada, correcao minima no owner, mascaramento
eliminado. Proximo ensaio MCP autenticado deve retornar
visualEvidence.status=available com previewUrl+basisRevision+audit.
