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
| `INTRANET_PARAMS_KEY_COLUMN` / `INTRANET_PARAMS_VALUE_COLUMN` | Default `PARAMETRO` / `CONTEUDO` |
| `INTRANET_PARAMS_AMBIENTE` | Opcional; filtra coluna `AMBIENTE` quando a tabela tem conjuntos por ambiente |
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

## Homologação operacional — evidências e bloqueios

Estado revalidado no Intranet (`PARAMETROS_MINHADELPI`, colunas `PARAMETRO`/`CONTEUDO`/`AMBIENTE`):

| Parâmetro | AMBIENTE 1 | AMBIENTE 2 |
|---|---|---|
| `USR_PROTHEUS` / `PSW_PROTHEUS` | PRESENT | PRESENT |
| `URL_REST` | HTTP cleartext (`host:8701`) | idem |
| `PATH_SUPPLIERS` | `/delpi/api/v1/suppliers` | idem |
| `PATH_AUTH` | **EMPTY** | **EMPTY** |

### PATH_AUTH — valor candidato (não aplicado)

Descoberta sem envio de credenciais (POST apenas com `grant_type=password`):

| Path | Resultado |
|---|---|
| `/api/oauth2/v1/token` (doc legada) | HTTP 404 |
| `/rest/api/oauth2/v1/token` | HTTP 400 `invalid_grant - username não informado` → endpoint existe |

Correção proposta (requer `PENDING_OWNER_APPROVAL` — **não executar sem owner**):

```sql
-- Backup lógico: SELECT ID, AMBIENTE, PARAMETRO, LEN(CONTEUDO) ...
-- Aplicar por AMBIENTE autorizado, um de cada vez:
UPDATE PARAMETROS_MINHADELPI
SET CONTEUDO = '/rest/api/oauth2/v1/token'
WHERE PARAMETRO = 'PATH_AUTH'
  AND AMBIENTE = ?   -- 1 ou 2, conforme autorização
  AND (CONTEUDO IS NULL OR LTRIM(RTRIM(CONTEUDO)) = '');
```

### Gate `SECURE_TRANSPORT`

- `URL_REST` vigente aponta para **HTTP** na porta REST.
- Porta 443 responde TLS com **certificado self-signed** (falha com verify padrão); path OAuth sob HTTPS:443 não espelha o AppServer REST.
- Smoke com credenciais reais exige `SECURE_TRANSPORT=PASS` (HTTPS válido / terminação TLS autorizada / decisão explícita do owner de segurança). Enquanto HTTP cleartext: **FAIL**.

### Permissão Keycloak / Core

- Código: `api-delpi.integrations.protheus.read` (manifest + decorator).
- Publicação: `POST /core-api/admin/apps/register` com nova versão do manifesto `api-delpi` (`apps.manage`), depois grant via RBAC admin — **não** usar `api-delpi.access.full` como atalho.
- Deploy canônico: `git pull` + `./infra/scripts/up-prod-sequential.sh --pull --build` (escopo `api-delpi`), sem editar container.
