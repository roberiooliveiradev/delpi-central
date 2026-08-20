# Apontamento de operação — `HZA010` e operador `SYS_USR`

Fonte única para responder **"esta operação está sendo produzida agora?"**. A `HZA010` registra abertura e encerramento de cada operação apontada no coletor do chão de fábrica.

Constantes canônicas: `app/domain/totvs/protheus_operation_appointments.py` e `app/domain/totvs/protheus_users.py`.

## Tabela e chave

A tabela física chama-se **`HZA010`** — não existe `SHZA010`. A chave casa 1:1 com a alocação da `SH8010`:

| `HZA010` | `SH8010` |
|---|---|
| `HZA_FILIAL` | `H8_FILIAL` |
| `HZA_OP` (11 posições) | `H8_OP` |
| `HZA_OPERAC` | `H8_OPER` |

## Colunas que importam

| Coluna | Significado |
|---|---|
| `HZA_DTINI` / `HZA_HRINI` | Início do apontamento (`YYYYMMDD` e `HH:MM:SS`) |
| `HZA_DTFIM` / `HZA_HRFIM` | Encerramento; vazios enquanto a operação roda |
| `HZA_OPERAD` | **Usuário Protheus**, não matrícula do RH |
| `HZA_STATUS` | `1` em andamento · `2` encerrado com apontamento gerado · `3` encerrado descartado |
| `HZA_TPTRNS` | `1` mão de obra · `2` máquina (recurso em `HZA_RECUR`) |
| `HZA_IDAPON` | Id do apontamento gerado (só em `HZA_STATUS = '2'`) |

## Nome do operador

`HZA_OPERAD` resolve contra **`SYS_USR`** (`USR_ID` → `USR_NOME`). `SRA010` (RH) e `RD0010` **não** cobrem esses códigos — foram sondados e não batem.

Ambos os lados precisam de `LTRIM`/`RTRIM` porque `USR_ID` vem com padding. Esse predicado não é sargável: **resolva o nome dentro do agregado de apontamentos**, nunca no `SELECT` externo sobre a `SH8` inteira. Na carga máquina isso foi a diferença entre ~2 s e mais de 60 s por consulta.

## "Em produção agora" ≠ status aberto

`HZA_STATUS = '1'` sozinho **não** significa produção em curso: a base acumula milhares de apontamentos abertos e esquecidos desde 2023. O estado ativo exige também recência do início (`ACTIVE_APPOINTMENT_LOOKBACK_DAYS = 2`, folga para o turno noturno que cruza a meia-noite).

Estados derivados canônicos:

| Estado | Regra |
|---|---|
| `in_progress` | Apontamento aberto **e** iniciado dentro da janela de recência |
| `started` | Já teve apontamento no histórico, nenhum ativo agora |
| `not_started` | Sem registro na `HZA010` |

## O que fazer

- Usar `active_appointment_predicate_sql` e `active_marker_sql`; o `MAX` do marcador elege o apontamento mais recente numa única agregação.
- Agregar por operação e trazer contagens (`active_appointment_count`, `appointment_count`) em vez de duplicar linhas da `SH8`.
- Combinar o filtro de data programada com **`OR` apontamento ativo**: quem está na máquina agora costuma ter sido programado ontem e sumiria da janela.

## O que não fazer

- Tratar `HZA_STATUS = '1'` como "rodando" sem janela de recência.
- Buscar o operador em `SRA010`/`RD0010`.
- Fazer `JOIN` de `SYS_USR` fora do agregado de apontamentos.
- Assumir um apontamento por operação: há vários (turnos, operadores, retomadas).

## Consumidores

- [production-machine-load.md](../production-machine-load.md) — status de produção da carga máquina.
