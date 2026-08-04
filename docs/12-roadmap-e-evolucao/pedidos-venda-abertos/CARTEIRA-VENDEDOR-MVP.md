# Carteira do vendedor (MVP A+1)

Status: implementado no código (branch de trabalho).

## Escopo

- Cadastro: usuário Minha DELPI (`user_id` = Keycloak `sub`) ↔ clientes TOTVS (`codigo` + `loja`).
- Na **Configuração**, clientes são **buscados no SA1 ativo** via `GET /pedidos-venda-abertos/customers/search`.
- **Transferência** parcial/total: `POST /sellers/{id}/customers/transfer`.
- **Logo do cliente** (avatar): `PUT/GET/DELETE /customers/{codigo}/{loja}/avatar` — arquivo em volume persistente; metadado em `customer_avatars` (migration V002).
- **Enriquecimento da lista**: `POST /customers/enrichment` — cidade/UF (SA1) + faturamento 12m + última compra (NF) + `has_avatar`.
- Tela **Configuração** — permissão `pedidos-venda-abertos.admin`.
- **Minha carteira** / **Pedidos** filtrados pela carteira; gerente filtra por `seller_id`.

## Persistência

- Schema `pedidos_venda_abertos`
- Migrations: `V001__create_seller_portfolio.sql`, `V002__customer_avatars.sql`
- Avatars: `PEDIDOS_VENDA_ABERTOS_AVATAR_UPLOAD_DIR` → `/app/data/pedidos-venda-abertos/avatars` (volume Compose)

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin pedidos-venda-abertos
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin pedidos-venda-abertos
```

## Permissões

| Código | Uso |
|--------|-----|
| `pedidos-venda-abertos.access` | Portal + própria carteira + ver avatar/enrichment |
| `pedidos-venda-abertos.admin` | Configuração, logos, busca SA1, todas as carteiras |

## Fora deste MVP

- Sparkline de tendência / aba Mapa
- Dashboard de desempenho
- Vínculo Protheus SA3 / `C5_VEND`
