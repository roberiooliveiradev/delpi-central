# Ledger de execução — Helpdesk DELPI

Fonte de estado. O roadmap não substitui esta tabela.

Estados: `PROVEN` | `PLANNED` | `TARGET` | `NOT_STARTED`.

| ID | Item | Estado | Evidência |
|---|---|---|---|
| H0.1 | GLPI 11.0.5 no container `inventario-ti-glpi-1` | PROVEN | arquivo de versão `11.0.5` no container, 21/09/2026 |
| H0.2 | `enable_hlapi = 1` | PROVEN | `glpi_configs`, 21/09/2026 |
| H0.3 | `enable_api = 0` | PROVEN | `glpi_configs`, 21/09/2026 |
| H0.4 | API 2.2.0 | PROVEN | `Router::API_VERSION` e URL `/api.php/v2.2` |
| H0.5 | Cliente `minha-delpi-helpdesk` ativo, grant `authorization_code`, escopo `api`, redirect do BFF | PROVEN | `glpi_oauthclients` id 1, 21/09/2026 |
| H0.6 | SSO SAML Keycloak | PROVEN | plugin `samlsso` instalado; tutorial do repositório |
| H0.7 | Iframe atual não é o host real do GLPI | PROVEN | manifesto `entry` `https://centraldelpi.com.br/helpdesk/`; gateway em `helpdesk.centraldelpi.com.br` |
| H1 | helpdesk-api e sessão OAuth | NOT_STARTED | — |
| H2 | Leitura de chamados | NOT_STARTED | — |
| H3 | Abertura e acompanhamento | NOT_STARTED | — |
| H4 | MFE nativo | NOT_STARTED | — |
| H5 | Anexo, satisfação, bancada técnica | TARGET | [`05-roadmap.md`](../05-roadmap.md) |

Próxima etapa autorizada pelo plano, ainda não iniciada: `E1.S1`.

Segredo do cliente OAuth não é registrado aqui.
