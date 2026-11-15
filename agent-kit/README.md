# agent-kit · delpi-verifier

Verificador independente para o trabalho dos agentes executores (Cursor IDE e Devin Desktop), em
**qualquer projeto**. O executor implementa; o `delpi-verifier`, em sessão headless separada, prova ou
refuta a entrega e devolve ordens de correção. O executor corrige e o ciclo se repete, por no máximo 3
rodadas. O executor **nunca** se autoverifica.

Esta pasta é autocontida: tem versão (`VERSION`), changelog, testes e instalador próprios. Ela mora no
`delpi-central`, mas não depende de nada do monorepo.

Versão atual: **0.2.1**.

---

## Arquitetura 0.2.1

```
executor (Cursor IDE ou Devin Desktop)
  → grava PEDIDO em <git-dir>/delpi-verifier/requests/
  → python ~/.delpi-agent-kit/verify.py --request-file <arquivo>
       → valida pedido (sem gastar token)
       → ativa marcador (PIDs) + DELPI_VERIFIER_ACTIVE=1 no motor
       → motor headless:
            1º Devin CLI  --model swe-2-high  (--permission-mode smart)
            2º fallback Cursor CLI --model composer-2.5
       → relatório em <git-dir>/delpi-verifier/reports/
       → ledger de vereditos
```

### Custo

| Motor | Modelo | Por quê |
|---|---|---|
| Devin CLI (padrão) | `swe-2-high` | Marcado **Free** no plano Devin Pro atual |
| Cursor CLI (fallback) | `composer-2.5` | Pacote próprio do Cursor — **não** Claude/GPT/Gemini (pacote de API) |
| Nenhum disponível | — | `INCONCLUSIVE` "verificador indisponível" (exit 3) |

Se o executor também for SWE, o relatório deve marcar `independencia: DEGRADADA` (contexto limpo ainda
ajuda).

### Guard por sessão (AK-3)

O guard **não** bloqueia a máquina inteira. Decisão por processo:

| Caminho | Condição | Efeito |
|---|---|---|
| **(a)** variável | `DELPI_VERIFIER_ACTIVE=1` no ambiente do hook | bloqueia escritas nesta sessão |
| **(b)** ancestralidade | marcador com PID vivo **e** o processo do hook descende desse PID (`/proc` no Linux/WSL) | bloqueia só a árvore do `verify.py`/motor |
| marcador sozinho | presente, sem (a) e sem (b) | **não** bloqueia (executores irmãos liberados) |
| PID morto | PIDs do marcador sem processo vivo | marcador removido na hora; liberado |

Proteção por motor:

| Superfície | Caminho que protege | Notas |
|---|---|---|
| Devin CLI headless (`verify.py`) | **(a)** | `run_engine` exporta `DELPI_VERIFIER_ACTIVE=1`; **(b)** reforça via PIDs no marcador |
| Cursor CLI headless (`verify.py`) | **(a)** | idem; fallback do launcher |
| Claude Code (agente com `--always`) | **(a) equivalente** | hook `guard --always` (escopo do subagent) |
| Cursor IDE / Devin Desktop (executor) | nenhum, por design | marcador de um eval **não** trava o executor |

Diagnóstico: `python ~/.delpi-agent-kit/verifier_hooks.py status`

Caminhos Windows/UNC (`\\wsl.localhost\…`, `C:\…`) são normalizados para Linux em `verify.py` e nos hooks
(`normalize_agent_path`), sem chamar processo externo.

### Limites

- `permission-mode auto` do Devin **não** roda testes; o kit usa `smart` + guard.
- Guard + `DELPI_VERIFIER_ACTIVE` / ancestralidade bloqueiam escrita **só** na sessão headless; não é sandbox perfeito.
- Em hosts sem `/proc` (ex.: Windows nativo), o marcador sozinho **não** bloqueia; a proteção do motor headless depende de (a).
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

- Subagents **não** são instalados por padrão (evita o Cursor acionar o verificador fora do SWE).
  Use `--with-subagents` só se precisar do comportamento 0.1.x.
- Reinstalar remove agentes antigos **do kit** e preserva arquivos alheios.
- No Windows, `verify.cmd` em `%USERPROFILE%\.delpi-agent-kit\` repassa para o WSL
  (perfil descoberto via `cmd.exe` + `wslpath`, ou `--windows-home`).
- Hooks: guard nos configs do Devin CLI / Cursor CLI (WSL) e stop gate + track-edit nos executores
  (Cursor IDE + Devin Desktop Windows).

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
