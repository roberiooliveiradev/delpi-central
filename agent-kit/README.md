# agent-kit · delpi-verifier

Verificador independente para o trabalho dos agentes executores (Cursor, Devin e, opcionalmente, Claude
Code), em **qualquer projeto**. O executor implementa; o `delpi-verifier`, com contexto limpo e outro
modelo, prova ou refuta a entrega e devolve ordens de correção. O executor corrige e o ciclo se repete,
por no máximo 3 rodadas.

Esta pasta é autocontida: tem versão (`VERSION`), changelog, testes e instalador próprios. Ela mora no
`delpi-central`, mas não depende de nada do monorepo.

---

## Por que existe e em que se baseia

Um modelo revisando o próprio trabalho na mesma conversa herda as premissas que produziram o erro e tende a
aprovar o que escreveu. O kit aplica as práticas que o mercado adotou para resolver isso:

| Prática | Onde está no kit |
|---|---|
| Revisor com contexto limpo, que recebe o pedido e o diff, não o raciocínio do executor | Subagent + "pedido de verificação" (`verifier/project-contract.md`) |
| Modelo de outra família | `--<plataforma>-model` no instalador; o relatório marca `independencia: DEGRADADA` se for a mesma família |
| Expectativas escritas antes de ler o código (contra o viés de concordância) | Passo 2 do protocolo |
| Prova executável vale mais que opinião | Passo 4; `TEST_NOT_RUN` nunca vira `PASS` |
| Encontrar e depois confirmar, com nota de confiança | Passo 8: só achado introduzido pelo escopo com nota ≥ 80 vira ordem de correção |
| Vigiar atalhos para passar no teste (teste editado, special-casing, `skip`) | Passo 6 + rodadas seguintes |
| Ciclo avaliador → executor com limite de rodadas | Parte A do contrato; stop gate |
| O verificador não corrige (não vira coautor) | Postura + guard |
| Decisões de produto/arquitetura voltam para o humano | `DECISION_REQUIRED` / `EXECUTION_DRIFT` |
| Medir antes de confiar | `evals/` (7 casos com defeitos plantados) |

---

## Estrutura

```
agent-kit/
├── VERSION, CHANGELOG.md, README.md
├── verifier/
│   ├── protocol.md          ← o método (corpo do agente) — fonte única
│   ├── report-format.md     ← formato fixo do relatório e das ordens de correção
│   └── project-contract.md  ← modelo da seção "Verificação" do AGENTS.md de cada projeto
├── adapters/                ← cabeçalho (frontmatter) de cada plataforma
├── hooks/verifier_hooks.py  ← guard, marcador, stop gate, registro de veredito
├── scripts/build.py         ← junta cabeçalho + protocolo em um arquivo por plataforma
├── scripts/install.py       ← instala em nível de usuário (vale para todos os projetos)
├── evals/                   ← casos de avaliação e pontuação
└── tests/                   ← testes do próprio kit (python -m unittest discover -s tests)
```

---

## Instalação

A instalação é feita uma vez por máquina, no nível do usuário (vale para todos os projetos):

```bash
python agent-kit/scripts/install.py --dry-run --cursor-model <ID> --devin-model <ID>   # mostra o plano
python agent-kit/scripts/install.py --cursor-model <ID> --devin-model <ID>             # instala
```

- Escolha para o verificador um modelo de **família diferente** da que o executor usa em cada plataforma.
  Sem `--<plataforma>-model`, o verificador usa o padrão da plataforma e a independência não fica
  garantida (o instalador avisa).
- Rode o instalador com o **mesmo Python do ambiente onde o agente roda** (Windows ou WSL): o caminho desse
  Python vai gravado nos hooks.
- Claude Code é opcional: `--platforms cursor,devin,claude --claude-model <ID>`.
- Toda configuração alterada ganha backup `*.bak-<data>`. Rodar de novo atualiza no lugar.
- Saída `3` = sobrou ação manual (ex.: `config.json` do Devin com comentários: o instalador não reescreve
  arquivo comentado e deixa um snippet para mesclar à mão).

O que é instalado:

| Plataforma | Agente | Hooks |
|---|---|---|
| Cursor | `~/.cursor/agents/delpi-verifier.md` | entradas em `~/.cursor/hooks.json` |
| Devin | `~/.config/devin/agents/delpi-verifier.md` (Windows: `%APPDATA%\devin\agents`) | chave `hooks` de `config.json` no mesmo diretório |
| Claude Code (opcional) | `~/.claude/agents/delpi-verifier.md` | guard no próprio frontmatter do agente |
| Comum | `~/.delpi-agent-kit/` (script dos hooks, `VERSION`, `install.json`, estado) | — |

**Atualizar:** `git pull` no repositório e rodar o instalador de novo com os mesmos modelos (estão em
`~/.delpi-agent-kit/install.json`). **Remover:** `python agent-kit/scripts/install.py --uninstall` — remove
só o que o kit adicionou.

---

## Como usar em um projeto

1. Copie a seção de `verifier/project-contract.md` para o `AGENTS.md` da raiz do projeto e preencha a
   parte B (fontes de autoridade, comandos de verificação, regras, áreas sensíveis).
2. A partir daí, o executor segue o ciclo da parte A: chama `delpi-verifier` em primeiro plano, aplica as
   ordens de correção (ou contesta com evidência) e repete até `ACCEPT` ou 3 rodadas.
3. Nos prompts, basta um bloco no final: *"Antes do EXECUTION REPORT, siga o ciclo da seção Verificação do
   AGENTS.md e anexe o veredito do delpi-verifier sem editar."*

Chamada direta: no Cursor, `/delpi-verifier <pedido de verificação>`; no Devin, "use o subagent
delpi-verifier para ...".

---

## Como o kit garante o ciclo (e onde ele não garante)

**Três camadas, da mais fraca para a mais forte:**

1. **Instrução** — o protocolo e a parte A do contrato. Vale em qualquer plataforma.
2. **Permissões do agente** — Devin: `allowed-tools` sem ferramentas de edição. Claude Code: `tools: Read,
   Grep, Glob, Bash` + guard no frontmatter. Cursor: `readonly: false` de propósito, porque `readonly: true`
   roda em modo Ask, que bloqueia o shell e impediria o verificador de rodar testes.
3. **Hooks** — instalados em nível de usuário:
   - **guard**: enquanto o verificador roda, bloqueia comandos que alteram estado (git que escreve, `rm`,
     `mv`, redirecionamento para arquivo, instalação de pacote, containers, migrations, deploy, HTTP de
     escrita, SQL de escrita, edição de arquivo, MCP que escreve). Saída 2 = bloqueado.
   - **marcador**: Cursor e Devin não dizem ao hook se um comando vem do subagent. Por isso o início do
     `delpi-verifier` cria um marcador (Cursor: `subagentStart`; Devin: `PreToolUse` de `run_subagent`) e o
     fim remove (`subagentStop` / `PostToolUse`). O guard só age com o marcador ativo.
   - **stop gate**: em repositório com o marcador `<!-- delpi-verifier:contract` no `AGENTS.md`, se esta
     sessão editou arquivos por ferramenta (Cursor: `afterFileEdit`; Devin: `PostToolUse` de
     `write`/`edit`/`apply_patch`), o estado mudou desde o início da sessão e não há veredito registrado
     para o estado atual, o agente recebe a instrução de chamar o verificador antes de encerrar (Cursor: `followup_message`, no máximo 2
     vezes por turno; Devin: `decision: block`, sem repetir quando `stop_hook_active`).
   - **ledger**: o verificador grava o veredito em `.git/delpi-verifier/verdicts.jsonl` (dentro de `.git`,
     nunca é commitado), associado a um fingerprint do estado do repositório.

**Limites conhecidos (seja honesto com eles ao confiar no resultado):**

- O guard é uma lista de bloqueio, não um sandbox: um comando novo e criativo pode passar. Ele é defesa em
  profundidade junto com a instrução e as permissões.
- Se o `subagentStop` do Cursor não disparar (há relatos de instabilidade), o marcador fica preso e o guard
  passa a bloquear o executor. O marcador expira em 45 min; para liberar antes, rode
  `python ~/.delpi-agent-kit/verifier_hooks.py clear` (o guard deixa esse comando passar). Diagnóstico:
  `python ~/.delpi-agent-kit/verifier_hooks.py status`.
- Há relatos de hooks do Cursor no Windows que não entregam `followup_message`. Valide com os smoke tests
  do prompt de instalação antes de depender do stop gate.
- O stop gate só considera sessões que editaram arquivos por ferramenta, para não cobrar uma sessão pelas
  mudanças de outro agente na mesma árvore. Alteração feita só por comando de shell (script gerador, `sed`)
  não liga o gate — a instrução do contrato continua valendo.
- O stop gate garante que a verificação **rodou**, não que passou: o veredito vai no relatório.
  `SKIPPED` (dispensa) pode ser registrado pelo executor e fica visível no ledger e no relatório final.
- Subagents personalizados do Devin ainda são experimentais; o formato pode mudar.
- No Claude Code o verificador é sempre da família Claude: use-o só quando o executor for de outra família.
- Desligar o stop gate temporariamente: variável de ambiente `DELPI_VERIFIER_GATE=off`.

---

## Avaliação

Veja `evals/README.md`. Rode os 7 casos ao instalar e a cada mudança de protocolo, modelo ou plataforma, e
registre os resultados na tabela de lá.

## Desenvolvimento do kit

```bash
cd agent-kit && python -m unittest discover -s tests -v
python scripts/build.py --out /tmp/dak-dist --cursor-model x --devin-model y   # inspecionar os arquivos gerados
```

Mudou o protocolo? Atualize `CHANGELOG.md` e `VERSION`, rode os testes e os evals.
