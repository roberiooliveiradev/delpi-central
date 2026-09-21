# Ledger de execução — Meus Chamados de TI

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
| H0.7 | Iframe antigo não era o host real do GLPI | PROVEN | entry antiga `https://centraldelpi.com.br/helpdesk/` observada em 21/09/2026; manifesto vigente é microfrontend em `/apps/helpdesk` |
| H1 | helpdesk-api e sessão OAuth | PROVEN | autorização concluída e lista carregada em `minhadelpi.com.br/apps/helpdesk`, 21/09/2026 |
| H2 | Leitura de chamados | PROVEN | lista real do usuário logado na mesma sessão |
| H3 | Abertura e acompanhamento | NOT_STARTED | tela publicada; criação e acompanhamento ao vivo ainda não registrados |
| H4 | MFE nativo | PROVEN | menu Meus Chamados de TI em `/apps/helpdesk`, sem iframe |
| H5 | Anexo, satisfação, bancada técnica | TARGET | [`05-roadmap.md`](../05-roadmap.md) |

Próxima etapa: registrar no ledger a abertura e o acompanhamento feitos por um usuário real. H5 continua `TARGET`.

Segredo do cliente OAuth não é registrado aqui.
