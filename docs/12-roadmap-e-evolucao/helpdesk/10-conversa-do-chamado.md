# 10 — Conversa do chamado

> **Status:** a tela publicada está em [`WIREFRAMES.md`](./WIREFRAMES.md) §3. Este arquivo permanece o inventário da decisão.
> **Contrato vigente:** [`03-contrato.md`](./03-contrato.md).
>
> O `createDashboardMessageThread` já saía pelo barrel do plugin-ui. A entrega estendeu o fio com título, texto puro e identidade na bolha do solicitante; não criou outro componente.
> **Corpo da mensagem (HTML, formatação, imagem):** inventário em [`12-conteudo-da-mensagem.md`](./12-conteudo-da-mensagem.md). Não implementar a partir deste arquivo.

Este documento descreve o que falta para o detalhe de Meus Chamados de TI parecer a conversa do GLPI, dentro do kit da Minha DELPI. As fotos de referência são o chamado `1114` em `helpdesk.centraldelpi.com.br/front/ticket.form.php?id=1114`, visto pela interface padrão (central), com o usuário Super-Admin.

## 1. O que a foto é

A tela do GLPI tem três colunas mais uma barra fixa de salvar. O que a pessoa chama de chat é só a coluna do meio, na aba **Chamado**:

| Peça vista | No chamado 1114 |
|---|---|
| Cabeçalho | ponto verde, título «Chamado teste Api Minha delpi (1114)», paginação 1/15 |
| Mensagem de abertura | avatar «RT», fundo verde, «Criado em: 2 horas atrás por Robério Teixeira», título em negrito e a descrição |
| Responder | menu com criar tarefa, adicionar solução, adicionar documento e pedir aprovação |
| Barra inferior | excluir e salvar |

O restante da foto é o console do técnico: abas (Estatísticas, Aprovações, Base de conhecimento, Itens, Custos, Projetos, Histórico), atores editáveis, itens, níveis de serviço e objetos relacionados. Isso continua em `https://helpdesk.centraldelpi.com.br` para quem tem `helpdesk.console`. Meus Chamados de TI não ganha essa moldura.

A interface das fotos não é a interface simplificada de autoatendimento. Quem entra como colaborador no GLPI não vê o mesmo menu. O alvo da Minha DELPI é a conversa que o solicitante acompanha, não o formulário central inteiro.

## 2. O que a documentação do GLPI define

Fontes: [Tickets](https://help.glpi-project.org/documentation/modules/assistance/tickets), [Followup](https://help.glpi-project.org/documentation/modules/assistance/tabs/followup) e [Solution](https://help.glpi-project.org/documentation/modules/assistance/tabs/solution). A HLAPI 2.2 de produção (`/api.php/doc.json` no GLPI 11.0.5) confirma os campos citados abaixo.

| Ação no GLPI | O que a documentação diz | No chat da Minha DELPI |
|---|---|---|
| Mensagem de abertura | o chamado nasce com título, conteúdo HTML e data de criação | primeira bolha da conversa |
| Responder | acompanhamento: comentário, documento opcional, motivo de pendência; o chamado pode ir para pendente | só o comentário público, no compositor que já existe |
| Acompanhamento privado, origem, modelo, promover a chamado | recursos da interface padrão, com direito de ver privado | ficam no console |
| Tarefa | trabalho interno do técnico | fica no console; a timeline atual já esconde `Task` |
| Solução | encerra o fluxo e pede aprovação do solicitante; sem resposta, fecha sozinho (15 dias por padrão da doc) | bolha futura, não desta conversa |
| Aprovar ou recusar solução / pesquisa | direito «Approve solution / Reply survey (my ticket)», a partir do GLPI 11 | onda posterior, já fora em [`05-roadmap.md`](./05-roadmap.md) |
| Documento | pode ir junto do acompanhamento ou da solução | baixar o que já está no chamado já está publicado; enviar arquivo novo continua bloqueado pela HLAPI |

Papéis da equipe no schema `Ticket.team`: `requester`, `assigned`, `observer`. O autor da bolha de abertura é o membro `requester`. `user_recipient` é outro campo e não substitui o solicitante. O acompanhamento traz `user`, `content` (HTML), `date_creation`, `is_private` e `timeline_position`.

## 3. O que a tela publicada faz

Em `/apps/helpdesk/tickets/{id}`, como em [`WIREFRAMES.md`](./WIREFRAMES.md) §3:

- cabeçalho do kit com o título e **Atualizar**;
- cartão com categoria, urgência e status;
- conversa: bolha de abertura (solicitante, tempo, título e descrição) e bolhas de acompanhamento;
- **Baixar** na abertura, para arquivo já ligado ao chamado;
- campo **Responder** e **Enviar**.

A abertura aparece mesmo sem acompanhamento. Tarefa e acompanhamento privado não entram.

## 4. Alvo visual

Uma coluna, no chrome que o portal já desenha. Sem menu lateral de abas, sem coluna de atores e sem barra de salvar.

```text
HelpdeskPageHeader
  título do chamado
  [ Atualizar ]

HelpdeskSectionCard  «Conversa»
  ● status          categoria, se houver          urgência

  bolha de abertura
    avatar com as iniciais
    nome do solicitante · tempo relativo
    título
    descrição em texto puro

  bolha de acompanhamento
    avatar · nome · tempo
    texto
    baixar arquivo, quando o arquivo estiver ligado a essa mensagem

  HelpdeskTextArea  «Responder»
  [ Enviar ]
```

Claro e escuro continuam nos tokens `--delpi-ui-*` já mapeados em `.dashboard-helpdesk`. O verde da bolha do GLPI não entra como cor fixa. A bolha de quem escreveu e a bolha de outra pessoa se distinguem pelo tom do kit (`mine` / a outra), não pela paleta do GLPI.

O tempo «2 horas atrás» é formatação da tela a partir de `date_creation`. O JSON guarda o instante.

As iniciais saem do nome exibido. A foto da Minha DELPI (Core) só entra quando o BFF marca a mensagem como do usuário logado, por id do GLPI ou e-mail. Nome não identifica autor. Foto do GLPI e armazenamento de avatar continuam fora deste módulo.

## 5. Componente

O `HelpdeskTimeline` atual (`createTimeline`) é uma trilha de eventos: título, hora e detalhe. Não é a bolha com avatar da foto.

O kit já tem `MessageThread` em `plugins/plugin-ui/src/components/collaboration/MessageThread.tsx`: iniciais, bolha, lado «meu» / outro, hora, texto e um espaço `belowBody` para o anexo. O factory `createDashboardMessageThread` já saía pelo barrel que o MFE importa. A tela usa esse factory, com título, texto puro e o nome do solicitante visível na própria bolha. Nenhum CSS de bolha nasceu em `plugins/helpdesk`.

`RoomConversationShell` é o chrome das salas de outro produto. O helpdesk não importa esse shell nem a regra de sala.

O compositor de resposta continua `HelpdeskTextArea` e `ActionButton`. `MentionComposer` fica nas salas; o acompanhamento desta entrega é texto puro, como o contrato já devolve.

## 6. Contrato

| Necessidade da conversa | Onde está no GLPI 11.0.5 | No BFF |
|---|---|---|
| Instante da abertura | `Ticket.date_creation` | `created_at` no detalhe |
| Nome do solicitante | `Ticket.team[]` com `role=requester`; a limpeza da equipe também preserva `display_name` | `requester_display_name` |
| Texto da abertura | `Ticket.content` (HTML) | `description`, já em texto puro; HTML sanitizado só no alvo de [`12-conteudo-da-mensagem.md`](./12-conteudo-da-mensagem.md) |
| Acompanhamento | `Followup.user`, `content`, `date_creation` | `timeline[]` com `author_display_name`, `content`, `created_at`, `mine` |
| Autor da mensagem | `Followup.user.id` / `team[].id` e `GET /session` → `user_id`; e-mail do JWT se o GLPI trouxer e-mail | `mine` / `requester_mine` — nunca o nome |
| Acompanhamento privado | `Followup.is_private` | não entra em `timeline` |
| Arquivo do chamado | `Timeline` tipo `Document`, `documents_id` | `attachments[]` e o download já publicados; a tela mostra o botão na abertura |
| Arquivo de um acompanhamento | documento ligado ao follow-up, não ao chamado | a HLAPI do item `Followup` não devolve essa lista; o download continua do chamado inteiro |

Texto visível continua passando pelo mesmo reparo de acento e pela remoção de HTML já feitos no tradutor. A conversa não volta a mostrar tag.

Enviar arquivo novo, tarefa, solução, aprovação, atores editáveis, SLA e entidade continuam fora. O envio de arquivo esbarra na HLAPI, que não recebe o binário; a API legada permanece desligada.

## 7. O que não copiar

| Peça da foto | Decisão |
|---|---|
| Abas Estatísticas, Aprovações, Base de conhecimento, Itens, Custos, Projetos, Histórico | console GLPI |
| Atores, itens, níveis de serviço, objetos relacionados | console GLPI; a entidade segue a padrão do usuário |
| Excluir e Salvar | o chamado não se edita por essa tela |
| Paginação 1/15 entre chamados | a lista da Minha DELPI já é a navegação |
| Criar tarefa, adicionar solução, pedir aprovação | console; solução e pesquisa ficam na onda posterior |
| Modelo, origem, pendência e acompanhamento privado | interface padrão; o solicitante só responde em público |
| Verde, tipografia e três colunas do GLPI | o kit e uma coluna |

## 8. Prova

A prova automatizada cobre a abertura, o acompanhamento de outra pessoa, o solicitante vazio, a tarefa e o privado. A conferência no browser fica para quando o MFE for publicado.

| Caso | Resultado |
|---|---|
| Positivo | o chamado 1114 abre com a bolha «RT / Robério Teixeira», o título e a descrição, sem «nenhum evento» no lugar dessa abertura |
| Irmão | um acompanhamento de outra pessoa aparece como outra bolha, com o nome e a hora dele |
| Negativo | tarefa, solução, aprovação e campo de ator não aparecem; acompanhamento privado não aparece para o solicitante |
| Arquivo | o botão baixar continua só para documento daquele chamado |
| Tema | claro e escuro usam o token do kit; recarregar a página mantém a mesma conversa |

A ajuda in-app (`helpTooltips.detail`) muda no mesmo entregável, descrevendo responder e baixar, sem path de API.
