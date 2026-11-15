# agent-kit · delpi-verifier

Verificador independente para o trabalho dos agentes executores (Cursor IDE e Devin Desktop), em
**qualquer projeto**. O executor implementa; o `delpi-verifier`, em sessão headless separada, prova ou
refuta a entrega e devolve ordens de correção. O executor corrige e o ciclo se repete, por no máximo 3
rodadas. O executor **nunca** se autoverifica.

Esta pasta é autocontida: tem versão (`VERSION`), changelog, testes e instalador próprios. Ela mora no
`delpi-central`, mas não depende de nada do monorepo.

Versão atual: **0.3.0**.

---

## Arquitetura 0.3.0

```
executor (Cursor IDE ou Devin Desktop)
  → grava PEDIDO em <git-dir>/delpi-verifier/requests/
  → python ~/.delpi-agent-kit/verify.py --request-file <arquivo>
       → valida pedido (sem gastar token)
       → motor headless com DELPI_VERIFIER_ACTIVE=1 no ambiente do filho:
            1º Devin CLI  --model swe-2-high  (--permission-mode smart)
            2º fallback Cursor CLI --model composer-2.5
       → relatório em <git-dir>/delpi-verifier/reports/
       → ledger de vereditos
```

Único caminho de verificação: `verify.py` → sessão headless. Não há instalação de agentes Task
nem marcador em disco.

### Custo

| Motor | Modelo | Por quê |
|---|---|---|
| Devin CLI (padrão) | `swe-2-high` | Marcado **Free** no plano Devin Pro atual |
| Cursor CLI (fallback) | `composer-2.5` | Pacote próprio do Cursor — **não** Claude/GPT/Gemini (pacote de API) |
| Nenhum disponível | — | `INCONCLUSIVE` "verificador indisponível" (exit 3) |

Se o executor também for SWE, o relatório deve marcar `independencia: DEGRADADA` (contexto limpo ainda
ajuda).

### Isolamento

| Sessão | Como o guard bloqueia escrita |
|---|---|
| Headless `verify.py` (Devin/Cursor CLI) | só `DELPI_VERIFIER_ACTIVE=1` no ambiente do processo filho |
| Outros agentes / conversas na mesma máquina | **não** bloqueados |

Caminhos Windows/UNC (`\\wsl.localhost\…`, `C:\…`) são normalizados para Linux em `verify.py` e nos hooks
(`normalize_agent_path`), sem chamar processo externo.

### Limites

- `permission-mode auto` do Devin **não** roda testes; o kit usa `smart` + guard.
- Guard + `DELPI_VERIFIER_ACTIVE` bloqueiam escrita na sessão headless; não é sandbox perfeito.
- Timeout padrão: 30 min (configurável em `install.json`).
- Sem Devin CLI autenticado e sem Cursor CLI: verificação não roda — não há autoverificação.

---

## Instalação

```bash
python agent-kit/scripts/install.py --dry-run \
  --devin-model swe-2-high --cursor-model composer-2.5
python agent-kit/scripts/install.py \
  --devin-model swe-2-high --cursor-model composer-2.5
# se o interop WSL não achar o perfil Windows:
#   --windows-home /mnt/c/Users/<user>
```

- Reinstalar a 0.3.0 remove restos de 0.1.x/0.2.x do kit (arquivos de agente com o marcador do kit,
  entradas de hook legadas que citam `verifier_hooks.py`, estado órfão) e preserva arquivos/hooks alheios.
  Backups `*.bak-*`; visível no `--dry-run`.
- No Windows, `verify.cmd` em `%USERPROFILE%\.delpi-agent-kit\` repassa para o WSL
  (perfil descoberto via `cmd.exe` + `wslpath`, ou `--windows-home`).
- Hooks: session-start, track-edit, guard e stop-gate (Cursor IDE + Devin Desktop / CLI).

---

## Como usar em um projeto

1. Copie a seção de `verifier/project-contract.md` para o `AGENTS.md` e preencha a parte B.
2. O executor grava o pedido em `<git-dir>/delpi-verifier/requests/` e roda:

```bash
python ~/.delpi-agent-kit/verify.py --request-file <arquivo>
# opcional: --engine auto|devin|cursor
```

3. Aplica OCs (ou contesta com evidência), repete até `ACCEPT` ou 3 rodadas.

---

## Avaliação

Veja `evals/README.md`. Rode via `verify.py` (coluna **motor** na tabela).

## Desenvolvimento do kit

```bash
cd agent-kit && python -m unittest discover -s tests -v
```
