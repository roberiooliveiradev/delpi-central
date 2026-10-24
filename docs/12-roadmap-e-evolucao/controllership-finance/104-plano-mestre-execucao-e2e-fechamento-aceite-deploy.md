# Documento 104 — Plano mestre de execução E2E da Central de Fechamento: implementação, aceite e deploy por Operador SSH

**Data da diretriz do PO:** 24/10/2026  
**Produto:** Portal Controladoria & Finanças / Minha DELPI  
**Processo:** PROC-0072 — Gestão do Fechamento Mensal da Controladoria  
**Natureza:** PLANO DE EXECUÇÃO CONSOLIDADO, não relato de código nem evidência de deploy  
**Owner de execução:** Devin, coordenado pelo GPT Arquiteto; negócio/aceite por Controladoria e PO; deploy por Operador SSH habilitado  
**Referências normativas:** [93 — roadmap E2E](./93-roadmap-executivo-central-fechamento-end-to-end-checkpoints.md), [23 — ledger RQ/AC](./23-ledger-rq-ac-testes.md), [37 — P5 C2](./37-p5-submissao-e-revisao-no-portal.md), [41 — validação](./41-estrategia-validacao-e-gates-implementacao-v1.md), [14 — segurança](./14-seguranca-rbac-auditoria-e-ia.md), [17 — inventários](./17-backlog-de-confirmacoes-e-inventarios.md), [100 — evidências](./100-ciclo3-p6-min-p2-read-runtime-evidencia-de-execucao.md), [103 — P2-Upload](./103-ciclo3-p2-upload-contract-gate.md), [94 — CLARA](./94-clara-especialista-mcp-controladoria-financas.md) e [infra/README-ambiente](../../../infra/README-ambiente.md).

## 0. Ordem do PO e resultado a entregar

O PO solicita abandonar a sequência de microauditorias e executar o fechamento mensal **de ponta a ponta**, em pacotes contínuos, com **três paradas formais no máximo**: (G1) bloqueio material de autoridade/contrato, agrupado em uma pauta única; (G2) aceite de negócio integrado; (G3) release/rollback no ambiente destino. Testes, code review, documentação mínima e correções dentro de cada pacote **não** são novos gates; Devin deve continuar executando quando houver autoridade, contrato e ambiente.

**Resultado operacional desejado:** usuário abre competência com snapshot governado, obtém e anexa evidências, Controladoria valida/rejeita, acompanha fontes R01–R15, executa cutoff e conciliação quando houver fontes oficiais, trata pendências, cria/finaliza/submete pacotes por destinatário, revisores elegíveis decidem por área/versão, e o sistema conclui ou mantém pendente/rejeitado de acordo com C2 — tudo na Minha DELPI, com trilha de auditoria e isolamento entre competências.

**Estados distintos:** IMPLEMENTED, TESTED, HUMAN_ACCEPTED, DEPLOYED e OPERATIONALLY_VERIFIED nunca são sinônimos. Não anunciar fechamento completo por existência de rota, tela, CI verde ou HTTP 200. A decisão de implementar um pacote não concede a permission extra nem transforma dependência sem autoridade em fato.

**Execução e produção:** o PO solicita implementação e deploy via Operador SSH. Registrar a intenção executiva, mas **não executar deploy antecipado**: o operador só efetiva o rollout após G2 e preflight/rollback G3, no ambiente identificado e com acesso autorizado. Nenhum segredo, host, chave ou token deve constar deste documento, do prompt ou dos logs comuns. O presente commit é apenas documental.

## 1. Baseline verificável e escopo

- **PROVEN no GitHub:** P6-MIN + P2-READ com snapshot de 53 itens; P2-Upload U1–U8 publicados sobre V003; Home e consultas auxiliares de financeiro/estoque presentes no HEAD. O último commit específico de U5–U8 examinado pelo GPT foi 62f111ea6911f78b9c7002f806da4aaf4d4b245c, com veredito **REWORK** limitado a idempotência/contrato U5 e semântica de imutabilidade de document_version. Não declarar CP04 aceito sem resolver ou classificar esses dois itens no pacote A.
- **TEST_NOT_RUN / residual:** smoke humano autenticado, recreate literal do serviço/storage e AC-P2-UP-20 (trava após submissão P5); não inventar PASS. Relatos de suíte executada estão no doc 100.
- **TARGET:** CP05 validação humana P2, CP06 R01–R15, CP07 P3, CP08 P4, CP09/10 P5, CP11 cockpit/admin/superfícies e CP12 E2E. Detalhamento de RQ/AC continua pertencendo ao doc 23.
- **AS-IS:** TÉO/Transformômetro é autoridade do processo e de suas evidências; docs 59/90/95 registram crosswalk 53/53 e pendências por item. Se TÉO estiver indisponível, preservar o último registro marcado/proveniente, não afirmar confirmação live.
- **Fora do núcleo de fechamento operacional:** página de Contabilidade/DRE CF-FUTURE adiada por decisão prévia; não ativá-la incidentalmente. CLARA/MCP é trilho paralelo M00–M06 do doc 94, com gates próprios; não confundir ausência do especialista com inexistência da execução operacional P1–P6, nem declarar FULL_SCOPE_COMPLETE incluindo CLARA sem M06.
- **Identidade técnica imutável:** plugin controllership-finance; MFE plugins/controllership-finance, basePath /apps/controllership-finance; BFF controllership-finance-api, baseUrl /apps/controllership-finance-api; somente controllership-finance.access e controllership-finance.manage.

Preflight no **HEAD real** de cada bloco: origin/main, branch, git status, Project Instructions, instruções oficiais, somente regras .cursor aplicáveis, contratos/producers/consumers, tests e árvore de dependência. HEAD remoto e worktree do executor são evidências distintas; atualizações concorrentes não podem ser sobrescritas.

## 2. Plano de implementação contínua — quatro pacotes, sem micro-GOs

### PACOTE A — Base de workflow e P2 completo (CP02–CP05)

**Construir / concluir:**
1. Resolver os dois resíduos concretos U5 (idempotência do replace: contrato ↔ DTO ↔ backend ↔ MFE ↔ testes; sem reutilizar chave U1 inadequadamente) e versionamento (imutabilidade de conteúdo versus mutabilidade de estado). Se for nova escolha material, elevar **somente essa decisão** em G1.
2. P6 operacional completo: catálogo/versionamento prospectivo de templates, requisitos/roles/recipients/áreas, configuração de validators, elegibilidade, auditoria, OCC e UI de Administração com MANAGE + escopo. Preservar snapshot de competência aberta; nunca gerir usuários/roles/permissões do Core.
3. P2 completo: N/A de REQUIRED proibido; CONDITIONAL conforme regra; documentos multi-anexo/roles; validação e rejeição humanas com motivo, histórico, substituição requer nova validação; PER_ATTACHMENT/WHOLE_SET quando configurado; item excepcional só da competência; correção estrutural versionada; notificação quando disponível; estado e Help coerentes.
4. Levantar E05/E06, CP-D02/03 por owner Controladoria como inputs concretos de seed/fluxo. Não fabricar associação de validador, R-ID CK-E-27 ou catálogo de motivos.
5. Instalar o bloqueio P2 sobre versões/documentos referenciados por pacotes **quando existir** P5 submetido (AC-P2-UP-20), sem falso P5 em runtime enquanto a tabela/fonte ainda não estiver presente.

**Aceite observável:** duas competências com snapshots independentes; uploader pode também validar somente por ação autorizada independente; sem autoaceite; rejeição motiva e preserva evidência; substituição reinicia validação; segundo usuário inelegível e recurso irmão negados; publicação P6 não altera competência aberta; download por versão autorizado; AC-P2 RQ-02..12 e AC-P2-UP-16..24 rastreados.

### PACOTE B — Fontes, automação governada, P3 e P4 (CP06–CP08)

**Construir / concluir:**
1. Integrar R01–R15 **por lote técnico com prova por R-ID e por item**. Reutilizar consultas existentes R01/R02/R03 apenas como auxiliares até paridade oficial G1–G6; não renomear consulta SE5/SB9 como relatório TOTVS oficial. Para Rxx sem API/fonte reproduzível, disponibilizar coleta manual/evidência e status honesto, sem fabricar SQL, exportação oficial ou G6.
2. Batches do doc 93: B0 reuso existente; B1 R05/R06/R07/R08/R10/R11; B2 R03 oficial/R04/R09/R12/R15; B3 R13/R14 externos/mistos. Cada R-ID terá owner, parâmetros, competência/filial, origem, freshness/finality, contrato producer, output comparável com artefato oficial, divergência e decisão humana G6. Executar lotes em sequência/compatível paralelo, sem PR/GO separado para cada R-ID.
3. P3: cutoff humano autorizado, revalidação posterior dos inputs, conciliação de Entradas/Saídas – P7 – H02, tolerância **exatamente R$ 0,00**, source_unavailable e zero pré-cutoff nunca significam fechamento; STOCK_CLOSED só reflete estado canônico do owner e **não** grava sacramentação TOTVS.
4. P4: pendências/classificações com estados fechados, sugestão determinística/IA não efetiva, ownership/claim/reassign, justificativa para DISMISSED, trilha e regra humana, sem escrever correções no ERP nem inventar SLA.

**Aceite observável:** matriz R01–R15 com G1–G6 por R-ID (G6 sem aceite humano real = PENDING); dois contextos/filiais e inputs faltantes; paridade zero fecha apenas após cutoff e revalidação, R$ 0,01 bloqueia; indisponibilidade não vira zero; classificação não escreve ERP; pending/sibling com auditoria e AuthZ negativa.

### PACOTE C — P5, cockpit, superfícies comuns e administração integrada (CP09–CP11)

**Construir / concluir:**
1. P5 por destinatário: PackageVersion imutável por conteúdo/identidade, composição de evidências P2 validadas e resultados P3/P4 aplicáveis, finalização separada de submissão; versões e recipients independentes; submissão disponibiliza **dentro da Minha DELPI**, jamais e-mail com pacote anexo.
2. Reviewer: identidade Core, ACCESS efetivo, elegibilidade corporativa por grupo/função, área requerida da versão, assignment/scope e business rule; notificações Core in-app com e-mail best-effort; Minhas tarefas como TaskProjection self-only, nunca TaskEntity paralela.
3. Ciclo de revisão com esclarecimento/correção, histórico e nova PackageVersion sem herdar aceites; quórum **por área**, não por quantidade de pessoas; sem revisor ou sem áreas = pacote pode submeter, mas **nunca** aceite por vacuidade.
4. Conclusão mensal governada pelo C2 vigente do doc 37: todos os pacotes aplicáveis submetidos + aceite humano real na versão atual de cada pacote + aceite de cada área obrigatória vigente + nenhum esclarecimento aberto + nenhuma rejeição terminal. Rejeição de área não é automaticamente terminal; coordenador formal confirma terminal com elegibilidade e justificativa. Nenhuma retificação/override de aceite V1.
5. P1 cockpit agrega eixos independentes P2/P3/P4/P5 com origem/freshness/indisponibilidade e sem false green; integrar Início, Visão geral, Sala de interação, Minhas tarefas, Administração, Ajuda e deep route do usuário com kit @delpi/plugin-ui. Help muda no mesmo commit da capacidade real. Claro/escuro na mesma árvore, desktop/mobile/teclado/foco e F5/deep links.

**Aceite observável:** dois destinatários e dois revisores elegíveis de áreas distintas; outra área/pacote não herda resultado; nova versão reseta aceites atuais sem apagar históricos; falha de e-mail não desfaz submissão; 0 reviewer/0 área nunca concluem; rejeição terminal separada; cockpit não mistura STOCK_CLOSED, PACKAGE_FINALIZED, SUBMITTED e MONTHLY_CLOSING_COMPLETED.

### PACOTE D — Integração, homologação, operação e implantação (CP12)

**Construir / concluir:**
1. E2E real em ambiente não produtivo: ao menos duas competências, filiais/contextos aplicáveis, duas versões, dois destinatários, múltiplos atores, usuário sem ACCESS, MANAGE sem ACCESS, Core indisponível, source TOTVS indisponível, notification failure e resource sibling.
2. Recreate literal de containers com checksum e persistência dos anexos; migrations desde banco limpo e upgrade a partir de base existente; integridade e audit append-only; observabilidade, logs sem segredo, saúde dos serviços, retenção e tratamento manual/documentado de órfãos sem deleção de evidência válida.
3. Aceite funcional real de Controladoria/PO para as tarefas e regras aplicáveis, inclusive G6 por R-ID; registrar pendências/limitações com impacto. Simulações, mocks e CI não substituem assinatura humana nem prova de fonte oficial.
4. Preparar release SHA imutável, plano de migration/backup/recovery e rollback de app/dados, lista de serviços, janela, responsáveis e smoke; **execução SSH de produção exclusivamente pelo Operador SSH autorizado após G2/G3**.
5. Após rollout: health, login real de usuários autorizados/não autorizados, abertura de competência, upload/validação, package/review quando houver dados seguros, consulta dos relatórios habilitados, read-back dos resultados, métricas e rollback se falhar.

**Aceite observável:** matriz completa por RQ/AC no SHA final; end-to-end real sem bypass; performance/observabilidade e recoverability; sem PENDING silencioso nos requisitos críticos de conclusão; autorização real do release; post-deploy smoke e leitura posterior.

## 3. Apenas três paradas formais — não multiplicar auditorias

**G1 — BOUNDARY / DECISION STOP (agrupado, apenas quando necessário).** Antes do código que dependa de escolha material ainda aberta: T05 elegibilidade Core por área, T03 owner de STOCK_CLOSED, E05/E06/CP-D02/03, origem oficial dos Rxx, U5 idempotência e P5 C2 se aparecer contradição efetiva, e decisões CLARA separadas. Devin deve produzir **uma** pauta consolidada com decisão, owner, opções, impacto e recomendação. Continuar imediatamente outras partes independentes do pacote; não inventar padrão nem paralisar o programa inteiro. Nenhuma decisão recomendada é aplicada antes da aprovação. Documento que apenas descreve contrato não prova runtime.

**G2 — BUSINESS ACCEPTANCE STOP (ao concluir A+B+C e integração D não produtiva).** PO/Controladoria recebem demo funcional guiada por cenário, matriz RQ/AC, G6, assinatura/aceite humano e residuais classificados. Saídas: ACCEPT / ACCEPT_WITH_RESIDUAL / REWORK apenas se falha de outcome material; testes verdes isolados não equivalem a aceite. Não exigir gate humano por tela ou por R-ID; coletar aceites oficiais de dados onde a regra exigir.

**G3 — RELEASE / OPERATOR SSH STOP (antes de tocar produção).** Aprovação de janela e alvo, usuário operador habilitado, backups validados, rollback praticável, migrations compatíveis, secrets presentes somente no secret store/env do host, SHA publicado, checks e smoke roteirizados. Se falhar preflight, STOP deployment sem rollback destrutivo. Após deploy, postcondition/health/smoke decide ACCEPT de release ou rollback.

**Rotina Devin dentro dos pacotes:** READ → VERIFY → IMPLEMENT MINIMAL DIFF → TEST (positive/sibling/negative/real owner) → VERIFY OUTCOME → HELP → RESIDUAL SEARCH → COMMIT/SHA → NEXT. Correções locais são executadas no próprio pacote, sem abrir uma sequência de prompts de auditoria; escalar apenas DECISION_REQUIRED genuína, EXECUTION_DRIFT ou risco material de segurança/dados.

## 4. Matriz compacta: o que deve ser aceito

| Bloco | Aceite de resultado, não apenas existência de artefato | Evidência |
|---|---|---|
| P6 + P2 | snapshot governado, 53 itens, N/A correto, upload/versão/validação/rejeição sem autoaceite, autorização actor/scope | AC-P2/AC-P2-UP; DB, HTTP, UI, dois atores/competências |
| R01–R15 | paridade do relatório oficial quando aplicável; G1–G6 por R-ID; manual honesto se a automação não for comprovada | crosswalk item→R-ID→arquivo oficial→owner→G6 humano |
| P3 | cutoff explícito, revalidação, diferença monetária exatamente 0, indisponibilidade bloqueia e ERP owner é respeitado | testes com 0, ±0,01, source_missing e estado canônico |
| P4 | pending/claim/reassign/decisão humana sem escrita ERP ou promoção automática de sugestão | histórico, usuário irmão, caso negativo |
| P5 | PackageVersion e recipient snapshots, submit in-portal, elegibilidade, C2 por versão e área, nenhum aceite por vacuidade | testes zero-area/zero-user, duas áreas, duas versões, reviewer errado |
| P1 / comuns / P6 UI | eixos separados, links owner, tarefas self-only, admin MANAGE, Help, responsivo/acessível | testes UI, 403/404, tema, teclado, F5/deep link |
| Plataforma / release | fail-closed Core, sem permission nova, persistência após recreate, migration/recovery, integração real e release rastreável | logs, DB, CI, smoke autenticado, operator checklist e rollback |

Aplicar todos os AC do [ledger 23](./23-ledger-rq-ac-testes.md); a tabela acima é índice de aceite, não substituição de AC. Classificações PROVEN/TO_INVENTORY/PLANNED/TARGET e PASS/FAIL/PENDING/INCONCLUSIVE/TEST_NOT_RUN/STALE_EVIDENCE com SHA, ambiente, ator e postcondition.

## 5. Operador SSH — procedimento de deploy seguro

**Authority operacional:** [infra/README-ambiente](../../../infra/README-ambiente.md) e script vigente [infra/scripts/up-prod-sequential.sh](../../../infra/scripts/up-prod-sequential.sh). A execução SSH não acontece por GitHub e não deve ser simulada. Devin só pode acioná-la por sessão/canal autorizado do Operador SSH; não há credencial, hostname nem chave aprovados neste documento.

**Ordem obrigatória:**
1. Identificar ambiente/host e operador; confirmar permission/approval operacional, janela, SHA release exato, versão de imagens, infraestrutura e serviços afetados. Preflight seguro via SSH (somente leitura): versão de código, saúde/compose, discos/volumes, uso RAM, migrations aplicadas, upstream/gateway.
2. Confirmar backup consistente e restauração praticável de PostgreSQL e arquivos persistentes; confirmar versão de migration e compatibilidade de rollback. Nunca rodar suite PG destrutiva no cluster produtivo.
3. No host autorizado, na **raiz do repositório**, usar **somente** o processo/documentação vigente de deploy sequencial, preferindo rebuild apenas de serviços afetados. Primeiro remote plugin-ui, depois MFE(s); BFF e migrações na ordem do runbook. Inspecionar a lista com o modo --list e os parâmetros efetivamente suportados. Não executar docker compose up --build indiscriminadamente em toda a stack.
4. Conferir secrets/env por referência ao mecanismo existente, sem imprimir seus valores, sem colocá-los em prompt, comando registrado ou log. Não alterar Keycloak/Core grants por conveniência.
5. Executar checks de gateway/upstreams segundo runbook (script de produção já prevê nginx -t, reload e healthcheck conforme o caso); smoke real autenticado, postconditions no banco e integridade dos documentos, estados funcionais e eventos.
6. Se falha material: suspender rollout, restaurar aplicação/imagens no SHA anterior; para schema/data seguir plano específico de reversão/backup, **nunca** DROP ou rollback destrutivo inferido. Comunicar incidente com evidência saneada. Se PASS, registrar release SHA, hora, operador, checks, migrações, smoke, pendências e autorização da Controladoria/PO.

**Estado atual:** deploy SSH NOT_RUN; nenhuma execução de produção ou autorização técnica de ambiente é inferida da existência deste plano.

## 6. Trilha paralela CLARA e escopo diferido

CLARA M00–M06 permanece governada pelo [doc 94](./94-clara-especialista-mcp-controladoria-financas.md). A identidade e CLARA-D01=B foram aprovadas, **não** a implementação MCP/ACT ou os contratos ainda pendentes D02..D05. Em paralelo ao trabalho operacional, Devin pode preparar a matriz e conhecimento M00/M01; runtime MCP/Chat/ACT somente após decisões/autorizações próprias e testes de delegação por ator. Não chamar o produto integralmente concluído no escopo que inclua CLARA enquanto M06 não estiver real.

A futura superfície da Contabilidade/DRE (CF-FUTURE) continua DEFERRED_BY_PO e não entra em deploy por arrasto.

## 7. Report consolidado e critério de encerramento

A cada pacote A–D entregar **um relatório consolidado**, não micro-relatórios por rota:
- BASE_HEAD, FINAL_HEAD, git status do executor, lista de commits/SHAs e diffs; boundaries alterados.
- RQ/AC realizados por página/fluxo e por R-ID; owner, fonte, evidence G1–G6, output real, negatives e postcondition.
- Testes unitários/contrato/PG isolado/HTTP/frontend/structural/E2E; quais não foram executados; autenticação real e acesso indevido negado.
- Decisões novas e premissas invalidadas; stop parcial e workstreams que seguiram; estado de deploy/rollback.
- Logs operacionais saneados, Help, riscos de retenção/antimalware e pendências sem promover estados.
- Decisão GPT somente ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE; decisão de negócio G2 pelo PO/Controladoria; release G3 pelo operador habilitado com autorização aplicável.

**Conclusão operacional do fechamento:** CP02–CP12 com pós-condições e cenário real comprovados, matriz 53/53 com tratamento honesto de automação/manual, G6 de fontes oficiais quando exigido, C2 humano válido, segurança e persistência; deploy marcado DEPLOYED apenas após o operador confirmar, e OPERATIONALLY_VERIFIED apenas depois do smoke/read-back. Se houver limitação aprovada que impeça automação de Rxx, registrar explicitamente MANUAL_OPERATIONAL_SCOPE; nunca rotular a automação integral como concluída.

**Instrução Devin:** executar os pacotes A→D de forma contínua, podendo paralelizar B com partes independentes de A; parar apenas em G1, G2 ou G3, com STOP local para risco material. Não solicitar nova autorização de implementação por página quando o GO transversal compatível estiver expressamente registrado; não tratar esta especificação como revogação das exigências de owner/contrato e segurança.
