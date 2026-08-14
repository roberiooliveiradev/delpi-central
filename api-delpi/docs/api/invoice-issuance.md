# Emissão de Notas Fiscais — `/invoice-issuance`

Fila de **solicitação de emissão** de NF (saída) para o Faturamento. Destinatário obrigatório no TOTVS (`SA1` cliente ou `SA2` fornecedor). Sem conciliação `SF2` nesta versão.

| Permissão | Uso |
|-----------|-----|
| `invoice-issuance.access` | Abrir o MFE |
| `invoice-issuance.create` | Criar, corrigir própria `returned`, cancelar própria `pending` |
| `invoice-issuance.view` | Consultar todas as solicitações (ambas filiais) |
| `invoice-issuance.view.filial-01` / `.filial-02` | Menu + gate de filial na API |
| `invoice-issuance.process` | Iniciar, devolver, marcar emitida, cancelar em atendimento |
| `invoice-issuance.manage` | Admin + cancelar não terminais |

**Caller header (MFE):** `X-Delpi-Caller-App: invoice-issuance`

Plugin: `plugins/invoice-issuance` · Roadmap: [docs/12-roadmap-e-evolucao/invoice-issuance/](../../../docs/12-roadmap-e-evolucao/invoice-issuance/).

**Persistência:** schema Postgres `invoice_issuance` (migrations `V001`–`V003` em `api-delpi/migrations/plugins/invoice-issuance/`). Aplicar **somente** com `up` — nunca `reset` em produção.

## Rotas

| Método | Rota | `operationId` | Permissão |
|--------|------|---------------|-----------|
| GET | `/invoice-issuance/parties` | `search_invoice_issuance_parties` | create/process/manage |
| GET | `/invoice-issuance/products` | `search_invoice_issuance_products` | create/process/manage |
| GET | `/invoice-issuance/products/{code}/warehouse-01-balance` | `get_invoice_issuance_warehouse_01_balance` | create/process/manage |
| GET | `/invoice-issuance/open-sales-orders` | `list_invoice_issuance_open_sales_orders` | create/process/manage |
| GET | `/invoice-issuance/carriers` | `search_invoice_issuance_carriers` | create/process/manage |
| POST | `/invoice-issuance/requests` | `create_invoice_issuance_request` | create/process/manage |
| GET | `/invoice-issuance/requests` | `list_invoice_issuance_requests` | qualquer read* |
| GET | `/invoice-issuance/requests/{id}` | `get_invoice_issuance_request` | qualquer read* |
| PATCH | `/invoice-issuance/requests/{id}` | `update_invoice_issuance_request` | criador + `returned` |
| POST | `/invoice-issuance/requests/{id}/resubmit` | `resubmit_invoice_issuance_request` | criador + `returned` |
| POST | `/invoice-issuance/requests/{id}/start` | `start_invoice_issuance_request` | process/manage |
| POST | `/invoice-issuance/requests/{id}/return` | `return_invoice_issuance_request` | process/manage |
| POST | `/invoice-issuance/requests/{id}/issue` | `issue_invoice_issuance_request` | process/manage |
| POST | `/invoice-issuance/requests/{id}/cancel` | `cancel_invoice_issuance_request` | create† / process‡ / manage |

\* `access|create|view|view.filial-*|process|manage`  
† `create`: somente própria em `pending`  
‡ `process`: em `in_progress`

Query `parties`: `party_type=customer|supplier`, `query` (mín. 2 caracteres — código, nome ou CNPJ). Bloqueados (`MSBLQL=1`) vêm na lista mas não são selecionáveis no MFE.

Query `open-sales-orders`: `branch` (`01`/`02`), `party_code` e `party_store` do **cliente** (SA1). Retorna pedidos agrupados com linhas em saldo (`saldo > 0`) só da filial do wizard. Sem membership comercial / PVA.

Query `carriers`: `query` (mín. 2 caracteres — código `A4_COD`, nome reduzido `A4_NREDUZ`, razão `A4_NOME` ou CNPJ). Nome de uso = `A4_NREDUZ`. Bloqueadas (`MSBLQL=1`) vêm na lista mas não são selecionáveis. Transportadora é opcional.

Query `requests`: `branch` obrigatório (`01`/`02`); `status` (`open` = pending/in_progress/returned); `invoice_type`; `q`.

## Estados

`pending` → `in_progress` → `issued` | `returned` | `cancelled`.  
`returned` → (PATCH + resubmit) → `pending`.

Itens de **venda** e **devolução** nascem com `stock_write_off=true` (baixa de estoque). Amostra, conserto e outros nascem sem baixa. O cliente pode desmarcar; valor explícito no payload prevalece. No wizard o tipo de NF vem **antes** dos itens, para esse padrão já valer ao incluir o produto. Com baixa marcada, a UI mostra o saldo do almoxarifado 01.

## Notificações

Requer `CORE_API_BASE_URL` + `CORE_API_INTEGRATIONS_SERVICE_TOKEN` e `INVOICE_ISSUANCE_NOTIFICATIONS_ENABLED=true` (default).

- Cadastro/reenvio → sino para quem tem `invoice-issuance.process` (`permissionCodes`, exclui o ator)
- Devolução / emissão / cancelamento → sino para o solicitante (`userIds`)

Deep link: `/apps/invoice-issuance/filial-0x?requestId={id}`. Categoria Core: `invoice_issuance`.

## Lookups TOTVS

- Clientes: `SA1` com `A1_CGC` (CNPJ)
- Fornecedores: `SA2` (`TotvsSupplierRepository`)
- Itens: `SB1` (permissão do plugin, não `ENGINEERING_LMP_ACCESS`)
- Saldo informativo: `SB2` `B2_LOCAL = 01` (almoxarifado). Não bloqueia o envio.
- Pedidos de venda em aberto: view `VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES` (mesmo lookup TOTVS da conta 360, **sem** carteira). Só para destinatário cliente; filtrado pela filial da solicitação.
- Transportadoras: `SA4` (`A4_COD`, nome de uso `A4_NREDUZ`, fallback `A4_NOME`). Ver [padroes-totvs/transportadora.md](./padroes-totvs/transportadora.md).

## Migrations

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin invoice-issuance
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin invoice-issuance
```

## Smoke

```bash
BASE=http://localhost/apps/api-delpi/invoice-issuance
curl -s "$BASE/parties?party_type=customer&query=acme" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Delpi-Caller-App: invoice-issuance"
```
