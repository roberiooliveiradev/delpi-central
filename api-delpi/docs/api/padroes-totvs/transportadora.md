# Transportadoras (SA4)

Cadastro de transportadoras no Protheus. Usado na solicitação de emissão de NF (`/invoice-issuance/carriers`).

| Campo | Significado Delpi |
|-------|-------------------|
| `SA4010` | Tabela de transportadoras (empresa 010) |
| `A4_COD` | Código |
| `A4_NREDUZ` | Nome de uso na emissão / fila |
| `A4_NOME` | Razão social |
| `A4_CGC` | CNPJ |
| `A4_MSBLQL` | `1` = bloqueada (listar, não selecionar) |

## O que fazer

- Buscar por código, `A4_NREDUZ`, `A4_NOME` ou CNPJ.
- Gravar o **nome reduzido** (`A4_NREDUZ`, fallback `A4_NOME`) e o código `A4_COD`.
- Filtrar `D_E_L_E_T_ = ''`. Leitura analítica com `NOLOCK`.

## O que NÃO fazer

- Confundir transportadora (`SA4`) com fornecedor (`SA2`).
- Usar `A4_NOME` como rótulo principal quando `A4_NREDUZ` existe — o Faturamento identifica pelo reduzido.
- Permitir seleção de cadastro bloqueado (`MSBLQL = 1`).
