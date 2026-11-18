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
- **Exceção explícita — Pesquisa de Satisfação de Clientes (Portal Comercial):**
  desenvolvimento e integração **somente DEV**; testes funcionais,
  de integração, segurança, permissões e validação com múltiplos
  usuários/cenários em **HML (homologação)**. **É proibido executar
  deploy da funcionalidade, suas migrações, rotas ou habilitar suas
  capacidades em PROD por commit/push, por incremento ou como efeito
  incidental de deploy de outros serviços.** A regra de deploy
  automático pós-push acima **não se aplica à Pesquisa de Satisfação**.
  A publicação em PROD exige: solução completa em HML, critérios de
  aceite e regressão demonstrados, autorização explícita do
  solicitante/PO e plano de implantação/rollback aprovado. Até então,
  proteger integração compartilhada por controle real de exposição
  (feature gates desabilitados e isolamento de migrações/rotas conforme
  verificação do owner); não presumir que branch `main` ou gate de
  frontend, isoladamente, impeça efeitos produtivos. **Se não for
  possível garantir que deploy de outro serviço não exponha a pesquisa,
  interromper a publicação e reportar o risco ao owner.** Escopo
  desta exceção: Pesquisa de Satisfação; outras aplicações mantêm
  sua política própria até decisão específica.
- Regras canônicas de engenharia: `.cursor/rules/` (ver
  `development-standards-index.mdc` e `delia-execution-protocol.mdc`
  para tasks DÉLIA).
- Inventário de env/Compose é **fechado**: só `infra/.env.dev.example`,
  `infra/.env.prod.example`, `infra/env.hml.example` + `docker-compose.yml`,
  `docker-compose.dev.yml`, `docker-compose.hml.yml`. Não criar overlays,
  `env.<x>.example` ou `.env.<variante>` — variação vai em env var ou
  profile (`platform-delivery-runtime-operations.mdc`).

## Fontes TOTVS/ERP — orientação para agentes

Em tarefas que envolvam ADVPL/TLPP, rotinas MATA/FINA, RESTALL, RPO, cadastro SB1/SA5 ou integração de escrita Protheus, invocar a skill `.devin/skills/totvs-protheus-integration/SKILL.md` (Devin) e aplicar `.cursor/rules/totvs-product-patterns.mdc` e `.cursor/rules/totvs-protheus-write-integration.mdc`.

- **Fonte versionada primária de código Protheus:** repositório privado `Delpi-ti/protheus-erp`, branch `master`, no SHA atual obtido por acesso GitHub autorizado. Registrar repo/branch/SHA/path/blob SHA; jamais supor acesso ou atualização automática.
- **Espelho de referência:** `docs/13-fontes-totvs-protheus/` neste repositório; comparar blob SHA com o upstream. Bibliotecas e contratos: `api-delpi/docs/api/padroes-totvs/` e `api-delpi/docs/integrations/`.
- **Runtime:** nem o GitHub nem o RESTALL provam versão compilada no RPO; exigir evidência de ambiente/compilação ou marcar `INCONCLUSIVE`/`TO_INVENTORY`. Acesso ao repositório não autoriza compilação, RPO write, deploy ou ERP write.
- **Rotinas:** MATA010/ExecAuto é um contrato específico; MATA061/SA5 tem modelo MVC, não presumir ExecAuto. Antes de nova API, inventariar equivalentes, permissões, reuso e read-back integral; respeitar PREPARE/ACT, owner ERP e Core AuthZ.


## Workspace ADVPL — decisão de escopo do PO

Fontes ADVPL novos/evoluídos de integrações DELPI serão desenvolvidos e versionados somente em `api-delpi/integrations/protheus-advpl/` (ver `README.md` local e módulos por capacidade). O repositório privado `Delpi-ti/protheus-erp` é **referência READ-ONLY** até autorização futura explícita. O espelho `docs/13-fontes-totvs-protheus/` não é workspace de novas alterações. Pacotes de compilação ZIP são gerados de commits aprovados e entregues à equipe ERP; compilação no TST01/PRD, alterações do RPO e escritas ERP requerem gates independentes. Commits de fonte/documentação nesta pasta não autorizam deploy da API ou do Protheus; se o protocolo geral de deploy entrar em conflito, escalar ao owner antes de executar.

## Verificação (delpi-verifier)

<!-- delpi-verifier:contract v1 -->

Verificação independente da entrega por outro agente, com outro modelo. Kit, protocolo e
instalação: `agent-kit/README.md`.

### A. Ciclo do executor

Obrigatório antes de declarar a tarefa concluída e **antes do commit/push e do deploy
canônico** acima. Fonte canônica do ciclo: parte A de
`agent-kit/verifier/project-contract.md`. Em resumo:

1. Depois de alterar código, configuração, migration, contrato ou teste, gravar o
   `PEDIDO DE VERIFICAÇÃO` em `<git-dir>/delpi-verifier/requests/` (nunca no working tree)
   e rodar um comando: `python ~/.delpi-agent-kit/verify.py --request-file <arquivo>`
   (objetivo com RQ/AC, escopo `working tree` ou `base..head`, alegações, modelo do
   executor, rodada). O executor nunca se autoverifica.
2. Corrigir cada ordem de correção (OC) no código de produção, ou contestar com evidência.
   Nunca alterar teste, runner ou limites de cobertura para a reconferência passar.
3. Repetir com `verify.py` (rodada + 1), no máximo 3 rodadas.
4. `DECISION_REQUIRED` ou `EXECUTION_DRIFT` encerram o ciclo: devolver a decisão ao usuário.
5. EXECUTION REPORT com o veredito do verificador sem edição e a tabela de rodadas.

### B. Específico deste repositório

- **Fontes de autoridade:** a hierarquia de `.cursor/rules/evidence-driven-execution.mdc`
  (§ Hierarquia de fontes de verdade), começando por
  `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`.
- **Definition of Done e evidência:** `.cursor/rules/test-and-commit.mdc`,
  `.cursor/rules/platform-quality-testing.mdc` e
  `docs/11-padroes-de-desenvolvimento/checklist-code-review.md` (declarar quais das oito
  responsabilidades foram materiais).
- **Comandos de verificação:**
  - testes do serviço/plugin afetado, conforme o workflow em `.github/workflows/` ou o
    `scripts/ci-*.sh` correspondente;
  - gates transversais: § "Comandos de enforcement transversal" de `test-and-commit.mdc`;
  - regras `.cursor` alteradas: `python scripts/audit_cursor_rules.py`;
  - documentação: `python scripts/audit_documentation_structure.py`;
  - `agent-kit/` alterado: `cd agent-kit && python -m unittest discover -s tests`.
- **Regras que não podem ser quebradas:** mapa canônico de
  `.cursor/rules/centralized-rules-first.mdc` (owners transversais) e as regras `.cursor`
  aplicáveis aos arquivos do diff.
- **Áreas sensíveis:** autenticação/autorização (fail-closed, teste negado), escrita no
  Protheus e feature gates produtivos, migrations, e a exceção da Pesquisa de Satisfação
  (seção Entrega): nada no diff pode expor a funcionalidade em PROD.
- **Comandos proibidos ao verificador (além dos padrões do kit):** deploy em `srv-api`
  (`ssh`, `up-prod-sequential.sh`), subir/derrubar containers, migrations, chamadas de
  escrita a APIs ou bancos de HML/PROD.
- **Vocabulário extra:** classificações de evidência de `evidence-driven-execution.mdc`
  (`CONFIRMADO_NO_CODIGO`, `INFERENCIA`, …) e estados de ledger `RQ-*`.

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

## Exceção operacional ATLAS | MCP Linux (decisão específica do owner, 17/11/2026)

Para **qualquer alteração do ATLAS** (arquivos `linux-ops-mcp/linux_ops_mcp/atlas_*`, `linux-ops-mcp/review-only/atlas-*`, documentação `mcp-linux-control`, gates/CI ATLAS), prevalece sobre a regra geral de commit direto em `main` e deploy automático:

- Trabalhar **somente em branch exclusiva e PR por pacote**, com autorização do owner para criação/troca de branch conforme governança abaixo; nunca integrar a PR automaticamente. Somente o owner decide o merge.
- A aprovação de código e o merge **NÃO** autorizam `git pull`, scripts `up-prod-sequential.sh` / `up-hml-sequential.sh`, instalação systemd, criação de UID/GID/ACL, geração de chave ou ativação no `srv-api`. Qualquer ação no host exige autorização operacional própria, escopo/comandos exatos, janela, baseline e rollback.
- Durante as Etapas 62 a 72: `SOURCE-ONLY`, quatro MCP **READ**, `PREPARE/ACT OFF`, `status=blocked`. Unidades `.review` e `candidate-units/*.candidate` são deliberadamente **não instaláveis** (sem `[Install]`, sentinel impossível, `ExecStart=/usr/bin/false`). Nunca transformar esses artefatos em unidades operacionais sem nova aprovação, packaging e revisão. Deploy geral do repositório **não** deve copiar ATLAS para `/etc/systemd/system`.
- Fluxo obrigatório: CI no HEAD, DELPI Verifier independente documentado, riscos residuais explicitados, parecer/aceite do owner em GitHub; nenhum resultado de CI ou assinatura local substitui atestação host ou parecer humano SEC-01.
- Alterações em código de outros módulos e deploys não ATLAS continuam sob suas respectivas políticas, mas não podem habilitar inadvertidamente um componente ATLAS em HML/PROD.
