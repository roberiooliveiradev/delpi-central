# ATLAS P2.2d — Host signer isolado e journal PostgreSQL inerte

> **Data:** 2026-11-15
> **Estado:** CODIGO TESTADO LOCALMENTE E PUBLICADO NA MAIN. **HML E PROD NAO ALTERADOS.**
> **Objetivo:** estabelecer a cadeia de evidencias para a revisao *real* do container e a base transacional de propostas de deploy, sem disponibilizar ACT ou PREPARE no MCP publico.

## 1. O que foi efetivamente desenvolvido

| Arquivo | Responsabilidade | Estado |
|---|---|---|
| \`linux-ops-mcp/linux_ops_mcp/deploy_host_source.py\` | Interface estreita \`GET /containers/{nome}/json\` via transporte Docker injetado; valida o nome configurado, labels de service/project, ID de imagem e status de saude | CODIGO / NAO CONFIGURADO NO HOST |
| \`linux-ops-mcp/linux_ops_mcp/deploy_host_signer.py\` | Confere MAC de **registro de release emitido pelo futuro executor**; compara imagem registrada e imagem em execucao; emite o \`SignedHostReceipt\` existente com outra chave e challenge | CODIGO / SEM SIGNER OU CHAVES REAIS |
| \`it-portal-api/it_portal_app/infrastructure/persistence/atlas_deploy_journal.py\` | \`issue_challenge\` e \`store_prepared\` com transacao PostgreSQL, nonce aleatorio, hash armazenado, unicidade de pedido e evento atomico | CODIGO / SEM TABELAS OU ROTAS ATIVAS |
| [05-atlas-p22d-candidate-schema.sql](./05-atlas-p22d-candidate-schema.sql) | DDL candidato de \`atlas_deploy_challenges\`, \`atlas_deploy_proposals\`, \`atlas_deploy_events\` | DOCUMENTO PARA REVIEW, **FORA DA PASTA DE MIGRATIONS** |
| \`linux-ops-mcp/tests/test_deploy_host_source_signer.py\` | Testes HTTP mockado, HMAC, binding do container, imagem divergente e estado de saude | 17 PASS |
| \`it-portal-api/tests/test_atlas_deploy_journal.py\` | Testes de politica SQL com banco simulado: create/replay/conflict, nonce one-shot e rollback atomico | 15 PASS |
| \`it-portal-api/tests/test_atlas_schema_draft.py\` | Testes estaticos do DDL proposto | 3 PASS |

**Regressao local combinada:** \`190 passed\` em Python 3.13/pytest 9, executada com pacotes locais dos incrementos P2.1/P2.2a/b/c e os arquivos P2.2d; \`python -m compileall\` sem erro. **Os testes de banco usam um FakePg**, nao PostgreSQL real; os testes do Docker usam \`httpx.MockTransport\`, nao engine real. Portanto, essas contagens **nao** sao smoke de HML e nao provam que as fontes externas estejam configuradas.

Os seis arquivos de codigo, testes e SQL (exceto teste estatico novo) foram comparados por hash FNV de seus bytes/texto publicados na \`main\` com os arquivos testados localmente. O novo teste estatico reproduz os mesmos assertions sobre o caminho do SQL na estrutura do repositorio.

## 2. Cadeia de confianca de revisao

1. **Executor futuro** prepara registro de release para um \`execution_id\` UUIDv4, \`commit_sha\` 40hex, \`image_id\` sha256, host/ambiente/servico e repositorio canônicos, assinando com chave exclusiva de *release*. Esse executor **nao existe ainda**; nenhum registro autentico foi criado.
2. **Leitor local isolado** inspecionara somente container cujo nome e labels pertençam a catalogo definido pelo backend. Ele nao recebe shell/path/URL do ChatGPT. No codigo atual, o \`DockerReadOnlyInspect\` recebe um \`httpx.AsyncBaseTransport\` injetado: **nao existe socket aberto por default**.
3. **Signatario local futuro** valida registro HMAC do executor, compara o \`image_id\` assinado ao \`Image\` do container observado e assina uma prova com **outra chave** em um nonce de 256 bits fornecido pelo backend. Se imagem, identificador ou meta do target divergirem, **nega**.
4. **Backend futuro** verifica \`SignedHostReceipt\` existente, consome nonce exatamente uma vez na transacao do journal e cruza os outros gates Core/CI/saude/migrations/rollback de P2.2a. **Assinatura por si so nao autoriza deploy**.
5. **P2.1** permanece deny-by-default. O comprovante emitido pelo host propositalmente informa \`checkout_clean=False\` (Docker nao comprova arvore Git), e a verificacao posterior continua forçando \`migrations_safe=False\` e \`rollback_ready=False\`. Uma prova valida nao habilita PREPARE por acidente.

**Limites de privilégio:** o Docker daemon socket equivale a controle elevado sobre host, mesmo com codigo que so faz GET. **Proibido montar o socket no MCP ChatGPT ou usar este script como wrapper de comandos**. Implantacao futura requer um proxy Docker de leitura e escopo estrito (ou API interna de inventario que emita apenas IDs/estado), identity isolada, segredo protegido e review de seguranca. O retorno bruto do \`inspect\` pode conter variaveis de ambiente; a aplicacao descarta tudo menos \`Id\`, \`Image\`, \`Name\`, \`State\` e duas labels, sem logar o body.

## 3. Journal: atomicidade proposta, nao aplicada em producao

- \`issue_challenge\`: somente backend autenticado pode chamar; gera \`secrets.token_hex(32)\`, grava SHA-256 do nonce em \`atlas_deploy_challenges\`, com TTL de 90 segundos usando o relogio do banco e transacao.
- \`store_prepared\`: somente apos attestation e policy independentes; valida UUIDv4, ambiente, servico, hashes e SHA. Insere proposta \`pending_approval\` com UNIQUE \`(requester_subject,request_id)\`. **Na mesma transacao**, consome nonce ainda valido e nao consumido e grava evento \`prepared\`.
- Reenvio da mesma solicitacao retorna o mesmo \`proposal_id\` **apenas se SHA, base, servico, hash e nonce coincidirem**; nao consome outro desafio nem duplica evento. Conflito de payload, nonce vencido, faltante ou reutilizado gera bloqueio. Erro de SQL torna-se codigo seguro, sem mostrar connection strings ou secrets.
- A proposta SQL adiciona FK do digest da proposta para o challenge, UNIQUE do digest, TTL maximo, bloqueio de duas execucoes simultaneas do mesmo target e auditoria append-only na perspectiva da aplicacao. Os privilegios de DB devem negar UPDATE/DELETE em eventos.
- **Sem migration aplicada**: o DDL ficou em \`docs/.../05-atlas-p22d-candidate-schema.sql\`, NAO em \`it-portal-api/migrations/\`. O runner existente pode aplicar migrations automaticamente se habilitado; por isso a numeracao e ownership devem ser coordenados com o roadmap Delpi Remote antes de criar V016+.

**Atenção de integracao:** a API ainda nao possui rotas PREPARE, aprovacoes, Core grants \`linux_ops.deploy.*\`, schema aplicado ou catalogo produtivo. O novo modulo \`atlas_deploy_journal.py\` **nao e importado por nenhuma rota**. O journal nao recebe evidencia de release independente nem proof provider real ainda. O usuario superadmin nao elimina o gate de aprovacao.

## 4. Verificacoes para concluir o gate P2.2d em HML

- [x] Implementar leitor de metadados Docker por GET com target fixo e erros sanitizados.
- [x] Implementar registro de release assinado + comprovante host separado, com chaves distintas, challenge e comparacao de ID da imagem.
- [x] Implementar adaptador SQL de PREPARE com transacao, nonce one-shot, idempotencia e evento.
- [x] Produzir DDL candidato fora do runner automatico.
- [x] Executar suite offline e validar bytes publicados na \`main\`.
- [ ] Aprovar catalogo de **um** container HML, projeto Compose e health-check, sem supor nomes de runtime.
- [ ] Review independente \`delpi-verifier\` conforme AGENTS.md e CI GitHub da \`main\`.
- [ ] Provar restricao read-only do inspector por proxy/ACL isolada, **sem** Docker socket ao MCP.
- [ ] Configurar chaves em secret store, produtor imutavel do release record e canal de challenge com binding por proposta.
- [ ] Validar DDL e concorrencia/idempotencia com **PostgreSQL real descartavel**, antes de versionar migration.
- [ ] Coordenar numero de migration e testar rollback/upgrade em HML, sem migrations incidentais em PROD.
- [ ] Integrar somente backend privado, com Core grants explicitos e refresh de permissao; nao publicar ACT.

## 5. Proxima frente: P2.2e

**Objetivo:** homologar as tres fontes reais (GitHub/CI, Core, release do container) e o journal PostgreSQL com concorrencia, **em ambiente HML**, num unico alvo aprovado. Depois podera existir uma ferramenta \`preview_deployment\` de PREPARE **sem ACT**, sujeito a novo code review de autorizacao. Ainda nao ha permissao para execucao real de deploy via ChatGPT.

**Estado final desta entrega:** \`P2.2D_CODE_MAIN_OFFLINE_PASS\`, \`HOST_SIGNER_RUNTIME_NOT_INSTALLED\`, \`JOURNAL_DB_NOT_APPLIED\`, \`MCP_TOOLS_FOUR_READ_ONLY\`, \`HML_NOT_EXECUTED\`, \`PROD_UNCHANGED\`.


## 6. Validacao local real no srv-api - P2.2d (2026-11-15)

**Evidencia informada pelo operador:** apos `git pull` e criacao de ambiente virtual temporario, executou a suite seletiva em `srv-api` com `PYTHONPATH="$PWD/linux-ops-mcp:$PWD/it-portal-api" PYTHONDONTWRITEBYTECODE=1 "$VENV/bin/python" -m pytest -q -p no:cacheprovider linux-ops-mcp/tests/test_deploy_host_source_signer.py it-portal-api/tests/test_atlas_deploy_journal.py it-portal-api/tests/test_atlas_schema_draft.py`. A primeira tentativa falhou ainda na coleta de testes por `ModuleNotFoundError: No module named 'fastapi'` importado pelo `it-portal-api/tests/conftest.py`; o usuario instalou as dependencias de `it-portal-api/requirements.txt` e o pacote `./shared` **somente no venv**. Nova execucao resultou em **35 testes aprovados, 100%, nenhuma falha**, usando Python **3.12** (evidenciado pelo caminho de `site-packages`).

**Warnings nao bloqueantes:** `StarletteDeprecationWarning` sobre `httpx` / `starlette.testclient`; `FastAPIDeprecationWarning` sobre argumento `root_path` de `it_portal_app.main`. Nao fazer mudanca de dependencia produtiva apenas para suprimir warnings.

**Classificacao:** `P22D_SRV_API_TESTS_LOCAL_PASSED`. Isto demonstra testes **mockados em ambiente isolado rodando sobre a maquina srv-api**, nao validacao do Docker real, PostgreSQL real, release signer instalado, API PREPARE publicada, migration aplicada ou deploy. `P22D_HML_REAL_SOURCES=NOT_VERIFIED`, `P22D_PROD_MUTATIONS=NONE_REPORTED`.

**Proximo passo seguro para o operador:** validar `docker ps --format '{{.Names}} {{.Status}}'` limitado a `linux-ops-mcp`/`it-portal-api` e chamadas HTTP sem credenciais para metadata OAuth (200) e recurso MCP sem bearer (401); nao executar `up-prod-sequential.sh`, migration, `docker exec` de escrita ou montar docker.sock no MCP nesta fase.
