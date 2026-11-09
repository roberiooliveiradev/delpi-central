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
