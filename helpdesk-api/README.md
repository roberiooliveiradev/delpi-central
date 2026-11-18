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
| `GLPI_LEGACY_TICKET_SEARCH_*_FIELD` | overrides dos search-option ids do Search/Ticket clássico. Defaults canônicos GLPI 10/11: requester `4`, assignee `5` (Technician, `glpi_tickets_users` type=ASSIGN), status `12`, categoria `7`, urgência `10`, datas `15/19/17/16`. Só ajustar com `listSearchOptions/Ticket` real como evidência |

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


## Notificação de chamados solucionados (#1616)

A solução é confirmada no GLPI antes de gerar o evento. Somente uma transição de
status anterior diferente de 5 para status 5 (Solucionado), registrada pelo
Helpdesk BFF, cria um aviso ao solicitante. Outras atualizações do chamado não notificam.

Fluxo: Helpdesk API -> validação do GLPI -> vínculo exato GLPI/e-mail/diretório
Minha Delpi -> outbox PostgreSQL -> Core API -> sininho do Portal.

- Categoria: helpdesk_ticket_solved; origem: helpdesk; ícone e preferências
  seguem o catálogo existente. A notificação leva ao detalhe do chamado.
- Identidade: o destinatário é o solicitante do GLPI mapeado ao UUID do Portal;
  ausência de vínculo não permite redirecionar o aviso ao técnico.
- Fila: migration V007, deduplicação por (ticket_id, solution_id),
  worker com FOR UPDATE SKIP LOCKED e retentativas progressivas.
  Nas falhas entre HTTP 2xx e commit local, a semântica é at-least-once.
- Produção: os serviços alterados são core-api, portal e helpdesk-api.
  O docker-compose.yml habilita as migrations no startup e a notificação por padrão.
  Confirmar configuração do CORE_API_INTEGRATIONS_SERVICE_TOKEN sem expor o valor.
  Homologação deixa a origem GLPI indisponível e o worker desativado.
- Limite: esta integração observa a criação de solução pelo BFF (Portal e
  ferramentas que invocam sua API). Uma solução lançada somente no GLPI
  nativo não passa por esse fluxo. A captura direta do GLPI exige evento
  nativo autenticado (webhook), que não é configurado nesta entrega.
- Segurança: quem entrega é a Core API; acesso ao app Helpdesk e preferências
  de notificações do usuário são respeitados. Sem disparo geral.

Smoke após deploy: resolver um chamado de teste pelo Portal, abrir o sininho
do solicitante, seguir o link até a solução e repetir o mesmo envio com a
mesma chave de idempotência. Deve haver só um registro de evento. Se a Core
estiver indisponível, conferir a fila pendente sem criar novos disparos.
