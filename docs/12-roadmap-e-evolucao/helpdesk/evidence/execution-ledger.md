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
| H1 | helpdesk-api e sessão OAuth | NOT_STARTED | código e testes automatizados no repositório; homologação com usuário real (E5.S2) ainda não executada |
| H2 | Leitura de chamados | NOT_STARTED | contrato coberto por teste de API; leitura ao vivo no GLPI ainda não homologada |
| H3 | Abertura e acompanhamento | NOT_STARTED | idempotência coberta por teste; POST ao vivo no GLPI ainda não homologado |
| H4 | MFE nativo | NOT_STARTED | manifesto federado e tela no repositório; navegação no portal publicado ainda não homologada |
| H5 | Anexo, satisfação, bancada técnica | TARGET | [`05-roadmap.md`](../05-roadmap.md) |

Próxima etapa: publicar a stack com as variáveis do `.env` e homologar com um usuário real (`E5.S2`). Até lá H1–H4 permanecem `NOT_STARTED`.

Segredo do cliente OAuth não é registrado aqui.
