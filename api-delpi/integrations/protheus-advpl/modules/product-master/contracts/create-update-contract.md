# Contrato CREATE/UPDATE — product-master (SB1 / MATA010)

Fonte candidato: `src/DLP04I01.PRW` (`SOURCE_CANDIDATE`, sem compilação).

## Superfície REST (preservada do upstream)

| Verbo | Path | Rotina | ExecAuto op |
|---|---|---|---|
| POST | `/v1/IncProduto/incluir` | `MATA010` | 3 (inclusão) |
| PUT  | `/v1/IncProduto/alterar` | `MATA010` | 4 (alteração) |

`Content-Type: application/json`. Resposta `RETOBJ`:
`{"code","message","detailedMessage","id"}` + HTTP `200` (sucesso) ou `400`
(JSON inválido, payload incompleto ou erro oficial via `GetAutoGrLog`).

## Regra de representação completa

Os **22 campos** abaixo são **obrigatórios em POST e PUT**. Campo ausente,
`null` ou tipo inválido → `400` com a lista no `detailedMessage`.
`null` JSON é indistinguível de campo ausente no `JsonObject` — ambos rejeitados.

## Matriz de campos

| Campo | Tipo | Status | Observação |
|---|---|---|---|
| B1_COD | C | SUPPORTED | chave do produto |
| B1_DESC | C | SUPPORTED | |
| B1_GRUPO | C | SUPPORTED | |
| B1_TIPO | C | SUPPORTED | |
| B1_UM / B1_SEGUM | C | SUPPORTED | |
| B1_LOCPAD | C | SUPPORTED | |
| B1_POSIPI / B1_EX_NCM / B1_EX_NBM | C | SUPPORTED | |
| B1_REFEREN / B1_REFCANT / B1_CODDES | C | SUPPORTED | |
| B1_YHOHS | C | SUPPORTED | custom DELPI |
| B1_TE / B1_TS | C | SUPPORTED | |
| B1_TIPCONV / B1_TPMAT / B1_ESPECIE / B1_ORIGEM | C | SUPPORTED | |
| B1_PICMRET | N | SUPPORTED | `N` nativo ou `C` estrita (ver regra numérica) |
| B1_CONV | N | SUPPORTED | idem |

## Regras de tipo (pós-hardening)

- **Numérico** (`B1_PICMRET`, `B1_CONV`): aceita `N` nativo do JSON ou
  string no formato `lIsNumStr` — sinal opcional **somente** na 1ª posição,
  ≥1 dígito, ≤1 ponto decimal `.`, sem separador de milhar e sem espaços.
  Rejeitados: `"abc"`, `"12x"`, `""`, `" "`, `"1,2,3"`, `null`, ausente.
  `"0"` e `0` são valores válidos distintos de ausência.
- **Caractere** (demais 20 campos): somente `ValType "C"` — objeto, array,
  booleano e número são rejeitados; nenhuma conversão automática de tipo.
- `null` ≡ ausente no `JsonObject` → ambos rejeitados (documentado).
- Validação pertence à fachada ADVPL; regras finais de negócio permanecem
  na MATA010. Rotas SQL de leitura da API DELPI **não** são contrato nem
  caminho de implementação do `.PRW`.

`SUPPORTED` = no contrato publicado e no fonte. Campos SB1 fora da lista =
`NOT_SUPPORTED` nesta versão (expansão exige owner + validação TST01).
Validações finais (obrigatórios SX3, triggers, PEs) pertencem à MATA010.

## Exemplos (sintéticos)

Válido — POST: todos os 22 campos, `"B1_CONV": 1` (N) ou `"1"` (C).

Inválidos → 400:
- `{"B1_COD": "X", "B1_DESC": "Y"}` — 20 campos ausentes;
- `{"B1_PICMRET": null, ...}` — nulo ≡ ausente;
- `{invalid json` — parse falha;
- `{"B1_CONV": "", ...}` — numérico vazio.

## Erros

| Causa | HTTP | detailedMessage |
|---|---|---|
| JSON inválido | 400 | "Corpo da requisicao nao e um JSON valido" |
| Payload incompleto | 400 | "Payload incompleto — campos ausentes/nulos/invalidos: …" |
| Erro oficial MATA010 | 400 | conteúdo de `GetAutoGrLog()` |
| Exceção runtime | 400 | `e:Description + e:ErrorStack` |

## Dependências e requisitos de compilação

- Includes: `TOTVS.CH`, `RESTFUL.CH`, `TOPCONN.CH`, `TBICONN.CH`, `FWMVCDef.ch`.
- `MSExecAuto({|x,y| Mata010(x,y)}, aSB1, 3|4)` + `PRIVATE lMsErroAuto/lMsHelpAuto/lAutoErrNoFile`.
- Sem dependência de outros módulos, API DELPI ou SQL.

## Lacunas → homologação TST01

- Compilação e execução real: `TEST_NOT_RUN`.
- PEs/triggers ativos na MATA010 do ambiente (inventário RPO pendente).
- Semântica de atualização parcial via ExecAuto: não comprovada → PUT parcial
  permanece **não suportado** por contrato.
- Compatibilidade com consumidor existente (façade api-delpi já exige
  representação completa — ver `protheus-rest-product-update-ledger.md`).
