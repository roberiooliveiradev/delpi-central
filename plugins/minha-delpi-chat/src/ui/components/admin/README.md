# Admin Minha DELPI Chat

A área admin é organizada por ambientes isolados. Cada aba ou bloco complexo deve ficar em sua própria pasta, com componente e CSS próprios.

## Estrutura

- `shell/`: topbar, abas e alertas do admin.
- `metrics/`: resumo operacional.
- `knowledge/`: base global de conhecimento.
- `guidelines/`: diretrizes globais de comportamento.
- `tools/`: provider LLM, actions e health técnico.
- `audit/`: auditoria, filtros, resumo, tabela e paginação.

## Regras

1. Não colocar CSS de aba dentro de `ChatAdminPage.css`.
2. Não usar seletores genéricos compartilhados entre abas quando o componente for isolado.
3. Toda aba deve expor componentes menores para formulário, lista, tabela, filtros e ações.
4. Contratos administrativos ficam centralizados em `data/api/adminApi.ts` e `adminTypes.ts`.
5. Não chamar endpoints futuros até o backend implementar a rota.
6. A base de conhecimento do admin representa contexto global do chat; anexos de conversa não pertencem a essa tela.
