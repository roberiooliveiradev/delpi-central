# HELP-AND-ONBOARDING — Portal Suprimentos

Satélite obrigatório (`feature-help-sync.mdc`). **Não** deixar «manual depois».

## Superfícies (padrão Comercial)

| Superfície | Path futuro |
|------------|-------------|
| Manual in-app | `plugins/supplies/src/content/userManualContent.ts` + rota `/help` |
| Quero → onde | `userManualToolLinks.ts` + `MANUAL_TOOL_TARGETS` |
| Tooltips | `helpTooltips.ts` (PT de negócio; sem `operationId` / path técnico) |
| FAQ | seção no Manual |
| Glossário | `glossaryContent.ts` (OTD, ESTSEG, SC, PC, CPV, giro vezes vs meses, filial 01/02) |
| Espelho markdown | `docs/12-roadmap-e-evolucao/supplies/MANUAL-USUARIO-PORTAL-SUPRIMENTOS.md` (criar na E16) |

Herdar textos já canônicos de:

- `plugins/dashboard-supplies/src/content/helpTooltips.ts`
- README ESTSEG (déficit, SC1 não projeta)
- contrato SC (resíduo ≠ cancelado; comprador ≠ C7_USER)

## Conteúdo mínimo P0 (E4/E16)

- O que é o Portal vs apps antigos (coexistência).
- Início vs Visão geral.
- Como filtrar filial.
- Onde ver SC, ESTSEG, item, fornecedor.
- O que cada KPI do Overview significa (link fichas, linguagem de negócio).
- 403: «sem permissão para esta filial / este módulo».
- FAQ: diferença estoque × estoque de segurança; OTD × atraso; Sheets × indicadores.

## Sync por feature

Cada E\* user-facing inclui na receita: atualizar tooltip + linha Quero→onde + teste estrutural de chaves.

## Onboarding

Primeira visita: PageHero + 3 atalhos por cap (não tour modal cobrindo sidebar). Empty states com CTA para Ajuda.
