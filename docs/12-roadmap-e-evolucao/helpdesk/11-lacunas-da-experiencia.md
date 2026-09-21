# 11 — Lacunas da experiência

> **Status:** inventário da experiência. A onda de lista, filtros e prévia de anexo está em implementação. Não altera [`06-plano-execucao.md`](./06-plano-execucao.md).
> **Tela publicada:** [`WIREFRAMES.md`](./WIREFRAMES.md).
> **Conversa já especificada:** [`10-conversa-do-chamado.md`](./10-conversa-do-chamado.md).
> **Contrato vigente:** [`03-contrato.md`](./03-contrato.md).

Este documento lista o que a pessoa ainda não encontra em Meus Chamados de TI, comparado com o que as fotos de 21/09/2026 mostram no MFE e no GLPI. Não é etapa de código.

O produto continua o do colaborador. O console do técnico permanece em `https://helpdesk.centraldelpi.com.br`.

## 1. O que as fotos mostram

| Foto | Superfície | O que se vê |
|---|---|---|
| Detalhe MFE, chamado 2 | `minhadelpi.com.br/apps/helpdesk/tickets/2` | seção Conversa, urgência Média, status Em atendimento (atribuído), duas bolhas à direita, data `19/02/2026`, arquivo como botão `Baixar 51-eQqV5j-…jpg`, campo Responder |
| Lista MFE | `/apps/helpdesk` | cartões com título, urgência e status; um item Solucionado; sem busca, sem filtro, sem data, sem id |
| Detalhe GLPI, chamado 6288 | `helpdesk.centraldelpi.com.br/front/ticket.form.php?id=6288` | conversa com nome, data, foto do técnico, imagem no meio da mensagem, atores à direita, abas à esquerda |
| Imagem no GLPI | o mesmo chamado | a foto abre no próprio fio, com o texto em volta |
| Lista GLPI | `front/ticket.php` | busca, ordenação, colunas (id, título, entidade, status, datas, solicitante, técnico, categoria, último editor), paginação 15/128128, contadores do parque |

A lista do GLPI é a bancada Super-Admin. Meus Chamados de TI não copia essa grade nem os 128 mil chamados. Copia a capacidade de **achar e ler o próprio chamado**, e de **ver a imagem** sem depender do nome cru do arquivo.

## 2. O que já está publicado

| Capacidade | Onde |
|---|---|
| Lista dos chamados visíveis ao token | `GET /tickets` → tabela com ordenação de coluna |
| Abrir chamado | título, descrição, categoria, urgência |
| Conversa | abertura + acompanhamentos em `HelpdeskMessageThread` |
| Responder | texto + `Idempotency-Key` |
| Arquivo já ligado ao chamado | botão Baixar; 404 se o `document_id` não for daquele chamado |
| Console do técnico | rota `helpdesk.console`, fora do MFE |

A lista já devolve `updated_at`. A tela não mostra. O detalhe já devolve `created_at`, `requester_display_name`, `attachments[].mime`. A tela não usa o mime para prévia e, na foto do chamado 2, o nome do solicitante não aparece.

## 3. Ledger do que falta

Estado de cada item neste inventário:

```text
PROXIMA_ONDA          → entra no plano seguinte da experiência do colaborador
CONTRATO_AUSENTE      → o JSON/query ainda não existe
KIT_JA_EXISTE         → o primitivo está no plugin-ui; o MFE ainda não monta
HIPOTESE_A_VALIDAR    → falta provar no pipeline real antes de receitar
CONSOLE_GLPI          → fica no host do helpdesk
BLOQUEADO             → evidência impede a entrega agora
```

### 3.1 Lista — achar o chamado

Pedido explícito das fotos: filtros e listagem de dados.

| ID | Lacuna | Evidência | Estado | Dono |
|---|---|---|---|---|
| L-01 | Busca por texto (título / conteúdo visível) | lista MFE sem campo; GLPI tem «Pesquisar» | IMPLEMENTADO | BFF `q` + `FilterInputField` |
| L-02 | Filtro de status | a lista mistura Novo, Em atendimento e Solucionado; o subtítulo diz «abertos» | IMPLEMENTADO | BFF + `FilterSelectField` |
| L-03 | Filtro de urgência | o dado já existe no cartão; não dá para restringir | IMPLEMENTADO | BFF + kit de filtro |
| L-04 | Filtro de categoria | categorias já vêm de `GET /ticket-categories` | IMPLEMENTADO | BFF + filtro |
| L-05 | Filtro de período (abertura ou última atualização) | GLPI tem data de abertura e última atualização; o MFE não mostra nenhuma | IMPLEMENTADO | BFF `updated_from`/`updated_to` + date |
| L-06 | Id do chamado visível | GLPI coluna ID; MFE só o path | IMPLEMENTADO | apresentação; `id` já está no JSON |
| L-07 | Data de abertura na lista | GLPI «Data de abertura»; BFF da lista não publica `created_at` | IMPLEMENTADO | `TicketSummary.created_at` |
| L-08 | Data da última atualização na lista | contrato já tem `updated_at`; a tela ignora | IMPLEMENTADO | `ticketRecordFields` |
| L-09 | Técnico atribuído na lista e no detalhe | GLPI «Atribuído»; o `team` com `role=assigned` já existe no ticket | IMPLEMENTADO | `assigned_display_name` |
| L-10 | Ordenar (última atualização, abertura, título) | GLPI «Ordenado por Última atualização»; BFF devolve a ordem do GLPI sem parâmetro | IMPLEMENTADO | query `sort` |
| L-11 | Paginação | GLPI 15 por página; BFF pede a coleção inteira de `GET /Assistance/Ticket` | IMPLEMENTADO | `page`/`has_more`; sem total inventado |
| L-12 | Estado vazio com filtro ativo | hoje o vazio significa «nenhum chamado»; com filtro precisa dizer «nenhum neste recorte» | IMPLEMENTADO | apresentação + ajuda |

Filtros: `createDashboardFiltersKit`. Lista: `HelpdeskDataTable` (`DataTable` do kit), com scroll horizontal intencional. Sem coluna de entidade, último editor ou contadores do parque. Técnico aparece, mas não ordena — a HLAPI não tem propriedade simples de atribuído.

Não copiar da foto do GLPI para esta lista: entidade, data de solução, último editor, contadores do parque (1 000 novos, 128 128 linhas). Isso é a bancada.

### 3.2 Arquivo — prévia, modal e download

Pedido explícito das fotos: a imagem como prévia e um modal com download.

| ID | Lacuna | Evidência | Estado | Dono |
|---|---|---|---|---|
| A-01 | Miniatura da imagem na conversa | chamado 2 no MFE é um botão com o nome hash do GLPI; no 6288 a foto está no fio | IMPLEMENTADO | `AttachmentPreviewStrip` no `belowBody` |
| A-02 | Clicar abre modal de prévia | GLPI mostra a imagem grande no próprio chamado | IMPLEMENTADO | `FilePreviewModal` (`headerActions` já aceita Baixar) |
| A-03 | Download no modal, não no lugar da prévia | o download autenticado já existe | IMPLEMENTADO | `GET .../attachments/{document_id}` |
| A-04 | PDF e outros tipos que o kit prevê | `FilePreviewModal` já distingue image/pdf/text/docx; arquivo sem prévia continua só download | IMPLEMENTADO | mesmo modal |
| A-05 | Blob só na memória da página | a regra de upload persistente já proíbe gravar o arquivo na Minha DELPI | HERDADO | `URL.createObjectURL` + revoke |
| A-06 | Documento de outro chamado | 404 sem bytes — não pode mudar | invariante | serviço atual |
| A-07 | Imagem de um acompanhamento específico | no 6288 a foto está na mensagem do técnico; a HLAPI do Followup não devolve essa lista; hoje todos os `Document` da timeline vão para a abertura | HIPOTESE_A_VALIDAR | não inventar o vínculo |
| A-08 | Enviar arquivo novo | HLAPI 11.0.5 só aceita JSON; API legada desligada | BLOQUEADO | decisão explícita para ligar a API antiga |

Kit já existente: `createDashboardAttachmentPreviewStrip`, `FilePreviewModal`, `resolveFilePreviewKind`, `useFilePreviewLoader`. O helpdesk não os importa. A prévia usa o mesmo GET de download, com `Accept: application/octet-stream`, limite de 20 MB já no BFF. Sem CSS de thumb no MFE.

### 3.3 Conversa — o que a foto do chamado 2 ainda não entrega

A conversa em bolhas já foi publicada. As fotos mostram o corte que ainda falta.

| ID | Lacuna | Evidência | Estado |
|---|---|---|---|
| C-01 | Nome do solicitante na abertura | chamado 2: bolha sem «Robério» / iniciais reais | IMPLEMENTADO no tradutor (`requester` ou `user_recipient`); lado da bolha depende do nome ao vivo |
| C-02 | Nome de quem acompanhou | GLPI 6288 escreve Mainena e Michael; o MFE no 2 só mostra o relógio | IMPLEMENTADO no tradutor (`display_name` / nome completo) |
| C-03 | «Criado em … por …» | o GLPI escreve a frase; o MFE só põe a data relativa ou `dd/mm/aaaa` | IMPLEMENTADO — rótulo «Criado em …» |
| C-04 | Foto do técnico | o 6288 tem avatar com foto; este módulo não guarda foto | CONSOLE_GLPI / fora — iniciais bastam |
| C-05 | Lado da bolha | no 2 as duas mensagens foram para a direita; `mine` hoje é «autor = solicitante» | rever quando C-01 estiver preenchido |
| C-06 | Título da abertura vs cartão de urgência | o cartão do 2 virou «Média» porque a categoria está vazia (`itilcategories_id=0`) | já documentado; não inventar categoria |
| C-07 | Tarefa, solução, aprovação, atores, SLA | fotos do 6288 | CONSOLE_GLPI — já em [`10-conversa-do-chamado.md`](./10-conversa-do-chamado.md) |

### 3.4 Abrir chamado

| ID | Lacuna | Estado |
|---|---|---|
| N-01 | Anexar arquivo na abertura | BLOQUEADO — mesmo motivo de A-08 |
| N-02 | Escolher entidade ou abrir em nome de outro | fora — HD-011 |
| N-03 | Modelo de chamado / origem / pendência | CONSOLE_GLPI |

### 3.5 Depois do fechamento e bancada

Já estavam em H5. Continuam fora desta onda de filtros/prévia, salvo decisão nova.

| ID | Lacuna | Estado |
|---|---|---|
| H-01 | Aprovar ou recusar solução | CONSOLE_GLPI / H5 |
| H-02 | Pesquisa de satisfação | H5 |
| H-03 | Fila, atribuição, tarefa, validação | CONSOLE_GLPI |
| H-04 | Mudança e problema | outro itemtype |
| H-05 | Itens, custos, base de conhecimento, histórico, estatísticas | CONSOLE_GLPI |
| H-06 | Seletor de entidade | H5 |

## 4. Contrato da lista

Publicado em [`03-contrato.md`](./03-contrato.md). `GET /tickets` agora devolve `created_at`, `assigned_display_name`, `page`, `page_size` e `has_more`, e aceita `q`, `status`, `urgency_id`, `category_id`, `updated_from`, `updated_to`, `sort`, `page` e `page_size`. O binding HLAPI (`filter` RSQL, `start`, `limit`, `sort`) foi lido em `api.php/doc.json` 2.2.0.

Prévia de arquivo **não** cria rota nova. O modal reusa `GET /tickets/{id}/attachments/{document_id}`. O browser não chama o GLPI.

## 5. Alvo visual da próxima onda

Uma coluna, kit da Minha DELPI, tokens `--delpi-ui-*`. Sem grade do GLPI e sem verde fixo.

```text
/apps/helpdesk
  HelpdeskPageHeader
  HelpdeskSectionCard  «Meus chamados»
    FiltersRow          busca, status, urgência, categoria, período
    HelpdeskDataTable   colunas com ordenação no helpdesk
    paginação Anterior / Próxima via has_more

/apps/helpdesk/tickets/{id}
  Conversa  (já publicada)
    belowBody da abertura
      AttachmentPreviewStrip   miniatura se image/pdf
    FilePreviewModal
      prévia
      [ Baixar ]
```

Claro e escuro continuam no mapeamento já feito em `.dashboard-helpdesk`. Ajuda (`helpTooltips.list` e `.detail`) muda no mesmo entregável: filtrar, ver data, abrir a imagem, baixar. Sem path de API. O subtítulo «Chamados abertos no seu nome» deixa de mentir se a lista incluir Solucionado — ou o filtro padrão passa a ser «abertos», com Solucionado/Fechado como recorte explícito.

## 6. Hipótese da lista truncada

Na mesma sessão, o MFE mostrou uns seis chamados e o GLPI Super-Admin mostrou 128 128. Três leituras cabem:

```text
H1  o token OAuth do BFF enxerga só o perfil colaborador — lista pequena, filtro pode ser local
H2  a HLAPI já pagina e o BFF só lê a primeira página — a pessoa perde chamado sem saber
H3  o Super-Admin no MFE um dia recebe o parque inteiro — filtrar no browser é inaceitável
```

Nenhuma está confirmada neste inventário. Antes de implementar L-01…L-11, a primeira subetapa é medir no `GET /Assistance/Ticket` de produção: quantos itens vêm, se há `start`/`limit`/`filter`, e o que o token do colaborador vê versus o do Super-Admin. Sem isso, não há receita de paginação.

## 7. O que não copiar

| Peça da foto do GLPI | Decisão |
|---|---|
| 11 colunas e rolagem horizontal | o wireframe vigente: cartão em uma coluna |
| Contadores do parque | bancada |
| Entidade, último editor, data de solução | bancada; a entidade segue a padrão do usuário |
| Foto de perfil | iniciais |
| Imagem embutida como HTML do GLPI | blob autenticado no modal do kit; sem HTML cru |
| Abas, atores editáveis, excluir, salvar | console |
| Envio de arquivo no menu Responder | BLOQUEADO |

## 8. Prova, quando houver implementação

Ainda não é etapa. Quando for planejada, a prova mínima é:

| Caso | Resultado |
|---|---|
| Positivo — filtro | «Monitor falhando» aparece ao filtrar Em atendimento / Média; some ao filtrar só Solucionado |
| Irmão — busca | o título «Email não funcionando» sai pela busca; um título que não existe deixa a lista vazia do recorte, não um erro |
| Negativo — permissão | 403 e 409 continuam banner; filtro não transforma proibido em lista vazia |
| Positivo — imagem | no chamado 2, a jpg vira miniatura; o clique abre o modal e o Baixar baixa o mesmo `document_id` |
| Irmão — sem prévia | um pdf ou um tipo `none` abre o modal com «pré-visualização não disponível» e ainda baixa |
| Negativo — arquivo alheio | `document_id` que não está no chamado continua 404, sem bytes |
| F5 | filtro na URL ou estado derivado do GET; recarregar não inventa chamado |
| Tema | claro e escuro pelos tokens do kit |

## 9. Fora deste inventário como autorização

Este arquivo não abre E*.S*, não marca H5 como `PROVEN` e não liga a API legada. [`10-conversa-do-chamado.md`](./10-conversa-do-chamado.md) descreve a conversa já publicada. O que falta daqui para a frente é lista com filtro, dados no cartão, prévia e modal — mais as hipóteses C-01, A-07 e L-11, que precisam de evidência viva antes da receita.
