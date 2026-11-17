# ATLAS | P2.2h.2ah | Leitura de HEAD sem executar Git no checkout compartilhado

**Data:** 16/11/2026 (BRT). **Estado:** PR Draft, aguardando CI e revisao independente. **HML/PROD:** sem deploy.

## Evidencia do ensaio manual no srv-api

A conta tecnica local atlas-hml foi provisionada pelo operador com UID 995 e grupo exclusivo atlas-hml (GID 985), sem grupos sudo, docker ou projetos. O operador validou leitura de codigo e negacao de escrita no checkout compartilhado de /home/operador/projetos/delpi-central. O preflight rodou com Python/HTTPX em ambiente virtual root-owned e reportou corretamente conta nao privilegiada, mas HML_GIT_OBSERVATION_UNAVAILABLE e HML_PROXY_UNAVAILABLE.

A investigacao manual identificou o motivo do primeiro bloqueio: ao executar o Git como atlas-hml, o Git recusou a propriedade de checkout (detected dubious ownership). O teste pontual com git -c safe.directory=/home/operador/projetos/delpi-central ... rev-parse --verify HEAD, somente em um comando de diagnostico, devolveu um SHA de 40 caracteres. **Essa consulta nao e um comprovante de release implantada, fonte confiavel ou atestacao de integridade.**

Nao se aplica safe.directory global, nao se altera proprietario/grupo do checkout, nao se concede docker/sudo ao coletor e nao se executa Git no checkout compartilhado pelo CLI a partir desta mudanca.

## Entrega: metadados minimos apenas de HEAD e ref main

1. linux-ops-mcp/linux_ops_mcp/atlas_hml_git_head_peek.py: leitor local dedicado, sem subprocessos e sem executar Git. Usa somente caminho fixado do host e descritores os.open com O_NOFOLLOW, O_DIRECTORY, O_CLOEXEC e leitura limitada de arquivos regulares. Le .git/HEAD exigindo ref: refs/heads/main, a ref loose .git/refs/heads/main ou sua forma packed .git/packed-refs. SHA e validado por formato exato [0-9a-f]{40}. Le HEAD e ref duas vezes para detectar mudancas obvias entre leituras (nao fornece snapshot atomico).
2. linux-ops-mcp/linux_ops_mcp/atlas_hml_local_probe.py: a CLI explicita, apenas manual, usa modo metadata-only ao executar sob conta de menor privilegio, sem chamar Git do checkout. O objeto responde git_observation_method="filesystem_head_only_untrusted" e git_clean_nonignored=null, informa bloqueios HML_GIT_METADATA_ONLY_UNTRUSTED e HML_GIT_STATUS_NOT_CHECKED. Se refs/symlinks/permissoes forem inseguros ou main estiver ausente, responde codigo finito HML_GIT_METADATA_UNAVAILABLE, sem caminhos, conteudos ou stack trace.
3. linux-ops-mcp/tests/test_atlas_hml_git_head_peek.py: exercita Git temporario real so na preparacao dos fixtures (nao no leitor), refs loose/packed, branch diferente, detached, symlinks, bytes e SHA malformados, races, hooks e configuracoes suspeitas nao executadas, conta privilegiada recusada e CLI sem Git. CI ATLAS incorpora a suite e CI Linux MCP continua executando todos os testes.

## Invariantes e limites

- O diretorio Git e group-writable e, portanto, os bytes de HEAD e refs podem ser trocados por pessoa no grupo com escrita. Eles devem ser tratados como **diagnostico nao confiavel**, nunca como atestacao, permissao de deploy ou evidencia de OCI, CI ou Docker. HEAD nao prova revisao de container em execucao.
- Este leitor NAO observa arquivos alterados, status limpo/sujo, ignored/untracked, origem remota, commit object, assinatura, consistencia transacional, dono do checkout, transporte, mTLS, Keycloak S2S, consentimento Core, nonce, backup ou rollback. Todos esses controles continuam pendentes.
- status="blocked", checkout_integrity_attested=false, collector_identity_attested=false, prepare_eligible=false, can_execute=false. PREPARE e ACT continuam OFF.
- Sem API, rota MCP, daemon, novo socket, credencial, provisionamento de identidade, grant DB/Core, migration ou deploy.
- O caminho de status Git completo (GitCheckoutReadOnlyObserver) permanece disponivel como biblioteca para fontes controladas e testes isolados, mas **nao e invocado pelo CLI contra o checkout compartilhado**.

## Comando seguro de avaliacao apos merge, somente leitura

    cd /home/operador/projetos/delpi-central
    git pull --ff-only
    sudo -u atlas-hml env PYTHONPATH=/home/operador/projetos/delpi-central/linux-ops-mcp /opt/atlas-hml/venv/bin/python -B -m linux_ops_mcp.atlas_hml_local_probe

O pull requer administracao normal do repositorio pelo operador; a CLI nao modifica o host. No segundo comando nao ha sudo dentro do processo atlas-hml e nao ha excecao Git safe.directory. Resultado esperado: SHA HEAD local sob main, status de limpeza desconhecido e Docker indisponivel se o proxy nao estiver instalado. A saida sempre permanecera BLOCKED. Os testes nao substituem revisao independente delpi-verifier e aprovacao humana.

## Proxima fase dependente de mudanca aprovada

Revisar PR do proxy UNIX HML com menor privilegio e SO_PEERCRED, ainda sem instalar servico. Para avancar de metadados de HEAD para identidade atestada, e preciso fonte de snapshot imutavel e assinada, vinculacao a ImageID/CI, contrato de rollback/restauracao e aprovacao explicita do owner. Nao tratar um SHA encontrado em .git como prova de revisao em producao.
