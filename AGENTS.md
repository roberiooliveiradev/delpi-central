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

## Git Branch and Worktree Governance — User Approval Required

Regra 1 — Branch canônica. `main` é a branch canônica de integração
do projeto. Agentes não devem criar estratégias paralelas de
branching por iniciativa própria.

Regra 2 — Proibição de troca automática. Nenhum agente pode executar
comandos que alterem a branch ativa sem autorização explícita do
usuário, incluindo `git switch`, `git checkout` para outra branch,
checkout detached e equivalentes (CLI ou interface gráfica).

Regra 3 — Proibição de criação automática. Nenhum agente pode criar
feature branches, branches temporárias/de teste/de recuperação,
worktrees adicionais ou detached, ou branches remotas, sem
autorização explícita do usuário.

Regra 4 — Worktree existente. Worktrees preexistentes devem ser
preservados. Não excluir, limpar, mover, reutilizar ou alterar outro
worktree automaticamente.

Regra 5 — Git status obrigatório. Antes de modificar código:

```bash
git rev-parse HEAD
git branch --show-current
git status --short
git worktree list
```

Identificar também o HEAD remoto e a relação de ancestralidade
quando a tarefa envolver publicação.

Regra 6 — Alterações concorrentes. Alterações não relacionadas à
task devem ser preservadas: não sobrescrever, não descartar, não
incluir automaticamente no commit, não usar `stash` sem autorização
e não usar reset/clean para abrir caminho.

Regra 7 — Branch inesperada. Ao encontrar branch diferente da
esperada: registrar branch e HEAD, inspecionar o estado, não trocar
automaticamente e não criar outra branch como solução. Solicitar
decisão do usuário quando a execução depender da mudança.

Regra 8 — Proibição de transferência implícita. Autorização para
implementar código não implica autorização para criar branch, trocar
branch, criar worktree ou migrar commits entre branches — essas
ações exigem autorização específica.

Regra 9 — Push e integração. Não fazer push de branch inesperada,
não misturar commits de tarefas diferentes e não integrar feature
branches na `main` sem autorização explícita. A política canônica de
commit direto em `main` (seção Entrega) permanece: ela autoriza
commit/push em `main`, não operações de branch.

Regra 10 — Conflito de instruções. Se outra instrução recomendar
criar worktree ou branch automaticamente para preservar
concorrência, a criação passa a exigir autorização do usuário.
Não resolver o conflito silenciosamente — reportar a divergência.
