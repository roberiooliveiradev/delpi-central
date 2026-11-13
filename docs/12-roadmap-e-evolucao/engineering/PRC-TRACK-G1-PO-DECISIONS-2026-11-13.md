# PRC-TRACK — Deliberações do Product Owner para G1 (13/11/2026)

> **DIRETRIZ SIMPLIFICADORA DO PO — CR-13 (13/11/2026; PREVALECE sobre exigências de aprovação especial nas seções precedentes):** O ciclo de vida das bandeiras (adicionar, visualizar, resolver e remover) é **controle operacional interno da Engenharia**, tratado pela **Engineering API no fluxo do Portal Engenharia/PRC**. **Quem já possui acesso autorizado ao Portal Engenharia pode operar bandeiras, usando as permissões existentes; não criar novos papéis, grants específicos, approval workflow ou aprovação de outro responsável exclusivamente para bandeiras.** O backend continua responsável por validar sessão, acesso existente, integridade, estado e rastreabilidade; acesso à UI não substitui validação no servidor. A operação de remoção é direta pelo usuário autorizado, sem aprovação adicional. Não introduzir justificativa formal obrigatória ou rito de aprovação novo para remoção/resolução: usar o registro de evento existente com ator, instante, alvo, contexto de revisão e origem. A regra é simples, sem alterar ADR-04 (RESOLVED aparece na versão do evento; REMOVED desaparece nela) ou CR-09 (solicitação ainda aberta não publica alteração no produto). **A CR-13 fica decidida neste nível, sem novas opções/questionários.** Detalhes de contrato técnico só se justificam quando necessários para implementação segura e interoperabilidade. `PO_APPROVED_BUSINESS_DIRECTION / COORDINATION_RATIFICATION_PENDING`.


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

## 8. Deliberação complementar do PO — CR-02 (13/11/2026)

**Escolha expressa:** **A — Ficha consolidada por versão**. **Comentário:** sem comentário. **Classificação:** `PO_APPROVED_BUSINESS_DECISION`; contrato e implementação sujeitos à Coordination.

**Regra vinculante de produto:** cada Vn contém uma representação consolidada de todos os campos pertencentes ao catálogo de acompanhamento PRC da Engineering API, incluindo vínculos de fornecedores dentro da cobertura definida. Não é apenas o delta da solicitação. O delta é registrado separadamente para comparação/auditoria. Dados desconhecidos ou não cobertos não podem ser inventados nem apresentados como comprovadamente oficiais.

**Consequências de contrato:**
1. `schemaVersion` do catálogo e snapshot; identidade de produto, revisão, solicitação, confirmação e provenance.
2. Em UPDATE parcial, recomposição a partir da última base conhecida e confirmada e dos campos efetivamente registrados/verificados na nova solicitação, com regras explícitas para omissão, `null`, remoção e desconhecido.
3. Fornecedores por chave estável `supplierCode+store` e atributos acompanhados; separação entre vínculo ausente, removido e não observado.
4. Diff Vx×Vy no backend usa os **dois estados consolidados**, não só `changedPaths` do draft.
5. A comparação para criar Vn é normalizada e considera somente diferenças técnicas reais; conclusão no-op não cria revisão, preservando seu próprio ledger.
6. Revisões imutáveis anteriores não devem sofrer backfill inferido; snapshot legado precisa `coverage/provenance` e aviso de qualidade dos dados.

**Ainda requer ratificação técnica:** política de campos confirmados vs apenas registrados na API, esquema e cobertura; semântica de merge UPDATE parcial; suporte a V1 sem histórico prévio. **Não autoriza código/migration/deploy.**

## 9. Deliberação complementar do PO — CR-03: nascimento da V1 (13/11/2026)

**Escolha expressa:** **A — Criar V1 como baseline inicial mesmo sem mudança técnica**. **Comentário:** sem comentário. **Classificação:** `PO_APPROVED_BUSINESS_DECISION / COORDINATION_RATIFICATION_PENDING`.

**Regra funcional com precedência sobre textos anteriores:**

1. **Primeiro acompanhamento confirmado:** na primeira conclusão PRC validada para um produto sem registro de versão anterior, criar **V1** como *baseline técnico inicial dos campos PRC acompanhados*, mesmo que a solicitação não tenha provocado modificação técnica real. Esse snapshot usa o contrato CR-02 de ficha consolidada e requer proveniência/coverage adequadas. UPDATE preexistente pode originar V1: isso **não significa criação do produto no TOTVS**.
2. **Produto já acompanhado:** somente conclusão PRC validada com **diferença técnica real** diante da última versão consolidada gera **Vn+1**.
3. **No-op posterior:** conclusão PRC verificável sem diferença é auditada e vinculada ao record/revision atuais, sem nova revisão, sem alterar snapshot imutável, nem duplicar por replay.
4. **Falha/divergência:** verificação não matched ou conclusão não efetivada **não cria V1 nem Vn+1**.
5. **Invariante:** `revisionNumber` é sequência de *baseline inicial + alterações reais confirmadas*, não contagem de solicitações concluídas.

**Compatibilidade com ADR-05:** a opção B da ADR-05 permanece válida para **V2 em diante**; CR-03-A é a **exceção explícita de inicialização do histórico**. Não há contradição se a regra for `IF no existing revision AND validated completion THEN V1 baseline ELSE IF real diff THEN next revision ELSE completion no-op`.

**Impactos de contrato/implementação a ratificar:** caminho atômico de primeira V1; distinguir `baseline_initial` versus `technical_change` versus `no_technical_change` nos metadados/eventos; construir V1 com dados CR-02 e qualidade suficiente; testar dois fluxos CREATE/UPDATE e retries; associar no-op à versão vigente; migrações/grants somente após inventário; compatibilidade de `current_revision_number` e evidence ledger. O `complete_request` atual cria revisão em todas as conclusões matched, portanto a exceção V1 e a supressão subsequente de no-op exigem mudanças condicionais, não mero ajuste de frontend.

**Aceite adicional:** `CR03-AC01` UPDATE primeira conclusão matched sem mudança → V1 baseline; `CR03-AC02` segunda matched sem diff → continua V1; `CR03-AC03` próxima matched com diff → V2; `CR03-AC04` falha, retry ou concorrência não produzem revisão indevida; `CR03-AC05` histórico rotula V1 como primeiro acompanhamento, não criação ERP.

**Estado:** decisão funcional do PO registrada; ratificação de contrato, segurança, transação e rollout continua com Coordination. Nenhuma alteração de código/migration/deploy autorizada.

## 10. Deliberação complementar do PO — CR-04: proveniência e confirmação dos campos (13/11/2026)

**Escolha expressa:** **A — Preservar valores e identificar sua confirmação**. **Comentário:** sem comentário. **Status:** `PO_APPROVED_BUSINESS_DECISION / COORDINATION_RATIFICATION_PENDING`.

**Regra funcional:** o snapshot consolidado mantém os valores dos campos acompanhados pela Engineering API, sem apagar campos apenas porque não foram individualmente reverificados em determinada solicitação. **Cada campo precisa de origem, cobertura e estado de confirmação explícitos.** Distinguir pelo menos: (a) valor confirmado pela fonte oficial no contexto da verificação atual, (b) valor carregado de última versão previamente confirmada válida, (c) valor registrado pela Engenharia mas sem evidência individual suficiente para ser proclamado oficial, e (d) desconhecido/indisponível. Nenhum dos estados permite declarar verificação inexistente, nem contornar gates de conclusão PRC.

**Compatibilidade:** 
- **CR-02 — ficha consolidada:** preserva os campos acompanhados, com seus metadados de proveniência; UPDATE parcial não descarta dados mantidos da base anterior. O delta da PRC permanece separado.
- **CR-03 — baseline inicial V1:** a primeira conclusão matched materializa V1 com os valores conhecidos e seus estados de confirmação/coverage; não presume que todos são observados no TOTVS nem que o produto foi criado por aquela PRC. Em V2+, somente diferença **técnica real de valores/vínculos** confirmada cria nova revisão; mudança exclusiva de metadados de confirmação **não** deve criar versão técnica sem nova decisão do owner. Correções de proveniência devem ser auditáveis e não reescrever snapshots imutáveis por inferência.

**Gates de contrato (Coordination/Engineering API):** catálogo versionado de campos PRC; enum e significado do estado de confirmação; `valueOrigin`, `evidenceId`, `verifiedAt`, `sourceRevision`, `coverage`, `schemaVersion`; semântica de `null` vs ausência vs desconhecido; mecanismo de merge UPDATE parcial; confidencialidade e AuthZ por objeto; compatibilidade do DTO existente. O estado `registered_unverified` não pode ser promovido a `official_verified` por inferência. `matched` de uma conclusão ainda exige as validações obrigatórias pelo owner, independentemente da apresentação do campo.

**AC adicionais:** `CR04-AC01` UPDATE de descrição preserva classificação anterior com origem herdada; `CR04-AC02` valor registrado não individualmente confirmado aparece com indicação explícita, não como confirmado TOTVS; `CR04-AC03` campo desconhecido não recebe valor fabricado; `CR04-AC04` primeira V1 contém cobertura declarada; `CR04-AC05` atualização somente de estado de confirmação não gera V2 sem diff técnico; `CR04-AC06` campos/vínculos comparados preservam rastreio de origem; `CR04-AC07` falha de verificação impede conclusão mesmo que ficha contenha campos registrados.

**Não autoriza** implementação, migration, deploy ou mudança de owner; detalhes técnicos exigem ratificação pela Coordination.

## 11. Deliberação complementar do PO — CR-05: UPDATE parcial e fornecedores (13/11/2026)

**Escolha expressa:** **A — Preservar campos e fornecedores não alterados e aplicar somente mudanças explícitas.** **Comentário:** sem comentário. **Status:** `PO_APPROVED_BUSINESS_DECISION / COORDINATION_RATIFICATION_PENDING`.

**Regra funcional:** em solicitação UPDATE, a nova ficha consolidada herda da última versão Vn os campos e vínculos de fornecedores não abrangidos por uma operação explícita. Somente alterações, inclusões e remoções declaradas, autorizadas e efetivamente validadas podem modificar o estado técnico consolidado. Omissão de atributo/cadastro de fornecedor **não é** comando para zerar, excluir ou substituir. Identidade do vínculo de fornecedor: `supplierCode + store`, com atributos técnicos registrados pelo PRC, sujeitos à identificação e cobertura válidas.

**Compatibilidade com decisões anteriores:**
- **CR-02:** cada revisão permanece um **snapshot consolidado completo do escopo de campos PRC conhecidos**, não apenas delta. O delta aplicado e a proveniência da solicitação continuam separados.
- **CR-03:** na primeira conclusão válida, V1 é baseline inicial mesmo sem mudança. Nas demais, o merge de UPDATE parcial somente resulta em Vn+1 quando o diff técnico consolidado for real; no-op conclui e audita sem incrementar.
- **CR-04:** cada valor herdado mantém a origem e o nível de verificação de sua evidência anterior; não é automaticamente reconfirmado. Valores alterados recebem proveniência e confirmação correspondentes. Lacunas continuam desconhecidas, sem valor inventado.

**Semântica de domínio a ratificar:** `omitted` (nenhuma mudança), `set(value)` (mudança explícita, inclusive significado contratual de `null`), `remove` (remoção explícita autorizada), `unknown/not_observed` (cobertura insuficiente, não equivale a remoção), e operações em fornecedores por chave estável. A Engineeering API deve confirmar o formato canônico, permissões de remover fornecedor, limites da leitura oficial, idempotência/CAS, compatibilidade de DTOs e tratamento de valores legados. **Não inferir que uma operação REMOVE de fornecedores já pode ser concluída no runtime**: há gates existentes de SA5 a inventariar. A regra de negócio aprovada não os contorna.

**Critérios de aceite CR05:** (1) alterar somente descrição mantém unidade, classificação e fornecedores; (2) fornecedor não mencionado permanece; (3) atributo omitido não apaga valor; (4) exclusão explícita autorizada afeta apenas alvo correto, preservando histórico; (5) field-null e field-omission têm efeitos distintos definidos em contrato; (6) proveniência dos herdados permanece original; (7) merge sem diferença após V1 não gera Vn+1; (8) operação não verificada/sem autorização falha sem publicar revisão.

**Sem código, migration ou deploy.** Esta decisão funcional não substitui ratificação da Coordination sobre contrato, autoridade, operações de remoção ou segurança.


## 12. Deliberação complementar do PO — CR-06: limpeza explícita e validada (13/11/2026)

**Escolha expressa:** **A — Limpeza explícita com validação do campo**. **Comentário:** sem comentário. **Classificação:** `PO_APPROVED_BUSINESS_DECISION / COORDINATION_RATIFICATION_PENDING`.

**Regra funcional:** em UPDATE parcial, **campo omitido** preserva o valor consolidado e a proveniência anterior; **valor vazio/null recebido sem operação inequívoca de limpeza não é autorização para apagar**; para limpar um campo exige-se intenção **explícita de limpeza** expressa pelo contrato PRC, permissão do ator, compatibilidade com o catálogo técnico e confirmação oficial quando aplicável. Campos obrigatórios ou que não admitem vazio **não podem ser limpos**. Rejeitar operação inválida sem publicar revisão nem alterar estado técnico.

**Compatibilidade:**
- **CR-02:** somente operações aceitas compõem o snapshot técnico consolidado, preservando demais campos e vínculos.
- **CR-03:** primeira conclusão validada inaugura V1; em V2+, limpeza que muda valor técnico pode gerar Vn+1; limpeza sem diferença efetiva é no-op auditado.
- **CR-04:** limpar um campo não significa que a fonte ficou `unknown`: registrar **operação deliberada**, origem/evidência e estado de verificação; `unknown/unobserved` representa falta de informação, não limpeza.
- **CR-05:** omissão é diferente de `CLEAR` explícito; fornecedores omitidos permanecem. **Não confundir limpeza de atributo de vínculo com remoção de todo vínculo**. Operação REMOVE de fornecedor segue gates próprios existentes, incluindo restrições SA5.

**Regras técnicas para ratificação (não presumir contrato existente):** verificar catálogo de campos nuláveis/obrigatórios; inventariar DTOs atuais para escolher indicador explícito de operação (`CLEAR` ou equivalente) de modo backward-compatible; padronizar semântica de `null`, string vazia e espaços; distinguir operação `SET`/ `CLEAR`/ `REMOVE_LINK`/ omissão; validar solicitação, AuthZ live, CAS/idempotência, read-back oficial e auditabilidade. Não mapear automaticamente `null` para limpeza sem prova de intenção.

**Critérios de aceite:** `CR06-AC01` campo omitido preserva valor; `CR06-AC02` vazio ambíguo sem CLEAR não apaga; `CR06-AC03` CLEAR explícito em campo que admite limpeza, autorizado e verificado, remove somente valor-alvo; `CR06-AC04` CLEAR em obrigatório/não suportado é rejeitado; `CR06-AC05` limpeza de atributo fornecedor não remove vínculo; `CR06-AC06` técnico diff real após V1 gera próxima versão, sem mudança mantém versão; `CR06-AC07` mismatch, 403, 409 ou source unavailable não publicam revisão; `CR06-AC08` provenance da operação de limpeza permanece auditável.

**A decisão não confirma a existência de suporte CLEAR no runtime e não autoriza código, migrations ou deploy.** Ratificação de DTO, campos e segurança cabe à Coordination/Engineering API.


## 13. Deliberação complementar do PO — CR-07: resolução definitiva, sem reabertura (13/11/2026)

**Escolha expressa:** **C — Não permitir reabertura**. **Comentário:** sem comentário. **Status:** `PO_APPROVED_BUSINESS_DECISION / COORDINATION_RATIFICATION_PENDING`.

**Regra funcional:** uma bandeira `RESOLVED` não pode voltar para `OPEN` sob o mesmo `flagId`; encerramento é definitivo. Se o problema reincidir, a Engenharia deve criar **nova bandeira com novo ID**, mesmo que tenha o mesmo `recordId + targetKey`. Cada ocorrência tem ciclo de vida independente, proveniência da revisão de criação e auditoria própria. A bandeira anterior permanece encerrada e seu histórico não é reescrito. **Não exigir vínculo entre ocorrências nem criá-lo automaticamente:** relação opcional é `TO_DECIDE` com o owner.

**Compatibilidade ADR-03:** a unicidade é de **no máximo uma bandeira OPEN por produto + alvo técnico**, e **não** unicidade eterna de um único registro por alvo. Múltiplas ocorrências históricas `RESOLVED/REMOVED` para o mesmo alvo são permitidas; nova OPEN após encerramento é válida desde que não haja outra OPEN no mesmo alvo. Preservar lock/constraint contra criação OPEN duplicada concorrente. Ajustar qualquer frase anterior “mesma bandeira reaberta” ou “identidade única perpétua por alvo” à regra substitutiva do PO.

**Compatibilidade ADR-04:** criada V3 → OPEN V3; resolvida V4 → RESOLVED visível V4, **ausente V5+**; removida V4 → ausente em V4 e seguintes. Nova ocorrência aberta na V6 (outro ID) → OPEN na V6, sem retroagir a V3/V4/V5. Resolução/remoção/criação de flags não cria versão técnica. Uma nova bandeira pode nascer enquanto Vn é vigente, mesmo que a versão técnica Vn não tenha sido criada pela ocorrência.

**Gap comprovado em código:** `engineering-api/engineering_app/application/use_cases/product_registration/service.py::reopen_flag` e rota `POST /v1/product-registration/requests/{request_id}/flags/{flag_id}/actions/reopen` existem no código consultado. A decisão do PO **não revoga automaticamente** este endpoint legado. Coordination deve definir compatibilidade, consumidores e estratégia de descontinuação/bloqueio da reabertura no **novo contrato de produtos acompanhados**, com segurança backend-first. Não ocultar botão apenas no frontend.

**AC:** `CR07-AC01` tentativa de reabrir RESOLVED por flagId rejeitada pela API de produtos acompanhados com erro contratual; `CR07-AC02` encerrada em V4 permanece RESOLVED só em V4; `CR07-AC03` nova flag mesmo target em V6 recebe novo flagId; `CR07-AC04` OPEN concorrente no mesmo produto+alvo rejeita duplicata; `CR07-AC05` V3/V4/V5 históricos não alterados por nova ocorrência; `CR07-AC06` eventos auditáveis, AuthZ live/CAS/idempotência; `CR07-AC07` endpoint legado de reopen não pode contornar política ratificada para flags de produto e tem comportamento de compatibilidade explicitamente testado.

**Não autoriza** desativar endpoints existentes, migration, alteração de código, rollout ou mudança de owner. `ARCHITECTURE_DECISION_REQUIRED` para coexistência de D16 legado e nova política.


## 14. Deliberação complementar do PO — CR-08: bandeiras anteriores à primeira V1 (13/11/2026)

**Escolha expressa:** **A — Incorporar bandeiras abertas com vínculo comprovado**. **Comentário:** sem comentário. **Estado:** `PO_APPROVED_BUSINESS_DECISION / COORDINATION_RATIFICATION_PENDING`.

**Regra funcional:** ao criar o primeiro acompanhamento V1 de produto já cadastrado, incorporar à projeção do produto **somente bandeiras PRC legadas que estejam OPEN** e para as quais seja possível provar, por fontes autorizadas, a correspondência inequívoca com (1) `official_source + official_product_code`, (2) o alvo técnico FIELD ou SUPPLIER_LINK com `supplierCode+store+attribute` e (3) o caso de origem. A integração à V1 é uma **associação/projeção governada**, não abertura retroativa de bandeira em V0 nem criação de revisão técnica adicional. Preservar ID da ocorrência quando comprovadamente seguro; não fundir ou renumerar flags sem plano de compatibilidade.

**Exclusões explícitas:** RESOLVED, REMOVED, soft-deleted, GENERAL sem alvo identificável e vínculos ambíguos **não são ativados** na V1. Registros encerrados permanecem disponíveis no histórico de suas solicitações de origem, conforme escopo de acesso. Identidade incerta segue **quarentena para revisão autorizada** — nunca atribuição automática por descrição/código parcial, nem tentativa de gerar vínculo novo a partir de inferência de IA.

**Compatibilidade com decisões anteriores:**
- **CR-03:** primeira conclusão verificada cria V1 baseline independentemente de diff técnico; migração de bandeira OPEN **não cria V2** e não altera snapshot de campos PRC.
- **ADR-04:** bandeira incorporada na V1 aparece OPEN e propaga às versões subsequentes enquanto aberta. Se RESOLVED em V4, é visível RESOLVED apenas na V4, ausente V5+; se REMOVED em V4, ausente já em V4 e posteriores. Estado anterior à V1 não deve ser inventado como versão técnica.
- **CR-07:** incorporar OPEN **não reabre** flags encerradas. Reincidência posterior de problema encerrado gera nova ocorrência/ID, sem reutilização do antigo. Máximo uma OPEN por produto+alvo.
- **ADR-03:** não clonar registros; rastrear a origem em requestId e a associação ao recordId. Em caso de múltiplas OPEN legadas no mesmo produto+alvo, **não escolher automaticamente** a vencedora.

**Gates de autoridade e migração a submeter à Coordination:** definir owner Engineering API/PRC, regras oficiais de lookup de produto e alvo, compatibilidade de IDs e consumidores D16 por requestId, vínculo temporal da incorporação (`associationAt`/V1), colisões OPEN, permissões de leitura/escrita, trilha auditável, idempotência, backfill parcial/reversível, relatório de exceções e rollback sem reescrever passado. Não consultar banco de outro bounded context nem promover provider/MCP à authority. HML com principal autorizado.

**Critérios de aceite:** `CR08-AC01` flag OPEN inequívoca de PRC anterior aparece OPEN em V1; `CR08-AC02` flag RESOLVED/REMOVED anterior não aparece na V1; `CR08-AC03` flag sem código/target confiável fica pendente e não aparece; `CR08-AC04` colisões OPEN no mesmo alvo impedem incorporação automática e geram exceção auditável; `CR08-AC05` associação não gera V2/alteração de snapshot; `CR08-AC06` lifecycle V1→V4 segue ADR-04; `CR08-AC07` nenhum flagId encerrado é reaberto; `CR08-AC08` backfill repetido não duplica, AuthZ/concurrency e histórico são preservados.

**Sem alteração de código, migration, grants, runtime ou deploy.** A decisão do PO não equivale à ratificação da Coordination.


## 15. Deliberação complementar do PO — CR-09: alterações só na conclusão da solicitação (13/11/2026)

**Escolha expressa:** **B — Somente após conclusão da solicitação**. **Comentário literal do PO:** “a solicitação só deve alterar o produto após concluida, solicitação não é uma nova versão do produto.” **Status:** `PO_APPROVED_BUSINESS_DECISION / COORDINATION_RATIFICATION_PENDING`.

**Regra funcional prevalente:** durante `OPEN/IN_PROGRESS` (ou estado equivalente a inventariar), os dados técnicos e as bandeiras permanecem **no escopo da solicitação PRC**, sem alterar a ficha consolidada, a projeção de bandeiras, o número da versão ou a lista de alterações do produto acompanhado. A conclusão **válida, autorizada e confirmada** é o único gate para integrar alterações da solicitação à projeção de produto. **Solicitação PRC não é sinônimo de versão**: a primeira conclusão válida de produto sem versões cria baseline V1 (CR-03); em versões posteriores, só diff técnico confirmado gera Vn+1 (ADR-05); conclusão no-op pode integrar bandeiras ainda OPEN sem criar nova versão.

**Bandeiras:** se uma bandeira da solicitação estiver **OPEN no instante da conclusão válida**, pode ser incorporada ao produto apenas após validação de identidade oficial, alvo técnico, AuthZ e colisões OPEN. A bandeira não passa ao produto enquanto a solicitação estiver aberta. Se a bandeira foi RESOLVED/REMOVED **antes da conclusão**, não entra na projeção do produto; seus eventos permanecem auditáveis na solicitação. A resolução/remoção **depois da incorporação** segue ADR-04: RESOLVED visível na revisão vigente do evento, REMOVED ausente já naquela revisão, ambas ausentes nas posteriores. **Nenhuma ação de bandeira cria Vn.**

**Compatibilidade:**
- **CR-07:** não reabrir bandeira encerrada; novo problema exige novo ID. A conclusão não reativa uma bandeira RESOLVED.
- **CR-08:** incorporação inicial em V1 de flags legadas OPEN com vínculo comprovado deve respeitar **também o gate de conclusão de suas solicitações de origem**. Um registro histórico OPEN de PRC ainda em andamento **não é elegível** para associação na V1 por mero backfill. A decisão CR-09 **restringe** o conjunto elegível da CR-08; o legado com estado de conclusão não verificável fica `PENDING_OWNER_REVIEW`, não entra automaticamente.
- **ADR-04:** a visibilidade temporal da bandeira no produto só começa após conclusão/associação autorizada, na versão então vigente (ou V1 se criada na conclusão); não simular flag presente em revisões anteriores pela data de abertura na solicitação.
- **CR-02/03/04/05/06 e ADR-05:** nenhuma alteração técnica no produto durante a solicitação; conclusão gera baseline V1, nova versão com diff, ou no-op com auditoria, conforme regras aprovadas.

**Exemplo:** produto V3; solicitação UPDATE aberta cria flag F na PRC → **V3 produto sem F**. PRC concluída e validada sem mudança técnica, F continua OPEN → **produto segue V3**, F passa a aparecer OPEN em V3 (contexto de associação), sem V4. Se V4 surgir mais tarde por mudança técnica, F propaga enquanto OPEN. Se F foi encerrada antes da conclusão, F **não aparece** no produto em V3.

**Conflitos técnicos a submeter à Coordination:** relação entre flag por request D16 e flag por record; prova de conclusão `matched`; momento de associação `completedAt / associatedAt / revisionContext`; concorrência entre conclusão e mutações de flag; caso de PRC cancelada/rejeitada e legado sem status comprovável; modo de consulta request-local separado da ficha de produto; rota legada `reopen`, migração idempotente e retrocompatibilidade. A documentação não presume que o runtime atual já implemente essa separação.

**AC CR09:** (01) flag OPEN na solicitação em andamento não altera ficha/lista/versões do produto; (02) conclusão validada incorpora apenas OPEN elegível; (03) flag RESOLVED/REMOVED antes de concluir não incorpora; (04) conclusão no-op com OPEN associa a Vn vigente sem criar Vn+1; (05) conclusão que gera Vn+1 incorpora após transação e associa a essa Vn+1; (06) falha, rejeição, cancelamento ou AuthZ negada não publicam alterações; (07) CR-08 backfill exclui PRCs não concluídas; (08) idempotência/CAS evita duplicação e race; (09) flags associadas seguem ADR-04 e CR-07.

**Sem código, migration ou deploy.** Requer ratificação da Coordination sobre contrato, migração, autoridade e testes.


## 16. Deliberação complementar do PO — CR-10: conflito OPEN bloqueia conclusão integral (13/11/2026)

**Escolha expressa:** **A — Exigir resolução do conflito antes da conclusão, sem publicação parcial.** **Comentário:** sem comentário. **Estado:** `PO_APPROVED_BUSINESS_DECISION / COORDINATION_RATIFICATION_PENDING`.

**Regra funcional aprovada:** se uma PRC candidata à conclusão contém uma bandeira `OPEN` para `recordId + targetKey` que já está ocupado por outra `OPEN` no produto acompanhado (ou por outra bandeira elegível na mesma conclusão), **bloquear a conclusão da solicitação** até tratamento explícito, autorizado e auditável da duplicidade. O bloqueio **não publica snapshot técnico, não cria Vn, não incorpora bandeira, não atualiza ponteiro de versão, não marca pedido como concluído e não produz conclusão parcial**. A solicitação permanece no estado anterior compatível com seu contrato, com erro de conflito e indicação do alvo quando permitido por AuthZ. Não fundir, resolver, remover, reabrir ou descartar flags automaticamente.

**Compatibilidade com decisões anteriores:**
- **ADR-03:** mantém invariante de **no máximo uma OPEN simultânea por produto/alvo**; impedir duplicidade inclusive concorrência e flags OPEN concorrentes da própria solicitação.
- **CR-07:** bandeiras RESOLVED não reabrem; ocorrência encerrada permanece histórica; se houver reincidência após encerramento, criar novo ID, respeitando unicidade OPEN.
- **CR-08:** durante associação de OPEN legadas na V1, colisões permanecem em fila de exceção **sem associação automática**; se a colisão pertence ao conjunto da solicitação que está tentando concluir, **CR-10 bloqueia essa conclusão inteira**. Backfill histórico offline não reabre/conclui PRC e não deve ser confundido com o fluxo transacional de conclusão.
- **CR-09:** solicitações em andamento não alteram produto. Apenas uma conclusão válida pode promover dados e bandeiras, mas somente se todos os gates forem satisfeitos; o conflito é falha de pré-condição e impede commit integral.
- **CR-02/03/04/05/06 + ADR-05:** a primeira V1, o diff real Vn+1 e o no-op só se efetivam se não houver conflito pendente; no-op não é motivo para ignorar duplicidade de OPEN.

**Tratamento do conflito antes de nova tentativa:** exige ação humana/autorizada conforme os contratos vigentes das bandeiras request-local e product-tracking; a escolha do mecanismo (retirar bandeira duplicada da solicitação, encerrar ocorrência existente quando tecnicamente cabível, ou outro fluxo) **não foi autorizada automaticamente** por CR-10. Toda ação deve respeitar CR-07/ADR-04 e trilha histórica. Revalidar permissões, flags, revisão e versão com locking/CAS no retry; não contar com checagem apenas no frontend.

**Critérios de aceite:** `CR10-AC01` duas OPEN mesmo produto/alvo antes de complete → 409/erro de conflito contratual, PRC não conclui; `CR10-AC02` snapshot, current_revision, association e status de conclusão permanecem inalterados; `CR10-AC03` caso no-op também bloqueia; `CR10-AC04` resolução autorizada do conflito seguida de retry idempotente pode concluir; `CR10-AC05` duas conclusões concorrentes não publicam duas OPEN; `CR10-AC06` campos de erro não vazam dados de bandeiras sem AuthZ; `CR10-AC07` nenhuma bandeira é automaticamente resolvida/removida/reaberta/fundida; `CR10-AC08` coexistência com legadas e backfill preserva requests concluídos.

**Status de execução:** `TEST_NOT_RUN`. Nenhum código, migration, deploy ou alteração de schema autorizado. O contrato transacional exige ratificação pela Coordination.


## 17. Deliberação complementar do PO — CR-11: trazer a bandeira existente para a solicitação (13/11/2026)

**Escolha expressa:** **Outra proposta**. **Comentário literal do PO:** “quando vier a solciitação de alteração do campo já trás a bandeira, e se preciso o analista até resolve a solicitação. Geralmente é isso que vai acontecer.” **Status:** `PO_APPROVED_BUSINESS_INTENT / COORDINATION_RATIFICATION_PENDING`.

**Interpretação funcional fiel à proposta:** ao iniciar/abrir uma solicitação PRC de alteração de campo ou atributo de vínculo que **já possua bandeira OPEN no produto**, a interface da **solicitação** deve mostrar essa bandeira preexistente por `flagId`, com estado, alvo e histórico autorizado. O analista utiliza essa informação no atendimento e pode encaminhar/concluir a própria solicitação conforme o rito PRC; **não criar nova bandeira automaticamente** para o mesmo `recordId+targetKey`. O PO falou em “resolve a solicitação”: **não presumir que isso equivale a RESOLVE automático da bandeira**. A bandeira só muda de estado mediante ação expressa e autorizada, obedecendo ADR-04/CR-07 e o gate CR-09. Caso haja intenção explícita de resolvê-la no atendimento, o efeito sobre o produto deve ocorrer somente após conclusão válida, conforme contrato a ratificar.

**Compatibilidade com CR-09:** `request-local` pode **ler e exibir** (com AuthZ) bandeiras OPEN já publicadas no produto, mas **não altera** sua presença/estado nem o snapshot técnico do produto enquanto a PRC estiver em andamento. A leitura da bandeira existente não transforma a solicitação em versão. Mudanças propostas e ações pendentes ficam no escopo do request até conclusão validada.

**Compatibilidade com CR-10:** visualizar/referenciar a bandeira já OPEN **não é uma segunda OPEN**, logo **não há conflito** quando a solicitação apenas referencia o `flagId` existente. Se alguém tentar criar efetivamente **outra** bandeira OPEN para mesmo alvo, ou houver identidade/associação duvidosa, mantém-se o **bloqueio integral da conclusão** até resolução autorizada, sem publicação parcial. O fluxo preferencial evita a duplicidade antes que seja criada: o campo já exibe o aviso existente durante o atendimento, com possibilidade de acompanhamento da solicitação sem novo `flagId`.

**Compatibilidade ADR-03/ADR-04/CR-07:** reutiliza-se o `flagId` existente **por referência**, não fusão/clone; no máximo uma OPEN por alvo. Uma bandeira RESOLVED não reabre; reincidência nova após encerramento exige novo ID. RESOLVED aparece na revisão de resolução e não nas seguintes; REMOVED desaparece na revisão da remoção. Ações durante request que pretendam alterar estados do produto ficam **pendentes até conclusão**, não produzem Vn técnica.

**Exemplo:** produto V3 tem F101 OPEN no campo X; nova PRC para X abre e **mostra F101**. Analista trata e conclui solicitação: se nenhuma ação sobre a flag for requerida, F101 segue OPEN; se houver RESOLVE explicitamente autorizada como parte da conclusão válida, F101 fica RESOLVED na V3 (quando no-op) ou na V4 (quando houver diff técnico), conforme revisão vigente ao publicar, sem criar revisão exclusivamente pela flag. Se um segundo flagId OPEN F202 for criado no request para X, a conclusão é bloqueada por CR-10.

**Pontos técnicos pendentes de ratificação:** resolução de uma flag de produto referenciada por request sem mutação antecipada; desenho de intents `reference_existing` vs `create_new` vs `resolve_existing`/sem ação; permissões de leitura e ação cross-request; transação e evento no fechamento; estado da flag se PRC é cancelada/rejeitada; conciliação de mudança de alvo/status entre abertura e conclusão; impacto do endpoint legado D16 e seus consumers. Não assumir que o contrato/UX atual já suporta isso.

**AC CR11:** (01) PRC do campo X carrega F101 OPEN existente, autorizada; (02) referência a F101 não duplica flag nem bloqueia CR-10; (03) produto mantém F101 e V3 inalterados enquanto pedido aberto; (04) conclusão sem intenção de RESOLVE preserva OPEN; (05) intenção de resolução autorizada só produz efeito no corte de conclusão válida e estado por ADR-04; (06) duplicata F202 OPEN bloqueia toda conclusão por CR-10; (07) acesso sem permissão não expõe F101; (08) cancelamento/rejeição não altera estado no produto; (09) concorrência/retry são idempotentes.

**Sem código, migrations, alterações de runtime ou deploy.** Esta interpretação preserva o sentido do comentário do PO sem transformar “resolver solicitação” em ordem implícita de encerrar bandeira.


## 18. Deliberação complementar do PO — CR-12: resolução explícita pela Engenharia (13/11/2026)

**Escolha expressa:** **A — Analista decide explicitamente; sem ação a bandeira permanece aberta.** **Comentário:** sem comentário. **Status:** `PO_APPROVED_BUSINESS_DECISION / COORDINATION_RATIFICATION_PENDING`.

**Regra funcional:** a alteração técnica confirmada de um campo sinalizado **não implica resolução automática** de sua bandeira. Ao concluir a PRC, o analista pode manifestar **intenção explícita de RESOLVE**, com justificativa, sujeita à autorização e às validações do owner. Na ausência dessa intenção, a mesma ocorrência OPEN segue aberta no produto (e é propagada em revisões seguintes conforme ADR-04). A intenção não altera o produto durante o andamento da solicitação. Se a conclusão não for validada/autorizada, **não publicar nem a alteração técnica nem a resolução**.

**Compatibilidade:**
- **CR-09:** a solicitação só altera o produto após conclusão validada; RESOLVE é intenção request-local até esse gate. Conclusão pode gerar V1 (primeiro acompanhamento), Vn+1 por diferença real ou no-op sem nova Vn.
- **CR-10:** duas ocorrências OPEN concorrentes para o mesmo produto/alvo continuam bloqueando **toda conclusão**; marcar RESOLVE não é atalho silencioso para contornar conflito. Revalidar unicidade e estado na transação.
- **CR-11:** o analista vê a flag OPEN já existente no campo e usa **referência ao mesmo flagId**, sem criar uma nova ocorrência. “Resolver/concluir solicitação” continua distinto de marcar bandeira como resolvida.
- **ADR-04:** se RESOLVE explícito é publicado ao completar enquanto V4 é a revisão vigente, a bandeira aparece **RESOLVED na V4**, não em V5+. Se a própria conclusão cria V5 por diferença técnica, a resolução aparece na **V5**; versões anteriores preservam sua projeção do contexto histórico. REMOVED continua operação distinta e não faz parte de RESOLVE.
- **CR-07:** nenhuma reabertura de RESOLVED; reincidência futura exige novo flagId.

**Regras de contrato a ratificar:** ação explícita no request (flagId, expectedFlagVersion, justificativa, ator, autorização, timestamp/eventId), validação de que ocorrência está OPEN e pertence ao produto/alvo autorizado, ordem transacional do snapshot e evento, revisionContext pós-conclusão, idempotência/CAS, comportamento quando outra ação alterou a flag antes do commit, limites de autorização para RESOLVE e política de justificativa. **A escolha do PO não define automaticamente o texto obrigatório exato de justificativa ou o critério de aprovação técnica**; o owner deve fixá-los.

**AC:** `CR12-AC01` PRC modifica campo com OPEN mas sem intenção → flag segue OPEN; `CR12-AC02` RESOLVE explícito válido é registrado só na conclusão; `CR12-AC03` no-op V4 + RESOLVE → RESOLVED em V4, sem nova versão; `CR12-AC04` diff gerando V5 + RESOLVE → RESOLVED em V5, não V4; `CR12-AC05` falha/403/409/cancelamento não altera produto/flag; `CR12-AC06` colisão OPEN CR-10 bloqueia conclusão mesmo com intenção de RESOLVE; `CR12-AC07` retry não duplica evento nem revisão; `CR12-AC08` audit trail registra ação, justificativa, revisão e evidência.

**Nenhum código, migration, alteração de schema ou deploy.** Contratos e transação sujeitos à Coordination.
