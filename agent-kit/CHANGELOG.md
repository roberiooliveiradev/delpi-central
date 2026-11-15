# Changelog — agent-kit

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
