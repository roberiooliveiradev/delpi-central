# 14 — Página do chamado e estados

> **Status:** inventário. Ordem de código: [`16-plano-paridade.md`](./16-plano-paridade.md) E7.S1 e E9 (HD-019, HD-023). Não altera [`06-plano-execucao.md`](./06-plano-execucao.md).
> **Pedido:** a página do chamado e os estados devem cobrir o que o GLPI já entrega ao solicitante. Este arquivo só documenta.
> **Tela publicada:** [`WIREFRAMES.md`](./WIREFRAMES.md) §3.
> **Foto de 21/09/2026:** `front/ticket.form.php?id=1101` (interface central, Super-Admin) — três colunas, abas, atores, menu Responder.
> **Conversa:** [`10-conversa-do-chamado.md`](./10-conversa-do-chamado.md). **Corpo:** [`12-conteudo-da-mensagem.md`](./12-conteudo-da-mensagem.md). **Lista:** [`13-listagem-de-chamados.md`](./13-listagem-de-chamados.md).
> **Contrato vigente:** [`03-contrato.md`](./03-contrato.md).

Este documento responde: o que o formulário de chamado do GLPI contém, o que o ciclo ITIL de status faz, o que a Minha DELPI mostra hoje e o que **deve** entrar na página quando houver autorização de código.

## 1. Recorte do produto

`/apps/helpdesk/tickets/{id}` é a página do **solicitante**: ler o chamado, ver o estado, acompanhar. Não é `ticket.form.php` do técnico.

```text
página do solicitante  = cabeçalho + estado + conversa + responder (se o perfil deixar)
formulário central     = três colunas, abas, atores editáveis, salvar, excluir, 2/15
```

Dois fluxos distintos:

| Fluxo | Pergunta |
|---|---|
| Página | o que a pessoa precisa ver além da bolha? |
| Estado | quais status o GLPI tem e como a Minha DELPI os mostra e recorta? |

Isto **estende** HD-009, HD-013, HD-015 e HD-016. Aprovar solução / reabrir / pesquisa = H5 ([`05-roadmap.md`](./05-roadmap.md)), não este inventário como autorização. Forms, TTR, vínculos e abas que não cabem aqui: [`15-capacidades-glpi.md`](./15-capacidades-glpi.md).

## 2. Fontes e grau de evidência

| Fonte | Classe | Uso |
|---|---|---|
| [Ticket life cycle](https://help.glpi-project.org/documentation/modules/assistance/tickets/ticketlifecycle) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | 7 status fixos; regras de transição; urgência×impacto=prioridade; tipo incidente/requisição |
| [Life cycle matrix](https://help.glpi-project.org/documentation/modules/administration/profiles/lifecyclematrix.md) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | matriz por perfil; interface simplificada: fechar e reabrir |
| [Followup](https://help.glpi-project.org/documentation/modules/assistance/tabs/followup) / [Solution](https://help.glpi-project.org/documentation/modules/assistance/tabs/solution) | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | responder vs solucionar vs aprovar |
| Foto 1101 `ticket.form.php` | CONFIRMADO (captura) | abas, atores, menu Responder, 2/15, ponto de status |
| Schema HLAPI `Ticket.status` `{id, name}` | CONFIRMADO_NO_CODIGO | o BFF publica só o `name` |
| `mapping._STATUS_GROUPS` e `_status_ids` | CONFIRMADO_NO_CODIGO | grupos + ids `1,2,3,4,5,6,10` |
| `statusBadgeVariant` | CONFIRMADO_NO_CODIGO | casa **rótulo** PT; Aprovação e Planejado não têm variante própria |
| Forum / DeepWiki GLPI 11 `APPROVAL=10` | CONFIRMADO_EM_DOCUMENTACAO_CANONICA | id 10 = Approval; o BFF já aceita `10` no filtro |
| Rótulo PT-BR exato de cada id nesta produção | HIPOTESE_A_VALIDAR | capturar `status` dos sete ids |

Os status **não se cadastram**. A matriz do perfil só esconde transição, não cria estado novo.

## 3. Página do chamado no GLPI

### 3.1 O que a foto 1101 mostra

Três colunas + barra inferior. Interface **central**, não a simplificada.

| Zona | Peças | Destino |
|---|---|---|
| Cabeçalho | ponto de status, título + `(1101)`, paginação 2/15 | título/id/status SIM; 2/15 CONSOLE (a lista navega) |
| Esquerda | Chamado, Estatísticas, Aprovações, Base de conhecimento, Itens, Custos, Projetos, Problemas, Mudanças, Contratos, Histórico, PDF | CONSOLE_GLPI |
| Centro | abertura («Criado em … por …»), descrição | conversa — [`10`](./10-conversa-do-chamado.md) + [`12`](./12-conteudo-da-mensagem.md) |
| Direita | Atores (requerente, observador, atribuído), Itens, Níveis de serviço, objetos relacionados | ler técnico/solicitante SIM; editar e o resto CONSOLE |
| Responder ▾ | tarefa, solução, documento, aprovação | comentário público SIM; o restante CONSOLE / H5 / A-08 |
| Rodapé | excluir, salvar | CONSOLE — o MFE não edita o chamado |

Na foto 1101 o atribuído está vazio e o status é Novo (ponto verde). Isso é estado válido: chamado recém-aberto, sem técnico.

### 3.2 Interface simplificada do solicitante

Quem entra como colaborador no GLPI **não** vê o menu da foto. Vê título, status, conversa e responder. A Minha DELPI copia esse recorte, no kit, numa coluna.

### 3.3 O que a Minha DELPI faz hoje

`/apps/helpdesk/tickets/{id}`:

```text
HelpdeskPageHeader   título · Voltar · Atualizar
HelpdeskRecordCard   categoria | #id · técnico | badge de status
HelpdeskMessageThread  abertura + acompanhamentos (texto puro)
HelpdeskTextArea     Responder  (sempre visível se o GET ok)
```

| Peça | Hoje |
|---|---|
| Título, id, status (string), categoria, urgência, técnico | cartão |
| Datas | só na conversa, relativas |
| Observador | não |
| Tipo / prioridade / impacto / entidade / SLA | não |
| Responder com chamado solucionado/fechado | o formulário continua na tela; o GLPI decide 403 |
| Aprovar solução / reabrir / pesquisa | não |
| Excluir Novo | não — e não entra (CONSOLE / risco) |
| F5 | o id está no path |

## 4. Estados do chamado

### 4.1 Os sete status (imutáveis)

Documentação oficial + constantes `CommonITILObject` no GLPI 11:

| Id | Constante | EN (doc) | PT-BR típico | Quem muda |
|---|---|---|---|---|
| 1 | `INCOMING` | New | Novo | criação |
| 10 | `APPROVAL` | Approval | Aprovação / Aguardando validação | validação |
| 2 | `ASSIGNED` | Processing (assigned) | Em atendimento (atribuído) | técnico/grupo/fornecedor atribuído |
| 3 | `PLANNED` | Processing (planned) | Em atendimento (planejado) | tarefa planejada |
| 4 | `WAITING` | Pending | Pendente | técnico (motivo de pendência); ITIL prefere o solicitante |
| 5 | `SOLVED` | Solved | Solucionado | solução proposta |
| 6 | `CLOSED` | Closed | Fechado | solicitante aprova a solução (ou prazo da doc, 15 dias) |

Não existe oitavo status. Não se traduz «Novo» no BFF para outro vocabulário. O rótulo visível é o `name` que o GLPI devolve no locale do token.

### 4.2 Transições (doc)

```text
criar            → 1 Novo
atribuir         → 2 Atribuído
tarefa planejada → 3 Planejado
pendência        → 4 Pendente
solução          → 5 Solucionado
aprovar solução  → 6 Fechado
```

O técnico pode forçar status se a matriz do perfil deixar. O solicitante, na interface simplificada, em geral: acompanhar; às vezes fechar (aprovar) e reabrir. Isso é **direito do perfil GLPI**, não regra do MFE.

### 4.3 Grupos que o BFF já usa na lista

| Query `status` | Ids | Cabe na doc? |
|---|---|---|
| `open` | 1, **10**, 2, 3, 4 | sim — ainda não resolvido |
| `in_progress` | 2, 3 | sim — em atendimento |
| `solved` | 5 | sim |
| `closed` | 6 | sim |
| *(ausente)* | 4 sozinho | [`13`](./13-listagem-de-chamados.md) G-23 `pending` |
| *(ausente)* | 10 sozinho | ALVO `approval` — hoje some dentro de `open` |
| id numérico `1`…`6`,`10` | um id | o BFF já aceita; a tela não oferece |

### 4.4 Badge hoje (problema de classe)

`statusBadgeVariant` decide pela **string**:

| Casa | Variante | Furo |
|---|---|---|
| começa com «novo» | `info` | ok para Novo |
| contém «solucion» | `success` | ok |
| contém «atendimento» ou «atribu» | `warning` | Planejado e Atribuído iguais — aceitável |
| contém «pendente» ou «fechado» | `neutral` | Fechado e Pendente iguais |
| resto | `neutral` | **Approval (10)** cai aqui se o rótulo for «Aprovação» |

Identidade do estado não pode ser o nome. O alvo é `status_id` no contrato; o badge mapeia **id**, o rótulo continua o `name` do GLPI.

### 4.5 Tipo, urgência, impacto, prioridade

A doc de ciclo: o solicitante define **urgência**; o técnico, **impacto**; **prioridade** sai da matriz. **Tipo** é Incidente ou Requisição.

Na Minha DELPI a abertura só pede urgência ([`WIREFRAMES`](./WIREFRAMES.md) §2). Tipo/impacto/prioridade **não** entram na página do colaborador. Não é estado do chamado.

## 5. Ledger

```text
IMPLEMENTADO   ALVO_LEITURA   ALVO_RECORTE   ALVO_ESCRITA
HIPOTESE_A_VALIDAR   BLOQUEADO   CONSOLE_GLPI   H5   FORA
```

### 5.1 Página

| ID | Capacidade | Estado | Dono |
|---|---|---|---|
| P-01 | Título, id, status visível, categoria, urgência, técnico | IMPLEMENTADO | cartão |
| P-02 | Conversar e responder em público | IMPLEMENTADO | [`10`](./10-conversa-do-chamado.md) |
| P-03 | HTML / imagem no corpo | **IMPLEMENTADO** E8 | [`12`](./12-conteudo-da-mensagem.md) |
| P-04 | Data-hora absoluta no cabeçalho (aberto / atualizado / solução) | **IMPLEMENTADO** | cartão do detalhe |
| P-05 | Observador só leitura (rótulo) | **IMPLEMENTADO** se `team.observer` | `observers_display_name` |
| P-06 | Esconder Responder quando o GLPI não aceita acompanhamento (fechado, sem direito) | **IMPLEMENTADO** | `can_followup=false` só em status 6 |
| P-07 | Aprovar / recusar solução | H5 | — |
| P-08 | Reabrir fechado | H5 (matriz simplificada) | — |
| P-09 | Pesquisa de satisfação | H5 | — |
| P-10 | Excluir chamado Novo | CONSOLE_GLPI | a doc permite ao solicitante; esta tela não apaga |
| P-11 | Editar atores, SLA, itens, categoria, urgência depois de aberto | CONSOLE_GLPI | sem PATCH de Ticket |
| P-12 | Abas, PDF, 2/15, Salvar, lixeira, tarefa, documento novo | CONSOLE_GLPI / A-08 | — |
| P-13 | Tipo / prioridade / impacto / entidade | FORA | igual ao 13 D-05 |
| P-14 | Um cartão + uma conversa; sem três colunas | invariante | kit |

### 5.2 Estados

| ID | Capacidade | Estado | Dono |
|---|---|---|---|
| S-01 | Publicar `status_id` (1, 2, 3, 4, 5, 6, 10) + `status` (rótulo GLPI) | ALVO_LEITURA | BFF ADDITIVE |
| S-02 | Badge e filtro por **id**, não por substring do nome | ALVO_LEITURA | MFE / kit |
| S-03 | Os sete rótulos aparecem como o GLPI mandou | ALVO_LEITURA | sem dicionário paralelo |
| S-04 | Variante de Approval e Planned distintas o bastante (Approval ≠ Novo; Planned pode herdar warning) | ALVO_LEITURA | mapa id→variante do kit |
| S-05 | Grupo `pending` (4) na lista | ALVO_RECORTE | já no 13 G-23 |
| S-06 | Grupo `approval` (10) na lista | ALVO_RECORTE | hoje diluído em `open` |
| S-07 | `open` continua incluindo 10 até existir `approval` | invariante de compat | não quebrar quem já filtra `open` |
| S-08 | Colaborador **não** escolhe status ao abrir nem no detalhe | invariante | GLPI nasce Novo; técnico transita |
| S-09 | Motivo de pendência | CONSOLE_GLPI | a página só mostra o status Pendente |
| S-10 | PATCH de status pelo MFE | FORA | sem rota; matriz vive no GLPI |

## 6. Contrato-alvo (quando for implementar)

ADDITIVE. Não é etapa de código.

`GET /tickets` e `GET /tickets/{id}`:

| Hoje | Permanece | Novo |
|---|---|---|
| `status` string | rótulo GLPI | `status_id` inteiro |
| — | — | `can_followup` boolean (se H1 da página fechar) |
| — | — | `observers_display_name` opcional |

Query da lista:

| Hoje | Novo |
|---|---|
| `status=open\|in_progress\|solved\|closed` | `pending`, `approval` (ADDITIVE) |
| `status=10` já válido | a tela pode passar a oferecer |

O MFE antigo que só lê `status` string **não quebra**.

## 7. Arquitetura-alvo

```text
GLPI Ticket.status {id, name}
  → BFF publica status_id + name + (can_followup)
  → lista e detalhe: badge por id, rótulo por name
  → recorte: grupos canônicos incluindo pending e approval
```

| Camada | Faz | Não faz |
|---|---|---|
| GLPI | estado real, matriz, solução | — |
| BFF | id + rótulo + grupos; não traduz «Novo» | PATCH de status |
| MFE | badge do kit, esconde Responder se `can_followup=false` | if por nome («solucion») |
| Kit | variantes `info/warning/success/neutral` | cor verde do ponto GLPI |

## 8. Superfícies

| Fluxo | Superfície | Papel |
|---|---|---|
| Ver estado | lista (coluna) e detalhe (cartão) | mesma fonte `status_id` |
| Filtrar | [`13`](./13-listagem-de-chamados.md) | S-05, S-06 |
| Conversar | detalhe | [`10`](./10-conversa-do-chamado.md) / [`12`](./12-conteudo-da-mensagem.md) |
| Fechado sem resposta | detalhe | P-06 |
| Aprovar / pesquisar | detalhe | H5 |
| Console | host GLPI | abas da foto 1101 |
| Ajuda | `helpTooltips.detail` | estados em português do GLPI, sem id técnico |

## 9. Estado antes × depois

| Caso | Hoje | Alvo |
|---|---|---|
| P0 — 1101 Novo, sem técnico | título, #1101, badge Novo, conversa, Responder | + `status_id=1`; datas absolutas; técnico vazio continua válido |
| Irmão — Aprovação (10) | some em «Abertos»; badge neutro se o nome não tiver «novo» | grupo `approval`; variante própria |
| Irmão — Pendente | «Abertos»; badge se o rótulo tiver «pendente» | grupo `pending`; badge por id |
| Irmão — Fechado | Responder visível; POST pode 403 | sem campo se `can_followup=false` |
| Negativo — mudar para Pendente na Minha DELPI | não existe | continua sem |
| Negativo — copiar abas da foto | não | continua sem |
| Invariante | privado, tarefa, solução, upload, entidade | 10 / 12 / A-08 / HD-011 |
| Identidade | id / e-mail | status também por **id**, não por nome |

## 10. Decisões travadas × não prontas

### Travadas

| ID | Decisão | Evidência |
|---|---|---|
| D-01 | Página do solicitante, não o formulário de três colunas | 10 + foto 1101 |
| D-02 | Sete status fixos; `status_id` é a chave | doc lifecycle |
| D-03 | Rótulo = `name` do GLPI; sem tabela PT no BFF | uma fonte |
| D-04 | Sem PATCH de Ticket / status / atores | contrato atual |
| D-05 | Aprovar, reabrir, satisfação = H5 | 05 |
| D-06 | Excluir Novo = console | P-10 |
| D-07 | Tipo/prioridade/impacto fora | lifecycle + formulário só urgência |
| D-08 | `open` não perde o 10 até existir `approval` | compat |
| D-09 | Conversação e HTML continuam 10 e 12 | ownership |

### Não prontas — fechadas em E6.S1 (21/09/2026)

| ID | Veredito | Bloqueia |
|---|---|---|
| H1 | **PROVEN com drift** — Colaborador: follow-up em status **5 = 200**; status **6 = 403** `ERROR_RIGHT_MISSING`. PATCH de status = 403. | P-06: `can_followup=false` **só** no fechado |
| H2 | **PROVEN** — schema + live: `1 Novo`, `2 Em atendimento (atribuído)`, `5 Solucionado`, `6 Fechado`; enum também 3/4/10 | S-03 conferido; sem dicionário PT no BFF |
| H3 | **PARCIAL** — 1101 traz `team[].role=requester` (+ id/nome); 1114 veio `team[]` vazio no Super-Admin; `POST …/TeamMember` observer = 201 | P-05: publicar observador **se** o GET trouxer o role |
| H4 | **FORA** para PATCH — Colaborador não muda status (403). Reabrir/fechar não é PATCH neste perfil. | H10 só com operation de Solution/Validation |

## 11. Prova, quando houver autorização

| Caso | Resultado |
|---|---|
| Positivo — Novo | 1101 abre com `status_id=1` e rótulo do GLPI |
| Irmão — os sete ids | cada um tem badge estável mesmo se o nome mudar de acento |
| Irmão — lista | `approval` e `pending` recortam; `open` ainda inclui 10 |
| Negativo — nome | dois status cujo rótulo contém «atendimento» não se confundem no **filtro** (filtro é id/grupo) |
| Negativo — escrita | a tela não envia `status` no POST de abertura nem de follow-up |
| Negativo — foto 1101 | abas, atores editáveis, 2/15, Salvar não aparecem |
| Fechado | sem Responder se o BFF disser que não pode |
| F5 | o mesmo chamado e o mesmo estado |
| Tema | tokens do kit; sem ponto verde fixo |

## 12. Ajuda

No mesmo entregável de código, sem path de API:

| Tooltip | Alvo |
|---|---|
| `helpTooltips.detail` | o selo é o estado no helpdesk (novo, em atendimento, pendente, solucionado, fechado, aguardando aprovação). Responder some quando o chamado não aceita mais mensagem. Aprovar solução, se existir, entra só com H5 |

## 13. O que este arquivo não faz

- não abre E*.S* nem H5;
- não autoriza o formulário de três colunas;
- não autoriza PATCH de status;
- não cria dicionário de status em português no código;
- não substitui [`10`](./10-conversa-do-chamado.md), [`12`](./12-conteudo-da-mensagem.md) ou [`13`](./13-listagem-de-chamados.md).

Quando o pedido passar de «documentar» para «implementar», a primeira subetapa é publicar `status_id` e fechar H1 (Responder em solucionado/fechado). Só então P-04…P-06 e S-01…S-06 viram plano.
