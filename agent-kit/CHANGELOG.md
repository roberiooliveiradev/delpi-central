# Changelog — agent-kit

## 0.3.1 — 2026-11-15

- **OC-1 CI:** o smoke do workflow `agent-kit.yml` chama `build.py` só com `--out` (flags
  `--cursor-model`/`--devin-model` removidas na 0.3.0) e falha se `protocol.headless.md`
  estiver vazio ou sem `## Formato do relatório`.
- **OC-2 formato:** se a saída do motor não tiver `veredito:` válido, `verify.py` relança o
  mesmo motor uma vez com lembrete de formato; o relatório registra `tentativas: 2`. Duas
  falhas → `INCONCLUSIVE` com motivo `relatório fora do formato (2 tentativas)`.
- Prompt headless termina com a lista explícita de vereditos aceitos; PASS/FAIL nunca são
  veredito. `render_headless_protocol` não duplica `## Formato do relatório` quando o
  protocolo headless já embute o formato.

## 0.3.0 — 2026-11-15

**BREAKING**

- Removidos o modo legado `--with-subagents`, a plataforma `claude` no instalador e os arquivos
  gerados em `adapters/` (Cursor/Devin/Claude frontmatter).
- Removidos dos hooks: `mark-start`, `mark-stop`, `activate`, `clear`, marcador em disco
  (`verifier-active.json`), write-lock por linhagem de PIDs e a flag `--always` do guard.
- Isolamento único: `verify.py` → sessão headless com `DELPI_VERIFIER_ACTIVE=1` no processo filho.
  O guard bloqueia escrita só quando essa variável está definida; arquivos de marcador órfãos
  não têm efeito.

**Migração (0.1.x / 0.2.x → 0.3.0)**

1. Rode `python agent-kit/scripts/install.py --dry-run …` e confira as remoções.
2. Reinstale com os mesmos modelos de `~/.delpi-agent-kit/install.json`.
3. A reinstalação remove: `delpi-verifier.md` com o marcador do kit em
   `~/.cursor/agents`, `~/.config/devin/agents`, `%APPDATA%\devin\agents` e `~/.claude/agents`;
   entradas de hook legadas que citam `verifier_hooks.py`; estado
   `~/.delpi-agent-kit/state/verifier-active.json` órfão. Arquivos e hooks alheios são
   preservados; backups `*.bak-*`.
4. `--uninstall` continua removendo tudo o que qualquer versão do kit instalou.

## 0.2.1 — 2026-11-15

- **Nota pós-AK-3:** um commit concorrente (`9bf93a67`) reintroduziu marcador+PIDs no
  `verify.py`; `dfbf4b11` restaurou OC-1 (sem marcador no launcher headless).
- **OC R1 (legado `--with-subagents`):** `mark-start` grava o PID do host (`getppid`) para
  write-lock por linhagem — o subagent verificador volta a ser bloqueado; sessões irmãs
  fora da linhagem continuam livres. `verify.py` headless segue sem marcador global.
- **OC-1 concorrência:** `verify.py` deixa de gravar `verifier-active.json`. O isolamento da
  sessão headless vem só de `DELPI_VERIFIER_ACTIVE=1` no ambiente do processo filho. O marcador
  global permanece apenas para o legado `--with-subagents` (`mark-start` / `mark-stop` /
  `activate`).
- **OC-2 portabilidade:** descoberta do perfil Windows via `cmd.exe /c echo %USERPROFILE%` +
  `wslpath -u` (fallback stdlib drive→`/mnt`); opção `--windows-home`; sem nome de usuário
  literal no código.
- **OC-3 caminhos:** `normalize_agent_path` (stdlib) em `verifier_hooks.py`, usada por
  `verify.py` (`--request-file`, `--repo`, `repositorio:`) e pelos hooks (`payload_repo`):
  UNC `\\wsl.localhost\` / `\\wsl$\` → Linux; `C:\` → `/mnt/c/...`.
- Prompt: `git diff --stat` limitado a 200 linhas; `OSError` ao lançar o motor →
  `INCONCLUSIVE` com motivo (sem exceção não tratada).

## 0.2.0 — 2026-11-15

- Verificação deixa de rodar como subagent e passa a ser lançada pelo `verify.py` em sessão
  headless: Devin CLI com `swe-2-high` (grátis no plano atual) por padrão; fallback Cursor CLI
  com modelo do pacote próprio (`composer-2.5`). Sem motor → `INCONCLUSIVE` "verificador
  indisponível"; o executor nunca se autoverifica.
- `scripts/verify.py`: valida o pedido antes de gastar tokens; ativa marcador +
  `DELPI_VERIFIER_ACTIVE=1`; timeout configurável; salva relatório em
  `<git-dir>/delpi-verifier/reports/`; preenche o ledger se o motor não registrou.
- Instalador: subagents fora do padrão (`--with-subagents` restaura 0.1.x); remove agentes
  antigos do kit; grava engines/modelos/timeout em `install.json`; `verify.cmd` no Windows
  repassa para o WSL.
- Hooks: guard reconhece `DELPI_VERIFIER_ACTIVE`; stop gate aponta para `verify.py`; comando
  `activate` para o launcher.
- Protocolo headless (sem frontmatter); contrato/AGENTS.md parte A atualizados.

## 0.1.1 — 2026-11-15

- Pedido de verificação aceita `repositorio:` (subprojeto ou repositório de avaliação fora da raiz do
  workspace); `run_case.py prepare` já imprime o campo.
- Evals podem rodar dentro do próprio workspace, em `agent-kit/.eval-runs/` (ignorada pelo git).

## 0.1.0 — 2026-11-15

Primeira versão do `delpi-verifier`.

- Protocolo de verificação independente em 10 passos (`verifier/protocol.md`): expectativas escritas antes
  de ler o diff, checagens executáveis, confronto AC × evidência e alegações × realidade, caça adversarial
  (incluindo atalhos para passar no teste), busca residual, confirmação com nota de confiança (só ≥ 80 vira
  ordem de correção), `DECISION_REQUIRED`/`EXECUTION_DRIFT` e registro do veredito.
- Formato fixo de relatório e de ordens de correção (`verifier/report-format.md`).
- Ciclo do executor com até 3 rodadas e modelo de contrato por projeto (`verifier/project-contract.md`).
- Adaptadores para Cursor, Devin e Claude Code, gerados a partir do mesmo protocolo (`scripts/build.py`).
- Hooks (`hooks/verifier_hooks.py`): guard que bloqueia comandos de escrita enquanto o verificador roda,
  stop gate que exige veredito registrado quando o repositório mudou na sessão, ledger de vereditos em
  `.git/delpi-verifier/`.
- Instalador em nível de usuário com `--dry-run`, backup, atualização idempotente e `--uninstall`
  (`scripts/install.py`).
- 7 casos de avaliação com defeitos plantados e pontuação automática (`evals/`).
