# Cadastro de cliente (SA1)

Convenções Delpi ao buscar / identificar cliente TOTVS para Portal Comercial e emissões.

## Campos de nome

| Campo | Uso |
|-------|-----|
| `A1_NOME` | Razão social |
| `A1_NREDUZ` | Nome fantasia / reduzido operacional (pedidos, gap, Minha carteira) |

Busca de vínculo de carteira (`search_active_customers`) deve casar em **código**, **`A1_NOME`** e **`A1_NREDUZ`**. Display preferencial: `COALESCE(NULLIF(RTRIM(A1_NREDUZ), ''), A1_NOME)`.

O centro que separa unidades do mesmo código **não** é nome nem loja. Ele fica em `SA7.A7_XCENT`. Ver [centro-cliente.md](./centro-cliente.md).

Referência de implementação: lookup NF (`TotvsInvoiceIssuanceLookupRepository.search_customers`) já inclui `A1_NREDUZ`.

## Bloqueio (`A1_MSBLQL`)

- `'1'` = bloqueado/inativo no cadastro; `'2'` (ou legado vazio) = ativo.
- **Domínio de Carteiras opera somente com clientes ativos**: `A1_MSBLQL <> '1'` é exigência de elegibilidade — vale para o universo «sem cobertura», métricas de pedidos abertos por cliente, busca de vínculo e validação backend de writes (criação/inclusão/substituição/transferência).
- Superfícies de consulta fora de Carteiras (Conta 360, mentions, busca genérica) continuam incluindo bloqueados — a busca SA1 expõe `include_blocked` (default `true`) e o chamador decide.
- BFF → api-delpi: `GET /customers/search?include_blocked=false`; elegibilidade em lote via `POST /customers/enrichment` (campo `blocked`).

## Loja (`A1_LOJA` / `C5_LOJACLI`)

Loja numérica: normalizar com `zfill(2)` (`1` → `01`) em chaves de cobertura / identidade. SC5 e SA1 podem divergir no padding. Na agregação de métricas, o join SA1×SC5 casa loja por igualdade **ou** por `TRY_CAST(… AS INT)`.

## Gap «sem cobertura» × cadastro

Universo operacional = pedidos abertos **∩ SA1 ativa** (`tipo_entidade='CLIENTE'` da view + `A1_MSBLQL <> '1'` + `D_E_L_E_T_` vazio). Código só no SC5 (órfão, sem linha em `SA1010`) **não** entra no gap nem na busca de vínculo — regularizar cadastro no Protheus antes de amarrar carteira.

### Colisão cliente × fornecedor

`C5_CLIENTE`/`C5_LOJACLI` podem carregar código de **fornecedor SA2** (ex.: pedidos de beneficiamento `C5_TIPO='B'`). SA1 e SA2 são entidades distintas que compartilham o espaço de códigos — `000006/01` pode ser um cliente e um fornecedor diferentes. Consultas com semântica de **cliente** devem filtrar `v.tipo_entidade = 'CLIENTE'` da `VW_PEDIDOS_VENDA_ABERTOS_COMPRADORES`; consultas de **pedidos** preservam os dois tipos e resolvem o nome pela entidade real (`nome_cliente` da view; em queries diretas ao SC5, `C5_TIPO='B'` resolve na SA2).

## Segmento comercial (WEG × novos negócios)

Heurística transversal (`CommercialCustomerSegmentService`): WEG = `A1_COD` / cliente da linha = `000001`; **novos negócios** = demais. Usada em ROL %, OTD e na carteira semanal previsto × realizado — ver [carteira-semanal-previsto-realizado.md](./carteira-semanal-previsto-realizado.md).
