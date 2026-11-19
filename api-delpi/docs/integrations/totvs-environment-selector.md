# Seletor lógico de ambiente TOTVS — `TOTVS_TARGET_ENV`

Status: implementado (fail-closed), **não ativado** em nenhum ambiente
operacional. Origem: `EVA-TOTVS-G2B-ENVIRONMENT-RESOLUTION-AND-SA5-READ-01`
e hardening `EVA-TOTVS-ENVIRONMENT-SELECTOR-SAFETY-HARDENING-01`.
Código: `app/infrastructure/providers/totvs/environment.py`.

## O que faz

Uma única escolha lógica backend resolve dois destinos independentes:

- **SQL TOTVS** — nome do banco de negócio no pool ODBC.
- **REST Protheus** — conjunto de parâmetros `INTRANET_PARAMS_AMBIENTE`
  (que contém `URL_REST`, credenciais e paths oficiais).

O seletor **não** substitui credenciais, connection strings, o pin
`PROTHEUS_REST_EXPECTED_BASE_URL`, feature gates nem AuthZ do Core.

## Catálogo aprovado

| `TOTVS_TARGET_ENV` | `sql_database` | `PARAMETROS_AMBIENTE` |
|---|---|---|
| `TST01` | `DELPI_TST01` | `2` |
| `PROD` | `DELPI` | `1` |

Valores fora do catálogo → `RuntimeError` (fail closed).

## Matriz de runtimes autorizados (`API_DELPI_ENV`)

| Runtime (`API_ENV`) | `TST01` | `PROD` |
|---|---|---|
| DEV (`development`) | permitido | **bloqueado** |
| HML (`homologation`) | permitido | **bloqueado** |
| PROD (`production`) | bloqueado sem política explícita | permitido |
| não classificável | bloqueado | bloqueado |

## Regras fail-closed

- Seletor inválido, divergência `TOTVS_DB_DATABASE` ou
  `INTRANET_PARAMS_AMBIENTE` contra o catálogo → erro, nenhum destino.
- `sql_read_enabled=False` (banco `DISABLED`/ausente) → nenhuma conexão
  é aberta (`build_totvs_connection_string` falha antes do `pyodbc`).
- `DISABLED` nunca faz fallback para `DB_DATABASE`.
- Destino do pool congelado na primeira conexão — mudança de config em
  runtime → erro; conexão `DELPI` nunca é reutilizada como `DELPI_TST01`.
- Nenhum parâmetro de request influencia a resolução.
- `rest_write_pin_configured` só reporta a existência do pin — nunca
  prova destino correto nem autoriza escrita. Gates `*_ENABLED` OFF,
  `assert_protheus_write_target` e AuthZ Core continuam independentes.

## Modo legado (seletor ausente)

Comportamento idêntico ao anterior: `TOTVS_DB_DATABASE` (ou `DB_DATABASE`)
e `INTRANET_PARAMS_AMBIENTE` explícitos. Novo: banco `DISABLED`/ausente
bloqueia a conexão (antes falharia depois, no driver).

## Ativação futura (procedimento)

1. Definir `TOTVS_TARGET_ENV` no `.env` governado do ambiente
   (TST01 em DEV/HML; PROD em PROD) — alteração separada e aprovada.
2. Garantir `API_DELPI_ENV` correto (matriz acima).
3. Alinhar ou remover `TOTVS_DB_DATABASE`/`INTRANET_PARAMS_AMBIENTE`
   explícitos (divergência falha fechada por desenho).
4. Manter `PROTHEUS_REST_EXPECTED_BASE_URL` e gates como estão.
5. Rodar `tests/test_totvs_environment.py` + smoke de leitura antes e
   depois da ativação.

## Rollback

Remover `TOTVS_TARGET_ENV` do `.env` → modo legado. Nenhum código
precisa ser revertido.

## GET SA5

`ProductSuppliersRepository.get_supplier_link()` lê o vínculo pela chave
integral (7 campos), retorna `None` se inexistente e erro explícito se a
PK retornar mais de uma linha (anomalia). SQL read-only — nunca caminho
de escrita Protheus. `WITH (NOLOCK)` não é prova de pós-condição de
escrita; homologação de escrita exige read-back separado.
