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
| H3 | Abertura e acompanhamento | PROVEN | perfil Colaborador — Chamados, `user_id` 69, 21/09/2026: `POST /Assistance/Ticket` → id **1120**; `POST …/Timeline/Followup` → id **593**. Super-Admin (sessão irmã) também criou **1119** + follow-up **591**. Sem senha neste arquivo. |
| H4 | MFE nativo | PROVEN | menu Meus Chamados de TI em `/apps/helpdesk`, sem iframe |
| H5 | Anexo, satisfação, bancada técnica | TARGET | fatiado em H10/H12/CONSOLE — [`05-roadmap.md`](../05-roadmap.md) |
| H6 | Gates HLAPI da paridade | PROVEN | 21/09/2026 — vereditos em [`12`](../12-conteudo-da-mensagem.md) §15, [`13`](../13-listagem-de-chamados.md) §13, [`14`](../14-pagina-e-estados-do-chamado.md) §10, [`15`](../15-capacidades-glpi.md) §9 |

H3 e H6 fechados. Paridade E6–E13 + verify-final concluídos. E14 (menção leitura M-07) entregue; M-23 (`@` no compositor) BLOQUEADO sem catálogo HLAPI. Sem senha neste arquivo.

Segredo do cliente OAuth não é registrado aqui.
