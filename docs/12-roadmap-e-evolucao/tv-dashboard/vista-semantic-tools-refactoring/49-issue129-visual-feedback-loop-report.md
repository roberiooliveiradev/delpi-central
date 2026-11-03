# 49 — VISTA/TV — ISSUE #129 VISUAL FEEDBACK LOOP REPORT

Data: 2026-11-03 | Commits: d3185dc1a3, a9d75ebb0f, 6bf7ae3c88
Deploy: backend ja em srv-api (e2e e ferramenta, nao runtime).

## Inventario — EXISTING_EQUIVALENT = YES (parcial)

- Playwright: plugins/engineering/e2e + plugins/bpmn-modeler/e2e
  (configs reais, SSO via env).
- Palco canonico publico: plugins/public-hub → tv-dashboard/present
  → PresentationView (shared package, EDITOR==PREVIEW==TV) — exige
  share token governado.
- tv-dashboard-presentation: vitest only — sem dev server/e2e.

## Implementado — REUSE

plugins/tv-dashboard-presentation/e2e/:
- playwright.config.ts — viewport 1920x1080, artifacts gitignored.
- presentation-capture.spec.ts — goto present?token=, espera
  estavel (stage+networkidle), screenshot real.
  Sem TV_PRESENT_TOKEN → falha explicita (nunca VISUAL_PASS).

## Gap comprovado — PROVEN

Percepcao multimodal da VISTA: nenhuma capability de imagem no
MCP/GPT Actions no HEAD — VISTA nao recebe PNG. F2_VISION_EVAL =
CAPABILITY_GAP, nao simulada por JSON.

## Ciclo F3 — PLANNED

Infra de captura seeded; loop render→avalia→refina exige (a)
preview autorizado (share LAB ou SSO), (b) canal de imagem para
o avaliador, (c) LAB auth para COMMIT — todos externos.

## Testes

2455/2455 PASS; spec novo = TEST_NOT_RUN (sem TV_PRESENT_TOKEN
nesta sessao).

## Residuos

- LAB share token: governanca Core API (exposicao publica).
- Multimodal eval: CAPABILITY_GAP — canal de imagem no runtime
  VISTA nao existe.
- COMMIT LAB: AUTHORIZATION_GATE documentado.

## Veredito

DI_F4_CAPTURE = PASS (infra) — harness de screenshot real no
palco canonico commitado; VISUAL_E2E_PASS nao declarado —
depende de token governado + capability de imagem no runtime.
