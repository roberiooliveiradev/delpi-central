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
