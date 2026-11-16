# ATLAS | P2.2h.2m–2o: pacote integrado de evidencias Git + host Docker + nonce

**Data:** 16/11/2026. **Status:** em Pull Request, revisão e validações pendentes.
**Execução:** PREPARE_DISABLED / ACT_DISABLED, nenhum deploy de produção.

## Resultado esperado em uma única entrega

Reduzir a fragmentação entre o observador Git da PR #214, o comprovante Docker v2 da PR #212 e o preflight OCI da PR #213. Este pacote implementa, testa e documenta três contratos conectados:

1. **P2.2h.2m, emissão:** issue_git_checkout_witness executa GitCheckoutReadOnlyObserver.read no host aprovado e assina o estado exato de Git (HEAD, branch, arquivos tracked/untracked não ignorados, timestamp), identificando host/env/service/container/Compose e nonce. Não aceita observação sem tipo correto, stale ou supostamente autorizada; não gera chaves nem inicia processo.
2. **P2.2h.2n, verificação:** verify_git_checkout_witness valida HMAC com domínio separado (atlas:git-checkout-observation:v1), JSON com campos únicos e tipos estritos, SHA, alvo e nonce exatos, timestamp UTC com prazo de 90s/tolerância de 5s. Rejeita replay com outro nonce, assinatura adulterada e troca de identidade. Retorna apenas VerifiedGitCheckoutWitness, com checkout_trust_approved=False, challenge_consumed=False, rollback_ready=False e prepare_eligible=False.
3. **P2.2h.2o, correlação:** inspect_signed_host_checkout_bundle revalida **os bytes de ambas assinaturas** por caminhos independentes: inspect_host_oci_preflight_v2 para Docker/intent e verify_git_checkout_witness para checkout. Exige duas chaves diferentes, challenge igual aos hashes calculados como SHA256(bytes.fromhex(nonce)), target canônico e timestamps com diferença máxima de 15 segundos. Expõe diagnóstico de divergência de HEAD versus commit Docker/base, checkout sujo, branch diferente da main e leituras afastadas, sem abrir elegibilidade.

## Arquivos e limites

- linux-ops-mcp/linux_ops_mcp/deploy_git_checkout_witness.py: assinatura e validação da observação. Um token HMAC não autentica o SO ou processo emissor por si só.
- linux-ops-mcp/linux_ops_mcp/deploy_host_checkout_evidence_bundle.py: verificador agregado, somente diagnóstico, sempre bloqueado.
- linux-ops-mcp/tests/test_deploy_host_checkout_evidence_bundle.py: repositórios Git descartáveis, Docker simulado, receipt v2 verdadeiro e chaves sintéticas. Cobre replay, adulteração, troca de chave, troca de host, schema inesperado, branch/checkout sujos, commit incoerente, freshness e assinatura valida com bloqueio.
- .github/workflows/atlas-p22e-integration.yml: adiciona esses testes ao job Docker descartável, sem host PROD. Todos os comandos de escrita Git em testes ocorrem exclusivamente no tmp_path.

## Segurança e o que a entrega NÃO faz

- O repositório local e a configuração Git podem sofrer interferência, inclusive em arquivos ignorados. O checkout Git é **observado, mas não atestado como fonte operacional independente**. A inspeção de arquivos é não atômica. A assinatura HMAC apenas detecta adulteração do conteúdo transmitido depois de emitido. Nunca elevar checkout_clean de um HostProof para True a partir dessa assinatura isolada.
- O nonce precisa ser emitido por autoridade confiável e consumido no PostgreSQL com transação one-shot na futura operação de PREPARE. Esta entrega não lê nem escreve o journal; as assinaturas por si não evitam replay caso a autoridade reemita/aceite o mesmo nonce.
- CI release e GHCR precisam de autenticação real pelos leitores do it-portal-api, ainda não conectados a esta execução. Nenhum DTO construído por cliente é prova criptográfica válida; target, chaves e nonce são fornecidos exclusivamente por processo backend confiável. Não permitir que HTTP/MCP selecione observer ou path.
- Continua sem comprovação de backup/rollback, migrations safe, grants Core humanos e proteção completa contra race conditions. O relatório retorna **sempre status=blocked**; PREPARE e ACT não são implementados/ligados.
- Não altera Docker Compose, scripts de deploy, Keycloak, segredos produtivos, migrations, rotas, serviços ou banco. Deploy manual de outros colaboradores intocado.

## Aceite antes de merge

- [ ] Cinco checks GitHub Actions aprovados (Docker com testes novos, PostgreSQL descartável, auditoria, arquitetura, contrato read-only).
- [ ] Revisão independente delpi-verifier executada por outro agente, com evidência de veredito; a CI não substitui isso.
- [ ] Revisão humana de HMAC, segregação de chaves e tratamento de witness não atestado.
- [ ] Ensaio controlado de leitura e assinatura em HML com serviço/usuário de privilégio mínimo e chaves fora do Git/chat, após autorização operacional.
- [ ] Comprovação real e independente de rollback/migrations/Core e de emissão/consumo de challenge no journal antes de qualquer autorização PREPARE.

**Próximo pacote, após condições de operação definidas:** prova de identidade do coletor host e attestation read-back, correlação backend com OCI e journal read-only, testes em HML, então preparar uma API PREPARE default-off com RBAC e writer estrito. ACT permanece em uma fase futura separada com aprovação operacional explícita.
