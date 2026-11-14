# PRC-TRACK — Fonte canônica de regras, conflitos resolvidos e plano único

> **Revisão documental:** 2026-11-13. **Status:** `PO_APPROVED_BUSINESS_RULES / ARCHITECTURE_DECISION_REQUIRED / IMPLEMENTATION_NOT_STARTED`. **Este documento substitui as interpretações funcionais conflitantes dos textos históricos listados na seção 8; não substitui código, contrato ratificado, owner nem fonte oficial.**
>
> **Política editorial:** uma regra funcional por assunto, sem abrir nova pergunta para algo já decidido. Evidência de código = `PROVEN_CODE`, não prova de runtime; planos = `TARGET`; validações = `TEST_NOT_RUN` enquanto não executadas. O registro integral e as falas originais do PO ficam em [G1 PO decisions](./PRC-TRACK-G1-PO-DECISIONS-2026-11-13.md).

## 1. Síntese vinculante (regras de negócio decididas)

**Objeto e fronteiras.** A superfície é o **Portal Engenharia**, na ferramenta PRC **Controle e Cadastro de Produtos**. A **Engineering API / domínio PRC** gerencia solicitações, fichas técnicas acompanhadas, histórico e bandeiras. O **TOTVS** conserva a autoridade dos dados oficiais do produto. **Keycloak** fornece identidade, **Core** provê acesso/RBAC vigente, **Plugin UI** componentes visuais e **EVA** apenas interpretação assistida. Produtos acompanhados são identificados pela identidade existente `official_source+official_product_code`, sem filial no escopo declarado pelo PO; confirmar invariantes nos contratos existentes, não inventar nova chave.

**Versionamento.**
1. **Solicitação PRC não é versão.** Durante uma solicitação não concluída, nenhum campo técnico ou bandeira pendente é publicado no produto acompanhado.
2. A **primeira conclusão validada** do produto sem histórico gera **V1 baseline de acompanhamento**, mesmo sem diferença técnica; não significa criação do produto no TOTVS.
3. Em produto já acompanhado, **só diferença técnica real confirmada no conjunto de campos/vínculos PRC** cria Vn+1. Conclusão verificada sem diff técnico = no-op auditado na Vn atual.
4. Cada Vn é **ficha consolidada** dos campos registrados/acompanhados na Engineering API e dos vínculos de fornecedores autorizados, com schema/cobertura/proveniência; não é só delta nem um espelho completo do TOTVS. Revisões técnicas publicadas são imutáveis.
5. **UPDATE parcial:** campos e fornecedores omitidos preservam os valores e proveniências da base anterior; aplicar somente alterações, inclusões ou exclusões explícitas validadas. Chave do fornecedor: `supplierCode+store`, mais atributo quando alvo de flag/diff. `null`/vazio ambíguo não é CLEAR; limpeza exige intenção explícita em campo que a permita e verificação adequada. Não presumir REMOVE de vínculo oficialmente suportado.
6. Cada valor acompanhado declara **origem e confirmação** (confirmado na fonte no contexto apropriado, herdado de valor previamente confirmado, registrado sem comprovação individual, desconhecido/não aplicável). Não transformar campo herdado em “reverificado” automaticamente; falha do gate de conclusão oficial impede publicação. Só atualização de metadados de evidência não gera Vn técnica.

**Bandeiras — controle simples da Engenharia.**
7. Adicionar, consultar, resolver e remover são **operações do fluxo da Engineering API**, usando **acesso já autorizado ao Portal Engenharia** e validação backend-first dos direitos existentes. **Sem novos papéis, permissões específicas, aprovadores, fluxo de aprovação ou justificativa formal adicional criada para bandeiras.** Registrar evento mínimo auditável (identidade, ator, instante, alvo, revisão de contexto e origem); não inventar workflow novo. O antigo texto exigindo aprovação especial e justificativa mandatória é `SUPERSEDED`.
8. Uma **ocorrência** tem seu `flagId` próprio. Somente uma **OPEN simultânea por produto+alvo**. RESOLVED/REMOVED são finais; **não reabrir**. Recorrência posterior usa **novo flagId**. Nunca clonar uma ocorrência a cada revisão.
9. **Visibilidade por revisão e evento:** F criada em V3 → OPEN em V3 e versões seguintes enquanto aberta. **RESOLVE enquanto V4 vigente → RESOLVED verde visível em V4, ausente de V5 em diante**. **REMOVE enquanto V4 vigente → ausente já na V4 e em todas as posteriores**. V3 conserva OPEN. RESOLVE/REMOVE isoladamente não cria revisão técnica. Histórico de eventos permanece auditável, inclusive quando a bandeira deixa de aparecer.
10. A PRC de alteração **apresenta por referência** a bandeira OPEN já existente no campo/atributo, sem criar duplicata. Resolver ou concluir a **solicitação** não resolve automaticamente a **bandeira**. O analista pode escolher explicitamente RESOLVE; **sem ação, permanece OPEN**. Qualquer intenção de alterar o produto durante uma PRC fica request-local até conclusão validada; resolução ao completar usa o contexto de revisão final daquela conclusão (no-op = Vn vigente; diff = Vn+1 recém-criada).
11. **Bandeiras criadas na PRC ainda em andamento** permanecem na própria solicitação, não aparecem no produto. **Somente após conclusão válida**, flags que continuarem OPEN, com identidade e alvo inequívocos e sem conflito, podem integrar a projeção do produto. Bandeiras encerradas **antes** da conclusão não são incorporadas; permanecem no histórico da solicitação.
12. Ao iniciar V1, flags **legadas OPEN** somente podem ser incorporadas se **produto/alvo forem comprovados E solicitação de origem estiver concluída/verificável**. Encerradas, ambíguas, sem alvo, de solicitação aberta/cancelada/status incerto ou em colisão não entram automaticamente. Preservar histórico e colocar exceções para revisão do owner, não atribuir por inferência.
13. **Conflito real de duas OPEN no mesmo produto+alvo na conclusão de nova PRC = bloqueio integral**. Sem concluir PRC, sem publicar campo/snapshot, sem Vn e sem integrar bandeiras. A simples referência à ocorrência já aberta **não constitui** segunda OPEN e não bloqueia. Não mesclar ou encerrar automaticamente. Backfill offline de requests históricos concluídos com colisão fica pendente de revisão, sem desfazer retroativamente o status dessas solicitações.

**Experiência e entrega.**
14. Preservar a UX aprovada: **uma** top bar e hero PRC, segmentos `Solicitações | Produtos acompanhados`, lista por produto, detalhe com **Ficha técnica | Versões**, fornecedores em tabela, timeline de versões **acima** da comparação, diff entre quaisquer Vx×Vy; responsividade e acessibilidade. Reusar `PrcTechnicalSheetView` e componentes do **Plugin UI**. Sem nova app/aba geral nem edição direta de TOTVS.
15. Diff entre fichas Vx×Vy é **calculado no backend Engineering API**. Eventos de bandeira não são mudanças do cadastro técnico. Histórico técnico e histórico de solicitações são coisas diferentes.
16. Antes do novo frontend U1–U3: **migração/reuso do Plugin UI comprovados** e **todas as rotas necessárias ao escopo B1–B3 validadas na homologação autorizada** (positivos/negativos, concorrência, idempotência, AuthZ). Não confundir 100% de rotas funcionais com cobertura de testes 100%. QA visual das páginas novas só após implementadas.

## 2. Casos de teste que definem a semântica

| ID | Entrada | Saída obrigatória |
|---|---|---|
| R01 | Primeiro UPDATE matched sem mudança, produto sem histórico | V1 baseline; provenance e requestId; não dizer “produto criado no ERP” |
| R02 | Segundo UPDATE matched no-op | Continua V1; solicitação concluída auditada |
| R03 | UPDATE parcial muda descrição | Nova Vn se diff; demais campos/fornecedores herdados com origem preservada |
| R04 | Campo omitido ou vazio ambíguo | Omitido preserva; vazio ambíguo nunca limpa silenciosamente |
| R05 | CLEAR explícito permitido e confirmado | Somente alvo alterado; Vn+1 se diferença real |
| R06 | F criada V3, RESOLVE V4 | F OPEN V3; RESOLVED V4; ausente V5+ |
| R07 | F criada V3, REMOVE V4 | F OPEN V3; ausente V4+ |
| R08 | F RESOLVED em V4; problema reincide V6 | Novo flagId em V6; nenhuma reabertura ou reescrita de V4 |
| R09 | PRC aberta sobre X tem F101 OPEN no produto | PRC mostra referência F101, produto permanece com F101 OPEN |
| R10 | PRC concluída matched/no-op, flag nova OPEN elegível | Mesma Vn; só após conclusão OPEN é associada |
| R11 | PRC conclui com intenção RESOLVE F101 e diff técnico cria V5 | F101 RESOLVED V5; revisão anterior preservada |
| R12 | PRC resolve flag local antes de completar | Flag não é incorporada ao produto |
| R13 | Nova PRC tenta publicar F202 OPEN onde F101 OPEN já existe | Falha de conclusão inteira; nenhum efeito parcial no produto/status |
| R14 | V1 com flag antiga OPEN, mas PRC origem não concluída | Não incorporar; manter isolada da ficha |
| R15 | V1 com legada OPEN de PRC concluída, alvo/identidade comprovados | Associar uma ocorrência sem clone ou nova Vn técnica |
| R16 | Ação de flag por usuário sem acesso existente | Backend nega, sem criar novo papel/approver; nenhum vazamento |
| R17 | Concluir PRC sem intenção de resolução | F101 permanece OPEN ainda que campo tenha mudado |
| R18 | HML concorrência, retry, flag altera estado durante complete | CAS/idempotência, sem dupla OPEN, dupla revisão ou sucesso parcial |

Exemplos são **TARGET de aceite**, não evidência de testes executados.

## 3. Matriz de inconsistências identificadas e tratamento

| IC | Contradição/inconsistência documental | Correção canônica | Tratamento |
|---|---|---|---|
| IC-01 | “Cada conclusão gera revisão”/“UPDATE seguinte gera V2” | V1 inaugural; V2+ **só diff real**, no-op sem incremento | `SUPERSEDED` |
| IC-02 | “Snapshot oficial completo TOTVS” versus campos da Engineering API | **Ficha PRC consolidada**, evidências/coverage por campo; não declarar captura integral oficial | `SUPERSEDED` |
| IC-03 | “Bandeira única para sempre por alvo” versus reincidência | Uma OPEN simultânea, **novo ID por nova ocorrência** após encerramento | `SUPERSEDED` |
| IC-04 | REOPEN como ação permitida / evento TARGET | **REOPEN proibido no produto acompanhado**; rota D16 legada existente precisa plano de compatibilidade | `SUPERSEDED + CODE_GAP` |
| IC-05 | RESOLVED desaparece da revisão corrente | **RESOLVED é visível na revisão do evento**; REMOVED desaparece nessa revisão | `SUPERSEDED` |
| IC-06 | Estado histórico “no corte de publicação Vn” ignora eventos posteriores enquanto Vn vigente | Distinguir **snapshot técnico de publicação** e **projeção da vigência de Vn por eventos**. Não reescrever snapshot; exibir RESOLVED na revisão vigente ao resolver | `CONTRACT_DETAIL_PENDING` |
| IC-07 | Flags do request podem modificar produto antes de concluir | **Somente conclusão validada publica**; request referencia OPEN existente para leitura sem criar/mutar | `SUPERSEDED` |
| IC-08 | CR-08 migra toda flag OPEN sem qualificar PRC origem | Exigir **PRC origem concluída** para associação automática | `SUPERSEDED` |
| IC-09 | CR-10 proíbe conclusão mesmo quando há só referência a flag existente | **Referência não é duplicata**; bloqueio só com **duas ocorrências OPEN distintas** | `CLARIFIED` |
| IC-10 | Tratar conflito por segunda aprovação, automerge, outbox parcial | Sem nova aprovação, sem automerge, **bloqueio integral no complete**; caso histórico em quarentena | `SUPERSEDED` |
| IC-11 | Aprovação especial/justificativa obrigatória/nova permissão para flags | **Acesso vigente ao Portal Engenharia** e auditoria simples na Engineering API; backend continua enforcing | `SUPERSEDED` |
| IC-12 | Confusão entre concluir solicitação e resolver bandeira | **Ação RESOLVE explícita**; caso concluído sem ação mantém OPEN | `CLARIFIED` |
| IC-13 | “CR-06/CR-07” usados no documento inicial como identificadores de contratos API/HML e, depois, como IDs de decisões PO | **IDs de namespaces diferentes**: `ADR-06/ADR-07` para macrodecisões; `CR-02…CR-13` para deliberações do PO; `API-Cxx` apenas para tabela de endpoints, `GATE-HML` para rollout. Evitar CR-06/07 nu em tabelas antigas | `NAMING_DRIFT` |
| IC-14 | Requisitos visuais de reabertura, botões permitidos e componentes legados que contêm reopen | Retirar `reopen` do **TARGET** do novo produto; inventariar consumidores D16 antes de mudar código | `SUPERSEDED + CODE_GAP` |
| IC-15 | “Sem regras adicionais” versus necessidade de AuthZ backend-first | **Reusar acesso existente**, sem criar papéis; Core/Keycloak e Domain API continuam autoridade | `CLARIFIED` |
| IC-16 | Empilhar emendas CR-02…CR-13 após trechos antigos sem consolidar | Este documento é **fonte canônica de regra funcional**; históricos são evidência/auditoria, não checklist de implementação literal | `RESOLVED_DOC_GOVERNANCE` |

**Atenção IC-06:** definir projeção temporal precisa não é nova decisão de produto. O PO já fixou o que aparece na revisão da ação. Cabe ao owner entregar o contrato técnico que realize isso; somente impossibilidade real deve voltar à Coordination.

## 4. Plano central de execução — sem perguntas redundantes

| Gate | Escopo | Owner | Entregável e saída esperada | Estado |
|---|---|---|---|---|
| **G0** | Revalidar HEAD/status, authorities, estado do PRC, Plugin UI e rotas existentes | Execução Engenharia + Coordination | Evidence ledger com SHA, consumers e diffs; gaps concretos | `PARTIAL / TO_INVENTORY` |
| **G1** | Ratificar **este conjunto fechado de regras** e apenas os contratos necessários, usando Core/Domain AuthZ existentes | Coordination + Engenharia owner | Registro `APPROVED/REVISE/REJECT` dos contratos com owners, limites e rollback | `ARCHITECTURE_DECISION_REQUIRED` |
| **B1** | V1 baseline, no-op, CR-02 ficha consolidada e cobertura, UPDATE parcial, diff real, integração `complete_request` | Engineering API | Código bounded + testes SHA + auditoria; nenhuma alteração não autorizada do TOTVS | `PLANNED` |
| **B2** | Flags produto: uma OPEN/target; request-local vs produto, referência read-only em PRC, ciclo OPEN→RESOLVED/REMOVED, CR-08 legado, conflito atomicidade CR-10 | Engineering API | Contratos/implementação segura + compatibilidade D16 + testes | `PLANNED` |
| **B3** | API de lista, snapshots, flags em corte de revisão e comparação server-side | Engineering API | DTOs/erros/AuthZ/paginação, contract tests; cobertura incomparável explícita | `PLANNED` |
| **G-HML** | Homologar Plugin UI + todos endpoints de B1–B3 com acesso legítimo | QA + owner Engenharia | Evidências PASS no SHA, casos R01–R18 e negativas; sem bypass de acesso | `PENDING` |
| **U1** | Mesma página PRC, segmentos e lista produtos acompanhados | Portal Engenharia MFE + Plugin UI | UX P1 aprovada, regressão queue, navegação | `PLANNED` |
| **U2** | Ficha técnica, fornecedores, bandeiras por contexto e read/reference em PRC | MFE + Plugin UI | UX P2, sem lógica autoritativa no frontend | `PLANNED` |
| **U3** | Timeline acima de comparação Vx×Vy, estados e responsividade | MFE + Plugin UI | UX P3 e QA 320–1920, light/dark | `PLANNED` |
| **Q/D** | E2E, negativa/concorrência, rollout e rollback | QA + owners | Evidence ledger + readiness e deploy quando autorizado | `PENDING` |

**Contrato antes do código:** confirmar owner/consumer, AuthN/AuthZ existente, schema/DTO, erros, concorrência e pós-condições, compatibilidade, observabilidade, rollback e testes. **Abstraction Gate:** reutilizar records/revisions, flags/D16 e UI kit onde houver equivalentes; não criar BC, permission layer, policy engine ou approval workflow novos para uma necessidade simples.

## 5. Bloqueadores técnicos reais a resolver pela Coordination (sem retornar ao PO por preferência)

| Nº | Bloqueador técnico / evidência | Ação de Coordination |
|---|---|---|
| T01 | `_build_snapshot` no service PRC foi inventariado como cópia de `draft_data`; não prova cobertura/proveniência CR-02/04 | Ratificar fonte por campo, field catalog, versão do schema, read-back, merge e tratamento legado |
| T02 | `complete_request` do repo atualmente insere revisão a cada matched; conflita com V1 baseline + no-op subsequente | Ratificar transação/caminhos idempotentes com CAS e ledger de PRC sem revisão |
| T03 | Flags D16 são predominantemente request-scoped com endpoint `reopen`; produto requer ocorrência por record/target e sem REOPEN | Inventariar consumers, compatibilidade/migração e containment da rota legada |
| T04 | Flags de request e estado do produto não devem se misturar antes de complete; CR-10 exige bloqueio sem publicação parcial | Definir fronteira transacional, validação/captura de estado, falhas externas e compensação |
| T05 | V4 pode exibir RESOLVED evento ocorrido durante vigência, sem mudar snapshot técnico de publicação | Ratificar API de projeção temporal por vigência de versão e eventos/ordem; não pedir outra escolha visual |
| T06 | Legadas OPEN pré-V1 podem ter vínculo, status de origem ou alvo ambíguos e colisões | Plano conservador de associação idempotente com exceções e rollback |
| T07 | Plugin UI extraction ainda não tem aceitação visual e evidência de export final confirmada neste dossiê; HML ainda não executada | Fechar G0 com SHA, testes e acessos autorizados, validar G-HML |
| T08 | IDs CR-06/CR-07 do primeiro contrato colidem com decisões de mesmo nome posteriores; AC originais contradizem PO | Remapear identificadores em contratos e cases; **usar R01–R18** como testes canonizados |

Esses pontos não são convite a novas rodadas de perguntas de negócio: os contratos devem cumprir as regras da seção 1. **Se a solução técnica exigir novo owner, BC, source of truth ou autoridade, registrar `ARCHITECTURE_DECISION_REQUIRED` e retornar à Coordination.**

## 6. Critérios de saída e não alegações

- `PO_APPROVED` = intenção/regra de produto definida; **não** representa ratificação arquitetural.
- `PROVEN_CODE` = arquivo lido no GitHub, sujeito a HEAD e teste; **não** prova rota em produção/HML.
- `G1 PASS` só com decisão formal de Coordination e contratos acordados.
- `G-HML PASS` só com API e Plugin UI verificados em homologação autorizada, SHA e evidências de cenário.
- `U1/U2/U3 PASS` só com browser QA e consumer tests.
- No estado deste documento: **nenhuma migration, mudança de código, execução de testes ou deploy foi realizada por esta revisão documental.**

## 7. Regras para decisões futuras

1. **Antes de perguntar, consultar este documento e a decisão original.** Não reabrir CR-02…CR-13/ADR-01…07 só porque algum texto antigo conserva uma dúvida.
2. **Não inventar microdecisões** (novo papel, aprovador, justificativa formal, eventos extras) quando comportamento e permissões existentes bastam.
3. Identificar dúvida nova como `CONTRACT_DETAIL` (owner implementa) ou `BUSINESS_CONFLICT` (evidência concreta contradiz decisão). Somente conflito material sem interpretação possível deve voltar ao PO.
4. Alterar primeiro **esta fonte canônica**; manter emendas históricas por rastreabilidade, com link e nota de supersession. Não reproduzir a mesma regra em múltiplos documentos sem referência.
5. Qualquer execução deve citar SHA e testes no SHA. Sem evidência, status `PENDING/TEST_NOT_RUN`.

## 8. Relação com documentação histórica (não apagar passado)

- [Decisões PO completas](./PRC-TRACK-G1-PO-DECISIONS-2026-11-13.md) — **registro de origem e evolução**; texto pré-emenda pode divergir; seção 1 deste documento prevalece.
- [Propostas de contrato G1](./PRC-TRACK-G1-CONTRACT-RATIFICATION-PROPOSAL.md) — **arquivo de propostas e alternativas históricas**; somente o plano canônico é referência funcional atual, sujeito a ratificação técnica.
- [Plano inicial de implementação](./PRC-TRACKED-PRODUCTS-IMPLEMENTATION-PACKAGE-PLAN.md) — matriz ampla P1–P3, G0–D, AC antigos; usar os gates e R01–R18 deste plano quando divergir.
- [Baseline de regras de produto](./PRC-PRODUCT-TRACKING-VERSIONS-TRANSVERSAL-FLAGS-DECISIONS.md) — baseline anterior, não fonte mais recente sobre no-op, reabertura ou origem de campos.
- [Especificação visual](./PRC-PRODUCT-TRACKING-FRONTEND-VISUAL-SPEC.md) — referência para **layout UX aprovado P1/P2/P3**, não autoridade sobre REOPEN ou momento de publicação.
- [Inventário visual e wireframes](./PRC-TRACKED-PRODUCTS-UI-COMPONENT-INVENTORY-RESPONSIVE-WIREFRAMES.md) — evidências UI e TARGET dimensional.
- [G0/G1 inventory](./PRC-TRACK-G0-INVENTORY-G1-COORDINATION-DECISION-PACKET.md) — histórico das primeiras hipóteses de G1, superadas quando contradizem CR-02…CR-13.
- [Migração Plugin UI](./PRC-PLUGIN-UI-COMPONENT-EXTRACTION-MIGRATION-PLAN.md) — plano técnico, mas não autoriza reabertura de bandeira no produto novo.


## 9. Ordem de execução aprovada pelo PO — backend de produto → backend de bandeiras → frontend completo

> **Direção de execução atual (prevalece sobre a decomposição antiga):** iniciar implementação com **todos os contratos de produto acompanhado**, só depois **todos os contratos de bandeiras**, e finalmente **frontend completo**, com rotas backend aceitas. Ambientes de teste: **DEV** e **homologação**, com **multiusuários em HML**. **Produção somente após testes, revisão, aprovação e deploy governado**; não confundir autorização para iniciar implementação com autorização para publicar mudança ainda não testada.

### 9.1 Inventário de código efetuado antes da implementação

| Contrato | Código existente observado no GitHub | Lacuna de produto acompanhado |
|---|---|---|
| `GET /v1/product-registration/technical-records/{record_id}` | Rota/service/repository existentes | DTO é registro PRC, não ficha consolidada CR-02/04/05/06 confirmada |
| `GET /.../{record_id}/revisions` | Rota/service/repository existentes | Indexar baseline e deltas reais, associar no-op e provenance |
| `GET /.../{record_id}/revisions/{revision_number}` | Rota/service/repository existentes | Cobertura e fonte de valores do snapshot precisam evoluir |
| `GET /v1/product-registration/technical-records` | **Não identificado** no conjunto de rotas PRC lido | Listagem paginada de **produtos acompanhados**, não solicitações |
| `GET /.../{record_id}/comparison?from=&to=` | **Não identificado** | Diff server-side Vx×Vy por campo, cobertura e fornecedor+loja |
| `complete_request` | Existente; adapter Postgres insere revisão em toda conclusão | V1 baseline e V2+ somente com diff real; no-op auditado, transação e flags na conclusão |
| Flags D16 por `requestId` | Rotas create/update/resolve/reopen/delete e dados request-scoped existem | Produto exige associação após conclusão, unicidade OPEN por record+target, REOPEN proibido e projeção por revisão |

**Esta tabela descreve evidência de código, não runtime.** Verificar HEAD, tests e contratos do owner novamente em cada etapa.

### 9.2 Fase P-BE — rotas e regras de PRODUTO (primeiro)

**P-BE-00:** HEAD/status/owners e contrato de request/response/errors/AuthN/AuthZ antes de escrever; preservar módulos e consumidor PRC atual.

**P-BE-01:** adicionar lista paginada autorizada `GET /v1/product-registration/technical-records` (distinta da fila de requests), com filtros `search`, ordenação determinística, page/pageSize, identidade oficial sem filial. Não incluir flags até contrato B2; `openFlagCount` opcional e não inventado. Resposta só de records acompanhados, com `recordId,officialSource,officialCode,currentRevisionNumber,updatedAt` e informações adicionais somente quando houver fonte contratada. **Novo endpoint não altera schema nem snapshots existentes.**

**P-BE-02:** corrigir pipeline de conclusão e persistência para V1 inicial + consolidação de UPDATE parcial CR-02/04/05/06, provenance por campo, supplierCode+store, diferença canônica real e no-op sem revisão; preservar gate `matched`, AuthZ, ledger e consistência transacional, migrations oficiais do owner se indispensáveis e ratificadas.

**P-BE-03:** estabilizar leitura de ficha/revisões, DTO de cobertura, origem e causalidade; assegurar que legado incompleto não se apresente como confirmado.

**P-BE-04:** comparação `GET /v1/product-registration/technical-records/{record_id}/comparison?from=Vx&to=Vy` por backend, campos/vínculos com normalização e `incomparable` quando coverage insuficiente; auditoria read-safe. Não misturar eventos de bandeira com diff técnico.

**Gate produto:** `P-BE-01..04` testados em DEV e/ou HML com matriz de autorização e efeitos negativos, idempotência e concorrência. *Nenhum frontend novo nesta fase.*

### 9.3 Fase F-BE — rotas e regras de BANDEIRAS (depois de produto)

**F-BE-01:** inventário D16 e compatibilidade; modelo da ocorrência única e até uma OPEN por produto+alvo; impedir reabertura no contrato novo sem quebrar consumidor legado silenciosamente. Sem papéis/aprovadores/grants novos.

**F-BE-02:** leitura do estado atual, estado por revisão e histórico de flags no produto; resolver em Vn = RESOLVED na Vn e ausente na próxima, remover em Vn = ausente já nela; eventos independentes de versões.

**F-BE-03:** PRC de UPDATE lê a flag OPEN existente por referência; enquanto request aberta nenhuma mudança de flag é publicada no produto. Ao completar com verificação matched, promover só flags locais OPEN elegíveis, executar intents expressas de RESOLVE de forma consistente; duplicata OPEN bloqueia conclusão integral (CR-10), e não apenas associação. Não resolver automaticamente por mudança técnica.

**F-BE-04:** CR-08 legado: associar à primeira V1 somente OPEN provenientes de requests concluídos e comprovadamente vinculados; ambiguidade/colisão não migra automaticamente; compatibilidade reversível e teste de reexecução.

**Gate bandeiras:** executar DEV e HML incluindo **dois ou mais usuários autorizados** em concorrência (CREATE/RESOLVE/REMOVE, complete/no-op, disputas por target), e usuários negados/fora de escopo. Exigir evidência SHA, idempotência, ausência de novo role e integridade da história.

### 9.4 Fase FRONT — frontend completo só depois dos dois gates backend

- **U1:** PRC existente com segmentos `Solicitações | Produtos acompanhados`, listagem paginada de produtos e filtro/URL. Uma topbar/hero.
- **U2:** ficha consolidada, fornecedores em tabela, seletor de revisão, flags contextuais já governadas no backend; reutilização exclusiva de componentes existentes/extraídos do Plugin UI.
- **U3:** timeline de versões acima da comparação Vx×Vy, responsável/dados de solicitação e indicadores de origem/comparabilidade; responsividade 320–1920, acessibilidade e temas.
- **FRONT-GATE:** testes de integração e E2E HML com multiusuários, regressão PRC/My Requests, permissões, navegadores, paths e screenshots; Plugin UI remote aceito.

### 9.5 Deploy produtivo

**Ordem rígida:** DEV (quando disponível) → HML com acessos autorizados e multiusuários → evidências `PASS` + revisão técnica/Coordination → deploy produtivo governado do backend → smoke/monitoramento → deploy do frontend somente quando os dois backends estiverem contratados e funcionais → smoke/rollback. **Não fazer deploy automático em produção apenas porque passou teste local.** Estado atual: `IMPLEMENTATION_STARTED` apenas quando houver commit de código; `HML_TEST_NOT_RUN` até evidência, `PROD_NOT_DEPLOYED`.

**Definição de pronto do backend para liberar FRONT:** endpoints necessários respondem e contratos estão verificados com dados autorizados; tests positivos, negativos e concorrentes em HML, provenance/coverage e no-op demonstrados; flags sem duplicação, sem reopen, isolamento por request e histórico temporal correto; log de SHA/rollback e validação de Plugin UI. Qualquer exceção real volta à Coordination com `EXECUTION_DRIFT`, não ao PO como nova micropergunta.

## 10. Responsabilidade de execução definida pelo PO — Devin

**Devin é o executor exclusivo de todas as implementações** de código, migrations, testes de execução e pull requests. **ChatGPT/EVA é coordenador técnico e autor/revisor dos prompts de implementação**, faz supervisão de evidências, riscos e cumprimento de contratos, sem editar diretamente código da aplicação. Owners Engenharia/Core/Coordination mantêm as autoridades previstas; escolher Devin como executor **não altera ownership de domínio**. Sequência vinculante: **produto backend → bandeiras backend → DEV/HML multiusuário → frontend completo → validação HML → deploy produtivo aprovado**. [Plano de coordenação e primeiro prompt para Devin](./PRC-TRACK-DEVIN-IMPLEMENTATION-COORDINATION-AND-PROMPTS.md). A fase DEVIN-PROD-00 é inventário/contrato; não equivale a código implementado nem autoriza schema/prod.


## 11. Decisão PO sobre T01/T02 — ratificação condicional de direção técnica (13/11/2026)

O PO **aceitou as recomendações T01/T02** e autorizou seu registro no GitHub. Referência: [pacote técnico detalhado e decisão](./PRC-TRACK-T01-T02-COORDINATION-TECHNICAL-RATIFICATION-PACKET.md), §7.

- **T01 — APPROVED_BY_PO_WITH_CONDITIONS:** usar catálogo PRC existente, snapshot consolidado com schema/coverage/provenance, UPDATE parcial preservando origem e omitidos, supplierCode+store e read de histórico legado sem inferência. Reutilizar adapters existentes e impedir falsa certificação TOTVS.
- **T02 — APPROVED_BY_PO_WITH_CONDITIONS:** primeira conclusão válida gera V1; no-op posterior auditado sem nova revisão; V2+ só diff técnico real, fechamento transacional com CAS, locking, idempotência e compatibilidade.
- **Validação técnica ainda necessária:** domain owner da Engineering API confirmar contratos concretos, consumers e rollback. **Não equiparar aprovação de direção pelo PO a autorização final de alteração arquitetural/produção.**
- **Implementação:** até essa ratificação do owner, `DEVIN-PROD-02 = PENDING_OWNER_GATE / TEST_NOT_RUN`. Depois, executar menor diff no backend, PR, testes no SHA, HML governada e aceite independente Cursor.
- **PRD:** pós-deploy apenas health, observabilidade e consultas explicitamente read-only; nunca escrita de dados de negócio para teste.

Este §11 atualiza o status histórico `ARCHITECTURE_DECISION_REQUIRED` de T01/T02: a **direção PO está aprovada**, porém o **gate de contrato por autoridade técnica competente continua aberto**. Outras pendências T03–T08 não são implicitamente ratificadas.


## 12. T01/T02 — owner de Engenharia ratificou; PROD-02 liberado (13/11/2026)

**Decisão expressa do owner de Engenharia nesta conversa:** `T01=RATIFIED`; `T02=RATIFIED`, com as condições técnicas aceitas pelo PO e registradas no [pacote T01/T02 §8](./PRC-TRACK-T01-T02-COORDINATION-TECHNICAL-RATIFICATION-PACKET.md). Esta decisão **supersede o estado PENDING_OWNER_GATE** registrado no §11 para T01/T02, sem apagar o histórico.

**Gate agora:** `DEVIN-PROD-02 IMPLEMENTATION_AUTHORIZED / IMPLEMENTATION_TEST_NOT_RUN`. Devin pode iniciar implementação bounded no backend de produto com inventário de consumidores/port/schema no SHA atual, diff mínimo, testes memory + Postgres, PR sob proteções e HML governada. Não esperar a revalidação independente Cursor do PROD-01 para começar trabalho T01/T02.

**Sem alargar a autorização:** T03–T08, bandeiras, frontend, mudanças de domínio/permissões, migrations destrutivas e deploy de produção continuam sujeitos a seus próprios contratos/gates. Exigir evidência de compatibilidade e rollback antes de aceitar migration/merge. TESTAR escrita exclusivamente DEV/HML; em PRD somente disponibilidade, saúde, métricas e GET comprovadamente não mutável.

**Owner decision ≠ implementação ou runtime PASS.** Qualquer `EXECUTION_DRIFT` concreto retorna à Coordination, não gera ciclo de hipóteses sem evidência.


## 13. PO — revision lineage exclusively on validated completion (14/11/2026)

**Ratificação semântica:** PRC aberta pode identificar produto-alvo em UPDATE e usar `baseRevision` somente como referência para concorrência/comparação; não gera nem recebe revisão própria. `caseVersion` é versão de transação do atendimento. **Somente a conclusão com verificação e publicação válida associa `request_id` à revisão técnica produzida**; não-op em produto com revisão preserva Vn e audita a solicitação sem gerar Vn+1; primeira conclusão válida de produto sem histórico versionado produz V1 baseline R01, com provenance, mesmo sem diff. CREATE pendente/rejeitada não cria vínculo fictício. O código TOTVS oficial continua sob autoridade externa.

**Estado:** `PO_RATIFIED / IMPLEMENTED_AND_PROVEN_HML (14/11/2026, impl 4788a1efa6)`. Compatível com R01–R03 e a natureza de `product_registration_revisions.request_id` no contrato; `stale_revision` permanece fail-closed no fechamento (guarda produto vigente vs baseline). `baseRevision` deixou de ser emitido no detalhe; intake legado continua tolerado e revalidado server-side. UI V3: chip Rn removido do hero; caso concluído exibe somente o resultado de publicação do próprio caso. Ver adendos PRC-REF-025 e §§15–16 do contrato técnico.

## 14. Ratificação PO — solicitações não possuem revisão até conclusão (14/11/2026)

**Decisão superveniente:** não atrelar revisão de produto a solicitação em aberto; `baseRevision` não é dado de negócio do caso nem vínculo de produto/revisão. O código produto-alvo de UPDATE é permitido, mas conclusão deve confrontar estado oficial e revisão técnica vigente **na hora do fechamento**, com fail-closed em concorrência/rebase incerto. Quando uma solicitação concluída efetivamente publica nova revisão Vn+1 ou inaugural V1, guardar vínculo causal `request_id` na revisão; no-op posterior conclui sem nova revisão nem autoria falsa de Vn anterior. Preservar R01–R18, sobretudo R01, R02, R03 e R18.

**Autoridade e execução:** PO autoriza mudança semântica/protocolar PRC; Engenharia API permanece owner, TOTVS fonte oficial. Alterações de contratos de outros bounded contexts ou authority exigem retorno à Coordination; inventário técnico, compatibilidade, migração governada e rollback são obrigatórios. Sem deploy PRD. `IMPLEMENTED_HML (impl 4788a1efa6, 14/11/2026)` — detalhe emite `publishedRevision` causal (ou `null`), sem `baseRevision`; UI mostra «Revisão técnica gerada: Vn»/«Concluída sem nova revisão técnica» só no caso concluído; «Solicitação de origem» na aba Revisões.
