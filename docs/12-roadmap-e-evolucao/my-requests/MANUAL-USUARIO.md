# Manual do usuário — Minhas Solicitações

Espelho da Ajuda in-app (`plugins/my-requests/src/content/helpTooltips.ts`).

## O que é

**Minhas Solicitações** reúne pedidos do dia a dia (emissão de nota fiscal, criação de matéria-prima e outros tipos) em um único lugar. Você acompanha o andamento, conversa por comentários e envia arquivos — tudo com a mesma aparência dos demais módulos do portal.

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

O que está elegível para o seu atendimento. Mesmos filtros e paginação. Abra a solicitação para iniciar, devolver, concluir ou registrar a emissão, conforme os botões disponíveis.

## Nova solicitação

Escolha o **tipo** em um **card** (ícone, nome e breve descrição). O formulário abre na hora:

- emissão de NF — passo a passo (wizard);
- matéria-prima — campos do formulário do tipo;
- outros — fluxo genérico.

A **filial**, quando o tipo exige, aparece **dentro** do formulário (01 = Santa Catarina, 02 = Espírito Santo). Tipos sem multi-unidade não pedem filial. Link direto com `?type=…` abre o formulário do tipo.

## Detalhe

A leitura da página segue três fases:

1. **O que foi solicitado** — dados gerais, dados do tipo (ex.: emissão) e documentos do pedido;
2. **Atendimento** — progresso, ações, comentários e documentos gerados no atendimento;
3. **Histórico** — linha do tempo (último bloco).

O **status** aparece no topo. Se a solicitação foi **devolvida para ajuste**, o **motivo da devolução** aparece em um card em destaque com o botão **Corrigir dados** (quando liberado). Isso abre o formulário de edição; depois de salvar, use **Reenviar solicitação** nas ações disponíveis.

O **progresso do atendimento** (etapas + percentual) vem do sistema. Em telas largas o rastreador fica horizontal; em telas estreitas usa «Ver etapas». Os **botões de ação** só mostram o que a API liberou. **Devolver** e **cancelar** pedem motivo em uma janela.

Documentos do pedido usam miniaturas. Você pode anexar arquivos **ao criar** a solicitação. No detalhe, adicionar ou remover anexos do pedido só é possível quando ela está **devolvida para ajuste**. Documentos gerados no atendimento continuam a cargo de quem processa.

| Painel | Fase | Uso |
|--------|------|-----|
| Motivo da devolução / cancelamento | topo | Destaque do motivo + atalho para corrigir |
| Dados da solicitação | Solicitação | Tipo, status, filial, solicitante e data |
| Dados da emissão | Solicitação | Resumo da NF (quando for esse tipo) |
| Documentos da solicitação | Solicitação | Anexos do pedido (miniaturas) |
| Progresso do atendimento | Atendimento | Etapas e percentual |
| Ações disponíveis | Atendimento | Botões liberados no momento |
| Comentários | Atendimento | Comunicação operacional |
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
- Na conferência você também pode **anexar documentos** que complementam o pedido; eles são enviados junto com a criação.
- O rascunho fica só na sessão atual (recarregar a página perde o preenchimento).
- O formulário usa a largura da página (responsivo em desktop e celular).

Buscas de cliente/fornecedor/produto/transportadora usam o serviço do módulo (não é preciso sair do app). A transportadora é opcional.

## Formulário de matéria-prima

Preencha descrição, unidade e observações (conforme o tipo) e envie. A filial aparece quando o tipo exige.

## Sem acesso

Se o portal abrir a mensagem de que você não tem permissão, peça acesso ao administrador do portal.

## Notificações

Atualizações podem aparecer no sino do portal na categoria **Minhas Solicitações**. Ajuste em Preferências de notificação.

---

## Notas de suporte (técnicas)

- API do browser: somente `/apps/requests-api`.
- Permissões típicas: `my-requests.access`, `view.filial-*`, `view-all` / `manage`, `*.create` / `*.process` por tipo.
- Labels amigáveis: `src/content/presentationLabels.ts` (códigos enviados à API permanecem canônicos).
- App legado `invoice-issuance`: removido do Compose; canônico = este módulo.
- Lookups TOTVS e IAM legado: ver `LOOKUPS-CANONICAL.md` e `IAM-LEGACY-PERMISSIONS.md`.
- Homologação UI live (Ops): `PARITY-P0.md` itens 1–2.
