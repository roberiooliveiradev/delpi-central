# Documento 105 — GO de conclusão integral das pendências da Central de Fechamento antes do refinamento final

**Diretriz do PO:** 25/10/2026 — "vamos implementar tudo que falta, ao final fazemos o refinamento".  
**ID:** CF-PROC0072-REMAINDER-BUILD-GO-001  
**Produto/processo:** Portal Controladoria & Finanças / PROC-0072.  
**Natureza:** GO de implementação **para capacidades com autoridade/contrato suficientes** e plano de fechamento de lacunas; não constitui aceite de negócio, autorização de produção nem aprovação tácita de decisões materiais pendentes.  
**Referências:** [104 — plano mestre](./104-plano-mestre-execucao-e2e-fechamento-aceite-deploy.md), [93 — CP00–CP12](./93-roadmap-executivo-central-fechamento-end-to-end-checkpoints.md), [23 — RQ/AC](./23-ledger-rq-ac-testes.md), [37 — P5-H/C2/T05](./37-p5-submissao-e-revisao-no-portal.md), [17 — pendências](./17-backlog-de-confirmacoes-e-inventarios.md), [100 — evidências](./100-ciclo3-p6-min-p2-read-runtime-evidencia-de-execucao.md), [14 — segurança](./14-seguranca-rbac-auditoria-e-ia.md), [41 — validação](./41-estrategia-validacao-e-gates-implementacao-v1.md) e instruções oficiais do GPT Arquiteto. O Documento 105 **complementa, não substitui** essas autoridades.

## 0. Mandato, baseline e modo de trabalho

O PO prioriza **completude funcional de uma vez, com refinamento visual/usabilidade ao final**, evitando ciclos de micro-REWORK. O executor Devin inicia o programa, implementa continuamente as partes aprovadas e contratualmente determinadas, executa os testes e publica commits por workstream. Integração, autorização, segurança, Help mínimo, acessibilidade funcional, modelo de dados íntegro e testes **não são polimento adiado**; devem acompanhar cada capacidade. O refinamento ao final compreende apenas ajustes visuais, consistência fina de UX, ergonomia e melhorias não bloqueantes depois de comprovado o fluxo.

**Baseline verificado no GitHub na emissão:** \`acfdd136f1bd73da755920b2218198bd6dc1ef43\` em \`main\`. O executor **deve** reobter \`origin/main\`, branch, \`git status\`, Project Instructions, \`.cursor\` aplicável, contratos/producers/consumers e testes; GitHub remoto não comprova worktree limpo. Rebase seguro sem sobrescrever trabalho concorrente. O último pacote de correção C2/G1/G2 está publicado nesse SHA; 482 testes backend foram **reportados pelo executor**, não reexecutados pelo GPT. Smoke humano, fontes oficiais reais e deploy desta leva: \`TEST_NOT_RUN\`.

**Implementação existente, não reconstruir:** P6-MIN/P2-READ, P2-Upload U1–U8/validação, P3 cutoff/readiness, P4 pendências, P5 packages/review/C2, cockpit, admin P6 de versões; migrations V001–V009 e E2E em PostgreSQL descartável. A implantação produtiva registrada pelo operador permanece no estado A3 de referência (ver doc 100); nada neste GO concede novo deploy.

**Escopo de GO:** completar **todas as pendências do Portal Controladoria & Finanças referentes à Central de Fechamento, P1–P6 e páginas comuns**, e a cadeia de dados R01–R15 que suporta o processo, desde que haja autoridade vigente, contrato e owner. O usuário autorizou a implementação desse escopo contínuo, **não** a decisão unilateral sobre contrato novo, boundary, RBAC, escolha de owner, fonte oficial, concessão, confirmação humana, breaking change ou retenção. Esses pontos devem chegar a um **único G1 consolidado**; executar outras partes independentes sem esperar. Nenhum micro-GO por página.

**Preservar escopo anteriormente adiado:** CLARA/MCP (doc 94, implementação própria ainda não autorizada) e página futura Contabilidade/DRE (doc 91, \`DEFERRED_BY_PO\`) **não são reativados por arrasto**. Incluir ambos na matriz final de lacunas, separando-os explicitamente do aceite P1–P6. Se o PO quiser ampliar o GO para eles, será uma decisão específica de reativação/gate, não uma inferência de "tudo".

## 1. Matriz das pendências — implementar e aceitar, não apenas produzir telas

| Frente | Faltante a completar | Aceite objetivo | Contrato/stop |
|---|---|---|---|
| **F1 — P6 lifecycle e catálogos** | \`DRAFT→REVIEW→PUBLISH→EFFECTIVE_FROM\`; interface e backend governados para bancos/contas (E01), motivos de rejeição core+extensões (E06), roles de documento (E05), targets de notificações (T02), responsáveis/validadores/recipients; versionamento/OCC/scope; template de **áreas obrigatórias por tipo de pacote** | Publicação não altera competência aberta nem PackageVersion já submetida; codes históricos continuam referenciáveis; ACCESS não administra; MANAGE+escopo+regra; testes de concorrência e Help | Modelagem P5-H multi-área, seeds E01/E05/E06 e owner precisam contrato/decisão G1; não perpetuar \`required_areas=[recipient_area]\` como substituto sem aprovação explícita |
| **F2 — Core T05 e coordenação formal** | Descobrir fonte S2S tipada de grupo/função corporativa por área, identidade ativa, assignment, escopo e coordenador formal; adapter BFF e autorização em cada ato P5 e P2/P4/P6 quando pertinente | Usuário com ACCESS sem função/assignment não revisa; MANAGE isolado não revisa; coordenador formal distinto de grant global; falha Core→fail-closed, testes reais de segundo usuário, histórico e reatribuição | Core é owner; não criar permission, role/grupo local como substituto, nem inferir elegibilidade de JWT. Se contrato físico inexistente, G1; continuar F3–F6 independentes |
| **F3 — P3/T03 e relatórios R01–R15** | Inventariar e ligar **producers canônicos** a cada R-ID e aos domínios ENTRADAS_SAIDAS/P7/H02; fonte oficial, competência/filial, regra/versão, freshness, provenance, G1–G6, artefato checksum e comparação humana; T03 \`STOCK_CLOSED\` por owner autorizado via HTTP/evento/contrato; fallback manual governado para fontes externas/mistas | R01–R15 têm item→source→owner→contrato→evidência→G6 ou \`PENDING_CONTRACT\` explícito; \`OFFICIAL\` não pode ser promovido só porque documento foi anexado/cliente assim declarou; P3 bloqueia ±R$ 0,01, source missing, stale e pré-cutoff; T03 não é escrito pelo Portal no ERP | R04/R06/R07/R09/R12/R15 e contratos oficiais T01/T03 exigem inventário/owner. Sem fonte real, implementar somente fluxos manuais aprovados; não fabricar APIs/SQL/outcome. TÉO AS-IS; api-delpi/TOTVS TARGET de fontes |
| **F4 — P5 completude operacional** | Usar snapshot P6 multi-área quando aprovado; validação T05, C2 com P3 vigente/official real; notifications Core in-app/e-mail best-effort, inbox/deep links; TaskProjection self-only por área, rejeição terminal retira ação sem apagar histórico; bloquear mutação de evidência de versão submetida; P5-H/P5-J completos | Dois recipients, áreas e revisores diferentes, zero revisor/zero área, reviewer tardio, nova versão, rejeição terminal, notification failure, competence sibling; nenhuma aprovação por vacuidade, nenhuma retificação de aceite, sem anexo de pacote por e-mail | Não usar outbox interna como prova de notificação efetivamente entregue. T02/Core, T05, P6; execução de integração após decisão da interface do owner |
| **F5 — Páginas comuns do Portal** | Visão geral (RQ-OVW), Minhas tarefas (RQ-TASK), Sala de interação (RQ-ROOM), Página do usuário (RQ-USER), ajustes governados da Home e nav; visão P1/cockpit e Administração/Ajuda coerentes | \`@delpi/plugin-ui\` first, rotas/gates, self-only, context room, sem TaskEntity paralela, chat não valida/fecha, KPIs somente com owner/source/formula/freshness, profile no deep route, URL/F5, erros/partial, desktop/mobile/teclado/foco/tema | Reutilizar contratos/core/platform kit; necessidade de chat persistente/realtime/capabilities novas exige inventory e G1 se não houver contrato. Não simular sala ou notificações \`PASS\` com mocks |
| **F6 — Persistência, segurança, operação e E2E** | Recreate real dos anexos em ambiente não produtivo; retenção/limpeza \`.part\` sem apagar evidência; antivírus/capability da plataforma quando existir; migrations desde clean + upgrade, S2S real, duas competências/filiais/recipients/versões/atores; AC 23, Help, accessibility testing | Hash e binário preservados após recreate; negativa auth real; 401/403/404/409/503/partial; rollback/roll-forward ensaiáveis; relatório G1–G6 por R-ID; smoke humano e G2/G3 só com ambiente autorizado | Retenção, malware scanning, lista de tipos OFX/QIF/TXT e E05 dependem de política/owner. Não assumir disponibilidade de capability pelo simples desejo |

### Regra de integração e de falso positivo

- \`STOCK_CLOSED != PACKAGE_FINALIZED != PACKAGE_SUBMITTED_FOR_REVIEW != MONTHLY_CLOSING_COMPLETED\`.
- \`ATTACHED != VALIDATED\`, \`P2 validation != G6 official report acceptance != P5 review\`.
- \`OFFICIAL\` deve ter contrato de origem/validação genuíno; anexo com \`official_document_id\` **sozinho** não demonstra equivalência oficial.
- \`required_areas=[recipient_area]\` é fallback de código atual para pacote monoárea, **não** fonte versionada P6 para pacote multiárea.
- C2 \`derive_closing_state\` deve validar P3 blockers correntes **e** prova oficial adequada, todas as PackageVersions submetidas, cada required area atual aprovada por humano elegível, nenhuma clarification aberta e nenhuma rejeição terminal.
- Revisor/coordenador com assignment local não comprova automaticamente vínculo formal via Core.
- \`HTTP 200 != business outcome\`, \`teste verde != homologação\`, \`rota != capacidade runtime\`, \`docs != deployed\`.

## 2. Plano de execução contínua — quatro macrofrentes, sem pausa por feature

### L1 — Bases e contratos não bloqueados

Executar em paralelo: F1 lifecycle P6 e UI onde o contrato é inequívoco; F5 superfícies com reuso já disponível; F6 testes/reliability/storage; F4 notificações/task projection onde Core/kit vigente já tenha contrato, e correção de evidência pós-submissão quando os contratos P5 existentes determinarem comportamento. Criar matriz de gaps consolidada **uma vez**, não repetir discovery por tela. Para decisões de schema/owner/permission/contrato novas, documentar \`DECISION_REQUIRED\` em G1 e **não** implementar unilateralmente.

### L2 — Integrações com owners reais

Implementar, após contratos aceitos, F2 T05/Core; F1 catálogo P5-H multiárea prospectivo com snapshot por tipo, vigência e segurança; F3 T03/producer R-ID/output oficial e G6; F4 notificações e tarefas. Trabalho independente de owners externos não fica bloqueado por um único R-ID; marcar cada R-ID como \`PROVEN|TO_INVENTORY|TARGET\` com \`PASS|PENDING|TEST_NOT_RUN\` por gate. Não aumentar o denominador R01–R15 sem mudança de escopo aprovada.

### L3 — Fechamento de capacidades e refinamento final

Executar P1–P6 e páginas comuns integradas end-to-end (duas competências, dois destinatários, multi-área, dois atores e contexto de filial), corrigir regressões no próprio workstream, sincronizar Help em cada alteração; depois **uma única passagem de refinamento** de navegação, densidade de dados, ergonomia, mensagens/estados, UX responsiva e consistência do design system. Refinamento não pode mascarar ausência de source/authorization nem mudar contrato sem aprovação.

### L4 — G2/G3 e operação

Preparar matriz RQ/AC e G6, demonstrar com Controladoria/PO em ambiente não produtivo e obter aceite G2 explícito. Somente após G2, agendar G3 com Operador SSH autorizado, backups PostgreSQL+arquivos validados, rollback praticável, SHA de release fixo, migrations verificadas, script \`infra/scripts/up-prod-sequential.sh\`, smoke autenticado, read-back e relatório D4. **Este GO não autoriza deploy nem migration em produção**, e o executor não pode tratar acesso ao host como autorização. O deploy anterior A1–A3 foi \`EXECUTION_DRIFT\`, regularizado por inspeção read-only no doc 100, não precedente para novos releases.

## 3. Apenas três gates, com um único G1 de decisões reais

- **G1 — pacote consolidado de decisões materiais.** Quando a implementação depender de escolha nova de owner, schema, elegibilidade, persistência, workflow, upstream, breaking contract, retenção ou autorização, registrar \`DECISION_REQUIRED\` com opções A/B, impacto, risco e recomendação. Agrupar **todos** os itens num relatório único. Não implementar recomendação até decisão do PO/owner. Continua os outros trilhos sem bloqueio.
- **G2 — homologação integrada de negócio.** A Controladoria valida outputs oficiais G6, áreas/review/C2, segurança e operação manual/híbrida; decide ACCEPT/ACCEPT_WITH_RESIDUAL/REWORK para o escopo apresentado. Se parte do produto ficar TARGET por dependência externa, homologação parcial deve ser rotulada assim e aprovada explicitamente; não chamar \`FULL_SCOPE_COMPLETE\`.
- **G3 — liberação operacional pelo Operador SSH.** Somente após G2, operador autorizado confirma host, backup, restore, SHA, migrações, recursos, rollback, janela e smoke. Falha de preflight bloqueia deploy, não dispara rollback/destruição inferida.

**Não criar G1 repetido por tema, nem gate de aceite por botão.** Teste, code review, regressão e correção fazem parte do ciclo do próprio workstream. Exceções legítimas: security data exposure, perda de dados, \`EXECUTION_DRIFT\`, risco de migração/prod e decisão material não resolvida no subgrafo afetado.

## 4. Critérios objetivos para encerrar a construção

1. Todos RQ/AC pertinentes P1–P6, HOME/OVW/ROOM/TASK/USER/ADMIN/HELP/UX do ledger 23 têm \`PASS\` com SHA, teste e outcome ou \`PENDING\`/decisão explícita; nenhum item oculto.
2. P6 versiona types, areas e catálogos aprovados sem retroatividade; P5 congela área exigida do catálogo vigente, elegibilidade de reviewer e coordenador usa Core authoritative e business scope.
3. R01–R15 possuem source e G1–G6 comprovados ou estados manuais/pendências declarados por owner; P3 oficial e T03 demonstram paridade/fonte real, C2 não conclui com input obsoleto ou sem aceite humano.
4. P5 notificações reais, TaskProjection self-only, revisão multi-área por versão e evidência imutável; nenhuma permission nova além de \`controllership-finance.access\`/\`manage\`.
5. UI e Help coerentes; tema/mobile/foco/teclado testados, deep link/F5 e 401/403/partial observáveis; sem duplicar kit.
6. PostgreSQL em ambiente descartável isolado, migrations upgrade/clean, arquivos após recreate, testes unit/component/contract/integration/E2E, negativos de AuthZ e smoke autenticado de ambiente autorizado; sempre \`TEST_NOT_RUN\` quando faltar prova.
7. Refinamento final separado de correção de regra/segurança; G2 humano e G3 operador nunca inferidos. Release não marcado DEPLOYED até operação comprovada.

## 5. Relatório único de acompanhamento a cada macrofrente

\`\`\`text
EXECUTION_ID=CF-PROC0072-REMAINDER-BUILD-GO-001
BASE_HEAD:
FINAL_HEAD:
GIT_STATUS:
COMMITS:
F1_P6:
F2_CORE_T05:
F3_R01_R15_P3_T03:
F4_P5_NOTIFICATIONS_TASKS:
F5_OVW_ROOM_USER_HOME:
F6_E2E_STORAGE_SECURITY:
RQ_AC_MATRIX:
OFFICIAL_G1_G6_EVIDENCE:
BUSINESS_RULE_POSTCONDITIONS:
AUTHZ_NEGATIVES:
BACKEND_PG_FRONTEND_CONTRACT_E2E:
HELP_A11Y_MOBILE:
REFINEMENT_PASS:
G1_DECISION_REQUIRED:
G2_HUMAN_ACCEPTANCE:
G3_SSH_RELEASE:
DEPLOY_STATUS:
SMOKE_AUTHENTICATED:
RESIDUALS:
EXECUTION_DRIFT:
NEXT_ACTION:
\`\`\`

**Instrução ao Devin:** iniciar o GO imediatamente no HEAD real. Implementar cada parte que tenha contrato/authority inequívocos, sem solicitar novo prompt por feature. Agrupar decisões genuínas em G1; nenhuma escolha nova de schema/owner/permission/contract é aprovada por este plano. **Finalizar a construção antes do refinamento**, mas nunca adiar segurança, testes, Ajuda ou gates de produção.


## 6. Supersessão de escopo aprovada pelo PO em 25/10/2026

**Diretriz posterior:** [Documento 106 — CLARA batch, Keycloak/ChatGPT](./106-clara-batch-ssh-keycloak-chatgpt-go-e-gates.md) substitui o escopo histórico deste plano que incluía Sala de interação e expansão de Minhas tarefas. Essas funcionalidades ficam **adiadas**; preservar código preexistente sem exposição da navegação. **CLARA/MCP passa a integrar o escopo ativo**, com corpus próprio e execução múltipla governada. P1–P6/R01–R15 permanecem prioridade. G1 de owners, G2 humano e G3 Operador SSH continuam vinculantes.
