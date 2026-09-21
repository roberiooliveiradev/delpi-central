# 16 — Plano de paridade do solicitante

> **Status:** em execução. **E6.S0 e E6.S1 concluídos** em 21/09/2026.
> **Não altera** [`06-plano-execucao.md`](./06-plano-execucao.md) (`E1…E5`).
> **Ondas:** [`05-roadmap.md`](./05-roadmap.md) H6…H12.
> **Inventários:** [`12`](./12-conteudo-da-mensagem.md) · [`13`](./13-listagem-de-chamados.md) · [`14`](./14-pagina-e-estados-do-chamado.md) · [`15`](./15-capacidades-glpi.md).
> **Contrato vigente:** [`03-contrato.md`](./03-contrato.md) — evoluções **ADDITIVE**.
> **Identidade:** id GLPI ou e-mail; nome é rótulo.

## Overview

O colaborador passa a ver e gravar no Meus Chamados de TI o que o GLPI já entrega no fluxo do solicitante (estado, lista, HTML, fechar o ciclo), sem virar a bancada Super-Admin.

## Leitura do pedido

| Peça | Valor |
|---|---|
| Objetivo | roadmap completo para implementar a paridade documentada |
| Restrições | sem editar `06`; sem API legada; sem HD-011; sem três colunas |
| Dependência | H6 fecha gates antes de H8-imagem, H10, H11 |
| Entregável | este plano + `05` + HD-019…026 |
| Aceite | cada `E*.S*` com teste e, se user-facing, ajuda |

## Ledger

| RQ | Requisito | Estado no plano |
|---|---|---|
| RQ-01 | `status_id` + badge/filtro por id; grupos pending/approval | ATENDIDO_NO_PLANO E7.S1 |
| RQ-02 | Lista: data absoluta, período de abertura, page_size | ATENDIDO_NO_PLANO E7.S2 |
| RQ-03 | Lista: solved_at / busca no content se H6 | DESBLOQUEADO — 13-H1 e 13-H2 **PROVEN** → E7.S3 |
| RQ-04 | HTML sanitizado na bolha | ATENDIDO_NO_PLANO E8.S1–S2 |
| RQ-05 | Compositor rico abrir+responder | ATENDIDO_NO_PLANO E8.S3 |
| RQ-06 | Imagem no corpo via BFF se H6 | DESBLOQUEADO — 12-H1 **PROVEN**; A-07 continua FORA → E8.S4 |
| RQ-07 | Página: datas, can_followup, observador | ATENDIDO_NO_PLANO E9.S1 — `can_followup` só false no status 6 |
| RQ-08 | Aprovar/reabrir/satisfação se HLAPI | PARCIAL — Solution/Validation **têm** path; Satisfaction **sem** path (CONSOLE) → E10 |
| RQ-09 | TTR, vínculo, Form, observer write se H6 | TTR + observer **PROVEN**; Form + vínculo **FORA** → E11 |
| RQ-10 | Upload | BLOQUEADO_COM_EVIDENCIA E12 |
| RQ-11 | Ajuda no mesmo entregável | HERDADO_POR_SOLUCAO_TRANSVERSAL cada S user-facing |
| RQ-12 | Bancada / Change / entidade / API legada | FORA_DO_ESCOPO_COM_JUSTIFICATIVA |
| RQ-13 | H3 no ledger | **ATENDIDO** E6.S0 — ids 1120 / 593 |

## Evidências e hipóteses

CONFIRMADO: tela e BFF publicados; HTML achatado; status só string; lista relativa; HLAPI JSON-only; sete status fixos; `team` não filtra em RSQL.

E6.S1 fechou as hipóteses. Vereditos no [`05`](./05-roadmap.md) H6. **EXECUTION_DRIFT:** 14-H1 não é 403 em status 5 — só em 6.

## Arquitetura atual → alvo

```text
HOJE   GLPI HTML/status/datas → display_text + status.name → MFE plain
ALVO   GLPI → BFF allowlist + status_id + datas → contrato aditivo → kit render-only
```

Owner do corpo e do status: helpdesk-api. Owner da bolha/editor: plugin-ui. MFE só monta.

## Estado antes × depois

| Caso | Antes | Depois | Muda? |
|---|---|---|---|
| P0 6288 formatado | texto puro | HTML + imagem via BFF se H1 | sim |
| Lista 1114 | datas relativas | absoluta + status_id | sim |
| Fechado | Responder sempre | some se can_followup=false | sim |
| Super-Admin 128128 | — | continua sem total | não |
| Upload | bloqueado | bloqueado | não |
| Identidade | id/e-mail | id/e-mail | não |

## Decisões travadas

| ID | Decisão |
|---|---|
| D-01 | ADDITIVE no contrato (`*_html`, `status_id`, datas novas) |
| D-02 | Sanitizer no BFF; kit é defesa |
| D-03 | Sem TinyMCE / renderer HTML no MFE |
| D-04 | Sem `MentionComposer` (cola imagem) |
| D-05 | Sem filtro por `team` |
| D-06 | `open` inclui 10 até existir `approval` |
| D-07 | H6 morto remove etapa filha; não inventa UI |
| D-08 | H12 não liga API legada neste plano |
| D-09 | Console permanece `helpdesk.console` |

## Matriz de fluxos

| Fluxo | Superfície | Papel |
|---|---|---|
| Investigar | HLAPI / BFF | E6 |
| Listar | `/apps/helpdesk` | E7 |
| Abrir / responder | new + detalhe | E8 |
| Ler detalhe | `/tickets/{id}` | E8+E9 |
| Fechar ciclo | detalhe solucionado | E10 |
| F5 | URL + GET | invariante |
| Ajuda | helpTooltips | cada S user-facing |
| Console | host GLPI | FORA |

## Riscos

| Risco | Mitigação |
|---|---|
| XSS no HTML | allowlist BFF + teste negativo |
| Browser no host GLPI | rewrite só document_id ∈ attachments |
| Compat MFE antigo | campos atuais ficam texto |
| H6 inconclusivo | etapa filha vira FORA no próprio S |
| Satisfação/Forms sem operation | não desenhar tela |

---

## E6 — Investigação e ledger H3

### E6.S0 — Registrar H3 no ledger

- **Objetivo:** abertura e acompanhamento ao vivo `PROVEN` ou `FAIL` explícito.
- **RQ:** RQ-13
- **Fazer:** homologar POST de teste (chamado marcado) e follow-up; atualizar `evidence/execution-ledger.md` e o status H3 em `05`/`06`.
- **Não fazer:** mudar produto; commitar senha.
- **Evidência:** `06` E5.S2 ainda aberto para escrita.
- **Deps:** nenhuma de paridade.
- **Teste:** o id existe no GLPI no usuário do token.
- **Pronto:** ledger H3 ≠ `NOT_STARTED`. **CUMPRIDO** — H3 `PROVEN` (1120 / 593, Colaborador `user_id` 69).
- **Commit:** `docs(helpdesk): registra H3 da escrita ao vivo no ledger.`

### E6.S1 — Fechar gates HLAPI

- **Objetivo:** cada hipótese 12/13/14/15 vira PROVEN, FORA ou BLOQUEADO.
- **RQ:** RQ-03, RQ-06, RQ-07, RQ-08, RQ-09
- **Fazer:** `GET /Assistance/Ticket/{id}` e um item da lista (6288, 1114, 1101) — **só nomes de propriedades** e um recorte de `content` com PII removida em fixture de teste se necessário. Anotar em 12 §15, 13 §13, 14 §10, 15 §9. Riscar no `05` as linhas H11/H8-imagem que morrerem.
- **Não fazer:** logar corpo; commitar HTML com nome/foto; implementar UI.
- **Evidência:** inventários marcam HIPOTESE.
- **Deps:** sessão OAuth de homologação.
- **Teste:** tabela gate → veredito no próprio S.
- **Pronto:** nenhuma HIPOTESE material sem veredito. **CUMPRIDO** — tabela no [`05`](./05-roadmap.md) H6.
- **Commit:** `docs(helpdesk): fecha as hipóteses HLAPI da paridade.`

---

## E7 — Estados e lista (H7)

### E7.S1 — `status_id` e grupos

- **Objetivo:** lista e detalhe publicam `status_id`; badge e filtros usam id.
- **RQ:** RQ-01 · HD-019
- **Fazer:** `mapping._status_name` passa a devolver id+name; JSON aditivo; `statusBadgeVariant` por id (1 info, 2/3 warning, 4/6/10 conforme [`14`](./14-pagina-e-estados-do-chamado.md) S-04); query `pending` e `approval`; `open` inalterado.
- **Não fazer:** dicionário PT no BFF; filtrar por substring.
- **Evidência:** `_STATUS_GROUPS` e `_status_ids` já conhecem 1–6 e 10.
- **Deps:** nenhuma.
- **Teste:** positive id=1; irmão id=10 com `approval`; negativo `status=foo` 422; badge de «Aprovação» não depende do texto.
- **Pronto:** GET lista/detalhe com `status_id`; UI filtra `pending`.
- **Commit:** `feat(helpdesk): publica o id do estado e recorta pendente e aprovação.`

### E7.S2 — Datas absolutas e recorte de abertura

- **Objetivo:** células com data-hora; filtro `created_*`; seletor 10/20/50.
- **RQ:** RQ-02 · HD-020
- **Fazer:** formatar instante já no JSON; `created_from`/`created_to` → `date_creation`; a tela envia `page_size`.
- **Não fazer:** total do parque; sort por técnico.
- **Evidência:** 13 G-02, G-25, G-31; query `page_size` já existe.
- **Deps:** nenhuma.
- **Teste:** positive intervalo de abertura; irmão page_size=10 e has_more; negativo data inválida 422; F5 mantém query.
- **Pronto:** foto 1114 mostra dia/hora; ajuda da lista atualizada.
- **Commit:** `feat(helpdesk): mostra a data completa e filtra pela abertura.`

### E7.S3 — Resolução e busca no conteúdo

- **Objetivo:** `solved_at`/`closed_at` e `q` no content **somente** se E6.S1 PROVEN.
- **RQ:** RQ-03 · HD-020
- **Fazer:** se 13-H2: campos aditivos + sort opcional. Se 13-H1: `name=like` **ou** `content=like` no mesmo `q`. Se FORA: anotar 13 e **não** abrir UI.
- **Não fazer:** inventar data; buscar HTML cru.
- **Deps:** E6.S1.
- **Teste:** se PROVEN — positive termo só no content; negativo `q` com `;`. Se FORA — nenhum campo novo.
- **Pronto:** veredito de E6 cumprido.
- **Commit:** `feat(helpdesk): completa a lista com o que a HLAPI comprovou.` **ou** `docs(helpdesk): descarta solved_at/content na lista por evidência.`

---

## E8 — Corpo da mensagem (H8)

### E8.S1 — Contrato HTML no BFF

- **Objetivo:** `description_html` / `timeline[].content_html` sanitizados; texto atual permanece.
- **RQ:** RQ-04 · HD-021
- **Fazer:** allowlist [`12`](./12-conteudo-da-mensagem.md) §7; `display_text` só em rótulo; rewrite de `src`/`href` de documento **só** se E6 confirmou H1/H2 (senão remove `<img>` perigosa e deixa anexo no belowBody).
- **Não fazer:** HTML no mesmo campo `description`; logar corpo.
- **Evidência:** `_text` hoje achata; testes `strips_html` devem passar a: texto derivado + html sem script.
- **Deps:** E6.S1 para regra de img.
- **Teste:** positive `<p><strong>`; irmão `https` link; negativo `<script>`, `javascript:`, `onerror`; docid alheio some.
- **Pronto:** GET detalhe com os dois campos.
- **Commit:** `feat(helpdesk): publica o HTML sanitizado da mensagem.`

### E8.S2 — Modo HTML no kit + MFE

- **Objetivo:** `MessageThread` renderiza HTML já sanitizado; helpdesk deixa `plain`.
- **RQ:** RQ-04 · HD-021
- **Fazer:** `bodyMode="html"` no plugin-ui (não markdown); helpdesk liga; tokens `--delpi-ui-*`; clique em img reusa `FilePreviewModal` se houver document_id.
- **Não fazer:** `dangerouslySetInnerHTML` com HTML cru; CSS de bolha no MFE.
- **Deps:** E8.S1.
- **Teste:** kit: html vs script; helpdesk: 6288/irmão lista; negativo markdown não interpreta `**`.
- **Pronto:** bolha mostra lista/negrito do GLPI.
- **Commit:** `feat(helpdesk): renderiza a mensagem pelo modo HTML do kit.`

### E8.S3 — Compositor rico

- **Objetivo:** abrir e responder usam o mesmo `RichTextEditor`; POST HTML sanitizado de novo no BFF.
- **RQ:** RQ-05 · HD-022
- **Fazer:** factory do kit; teto de tamanho (M-29); menção só se E6 tiver catálogo por **id**.
- **Não fazer:** `MentionComposer`; colar imagem; editor diferente na abertura.
- **Deps:** E8.S1.
- **Teste:** positive negrito volta no GLPI e no F5; irmão texto puro ainda grava; negativo script no POST some.
- **Pronto:** ajuda create/detail descreve formatação, sem path.
- **Commit:** `feat(helpdesk): grava abertura e resposta em HTML sanitizado.`

### E8.S4 — Imagem no fio

- **Objetivo:** `<img>` reescrita para o GET de anexo **se** 12-H1/H2; A-07 só se H4 PROVEN.
- **RQ:** RQ-06 · HD-021
- **Fazer / não fazer:** conforme E6; se H3 (só Document) — belowBody basta, sem etapa extra.
- **Deps:** E6.S1, E8.S1–S2.
- **Teste:** F5 sem cookie GLPI; 404 de document alheio.
- **Pronto:** P0 6288 perceptível ou documentado FORA.
- **Commit:** `feat(helpdesk): mostra a imagem do fio pelo download autenticado.` **ou** docs de descarte.

---

## E9 — Página (H9)

### E9.S1 — Cartão, Responder, observador

- **Objetivo:** datas absolutas; esconder Responder se `can_followup=false`; observador rótulo se existir.
- **RQ:** RQ-07 · HD-023
- **Fazer:** campo aditivo `can_followup` — **false só se `status_id==6`** (14-H1: solucionado ainda aceita follow-up; fechado 403). Observador sem virar identidade.
- **Não fazer:** PATCH; abas da foto 1101.
- **Deps:** E7.S1; E6.S1 para can_followup.
- **Teste:** Novo mostra Responder; Fechado some se PROVEN; F5.
- **Pronto:** ajuda detail atualizada.
- **Commit:** `feat(helpdesk): ajusta a página ao estado que o GLPI permite.`

---

## E10 — Fechar o ciclo (H10)

### E10.S1 — Solução, reabrir, satisfação

- **Objetivo:** o solicitante aprova/recusa solução, reabre se a matriz deixar, responde pesquisa — **só** com operation HLAPI comprovada em E6.
- **RQ:** RQ-08 · HD-024
- **Fazer:** Satisfaction **não tem path** → CONSOLE (15). Solution e Validation **existem** (`GET/POST …/Timeline/Solution` e `…/Validation`) — só então tela de aprovar/recusar. Reabrir via PATCH de status = 403 no Colaborador.
- **Não fazer:** tela de pesquisa; PATCH de status; inventar path de Satisfaction.
- **Deps:** E6.S1, E9.S1.
- **Teste:** positive aprovar fecha (status 6); irmão recusar; negativo chamado alheio 404; sem operation = sem rota.
- **Pronto:** HD-024 ou 15 X-46/X-51 = CONSOLE com evidência.
- **Commit:** `feat(helpdesk): deixa o solicitante encerrar o ciclo no próprio chamado.` **ou** docs.

---

## E11 — Condicionais (H11)

### E11.S1 — TTR, vínculo, Form, observer write

- **Objetivo:** uma capacidade por evidência PROVEN; as outras FORA.
- **RQ:** RQ-09 · HD-025
- **Fazer:** TTR (`sla_ttr`/`sla_tto`) e observer (`POST …/TeamMember`). Form e vínculo **FORA** — não abrir UI.
- **Não fazer:** tela para gate morto; criar SLA/vínculo/item.
- **Deps:** E6.S1.
- **Teste:** por capacidade viva; negativo HD-011 (observer não manda requester/entity).
- **Pronto:** 15 X-09/X-13/X-28/X-29 atualizados.
- **Commit:** `feat(helpdesk): entrega só o condicional que a HLAPI comprovou.` **ou** docs.

---

## E12 — Upload (H12)

### E12.S1 — Park

- **Objetivo:** A-08 documentado; zero rota multipart.
- **RQ:** RQ-10 · HD-026
- **Fazer:** nada de código. Se no futuro a HLAPI ganhar upload, **novo** plano — não este S.
- **Não fazer:** ligar API legada.
- **Pronto:** HD-026 = BLOQUEADO no 07.
- **Commit:** nenhum, salvo drift documental.

---

## Critérios de pronto do plano

- H7 visível: status_id + data absoluta na lista e no detalhe.
- H8 visível: formatação do GLPI na bolha; escrita rica; imagem só se H6.
- H9: Responder some quando o GLPI recusa.
- H10/H11: ou na tela com operation, ou CONSOLE com evidência — sem limbo.
- H12: continua bloqueado.
- RQ-12 intacto (sem bancada).
- Ajuda atualizada em cada S user-facing.

## Verify-final

1. Rebuild helpdesk + helpdesk-api.
2. Lista 1114: data absoluta, status_id, F5.
3. Detalhe com `<img>` (1108 / 1045 / 467; **6288 inexistente**): HTML; imagem se rewrite.
4. Abrir+responder HTML; F5.
5. Chamado fechado: sem Responder se PROVEN.
6. 403/409 inalterados.
7. Nenhum path `/front/document.send.php` no HTML publicado.
8. Relar o pedido «implementar tudo»: tudo = H6…H11 possíveis; não a foto Super-Admin.

## Revisão adversarial

1. «Tudo» não inclui a bancada — explícito no 05.
2. E7.S3/E8.S4/E10/E11 podem ser docs — não são etapas fantasmas.
3. `status_id` não usa nome — D-06.
4. Sanitizer no BFF — D-02.
5. 06 intocado.
6. Upload não escorrega para E8.S3.

## YAML das subetapas

```yaml
todos:
  - id: e6-s0-ledger-h3
  - id: e6-s1-hlapi-gates
  - id: e7-s1-status-id
  - id: e7-s2-dates-page-size
  - id: e7-s3-solved-content
  - id: e8-s1-html-contract
  - id: e8-s2-html-thread
  - id: e8-s3-rich-composer
  - id: e8-s4-inline-image
  - id: e9-s1-page-followup
  - id: e10-s1-close-loop
  - id: e11-s1-conditionals
  - id: e12-s1-upload-park
```
