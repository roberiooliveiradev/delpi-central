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
| G0-SEC | Threat model/revisao de seguranca, LGPD, licenciamento, analise de compatibilidade de MeshCentral, redes e backups | **PENDENTE DE REVISAO** | Aceite formal do responsavel de TI e seguranca com registro |
| G1-DOM | Regras puras para cadastro de estacoes + testes | **EM REVISAO** | Normalizacao, limites, catalogos e rejeicao de segredos validados |
| G1-API | Migration independente, CRUD de estacoes e RBAC separado de servidores | **EM REVISAO** | API e testes integracao verdes; nenhum agente remoto |
| G1-UI | Area Computadores, busca/filtros/detalhe no plugin it-portal | **EM REVISAO** | Permissoes e testes de UI; sem botao remoto ativo |
| G1-OWNER | Selecionar colaborador usuario da plataforma como responsavel do computador; vinculo por identidade estavel | **VALIDADO** | Busca seletiva, vinculacao por ID do Core, exibicao do nome, auditoria de troca e tratamento de usuarios inativos |
| G2-AGENT | Identidade por dispositivo e coletor read-only de telemetria Windows | **EM DESENVOLVIMENTO** | Piloto, autenticacao individual, reconciliacao idempotente e remocao segura |
| G2-S1 | Coletor Windows LOCAL + contrato estrito de snapshot, sem envio automatico | **EM REVISAO** | Execucao em PowerShell 5.1 no Windows piloto, testes e aceite do snapshot |
| G2-S2 | Identidade individual de agente e ingestao autenticada, revogavel e idempotente | **EM REVISAO** | Codigo de S2S com flag off, migration V011, testes integrados e piloto Keycloak pendentes |
| G2-S3 | Enrolment governado, agendamento Windows e desinstalacao de agente | **EM REVISAO** | Pacote assistido e testes em CI; assinatura corporativa, piloto Windows, revogacao e teste de rotina pendentes |
| G3-ENGINE | MeshCentral isolado e testado em laboratorio | **NAO INICIADO** | Licenca, versao fixada, atualizacoes, TLS, backup, recuperacao, restricao de rede |
| G4-AUTH | Broker de sessoes, Keycloak/MFA e permissoes independentes | **NAO INICIADO** | Revogacao, tokens de uso unico, fail-closed, logs, kill switch |
| G5-REMOTE | Tela, teclado e mouse no navegador para computador piloto | **NAO INICIADO** | Testes presenciais de concorrencia, UAC, lock-screen, desconexao e latency |
| G6-EXTRAS | Clipboard bidirecional e arquivos | **NAO INICIADO** | Avaliacao e teste de DLP, escopos independentes, transferencia auditavel |
| G7-ROLLOUT | Implantacao em ondas SC/ES | **NAO INICIADO** | Aceite, notificacao aos usuarios, playbook suporte, rollback e monitoramento |

Status permitidos: NAO INICIADO, EM DESENVOLVIMENTO, DOCUMENTADO, EM REVISAO, VALIDADO, IMPLANTADO, BLOQUEADO. Nunca marcar `IMPLANTADO` sem evidencias do runtime; `VALIDADO` nao e sinonimo de CI verde.

**Publicacao G1 (evidencia recebida 13/11/2026):** operador executou a implantacao da API e do MFE; API `healthy`, migration V009 e tabela `it_portal.workstations` verificadas no PostgreSQL, frontend recriado (`Up 2 seconds`). **Pendente:** registrar/confirmar manifesto estrutural `0.3.4` e RBAC no Core, validar assets web e executar testes de usuario antes de considerar G1 homologado. Detalhes em [runbook](G1-RELEASE.md) e [diario](EXECUTION-LOG.md).

**Aceite funcional G1-OWNER (13/11/2026):** o operador informou que o pull, deploy e a funcionalidade de responsavel vinculado funcionaram perfeitamente em producao. Esta e evidencia de aceite funcional comunicada pelo usuario, NAO prova independente de todos os testes integrados, RBAC negativo ou CI. Detalhes no diario.

**G2-S2 (13/11/2026):** API de inventario + migration V011 + painel versionados e CI de API/DB/UI aprovado. O operador executou pull/deploy em srv-api e informou que **funcionou**, apos verificar os comandos de backup, health e V011; esta e **evidencia relatada pelo usuario**, nao acesso independente ao runtime. A feature de ingestao permanece DESLIGADA na configuracao validada, portanto ainda nao ha coleta real, Keycloak por workstation ou agente instalado. Ver [G2-S2](G2-S2-S2S-INGEST-RELEASE.md).

**G2-S3 (13/11/2026):** pacote assistido Windows preparado em codigo para instalacao futura, com default PLAN, assinatura corporativa obrigatoria para ativar, DPAPI CurrentUser, tarefa criada DESABILITADA, habilitacao separada e desinstalacao apos revogacao. **CI VERDE** no commit `02e3df851438`: parser PowerShell, teste do plano nao mutante, pytest HTTP/API, banco de testes V001..V011, architecture-gate e audit. **NENHUMA maquina foi alterada.** Sem assinatura corporativa ou teste Windows real. Ver [G2-S3](G2-S3-WINDOWS-AGENT-ROLL-OUT.md).

**Proximo passo executavel:** continuar a revisao de seguranca e preparar o processo corporativo de assinatura/distribuicao SEM ativar cliente ou tarefa. Somente quando o operador estiver presencialmente no escritorio: piloto G2-S1 Windows, Keycloak/audiencia/escopo/binding individual + TLS, primeiro envio G2-S2, pacote assinado e instalacao/Enable/Uninstall G2-S3 com evidencias. Nenhuma instalacao ou agendamento remoto agora. G0-SEC continua gate de acesso remoto.

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
- [Contrato inicial de inventario G1](INVENTORY-CONTRACT.md)
- [G1-OWNER: vinculo do responsavel a usuario da plataforma](G1-OWNER.md)
- [G1-OWNER: publicacao e verificacao futura](G1-OWNER-RELEASE.md)
- [G2-S1: coletor local Windows e contrato de snapshot](G2-S1-LOCAL-COLLECTOR.md)
- [G2-S2: API de ingestao, seguranca e runbook de release](G2-S2-S2S-INGEST-RELEASE.md)
- [G2-S3: pacote de instalacao, tarefa desabilitada e rollback Windows](G2-S3-WINDOWS-AGENT-ROLL-OUT.md)
- [Convencao de nomenclatura de computadores (proposta)](NAMING-CONVENTION.md)
- [Diario de execucao e passagem de bastao](EXECUTION-LOG.md)
