# Evidence ledger — Meus Chamados de TI

Estados: `PROVEN` | `PLANNED` | `TARGET` | `NOT_STARTED`.

| ID | Fato | Estado | Evidência |
|---|---|---|---|
| H0.1 | GLPI 11.0.5 no container `inventario-ti-glpi-1` | PROVEN | arquivo de versão `11.0.5` no container, 21/09/2026 |
| H0.2 | `enable_hlapi = 1` | PROVEN | `glpi_configs`, 21/09/2026 |
| H0.3 | `enable_api` (API legada) — exceção H12 Document-only | PROVEN | produção 21/09/2026: `enable_glpi_legacy_api.sh` + App-Token cifrado + `GLPI_LEGACY_*` no `helpdesk-api`; initSession 200 |
| H0.4 | API 2.2.0 | PROVEN | `Router::API_VERSION` e URL `/api.php/v2.2` |
| H0.5 | Cliente `minha-delpi-helpdesk` ativo, grant `authorization_code`, escopo `api`, redirect do BFF | PROVEN | `glpi_oauthclients` id 1, 21/09/2026 |
| H0.6 | SSO SAML Keycloak | PROVEN | plugin `samlsso` instalado; tutorial do repositório |
| H0.7 | Iframe antigo não era o host real do GLPI | PROVEN | entry antiga `https://centraldelpi.com.br/helpdesk/` observada em 21/09/2026; manifesto vigente é microfrontend em `/apps/helpdesk` |
| H1 | helpdesk-api e sessão OAuth | PROVEN | autorização concluída e lista carregada em `minhadelpi.com.br/apps/helpdesk`, 21/09/2026 |
| H2 | Leitura de chamados | PROVEN | lista real do usuário logado na mesma sessão |
| H3 | Abertura e acompanhamento | PROVEN | perfil Colaborador — Chamados, `user_id` 69, 21/09/2026: `POST /Assistance/Ticket` → id **1120**; `POST …/Timeline/Followup` → id **593**. Super-Admin (sessão irmã) também criou **1119** + follow-up **591**. Sem senha neste arquivo. |
| H4 | MFE nativo | PROVEN | menu Meus Chamados de TI em `/apps/helpdesk`, sem iframe |
| H5 | Anexo, satisfação, bancada técnica | TARGET | fatiado: download H4; upload H12 **PROVEN**; ciclo write H10 CONSOLE — [`05-roadmap.md`](../05-roadmap.md) |
| H6 | Gates HLAPI da paridade | PROVEN | 21/09/2026 — vereditos em [`12`](../12-conteudo-da-mensagem.md) §15, [`13`](../13-listagem-de-chamados.md) §13, [`14`](../14-pagina-e-estados-do-chamado.md) §10, [`15`](../15-capacidades-glpi.md) §9 |
| H14 | Menção leitura (chips) | PROVEN | E14 — [`e14-mentions.md`](./e14-mentions.md); M-23 park |
| G-05 | `requester_display_name` na lista | PROVEN | commit `d1fb8a0af`, 21/09/2026 |
| lista.href | Chamado/título com path estável + meio-clique | PROVEN | commit `e0439aab9`, 21/09/2026 |
| G-07+ | `sort=closed_at` → `date_close` | PROVEN | commit `e0439aab9`, 21/09/2026 |
| G-32b | Voltar restaura recorte da lista | PROVEN | commit `2b7a258de`, 21/09/2026 |
| cartão.urgência | subtítulo `#id · urgência · técnico` | PROVEN | commit `ed6a67b5b`, 21/09/2026 |
| lista.ux | Filtros só no builder; Tabela\|Cards; page_size na paginação; tema dark | PROVEN | 21/09/2026 |
| lista.ux.pagination | Rodapé `createDashboardPaginationKit` (setas, Ir para, resumo); `HintAction` sem ícones ?; `HelpdeskListPaginationFooter` | PROVEN | commit `1d999772a`, 21/09/2026 |
| H10.solution.read | Bolha `kind=solution` na conversa (Timeline Solution) | PROVEN | testes mapping + conversationMessages, 21/09/2026 |
| H10.solicitante.bridge | CTA «Abrir no helpdesk» em solucionado/fechado/aprovação (deep link GLPI) | PROVEN | `glpiTicketFormUrl` + `solicitanteLifecycleCue`, 21/09/2026 |
| H12.upload.bff | `POST /tickets/{id}/attachments` via apirest Document + App-Token + User-Token técnico | PROVEN | BFF + testes FakeGlpi/MockTransport; live Document+Ticket 201, 21/09/2026 |
| H12.upload.mfe | Colar/arrastar/clipe no compositor (abrir + responder) | PROVEN | kit `onPasteImages` + IDB pending F5; testes RichTextEditor + persist pending; build helpdesk+plugin-ui 22/09/2026 |
| H12.upload.live | enable_api + `GLPI_LEGACY_*` + tech user Technician (profiles_id 6) em produção | PROVEN | env no container `delpi-helpdesk-api`; docs 1177/1178 no chamado **1122**; commit deploy `3e34b1226` / `0afc3154a`, 21/09/2026 |
| H12.preview.blob | Preview no compositor via `blob:` (GET anexo exige Bearer) | PROVEN | draft sem `blob:` (`attachment:pending:{id}` / BFF path); resolve + IDB hydrate create/reply; testes `persistHelpdeskAttachmentHtml` |
| H12.paste.snipping | Ctrl+V Snipping Tool (mime vazio / data: / clipboard.read) | PROVEN | `richTextClipboardImages` + async no RTE e MentionComposer; teste paste `onPasteImages`; ACEITE live pós-rebuild remote |
| H12.kit.centralize | Paste/imagem no `RichTextEditor` alinhado à sala | PROVEN | mesmo `collectPasteImageFiles` / async; host só materializa |
| H12.resize | Redimensionar imagem no `RichTextEditor` (width/height HTML) | PROVEN | plugin-ui `richTextImageResize`; commit `298bb2404` |
| H12.help | Helps curtos + `attachHint` / reply / attachments | PROVEN | `helpTooltips.ts` + testes de teto; 21/09/2026 |

## Resumo vigente (22/09/2026)

H3 e H6 fechados. Paridade E6–E13 + verify-final concluídos. E14 (menção leitura M-07) entregue; M-23 (`@` no compositor) **BLOQUEADO** sem catálogo HLAPI. H10: **leitura** da solução + ponte UX ao GLPI PROVEN; write continua CONSOLE. **H12 Document upload BFF/live PROVEN**; **P0 colar + F5 preview corrigido no código** (kit + IDB + HTML estável) — rebuild `plugin-ui` remote antes do MFE em publish. Residuais: M-23, H10 write, bancada FORA. Sem senha neste arquivo.
