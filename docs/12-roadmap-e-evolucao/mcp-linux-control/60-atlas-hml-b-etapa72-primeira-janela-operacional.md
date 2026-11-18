# ATLAS | Etapa 72: prontidao para a primeira mudanca operacional HML

**18/11/2026 | Issue #232 | SOURCE-ONLY | status BLOCKED | PREPARE/ACT OFF | quatro MCP READ**

Esta entrega **nao autoriza nem executa** alteracoes no srv-api. Em vez de mais
etapas apenas declarativas, concentra o pacote pratico para a primeira janela:
coleta de evidencias, protecao do checkout, gate de seguranca, criterios de STOP
e procedimento de rollback. A janela e cada comando operacional exigem
autorizacao propria do owner depois de PR/CI/Verifier/merge.

## 1. Ponto de partida, confirmado antes do pacote

- PR #278 mesclada em main; ultimo checkout reportado no srv-api:
  0869cb82a9c68846e58a285926d02c98d6d4847e.
- Ao comparar com main na abertura da etapa 72, o checkout estava **31 commits
  atras**, sem mudancas remotas nos dois paths que o operador alterou. A contagem
  pode mudar enquanto outras equipes fazem merge. Confirmar novamente na janela.
- Alteracoes locais preservadas: modo 100644 => 100755 em
  infra/scripts/up-hml-sequential.sh; linha delpi_mcp/avatar_image.py em
  shared/delpi_auth.egg-info/SOURCES.txt.
- Ubuntu 24.04, Docker via dockerd -H fd://, containerd e docker.service ativos.
  Docker socket /run/docker.sock root:docker 0660, sem ACL estendida aparente.
- AppArmor habilitado (Y) NAO comprova perfil efetivo de futuros PIDs.
  Ausencia de portas 2375/2376 nao comprova ausencia de endpoint Docker alternativo.
- HML public-hub running+healthy, PROD public-hub running **SEM healthcheck**.
  Nao declarar a aplicacao PROD healthy sem teste funcional independente.
- atlas-hml existe (UID 995 / GID 985); atlas-hml-bridge e atlas-hml-signer
  nao existem; nenhum diretorio/systemd unit do signer instalado.
- O proprio usuario da coleta tem grupo docker: jamais copiar esse grupo
  para identidades futuras do ATLAS.

## 2. Entrega que pode ser usada DEPOIS de autorizacao separada

Arquivos adicionados no repositorio:
- linux-ops-mcp/ops-review/atlas-hml-stage72-host-evidence.sh.review
  Script POSIX de observacao, nao executavel por padrao e fora de qualquer
  auto-discovery de deploy; usa Git com GIT_OPTIONAL_LOCKS=0, consulta Docker
  so por inspect dos dois nomes exatos, le systemd, DAC/ACL e AppArmor. Reporta
  status de PROD SEM HEALTHCHECK e estados de seguranca NAO ATESTADOS.
- linux-ops-mcp/linux_ops_mcp/atlas_hml_b_stage72_operator_evidence.py
  CLI stdout-only que aciona o coletor Stage71 ja existente.
  Exige escolher --fixture-root (CI) ou --host-readonly (operador autorizado).
  Resultado JSON estavel, status=blocked, host_attested=false e
  can_execute=false, mesmo com dados aparentemente conformes.
- linux-ops-mcp/tests/test_atlas_hml_b_stage72_operator_evidence.py
  Testa restricao do CLI, evidencia JSON, ausencia de escrita nos fixtures
  e revisao estatica de comandos proibidos no shell. CI executa sh -n.

**ESTES ARQUIVOS NAO SAO NOVOS MCP TOOLS. NAO DEVEM SER INSTALADOS COMO SERVICES.**

Quando houver autorizacao somente para coleta de dados, o operador podera
executar, em janela delimitada, com copia revisada do repositorio:

    cd /home/operador/projetos/delpi-central
    sh linux-ops-mcp/ops-review/atlas-hml-stage72-host-evidence.sh.review

    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=linux-ops-mcp \
      python -B -m linux_ops_mcp.atlas_hml_b_stage72_operator_evidence --host-readonly

O primeiro script inclui consulta Docker read-only, feita por um usuario com
privilegios no socket, e nao deve rodar sem autorizacao de coleta. Nenhum dos
comandos acima atualiza o repositorio, inicia serviço ou cria diretorio.
NUNCA tratar o output como atestacao independente SEC.

## 3. Gate da janela A: reconciliacao Git (futura, nao aprovada aqui)

**Escopo:** SOMENTE sincronizar checkout de codigo. Nenhum deploy, build,
docker compose, restart, alteracao de permissoes ou instalacao.

Precondicoes STOP:
1. Owner aprova por escrito janela, responsavel, caminhos, comandos exatos,
   destino de backup e procedimento de retorno; confirma mais nenhuma
   equipe alterando este checkout.
2. Coletar HEAD, branch main, origin/main local, worktree e worktrees vinculados;
   registrar SHA da main remota imediatamente antes da janela.
3. Conferir que as UNICAS modificacoes locais continuam os dois paths
   documentados, que o INDEX esta limpo e que nao ha arquivo untracked
   conflitante, merge/rebase em curso ou diff inesperado.
4. Preservar antes de qualquer operacao todos os diffs (inclusive modo 100755)
   em artefato com acesso restrito fora do checkout; validar arquivo e
   manifest de hash. Nao publicar backup em GitHub.
5. Apos fetch de main, comprovar ancestry fast-forward e que o intervalo
   remoto NAO alterou os dois paths modificados; revisar a lista de mudancas.
6. Se qualquer comparacao falhar: **STOP**, sem reset, stash, clean nem force.

Receita candidata para a janela, a ser revisada, comecando por leituras:

    repo=/home/operador/projetos/delpi-central
    export GIT_OPTIONAL_LOCKS=0
    git -C "$repo" rev-parse HEAD
    git -C "$repo" status --porcelain=v1
    git -C "$repo" diff --summary
    git -C "$repo" diff --check
    git -C "$repo" worktree list

As proximas acoes ESCREVEM em disco e continuam proibidas nesta etapa:
- backup binario e metadados em destino owner aprovado fora do repositorio;
- git fetch origin main (altera refs locais);
- git merge-base --is-ancestor <HEAD_ANTES> origin/main;
- git diff --name-only <HEAD_ANTES> origin/main -- <DOIS_PATHS_SUJOS>;
- git merge --ff-only origin/main SOMENTE se todas precondicoes se confirmarem.

Depois do futuro fast-forward verificar commit exato, os dois diffs preservados,
estado dos dois hubs e ausencia de deploy; STOP ante qualquer surpresa.
**Nao recomendar git pull automatico, git reset --hard, git clean -fd ou
git stash como atalho.** Reversao de fast-forward exige plano especifico
de integracao e preservacao de outros commits; nunca reset automatico.

## 4. Gate da janela B: preparacao de identidades e diretorios HML

Escopo futuro **separado** de Git e de ativacao. Sem comandos mutantes nesta PR.
A janela B exige prova independente de identidade/host, inventario de grupos,
revisao de AppArmor e endpoints Docker, change-control e rollback.

Recursos pretendidos:
- atlas-hml-bridge: usuario de sistema nao-root, no-login, grupo primario
  proprio, sem grupo docker/sudo/privilegios e sem acesso a chave;
- atlas-hml-signer: usuario de sistema nao-root, no-login, grupo primario
  proprio, UID e GID distintos dos demais;
- /run/atlas-hml-readonly             root:atlas-hml                 0750;
- /run/atlas-hml-signer               signer:signer                  0750;
- /run/atlas-hml-signer-socket        signer:bridge                  02750;
- /var/lib/atlas-hml-signer-state     signer:signer                  0750;
- /var/lib/atlas-hml-signer-keys      signer:signer                  0700.

A traducao abreviada signer/bridge refere-se as identidades completas
atlas-hml-signer e atlas-hml-bridge. O futuro sign.sock deve ser criado
pelo proprio signer JA NAO-ROOT, herdar o grupo bridge via setgid e ter
modo 0660. Nao usar socket root-prebound, chown silencioso ou fallback de GID.

Rollback B (exige registro manual e aprovacao na propria janela):
- nao parar Docker, nginx, Public Hub de PROD ou qualquer aplicativo;
- nao alterar unidades globais, socket Docker ou perfis LSM compartilhados;
- parar SOMENTE unidades exclusivas ATLAS, quando existirem;
- remover SOMENTE artefatos dedicados ATLAS criados na janela, depois de
  conferir identidade, propriedade, vinculos e ausencia de chaves/estado
  que precisam ser preservados para resposta a incidente;
- NAO apagar contador, checkpoint monotônico ou backups de chave como
  meio de rollback. Qualquer restauracao exige revisao independente.

## 5. Gate da janela C: piloto HML, outra aprovacao

NAO CONTEMPLADA NESTA PR. Para sair de BLOCKED:
- SEC-01..10 atestados por fonte independente OU excecao formal no item
  aplicavel, com ressalva de root no mesmo host;
- verificar perfis AppArmor efetivos dos PIDs reais e ausencias de FDs
  conectados ao Docker; testar que bridge nao acessa chave/sockets Docker;
- origin de imagem + digest + revision Git Docker/HML medidos independentemente;
- bootstrap gen1 com ancora EXTERNA real, change/owner, nunca ausencia=genesis;
- chave operacional, segregacao de recovery e vinculo GLPI aprovados;
- packaging para unidades operacionais revisadas em PR SEPARADA: arquivos
  *.candidate e *.review atuais nao podem ser instalados ou ativados;
- prova funcional de PROD anterior e posterior (nao confundir running com healthy);
- rollback testado e estritamente limitado ao ATLAS.

**Decision:** Etapa 72 e somente preparacao para autorizacao da janela A.
Status BLOCKED, host_attested=false, PREPARE/ACT OFF, quatro MCP READ.
Progresso geral permanece 60% ate evidencias operacionais reais.
