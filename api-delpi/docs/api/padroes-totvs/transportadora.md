# Transportadoras (SA4)

Cadastro de transportadoras no Protheus. Usado na solicitação de emissão de NF (`/invoice-issuance/carriers`).

| Campo | Significado Delpi |
|-------|-------------------|
| `SA4010` | Tabela de transportadoras (empresa 010) |
| `A4_COD` | Código |
| `A4_NREDUZ` | Nome de uso na emissão / fila |
| `A4_NOME` | Razão social |
| `A4_CGC` | CNPJ |
| `A4_END` / `A4_BAIRRO` / `A4_MUN` / `A4_EST` / `A4_CEP` | Endereço (rua, bairro, município, UF, CEP) |
| `A4_DDD` / `A4_TEL` | Telefone (DDD + número) |
| `D_E_L_E_T_` | Exclusão lógica — único filtro de “inativa” neste cadastro |

A `SA4010` da Delpi **não tem** `A4_MSBLQL` (38 colunas; bloqueio `MSBLQL` existe em `SA1`/`SA2`/`SB1`, não em `SA4`). Consultar essa coluna derruba a busca (erro SQL → 5xx no lookup).

## O que fazer

- Buscar por código, `A4_NREDUZ`, `A4_NOME` ou CNPJ.
- Gravar na solicitação o **snapshot** (código, reduzido, razão, CNPJ, endereço e telefone) — a ficha do Faturamento não depende de nova consulta SA4.
- Filtrar `D_E_L_E_T_ = ''`. Leitura analítica com `NOLOCK`.

## O que NÃO fazer

- Confundir transportadora (`SA4`) com fornecedor (`SA2`).
- Usar `A4_NOME` como rótulo principal quando `A4_NREDUZ` existe — o Faturamento identifica pelo reduzido.
- Selecionar `A4_MSBLQL` — o campo não existe nesta base.
