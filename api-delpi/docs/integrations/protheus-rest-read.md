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

A documentação técnica registra valores de path com rótulos invertidos. O backend aceita:

1. labels alinhados (auth=oauth/token, suppliers=supplier); ou
2. inversão comprovada (labels trocados de forma inequívoca).

Qualquer outro par ambíguo/desconhecido falha com `PROTHEUS_CONFIG_INVALID` — sem UPDATE na tabela.

## Token

Cache in-memory no processo com margem de expiração. Fingerprint usa `username|auth_url|sha256(password)` (sem senha em texto puro). Rotação de credencial invalida o cache. A procedure `pr_InserirTokenProtheus` **não** é usada nesta entrega.

## Diagnóstico de conexão

- `connection=ok`: HTTP 2xx no probe **ou** erro de negócio reconhecido (`PROTHEUS_SUPPLIER_NOT_FOUND`).
- `connection=failed`: timeout, indisponibilidade, token inválido ou `PROTHEUS_UPSTREAM_ERROR` (falha inesperada do ERP).

Campo `transport`: `https` | `http_cleartext` | `unknown`.

## Segurança / transporte OAuth

- Contrato Protheus: `grant_type`/`username`/`password` na **query string** do POST de token.
- Credenciais e tokens **nunca** retornam nas respostas de diagnóstico nem em logs (redaction obrigatória).
- TLS verify permanece ativo; não há `verify=False`.
- Preferir `URL_REST` em HTTPS. Se o ambiente só oferece HTTP cleartext, **não** executar testes com credenciais reais sem autorização explícita do owner da integração (risco de exposição em proxies/captura de rede).
