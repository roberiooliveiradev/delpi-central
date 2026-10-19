# Protheus REST — leitura (status + fornecedor)

## Escopo desta entrega

- `GET /integrations/protheus/status` — diagnóstico seguro (configuração, autenticação técnica, conectividade).
- `GET /integrations/protheus/suppliers/{supplier_id}` — consulta REST de fornecedor (`supplier_id` = 8 dígitos).

Não inclui POST/PUT de fornecedores nem consulta SA2 como substituto do REST.

## Ownership

- Owner: `api-delpi`
- Parâmetros técnicos: tabela `PARAMETROS_MINHADELPI` no SQL Server Intranet (`INTRANET_DB_*`)
- Credenciais Protheus (`USR_PROTHEUS` / `PSW_PROTHEUS`) **não** são configuradas por env na api-delpi

## Variáveis de ambiente (conexão Intranet)

| Variável | Uso |
|---|---|
| `INTRANET_DB_DATABASE` | Default `IntranetDelpiDev` |
| `INTRANET_DB_HOST` | Opcional; fallback `TOTVS_DB_HOST` / `DB_HOST` |
| `INTRANET_DB_USER` / `INTRANET_DB_PASSWORD` | Opcional; fallback TOTVS/DB |
| `INTRANET_PARAMS_TABLE` | Default `PARAMETROS_MINHADELPI` |
| `INTRANET_PARAMS_KEY_COLUMN` / `INTRANET_PARAMS_VALUE_COLUMN` | Default `PARAMETRO` / `VALOR` |
| `PROTHEUS_REST_TIMEOUT_SECONDS` | Default `30` |

## Autorização

Permissão: `api-delpi.integrations.protheus.read` (ou `api-delpi.access.full`).

## Inversão PATH_AUTH / PATH_SUPPLIERS

A documentação técnica registra valores de path com rótulos invertidos. O backend resolve por **semântica** (`oauth`/`token` vs `supplier`) sem UPDATE na tabela e expõe `config_path_label_mismatch` no status.

## Token

Cache in-memory no processo com margem de expiração. A procedure `pr_InserirTokenProtheus` **não** é usada nesta entrega (lacuna documentada).

## Segurança

- Tokens e senhas nunca retornam nas respostas de diagnóstico.
- Query string OAuth é o contrato do Protheus; URLs com credenciais são redactadas em logs.
- TLS verify permanece ativo; não há `verify=False`.
