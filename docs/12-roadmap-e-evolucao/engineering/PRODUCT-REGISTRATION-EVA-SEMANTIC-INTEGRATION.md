# Product Registration — plano de paridade EVA por ações semânticas

> **2026-11-06 | Status:** `TARGET / DESIGN_SPECIFIED / IMPLEMENTATION_NOT_STARTED`
> **Evidência de integração:** `engineering-api/engineering_app/application/eva/semantic_registry.py`, `engineering-api/engineering_app/interface/mcp/semantic_bridge.py`, `engineering-api/engineering_app/interface/mcp/tool_bridge.py`, `engineering-api/engineering_app/interface/mcp/server.py`.
> **Base funcional:** [PRODUCT-REGISTRATION-MVP-TECHNICAL-CONTRACT.md](./PRODUCT-REGISTRATION-MVP-TECHNICAL-CONTRACT.md).
> **Regra principal:** não criar nova tool MCP, outro servidor MCP, nova authority, nem acesso do modelo a URL, SQL, função arbitrária, TOTVS ou banco. Estender ações de entidade no registro semântico existente; REST, Portal e EVA compartilham casos de uso de aplicação, validação de domínio, autorização, idempotência e auditoria.

## 1. Contrato arquitetural e princípio de paridade

**Princípio de produto:** para cada operação legítima disponível ao usuário na interface do Product Registration, a EVA deve ter uma ação semântica equivalente **quando o mesmo usuário tiver permissão e houver contrato executável aprovado**. Paridade significa capacidade de consultar/preparar/invocar a mesma operação governada, **não** autorização extra, automação de aprovação técnica, criação oficial no ERP ou bypass de confirmação humana.

**Arquitetura existente, observada em GitHub em 2026-11-06:**

- Seis tools públicas estáveis: `get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete`. Registradas em `SEMANTIC_TOOL_NAMES`; dispatch por `(entity, action)` via `SemanticAction`, nunca URL arbitrária.
- `get_context` publica catálogo e disponibilidade; `_resolve` rejeita ação desconhecida ou não `proven`, e tool incompatível; status `planned` não pode ser executado.
- `read`: registry allowlist, `ref`, filtros permitidos, paginação controlada, `_READ_DISPATCH`. Acesso humano e Core AuthZ na bridge.
- `analyze`: `analysis_type` numa allowlist `_ANALYZE_KINDS`, dispatch explícito, cálculos/sugestões com proveniência, não fato oficial.
- `knowledge`: corpus versionado e autorizado, não resposta inventada.
- `execute`: `(entity,action)`, payload/changes, `idempotency_key`, `expected_version`, `phase` e `_EXECUTE_DISPATCH`. `ENG_EVA_ACT_ENABLED` bloqueia mutações quando desligado; alguns writes existentes podem agir diretamente após intenção inequívoca e AuthZ, mas **não extrapolar esse comportamento para aprovação técnica irreversível de cadastro**.
- `delete` tem confirmação destrutiva com `proposal_ref` selado e elicitation; **não há delete de registro técnico no MVP**. Não registrar `product_registration.delete`.
- Bridge já possui `_require_engineering_human` e cliente delegado para dados oficiais; estas checks são pré-condições, não substituem AuthZ de recurso e permissão `product-registration.*`.

**Nova entidade semântica candidata (não confundir com `product.*` oficial ERP):** `product_registration`. O namespace `product` atual é leitura de dados oficiais/BOM/desenhos; solicitações, draft e revisão técnica pertencem a `product_registration`. Não alterar o significado de `product.update` planejado e bloqueado para escrita ERP.

Arquitetura:

```
ChatGPT / EVA
  -> MCP existing 6 tools (same server, transport, identity)
  -> semantic registry allowlisted (product_registration.*, planned -> proven only after tests)
  -> semantic dispatch + actor context
  -> SAME application use case / domain policy used by REST
  -> repository / authorized OfficialProductReader
  -> engineering data + verified ERP read
Portal UI -> REST /v1/product-registration/* -> SAME use case
```

**Não** fazer EVA chamar REST do próprio serviço internamente com token privilegiado quando pode usar use case. Se HTTP for indispensável por boundary real, delegar exatamente a identidade do usuário e comprovar paridade sem autorizações adicionais. EVA não vira source of truth de request, revisão, verificação nem permissão.

## 2. Matriz completa: 18 rotas REST e capacidades semânticas

As ações abaixo são **TARGET**, todas com `status=planned` até implementação, testes e atualização de catálogo no SHA real. `execute` tem ao menos `prepare` e `act` para ações não terminais; finalize exige política mais forte de confirmação. Os filtros são allowlist da REST, nunca nomes de colunas SQL recebidos do modelo.

| # | REST planejada | Tool já existente | entity.action proposta | Exigência adicional |
|---|---|---|---|---|
| 01 | `POST /intake/requests` | `execute` | `product_registration.submit` | `prepare/act`, source atribuído pelo sistema, requester=principal, idempotência; EVA não pode alegar ser sistema externo |
| 02 | `GET /requests` | `read` | `product_registration.list` | paginação e filtros com escopo do ator |
| 03 | `GET /requests/{requestId}` | `read` | `product_registration.detail` | `ref=requestId`, `allowedActions` backend |
| 04 | `GET /requests/{requestId}/timeline` | `read` | `product_registration.timeline` | histórico escopado, paginado |
| 05 | `POST /requests/{id}/actions/start` | `execute` | `product_registration.start` | `prepare/act`, `expected_version`, AuthZ do caso |
| 06 | `PATCH /requests/{id}/draft` | `execute` | `product_registration.update_draft` | changes por fieldPath, patch allowlist, CAS, reason |
| 07 | `POST /requests/{id}/actions/request-information` | `execute` | `product_registration.request_information` | motivo + campos pendentes obrigatórios |
| 08 | `POST /requests/{id}/actions/resume` | `execute` | `product_registration.resume` | checar pendência atendida/ator autorizado |
| 09 | `POST /requests/{id}/actions/submit-review` | `execute` | `product_registration.submit_review` | validação da ficha, não aprova nem conclui |
| 10 | `POST /requests/{id}/actions/reject` | `execute` | `product_registration.reject` | consequência terminal: `prepare` + confirmação humana verificável de alvo/impacto antes do ACT |
| 11 | `POST /requests/{id}/actions/verify-and-complete` | `execute` | `product_registration.verify_and_complete` | `prepare` prova readiness; `act` só com confirmação humana vinculada, live AuthZ e comparação TOTVS na execução |
| 12 | `GET /requests/{id}/verifications` | `read` | `product_registration.verifications` | visibilidade/redação de dados oficiais |
| 13 | `GET /technical-records/{recordId}` | `read` | `product_registration.record` | cópia técnica, nunca fato ERP sem freshness |
| 14 | `GET /technical-records/{recordId}/revisions` | `read` | `product_registration.revisions` | lista histórico e provenance, paginada |
| 15 | `GET /technical-records/{recordId}/revisions/{n}` | `read` | `product_registration.revision` | `ref=recordId`, `filters.revision_number` whitelist |
| 16 | `GET /reference-data` | `read` | `product_registration.reference_data` | versionamento de schema e policy de campos |
| 17 | `GET /outbound/requests/{requestId}` | `read` | `product_registration.outbound_result` | aplicar escopo da origem/consumer; EVA humana não finge service principal |
| 18 | `GET /outbound/requests` | `read` | `product_registration.outbound_list` | somente se houver uso humano permitido; caso saída seja exclusivamente S2S, **não expor à EVA**; paridade de usuário não cria permissão de integração |

**Contagem:** 18 mapeamentos de superfície; **não são 18 tools**, são ações dentro das tools existentes. Algumas capacidades de integração S2S são **não aplicáveis** a um agente humano se não houver consumer/permission legítimos. Se uma mesma operação pode ser coberta sem duplicar o catálogo (ex.: `list` com filtro `source` versus `outbound_list`), aplicar Abstraction Gate e consolidar antes do diff.

Operações REST fora da matriz: o lookup oficial `product.search/detail/suppliers` já existe na semântica; reutilizá-lo quando seus contratos proverem o dado, sem inventar `product_registration.erp_lookup` duplicado. A validação assistida pelo analista pode justificar `analyze` com `analysis_type="product_registration.technical_review"` **somente quando houver use case real com fontes e critérios verificáveis**; de outro modo EVA pode analisar os dados autorizados obtidos por `read` e devolver sugestões explicitamente `DRAFT/CANDIDATE`, sem registrar fato/proposta automaticamente.

## 3. Política de ação EVA e salvaguardas

| Classe | Exemplos | Política |
|---|---|---|
| `read` | fila, detalhe, timeline, revisão, verificação | mesmo scope/Core permissions da REST; não ler dados por URL livre; resultado com source, snapshotAge/freshness |
| `analysis` | consistência de descrição, campos obrigatórios, comparações exploratórias | `DRAFT/CANDIDATE`, grounded no `requestId`, `recordId`, `schemaVersion`, evidências e limitações; nenhuma escrita por análise |
| `moderate execute` | submit, start, update_draft, request_information, resume, submit_review | `ENG_EVA_ACT_ENABLED` e live Core+domain AuthZ, allowlist, expectedVersion/idempotency, `prepare` quando ambíguo; `act` só quando intenção específica e dados são inequívocos |
| `high-impact execute` | reject, verify_and_complete | **PREPARE → proposta selada ligada ao ator/alvo/versão/diff/TTL → confirmação humana verificável → ACT**; ausência de canal de confirmação → `confirmation_unavailable`, não prosseguir |
| `delete` | nenhum | sem ação semântica e sem API de exclusão de revisão/request no MVP |
| `knowledge` | instruções de cadastro | usar corpus autorizado já existente/estendido conforme seu owner; sem novo tool; publicar somente tópicos versionados e realmente servidos |

**Concluir nunca é ato livre da EVA.** O humano autorizado pode iniciar a operação através da EVA; no `ACT`, o caso de uso verifica estado/versão, busca novamente os campos oficiais pelo `OfficialProductReader`, compara `create/update` conforme política e só então persiste `completed`/revisão imutável. Uma proposta selada ou campo `confirmed=true` fornecido pelo modelo não substitui confirmação humana via canal confiável. MCP elicitation deve ligar alvo, código ERP, delta, efeito e revisão, com echo de identificador quando necessário. Se o cliente MCP não suportar, direcionar à confirmação na UI legítima sem fazer escrita pelo modelo, por handoff explícito; **não** inventar ação em nome do usuário.

Ações `reject` e `verify_and_complete` não são `delete` mas são **terminais / de alto impacto**, portanto podem usar a infraestrutura existente de `proposal_store`/elicitation com policy específica; nunca reusar automaticamente o fluxo `nonconformity.delete` ou o mesmo objeto de proposta sem boundary real.

**O limite "tudo que o usuário faz EVA faz"** significa paridade de capacidades autorizadas e de **invocação governada**, não independência de aprovação humana, nem possibilidade de executar funcionalidades indisponíveis. Usuário sem `engineering.product-registration.verify` também não consegue finalizar via EVA. Permissão de consultar um registro não permite editar ou ver outro.

## 4. Contratos técnicos de dispatch

### Catálogo tipado

Registrar entradas candidatas em `SEMANTIC_ACTIONS` usando `_a(entity="product_registration", action=..., tool=..., risk=..., ref_arg=..., fields=..., paginated=..., phases=..., requires=...)` de acordo com assinatura vigente. Não alterar `SEMANTIC_TOOL_NAMES`. Não alterar `get_context` para mostrar `proven` antes de teste. Preservar status `planned/not_implemented` honesto, catalogado conforme convenção do registro.

`read`:
- allowlist em `_READ_DISPATCH` para `product_registration.*`;
- args convertidos em DTO dos casos de uso oficiais, sem montar queries SQL ou URLs a partir da entrada do modelo;
- filtros e `ref` whitelisted, paginação bounded; retornos `CallToolResult` com `entity/action`, `source`, `requestId`, `provenance`, `caseVersion` e `freshness` conforme operação;
- erros `not_found`, `forbidden`, `stale_version`, `unavailable`, `not_implemented` tipados.

`execute`:
- `_EXECUTE_DISPATCH` mapeado explicitamente ao use case do Product Registration, sem chamar handlers HTTP ou `main.py`;
- `phase`, `payload`, `changes`, `target_ref`, `idempotency_key`, `expected_version` da assinatura existente; validar `expected_version` numérico UUID/ETag conforme contrato antes de encaminhar;
- caso de uso recebe actor completo de `_require_engineering_human`, origem derivada do contexto (não confiável se fornecida em payload) e política live de recurso;
- `prepare` apenas valida/calcula impacto e produz proposta quando exigido, sem mutação; `act` revalida state, AuthZ e preconditions no instante da escrita; read-back + auditoria + idempotência;
- status `planned` não deve resolver nem constar como ativo em listagem de capacidades disponíveis.

`analyze`:
- não reusar `product.drawing_analysis` para editar/finalizar cadastro; ele continua desenho, DRAFT;
- se houver use case `technical_review`, adicionar `analysis_type` à allowlist e despacho explícito já existentes; fatos observados separados de sugestões; não inventar cota, material, grupo, Part Number ou regra.

`get_context`/descoberta:
- catálogo semantic version incrementado conforme compatibilidade real;
- alinhar descrição de capacidade, `ref_arg`, filtros, phases, risco, estado, requisitos e mensagens; catálogo e dispatch não podem divergir;
- sem queimar `proven` no registry antes de deployment/testes no SHA exato.

`knowledge`:
- atualizar somente corpus governado, por tópico validado, quando houver conteúdo de Engenharia aprovado para orientar usuário; material técnico pode ser apresentado via `read reference_data` sem criar tópico redundante.

## 5. Mapa de permissão: UI ↔ REST ↔ EVA

| Operação | REST exige | EVA também exige |
|---|---|---|
| listar/ler | `engineering.access` + `product-registration.read` + escopo | mesmos checks + principal humano |
| criar solicitação | `product-registration.create` + source autorizada | mesmos checks + `ENG_EVA_ACT_ENABLED`; requester=ator real |
| iniciar/editar/devolver/revisar | `product-registration.process` + ownership/case state | mesmos checks + gate ACT; actor/version e audit |
| rejeitar | `product-registration.process` + estado válido | mesmos checks + confirmação terminal verificável |
| concluir | `product-registration.verify` + process + verificação TOTVS | mesmas checks + confirmação do analista + ERP read-back no ACT |
| consultar outbound | permissão e escopo da origem/consumer | apenas se operação humana correspondente for autorizada; não impersonar S2S |

Não tratar `engineering.access` como suficiente para mutações. Flags EVA governam execução **além** de RBAC; flags não autorizam nada. Ferramenta pode estar visível como `planned` sem ser utilizável.

## 6. Ciclo de vida de desenvolvimento em cada rota nova

Definir regra de **Paridade EVA como critério de aceite transversal** de todo slice PRC:

```text
RQ/AC + owner
  -> contrato REST/versioning + use case/ports + AuthZ
  -> implementação REST + tests
  -> SEMANTIC_ACTIONS registration (planned)
  -> semantic dispatch to SAME use case + tests
  -> contract/parity/security tests UI/API/EVA
  -> release gate: promoted proven only after evidenced success
```

Para cada rota:
1. Registrar classificação `read|analysis|moderate|terminal|S2S-only`, se o usuário humano pode exercer a mesma ação; se não, descrever `NOT_APPLICABLE` com motivo.
2. Garantir DTO e operação compartilhada. Não duplicar regras de workflow/draft/verificação em `semantic_bridge.py`.
3. Criar testes REST vs EVA para mesmo actor e mesmo request/case, incluindo `allowedActions`, field-level AuthZ, source scoping, caseVersion, idempotency, concorrência, envelope e read-back.
4. Negativos: JWT inválido; falta de permission Core; actor alheio; filtros arbitrários; tentativa de tool/ação não registrada; `ENG_EVA_ACT_ENABLED=false`; reuso de proposal; token/target trocado; sem elicitation; dado ERP divergente/inacessível; finalização sem confirmação; duplo clique/double ACT.
5. Read: dados com provenance e freshness. Write: evento auditado com `actor=Keycloak sub`, `channel=eva` vs `portal`, correlation ID, sem esconder origem da ação.
6. Classificar testes `PASS/FAIL/PENDING/INCONCLUSIVE/TEST_NOT_RUN` por SHA. Se REST estiver publicado mas EVA não estiver pronta, registrar **PARITY_GAP** e não alegar paridade completa; avaliar bloqueio de release conforme risco e autorização de produto.
7. Não criar novas tools nem capacidades de edição oficial de TOTVS.

## 7. Sequência de execução da ampliação EVA

| Slice | Entrega | Evidência de saída |
|---|---|---|
| `PRC-EVA-0` | Inventariar catálogo semântico do HEAD real, estado de VAL-01, owners e contratos REST do vertical | diff/overlap + matriz 18 rotas, seis tools intactas |
| `PRC-EVA-1` | `read`: list, detail, timeline, reference_data, record, revisions, verifications (e demais leituras autorizadas) | teste REST ↔ EVA com mesmo actor, filtros/paginação e 403 |
| `PRC-EVA-2` | `execute`: submit, start, update_draft, request_information, resume, submit_review | prepare/act, idempotência, CAS, gates e outcomes |
| `PRC-EVA-3` | ações terminais reject, verify_and_complete com proposal/confirmation e verificação oficial | testes confirmação, AuthZ live, TOTVS mismatch, SEM_REVISION_GAP=0 |
| `PRC-EVA-4` | analyze/candidates técnicos + conhecimento versionado quando houver caso de uso e corpus real | grounding/segurança/limitations, no writes |
| `PRC-EVA-5` | regressão e rollout, atualização de catálogo `proven` no SHA de deploy, help/docs | testes seis tools existentes + novas ações, rollback, sem colisões VAL-01 |

**PRC-EVA não precisa esperar o módulo inteiro:** cada slice REST cria/valida seu equivalente semântico no mesmo ciclo de desenvolvimento, reservando componentes compartilhados para integração serializada.

## 8. Coordenação paralela e ownership de arquivos

**Fatos no GitHub lidos:** registry em `engineering-api/engineering_app/application/eva/semantic_registry.py`, dispatch em `engineering-api/engineering_app/interface/mcp/semantic_bridge.py`, adaptadores/use cases legados em `engineering-api/engineering_app/interface/mcp/tool_bridge.py`. A frente VAL-01 já trabalha em percepção/OCR e toca `semantic_bridge.py` segundo o inventário de worktree. **Não editar em paralelo esse arquivo**.

- PRC pode criar código em novo diretório `domain/product_registration`, `application/product_registration`, `composition/product_registration_composer.py` e testes próprios.
- `semantic_registry.py`, `semantic_bridge.py`, `tool_bridge.py`, `main.py`, Core manifest/auth e deploy são **shared-touch**: integrador designado faz merge serial após conferência de HEAD/diff e estado do outro agente. O ideal é organizar novos handlers específicos de Product Registration em módulos separados e apenas registrar dispatch mínimo em código compartilhado.
- Nenhum import do contexto drawing/OCR nem dependência runtime de Requests API/Controle MP. Não editar/formatar `drawing`, `understanding`, `paddleocr`, SLANet, comparadores/jobs ou testes VAL-01.
- Antes de mudar código, confirmar `origin/main`, `HEAD`, `git status`, worktrees, regras `AGENTS.md`/`.cursor`, equivalentes e RQ/AC; trabalhar somente no diff reservado. Após merge, reexecutar regressão REST/MCP/EVA/drawing no **mesmo SHA**; publicar por digest com rollback e autorização Ops.
- Os MCP handlers não são authority; se o contrato oficial bloquear, retornar erro explícito, sem fallback privilegiado.

## 9. RQ, AC e decisão de disponibilidade

- `RQ-PRC-EVA-01`: cada capacidade humana da área de cadastro tem equivalente semântico nas seis tools existentes, salvo exceção S2S-only documentada.
- `RQ-PRC-EVA-02`: sem duplicação de use case ou regra de negócio; semantic adapters consomem contratos oficiais.
- `RQ-PRC-EVA-03`: autorização de operação e objeto idêntica REST/EVA; flags ACT adicionais e audit channel.
- `RQ-PRC-EVA-04`: rejeição/conclusão exigem confirmação humana verificável; EVA não realiza cadastro ERP nem dá aprovação autonomamente.
- `RQ-PRC-EVA-05`: análise de descrição é `DRAFT/CANDIDATE` com contexto/campo/evidência; nenhum write sem execute separado.
- `RQ-PRC-EVA-06`: catálogo semantic e dispatch refletem status real, sem novas tools, com compatibilidade de contratos.
- `AC-PRC-EVA-01`: contagem de tools MCP públicas **permanece seis**; qualquer tool adicional = FAIL.
- `AC-PRC-EVA-02`: `get_context` anuncia apenas as ações realmente disponíveis, ou `planned` com negativa honesta; entidade desconhecida = erro tipado.
- `AC-PRC-EVA-03`: cada route read tem action testada com mesmo actor/ref/filtros, mesma visibilidade e dados equivalentes.
- `AC-PRC-EVA-04`: cada mutate REST tem action execute correspondente (salvo exceção formal); CAS/Idempotency/auth/audit parity.
- `AC-PRC-EVA-05`: tentativa de concluir pela EVA sem verificação TOTVS, sem confirmação humana ou sem permissão = FAIL CLOSED, sem revisão vigente.
- `AC-PRC-EVA-06`: rejeição terminal não muda record vigente; confirmar via EVA não é suficiente para simular operação ERP.
- `AC-PRC-EVA-07`: executar ações durante `ENG_EVA_ACT_ENABLED=false` = bloqueado; nenhum método alternativo contorna flags.
- `AC-PRC-EVA-08`: regressão de `product.drawing_*`, NC, LMP e demais 6 tools sem drift; isolamento da worktree VAL-01 comprovado.
- `AC-PRC-EVA-09`: auditoria, source, actor, caseVersion, idempotency, official verification evidence e correlation preservados.
- `AC-PRC-EVA-10`: quando capacidade REST ainda não implementada, EVA relata `not_implemented`, sem alegar execução ou acesso.
- `AC-PRC-EVA-11`: client sem suporte à confirmação deve receber `confirmation_unavailable` e nenhuma escrita terminal.
- `AC-PRC-EVA-12`: análise assistiva não altera produto técnico ou TOTVS; sugestões trazem limitações e referências.

**Estado:** `PLAN_UPDATED` apenas quando publicado; `SEMANTIC_INTEGRATION=PLANNED`; `CODE=NOT_CHANGED`; `EVA_PARITY_TESTS=TEST_NOT_RUN`; `VAL01_SHARED_MERGE=PENDING`.


## Regra de fonte oficial para ações semânticas Product Registration (2026-11-06)

> **Decisão explícita do Product Owner, prevalente para Product Registration:** toda busca, consulta, lookup, conferência de atributos, fornecedores/Part Number e validação de conclusão baseada no TOTVS **deve passar pelo BFF da `engineering-api`, que consome exclusivamente contratos oficiais da `api-delpi`**, com identidade delegada e autorização do usuário. A `api-delpi` é owner da integração/consulta ao TOTVS; a Engineering API adapta o contrato para os casos de uso de Engenharia. Nem `plugins/engineering` nem a EVA acessam diretamente TOTVS, banco SQL/ODBC, API Flask do Controle MP ou `api-delpi` contornando o BFF de Engenharia.

Fluxo autorizado: `Portal ou EVA -> Engineering API (REST ou mesma application use case via ações semânticas) -> OfficialProductReader adapter -> api-delpi /products/* (read-only) -> TOTVS`. Para EVA, usar os mesmos ports/use cases e AuthZ, **sem novas tools MCP**; não duplicar HTTP call no handler semântico. Sem escrita ERP neste MVP: analista realiza criação/alteração manual no TOTVS; `verify-and-complete` lê resultado pela `api-delpi`, compara campos, e só conclui quando todos os campos exigidos são comprovados.

**Gate D / lacuna atual:** o relatório PRC-C3 indica que `B1_CONTA` (`accountingAccount`) não é exposto pela view `engineering` embora outros atributos e SA5/Part Number estejam disponíveis. Resolver **no contrato/owner `api-delpi`**, verificando escopo/autorizações, ou propor view oficial apropriada; não adicionar acesso SQL/TOTVS direto à Engineering API e não relaxar comparação. Enquanto qualquer campo obrigatório não for verificável via `api-delpi`, bloquear `completed` (fail-closed, erro `unverifiable`). Aprovação de novo campo/view é do owner da API e das permissões, não do BFF.

**Critérios de aceite:** busca e verificação usam somente adapter oficial `api-delpi`; autorização humana propagada; ausência/403/timeout/campo omitido produzem status honesto sem revisão publicada; testes REST/EVA usam mesmo caso de uso e demonstram ausência de SQL direto, de escrita ERP e de downstream legado. Qualquer mudança nessa fronteira exige `ARCHITECTURE_DECISION_REQUIRED`. **Documentação apenas; sem deploy, migration ou mudança de código nesta atualização.**


## Decisão aprovada do Product Owner — PRC RBAC, BFF e HML (2026-11-06; vigente)

**Leia antes de implementar:** [PRODUCT-REGISTRATION-PO-DECISIONS-2026-11-06.md](./PRODUCT-REGISTRATION-PO-DECISIONS-2026-11-06.md). Esta decisão **substitui** as propostas anteriores de cinco permissões `engineering.product-registration.*` e a premissa de que `engineering.access` não autoriza o CRUD do módulo. Modelo vigente: `engineering.access` para CRUD/workflow operacional e `engineering.manager` para administração, com AuthZ backend live, escopo/identidade e invariantes de domínio intactos. **Ainda não implementado no PRC/Core; não alegar RBAC pronto.** Engenharia é owner do workflow e `api-delpi` é owner da leitura oficial TOTVS; autorizado estender `B1_CONTA` na `api-delpi` (inclusive SQL interno, sem bypass pela Engenharia). HML autorizada **condicionalmente** à execução por operadores habilitados, gates e testes; produção não autorizada. Merge markers PRODUCTS corrigidos na `main`, porém build/typecheck completos devem ser executados para comprovar integração.


## Decisão PO vigente — SA5 Part Number vazio (2026-11-06)

**Contrato aprovado:** [PRODUCT-REGISTRATION-PO-DECISIONS-2026-11-06.md](./PRODUCT-REGISTRATION-PO-DECISIONS-2026-11-06.md#decisão-adicional-aprovada--part-number-opcional-quando-ausente-no-totvs-2026-11-06). `suppliers[].partNumber` (`SA5.A5_CODPRF`) **não é required não-vazio** quando a fonte oficial TOTVS retorna Part Number vazio; qualquer regra histórica contrária deste documento está substituída. Aceitar no intake/draft `partNumber` omitido, `null` ou `""` e normalizar de forma consistente. **Não confundir campo oficial ausente (unverifiable) com valor oficial vazio (verificável).** Quando informado não vazio ou explicitamente selecionado para alteração, comparar o valor final exato com SA5 via `Engineering API -> api-delpi -> TOTVS`; mismatch continua bloqueando publicação. Remoção explícita para vazio é delta auditável, distinta de omissão de alteração. Comparar identidade do vínculo por supplierCode/store, sem ignorar PN informado ou ambiguidade/duplicata; preservar CAS, revisão imutável, provenance e AuthZ. **Status: decisão aprovada, implementação/testes ainda pendentes; não declarar deploy ou HML PASS.**


## D16 — EVA: paridade das bandeiras de acompanhamento

**Contrato:** [D16 — CRUD operacional de bandeiras](./PRODUCT-REGISTRATION-D16-ATTENDANCE-FLAGS-CRUD-EVA-UX-PLAN.md). As operações `flag_list`, `flag_detail`, `flag_create`, `flag_update`, `flag_resolve`, `flag_reopen`, `flag_delete` são ações semânticas sob `product_registration`, nas **seis tools existentes**, consumindo exatamente os mesmos application use cases do REST (sem DTO/validação paralela e sem tool nova). Leitura exige acesso ao caso; criação/edição/resolução/reabertura usa PREPARE/ACT, live AuthZ, CAS e idempotência; exclusão lógica exige proposta selada + confirmação humana verificável (`confirmation_unavailable` bloqueia sem elicitation). Channel=`eva`; actor = principal humano. Não confundir com feature flags `ENG_EVA_ACT_*` nem com `field_flag` do Controle MP legado. **Status PROVEN** em `semantic_registry` + `prc_semantic` + `TestFlagEvaParity` (in-memory).


## D16-REF-01 — EVA: bandeira contextual e consultas consolidadas

Ver [adendo D16-REF-01](./PRODUCT-REGISTRATION-D16-ATTENDANCE-FLAGS-CRUD-EVA-UX-PLAN.md#d16-ref-01--decisão-po-superveniente-bandeiras-por-campo-experiência-contextual-e-consultas-transversais). Ampliar a semântica das ações de bandeira já existentes para exigir alvo técnico **inequívoco** em novas criações: FIELD+targetPath ou SUPPLIER_LINK+supplierKey+targetAttribute (partNumber/catalogNumber). PREPARE explicita campo/fornecedor, caso e conteúdo, ACT revalida acesso, versão e unicidade e não modifica TOTVS nem dados técnicos. Expor consultas de bandeiras por produto, caso, tipo, campo, atributo, estado e agregados de itens/produtos com pendências **através da tool read existente**, sem criar 7ª tool; preferir ampliar flag_list em vez de ação redundante. Resultados sempre filtrados por AuthZ de objeto e com contagem/paginação real, inclusive para solicitações encerradas. Não presumir que PN vazio signifique pendência sem bandeira explícita. Histórico de GENERAL legado não é inventado como FIELD. **TARGET, não implementado por esta nota.**


## PRC-REF-017 — EVA: paridade CREATE/UPDATE verify-and-complete

A ação semântica `product_registration.verify_and_complete` continua a única via EVA de conclusão. CREATE: PREPARE/ACT devem receber `official_code` informado pelo analista (código gerado no TOTVS); a EVA não inventa código. UPDATE: código baseline da solicitação; troca arbitrária rejeitada pelo mesmo use case REST (`officialCode` immutable). Divergências campo a campo (`field_results` com previous/expected/observed) bloqueiam `completed` e permanecem consultáveis. Sem tool MCP adicional; sem write ERP. **Status:** IMPLEMENTED_DEV (mesmo `verify_and_complete` + testes `test_prc_eva_parity`).


## PRC-REF-019 — EVA e rodadas de informações ao solicitante

**PROVEN / IMPLEMENTED_DEV (2026-11-09).** Ver [PRC-REF-019](./MFE-PRODUCT-REGISTRATION-POST-REDESIGN-REFINEMENT-PLAN.md). Capabilities: `request_information` (questions/message), `information_round_list|get`, `information_question_accept`, `information_follow_up`, `resume` (gate + waiver) — status `proven` no registry; mesmos use cases REST via 6 MCP tools; PREPARE/ACT; sem draft/submit do solicitante na EVA (ação humana do requester). Texto do solicitante tratado como não confiável. Bandeiras D16 não saem por outbound. `PENDING_NOTIFICATION_OWNER`; AuthZ solicitante externo sem `engineering.access` → `ARCHITECTURE_DECISION_REQUIRED`.

**FIX-01:** detalhe REST/EVA herda o mesmo `_attach_information_exchange` (filtro de `resume` + bloco `informationExchange`). Sem novas MCP tools; sem regressão de dispatch.
