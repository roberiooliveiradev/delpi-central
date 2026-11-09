# D16 — Bandeiras de acompanhamento do atendimento PRC: CRUD, Portal e EVA

**Decisão de produto:** 2026-11-09. **Status:** IMPLEMENTED_IN_DEV / CONTRACT_LOCKED. **Task:** ENG-PRC-D16-ATTENDANCE-FLAGS-FULL-CRUD-AND-EVA. **Escopo:** CRUD REST + PG + UI + EVA parity + testes (DEV only).
**Owner:** Engineering API para o agregado de bandeiras e auditoria; Portal Engenharia para UI; EVA como consumer governado dos mesmos casos de uso. Core mantém RBAC; Keycloak identidade; TOTVS permanece fonte de dados oficiais de produto/SA5; api-delpi faz somente leitura oficial. Não criar outro bounded context.

### Outcomes (execução)

| Superfície | Estado | Evidência |
|---|---|---|
| Domínio `flags.py` (title≤120, desc≤1000, subjects, soft-delete policy) | PROVEN | `tests/test_d16_attendance_flags.py` domain |
| Migration `V015__prc_attendance_flags.sql` | PROVEN (código) / PENDING (PG real se DSN) | `api-delpi/migrations/plugins/engineering/` |
| Repo in-memory + postgres + ports/service | PROVEN | pytest REST + EVA |
| REST nested `/flags` CRUD + resolve/reopen/delete | PROVEN | `TestFlagRestCrud` |
| AuthZ `engineering.access` + escopo do caso | PROVEN | isolation + process gate |
| Eventos `flag.*` na timeline | PROVEN | timeline assert |
| EVA semantic actions (sem nova MCP tool) + delete PREPARE/commit | PROVEN | `TestFlagEvaParity` |
| UI Ficha técnica `PrcAttendanceFlags` | PROVEN (código/Vitest) / PENDING Playwright DEV | MFE + help |
| Pós-conclusão mutável (`FLAG_MUTATION_AFTER_TERMINAL=True`) | PROVEN (contrato código) | domain flag |
| Sem PN=0 / sem SB1-SA5 / sem TOTVS write | PROVEN (by design) | residual: flags não tocam baseline/TOTVS |

## 1. Problema e decisão PO

No Controle MP anterior, analistas marcavam **flags/bandeirinhas com texto** para lembrar verificações e cobranças posteriores durante o atendimento, podendo adicionar e remover a marca. Exemplos:
- «A descrição precisa ser verificada com quem solicitou».
- «Matéria-prima cadastrada; solicitar o Part Number correto ao requisitante e revisar posteriormente».

Essa anotação é **acompanhamento operacional do analista**, não campo SB1, atributo SA5, revisão de desenho, justificativa técnica ou verificação oficial TOTVS. **Não copiar o expediente legado de preencher Part Number com `0`**: não criar regra nem autopreenchimento; PN permanece dado oficial/candidato de produto e pode ser vazio, conforme contrato vigente. Se o dado estiver ausente, a bandeira descreve a pendência sem adulterá-lo.

**Decisão:** criar bandeiras CRUD na **Engineering API**, ligadas ao caso de Product Registration; disponíveis para usuário operacional autorizado e para EVA via **mesmos use cases**. Bandeiras são independentes das ações `request-information`, do estado `needs_information` e do gate de conclusão, salvo política de owner explicitamente aprovada. Não há bloqueio automático de cadastro somente porque existe bandeira aberta.

### Distinção de escopos — evitar confusão
- **PRC case flag:** bandeira vinculada a `requestId`, visível no detalhe da solicitação e auditável. Esse é o **MVP aprovado**.
- **Produto oficial, transversal a solicitações:** necessidade de acompanhamento após conclusão; não criar automaticamente um segundo tipo de flag persistida sobre produto ou um cadastro técnico paralelo. No MVP, manter bandeiras consultáveis **após fechamento do caso**, com referência ao código do produto quando conhecido e caminho de retorno ao caso. Se surgir necessidade de consolidar bandeiras de várias solicitações por código oficial, definir consulta/read model governado adicional no mesmo owner depois de provar consumidor, índice/escopo e autorização. Mudança de SoT/owner = ARCHITECTURE_DECISION_REQUIRED.
- **Flag legada de campo:** inventário `PRODUCT-REGISTRATION-COMPLETE-INVENTORY.md` cita `PATCH /api/requests/fields/<id>/flag` e `PATCH /api/products/fields/<id>/flag`; também flag de conversa. São apenas **referência funcional**, não contrato nem dependency runtime. Não importar serviços, banco, sockets ou internals do Controle MP.

## 2. Modelo de domínio TARGET — bandeira como entidade do caso

```text
ProductRegistrationRequest (aggregate root / autorização e escopo)
  └─ AttendanceFlag [0..N]
      id (UUID imutável)
      requestId (FK Engineering)
      title (texto curto obrigatório, sugestão max 120)
      description (texto multilinha obrigatório, sugestão max 1000)
      status: OPEN | RESOLVED
      subject: GENERAL | FIELD | SUPPLIER_LINK (alvo opcional)
      targetPath? (path SB1 allowlisted, se FIELD)
      supplierKey? (supplierCode/store + produto/filial se chave oficial exigir, se SUPPLIER_LINK)
      createdAt, createdBy
      updatedAt, updatedBy
      resolvedAt?, resolvedBy?
      deletedAt?, deletedBy? (soft-delete auditável)
      version (CAS)
```

**Limites 120/1000 são TARGET recomendados, não regra de domínio oficial já implementada.** Contrato antes de migration; preferir limites claros, tamanho seguro e erros 422. O texto pode citar PN ou descrição sem exigir `targetPath`; assunto é contextual e não pode autorizar escrita sobre SB1/SA5. `subject/target` deve ser minimalista: começar por GENERAL e FIELD/SUPPLIER_LINK somente se experiência e consumers reais comprovarem necessidade; não construir sistema de tags genérico.

Estado formal:
- `OPEN → RESOLVED` pela pessoa autorizada (motivo de resolução opcional conforme contrato), com `resolvedAt/by`.
- `RESOLVED → OPEN` (reabrir quando a pendência voltar; auditar).
- `OPEN/RESOLVED → DELETED` remoção lógica, sem desaparecer do histórico/auditoria.
- UPDATE altera descrição/título/contexto sem recriar identidade; version/CAS obrigatório.
- DELETE normal é soft-delete; evento append-only com autor e estado anterior. Hard-delete reservado a retenção governada, não endpoint operacional.
- Ao concluir/rejeitar solicitação, **não excluir nem resolver bandeiras automaticamente**. Política de edição posterior: leitura permanece; criação/edição/resolução por analista com acesso ao caso, respeitando live AuthZ e regra de caso (não presumir que terminal bloqueia acompanhamento). Formalizar comportamento exato no contrato do owner antes da implementação. Bandeiras abertas não são verificação ERP e não substituem pedido formal de informação.

**Não incluir flag em `requestedChanges`, `official_baseline`, `supplierLinkChanges` ou diff de campos.** Sua edição não altera fingerprint do contexto TOTVS, case workflow status, revisão técnica oficial ou `verify-and-complete`. Versionar flag separadamente; CAS/UoW para auditoria, sem provocar conflitos falsos no wizard.

## 3. CRUD completo e rotas propostas (confirmar padrões reais antes de implementar)

Prefixo existente Engineering API: `/v1/product-registration/requests/{requestId}`. MFE consome via gateway `/apps/engineering-api/...`.

| Método | Rota TARGET | Descrição | Resultado sugerido |
|---|---|---|---|
| GET | `/flags?status=open|resolved|all&page=&pageSize=` | listar paginado, não-vazamento e contadores derivados governados | 200 + flags + page/hasMore/count autorizado |
| GET | `/flags/{flagId}` | detalhe, somente quando pertence ao request autorizado | 200/404/403 |
| POST | `/flags` | criar bandeira | 201 + flag |
| PATCH | `/flags/{flagId}` | alterar título, descrição, alvo | 200 + flag nova |
| POST | `/flags/{flagId}/actions/resolve` | marcar resolvida | 200 |
| POST | `/flags/{flagId}/actions/reopen` | reabrir | 200 |
| DELETE | `/flags/{flagId}` | remover logicamente do quadro; auditar | 204 ou 200 conforme padrão |
| GET | `/flags/{flagId}/events` (opcional) | histórico específico caso timeline geral não baste | 200; aplicar Abstraction Gate antes |

Preferir `GET detail` do caso com `flagsSummary={openCount,resolvedCount}` apenas se UI precisar; **não carregar lista inteira a cada detalhe**. Eventos podem integrar timeline existente com `flag.created/updated/resolved/reopened/deleted`; avaliar projeção/contrato antes de expor um endpoint extra. `GET by id` pode ser dispensável **somente se** o padrão existente de edição/lista já trouxer tudo; justificar explicitamente em Abstraction Gate, sem entregar CRUD incompleto.

### Esquemas de exemplo (TARGET, não existentes)

POST:
```json
{"title":"Revisar descrição","description":"Confirmar a descrição técnica com o solicitante antes da próxima revisão.","subject":"FIELD","targetPath":"description"}
```

PATCH:
```json
{"description":"Solicitante respondeu; validar a descrição recebida.","expectedVersion":2}
```

Response:
```json
{"id":"uuid","requestId":"uuid","title":"Revisar descrição","description":"Confirmar a descrição técnica com o solicitante antes da próxima revisão.","status":"OPEN","subject":"FIELD","targetPath":"description","version":1,"createdAt":"2026-11-09T12:00:00Z","createdBy":{"id":"principal"}}
```

Não aceitar ator informado pelo cliente nem confiar em `requestId` do body quando já existe no path. `Idempotency-Key` em create e mutações conforme padrão do módulo; `expectedVersion`/If-Match em PATCH/resolve/reopen/delete. Respostas de conflito `409 version_conflict`, `404 flag_not_found`, `422 validation_error`, `403 forbidden`, estados inválidos com erro tipado. Sanitizar/escapar texto, não renderizar Markdown/HTML arbitrário. Erros devem seguir envelope e `operation_id` correntes.

## 4. Permissões e workflow

- **Keycloak** identifica ator; **Core** mantém `engineering.access` para CRUD operacional, `engineering.manager` somente administração existente. **Não criar nova permissão `engineering.flags.*` sem decisão Core.**
- A Engineering API também valida **acesso ao request**, status/escopo e possibilidade de editar bandeira com `allowedActions` ou projeção específica calculada server-side; frontend não decide autorização.
- Para solicitantes e demais readers: evitar exposição acidental de observações operacionais. Como `engineering.access` é a permissão operacional vigente, fechar matriz de perfis e visibilidade no owner antes de disponibilizar endpoints; falha fechada para atores não autorizados. Não expor flags automaticamente em outbound/integração externa.
- Não exigir `engineering.manager` para rotina normal de analista. Criar/editar/resolver/deletar seguem mesma autorização live em REST e EVA.
- Bandeiras são **lembretes de trabalho**, não representam aprovação técnica, tarefa formal do solicitante, bloqueio de verificação, conclusão ERP nem compromisso de prazo.
- Sem automação de cobrança, notificações externas, atribuição de responsáveis ou SLA no MVP. Se esses requisitos surgirem, contrato separado de owner, evento e autorização.

## 5. UI — aba Ficha técnica / atendimento

**Posição aprovada como TARGET visual:** seção compacta `Bandeiras de acompanhamento` no detalhe da solicitação, idealmente **após o bloco de ações/abas ou no topo da Ficha técnica, antes de Identificação e classificação**, para que o atendente veja o que precisa revisar. O usuário forneceu captura da aba `Ficha técnica`, com cartões `Identificação e classificação`, `Estoque e contabilidade` e `Fornecedores`; preservar esses cartões e o layout existente. Badge de contagem de bandeiras abertas junto à aba ou cabeçalho, sem poluir com alertas em cada campo.

### Wireframe desktop

```text
Ficha técnica                                 Bandeiras de acompanhamento  [2 abertas]  [+ Nova bandeira]
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [🚩] Revisar descrição                                          [Aberta]  [Editar] [Resolver] [⋯] │
│       Confirmar descrição técnica com o solicitante                                            │
│       Campo: Descrição  ·  Por: analista  ·  Criada: 09/11                                      │
├───────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [🚩] Solicitar Part Number                                     [Aberta]  [Editar] [Resolver] [⋯] │
│       Cobrar PN do requisitante; não alterar PN oficial para zero                              │
│       Vínculo: fornecedor 000089 / 01                                                           │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
[Mostrar resolvidas]  [Histórico de bandeiras]
```

- Botão `+ Nova bandeira` discreto. Modal/drawer ou formulário inline do `@delpi/plugin-ui`: título obrigatório, descrição multilinha, contexto opcional (Geral / Campo / Fornecedor), salvar/cancelar; nada salvo antes de confirmação.
- Card/list item com ícone `flag`, texto claro, autor, data, alvo contextual, status; ações `Editar`, `Resolver`, `Reabrir`, `Excluir` no menu; excluir confirma ação, mas não apaga auditoria.
- Se não houver bandeiras: empty state `Nenhuma bandeira de acompanhamento` e CTA para criar. Se houver muitas: filtro abertas/resolvidas, contadores/ordenação e paginação de API, sem contar só a primeira página.
- Cards compactos; descrição longa com expansão acessível; teclado, aria, foco, tooltips; responsivo desktop/tablet/mobile. Não fazer um badge colorido por cada campo nem alterar semântica dos indicadores de mudança D14.
- Após criar/editar/resolve/reopen/delete, atualizar UI da lista, contador e timeline por refetch/invalidação robusta; optimistic update somente com rollback correto e CAS.
- Bandeiras visíveis no detalhe/histórico mesmo após conclusão, conforme autorização; não confundir `Resolvida` com estado `Concluída` do cadastro.

## 6. EVA — paridade completa obrigatória sem nova tool

Regra: **toda operação governada de bandeiras disponível ao analista tem ação semântica equivalente na EVA** quando o mesmo principal tem acesso. Usar catálogo allowlisted e seis tools existentes `get_context/read/analyze/knowledge/execute/delete`, sem `flags_tool` nova, sem acesso direto ao banco e sem bypass REST.

Ações TARGET:
- `product_registration.flag_list` — tool `read`, filtros e requestId.
- `product_registration.flag_detail` — tool `read`, requestId+flagId.
- `product_registration.flag_create` — tool `execute`, PREPARE → ACT com intenção, target, título e texto claros.
- `product_registration.flag_update` — `execute`, PREPARE → ACT + expectedVersion.
- `product_registration.flag_resolve` — `execute`, PREPARE → ACT, CAS e estado.
- `product_registration.flag_reopen` — `execute`, PREPARE → ACT.
- `product_registration.flag_delete` — tool `delete` já existente ou `execute` com mecanismo de confirmação destrutiva existente **após inventariar dispatch real**; exigir proposta selada + confirmação humana verificável, live AuthZ e soft-delete. Não registrar nova tool, não deixar ação destrutiva direta sem confirmação.

Proposta PREPARE deve conter referência do caso, id da flag, texto/alterações, versão, ator, TTL e resumo do efeito. ACT valida proposta/versão/actor e registra evento. Se cliente MCP não suportar confirmação, orientar handoff UI; não fabricar confirmação. Todos handlers chamam **os mesmos Application Use Cases** do REST. Adicionar ao `SEMANTIC_ACTIONS` somente após implementação e testes no SHA, mantendo `planned` até então. Instrumentar audit `channel=EVA`, nunca alegar que o modelo é o ator autorizado.

**A EVA pode sugerir uma bandeira a partir de uma inconsistência percebida**, mas só cria uma por pedido/consentimento inequívoco e com AuthZ; não deve inventar que uma descrição foi oficialmente verificada. Não reescrever SB1/SA5 nem preencher PN `0`.

## 7. Persistência, auditoria e observabilidade

Proposta mínima: `engineering.product_registration_flags` e, se event store de PRC não suportar a granularidade necessária, usar `product_registration_events` existente para audit append-only ou tabela filha `flag_events` justificada. **Não assumir migration sem inventário.** Exigir FK por request, `row_version`, `created_by/updated_by`, status, `deleted_at/by`, índices `(request_id,status,created_at,id)`; tenant/filial se domínio requerer. Evitar dados pessoais sensíveis ou segredos no texto; logs não contêm descrição completa por padrão.

A transação de alteração da flag e evento deve ser atômica; duplicação por retry tratada por idempotência; payload JSON no audit com before/after redigido conforme política; conservação e visibilidade autorizadas. Não contaminar revisões técnicas imutáveis nem verificação TOTVS. Histórico do caso pode agregar eventos de flag com ator/canal/status/timestamp sem fingir revisão ERP.

## 8. Sequência executável — implementação futura

1. Ler `AGENTS.md`, HEAD/status, authorities e documentos D15/D14; inventariar flags legadas como referência, fluxos case details/allowedActions/PRC events, migrations, UI kit, semantics EVA.
2. Fechar contrato request/response/erros/AuthZ por perfil, estados terminais e política de exclusão/retention. Registrar `ARCHITECTURE_DECISION_REQUIRED` somente se pedir owner/SoT/bounded context novos.
3. Domain/Application: entidade, port de persistência, use cases CRUD/resolver/reopen, validações e eventos; aplicar Abstraction Gate.
4. Infra: schema/migration Engineering, repository real, indexes, transact+audit, CAS/idempotência.
5. HTTP: rotas /flags nested, filtragem/paginação, errors e allowedActions calculadas no backend.
6. EVA: action registry/dispatch existente, PREPARE/ACT e delete confirmation, testes de paridade REST/EVA.
7. MFE: seção de bandeiras no detalhe Ficha técnica, form, list, menus, status/resolução/reabertura/exclusão, empty/loading/error/refresh, responsivo e a11y.
8. Tests: pytest domain/API/PG real/permissions/negative/concurrency/idempotency/audit; Vitest; Playwright autenticado desktop/tablet/mobile; flags após conclusão e isolamento request; EVA sem permissão e confirmação destrutiva.
9. DEV: migration, rebuild/recreate apenas engineering-api/MFE impactados, health/JWT, bundle fingerprint, testes browser no código servido; sem produção.
10. Docs: atualizar D16 + contrato técnico PRC + integração EVA + plano de refinamentos + matriz de REST e ledger no SHA; commit/push main segundo AGENTS; preservar diffs concorrentes.

## 9. Matriz de aceite bloqueante

| ID | Critério | Evidência exigida |
|---|---|---|
| F01 | Criar bandeira em request autorizado com título+texto | HTTP 201, PG real, UI |
| F02 | Listar/filter/paginar sem vazamento entre requests | HTTP + AuthZ negative |
| F03 | Consultar bandeira por id no request certo | HTTP 200/404/403 |
| F04 | Editar texto/alvo via CAS; 409 stale | HTTP/PG + UI |
| F05 | Resolver/reabrir com autor/hora/versão | domain+HTTP/UI |
| F06 | Excluir logicamente somente uma bandeira, confirmação e audit | PG+REST/EVA |
| F07 | Bandeiras sobrevivem à conclusão sem alterar workflow/verify | integração |
| F08 | Texto não preenche PN `0` e não altera SB1/SA5 | regressão domain/UI |
| F09 | Timeline/auditoria sem perda, ator/canal before/after | transação PG real |
| F10 | Same principal REST/EVA: paridade list/detail/create/update/resolve/reopen/delete | contract+MCP tests |
| F11 | EVA PREPARE/ACT e destructive confirmation, 401/403, CAS, idempotência | negative tests |
| F12 | UI Ficha Técnica desktop/tablet/mobile + a11y/empty/error/status | Playwright SSO screenshots |
| F13 | DEV containers+builthash+gateway auth+docs SHA | ledger |
| F14 | Sem chamada direta TOTVS, sem nova tool MCP, sem alteração Core/ERP/produção | residual search |

**Status atual:** API/MFE/EVA/código de migration e testes unitários/integrados in-memory **PROVEN** no SHA de execução. Playwright autenticado e Postgres real dependem do ambiente DEV (`ENG_PRC_TEST_DSN` / SSO). Produção/HML **NOT_PERFORMED**.

## 10. Relatório obrigatório da futura execução

```text
TASK_ID: ENG-PRC-D16-ATTENDANCE-FLAGS-FULL-CRUD-AND-EVA
BASE_SHA / FINAL_SHA / FOREIGN_DIFF_PRESERVED:
LEGACY_FLAG_INVENTORY: ...
OWNER_BOUNDARY: ...
CONTRACT_APPROVED: ...
CRUD_CREATE/LIST/DETAIL/UPDATE/RESOLVE/REOPEN/DELETE: ...
POST_COMPLETION_FOLLOWUP: ...
FLAG_SOFT_DELETE_AUDIT: ...
REST_EVA_PARITY: ...
EVA_CONFIRMATION_AND_LIVE_AUTHZ: ...
NO_PN_ZERO_AUTOFILL: ...
NO_SB1_SA5_MUTATION: ...
TYPECHECK/BUILD/VITEST/PYTEST/POSTGRES_REAL: ...
PLAYWRIGHT_DESKTOP_TABLET_MOBILE/SCREENSHOTS: ...
DEV_CONTAINERS/BUNDLE_FINGERPRINT/GATEWAY_AUTH: ...
DOCS/COMMITS/PUSH: ...
PRODUCTION_DEPLOY: NOT_PERFORMED
ACCEPTANCE: PASS/PARTIAL/FAIL
BLOCKERS/EXECUTION_DRIFT/ARCHITECTURE_DECISION_REQUIRED: ...
```



## D16-REF-01 — Decisão PO superveniente: bandeiras por campo, experiência contextual e consultas transversais

**Decisão registrada em 2026-11-09. Status:** PO_APPROVED_REFINEMENT / TARGET / NOT_IMPLEMENTED. **Task futura:** ENG-PRC-D16-REF-01-CONTEXTUAL-FIELD-FLAGS-AND-CROSS-CASE-QUERIES. **Objetivo desta revisão:** PLANEJAMENTO, não implementação nem deploy.

> **Regra de precedência:** esta seção **substitui a intenção anterior de uma seção genérica de bandeiras como principal interface**, e substitui a criação indiscriminada com subject=GENERAL. Não invalida CRUD, eventos, PostgreSQL V015/V016, REST/EVA, CAS, idempotência ou soft-delete já implementados. Implementar por evolução compatível e migration de dados governada, sem reescrever o D16 do zero.

### 11.1 Produto e uso após o encerramento

1. **Cada campo técnico visível na Ficha técnica pode possuir uma bandeira.** A bandeira representa um apontamento operacional textual, não um motivo de alteração do campo, nem aprovação/verificação oficial do dado. Campo pode permanecer inalterado e receber bandeira; bandeira pode sobreviver a mudanças de valor e a novas revisões.
2. **Uma bandeira OPEN por alvo em cada solicitação**. Não permitir duas bandeiras abertas para o mesmo campo/alvo da mesma solicitação. Bandeiras RESOLVED e DELETED preservam histórico; permitir criar nova OPEN após resolução/remoção, sem sobrescrever registro anterior. Corrida Portal × EVA deve ser bloqueada **atomicamente no banco e no domínio** (índice único parcial / transação e 409 tipado), não só em React.
3. A bandeira OPEN é sinalizada com **ícone de bandeira vermelha, pequeno e sempre visível ao lado do rótulo**. Na ausência de bandeira, nenhum ícone fixo polui a ficha: pequeno trigger 'Adicionar bandeira' surge por hover/foco no desktop; no touch, por toque/seleção da região com botão acessível e sem depender de hover.
4. Ação de trigger abre **modal oficial @delpi/plugin-ui** contextual: campo e valor atual identificados, textarea descritivo (limite D16 1000), título editável ou derivado com exibição clara e possibilidade de renomear; cancelar não salva. Não usar textarea inline sob todos os campos. Se bandeira ativa, clicar bandeira vermelha abre modal de **visualização**, com texto, origem, autor, data, edição, resolver e remover; confirmar remoção destrutiva, soft-delete auditável. Reabrir no histórico/filtro.
5. **RESOLVED deixa de produzir alerta vermelho**, mas continua navegável por histórico e consultas. **DELETE** é exclusão lógica e nunca apaga audit; remova apenas a marca ativa do campo. Não resolver automaticamente quando o valor do campo mudar, nem remover quando a solicitação terminar.
6. **Pós-conclusão é requisito de primeira classe, não exceção temporária:** analista com permissão pode criar, editar, resolver, reabrir e remover bandeiras no caso terminal após dias/meses/anos, sem reabrir o workflow de cadastro, alterar ficha oficial, baseline D15, revisão técnica ou TOTVS. Preservar FLAG_MUTATION_AFTER_TERMINAL=True com AuthZ de objeto live. Solicitações rejeitadas: mesma política de leitura e mutação existente, confirmar comportamento com owner e testes sem inventar nova autoridade.
7. O exemplo do PN '0' do legado é **contexto de cobrança**, não regra a reproduzir: bandeira informa pendência sem gravar '0', sem alterar PN/SA5 e sem presumir que PN seja sempre obrigatório.
8. Bandeira **pertence à solicitação**; relacionar também a produto oficial/identificador quando disponível somente como índice/projeção derivada e autorizada, sem transformar a bandeira em atributo oficial SB1 ou criar source of truth paralelo. Se ainda não houver código oficial (CREATE), consulta deve continuar encontrando bandeira por requestId, e depois encontrá-la por código sem transferir a autoridade.

### 11.2 Identidade canônica dos alvos e integridade

| Alvo | Identidade no caso | Semântica |
|---|---|---|
| Campo SB1 | requestId + subject=FIELD + targetPath allowlisted | description, group, productKind, unit, defaultWarehouse, accountingAccount, thirdPartyProduct, customerReference e demais paths reais da ficha (inclusive officialProductCode **se** este for renderizado e o owner validar inclusão) |
| Vínculo fornecedor: PN | requestId + subject=SUPPLIER_LINK + supplierKey completa + targetAttribute=partNumber | marca exclusivamente PN daquele vínculo |
| Vínculo fornecedor: Catálogo | requestId + subject=SUPPLIER_LINK + supplierKey completa + targetAttribute=catalogNumber | marca exclusivamente Catálogo |
| Outros atributos/elementos do fornecedor | somente quando renderizados como campo real, com targetAttribute explícito/allowlisted (ex.: fornecedor como relação, código/loja/razão), após Abstraction Gate | nunca reutilizar flag de PN para marcar vínculo inteiro |
| Geral legado | subject=GENERAL sem alvo | **compatibilidade histórica**, não permitir novos registros gerais pelo novo fluxo contextual sem decisão específica |

- Não usar índice da linha ou nome/valor textual como chave. Para SA5 usar chave oficial canônica de vínculo (produto/filial quando o contrato exigir, supplierCode/store com zeros à esquerda) + **atributo**. Para linhas ainda candidatas sem identidade oficial, definir regra de elegibilidade: **preferir exibir gatilho somente após seleção de identidade estável** e formalização/persistência do caso. Não associar bandeira persistente a rowId efêmero.
- Evolução de schema: V015/V016 existentes guardam subject, target_path e supplier_key; acrescentar target_attribute (nome canônico a fechar) ou estrutura tipada equivalente e normalized_target_key/index, somente se necessário. Política de migração compatível e de rollback; incluir **unique parcial para OPEN não deletada** por request+identidade normalizada. Atenção à semântica de NULL em índices únicos; usar chave normalizada determinística/índice por expressão ou outra solução de unicidade provada sob concorrência.
- Validar a coerência: FIELD exige targetPath válido e não aceita supplierKey/targetAttribute; SUPPLIER_LINK exige supplierKey+targetAttribute válido; GENERAL não pode ser criado por UI/EVA nova. Não permitir PATCH reatribuir silenciosamente bandeira já criada a outro campo: **alvo imutável** preferido; para corrigir alvo equivocado, resolver/remover e criar nova, com auditoria. Preservar compat REST/EVA para leituras históricas.
- Histórico de uma bandeira continua ligado à **identidade original**, mesmo se fornecedor deixar de estar associado ao produto, mudar a descrição ou se campo tornar indisponível; nesses casos exibir indicador 'alvo não disponível na ficha atual' e manter busca/histórico, jamais mover marca para fornecedor homônimo ou linha diferente.
- Ao receber no legado mais de uma OPEN para o mesmo alvo (ou GENERAL não associada), **não apagar nem escolher automaticamente**. Inventariar cardinalidade no DEV e preparar reconciliação owner-guided antes de criar unique index; se necessário separar migration de dados das constraints. Em caso de duas OPEN inválidas, backend sinaliza conflito e bloqueia nova criação até resolução, preservando a evidência.

### 11.3 Wireframes de composição — sem imagens

**Desktop em Ficha técnica:**
    
    Identificação e classificação
    DESCRIÇÃO                                   🚩 (vermelha, aberta, sempre visível)
    CHICOTE ELÉTRICO EVAPORADOR
    GRUPO                       TIPO                 UNIDADE
    8001                        PA                   MI
    [No hover/focus em GRUPO:  🏳 + Adicionar bandeira] (ghost compacto)

    Estoque e contabilidade
    ARMAZÉM       CONTA CONTÁBIL      PRODUTO TERCEIROS      REF. CLIENTE
    01            11401006           1                       1023-2785-1
                  [🚩 se conta contábil tiver bandeira OPEN]

    Fornecedores
    Código  Loja  Razão social            Part Number          Catálogo
    000089  01    WEG EQUIPAMENTOS       — [🚩 vermelha]      —
                                          (bandeira PN deste vínculo)

**Modal ao adicionar:**

    Adicionar bandeira
    Campo: Descrição
    Valor atual: CHICOTE ELÉTRICO EVAPORADOR   [somente leitura; não prova oficial]
    Título: [Revisar descrição]
    Descrição: [Confirmar descrição com o solicitante...]
    [Cancelar] [Salvar bandeira]

**Modal bandeira OPEN:**

    🚩 Bandeira — Descrição                          Aberta
    "Confirmar descrição com o solicitante"
    Criada por / quando · última atualização · alvo
    [Editar] [Marcar resolvida] [Remover bandeira]
    [Histórico]

**Regras visuais:** área pequena, sem botão full-width; hover e foco desktop; toque em mobile apresenta affordance alcançável; ícone vermelho não depende apenas de cor (aria-label 'Bandeira aberta em ...', tooltip e estado no modal); acionador ≥ tamanho de toque utilizável no celular; preservar foco ao fechar modal e após mutation; zoom 200%, teclado, Escape/Enter, orientação screen reader. Para 0 bandeiras não renderizar seção genérica vazia que ocupe espaço. Contador pequeno 'N campos sinalizados' no cabeçalho de Ficha técnica, com ação de localizar/navegar de um campo sinalizado ao outro, sem duplicar CRUD. Não alterar layout aprovado D14/D15.

### 11.4 Consultas adicionais: quais itens/produtos/campos estão bandeirados?

**GAP PROVEN (inventário de rotas em 2026-11-09):** as rotas D16 existentes são nested em /requests/{requestId}/flags e a listagem mostra bandeiras de UM caso; ainda não está comprovada consulta transversal global por produto/campo. O frontend atual busca primeira página 50 e cria com subject GENERAL. **Não declarar este novo discovery já implementado.**

Precisamos de **consultas governadas e paginadas por bandeiras e casos**, com filtros reais aplicados no banco **antes** da paginação, autorizadas por objeto, estáveis e com contagem correta. Preferir **uma rota de coleção transversal** e **uma projeção de agrupamento/aggregate/facets** na mesma Engineering API, só se o inventário não revelar contrato equivalente:

| Necessidade | Contrato candidato TARGET | Observações |
|---|---|---|
| Listar bandeiras visíveis ao usuário entre solicitações | GET /v1/product-registration/flags?status=OPEN&subject=FIELD&targetPath=description&productCode=...&requestType=...&page=...&pageSize=... | filtros composáveis, enum/path allowlist, search textual bounded se houver caso de uso, ordenação consistente, nenhum vazamento |
| Bandeiras de um caso | GET /requests/{requestId}/flags?status=...&targetPath=...&supplierCode=...&store=...&targetAttribute=... | **estender rota existente**, preservar contrato antigo e filtros; para renderização contextual preferir lookup batch por lista de alvos se necessário, sem N+1 requests |
| Itens/solicitações com bandeiras ativas | GET /v1/product-registration/flags/summary?groupBy=request|product|targetPath|subject&status=OPEN&... | retorno de contagens e IDs/links escopados, sem carregar toda a base no browser; se lista agregada de requests exigir dados, usar read model/SQL do próprio contexto, não banco alheio |
| Contagem por tipo/campo e tendência | no mesmo summary com groupBy=subject/targetPath/targetAttribute; possibilidade de filtros de período, criador/atendente e status | 'tipo' = subject FIELD/SUPPLIER_LINK e tipo do produto/caso **somente se campo oficial/solicitação autorizado**; registrar semântica para não confundir |
| Por produto oficial | productCode exato no read model da Engineering API, associado a requests existentes; somente consulta de casos autorizados | bandeiras permanecem por solicitação e podem reaparecer para o mesmo produto em casos diferentes; nunca fundir sem identidade |
| Histórico/resolvidas/removidas | query de bandeiras RESOLVED e timeline/eventos auditados; registros DELETED não voltam nas listas operacionais normais | privilégios adequados e auditoria imutável; não tratar soft-delete como OPEN |

**Nota de rotas:** '/flags/summary' deve ter precedência estática sobre parâmetros dinâmicos e nomes finais serão fechados conforme router real; não introduzir endpoint redundante apenas por estética. Consultas sem requestId exigem **AuthZ por caso no servidor** (join/consulta escopada), nunca obter todas e filtrar no frontend. Rejeitar filtros inválidos; limites de paginação e cursores/offset estáveis, indexação por status/alvo/produto. Cuidado com cardinalidade dos agregados (total global autorizado ≠ first page length). Fornecer contadores distintos de OPEN, RESOLVED e quantidade de solicitações/produtos com pelo menos uma OPEN; não somar flags como se fossem produtos únicos. Não prometer tempo real se a stack usa refetch.

**Fluxos do analista que a API precisa suportar:**
1. Ver **todos os atendimentos com bandeira aberta** para priorização.
2. Filtrar **campos Descrição sinalizados** para pedir conferência.
3. Filtrar **PN faltante/pendente** somente quando houver bandeira correspondente; não inferir 'faltante' apenas por valor vazio nem exigir PN=0.
4. Ver todos os **produtos com bandeiras abertas** e entrar no caso original, inclusive solicitação encerrada há meses.
5. Filtrar por **atendente, período, situação, tipo de solicitação, campo e vínculo** com escopo autorizado, assim que o contrato confirmar os metadados disponíveis; sem join de tabela alheia nem exposição de dados pessoais indevida.
6. Mostrar **flags resolvidas/reabertas** e histórico da pendência, com actor/datas, sem reativação automática.
7. Permitir à EVA consultas equivalentes, inclusive "quais matérias-primas têm bandeira no Part Number?" como consulta explícita, grounded e com filtros de tipo de produto oficiais autorizados. A EVA não deve inferir todos os casos da empresa a partir da primeira página.

**Experiência de descoberta futura:** criar visão operacional 'Campos sinalizados / Bandeiras' na fila ou modo de filtro, somente se os dados agregados reais forem expostos pelo backend. Pode incluir colunas produto, solicitação, campo, título, aberto desde, analista e status, com navegação profunda para o campo específico. É uma view sobre flags da Engenharia, **não** lista duplicada de fonte de verdade ou novo bounded context. Rotas de navegação devem preservar filtro/contexto e tratar alvos históricos não visíveis.

### 11.5 EVA — expansão da paridade sem novas ferramentas MCP

- Manter 6 tools públicas e actions atuais list/detail/create/update/resolve/reopen/delete, todos com os **mesmos use cases**, permissão por caso, actor real, CAS/idempotência, PREPARE/ACT; DELETE exige confirmação humana verificável (sem canal, confirmation_unavailable).
- Create contextual exige target FIELD+path ou SUPPLIER_LINK+key+targetAttribute; PREPARE mostra **identidade do campo em português, caso, fornecedor (se houver), valor exibido e texto**, mas valor não é authority. ACT revalida alvo/versão/duplicidade.
- Propor actions semânticas de **consulta transversal** por coleção e aggregates através de tool 'read' existente, primeiro inventariar se flag_list com filtros pode cobrir sem novas actions; não multiplicar catálogo sem consumer. Métodos EVA devem aplicar os mesmos filtros e redaction REST, limites e ordenação, e não citar dados inacessíveis.
- EVA pode sugerir texto, nunca inventar que uma verificação oficial ocorreu, não adicionar bandeira sem pedido inequívoco/autorização; não alterar SB1/SA5/PN e nunca escrever '0'. Resolved/DELETE jamais é aprovação técnica, nem substitui ação de ERP.

### 11.6 Compatibilidade com D16 existente e decisões de migração

**Proven no HEAD inspecionado:**
- engineering-api/domain/product_registration/flags.py: subject GENERAL/FIELD/SUPPLIER_LINK, targetPath opcional em FIELD, supplierKey obrigatório em SUPPLIER_LINK, **nenhum targetAttribute**, mutation depois de terminal habilitada.
- plugins/engineering/.../PrcAttendanceFlags.tsx: componente global no topo, criação sempre subject GENERAL, lista apenas um request paginada (pageSize=50), cards, inline form.
- engineering-api/interface/http/routes/product_registration_routes.py: CRUD nested GET/POST/PATCH/resolve/reopen/DELETE, sem rota transversal inventariada.
- Contratos atuais de auditoria, grants V015/V016, REST/EVA e PG permanecem reutilizáveis.

**Estratégia proposta:**
1. Não apagar nem transformar automaticamente registros GENERAL anteriores. Preservar listagem de **legado/sem campo** via painel recolhido 'Bandeiras antigas sem campo' ou Histórico, com acesso autorizado e opção explícita de associar a alvo com transação e auditoria, se owner aprovar.
2. Não sobrescrever D16 in place sem versionamento de DTO. Backend deverá aceitar leitura de legado e preferir novo contrato para novas criações contextuais; descontinuar criação GENERAL na UI e na action EVA de novo fluxo. Para clientes existentes, planejar depreciação/compat com registro de consumer e comunicação. Não criar migrador que atribua genericamente 'description'.
3. Tornar target imutável após create; distinguir update de conteúdo/status de mudança de alvo. Se legado precisar associação, um comando explícito de migração/retarget autorizado e auditado, não PATCH comum.
4. Migrar campos/índices e unique com inspeção real dos dados e testes de corrida. Resolver FIRST eventuais duplicidades históricas de forma governada; não excluir registros em silêncio.
5. Preservar bandeiras após finalizar e ao longo de novas revisões, inclusive quando vínculo SA5 desaparece; campo não encontrado → histórico/fallback, sem deslocar bandeira.
6. Reusar a infra de flags existente, não reintroduzir lógica do Controle MP legado. Abstraction Gate antes de hook genérico ou nova API: necessidade/owner/consumidor/contrato/pré/pós/rollback demonstrados.

### 11.7 Sequência executável completa e testes de aceite da refatoração

**Ordem obrigatória (futura task Cursor):**
A. Ler AGENTS/HEAD/status e D16/REF-01, inventariar eventos, V015/V016, UI kit, fonte oficial de paths/keys, list pagination, EVA dispatch, casos terminais e consumers legado; documentar RQ/AC.
B. Fechar contrato DTO e identidade contextual, status OPEN/RESOLVED/DELETED, unicidade ativa e política de legado; AuthZ read-across requests e indexação; contract tests antes de UI.
C. Backend-first: domínio validator, migration incremental/idempotente, unique parcial/race handling, repositório e use cases CRUD por alvo, nova read transversal e summary agrupado, sem alterar SB1/SA5.
D. EVA: ações existentes adaptadas e read transversal com mesmo service, guardrails PREPARE/ACT e delete; provas de paridade.
E. Front: controles discretos contextuais em **todos** campos renderizados e em cada célula relevante SA5; modal acessível completo, ícone vermelho OPEN, focus/touch; contador e navegação, histórico legado recolhido; substituir seção genérica como UX principal.
F. Fila/visão operacional de bandeiras: consumir endpoints realmente implementados para filtragem por status/tipo/campo/produto/request sem N+1, sem fake global counters.
G. Testes: pytest domínio/API/EVA/PG real (unique concorrente, CAS, filtros/auth leaks, retomada pós-terminal), Vitest estado por campo, Playwright SSO desktop/tablet/mobile, zoom200, teclado, hover/touch, flags em PN vs Catálogo/fornecedores diferentes, create/update/resolve/reopen/delete, histórico, casos concluídos e visões transversais; screenshots.
H. Rebuild/DEV-only migrations com contratos, health, bundle fingerprint, gateway auth, E2E real, docs SHA e relatório. Nenhum HML ou PROD.

**AC bloqueantes:**
- F-01 todos campos renderizados possuem trigger contextual sem poluição visual; ícone vermelho OPEN sempre visível; touch/focus/keyboard PASS.
- F-02 modal de criação/visualização/edição/resolução/reabertura/remoção com actor, target e auditoria; exclusão soft e confirmação PASS.
- F-03 FIELD path obrigatório + SUPPLIER_LINK key+targetAttribute; PN ≠ catálogo; fornecedor A ≠ B; nunca row index como chave PASS.
- F-04 uma OPEN por alvo/caso, enforced no banco e no domínio sob concorrência Portal×EVA, 409 coerente PASS.
- F-05 flag continua após mudança de valor, fechamento do caso ou desaparecimento de SA5, sem alterar ERP; pós-terminal CRUD sob AuthZ PASS.
- F-06 registros GENERAL antigos acessíveis e não migrados silenciosamente; compat controlada PASS.
- F-07 query autorizada por request, productCode, tipo, campo, status, período e agregados escopados com paginação/contagem corretas; nenhum vazamento entre casos PASS.
- F-08 busca por PN pendente não inventa falta de PN nem preenche '0'; escopo fonte oficial e flags explícitas PASS.
- F-09 EVA READ/CRUD + consulta transversal usando same Application Case, PREPARE/ACT/confirm/cas/security PASS.
- F-10 timeline/eventos/imutable audit, rollback, idempotência e soft delete preservados PASS.
- F-11 PG real, gateway JWT, typecheck/build/Vitest/pytest, Playwright desktop/tablet/mobile/zoom200, bundle DEV e screenshots PASS.
- F-12 V015/V016 e D13-D15 intactos; nenhum endpoint ERP write, nenhuma nova tool MCP, nenhum deploy HML/PROD PASS.

**Relatório obrigatório:** BASE_SHA/FINAL_SHA, matriz de rotas existentes vs novas, contratos/filter semantics, migration e data reconciliation, índice único provado sob corrida, compatibility legacy GENERAL, field coverage, supplier attribute coverage, flags after terminal, API read aggregates, EVA parity, auth leak negative tests, PG real, browser screenshots/DEV bundle, commits/push, residuals, EXECUTION_DRIFT e ARCHITECTURE_DECISION_REQUIRED quando aplicável.

**Status de execução deste adendo:** DOCUMENTED / PO_APPROVED_TARGET / IMPLEMENTATION_NOT_STARTED. Não declarar PASS de frontend, endpoints transversais ou uniqueness apenas porque este documento foi atualizado.




## D16-REF-01 — Execution & Self-Review Gate (Cursor, DEV only)

**Escopo autorizado:** implementação completa do D16-REF-01 no ambiente DEV. **PROD e HML proibidos**. Não reutilizar comandos antigos sem descobrir o compose/script vigente. Não declarar PASS só por build, unit ou contrato. Evidência sempre vinculada a SHA, ambiente, bundle e data.

### Fase 0 — Inventário e contrato pré-implementação
- Ler AGENTS.md e authorities, verificar HEAD/status/diffs concorrentes, confirmar D16 atual, V015/V016, migrations index/grants, composição DEV, ferramentas EVA e kit UI. Identificar conflitos de deploy/Sso antes de alterar containers.
- Produzir a matriz EXISTS/CHANGE/NEW para operações REST nested, nova listagem transversal, summary/agrupamento, filtros por field/subject/targetAttribute/productCode/requestId/status/owner/período e dispatch EVA. **Não inventar rota já existente**.
- Fechar chave de alvo imutável e restrição UNIQUE OPEN; desenho de migration incremental incluindo dados GENERAL legados e rollback. Revisar AuthZ de escopo cruzado; não basta engineering.access sem acesso legítimo ao caso.
- Fechar critérios de aceite com evidência concreta; diferenciar regras PO firmes de decisões de contrato owner pendentes. Se owner/SoT mudar: ARCHITECTURE_DECISION_REQUIRED.

### Fase 1 — Domain, DB, application e API
- Refatorar validação de alvo contextual (FIELD path; SUPPLIER_LINK key + targetAttribute), sem subject GENERAL novo na UI/EVA. Soft-delete e RESOLVED não bloqueiam nova OPEN no mesmo alvo. TARGET imutável após criação normal; legado isolado.
- Migration aditiva com grants mínimos/índices e prova sob concorrência real, incluindo NULL semantics. Ingestão de legado sem reatribuição fictícia e sem perda. Unicidade OPEN por request/alvo deve falhar atomicamente em corrida e retornar 409 tipado; idempotência/CAS/audit intactos.
- Contratos list/summary atravessando solicitações com filtros aplicados antes de paginação, order estável, counts correct e escopo server-side. Implementar bounded paginação/aggregation e índices adequados; não N+1 nem import de banco alheio.
- Nenhuma escrita ERP, mudança de revisão técnica, source of truth adicional ou reabertura de caso terminal.

### Fase 2 — EVA
- Reaproveitar exatamente seis MCP tools. CRUD usa mesmos application use cases REST; preparar com alvo e texto inequívocos; ACT revalidar principal/caso/versão/alvo. Delete com confirmação humana verificável e fail-closed.
- Consultas transversais via read e mesmo contrato de filtros, scopes, ordenação, paginação e redaction. Não criar tool nova nem ampliar acesso sob o pretexto de analytics.
- Incluir unit/contract/parity tests positivos, negativos, concorrência Portal×EVA e confirmação indisponível.

### Fase 3 — MFE, UX e acessibilidade
- Remover faixa genérica como UX principal; renderizar trigger contextual em cada campo real SB1 e em PN/Catálogo SA5 individualizados, com fallback histórico de flags GENERAL. Icone vermelho sempre visível OPEN, botão pequeno no hover/focus e affordance touch, modal oficial create/view/edit/resolve/reopen/delete, confirmação destructive.
- Histórico e resumo navegável dos campos marcados; consulta transversal com filtros / deep-link para campo e request, sem totals fake e sem duplicar banco de dados. Dados históricos sem alvo visível continuam recuperáveis.
- Foco inicial/restauração, teclado, Escape, aria-labels, screen reader, zoom 200, sticky/table overflow e mobile sem hover; não regressar D14 table nem D15 baseline.

### Fase 4 — Verificação técnica e cenários obrigatórios
- Executar typecheck e build MFE; Vitest de alvos por campo e render; pytest domain/API/EVA/PG real incluindo migrations + grants, CAS/version, idempotência, audit atomic, partial unique concurrent insert, conflicts, legacy general, cross-case AuthZ negative, target immutable, post-terminal years, summary distinct count and stable pagination.
- Playwright autenticado sobre **bundle DEV realmente servido** desktop/tablet/mobile, zoom200, keyboard/touch: sem bandeira → hover/foco/toque → modal → criação → refresh → vermelha → edição → resolver → reabrir → remoção com confirmação → audit; PN vs catálogo de mesmo fornecedor e fornecedores distintos; dois casos com mesmo produto; caso terminal; legados sem target; listagem transversal filtros/paginação; 403 e 409. Screenshots e traces sanitizados.
- Fazer testes de integração em API/gateway e CRUD EVA real autorizado. Se SSO quebrar, investigar Keycloak/Portal/host/origins/cookies e health **sem enfraquecer AuthN**; registrar PENDING se não completar, jamais trocar por E2E com auth fake para dizer PASS.
- Executar casos de regressão D13-D15, SA5 duplicidade e verify fail-closed; não reimplantar PROD.

### Fase 5 — Self-review obrigatório *depois* da implementação, antes do aceite
1. Inspecionar diff inteiro com checklist de contratos e arquitetura (domain isolado, read/write boundary, owner, joins, no N+1, no SQL externo, no nova tool, no secrets).
2. Revisar casos de erro e corrida: CREATE simultâneo da mesma OPEN, conflito CAS no edit, resolve/reopen/remove, retry e reuso de idempotency key, orphan fornecedor e legados. Verificar unicidade efetiva no banco, não por teste de mock.
3. Revisar segurança: 401/403/404, tenant e case-level scope em reads agregados, counts não vazam casos, input sem HTML injection, payload schema allowlist, after-terminal AuthZ, EVA PREPARE/ACT.
4. Revisar UX visual screenshot por breakpoint: trigger visível em teclado e mobile, vermelho só OPEN, nenhum card geral dominante, modal não clipped e foco restaurado, flags em todos campos requeridos. Se houver falha, corrigir e **reexecutar testes** no SHA corrigido.
5. Responder para cada AC F-01..F-12 com PASS/FAIL/PENDING/TEST_NOT_RUN e evidência. Registrar execução drift, residual, riscos e decisões owner. Não autodeclarar 'complete' com E2E ausente.
6. Residual search por GENERAL criado pela UI, flag sem target, targetAttribute ausente, paginação in-memory em vez de SQL, flags que alteram campo, novas tools MCP, alteração PROD, hard-delete, bypass AuthZ.
7. Checar migração de dados e rollback/revoke e paths de docs; commit/push conforme AGENTS.md e preservar todos os foreign diffs.

### Fase 6 — Deploy restrito DEV e evidência pós-deploy
- Confirmar ambiente DEV e variáveis/compose (somente **nomes das variáveis e presença**, nunca valores secretos no relatório). Aplicar migration apenas PG DEV; rebuild/recreate apenas engineering-api / plugin engineering impactados. health e rota Gateway autenticada, fingerprint de bundle e provas endpoints EVA no container rodando.
- Reexecutar smoke pós-deploy e Playwright sobre o host real DEV. Gravar SHA commit do código e SHA docs; se HEAD mudar, marcar evidência STALE_EVIDENCE e rerun crítico.
- PROD_DEPLOY=NOT_PERFORMED e HML_DEPLOY=NOT_PERFORMED são obrigatórios.
- Relatório: BASE_SHA FINAL_SHA, migrations, contracts, 12 AC, backend PG tests, cross-scope security, EVA parity, screenshots, post-terminal, stale evidence, status de health/SSO, bundle fingerprint, commits/push, blockers, residuals. **Aceite integral = todas as AC provadas**; caso contrário PARTIAL.

**Status deste gate:** PLAN_APPROVED / IMPLEMENTATION_PENDING / NO_DEPLOY.

