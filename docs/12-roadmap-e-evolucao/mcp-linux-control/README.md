# ATLAS — Roadmap mestre e fonte de continuidade

> **Projeto:** ATLAS — Infraestrutura Linux e Orquestracao de Operacoes DELPI
> **Owner:** TI / Minha DELPI
> **Atualizacao:** 2026-11-16
> **Situacao em 2026-11-16:** P1 READ operando; P2.1 integrado; P2.2a-f em codigo; **P2.2g CI_SIGNED_RELEASE_PASS; P2.2h.1 PROD_PREFLIGHT_OPERATOR_PASS; P2.2h.2b MERGED_PR_199; P2.2h.2c MERGED_PR_202 / SELF_APPROVAL_ALLOWED_IN_CONTRACT** no push `f81ddd0075de1e4ef8bb68ca58791e9c43e70759`, manifesto `sha256:4689d4538134e5d9cb9de421569a132f733423f031300f160174e65e9853385a`, atestacao Sigstore/SLSA verificada. **PROD NAO PROMOVIDA / HOST NAO VERIFICADO**; runtime, HML, permissao Core, journal/migrations, PREPARE/ACT e verificador independente pendentes.
> **Repositorio:** `roberiooliveiradev/delpi-central`; PRs integradas [#184](https://github.com/roberiooliveiradev/delpi-central/pull/184), [#191](https://github.com/roberiooliveiradev/delpi-central/pull/191) e [#193](https://github.com/roberiooliveiradev/delpi-central/pull/193). A P2.2g possui artefato OCI assinado, **nao equivale a deploy**.
> **Diretriz de produto:** objetivo principal = deploy controlado sob demanda; melhoria da telemetria geral Linux congelada ate nova prioridade.

## 1. Visao do produto

O ATLAS sera o **operador conversacional de infraestrutura e implantacoes**, conectado ao ChatGPT por MCP OAuth do Keycloak. Ele consulta informacoes de estado e, em fases governadas, prepara, solicita aprovacao e acompanha implantacoes de codigo versionado. **Nao** sera um shell generico, root remoto ou superadmin de Docker.

Pedido-alvo: "ATLAS, revise o commit publicado no GitHub para o Portal do TI, prepare um deploy com riscos e dependencia, apresente a aprovacao, publique somente o servico autorizado e confirme versao e saude."

Modelo de autoridade: GitHub/CI prova o codigo aprovado; Core/Keycloak prova identidade/permissoes; aprovacao nominativa externa ao chat prova a decisao; executor isolado executa apenas um plano selado; observacao read-back comprova resultado. Nenhum desses passos pode ser substituido por instrucao de modelo, prompt, log ou issue.

## 2. Fontes de verdade (nao duplicar)

| Fonte | Responsabilidade |
|---|---|
| [01-discovery-architecture-and-security-roadmap.md](./01-discovery-architecture-and-security-roadmap.md) | Historico cronologico P0/P1, evidencias de conexao, diagnosticos e controles de seguranca |
| [02-atlas-deploy-control-plane-p2.md](./02-atlas-deploy-control-plane-p2.md) | Contrato tecnico P2-P4, ferramentas PREPARE/ACT, politica de SHA/CI, aprovacao, executor, testes |
| `linux-ops-mcp/` | Codigo real do MCP; hoje 4 ferramentas READ; nenhum deploy publicado |
| `infra/scripts/up-prod-sequential.sh` e `up-hml-sequential.sh` | Mecanismos canonicos sequenciais a reusar sob gates, nao shell livre |
| [Portal do TI — roadmap](../it-portal/README.md) | Fonte do inventario, servidores, servicos, governanca de ativos e API |
| [Delpi Remote — roadmap](../it-portal/delpi-remote/README.md) e [execucao](../it-portal/delpi-remote/EXECUTION-LOG.md) | Fonte exclusiva de computadores/agente/controle remoto; nao antecipar gates |
| [Normas runtime](../../../.cursor/rules/platform-delivery-runtime-operations.mdc) e [local-first](../../../.cursor/rules/local-first-deploy.mdc) | Regras de producao, segurança, versionamento, migracoes e deploy |

Este indice e a **fonte de continuidade** do ATLAS. Cada detalhamento deve residir no documento dono; este arquivo so sintetiza situacao, gates e proximas entregas.

## 3. Roadmap com estados e criterios de aceite

| Marco | Entrega | Estado em 16/11/2026 | Gate de aceite |
|---|---|---|---|
| A0 | Inventario de `srv-api`, limites e riscos | DOCUMENTADO | Evidencia sem secrets, arquitetura de acesso aprovada |
| A1 | MCP privado/publicado HTTPS + Keycloak OAuth + READ | **OPERADOR_CONFIRMOU_PASS** | Consulta real `get_host_health` pelo ChatGPT com snapshot/timestamp |
| A1-R | Lacunas CPU %, contagem Docker, `partial` | ADIADO_POR_DECISAO_DO_OWNER | So reabrir conforme nova prioridade, sem condicionar o deploy |
| A2.0 | Contrato de deploy, boundaries, aprovacao e testes negativos | DOCUMENTADO_EM_PR | Documento P2-P4 revisado, sem runtime |
| **A2.1** | **Modulo puro de politica de preview: allowlist, SHA, CI/attestation, TTL, hash, tests** | **MERGED_PR_191 / CI_PASS** | Sem I/O, deny by default, testes negativos locais e CI; nenhuma tool ACT |
| A2.2 | Atestacao CI/host/Core, journal OCI e API PREPARE | **P2.2g SIGNED_CI_PASS / P2.2h.1 PREFLIGHT_OPERATOR_PASS / P2.2h.2a MERGED / P2.2h.2b MERGED_PR_199 / P2.2h.2c MERGED_PR_202 / SELF_APPROVAL_ALLOWED_IN_CONTRACT / ACT_DISABLED** | Banco descartável, revisão independente, aprovação nominativa e rollback exigidos |
| A2.3 | Tela de aprovacao nominativa no portal + expirar/revogar/cancelar | NAO_INICIADO | Ator autorizador, plano/hash e replay revalidados fora do ChatGPT |
| A3.1 | Executor host isolado, catalogo um serviço HML, dry-run real | NAO_INICIADO | Sem shell/SSH/docker.sock no MCP, nenhum efeito em PROD |
| A3.2 | Piloto de deploy HML com health e rollback/roll-forward | NAO_INICIADO | Same approved SHA, estado + smoke reais, negativo de rollback |
| A4 | Piloto PROD restrito a um servico nao critico | BLOQUEADO_ATE_A3 | Aprovacao, preflight, backup/rollback, version attestation e aceite owner |
| A5 | Integracao de operacoes com Portal do TI e outros especialistas | FUTURO | Endpoint owner, permissoes independentes, gates especificos e auditoria |
| A6 | Operacoes recorrentes governadas/observabilidade proativa | FUTURO | Escopo de leitura separado, recorrencia opt-in, sem ACT autonomo |

Estados documentais nao substituem testes. `CODIGO_EM_PR` nao significa implementado no runtime nem validado pelo ChatGPT.

## 4. Evolucao integrada ao Portal do TI

**O ATLAS sera uma interface operacional; o Portal do TI permanece owner dos dados e controles.** Integrar por APIs especificas e identidade, nao por consultas SQL genericas, shell, duplicacao de inventarios ou reutilizacao indevida de tokens.

| Capacidade futura do ATLAS | Fonte no Portal de TI | Precondicao |
|---|---|---|
| Consultar servidores e servicos Windows/Linux | `it-portal-api` (inventario, observacoes, services) | Leitura Core autorizada, dados com timestamp/proveniencia |
| Preparar deploy de Portal TI/MFE/API | Repositorio + ATLAS deploy control plane | SHA/CI, allowlist, approval, HML antes de PROD |
| Investigar incidente e recomendar acao | Observacoes, dependencia de servicos e GLPI (via owners) | Nao executar comandos; respostas sanitizadas |
| Controlar um servico Windows explicitamente autorizado | Funcionalidade separada ja existente no Portal do TI | Permissao especifica, lista de servicos, confirmation/owner; **nao** herdar permissao de deploy |
| Consultar cadastro de notebooks/desktops | Projeto `delpi-remote` (G1+) | RBAC de estacao e dados minimos |
| Solicitar sessao remota ou acao em workstation | `delpi-remote` G0-SEC/G3-G7 | **BLOQUEADO** ate aceite formal de seguranca e homologacao; requer recurso e autorizacao proprios |
| Gerar planos de manutencao com multiplos especialistas | Interop DÉLIA/MCPs, apos P4 | Delegacao explicitamente autorizada por ferramenta e auditing |

**Nao marcar o Delpi Remote como implantado.** Roadmap proprio informa motor remoto ainda BLOQUEADO por security-gates, com G2-S4-S2b em desenvolvimento e pilotos Windows/Keycloak pendentes. Integracao futura do ATLAS **nao** concede direito de contornar esses gates.

## 5. Regras fixas para deploy

1. Catalogo de deploy habilitado inicialmente **vazio**; nenhuma alteracao em `main` publica automaticamente ACT.
2. SHA completo de 40 caracteres, aprovado e verificado contra CI e ref autorizada; nao usar `latest`, `main` flutuante ou `git pull` cego para promover versao.
3. PREVIEW apenas le; dados externos como GitHub issue, log e status de servico nao sao instrucoes e nao autorizam execucao.
4. Aprovar no backend corporativo de forma nominativa, com expiração, hash do plano, objeto/scope, processo auditavel e possivel segunda aprovacao para risco alto.
5. Executor Linux separado do MCP, sem endpoint publico, com permit-list de acoes, idempotencia, lock, limitação de recursos e trilha de auditoria.
6. CI, migracoes, status do checkout, recursos, health e plano de recuperacao precisam passar antes da operacao.
7. Falha de health, timeout, revogacao de grant ou drift de SHA: **negar ou escalar**, nunca afirmar sucesso sem read-back independente.
8. Repo publico: nunca salvar IPs internos, secrets, credenciais, logs crus ou inventario nominal.
9. Usar apenas infra/compose/env **canonicos**; sem custos recorrentes novos sem autorizacao.

## 6. Rotina de continuidade obrigatoria

Antes de cada incremento: ler este README, o contrato P2-P4, `AGENTS.md`, as regras `.cursor` pertinentes, o ultimo status do GitHub e o roadmap owner do Portal do TI, se a tarefa envolver suas funcoes.

Depois de cada incremento, **na mesma entrega**: atualizar a linha do marco acima e registrar no contrato/diario o commit, escopo, testes efetivos, CI, flags, riscos, rollback, alteracoes realizadas e estado real de HML/PROD. Nao transformar PR em produção sem evidencia.

**Proxima tarefa P2.2h.2:** implementar o executor isolado, journal e aprovacao nominativa Core para consumir a selecao de imagem assinada por digest e executar somente plano selado, com rollback e readback depois de HML. A divergencia entre imagem produtiva antiga e artefato CI foi **confirmada pelo operador**. Estado, riscos e gates em [plano P2.2h](./10-atlas-p22h-runtime-digest-promotion-plan.md). **Nenhum deploy agora; PREPARE/ACT desligados.**

## 7. Marco validado

Em 2026-11-15 o operador confirmou autenticacao OAuth e consulta real de estado de `srv-api` via ATLAS: snapshot parcial as 09:03:47 America/Sao_Paulo; RAM e armazenamento medidos, estado systemd fornecido. Esse marco comprova READ, **nao** deploy, aceite de ferramentas restantes, controle de servidor ou autorizacao de escrita.

**Rastreabilidade:** PR [#184](https://github.com/roberiooliveiradev/delpi-central/pull/184) ja mesclada preserva o marco P1 e o contrato P2; PR [#191](https://github.com/roberiooliveiradev/delpi-central/pull/191) foi integrada na main com a politica P2.1 (CI verde).


## 8. Incremento A2.2a: contratos de atestacao em codigo (15/11/2026)

**Codigo:** `linux-ops-mcp/linux_ops_mcp/deploy_attestation.py` e `linux-ops-mcp/tests/test_deploy_attestation.py` diretamente na main, sem importacao no `server.py`. A funcao pura `attest_preview_evidence` so cria `TrustedDeployEvidence` se registros estruturados de tres authorities estiverem coerentes:

- **GitHub** (`GithubProof` + `WorkflowRunProof`): repositorio canonico, commit SHA exato na branch main, ancestralidade comprovada pelo futuro adaptador REST, lista obrigatoria nao vazia de workflows por ID, status/conclusao `completed/success`, evento `push`, `run_id` e SHA/branch correspondentes. Duplicidades, workflow ausente ou falho bloqueiam.
- **Host** (`HostProof`): mesmo alvo, ambiente e repositorio, revisao instalada distinta e 40-hex, checkout limpo, health/migrations/rollback prontos. Sem origem local autenticada o sistema nao tem esses fatos, logo PREPARE real continua bloqueado.
- **Core** (`CoreProof`): sujeito humano igual ao solicitante, snapshot fresco com concessoes explicitas `linux_ops.deploy.view` + `linux_ops.deploy.prepare`; superadmin sem concessao especifica nao equivale a permissao para deploy. Esses codigos sao **candidatos ainda nao provisionados** no Core.

A janela de frescor da avaliacao e 120 s, com tolerancia de 5 s para clock futuro. **A validacao estrutural nao autentica por si so a fonte:** apenas backend com acesso proprio a GitHub, leitor local e Core podera construir esses objetos. O MCP nao expoe argumentos para injetar provas e suas quatro tools READ permanecem intocadas.

**Testes:** 76 cenarios em `test_deploy_attestation.py` + `test_deploy_policy.py` passaram localmente sob Python 3.13, pytest 9.0.2, sem rede, banco ou host. A comprovacao de GitHub CI e revisao independente do verificador permanecem pendentes de evidencia. **Nao existem endpoint de PREPARE, API de aprovacao, journal, permissão provisionada, executor host, autorizacao de producao ou deploy efetivo.**


## 9. Incremento A2.2b: leitores reais GitHub e Core, sem ferramenta de deploy (15/11/2026)

**Codigo na main:** `linux-ops-mcp/linux_ops_mcp/deploy_evidence_readers.py` e `linux-ops-mcp/tests/test_deploy_evidence_readers.py`. Leitores privados para uma futura API de governanca, **nao registrados no MCP atual**.

- `GithubReleaseReader`: consulta GET somente na API oficial fixa do repo DELPI; valida ref exata `main`, ancestry do SHA, runs `push`/CI, tamanho de resposta, tipo de JSON e erros em fail-closed. Sem rota arbitraria, redirecionamento ou proxy de ambiente. Um workflow CI exigido sera uma escolha do catalogo backend por servico, nao parametro de prompt.
- `CorePermissionReader`: reusa `load_user_rbac(..., force_refresh=True)` e exige identidade humana autenticada, correspondencia do subject e grants **explicitos** de VIEW/PREPARE; flag superadmin nao concede deploy.
- **HostProof** nao tem fonte confiavel: a revisao de Git local nao comprova o SHA realmente ativo no container. Falha fechada ate a etapa A2.2c. Aprovacao de usuario, journal, migrations, grant Core e executor nao foram implementados.
- **Tests locais** 32 PASS com HTTP mockado e Core fake (Python 3.13, pytest 9.0.2); compilacao PASS. GitHub Actions do novo codigo e `delpi-verifier` independente seguem **a verificar**. Nao houve teste autenticado com GitHub/Core/host real nem deploy HML/PROD.
- [Modelo do journal e runbook dos bloqueios](./03-atlas-deploy-journal-p2b.md) tem candidate schema transacional, chave de idempotencia, transicoes atomicas e eventos append-only de API. **Nao e migration aplicada**.

**Gate seguinte A2.2c:** host attestation real, decisao de ownership DB/migration, catalogo de alvos e workflow IDs, journal PostgreSQL com concorrencia e RBAC, API PREPARE sob flag OFF.


## 10. Incremento A2.2c: comprovante runtime assinado e regra PREPARE (15/11/2026)

**Codigo em main, ainda offline:**
- `linux-ops-mcp/linux_ops_mcp/deploy_host_receipt.py`: verifica HMAC-SHA256 do comprovante gerado por um **futuro emissor confiavel do host**, challenge de 256 bits, repo/servico/ambiente/host, SHA e `ImageID` de release **igual** ao `ImageID` observado do container, timestamp UTC <=90s e booleanos estritos; recusa campo extra, assinatura invalida ou divergencia. **Nao acessa Docker, SSH, Git, SQL ou qualquer servico real.** `migrations_safe` e `rollback_ready` permanecem obrigatoriamente **False** ate atestacao independente.
- `linux-ops-mcp/linux_ops_mcp/deploy_journal_policy.py`: helper de decisao PREPARE com idempotency UUIDv4, mesma identidade/payload, SHA/TTL/candidate coerente. **Nao e journal persistente, nao possui transacao/UNIQUE/lock, nao aprova e nao executa.**
- Testes `test_deploy_host_receipt.py` (30 PASS local) e `test_deploy_journal_policy.py` (17 PASS local): **47 PASS locais**, Python 3.13, sem rede nem host, compilacao PASS. CI GitHub e verificador independente ainda requerem comprovacao. Nao afirmamos smoke real de homologacao.

**Documentacao detalhada:** [04-atlas-p22c-host-receipt-journal-contract.md](./04-atlas-p22c-host-receipt-journal-contract.md). **Bloqueios reais:** nenhum signer instalado/chave provisionada no srv-api; sem registro imutavel de release, anti-replay DB ou produtor real de HostProof; tabelas V016 ainda nao criadas por necessidade de coordenar migration com Delpi Remote; grants Core/CI por servico/rollback/approval/ACT ainda pendentes. As quatro tools MCP READ nao mudaram.

**Proximo lote P2.2d:** emissor HML com allowlist + provenance de container/image, backend challenge one-shot e journal Postgres real sob transacao, mantendo ACT e producao desligados.


## 11. Incremento A2.2d: fonte de runtime, signer e journal transacional inerte (15/11/2026)

**Codigo na main:**
- `linux-ops-mcp/linux_ops_mcp/deploy_host_source.py` le via GET exclusivamente o inspect de um container configurado estaticamente, com labels Compose e limites de resposta; nenhum `docker.sock` montado no MCP. Depende de um **transporte/Proxy apenas de leitura externo**, ainda nao implantado, e nao aceita nome/URL de ChatGPT.
- `linux-ops-mcp/linux_ops_mcp/deploy_host_signer.py` valida HMAC de release record assinado pelo **futuro executor**, compara imagem de release e imagem Docker observada e cria um comprovante HMAC com uma SEGUNDA chave, nonce e timestamp. Nao gera release record de verdade, nao tem chaves reais, nao instala servico; sempre `checkout_clean=False`, `migrations_safe=False`, `rollback_ready=False` para nao criar falso positivo de preparacao.
- `it-portal-api/it_portal_app/infrastructure/persistence/atlas_deploy_journal.py` implementa `issue_challenge` e `store_prepared` com SQL parametrizado, relogio do banco, transacao, nonce unico, hash do nonce, idempotencia de `request_id`, evento de auditoria e rollback se challenge invalido. **Nenhuma rota o importa, sem Core grants ou tabelas aplicadas.**
- [DDL candidato](./05-atlas-p22d-candidate-schema.sql) FORA do diretorio de migrations, em razao de concorrencia com o desenvolvimento Delpi Remote.
- **Testes:** `test_deploy_host_source_signer.py` 17, `test_atlas_deploy_journal.py` 15, `test_atlas_schema_draft.py` 3, total **35 casos novos**; suite isolada cumulativa P2.1-P2.2d **190 PASS em Python 3.13**, `compileall` PASS. Docker/DB simulados; PostgreSQL real, HML, CI GitHub e verificador independente ainda **nao comprovados**.
- **Evidencia e gates:** [runbook P2.2d](./06-atlas-p22d-runtime-attestation-and-journal.md). Hash FNV dos seis arquivos principais em GitHub foi comparado aos fontes testados, 6/6 correspondentes.
- **Nao houve deploy, migration, release assinada real, execucao Docker, novo endpoint MCP nem alteracao de Keycloak/Compose.** Quatro ferramentas READ do ATLAS permanecem intactas.

**Proximo gate A2.2e:** conferir nomes/labels de um alvo HML real (sem supor identidade), revisar isolamento do Docker inspect, adicionar issuer real de release record + challenge vinculados ao backend, testes no PostgreSQL descartavel e proposta de migration com ownership controlado. Somente apos tudo isso considerar PREPARE governado; ACT permanece bloqueado ate P3.


## 12. Incremento A2.2e: integracao descartavel de PostgreSQL e Docker (2026-11-15)

**Evidencia do operador:** os 35 testes seletivos P2.2d passaram no venv Python 3.12 dentro de srv-api. O operador tambem confirmou os checks seguintes de containers e rotas OAuth/401 sem fornecer logs; registro de confirmacao humana, nao coleta direta do assistente.

**Codigo na main:**
- `atlas_deploy_journal.py`: corrigida a ordem de PREPARE para adquirir `pg_advisory_xact_lock`, verificar replay com `SELECT .. FOR UPDATE`, consumir nonce valido ANTES de inserir proposta referenciada por FK e registrar evento na mesma transacao. Impede duplicacao por duas requisicoes concorrentes e transforma falta de challenge em bloqueio seguro. O journal segue sem rota publica.
- `it-portal-api/tests/integration/test_atlas_postgres_journal.py`: **7 testes reais de transacao Postgres**, protegidos por gate de CI de banco isolado e host loopback; nao rodam em DB produtivo.
- `linux-ops-mcp/tests/test_atlas_docker_engine_ci.py`: **2 testes com Docker Engine real em runner GitHub descartavel**, container de teste Alpine/labels e manifest sintetico. Nao e evidencia de HML ou provenance de build DELPI.
- [Workflow de integracao isolada](../../../.github/workflows/atlas-p22e-integration.yml): dois jobs somente em `ubuntu-latest`, `permissions: contents: read`, sem segredos da Delpi nem deploy.
- [Runbook P2.2e](./07-atlas-p22e-disposable-ci-and-hml-gates.md) com riscos, criterios e proximos passos.
- **Testes locais efetivamente executados:** 16 PASS no FakePg revisado, 3 SKIP quando PostgreSQL/Docker nao estao presentes; compilacao PASS; workflow parseado. **GitHub Actions do novo workflow ainda sem evidencia de conclusao**; `delpi-verifier` e HML real pendentes.
- **Nenhuma migration produtiva, endpoint PREPARE/ACT, alteracao de Compose/Keycloak, segredo ou container da Delpi foi aplicado.** Quatro tools READ do ATLAS preservadas.

**Proximo gate:** verificar o CI PostgreSQL/Docker, review independente e depois definir um unico target HML seguro com provenance da imagem, canal Docker read-only e testes de banco com owner antes de qualquer exposicao PREPARE.


## 13. Incremento A2.2f: OCI SHA do Public Hub, sem rebuild no srv-api (15/11/2026)

**Motivo comprovado no piloto READ HML:** o operador coletou `docker inspect` do `delpi-hml-public-hub` (`running=true`, `healthy`, labels Compose `delpi-hml/public-hub`), depois `docker image inspect` da imagem `sha256:63ad3152e179d4a75e3cc1823a4062b300786fe841a635c4bbb8086e38e1112d`. `org.opencontainers.image.revision` e `.source` estavam ausentes. Imagem criada em 14/11/2026, mas isso nao prova SHA do commit.

**Entregas no repositorio:**
- `plugins/public-hub/Dockerfile` com stage leve `provenance-contract` que exige SHA lowercase de 40 hex e grava labels OCI `revision` + `source`. Stage final/default `production` herda as labels; builder de UI anterior preservado.
- `infra/docker-compose.yml` fornece `PUBLIC_HUB_SOURCE_REVISION` apenas ao build do Public Hub. `docker-compose.hml.yml` herda o arg por `extends`. `docker-compose.dev.yml` usa `development` sem SHA para nao bloquear desenvolvedores e nao alegar atestacao falsa.
- Helper `infra/scripts/public-hub-provenance.sh` verifica SHA Git de 40 hex no checkout ativo e recusara builds se inputs do Public Hub estiverem sujos/nao commitados. Scripts sequenciais HML e PROD exportam esse arg **somente** ao construir `public-hub`; o `SOURCE_REVISION` historico dos demais servicos nao mudou.
- `infra/scripts/tests/test_public_hub_provenance.py` **11 PASS offline** (Python3.13, git repos temporarios, sem Docker, sem HML); shell helper `bash -n` PASS.
- [Workflow CI OCI dedicado](../../../.github/workflows/atlas-public-hub-oci.yml) constrói **somente stage leve** em runner GitHub temporario, confere labels e rejeita revisoes ausentes/invalidas. **CI Docker nao confirmado como PASS**; nenhuma imagem final com etiqueta foi construida durante esta entrega.
- Detalhes operacionais, limitacoes e gate futuro: [runbook P2.2f](./08-atlas-p22f-public-hub-oci-revision.md).

**Seguranca:** label OCI e dado informativo, nao prova criptografica; ainda faltam manifest assinado do executor CI, correlacao SHA->ImageID, signer isolado, grants Core e journal real. `preview_deployment`, ACT e as migrations continuam inativas. **Nenhum container, Docker socket, DB, Compose ativo ou serviço HML/PROD foi modificado**. Engenharia de Roberto permanece fora do escopo.

**Proximo passo:** conferir CI OCI e obter aceite do owner antes de rebuild HML de Public Hub; ate la continuar apenas inspecao e aprovar apenas o codigo versionado. Em seguida planejar a atestacao de proveniencia assinada por pipeline para imagem final em execucao.


## 14. Retomada P2.2f.1: CI comprovado e contexto local de build (16/11/2026)

- **Fonte atual revalidada:** branch `main`, HEAD inicial `e18ee9a31c08ed29092962c524bba95434d5255f`, checkout inicialmente limpo; nenhum worktree anterior reutilizado.
- **CI existente confirmado:** P2.2e run [43719312596](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43719312596), SHA `5f7c4a1d65eebaee43c2479ea339dd13f81920d1`, dois jobs `completed/success`; P2.2f run [43721625404](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43721625404), SHA `1ac5b10f8ef6b4677cdcd5f736ca9020908a2d41`, job OCI `completed/success`. Nao sao evidencias de CI da correcao ainda local.
- **Lacuna reproduzida:** Git `status` omitia arquivos ignorados ainda copiados pelo Docker (ex. `.env.local`); politica `plugins/.dockerignore` nao era input protegido. Nove novos cenarios falharam antes da correcao.
- **Correcao desta entrega:** helper verifica politica Docker restrita, impede override `Dockerfile.dockerignore`, cobre dirty `.dockerignore` e recusa arquivos ignorados nos inputs, com excecao apenas de `node_modules/dist/.git` comprovadamente excluidos. Workflow passa a verificar o checkout real e observar mudancas nas politicas Docker. Nenhum segredo/nome de arquivo local entra nas mensagens.
- **Evidencia local:** 23 testes do guard PASS; regressao selecionada ATLAS + guard 163 PASS em Python 3.12. Sem Docker local, nao houve build. Revisao obrigatoria executada com `verify.py`: `veredito: INCONCLUSIVE`, `motivo: verificador indisponivel` (saida original no runbook).
- **Estado de entrega:** codigo e documentacao publicados diretamente em `main` por GitHub, no commit `65ece2215e83c182269bdfbf1f2e93ce255ba30f`, com CI novo confirmado PASS e revisao independente pendente. A indisponibilidade foi inicialmente interpretada como bloqueio absoluto; a leitura de `agent-kit/hooks/verifier_hooks.py` confirmou que `INCONCLUSIVE` pertence a `GATE_PASS_VERDICTS`, permitindo registrar o resultado sem alegar ACCEPT. Nenhuma alteracao HML/PROD, grants, migration, chave, executor ou endpoint MCP. Detalhamento e retomada: [P2.2f, secao 6](./08-atlas-p22f-public-hub-oci-revision.md#6-retomada-em-16112026-ci-confirmado-e-correcao-local-p22f1).


### Fechamento de publicacao P2.2f.1 (16/11/2026)

Codigo publicado diretamente pelo conector GitHub em [65ece2215e](https://github.com/roberiooliveiradev/delpi-central/commit/65ece2215e83c182269bdfbf1f2e93ce255ba30f), sem branch intermediaria ou force push. Arvore de codigo GitHub conferida com a arvore local testada; guard read-back corresponde ao blob `dac742ec18259c37847a99040f001f0874f3c0a2`. Gates locais Phase 3 e Platform Guardrails sobre o diff real: zero findings. Os quatro workflows acionados concluiram `success`: [OCI](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43849195548), [READ MCP](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43849195553), [Architecture](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43849195523), [Cursor Rules](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43849195596). Registro final e limites no runbook P2.2f, secao 6.6. Sem deploy, migration, signer ou habilitacao PREPARE/ACT.


### Confirmacao do operador: Public Hub PROD (16/11/2026)

O operador escolheu explicitamente producao, recebeu o comando canonico `git pull --ff-only` + `./infra/scripts/up-prod-sequential.sh --build public-hub` no checkout de producao e confirmou **"Feito"**. Estado: `PROD_PUBLIC_HUB_DEPLOY_OPERATOR_CONFIRMED`, com **SHA/ImageID/metadados e estado do container ainda nao coletados apos a execucao**. Confirmacao humana, sem logs de build nem leitura autonoma de runtime. Atualiza a situacao operacional posterior aos registros historicos de ausencia de deploy; nao transforma o deploy manual em atuacao do ATLAS nem comprova HML/P3/P4. As quatro tools READ, grants e PREPARE/ACT permanecem sem alteracao. Proximo incremento: read-back minimo da imagem PROD e P2.2g (imagem final, identificador imutavel e evidencia assinada do pipeline), sem aceitar etiquetas OCI como assinatura.


## 15. Read-back OCI PROD informado pelo operador (16/11/2026)

Estado `PUBLIC_HUB_PROD_OCI_METADATA_OPERATOR_REPORTED_PASS`: container `/delpi-public-hub` em `running`; `ImageID` do container e do image inspect identicos: `sha256:7ef60f87eb35e004ab5af8d95289a3836e20757d3fba626e14b98c2ad0a48cfb`. Label OCI `revision=03cecb7ed90946c799a66ca9b22b45beb221282e`, `source=https://github.com/roberiooliveiradev/delpi-central`. Revisao corresponde ao commit de fechamento publicado antes do deploy manual. **Fonte: saida de comandos filtrados fornecida pelo operador; nao coleta autonoma.** Nao comprova assinatura de build, CI da imagem, smoke HTTP, healthcheck ou readiness. Proximo codigo P2.2g: construir/validar imagem final no CI e vincular evidencia assinada ao artefato exato; imagem recompilada no host nao herda assinatura de outro build. PREPARE/ACT seguem inativos.


## 16. P2.2g: imagem final e proveniencia assinada (candidato em PR, 16/11/2026)

**Escopo entregue em codigo de PR:** workflow OCI atualizado para testar frontend + stage final e, **somente em push main apos gates**, publicar por digest no GHCR, emitir atestacao GitHub Actions/Sigstore SLSA vinculada ao manifesto e verifica-la; script read-only compara comprovacao assinada, SHA/ref/workflow e a imagem efetivamente ativa. [Runbook P2.2g](./09-atlas-p22g-signed-final-image.md).

**Estado da evidencia:** `CODE_IN_PR / CI_PENDING / SIGNATURE_NOT_YET_ISSUED / HOST_NOT_VERIFIED`. Testes simulados nao substituem assinatura real nem read-back no host. A imagem local existente com ImageID `sha256:7ef60f87eb35e004ab5af8d95289a3836e20757d3fba626e14b98c2ad0a48cfb` **nao foi promovida, assinada ou modificada**. Nem labels OCI nem mesmo SHA de fonte provam equivalencia de bytes de duas builds distintas.

**Gates apos PR:** CI e verificacao independente, permissao GHCR, imagem final assinada pelo pipeline da main, futura promocao por digest fixo autorizada, cotejo local read-only, health/smoke, ownership de HML, proxy ACL, migracao e Core grants. **PREPARE/ACT continuam desligados**. Nao efetuar deploy com a implementacao desta PR.


## 17. Fechamento P2.2g: artefato final assinado pelo CI, sem deploy (16/11/2026)

**Codigo:** PR [#193](https://github.com/roberiooliveiradev/delpi-central/pull/193) mesclada em `main`. Uma falha de teste assíncrono de restauracao do posto sensor CT-99 bloqueou o primeiro run apos merge; correção test-only em [`f81ddd0075de1e4ef8bb68ca58791e9c43e70759`](https://github.com/roberiooliveiradev/delpi-central/commit/f81ddd0075de1e4ef8bb68ca58791e9c43e70759), sem alterar comportamento produtivo.

**CI assinado comprovado:** [workflow `43863936825`](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43863936825) `completed/success`, 140 testes Vitest e gates SHA, Vite e lint do delta aprovados. `main` publicou a stage Docker `production` no GHCR com manifesto imutavel `sha256:4689d4538134e5d9cb9de421569a132f733423f031300f160174e65e9853385a` e ImageID `sha256:1a4cfd5d0370e35739cb679d3c0170845e55213488c2c5f7c7d249afba5365a9`. [Atestacao #68104175](https://github.com/roberiooliveiradev/delpi-central/attestations/68104175) via Sigstore/SLSA, validada no proprio workflow com SHA/ref/workflow assinante.

**Runtime permanece separado:** nenhum deploy automatico no host; evidencia anterior do operador aponta ImageID local diferente e nao equivale ao digest assinado. Somente apos um plano autorizado de promocao **por digest** e leitura da imagem efetivamente executada se podera marcar `HOST_PROVENANCE_PASS`. CI nao substitui revisao independente do `delpi-verifier` nem gates de ownership, Core, proxy ACL, migrations, journal e aprovacao. **PREPARE/ACT inativos**. Runbook detalhado [P2.2g](./09-atlas-p22g-signed-final-image.md).


## 18. P2.2h: readback real e plano de promocao por digest (16/11/2026)

**Fonte:** saida de `docker inspect` fornecida pelo operador para `delpi-public-hub` em PROD: `Estado=running`, `ImageID=sha256:7ef60f87eb35e004ab5af8d95289a3836e20757d3fba626e14b98c2ad0a48cfb`, `RevisaoGit=03cecb7ed90946c799a66ca9b22b45beb221282e`. Release CI atestada pelo GitHub `f81ddd0075de1e4ef8bb68ca58791e9c43e70759`: manifesto `sha256:4689d4538134e5d9cb9de421569a132f733423f031300f160174e65e9853385a`, config ImageID `sha256:1a4cfd5d0370e35739cb679d3c0170845e55213488c2c5f7c7d249afba5365a9`. **Divergencia comprovada, não há host provenance PASS**; `running` não prova smoke/health.

**Entrega neste incremento:** [plano P2.2h](./10-atlas-p22h-runtime-digest-promotion-plan.md) com requisitos de promoção apenas por digest imutável, preflight fail-closed, aprovação e segregação de identidade, integração com Compose canônico, smoke, idempotência e rollback planejado. **Sem mudança de código/runtime, sem execução Docker, sem habilitar ACT ou migrations**. O próximo incremento material é implementação + CI + revisão independente antes de propor o primeiro uso autorizado em PROD.


## 19. P2.2h.1: Compose opt-in e preflight de release assinada, sem ACT (16/11/2026)

- Codigo publicado na `main`: `infra/scripts/public-hub-release-preflight.sh`, testes em `infra/scripts/tests/test_public_hub_release_preflight.py`, var de imagem opcional no Compose PROD/HML e defaults locais preservados, exemplos env oficiais e protecao nos scripts sequenciais para forcar mode local mesmo que override tenha sido configurado em ambiente.
- **Preflight READ-only:** exige SHA Git e digest de manifesto completos + ImageID anterior esperado; verifica atestacao do GHCR com source ref main, workflow oficial, issuer GitHub OIDC e compara container Compose atual. `--apply` bloqueado; **nao faz pull, tag, build, up, stop, rm ou deploy**.
- **Testes e CI:** 22 casos locais PASS, [workflow ATLAS P2.2h 43871507381](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43871507381) com jobs PASS: Python offline e renderizacao real `docker compose config` de PROD/HML em default e pinado. [Architecture Enforcement 43871507384](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43871507384) `success`. O primeiro run do novo workflow falhou porque o profile HML nao estava habilitado; corrigido com `--profile public-hub` e revalidado.
- **Gates pendentes:** `delpi-verifier` independente nao executado nesta sessao (motor nao disponivel), aprovacao Core, journal, executor, health/rollback, observacao Docker no host e ensaio HML. O pipeline legado OCI de outro commit sofreu falha intermitente de Vitest em `PostActivity.test.tsx` (139/140); isso nao altera a assinatura CI comprovada da release anterior `f81ddd...`.
- [Registro e modo de consulta somente leitura](./10-atlas-p22h-runtime-digest-promotion-plan.md). **Producao intocada pelo ATLAS neste incremento.**



## 20. P2.2h.1 validado no srv-api, avancar governanca P2.2h.2 (16/11/2026)

O operador executou `public-hub-release-preflight.sh --plan prod` apos `git pull --ff-only` e reportou **[PLAN_OK_NO_DEPLOY]**. A atestacao Sigstore/GitHub do manifesto `sha256:4689d4538134e5d9cb9de421569a132f733423f031300f160174e65e9853385a`, commit `f81ddd0075de1e4ef8bb68ca58791e9c43e70759`, passou; Compose project `infra`, container `delpi-public-hub`, ImageID atual `sha256:7ef60f87eb35e004ab5af8d95289a3836e20757d3fba626e14b98c2ad0a48cfb` sem drift. Checksum de plano diagnostico `17f1730c4b5798168ca35c215b3e66f3947fdb998b82328219f03ed0d1e07110`, **nao e aprovacao**.

O CLI retornou ainda `promotion=BLOCKED approval=NOT_IMPLEMENTED readiness=NOT_VERIFIED rollback=NOT_VERIFIED`. Nao houve alteracao de container nem readback de release instalada. A imagem assinada **nao** esta executando e nenhuma parte do workflow ACT foi habilitada.

Proximo desenvolvimento: vincular digest OCI assinado + ImageID anterior/novo, CI e hostproof com challenge fresco a proposta Core/journal, e aprovacao nominativa fora do chat, **antes** de construir qualquer executor ativo. A estrutura de PREPARE existe de forma inerte no Portal TI, mas ainda nao sela esses campos OCI. Contratos e evidencia no [plano P2.2h](./10-atlas-p22h-runtime-digest-promotion-plan.md). **Revisao independente, schema owner, HML e rollback continuam obrigatorios.**


## 21. P2.2h.2b: binding OCI transacional no journal (candidato em PR, 16/11/2026)

O contrato puro OCI P2.2h.2a foi integrado pela [PR #197](https://github.com/roberiooliveiradev/delpi-central/pull/197), sem habilitar PREPARE/ACT. Este incremento propõe o adapter `atlas_deploy_oci_journal.py` para gravar, em **uma única transação PostgreSQL**, proposta genérica, vínculo imutável da imagem OCI assinada e evento `prepared`, com challenge consumido uma única vez e advisory lock de idempotência.

O novo [schema OCI candidato](./12-atlas-p22h2b-disposable-oci-bindings.sql) é **somente documental e para banco descartável no CI**. Não é migration versionada e não pode ser aplicado no PostgreSQL de produção. [Documentação do incremento](./13-atlas-p22h2b-oci-journal-integration.md) descreve provas, invariantes, testes e lacunas.

**Estado:** código em PR; CI e verificador independente ainda devem confirmar; nenhuma rota, grant, migração PROD, executor ou operação de container foi adicionada. O sucesso do pré-verificador `PLAN_OK_NO_DEPLOY` continua somente leitura; `ACT_DISABLED`.

## 22. P2.2h.2c: pré-validação Core e prévia de revisão, sem ACT (16/11/2026)

PR [#199](https://github.com/roberiooliveiradev/delpi-central/pull/199) integrada à main; journal OCI transacional em código, migration não aplicada. O incremento P2.2h.2c adiciona apenas contrato Python **pure/inert** de revisão por usuário humano, permissões Core candidatas `it-portal.deploy.view` e `it-portal.deploy.approve`, janela temporal e **autoaprovação permitida ao usuário autorizado** (sem aprovação automática). Retorno é somente `review_candidate_only`, nunca aprovação real. A prévia visual isolada em `plugins/it-portal/src/features/deploy-approvals/` exibe SHA/digest/ImageIDs, mas não está registrada em App, rotas, capabilities ou navegação; ambos botões permanentemente desabilitados.

**Invariante operacional:** deploy manual existente do Git/Docker/Compose continua inalterado e sem dependência do ATLAS; mudança manual de runtime deve invalidar apenas planos ATLAS desatualizados. **Não há endpoint, grant, DB migration, restart, autorização externa ou ACT.** [Contrato de revisão P2.2h.2c](./14-atlas-p22h2c-approval-review-candidate.md). Revisor `delpi-verifier` ainda pendente. Próximo passo é autorizar permissões Core com o owner e construir GET real somente leitura antes de considerar aprovação POST.

## 23. Regra de aprovacao por operador unico: requester = approver permitido (16/11/2026)

**Decisao expressa do owner TI:** o ATLAS deve admitir que o mesmo usuario autenticado **solicite e aprove** sua propria implantacao. Em uma equipe com apenas um aprovador, exigir uma pessoa diferente impediria o objetivo de facilitar o deploy. Isso e uma **aprovacao nominativa explicita** no Portal do TI, nao um consentimento automatico da proposta nem autorizacao pelo ChatGPT.

Contratos atualizados: `it-portal-api/it_portal_app/domain/atlas_deploy_approval_review.py` e `it-portal-api/it_portal_app/infrastructure/persistence/atlas_deploy_oci_seal.py`. Retirados os erros `ATLAS_SELF_APPROVAL_DENIED` e `OCI_SELF_APPROVAL_DENIED`. Testes cobrem usuario unico autorizado, permissao Core ausente ou stale, proposta revogada, idempotencia/nonce e vinculacao a imagem assinada. A interface existente continua uma **previa inerte**, com botoes desabilitados.

**Controles preservados:** permissao Core separada por **acao** (view/prepare/approve/execute), usuario humano ativo, declaracao explicita `approved_in_portal`, hash OCI imutavel, SHA/digest pinned, limites de tempo, journal com evento de solicitacao e de aprovacao futura contendo **ambos os sujeitos** (mesmo quando iguais), revogacao, revalidacao do estado do host, rollback e executores isolados. `delpi-verifier` continua sendo revisao **independente de codigo**, processo distinto da decisao de implantar do owner.

**Compatibilidade operacional obrigatoria:** Git/Docker e scripts `up-prod-sequential.sh` e `up-hml-sequential.sh` continuam disponiveis para os demais desenvolvedores, sem submissao ao ATLAS. Drift de deploy manual cancela apenas proposta automatizada antiga. Nenhum Core grant, migration, endpoint, botao ativo, ACT, restart ou alteracao de container foi realizado por este ajuste. Proximo passo: politica de consentimento explicito no Portal com auditoria de ator unico e provas de origem confiavel.
