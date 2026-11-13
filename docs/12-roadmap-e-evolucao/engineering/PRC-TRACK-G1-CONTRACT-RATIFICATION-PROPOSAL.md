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

## 8. Emenda CR-04 — origem e estado de confirmação de cada campo (PO, 13/11/2026)

**Decisão do PO:** opção **A — Preservar valores e identificar sua confirmação**, sem comentário. `PO_APPROVED / COORDINATION_RATIFICATION_PENDING`.

### Semântica proposta, ainda não contrato ratificado

| Categoria de origem/estado | Conteúdo | Regra de apresentação e validação |
|---|---|---|
| `official_verified` | Valor conferido via fonte oficial no contexto da verificação documentada | Exibir como verificado, com `evidenceId`/timestamp e escopo de verificação |
| `inherited_confirmed` | Valor vindo de última revisão com proveniência válida | Exibir valor e confirmação original, **não** atribuir nova verificação à solicitação atual |
| `registered_unverified` | Valor mantido pela Engineering API, sem comprovação individual suficiente | Exibir como registrado/não confirmado; não chamá-lo de oficial |
| `unknown` | Sem valor conhecido confiável ou não disponível | Exibir ausência/indisponibilidade, nunca inferir valor |
| `not_applicable` (quando houver contrato) | Campo não aplicável sob regra de domínio | Diferenciar de `unknown` e de `null` |

**Nota:** nomes de enum e DTO acima são `TARGET` e dependem de inventário de esquemas existentes, sem supor que já existam. O owner deve definir se `valueOrigin` e `verificationState` são atributos distintos (recomendado, pois origem e validação não são a mesma coisa), tipos, versão e compatibilidade. Não expor `evidence` sensível a usuários fora do escopo autorizado.

### Consequências para B1/B3

1. **CR-02:** snapshot Vn é consolidado e cobre o catálogo de campos PRC autorizado; cada valor conhecido carrega provenance, status e cobertura. UPDATE parcial mantém estado anterior com seu timestamp original, não o transforma em confirmado novamente.
2. **CR-03:** primeiro matched, mesmo sem alteração, gera V1 com coverage real e prova de conclusão; campos não conferidos individualmente permanecem assim rotulados. Não criar V1 quando conclusão falhar.
3. **ADR-05:** `canonicalTechnicalDiff` observa **valores técnicos e vínculos**, não mudanças isoladas de metadados de evidência; sem diff técnico após V1, sem Vn+1, com ledger de verificação atualizado.
4. **B3:** diff servidor Vx×Vy pode indicar `unverifiable/incomparable` quando a qualidade da cobertura impede comparação; não mostrar igualdade confirmada quando fonte é desconhecida. Provenance não cria causalidade da PRC.
5. **B2:** eventos de flags continuam separados; confirmação de campo não encerra bandeira automaticamente.

### Contrato formal ainda pendente

Requer owners explicitarem: catálogo de campos, leitura oficial, `null`/ausência/removido/desconhecido, tratamento de fonte de evidência, herança de estado sob UPDATE parcial, limites de acesso, erros de conclusão e testabilidade. A decisão do PO **não** flexibiliza a verificação `matched` exigida atualmente para conclusão, nem concede autoridade à interface ou ao modelo.

**Cenários HML a acrescentar:** campo alterado validado + campo herdado; valor registrado não conferido; ausência/unknown; primeira V1 com metadados; sem mudança técnica e evidência nova não gera V2; verificação mismatch/unverifiable permanece bloqueada; API de comparação distingue incomparabilidade.

**Estado:** `PROPOSED_FOR_COORDINATION / TEST_NOT_RUN`. Sem alteração de código ou schema.

## 9. Emenda CR-05 — merge governado de UPDATE parcial (PO, 13/11/2026)

**Decisão do PO:** opção **A — Preservar campos e fornecedores não alterados e aplicar somente mudanças explícitas**, sem comentário. `PO_APPROVED / COORDINATION_RATIFICATION_PENDING`.

### Contrato de domínio proposto para ratificação

**Input conceitual:** `previousConsolidatedSnapshot` (CR-02 + CR-04), `validatedExplicitOperations` do PRC, `verificationEvidence`, `expectedRevision` e identidade oficial do produto. **Output:** `nextConsolidatedSnapshot`, `canonicalTechnicalDiff`, `changeProvenance` e resultado de conclusão (`baseline_initial | technical_change | no_technical_change`).

| Tipo de input | Efeito requerido | Segurança/limitação |
|---|---|---|
| Campo **omitido** da operação | Preserva valor, origem, coverage e estado de confirmação da revisão anterior | Não inferir que foi reconfirmado |
| Campo com **set explícito** | Substitui somente o campo alvo, se autorizado e validado | `null`/vazio devem ter semântica definida por field spec; erro se inválido |
| Campo com **remoção explícita** | Aplica remoção somente se essa operação existir no contrato do campo e for autorizada/verificada | `remove` não equivale a atributo simplesmente não observado |
| Fornecedor **não mencionado** | Preserva vínculo e seus atributos; identidade `supplierCode + store` | Não interpretar ausência na lista delta como exclusão |
| Fornecedor com **ADD/UPDATE explícito** | Modifica apenas vínculo/atributo declarado e validado | Campos não alterados mantêm provenance; PN/catalog conforme gates oficiais |
| Fornecedor com **REMOVE explícito** | Alvo ausente no próximo snapshot apenas se a operação estiver **autorizada e suportada** pela fonte oficial | A regra de negócio não revoga gates existentes de conclusão REMOVE/SA5; se não suportado: fail-closed |

**Processamento determinístico recomendado:** validar operações e AuthZ → conferir baseline/expectedRevision (CAS) → aplicar delta à base consolidada com semântica estrita de omissão vs alteração vs remoção → confrontar operações verificáveis na fonte oficial → produzir snapshot consolidado/versionado com provenance → calcular diff técnico normalizado → materializar V1 se primeira confirmação (CR-03), Vn+1 só com diff real, ou concluir no-op e registrar auditoria. Exigir transação/idempotência e nenhuma publicação em caso de mismatch/unverifiable.

**Alterações dos contratos de API:** não presumir endpoints novos de edição; reutilizar DTOs PRC existentes quando suportam `changedPaths` e `supplierLinkChanges`, evoluindo em versão compatível após inventário. Campos opcionais ausentes não devem sofrer coerção automática a `null`. Distinguir `notProvided`, `explicitNull`, `explicitRemove`, `unknown`. Lista de fornecedores e suas alterações precisam chaves estáveis, incluindo `store`. `canonicalTechnicalDiff` é computado no backend entre estados consolidados; metadados de verificação sozinhos não criam Vn.

**Riscos que impedem codificação sem ratificação:** UPDATE parcial legado, snapshots anteriores do draft e sua cobertura, política de campo anulável, capacidade real de REMOVER fornecedor SA5 e read-back, colisão de supplier key, mudança de schema e migração não destrutiva, 409/CAS, AuthZ e testes negativos.

**HML / aceitação:** descrição modificada sem mexer em classificações/fornecedores; atributo de fornecedor atualizado mantendo demais; novo fornecedor ADD; fornecedor omitido preservado; REMOVE só quando habilitado pelo owner e oficialmente confirmável; campo omitido ≠ explicit-null; caso mismatch/403/409 não publica; primeiro V1, UPDATE com diff V2 e posterior no-op mantêm histórico/proveniência.

**Estado:** `PROPOSED_FOR_COORDINATION / TEST_NOT_RUN`. Não autoriza implementation, migration ou deploy.


## 10. Emenda CR-06 — limpeza explícita e validação por campo (PO, 13/11/2026)

**Decisão PO:** opção **A — Limpeza explícita com validação do campo**, sem comentário. `PO_APPROVED / COORDINATION_RATIFICATION_PENDING`.

### Contrato proposto, ainda sujeito a inventário e ratificação

| Intenção recebida | Operação canônica TARGET | Efeito permitido |
|---|---|---|
| Campo não presente no delta | `UNCHANGED/OMITTED` | Herdar valor e provenance da última ficha consolidada |
| Novo valor preenchido com intenção válida | `SET(value)` | Aplicar somente ao alvo explicitamente autorizado e verificado |
| Limpeza deliberada de campo opcional | `CLEAR(target)` ou equivalente | Limpar somente quando o catálogo PRC e o sistema oficial admitirem |
| `null`, `""` ou espaços sem intenção explícita | **AMBIGUOUS / validation error** | Nunca converter silenciosamente em CLEAR |
| Campo obrigatoriamente preenchido | `CLEAR` inválido | Erro de validação, nenhuma mutação de snapshot |
| Vínculo de fornecedor omitido | `UNCHANGED` | Preservar vínculo e atributos |
| Remover todo vínculo | `REMOVE_LINK(supplierCode,store)` | Fluxo distinto e sujeito a gate SA5/owner, não dedutível de CLEAR do atributo |

A forma final do DTO e seu versionamento dependem de inventário do contrato atual; **não assumir que os nomes das operações acima são implementados**. Definir nulabilidade e tipo por campo, regras de strings vazias/whitespace, compatibilidade com clients legados e erros determinísticos 400/409/422/403 conforme semântica confirmada. O valor limpo precisa registrar proveniência da solicitação/evidência de confirmação; `unknown` é um estado epistemológico diferente de `cleared`.

**Integração com CR-02 a CR-05:** o merge do UPDATE trabalha sobre snapshot consolidado; CR-03 V1 baseline não exige alteração; para V2+, somente CLEAR validado com diferença técnica efetiva produz nova Vn; metadados e flags não alteram versão. Autorização backend-first e verificação `matched` continuam gates obrigatórios. Nunca forçar API oficial a apagar dado não suportado.

**HML / contract tests:** omissão preserva, vazio ambíguo falha sem limpar, CLEAR opcional validado altera alvo e provenance, CLEAR obrigatório rejeitado, CLEAR sem permissão rejeitado, CLEAR repetido sem diferença não gera Vn, REMOVE_LINK só com contrato/gate próprio, erro de verificação e concorrência não publica versão, cliente legado não executa limpeza implícita.

**Pendente para Coordination:** matriz campo→`nullable/clearable`, desenho de DTO de operações, política de migração de payloads antigos, read-back oficial e observabilidade. `TEST_NOT_RUN`; sem implementação.


## 11. Emenda CR-07 — flags resolvidas não reabrem; reincidência usa novo ID (PO, 13/11/2026)

**PO escolheu C — Não permitir reabertura (sem comentário).** `PO_APPROVED / COORDINATION_RATIFICATION_PENDING`.

**Contrato de domínio proposto:**
- `OPEN -> RESOLVED` ou `OPEN -> REMOVED`: transições finais. **Sem `RESOLVED -> OPEN`** ou `REMOVED -> OPEN` no novo acompanhamento de produtos.
- `CREATE` após encerramento para mesmo `recordId + targetKey`: gera **novo flagId**, nova ocorrência. Estados encerrados antigos preservados; no máximo **uma OPEN simultânea** por recordId+targetKey. Implementar restrição transacional/índice parcial quando ratificados os mecanismos de persistência.
- Histórico de exibição: ocorrência #1 OPEN V3, RESOLVED V4, ausente V5+; ocorrência #2 criada V6 OPEN V6+ até seu encerramento. Não reutilizar flagId nem propagar ocorrência antiga.
- Registrar `createdWhileRevision`, `resolvedWhileRevision`, `removedWhileRevision`, timestamp, ator, requestId de origem quando aplicável, evento e correlação; sem nova versão por ação de flag. Consultas históricas exibem estado por ocorrência e vigência.
- **Contrato de erro:** reabertura não é ação permitida nos novos DTOs e `allowedActions`; tentativas diretas são rejeitadas **no backend**, sem depender de botão oculto; definir 409/422 ou equivalente na ratificação. AuthZ continua fail-closed.
- **Compatibilidade obrigatória:** código existente D16 implementa `reopen_flag` e `POST /requests/{request_id}/flags/{flag_id}/actions/reopen`. Inventariar consumidores e distinguir flags legadas por solicitação de flags novas por produto. Política de bloquear, manter para legado com escopo estrito ou deprecar exige decisão Coordination, testes, rollback e nenhuma quebra silenciosa.

**Correção de precedente:** ADR-03 “identidade única” designa **um ID por ocorrência** e limite de uma OPEN simultânea por alvo, não proibição de criar uma nova ocorrência após RESOLVED. ADR-04 permanece válida para cada ocorrência independente.

**Novos HML tests:** flag resolvida não reabre pela API do produto; ação direta HTTP não contorna; nova ocorrência mesmo target pode abrir após finalização, com outro flagId; duas novas OPEN simultâneas produzem apenas uma; estados V3/V4/V5 permanecem; rota legada tem política testada e não permite escape; audit trail, AuthZ, idempotência, sem nova Vn.

**Estado:** `PROPOSED_FOR_COORDINATION / TEST_NOT_RUN`. Nenhum código, schema, grant ou deploy alterado.


## 12. Emenda CR-08 — associação segura de flags PRC anteriores à V1 (PO, 13/11/2026)

**Decisão PO:** **A — Incorporar bandeiras OPEN com vínculo comprovado**, sem comentário. `PO_APPROVED / ARCHITECTURE_DECISION_REQUIRED / TEST_NOT_RUN`.

### Contrato proposto para ratificação (não implementado)

**Fonte:** flags existentes do domínio PRC/D16, acompanhadas de requestId, status, subject, targetKey e evidência de vínculo ao produto oficial; Engineering API exerce autoridade sobre associação. **Não é importação de dados arbitrários nem alteração automática de TOTVS**.

**Processo proposto:**
1. Construir V1 de acordo com CR-02/03/04/05/06 e verificação PRC existente; associação das flags é etapa **separada, auditável e idempotente**.
2. Selecionar somente `OPEN`, não deletadas, com correspondência documental/contratual inequívoca de `official_source+official_product_code` e FIELD/SUPPLIER_LINK com alvo ainda aplicável à V1.
3. Verificar escopo do principal e política backend de acesso à solicitação de origem e ao produto acompanhado. Falhar fechado sem autorização suficiente.
4. Se houver uma única OPEN elegível por `recordId+targetKey`, preservar identidade de ocorrência, associar a `recordId` e registrar `associatedAt`, `associatedAtRevision=V1`, `originRequestId`, evidence/correlationId (nomes apenas TARGET).
5. Se houver duas ou mais OPEN para o mesmo alvo, vínculo incerto, alvo ausente ou status incompleto: **não migrar automaticamente**, registrar exceção revisável pelo owner. Não resolver, remover, fundir ou reabrir automaticamente.
6. OPEN incorporada se propaga somente enquanto aberta. RESOLVED na revisão vigente continua visível na revisão do evento e desaparece na seguinte; REMOVED desaparece na revisão do evento; nenhuma dessas ações gera versão técnica.
7. Backfill repetível e reversível da **associação**, sem apagar registros/ledger legados ou modificar snapshots técnicos. Definir comportamento de erro parcial, logs seguros, índices e grants antes de executar.

**Invariantes:** `recordId + targetKey` tem no máximo uma ocorrência OPEN; encerradas antigas não são incorporadas à projeção corrente; nunca forjar V0 nem atribuir RESOLVED à V1; nenhum clone/duplicação de flag; nova reincidência após resolução exige novo flagId CR-07. A relação documental original continua consultável por requestId quando autorizado.

**Coordination must ratify:** owner da migração e contrato de compatibilidade com D16, critério de prova de produto/alvo, janela temporal e política de inclusão de flags de solicitação ainda em andamento, conflito de múltiplas OPEN, esquema de associação/ledger, AuthZ incluindo owners de origem, e rollout/rollback. O usuário aprovou a **política funcional**, não uma implementação ou backfill em produção.

**HML tests:** OPEN elegível → V1, resolvida anterior → não entra, removida anterior → não entra, GENERAL/target missing → quarantined, colisões → sem incorporação, migration retry → sem duplicação, autorização negada → sem vazamento, V1 sem V2 artificial, RESOLVE/REMOVE pós-V1, sem bypass da rota reopen legada.

**Estado:** `PROPOSED_FOR_COORDINATION / TEST_NOT_RUN`. Nenhum código/migration/deploy executado.
