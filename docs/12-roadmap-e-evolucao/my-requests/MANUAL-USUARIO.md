# Manual do usuário — Minhas Solicitações

Espelho da Ajuda in-app (`plugins/my-requests/src/content/helpTooltips.ts`).

## O que é

**Minhas Solicitações** centraliza pedidos operacionais (emissão de NF, criação de MP, etc.) em um único app. O motor de workflow e as permissões ficam na **requests-api**; a tela só mostra o que a API libera. A interface usa o kit visual compartilhado do portal (`plugin-ui`) — botões, tabelas e cards seguem o mesmo padrão dos demais módulos.

Layout e componentes por tela (wireframes): [WIREFRAMES.md](./WIREFRAMES.md).

## Onde encontrar

- Tile no portal: **Minhas Solicitações** → `/apps/my-requests`
- Rotas internas:
  - `/mine` — suas solicitações
  - `/work-queue` — fila de trabalho
  - `/new` — criar
  - `/requests/:id` — detalhe

## Minhas

Lista o que **você** criou. Clique no número para abrir o detalhe.

## Fila de trabalho

Itens elegíveis ao seu perfil de processar/gerenciar. O escopo vem da API (não do frontend).

## Nova solicitação

Escolha o **tipo** e a **filial**. Para **emissão de NF**, abra o wizard specialized (6 passos). Para **matéria-prima**, abra o formulário schema-driven (descrição, unidade, observações). Outros tipos usam o fluxo genérico.

## Detalhe

Mostra status, meta e **ações permitidas** (`allowed_actions`). Os botões refletem o WorkflowEngine — o MFE **não** decide sozinho se uma transição é válida.

Painéis:

| Painel | Uso |
|--------|-----|
| Linha do tempo | Eventos (criação, transição, upload, comentário) |
| Comentários | Thread da solicitação |
| Anexos | Arquivos do solicitante |
| Artefatos | Evidências do processamento |

## Permissões típicas

- `my-requests.access` — abrir o app
- `my-requests.view.filial-01` / `.filial-02` — escopo de filial
- `my-requests.view-all` / `.manage` — visão ampliada / admin
- `my-requests.invoice-issuance.create` / `.process` — tipo NF
- `my-requests.raw-material-creation.create` / `.process` — tipo MP

## Notificações

Atualizações podem aparecer no sino do portal na categoria **Minhas Solicitações** (`my_requests`). Ajuste em Preferências de notificação.

## Wizard de emissão de NF

Quando o tipo é **invoice-issuance**, a tela Nova abre o wizard specialized (6 passos: destinatário → tipo → itens → frete → adicionais → conferência). Lookups e criação usam apenas `/apps/requests-api` (nunca api-delpi no browser).

No detalhe, solicitações NF mostram o painel **Dados da emissão** além das ações `allowed_actions`.

## Formulário de matéria-prima

Quando o tipo é **raw-material-creation**, a tela Nova abre o formulário schema-driven (campos vindos do `form_schema` do tipo: descrição, unidade UN/KG/M, observações). A criação usa apenas `/apps/requests-api`.

## Limitações atuais

- Cutover do app legado de emissão: etapa E8 (plugin `invoice-issuance` permanece em dual-run)
