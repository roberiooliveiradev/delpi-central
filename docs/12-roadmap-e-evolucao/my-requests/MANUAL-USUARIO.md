# Manual do usuário — Minhas Solicitações

Espelho da Ajuda in-app (`plugins/my-requests/src/content/helpTooltips.ts`).

## O que é

**Minhas Solicitações** centraliza pedidos operacionais (emissão de NF, criação de MP, etc.) em um único app. O motor de workflow e as permissões ficam na **requests-api**; a tela só mostra o que a API libera.

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

Escolha o **tipo** e a **filial**. Wizards especializados (ex.: emissão de NF completa) entram em entregas futuras; o shell cria o registro genérico.

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
- Placeholders `raw-material-creation.*` para o vertical de MP

## Notificações

Atualizações podem aparecer no sino do portal na categoria **Minhas Solicitações** (`my_requests`). Ajuste em Preferências de notificação.

## Limitações atuais (E5)

- Wizard NF e lookups TOTVS: etapa E6
- Vertical MP schema-driven: etapa E7
- Cutover do app legado de emissão: etapa E8
