# Delpi Remote | Fonte de verdade do projeto

**Estado em 2026-11-13:** inicio autorizado pelo responsavel de TI. Gate 0 (arquitetura e planejamento) documentado; revisao de seguranca e validacao operacional **pendentes**. NENHUM acesso remoto foi ativado por esta entrega.

**Repositorio:** `roberiooliveiradev/delpi-central`. **Issue principal:** [#179](https://github.com/roberiooliveiradev/delpi-central/issues/179).

## Como continuar este trabalho em outro chat ou por outro desenvolvedor

1. Ler **este README**, `ARCHITECTURE.md`, `SECURITY-GATES.md` e `EXECUTION-LOG.md`, nesta ordem.
2. Consultar a [issue #179](https://github.com/roberiooliveiradev/delpi-central/issues/179), o estado de `main`, os commits recentes e `AGENTS.md`.
3. Confirmar os estados reais no codigo e em teste. **Nao** inferir que documentos ou merge significam implantacao/homologacao.
4. Escolher a **primeira tarefa pendente** na tabela abaixo, sem saltar gates.
5. Ao concluir **cada tarefa**, atualizar **na mesma entrega** o estado deste arquivo e acrescentar uma entrada com evidencias ao `EXECUTION-LOG.md`. Linkar commit, testes, riscos, rollback, proxima tarefa e issue.
6. A integracao e o controle remoto devem permanecer **desabilitados por padrao** ate autorizacao e homologacao especificas.

## Escopo aprovado

Inventario corporativo de desktops e notebooks; agente de inventario; controle remoto pelo navegador usando servico self-hosted; tela, mouse, teclado, clipboard e transferencia de arquivos em fases; acesso nao assistido apenas para estacoes corporativas inscritas e autorizadas; auditoria e gestao pelo Portal de TI. Evitar custos de licencas de softwares proprietarios.

Acesso sem pedir senha Windows por sessao **nao** significa acesso anonimo: toda sessao exige identidade humana forte, politica do equipamento, permissoes especificas e auditoria. **Nao** implementar senha mestre compartilhada.

## Roadmap e checkpoints

| ID | Entrega | Estado | Criterio para encerrar |
|---|---|---|---|
| G0-DOC | Arquitetura, desenho de seguranca, contrato de inventario e plano de continuidade | **DOCUMENTADO** | Este pacote versionado e ligado a issue #179 |
| G0-SEC | Threat model/revisao de seguranca, LGPD, licenciamento, analise de compatibilidade de MeshCentral, redes e backups | **EM REVISAO** | Preflight automatizado e risco da release avaliados; **aceite formal ainda ausente** |
| G0-SEC-S0 | Auditoria estatica automatizada de bloqueio do controle remoto, matriz de 12 gates e ADR de risco | **EM REVISAO** | CI verde, revisao humana das evidencias e nenhum servico/rota remota habilitado |
| G0-SEC-S1 | Admissao offline de candidato MeshCentral, revisao de riscos conhecidos e integridade de artefatos | **EM REVISAO** | Gate CI `G3-LAB BLOCKED`, artefato exato/SHA256, mitigacao do exploit e teste Windows pendentes |
| G0-SEC-S2 | Minutas para TI/RH/Juridico: privacidade, rede isolada, revogacao e restore, com validacao offline | **EM REVISAO** | Revisao privada dos 10 checkpoints, definicao de retencao e RPO/RTO, topologia e testes negativos |
| G1-DOM | Regras puras para cadastro de estacoes + testes | **EM REVISAO** | Normalizacao, limites, catalogos e rejeicao de segredos validados |
| G1-API | Migration independente, CRUD de estacoes e RBAC separado de servidores | **EM REVISAO** | API e testes integracao verdes; nenhum agente remoto |
| G1-UI | Area Computadores, busca/filtros/detalhe no plugin it-portal | **EM REVISAO** | Permissoes e testes de UI; sem botao remoto ativo |
| G1-OWNER | Selecionar colaborador usuario da plataforma como responsavel do computador; vinculo por identidade estavel | **VALIDADO** | Busca seletiva, vinculacao por ID do Core, exibicao do nome, auditoria de troca e tratamento de usuarios inativos |
| G2-AGENT | Identidade por dispositivo e coletor read-only de telemetria Windows | **EM DESENVOLVIMENTO** | Piloto, autenticacao individual, reconciliacao idempotente e remocao segura |
| G2-S1 | Coletor Windows LOCAL + contrato estrito de snapshot, sem envio automatico | **EM REVISAO** | Execucao em PowerShell 5.1 no Windows piloto, testes e aceite do snapshot |
| G2-S2 | Identidade individual de agente e ingestao autenticada, revogavel e idempotente | **EM REVISAO** | Codigo de S2S com flag off, migration V011, testes integrados e piloto Keycloak pendentes |
| G2-S3 | Enrolment governado, agendamento Windows e desinstalacao de agente | **EM REVISAO** | Pacote assistido e testes em CI; assinatura corporativa, piloto Windows, revogacao e teste de rotina pendentes |
| G2-S4 | Provisionamento automatizado de identidades individuais, sem cadastro manual por computador | **EM DESENVOLVIMENTO** | Preparacao automatica, bootstrap seguro, binding dinamico e revogacao |
| G2-S4-S1 | Preparar Client Keycloak desabilitado pela ficha do Portal | **EM REVISAO** | CI API/UI/Postgres V012 aprovado; Keycloak HML, Windows real e feature off ate piloto |
| G2-S4-S2 | Bootstrap de uso unico, ativacao S2S, binding dinamico e revogacao | **EM DESENVOLVIMENTO** | S2a com vinculo DB/revogacao em codigo; S2b precisa Keycloak/Windows HML |
| G2-S4-S2a | Vinculo S2S dinamico por DB e revogacao individual Keycloak | **EM REVISAO** | V013 com grant OFF, testes CI e homologacao real pendentes |
| G2-S4-S2b | Bootstrap Windows de uso unico, attestation, ativacao e rotacao | **NAO INICIADO** | Sem secret no navegador; so ativar depois do piloto seguro e aceite |
| G3-ENGINE | MeshCentral isolado e testado em laboratorio | **BLOQUEADO** | Somente apos G0-SEC com aceite formal, versao/licenca/SBOM, TLS, backup e piloto isolado |
| G4-AUTH | Broker de sessoes, Keycloak/MFA e permissoes independentes | **NAO INICIADO** | Revogacao, tokens de uso unico, fail-closed, logs, kill switch |
| G5-REMOTE | Tela, teclado e mouse no navegador para computador piloto | **NAO INICIADO** | Testes presenciais de concorrencia, UAC, lock-screen, desconexao e latency |
| G6-EXTRAS | Clipboard bidirecional e arquivos | **NAO INICIADO** | Avaliacao e teste de DLP, escopos independentes, transferencia auditavel |
| G7-ROLLOUT | Implantacao em ondas SC/ES | **NAO INICIADO** | Aceite, notificacao aos usuarios, playbook suporte, rollback e monitoramento |

Status permitidos: NAO INICIADO, EM DESENVOLVIMENTO, DOCUMENTADO, EM REVISAO, VALIDADO, IMPLANTADO, BLOQUEADO. Nunca marcar `IMPLANTADO` sem evidencias do runtime; `VALIDADO` nao e sinonimo de CI verde.

**Publicacao G1 (evidencia recebida 13/11/2026):** operador executou a implantacao da API e do MFE; API `healthy`, migration V009 e tabela `it_portal.workstations` verificadas no PostgreSQL, frontend recriado (`Up 2 seconds`). **Pendente:** registrar/confirmar manifesto estrutural `0.3.4` e RBAC no Core, validar assets web e executar testes de usuario antes de considerar G1 homologado. Detalhes em [runbook](G1-RELEASE.md) e [diario](EXECUTION-LOG.md).

**Aceite funcional G1-OWNER (13/11/2026):** o operador informou que o pull, deploy e a funcionalidade de responsavel vinculado funcionaram perfeitamente em producao. Esta e evidencia de aceite funcional comunicada pelo usuario, NAO prova independente de todos os testes integrados, RBAC negativo ou CI. Detalhes no diario.

**G2-S2 (13/11/2026):** API de inventario + migration V011 + painel versionados e CI de API/DB/UI aprovado. O operador executou pull/deploy em srv-api e informou que **funcionou**, apos verificar os comandos de backup, health e V011; esta e **evidencia relatada pelo usuario**, nao acesso independente ao runtime. A feature de ingestao permanece DESLIGADA na configuracao validada, portanto ainda nao ha coleta real, Keycloak por workstation ou agente instalado. Ver [G2-S2](G2-S2-S2S-INGEST-RELEASE.md).

**G2-S3 (13/11/2026):** pacote assistido Windows preparado em codigo para instalacao futura, com default PLAN, assinatura corporativa obrigatoria para ativar, DPAPI CurrentUser, tarefa criada DESABILITADA, habilitacao separada e desinstalacao apos revogacao. **CI VERDE** no commit `02e3df851438`: parser PowerShell, teste do plano nao mutante, pytest HTTP/API, banco de testes V001..V011, architecture-gate e audit. **NENHUMA maquina foi alterada.** Sem assinatura corporativa ou teste Windows real. Ver [G2-S3](G2-S3-WINDOWS-AGENT-ROLL-OUT.md).

**G2-S4-S1 (14/11/2026):** atendendo ao pedido de automatizar Clients individuais por computador. API/UI com client Keycloak desabilitado, migration V012 e trilha de auditoria, admin HTTPS restrito e feature flag OFF. Sem secret/token no frontend, sem ativacao de ingestao nem acesso remoto. Proxima fase S2 entrega bootstrap seguro e vinculo S2S dinamico. Ver [runbook](G2-S4-S1-AUTOMATED-KEYCLOAK-PREPARATION.md).

**G2-S4-S1 CI (14/11/2026):** codigo `944fa6e13fe9` e ajustes de testes `749874c3f746` passaram no [CI da API/PostgreSQL V012](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43608815197) e [CI da interface](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43608815228), com [architecture gate](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43608815147) aprovado. Nao houve deploy da V012 nem criacao real de Clients no Keycloak; testes usaram mock e banco descartavel. Gate de provisionamento permanece OFF. G2-S4-S2 pendente.

**G2-S4-S2a (14/11/2026):** preparado binding por PostgreSQL (V013, `ingest_authorized=false` por default) e revogacao individual com bloqueio DB antes de desabilitar Client Keycloak, auditoria e revisao manual em falha. JWT S2S continua validado por assinatura/issuer/audiencia/scope; Client esperado deriva do UUID do ativo, sem lista manual no env. `IT_PORTAL_WORKSTATION_DB_BINDINGS_ENABLED=false` e `IT_PORTAL_WORKSTATION_REVOKE_ENABLED=false` por default; sem fallback da allowlist estatica quando DB mode ativo. Nenhuma ativacao ou bootstrap Windows foi implementada; segue no S2b. Ver [runbook](G2-S4-S2A-DYNAMIC-BINDINGS-REVOCATION.md).

**Evidencia automatizada S2a (14/11/2026):** [API + PostgreSQL V013: SUCCESS](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43611957705) no commit `a0086959214f`; [frontend lint/Vitest/build: SUCCESS](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43611589167); [architecture-gate: SUCCESS](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43611957703); [audit: SUCCESS](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43611589188). Houve dois ajustes somente de teste (hostname e RETURNING); nenhuma mudanca de V013 apos CI. **G2-S4-S2a permanece EM REVISAO:** sem Keycloak real, sem Windows piloto, sem deploy produtivo. Flags OFF.

**G0-SEC-S0 (13/11/2026):** o preflight offline foi implementado com checklist de 12 verificacoes pendentes, auditoria de rotas/manifesto/Compose e testes que falham ao detectar acesso remoto prematuro. **CI verde** no commit `b3972d753599`: gate BLOCKED, pytest, integracao PostgreSQL, architecture-gate e audit. A avaliacao ADR-002 identificou alerta urgente dos mantenedores do MeshCentral 1.3.1 (23/10/2026) sobre exploracao ativa; versao apenas **candidata**, nao aprovada. **G3-ENGINE permanece BLOQUEADO** ate signoff formal e demonstracao de mitigacao.

**G0-SEC-S1 (13/11/2026):** atualizado intake offline da release MeshCentral 1.3.1 com tag vinculada ao commit upstream `f436143527458d56da0336ea3047c006703fb4e4` e risco aberto de regressao dos agentes Windows ([issue #8269](https://github.com/Ylianst/MeshCentral/issues/8269)). O digest do artefato e a mitigacao do aviso emergencial continuam **pendentes**; configuracao publica exige ambiente de laboratorio isolado, sem rede/credenciais/estacoes produtivas. Nenhuma instalacao ou sessao remota autorizada. Ver [G0-SEC-S1](G0-SEC-S1-ENGINE-INTAKE.md).

**G0-SEC-S1 CI (13/11/2026):** commit `b74c12e94bc4`, [API + gate G3-LAB BLOCKED: SUCCESS](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43542553147/job/132286203346), [architecture-gate SUCCESS](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43542552950/job/132286202669), [audit SUCCESS](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43542552981/job/132286202676). O CI verde comprova apenas **ausencia de autorizacao prematura**, nao mitigacao de exploit, aceite de segurança ou acesso remoto.

**G0-SEC-S2 (13/11/2026):** preparadas tres minutas (politica/privacidade, rede isolada e incidente/backup/revogacao) e registro publico de 10 checkpoints pendentes. **CI aprovado** no commit `f778d309210d`: preflight `G0-SEC-S2 BLOCKED`, testes Python/HTTP, PostgreSQL e gates de arquitetura/auditoria. A validacao de CI nao aprova politicas, ambiente nem acesso remoto. **G3-ENGINE permanece BLOQUEADO**. Ver [revisao G0-SEC-S2](G0-SEC-S2-REVIEW-RUNBOOK.md).

**Proximo passo executavel:** confirmar CI do G0-SEC-S2 e obter revisao TI/Seguranca/Infra/RH/Juridico em processo **privado**, incluindo risco da release, topologia real, retencao, RPO/RTO, kill switch e teste de restore. Sem aceite, **NO-GO para motor remoto**. G2-S1..S3 continua reservado para validacao presencial.

## Regras permanentes de engenharia

- Criar dominio `workstations` separado de `servers`, evitando assumir que estacoes sao servidores.
- Reaproveitar convencoes React/TS, FastAPI, Postgres `it_portal`, Keycloak, Core RBAC fresh e logs estruturados.
- O coletor de inventario e o motor remoto devem ter **identidades, segredos, permissoes e flags independentes**. Nunca ampliar `host-service-control` para shell arbitrario.
- Toda migration deve ser nova e imutavel; nao editar migrations historicas.
- Nao publicar segredos, tokens, certificados privados, nomes/IPs de maquinas reais ou inventario nominal no GitHub. **Este repositorio foi constatado publico** na verificacao inicial.
- Nao habilitar agente ou acesso remoto em servidores de producao sem change e janela aprovada.
- Nao criar branches nem mudar worktrees sem autorizacao especifica; ver `AGENTS.md`.
- Avisar ao usuario se nao houver acesso real a teste/deploy. Nenhum comando de implantacao deve ser dado como executado sem evidencia.

## Links do pacote

- [Arquitetura e decisoes](ARCHITECTURE.md)
- [Gates de seguranca e matriz de riscos](SECURITY-GATES.md)
- [G0-SEC-S0: preflight de seguranca offline e testes](G0-SEC-S0-AUTOMATED-PREFLIGHT.md)
- [G0-SEC: checkpoint estruturado (sem aprovacao)](G0-SEC-CHECKPOINTS.json)
- [G3-ADR-002: avaliacao inicial do MeshCentral e alerta de seguranca](G3-ADR-002-MESHCENTRAL-SECURITY.md)
- [G0-SEC-S1: intake offline da versao candidata](G0-SEC-S1-ENGINE-INTAKE.md)
- [G0-SEC-S2: pacote de revisao privada (minutas, rede e recuperacao)](G0-SEC-S2-REVIEW-RUNBOOK.md)
- [G0-SEC-S2: registro publico de pendencias (sem aprovacao)](G0-SEC-S2-REVIEW-REGISTER.json)
- [G3-LAB-CANDIDATE: manifesto de riscos e bloqueio](G3-LAB-CANDIDATE.json)
- [Contrato inicial de inventario G1](INVENTORY-CONTRACT.md)
- [G1-OWNER: vinculo do responsavel a usuario da plataforma](G1-OWNER.md)
- [G1-OWNER: publicacao e verificacao futura](G1-OWNER-RELEASE.md)
- [G2-S1: coletor local Windows e contrato de snapshot](G2-S1-LOCAL-COLLECTOR.md)
- [G2-S2: API de ingestao, seguranca e runbook de release](G2-S2-S2S-INGEST-RELEASE.md)
- [G2-S3: pacote de instalacao, tarefa desabilitada e rollback Windows](G2-S3-WINDOWS-AGENT-ROLL-OUT.md)
- [G2-S4-S1: cadastro automatico de Client Keycloak DESABILITADO](G2-S4-S1-AUTOMATED-KEYCLOAK-PREPARATION.md)
- [G2-S4-S2a: binding por banco e revogacao individual](G2-S4-S2A-DYNAMIC-BINDINGS-REVOCATION.md)
- [Convencao de nomenclatura de computadores (proposta)](NAMING-CONVENTION.md)
- [Diario de execucao e passagem de bastao](EXECUTION-LOG.md)
