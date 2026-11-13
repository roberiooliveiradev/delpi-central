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
