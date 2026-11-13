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
