# ATLAS | P2.2h.2j: comprovante assinado de host v2, com identidade Docker completa

**Data:** 16/11/2026. **Estado:** em Pull Request para revisão. **PREPARE_DISABLED / ACT_DISABLED.**

## Objetivo

As PRs #209 a #211 disponibilizaram a verificação da proveniência da release OCI, o read-back do ImageID via GHCR e a correlação de ambos. A etapa seguinte exige dados atuais do **host de execução**, sem presumir que a imagem assinada já está rodando nem confiar em uma transcrição fornecida por usuário/MCP.

O comprovante `SignedHostReceipt` v1 já protegia commit, ImageID, host, ambiente, serviço, saúde, momento e challenge por HMAC; porém não assinava `container_name` nem `compose_project`. O formato v2 fecha essa lacuna por contrato.

## Implementação

O novo módulo backend-only `linux-ops-mcp/linux_ops_mcp/deploy_host_runtime_v2.py` expõe duas funções privadas para o fluxo futuro:

1. `issue_host_runtime_receipt_v2`: reutiliza o signer v1, que verifica um `SignedReleaseRecord` autenticado separadamente e um resultado Docker GET restrito ao contêiner e labels exigidos; acrescenta `container_name` e `compose_project` do `RuntimeTarget` validado e assina um **novo corpo JSON versão 2**.
2. A chave de assinatura é exclusiva do host e diferente da chave do release record, já exigida pelo signer anterior. O MAC usa domínio `atlas:host-runtime-receipt:v2\x00`, separado da assinatura do v1, para impedir que comprovantes de versões distintas sejam confundidos. A função não cria chaves nem configura transporte.
3. `verify_host_runtime_receipt_v2`: exige uma configuração de target `RuntimeTarget` **server-owned** e um challenge recebido de fonte confiável, valida MAC em comparação constante, conjunto exato de campos, tipos estritos e data UTC. Rejeita repo/host/env/serviço/projeto/nome de contêiner/challenge diferentes, ImageIDs incompatíveis e evidência com mais de 90 segundos ou adiantada mais de 5 segundos.
4. Resultado `VerifiedHostRuntimeSnapshot`: contém commit já publicado como release record, ImageID efetivamente observado, ID de contêiner, saúde, timestamp, hash SHA-256 de **bytes do challenge** e digest SHA-256 do comprovante, sem expor a chave ou o challenge original. `signature_verified=True` indica apenas que o MAC local foi verificado e `challenge_bound=True` que corresponde ao nonce esperado, **não** que o nonce foi consumido no banco.
5. Preserva a capacidade de verificar v1 para consumidores existentes; o v2 recusa o comprovante v1, inclusive se alguém calcular manualmente MAC no domínio novo, porque o contrato de campos/versionamento é diferente.
6. Nenhuma dessas funções vira ferramenta MCP, rota FastAPI, serviço contínuo, comando de shell, montagens Docker no serviço ChatGPT ou executor de implantação.

## Segurança e limites inegociáveis

- O signer Docker atual não mede o estado do git checkout. Por isso ele **sempre assina `checkout_clean=False`**. O v2 adicionalmente rejeita qualquer comprovante que afirme `checkout_clean=True`, mesmo com um MAC válido, pois isso seria um fato sem observação correspondente.
- Um registro executor de release assinado por HMAC não é substituto de proveniência CI, aprovação humana, recuperação de backup, migrações ou rollback. `VerifiedHostRuntimeSnapshot` mantém `migrations_safe=False`, `rollback_ready=False` e `challenge_consumed=False` permanentemente nesta etapa.
- O token/chave HMAC e a escolha do target pertencem ao backend e ao processo host independente. Se forem fornecidos pelo browser/MCP, a verificação deixa de ser uma autoridade confiável. A leitura via Docker socket tem privilégio elevado; nenhum socket é exposto pelo incremento.
- O nonce ainda precisa ser emitido e consumido por uma transação no journal PostgreSQL para prevenir replay; este módulo não faz writes.
- O ID do contêiner Docker/Imagem não é equivalente à comprovação da integridade do sistema operacional. Não existem endpoints PREPARE/ACT para utilizar a prova.

## Testes

- `linux-ops-mcp/tests/test_deploy_host_runtime_v2.py`: emissão e verificação offline com inspector e release record falsos; negações de alteração de MAC/nonce, drift de ambiente/projeto/contêiner, campos JSON duplicados ou faltantes, tempos inválidos, imagens divergentes, checkout indevidamente marcado como íntegro, replay de v1 e inspeção falha.
- `linux-ops-mcp/tests/test_atlas_docker_engine_ci.py`: acrescenta comprovante v2 baseado em Docker Engine GET real de **contêiner piloto efêmero** do GitHub Actions. O teste continua `skip` fora de `GITHUB_ACTIONS=true` e `ATLAS_DISPOSABLE_DOCKER=true`.
- `.github/workflows/atlas-p22e-integration.yml`: eventos PR/push ativados pelos novos arquivos; job `Real Docker read-only inspection, ephemeral only` executa teste unitário e smoke Docker real sem acessar servidor PROD.
- CI não equivale a auditoria independente: executar `delpi-verifier` por agente diferente e revisão humana antes do merge, conforme contrato do repositório.

## Gates para a P2.2h.2k

- [ ] CI 5/5 checks aprovado em branch/PR e documentação de resultado.
- [ ] `delpi-verifier` independente por agente separado (não comprovado nesta sessão).
- [ ] Teste com host em HML que use proxy Docker estritamente só de leitura e segredos armazenados fora do Git e do chat; identidade do `RuntimeTarget` fixada no backend.
- [ ] Evidência independente e segura de workspace limpo, migrações/backup e rollback antes de qualquer sinal de elegibilidade PREPARE.
- [ ] Correlacionar `VerifiedHostRuntimeSnapshot` ao journal challenge e à release OCI, com identidade humana Core e writer DB de privilégio mínimo, sempre com flags desligadas até aprovação do owner.
- [ ] Proibir ACT por default e manter scripts atuais de pull/deploy manual intactos.

**Próximo incremento recomendado:** demonstrar o bloqueio fail-closed entre o comprovante host v2 e uma solicitação OCI, sem endpoint, até existir prova independente dos gates de checkout/rollback.

