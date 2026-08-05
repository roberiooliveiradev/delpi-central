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

| Situação | Label | Cor | Conta pendência? |
|---|---|---|---|
| Login/nome do apontamento = ensaiador do QPR na mesma OP+operação | Inspecionou | verde | não |
| Há inspeção exigível (QPK+QP7/QP8 na revisão da OP, ou QPR de outra pessoa) e o operador não lançou | Não inspecionou | vermelho | sim |
| Sem inspeção amarrada na OP+operação (sem QPK/revisão com essa operação e sem QPR) | Não possui inspeção cadastrada | cinza | não |

A tabela pode filtrar por status via query `inspecao_status` (`all` | `nao_inspecionou` | `inspecionou` | `sem_cadastro`). Na UI o padrão inicial é **Não inspecionou**. Os KPIs do summary continuam do dia inteiro; só a lista/página é filtrada. Sem filtro (`all`), a ordenação é: pendências reais primeiro; depois sem cadastro; depois ok.

Campo de contrato: `tem_inspecao_amarrada` = a OP tem cabeçalho QPK **e** a revisão amarrada (`QPK_REVI`) possui ensaio QP7/QP8 para aquela operação (não usar `MAX(QP6_REVI)` do produto — a OP pode estar em revisão antiga sem a operação apontada).

## Fontes TOTVS

| Fonte | Papel |
|---|---|
| `dbo.vw_Apontamentos_Eficiencia` | Apontamentos do dia |
| `dbo.QPR010` | Ensaios executados (`QPR_OP`, `QPR_OPERAC`, `QPR_ENSR`) |
| `dbo.QPK010` | Cabeçalho de inspeção da OP (`QPK_REVI`, `QPK_PRODUT`) |
| `dbo.QP7010` / `QP8010` | Especificação do produto **na revisão do QPK** (por operação) |
| `dbo.vw_minha_delpi_inspecoes_processo_por_ensaiador` | Mapa matrícula → login/nome |

## Escopo de apontamentos

Espelha o eficiência-fabril: filiais `01`/`02`, `STATUS_REGISTRO = 'OK'`, exclui `CT-00`, `CT-70`, `CT-16A`, `CT-99`.

## Contratos

- API: [inspecoes-processo.md](../../../api-delpi/docs/api/inspecoes-processo.md)
- SQL: `api-delpi/.../inspecoes_processo_auditoria_sql.py`
- UI: aba `?tab=auditoria`
