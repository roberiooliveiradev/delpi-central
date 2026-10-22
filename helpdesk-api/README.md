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
| `GLPI_LEGACY_UPLOAD_ENABLED` | H12/H10/listagem-ator — `true` liga sessão limada apirest (Document + ciclo + Search Ticket só para `assignee_id`/`sort=assigned`; default `false`) |
| `GLPI_LEGACY_APP_TOKEN` | App-Token do cliente apirest (cifrado no GLPI; valor plaintext no env do BFF) |
| `GLPI_LEGACY_USER_TOKEN` | User-Token do usuário técnico (`minha-delpi-upload`, perfil Technician) |
| `GLPI_DASHBOARD_READER_ENABLED` | Kill switch da leitura institucional do sumário. Default `false`. Não reutiliza upload nem profile-sync |
| `GLPI_DASHBOARD_READER_APP_TOKEN` | App-Token exclusivo do apiclient da conta `minha-delpi-dashboard-reader` |
| `GLPI_DASHBOARD_READER_USER_TOKEN` | User-Token exclusivo dessa conta. Não é senha e não é o token de upload |
| `GLPI_DASHBOARD_READER_ENTITY_IDS` | Allowlist exata de entidades. Vazia, ou com `0` sem `GLPI_DASHBOARD_READER_ALLOW_ROOT=true`, deixa o leitor indisponível. `0` é só a entidade raiz, não as filhas. Alias de leitura: `GLPI_DASHBOARD_READER_ALLOWED_ENTITIES`, usado só quando `ENTITY_IDS` está vazio |
| `GLPI_DASHBOARD_READER_GROUP_IDS` | Allowlist opcional de grupos. Vazia não filtra grupo. Preenchida, descarta chamado fora dela |
| `GLPI_DASHBOARD_READER_ALLOW_ROOT` | Default `false`. Só autoriza configurar o id `0`. Não consulta filhos recursivamente |
| `GLPI_ASSIGNEE_PROFILE_IDS` | CSV de `profiles_id` GLPI atribuíveis como técnico (default `6` = Technician). Resolução: HLAPI Profile→User → legado Profile_User → `search/User` field 20 (necessário quando o user_token técnico recebe 403 em Profile_User). |
| `GLPI_LEGACY_MAX_UPLOAD_BYTES` | teto do multipart (default `20971520`) |
| `GLPI_LEGACY_TICKET_SEARCH_*_FIELD` | overrides dos search-option ids do Search/Ticket clássico. Defaults canônicos GLPI 10/11: assignee `5` (Technician, `glpi_tickets_users` type=ASSIGN), status `12`, categoria `7`, urgência `10`, datas `15/19/17/16`. Só ajustar com `listSearchOptions/Ticket` real como evidência |

Gere a chave de cifra com `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` no host, e coloque o valor só no `.env` da infra.

## Leitor institucional do sumário

Escopo aprovado: entidades `0` (Delpi), `1` (Matriz SC) e `2` (Filial ES), sem filtro de grupo. O id `0` não inclui filhas. Uma entidade futura, mesmo filha da raiz, é descartada no BFF. A conta GLPI, o perfil e os tokens só são criados com autorização operacional.

Configuração, depois do provisionamento, só no `.env` do host:

```text
GLPI_DASHBOARD_READER_ENABLED=true
GLPI_DASHBOARD_READER_ENTITY_IDS=0,1,2
GLPI_DASHBOARD_READER_GROUP_IDS=
GLPI_DASHBOARD_READER_ALLOW_ROOT=true
```

`ALLOW_ROOT` só libera o id `0` na allowlist. Não ativa consulta recursiva.

Perfil GLPI: leitura de chamado nas entidades `0`, `1` e `2` com `is_recursive=0`. Sem criar, alterar, excluir, solução, documento ou administração. Não usar o perfil Technician. Se o produto só permitir a raiz recursiva, o privilégio residual fica no user token; o BFF continua descartando qualquer `entities_id` fora de `0,1,2`.

Rollback: `GLPI_DASHBOARD_READER_ENABLED=false` volta o sumário institucional para indisponível, sem cair em zero e sem usar o token de upload. Revogação: desativar o usuário GLPI, revogar o user token e o apiclient, e remover o scope `helpdesk.dashboard.read` do cliente `tv-dashboard-api`. Rotação: gerar outro user token, trocar só `GLPI_DASHBOARD_READER_USER_TOKEN` e reiniciar o BFF.

## H12 / H10 — API legada (Document + ciclo)

HLAPI não recebe binário nem fecha o ciclo do solicitante. Com a flag ligada, o BFF usa `apirest.php` + App-Token + User-Token técnico **depois** de provar ACL com o Bearer OAuth:

- H12: `POST /tickets/{id}/attachments` → `Document` + `Document_Item`
- H10: `POST …/solution/accept|reject` → `ITILFollowup` (`add_close` / `add_reopen`); `PUT …/satisfaction` → `TicketSatisfaction`

Provisionamento: `scripts/enable_glpi_legacy_api.sh`. Evidência: ledger `H12.upload.*` / `H10.write.*` e `evidence/e10-cycle-console.md`.
