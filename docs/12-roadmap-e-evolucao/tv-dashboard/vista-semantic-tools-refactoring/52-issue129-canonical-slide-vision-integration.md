# 52 — VISTA/TV — ISSUE #129 CANONICAL SLIDE VISION INTEGRATION

Data: 2026-11-03 | Commit: 96c2455b80 | Deploy: srv-api 08a5fb98b1c8

## Diagnostico — PROVEN (doc 51)

Capability EXISTE e esta exposta; gap = consumo: a composicao
(suggest/proposal) nao propagava previewUrl/rendered/audit.

## Implementacao — EXTEND (reuso total)

suggest_change anexa payload.visualEvidence quando ha slide:
- previewUrl assinada (slide_preview_token + build_preview_payload);
- rendered sob _apply_live_editor_visual_policy
  (editor_live, frescor 300s, canonical_stage);
- designAudit estrutural (DesignIntelligenceService);
- basisRevision — honesto: evidencia do estado persistido,
  nao da proposta (H4 documentado, nao mascarado).

Sem nova GPT Action, sem servico novo, sem renderer novo.

## Estados de evidencia — honestos

- PREVIEW_REFERENCE_AVAILABLE: previewUrl emitida.
- IMAGE_AVAILABLE: rendered.status do palco editor_live.
- EDITOR_CAPTURE_PENDING: editor offline -> pendente (nao PASS).
- STRUCTURAL_AUDIT_COMPLETED: designAudit issues.
- PIXEL_EVALUATION_COMPLETED: VLM ausente no dominio — nao
  declarado (G18 classificado).

## Testes

2455/2455 PASS — 97/97 DI; fixtures sem slide inalterados.

## Residuos — limitacoes honestas

- Evidencia e do estado PERSISTIDO (basisRevision); preview da
  proposta usa o caminho candidate/cacheKey ja contratado.
- Commit LAB: AUTHORIZATION_GATE (fresh-RBAC + consent).
- Pixel-VLM: ADR cross-boundary pendente.

## Veredito — ACCEPT_WITH_RESIDUAL

G3-G9 PASS: capabilities existentes reutilizadas e propagadas no
fluxo real; avaliacao estrutural acessivel; estados honestos
quando captura indisponivel. Residuo nao bloqueante: multimodal
pixel-VLM (G18) e LAB commit (authorization gate) — documentados.
