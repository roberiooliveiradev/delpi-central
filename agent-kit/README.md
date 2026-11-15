# agent-kit · delpi-verifier

Verificador independente para o trabalho dos agentes executores (Cursor IDE e Devin Desktop), em
**qualquer projeto**. O executor implementa; o `delpi-verifier`, em sessão headless separada, prova ou
refuta a entrega e devolve ordens de correção. O executor corrige e o ciclo se repete, por no máximo 3
rodadas. O executor **nunca** se autoverifica.

Esta pasta é autocontida: tem versão (`VERSION`), changelog, testes e instalador próprios. Ela mora no
`delpi-central`, mas não depende de nada do monorepo.

Versão atual: **0.2.0**.

---

## Arquitetura 0.2.0

```
executor (Cursor IDE ou Devin Desktop)
  → grava PEDIDO em <git-dir>/delpi-verifier/requests/
  → python ~/.delpi-agent-kit/verify.py --request-file <arquivo>
       → valida pedido (sem gastar token)
       → ativa marcador + DELPI_VERIFIER_ACTIVE=1
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
```

- Subagents **não** são instalados por padrão (evita o Cursor acionar o verificador fora do SWE).
  Use `--with-subagents` só se precisar do comportamento 0.1.x.
- Reinstalar remove agentes antigos **do kit** e preserva arquivos alheios.
- No Windows, `verify.cmd` em `%USERPROFILE%\.delpi-agent-kit\` repassa para o WSL.
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
