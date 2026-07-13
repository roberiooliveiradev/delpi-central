# Especificação — Auditoria apontamento × inspeção de processo

> Módulo: **Inspeções de Processo** · Plugin: `inspecoes-processo` · API: `GET /inspecoes-processo/auditoria-apontamentos`

## Objetivo

Listar os **apontamentos produtivos do dia** e cobrar o operador quando ele apontou uma OP+operação e **ele mesmo** não lançou a inspeção de processo correspondente no QIP.

## Regra canônica

```text
Apontamento do dia (EF, STATUS_REGISTRO = OK, CTs produtivos)
  → agrega por operador + OP + operação
  → mesmo operador inspecionou?
       EXISTS QPR010 (filial + OP + operação)
       AND matrícula QPR_ENSR mapeia para o mesmo login/nome do apontamento
```

### Identidade do operador

`COD_OPERADOR` / `H6_OPERADO` = `SYS_USR.USR_ID` (ex.: `000177`), **não** é a matrícula do QIP (`QPR_ENSR`, ex.: `20115`).

Bridge usada:

```text
QPR_ENSR
  → vw_minha_delpi_inspecoes_processo_por_ensaiador (Matricula → Login / Nome)
  → compara com LOGIN_OPERADOR (preferencial) ou NOME_OPERADOR (fallback)
```

### Status na UI

| Situação | Label |
|---|---|
| Login/nome do apontamento = ensaiador do QPR na mesma OP+operação | Operador inspecionou |
| Há QPR na OP+operação, mas de outra pessoa | Pendente (outra pessoa inspecionou) |
| Não há QPR na OP+operação | Pendente (sem inspeção) |

A tabela lista **todos** os apontamentos do dia (pendências primeiro).

## Fontes TOTVS

| Fonte | Papel |
|---|---|
| `dbo.vw_Apontamentos_Eficiencia` | Apontamentos do dia |
| `dbo.QPR010` | Ensaios executados (`QPR_OP`, `QPR_OPERAC`, `QPR_ENSR`) |
| `dbo.vw_minha_delpi_inspecoes_processo_por_ensaiador` | Mapa matrícula → login/nome |

## Escopo de apontamentos

Espelha o eficiência-fabril: filiais `01`/`02`, `STATUS_REGISTRO = 'OK'`, exclui `CT-00`, `CT-70`, `CT-16A`, `CT-99`.

## Contratos

- API: [inspecoes-processo.md](../../../api-delpi/docs/api/inspecoes-processo.md)
- SQL: `api-delpi/.../inspecoes_processo_auditoria_sql.py`
- UI: aba `?tab=auditoria`
