# Manual do usuário — Minhas Solicitações

Espelho da Ajuda in-app (`plugins/my-requests/src/content/helpTooltips.ts`).

## O que é

**Minhas Solicitações** reúne pedidos do dia a dia (emissão de nota fiscal, criação de matéria-prima e outros tipos) em um único lugar. Você acompanha o andamento, conversa na solicitação e envia arquivos — tudo com a mesma aparência dos demais módulos do portal.

Layout por tela: [WIREFRAMES.md](./WIREFRAMES.md).

## Menu superior (TopBar)

No topo do módulo você encontra:

| Item | Para quê |
|------|----------|
| **Minhas solicitações** | O que você abriu |
| **Fila de trabalho** | O que está na sua fila para atender |
| **Nova solicitação** | Abrir um pedido novo (se o seu perfil puder criar) |
| **Tipos / Admin** | Consultar tipos cadastrados (somente quem administra) |

Em telas estreitas o menu pode recolher em ícone de menu (hamburger), como no Portal Comercial.

## Onde encontrar

- Tile no portal: **Minhas Solicitações** → `/apps/my-requests`
- Atalhos internos: Minhas, Fila, Nova, Detalhe (pelo número), Administração

## Minhas solicitações

Lista o que **você** criou. Use a busca (número, destinatário ou descrição), filtre por tipo, status e filial e avance pelas páginas. Clique no **número** para abrir o detalhe. Tipos e status aparecem com nomes amigáveis.

## Fila de trabalho

O que está elegível para o seu atendimento (tipos que você processa). Mesmos filtros de busca/tipo/status/filial, mais o filtro **Minhas**:

- **Todas** — fila compartilhada (padrão: sem status finais);
- **Concluídas por mim** — solicitações que **você** fechou (`completed_by`);
- **Atribuídas a mim** — as que você iniciou o atendimento (assignee).

A tabela mostra também a coluna **Concluída por**. Abra a solicitação para iniciar, devolver, emitir nota, cancelar etc., conforme os botões liberados pela API.

Em emissão de NF, quem **conclui** costuma ser o solicitante (confirmação após a emissão). Quem atende usa **Atribuídas a mim** para achar o que iniciou, inclusive já fechadas.

## Nova solicitação

Escolha o **tipo** em um **card** (ícone, nome e breve descrição). O formulário abre na hora:

- emissão de NF — passo a passo (wizard);
- matéria-prima — campos do formulário do tipo;
- outros — fluxo genérico.

A **filial**, quando o tipo exige, aparece **dentro** do formulário (01 = Santa Catarina, 02 = Espírito Santo). Tipos sem multi-unidade não pedem filial. Link direto com `?type=…` abre o formulário do tipo.

## Detalhe

A leitura da página segue três fases:

1. **O que foi solicitado** — dados gerais, dados do tipo (ex.: emissão) e documentos do pedido;
2. **Atendimento** — progresso, ações (com ícone e ajuda), conversa sobre a solicitação e documentos gerados no atendimento;
3. **Histórico** — linha do tempo (último bloco).

O **status** aparece no topo. Se a solicitação foi **devolvida para ajuste**, o **motivo da devolução** aparece em um card em destaque com o botão **Corrigir dados** (quando liberado). Isso abre o formulário de edição; depois de salvar, use **Reenviar solicitação** nas ações disponíveis.

O **progresso do atendimento** (etapas + percentual) vem do sistema. Em telas largas o rastreador fica horizontal; em telas estreitas usa «Ver etapas». Os **botões de ação** ocupam a largura da seção (ícone + texto + ajuda ao passar o mouse) e só mostram o que a API liberou. Em atendimento de NF, **Emitir nota fiscal** aparece em «Em atendimento»; sem o PDF em Documentos gerados, o clique avisa o que falta. **Devolver** e **cancelar** pedem motivo em uma janela. A **conversa sobre a solicitação** fica abaixo das ações, em formato de mensagens (foto do Portal ou iniciais), e atualiza em tempo real.

Documentos do pedido usam miniaturas. Clique para **abrir em modal** (pré-visualizar e **baixar** com a sessão autenticada — não use a URL de download direto no navegador). Você pode anexar arquivos **ao criar** a solicitação (ficam pendentes até enviar o pedido). No detalhe, adicionar anexos do pedido só é possível quando ela está **devolvida para ajuste**: selecione os arquivos, revise/descarte e use **Salvar documentos**. Documentos gerados no atendimento seguem o mesmo fluxo de seleção → Salvar, a cargo de quem processa.

Ao **devolver** uma solicitação, além do motivo em texto, quem atende pode **marcar as seções** que precisam de correção (ex.: destinatário, itens). O solicitante vê essa lista no card de devolução e no formulário de correção.

| Painel | Fase | Uso |
|--------|------|-----|
| Motivo da devolução / cancelamento | topo | Destaque do motivo + atalho para corrigir |
| Dados da solicitação | Solicitação | Tipo, status, filial, solicitante e data |
| Dados da emissão | Solicitação | Resumo da NF (quando for esse tipo) |
| Documentos da solicitação | Solicitação | Anexos do pedido (miniaturas) |
| Progresso do atendimento | Atendimento | Etapas e percentual |
| Ações disponíveis | Atendimento | Botões com ícone e ajuda |
| Conversa sobre a solicitação | Atendimento | Mensagens entre solicitante e atendimento |
| Documentos gerados no atendimento | Atendimento | Resultados (ex.: NF em PDF) |
| Linha do tempo | Histórico | Registro do que aconteceu |

## Administração (tipos)

Quem tem permissão de administrar vê o catálogo de tipos (código, nome, ativo, se pedem filial e como o formulário é apresentado). É **somente consulta** nesta tela.

## Wizard de emissão de NF

Seis etapas: destinatário → tipo de NF → itens → frete → adicionais → conferência.

- Digite ao menos 2 caracteres nas buscas de destinatário, produto e transportadora: a lista aparece sozinha (não há botão Buscar). Chips com avatar confirmam a seleção. Passe o mouse no título do campo (Destinatário, Produtos, Transportadora, Filial, etc.) para ver a ajuda.
- Destinatário e transportadora: no máximo um chip. Produtos: selecione vários e use **Adicionar selecionados**.
- A barra de progresso e o rastreador de etapas avançam **na ordem**: o percentual só sobe depois que as etapas anteriores estão prontas (valores padrão de tipo/frete/peso não antecipam o progresso). Em telas menores, o rastreador fica compacto com «Ver etapas».
- Etapas futuras ficam bloqueadas até a anterior estar pronta; etapas concluídas podem ser reabertas.
- Ao selecionar o destinatário, o fluxo avança automaticamente para o tipo de NF.
- Na conferência, revise cada bloco e use **Alterar** para corrigir e voltar. Não há checklist técnico na tela — só o resumo amigável antes de **Enviar**.
- Na conferência você também pode **selecionar documentos** que complementam o pedido; eles são enviados junto com a criação (remova os indesejados antes de confirmar).
- O rascunho fica só na sessão atual (recarregar a página perde o preenchimento).
- O formulário usa a largura da página (responsivo em desktop e celular).

Buscas de cliente/fornecedor/produto/transportadora usam o serviço do módulo (não é preciso sair do app). A transportadora é opcional.

## Formulário de matéria-prima

Preencha descrição, unidade e observações (conforme o tipo) e envie. A filial aparece quando o tipo exige.

## Sem acesso

Se o portal abrir a mensagem de que você não tem permissão, peça acesso ao administrador do portal.

## Notificações

Atualizações aparecem no **sino do portal** (categoria **Minhas Solicitações**) e em **avisos na tela** quando o módulo está aberto:

- nova solicitação → quem processa o tipo (exceto o criador);
- mudanças de etapa relevantes → solicitante e/ou quem está atendendo;
- conversa → a outra parte (solicitante ↔ atendente).

Ajuste preferências no portal. O autor da própria ação não recebe sino dela.

---

## Notas de suporte (técnicas)

- API do browser: somente `/apps/requests-api`.
- Permissões típicas: `my-requests.access`, `view.filial-*`, `view-all` / `manage`, `*.create` / `*.process` por tipo.
- Labels amigáveis: `src/content/presentationLabels.ts` (códigos enviados à API permanecem canônicos).
- App legado `invoice-issuance`: removido do Compose; canônico = este módulo.
- Lookups TOTVS e IAM legado: ver `LOOKUPS-CANONICAL.md` e `IAM-LEGACY-PERMISSIONS.md`.
- Homologação UI live (Ops): `PARITY-P0.md` itens 1–2.
