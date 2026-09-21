# Meus Chamados de TI

Microfrontend em `/apps/helpdesk`. Os chamados continuam no GLPI; esta tela só consome a helpdesk-api.

A composição de cada tela, os estados e o claro/escuro estão em [`WIREFRAMES.md`](../../docs/12-roadmap-e-evolucao/helpdesk/WIREFRAMES.md). Não criar controle visual fora das factories de `src/ui/helpdeskUi.tsx`.

## O que a tela faz

| Rota | Capacidade |
|---|---|
| `/apps/helpdesk` | Lista com filtros, builder AND, multi-sort, preferência de colunas, paginação |
| `/apps/helpdesk/tickets/new` | Abrir chamado (título/descrição + categoria/urgência/observadores) |
| `/apps/helpdesk/tickets/{id}` | Conversa HTML, prévia de anexo, responder (oculto se fechado) |

- A primeira abertura pede autorização no helpdesk, com a sessão já existente.
- Chamado e título na lista têm `href` estável; Ctrl/meio-clique abrem em outra aba.
- Rascunho de abertura e de resposta sobrevive ao F5 neste navegador até o envio.
- Baixar anexo já ligado ao chamado está publicado. Enviar arquivo novo, `@` no compositor, aprovar/reabrir/satisfação e fila técnica ficam fora até decisão + HLAPI.

O path antigo `/helpdesk` redireciona para `/apps/helpdesk`.

## Desenvolvimento

```bash
cd plugins/helpdesk
npm test
npm run typecheck
npm run build
```

Contrato e roadmap: [`docs/12-roadmap-e-evolucao/helpdesk/`](../../docs/12-roadmap-e-evolucao/helpdesk/).
