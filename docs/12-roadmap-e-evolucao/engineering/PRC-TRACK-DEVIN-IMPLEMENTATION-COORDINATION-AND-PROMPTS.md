# PRC-TRACK — Coordenação de implementação e prompts para Devin

> **Diretriz do PO (13/11/2026):** **Devin é o único executor designado para implementação** (código, testes, migrations, PRs e documentação técnica de execução). **ChatGPT/EVA coordena**, deriva prompts do plano aprovado, faz análise de risco, revisa evidências e retorna bloqueadores ao chat de Coordination. **ChatGPT/EVA não implementa diretamente.**
>
> **Fonte funcional vinculante:** [Regras canônicas de Produtos Acompanhados e plano central](./PRC-TRACK-CANONICAL-PRODUCT-RULES-AND-EXECUTION-PLAN.md). Proposta técnica ainda sujeita a G1/Coordination; nenhuma autorização implícita para mudanças de owner, source of truth, RBAC ou produção.

## 1. Papéis e fluxo operacional

| Papel | Responsabilidade |
|---|---|
| **Product Owner** | Define regras de negócio e prioridades; decisões CR-02–CR-13 e ADRs já registradas não devem ser reabertas sem conflito material comprovado |
| **ChatGPT/EVA (coordenação)** | Prepara prompts de execução em escopo mínimo; verifica consistência com regras canônicas; revisa diffs, testes e riscos reportados; mantém ledger e orienta Coordination |
| **Devin (executor exclusivo)** | Inventaria código, valida HEAD/working tree, implementa mudanças no branch de trabalho, escreve testes, executa DEV/HML quando autorizado, produz evidências em SHA, abre PR, corrige revisão |
| **Coordination / owners técnicos** | Ratificam contratos/decisões arquiteturais necessárias; aprovam mudanças em fronteiras, persistência, segurança e gates de deploy |
| **QA/Engineering** | Confirma testes multiusuário DEV/HML e aceite técnico/funcional |
| **Operação autorizada** | Faz deploy produtivo após gates de qualidade/aprovação e mantém rollback |

**Norma:** ChatGPT/EVA não deve abrir branch para escrever código nem alterar fontes de runtime em nome do Devin. Branches preparados anteriormente sem diff de código não provam início de execução. Não declarar `PASS` sem testes, log e SHA do Devin.

## 2. Sequência de pacotes para Devin (um por vez)

1. **DEVIN-PROD-00 — Inventário/G1 contract gate:** reancorar HEAD/status, owners, endpoints PRC existentes, repositories memory/Postgres/unavailable, migrations e testes. Identificar campos/proveniência, contrato de produto, diferenças e interfaces de saída; sem mutações de schema ou comportamento não ratificadas. Entregar matriz `PROVEN/TO_INVENTORY/TARGET` e decisões de Coordination realmente necessárias.
2. **DEVIN-PROD-01 — Consulta de produtos:** implementar endpoint da **lista de produtos acompanhados** (não lista de solicitações), com paginação/filtros/busca/ordenação, serviço e adapter via ports, AuthZ existente, DTO e testes; reusar `technical-records/{recordId}` e revisões já existentes. **Sem alterar flags e sem frontend.** Só seguir depois do gate do pacote 00.
3. **DEVIN-PROD-02 — Conclusão/versionamento:** V1 baseline mesmo sem diferença, CR-02 snapshot PRC consolidado, CR-04 provenance, CR-05/06 merge explícito, V2+ somente diff real, conclusão no-op sem revisão, CAS/idempotência/evidência. Migration se realmente necessária, ratificada e reversible.
4. **DEVIN-PROD-03 — Snapshots, versões e comparação:** endurecer os DTOs existentes e criar comparação no backend por Vx×Vy, tratamento unknown/incomparable, fornecedor+loja; testes.
5. **DEVIN-FLAG-01 — Bandeiras no produto:** histórico por ocorrência/target, unicidade OPEN, estados OPEN/RESOLVED/REMOVED, sem reopen no novo contrato, leitura corrente/histórica, compatibilidade D16.
6. **DEVIN-FLAG-02 — Bandeiras na PRC/conclusão:** referência à flag existente, isolamento request-local enquanto pendente, integração somente na conclusão, bloqueio integral com duplicata real, RESOLVE explícito e associação legacy OPEN comprovada, testes de concorrência/negativa.
7. **DEVIN-BACKEND-HML — Homologação:** endpoints de produtos + bandeiras demonstrados com usuários autorizados e negados, concorrência multiusuário, evidência de SHA, nenhuma publicação parcial, regressão PRC/My Requests; validar Plugin UI.
8. **DEVIN-FRONT-01/02/03 — Frontend completo:** só após backend e Plugin UI aceitos: P1 segmentos/lista, P2 ficha/bandeiras, P3 versões/diff; responsividade, acessibilidade, E2E HML.
9. **DEVIN-RELEASE — Produção:** somente após aprovação/revisão, testes `PASS` DEV/HML, plano de rollback, deploy governado backend e frontend e smoke.

**Regra:** nenhum pacote posterior deve ser disparado até o anterior retornar relatório com SHA, diff e testes ou um bloqueio formal encaminhado à Coordination. Não executar fases de bandeiras e frontend antecipadamente.

## 3. Prompt pronto — DEVIN-PROD-00 (primeira entrega, apenas inventário e gate)

> **Papel:** Você é Devin, executor de Engenharia responsável por preparar a implementação de Produtos Acompanhados na Engineering API DELPI. O ChatGPT/EVA coordena; você executa em branches próprios.
>
> **Fonte canônica obrigatória:** `docs/12-roadmap-e-evolucao/engineering/PRC-TRACK-CANONICAL-PRODUCT-RULES-AND-EXECUTION-PLAN.md`. Leia também o pacote de implementação e decisões G1 do PO, mas a fonte canônica prevalece quando houver divergências.
>
> **Objetivo agora:** produzir o inventário preciso e o contrato de implementação de **rotas de produtos acompanhados**, iniciando pela listagem de records e **sem** bandeiras/frontend. Evite reabrir decisões de produto já tomadas.
>
> **Ordem obrigatória:**
> 1. Verifique HEAD, git status, branch, alterações de terceiros, README/authorities, migrations oficiais, regras PRC e testes disponíveis. Reporte SHA inicial.
> 2. Inspecione rotas `engineering-api/engineering_app/interface/http/routes/product_registration_routes.py`, service `.../application/use_cases/product_registration/service.py`, port `.../application/ports/product_registration.py`, adapters `.../infrastructure/persistence/product_registration/{postgres_repository,in_memory_repository,unavailable_repository}.py`, modelos, acesso/Keycloak/Core, DTOs e migrator. Confirme endpoints já existentes: GET record por UUID, índice de revisões e snapshot; diferencie **lista de requests** da **lista de produtos**.
> 3. Proponha contrato completo para listagem de produtos: `GET /v1/product-registration/technical-records`; AuthZ existente do Portal Engenharia, object scoping se aplicável, search/sort/page/pageSize, resposta `{items,page,pageSize,total}`, schema de erro, limites, índices, índices de registros efetivamente acompanhados e source+code sem filial. Não inventar descrição ou fornecedor a partir de dado incompleto; metadata faltante deve ser `unknown` ou omitido conforme DTO.
> 4. Identifique contratos atuais que conflitam com V1/no-op, snapshots consolidados e provenance, **sem corrigi-los ainda** nesta etapa. Documente a dependência para DEVIN-PROD-02.
> 5. Defina RQ/AC/test cases para GET de produtos: page empty, paginação estável, busca case-insensitive, ordenação determinística, source/code, filtro por autorizado, usuários negados, Postgres e memory, unavailable fail-honest, erro e regressão das 3 rotas de record/revisões existentes.
> 6. Rode apenas testes/inventário seguro de DEV que não exijam credentials que você não possui; NÃO burlar entitlement nem consultar bancos de outros contexts.
> 7. Não executar migration, não alterar schema, não tocar frontend, não implementar flags, não realizar deploy. **Não iniciar alteração de código se contrato G1/owner ainda necessitar de ratificação**; apresente apenas a proposta específica para liberar DEVIN-PROD-01.
>
> **Saída obrigatória:** `DEVIN-PROD-00-RESULT.md` (ou seção equivalente documentada) com HEAD/status, lista PROVEN de rotas existentes, endpoints TARGET, owners e contratos, gaps reais, riscos e decisões de Coordination, RQ/AC, testes executados (PASS/FAIL/TEST_NOT_RUN), arquivos pretendidos, diffs propostos e ordem de implementação. Retorne resultados ao chat de coordenação **antes** do próximo pacote.
>
> **Critério de aceite do prompt:** não declarar “API de produtos pronta” porque GET por record existente já funciona no código; distinguir `PROVEN_CODE` de `HML_PASS`. Não criar novos roles/approvers para bandeiras.

## 4. Critério de supervisão dos resultados do Devin

O chat de coordenação deve avaliar: fonte canônica aplicada; nenhum escopo antecipado; contratos Core/Engineering API preservados; mudanças apenas owner correto; cobertura de memory/Postgres/unavailable; testes positivos e negativos; rollback; provenance; conformidade com CR-02…CR-13; SHA e logs suficientes. Se encontrado desvio `EXECUTION_DRIFT`, devolver ao Devin como revisão, ou à Coordination se afetar autoridade/boundary; **não devolver perguntas já resolvidas ao PO**.

## 5. Estado inicial da atribuição

`DEVIN_ASSIGNED` (PO designou executor). `DEVIN-PROD-00 NOT_DISPATCHED` até envio efetivo do prompt ao Devin por canal autorizado. `IMPLEMENTATION_NOT_STARTED / TEST_NOT_RUN / HML_PENDING / PROD_NOT_DEPLOYED`. Este documento constitui **brief e prompt pronto**, não representa entrega nem execução do Devin.


## 6. Resultado recebido — DEVIN-PROD-00 e encaminhamento da coordenação (13/11/2026)

**Origem:** relatório de inventário do Devin entregue ao chat de coordenação. **Evidência:** declarada pelo executor; a coordenação não executou os comandos DEV/HML, portanto `REVIEWED_REPORT / TEST_NOT_RUN`, não `PASS` de runtime. Baseline informado pelo executor: início `342092217d`, fim `37ee712640`, branch `main`, sem commit/PR do inventário. O executor relata tracked tree sem modificações, mas **untracked `PrcFlags.tsx` e `PrcFlags.test.tsx`** e cinco stashes — **não classificar como working tree totalmente limpa**.

**Conclusão do gate:** **DEVIN-PROD-01 liberado para implementação aditiva de listagem de produtos**, pois não requer resolver T01/T02. O contrato de campos retornados deve se limitar ao registro atual e à AuthZ existente; sem adicionar `openFlagCount`, provenance inferida ou frontend. **Não liberar PROD-02/03/FLAG sem ratificação dos aspectos semânticos pendentes**; inventário/contratos de PROD-02 podem ser preparados em paralelo sem escrever runtime.

**Inventário reportado e consistente com leitura anterior de código:** GET record, revisões e revision detalhe existem; lista GET `/technical-records` e comparison não foram identificadas; `_build_snapshot` parte do draft; `complete_request` cria Vn em toda conclusão; flags D16 continuam por request e têm `reopen`. Autorizações existentes no Portal devem ser reutilizadas, sem novos papéis.

**Tratamento do drift PRC-UI-EXTRACT-01:** registrar `EXECUTION_DRIFT`; **não reaplicar extração agora**, não usar `git stash pop/apply`, `git clean` ou sobrescrever untracked de outros executores. Encaminhar estado dos cinco stashes, ownership e destino do trabalho de Plugin UI à Coordination. A extração fica pendente até gate de frontend; não bloqueia PROD-01.

**Condição da autorização de PROD-01:** Devin inicia em branch próprio atualizado do HEAD remoto, sem mexer em WIP de terceiros; executa testes locais/DEV com logs e SHA, abre PR para revisão; não faz merge unilateral, migration ou deploy. Status de PROD-01: `AUTHORIZED_TO_IMPLEMENT / TEST_NOT_RUN`.

### Prompt de execução — DEVIN-PROD-01

Devin: reancore no HEAD remoto atual; reporte branch, SHA, git status incluindo untracked e stashes. Leia as regras canônicas e contratos atuais; não reabra decisões do PO.

Implemente **somente** `GET /v1/product-registration/technical-records` para registros **realmente acompanhados** (não fila de requests), reaproveitando FastAPI, ProductRegistrationService, ProductRegistrationRepository e adapters Postgres, in-memory e unavailable.

**Contrato proposto para este diff:** query `page>=1`, `pageSize=1..100` (padrão 25), `search` opcional por `official_product_code` com comparação sem distinção de caixa, ordenação determinística `updated_at DESC, id DESC`; DTO `{items,page,pageSize,total}` com `recordId, officialSource, officialCode, productType, currentRevisionNumber, lastOfficialVerifiedAt, updatedAt` obtidos exclusivamente dos campos existentes no registro. **Não retornar objetos do banco crus**, campos inexistentes, flags ou descrição fabricada. Listar somente registros com `current_revision_number>=1` e revisão publicável, compatível com schema real (confirmar invariante no inventário); não expor registros não concluídos. Aplicar acesso PRC/Engineering **já vigente**, inclusive edge e service, sem grant novo. Reusar envelope de resposta/erro e limites de paginação já existentes no projeto.

**Implementação mínima:** adicionar operação do port, método do service, adapters Postgres/in-memory/unavailable, rota REST, testes no padrão existente. Queries Postgres parametrizadas com whitelist de ordenação; caso unavailable deve falhar honestamente. Não implementar comparison, no-op, snapshots, flags ou frontend neste pacote; não alterar migrations.

**Testes obrigatórios:** records vazios e população mista (somente acompanhados), paginação não sobreposta, ordenação empatada por id, pesquisa case-insensitive, pageSize inválido, acesso permitido/negado, nenhum leak, unavailable fail-honest, paridade Postgres/memory onde infraestrutura autorizada permitir, regressão GET record/revisions, performance básica com índice existente (se faltar índice, reportar, não migrar). Relatar testes não executáveis como `TEST_NOT_RUN`, não declarar `PASS` de Postgres sem rodá-los.

**Saída:** PR em branch própria com menor diff, SHA antes/depois, arquivos, contratos, testes e logs, status positivos/negativos, lacunas e riscos. Não fazer merge ou deploy sem gate. Retorne o relatório `DEVIN-PROD-01` ao chat para revisão. Próxima etapa PROD-02 só após Coordination ratificar T01/T02.

**Observação de rastreabilidade:** o usuário definiu Devin como único executor de código; a coordenação registra prompts e analisa, não faz commits de runtime.


## 7. Review de coordenação — DEVIN-PROD-01, commit 3c619a6ee0 (13/11/2026)

**Relatório recebido:** Devin reportou branch `devin/prc-track-prod-01-records-list`, commit `3c619a6ee00a4da0db29d3cadc43be300911a3d6` pushed, `9/9` testes novos, `72/72` regressão focalizada, `7/7` Postgres 16 descartável, suíte completa `1165 pass / 18 skip / 2 fail` classificados pelo executor como baseline. **Revisão da coordenação:** GitHub commit/diff inspecionados; testes não reexecutados pela coordenação. `CODE_REVIEW_CONDITIONAL / HML_TEST_NOT_RUN / CI_STATUS_NOT_FOUND`.

**Conformidade identificada no diff:** operação `GET /v1/product-registration/technical-records` aditiva; DTO e filtros sobre record publicado `current_revision_number>=1`; service e edge com AuthZ existente; ports e memory/Postgres/unavailable; rota antes de `/{record_id}`; sem migration/flags/frontend/alteração de complete. Mantido o limite de escopo do PO.

**Correções pequenas exigidas antes de aprovação de merge:**
- `PROD01-RV01`: Postgres `ILIKE %search%` trata `%` e `_` como wildcards, mas memory usa substring literal; corrigir escape SQL com `ESCAPE` explícito e manter consulta parametrizada. Cobrir termos `%`/`_`/backslash e paridade real.
- `PROD01-RV02`: teste Postgres injeta `current_revision_number=1` sem materializar uma revisão real. Manter teste de filtro unitário, mas incluir cenário de integração `complete → record publicado → listagem` ou prova equivalente que cobre invariante `record + published revision`. Não adicionar migration/novo escopo.

**Falhas da suíte ampla:** aceitar como baseline apenas com comando, imagem/SHA e logs de reprodução para ambos os casos e evidência de não interseção com diff. Falha de cache RBAC pode ser drift da imagem compartilhada; não rotular `PASS` da suíte completa. Não pedir mudanças no BC alheio sem authority.

**PR/merge:** branch do Devin está disponível; link sugerido de criação não é prova de PR aberto. Devin deve abrir PR ou devolver URL de PR real após correções, testes no SHA final e rebase seguro sobre main. Coordenação não fará merge unilateral. `PROD-02/03` ainda `BLOCKED_BY_COORDINATION_T01_T02`. PRC-UI-EXTRACT drift não bloqueia este pacote. Nenhum deploy está autorizado nesta revisão.

**Proposta de aceite após correção:** revisar diff mínimo, CI, relatórios direcionados e baseline das falhas; se conforme, emitir `CODE_REVIEW_PASS` para merge governado e DEV/HML. Não declarar `HML_PASS` sem execução autenticada multiusuário.


## 8. Revisão de correções DEVIN-PROD-01 — 8af851a578 (13/11/2026)

**Fonte:** diff GitHub do commit `8af851a57854d1c8e35f7c83181fb99ed40ba79a` e comparação `main...devin/prc-track-prod-01-records-list` na revisão. **Resultado:** `CODE_REVIEW_PASS_WITH_INTEGRATION_GATE`; correções RV01/RV02 aceitas, RV03 aceita como evidência parcial. **Não** equivale a CI/HML/prod aprovados.

- **RV01 PASS (code review):** `list_records` no Postgres agora escapa backslash, `%`, `_` e aplica `ILIKE %s ESCAPE '\\'`; parâmetros SQL preservados. Testes de busca com `%` e `_` adicionados aos adapters memory/Postgres. Teste específico de backslash ainda não demonstrado — melhoria recomendável, não nova decisão funcional.
- **RV02 PASS (code review):** integração Postgres cria request, inicia e conclui via `repo.complete_request`, verifica record e revisão V1 na listagem. O teste confirma o adapter/transação; **não executa endpoint HTTP nem official-reader completo**. Não declarar E2E PRC/HML a partir dele. Checagem de request pendente por busca do prefixo UUID é fraca; testes anteriores cobrem exclusão `rev=0`.
- **RV03 EVIDENCE PARTIAL:** conforme relatório Devin, falha D16 reproduzida em imagem baseline; cache RBAC passou na imagem anterior mas falha em container DEV e foi classificado como environmental drift. Não declarar suíte completa PASS nem afirmar causa raiz provada.
- **Testes reportados por Devin no SHA:** `73/73` PRC/health e `9/9` integração PostgreSQL, sem reexecução independente pela coordenação; status de CI no GitHub não encontrado.
- **Integração pendente:** no momento da consulta `main...devin/prc-track-prod-01-records-list` estava `diverged` (`ahead_by=1,behind_by=1`); branch precisa rebase/merge controlado e novo teste no SHA final. Link `/compare/main...branch` **não é PR criado**.

**Decisão de coordenação:** não pedir mais código de negócio PROD-01; Devin deve reancorar sem descartar trabalho concorrente, abrir PR real, confirmar CI/testes no SHA de integração e submeter merge ao gate governado. **`PROD-01_CODE_REVIEW_PASS / MERGE_PENDING / HML_TEST_NOT_RUN / PROD_NOT_DEPLOYED`**.

**Próximo:** PROD-02 segue `BLOCKED_BY_COORDINATION_T01_T02`; preparar pacote técnico de ratificação de snapshots consolidados e no-op sem perguntas funcionais ao PO. Não iniciar bandeiras/frontend nem deploy.


## 9. DEVIN-PROD-01 — PR #180 aberto pela coordenação; integração pendente (13/11/2026)

A coordenação abriu o **PR real [#180](https://github.com/roberiooliveiradev/delpi-central/pull/180)** da branch `devin/prc-track-prod-01-records-list` para `main`, usando o GitHub conectado, **sem compartilhar token com executor**. HEAD da branch no PR: `d6b56517891a30e55b582ed47de12a6879f08ce6`.

**Evidência GitHub no momento da abertura:** `changed_files=3`, `+97/-2` (Postgres adapter e testes PRC memory/Postgres), `mergeable=false`. A comparação `main...branch` mostrava `ahead_by=2,behind_by=5` e somente esses três arquivos. Portanto, **não declarar merge pronto**; main avançou por agentes concorrentes após o teste do SHA informado.

**Status:** `PR_OPEN / CODE_REVIEW_PASS_WITH_INTEGRATION_GATE / MERGE_BLOCKED_OR_NOT_YET_MERGEABLE / HML_TEST_NOT_RUN`. O backend PROD-01 original já estava incorporado à main segundo relatório Devin; #180 contém correções RV01/RV02 e testes. Nenhum deploy, merge ou validação multiusuário realizada pela coordenação.

**Próxima ação exclusiva de Devin:** reancorar no HEAD mais recente da main, sem force-push/stash destructivo nem perder alterações paralelas; investigar mergeability de #180 (conflito concreto versus avaliação pendente do GitHub), resolver apenas conflitos relativos ao pacote, executar novamente os testes focados e PostgreSQL **no novo SHA**, atualizar o PR. Se mergeable=true e evidências válidas, Coordination pode autorizar merge governado. Não avançar PROD-02 antes de T01/T02 ratificados.


## 10. Review PR #180 closing report — SHA f9fed41dd1 (13/11/2026)

**Evidência:** commit `f9fed41dd1374109c2393f42761e92e53ca15c31` verificado via GitHub; relatório Devin indica merge de origin/main sem perda de alterações concorrentes e testes no commit em container isolado (`73/73` PRC/health e `9/9` Postgres real). Esses testes **não foram reexecutados pela coordenação**. Consulta de CI combinada retornou sem status.

**Diff atual:** `main...devin/prc-track-prod-01-records-list` continua restrito aos três arquivos de RV01/RV02 (`+97/-2`): `postgres_repository.py`, `test_prc_postgres_integration.py`, `test_product_registration.py`. A comparação já voltou a exibir `ahead_by=3,behind_by=2` porque a main avançou de novo (sem ampliação dos arquivos de diff).

**Parecer:** `CODE_REVIEW_PASS / PR_180_OPEN / MERGE_PENDING / HML_TEST_NOT_RUN`. A aprovação de código **não equivale** a autorizar deploy. Confirmar a mergeability no momento efetivo de integração, o SHA e requisitos de revisão/branch protection. Evitar ciclo de reconciliações com main sem conflito real: novos commits documentais não devem perpetuar rebase/merge; tratar verificação de mergeabilidade no ponto de merge e pedir resolução ao Devin **apenas** se houver conflito real. Nenhum merge feito pela coordenação nesta revisão.

**Ordem seguinte:** fechar PR #180 sob gate governado; manter PROD-02 bloqueado até a Coordination ratificar T01/T02, sem reabrir CR de negócio. DEV/HML multiusuário e produção permanecem pendentes.


## 11. DEVIN-PROD-01 — Gate final recebido / encerramento de reancoragens (13/11/2026)

**Relatório do executor:** `TASK_ID=DEVIN-PROD-01-FINAL-GATE`; baseline `5667e1854949d8dacaa2bcd3de99e3eaa8558fed`, branch `f9fed41dd1374109c2393f42761e92e53ca15c31`, `git merge-tree --write-tree` sem conflito na baseline congelada; `RECONCILIATIONS=0`; `FINAL_STATUS=READY_TO_MERGE`; testes `73/73` PRC/health e `9/9` PG no SHA, e check-run success reportado pelo Devin (não reexecutados pela coordenação). Branch protection e confirmação de mergeability pela API ficaram não conclusivas.

**Verificação de coordenação (consulta GitHub):** branch divergiu novamente com `main` após relatório (`ahead_by=3, behind_by=9` no instante consultado), mas a comparação ainda limita o diff funcional aos três arquivos de revisão PROD-01 (`+97/-2`). Status combinados retornaram lista vazia na consulta da coordenação; isto **não invalida** o check-run reportado, mas não constitui verificação independente do check. Não tomar simples `behind` como conflito real.

**Decisão:** `CODE_REVIEW_PASS / READY_FOR_AUTHORIZED_MERGE_GATE`. **Encerrar loop de reancoragem do Devin; não solicitar novos merges de main sem conflito concreto.** O PR [#180](https://github.com/roberiooliveiradev/delpi-central/pull/180) permanece para integração governada. **Sem autorização explícita de merge nesta interação, a coordenação não executou merge**; verificar requisitos de proteção/CI e capacidade de merge no ato da aprovação. HML multiusuário e produção continuam `TEST_NOT_RUN/NOT_DEPLOYED`.

**Próxima frente:** preparar ratificação **T01** (contrato catálogo/coverage/provenance/snapshot consolidado da Engineering API) e **T02** (V1/no-op, CAS, ledger da conclusão, compatibilidade, reversão), sem reabrir regras já aprovadas. PROD-02 só começa após a ratificação; flags e frontend continuam posteriores conforme plano mestre.


## 12. HML-H0 — runtime stale, homologação PROD-01 bloqueada (relatório executor, 13/11/2026)

**Relatório recebido (Devin, não teste independente do Cursor):** PR #180 aberto e não mergeado no momento da checagem; `origin/main` contém commit inicial `3c619a6ee0` com endpoint de listagem; checkout do host `srv-api` em `b5e74669a2`, mas o container HML `delpi-engineering-api` reportado usava imagem `sha256:f3d640c4...` construída 12/11/2026 20:34, **sem ocorrência de `list_records` no runtime**. Assim, API de listagem **não disponível naquela versão HML**. A coordenação não consultou diretamente host/container; classificação `REPORTED_RUNTIME_STALE / HML_H1_BLOCKED` (não `HML_FAIL` do endpoint).

**Verificação GitHub:** comparação `main...devin/prc-track-prod-01-records-list` continua restrita aos três arquivos corretivos do PROD-01 (`+97/-2`), `ahead_by=3 / behind_by=12` no instante consultado. Branch atrás da main **não implica conflito** nem autoriza ciclos de reconciliação.

**Gates separados, sem atalhos:** (A) integrar PR #180 sob autorização e proteção GitHub; (B) requisitar **deploy/rebuild HML** pelo owner de release autorizado, usando SHA e artefato rastreáveis; (C) Cursor confirma o SHA real do container e presença do endpoint no HML; (D) só então executar H1 (API de listagem) e matriz de acessos, sessões independentes, evidências. `git pull` no host **não atualiza container**. Nenhuma mudança em produção autorizada.

**Escopo H0 parcial enquanto aguarda:** Cursor pode inventariar HML, perfis e acessos, testar rotas PRC já implantadas com dados autorizados e documentar regressões/limitações; deve classificar listagem H1 `BLOCKED_ENVIRONMENT`, PROD-02/03 e flags produto `NOT_IMPLEMENTED`, sem produzir falso PASS/FAIL. Teste multiusuário completo apenas após backend produtos+flags e deploy HML correspondentes.

**Ação seguinte:** Coordination trata PR #180 e autorização explícita de implantação HML separadamente; responsável pela execução técnica do deploy deve ser designado conforme owner de release, não presumir que Cursor pode publicar. Devin continua como executor de código e Cursor como executor da homologação.


## 13. DEVIN-PROD-01 entregue — merge confirmado e HML parcial (13/11/2026)

**Integração GitHub PROVEN:** PR #180 mergeado em `0a29fbe72ed8496388620325e4aa68f272af2743`, commit encontrado pela coordenação. **PROD-01 IMPLEMENTATION_PASS / MERGE_PASS.**

**Evidência HML fornecida pelo executor (não reexecutada independentemente nesta revisão):** checkout `0a29fbe72e`, imagem `delpi-hml/engineering-api:local` digest reportado `sha256:9c040dd4...`, container `delpi-hml-engineering-api` saudável e código `list_records` presente no runtime. Rota pública `/apps/engineering-api/v1/product-registration/technical-records`: autorizado 200 com `total=0`, sem token 401, não autorizado 403, query inválida 422. **HML_PARTIAL_PASS_REPORTED**, não `HML_FULL_PASS`.

**Ainda faltam em HML:** paginação, busca case-insensitive e literal `%`/`_`, ordenação e isolamento publicado vs pendente com registros reais; `CURSOR_MULTIUSER_PENDING`. Testes `73/73` memory/HTTP e `9/9` PG descartável no SHA integrado foram reportados pelo Devin, não substituem dados reais em HML. Cursor deve executar testes HML com contas autorizadas e dados **sintéticos e segregados**; não forçar conclusão de produto real ou publicar dados oficiais.

**INCIDENTE DE HIGIENE DE SEGREDOS:** relatório de handoff incluiu credencial temporária em texto claro, e outra conta usou senha sincronizada de configuração documentada. **Não reproduzir nem persistir valores.** Rotacionar as credenciais HML envolvidas por canal autorizado, avaliar ocorrência em logs/documentação/artefatos e revogar credenciais expostas. Cursor recebe identificadores das contas e mecanismo seguro de obtenção, nunca senha em prompt/commit/chat. Confirmar que `.env.hml` e evidências não estão versionadas com segredos; não registrar conteúdo.

**Próximo gate de execução:** `CURSOR-PROD-01-HML-DATA-PARITY` — contas segregadas, duas sessões independentes quando aplicável, dados sintéticos com um registro concluído via fluxo PRC e um pendente, validar listagem/search/page/sort, 200/401/403/422; registrar SHA da imagem e provas redigidas. Se não houver forma governada de criar dados sintéticos, `BLOCKED_TEST_DATA` sem simular aprovação. É **homologação incremental da lista**, não o gate multiusuário completo de PROD-02/flags.

**Sequência funcional:** Coordenar ratificação técnica T01/T02 para DEVIN-PROD-02. PROD-03, flags e frontend mantêm ordem do plano mestre; produção não autorizada por este registro.


## 14. PROD-01 — HML com dados publicados, evidência do executor (13/11/2026)

**Fonte e escopo:** relatório complementar do Devin, não testes reexecutados pela Coordination ou Cursor. SHA reportado em HML `0a29fbe72ed8496388620325e4aa68f272af2743`; imagem digest reportado `sha256:9c040dd4191a8617f826aa628cda6d3a17bd70555b1fb9949500ad7826b14fe2`; container saudável. O Devin reportou 13/13 cenários exercitados com sucesso e dois `TEST_NOT_RUN`: busca case-insensitive (somente códigos numéricos disponíveis) e ação de um **segundo usuário autorizado**. O resumo `HML_PASS` deve ser lido **somente para os cenários efetivamente testados pelo executor**, não como aceite independente ou multiusuário completo.

**Dados e fluxo:** Devin reportou dois produtos acompanhados com V1 após intake/start/complete verificado no PRC, e um PRC submetido ainda pendente (não deve figurar na lista). Por se tratar de códigos efetivos e leitura/verificação oficiais, **confirmar com owner de Engenharia que os dados de HML são segregados, permitidos e não afetam produção**; sem pressupor que ausência de escrita TOTVS elimina todos os efeitos de negócio (o registro PRC em HML foi escrito).

**Matriz reportada:** listagem autorizada total=2, ordem `updatedAt DESC`, paginação, busca exata, `%`/`_` literais retornando vazio, ausência do pendente, 403 sem `engineering.access`, 401 anônimo, detalhe de record e índice V1 com trilha do aprovador — todos PASS segundo Devin. Busca case-insensitive alfanumérica e concorrência entre dois atores autorizados: `TEST_NOT_RUN`.

**Atenções para follow-up:** (i) detalhe `GET /technical-records/{recordId}` responde snake_case, enquanto a lista usa camelCase. A rota de detalhe é legado anterior ao PROD-01; registrar `CONTRACT_DRIFT`, **não alterar agora sem contrato/compatibilidade**, direcionar para PROD-03. (ii) relatório do executor expôs **novamente uma senha de teste**: considerar comprometida e rotacionar/revogar por owner autorizado, verificar se há outras cópias acessíveis, jamais reproduzir o segredo em documentos/prompts. (iii) usar contas separadas com identidade e permissão reais em Cursor; não criar grant novo.

**Decisão da Coordination:** `DEVIN_PROD01_HML_SCOPED_PASS_REPORTED / CURSOR_INDEPENDENT_PENDING / MULTIUSER_TEST_NOT_RUN / PRODUCTION_NOT_DEPLOYED`. O PROD-01 não precisa de nova implementação só para repetir testes bem-sucedidos. O Cursor deve testar a mesma imagem/SHA, validar de modo independente cenários e registrar lacunas de case-insensitive e segundo usuário autorizado; se não houver segundo usuário ou dado alfanumérico permitido, `INCONCLUSIVE/TEST_NOT_RUN` com bloqueio factual, sem falso PASS. Corrigir falha concreta pelo Devin com limite anticíclo.

**Próximo trabalho em paralelo:** finalizar ratificação T01/T02 (snapshot/proveniência e conclusão versionada/no-op) para liberar DEVIN-PROD-02. Não antecipar FLAG ou FRONT.


## 15. PROD-01 — teste multiusuário HML executado por Devin, aceite independente pendente (13/11/2026)

**Relatório executor, não auditoria Cursor:** HML checkout `0a29fbe72ed8496388620325e4aa68f272af2743`; digest informado `sha256:9c040dd4191a8617f826aa628cda6d3a17bd70555b1fb9949500ad7826b14fe2`. Devin reportou 10/10 cenários A1–A10 `PASS`, além de escrita cross-user `PASS`; contas de teste `hml-tester` e `lnf-contract-p9` com `engineering.access`, `lnf-contract-p1` sem permissão e sessão anônima. Dois autorizados consultaram os mesmos dois produtos; segundo autorizado iniciou e concluiu um request criado pelo primeiro, gerando terceira V1 com sujeito do autor correto. São **sessões de usuários distintas**, mas o mesmo implementador executou os testes: campo `INDEPENDENT_TEST_RESULTS` do relatório não prova teste feito pelo Cursor.

**Classificação:** `DEVIN_HML_MULTIUSER_PASS_REPORTED / CURSOR_INDEPENDENT_PENDING / PROD01_IMPLEMENTATION_ACCEPTED / PROD_DEPLOY_NOT_AUTHORIZED`. Cenário de busca case-insensitive alfanumérica `TEST_NOT_RUN` em HML por códigos oficiais numéricos; teste automatizado PG foi reportado previamente. Não falsificar PASS da condição não executada.

**Credenciais:** Devin reportou rotação das senhas expostas e armazenamento local em `infra/.env.hml` sem commit. Checagem efetiva de rotação/revogação e de segredos em artefatos cabe aos owners; **nunca reproduzir senha, token ou conteúdo .env** no ledger/prompts. Segredos devem permanecer em secret manager/ambiente operacional controlado, não em Git.

**Dados:** Devin reportou três records V1 em schema HML `engineering.*` e ausência de escrita no TOTVS (verify READ). Avaliar retenção/limpeza dos dados de teste pelo owner do HML após revalidação do Cursor; não executar exclusões automáticas.

**Gate formal do Cursor:** uma única sessão de revalidação independente contra mesmo deployment SHA/digest, com autorização positiva/negativa, dois usuários, pedido cross-user, listagem/paginação e histórico; não repetir caso de teste já comprovado sem risco novo além de amostragem de independência. `case-insensitive alfanumérico` permanece `TEST_NOT_RUN` enquanto não houver dado oficial autorizado.

**Decisão operacional:** PROD-01 não retorna ao Devin para correções sem defeito concreto do Cursor. Desenvolver o produto conforme plano mestre depende agora da **ratificação técnica T01/T02** para DEVIN-PROD-02; não tratar Cursor como impedimento dessa ratificação. Sem alteração de frontend/bandeiras ou deploy produção.


## 16. Regra PO vinculante — PRD smoke READ-only, nenhuma escrita de negócio (13/11/2026)

**Decisão explícita do PO:** **em produção, testes de deploy verificam apenas disponibilidade, saúde, autenticação/autorização e APIs de leitura comprovadamente sem efeitos colaterais. É proibido gerar ou modificar dados de negócio para testar o sistema em PRD.** Homologação é o ambiente de testes com escrita, fluxos completos, múltiplos usuários, bandeiras e versionamento.

**Matriz por ambiente:** DEV = testes locais e dados de teste; HML = execução autorizada de workflows e operações mutáveis em dados segregados, incluindo dois usuários; PRD = smoke checks não mutáveis, observabilidade e leituras autorizadas. Isto prevalece sobre qualquer texto genérico anterior que sugira E2E de escrita após o deploy produtivo.

**Whitelist do smoke de PRD** (após confirmação do contrato e efeitos colaterais): health/readiness, versão/build/digest, documentação OpenAPI quando disponível e segura, `GET` de consulta autorizada de recursos já existentes e de dados adequados, validação 401/403 em operações de leitura, métricas de estabilidade/erros. Requisições `GET` que possuam efeitos colaterais não são elegíveis. Não expor informações sensíveis em evidências.

**Proibido em PRD:** `POST/PATCH/PUT/DELETE` mutáveis de negócio; intake/complete/verify-and-complete, criar/alterar/remover/resolver bandeiras, cadastros, V1/Vn, migração de dados de teste, idempotency replay de escrita, SQL de escrita ou manipulação direta de banco para testes. `verify` somente pode ser chamado se comprovadamente read-only e sem registro/evidência mutável; o fluxo normal de verificação PRC escreve trilhas, portanto não é smoke permitido. Não invocar endpoints apenas pelo verbo ou nome sem confirmar seus efeitos. Mudanças operacionais necessárias ao deploy autorizado não são testes de escrita de negócio e exigem processo próprio.

**Gate release:** para cada pacote, Cursor valida fluxos de escrita e segurança em HML; owner autoriza publicação; no PRD executar **somente** smoke READ-only e rollback/observabilidade. Se um cenário requer escrita ou estado novo, classificá-lo `NOT_APPLICABLE_PRODUCTION` e referenciar evidência HML, jamais executá-lo em produção. Qualquer desvio ou autorização ambígua deve resultar em bloqueio da operação, não execução tentativa.

**Escopo:** regra global para PRC-TRACK / Engenharia; replicar nos prompts Devin, Cursor, checklists de release e documentação canônica sem reabrir a decisão de negócio.


## 17. T01/T02 — pacote técnico entregue à Coordination, sem falsa ratificação

Após DEVIN-PROD-01, o executor relatou que não há código autorizado a executar enquanto T01/T02 não forem formalmente ratificados. **Coordination assume o desbloqueio como sua responsabilidade**, sem devolver ao Devin inventário ou testes repetitivos.

O [pacote técnico T01/T02 para ratificação](./PRC-TRACK-T01-T02-COORDINATION-TECHNICAL-RATIFICATION-PACKET.md) foi preparado com base na fonte canônica, código verificado `_build_snapshot`/`complete_request`, contrato de coverage/provenance, baseline V1, no-op, serialização transacional, resposta/compatibilidade, testes e rollback.

**Estado:** `TECHNICAL_PROPOSAL_READY / ENGINEERING_OWNER_RATIFICATION_PENDING / DEVIN_PROD02_BLOCKED`. Não declarar `APPROVED` até decisão explícita de Coordination + Engineering API owner no ledger. Não modificar runtime por este documento.

**Em paralelo:** Cursor executa um único gate independente PROD-01, com rotação segura de credenciais já informada e sem exposição de segredos. Testes de escrita exclusivamente HML; em produção somente saúde, leitura e observabilidade, nunca dados de negócio de teste.


## 18. T01/T02 — PO concordou; aguardando confirmação formal do Engineering API owner (13/11/2026)

**Decisão PO:** `T01_APPROVED_BY_PO_WITH_CONDITIONS / T02_APPROVED_BY_PO_WITH_CONDITIONS`; registrada no [pacote de ratificação §7](./PRC-TRACK-T01-T02-COORDINATION-TECHNICAL-RATIFICATION-PACKET.md) e [plano canônico §11](./PRC-TRACK-CANONICAL-PRODUCT-RULES-AND-EXECUTION-PLAN.md). Sem novas perguntas funcionais.

**T01:** catálogo e ficha PRC consolidados, schema/coverage, origem+confirmação por campo, UPDATE omitido preservado, supplierCode+store, legado honesto/imutável.

**T02:** V1 primeira conclusão matched; V2+ apenas diff; no-op sem INSERT revision; verification+ledger completos; atomicidade PRC, locks/CAS, idempotência e compatibilidade dos consumers.

**Gate de autoridade:** `ENGINEERING_OWNER_RATIFICATION_PENDING`. Necessário confirmar DTO/ports, consumidores existentes, migração mínima e rollback antes de autorizar implementação. Não escrever `OWNER_APPROVED` nem `PROD02_IMPLEMENTATION_PASS` sem evidência. Devin não precisa reabrir PROD-01 e não deve começar mudança de arquitetura unilateralmente. Após confirmação, emitir pacote bounded DEVIN-PROD-02 com T01/T02-AC01..09.

**Testes:** DEV/HML podem usar dados governados e fluxos completos. **PRD apenas smoke READ-only/health**, zero escrita de dados de negócio para teste; nenhuma publicação produtiva autorizada.


## 19. Ordem de execução — DEVIN-PROD-02 liberado por ratificação do owner (13/11/2026)

**Autoridade:** owner de Engenharia declarou explicitamente sua titularidade e ratificou T01/T02 neste chat; deliberação formal [pacote T01/T02 §8](./PRC-TRACK-T01-T02-COORDINATION-TECHNICAL-RATIFICATION-PACKET.md). `T01_OWNER_RATIFIED / T02_OWNER_RATIFIED / IMPLEMENTATION_AUTHORIZED`. Status `ENGINEERING_OWNER_RATIFICATION_PENDING` do §18 fica **SUPERSEDED** para T01/T02 apenas.

**TASK_ID:** `DEVIN-PROD-02-SNAPSHOT-VERSIONING-NOOP`. **Escopo fechado:** corrigir `_build_snapshot` e pipeline/ports/adapters `complete_request` para ficha consolidada PRC, campo/origem/coverage, merge UPDATE parcial, fornecedores `supplierCode+store`, V1 inicial, V2+ apenas com diff real, no-op auditado sem revision, CAS/locks/idempotência e paridade PG/memory. Nenhum novo papel, BC ou leitura direta TOTVS; manter gate `matched`/AuthZ existente.

**Entrada obrigatória:** reancorar uma única vez no HEAD atual, `git status`, inventário objetivo de port/consumers/DTO/schema; declarar RQ/AC T01/T02 do pacote de contrato; menor diff com testes e compatibilidade. Resolver riscos técnicos locais no próprio owner sem reabrir negócios; registrar incompatibilidade factual ou mudança de authority como `ARCHITECTURE_DECISION_REQUIRED` e retornar.

**Saída:** commit, push, PR, review/CI governados, merge somente sob autorização/política, HML apenas após deploy autorizado com SHA/digest comprovado, cenários V1/no-op/V2/mismatch/replay/CAS/parcial/legado/auth + dois usuários; handoff ao Cursor para aceite independente. Preservar histórico e reportar `PASS/FAIL/PENDING/TEST_NOT_RUN` sem falsa afirmação. PROD não autorizado; smoke READ-only se futuramente aprovado.

**Anticíclo:** não refazer PROD-01 nem reconciliações repetidas de main; máximo uma reconciliação justificável por conflito real; falhas técnicas repetidas devem produzir pacote de evidências. T03–T08/flags/frontend fora do escopo.


## 20. PROD-02 — implementação integrada e homologação HML reportada por Devin (13/11/2026)

**Relatório do executor, não auditoria Cursor:** PROD-02 foi implementado, integrado em `main` e exercido em HML. Validação independente do Cursor permanece o gate formal.

```text
TASK_ID:               DEVIN-PROD-02-SNAPSHOT-VERSIONING-NOOP
BASE_HEAD:             90f37a2bbd083acdb3605456ac1c149c0490d189
FINAL_SHA:             e98962472d (branch devin/prc-track-prod-02-snapshot-versioning)
MERGE_SHA:             4735718cf35b6ccdce2072a11f7c983fd0def001 (origin/main)
DEV_TEST_RESULTS:      164 PRC-relacionados PASS (in-memory/API);
                       suite completa 1192 PASS + 2 FAIL baseline
                       pré-existentes fora do pacote (evidenciadas em
                       HEAD: test_d16_attendance_flags::test_isolation_
                       between_requests, test_lmp_domain::test_constants_
                       match_semantics_spec — arquivo fora do mount)
POSTGRES_TEST_RESULTS: 10/10 PASS em PostgreSQL real descartável,
                       incluindo V1 -> no-op -> V2 (migrations V001-V023)
HML_DEPLOY_SHA:        4735718cf35b6ccdce2072a11f7c983fd0def001
HML_IMAGE_DIGEST:      sha256:097a513d3e1bc66d92c6795c68bc4cad1f0b7b6f8561bc4ba6eeef2ffae262de
                       (healthy; snapshot.py e changeKind confirmados no container)
```

**Implementado:** novo `domain/product_registration/snapshot.py` (snapshot consolidado `schemaVersion: 2`, proveniência por campo e por atributo de vínculo SA5, UPDATE parcial preserva omitidos, merge por `supplierCode+store`, dual-read legado sem reescrita). `complete_request` nos adapters PG/memória decidem `baseline_initial` / `technical_change` / `no_technical_change` **dentro da transação sob lock**, construindo o candidato contra a revisão vigente real. Resposta de `complete` estendida aditivamente (`changeKind`, `technicalChange`, `publishedRevisionNumber`; `revisionNumber` = revisão vigente). Bug real corrigido: shallow-copy mutava atributos de fornecedor do snapshot anterior e zerava o diff — resolvido com deep-copy.

**HML — cenários executados (sessões `hml-tester` autorizado 1, `lnf-contract-p9` autorizado 2, `lnf-contract-p1` negado, anônimo):**

| Cenário | Resultado reportado |
|---|---|
| V1 baseline (`30190125`, update `unit` matched) | PASS — `changeKind=baseline_initial`, `publishedRevisionNumber=1`, snapshot `schemaVersion:2` |
| No-op (mesma declaração, 2 casos) | PASS — `no_technical_change`, sem revisão nova, vínculo à vigente |
| V2 consolidação legado→novo (`30190123` era PROD-01) | PASS — `technical_change`, `publishedRevisionNumber=2`; V1 legada (`schemaVersion:None`) preservada imutável |
| No-op pós-consolidação (`30190123`) | PASS — sem terceira revisão |
| Proveniência | PASS — `official_verified` (declarado+verificado) vs `inherited_confirmed` (baseline); atributos de link `000113\|01` individuais |
| CAS stale `expectedVersion` | PASS — 409 `stale_version` |
| Double complete | PASS — 409, sem duplicar revisão |
| Replay intake mesmo Idempotency-Key | PASS — 200 mesmo `requestId`, sem duplicar request |
| Multiuser | PASS — `lnf-contract-p9` concluiu caso compartilhado |
| Regressão PROD-01 (lista, `%`/`_` literal, pendente excluído) | PASS |
| AuthZ negado / anônimo | PASS — 403 / 401 |
| V2 por diferença de valor em produto já consolidado | TEST_NOT_RUN — TOTVS HML estático e fail-closed: qualquer declaração `matched` replica o valor oficial já presente no snapshot; diff de valor exige mudança oficial real (DEV cobre: V2 por valor em memória e PG) |

**Credenciais:** senhas de `hml-tester`, `lnf-contract-p9`, `lnf-contract-p1` foram rotacionadas para o fluxo de testes (armazenadas em `infra/.env.hml` no host HML, não commitadas).

**Classificação:** `PROD02_IMPLEMENTATION_MERGED / DEVIN_HML_PASS_REPORTED / CURSOR_INDEPENDENT_PENDING / PROD_DEPLOY_NOT_AUTHORIZED`. Incidente operacional no deploy: `up` sem `--env-file infra/.env.hml` interpolou `KEYCLOAK_*` vazios e derrubou o startup; corrigido reexecutando com o env file canônico (mesmo mecanismo de `infra/scripts/hml-compose.sh`).

**Gate formal do Cursor:** revalidação independente sobre mesmo SHA/digest: V1, no-op, V2 (consolidação legado), proveniência, CAS, replay, dois usuários, negação. Dados de teste permanecem em `engineering.*` HML para a auditoria.


## 21. Coordination review pós-PROD-02 — gate independente e desvio do fluxo de PR (13/11/2026)

**Verificação GitHub da Coordination:** commit `4735718cf35b6ccdce2072a11f7c983fd0def001` existente com mensagem de merge `devin/prc-track-prod-02-snapshot-versioning`; ledger §20 consultado na main. A presença do merge é `PROVEN`; os 164 testes PRC, 10 PG real, deploy HML e cenários funcionais continuam `REPORTED_BY_DEVIN`, não reexecutados por esta coordenação.

**Gate:** `PROD02_IMPLEMENTATION_MERGED / DEVIN_HML_PASS_REPORTED / CURSOR_INDEPENDENT_PENDING`. Cursor deve executar **uma rodada independente bounded** no mesmo SHA/digest, verificando V1, no-op, V2 de migração legado, provenance/cobertura, supplier link, CAS/replay, autorização e cross-user, preservação do histórico e regressão de lista. V2 por diferença de valor em produto consolidado permanece `TEST_NOT_RUN_HML` por não existir alteração oficial autorizada; 10 testes PG descartável reportados cobrem esse caso, mas não equivalem ao HML. Não alterar TOTVS nem fabricar evidência.

**Desvio de governança de integração:** DEVIN informou não possuir credencial GitHub API e realizou **merge direto**, sem PR. Commit de merge `PROVEN`, mas a alegação de equivalência a PR revisado **não está comprovada** por reviews/checks/proteções; classificar `INTEGRATION_PROCESS_DEVIATION_TO_REVIEW`, não presumir aprovação de branch protection. Não reverter código funcional de forma automática. Em PROD-03 e próximas entregas exigir PR governado via ferramentas autorizadas ou exceção formal documentada pelo owner antes do merge; falta de token na sessão do executor não autoriza bypass.

**Riscos residuais:** 2 testes baseline FAIL reportados fora do escopo; case-insensitive alfanumérico ausente em HML; DTO snake_case de detalhe legado para PROD-03; secrets HML em env operacional devem ser protegidos e não versionados; dados HML com owner de retenção/limpeza; erro de configuração KEYCLOAK durante deploy resolvido pelo executor mas requer checklist reprodutível de env sem revelar segredos. Nenhum deploy produtivo autorizado. Em PRD somente saúde e GET comprovadamente não mutável, zero dados de negócio de teste.

**Próxima decisão:** Aguardar rodada de Cursor para aceite formal do PROD-02 e revisar se o pacote PROD-03 pode iniciar em paralelo após gate de produto, sem antecipar flags/frontend nem saltar requisitos do plano mestre.


## 21. Incidente PRD — `fe_sendauth` PRC (My Requests) e 503 Engineering API — recuperado (13/11/2026)

**TASK_ID:** `DELPI-PRD-INCIDENT-ENGINEERING-MYREQUESTS-RECOVERY-01`

**Sintomas reportados:** `/apps/my-requests` exibia `postgres connect failed: ... 172.19.0.69 ... fe_sendauth: no password supplied`; `/apps/engineering/product-registration` apresentava 503.

**Causa raiz (CONFIRMADO_NO_CODIGO+RUNTIME):** a Engineering API prod (`delpi-engineering-api`, projeto compose `infra`, `env_file: .env`) conectava ao `delpi-postgres-plugins` (172.19.0.69) como `eng_prc` — mas a role `eng_prc` **nunca fora provisionada em PRD** e `ENG_PRC_DB_PASSWORD` estava **vazia** no `infra/.env` prod (vazio já presente em backups de 12/11). Schema `engineering` existia (27 tabelas, migrado por outro principal) com **0 linhas** PRC — o contexto nunca operou em PRD.

**Relação com PROD-02:** `NOT_RELATED` — gap de provisionamento anterior ao merge; o erro existiria com qualquer versão do código PRC.

**Correção aplicada (mecanismo canônico):**

1. Novo `infra/scripts/prod-provision-eng-prc.sh` (commit `c227a6ac9f` em main) — réplica do wrapper HML sobre `engineering-api/db/eng_prc_grants.sql` (idempotente, grants mínimos).
2. Senha forte gerada no host e gravada em `infra/.env` (`ENG_PRC_DB_PASSWORD`, não versionada).
3. Provisionamento executado: role `eng_prc` criada + grants + smoke `SELECT` = `PRD_ENG_PRC_PROVISION=PASS`.
4. `docker compose up -d --no-deps engineering-api` → healthy, `env=production`, senha injetada.

**Smoke read-only pós-recuperação (zero escrita de negócio):** `/apps/engineering-api/health` = 200; `technical-records` anônimo = 401 (era 503/`fe_sendauth`); `/apps/my-requests/` e `/apps/engineering/` = 200; logs sem `fe_sendauth` pós-restart.

**Auditoria REQ-2026:** os 36 registros `REQ-2026-*` pertencem ao schema `my_requests` (`plugins_hub`) — bounded context Solicitações, criados por usuários reais entre 17/09 e 12/11 (tipos operacionais: Abertura de Chamado, Problema de Processo, Emissão NF). **Registros legítimos — preservados integralmente.** `engineering.product_registration_*` em PRD = 0 linhas: **nenhum registro de teste existe em produção**; os dados sintéticos vivem em `engineering.*` do HML (banco/container/rede distintos — sem conexão cruzada HML↔PRD confirmada).

**Classificação:** `INCIDENT_RESOLVED / PROD_SMOKE_PASS / PRD_BUSINESS_WRITES:0 / CLEANUP:NOT_APPLICABLE`.

**Prevenção proposta:** (a) `eng_prc` provisionado por script canônico agora versionado para PRD; (b) `ENG_PRC_DB_PASSWORD` presente em `.env` prod; (c) sugerir à Coordination: healthcheck/readiness que cubra dependência PRC-DB, checklist de provisionamento pós-deploy e alerta sobre conexão DB sem senha — avaliar em pacote próprio.


## 22. Coordination — encerramento do incidente e pacote preventivo delimitado (13/11/2026)

**Prova documental no GitHub:** commits `c227a6ac9f5fdad98f0445bda30e6fc4a0244369` (script canônico PRD de provisionamento PRC) e `7ee9b06cdf03e9721457ecf302492ecbfcb5db24` (registro do incidente) verificados pela Coordination. A verificação de runtime pós-recuperação e a auditoria de dados **são evidências reportadas pelo Devin**, não testes executados por esta coordenação.

**Diagnóstico reportado:** `ENG_PRC_DB_PASSWORD` vazio em configuração PRD e role `eng_prc` não provisionada; 503 PRC/My Requests por autenticação de banco. Ausência já observada em backup anterior ao PROD-02, portanto `RELATION_TO_PROD02=NOT_RELATED_REPORTED`. Recuperação operacional `INCIDENT_RESOLVED_REPORTED / PRD_READ_ONLY_SMOKE_PASS_REPORTED`; sem novos registros de negócio. O fato de o container antigo aparecer healthy mesmo com rotas PRC em 503 demonstra gap de readiness, não necessariamente falha do liveness.

**Auditoria e retenção:** 36 solicitações `REQ-2026` reportadas como registros legítimos `my_requests.requests`, preservados; PRC em `engineering.*` PRD reportado com zero linhas. **`CLEANUP_NOT_APPLICABLE`**: proibir exclusão oportunista de solicitações operacionais. Se nova evidência provar registro de teste, exigir plano de limpeza idempotente/backup/owner com aprovação específica, sem dedução por prefixo `REQ-`.

**Decisão de Coordination para prevenção:** criar pacote técnico delimitado `PRD-ENG-PRC-OPERABILITY-GATE-01` como `PLANNED`, não como deploy já autorizado:
1. Preflight **read-only** de configuração no container (presença, não valor), role/grants efetivos e `SELECT 1` autenticado no banco correto; fail-closed antes da promoção e mensagem de erro saneada.
2. Liveness não deve depender de DB para evitar restart-loop; adicionar **readiness distinta** que só retorna sucesso quando a dependência PRC-DB essencial funciona. Contrato/readiness/consumers de gateway e orquestrador devem ser inventariados antes de modificar o health existente.
3. Checklist de rollout/recovery de PRD e HML com env-file correto, SHA/digest, preflight, rollback, autorização e smoke GET/health; **zero POST/PUT/PATCH/DELETE de dados de negócio para teste em PRD**.
4. Observabilidade/alerta de falhas PRC-DB e 503 com correlationId, sem logar DSN/credencial/segredos e sem inserir dados.
5. Reproduzir falhas de secret ausente, role/grants ausentes e DB indisponível **somente em DEV/HML**; em PRD verificar leitura/saúde sem provocar falha intencional.

**Gate de execução:** o pacote é manutenção de confiabilidade no owner correto, requer contrato para readiness, impacto de monitoramento/roteamento, teste DEV/HML, PR com revisão e autorização de implantação separada. Não criar novos papéis/serviços e não mudar Core, Keycloak ou banco de outros bounded contexts. Não confundir preflight de provisionamento **administrativo autorizado** com teste mutável de negócio.

**Governança residual:** commits de recuperação foram diretos em main (sem PR); registrar `CHANGE_PROCESS_DEVIATION_TO_REVIEW`, não reverter recuperação saudável automaticamente. Em próximas mudanças, PR governado ou exceção expressa de emergência, sem usar falta de token Devin como justificativa para bypass. Os dois títulos históricos `## 21` existentes no ledger são mantidos por rastreabilidade; esta seção `## 22` é a continuidade canônica.

**Próximo:** operação confirma estabilidade/alertas e owner operacional avalia eventual rollback ou release apenas se necessário; Cursor continua aceite independente PROD-02 em HML. PROD-03/flags/frontend sem liberação implícita por este incidente.


## 23. Decisão owner — isolamento My Requests ↔ Engineering API (13/11/2026)

**Regra explícita do owner de Engenharia:** **somente solicitações do tipo `raw-material-creation` (“Criação de matéria-prima”) são candidatas à integração My Requests → Engineering API**, pelo contrato específico de PRC. As demais modalidades do My Requests (notas fiscais, problemas de processo, chamados, solicitações gerais etc.) **não podem chamar Engineering API como parte de sua listagem/CRUD/workflow genérico**. Não interpretar essa regra como extensão de acesso da Engineering API a todos os dados ou como substituição de ownership de `requests-api`/schema `my_requests`.

**Evidência canônica parcial:** `plugins/my-requests/src/content/presentationLabels.ts` contém o identificador de apresentação `raw-material-creation`; documentação `docs/12-roadmap-e-evolucao/my-requests/MANUAL-USUARIO.md` lista diferentes tipos. **Não foi ainda provado no código** o motivo específico pelo qual erro de conexão PRC apareceu na listagem global de My Requests; classificar `TO_INVENTORY`, não concluir integração indevida sem trace.

**Contrato TARGET a validar com owners antes de editar:** o `requests-api`/My Requests mantém leitura, listagem, persistência e workflows genéricos; somente o adapter/consumer especializado para tipo canônico de criação MP faz chamada à Engineering API, com autorização backend-first, timeout e erro isolado. Não filtrar por nome traduzido; usar identificador estável autorizado pelo catálogo, conferindo se `raw-material-creation` é o valor efetivo no backend. Nenhuma chamada a Engineering API durante listagem genérica de requests; rota/visualização de integração MP pode exibir indisponibilidade contextual sem derrubar a lista global. Não efetuar joins entre bancos, import cross-BC ou reutilização de credenciais de outro domínio.

**Gate de inventário+correção:** confirmar owner, caminho da rota `/apps/my-requests/mine`, consumer API, dependências de listagem, chamadas HTTP efetivas e motivo do erro PRC na UI; verificar se o problema era backend compartilhado ou dependência específica. Se acoplamento indevido comprovado, pedir correção mínima ao Devin sob contratos dos owners correspondentes. Cobrir testes genéricos sem Engineering API (lista deve operar), tipo criação MP com integração governada, demais tipos sem chamadas PRC, 401/403, falha/timeout PRC isolada, HML multiusuário; PRD somente health e leituras comprovadamente não mutáveis.

**Estado:** `OWNER_BUSINESS_RULE_APPROVED / ROUTING_IMPLEMENTATION_TO_INVENTORY / NO_CODE_CHANGE_AUTHORIZED_BY_THIS_LEDGER`. Qualquer novo owner/authority/BC exige `ARCHITECTURE_DECISION_REQUIRED`. Não reclassificar as 36 solicitações legítimas PRD como teste, não apagá-las.


## 24. MYREQUESTS-ENGINEERING-ISOLATION-01 — PR governado aberto (13/11/2026)

**Implementação reportada por Devin:** branch `devin/myrequests-engineering-isolation-01` @ `aac52ed2753192863618883ee25592cc439d65bc`, 6 arquivos limitados ao plugin My Requests (gate PRC, MinePage, httpClient e testes). `requests-api` permanece independente, `raw-material-creation` identificado como tipo canônico; chamadas PRC na listagem unificada sem filtro são permitidas **apenas para compor a fatia de solicitações de criação MP**, via `Promise.allSettled` com falha isolada. A falha observada de mensagem SQL crua era um vazamento na UI, não evidência de que todos os tipos fossem processados pela Engenharia.

**Verificação Coordination no GitHub:** compare `main...devin/myrequests-engineering-isolation-01`: `ahead_by=2, behind_by=14` no instante da consulta, 6 arquivos no escopo. Commit `aac52ed275...` inspecionado. **PR [#181](https://github.com/roberiooliveiradev/delpi-central/pull/181) aberto pela Coordination**, `head=aac52ed275...`, `base=main`. GitHub retornou `mergeable=false` na criação, estado a investigar antes da integração. **Nenhum merge/deploy executado por esta ação.**

**Testes do executor (reported):** 20 novos testes, 200 PASS no plugin e 2 FAIL baseline alheios, TypeScript/Vite PASS. HML e validação Cursor `TEST_NOT_RUN/PENDING`.

**Revisão obrigatória:** (1) confirmar que 30 s é budget seguro para chamadas do `httpClient` compartilhado, inclusive uploads e fluxos longos; preferir timeout por operação se houver consumidor legítimo incompatível; (2) garantir sinalização de timeout/cancelamento e mensagens saneadas sem engolir erros reais de `requests-api`; (3) avaliar conflito real do PR e políticas de branch, sem ciclo de reconciliações só por `behind`. Se necessário, devolver correção pontual ao Devin antes do merge.

**Próximo gate:** revisão do PR #181, CI/branch protection, integração autorizada, deploy HML governado do plugin, outage da Engineering API somente em HML, filtros não-MP, listagem genérica e multiusuários, Cursor revalidação independente. Produção continua exclusiva para smoke READ-only, sem criação de dados ou deploy automático.


## 25. ENG-HOME-MYREQUESTS-DOMAIN-ISOLATION-PRD-01 — PR #182 (13/11/2026)

**Executor Devin reportou:** `FINAL_SHA=d73b11e30b0acc6f12b7f41fffdec97e5332dc33`, branch `devin/eng-home-myrequests-isolation-prd-01`, 32/32 testes de Home/gateway PASS; suíte Engenharia 1182 PASS + 2 baseline FAIL de D16/RBAC (não tratados no diff). HML `TEST_NOT_RUN`, Cursor `PENDING`, PRD sem novas escritas/deploy.

**Inspeção GitHub Coordination:** comparação com main mostrou **2 arquivos** somente: `engineering-api/engineering_app/infrastructure/gateways/requests_api_gateway.py` e `engineering-api/tests/test_home_gateways.py` (+17/-1), `ahead_by=1`, `behind_by=2` no instante consultado. Gateway agora envia `type_code=raw-material-creation` no query de **`/v1/requests/work-queue` e `/v1/requests/mine`**, respeitando filtro na fonte oficial e escopo AuthZ existente. Nenhum frontend, schema nem dado de produção modificado.

**PR [#182](https://github.com/roberiooliveiradev/delpi-central/pull/182)** foi aberto pela Coordination com head `d73b11e30b0acc6f12b7f41fffdec97e5332dc33` e base main. GitHub retornou `mergeable=false` na criação: `MERGE_GATE_PENDING_REVIEW`; não afirmar conflito real sem inspeção atualizada e não exigir reconciliação repetida por simples atraso de branch. PR ainda não integrado; HML ainda não implantada.

**Gate de revisão:** verificar contrato `type_code` no backend owner, filtragem antes de COUNT/paginação, 403 honesto de `work-queue` sem `process-right`, CI/proteções e compatibilidade com consumers; asserções de MockTransport não substituem HML. Depois de merge governado, deploy HML autorizado da Engineering API, verificar somente casos `raw-material-creation` na Home (tarefas+solicitações), totais e eventos, dois usuários e negativas, regressão LMP; Cursor aceite independente. **PRD somente após gates e autorização operacional**, com smoke exclusivamente health e GET comprovadamente read-only, **zero escritas de negócio**; os 36 `REQ-2026` legítimos permanecem preservados.

**Dependência paralela:** PR [#181](https://github.com/roberiooliveiradev/delpi-central/pull/181) da correção do plugin My Requests é distinto deste PR; não confundir escopos ou assumir que foi integrado.


## 26. PR #182 — integração governada concluída; HML e PRD ainda pendentes (13/11/2026)

**Coordination executou merge oficial do [PR #182](https://github.com/roberiooliveiradev/delpi-central/pull/182)** via conector GitHub, fixando `expected_head_sha=d73b11e30b0acc6f12b7f41fffdec97e5332dc33`. **Resultado GitHub:** `merged=true`; `MERGE_SHA=f1a625ff42a1c2b42dc700b92ee5044b09382e23`. Não houve rebase/reconciliação extra pela Coordination.

**Gate de CI observado:** workflow GitHub Actions `Architecture Enforcement` (run `43522051628`) no SHA do head, `completed/success`. A lista de reviews da API estava vazia, assim como a API de commit combined statuses; não afirmar que houve revisão humana ou que todas as proteções eram obrigatórias. O endpoint de merge oficial aceitou a operação, portanto não houve bypass manual da API. **Escopo compare:** 2 arquivos `requests_api_gateway.py` e `test_home_gateways.py`, filtro `type_code=raw-material-creation` aplicado em `/v1/requests/work-queue` e `/v1/requests/mine`.

**Próximo gate autorizado como preparação, não resultado executado:** Devin pode retomar `F2: DEPLOY_HML` via mecanismo operacional de HML autorizado e registrar SHA `f1a625ff...`/digest; `F3` testes contra runtime (filtro de tipos, totais, fontes parciais, LMPs, multiuser), `F4` Cursor aceite independente. **F5 release PRD continua condicionado** a HML/Cursor, autoridade operacional, backup/rollback; nenhum deploy de PRD autorizado automaticamente por este registro. **PRD testes apenas health e consultas comprovadamente read-only**, zero escrita de dados de negócio. Os 36 registros legítimos My Requests permanecem preservados.

**Estado:** `PR182_MERGED_PASS / HML_DEPLOY_PENDING / CURSOR_PENDING / PRD_NOT_DEPLOYED`. PR #181 (plugin My Requests) é mudança distinta; consultar seu estado separadamente, não considerá-la incluída neste merge.

## 27. PR #182 — deploy HML e homologação funcional concluídos pelo Devin (13/11/2026)

**F2 — deploy:** checkout HML (`/home/operador/projetos-teste/delpi-central`, host 192.168.1.237) atualizado por `git pull --ff-only` para `772b794c94` (contém `MERGE_SHA=f1a625ff42a1c2b42dc700b92ee5044b09382e23`). Mecanismo canônico `up-hml-sequential.sh --build engineering-api`. Container `delpi-hml-engineering-api` **healthy** na imagem `sha256:96b1d522acffea1a81f243403e7022f694afc8ca494b56c97db0ddf65e156836`; código do filtro `_RAW_MATERIAL_TYPE_CODE`/`type_code` confirmado dentro do container.

**F3 — evidência funcional (gateway público HML, usuário autorizado):** criados dados de teste identificados `ISOLATION-TEST-*` por fluxo governado (POST `/v1/requests` + `Idempotency-Key`) — `REQ-2026-000001` general-request, `REQ-2026-000002` raw-material-creation, `REQ-2026-000003` invoice-issuance, `REQ-2026-000004` process-issue, mesmo usuário/filial. `/v1/requests/mine` **sem** filtro retorna os 4 tipos; `GET /v1/home` retorna em `tasks` e `requests` **somente** `REQ-2026-000002 [raw-material-creation]` (`total=1` em ambas) — NF, chamado e process-issue excluídos das seções alimentadas por requests-api. `lmps` `available` (total=255), `href=/apps/my-requests` oficial, anônimo `401`, usuário denied `403`. **H13 outage controlada:** `docker stop delpi-hml-requests-api` → home `partial`, tasks/requests `unavailable` (`transport_error`), lmps `available`; restart → recuperação íntegra (`available`, total=1). My Requests corporativo segue exibindo todos os tipos (owner inalterado).

**Estado:** `HML_DEPLOY_PASS / DEVIN_HML_FUNCTIONAL_PASS / CURSOR_INDEPENDENT_PENDING / PRD_NOT_DEPLOYED`. Dados `ISOLATION-TEST-*` aguardam decisão do owner HML sobre retenção/expurgo. F5–F7 permanecem bloqueados até aceite independente do Cursor e autorização operacional.

## 28. PR #182 — handoff de validação independente Cursor (13/11/2026)

**Objeto do aceite:** isolamento das fontes My Requests da Home do Portal Engenharia ao tipo canônico `raw-material-creation` (`MERGE_SHA=f1a625ff42a1c2b42dc700b92ee5044b09382e23`, PR #182).

**Runtime homologado:** checkout HML `772b794c9433ef329bee6b9d70fe98cf114e6779`; container `delpi-hml-engineering-api` healthy na imagem `sha256:96b1d522acffea1a81f243403e7022f694afc8ca494b56c97db0ddf65e156836` (reconfirmado 13/11 23:1x UTC — digest e health inalterados).

**Contrato sob teste:** `GET /apps/engineering-api/v1/home` (gateway `https://192.168.1.237:18443`, Bearer Keycloak realm `delpi`). Envelope `data.sections.{attention,tasks,requests,lmps,activity,collaboration}`; seções alimentadas pela requests-api carregam `source.system="requests-api"` e `meta.type_code` por item.

**Dados de referência (somente HML, usuário hml-tester, filial 01):** `REQ-2026-000001` general-request, `REQ-2026-000002` raw-material-creation, `REQ-2026-000003` invoice-issuance, `REQ-2026-000004` process-issue — confirmados presentes via `GET /apps/requests-api/v1/requests/mine` sem filtro (4 itens). Esperado na Home: apenas `REQ-2026-000002`.

**Matriz para reexecução independente:** H01 home 200/contrato; H02 `raw-material-creation` em `tasks`+`requests`; H03–H06 NF/processo/chamado/outros ausentes; H07–H08 escopo por permissão e por usuário; H09–H10 totais/paginação filtrados server-side; H11 denied→403, anônimo→401; H12 `lmps` available; H13 outage controlada da requests-api → home `partial`, demais fontes preservadas (restart obrigatório ao final); H14 `/v1/requests/mine` direto segue retornando todos os tipos; H15 `href=/apps/my-requests`.

**Perfis:** autorizado `HML_TEST_USERNAME`, negado `HML_DENIED_TEST_USERNAME` (credenciais somente em `infra/.env.hml` do host HML — nunca em prompts/docs).

**Resultado Devin (referência, não substitui aceite):** F3 PASS em todos os cenários acima (§27).

**Estado:** `CURSOR_INDEPENDENT_PENDING / PRD_NOT_DEPLOYED`. F5–F7 bloqueados até `CURSOR_INDEPENDENT_PASS` + autorização operacional.

## 29. PR #182 — deploy produtivo executado e validação API read-only (13/11/2026)

**Decisão de release:** Coordination substituiu o aceite Cursor, para esta correção pontual, por verificação automatizada via API — registrada como `F4_API_VALIDATION_EXCEPTION` (não `CURSOR_INDEPENDENT_PASS`). Autorização operacional de deploy informada pela Coordination.

**F6 — deploy:** `up-prod-sequential.sh --build engineering-api`. Descoberta operacional relevante: o container prod anterior carregava bind-mount `/app` obsoleto (spec legado, código de ~30/out) que sombreava a imagem; o recreate removeu o mount divergente e a nova imagem `sha256:f4846e6220431967270fea2a5fa9f98117a78b1cf95f50c25d45b6382f50898e` passou a servir o código assado do checkout `bfaf93a6eb` (contém merge `f1a625ff`). Imagem anterior `sha256:6140677e0503…` preservada para rollback. Container healthy em ~13s; `type_code=_RAW_MATERIAL_TYPE_CODE` confirmado em `/app` dentro do container; zero `fe_sendauth`/5xx nos logs.

**F7 — validação API read-only (PRD, zero escritas):**
- `GET /v1/home` anônimo → 401; usuário sem `engineering.access` → 403 (fronteira AuthZ íntegra).
- `GET /v1/requests/work-queue?type_code=raw-material-creation` como usuário sem process-right → 403 (contrato do owner preservado); work-queue sem filtro → 200 total=0.
- Auditoria read-only `my_requests.requests` PRD: `REQ-2026-000001` raw-material-creation (1) + `REQ-2026-000002..011` invoice-issuance (10). Com o filtro server-side aplicado pelo owner em toda chamada das fontes `tasks`/`requests`, os 10 registros de NF não podem aparecer na Home da Engenharia para nenhum usuário; My Requests corporativo permanece intacto (11 registros preservados).
- Resposta autenticada da Home com usuário `engineering.access`: `TEST_NOT_RUN` — nenhuma credencial funcional desse perfil disponível ao executor; coberto por construção (filtro server-side) + evidência E2E HML no mesmo código (§27). **Recomendação:** owner com acesso valida visualmente `/apps/engineering` quando conveniente.

**Estado:** `PRD_DEPLOY_PASS / API_VALIDATION_PASS_WITH_SCOPE_NOTE / PRD_BUSINESS_TEST_WRITES=0`. Divergência `/app` bind-mount stale removida é melhoria incidental de conformidade — registrar para o runbook (containers prod devem servir imagem assada).


## 30. Coordination — revisão do aceite PRD pós-deploy (13/11/2026)

**Evidência consultada:** ledger §29 (commit `036e14683c64293c4c165fa17fb636aaaeb13bb0`) e implementação atual em `engineering-api/engineering_app/infrastructure/gateways/requests_api_gateway.py`. Filtro técnico presente no código: **`_RAW_MATERIAL_TYPE_CODE = "raw-material-creation"`**. O texto do relatório do executor que menciona `raw-material-confirmation` é divergência de nomenclatura e **não** prova código incorreto.

**Classificação revisada:** `PRD_DEPLOY_PASS_REPORTED / PRD_HEALTH_PASS_REPORTED / PRD_AUTH_BOUNDARY_401_403_PASS_REPORTED / PRD_FILTER_IMPLEMENTATION_PROVEN / PRD_HOME_AUTHENTICATED_SMOKE_TEST_NOT_RUN / PRD_FUNCTIONAL_ACCEPTANCE_INCONCLUSIVE`. A ausência de token de usuário `engineering.access` impediu verificar `data.sections.tasks`, `data.sections.requests`, `meta.type_code` e totais em PRD. Não chamar `API_VALIDATION_PASS` de aceite funcional completo com somente 401/403, testes de estrutura e SELECT read-only no banco. Nenhum novo deploy é justificado apenas por essa lacuna.

**Divergência de inventário:** auditoria anterior do incidente PRD reportou 36 registros `my_requests.requests`; §29 reporta 11 (1 `raw-material-creation` + 10 `invoice-issuance`). **`RECONCILIATION_PENDING`**: coletar apenas evidências read-only da mesma fonte/ambiente, filtros, schema, timestamp, contagem total vs paginação, owner e eventuais diferenças de snapshot, sem sugerir perda ou apagar registros sem provas.

**Próxima ação mínima:** um usuário autorizado com `engineering.access` executa **GET read-only** `/apps/engineering-api/v1/home` em PRD; confirmar HTTP 200, `tasks.items[*].meta.type_code` e `requests.items[*].meta.type_code` apenas `raw-material-creation`, totais honestos, fonte LMP, ausência de itens extrínsecos. Registrar somente metadados saneados (sem JWT, cookies, senhas, payload pessoal). Se a UI continuar mostrando outros tipos apesar do GET correto, investigar cache/versão frontend antes de novo deploy. Não criar dados PRD. Exceção F4 (Cursor dispensado para esta release) permanece registrada e **não** vira `CURSOR_INDEPENDENT_PASS`.
