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
- Após commit/push, executar **sempre** o deploy canônico em
  `srv-api` (`operador@192.168.1.237`, `~/projetos/delpi-central`):
  `git pull --ff-only` + `./infra/scripts/up-prod-sequential.sh
  --build <serviços afetados>` — sem aguardar nova autorização por
  fatia. Feature gates produtivos (ex.: escrita Protheus) seguem
  desligados salvo autorização explícita do PO (diretriz do usuário).
- Regras canônicas de engenharia: `.cursor/rules/` (ver
  `development-standards-index.mdc` e `delia-execution-protocol.mdc`
  para tasks DÉLIA).
