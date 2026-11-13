# PRC-TRACK — G1 proposta de ratificação de contratos e fronteiras

> **Data:** 2026-11-13 · **Status:** `PROPOSED_FOR_COORDINATION / ARCHITECTURE_DECISION_REQUIRED`. **Não ratificado. Sem autorização de código, schema ou deploy.**
>
> Deriva de [decisões do PO](./PRC-TRACK-G1-PO-DECISIONS-2026-11-13.md) (inclusive emenda final RESOLVED vs REMOVED), [pacote de implementação](./PRC-TRACKED-PRODUCTS-IMPLEMENTATION-PACKAGE-PLAN.md) e [G0](./PRC-TRACK-G0-INVENTORY-G1-COORDINATION-DECISION-PACKET.md). Este documento é uma **proposta técnica a submeter à Coordination**, não uma nova decisão de produto.

## 1. Regra funcional imutável recebida do PO

- **Owner desejado:** Engineering API / PRC; identidade existente por `official_source + official_product_code`, sem diferenciação por filial no domínio informado pelo PO (provar invariantes no contrato).
- **Cobertura:** acompanhar campos registrados pela Engineering API (catálogo de ficha PRC), não todo o catálogo TOTVS; provenance e verificação precisam ser explicitadas.
- **Versões:** V1 no primeiro estado técnico efetivamente acompanhado, Vn+1 **somente se existir diferença técnica real**; conclusão PRC verificada sem diferença fica auditada e **não gera revisão**.
- **Flags:** uma identidade lógica por produto+alvo. Propagação apenas de flag OPEN; **resolvida enquanto V4 vigente: aparece RESOLVED em V4, não em V5+**; **removida enquanto V4 vigente: desaparece na própria V4 e V5+**; V3 original mantém OPEN. Ação não gera nova versão técnica.
- **Leitura e diff:** Engineering API é autoridade da API de acompanhamento e computa comparação Vx×Vy. Portal Engenharia compõe UI usando somente Plugin UI para componentes reutilizáveis.
- **Gate:** Plugin UI aceita/testado e rotas do novo escopo **funcionais e validadas em homologação** antes da implementação de novas páginas U1–U3; QA browser das novas páginas depois da implementação e antes do release.

## 2. Quadro de decisão para a Coordination (não presumir aceite)

| ID | Proposta técnica | Owner da decisão | Gate |
|---|---|---|---|
| CR-01 | Manter Engineering API/PRC como owner; records/revisions da V012; chave source+code, sem filial após evidência | Coordination + Engineering Domain Owner | PROPOSED |
| CR-02 | Snapshot **consolidado dos campos PRC acompanhados** com schema versionado, `valueOrigin`, coverage e evidence; delta separado | Engineering API owner + Coordination | PROPOSED |
| CR-03 | Sem mudança técnica, concluir pedido e registrar verification/ledger **sem inserir revisão**; operação transacional/idempotente | Engineering API owner + Coordination | PROPOSED |
| CR-04 | Identidade única de flag `recordId+targetKey` e eventos com versão vigente/contexto, sem clones entre versões | Engineering API owner + Coordination | PROPOSED |
| CR-05 | Projeção temporal: OPEN até encerramento; RESOLVED no contexto Vn da resolução; REMOVED já ausente nesse Vn; ambos ausentes em Vn+1 | Engineering API owner + Coordination | PROPOSED |
| CR-06 | API para lista paginada, ficha/snapshot, flags por produto e corte, ações governadas, diff servidor | Engineering API owner/Core Authorization | PROPOSED |
| CR-07 | HML auth positivo/negativo e contract tests completos antes de frontend; Plugin UI remote e consumer tests aceitos | QA/Engineering + Coordination | PROPOSED |

### Decisões de detalhe **não autorizadas automaticamente**

1. Se um UPDATE parcial não contém todos os campos PRC, o snapshot consolidado deve usar apenas o último estado previamente confirmado com origem/cobertura válida + alterações confirmadas, sem supor que dados omitidos permanecem oficiais. O owner deve definir os critérios de merge e o handling de dados ausentes.
2. A primeira conclusão verificada sem diferenças em um produto **ainda não acompanhado**: é preciso decidir se estabelece V1 como baseline inicial ou permanece apenas registro de solicitação sem versão. A regra de no-op por si só não decide a existência de baseline.
3. A flag resolvida e removida **na mesma Vn** pode passar por múltiplas transições; desempate por ordem de evento e semântica da projeção precisam ser definidos, com estados históricos auditáveis.
4. Uma flag pode ser reaberta. Se reaberta em V5, como o histórico da mesma identidade e a projeção V5/V6 são exibidos? Exige definição explícita para não atribuir OPEN a V4 retroativamente.
5. Se uma flag é removida, a persistência usa soft-delete auditável, mas **a UI deve tratá-la como ausente em Vn da remoção**. Recuperação/restauração precisa regra específica; não fazer backfill inferido.
6. F5/URL: corte de publicação de V4 ≠ visualização de estados de flags modificados enquanto V4 era a versão vigente. O backend deve expor **visão da versão técnica e projeção dos eventos daquela vigência**, com corte temporal inequívoco. Não confundir revisão técnica imutável com projeção viva mutável enquanto V4 é a atual.

## 3. Proposta de contratos B1/B2/B3 (schema ilustrativo, não implementado)

### B1 — Escrita PRC confirmada e histórico técnico

`verify-and-complete` (existente) continua exigindo verificação `matched`, autorização e idempotência. Em conclusão:
1. consultar/validar origem oficial por caminhos acordados;
2. construir **estado consolidado de campos PRC** com `schemaVersion`, `coverage`, `fieldOrigins`, `supplierLinks` e `verificationId`;
3. comparar com última versão consolidada usando normalização do domínio (unidade, vazio vs ausente, fornecedor code+store, ordem);
4. se diferença real: salvar `revisionNumber=previous+1`, prova/ledger/solicitação em transação;
5. se nenhuma diferença e registro já tem snapshot: concluir e auditar `noTechnicalChange=true`, apontando para registro/revisão vigente, **sem criar revisão**;
6. se primeira conclusão sem baseline: **bloquear decisão técnica de criar V1** até CR-03 fixar política.
 
Requisitos: revisão antiga imutável, migração mínima backward-compatible, sem captura de campos fora da Engineering API, nenhum draft tratado como prova TOTVS sem `coverage`.

### B2 — Registro lógico de flag e projeção

Chave lógica proposta: `recordId + targetKey`; `targetKey` do catálogo FIELD ou SUPPLIER_LINK(`supplierCode`, `store`, `attribute`). Um único registro OPEN por alvo; eventos possuem `flagId`, `recordId`, `action` (`OPEN|RESOLVE|REMOVE|REOPEN`), `occurredAt`, `actor`, `revisionContext` e `requestId?` (proveniência, quando aplicável), `eventSequence`, `expectedVersion` e correlationId.

**Projeção de apresentação (proposta para o contrato):**

| Contexto | Evento | Estado visível na ficha |
|---|---|---|
| V3 | CREATE/OPEN | OPEN, vermelha |
| V4 | Sem encerramento | OPEN, vermelha |
| V4 | RESOLVE | **RESOLVED, verde, permanece visível na V4** |
| V4 | REMOVE | **ausente imediatamente na V4** |
| V5 e posteriores | Último encerramento RESOLVE/REMOVE ocorrido em V4 sem reabertura | **ausente** |
| V3 histórico | RESOLVE/REMOVE posterior (V4) | **OPEN** na V3, sem reescrita |

O estado técnico de V4 **não é modificado** por eventos de flags. Se V4 for a revisão atual, a projeção V4 reage imediatamente ao evento; ao publicar V5, RESOLVED de V4 não se propaga. O histórico de auditoria pode mostrar o evento independentemente de a bandeira aparecer na ficha.

**Design gate:** as rotas D16 hoje trabalham com `requestId` e unicidade OPEN por solicitação. Definir migration e coexistência do modelo legado, sem novos owner/BC ou acesso a banco de outros módulos, com impacto em consumers e grants documentado.

### B3 — API e diff

**Paths propostos, não confirmados:**
- `GET /v1/product-registration/technical-records?page&pageSize&search&flagState&sort` → lista somente autorizada; `{items,total,page,pageSize}`; código, descrição, Vn, OPEN atuais e última evolução com mudança.
- `GET /v1/product-registration/technical-records/{recordId}` existente → ajustar DTO **compatível** para metadados/conteúdo autorizado.
- `GET /v1/product-registration/technical-records/{recordId}/revisions` e `.../{revisionNumber}` existentes → DTOs com snapshot PRC e provenance, sem afirmar cobertura total.
- `GET /v1/product-registration/technical-records/{recordId}/flags?revisionNumber=N` → projeção do contexto Vn; `mode=current` quando necessário.
- `POST/PATCH /v1/product-registration/technical-records/{recordId}/flags` e actions → AuthZ live/target, CAS e Idempotency-Key, erros 403/409/422.
- `GET /v1/product-registration/technical-records/{recordId}/comparison?from=N&to=M` → diff backend por campo e vínculo fornecedor+loja; cobertura unknown/incomparable e eventos de flags **em seção distinta**, sem atribuição causal infundada.

**Owners / segurança / observabilidade:** AuthN Keycloak, RBAC Core, autorização por objeto Engineering API fail-closed. Erros padronizados com operationId/correlationId, limites/paginação, tokens nunca em logs/prompt/UI kit, auditoria append-only, replay seguro. API de comparação não altera snapshot nem flags.

## 4. Critérios mínimos para ratificação e testes HML

| ID | Critério de verificação em HML |
|---|---|
| CR-AC01 | registros únicos por source+code; teste de identidade sem filial autorizado |
| CR-AC02 | primeira versão e UPDATE parcial com origem/coverage dos campos PRC corretos; zero falso campo oficial |
| CR-AC03 | UPDATE matched com diff gera Vn+1; matched no-op conclui sem Vn+1; replay é idempotente |
| CR-AC04 | conciliação de CAS concorrente e estados 403/409/422; sem perda de histórico |
| CR-AC05 | OPEN V3 continua V4 enquanto aberta |
| CR-AC06 | RESOLVED em V4: OPEN V3, RESOLVED V4, ausente V5 |
| CR-AC07 | REMOVED em V4: OPEN V3, ausente V4, ausente V5 |
| CR-AC08 | RESOLVE/REMOVE não cria Vn; eventos trazem revisionContext/ator/instante |
| CR-AC09 | uma OPEN por produto/alvo, fornecedor+loja+atributo, inclusive corrida |
| CR-AC10 | API lista somente dados autorizados, filtros e paginação determinísticos, sem vazamento |
| CR-AC11 | diff servidor V1×V5 somente alterações reais, campos incomparáveis destacados, fornecedores por chave |
| CR-AC12 | compatibilidade de PRC queue/detalhe, Catálogo TOTVS e My Requests; sem bypass de entitlement |
| CR-AC13 | Plugin UI commit, exports MF, testes consumers e QA visual host autorizado validados |
| CR-AC14 | rollback/feature gate testados, migration compatível, logs sem tokens, evidência de SHA |

`100% rotas funcionais` significa **todos os endpoints necessários ao escopo B1–B3 cobertos por testes de contrato e caminhos positivo/negativo em HML**, não suposta cobertura de código de 100%. E2E visual do novo frontend ocorre após U1–U3 e antes do deploy.

## 5. Encaminhamento

Coordination deve registrar por CR-01…CR-07: `APPROVED|REVISE|REJECT`, rationale, owner, consumer, interface/DTO, AuthN/AuthZ, invariantes, migration, rollback, testes, versionamento e SHA de evidência. **Sem ratificação: `BLOCKED` para mutações de esquema e desenvolvimento B1/B2/B3.**

Após ratificação: produzir primeiro contrato B1 com RQ/AC e prompt de implementação bounded, depois B2, B3, validação HML e frontend. O relatório do executor da migração Plugin UI continua `REPORTED` até commit/QA confirmados.

**Nenhuma confirmação de runtime, ratificação, alteração de código ou deploy neste documento.**

## 6. Resultado da deliberação CR-02 — PO aprovou ficha consolidada (13/11/2026)

**Escolha:** `A — Ficha consolidada por versão` · **Comentário:** sem comentário · **Estado:** `PO_APPROVED / COORDINATION_RATIFICATION_PENDING`.

A orientação do PO resolve a alternativa *estado consolidado vs somente delta*: **cada revisão Vn deve representar a ficha consolidada dos campos acompanhados pela Engineering API (catálogo PRC)**; a lista de mudanças da solicitação permanece separada e não substitui o snapshot. Em UPDATE parcial, preservar campos da última base confirmada válida sob contrato de cobertura e combinar as alterações efetivamente confirmadas, sem inferir valores não observados. Toda versão expõe `schemaVersion`, cobertura/proveniência e vínculos identificados por fornecedor+loja. Não confundir `draft_data` com observação oficial nem ampliar para todo o TOTVS.

**Requisitos para contrato CR-02:** definir matriz de campos `present/unknown/not_applicable`, origem do valor, null/omissão/remoção, merge de fornecedores, evolução de schema, evidência de verificação, snapshots legados, atomicidade da conclusão e comportamento de falha. A comparação V1×V5 é entre snapshots consolidados; teste matched-no-op não cria Vn. Não reescrever histórico por mudanças posteriores.

**Efeito sobre questões abertas:** a dúvida “consolidado ou delta?” está **DECIDIDA PELO PO**. Permanecem **PENDING_COORDINATION** (a) critérios concretos de origem/verificação dos dados, (b) fórmula de merge e cobertura de UPDATE parcial, (c) primeira V1 quando não existe baseline de acompanhamento, e (d) migrations/compatibilidade e AuthZ.

**Estado de execução:** `TEST_NOT_RUN`; nenhum código ou schema foi alterado por esta decisão.

## 7. Emenda CR-03 — baseline inicial V1 independente de diff (PO, 13/11/2026)

**PO escolheu A, sem comentário.** Regra funcional a ratificar: na primeira conclusão PRC validada de um produto ainda não acompanhado, **materializar V1 como baseline da ficha consolidada CR-02**, mesmo se não houver mudança técnica. A partir daí, somente diff técnico real com último snapshot gera V2...Vn; no-op posterior conclui e registra evidence/ledger sem versão.

**Algoritmo conceitual proposto (não código):**
- `verified != matched` → não criar baseline/revisão.
- `record não existe ou não tem revisão confirmada` e `matched` → construir snapshot consolidado, validar cobertura mínima contratada, persistir `V1` com evento `baseline_initial`, mesmo `diff=[]`.
- `record já tem Vn`, `matched`, `canonicalDiff(Vn,current)=[]` → concluir caso e vincular `recordId/currentRevision` com `noTechnicalChange=true`; não incrementar.
- `record já tem Vn`, `matched`, `canonicalDiff != []` → criar Vn+1 com evidência e vínculo ao request.
- Em todos os caminhos: transação/locking/CAS, idempotência, AuthZ e proveniência; não assumir que V1 prova criação ERP.

**A decisão elimina a dúvida anterior** “primeira V1 com no-op fica sem baseline?”: **deve criar V1**. Continuam pendentes da Engineering API/Coordination: campos/proveniência e cobertura mínima do baseline, semântica de UPDATE parcial e null/ausente, no-op canônico de fornecedores, migration backward-compatible, erro/retry/concurrency e contrato de conclusão com revisão inalterada. **Não modificar documentação legada silenciosamente**: esta emenda tem precedência.

**Novos cenários HML:** primeira UPDATE matched/no-diff gera V1; primeira CREATE matched gera V1 sem atribuir prova ERP de criação além do contrato oficial; segunda no-op mantém V1; diff posterior gera V2; unmatched/forbidden não gera V1; replay e duas conclusões concorrentes não duplicam revisões; listagem mostra V1 e última evolução baseline.

**Estado:** `PO_APPROVED / COORDINATION_RATIFICATION_PENDING / TEST_NOT_RUN`. Sem autorização de implementação.
