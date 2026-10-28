# Git Main Alignment + Agent Branch Governance

Registro técnico da recuperação/inventário do estado Git do
`delpi-central` e da política obrigatória de branches/worktrees
para todos os agentes (Devin, Cursor, Codex e demais).

---

## 1. Contexto

O checkout principal (`~/projetos/delpi-central`) estava na branch
`feat/metalography-visual-fidelity` com 10 arquivos rastreados
modificados, diversos arquivos não rastreados e a pasta
`engineering-api/` ausente do working tree — o que motivou a
suspeita de divergência. `git pull --ff-only origin main` foi
corretamente bloqueado pelo Git (alterações seriam sobrescritas);
esse bloqueio protegeu o trabalho local e não foi contornado.

## 2. Diagnóstico factual (somente leitura)

| Fato | Evidência |
|---|---|
| Branch ativa | `feat/metalography-visual-fidelity` |
| HEAD | `c02bbd84022ade641a386c55639c8b6f17322cbb` |
| `origin/main` | `d136d09b5b9b8194b408dcba978881c0b084b87e` |
| `merge-base HEAD origin/main` | `c02bbd8402` — **HEAD é ancestral de `origin/main`** |
| Divergência `HEAD...origin/main` | **0 à frente / 842 atrás** |
| Feature vs `origin/feat/metalography-visual-fidelity` | 237 commits à frente do próprio remote (`24a58bb7b1`) |
| Local `main` | `fad973015d` — checked out no worktree `delia-semrel-wt`; ancestral de `origin/main` → **fast-forward possível** |
| Sparse checkout | inexistente |
| `engineering-api` em `origin/main` | `040000 tree` — `engineering_app/main.py` e doc F2a confirmados por `git ls-tree` |
| Worktrees | ~35 registrados (vários detached; um prunable `proc-0076`) |

### Leitura correta da situação

- **Não há divergência de commits entre a feature e `main`**: todos
  os commits da feature já estão integrados em `origin/main` (a
  feature é ancestral estrita). Os "237 commits" são frente ao
  *remote da própria feature*, não frente à `main`.
- `engineering-api/` não aparece no checkout porque a feature é de
  antes da F1 (a pasta nasceu na F1/F2a, já publicada na `main`).
- O bloqueio do pull é **exclusivamente por arquivos locais
  modificados/não rastreados**, não por história.

## 3. Inventário de alterações (sem conteúdo sensível)

**Rastreados modificados (10):** arquivos de `api-delpi`
(supplies/protheus — payload, use cases, repository, router e 3
testes), `core-api/app/content/notification_catalog.json` e
`gateway/nginx.dev.conf`.

**Não rastreados (~49 entradas):** diretórios `.worktrees/*`
(vários worktrees preexistentes), arquivos soltos de nomes
diversos — incluindo nomes potencialmente sensíveis (`credencial`,
`forged`, `devnull`, etc.) que **não foram inspecionados, copiados
ou publicados** — e artefatos de docs/scripts locais.

Nenhum arquivo foi lido, movido ou copiado. Nenhum segredo entrou
neste documento, em logs, prompts ou no Git.

## 4. Estado de `main` e `engineering-api`

- `origin/main` @ `d136d09b5b` contém `engineering-api/` completa
  (F1 + F2a) — `git ls-tree` comprovado.
- `main` **local** @ `fad973015d` (em `delia-semrel-wt`) está 1
  commit atrás; fast-forward para `origin/main` é possível **mas
  exige operar o worktree de terceiro** → pendente de autorização.
- A branch ativa do checkout principal pode ser fast-forwardada em
  história (ancestral), porém o pull é bloqueado pelos arquivos
  locais modificados — decisão do usuário sobre o destino desse
  trabalho precede qualquer movimentação.

## 5. Estratégia de preservação

- Zero operações destrutivas: nenhum `reset --hard`, `clean`,
  `checkout -f`, `switch -f`, `push --force`, `stash`, `merge`,
  `rebase`, `cherry-pick`, `worktree add/remove` ou `branch -D`.
- Todo o inventário foi feito com comandos somente-leitura.
- A publicação desta governança usou um worktree detached
  preexistente do executor (`.worktrees/eva-f0`), cujo HEAD foi
  realocado para `origin/main` com `git reset --mixed` — operação
  não destrutiva sobre um HEAD detached já integralmente contido na
  `main` (nenhum commit ou arquivo perdido); nenhuma branch foi
  criada ou trocada.

## 6. Política de branches/worktrees (Fase C)

Seção **"Git Branch and Worktree Governance — User Approval
Required"** adicionada a `AGENTS.md`, com 10 regras:

1. `main` é a branch canônica — sem estratégias paralelas.
2. Proibida troca automática de branch (switch/checkout/detached).
3. Proibida criação automática de branches/worktrees/remotes.
4. Worktrees preexistentes são preservados.
5. `git rev-parse HEAD`, `branch --show-current`, `status --short`
   e `worktree list` obrigatórios antes de modificar código.
6. Alterações concorrentes: preservar; sem stash/reset/clean.
7. Branch inesperada: registrar, inspecionar, pedir decisão.
8. Autorização de código ≠ autorização de branch/worktree.
9. Push/integração: sem push de branch inesperada, sem mistura de
   tasks, sem integrar features à `main` sem autorização.
10. Conflito de instruções: regra que recomendava worktree
    automática agora exige autorização — reportar divergência.

### Cobertura de agentes (Fase D)

`AGENTS.md` é a única superfície normativa de agentes: `.devin/
config.json` (`read_config_from`) cobre `agents_standard`, `cursor`,
`windsurf`, `claude`, `copilot`, `opencode` e `zed`; `.devin/rules/
cursor-rules-canonical.md` delega a `.cursor/rules/`; nenhuma regra
`.mdc` menciona worktree/criação de branch. **Zero conflitos a
reconciliar** — menor diff possível aplicado.

## 7. Procedimento seguro para disponibilizar `main` (autorizado vs pendente)

**Executado (autorizado pela política de entrega + esta missão):**

- `git fetch origin` — referências atualizadas.
- Inventário completo somente-leitura.
- Publicação de `AGENTS.md` + este documento na `main` via
  worktree detached preexistente do executor (commit + push
  `HEAD:main`, fast-forward, escopo restrito aos 2 arquivos).

**Pendente de autorização explícita do usuário:**

- Atualizar `main` local (`delia-semrel-wt`) — `git pull --ff-only`
  naquele worktree, ou operação equivalente escolhida pelo usuário.
- Destino dos 10 arquivos modificados e dos não rastreados no
  checkout principal: commit na feature, stash autorizado, ou
  fast-forward da feature para `origin/main` (história compatível —
  HEAD é ancestral) após decisão sobre o trabalho pendente.
- Descarte/organização de worktrees órfãos (`proc-0076` prunable) e
  arquivos não rastreados — nunca automático.
- Registro de `engineering-api` no checkout da feature ocorre
  automaticamente quando a feature for alinhada à `main` (a pasta
  já existe em `origin/main`).

## 8. Verificação e testes (Fase E)

- Política explícita em `AGENTS.md` — 10 regras presentes.
- Nenhuma instrução ativa contradiz a política (busca por
  `worktree|git switch|checkout -b|branch` em `.cursor/rules`,
  `.devin/`, `AGENTS.md`, docs normativos — zero ocorrências fora
  deste documento e de histórico documental não-normativo).
- `engineering-api` comprovada em `origin/main` via `git ls-tree`.
- Checkout principal **intocado**: branch, HEAD, arquivos
  modificados e não rastreados idênticos ao inventário inicial.
- Nenhum commit existente perdido; nenhum dado sensível publicado.

## 9. Limitações e residuais

- `main` local permanece em `fad973015d` até autorização — este
  relatório não declara `main` sincronizada; apenas `origin/main`
  está atualizada.
- A classificação semântica dos 49 arquivos não rastreados e dos 10
  modificados cabe ao usuário/owner — não foram inspecionados.
- Worktree `proc-0076` reporta "prunable" (gitdir órfão) —
  limpeza exige autorização.
- O procedimento de fast-forward da feature/checkout exige decisão
  sobre o trabalho não commitado — bloqueado por política, não por
  impossibilidade técnica.

## 10. Arquivos normativos alterados

- `AGENTS.md` — nova seção de governança (10 regras).
- Este documento — registro canônico da operação.
