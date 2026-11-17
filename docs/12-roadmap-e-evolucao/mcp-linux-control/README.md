# ATLAS — Roadmap mestre e fonte de continuidade

> **Projeto:** ATLAS — Infraestrutura Linux e Orquestracao de Operacoes DELPI
> **Owner:** TI / Minha DELPI
> **Atualizacao:** 2026-11-17
> **Situacao em 2026-11-16:** P1 READ confirmado; P2.1 integrado; P2.2a–f em codigo; P2.2g OCI_SIGNED_CI_PASS; P2.2h.1 PROD_PREFLIGHT_OPERATOR_PASS; P2.2h.2b PR #199, P2.2h.2c PRs #202/#203 e P2.2h.2d PR #205 integradas; **P2.2h.2e PR #206 integrada e VIEW_ONLY_PROD_OPERATOR_CONFIRMED** (V016 instalada, role DB exclusiva e tela de consulta com zero propostas). **O release OCI assinado ainda nao foi promovido por digest em PROD; PREPARE/approval/ACT e executor isolado continuam pendentes.** `delpi-verifier` independente e testes negativos end-to-end ainda nao comprovados. Evidencias e pendencias em [registro de ativacao](./16-atlas-journal-v016-core-view-activation-plan.md).
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
| A2.2 | Atestacao CI/host/Core, journal OCI e API PREPARE | **P2.2g SIGNED_CI_PASS / P2.2h.1 PREFLIGHT_OPERATOR_PASS / P2.2h.2b/c/d MERGED / P2.2h.2e VIEW_ONLY_PROD_OPERATOR_CONFIRMED / PREPARE_INATIVO / ACT_DISABLED** | Journal V016 e tela de leitura operacionais segundo evidencias do operador; ainda faltam verificador independente, negativas 403/503, criacao auditada de proposta, aprovacao e executor com rollback |
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

**Proxima tarefa P2.2h.2:** apos o aceite visual da consulta em PROD, fechar as evidencias de seguranca faltantes (403/503, grants Core, verificador independente e restore test); implementar **PREPARE persistido com proposta OCI assinada**, decisao nominativa no Portal e depois executor isolado com readback e rollback. **Nao habilitar ACT** apenas porque a pagina VIEW apareceu. O release OCI assinado segue sem promocao por digest no host. O deploy manual continua independente.

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


## 21. P2.2h.2b: binding OCI transacional no journal (PR #199 integrada, 16/11/2026)

O contrato puro OCI P2.2h.2a foi integrado pela [PR #197](https://github.com/roberiooliveiradev/delpi-central/pull/197), sem habilitar PREPARE/ACT. Este incremento propõe o adapter `atlas_deploy_oci_journal.py` para gravar, em **uma única transação PostgreSQL**, proposta genérica, vínculo imutável da imagem OCI assinada e evento `prepared`, com challenge consumido uma única vez e advisory lock de idempotência.

O novo [schema OCI candidato](./12-atlas-p22h2b-disposable-oci-bindings.sql) é **somente documental e para banco descartável no CI**. Não é migration versionada e não pode ser aplicado no PostgreSQL de produção. [Documentação do incremento](./13-atlas-p22h2b-oci-journal-integration.md) descreve provas, invariantes, testes e lacunas.

**Estado:** código integrado à `main` pela PR #199 com CI PostgreSQL descartável aprovado; verificador independente, migração produtiva, Core grants, API e executor continuam pendentes. Nenhuma operação de container foi adicionada. O sucesso do pré-verificador `PLAN_OK_NO_DEPLOY` continua somente leitura; `ACT_DISABLED`.

## 22. P2.2h.2c: pré-validação Core e prévia de revisão, sem ACT (16/11/2026)

PR [#199](https://github.com/roberiooliveiradev/delpi-central/pull/199) integrada à main; journal OCI transacional em código, migration não aplicada. O incremento P2.2h.2c adiciona apenas contrato Python **pure/inert** de revisão por usuário humano, permissões Core candidatas `it-portal.deploy.view` e `it-portal.deploy.approve`, janela temporal e **autoaprovação permitida ao usuário autorizado** (sem aprovação automática). Retorno é somente `review_candidate_only`, nunca aprovação real. A prévia visual isolada em `plugins/it-portal/src/features/deploy-approvals/` foi integrada à `main` pela PR #202; exibe SHA/digest/ImageIDs, mas não está registrada em App, rotas, capabilities ou navegação; ambos botões permanentemente desabilitados.

**Invariante operacional:** deploy manual existente do Git/Docker/Compose continua inalterado e sem dependência do ATLAS; mudança manual de runtime deve invalidar apenas planos ATLAS desatualizados. **Não há endpoint, grant, DB migration, restart, autorização externa ou ACT.** [Contrato de revisão P2.2h.2c](./14-atlas-p22h2c-approval-review-candidate.md). Revisor `delpi-verifier` ainda pendente. Próximo passo é autorizar permissões Core com o owner e construir GET real somente leitura antes de considerar aprovação POST.

## 23. Regra de aprovacao por operador unico: requester = approver permitido (16/11/2026)

**Decisao expressa do owner TI (implementada no contrato pela [PR #203](https://github.com/roberiooliveiradev/delpi-central/pull/203), integrada à `main`):** o ATLAS deve admitir que o mesmo usuario autenticado **solicite e aprove** sua propria implantacao. Em uma equipe com apenas um aprovador, exigir uma pessoa diferente impediria o objetivo de facilitar o deploy. Isso e uma **aprovacao nominativa explicita** no Portal do TI, nao um consentimento automatico da proposta nem autorizacao pelo ChatGPT.

Contratos atualizados: `it-portal-api/it_portal_app/domain/atlas_deploy_approval_review.py` e `it-portal-api/it_portal_app/infrastructure/persistence/atlas_deploy_oci_seal.py`. Retirados os erros `ATLAS_SELF_APPROVAL_DENIED` e `OCI_SELF_APPROVAL_DENIED`. Testes cobrem usuario unico autorizado, permissao Core ausente ou stale, proposta revogada, idempotencia/nonce e vinculacao a imagem assinada. A interface existente continua uma **previa inerte**, com botoes desabilitados.

**Controles preservados:** permissao Core separada por **acao** (view/prepare/approve/execute), usuario humano ativo, declaracao explicita `approved_in_portal`, hash OCI imutavel, SHA/digest pinned, limites de tempo, journal com evento de solicitacao e de aprovacao futura contendo **ambos os sujeitos** (mesmo quando iguais), revogacao, revalidacao do estado do host, rollback e executores isolados. `delpi-verifier` continua sendo revisao **independente de codigo**, processo distinto da decisao de implantar do owner.

**Compatibilidade operacional obrigatoria:** Git/Docker e scripts `up-prod-sequential.sh` e `up-hml-sequential.sh` continuam disponiveis para os demais desenvolvedores, sem submissao ao ATLAS. Drift de deploy manual cancela apenas proposta automatizada antiga. Nenhum Core grant, migration, endpoint, botao ativo, ACT, restart ou alteracao de container foi realizado por este ajuste. Proximo passo P2.2h.2d: integrar uma API GET de consulta ao journal com autorizacao Core efetiva e permitir apenas visualizacao real; depois elaborar consentimento explicito de aprovacao no Portal com auditoria de ator unico e provas confiaveis. Nenhuma aprovacao operacional nem ACT foi habilitada.


## 24. P2.2h.2d: GET autenticado do journal OCI (PR #205 integrada, 16/11/2026)

Implementada no codigo do Portal do TI a consulta GET **somente leitura** de propostas OCI, com autenticacao de usuario Keycloak, permissao Core **explicita** `it-portal.deploy.view` revalidada em `force_refresh=True`, identidade do ator conferida, filtros/paginacao e consultas PostgreSQL `REPEATABLE READ READ ONLY` limitadas a `public-hub` com binding OCI imutavel. Rotas: `GET /atlas/deployments` e `GET /atlas/deployments/{proposal_id}`. Resposta omite challenges e comprovantes sensiveis, e retorna 503 em ausencia de tabelas/DB, nunca resposta vazia enganosa.

Frontend integrado com nova tela de lista/detalhe e historico, exibida no menu **somente** quando a capacidade de VIEW estiver presente. Nenhum botao de aprovacao ou execucao foi disponibilizado. O codigo e a UI seguem fail-closed por padrao (`IT_PORTAL_ATLAS_JOURNAL_READ_ENABLED=false`). **A consulta nao esta habilitada em PROD**: o operador confirmou `ATLAS_JOURNAL_READ_ENABLED=False` e as tres tabelas de consulta ausentes; a migration V016, role DB de leitura e registro do grant Core estao em preparacao separada. O codigo da API e as rotas estao publicados, mas nao existe ainda consulta funcional em producao. [Plano de P2.2h.2d](./15-atlas-p22h2d-authenticated-journal-read.md).

**Proximo gate**: CI API/UI/PostgreSQL descartavel + revisao independente `delpi-verifier`, aprovar migration e grants com owners, testar GET real em HML e somente depois habilitar flag em ambiente autorizado. `ACT_DISABLED`; deploy manual dos demais colaboradores permanece intacto.


## 25. P2.2h.2e: preparar V016, role SELECT e permissao Core (PR candidata, 16/11/2026)

**Evidencia de PROD fornecida pelo operador:** `delpi-it-portal-api` saudavel, dois endpoints `/atlas/deployments` publicados na OpenAPI, mas `settings.ATLAS_JOURNAL_READ_ENABLED=False`. Consulta read-only a `to_regclass` retornou `None` para `atlas_deploy_proposals`, `atlas_deploy_oci_bindings` e `atlas_deploy_events`. Logo o menu **Implantacoes ATLAS** nao aparece corretamente com a flag desligada e sem permissao registrada.

**Incremento em preparacao:** `it-portal-api/migrations/V016__atlas_deploy_oci_journal.sql` migra quatro tabelas e triggers somente quando o owner configurar **explicitamente** `IT_PORTAL_ATLAS_JOURNAL_SCHEMA_APPLY_ENABLED=true`; `run_migrations()` conserva V001-V015 e nao aplica V016 em restart normal. `infra/docker-compose.yml` envia flags com default `false` e credenciais de login PostgreSQL separado; o BFF de consulta agora falha com 503 quando nao ha role **dedicada de somente leitura**, sem cair na role de escrita. Manifesto `plugins/it-portal/it-portal.manifest.json` `0.3.5` cadastra como **proposta** o grant de Core `it-portal.deploy.view` e a rota do modulo, sem atribuir acesso automaticamente.

**Nenhuma ativacao ou escrita produtiva ocorreu.** PR precisa de CI API/PostgreSQL/UI, revisao independente `delpi-verifier` e aprovacao DBA/Core. Apos merge, nao rodar SQL de docs manualmente: coordenar backup, migration V016 sob gate temporario, role/GRANT minima, registro estrutural do manifesto, atribuicao individual de `it-portal.deploy.view`, e **somente depois** habilitar `IT_PORTAL_ATLAS_JOURNAL_READ_ENABLED=true`. Sem proposta OCI real, a lista aparecerá vazia mesmo apos ativar a interface. [Runbook de ativacao controlada](./16-atlas-journal-v016-core-view-activation-plan.md).

**Invariantes:** `ACT_DISABLED`, PREPARE inerte, nenhuma aprovacao no ChatGPT, nenhuma mudanca em scripts `up-prod-sequential.sh`, `up-hml-sequential.sh`, `git pull` ou no deploy manual de outros desenvolvedores.


## 26. P2.2h.2e: consulta do journal ATLAS validada visualmente em producao (16/11/2026)

**Fonte:** confirmacoes do operador por terminal e captura da tela **Implantacoes ATLAS**. A [PR #206](https://github.com/roberiooliveiradev/delpi-central/pull/206) foi integrada a `main`. O operador gerou backup completo de `plugins_hub` (`pg_dump -Fc`, catalogo validado por `pg_restore -l`), aplicou V012–V015 e, depois, a V016 pelo runner versionado com gate temporario explicitamente habilitado. `schema_migrations` registrou V016; as quatro tabelas de journal apareceram no PostgreSQL.

A role dedicada `it_portal_atlas_journal_reader` teve leitura validada nas tres tabelas de propostas/vinculos/eventos e **nao** em `challenges`. A API confirmou `atlas_journal_read_db_configured=True`, `current_user` igual a essa role e `default_transaction_read_only=on`, com **0 propostas reais**. A tela mostrada pelo operador inclui filtros, aviso de leitura e estado vazio **Nenhuma solicitacao encontrada**; portanto, a capacidade VIEW esta **visivel e funcional no nivel comprovado pela observacao do operador**. O manifesto `0.3.5` e a permissao Core `it-portal.deploy.view` sao precondicoes do codigo, mas seu registro e concessao exatos nao foram auditados separadamente nesta conversa.

**Limites de aceite:** nenhuma proposta criada; nenhum PREPARE, aprovacao real, ACT, promocao OCI por digest ou rollback automatizado; somente visualizacao. Restam validacao independente `delpi-verifier`, teste completo de restauracao de backup, verificacao de triggers e testes negativos de API/segregacao (403 sem grant, 503 sem reader). A divergencia de collation do PostgreSQL foi identificada e **adiada por decisao do operador**, sem `REINDEX` nem `REFRESH COLLATION VERSION`; criar manutencao DBA separada. Esta fase **nao habilita** deploy automatico e nao altera o deploy manual existente.

**Proximo incremento:** PREPARE real com atestacao confiavel, journal transacional e proposta assinada, seguido de aprovacao explicita e nominativa no Core, e somente apos os gates de host/rollback um executor ACT isolado. Registro detalhado: [V016 e aceite PROD VIEW](./16-atlas-journal-v016-core-view-activation-plan.md).


## 27. P2.2h.2f: vinculo criptografico do nonce no journal OCI (PR para revisao, 16/11/2026)

A proxima evolucao acrescenta a verificacao transacional de que o hash de challenge presente na prova do host corresponde **ao mesmo nonce** consumido na tabela de challenges, impedindo substituicao por prova de outro challenge. A [nota tecnica de P2.2h.2f](./17-atlas-p22h2f-challenge-binding-review.md) registra o caso negativo e as pendencias. O incremento inclui teste de regressao em PostgreSQL descartavel e nao habilita endpoints de PREPARE nem ACT. **Status atualizado:** PR [#208](https://github.com/roberiooliveiradev/delpi-central/pull/208) integrada a `main` em 16/11/2026 com cinco checks CI aprovados; `delpi-verifier` independente e deploy nao comprovados. O PREPARE e o ACT continuam inertes.


## 28. P2.2h.2g: leitor de proveniencia OCI verificada, sem PREPARE/ACT (16/11/2026)

Incremento proposto em branch/PR: um **leitor backend somente de verificacao** invoca `gh attestation verify` para o digest imutavel da imagem `public-hub` e o commit completo, com repositorio, workflow `atlas-public-hub-oci.yml`, `refs/heads/main`, issuer e SLSA v1 fixados. Exige GitHub CLI atualizado, valida documento assinado DSSE e subject OCI e retorna SHA-256 dos **bytes exatos da declaracao** como prova de proveniencia (sem inventar ImageID ou autorizacao). Testes isolados simulam o verificador, sem acesso ao registry, GitHub nem servidor; workflow CI executa os novos testes. Detalhes: [18-atlas-p22h2g-oci-provenance-reader.md](./18-atlas-p22h2g-oci-provenance-reader.md).

**Estado atualizado:** PR [#209](https://github.com/roberiooliveiradev/delpi-central/pull/209) integrada a `main` em 16/11/2026, com 5 checks de CI aprovados. Nenhum endpoint, permissao de PREPARE, conta DB de escrita, host attestation elegivel ou ACT foi habilitado. O teste real de assinatura GHCR e a revisao `delpi-verifier` independente nao foram evidenciados. A comprovacao de `image_config_id` e da fonte de host exige os proximos adaptadores, seguida de identidade humana e RBAC Core antes de expor API PREPARE. Preservar o deploy manual, o ACT desabilitado e os gates de PRODUCAO existentes.


## 29. P2.2h.2h: resolucao somente leitura do ImageID OCI no GHCR (16/11/2026)

A evolucao candidata introduz `GHCRImageIdentityReader` no backend, sem rota, exportacao de tokens, escrita no banco, PREPARE ou ACT. A leitura do `ghcr.io/roberiooliveiradev/delpi-public-hub` por **digest SHA-256 imutavel** recalcula o hash dos bytes retornados, compara o header `Docker-Content-Digest` quando presente e recusa manifests com esquema/media type nao autorizados. Para indices OCI/multiarquitetura, seleciona exatamente uma entrada `linux/amd64` e valida o digest e tamanho do manifesto filho. O digest `config.digest` resultante representa o **ImageID Docker** do manifesto especifico. Manifests diretos sao aceitos, mas o campo plataforma fica `unverified` ate uma fonte independente confirmar arquitetura. Um 401 pode solicitar apenas token anonimo de pull via endpoint GHCR fixo; credenciais privilegiadas, quando exigidas, serao fornecidas exclusivamente pelo backend.

`OCIImageIdentity` ainda nao constitui prova de assinatura, identidade de host, autorizacao ou release executavel; precisa ser correlacionado ao `VerifiedOCIStatement` da etapa anterior e a observacao de Docker com challenge autenticado. Testes hermeticos, mockados, verificam hash/manifests/indice, 401, redirecionamentos, scope, limites e erros fail-closed. Detalhes: [19-atlas-p22h2h-registry-image-identity.md](./19-atlas-p22h2h-registry-image-identity.md). **Estado atualizado:** PR [#210](https://github.com/roberiooliveiradev/delpi-central/pull/210) integrada a `main` em 16/11/2026 com 5 checks de CI aprovados. Teste com manifesto real GHCR e `delpi-verifier` independente nao comprovados. Sem deploy PROD e com PREPARE/ACT desabilitados.


## 30. P2.2h.2i: correlacao de proveniencia assinada + ImageID GHCR (16/11/2026)

O incremento candidato apresenta `OCIReleaseEvidenceReader` (backend privado), que consulta **duas fontes de verdade independentes**: `GitHubOCIProvenanceReader` (GitHub CLI/Sigstore verificado para workflow, SHA e digest OCI fixados) e `GHCRImageIdentityReader` (manifesto SHA-256 com read-back do ImageID `config.digest`). O agregador recusa alvos invalidos **antes** de consultar fontes, exige igualdade de repositorio, imagem, workflow, ref, commit e digest, atestado SLSA com hash integro, manifest de `linux/amd64` selecionado inequivocamente e duas evidencias frescas com ordem temporal coerente. Compondo apenas resultados das fontes, gera `CIReleaseEvidence` com o `verified_at` **mais antigo**, sem mascarar expiracao. Testes unitarios negativos e teste hermetico que exercita os dois adaptadores sem acesso real a rede ou host, incluidos no job PostgreSQL descartavel. Registro: [20-atlas-p22h2i-release-evidence-composition.md](./20-atlas-p22h2i-release-evidence-composition.md).

**Status atualizado:** PR [#211](https://github.com/roberiooliveiradev/delpi-central/pull/211) integrada em 16/11/2026 com 5 checks de CI aprovados, sem deploy PROD; `CI_RELEASE_EVIDENCE_CANDIDATE_ONLY`. Revisão `delpi-verifier` independente e teste de assinatura real não demonstrados. Este agregador nao e endpoint, autorizacao de usuario, grant Core, PREPARE persistido nem ACT. Proxima dependencia: verificar fonte de host autenticada ligada a challenge e rollback, e validar as provas reais GitHub/GHCR sob autorizacao do owner antes de qualquer conexao com escrita. `delpi-verifier` e revisao humana seguem obrigatorios. Deploy manual dos outros colaboradores preservado.


## 31. P2.2h.2j: comprovante assinado de estado do host v2, com alvo e challenge (16/11/2026)

A evolucao candidata introduz `linux_ops_mcp.deploy_host_runtime_v2`, que emite um comprovante assinado somente de observacao **a partir do signer legado e do Docker GET**. O formato v2 inclui dentro do MAC, com dominio criptografico diferente do v1, os identificadores de **host, ambiente, servico, container e projeto Compose**, alem de commit, ImageID, estado, health, timestamp e nonce. O verificador `verify_host_runtime_receipt_v2` valida a assinatura HMAC, o alvo esperado pelo backend, o challenge exato, a validade temporal de 90s, o conteudo e a igualdade entre ImageID aprovado no release record e ImageID do Docker. Retorna somente dados estruturados e o SHA-256 do nonce (nunca o nonce nem o segredo) para futura vinculacao ao journal. Testes hermeticos cobrem replay, drift, assinatura/tempo, ambiente, servico, Docker e checkout; a CI efetua smoke de um contêiner Docker descartavel real. Detalhes: [21-atlas-p22h2j-host-runtime-receipt-v2.md](./21-atlas-p22h2j-host-runtime-receipt-v2.md).

**Status atualizado:** PR [#212](https://github.com/roberiooliveiradev/delpi-central/pull/212) integrada a `main` em 16/11/2026 com cinco checks de CI aprovados; sem deploy de PROD. A verificacao HMAC **nao consome** o challenge no PostgreSQL e nao valida git checkout, migracoes ou rollback: `checkout_clean=False`, `migrations_safe=False`, `rollback_ready=False`, `challenge_consumed=False` por design. Nenhum daemon, endpoint, socket Docker em PROD, segredo, grant, migration, PREPARE ou ACT adicionado. Comprovantes v1 existentes permanecem compatíveis; o v2 tem verificador separado e nao aceita v1. Deploy manual nao alterado.


## 32. P2.2h.2k: reconciliacao diagnostica host OCI e challenge, permanentemente bloqueada (16/11/2026)

O incremento candidato cria `linux_ops_mcp.deploy_host_oci_preflight`, uma verificacao offline e **somente leitura** que revalida a assinatura HMAC do receipt v2 (backend-owned) e cruza a identidade do host `public-hub` com uma projecao estrita da intencao OCI: ambiente, servico, base/target SHA, ImageIDs, manifesto, hash da declaracao, rollback image ID e hash SHA-256 do **nonce de 32 bytes**. O alvo e limitado aos conteineres/projetos Compose canônicos em HML e PROD. Divergencias de commit/imagem/rollback, alvo nao autorizado, falhas de MAC, nonce e tempo de prova são negadas ou documentadas por codigos finitos. O modulo produz `HostOCIPreflightReport.status="blocked"` **em todos os casos**, inclusive quando imagem, health e nonce coincidem. Blocos obrigatorios: CI nao revalidada aqui, checkout e migracoes nao atestados, rollback nao atestado, nonce nao consumido e autorizacao Core ausente. Testes hermeticos (incluindo emissao HMAC real por signer test-only) integram o CI em Docker descartavel. Nota tecnica: [22-atlas-p22h2k-host-oci-preflight-blocked.md](./22-atlas-p22h2k-host-oci-preflight-blocked.md).

**Status atualizado:** PR [#213](https://github.com/roberiooliveiradev/delpi-central/pull/213) integrada a main em 16/11/2026 com cinco checks de CI aprovados, sem deploy de producao. PREPARE_DISABLED / ACT_DISABLED; sem novas rotas, grants, migrations ou escrita. Revisao delpi-verifier independente nao comprovada. Nao considerar tipos Python fornecidos pelo cliente como evidencias confiaveis: para uma fase futura, correlacionar essa observacao com leitores reais OCI do backend, challenge persistido one-shot, grants Core, comprovacao de checkout/rollback e procedimento de revisao independente.


## 33. P2.2h.2l: observacao local somente leitura do checkout Git (16/11/2026)

Incremento candidato em branch/PR: linux_ops_mcp.deploy_git_checkout_readonly.GitCheckoutReadOnlyObserver verifica o checkout autorizado do host (/home/operador/projetos/delpi-central), com diretório fixado no backend, sem git pull, fetch, reset, deploy, Docker, HTTP ou escrita no journal. A rotina exige diretorio Git comum, recusa symlinks e gitdir externo, valida top-level, commit SHA e branch, executa git status --porcelain=v1 -z com arquivos untracked e submodules e revalida branch/HEAD/raiz depois da leitura. Ambiente git sanitizado, prazo de 5 s, limitação de saída e erros finitos sem stderr nem nomes de arquivos. Retorna GitCheckoutObservation com status inspection_only_blocked, checkout_attested=False, challenge_bound=False, rollback_ready=False e prepare_eligible=False, mesmo quando o checkout parece limpo. Testes exercitam um repositorio Git real temporario dentro do GitHub Actions, sem tocar no checkout de producao. Documentação: [23-atlas-p22h2l-git-checkout-observer.md](./23-atlas-p22h2l-git-checkout-observer.md).

**Estado atualizado:** PR [#214](https://github.com/roberiooliveiradev/delpi-central/pull/214) mesclada em 16/11/2026, com cinco checks CI aprovados; nenhum deploy de producao necessario. Revisao independente delpi-verifier nao comprovada. Nenhum agente, servico, permissionamento ou secret novo; PREPARE e ACT seguem inertes. O leitor nao observa arquivos ignorados nem constitui prova autenticada de host. Necessarios host signer confiavel, challenge one-shot persistido, revisao contra race, Core e backup/rollback comprovados antes de liberar qualquer PREPARE.


## 34. Pacote integrado P2.2h.2m–2o: witness Git assinado, challenge e reconciliacao host OCI (16/11/2026)

A entrega **agrupa tres capacidades em uma unica PR**: (m) emissao de witness Git por GitCheckoutReadOnlyObserver real, com SHA, branch, estado dos arquivos nao ignorados, host, ambiente, servico, projeto Compose e nome de container; (n) verificacao de assinatura HMAC SHA-256 em dominio exclusivo e challenge one-shot, validacao de timestamp/target/estrutura e rejeicao de adulteracoes/replay; (o) reconciliacao fail-closed de witness Git com receipt Docker v2 e preflight OCI existente, ambos validados independentemente com **chaves distintas**, mesmo nonce, commit de base e janela curta de observacao. A auditoria evidencia divergencias de branch, Git sujo, HEAD diferente do commit em producao e gap temporal, sem confundir git status local com atestacao independente do processo.

**Entrega sempre status=blocked e prepare_eligible=False, mesmo quando as provas coincidem**. O host ainda nao tem identidade atestada por infraestrutura dedicada; Git nao mede arquivos ignorados nem snapshot atomico. Journal nao emite/consome challenge neste modulo, e CI release/rollback/migrations/Core seguem como provas externas pendentes. O modulo nao cria daemon, endpoint, secret, grant, migration ou alteracao de Docker/PROD; testes temporarios no CI usam Git real e Docker falso, com cenarios negativos e MAC real em chaves sinteticas. Detalhes: [24-atlas-p22h2m-o-checkout-host-evidence-bundle.md](./24-atlas-p22h2m-o-checkout-host-evidence-bundle.md).

**Status atualizado:** PR [#215](https://github.com/roberiooliveiradev/delpi-central/pull/215) integrada a main em 16/11/2026, com cinco checks CI aprovados; sem necessidade de deploy em producao. Revisao independente delpi-verifier e humana nao comprovadas. Proxima entrega de maior porte, depois da revisao e ensaio HML: plano de comprovacao real do host (identidade/segregacao OS), nonce DB one-shot e gates auditaveis de rollback/migrations/Core, sem habilitar ACT por inferencia.


## 35. Pacote integrado P2.2h.2p-r: challenge PostgreSQL read-only + CI GitHub/GHCR + readiness bloqueada (16/11/2026)

Tres capacidades em uma entrega: (p) inspecao do challenge PostgreSQL com SELECT e relogio do banco, escopo requester Core/ambiente/public-hub/nonce, TTL ate 90s e sem reservar, consumir ou expor nonce; (q) correlacao pelo leitor OCI existente que verifica assinatura GitHub e ImageID GHCR com expectativa imutavel do backend (manifesto, commit, statement e imagem); (r) segunda consulta apos a validacao externa para detectar challenge consumido ou expirado, resultando em diagnostico **sempre bloqueado**. Testes com PG 16 descartavel, mais negacoes unitarias, integrados ao workflow CI. O papel atual it_portal_atlas_journal_reader nao possui SELECT nos challenges: NAO conceder ou reutilizar esse privilegio sem revisao. A funcao diagnostica continua desligada por padrao e nao esta ligada a rota ou servico. Ver [25-atlas-p22h2p-r-readiness-review.md](./25-atlas-p22h2p-r-readiness-review.md).

**Estado atualizado:** PR [#216](https://github.com/roberiooliveiradev/delpi-central/pull/216) integrada a main em 16/11/2026, com cinco checks GitHub Actions aprovados e sem deploy de producao. Revisao delpi-verifier independente e aprovacao operacional do host nao demonstradas. PREPARE_DISABLED, ACT_DISABLED, sem migration, papel DB, grant, endpoint, chave, Docker socket ou deploy. SELECTs nao impedem corrida de consumo apos a ultima consulta. Proxima entrega devera incluir identidade confiavel do coletor host, transporte autenticado, backup/rollback/migrations comprovados, Core RBAC e writer transacional de menor privilegio, somente com aprovacao operacional.


## 36. Pacote P2.2h.2s-u: receipts Linux -> Portal TI, diagnostico integral e ensaio de interoperabilidade (16/11/2026)

Entrega agrupada: (s) verificador privado do Portal TI para os bytes dos comprovantes assinados Docker v2 e Git v1, com dois HMACs de dominio distinto, chaves separadas, nonce exato de 32 bytes, identidade de host/ambiente/servico/Compose/container, SHA do commit-base, ImageID e frescor <=90s, tolerancia de relogio 5s e janela Git/Docker <=15s; (t) diagnostico FullReadOnlyReadinessReviewer combina journal SELECT do challenge e release GitHub/Sigstore/GHCR da PR #216, verifica os dois receipts e reconsulta o nonce apos a correlacao. (u) CI valida unitariamente os contratos e testa o uso dos assinadores verdadeiros de linux-ops-mcp pelo verificador do it-portal-api usando Git temporario e Docker simulado. Runbook define identidades OS, canal de comunicacao, grants minimos, backup/rollback/migracoes e gates do ensaio HML. Mais detalhes: [26-atlas-p22h2s-u-cross-context-readiness.md](./26-atlas-p22h2s-u-cross-context-readiness.md).

**Estado atualizado:** PR [#217](https://github.com/roberiooliveiradev/delpi-central/pull/217) integrada a main em 16/11/2026, com 6/6 checks GitHub CI aprovados; sem deploy de producao. O delpi-verifier independente, atestacao OS do coletor e autorizacoes Core/DB continuam sem comprovacao operacional. Nenhuma API/MCP route, GRANT, migration, secret provisioning, servico ou Docker socket no BFF. Contrato puro de HMAC nao atesta a identidade do coletor OS e nao avalia arquivos ignorados ou snapshot Git atomico. Resultado SEMPRE bloqueado, prepare_eligible=False, can_execute=False; leitura final SELECT nao consome nonce, nao elimina race e nao constitui permissoes Core. Nenhuma acao em PROD e nenhuma alteracao de deploy manual.


## 37. P2.2h.2v-x: Core RBAC fresco + diagnostico HML e hardening de challenge (16/11/2026)

Este pacote agrega tres controles relacionados. (v) Core: o novo atlas_deploy_core_gate.py usa load_user_rbac(token, force_refresh=True) para conferir um usuario humano validado pelo middleware, subject UUIDv4 e as permissoes explicitas it-portal.access, it-portal.deploy.view e a permissao candidata e NAO PROVISIONADA it-portal.deploy.prepare. Nega token de servico, grant ausente, superadmin sem grant, Core offline e subject divergente. (w) HML: atlas_deploy_hml_admission.py limita diagnosticos ao Public Hub HML, vincula actor ao requester do challenge, consulta Core ANTES e DEPOIS de correlacionar evidencias OCI, Git/Docker e journal, e devolve HMLPilotBlockedDiagnostic sempre status blocked, prepare_eligible=False, can_execute=False, incluindo pendencias de backup, restore, rollback, migrations, writer e identidade do coletor. (x) Race de challenge: o diagnostico de release agora conserva challenge_issued_at e a terceira consulta DB exige que a data de emissao continue identica, mesmo se o vencimento nao mudar. Testes hermeticos incluem negacoes, grant revogado, clocks, Core indisponivel e concorrência.

Nao ha alteracao do manifesto Core, grants, roles DB, endpoints, migrations, segredos, servicos ou deploy. O grant it-portal.deploy.prepare AINDA NAO EXISTE como capacidade ativada neste pacote; testes usam Core simulado. A saida so comprova a leitura fresh do Core, sem conceder PREPARE ou ACT, e o diagnostico segue default OFF e invisivel ao MCP. Detalhes: [27-atlas-p22h2v-x-core-hml-gates.md](./27-atlas-p22h2v-x-core-hml-gates.md).

**Estado atualizado:** PR [#218](https://github.com/roberiooliveiradev/delpi-central/pull/218) integrada a main em 16/11/2026, CI 5/5 checks aprovados; nenhuma acao em producao. Revisao delpi-verifier independente, grants reais, identidade do host, backup/rollback/migracoes permanecem nao comprovados. Para futuro piloto HML restam aprovacao do owner, papel DB SELECT challenges segregado, transporte autenticado para o host, identidade do coletor, credenciais S2S, prova real de restauracao/rollback e migrations, RBAC humano nominativo e writer one-shot governado. PREPARE e ACT ficam OFF.


## 38. P2.2h.2y-aa: Keycloak S2S do coletor HML, evidencias de recuperacao e decisao consolidada (16/11/2026)

Lote integrado com tres contratos conectados: (y) `atlas_deploy_hml_s2s_collector.py` reusa o validador criptografico JWT S2S compartilhado para um cliente tecnico Keycloak explicitamente allowlisted, audience fixa, scope candidato `it-portal.atlas.hml.observe`, alvo host/container/Compose HML e token de curta duracao. Um token Keycloak autentica o CLIENT, nao o processo OS, transporte mTLS nem integridade do host. (z) `atlas_deploy_hml_recovery_review.py` confere apenas consistencia e frescor das referencias de inventario de backup, restauracao, rollback para ImageID-base e review de migracao, com suposta segregacao de observador/revisor; NENHUMA dessas alegacoes e tratada como prova de restauracao, rollback ou migracao segura. (aa) `atlas_deploy_hml_technical_admission.py` executa S2S primeiro, depois o diagnostico HML existente que revê Core humano fresco + release assinada + host HMAC + challenge PostgreSQL, checa validade S2S apos processamento e integra diagnostico de recuperacao. Resultado sempre status BLOCKED, prepare_eligible=False e can_execute=False. Testes negativos com JWT fake validado pela politica REAL do shared, sem Keycloak/JWKS real; sem rede, grant, host ou banco empresarial. Ver [28-atlas-p22h2y-aa-hml-s2s-recovery.md](./28-atlas-p22h2y-aa-hml-s2s-recovery.md).

**Estado atualizado:** PR [#219](https://github.com/roberiooliveiradev/delpi-central/pull/219) integrada em 16/11/2026 com 5/5 checks CI aprovados. Sem deploy em producao; nenhum cliente Keycloak, escopo, segredo, role/grant DB, migration, socket ou servico foi provisionado. Antes de qualquer piloto operacional, aprovar configuracao Keycloak S2S dedicada, canal do coletor sob identidade OS, proxy Docker GET restrito, papel SELECT challenge exclusivo, grants Core nominativos e prova real de restauracao e rollback. PREPARE e ACT permanecem desabilitados. Nenhum comando de deploy PROD.


## 39. P2.2h.2ab-ad: preflight local HML real, somente leitura, sem agente instalado (16/11/2026)

**Complemento P2.2h.2ah (PR Draft, sem deploy):** o ensaio manual com a conta tecnica atlas-hml confirmou que o Git recusa o checkout compartilhado por dubious ownership; a excecao safe.directory por comando provou apenas leitura diagnostica, nao atestacao. O pacote P2.2h.2ah introduz leitura direta e limitada de .git/HEAD e refs/heads/main, sem processo Git e sem acesso a .git/config, com status metadata_only_untrusted, limpeza desconhecida e PREPARE/ACT OFF. Veja [31-atlas-hml-head-metadata-only.md](./31-atlas-hml-head-metadata-only.md).

Pacote integrado de tres capacidades: (ab) **inspecao OS real** de UID/EUID, grupo privilegiado e permissao de escrita no checkout fixado, recusando observar Git/Docker quando processo opera como root, setuid, grupo docker/sudo/wheel ou usuario com checkout mutavel; (ac) **sonda local Git + Docker**, com GitCheckoutReadOnlyObserver existente (comandos Git sem locks e status de tracked/untracked nao ignorados) e DockerReadOnlyInspect existente, apenas GET do container HML canonico, via socket UNIX FIXO /run/atlas-hml-readonly/inspect.sock, sem acesso ao docker.sock bruto, TCP ou execucao; o socket deve ser provisionado separadamente pelo owner e seu GET-only policy auditado independentemente. Se proxy inexiste ou nao passa checagem de path, reporta a ausencia sem acessa-lo; (ad) **CLI de preflight explicito**, uma invocacao, saida JSON sanitizada, testes com repositorio Git temporario, Docker GET simulado, grupos/UID, symlink/socket/world-writable e tratamento de erros. Todo resultado continua status=blocked, prepare_eligible=False, can_execute=False, identidade OS/transporte/rollback/nonce nao atestados. Modulo: linux-ops-mcp/linux_ops_mcp/atlas_hml_local_probe.py; testes: linux-ops-mcp/tests/test_atlas_hml_local_probe.py. Documento: [29-atlas-p22h2ab-ad-hml-local-preflight.md](./29-atlas-p22h2ab-ad-hml-local-preflight.md).

**Estado atualizado:** PR [#220](https://github.com/roberiooliveiradev/delpi-central/pull/220) mesclada a main em 16/11 (America/Sao_Paulo), com 5/5 checks CI aprovados. Nao requer deploy: para executar manualmente a CLI e necessario somente git pull --ff-only no checkout e Python com httpx; diagnostico nunca faz deploy. Revisoes delpi-verifier independente e humana nao comprovadas. Nao ha API/MCP endpoint, container, Keycloak grant, socket, proxy, credencial, migration, network listener ou deploy. Comando manual futuro para verificar a postura, **somente apos merge** e pull executado pelo operador:
\`cd /home/operador/projetos/delpi-central && PYTHONPATH=linux-ops-mcp python3 -B -m linux_ops_mcp.atlas_hml_local_probe\`
A execucao nao modifica PROD, mas leitura real em HML exige autorizacao do owner e confirmacao de politica do proxy se este for instalado. Return code 0 significa apenas que um JSON de diagnostico foi impresso, nunca que o deploy e seguro. O usuario operador atual provavelmente tem permissoes de escrita no checkout; a ferramenta devera apresentar bloqueios ate existir uma conta OS dedicada de menor privilegio. PREPARE/ACT seguem OFF.


## 40. P2.2h.2ae-ag: proxy UNIX de Docker GET HML, source-only e sem servico instalado

Pacote integrado unico: (ae) um handler local que **nao abre nem cria sockets**, recebe unicamente FD de socket UNIX pre-bound em caminho fixado /run/atlas-hml-readonly/inspect.sock por futuro supervisor independente, exige UID do coletor nao-root via SO_PEERCRED do kernel e path/owner/permissoes de diretorio/arquivo seguros; (af) parse minimo e limitado de HTTP, aceitando **exatamente GET /containers/delpi-hml-public-hub/json** com Host docker.local e sem corpo, sem metodos mutantes, query, pipelining, autorizacao HTTP, headers de transporte ou caminho alternativo; executa no maximo uma leitura DockerReadOnlyInspect de container/Compose allowlisted, emitindo JSON **reduzido** a Id, Image, Name, labels Compose e estado Running/Health. Nunca devolve Env, mounts, token, Docker raw JSON nem comandos; (ag) integracao de ponta a ponta em testes com socket UNIX real, HTTPX AsyncHTTPTransport UDS, Docker MockTransport, cliente DockerReadOnlyInspect real e casos negativos (UID, POST, paths, comprimento, symlink, raw alias, modo permissivo, status/erro upstream), preservando CI Linux MCP + CI ATLAS e runbook operacional. Modulo: linux-ops-mcp/linux_ops_mcp/atlas_hml_unix_proxy.py; testes linux-ops-mcp/tests/test_atlas_hml_unix_proxy.py. Detalhes: [30-atlas-p22h2ae-ag-hml-uds-proxy.md](./30-atlas-p22h2ae-ag-hml-uds-proxy.md).

**Estado atualizado:** PR [#221](https://github.com/roberiooliveiradev/delpi-central/pull/221) mesclada em 16/11 (BRT) com 5/5 checks CI aprovados; codigo do proxy nao foi instalado no servidor e ainda depende de revisoes independentes. Nenhum daemon/CLI/autostart/servico Unix socket, grant, Keycloak, migracao, container, proxy real ou credencial foi provisionado em HML/PROD. O novo codigo NAO atesta que a politica do supervisor Docker esta correta: a fonte upstream continua precisando de revisao humana independente e acesso minimo. Um client UNIX validado por UID NAO atesta automaticamente a identidade remota nem da direito a PREPARE. Toda resposta local SingleRequestProxyResult tem status blocked, prepare_eligible=False e can_execute=False. Nao mesclar automaticamente; PREPARE/ACT OFF.


## 41. P2.2h.2ai-ak: hardening da politica UNIX HML source-only (16/11/2026)

**Estado:** PR Draft em revisao, sem alteracoes de servidor. O proxy e o preflight compartilham agora uma politica unica de identidade local, grupo e permisos do socket HML, conferem um listener AF_UNIX em escuta e vinculam a allowlist de UID ao usuario nominal `atlas-hml`, limitando tambem o deadline da consulta. Novos testes negativos usam somente sockets descartaveis. **Sem instalacao, supervisor, alteracao de grupos, Docker real, Keycloak ou deploy.** CI e revisao independente devem ser conferidos na PR. [Runbook P2.2h.2ai-ak](./32-atlas-hml-uds-policy-hardening.md). **PREPARE/ACT permanecem OFF**; SHA de HEAD continua diagnostico nao confiavel.

## 42. P2.2h.2al-an: guard source-only para upstream Docker Engine HML (17/11/2026)

**Estado:** PR Draft candidata, sem deploy. PR #223 foi mesclada em 17/11/2026 com 5/5 checks de CI no head final, sem habilitacao do proxy. O proximo lote adiciona `HMLDockerGETTransport` e `HMLDockerInspectOnly` para exigir, dentro de um futuro processo upstream, somente GET do container `delpi-hml-public-hub`, alvo HML exato, limites de headers e corpo e recusa de redirects, upgrade e respostas inesperadas. Testes de HTTPX MockTransport, CI Docker/PostgreSQL descartaveis e suite Linux MCP cobrem a interface, **nao o isolamento de privilegios do host**. Acesso ao socket bruto Docker continua sendo poder elevado, independentemente do guard Python. Revisor humano e `delpi-verifier` pendentes. [Runbook 33](./33-atlas-hml-engine-guard-source-only.md). PREPARE/ACT OFF, nenhuma instalacao/alteracao de servico/socket/Keycloak/DB.

## 43. P2.2h.2ao-aq: cadeias de observacao HML integradas no CI (17/11/2026)

**Estado:** PR Draft, CI e verificacao independente por confirmar; nenhuma instalacao ou deploy. [PR #224](https://github.com/roberiooliveiradev/delpi-central/pull/224) foi mesclada em 17/11 (merge commit `911ff0f7da6310be613030a800a9951eaed2f6ff`), mas seu guard de transporte ainda era um componente source-only. Este incremento vincula o caminho HML real do proxy ao inspector `HMLDockerInspectOnly` por tipo exato e reutiliza o `HML_TARGET` canonico. Um teste descartavel cobre `DockerReadOnlyInspect` por socket AF_UNIX, `serve_one_prebound`, `HMLDockerInspectOnly` e upstream HTTPX mockado, incluindo recusa de identidade, metodo, alvo, Compose e resposta indevida. Um ensaio tambem liga o leitor ao `inspect_hml_local`, que **continua BLOCKED**. Nao concede poderes Docker ao MCP, nao instala socket, servico, supervisor ou configura o servidor, e **nao atesta isolamento do upstream**. Revisao humana e `delpi-verifier` continuam gates de seguranca obrigatorios. [Runbook e criterios de aceite](./34-atlas-hml-boundary-chain-acceptance.md). PREPARE/ACT OFF.

## 44. P2.2h.2ar-at: Engine real descartavel por detras do proxy HML (17/11/2026)

**Estado:** PR Draft candidata, sem alteracoes no servidor. [PR #226](https://github.com/roberiooliveiradev/delpi-central/pull/226) mesclada em 17/11/2026 (merge commit `102ecff8d3b07f7071b636471a7e00028abcabd3`), com 5/5 checks de CI na HEAD da PR. Os testes anteriores usavam `httpx.MockTransport` como Engine. Este novo pacote realiza a **cadeia completa em runner GitHub-hosted descartavel com Docker Engine real**: leitor Docker via socket UNIX temporario, proxy `serve_one_prebound`, guard `HMLDockerInspectOnly` e GET do contêiner efemero que imita somente o alvo `delpi-hml-public-hub`. Casos negativos de metodo, destino, header e UID medem 0 consultas encaminhadas ao Engine. CI isolado cria e remove a fixture automaticamente; **nunca** usa o `srv-api` nem instala proxy ou daemon. `status=BLOCKED`, `prepare_eligible=false` e `can_execute=false` permanecem. O isolamento real do processo upstream, a identidade OS do host, restauracao/rollback, aprovacao Core e challenge continuam pendentes. [Runbook 35](./35-atlas-hml-real-engine-chain-ci.md). PREPARE/ACT OFF; revisoes independentes obrigatorias.

## 45. P2.2h.2au-ax: diagnostico de isolamento OS do coletor HML, manual e READ-only (17/11/2026)

**Estado:** PR Draft candidata, sem deploy, verificacao CI e revisao independente pendentes. A [PR #227](https://github.com/roberiooliveiradev/delpi-central/pull/227) foi integrada em 17/11/2026 (merge commit `cad2b36e84b624117aa335de7b7c186c6e5aa1f8`), apos 5/5 checks CI no head; o job Docker real descartavel passou 242 testes, o Linux MCP 472 com 9 skips. Essa prova **nao** atesta o processo Linux da DELPI. O novo `atlas_hml_collector_isolation.py` coleta exclusivamente evidencias momentaneas da conta `atlas-hml` (NSS, grupos, checkout write, `os.access` aos sockets Docker conhecidos, capabilities, NoNewPrivs, seccomp, variaveis Docker sem valores), sem conectar a nenhum socket nem modificar servidor. Cada campo ausente/invalido causa bloco; ate com todos os campos positivos, `status=blocked`, `prepare_eligible=false`, `can_execute=false` e atestacoes continuam falsas. Os testes e CI garantem somente contrato do codigo; revisao independente de host, isolamento upstream, restore/rollback, Git integro, grants Core e challenge permanecem pendentes. [Runbook 36](./36-atlas-hml-collector-isolation-review.md). PREPARE/ACT OFF, nenhuma instalacao ou alteracao de servico.

## 46. P2.2h.2ay-bb: dossie unificado de pre-ativacao HML, metadata-only (17/11/2026)

**Estado:** PR Draft, CI e revisao independente pendentes, sem deploy nem alteracao no `srv-api`. [PR #229](https://github.com/roberiooliveiradev/delpi-central/pull/229) mesclada em 17/11/2026, merge commit `b2a7cd3c9631bece590d0b06252cca58ec3b144d`; no HEAD da PR a suite Linux MCP teve 555 PASS e 9 SKIP, Docker CI 325 PASS, e 5/5 checks verdes. O codigo da PR #229 **ainda nao tem medicao real de isolamento do host pelo operador**. Este pacote entrega uma CLI adicional `atlas_hml_host_review_bundle.py` que unifica postura da conta tecnica, `.git/HEAD` metadata-only e verificacao **somente de metadados** do socket HML, num unico JSON sanitizado. Contas inseguras nao leem sequer Git/socket. O bundle nao executa Git nem conecta a Docker; mesmo com todos os checks positivos, `status=blocked`, HEAD nao confiavel, ausencia de atestacao independente, `prepare_eligible=false` e `can_execute=false`. O plano futuro de isolamento e permissao do upstream com acesso ao Docker Engine, o `delpi-verifier`, Core, restauracao, rollback e challenge continuam bloqueados. [Runbook 37](./37-atlas-hml-host-review-bundle.md). PREPARE/ACT OFF.

## 47. P2.2h.2bc-bf: proposta de isolamento do supervisor e contrato snapshot HML (17/11/2026)

**Estado:** Draft PR source-only, com CI e revisao independente a confirmar; nenhuma instalacao no `srv-api`. A PR #230 ja foi mesclada em `cdfd7bff83d91c0dc662b9ee47bd4117ce287c7a`; o dossie executado pelo operador confirma privilegios limitados do `atlas-hml` (DAC, grupos e capabilities), mas `HML_PROXY_UNAVAILABLE` continua. A [issue #232](https://github.com/roberiooliveiradev/delpi-central/issues/232) registra a escolha de arquitetura ainda pendente. Este pacote propõe, **sem aprovar**, a alternativa de produtor one-shot com Docker temporario + snapshot reduzido + apresentador UDS sem Docker; o processo produtor elevado ainda exige auditoria independente. Inclui `atlas_hml_snapshot_candidate.py`, validador **puro** de JSON HML, com limite de 2048 bytes e tempo autodeclarado; rejeita PROD, campos extra, chaves duplicadas, IDs/booleans invalidos, stale/future; em todos os casos aceitos, `status=blocked`, `prepare_eligible=false`, `can_execute=false`. **Nao** possui IO, socket, service, daemon, produtor, autenticacao do snapshot, leitura de arquivo nem nova tool MCP. [Runbook/ADR candidata 38](./38-atlas-hml-supervisor-architecture-proposal.md). PREPARE/ACT permanecem OFF; review humano, `delpi-verifier`, CI final e aprovacao de arquitetura ainda obrigatorios.

## 48. P2.2h.2bg-bj: leitura segura candidata do arquivo snapshot HML por descriptor (17/11/2026)

**Estado:** nova PR Draft source-only, CI e revisao independente ainda exigidos; **zero modificacoes no srv-api**. [PR #234](https://github.com/roberiooliveiradev/delpi-central/pull/234) mesclada em `009373b20066907b1a8fa31d2b1098a004d86d90`, com 5/5 checks (Linux 599 PASS, Docker descartavel 369 PASS, PG/arquitetura/audit PASS). O parser do snapshot `atlas_hml_snapshot_candidate.py` permanece **somente contrato**, sem autenticidade. Este incremento entrega `atlas_hml_snapshot_file_reader.py`, um leitor de arquivo HML fixo `/run/atlas-hml-readonly/inspect-snapshot.json` por descritor POSIX, sem criar arquivos/servicos; exige diretório root:`atlas-hml` modo 0750, arquivo root:`atlas-hml` modo 0640, regular, hardlink unico, leitura pequena (max 2048 B), `O_NOFOLLOW`, comparacao de inode/metadados antes/depois e mtime recente. Testes negativos apenas em `tmp_path` incluem symlink, hardlink, FIFO, owner/GID/mode, arquivo trocado e dados stale/PROD. **Metadata POSIX e JSON recente nao atestam produtor nem escrita atomica e nao autorizam PREPARE/ACT**. Nao ha produtor, scheduler, apresentador UDS, Docker real DELPI, API/Keycloak/DB ou alteracao de supervisor. [Runbook 39](./39-atlas-hml-snapshot-file-reader.md). A alternativa B segue **nao aprovada** ate decisao e revisao independente da [issue #232](https://github.com/roberiooliveiradev/delpi-central/issues/232). PREPARE/ACT OFF.

## 49. P2.2h.2bk-bn: publicacao atomica candidata do snapshot HML, source-only (17/11/2026)

**Estado:** PR Draft, CI e revisao independente por confirmar; nenhuma alteracao no `srv-api`. [PR #236](https://github.com/roberiooliveiradev/delpi-central/pull/236) mesclada em `0531a525eadf24fb7db3f18f1d04dbf76d1226b2`, com cinco checks PASS (Linux 626 PASS/9 SKIP, Docker CI 396 PASS, PostgreSQL/arquitetura/audit PASS). O leitor de snapshots POSIX nao foi instalado ou ativado no host. Este lote implementa `atlas_hml_snapshot_publisher_candidate.py`: gerador puro de JSON HML tipado, helper **interno** de publicacao atomica em diretorio de fixture, `O_EXCL|O_NOFOLLOW`, owner/GID/modes fixos, `fsync` de arquivo/diretorio, `os.replace` e revalidacao de inode final. Testes isolados cobrem substituicao de geracoes, destino inseguro, escrita parcial, falha no rename/fsync, troca de stage e rejeicao de PROD/stale. **Nao** existe CLI, produtor Docker, timer, daemon, socket ou mecanismo de deploy. Atomicidade local nao prova autenticidade do produtor, isolamento do Docker, anti-replay ou rollback real. Alternativa B ainda **nao aprovada** e exige revisor independente, `delpi-verifier`, mudanca autorizada e testes no servidor. [Runbook 40](./40-atlas-hml-snapshot-atomic-handoff.md); [issue #232](https://github.com/roberiooliveiradev/delpi-central/issues/232). PREPARE/ACT OFF.

## 50. P2.2h.2bo-br: cadeia one-shot GET Docker HML -> snapshot atomico -> leitor FD, CI-only (17/11/2026)

**Estado:** PR Draft, CI e revisao independente a confirmar, nenhum deploy no `srv-api`. [PR #237](https://github.com/roberiooliveiradev/delpi-central/pull/237) mesclada em `d1e23f930ff472cdc022288e500ae271358f4917`; seu HEAD teve 5/5 checks PASS (Linux 652 PASS/9 SKIP, Docker CI 422 PASS, PG/arquitetura/audit PASS). O publicador atomico de PR #237 permanece **somente candidato**. Novo pacote `atlas_hml_one_shot_candidate.py` liga o `HMLDockerInspectOnly` estrito ao JSON de 11 campos e publicador `tmp_path`, exercitando read-back por FD em testes com MockTransport e **Docker Engine real somente no runner GitHub descartavel**. O runner fornece o transporte e diretorio; nao ha CLI, service/timer, produtor instalado, novo socket, MCP tool ou acesso ao Docker DELPI. Falha da consulta nao publica nova geracao, falha previa ao rename preserva a anterior, todas as respostas permanecem `status=blocked`, `prepare_eligible=false`, `can_execute=false`. Sem parecer humano independente a arquitetura B segue NAO APROVADA e **nao fornece isolamento verificavel** do processo que podera deter `docker.sock`. Requer delpi-verifier, revisao de Seguranca, rollback real, atestacao e autorizacao separada antes de qualquer HML. [Runbook 41](./41-atlas-hml-one-shot-candidate.md); [issue #232](https://github.com/roberiooliveiradev/delpi-central/issues/232). PREPARE/ACT OFF.

## 51. P2.2h.2bs-bv: pacote de revisao independente da fronteira de privilegios HML (17/11/2026)

**Estado:** PR Draft source-only, CI e parecer independente ainda por confirmar, servidor `srv-api` intocado. A [PR #239](https://github.com/roberiooliveiradev/delpi-central/pull/239) foi mesclada em `a37e1400e24cfaf7560ab81139a825122e5c5f70` apos 5/5 checks PASS (Linux MCP 665 PASS/10 SKIP, Docker CI 436 PASS, PostgreSQL/arquitetura/audit PASS). O fluxo one-shot de HML funciona **apenas no CI descartavel**, nao existe produtor ou presenter instalado. Esta entrega adiciona **cinco blueprints `.review` nao instalaveis** de service/timer/socket/diretorio runtime, com `ExecStart=/usr/bin/false`, condicao artificial de ativacao, sem [Install] e `RefuseManualStart=yes`. O modulo `atlas_hml_supervisor_blueprint_review.py` compara o texto contra um contrato lexical estrito; testes recusam drift (grupo docker para presenter, socket 0666, sudo, capacidades, modo directory, paths Docker, nomes de unidade, ExecStart real). Tudo permanece `status=blocked`, `architecture_approved=false`, `prepare_eligible=false`, `can_execute=false`. As restricoes `systemd` sugeridas **nao constituem sandbox do processo root com acesso ao Docker Engine**, e o pai do UDS precisa ter grupo `atlas-hml` independente de `SocketGroup`. `delpi-verifier`, isolamento do host, decisao humana da [issue #232](https://github.com/roberiooliveiradev/delpi-central/issues/232), instalacao HML, revogacao/rollback e Core permanecem PENDENTES. [Runbook 42](./42-atlas-hml-supervisor-blueprint-review.md). PREPARE/ACT OFF.

## 52. Gate de decisao externa para isolamento do supervisor ATLAS HML (17/11/2026)

**Estado: DECISION_REQUIRED / apenas documentacao / sem deploy.** A [PR #240](https://github.com/roberiooliveiradev/delpi-central/pull/240) foi mesclada em `3013859c2654b1f6727cf93e89616febbf0affb8`; a main avancou depois com PRs de outros modulos. A etapa 51 entregou blueprints `.review` e CI descartavel, mas **nao atestou o processo privilegiado, o isolamento real no host, a origem do snapshot ou a reversao operacional**. A alternativa B segue candidata, sem aprovacao formal.

O novo [runbook 43 de decisao independente](./43-atlas-hml-independent-security-decision-gate.md) organiza o parecer da [issue #232](https://github.com/roberiooliveiradev/delpi-central/issues/232) em dez obrigacoes de evidencia (SEC-01 a SEC-10), compara os riscos A/B/C e registra criterios de recusa, segregacao do produtor root, demonstracao negativa de Docker bruto no apresentador, FD/ACL/UDS, autenticidade/replay do snapshot e rollback sem impacto PROD. **Nao e uma aprovacao nem uma operacao.**

**Proximo gate real:** parecer humano Linux/Seguranca independente e `delpi-verifier`, seguido da decisao nominativa do owner na issue #232. Nao criar instaladores, unidades operacionais ou permissoes antes da decisao; eventuais ensaios no `srv-api` exigem autorizacao separada. Todos os MCP tools seguem 4 READ; PREPARE/ACT OFF. **Progresso estimado permanece 52%** ate evidencia de isolamento e homologacao real.

## 53. P2.2h.2bw: prova OS real de fronteira Docker e snapshot em GitHub Actions descartavel (17/11/2026)

**Estado:** PR source-only aguardando CI e revisao independente, sem deploy. A [PR #242](https://github.com/roberiooliveiradev/delpi-central/pull/242) foi mesclada em `36e1e3631a5b03528796220732046e08a6420e01` (runbook 43), mas a [issue #232](https://github.com/roberiooliveiradev/delpi-central/issues/232) permanece ABERTA **sem comentarios de parecer humano ou decisao de arquitetura A/B/C**. A proxima prova automatizavel, sem instalar nada no host, e um ensaio de identidade de processo e FD em runner Docker descartavel.

O novo `test_atlas_hml_os_boundary_real_ci.py`, disparado via job `disposable-docker` da GitHub Actions, reduz UID/GID/grupos do child para `nobody` e demonstra: (CI-OS-01) uma **conexao nova** ao Docker Engine e negada por DAC; (CI-OS-02) uma conexao **previamente aberta e herdada** continua util mesmo apos perder UID, expondo o risco real de FDs privilegiados; (CI-OS-03) leitor consegue acessar snapshot root:grupo 0640 em diretorio root:grupo 0750 mas nao pode escrever, criar arquivos ou ler artefatos privativos, e o resultado permanece BLOCKED. O unico HTTP do novo ensaio e `GET /_ping` do Docker **da runner descartavel**, sem mutacoes no daemon nem no `srv-api`. Veja [runbook 44](./44-atlas-hml-disposable-os-boundary-evidence.md).

**Limitacao fundamental:** CI-OS-01..03 sao demonstracoes **somente na runner**, nao comprovam a identidade, heranca de FDs, isolamento, ACL, namespace, seccomp, LSM ou recuperacao reais do servidor. A arquitetura B ainda e **candidata nao aprovada**; Security/owner precisam emitir parecer independente e decisao na issue #232, complementado pelo `delpi-verifier`. Sem novos serviços, sockets, usuarios, grupos, Keycloak, migrations, Docker PROD/HML, grants, PR de executaveis ou habilitacao PREPARE/ACT. **Percentual mantido: 52%** ate validacao operacional verdadeira.

## 54. P2.2h.2bx: fail-closed de ACL POSIX no handoff snapshot HML (17/11/2026)

**Estado: Draft PR [#245](https://github.com/roberiooliveiradev/delpi-central/pull/245) source-only, CI 5/5 PASS no commit `3aeeaf7f3a0677051db33a421dd46a37de82f966`, verificador e parecer independente pendentes, zero deploy.** Os resultados CI naquele commit: Linux MCP **717 PASS/13 SKIP + 17 subtests PASS**, Docker descartavel **488 PASS + 17 subtests PASS**, ensaios OS **3/3 PASS**, PostgreSQL, arquitetura e auditoria **PASS**.  A [PR #243](https://github.com/roberiooliveiradev/delpi-central/pull/243) foi integrada a main em `972a20522821079cf72dc24933d86e8d5e633e96`. Os ensaios CI da PR anterior demonstraram que a negativa DAC do Docker socket nao revoga um FD ja herdado e que snapshots root:grupo podem ser lidos sem permissao de escrita no runner descartavel. A [issue #232](https://github.com/roberiooliveiradev/delpi-central/issues/232) continua aberta **sem decisao humana de arquitetura A/B/C e sem parecer independente de Seguranca**.

Esta etapa endurece o contrato candidato de snapshots ao verificar por descritores POSIX ausencia de `system.posix_acl_access` e, nos diretorios, `system.posix_acl_default`, alem de owner/mode/inode existentes. **Somente ENODATA** permite continuar; ACL adicional, EACCES, EOPNOTSUPP, API ausente ou falha inesperada permanecem bloqueios. O leitor confere antes/depois; o publicador confere diretorio, destino existente (via FD com identity match), stage e estado apos rename. Testes descartaveis cobrem ACL falsa, falha de sondagem, TOCTOU simulado e preservacao de snapshot antigo. Ver [runbook 45](./45-atlas-hml-snapshot-posix-acl-review.md).

**Limites:** verificar ACL nao autentica produtor root, nem impede acesso ao Engine por FDs, redes e aliases; nao substitui MAC/LSM, isolamento real, runbook de rollback e revisao humana. Nenhuma alteracao em host, Docker, Keycloak, Core, DB, grants, systemd, socket, identidade Linux ou APIs. Quatro ferramentas MCP continuam READ; todos os resultados candidatos seguem `status=blocked`, `prepare_eligible=false` e `can_execute=false`. **Progresso estimado: 52%**, sem evolucao artificial por testes/contratos; proxima etapa depende da decisao na issue #232 e `delpi-verifier`.

## 55. P2.2h.2by: arquitetura B escolhida como direcao de desenvolvimento e presenter snapshot-only (17/11/2026)

**DECISAO DO OWNER:** arquitetura B aprovada **somente para desenvolvimento**, sem autorizacao de instalacao em HML/PROD. A decisao foi registrada na [issue #232](https://github.com/roberiooliveiradev/delpi-central/issues/232#issuecomment-6956046761). O `delpi-verifier` da PR #245 concluiu em rodada 1 com `ACCEPT_WITH_RESIDUAL`, zero ordens de correcao e independencia entre Cursor `composer-2.5` e GPT-6; CI verificado; os riscos de falta de parecer humano, FD Docker herdado, autenticidade do snapshot e rollback **continuam**. Nao registrar como SEC-01 satisfeito por IA.

**Entrega desta etapa:** codigo candidato `atlas_hml_snapshot_presenter_candidate.py`, **sem entrypoint nem wiring MCP**, para servir um unico GET em UDS AF_UNIX previamente aberto por fixture, com `SO_PEERCRED` real, politica de ownership e request estrita. Usa somente leitor FD de snapshot e retorna JSON minimalista com `status=blocked` e `prepare_eligible=false/can_execute=false`. Nenhum cliente Docker, bind, listener persistente, timer, service, DB ou novo grant. Testes com UDS real em `tmp_path` recusam UID indevido, metodos e paths maliciosos, payloads, snapshot PROD/stale/symlink/ACL invalido e falso `SnapshotDiagnostic`. Workflow ATLAS no CI descartavel e gate de Linux MCP devem permanecer verdes. Detalhes e limites no [runbook 46](./46-atlas-hml-architecture-b-presenter-candidate.md).

**Gates que ainda bloqueiam operacao:** `delpi-verifier` da PR desta etapa; SEC-01 independente humano ou decisao de excecao formal pelo responsavel; prova real de ausencia de Docker raw e FD herdado no presenter, isolamento do produtor privilegiado, snapshots autenticos, UDS/ACL/systemd reais, janela e rollback no `srv-api`, sem impacto no Public Hub PROD. **PREPARE/ACT OFF, 4 tools MCP READ. Progresso geral segue 52% ate ensaio real no host.**

## 56. P2.2h.2bz: prova real de isolamento de processos e FDs em CI descartavel para arquitetura B (17/11/2026)

**Estado:** Draft PR fonte/teste-only; CI e verificador desta PR ainda por confirmar; **sem operacao de host**. A PR [#251](https://github.com/roberiooliveiradev/delpi-central/pull/251) foi integrada em `2998b25c7b26287aec13958c1689b1210936ce2d`, depois de `delpi-verifier` Cursor `ACCEPT_WITH_RESIDUAL`, zero OCs. A [issue #232](https://github.com/roberiooliveiradev/delpi-central/issues/232) registra a escolha da arquitetura **B como direcao de codigo**, e nao autoriza instalacao.

Nesta etapa, `test_atlas_hml_presenter_process_boundary_real_ci.py` executa o presenter candidato em **processo Linux efetivamente nao-root** (`nobody`) e cliente UNIX separado, com listener UDS prebound, snapshot `root:nobody` em `/tmp` efemero, grupos suplementares vazios e `subprocess(... close_fds=True, pass_fds=(listener,))`. A prova contrasta a **negação de conexao direta ao Docker** e a **ausencia de FD Docker herdado** apos `exec` com um controle negativo que herda propositalmente esse FD e deve recusar antes de servir. GET HML retorna diagnostico `BLOCKED`; GET PROD/POST sao negados. Tudo roda somente no workflow Docker descartavel, sem comando mutante Docker. Veja [runbook 47](./47-atlas-hml-disposable-process-fd-boundary.md) com matriz B-OS-01..05, limites e planejamento operacional futuro.

**Sem atestacao no `srv-api`:** `nobody` no CI nao substitui o real `atlas-hml`/systemd. A prova nao inspeciona FDs da unidade real, aliases, ACLs e namespaces do host, autenticidade do produtor root ou rollback. `delpi-verifier` independente desta PR, parecer humano/decisao de excecao na governanca, SEC-01..10, autorizacao formal HML e ensaios de rollback **seguem exigidos antes de ativar componentes**. Quatro ferramentas MCP seguem READ, `PREPARE/ACT OFF`. **Progresso total estimado permanece 52% ate evidencia operacional.**
