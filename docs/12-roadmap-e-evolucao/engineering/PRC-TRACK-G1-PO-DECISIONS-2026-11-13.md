# PRC-TRACK — Deliberações do Product Owner para G1 (13/11/2026)

> **REGRA FINAL DO PO — ADR-04 (2026-11-13; substitui todas as interpretações anteriores):** a bandeira é única por produto/alvo e propaga-se às revisões enquanto **OPEN**. Se **RESOLVED durante V4**, aparece em **V4 como RESOLVED** (verde), mas **não aparece em V5 em diante**. Se **REMOVED durante V4**, **não aparece nem em V4 nem nas posteriores**. V3 preserva OPEN nos dois cenários. O evento registra `revisionContext=V4`, instante, autor e operação; resolução/remoção não cria versão técnica. A ficha corrente da V4 reflete imediatamente resolução/remoção; versões anteriores preservam seu estado. Histórico de eventos continua auditável, inclusive após desaparecimento da bandeira. **A revisão de resolução é a revisão vigente quando ocorre a ação, e não uma revisão nova.** Se houver reabertura, definir contrato separado, não supor comportamento retroativo. Especificação de persistência/projeção ainda depende de Coordination.

> **Status:** `PO_DECISIONS_RECORDED / ARCHITECTURE_DECISION_REQUIRED` para alterações de autoridade, contrato e persistência. **Não é ADR ratificada pela Coordination.**  
> **Natureza:** registrar literalmente a intenção decisória, compatibilizar com o sistema existente e explicitar conflitos/bloqueios. **Sem autorização de migration, código ou deploy.**
>
> **Bases:** [G0/G1 evidence ledger](./PRC-TRACK-G0-INVENTORY-G1-COORDINATION-DECISION-PACKET.md), [pacote de implementação](./PRC-TRACKED-PRODUCTS-IMPLEMENTATION-PACKAGE-PLAN.md), [regras PRC de acompanhamento](./PRC-PRODUCT-TRACKING-VERSIONS-TRANSVERSAL-FLAGS-DECISIONS.md), [UX P1–P3](./PRC-PRODUCT-TRACKING-FRONTEND-VISUAL-SPEC.md).

## 1. Registro fiel das escolhas do Product Owner

| ADR | Escolha | Registro do PO | Classificação |
|---|---|---|---|
| 01 Ownership e identidade | Outra | “Engineering API como owner, reutilizando a identidade atual, no caso de produtos, não eiste diferença por filial.” | `PO_APPROVED_BUSINESS_INTENT`; ratificação de boundary/identidade pela Coordination |
| 02 Dados acompanhados | Outra | “os campos que precisamos acompanr são o registrados pela api de engenharia” | `PO_APPROVED_BUSINESS_INTENT`; contrato exato de campos/proveniência `TO_DEFINE` |
| 03 Flags por produto/alvo | A | Bandeiras persistentes por produto e alvo técnico | `PO_APPROVED_BUSINESS_INTENT`; migration/compatibilidade `ARCHITECTURE_DECISION_REQUIRED` |
| 04 Propagação de flags | Outra | “bandeiras devem ficar no produto, e transversais a revisão, então uma bandera colcoada na revisão 3 se não resolvida ou removida vai até revisão atual, cada nova.revisão replica a bandeira, assim tbm sabeos em qual revisão foi resolvida ou removida.” | `PO_APPROVED_BUSINESS_INTENT`; semântica física/temporal `TO_DEFINE` |
| 05 No-op e numeração | B | Gerar Vn **apenas quando houver diferença técnica real** | `PO_APPROVED_BUSINESS_INTENT`; corrige regra anterior; contrato `TO_DEFINE` |
| 06 Contratos e autorização | A | Engineering API com endpoints governados e comparação no backend | `PO_APPROVED_BUSINESS_INTENT`; desenho API/AuthZ `TO_DEFINE` |
| 07 Gate Plugin UI e HML | A + comentário | Gate completo antes do frontend; “podmos usar o ambiente de homologação para fazer todos so testes da ap, com as rotas 100% funcionais pdoemos seguir para o frontend.” | `PO_APPROVED_DELIVERY_INTENT`; execução/aceite de HML `PENDING` |

**Sem comentário adicional nas ADR-03, ADR-05 e ADR-06.** Aspas preservam o texto do PO, inclusive erros de digitação; abaixo segue interpretação arquitetural **proposta**, não confirmação de detalhes não mencionados.

## 2. Compatibilização e decisões técnicas que não devemos presumir

### ADR-01 — OWNER e identidade (compatível, com verificação técnica)

**Decisão de negócio:** `Engineering API / PRC` é owner do acompanhamento. Reusar a chave existente `official_source + official_product_code` **sem dimensão de filial** para produtos, conforme afirmação do PO. TOTVS/Domain API continua fonte oficial do cadastro; Core/Keycloak seguem AuthZ/identidade.

**Verificação exigida:** comprovar com contratos e dados autorizados que não há colisão por empresa/filial. O schema V012 declara unique por fonte+código. Não alterar chave, criar bounded context ou migration sem motivo e ratificação. Em caso de evidência divergente: `EXECUTION_DRIFT`, retornar à Coordination.

### ADR-02 — Conjunto de campos acompanhados (altera leitura anterior)

**Decisão de negócio:** o acompanhamento deve ser dos **campos registrados pela Engineering API** na ficha do PRC, e não necessariamente de todos os campos existentes no TOTVS. Isso define **escopo da ficha**, mas **não resolve sozinho** a diferença entre valor enviado pelo draft PRC, valor validado e valor oficialmente observado.

**Interpretação contratual recomendada (ratificar):**
- Definir o **catálogo de campos técnicos PRC governado pela Engineering API**, com schema versionado, incluindo vínculos de fornecedores que a API efetivamente registra.
- Após `verify-and-complete` com `matched`, criar snapshot **dos campos PRC cobertos**, com valor registrado, campos efetivamente verificados, evidência/proveniência e ausências. Não afirmar “fotografia integral do TOTVS”. Cada valor deve identificar se é observado, verificado por comparação ou registrado somente no PRC.
- Se o PO desejar **registrado pela API = draft validado**, isso pode ser aceito apenas com rótulo claro `PRC_VERIFIED_REGISTERED_STATE` (ou nome acordado), não `TOTVS_FULL_OFFICIAL_SNAPSHOT`; demonstrar que não existe confirmação indevida de atributos não verificados.
- O `_build_snapshot` atual copia `draft_data`; é necessário avaliar cobertura real, UPDATE parcial, fornecedores e suporte a valores ausentes antes de declarar `PASS`. Não completar snapshot com campos TOTVS fora do catálogo PRC. Não alterar revisões legadas retroativamente.

**Pergunta de contrato pendente (Coordination/owner):** para UPDATE parcial, a versão Vn representa (a) **estado consolidado completo dos campos PRC acompanhados**, combinando a base confirmada anterior + alterações validadas, ou (b) apenas o delta? **Recomendação: (a)** para permitir Ficha técnica Vn e diff V1↔V5; preservar delta separado, sem preencher lacunas desconhecidas por inferência.

### ADR-03 — Flags transversais (coerente com ADR-04)

**Decisão de negócio:** uma bandeira única por **produto + alvo técnico** (campo ou `supplierCode+store+attribute`), estável durante as versões, mantendo proveniência da solicitação/revisão de criação. Abertura, resolução, remoção e reabertura são eventos auditáveis; impedir duplicata OPEN inclusive em concorrência.

**Gap em código:** a pesquisa de flags existente ainda é por `request_id + target_key`. Evolução D16 para `recordId` e preservação dos consumidores request-centric exige contrato e migration governada, não duplicação de flags entre contextos.

### ADR-04 — “Replicar bandeiras” a cada nova revisão (coerente com ADR-03 **se for projeção**)

**Semântica desejada:** flag aberta na V3 aparece em V3, V4, V5 ... até que seja resolvida ou removida, com informação sobre quando e em qual contexto de evolução o evento ocorreu.

**Desenho recomendado:** **um registro lógico com ID único por flag + eventos de ciclo de vida**, e uma projeção/consulta `flagsAsOfRevision` (ou materialização derivada por Vn quando justificada) que **repete sua presença visual nas revisões**, sem criar clones operacionais do mesmo flag. Isto concilia ADR-03 com “cada nova revisão replica a bandeira”. Backfill não deve criar flags para fornecedor ainda inexistente, nem duplicar histórico artificial.

**Ponto de ambiguidade que exige decisão:** uma flag pode ser resolvida **entre V3 e V4 ou após a última V5**, sem criar revisão técnica. Logo, “em qual revisão foi resolvida” não é literalmente determinado pelo evento: o sistema pode mostrar **resolvida em data/hora X (estado passa a ser refletido em V4)** ou **resolvida enquanto V5 era a última versão**, sem declarar que a resolução criou V6. Eventos e números de revisão vigentes no momento da ação permitem exibir ambos sem falsear temporalidade.

**Proposta de semântica (para ratificação):** registrar `openedAtRevision`, `resolvedWhileRevision` e `resolvedAt`/ `removedAt` como **contexto temporal**, não atribuição causal à conclusão PRC; cortes históricos imutáveis; UI distingue estado da revisão e estado atual. Ação histórica somente leitura, mutação no produto atual mediante AuthZ.

### ADR-05 — Vn apenas quando há mudança real (altera regra anterior)

**Decisão substitutiva do PO:** **conclusão PRC validada sem diferença técnica real NÃO cria nova versão Vn**; o caso continua concluído/verificado e vinculado ao registro por ledger/evidência. A primeira versão V1 ocorre na primeira conclusão válida **com estado acompanhado efetivo**; não inventar versão em caso de no-op. Para UPDATE de produto ainda não acompanhado, avaliar a construção de V1 como primeiro snapshot conhecido, sem pressupor que baseline PRC anterior existia.

**Mudança explícita em documento anterior:** qualquer formulação “cada conclusão validada cria Vn” ou “subsequente conclusão gera Vn+1” deve ser lida **condicionalmente a diff real**. O número de revisões pode ser **menor** que o número de PRCs confirmadas. A UI de lista deve rotular `última evolução com mudança`, enquanto conclusões no-op ficam rastreáveis no workflow.

**Contrato necessário:** comparação de valores canônicos sob schema/cobertura equivalentes, supplier links por identidade; decidir se diferença de campo desconhecido conta, representação de primeira V1, baseRevision stale, CAS/idempotência, detecção no-op em transação e vínculo do request mesmo sem revision. **Há drift**: `postgres_repository.complete_request` atualmente incrementa número e insere revisão em todo matched completion. Não implementar sem aprovação de novo fluxo atômico.

### ADR-06 — API governada e diff no backend

**Decisão:** Engineering API expõe listagem autorizada paginada, registro/detalhe, snapshots Vn, flags por produto no estado atual e no corte da revisão, operações mutáveis governadas, e comparação **servidor-side** Vx×Vy. O MFE não reproduz regras autoritativas de diff.

**Requisitos:** DTOs e erros versionados; filtros `search,flagState,sort,page,pageSize`; diff por campo e fornecedor+loja (added/removed/changed), coverage/incomparable separados; eventos de flags separados, AuthZ live e por objeto/escopo, CAS/idempotência para writes, logs sem secrets; compatibilidade com rotas PRC e Catálogo TOTVS. Endpoint e nomes concretos permanecem `TARGET` até contrato formal.

### ADR-07 — Gate completo com API funcional em HML antes do frontend

**Decisão:** usar ambiente de **homologação autorizado** para executar testes da Engineering API com **rotas 100% funcionais dentro do escopo contratado** antes de iniciar U1–U3. Não equivale a 100% de cobertura de testes. G0 Plugin UI também precisa commit/export MF, testes e QA visual autenticado. Se a validação visual exigir contexto real, usar HML com entitlement autorizado e caso PRC real/fixture governado.

**Sequência ajustada:** 1) fechar extração do Plugin UI e validar HML do kit/consumidores existentes; 2) ratificar contratos B1–B3 e implementar backend por fases; 3) validar **todas as rotas do novo escopo** em HML, positivas/negativas, concorrência e proveniência; 4) iniciar frontend U1–U3; 5) QA browser integral das novas páginas; 6) deployment somente com autorização. Não bloquear design documental enquanto G0 aberto. Não burlar RBAC, nem declarar QA visual de páginas inexistentes.

## 3. Conflitos identificados e resolução proposta

| ID | Conflito/tensão | Tratamento |
|---|---|---|
| K01 | Documento anterior exige “snapshot oficial completo observado”; PO delimita acompanhamento aos campos registrados pela Engineering API | **Supersede o escopo anterior**: somente campos do catálogo PRC; provenance e cobertura obrigatórias. Rótulo “completo” só se cobertura completa do catálogo acompanhado. `ARCHITECTURE_DECISION_REQUIRED` para semântica observada vs draft validado. |
| K02 | “Cada revisão replica bandeira” vs flag com ID persistente única | Replicação **de visibilidade/projeção**, não duplicação física de flag; alternativa de materialização derivada somente com justification e rollback. |
| K03 | “Saber em qual revisão resolvida” vs resolução sem revisão nova | Registrar `revision vigente na transição` + timestamp/eventId; se entre revisões, indicar corte efetivo subsequente e contexto, sem inventar versão. |
| K04 | Regra anterior “uma versão por conclusão” vs ADR-05 B | **ADR-05 substitui regra anterior**: Vn somente com diff real, no-op com completion auditado e sem incremento. `EXECUTION_DRIFT` no fluxo atual de persistência. |
| K05 | Escolha ADR-07 gate completo vs HML antes frontend | Complementares: HML executa contratos/API, QA do Plugin UI; browser das novas páginas ocorre após sua implementação, antes do aceite final. |
| K06 | Identidade sem filial vs unique por source+code | Coerente segundo PO e schema atual; evidência de domínio/código oficial ainda deve ser verificada. |

## 4. Critérios de aceite revisados

- **PO-AC01:** acompanhamento por `official_source+official_product_code` sem filial (evidência da unicidade, AuthZ).
- **PO-AC02:** catálogo de campos PRC e fornecedor é explícito; Vn conserva campos registrados/confirmados e marca lacunas sem atribuir falso estado TOTVS.
- **PO-AC03:** CREATE/UPDATE verificados com **mudança** criam Vn; matched no-op conclui PRC sem Vn+1; retry não duplica; duas conclusões concorrentes respeitam CAS.
- **PO-AC04:** V1 do primeiro acompanhamento via UPDATE contempla baseline conhecido e não atribui criação ao ERP.
- **PO-AC05:** flag aberta em V3 está presente em V4/V5 enquanto OPEN, **mesmo ID**; evento de resolução/remoção registra data, ator, revisão vigente, e alterações posteriores não reescrevem histórico.
- **PO-AC06:** supplier target por `code+store+attribute`; remoções mantêm rastreabilidade, sem permitir editar flag do vínculo inexistente.
- **PO-AC07:** API entrega diff V1↔V5 para campos e fornecedores, com valores incomparáveis sinalizados e eventos de flags em seção separada.
- **PO-AC08:** C04–C08 operam em HML com testes de AuthZ positivo/negativo, 403/409, paginação, concorrência e auditoria; sem bypass de entitlement.
- **PO-AC09:** remote Plugin UI e QA existentes estão `PASS` antes de frontend; páginas passam QA browser responsivo depois da implementação e antes do release.
- **PO-AC10:** versões legadas permanecem imutáveis e com rótulo de origem/cobertura; sem backfill inferido.

## 5. Matriz de readiness / encaminhamento

| Área | Estado após deliberação PO | Próximo owner/ação |
|---|---|---|
| ADR-01 | `PO_APPROVED_BUSINESS_INTENT` | Coordination ratificar owner/chave e exigir evidência de unicidade |
| ADR-02 | `PO_APPROVED_SCOPE / CONTRACT_TO_DEFINE` | Engineering API owner + Coordination: catálogo, snapshot total PRC vs delta e provenance |
| ADR-03 | `PO_APPROVED_BUSINESS_INTENT / ARCHITECTURE_DECISION_REQUIRED` | Coordination: migração D16 e constraints |
| ADR-04 | `PO_APPROVED_BUSINESS_INTENT / TEMPORAL_SEMANTICS_TO_DEFINE` | Coordination: eventos, revisão vigente, projeção, compatibilidade |
| ADR-05 | `PO_APPROVED_NO_OP_POLICY / IMPLEMENTATION_DRIFT` | Engineering API owner: transação com no-op, testes |
| ADR-06 | `PO_APPROVED_API_OWNERSHIP / CONTRACT_TO_DEFINE` | Engineering API owner/Core: AuthZ, comparação e erros |
| ADR-07 | `PO_APPROVED_DELIVERY_GATE / PENDING_EXECUTION` | Engenharia/QA: Plugin UI commit, HML rotas 100% funcionais no escopo, visual e evidência |
| B1–B3, U1–U3 | `BLOCKED` | Não executar até contrato/Coordination/gates |

**Perguntas pontuais para resolver em contrato com owner (não substituir por premissas):** (1) UPDATE parcial: snapshot consolidado do catálogo PRC ou delta? (2) quais valores da API contam como oficialmente verificados vs apenas registrados? (3) evento de flag entre versões: exibir “resolvida enquanto Vn vigente” ou “resolvida na transição para Vn+1”? (4) no-op do primeiro acompanhamento sem snapshot prévio: quando nasce V1? Essas perguntas não impedem documentar a decisão funcional do PO, mas bloqueiam alteração de semântica persistida.

## 6. Próximo passo governado

Encaminhar à Coordination **ADR-01 a ADR-06** com matriz de decisão e perguntas acima, exigir ratificação explícita da autoridade, compatibilidade e contratos. **ADR-07** é gate operacional a executar em HML autorizado. Após ratificação: ajustar plano B1 (campos PRC/provenance/no-op), B2 (flags ID estável/projeção temporal), B3 (reads/diff servidor) e validar API 100% funcional no escopo em HML antes de abrir U1.

**Nenhuma implementação, schema migration, chamada de deploy ou ratificação da Coordination executada por este registro.**


## 7. Emenda PO à ADR-04 — resolução visível somente na revisão do evento

| Momento | Se flag criada em V3 é resolvida em V4 | Se flag criada em V3 é removida em V4 |
|---|---|---|
| V3 | **OPEN** — bandeira aberta | **OPEN** — bandeira aberta |
| V4 (revisão vigente da ação) | **RESOLVED** — bandeira verde, visível | **AUSENTE** — bandeira não aparece |
| V5 e seguintes | **AUSENTE** — não propaga a resolvida | **AUSENTE** — não propaga a removida |
| Histórico de eventos | criação V3 + resolução no contexto V4 | criação V3 + remoção no contexto V4 |

**Precedência:** esta emenda substitui a formulação antiga segundo a qual RESOLVED desapareceria imediatamente da ficha atual. **A resolução permanece visível na própria revisão do evento**, e não nas próximas. A remoção apaga a apresentação na própria revisão do evento. Ação não gera nova versão, apenas evento de flags. Manter mesma identidade técnica da bandeira nas revisões, sem clonar registro.

**Contratos pendentes para Coordination:** (a) estado de exibição de revisão atual pode ser atualizado por evento sem alterar snapshot técnico imutável; (b) revisão do evento = última Vn vigente no instante da mutação, gravada de forma auditável; (c) regras de visibilidade em caso de reabertura e flags criadas antes da primeira V1; (d) integridade da projeção durante concorrência/soft-delete. Estes detalhes **não mudam o comportamento funcional aprovado**.

**Novos AC obrigatórios:** B2-FLAG-01 criada em V3 → OPEN V3/V4/V5 enquanto não encerrada; B2-FLAG-02 resolvida durante V4 → OPEN V3, RESOLVED V4, AUSENTE V5; B2-FLAG-03 removida durante V4 → OPEN V3, AUSENTE V4/V5; B2-FLAG-04 resolver/remover não incrementa versão; B2-FLAG-05 eventos auditáveis e mesma identidade, AuthZ/CAS/idempotência.
