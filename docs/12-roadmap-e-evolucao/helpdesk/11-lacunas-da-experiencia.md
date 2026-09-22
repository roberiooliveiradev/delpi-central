# 11 — Lacunas da experiência

> **Status:** inventário histórico. L-01…L-12, C-08 e G-05 **IMPLEMENTADOS**. A-08/H12 Document upload BFF **PROVEN**; **colar + F5 preview = PROVEN**. **H10 ciclo write + TicketValidation PROVEN**. Residuais de produto: bancada FORA. Paridade: [`12`](./12-conteudo-da-mensagem.md)–[`15`](./15-capacidades-glpi.md). Não altera [`06-plano-execucao.md`](./06-plano-execucao.md).
> **Tela publicada:** [`WIREFRAMES.md`](./WIREFRAMES.md).
> **Conversa:** [`10-conversa-do-chamado.md`](./10-conversa-do-chamado.md).
> **Contrato vigente:** [`03-contrato.md`](./03-contrato.md).

Este documento lista o que a pessoa ainda não encontra em Meus Chamados de TI frente ao GLPI. Não é etapa de código.

O produto continua o do colaborador. O console do técnico permanece em `https://helpdesk.centraldelpi.com.br`.

## 1. O que as fotos mostram

| Foto | Superfície | O que se vê |
|---|---|---|
| Detalhe MFE, chamado 2 | `minhadelpi.com.br/apps/helpdesk/tickets/2` | seção Conversa, urgência Média, status Em atendimento (atribuído), duas bolhas à direita, data `19/02/2026`, arquivo como botão `Baixar 51-eQqV5j-…jpg`, campo Responder |
| Lista MFE | `/apps/helpdesk` | **publicado agora:** tabela + filtros (foto 21/09/2026). A frase antiga «cartões sem busca» está obsoleta; paridade em [`13-listagem-de-chamados.md`](./13-listagem-de-chamados.md) |
| Detalhe GLPI, chamado 6288 | `helpdesk.centraldelpi.com.br/front/ticket.form.php?id=6288` | conversa com nome, data, foto do técnico, imagem no meio da mensagem, atores à direita, abas à esquerda |
| Imagem no GLPI | o mesmo chamado | a foto abre no próprio fio, com o texto em volta |
| Lista GLPI | `front/ticket.php` | busca, ordenação, colunas (id, título, entidade, status, datas, solicitante, técnico, categoria, último editor), paginação 15/128128, contadores do parque |

A lista do GLPI é a bancada Super-Admin. Meus Chamados de TI não copia essa grade nem os 128 mil chamados. Copia a capacidade de **achar e ler o próprio chamado**, e de **ver a imagem** sem depender do nome cru do arquivo.

## 2. O que já está publicado

| Capacidade | Onde |
|---|---|
| Lista dos chamados visíveis ao token | `GET /tickets` → tabela com ordenação de coluna |
| Abrir chamado | título e descrição à esquerda; categoria e urgência à direita |
| Conversa | abertura + acompanhamentos em `HelpdeskMessageThread` `bodyMode=html` |
| Compositor | `HelpdeskRichTextField` na abertura e no Responder |
| Responder | texto + `Idempotency-Key` |
| Arquivo já ligado ao chamado | botão Baixar; 404 se o `document_id` não for daquele chamado |
| Console do técnico | rota `helpdesk.console`, fora do MFE |

A lista mostra `created_at`, `updated_at`, `solved_at` e `closed_at` em data-hora absoluta; requerente é coluna opcional (`requester_display_name`). O detalhe mostra solicitante na abertura, técnico no cartão e prévia de anexo pelo mime. Frases antigas («cartões», «datas relativas», «a tela não mostra data / mime / nome») são **drift** — corrigidas em 21/09/2026.

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
| L-01 | Busca por texto (título / conteúdo visível) | `q` OR content — G-21 **IMPLEMENTADO** | **IMPLEMENTADO** | BFF `q` + `FilterInputField` |
| L-02 | Filtro de status | grupos + pending/approval | **IMPLEMENTADO** | BFF + `FilterSelectField` |
| L-03 | Filtro de urgência | o dado já existe no cartão; não dá para restringir | **IMPLEMENTADO** | BFF + kit de filtro |
| L-04 | Filtro de categoria | categorias já vêm de `GET /ticket-categories` | **IMPLEMENTADO** | BFF + filtro |
| L-05 | Filtro de período (abertura ou última atualização) | `updated_*` + `created_*` — G-25 **IMPLEMENTADO** | **IMPLEMENTADO** | BFF + date |
| L-06 | Id do chamado visível | GLPI coluna ID; MFE só o path | **IMPLEMENTADO** | apresentação; `id` já está no JSON |
| L-07 | Data de abertura na lista | data-hora absoluta | **IMPLEMENTADO** | `TicketSummary.created_at` |
| L-08 | Data da última atualização na lista | absoluta | **IMPLEMENTADO** | `TicketListTable` |
| L-09 | Técnico atribuído na lista e no detalhe | GLPI «Atribuído»; o `team` com `role=assigned` já existe no ticket | **IMPLEMENTADO** | `assigned_display_name` |
| L-10 | Ordenar (última atualização, abertura, título) | multi-sort | **IMPLEMENTADO** | query `sort` |
| L-11 | Paginação + `page_size` | 10/20/50 | **IMPLEMENTADO** | `start`/`limit` +1 |
| L-12 | Estado vazio com filtro ativo | «nenhum neste recorte» | **IMPLEMENTADO** | apresentação + ajuda |

Filtros: `createDashboardFiltersKit`. Lista: `HelpdeskDataTable` (`DataTable` do kit), com scroll horizontal intencional. Sem coluna de entidade, último editor ou contadores do parque. Técnico aparece, mas não ordena — a HLAPI não tem propriedade simples de atribuído.

Não copiar da foto do GLPI para esta lista: entidade, último editor, contadores do parque (1 000 novos, 128 128 linhas). Isso é a bancada. Data de resolução e demais colunas do solicitante: [`13-listagem-de-chamados.md`](./13-listagem-de-chamados.md).

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
| A-07 | Imagem de um acompanhamento específico | P0 6288 inexistente; Followup sem lista de docs (12-H4 FORA); Document fica na abertura | FORA — não inventar vínculo por bolha |
| A-08 | Enviar arquivo novo | HLAPI JSON-only; exceção H12 apirest Document | **IMPLEMENTADO** | `POST …/attachments` + LEGACY_* live; ledger `H12.upload.live` |

Kit: `HelpdeskAttachmentPreviewStrip` e `FilePreviewModal` **já ligados**. A prévia usa o GET de download, `Accept: application/octet-stream`, limite 20 MB. Sem CSS de thumb no MFE.

### 3.3 Conversa — o que a foto do chamado 2 ainda não entrega

A conversa em bolhas já foi publicada. As fotos mostram o corte que ainda falta.

| ID | Lacuna | Evidência | Estado |
|---|---|---|---|
| C-01 | Nome do solicitante na abertura | rótulo no tradutor; `mine` por id/e-mail (não pelo nome) | IMPLEMENTADO |
| C-02 | Nome de quem acompanhou | GLPI 6288 escreve Mainena e Michael; o MFE no 2 só mostra o relógio | IMPLEMENTADO no tradutor (`display_name` / nome completo) |
| C-03 | «Criado em … por …» | o GLPI escreve a frase; o MFE só põe a data relativa ou `dd/mm/aaaa` | IMPLEMENTADO — rótulo «Criado em …» |
| C-04 | Foto do técnico | o 6288 tem avatar com foto; este módulo não guarda foto | CONSOLE_GLPI / fora — iniciais bastam |
| C-05 | Lado da bolha | no 2 as duas mensagens foram para a direita; `mine` era «autor = solicitante» | IMPLEMENTADO — `mine` no BFF por id GLPI ou e-mail; nome só rótulo |
| C-06 | Título da abertura vs cartão de urgência | o cartão do 2 virou «Média» porque a categoria está vazia (`itilcategories_id=0`) | já documentado; não inventar categoria |
| C-07 | Tarefa, solução, aprovação, atores, SLA | fotos do 6288 e 1101 | CONSOLE_GLPI — página/estados em [`14-pagina-e-estados-do-chamado.md`](./14-pagina-e-estados-do-chamado.md) |
| C-08 | Formatação, HTML, imagem no corpo | allowlist BFF + `*_html` + rewrite + kit html | **IMPLEMENTADO** E8 — [`12`](./12-conteudo-da-mensagem.md) |

### 3.4 Abrir chamado

| ID | Lacuna | Estado |
|---|---|---|
| N-01 | Anexar arquivo na abertura | **IMPLEMENTADO** — pending no create + upload após `POST /tickets` (H12) |
| N-02 | Escolher entidade ou abrir em nome de outro | fora — HD-011 |
| N-03 | Modelo de chamado / origem / pendência | CONSOLE_GLPI — matriz em [`15-capacidades-glpi.md`](./15-capacidades-glpi.md) X-10 / X-15 |
| N-04 | Formulários / catálogo de serviços GLPI 11 | HIPOTESE — X-09 no 15 |

### 3.5 Depois do fechamento e bancada

Já estavam no fatia H5→H10/bancada. Continuam fora desta onda, salvo decisão nova / HLAPI.

| ID | Lacuna | Estado |
|---|---|---|
| H-01 | Aprovar ou recusar solução | **IMPLEMENTADO** H10 Branch B |
| H-02 | Pesquisa de satisfação | **IMPLEMENTADO** H10 Branch B |
| H-03 | Fila, atribuição, tarefa, validação | atribuição + validação **IMPLEMENTADAS**; tarefa CONSOLE_GLPI |
| H-04 | Mudança e problema | outro itemtype |
| H-05 | Itens, custos, base de conhecimento, histórico, estatísticas | CONSOLE_GLPI |
| H-06 | Seletor de entidade | HD-011 / FORA |

## 4. Contrato da lista

Publicado em [`03-contrato.md`](./03-contrato.md). `GET /tickets` agora devolve `created_at`, `assigned_display_name`, `page`, `page_size` e `has_more`, e aceita `q`, `status`, `urgency_id`, `category_id`, `updated_from`, `updated_to`, `sort`, `page` e `page_size`. O binding HLAPI (`filter` RSQL, `start`, `limit`, `sort`) foi lido em `api.php/doc.json` 2.2.0.

Prévia de arquivo **não** cria rota nova. O modal reusa `GET /tickets/{id}/attachments/{document_id}`. O browser não chama o GLPI.

## 5. Alvo visual da próxima onda

Uma coluna, kit da Minha DELPI, tokens `--delpi-ui-*`. Sem grade do GLPI e sem verde fixo.

```text
/apps/helpdesk
  HelpdeskPageHeader
  HelpdeskSectionCard  «Meus chamados»
    TicketListFilterBuilder   único editor do recorte (AND)
    HelpdeskDataTable | DataCardsGrid
    HelpdeskListPaginationFooter   Por página + kit (setas, Ir para, resumo; HintAction)

/apps/helpdesk/tickets/{id}
  Conversa  (já publicada)
    belowBody da abertura
      AttachmentPreviewStrip   miniatura se image/pdf
    FilePreviewModal
      prévia
      [ Baixar ]
```

Claro e escuro continuam no mapeamento já feito em `.dashboard-helpdesk`. Ajuda (`helpTooltips.list` e `.detail`) muda no mesmo entregável: filtrar, ver data, abrir a imagem, baixar. Sem path de API. O subtítulo publicado é «Chamados no seu nome». A lista default é Todos. Não reabrir essa correção.

## 6. Hipótese da lista truncada — encerrada em parte

A paginação `start`/`limit` + `has_more` está publicada. A leitura que «o BFF só pede a primeira página e perde chamado» (H2 antigo) está **refutada pelo código**.

Continuam válidas:

```text
H1  o token colaborador enxerga só o que o perfil vê — lista pequena é esperada
H3  Super-Admin no MFE não justifica filtrar 128 128 no browser — invariante do 13
```

## 7. O que não copiar

| Peça da foto do GLPI | Decisão |
|---|---|
| 11 colunas da bancada | tabela do kit, colunas do solicitante — [`13`](./13-listagem-de-chamados.md) |
| Contadores do parque | bancada |
| Entidade, último editor | bancada; data de resolução **IMPLEMENTADA** no 13 (`solved_at`) |
| Foto de perfil | iniciais |
| Imagem embutida como HTML do GLPI | blob autenticado no modal do kit; sem HTML cru |
| Abas, atores editáveis, excluir, salvar | console |
| Envio de arquivo no menu Responder | **IMPLEMENTADO** H12 |

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

Inventário histórico: L/C/G fechados; A-08/H12 **PROVEN**; H10 ciclo + TicketValidation **PROVEN**. Residuais de produto: bancada FORA. Conversa: [`10`](./10-conversa-do-chamado.md). Listagem: [`13`](./13-listagem-de-chamados.md). Mensagem: [`12`](./12-conteudo-da-mensagem.md). Página: [`14`](./14-pagina-e-estados-do-chamado.md). Capacidades: [`15`](./15-capacidades-glpi.md).
