# ATLAS | Etapa 71: preflight e plano de provisionamento, sem intervencao no host

**Data:** 18/11/2026
**Referencias:** issue [#232](https://github.com/roberiooliveiradev/delpi-central/issues/232), etapas 65-70 e PR #277
**Estado:** SOURCE-ONLY | \`status=blocked\` | PREPARE/ACT OFF | quatro ferramentas MCP READ.
**Progresso de referencia:** **60%**. A entrega desta etapa NAO equivale a instalacao HML, atestacao SEC, nem permissao operacional.

## 1. O que esta PR prepara

1. \`atlas_hml_b_stage71_readonly_preflight.py\`: API explicitamente invocada, restrita a metadados de caminhos, identidades e unidades ATLAS conhecidas, com coleta de habilitacao AppArmor. Nao conecta ao Docker Engine, nao consulta endpoints de administracao, nao invoca systemd, nao abre processos, nao cria diretorios, nao altera ACL. Raiz de fixture injetavel para CI. Resultados continuam autodeclarados/nao atestados.
2. \`atlas_hml_b_stage71_provisioning_review.py\`: plano estatico de dois usuarios de sistema nao-root, grupos proprios e cinco diretorios; identifica ausencias e divergencias de UID/GID, colisao entre identidades, grupo Docker primario, ACL/mode nao conformes e unidades inesperadas. Nunca gera comandos executaveis nem provisiona recursos.
3. \`atlas_hml_b_stage71_git_reconcile.py\`: revisa dossier JSON estrito e sanitizado da situacao Git do \`srv-api\`. Reporta branch divergente, arquivos locais alterados, ancestrais declarados, indices, untracked, merge em andamento e conflitos; **sempre bloqueia** pull, stash, reset, clean e deploy ate decisao humana. Nunca executa Git.
4. Testes novos com filesystem descartavel, schema adversarial, dados inesperados, segredos em dossier, modo e UID de diretorios, restricoes de provisionamento, e recusa a tratar checkout sujo como sincronizado. Teste **elevado** Linux com processo signer UID 61021 recusa parent owned por UID 61022 e GID divergente; apenas no runner GitHub descartavel.

### Limites do probe

O coletor observa **somente**:
- Usuarios/grupos \`atlas-hml\`, \`atlas-hml-bridge\`, \`atlas-hml-signer\` (NSS do host apenas com \`root=/\`).
- Metadados DAC/ACL dos cinco diretorios ATLAS explicitamente previstos.
- Presenca de cinco nomes de unidade ATLAS em \`/etc\`, \`/run\` e \`/usr/lib/systemd/system\` (nao estados efetivos do systemd).
- Existencia, tipo e metadados do socket \`/run/docker.sock\`. **Nao conecta a ele**.
- Flag \`/sys/module/apparmor/parameters/enabled\`: **Y significa habilitado, nao confirma perfil efetivo do signer**.

NAO verifica:
- Endpoints TCP alternativos, \`DOCKER_HOST\`, Docker contexts, sockets adicionais, FDs ja abertos, perfis LSM por PID, credenciais reais, revisions Git, origem de contêiner, provedores de backup/ancora, permissao real para instalar.
- Status funcional do \`delpi-public-hub\`, que foi observado executando sem healthcheck; uma coleta de app em outra etapa sera necessaria para atestacao de producao.
- Independencia da propria coleta ou SEC-01..SEC-10.

A ausencia de um caminho nao autoriza sua criacao. Um resultado positivo de todos os checks continua com \`host_attested=False\`, \`can_execute=False\` e \`status=blocked\`.

## 2. Baseline fornecido pelo operador (nao atestado)

| Item | Fato reportado | Restricao |
| --- | --- | --- |
| SO | Ubuntu 24.04, kernel 6.8.0-147-generic | identidade host nao provada |
| Docker | \`dockerd -H fd:// --containerd=/run/containerd/containerd.sock\` | unit \`/usr/lib/systemd/system/docker.service\`; sem drop-ins informados |
| TCP Docker | portas padrao 2375/2376 nao vistas | portas alternativas/contextos nao excluidos |
| AppArmor | \`Y\` | perfis/constraints por PID nao provados |
| Docker/socket | Docker+containerd active; \`/run/docker.sock\` root:docker 0660 | nao inferir isolamento efetivo de signer/bridge |
| HML | \`delpi-hml-public-hub\` running + healthy | fixture de producao intocada |
| PROD | \`delpi-public-hub\` running sem healthcheck | nao declarar healthy |
| Identidade | \`atlas-hml\` UID 995, GID 985 presente | bridge e signer ausentes; nao inventar UID/GID |
| systemd/diretorios ATLAS | ausentes | esperado no estado pre-ativacao |
| Git host | \`main\` em \`0869cb82a9c68846e58a285926d02c98d6d4847e\` | \`origin/main\` local tambem nessa revisao; GitHub main agora a frente |
| Modificacoes locais | \`infra/scripts/up-hml-sequential.sh\` mudou **modo 100644→100755**; \`shared/delpi_auth.egg-info/SOURCES.txt\` incluiu \`delpi_mcp/avatar_image.py\` | NAO descartar nem fazer stash/reset/clean |
| GitHub base desta etapa | \`b00865e643301c31bb038a49b3f76e022da984cc\` | revisar HEAD remoto novamente antes da mudanca |

A diferenca Git do host para a main no momento do planejamento nao tocava os dois arquivos sujos. Isso NAO autoriza um pull automatico, pois pode haver novos commits concorrentes, outros worktrees e alteracoes nao visiveis na coleta.

## 3. Plano de identidades e filesystem para janela futura

\`atlas-hml\` **ja existe**, nao deve ser recriado nem receber grupo Docker.

| Recurso | Owner / grupo previstos | DAC |
| --- | --- | --- |
| Conta \`atlas-hml-bridge\` | usuario de sistema sem login, grupo primario \`atlas-hml-bridge\` | UID/GID alocados sob change-control |
| Conta \`atlas-hml-signer\` | usuario de sistema sem login, grupo primario \`atlas-hml-signer\` | UID/GID diferentes de bridge/atlas-hml |
| \`/run/atlas-hml-readonly\` | root : atlas-hml | \`0750\` |
| \`/run/atlas-hml-signer\` | atlas-hml-signer : atlas-hml-signer | \`0750\` |
| \`/run/atlas-hml-signer-socket\` | atlas-hml-signer : atlas-hml-bridge | **\`02750\`** setgid |
| \`/var/lib/atlas-hml-signer-state\` | atlas-hml-signer : atlas-hml-signer | \`0750\` |
| \`/var/lib/atlas-hml-signer-keys\` | atlas-hml-signer : atlas-hml-signer | \`0700\` |

O futuro socket \`sign.sock\` deve ser criado *pelo signer ja nao-root*, herdando GID bridge, modo **\`0660\`**, sem \`chown\`, sem herdar listener root-prebound. Grupo bridge tem travessia do parent mas nao escrita. A bridge nao deve receber grupo \`docker\`, \`sudo\`, nem acesso ao diretório de chave ou checkpoint. Apos provisionamento autorizado, verificar \`id\`, \`getent\`, ACL, supplementary groups e permissao negativa real.

**Nao existem comandos de provisionamento aprovados nesta PR.** Identidades reais, UID/GID, ACLs e caminhos precisam ser atestados antes de gerar/aplicar um roteiro mutante.

## 4. Reconciliação Git, estritamente planejada

Os dois arquivos locais pertencem a outras frentes do repositório e devem ser preservados. Acoes atuais permitidas apenas para futura observacao, quando o owner solicitar, incluem:

\`\`\`bash
repo=/home/operador/projetos/delpi-central
git -C "$repo" rev-parse HEAD
git -C "$repo" branch --show-current
git -C "$repo" status --porcelain=v1
git -C "$repo" diff --summary
git -C "$repo" diff --check
git -C "$repo" diff -- infra/scripts/up-hml-sequential.sh shared/delpi_auth.egg-info/SOURCES.txt
git -C "$repo" worktree list
\`\`\`

Para **futura** sincronizacao: confirmar revision remota de novo, preservar ambos os diffs e permissao executavel do script, revisar index/untracked/merge em andamento e apenas entao decidir com o owner a estrategia de sincronizacao. Nao executar \`git fetch\`, \`git pull --ff-only\`, \`git stash\`, \`git reset\`, \`git clean\`, \`chmod\` ou deploy agora.

O parser \`stage71_git_reconcile\` nao processa diffs brutos nem paths arbitrarios em sua resposta. Para permitir revisao humana, o dossier so reconhece as duas alteracoes conhecidas e sinaliza \`UNEXPECTED_LOCAL_MODIFICATION\` para outras.

## 5. Gates antes de qualquer instalacao, bootstrap ou piloto

1. PR Etapa 71 com CI no HEAD, DELPI Verifier independente, owner decide merge.
2. Change-control do owner: escopo HML preciso, janela, comandos aprovados, baseline e plano de reversao.
3. SEC-01 ate SEC-10: atestacao independente ou excecao formal adequada. Raiz root no mesmo host permanece risco residual e nao é autenticidade criptografica independente.
4. Ativar verificacoes host: NSS/UID/GID/supplementary groups, AppArmor por PID, FS ACL, socket e FD, endpoints Docker alternativos e isolamento do Docker Engine, unidades systemd efetivas. Produto de coletores nao substitui aprovacao.
5. Construir packaging operacional **separado**: \`candidate-units/*.candidate\` e \`review-only/*.review\` continuam nao instalaveis; \`ExecStart=/usr/bin/false\`, sentinel impossivel, sem \`[Install]\`.
6. Bootstrap operacional gen1 **somente** com ancora externa verdadeira + change/owner approval; ausencia de checkpoint nunca implica genesis. Chave Ed25519 real e copia PKCS#8/GLPI sao etapas separadas e autorizadas.
7. Piloto so HML: monitorar HML e comparacao PROD, sem reiniciar Docker Engine, containerd ou \`delpi-public-hub\`; abortar em risco de impacto ou qualquer bloqueio SEC. Rollback somente ATLAS, nao restaurar contador antigo automaticamente.

**Nenhum comando nesta PR cria usuarios, grupos, diretorios, chaves ou servicos. Nada e instalado no srv-api.**
