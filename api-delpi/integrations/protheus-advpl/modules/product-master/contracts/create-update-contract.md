# Contratos CRUD — product-master (SB1 / MATA010)

Fonte candidato: `src/DLP04I01.PRW` (`SOURCE_CANDIDATE`, sem compilação).
Catálogo canônico de campos: `contracts/sb1-field-matrix.json`
(SX3 do TST01, **319 campos** — paridade com PROD confirmada na sessão
de inventário).

## Superfície REST

| Verbo | Path | Operação | Rotina | ExecAuto op |
|---|---|---|---|---|
| POST | `/v1/IncProduto/incluir` | `product.create` | `MATA010` | 3 (inclusão) |
| PUT  | `/v1/IncProduto/alterar` | `product.update` | `MATA010` | 4 (alteração) |
| GET  | `/v1/IncProduto/metadados` | `product.metadata` | — | — (estático) |
| DELETE | `/v1/IncProduto/excluir` | `product.delete` | — | **BLOCKED** |

`product.read` (ficha completa) **não** é implementado no `.PRW`:
permanece na superfície governada de leitura da api-delpi (SELECT SB1),
conforme regra — SQL de leitura não define nem substitui mecanismo ADVPL.

`Content-Type: application/json`. Resposta `RETOBJ`:
`{"code","message","detailedMessage","id"}` + HTTP `200` (sucesso) ou
`400`/`404`/`409`/`501` conforme a operação.

## Catálogo de campos — contrato upstream v2

O `.PRW` carrega o catálogo completo de campos elegíveis: **285 campos**
(285 `READ_WRITE_ELIGIBLE` + `B1_COD` como chave; 5 campos memo SX3 sem coluna física classificados `TO_INVENTORY`, fora do contrato).
Os **28 protegidos** (`SYSTEM_MANAGED`/`IMMUTABLE`, exceto `B1_COD`) são
rejeitados explicitamente se enviados.

### product.create (POST)

- `B1_COD` **obrigatório** (chave do novo registro, ≤15 chars).
- Campos elegíveis ausentes são **omitidos do array ExecAuto** — a
  MATA010 aplica seus defaults oficiais e permanece autoridade final de
  obrigatoriedade de negócio (o contrato não inventa valores nem importa
  obrigatoriedade do contrato antigo de 22 campos).
- `null` JSON é indistinguível de ausente no `JsonObject`; em campo
  informado com tipo inválido → `400`.

### product.update (PUT) — representação completa

- `B1_COD` **obrigatório** para localizar o registro.
- A fachada ADVPL exige **todos os 285 campos do catálogo** (campo
  ausente → `400` com a lista). Representação completa é invariante:
  omitir campo em ExecAuto de alteração pode zerar o cadastro.
- **Atualização parcial é responsabilidade do consumidor governado**:
  a api-delpi lê o snapshot SB1 completo (`SELECT` read-only), faz merge
  do delta do cliente e envia a representação completa. Ausência no
  delta nunca vira vazio.

### product.metadata (GET)

Autodescrição do contrato (não lê dados do ERP):

```json
{"entity":"SB1","routine":"MATA010","mechanism":"MSExecAuto",
 "fields":[{"field":"B1_COD","kind":"C"}, ...],
 "fields_count":285,"matrix_ref":"contracts/sb1-field-matrix.json"}
```

`kind` ∈ `C|N|D|M`. A fonte única de verdade completa (descrição, size,
decimals, classificação, status) continua sendo `sb1-field-matrix.json`.

### product.delete (DELETE) — BLOCKED

Semântica oficial de exclusão da MATA010 (op 5) **não comprovada** no
inventário desta sessão (sem fonte MATA010 disponível no espelho, PEs
de ambiente não inventariados, restrições por movimentações/vínculos
SA5/SB2 não mapeadas). O método responde `501` `not_homologated` —
nunca executa exclusão. Produto inexistente em PUT não recebe `404`
dedicado na fachada — a MATA010 reporta via `GetAutoGrLog()` (400);
o `404` `PROTHEUS_PRODUCT_NOT_FOUND` existe na camada api-delpi, que
lê o snapshot antes de escrever.

## Regras de tipo (por campo, conforme SX3)

- **Numérico** (`kind=N`): aceita `N` nativo do JSON ou string no
  formato `lIsNumStr` — sinal opcional **somente** na 1ª posição,
  ≥1 dígito, ≤1 ponto decimal `.`, sem separador de milhar e sem
  espaços. Rejeitados: `"abc"`, `"12x"`, `" "`, `"1,2,3"`, `null`.
  `"0"` e `0` são válidos.
- **Caractere** (`kind=C`): somente `ValType "C"` — objeto, array,
  booleano e número são rejeitados; nenhuma conversão automática.
- **Data** (`kind=D`): string `AAAAMMDD` (8 dígitos).
- **Memo** (`kind=M`): os 5 campos memo SX3 estão `TO_INVENTORY` (sem coluna física no TST01) e não integram o catálogo;
  gravação efetiva do conteúdo memo depende de validação no TST01 —
  campos marcados `VALIDAR NO TST01` na matriz.
- Validação de catálogo pertence à fachada ADVPL; regras finais de
  negócio permanecem na MATA010.

## Erros

Envelope `RETOBJ`: `{"code","message","detailedMessage","id","errorType"}`.
`errorType` ∈ `client_error | official_validation | server_error |
not_homologated` (vazio em sucesso).

| Causa | HTTP | errorType | detailedMessage |
|---|---|---|---|
| JSON inválido | 400 | client_error | "Corpo da requisicao nao e um JSON valido" |
| Campo desconhecido, protegido ou tipo inválido | 400 | client_error | "Campos desconhecidos, protegidos ou invalidos: …" |
| PUT sem representação completa | 400 | client_error | "Alteracao exige representacao completa — campos ausentes (N): …" |
| `B1_COD` ausente (POST) | 400 | client_error | "Campos obrigatorios ausentes: B1_COD." |
| Erro oficial MATA010 | 400 | official_validation | `GetAutoGrLog()` sanitizado (trim, ≤2000 chars) |
| Exceção runtime | 500 | server_error | `e:Description` truncada — **sem** `ErrorStack` |
| DELETE | 501 | not_homologated | "Exclusao de produto nao habilitada: semantica oficial de exclusao da MATA010 pendente de comprovacao (TO_INVENTORY). Nenhuma operacao foi executada no ERP." |

## Dependências e requisitos de compilação

- Includes: `TOTVS.CH`, `RESTFUL.CH`, `TOPCONN.CH`, `TBICONN.CH`, `FWMVCDef.ch`.
- `MSExecAuto({|x,y| Mata010(x,y)}, aSB1, 3|4)` +
  `PRIVATE lMsErroAuto/lMsHelpAuto/lAutoErrNoFile`.
- Sem dependência de outros módulos, API DELPI ou SQL.

## Lacunas → homologação TST01

- Compilação e execução real: `TEST_NOT_RUN`.
- PEs/triggers ativos na MATA010 do ambiente (inventário RPO pendente).
- Campos memo `TO_INVENTORY` (sem coluna física): gravação somente após materialização da coluna na SB1010.
- Semântica de DELETE da MATA010: `TO_INVENTORY` — exige fonte
  MATA010 + inventário de vínculos antes de qualquer implementação.
- Gatilhos SX7 outbound observados não computam campos SB1; PEs que
  escrevam em SB1 (ex.: `B1_YDLPDSC` referenciado por PE) **não existem
  no SX3 do TST01** — divergência de dicionário registrada na matriz.
