# GLPI #1353 — Plano mestre de execução, testes, correções e aceite (Devin)

> **Status:** PLANNED — plano completo, execução condicionada a gates e autorizações. Data 2026-10-29.
> **Baseline remoto observado ao redigir:** `main` SHA `2ff0ae240bdb1c342afaefe3d54007d81d1ab13e`. Não é baseline do workspace Devin; HEAD/status são obrigatórios a cada etapa.
> **Objetivo aprovado desta tarefa:** documentação de plano ponta a ponta. A criação deste arquivo NÃO autoriza implementação não homologada, deploy, alterações no Protheus ou promoção de página.
> **Referências canônicas complementares:** [Fluxo D1](./GLPI-1353-PRODUCTION-CONSUMPTION-AUDIT-FLOW-20261029.md), [D2.1 regras](./GLPI-1353-CONSUMPTION-AUDIT-BUSINESS-RULES-D2.md), [D2.2 contratos](./GLPI-1353-CONSUMPTION-AUDIT-CONTRACTS-D2.md), [plano anterior](./GLPI-1353-CONSUMPTION-AUDIT-DEVIN-EXECUTION-PLAN.md), [README](./README.md), [IMPLEMENTATION-PLAN](./IMPLEMENTATION-PLAN.md), [MATRIZ-BOUNDARIES](./MATRIZ-BOUNDARIES.md), [ADR-009](./adr/ADR-009-product-access-and-operational-data-scope.md).

## 0. Contrato operacional GPT × Devin × GitHub

Devin deve seguir a trilha do começo ao fim **dentro dos escopos autorizados**, reparando defeitos descobertos em sua etapa, reexecutando testes e preservando evidências e SHAs. **Não existe aprovação automática por passagem de fase**: decisões de PCP, Joici/Michael, Segurança e Product Owner são gates externos. Quando o gate estiver bloqueado, registrar BLOCKED/INCONCLUSIVE com próxima ação objetiva; não presumir autorização. GPT revisa cada relatório e conclui exclusivamente `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`.

Em toda etapa: READ → VERIFY → CLASSIFY → DECIDE → MINIMAL DIFF (se autorizado) → TEST → VERIFY OUTCOME → RESIDUAL SEARCH → DOCUMENT → REPORT. Não alterar testes para esconder problemas. Uma etapa = um escopo coerente e um conjunto rastreável de commits. Sem alteração de branch/ref durante inventário READ-ONLY. Respeitar worktree suja/alheia.

## 1. Authorities e ownership não negociáveis

1. `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`.
2. Regras `.cursor`: globais `development-standards-index`, `evidence-driven-execution`, `centralized-rules-first`, `clean-code-architecture-guardrails`, `english-code-identifiers`; especialistas de plan-construction, plan-execution, test-and-commit, SQL Protheus, contratos API, segurança/S2S, qualidade e feature-help-sync conforme responsabilidade. Não carregar o catálogo inteiro.
3. ADRs/contratos canônicos, schema, código e testes no HEAD; docs/plano abaixo não substituem authority.
4. `api-delpi` é dona da semântica SC2/SH6/HZA/SH8/SG1/SD4/SD3, BOM histórica e cálculos. `supplies-api` permanece Flask, dona de Core-first AuthZ, composição e eventual estado próprio. `plugins/supplies` é UX, apenas BFF; Core API efetiva permissions; Keycloak identidade/credenciais.
5. JWT usuário não é permission authority; `supplies.access` para uso normal e `supplies.manage` para administração, sem implicação entre ambas. Filiais `01`/`02` são filtros fixos de dados, não permissões; `view-all` não se aplica. Backend fail-closed, sem grants por tela/endpoint/CRUD.
6. Sem import de domínio/application entre contextos; sem SQL TOTVS no BFF; sem espelhar SC2/SD3/SD4 em PG supplies; sem MFE→api-delpi; sem novo serviço por conveniência.

## 2. GOAL e limites de produto

Construir **Auditoria Inteligente de Consumo e Estoque** como capacidade **distinta** da E12 (`/supplies/safety-stock/consumption-analysis/*`: produto×período). Grão do GLPI #1353: filial × OP × operação × componente × unidade, preservando vínculos OP origem e evidência do movimento. A auditoria explica: teórico conforme BOM e referência homologadas, empenho SD4 e seu derivado, consumo SD3 classificado/líquido, apontamento/estado de operação, divergências e completude. Não confundir diferença aritmética com irregularidade, nem com falta física de estoque.

Escopo alvo faseado: producer C2 detalhe da OP → BFF detalhe → lista paginada C1 → consulta inversa C3 apenas se aprovada → UI/MFE apenas depois de autorização de página e gate E11, Help sincronizada → workflow de investigação D6 apenas depois de aprovação separada. Se o PO quiser inicialmente **somente backend**, a definição de pronto backend termina em `B6`, e a conclusão do produto inteiro permanece `PENDING` até UX/runtime.

## 3. Evidências e riscos herdados de D0/D1/P0

| Caso | Evidência existente | Risco que o teste deve impedir |
|---|---|---|
| OP `24884201006`, filial 01, produto `50226108` | SC2 planejado `0.125 MI`, `C2_QUJE=0`; SH6 apontamento `H6_QTDPROD=0.125`, tipo P; SH8 op 01 CT-23/op 02 CT-35 | SH8 não prova execução; divergência SH6/SC2 não pode ser resolvida por palpite |
| Cabo `10010030` op 01 | SG1 preliminar `646 × 0.125 = 80.75 MT`; SD4 derivado 80.75; SD3 classificada consumo 80.75 | Movimento adicional 0.64 é transferência inbound, NÃO sobreconsumo |
| Terminal `10080329` op 02 | SG1 preliminar 250 PC; SD4 250 original/250 aberta; sem baixa no recorte | Não emitir falsa falta de consumo quando execução não provada |
| `MOD216` | SB1 tipo MO/UM HR; SD3 0.233 HR | Não somar horas de MO ao consumo MP |
| Documento `220039841` | Há linha de outra OP no documento | `doc` isolado não é chave de OP |
| OP `24884201002` | SD4 `D4_OPORIG=24884201006` | Dupla contagem/atribuição indevida |
| SG1 2026-10-20..2049-12-31 | vigente na emissão do exemplo | Não usar data 'hoje' silenciosamente em OP histórica |

**P0 Devin aceito com residual pelo GPT (relatório fornecido em conversa, não prova runtime):** existem dois métodos S2S — token legado compartilhado e JWT individual client-credentials; o individual usa `DelpiS2SApiGateway` e `require_s2s_or_any_permission` com allowed_clients e scopes, mais forte, mas demanda aval Segurança/Keycloak. HZA010 está documentada como estado por operação; causalidade apontamento→baixa ainda candidata. SD3 por OP inteira carece de binding especializado para evitar N+1. SG1 aceita filtro parametrizado de vigência (`validity_filter_sql(reference_param=...)`). `allowed_tables.json` de SQL dinâmico não governa repositórios estáticos. Controles `D4_OPORIG`, netting de retorno/estorno, conversões, status SH6×SC2 e tolerâncias não estão homologados. O P0 apontou avanço externo HEAD sem diferenças nos diretórios da frente; revalidar.

## 4. Ledger RQ → AC → owner → evidência

| RQ | Acceptance Criteria | Owner de implementação | Provas necessárias |
|---|---|---|---|
| RQ-01 grão correto | AC-01 nenhuma linha mistura filial/OP/operação/componente/UM | api-delpi | SQL/query + fixture doc multi-OP e OP origem |
| RQ-02 fontes separadas | AC-02 SG1 teórico, SD4 original/open/derived e SD3 líquido classificados com source/quality | api-delpi | positivo + divergência SD3/SD4 |
| RQ-03 operação real | AC-03 SH8 cadastro ≠ execução; HZA/SH6 só conforme semântica homologada | api-delpi + PCP | case execução incerta → unknown |
| RQ-04 sem falsos alertas | AC-04 0.64 transferência, MOD216 MO e retornos não elevam consumo | api-delpi | regressões op real + irmão + negativo |
| RQ-05 histórico e origem | AC-05 BOM as-of, UM/conversão, D4_OPORIG sem dupla contagem | api-delpi | datas/OP filha/UM alternativa |
| RQ-06 AuthZ efetiva | AC-06 Core permission, branch e ownership fail-closed; manage-only sem access; spoof S2S negado | supplies-api + api-delpi | 401/403/503 e security contract |
| RQ-07 contratos HTTP | AC-07 OpenAPI/DTO consistente producer/BFF; errors, partial/inconclusive, paginação | ambos | contract tests e HTTP end-to-end |
| RQ-08 desempenho | AC-08 sem fan-out N+1; limites de consulta, timeout, custo mensurado | api-delpi + BFF | plano SQL e stress bounded, latência reportada |
| RQ-09 UX eventual | AC-09 kit-first, loading/empty/partial/error/403/404, ajuda, F5, mobile/desktop/temas/teclado | MFE (após go) | testes estruturais + smoke federado autenticado |
| RQ-10 segurança e escopo | AC-10 sem nova permission, writes ERP, mirror PG, leak de segredo ou alteração E12 | todos | residual search + diff review |
| RQ-11 governança | AC-11 evidência com HEAD/SHA, owners/aceites e gates reais | Devin + GPT | relatório a cada etapa |

## 5. GATES EXTERNOS — não inventar nem automatizar aprovação

| Gate | O que exige | Autoridade | Status inicial |
|---|---|---|---|
| G2-01 | Execução efetiva por operação e vínculo evento→baixa | PCP / owner Protheus | TO_INVENTORY |
| G2-02 | Resolver SH6 0.125 versus SC2 C2_QUJE 0, quantidades de referência | PCP / owner Protheus | TO_INVENTORY |
| G2-03 | Semântica estorno/devolução, saldo líquido e TM/CF | PCP / api-delpi | TO_INVENTORY |
| G2-04 | Data BOM histórica, substituição, UM/conversão/arredondamento | PCP / api-delpi | TO_INVENTORY |
| G2-05 | D4_OPORIG, OPs relacionadas, filtro C2_PRIOR=500 e dedup | PCP / api-delpi | TO_INVENTORY |
| G2-06 | Tolerâncias, momento de alerta, categorias/severidade | Joici / Michael | PENDING |
| G2-07 | S2S individual vs legado, scope Keycloak, schemas, policy, contratos | Segurança / owners BFF+producer | PENDING |
| G2-08 | Nomeação/posição no roadmap distinta da E12, gate E11 e autorização de página | Product Owner | PENDING |

**Stop obrigatório:** nenhum cálculo definitivo ou classificação acusatória enquanto regra essencial for PENDING. Para lacuna não resolvida permitir, somente com aprovação específica, um endpoint limitado de evidência bruta com `unknown`, não 'reconciled' conclusivo. Ausência de decisão nunca se transforma em default silencioso.

## 6. Trilha fechada por entregas e gates

### A0 — BASELINE + DRIFT CHECK (READ-ONLY em toda entrada)

- Registrar `git rev-parse HEAD`, `git status --short`, `git rev-parse origin/main`, branch, diffs e trabalho alheio. Não fazer pull/checkout/fast-forward/reset em leitura; preservar untracked.
- Revalidar sources oficiais, .cursor aplicável, README, IMPLEMENTATION-PLAN, ADR-009, documentação D1/D2, OpenAPI e código/tests HEAD; inventariar producers/consumers e versão dos contratos.
- Corrigir qualquer premissa stale somente **por decisão explícita**, nunca com mudança de código silenciosa.
- **Gate A0:** evidência HEAD/status/authority, diffs reconciliados. `EXECUTION_DRIFT` se owner/status/contrato mudar materialmente.

### A1 — D1 RESIDUAL / INVESTIGAÇÃO SEMÂNTICA (READ-ONLY)

- Reconstituir SH6/HZA010 e SH8 por OP/operação, filiais autorizadas, com SQL governado e sem PII; documentar timestamp/event IDs se efetivamente presentes. Comparar SD3 documentos e SD4; evitar correlação apenas por data ou documento.
- Investigar SH6 apontada mas C2_QUJE zero; estornos/retornos parciais, substituições, OP vinculada e família de produto, UM e quantidades; coletar casos positivo/irmão/negativo reais conforme autorização.
- Não simular causalidade automática. Solicitar validação PCP/Joici/Michael para regras pendentes e preservar respostas com fonte/proveniência.
- **Gate A1:** matriz G2-01..06 PROVEN ou explicitamente aprovada como comportamento `unknown` para fatia de evidências. Sem isso, STOP/inconclusive; não entrar no motor inferencial.

### A2 — P1 CONTRACT FREEZE + SECURITY DECISION (DOCUMENTAL)

- Definir C2 primeiro: `GET /supplies/consumption-audit/orders/{op}` no producer, `GET /consumption-audit/orders/{op}` no BFF (paths propostos). Documentar branch 01/02, OP 11 chars, operação, componente, data-base BOM, campos, tipos Decimal, timezone, status/completeness e semântica de null/zero.
- Formalizar classificação conservadora, opções `reconciled | arithmetic_difference | requires_investigation | unclassified` apenas quando apropriado; inconclusive/unknown para lacunas. Definir identidade de evidência, chave estável, reprocessamento/snapshot sem persistir dados Protheus.
- Contrato C1 lista paginada e C3 por componente somente se RQ/valor/volume justificar; limite de page, ordenação, filtros e período sem assumir qual data delimita.
- **Escolha preferida pendente:** S2S client-credentials individual (Keycloak scope dedicado, ex. `consumption-audit.read`, se aprovado); usar `DelpiS2SApiGateway` e `require_s2s_or_any_permission` somente com Security approval; nenhuma permission nova do Portal. Não aceitar token legado nessa rota quando contrato individual for escolhido.
- Definir error mapping upstream→BFF, 400/401/403/404/422/502/503/504, resource invisível, erros de Core e upstream, timeout, cache/latência, compatibilidade e projeção.
- Congelar OpenAPI/schema no owner e testes contract fixtures. Conseguir anuência PCP/Joici/Michael, Security e PO para scope autorizado.
- **Gate A2 = GATE-D2:** sem ratificação explícita permanece PENDING, S1 proibido.

### B1 — PRODUCER C2 / api-delpi (WRITE somente com GO explícito)

- Construir use-case/ports/adapters read-only no owner, com consulta por filial+OP, SH8/HZA/SH6 homologados, SG1 via filtro parametrizado, SD4 agrupado por operação, SD3 binding por OP **sem N+1**, classificação domain TOTVS, B1 tipos e OP origem.
- Não importar business rules do BFF, nem ampliar `/production/*` ou `/products/*`; nova rota focada `/supplies/consumption-audit/orders/{op}` segundo OpenAPI congelada.
- Adicionar auth S2S escolhida em A2 com validação token assinado, allowed client, scopes, audience/issuer, negativas spoof; compatibilidade com rota normal conforme contrato. Proibir write SQL/Protheus.
- Testar teoria/SD4/SD3 independentes, OPs filiais, datas/vigência, status unknown, retorno/estorno e missing records. Expor motivos de falta de completude.
- **Gate B1:** producer unit + contract + negative S2S PASS; chamada real read-only validada ou INCONCLUSIVE se indisponível; revisão GPT antes B2.

### B2 — BFF DETALHE / supplies-api Flask (após B1 PASS)

- Gateway `DelpiS2SApiGateway` para producer congelado; application service/DTO projection e Blueprint Flask; reusar políticas Core-first e tratamento envelope. Não calcular total SD3 ou SG1 no BFF.
- Fazer `supplies.access` efetivo, scope de filial 01/02 e recurso/ownership aplicável; `manage` isolada não confere acesso. Core offline = fail-closed; falsificação de caller negada no producer.
- HTTP timeout/connection error/invalid envelope mapeados com segurança; request-id, sem expor secret nem dados de outras filiais.
- Testes unit/contract da BFF (mock producer) e integração real autorizada, positivas/irmãos/negativos, erros e campos nulos.
- **Gate B2:** policy + contract + funcionamento producer↔BFF PASS; sem integração real => INCONCLUSIVE, não aceitar como E2E completo.

### B3 — C1 LISTAGEM PAGINADA (após B2; se aprovada)

- Producer lista OPs por período **após definição da data-base** e status de completude, com paginação bounded e sorting estável; BFF gateway/rota equivalente.
- Evitar fan-out OP×componente/consulta SD3 de cada item; plano SQL, cardinalidade e limites. Testar branch 01/02, zero resultados, erros, ordenação determinística e paginação de fronteira.
- **Gate B3:** testes de contrato/performance/segurança PASS.

### B4 — C3 COMPONENTE (opcional; se aprovado)

- Consulta inversa com chaves OP+operação+filial e paginação; requisitos de negócio e perf medidos antes de escrever.
- **Gate B4:** PASS ou NOT_IN_SCOPE aprovado; não bloquear B5 quando conscientemente excluído do MVP.

### B5 — INTEGRAÇÃO, RESILIÊNCIA E CORREÇÃO ATÉ VERDE (dentro da autorização backend)

- Rodar suites existentes e novas api-delpi, supplies-api, shared auth, OpenAPI schema-diff, lint/format/typecheck pertinentes. Registrar comando/ambiente/resultado e identificar flakes externos.
- Subir integração em ambiente permitido (não produção) usando configuração S2S segura. Testar requests autorizadas 01/02, token ausente/expirado/cliente inválido, granted access vs manage-only, filial inválida, outro recurso, Core indisponível, upstream offline, payload inválido, 404 e timeout.
- Fixture OP 24884201006: 80.75 consumo, 0.64 transferência, 0.233 HR MO, 250 PC empenho; não produzir alerta falso. Doc multi-OP, D4_OPORIG, BOM alterada, devolução parcial e conversão de UM como irmãos/negativos.
- **Ciclo iterativo obrigatório:** FAIL → classificar ROOT_CAUSE (code/contract/test-data/env/external) → corrigir menor diff no owner → repetir teste falho → repetir siblings e regressão completa → residual search → re-review. Não mascarar falha nem mudar expected para passar indevidamente.
- Validar objetivo original: BFF consome producer real com AuthZ, resposta audível, sem inventar saldo físico. Reportar evidence de HTTP, latência sem estimativas, SQL readonly e no N+1.
- **Gate B5:** PASS somente se todos testes executáveis e integração obrigatória passaram. Sem infraestrutura/autorização = INCONCLUSIVE, com blocker explícito.

### B6 — DOCUMENTAÇÃO, SHA E ACEITE BACKEND

- Atualizar contrato OpenAPI/schema, docs canônicas de Suprimentos, matriz de requirements e help somente quando houver feature de UI; não marcar rota PLANNED como PROVEN sem código/testes.
- Residual search por direct MFE→api-delpi, SQL TOTVS no BFF, duplicação rules/DTO, novas permissions, E12 alterada, shadow PG, secrets/logs e unauthorized paths.
- Commit(s) somente quando a execução da etapa e commit estiverem autorizados; preservar worktree alheia, registrar BASE/FINAL SHAs, git status e links para evidências.
- Produzir EXECUTION_REPORT final com cobertura RQ/AC, comandos, diffs, auth checks e postcondition. GPT decide `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`.
- **Gate BACKEND:** só fecha com contrato, authz, teste S2S real e integração; ausência do smoke integrado => INCONCLUSIVE.

### C1 — UI / MFE (opcional conforme PO; uma página por vez)

- Somente após fechamento de página em foco E11 e GATE-FEATURE exigido, autorização explícita e backend gate. Planejar rota específica sem confundir E12, kit `@delpi/plugin-ui`, CSS `.dashboard-supplies-portal`, query/deep links, filtros, detalhe OP e estados loading/empty/partial/error/403/404.
- Sincronizar Help/tooltip/manual, testes estruturais, responsividade, claro/escuro, teclado/foco e URL/F5.
- **Gate UI:** build/tests e smoke federado autenticado em runtime; sem smoke => INCONCLUSIVE. Não promover só por manifest/rota.

### C2 — Fluxo de investigação (posterior, autorização distinta)

- Se PO aprovar, persistir no PG `supplies` apenas ocorrência humana/atribuição/justificativa/resolução e auditoria do Portal; **não** armazenar snapshot canônico ERP. Modelar identidade estável de ocorrência, reanálise, optimistic locking, migrations aditivas, ownership/recursos, AuthZ e concorrência.
- APIs de POST/PATCH em supplies-api e UX correspondente, com testes de escrita/rollback e Help. Nenhuma escrita no Protheus.
- **Gate D6:** separado; não faz parte do backend mínimo.

### C3 — RELEASE / DEPLOY E ACEITE FINAL (somente mediante autorização explícita)

- Validar source SHAs e artefatos, pipeline CI, rollback e configuração S2S/Keycloak/segredos em ambiente autorizado. Deploy via fluxo oficial versionado, nunca mutação manual de container/produção. Não ativar feature sem gate de página.
- Smoke federado autenticado, role/capability, branch, erro e acesso real; monitorar falhas, logs/trace com redaction, observabilidade e rollback; registrar IDs/digests/SHAs, testes e evidências.
- **Gate FINAL:** funcionalidade somente DONE quando contract, backend, UX quando incluída, AuthZ, runtime, documentação, smoke e aceite PO comprovados. Se etapa opcional excluída, delimitar DONE_BACKEND separado de DONE_PRODUCT.

## 7. Matriz obrigatória de testes

| Eixo | Positivo | Irmão | Negativo |
|---|---|---|---|
| Dados | consumo cabo 80.75 | terminal 250 reservado; MO 0.233 HR | transferência 0.64 não conta; movimento unclassified |
| Identidade | OP 24884201006 filial 01 | OP vinculada 24884201002; mesmo doc de outra OP | OP invisível/filial inválida |
| Histórico | SG1 vigente na emissão | SG1 alterada em outra data e UM alternativa | faltando conversão = unknown |
| Operação | apontamento HZA/SH6 homologado | operação ainda em curso | SH8 cadastro sem execução; SH6≠SC2 inconclusivo |
| Estoque | SD4 original/saldo/derivado vs SD3 classificado | retorno/estorno parcial | sem contagem SB7 não afirmar falta física |
| Segurança | supplies.access Core efetiva, S2S válido | filial 02 e 01 com escopos | manage-only, JWT permission falsa, caller fake, Keycloak/Core down |
| Contratos | esquema producer/BFF | vazio/paginado/partial | payload malformado, 404, 502/503/504 |
| Resiliência | consulta curta bounded | muitos componentes/OPs | timeout, upstream offline, N+1, carga descontrolada |
| Produto | UI kit + help (quando incluída) | F5/deep link/móvel | 403/404, tema/foco e smoke federado ausente |

Cada caso deve reportar PRECONDITION, INPUT, EXPECTED, ACTUAL, TEST COMMAND, RESULT, EVIDENCE FILE/LOG REFERENCE, SHA. Sem exceção negativa por 'não ocorreu em fixture'. Teste verde isolado não prova runtime.

## 8. STOP CONDITIONS / EXECUTION_DRIFT

- Instrução/regras/código HEAD invalidarem premissa do plano; usar `EXECUTION_DRIFT`.
- PCP/Joici/Michael não homologarem fórmula/estado/tolerância: não implementar classificação que dependa disso.
- Security não aprovar S2S/client/scope: não inventar workaround com token legado ou abrir `/production/*`.
- PO não autorizar novo backend ou nova página, ou E11 gate impedir a fila: não avançar stage correspondente.
- Faltarem ambiente/credenciais seguras para smoke: `INCONCLUSIVE`, não PASS.
- Teste detectar defeito fora do owner: levantar contrato e passar ao contexto dono, sem import/bypass.
- Worktree sujo com risco de sobrescrita: parar e preservar; nenhum reset/clean automático.
- Mudança de schema/manifest/route/prod fora do allowed scope: interromper e pedir decisão.

## 9. Relatório e protocolo de ciclos de correção

Para cada etapa: TASK/STAGE; GOAL; BASE HEAD, ORIGIN MAIN, FINAL HEAD, BRANCH, GIT STATUS; STATUS `PASS|FAIL|PENDING|INCONCLUSIVE|TEST_NOT_RUN|EXECUTION_DRIFT`; FACTS PROVEN; TO_INVENTORY; OWNER; FILES INSPECTED/CHANGED; DIFF; CONTRACT IMPACT; SECURITY; TEST COMMANDS/results; RQ/AC COVERAGE; POSITIVE/SIBLING/NEGATIVE; RESIDUAL SEARCH; POSTCONDITION/OUTCOME; UNRESOLVED; SHAs; NEXT STEP.

**Se FAIL no escopo autorizado:** corrigir, testar novamente e documentar rework até atingir PASS ou STOP documentado. **Se INCONCLUSIVE por ambiente/owner externo:** não ficar em loop infinito, encerrar etapa com bloqueio e evidência; esperar autorização/owner. **Se teste não executado:** `TEST_NOT_RUN`, nunca PASS. **Se HEAD mudar:** comparar delta e rebaseline antes de seguir. GPT revisa e decide o avanço pelo gate.

## 10. DEVIN BRIEF para iniciar a trilha

**TASK:** executar A0 (rebaseline) e A1 (residual semântico READ-ONLY) e elaborar proposta A2 Contract Freeze do GLPI #1353. **Não começar B1/B2 por leitura deste plano.**
**GOAL:** fechar G2-01..08 e definir contrato C2 produtor/consumer pronto para aprovação.
**AUTHORITIES:** oficial GPT; .cursor aplicável; ADR-009; D1/D2; implementação HEAD; testes.
**OWNER:** api-delpi semântica Protheus; supplies-api BFF; Core efetivas; PCP e negócio aprovam regras; Security valida S2S.
**CURRENT_STATE:** P0 ACCEPT_WITH_RESIDUAL, D1 INCONCLUSIVE, D2 DRAFT, código consumption-audit não comprovado.
**EVIDENCE_REQUIRED:** HEAD/status, fonte por operação, estornos, CHAVE OP/origem, BOM data, grants S2S propostos, OpenAPI/DTO, plano testes, matriz de aceite.
**ALLOWED_SCOPE:** apenas leitura, investigação governada e preparação de documentação para revisão; persistência no Git de proposta documental requer autorização separada quando demandada.
**FORBIDDEN_SCOPE:** writes ERP, código produtor/BFF, Keycloak/grants, manifest/MFE, deploy, commits não autorizados, resolver lacuna por inferência.
**CONTRACTS:** C2 detalhe primeiro, C1/C3 depois, todos ainda PROPOSED. JWT permission não autoriza; Core fail-closed.
**SECURITY:** comparar S2S individual e legado, recomendar sem alterar; filiais 01/02.
**ACCEPTANCE:** relatório de A0/A1 e draft de freeze A2 com pending explicitados, testes desenhados e próximos gates.
**TESTS:** inventariar e desenhar testes; executar somente comandos seguros e permitidos nesta etapa.
**STOP_CONDITION:** authority conflict, semântica pendente que altere cálculo, S2S não homologado, scope não autorizado.
**RETURN:** formato seção 9, sem avançar B1–C3 por inferência.

## 11. Definition of Done e árvore de decisões

- `DONE_DISCOVERY`: D1 residual documentado com decisões e dados ou lacunas aceitas como unknown.
- `DONE_CONTRACT`: GATE-D2 aprovado por owners + Security e PO para escopo, OpenAPI congelado.
- `DONE_BACKEND`: B1/B2, B5/B6, contract tests, authz e smoke HTTP real PASS, sem falsos positivos da OP base; C1/C3 somente se dentro do MVP homologado.
- `DONE_PRODUCT`: DONE_BACKEND + C1 UI autorizada + Help + smoke federado autenticado + GATE-FEATURE + aceite PO.
- `DONE_INVESTIGATION_WORKFLOW`: D6 autorizado separadamente, não inferido por DONE_PRODUCT.
- Se apenas DONE_BACKEND for autorizado, registrar fim da trilha backend e os demais como NOT_IN_SCOPE, **não** declarar 'portal completo'.

### Controle de progresso para manter no relatório (não preencher PASS sem execução)

| Stage | Status inicial | Entry | Exit |
|---|---|---|---|
| A0 baseline | PENDING | acesso repo | HEAD/status/authority |
| A1 semântica | INCONCLUSIVE | D1 dado | PCP/negócio ou unknown aceito |
| A2 contract freeze | PENDING | A1 + security/PO | GATE-D2 approved |
| B1 producer | NOT_AUTHORIZED | A2 + GO | PASS producer |
| B2 BFF | NOT_AUTHORIZED | B1 PASS + GO | PASS contract/HTTP |
| B3 lista | NOT_AUTHORIZED | B2 + escopo | PASS ou NOT_IN_SCOPE |
| B4 componente | NOT_AUTHORIZED | uso aprovado | PASS ou NOT_IN_SCOPE |
| B5 integração/rework | NOT_AUTHORIZED | código autorizado | PASS ou INCONCLUSIVE |
| B6 docs/aceite backend | NOT_AUTHORIZED | B5 PASS | DONE_BACKEND |
| C1 UI | NOT_AUTHORIZED | PO + E11 gate | UI + Help + smoke |
| C2 investigação | NOT_AUTHORIZED | GO separado | GATE D6 |
| C3 deploy/release | NOT_AUTHORIZED | GO explícito | smoke e rollback comprovados |