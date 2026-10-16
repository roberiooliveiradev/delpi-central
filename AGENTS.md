# Instruções do projeto para agentes

## Entrega

- Commitar e dar push **sempre** diretamente na branch `main` —
  sem branch intermediária e sem PR por padrão (diretriz do
  Product Master).
- Fast-forward apenas; nunca force push. Se `origin/main` avançou,
  fazer fetch + rebase antes do push e revalidar o escopo.
- Commitar somente os arquivos do escopo da task; preservar
  alterações concorrentes no working tree (não dar stage em work
  de outras tasks).
- Regras canônicas de engenharia: `.cursor/rules/` (ver
  `development-standards-index.mdc` e `delia-execution-protocol.mdc`
  para tasks DÉLIA).
