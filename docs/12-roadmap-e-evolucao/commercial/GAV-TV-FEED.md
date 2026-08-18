# Conteúdo GR / Gestão à Vista — fontes do Portal Comercial

O editor de slides e playlists vive no **tv-dashboard**. O Portal Comercial **não** reimplementa GR.

## Deep link

`/apps/tv-dashboard`

Início (Home) do Comercial: alerta «GR de Vendas (TV)» → mesmo path.

## Indicadores já no Overview (reusar como data routes TV)

| Card Overview | Fonte HTTP (via BFF commercial-api / SI) | Nota |
|---------------|------------------------------------------|------|
| ROL vs meta | analytics ROL + SI goals | Líquido |
| Carteira em aberto | `/analytics/open-portfolio-summary` | Snapshot; não somar a ROL |
| Share empresa | `/analytics/portfolio-billing-share` | RBAC |
| Gap vs meta | meta SI − ROL | Carteira do mês = contexto |
| Carteira no tempo | `/analytics/open-portfolio-horizon` | Buckets entrega |
| Hit rate | closing-rate | Não alterar fórmula |
| OTD | sales-order-otd | |

## Placeholders (não fingir Existe)

Ticket médio, amostras, FNE, soma ROL+carteira — **bloqueados** até ficha/política.

## O que não fazer

- Editor de slides no `plugins/commercial`
- Duplicar `tv-dashboard-api` no commercial-api
