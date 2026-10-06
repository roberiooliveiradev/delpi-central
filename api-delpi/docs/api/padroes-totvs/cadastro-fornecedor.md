# Cadastro de fornecedor (SA2)

Convenções Delpi ao buscar / identificar fornecedor TOTVS. Detalhe completo (248 campos, índices, relações, dependências de CREATE/UPDATE): [playbook-cadastro-fornecedor-sa2.md](./playbooks/playbook-cadastro-fornecedor-sa2.md).

## Identidade e chave

| Item | Regra |
|------|-------|
| Chave de negócio | `A2_FILIAL + A2_COD + A2_LOJA` (única física: `SA2010_UNQ`) |
| `A2_CGC` (CNPJ/CPF) | **Não** é chave — duplicado em base (mesmo CGC com códigos distintos) e pode ser vazio |
| `A2_LOJA` | Convenção `'01'`; base contém valores sujos (`'1 '`, `' 1'`) — normalizar com `RTRIM`/`zfill(2)` |
| `A2_FILIAL` | Branco = cadastro compartilhado entre filiais (MODO=C); nunca filtrar por filial fixa sem tratar branco |

## Geração de código

`A2_COD` default = `GETSXENUM("SA2")` (sequencial 6 dígitos, ex.: `003929`) nas empresas 01 e 05. Empresas 03/04 **não têm** o default, e existem códigos manuais (`VIAGEM`, `FISCO`, `UNIAO`…). A ponte/API de escrita não deve gerar `MAX+1` próprio — delegar à rotina Protheus.

## Bloqueio (`A2_MSBLQL`)

`'1'` = bloqueado (104 registros); `'2'` = ativo; **vazio** em ~4% — tratar branco como "não bloqueado" somente após decisão de contrato (ver playbook §26/§39).

## Campos DELPI na SA2

| Campo | Significado |
|-------|-------------|
| `A2_YROHS` | RoHS? (67% preenchido; marcado obrigatório no dicionário) |
| `A2_YFGEN` | Fornecedor genérico |
| `A2_ZTABPRC` | Tabela de preço de compra → `AIA` |

## O que NÃO fazer

- Não assumir `SA2` = todo o cadastro: bancário e contato estão **na própria SA2** (conta única; PIX é dado de pagamento financeiro, não do cadastro).
- Não confundir `SA5` (produto × fornecedor, rotina MATA061) com o cadastro (MATA020) — fornecedor existe sem SA5; amarração é operação separada.
- Não usar `A2_GRUPO` como grupo real — não é povoado; grupos vivem em `SAD` (Grupo × Fornecedor).
- Não enviar campos técnicos (`D_E_L_E_T_`, `R_E_C_*`, `S_T_A_M_P_`, `I_N_S_D_T_`) nem acumuladores (`A2_MCOMPRA`, `A2_ULTCOM`…) em CREATE/UPDATE.

## Lookups frequentes

`A2_EST`→SX5 `'12'`; `A2_COD_MUN`→CC2 (por UF); `A2_CODPAIS`→CCH (`01058` = Brasil); `A2_PAIS`→SYA; `A2_COND`→SE4; `A2_NATUREZ`→SED; `A2_BANCO`→SA6; `A2_CONTA`→CT1; `A2_FORMPAG`→SX5 `'58'`.
