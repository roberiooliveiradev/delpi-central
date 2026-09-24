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
| `GLPI_LEGACY_UPLOAD_ENABLED` | H12/H10 — `true` liga sessão limada apirest (Document + ciclo solicitante; default `false`) |
| `GLPI_LEGACY_APP_TOKEN` | App-Token do cliente apirest (cifrado no GLPI; valor plaintext no env do BFF) |
| `GLPI_LEGACY_USER_TOKEN` | User-Token do usuário técnico (`minha-delpi-upload`, perfil Technician) |
| `GLPI_ASSIGNEE_PROFILE_IDS` | CSV de `profiles_id` GLPI atribuíveis como técnico (default `6` = Technician) |
| `GLPI_LEGACY_MAX_UPLOAD_BYTES` | teto do multipart (default `20971520`) |

Gere a chave de cifra com `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` no host, e coloque o valor só no `.env` da infra.

## H12 / H10 — API legada (Document + ciclo)

HLAPI não recebe binário nem fecha o ciclo do solicitante. Com a flag ligada, o BFF usa `apirest.php` + App-Token + User-Token técnico **depois** de provar ACL com o Bearer OAuth:

- H12: `POST /tickets/{id}/attachments` → `Document` + `Document_Item`
- H10: `POST …/solution/accept|reject` → `ITILFollowup` (`add_close` / `add_reopen`); `PUT …/satisfaction` → `TicketSatisfaction`

Provisionamento: `scripts/enable_glpi_legacy_api.sh`. Evidência: ledger `H12.upload.*` / `H10.write.*` e `evidence/e10-cycle-console.md`.
