# ATLAS — Objetivo final e contrato de deploy controlado (P2–P4)

> **Atualizado:** 2026-11-15
> **Owner:** TI DELPI / Minha DELPI
> **Estado atualizado 2026-11-15:** contrato P2 documentado; codigo P2.1 offline integrado na main por [PR #191](https://github.com/roberiooliveiradev/delpi-central/pull/191) (CI verde); P2.2a/P2.2b e P2.2c (recibo do host + idempotencia offline) versionados na main, testes locais PASS, CI e verificador independente pendentes; **nenhum PREPARE/ACT implantado, nenhuma tool nova no MCP**.
> **Fontes relacionadas:** [roadmap e evidências](./01-discovery-architecture-and-security-roadmap.md), `linux-ops-mcp/`, `infra/scripts/up-prod-sequential.sh`, `infra/scripts/up-hml-sequential.sh`, `.cursor/rules/local-first-deploy.mdc`, `.cursor/rules/platform-delivery-runtime-operations.mdc`.
> **Restrição de custo:** priorizar GitHub/Keycloak/Core/IT Portal, host, containers e homologação existentes. Não pressupor túnel ou runner pago.
> **Congelado por decisão do operador:** ampliação de telemetria CPU, contagem Docker e outros observáveis Linux; não é pré-requisito desta entrega. Atestação de revisão/health **de deploy** é requisito novo e separado.

## 1. Resultado final que o usuário deverá obter

Pedido conversacional alvo:

> "ATLAS, o código de `it-portal-api` já está no GitHub. Identifique o commit, verifique o que mudou, prepare um deploy seguro e, após minha aprovação, publique e valide."

Resultado esperado: ATLAS identifica **serviço e commit exatos**, compara com revisão efetivamente implantada, verifica autorização, CI, risco, migrações, dependências e saúde; apresenta uma proposta imutável para aprovação **fora da conversa** no portal DELPI; uma vez autorizada, um executor independente aplica somente o alvo autorizado e devolve evidência do resultado. Sem confirmação externa, a operação **não** inicia.

O ATLAS de hoje comprova OAuth + consultas READ; não possui ferramentas de PREPARE/ACT. O plugin GitHub utilizado na conversa pode apoiar análise de código, mas **não concede automaticamente acesso do ATLAS ao repositório**, nem substitui verificação no backend.

## 2. Fronteiras e componentes

```text
Usuário no ChatGPT ─── GitHub plugin (análise da revisão)
       │
       └── ATLAS MCP (OAuth humano; sem shell/socket Docker)
                │
                ├── PREVIEW/STATUS → Deploy policy API (permissões e evidências)
                └── REQUEST/ACT ───> Deploy policy API (journal + aprovação)
                                          │
                                          │ somente proposal aprovado/selado
                                          v
                               Executor Linux local isolado
                               (allowlist, lock, hash, timeouts)
                                          │
                                          v
                              Git SHA imutável + script canônico
                               + health por serviço + read-back
```

- **ATLAS MCP:** identifica o usuário e apresenta ferramentas tipadas; não recebe `/var/run/docker.sock`, credencial de GitHub com escrita, SSH, sudo, host mounts ou argumento `command`.
- **Policy API:** extensão governada de backend DELPI existente, usando Keycloak/Core e persistência/auditoria transacional existente; separa poderes de visualizar, preparar, aprovar e executar. Escolha definitiva do módulo dono depende de inventário no código, sem criar infraestrutura paralela.
- **Aprovação nominativa:** UI autenticada da Minha DELPI (ou mecanismo corporativo já existente, após inventário). Confirmação em ChatGPT **não** autoriza por si só um deploy. Aprovação guarda subject, proposal hash, alvo, SHA, validade, riscos e timestamp.
- **Executor host:** processo separado, não exposto em HTTP público, com interface de operações finitas. É o único componente autorizado a invocar Git/Compose; privilégios Docker equivalem a privilégios altos no host, portanto isolamento e auditoria são obrigatórios. Preferir canal privado de consulta a jobs aprovados ou socket Unix restrito, a decidir após inventário da operação local.
- **GitHub:** fonte de commit, CI e artefatos. Verificações do broker devem ser independentes da narrativa do modelo e de campos editáveis de PR/issue. Nunca instalar runner self-hosted privilegiado conectado a este repositório público.

## 3. Contratos MCP propostos (não publicados)

| Tool | Classificação | Entrada estritamente tipada | Efeito |
|---|---|---|---|
| `list_deployable_targets` | READ | `environment` = `hml` ou `prod` | Lista somente os serviços previamente autorizados e respectivos checks |
| `preview_deployment` | PREPARE sem mutação de produção | `environment`, `service_id`, `commit_sha` de 40 hex | Retorna diff/CI/preflight/risco e bloqueios, **sem deploy** |
| `request_deployment_approval` | PREPARE | `preview_id` | Persiste proposta selada `PENDING_APPROVAL`; UI corporativa coleta autorização |
| `deploy_approved_revision` | ACT | `proposal_id` opaco somente | Executa apenas proposta ainda aprovada, íntegra e vigente; nunca aceita shell/path/serviço/SHA como override |
| `get_deployment_status` | READ | `proposal_id` | Estado, versão real, etapas e erros **sanitizados** |
| `preview_rollback` | PREPARE | `deployment_id` | Só oferece revisão anterior se compatibilidade e restauração forem seguras |
| `execute_approved_rollback` | ACT | `rollback_proposal_id` | Fluxo separado de autorização e auditoria; não é botão irrestrito |

`get_deployment_revision` existente passa a ser requisito de identificação do alvo, **sem inventar SHA** a partir do HEAD do GitHub. Enquanto não houver origem local atestada da revisão implantada, `preview_deployment` retorna `BLOCKED_REVISION_UNVERIFIED` para produção. Nenhuma tool existente é reclassificada como mutação.

## 4. Proposta selada e máquina de estados

Campos mínimos persistidos, jamais aceitos como verdade apenas do ChatGPT:

- `proposal_id`, `requester_subject`, `environment`, `service_id` (enum derivado do catálogo governado), `commit_sha` imutável, `base_deployed_revision`, `ci_evidence`, `change_class`, `impact`, `migration_gate`, `health_contract`, `rollback_plan`.
- `canonical_payload_hash` SHA-256 do payload normalizado, `expires_at` curto (alvo: 10 min), `idempotency_key`, `approval_subject(s)`, `approved_at`, `execution_id`, `result_revision`, `verified_at`.
- Metadados públicos/sanitizados apenas nas respostas do MCP; credenciais, variáveis de ambiente e saída integral de comando nunca entram no journal/modelo.

```text
DRAFT -> PREPARED -> PENDING_APPROVAL -> APPROVED -> EXECUTING
          |                   |             |           |
          v                   v             v           +--> VERIFIED
        BLOCKED             EXPIRED       REVOKED        +--> FAILED_NEEDS_OPERATOR
                                                         +--> ROLLED_BACK (somente quando seguro)
```

Qualquer revogação de permissão, divergência de SHA, alteração do plano, dupla execução, expiração ou falta de saúde **invalida** a proposta. Transições devem ser atômicas e exclusivas por serviço/ambiente. Se ocorrer timeout de resposta, a consulta de status precede qualquer reenvio para evitar deploy duplicado.

## 5. Autorização independente da interface

- Reusar OAuth humano existente do ATLAS (`mcp-linux-ops`), `iss`, `aud` MCP exata e `mcp:tools`; esse scope só habilita o transporte.
- Propor permissões Core distintas: `linux_ops.deploy.view`, `linux_ops.deploy.prepare`, `linux_ops.deploy.approve`, `linux_ops.deploy.execute`. Código exato/cadastro dependem do catálogo de permissões existente.
- `ACT` exige reconsulta Core fresca, usuário humano, approval backend, segregação de funções conforme criticidade, janelas operacionais e lista de serviços autorizados. Status de superadmin **não equivale** a consentimento para qualquer serviço.
- `prod`: no mínimo aprovação nominativa fora do ChatGPT; segunda aprovação para alvos críticos ou migração de alto risco. `hml`: aprovação nominativa simplificada ainda preserva o gate.
- Guardas de backend não podem depender de `readOnlyHint`/`destructiveHint`, prompts ou prévia escrita por LLM.
- Auditoria imutável na perspectiva do usuário MCP, com subject, hash, versão, ação, timestamps, result, sem bearer/secret.

## 6. Política Git/CI e implantação sem terminal livre

- Só aceitar `commit_sha` completo, publicamente verificável e alcançável de uma referência aprovada do repositório canônico. Branch, tag mutável ou `latest` **não** substituem SHA.
- Exigir checks de CI pertinentes ao código e ao serviço **naquele SHA**, revisão/aceite exigidos pelo processo de entrega e avaliação de migrations antes do ACT.
- No `srv-api`, bloquear se checkout estiver sujo, divergente ou se revisão atual não for atestada. Não executar `git reset --hard`, `git clean`, `git checkout` forçado ou `git pull` não validado. Reconciliar drift via operador.
- Reusar `infra/scripts/up-prod-sequential.sh`/HML na parte de **build/up de serviço explicitamente enumerado**, nunca passando entrada textual livre ou `--pull` implícito que possa avançar HEAD além do aprovado.
- Gate novo de revisão pinada deve garantir `applied_sha == approved_sha`, e a ausência de `up -d` em serviços não solicitados. Não editar código ou config no host fora do Git.
- `healthcheck` de container e fumaça funcional são diferentes: ambos precisam de critérios por serviço quando aplicável. Resultado do script com exit 0 sozinho não permite `VERIFIED`.
- Migrations destrutivas/sem rollback interrompem o piloto automático; requerem plano operacional e autorização de manutenção explícitos. Rollback automático só quando houver artefato anterior e contrato de reversão compatível.

## 7. Catálogo e piloto

- **Default:** allowlist de deploy vazia e ACT desabilitado em produção; `policy_mode=deny` até onboarding individual.
- P2: inventariar quais serviços em `infra/docker-compose.hml.yml` são realmente implantáveis sem acionar dependências críticas; escolher **um único serviço de HML** com health/read-back verificável. Nome deve ser confirmado contra runtime e plano de migração antes de registrar.
- P3: ensaiar a sequência ponta a ponta no mesmo host, mas no stack HML isolado logicamente; limitar concorrência/build CPU e preservar produção.
- P4: habilitar **um único serviço produtivo não crítico** após aceite de segurança e teste de reversão. Nunca introduzir comando genérico para ampliar a lista.

## 8. Ordem fechada de implementação

| Lote | Implementação | Critério de saída |
|---|---|---|
| **P2.0** | Contrato, atores, estados, riscos, escolha do componente dono e testes negativos (este documento) | Revisão técnica concluída, sem alteração de runtime |
| **P2.1** | Módulo de policy puro, catálogo/allowlist, hash, TTL, idempotência, parser estrito de SHA, testes isolados | Tudo deny-by-default; nenhuma tool ACT publicada |
| **P2.2** | Journal transacional Core, RBAC separado, leitura de release e CI atestada, API PREPARE | Concurrency/replay/revocation/CI negatives passam |
| **P2.3** | Fluxo de aprovação nominativa no portal com expiração, cancelamento e audit read-back | ChatGPT sozinho não aprova deploy |
| **P3.1** | Executor restrito + canal interno, modo dry-run real em HML | Não altera containers; só serviço allowlisted |
| **P3.2** | Execução HML aprovada, lock, health, status e rollback seguro demonstrado | Teste ponta a ponta, revisão atestada |
| **P4.1** | Piloto PROD de serviço não crítico, com backup/rollback e dupla checagem de governança | Owner confirma mudança efetivamente implantada |
| **P4.2** | Expansão por serviço; catálogo de verificações, políticas de migração e janelas | Cada serviço passa por onboarding próprio |

## 9. Testes negativos indispensáveis

1. Usuário sem permissão, token de serviço ou superadmin sem aprovação nominativa → ACT negado.
2. Alvo não cadastrado, `service_id` com metacaracteres ou `commit_sha` malformado → rejeição antes de qualquer efeito.
3. SHA que não corresponde a CI verde, commit não alcançável, revisão local divergente ou checkout sujo → bloqueio.
4. Proposta expirada/revogada/alterada, dois ACT simultâneos ou dupla confirmação → **no máximo uma execução**.
5. Mudança de permissionamento entre PREPARE e ACT → negar, mesmo se UI ainda mostrar aprovado.
6. Health insuficiente, snapshot velho, serviço sem smoke definido, executor indisponível, migração irreversível → não reportar VERIFIED.
7. Instrumentação nunca imprime `Authorization`, `.env`, variáveis de segredo, logs de contêiner integrais, patches de configuração ou tokens.
8. Tentativa por prompt injection em issue, PR, log ou documento do repositório → não altera política, alvo, aprovação nem comandos.
9. Restart do broker durante execução → reconciliar pelo journal/executor; nunca disparar novamente por cegueira.

## 10. Registro de decisão e estado atual

| Data | Fato | Estado |
|---|---|---|
| 2026-11-15 | ATLAS OAuth e READ real via ChatGPT funcionaram, snapshot `partial` | `P1_AUTHENTICATED_READ_PROVEN` |
| 2026-11-15 | Operador priorizou deploys em vez de ampliar monitoramento | `PRIORITY_DEPLOY_GOVERNANCE` |
| 2026-11-15 | Contrato P2–P4 proposto neste documento | `P2_CONTRACT_PROPOSED` |
| 2026-11-15 | Core policy, journal, aprovação UI e executor | `NOT_IMPLEMENTED` |
| 2026-11-15 | Tool ACT ATLAS, deploy HML/PROD e testes adversariais | `NOT_EXECUTED` |

**Não confundir documento, código, CI, homologação e produção.** Nenhuma mudança deste documento autoriza efetuar um deploy agora.


## 11. P2.1 implementado como candidato offline em PR #191 (2026-11-15)

**Evidencia real de desenvolvimento, nao de release:**
- `linux-ops-mcp/linux_ops_mcp/deploy_policy.py` implementa somente `evaluate_deployment_preview` com `DeploymentPolicy` default deny, allowlist de alvos, SHA estrito 40-hex, IDs canonicos, atestacao estruturada e fresca (120s), bloqueios CI/ref, checkout sujo, revisao ausente, saude, migrations e rollback. Em producao, preview so pode ser elegivel com gates explicitos e rollback; isso **nao** concede autorizacao nem execucao.
- Preview elegivel em cenario sintetico HML recebe somente `proposal_hash` SHA-256 e `expires_at` de 10 min. Digest e idempotency request ID **nao** substituem ledger transacional, assinatura de aprovacao, backend Core RBAC ou validacao GitHub real. Atencao: `TrustedDeployEvidence` e um contrato de entrada **exclusivamente backend**; nao deve ser aceito como argumento MCP livre.
- `linux-ops-mcp/tests/test_deploy_policy.py` com **31 testes locais PASS** (Python 3.13, pytest 9.0.2, 2026-11-15). Testados deny-by-default, cancelamento de alvo desconhecido/metacaracter, SHA inadequado, reuso de IDs, evidencias ausentes/falsas/envelhecidas, incompatibilidade de revisao, falta de CI, saude e rollback, politica de producao e imutabilidade. Bytes do codigo/testes testados localmente foram conferidos contra arquivos publicados via GitHub por hash independente.
- O codigo **nao e importado** por `linux_ops_mcp/server.py` e portanto `tools/list` continua com quatro ferramentas READ. Nenhum endpoint, usuario de host, Keycloak, Core, migration, compose ou Docker foi alterado nesta etapa.
- `AGENTS.md` define verificador independente antes de merge; o subagente `delpi-verifier` nao esta disponivel nas ferramentas desta sessao, portanto **VERIFIER_PENDING**. GitHub CI da PR #191 precisa concluir; merge e deploy estao pendentes. O modulo so existe na branch de trabalho da PR, nao na `main` ate integracao autorizada.

**Proximo lote P2.2 (nao iniciado):** escolher modulo owner de journal e RBAC no backend, ligar atestacao GitHub/CI e revisao efetiva do host, desenhar API PREPARE idempotente/assinada com persistencia, permissionamento separado por ambiente e testes de concorrencia/revogacao. Nao publicar tool ACT nem criar executor antes da governanca.

**Indice mestre atualizado:** [README.md](./README.md). **Integracao futura com Portal do TI:** acompanhar [roadmap owner](../it-portal/README.md) e [Delpi Remote](../it-portal/delpi-remote/README.md), sem antecipar suas habilitacoes/seguranca.


## 12. A2.2a: gate de atestacao GitHub, host e Core, sem IO e sem permissao de ACT (2026-11-15)

**Escopo implementado no codigo:** `linux-ops-mcp/linux_ops_mcp/deploy_attestation.py`, com teste `linux-ops-mcp/tests/test_deploy_attestation.py`, apresenta `attest_preview_evidence`. Ele interpreta tres provas tipadas **ja colhidas por leitores backend confiaveis**: GitHub REST/Actions, marcador de revisao + saude do host e autorizacao fresh do Core. Retorna `verified_for_preview_only` apenas quando todas passam; negativa retorna codigos seguros, sem objetos capazes de executar.

**Verificacoes de release:** repo canonico `roberiooliveiradev/delpi-central`, main, SHA completo e presente no ref aprovado (backend provara a ancestralidade), lista nao vazia/sem duplicatas de workflow IDs exigidos por servico, cada workflow `push` em main para o SHA exato, `completed/success` e run identificavel. PR com CI verde em branch diferente **nao equivale** a release em main. O modelo nao pode injetar o conjunto de workflows exigidos; ele pertence ao catalogo backend.

**Verificacoes operacionais:** `HostProof` deve demonstrar ambiente/servico/repo exatos, SHA efetivamente instalado (nao GitHub HEAD), checkout limpo, health, risco de migration e rollback. Atualmente **nao existe leitor local de versao autoritativa**, portanto prova real nao pode ser fornecida. `CoreProof` exige usuario humano e permissoes explicitas `linux_ops.deploy.view` e `linux_ops.deploy.prepare`, mesmo para superadmin; grants ainda precisam ser registrados no Core por fluxo proprio. Provas expiram em 120 s (+ 5 s skew).

**Importantissimo:** estes objetos de entrada sao contratos de dados, nao evidencias autenticas so por terem classes Python. Na fase P2.2b, a API de policy sera responsavel por obter esses dados diretamente de providers confiaveis, sem aceitar `GithubProof`, `HostProof`, `CoreProof`, flags de CI ou `required_workflow_ids` como argumentos de ferramenta MCP. O resultado de `attest_preview_evidence` so alimenta `evaluate_deployment_preview` (P2.1) e nunca gera aprovacao nem permite ACT.

**Testes efetivos:** 76 cenarios locais de P2.1+P2.2a PASS em Python 3.13, pytest 9.0.2; incluem CI falsificado, ausente, em PR, falho, workflow duplicado, SHA divergente, repo alterado, prova vencida, host nao saudavel, revisao ausente, Core sem grant, service principal, tentativa de prod com policy desativada. GitHub CI e `delpi-verifier` ainda PENDING neste corte; nenhum HML/PROD foi executado.

**Proximos gates P2.2b/P2.2c:** (1) leitor GitHub REST com app/token estritamente de leitura e repositorio allowlisted, sem aceitar URL arbitraria; (2) leitor local de SHA atestado e estado de checkout/health, canal restrito, sem Docker no MCP; (3) verificacao de Core `force_refresh=True` e permissoes cadastradas; (4) journal transacional em Postgres com UNIQUE por idempotency key e transicoes atomicas e auditadas, sem escrever em producao antecipadamente; (5) API PREPARE deny-by-default + testes negativos de replay/concorrencia; (6) so depois UI de aprovacao e executor HML. Nenhuma rota MCP nova neste corte.


## 13. A2.2b: leitores confiaveis de evidencias e projeto do journal (2026-11-15)

**Entrega em codigo:** `linux-ops-mcp/linux_ops_mcp/deploy_evidence_readers.py` e `tests/test_deploy_evidence_readers.py`. Leitor GitHub usa apenas o repositorio canonico, SHA 40 hex, ref `main`, API compare ancestralidade e CI Actions `push` por SHA; Core usa `force_refresh=True` para nao herdar permissao revogada. As respostas ignoram campos nao necessarios e removem corpo upstream, token e exception text dos erros. Permissao de superadmin **nao** substitui `linux_ops.deploy.view` e `linux_ops.deploy.prepare` explicitamente concedidas. Leitores nao estao ligados ao servidor MCP e nao expuseram ferramentas novas.

**Evidencia:** 32 testes locais (MockTransport HTTP sem rede; Core fake) PASS, compilacao local PASS; bytes do codigo e testes versionados na main conferidos contra os testados. GitHub CI do push e auditoria `delpi-verifier` independente **PENDING**. Nenhuma consulta de GitHub/Core em producao foi executada pelos leitores.

**Dependencias nao entregues:** provador de revisao efetivamente em execucao por servico (`HostProof`), catalogo backend de workflow IDs exigidos, concessoes reais no Core, journal persistente, API PREPARE e UI nominativa. **A2.2b e um incremento parcial seguro, nao o aceite completo de A2.2.** Ausencia de qualquer elemento segue bloqueando o deploy.

**Rastreabilidade e proposta de persistencia:** [03-atlas-deploy-journal-p2b.md](./03-atlas-deploy-journal-p2b.md) detalha uso candidato do PostgreSQL `it_portal`, constraints para `requester_subject/idempotency_key`, status transacionais e log append-only de eventos, sem migration aplicada. Nao escolher numero de migration antes de coordenar com o roadmap paralelo Delpi Remote.

**Proximo passo A2.2c:** autoridade de release no host e testes com evidencias reais controladas; migration e repository SQL com UNIQUE/transacoes/replay; API backend fail-closed com Core fresh e catalogo CI, mantendo toda escrita ACT e execucao do host OFF.


## 14. A2.2c: contrato de recibo runtime do host e idempotencia, sem efeitos (2026-11-15)

O modulo `deploy_host_receipt.py` valida **recibos assinados**, vinculando host/ambiente/servico/commit a `ImageID` real observado e `ImageID` do registro de release que um futuro executor confiavel devera escrever. HMAC-SHA256, challenge aleatorio 256 bits, timestamps curtos, JSON estrito e comparacao de imagem com falha fechada; sem root, Docker socket, Git, rede, filesystem ou atuacao pelo MCP. Nenhum signatario/secret instalado, logo **nao existe HostProof real**. Qualquer retorno de `HostProof` conserva `migrations_safe=False` e `rollback_ready=False` ate prova independente, impedindo aprovacao/deploy prematuro.

O modulo `deploy_journal_policy.py` agrega apenas decisao pura de idempotencia de PREPARE (CREATE candidato, replay igual, conflict divergente, bloqueio de TTL/UUID/status), **nao grava em Postgres**, nao substitui UNIQUE/lock/transacao, nao aprova nem executa. Nao publicar como tool externa. Nenhuma migration V016 criada por risco de aplicacao incidental no proximo deploy do it-portal-api e necessidade de coordenar numeracao com Delpi Remote.

**Evidencias**: 30 testes offline do host + 17 do journal = **47 PASS locais**, Python 3.13, compileall OK, sem host/DB/CI real. GitHub CI/revisao independente ainda a confirmar. **Detalhes e proximo gate:** [04-atlas-p22c-host-receipt-journal-contract.md](./04-atlas-p22c-host-receipt-journal-contract.md). P2.2d devera implementar signer de host real e journal transacional PostgreSQL com antireplay DB; preview/A3/A4 permanecem bloqueados.
