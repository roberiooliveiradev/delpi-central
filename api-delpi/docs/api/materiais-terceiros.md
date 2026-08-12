# Materiais de Terceiros — API

Rotas somente leitura sobre a view TOTVS `dbo.VW_PD3_BENEF_RETORNOS` (`SB6` remessa × retornos). Relacionamento **somente** por `B6_FILIAL + B6_PRODUTO + B6_IDENT` — não usar `B6_TPCF` nem `B6_IDENTB6` como chave.

Plugin MFE: [plugins/materiais-terceiros/README.md](../../../plugins/materiais-terceiros/README.md).  
Padrões: [padroes-totvs/materiais-terceiros-sb6.md](./padroes-totvs/materiais-terceiros-sb6.md).

---

## Base

`/apps/api-delpi/supplies/third-party-materials`

Envelope padrão `{ success, message, data, meta }`. `branch` obrigatório (`01` \| `02`).

---

## Endpoints

| Método | Rota | `operationId` | Shape |
|--------|------|---------------|-------|
| GET | `/shipments` | `get_supplies_third_party_materials_shipments` | paged_list |
| GET | `/shipments/{shipment_recno}` | `get_supplies_third_party_materials_shipment` | playbook_report |
| GET | `/summary` | `get_supplies_third_party_materials_summary` | scalar |
| GET | `/returns/export` | `export_supplies_third_party_materials_returns` | document_export |

Paginação da lista: **por remessa** (2 etapas: `DISTINCT RECNO_REMESSA` + detalhe `IN`). A view tem 1 linha por retorno; saldo/qtd recebida se repetem — nunca somar nas linhas detalhadas.

Detalhe do retorno: `TIPO_PARCEIRO_RETORNO` (C/F). Código/loja do parceiro no retorno **não** existem na view homolog — não selecionar `COD_PARCEIRO_RETORNO` / `LOJA_PARCEIRO_RETORNO`.

Ref. Cliente (`SB1.B1_REFEREN`) **não** está na view live — a API faz `LEFT JOIN SB1010` e expõe `product.customer_reference`.

### Query params

| Param | Descrição |
|-------|-----------|
| `branch` | Filial TOTVS `01`/`02` (obrigatório) |
| `product` | Código do produto |
| `customer_reference` | Ref. Cliente (`SB1.B1_REFEREN`) — prefixo, case-insensitive |
| `partner_code` / `partner_store` | Cliente SA1 |
| `receipt_number` / `return_number` | NF entrada / NF retorno |
| `issued_from` / `issued_to` | Emissão da remessa (ISO) |
| `status` | `completed` \| `partial` \| `no_return` |
| `only_with_balance` | Só remessas com saldo |
| `include_test_products` | Default `false` — oculta `THIRD_PARTY_MATERIALS_IGNORED_PRODUCTS` (padrão `99999999`) |
| `page` / `page_size` | Cap 100 |
| `export_format` | `csv` \| `xlsx` (só export) |

### Permissões

- `materiais-terceiros.access` (ou `api-delpi.access`)
- `materiais-terceiros.view.filial-sc` / `.view.filial-es`
- `materiais-terceiros.export`

Toda rota com `branch` passa por `branch_access_error`.

### Exportação

Uma linha por retorno. Header `X-Export-Notice` e comentário no CSV: saldo da remessa se **repete**. Não some `pending_balance` / `received_quantity` nas linhas detalhadas.

---

## View TOTVS

Arquivo versionado: `app/infrastructure/persistence/totvs/third_party_materials/VW_PD3_BENEF_RETORNOS.sql`.

Validação Fase 0 (homolog):

```bash
python api-delpi/scripts/validate_third_party_materials_view.py
```

Aceite esperado (filial `01`, produto `10211413`): 43 remessas, 397 retornos, 3 com saldo, pendente 11419, `ABS(DIFERENCA_CONTROLE) > 0.000001` = 0.

A api-delpi **só consulta**. DBA aplica/confere a view no SQL Server antes do smoke live.

---

## Performance

- Filial sempre obrigatória; sem dump da base no primeiro load do MFE.
- Sem cache na v1. Medir plano em homolog antes de criar índice.
