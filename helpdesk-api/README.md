# helpdesk-api

BFF de Meus Chamados de TI. O GLPI é a fonte dos chamados. Esta API guarda só a sessão OAuth cifrada e as chaves de idempotência.

## Variáveis

Defina no ambiente do Compose. Não versione segredo.

| Variável | Uso |
|---|---|
| `GLPI_BASE_URL` | `https://helpdesk.centraldelpi.com.br` |
| `GLPI_OAUTH_CLIENT_ID` | cliente `minha-delpi-helpdesk` |
| `GLPI_OAUTH_CLIENT_SECRET` | segredo do cliente, só no servidor |
| `GLPI_OAUTH_REDIRECT_URI` | `https://centraldelpi.com.br/apps/helpdesk-api/auth/glpi/callback` |
| `GLPI_SAML_IDP_ID` | id numérico do IdP samlsso; produção usa `1` (`Minha DELPI`) |
| `HELPDESK_TOKEN_ENCRYPTION_KEY` | chave Fernet, distinta do segredo OAuth |
| `HELPDESK_API_ROOT_PATH` | `/apps/helpdesk-api` |
| `HELPDESK_RUN_MIGRATIONS_ON_STARTUP` | aplica o schema `helpdesk` |
| `PUBLIC_BASE_URL` | origem do portal após o callback |
| `PLUGINS_DB_*` | Postgres dos plugins |
| `JWT_SECRET` e `KEYCLOAK_*` | mesmo contrato das outras APIs de módulo |

Gere a chave de cifra com `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` no host, e coloque o valor só no `.env` da infra.
