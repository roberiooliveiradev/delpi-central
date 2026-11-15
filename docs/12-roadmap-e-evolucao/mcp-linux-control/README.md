# ATLAS — Roadmap mestre e fonte de continuidade

> **Projeto:** ATLAS — Infraestrutura Linux e Orquestracao de Operacoes DELPI
> **Owner:** TI / Minha DELPI
> **Atualizacao:** 2026-11-15
> **Situacao em 2026-11-15:** P1 READ autenticado e operando; P2.1 politica offline integrada na main com CI verde via PR #191; **P2.2b leitores GitHub/CI e Core fresh adicionados na main, validacao CI e verificador independente pendentes; nenhuma ferramenta de deploy publicada**.
> **Repositorio:** `roberiooliveiradev/delpi-central`; **PRs integradas:** [#184](https://github.com/roberiooliveiradev/delpi-central/pull/184) (P0-P1), [#191](https://github.com/roberiooliveiradev/delpi-central/pull/191) (P2.1); **P2.2a/P2.2b em codigo main, sem executor/endpoint e sem deploy**.
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

| Marco | Entrega | Estado em 15/11/2026 | Gate de aceite |
|---|---|---|---|
| A0 | Inventario de `srv-api`, limites e riscos | DOCUMENTADO | Evidencia sem secrets, arquitetura de acesso aprovada |
| A1 | MCP privado/publicado HTTPS + Keycloak OAuth + READ | **OPERADOR_CONFIRMOU_PASS** | Consulta real `get_host_health` pelo ChatGPT com snapshot/timestamp |
| A1-R | Lacunas CPU %, contagem Docker, `partial` | ADIADO_POR_DECISAO_DO_OWNER | So reabrir conforme nova prioridade, sem condicionar o deploy |
| A2.0 | Contrato de deploy, boundaries, aprovacao e testes negativos | DOCUMENTADO_EM_PR | Documento P2-P4 revisado, sem runtime |
| **A2.1** | **Modulo puro de politica de preview: allowlist, SHA, CI/attestation, TTL, hash, tests** | **MERGED_PR_191 / CI_PASS** | Sem I/O, deny by default, testes negativos locais e CI; nenhuma tool ACT |
| A2.2 | Atestacao GitHub/CI/host/Core, journal transacional, versao instalada e API PREPARE | **P2.2a/P2.2b LEITORES_MAIN / CI_PENDENTE; HostProof, journal persistente e API pendentes** | Permissoes separadas, CI por SHA, concorrencia/revogacao testadas |
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

**Proxima tarefa:** A2.2c: obter evidencia real/autorizada de revisao por servico no host (nao confundir checkout HEAD com release em execucao), coordenar owner da migration com Delpi Remote, implementar journal transacional PostgreSQL e definir catalogo de CI/workflows por servico. API PREPARE e ACT continuam inativas ate review e HML; A3/A4 bloqueadas.

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
