# 43 — VISTA/TV DI-E2E-DESIGN-01R CORRECTION REPORT

**Data:** 2026-11-02 · **Commit:** `aeea245338` · **Deploy:** `srv-api`
imagem `sha256:a06e370a2927`

## Root causes — `ROOT_CAUSE_PROVEN`

- **RC-2:** `FIX_LAYOUT` ("organiz") casava antes de `COMPOSE_SLIDE`
  — "Organize os elementos" sequestrava o pedido para patch de
  layout → `ready`+`patch_native_config` só (falso ready).
- **RC-1:** palavras de instrução (`desenvolva`, `usando`,
  `mantendo`, `fontes`, `oficiais`, `inventar`) e qualificadores
  de design/formato (`gráfico`, `título`, `1080p`, `alto`, `clara`)
  viravam objetivos de negócio → `Painel de Inventar`.
- **RC-3:** título derivado por ordem de set (arbitrária) — agora
  segue a ordem de aparecimento no briefing; sigla maiúscula do
  usuário preservada (`OEE`).
- **RC-5:** `_has_design_req` ampliado com termos de domínio
  promovia gibberish a `proposal` — restringido a termos visuais;
  checks normalizados NFKD (`gráfico`/`tabela`/`título`/`tendência`).

## Correção — `EXTEND`

- `design_intelligence_service`: COMPOSE_SLIDE precede FIX_LAYOUT.
- `dispatch_service`: stop set por papel semântico; título por
  posição no briefing; `_has_design_req` acento-safe e restrito.

## Reproduções — antes/depois

| | Antes | Depois |
|---|---|---|
| A (OEE completo) | `ready`+patch só | `proposal`+composição+goals{oee,eficiência,meta}+"Painel de OEE" |
| B (desenvolva+fontes) | `proposal`, "Painel de Inventar", goals junk | `proposal`+ds/bind+goals{oee,meta}+"Painel de OEE" |
| C (título explícito) | partial | `ready`+ops+"Painel de Eficiência Industrial" |
| D (slide vazio) | `ready`+blank | preservado |
| Gibberish | — | `unsupported` preservado |

## Testes

**2455/2455 PASS** — 97/97 DI; 2 asserts desalinhados com o
contrato de intent corrigido foram ajustados na iteração.

## Resíduos

- Bindings ambíguos (meta vs realizado OEE) seguem
  `NEEDS_SOURCE_SELECTION` — legítimo, não pick silencioso.
- Commit LAB exige PREPARE→CONFIRM autorizado — não executado.
- `VISUAL_VERIFICATION = TEST_NOT_RUN`.

## Veredito

**`DI_E2E_DESIGN_01R = B — COMPLETE_PROPOSAL_VERIFIED`** —
uma solicitação produz proposta completa e coerente (design+
objetivos+fontes+bindings tipados); a execução final depende do
gate de confirmação canônico, não de novo código.
