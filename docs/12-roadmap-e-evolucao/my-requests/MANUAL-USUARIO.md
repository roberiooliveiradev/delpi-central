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

Mostra tipo, status, filial, solicitante e data. Os **botões de ação** mudam conforme o andamento — só aparecem as opções liberadas para você naquele momento. **Devolver** e **cancelar** pedem um motivo em uma janela do app.

Painéis:

| Painel | Uso |
|--------|-----|
| Dados da emissão | Resumo da NF (quando for esse tipo) |
| Linha do tempo | Histórico do que aconteceu |
| Comentários | Conversa sobre o pedido |
| Anexos | Arquivos que você envia com o pedido |
| Arquivos do atendimento | Evidências do atendimento (ex.: PDF da nota) — quem atende pode enviar; solicitantes costumam só baixar |

## Administração (tipos)

Quem tem permissão de administrar vê o catálogo de tipos (código, nome, ativo, se pedem filial e como o formulário é apresentado). É **somente consulta** nesta tela.

## Wizard de emissão de NF

Seis etapas: destinatário → tipo de NF → itens → frete → adicionais → conferência.

- A barra de progresso e o rastreador de etapas mostram o que já foi preenchido. Etapas futuras ficam bloqueadas até a anterior estar pronta; etapas concluídas podem ser reabertas.
- Ao selecionar o destinatário, o fluxo avança automaticamente para o tipo de NF.
- Na conferência, revise cada bloco e use **Alterar** para corrigir e voltar. Não há checklist técnico na tela — só o resumo amigável antes de **Enviar**.
- O rascunho fica só na sessão atual (recarregar a página perde o preenchimento).

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
