# ATLAS P2.2c | Prova assinada do host e idempotencia PREPARE

**Data:** 2026-11-15. **Status:** implementacao offline e testes; nao conectado ao MCP, ao host real ou ao PostgreSQL. Nada instalado em PROD/HML.

## Problema e solucao em codigo

O SHA do checkout em Git nao equivale ao SHA realmente implantado nos containers. Para nao aceitar declaracoes do ChatGPT como evidencia do host, foi criado o verificador `linux-ops-mcp/linux_ops_mcp/deploy_host_receipt.py`. Ele nao le Docker nem executa comandos: so **valida** um comprovante de runtime que **um futuro emissor confiavel separado no host** tera de produzir. Compara repo, host, ambiente, servico, commit, registro de release e imagem observada no container com assinatura HMAC-SHA256 vinculada ao challenge backend.

O contrato exige:
- chave HMAC secreta de pelo menos 32 bytes fornecida em secret store, nunca no Git ou ferramenta MCP;
- `host_id`, `repository=roberiooliveiradev/delpi-central`, `environment=hml|prod`, `service_id` allowlisted e `commit_sha` de 40 hex;
- `release_image_id` e `running_image_id` com o mesmo `sha256:64hex`, `container_id` 64 hex, `running`, `healthy`, `checkout_clean` booleanos;
- `observed_at` UTC (ate 90 s de atraso, no maximo 5 s no futuro); `challenge` backend de 256 bits, diferente por operacao;
- JSON de ate 2 KiB, sem campos extras/duplicados, assinatura HMAC verificada com `hmac.compare_digest`; erro sempre em codigo sem payload/segredo.

**Limites de seguranca:** assinatura so autentica o **emissor**, nao demonstra por si que ele consultou a imagem Docker correta nem que a imagem foi construida do SHA declarado. Essas provas dependem da implantacao futura de um emissor isolado, de registro de release imutavel e da verificacao de provenance de CI. O backend tambem precisara gerar e **consumir uma vez** o challenge em journal transacional; este verificador ainda nao implementa anti-replay persistente nem oferece endpoint. Sem emissor instalado, a prova real continua **indisponivel**.

Mesmo quando HMAC e IDs sao validos, `HostProof` **forca** `migrations_safe=False` e `rollback_ready=False`. Evidencia de runtime **nao autoriza** migracoes, rollback ou deploy; esses gates exigem fontes independentes e sao bloqueantes no P2.1/P2.2a.

## Journal de preparacao, candidato ainda sem DB

Foi criado `linux-ops-mcp/linux_ops_mcp/deploy_journal_policy.py`, com `decide_prepare_insert` puro. Ele valida `request_id` UUIDv4, `requester_subject` UUIDv4, `environment`, `service_id`, `target_sha`, `base_sha` diferentes, `proposal_hash` SHA-256, UTC e TTL de no maximo 10 minutos, estado unico `pending_approval`. Retorna:
- `create_candidate`: possivel primeira insercao, **somente depois** dos demais gates e do lock DB;
- `replay_pending`: mesma identidade, request e payload identicos; nao gravar outro pedido;
- `conflict`: request igual com SHA/hash/payload divergentes;
- `blocked`: autor, tempo, estado ou formato invalido.

**Nao e banco transacional implementado.** Precisaremos de `UNIQUE(requester_subject, request_id)`, bloqueios de concorrencia, eventos auditados na mesma transacao e validacao de Core/CI/release **antes** de gravar. O desenho das tabelas esta em [03-atlas-deploy-journal-p2b.md](./03-atlas-deploy-journal-p2b.md). Nenhuma migration V016 foi criada, evitando aplicacao incidental em `it-portal-api` enquanto Delpi Remote evolui em paralelo.

## Evidencias desta etapa

- `linux-ops-mcp/tests/test_deploy_host_receipt.py`: **30 PASS** offline.
- `linux-ops-mcp/tests/test_deploy_journal_policy.py`: **17 PASS** offline.
- Total **47 PASS** com Python 3.13/pytest, sem conexao ao GitHub/Core/DB/Docker; compilacao Python OK. Os quatro arquivos foram publicados na main e comparados com os arquivos testados pelo hash de conteudo. **GitHub CI e revisao independente ainda pendentes**; nenhuma chamada real MCP de deploy foi realizada.
- O `linux-ops-mcp/linux_ops_mcp/server.py` continua com quatro tools READ. Sem instalacao de signer, segredo, journal PostgreSQL, endpoint PREPARE, aprovacao, executor, tool ACT ou deploy.

## Proximo gate P2.2d

1. Escolher um servico piloto HML e formalizar allowlist, labels/release record, verificacao da imagem em execucao e ownership de credenciais.
2. Implementar emissor host read-only **separado** do MCP, com Docker introspection estritamente limitada, canal autentico e tests negativos em HML. Gerar provas reais somente depois de aprovar o host signer; nunca passar secrets ao ChatGPT.
3. Coordenar numeracao e ownership da migration com Portal TI/Delpi Remote, implementar journal PostgreSQL com testes reais de idempotencia/concorrencia e challenge one-shot.
4. Adicionar gates independentes de migration/rollback/CI e grants Core; somente depois considerar expor PREPARE. A3/A4 e ACT permanecem bloqueados.

**Estado:** `P2.2C_CODE_OFFLINE_TESTED` / `HOST_PRODUCER_NOT_IMPLEMENTED` / `JOURNAL_PERSISTENCE_NOT_IMPLEMENTED` / `PROD_UNCHANGED`.
