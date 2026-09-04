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
  - `/admin` — tipos de solicitação (somente leitura; exige `my-requests.manage`)

## Minhas

Lista o que **você** criou. Use a **busca** (número da solicitação, código/nome do destinatário ou descrição — mínimo 2 caracteres), filtre por tipo, status e filial; use a paginação. Clique no número para abrir o detalhe.

## Fila de trabalho

Itens elegíveis ao seu perfil de processar/gerenciar. Mesma busca, filtros e paginação de Minhas. O escopo vem da API (não do frontend).

## Nova solicitação

Escolha o **tipo** e a **filial**. Para **emissão de NF**, abra o wizard specialized (6 passos). Para **matéria-prima**, abra o formulário schema-driven (descrição, unidade, observações). Outros tipos usam o fluxo genérico.

## Admin (tipos)

Com `my-requests.manage`, a aba **Admin** lista os tipos cadastrados no Request Engine (código, nome, ativo, escopo de filial). É **somente leitura** — não edita workflow nem formulário nesta tela.

## Detalhe

Mostra status, meta e **ações permitidas** (`allowed_actions`). Os botões refletem o WorkflowEngine — o MFE **não** decide sozinho se uma transição é válida. **Devolver** e **cancelar** pedem o motivo em um diálogo do app (não no prompt do navegador).

Painéis:

| Painel | Uso |
|--------|-----|
| Linha do tempo | Eventos (criação, transição, upload, comentário) |
| Comentários | Thread da solicitação |
| Anexos | Arquivos do solicitante — arraste/selecione no detalhe para enviar; baixe pelos links |
| Artefatos | Evidências do processamento — processadores enviam (genérico ou PDF da NF); solicitantes só baixam |

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

- App legado `invoice-issuance`: MFE removido do Compose (E13); bookmarks redirecionam no gateway. Canônico = Minhas Solicitações — **não** há dual-run de menu.
- Migração de histórico: ver `MIGRATION-RUNBOOK.md` + evidência em `PARITY-P0.md` (E15). Ambientes com dados legados devem reaplicar dry-run/`--apply`.
- Homologação UI live (criar/fila/lookups TOTVS no browser): checklist Ops em `PARITY-P0.md` itens 1–2.
- Permissões `invoice-issuance.*` podem ainda existir no Core até runbook IAM (`IAM-LEGACY-PERMISSIONS.md`); operadores novos usam só `my-requests.*`.
- Lookups TOTVS ainda passam pela api-delpi (path canônico a partir de E17); schema/volume legado retidos ≥ 90 dias.
