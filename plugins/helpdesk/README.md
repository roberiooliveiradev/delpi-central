# Meus Chamados de TI

Microfrontend em `/apps/helpdesk`. Os chamados continuam no GLPI; esta tela só consome a helpdesk-api.

## Ajuda

- A lista mostra os chamados visíveis para a pessoa logada.
- A primeira abertura pede autorização no helpdesk, com a sessão já existente.
- Abrir chamado pede título, descrição, categoria e urgência. O solicitante é o usuário do token.
- O detalhe em `/apps/helpdesk/tickets/{id}` permanece após atualizar a página.
- Anexo, satisfação e fila técnica ficam fora desta entrega.

O path antigo `/helpdesk` redireciona para `/apps/helpdesk`.
