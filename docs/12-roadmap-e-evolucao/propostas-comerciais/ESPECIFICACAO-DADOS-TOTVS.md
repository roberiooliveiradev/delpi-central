# Especificação de dados — Propostas Comerciais (TOTVS / Protheus)

> **Status:** implementado (jun/2026)  
> **Objetivo:** contrato read-only entre SQL Server, `api-delpi` e plugin MFE  
> **Implementação:** `api-delpi/app/infrastructure/totvs/propostas_comerciais/queries.py`

---

## 1. Escopo

- **Somente leitura** — nenhuma escrita no Protheus.
- **Sem view SQL dedicada** — joins diretos nas tabelas padrão do módulo comercial/CRM.
- Propostas com **`ADY_STATUS = 'A'`** (ativas).
- Identificador principal na API/UI: **`proposta_interna`** (`ADY_PROPOS`).

---

## 2. Tabelas envolvidas

| Alias | Tabela | Papel |
|-------|--------|--------|
| `ADY` | `ADY010` | Cabeçalho da proposta comercial |
| `AD1` | `AD1010` | Oportunidade de venda (vínculo prospect/cliente) |
| `ADZ` | `ADZ010` | Itens da proposta |
| `A1` | `SA1010` | Cadastro de **clientes** |
| `SUS` | `SUS010` | Cadastro de **prospects** |
| `U5` | `SU5010` | Contato comercial |
| `QB` | `SQB010` | Departamento do contato |
| `E4` | `SE4010` | Condição de pagamento |
| `A3` | `SA3010` | Vendedor |
| `UM` | `SUM010` | Cargo do vendedor |
| `B1` | `SB1010` | Cadastro de produtos (itens) |
| `CO` | `SYS_COMPANY` | Dados da filial emissora (empresa DELPI) |

Todas as tabelas Protheus respeitam `D_E_L_E_T_ <> '*'`.

---

## 3. Joins principais (`_COMMON_JOINS`)

```text
ADY010 ADY
  LEFT JOIN AD1010 AD1
    ON AD1.AD1_NROPOR = ADY.ADY_OPORTU
   AND AD1.AD1_REVISA = ADY.ADY_REVISA

  LEFT JOIN SA1010 A1
    ON A1.A1_COD = ADY.ADY_CLIENT
   AND A1.A1_LOJA = ADY.ADY_LOJENT

  LEFT JOIN SUS010 SUS
    ON SUS.US_COD = AD1.AD1_PROSPE
   AND SUS.US_LOJA = AD1.AD1_LOJPRO

  LEFT JOIN SU5010 U5  (contato)
  LEFT JOIN SQB010 QB  (departamento)
  LEFT JOIN SE4010 E4  (condição pgto)
  LEFT JOIN SA3010 A3  (vendedor)
  LEFT JOIN SUM010 UM  (cargo)
  LEFT JOIN SYS_COMPANY CO  (filial emissora)
```

### Filial emissora

```sql
RTRIM(CO.M0_CODFIL) = RTRIM(COALESCE(NULLIF(RTRIM(ADY.ADY_FILIAL), ''), AD1.AD1_FILIAL))
AND RTRIM(CO.M0_CODIGO) = '01'
```

Endereço da **empresa** no PDF/detalhe vem de `SYS_COMPANY` (filial), não de `SA1010`.

---

## 4. Cliente vs prospect

Algumas propostas não possuem `ADY_CLIENT` / `ADY_LOJENT` preenchidos — a oportunidade está ligada a um **prospect** (`AD1_PROSPE` / `AD1_LOJPRO`), não a um cliente `SA1010`.

| Situação | Origem dos dados | `tipo_cadastro` |
|----------|------------------|-----------------|
| `A1.A1_COD` preenchido (após trim) | `SA1010` | `cliente` |
| `A1` vazio e `SUS.US_COD` preenchido | `SUS010` | `prospect` |
| Ambos vazios | Campos de cliente vazios | `null` |

Regra de detecção (SQL):

```sql
CASE
  WHEN NULLIF(LTRIM(RTRIM(A1.A1_COD)), '') IS NOT NULL THEN 'cliente'
  WHEN NULLIF(LTRIM(RTRIM(SUS.US_COD)), '') IS NOT NULL THEN 'prospect'
  ELSE NULL
END AS cliente_tipo_cadastro
```

### Mapeamento de campos (COALESCE SA1 → SUS)

| Campo API (`cliente.*`) | Cliente (`SA1010`) | Prospect (`SUS010`) |
|-------------------------|--------------------|---------------------|
| `codigo` | `A1_COD` | `US_COD` |
| `loja` | `A1_LOJA` | `US_LOJA` |
| `nome` | `A1_NOME` | `US_NOME` |
| `nome_fantasia` | `A1_NREDUZ` | `US_NREDUZ` |
| `cnpj` | `A1_CGC` | `US_CGC` |
| `ie` | `A1_INSCR` | `US_INSCR` |
| `endereco` | `A1_END` | `US_END` |
| `bairro` | `A1_BAIRRO` | `US_BAIRRO` |
| `cidade` | `A1_MUN` | `US_MUN` |
| `uf` | `A1_EST` | `US_EST` |
| `cep` | `A1_CEP` | `US_CEP` |
| `telefone` | `A1_TEL` | `US_DDD` + `US_TEL` (concatenados) |
| `email` | — | `US_EMAIL` (somente prospect) |

Listagem (`cliente_nome`): `COALESCE(A1_NOME, SUS.US_NOME)`.

### Caso validado — prospect

| Campo | Valor |
|-------|--------|
| Proposta interna | `004836` |
| OV | `OV003590` |
| Oportunidade | `003590` |
| Prospect | `000091` / loja `01` — KRAH-ICE-BRASIL LTDA |

---

## 5. Filtros de listagem e detalhe

| Regra | SQL / comportamento |
|-------|---------------------|
| Propostas ativas | `ADY.ADY_STATUS = 'A'` |
| Ordenação listagem | `ADY_DATA DESC`, `ADY_PROPOS DESC`, `ADY_PREVIS DESC` |
| Limite listagem | `TOP (?)` — parâmetro `limit` (1–200, default 100) |
| Detalhe | `ADY_PROPOS = ?` + `TOP 1` |
| Itens | `ADZ_PROPOS = ?` e revisão = `ADY_PREVIS` da proposta ativa |

---

## 6. Itens (`DETAIL_ITEMS_SQL`)

| Campo API | Origem |
|-----------|--------|
| `item` | `ADZ_ITEM` |
| `produto` | `ADZ_PRODUT` |
| `descricao` | `COALESCE(ADZ_DESCRI, B1_DESC)` |
| `referencia_cliente` | `B1_REFEREN` |
| `ncm` | `B1_POSIPI` |
| `quantidade` | `ADZ_QTDVEN` |
| `unidade` | `ADZ_UM` |
| `preco_unitario` | `ADZ_PRCVEN` |
| `valor_total` | `ADZ_TOTAL` |
| `prazo_dias` | `ADZ_PRAZO` |
| `lote_minimo` | `ADZ_LTEMIN` |

---

## 7. Campos derivados no formatter (Python)

Formatação canônica em `PropostaComercialFormatter` — **não duplicar no MFE**:

| Campo | Regra |
|-------|--------|
| `numero_ov` | Prefixo `OV` + código da oportunidade |
| `cnpj`, `cep`, `ncm` | Máscaras pt-BR |
| `telefone` | Normalização `(DD) NNNN-NNNN` |
| `data` | `dd/MM/yyyy` (datas Protheus `YYYYMMDD`) |
| `soma_valores_r_mil` | Moeda BRL (`R$ …`) — valores em milheiros no Protheus |
| `condicoes.frete` | `C` → CIF; `F` → FOB |
| `condicoes.embalagem` | `1` → «Embalagem padrão DELPI» |
| `condicoes.icms` | Percentual formatado |
| `is_prospect` | `true` quando `tipo_cadastro == "prospect"` |

---

## 8. Observações técnicas

- Campo memo `ADY_OBS`: `REPLACE(..., CHAR(0), '')` para remover null bytes.
- Contato: `COALESCE(ADY_CNTPRO, AD1_CNTPRO)` → join `SU5010`.
- A API **não altera** dados no Protheus; overrides de PDF existem apenas na geração do arquivo exportado.

---

## 9. Arquivos de referência

| Arquivo | Responsabilidade |
|---------|------------------|
| `queries.py` | SQL read-only |
| `proposta_comercial_repository.py` | Execução via `BaseRepository` |
| `proposta_comercial_formatter.py` | Contrato JSON da API |
| `test_propostas_comerciais.py` | Regressão (cliente, prospect, PDF) |
