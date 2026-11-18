# Product Registration — contrato técnico do MVP Engineering-only

> **PRC_CURRENT_MASTER_2026_11_18 — fonte única para a evolução de automação de cadastro e similaridade técnica:** o plano que estava em `docs/12-roadmap-e-evolucao/controle-mp/EVOLUCAO.md` foi consolidado NESTE documento do Portal Engenharia, por decisão explícita do PO. O arquivo separado foi removido após a migração; histórico disponível no Git. Atualizações futuras de CREATE/UPDATE TOTVS, SA5, avaliação normativa e decisões de deduplicação devem ser incrementadas no capítulo `PRC-TOTVS-AUTOMATION-AND-NORMATIVE-SIMILARITY` abaixo. Os contratos oficiais dos owners permanecem em suas fontes próprias, referenciados daqui; este adendo não autoriza write/deploy.


> **Decisão funcional superveniente PRC-REF-022 (2026-11-10):** fluxo único Enviada → Em atendimento ⇄ Devolvida para correção → Concluída, editor compartilhado create/read/edit. O adendo REF-022 ao final deste documento prevalece sobre fluxos legados contraditórios. `IMPLEMENTED_DEV` (runtime Engineering API + Portal; AuthZ solicitante sem `engineering.access` = `ARCHITECTURE_DECISION_REQUIRED` / `PENDING_OWNER`).

> **Data:** 2026-11-06
> **Estado:** \`TARGET / CONTRACT_SPECIFIED / ARCHITECTURE_DECISION_REQUIRED\` para o ownership; \`IMPLEMENTATION_NOT_STARTED\`; \`TEST_NOT_RUN\`.
> **Precedência:** especificação executável do vertical \`product-registration\` dentro do Portal Engenharia. Complementa [ROADMAP](./ROADMAP.md), [IMPLEMENTATION-PLAN](./IMPLEMENTATION-PLAN.md), [DATA-MODEL](./DATA-MODEL.md) e o [inventário](./PRODUCT-REGISTRATION-COMPLETE-INVENTORY.md). Substitui **somente para este vertical** a intenção antiga de BFF runtime com a API Flask ou com \`requests-api\`. Não revoga decisões de outros módulos da Engenharia.
> **Limite:** esta especificação não autoriza migrations, alterações de código, infraestrutura, escrita ERP, migração de legado ou deploy; implementação depende de confirmar owners, padrões atuais de migration/DB, contratos oficiais de leitura ERP e gates de segurança.

## 1. Decisões de produto travadas e fronteiras

- Produto: **Controle e Cadastro de Produtos**, técnica \`product-registration\`, primeiro domínio concreto \`raw_material\`; rótulos de UI em pt-BR; nomes técnicos novos, rotas, DTOs, tabelas e campos em inglês.
- Primeira etapa: **tudo que gerencia entrada, fila, atendimento técnico, drafts, verificação, revisão e auditoria reside na \`engineering-api\`**, com UI no \`plugins/engineering\`. Sem chamar \`requests-api\`, \`my-requests\`, API Flask ou banco do Controle MP em runtime; migração e conectores de origem são posteriores.
- Contrato de entrada versionado independente da origem; homologação inicial pode usar um cliente/harness restrito e autenticado. Contrato de saída versionado **pull/GET** para consulta autorizada de status e resultado; push/evento para outras APIs somente quando houver consumer e delivery contract reais.
- **Cadastro/alteração oficial é manual no TOTVS.** Analista executa a operação no ERP e retorna ao Portal. Ao clicar Concluir, backend consulta **fonte oficial via adapter de leitura autorizado** e confronta os campos relevantes da ficha/alteração com o estado no ERP. Sem confirmação, não conclui nem publica revisão vigente.
- A Engenharia mantém **cópia técnica versionada do último estado oficial validado**, com provenance/freshness; a fonte oficial do produto permanece TOTVS/Domain API. A revisão não é uma segunda autoridade para cadastro ERP.
- \`create\`: obrigatório no intake somente o catálogo acordado da solicitação; código ERP não é obrigatório na abertura. \`update\`: seleção de um ou mais campos, valores propostos e baseRevision; não enviar/revalidar a ficha inteira pelo solicitante. O analista pode completar o draft, mas toda mudança efetiva deve ser explicitamente justificada e verificada.
- \`Part Number\` é \`part_number\` **por fornecedor**, diferente de \`catalog_number\`. No inventário legado corresponde a \`A5_CODPRF\`; \`catalog_number\` a \`A5_CODPRCA\`.
- EVA propõe validações \`DRAFT/CANDIDATE\`, não dá OK, não publica nem escreve no ERP. Busca de semelhantes no preenchimento do solicitante = \`FUTURE\`.
- \`ARCHITECTURE_DECISION_REQUIRED\`: registrar o bounded context operacional de solicitações de cadastro em Engenharia, sem mudar owner de cadastro oficial, Core/Keycloak nem criar dependência de Requests API.

## 2. Arquitetura lógica e divisão por camadas

\`\`\`text
Authorized caller/test harness
    -> /apps/engineering-api/v1/product-registration/intake/requests
plugins/engineering (product-registration UX)
    -> /apps/engineering-api/v1/product-registration/*
         interface/http/routes + schemas (FastAPI)
         application/use_cases (intake, queue, draft, decisions, verification)
         domain/product_registration (state machine, field rules, revisions)
         application/ports (repository, unit_of_work, official_product_reader,
                            identity/permissions, candidate_validator)
         infrastructure/adapters (Postgres, delegated api-delpi, EVA optional)
         PostgreSQL engineering.product_registration_* (operational + audit)
         -> official product reader (READ ONLY) -> api-delpi/domain owner -> TOTVS
Consumer authorized
    -> GET /apps/engineering-api/v1/product-registration/outbound/requests/{id}
No requests-api, My Requests, Flask DB/API in MVP.
\`\`\`

No domain/application imports de FastAPI, SQLAlchemy, DB, JWT SDK, LLM SDK, MCP ou httpx. Adapters implementam ports existentes ou mínimos necessários. Reusar \`delpi_auth\`, \`DownstreamClient\`, observabilidade e regras de migrations do repositório; não duplicar plataforma de auth/audit ou cliente HTTP.

## 3. Identificadores, autorização e convenções transversais

- Prefixo público **candidato alinhado ao root_path existente**: \`/apps/engineering-api/v1/product-registration\`; paths internos FastAPI \`/v1/product-registration\`. Frontend: \`/apps/engineering/product-registration\`, com subrotas internas \`/requests\`, \`/requests/:requestId\`, \`/test-intake\` apenas DEV/HML restrita.
- Keycloak \`sub\` é identidade humana canônica. Origem externa autenticada identifica source/caller e identidade de solicitante por contrato aprovado; client não pode forjar \`requesterSubject\`. \`engineering.access\` é só entrada no Portal, **não** concede criar, processar, concluir ou ler solicitação alheia. Propor granularidades: \`engineering.product-registration.read\`, \`.create\`, \`.process\`, \`.verify\`, \`.admin\`; códigos finais/registro Core precisam de revisão com owner Core antes de implementação.
- Toda rota de escrita checa live AuthZ (Core e política domínio), escopo por resource; leitura também escopada. Analista autorizado vê fila segundo regra de escopo formalizada; **não inferir fila global do legado**. Ausência/falha de permission → fail closed. Roles do Controle MP não são autoridade.
- Header \`Idempotency-Key\` obrigatório em POST intake e operações mutáveis sujeitas a retry; \`If-Match\` ou \`expectedVersion\` obrigatório em mudanças sobre request/draft. \`X-Request-Id\`/correlation propagado.
- Erros padronizados e sem vazamento de payloads/segredos: \`400 malformed\`, \`401 unauthenticated\`, \`403 forbidden\`, \`404 not_found\`, \`409 state_conflict|stale_version|duplicate_external_reference\`, \`422 validation_error|unverifiable_field\`, \`429 rate_limited\`, \`502 official_contract_error\`, \`503 official_unavailable\`, \`504 official_timeout\`. Verificar envelope real \`engineering-api\` antes de codificar, sem inventar segundo padrão HTTP.
- Paginação limit/offset ou cursor seguindo convenção já existente; proposta inicial \`page=1\`, \`pageSize=25\`, teto 100, ordenação estável \`createdAt DESC,id DESC\`; filtros devem estar em allowlist. Prazos/limites finais medidos e versionados em contract review.
- Não expor payload técnico completo em logs; em eventos armazenar diff minimizado e evidência oficial autorizada. Auditoria append-only. Timestamps UTC \`timestamptz\`; UUID em novos IDs, referência ERP \`text\` (preservar zeros à esquerda).

## 4. Mapa completo de rotas do MVP

**Não criar endpoints redundantes para chat, Socket.IO, migração, users/auth, Requests API ou escrita ERP.** Tabela é o contrato alvo; \`/intake\` e \`/outbound\` são as duas portas externas exigidas, e rotas de trabalho são internas à experiência Engineering.

| # | HTTP | Path após \`/v1/product-registration\` | AuthZ funcional | Objetivo / efeito |
|---|---|---|---|---|
| 01 | POST | \`/intake/requests\` | create + source allowlist | Ingerir \`create/update\` de origin autorizado; validação e idempotência; cria caso \`submitted\` |
| 02 | GET | \`/requests\` | read/process + scope | Fila paginada, \`status,type,assignee,source,search,dateFrom,dateTo\` e totais autorizados |
| 03 | GET | \`/requests/{requestId}\` | resource read | Detalhe do caso, original, draft, versão, field changes, allowedActions, ERP verification summary |
| 04 | GET | \`/requests/{requestId}/timeline\` | resource read | Histórico append-only de ações e decisões, paginado |
| 05 | POST | \`/requests/{requestId}/actions/start\` | process | Iniciar atendimento, \`submitted -> in_progress\`, atribuição governada |
| 06 | PATCH | \`/requests/{requestId}/draft\` | process | Alterar draft campo-a-campo com allowlist, CAS, motivo e diff; não publica |
| 07 | POST | \`/requests/{requestId}/actions/request-information\` | process | Registrar campos/razão de pendência; \`needs_information\` |
| 08 | POST | \`/requests/{requestId}/actions/resume\` | process | Retomar caso de \`needs_information\` para \`in_progress\` após correções autorizadas |
| 09 | POST | \`/requests/{requestId}/actions/submit-review\` | process | \`in_progress -> under_review\`, valida completude técnica |
| 10 | POST | \`/requests/{requestId}/actions/reject\` | process | Rejeitar com motivo obrigatório; não altera cadastro vigente |
| 11 | POST | \`/requests/{requestId}/actions/verify-and-complete\` | verify + process | Consulta oficial atual, compara campos e finaliza atomicamente se comprovado |
| 12 | GET | \`/requests/{requestId}/verifications\` | resource read | Tentativas de verificação, resultado e divergências, com dados redigidos |
| 13 | GET | \`/technical-records/{recordId}\` | resource read | Ficha técnica vigente, código ERP, versão e origem da sincronização |
| 14 | GET | \`/technical-records/{recordId}/revisions\` | resource read | Índice de versões e mudanças |
| 14a | GET | \`/technical-records\` | resource read | Produtos acompanhados publicados (PRC-TRACK PROD-01): `page`/`pageSize`/`search` por código oficial (case-insensitive), `updatedAt DESC, id DESC`; somente registros com revisão publicada |
| 15 | GET | \`/technical-records/{recordId}/revisions/{revisionNumber}\` | resource read | Snapshot histórico imutável + diff por campo |
| 16 | GET | \`/reference-data\` | read/create/process | Enum de tipos, campos, allowedPaths, schema version e requisitos por operação; valores oficiais apenas se disponíveis |
| 17 | GET | \`/outbound/requests/{requestId}\` | authorized consumer + resource scope | Contrato externo de status, tipo, resultado, verifiedAt, official code, revision link e provenance |
| 18 | GET | \`/outbound/requests\` | authorized consumer + source scope | Consulta paginada/filtrada dos pedidos da origem identificada; polling controlado sem ler fila global |

**Opcional somente se necessário no fluxo real:** \`GET /technical-records?officialCode=...\` para localizar ficha por código em update. Caso o lookup existente da ferramenta Produtos cubra a descoberta e o ID, não criar rota redundante. Sem endpoint de escrita em \`technical-records\` fora da decisão de \`verify-and-complete\`.

Contratos por rota:
- \`POST intake\` → \`201\` \`{requestId,caseStatus:"submitted",createdAt,source,requestType,links}\`; replay idempotente com mesma key/fingerprint retorna mesma operação sem duplicar; mesma key com payload distinto = 409.
- \`GET requests\` → \`{items:[{id,type,status,requester,source,createdAt,assignedTo,officialCode,version}],page,pageSize,total}\`; resumo escopado.
- \`GET detail\` → \`{id,requestType,source,requester,requestedChanges,technicalDraft,caseVersion,status,allowedActions,verificationSummary,publishedRevision}\`; \`allowedActions\` vem do backend. §16 (implementado 14/11/2026): \`baseRevision\` **não** é mais emitido no detalhe; \`publishedRevision:{recordId,revisionNumber}|null\` reflete somente a revisão efetivamente publicada pela conclusão daquela solicitação.
- \`PATCH draft\` → \`{changes:[{path,proposedValue,reason}],expectedVersion}\`; **JSON Patch genérico não é aceito**; paths do catálogo, tipos e autorização validados.
- \`POST actions\` → \`{expectedVersion,reason?,...}\` + \`Idempotency-Key\`; retorna caso atualizado ou 409.
- \`POST verify-and-complete\` → \`{expectedVersion,officialCode,reason?}\`; sucesso \`{status:"completed",recordId,revisionNumber,verifiedAt,verificationId}\`; falha de correspondência **409 \`erp_mismatch\`** com lista de caminhos/valores redigidos e caso **não concluído**. 503/504 ou campo sem leitura oficial = não conclui.
- \`GET outbound\` entrega só campos permitidos à origem/consumer, não snapshots internos completos automaticamente. Nenhum callback de escrita no consumer é contratado neste MVP.

## 5. Payloads nativos: exemplos ilustrativos em contrato candidato

Create:
\`\`\`json
{
  "source": "engineering-test",
  "externalRequestId": "test-001",
  "requestType": "create",
  "productType": "raw_material",
  "schemaVersion": 1,
  "requestedData": {
    "description": "DESCRICAO INICIAL",
    "group": "1001",
    "productKind": "MP",
    "defaultWarehouse": "01",
    "unit": "UN",
    "thirdPartyProduct": "1",
    "accountingAccount": "11401002",
    "customerReference": "",
    "suppliers": [
      {"supplierCode":"000001","store":"01","supplierName":"FORNECEDOR EXEMPLO","partNumber":"PN-001","catalogNumber":null}
    ]
  }
}
\`\`\`
Update:
\`\`\`json
{
  "source": "engineering-test",
  "externalRequestId": "test-002",
  "requestType": "update",
  "productType": "raw_material",
  "officialProductCode": "001234",
  "baseRevision": 3,
  "_note": "baseRevision: intake legado tolerado (§16); baseline/concorrência é resolvida server-side — o servidor nunca confia no valor do navegador e não o expõe como revisão do caso",
  "schemaVersion": 1,
  "changes": [
    {"path":"description","proposedValue":"DESCRICAO CORRIGIDA","reason":"Ajuste tecnico"}
  ]
}
\`\`\`

**Importante:** valores, grupos, Part Numbers e códigos do exemplo são fictícios. O catálogo físico/protocolar definitivo deve ser gerado do inventário e validado com owners. O \`requesterSubject\` **não é aceito cegamente do JSON**: para chamada humana é extraído do JWT; para origem S2S será identidade assinada/mapeada em contrato específico a aprovar. \`source\` não concede permissão por si só.

### Catálogo v1 de campos

| Native JSON path (EN) | Legado \`field_tag\` | TOTVS evidence candidate | Observações |
|---|---|---|---|
| \`officialProductCode\` | \`codigo_atual\` / \`novo_codigo\` | \`B1_COD\` | em create informado na conclusão; update identifica produto, recodificação requer regra especial |
| \`description\` | \`descricao\` | \`B1_DESC\` | texto inicial vs valor aprovado |
| \`group\` | \`grupo\` | \`B1_GRUPO\` | preservar string zeros/códigos |
| \`productKind\` | \`tipo\` | \`B1_TIPO\` | primeira categoria MP |
| \`defaultWarehouse\` | \`armazem_padrao\` | \`B1_LOCPAD\` | não assumir defaults legados |
| \`unit\` | \`unidade\` | \`B1_UM\` | opções inventariadas; políticas owner |
| \`thirdPartyProduct\` | \`produto_terceiro\` | \`B1_TPMAT\` | \`1\`="NÃO", \`2\`="SIM" no legado; normalização explícita |
| \`accountingAccount\` | \`cta_contabil\` | \`B1_CONTA\` | inventário revela gap na materialização legado, não copiar bug |
| \`customerReference\` | \`ref_cliente\` | \`B1_REFEREN\` | pode não ser obrigatório em toda nova ficha — gate de owner |
| \`suppliers[].supplierCode\` | \`fornecedores[].supplier_code\` | \`A5_FORNECE\` | campo fornecedor, usar identidade composta |
| \`suppliers[].store\` | \`fornecedores[].store\` | \`A5_LOJA\` | chave de loja |
| \`suppliers[].supplierName\` | \`fornecedores[].supplier_name\` | \`A5_NOMEFOR\` | display, source authority |
| \`suppliers[].partNumber\` | \`fornecedores[].part_number\` | \`A5_CODPRF\` | **Part Number** correto |
| \`suppliers[].catalogNumber\` | \`fornecedores[].catalog_number\` | \`A5_CODPRCA\` | diferente de Part Number |

O inventário prova que a UI legada exigia \`grupo,descricao,tipo,armazem_padrao,unidade,produto_terceiro,cta_contabil,ref_cliente\` e fornecedores com \`supplier_code/store/supplier_name/part_number\`; \`catalog_number\` não era required. **Regra v1 proposta:** em \`create\`, usar esses required de entrada, aceitando campo opcional só se owner confirmar; \`officialProductCode\` não é exigido até conclusão; para \`update\`, somente \`officialProductCode,baseRevision,changes\` e metadados de origem são obrigatórios. **Não exigir todos os campos para update.** Antes de congelar migração/schema, owner funcional precisa ratificar atributos vazios, normalização e lista de valores.

A comparação de fornecedores é **por chave composta** \`(supplierCode,store,partNumber)\` ou identidade oficial definida pelo owner; ordem de array não implica alteração. Alterar Part Number é um delta de relação de fornecimento, não atualização de toda a ficha.

## 6. Modelo de dados PostgreSQL/JSONB — migrations alvo

**Schema dedicado alvo:** \`engineering\` se já for owner apropriado, prefixos \`product_registration_*\`; **não** criar outro DB ou usar \`postgres-core\`. Migrations checksum/append-only no mecanismo já existente do serviço, a verificar antes de escrever SQL. O desenho abaixo fixa entidades, tipos e constraints lógicas; DDL exata deve ser revalidada quanto a extensions, convention, migrations e UoW no HEAD.

### 6.1 \`engineering.product_registration_requests\`

| Coluna | Tipo | Regra |
|---|---|---|
| \`id\` | UUID | PK |
| \`request_type\` | VARCHAR(16) | NOT NULL CHECK IN \`create,update\` |
| \`product_type\` | VARCHAR(64) | NOT NULL \`raw_material\` no MVP |
| \`source\` | VARCHAR(100) | NOT NULL; source authenticated/allowlisted |
| \`external_request_id\` | VARCHAR(200) | NULL para origens humanas sem ID externo |
| \`external_item_id\` | VARCHAR(200) | NULL; compatibilidade com origens multi-item |
| \`requester_subject\` | VARCHAR(200) | NOT NULL; vínculo identidade governado |
| \`requester_display_name\` | VARCHAR(255) | NULL; snapshot informativo, não AuthZ |
| \`official_product_code\` | VARCHAR(100) | NULL em create; required update e após cadastro oficial |
| \`base_revision_number\` | INTEGER | NULL para create; em update, baseline técnica de concorrência resolvida no servidor (§16) — **não** é revisão vinculada ao caso nem é apresentada como tal |
| \`requested_payload\` | JSONB | NOT NULL; create attributes ou update changes validados |
| \`payload_schema_version\` | INTEGER | NOT NULL CHECK >=1 |
| \`status\` | VARCHAR(32) | NOT NULL, estado governado |
| \`assigned_to_subject\` | VARCHAR(200) | NULL |
| \`row_version\` | BIGINT | NOT NULL DEFAULT 1, CAS |
| \`created_at\`,\`updated_at\` | TIMESTAMPTZ | NOT NULL |
| \`completed_at\`,\`rejected_at\` | TIMESTAMPTZ | NULL |
| \`completed_record_id\` | UUID | FK deferred/nullable para record |

Constraints/indexes: \`UNIQUE(source,external_request_id,external_item_id)\` **com NULLS NOT DISTINCT ou índices parciais conforme versão Postgres**, sem bloquear diversos pedidos sem external IDs; index \`status,created_at DESC\`; \`requester_subject,created_at\`; \`assigned_to_subject,status\`; \`official_product_code\`. Rejeitar colisão de origem com payload divergente.

### 6.2 \`engineering.product_registration_drafts\`

| Coluna | Tipo | Regra |
|---|---|---|
| \`request_id\` | UUID | PK/FK requests, 1 draft por caso |
| \`schema_version\` | INTEGER | NOT NULL |
| \`technical_data\` | JSONB | NOT NULL, objeto validado, **não** oficial |
| \`changed_paths\` | JSONB | NOT NULL array, paths autorizados e razões |
| \`row_version\` | BIGINT | NOT NULL, CAS |
| \`updated_by_subject\` | VARCHAR(200) | NOT NULL |
| \`updated_at\` | TIMESTAMPTZ | NOT NULL |

\`technical_data\` é candidato editável; não vira revisão oficial até \`verify-and-complete\`. Diferenças detalhadas e razões também ficam no ledger append-only.

### 6.3 \`engineering.product_registration_records\`

| Coluna | Tipo | Regra |
|---|---|---|
| \`id\` | UUID | PK |
| \`product_type\` | VARCHAR(64) | NOT NULL |
| \`official_product_code\` | VARCHAR(100) | NOT NULL; chave do catálogo externo |
| \`current_revision_number\` | INTEGER | NOT NULL >=1 após primeira conclusão |
| \`last_official_verified_at\` | TIMESTAMPTZ | NOT NULL |
| \`official_source\` | VARCHAR(100) | NOT NULL, autoridade consultada |
| \`created_at\`,\`updated_at\` | TIMESTAMPTZ | NOT NULL |

Unique \`(official_source,official_product_code)\` enquanto não houver separação de empresa/filial; **antes de migration confirmar chave oficial real incluindo filial/empresa se aplicável**. Nunca usar descrição como ID. Não conceder endpoint CRUD direto nessa tabela.

### 6.4 \`engineering.product_registration_revisions\`

| Coluna | Tipo | Regra |
|---|---|---|
| \`id\` | UUID | PK |
| \`record_id\` | UUID | FK records NOT NULL |
| \`revision_number\` | INTEGER | NOT NULL >=1 |
| \`request_id\` | UUID | FK requests NOT NULL |
| \`schema_version\` | INTEGER | NOT NULL |
| \`technical_snapshot\` | JSONB | NOT NULL objeto completo **verificado** |
| \`changes\` | JSONB | NOT NULL array de \`{path,before,after,reason}\` |
| \`official_evidence_id\` | UUID | FK verification attempts NOT NULL |
| \`approved_by_subject\` | VARCHAR(200) | NOT NULL |
| \`approved_at\` | TIMESTAMPTZ | NOT NULL |
| \`created_at\` | TIMESTAMPTZ | NOT NULL |

Unique \`(record_id,revision_number)\`; append-only: nenhuma modificação/deleção de revisão concluída, salvo procedimento regulado de correção com nova revisão. Em \`update\`, snapshot N+1 = snapshot N mais changes aprovados **e verificados na fonte oficial**, nunca um \`PUT\` completo do intake.

### 6.5 \`engineering.product_registration_events\`

| Coluna | Tipo | Regra |
|---|---|---|
| \`id\` | UUID | PK |
| \`request_id\` | UUID | FK NOT NULL |
| \`sequence_number\` | BIGINT | sequencial por caso, unique request+sequence |
| \`event_type\` | VARCHAR(100) | NOT NULL (\`submitted,assigned,draft_changed,...\`) |
| \`actor_subject\` | VARCHAR(200) | NOT NULL ou service actor explícito |
| \`occurred_at\` | TIMESTAMPTZ | NOT NULL |
| \`reason\` | TEXT | NULL |
| \`metadata\` | JSONB | NOT NULL; diff redigido, correlation id, provenance |
| \`previous_status\`,\`next_status\` | VARCHAR(32) | NULL se evento não muda estado |

Append-only; nenhuma dependência de chat legado. Para cada decisão de estado/draft, persistir evento na mesma UoW/transação que muda o agregado.

### 6.6 \`engineering.product_registration_verifications\`

| Coluna | Tipo | Regra |
|---|---|---|
| \`id\` | UUID | PK |
| \`request_id\` | UUID | FK NOT NULL |
| \`official_product_code\` | VARCHAR(100) | NOT NULL |
| \`requested_by_subject\` | VARCHAR(200) | NOT NULL |
| \`checked_at\` | TIMESTAMPTZ | NOT NULL |
| \`official_source\` | VARCHAR(100) | NOT NULL |
| \`result\` | VARCHAR(40) | \`matched,mismatched,not_found,unavailable,unverifiable\` |
| \`expected_fields\` | JSONB | NOT NULL, paths/valores de conferência |
| \`observed_fields\` | JSONB | NULL se indisponível; redacted |
| \`field_results\` | JSONB | NOT NULL, cada path \`matched|mismatched|unverifiable\` |
| \`evidence_fingerprint\` | VARCHAR(128) | hash de payload canônico e contexto autorizado |
| \`correlation_id\` | VARCHAR(128) | NOT NULL |
| \`error_code\` | VARCHAR(100) | NULL |

Guardar tentativas malsucedidas também. Rejeitar \`completed\` sem linha \`matched\` vinculada à revisão **e** código real verificado. Não gravar credenciais ou resposta integral confidencial do TOTVS.

### 6.7 \`engineering.product_registration_idempotency\`

| Coluna | Tipo | Regra |
|---|---|---|
| \`id\` | UUID | PK |
| \`actor_or_source\` | VARCHAR(200) | NOT NULL |
| \`operation\` | VARCHAR(100) | NOT NULL |
| \`idempotency_key\` | VARCHAR(200) | NOT NULL |
| \`request_fingerprint\` | VARCHAR(128) | NOT NULL |
| \`request_id\` | UUID | FK NULL |
| \`response_status\` | INTEGER | NULL enquanto processamento |
| \`response_payload\` | JSONB | NULL / minimal/redacted |
| \`created_at\`,\`expires_at\` | TIMESTAMPTZ | NOT NULL |

Unique \`(actor_or_source,operation,idempotency_key)\`; tentar executar concorrente da mesma chave deve serializar e nunca gerar duas revisões. Política de TTL/retention definida com owner; referência externa única garante deduplicação além do TTL.

**Tabelas opcionais não criadas no MVP:** \`attachments\` (não há requisito de upload explícito na primeira jornada); \`outbox\` (somente quando consumidor push/notifications estiver contratado); \`comments\` (reasons/timeline bastam); \`product_catalog\` como novo master ERP (proibido).

### 6.8 Integridade das transações

- Em \`verify-and-complete\`, consultar ERP **fora da transação longa** com limite explícito de timeout e marcar evidência associada ao \`expectedVersion\`; depois adquirir lock curto/CAS do caso e do record para garantir que draft/revision não mudaram; revalidar fingerprint da proposta e frescor do resultado antes de fazer \`completed\` + revision + record pointer + event na mesma transação. O lookup oficial pode ser repetido caso a leitura envelheça ou o estado mude.
- A leitura ERP não é transação distribuída: evidência \`verifiedAt\` + reconsulta/limite de frescor precisam do aceite do owner. \`verified\` não significa monitoramento contínuo do ERP.
- Em caso de falha de DB depois da consulta ERP, caso não conclui, permite repetir com idempotência; nenhuma operação de escrita ERP existe no módulo.
- Ao atualizar record por outra solicitação concorrente, \`baseRevision\` não corresponde → 409 \`stale_revision\`; solicitação pode ser reavaliada/rebaselined por ação explícita aprovada, nunca overwrite silencioso.

## 7. Máquina de estados, decisões e invariantes

| Estado | Ações permitidas | Próximo estado | Invariantes |
|---|---|---|---|
| \`submitted\` | \`start,reject\` | \`in_progress,rejected\` | já persistido e auditado |
| \`in_progress\` | \`edit_draft,request_information,submit_review,reject\` | \`needs_information,under_review,rejected\` | responsável autorizado, draft validado |
| \`needs_information\` | \`resume,reject\` | \`in_progress,rejected\` | motivo/campos pendentes registrados; correções só por autor autorizado |
| \`under_review\` | \`verify_and_complete,request_information,reject\` | \`completed\` (matched), \`needs_information,rejected\` | somente analista autorizado e campo verificável |
| \`completed\` | somente GET | terminal | verificação oficial matched, revisão publicada imutável |
| \`rejected\` | somente GET | terminal | justificativa obrigatória, sem atualizar record |

\`verify-and-complete\` sem match **permanece \`under_review\`**, cria verification attempt e devolve \`409 erp_mismatch\` com resumo. Timeout/indisponibilidade = 503/504, sem estado \`completed\`; verification attempt pode ser registrado. Se ERP não oferece campo requerido = \`unverifiable\`, nunca concluir. \`needs_information\` pode inicialmente representar pendência interna no Portal, sem envio ao solicitante externo; integração externa para devolução/retorno é posterior. Não reabrir terminal por update direto; abrir nova solicitação.

Aprovação técnica e confirmação ERP podem ocorrer no mesmo comando \`verify-and-complete\` como duas subetapas (check readiness, official verification) com distinção no ledger. O clique humano não substitui prova da operação TOTVS.

## 8. Verificação oficial: matriz de campo e comparação

1. Adapter \`OfficialProductReader\` recebe \`officialProductCode\`, contexto do usuário e correlation ID e retorna produto com fonte/autorização/frescor. Para fornecedores, consulta relação e retorna coleção com chaves completas.
2. Ao criar: confirmar \`B1_COD\` + atributos técnicos obrigatórios aprovados, inclusive fornecedores/Part Number quando parte da ficha aprovada. Ao alterar: confirmar **cada path alterado** de \`changes\` e os invariantes necessários. A observação precisa ser do TOTVS por **contrato oficial de leitura**, não do JSONB técnico local.
3. Comparação por tipo e regra: strings com normalização explicitamente aprovada (\`trim\`, caixa, zeros, precisão, sem confundir valor significativo), enums/conjuntos tipados, fornecedor por chave composta; nunca fuzzy match para determinar \`completed\`.
4. Proveniência por \`fieldPath\` com \`expectedValue\`, \`observedValue\`, \`match\`, \`officialField\`, \`checkedAt\`, \`sourceVersion\` quando fornecida. O sistema não pode inferir que o campo realmente **mudou** a partir da leitura final se não há baseline ERP anterior confiável; por isso para update exigir \`baseRevision\`/snapshot oficial anterior válido, e \`expectedValue\` diferente do baseline. Caso fonte tenha sido alterada fora do Portal, registrar a incerteza e não declarar causalidade; para conclusão verificar o **estado final esperado**, não afirmar autoria exclusiva da alteração ERP.
5. Se campo required não é retornado ou sem autorização, não aprovar. O inventário da API Flask comprova SB1/SA5 (\`B1_COD, B1_DESC, B1_GRUPO, B1_TIPO, B1_LOCPAD, B1_UM, B1_TPMAT, B1_CONTA, B1_REFEREN\`; \`A5_FORNECE,A5_LOJA,A5_NOMEFOR,A5_CODPRF,A5_CODPRCA\`). **Não comprova que a API oficial \`api-delpi\` retorna todos estes campos e permissões.** Este é um **contract gate externo real**, antes de implementar a operação 11 e antes de qualquer piloto com conclusão.
6. Sem permissão de ler campo oficial, devolver \`forbidden/unverifiable\` conforme owner sem revelar valor confidencial. Falha de comparação mantém o draft/caso e não altera revisão vigente.
7. \`TechnicalProductRecord\` pode guardar cópia do estado oficial **verificado** na revisão, não atuar como endpoint de gravação mestre nem usar o draft como substituto de leitura ERP.

## 9. UI, teste de intake e jornada do analista

Superfície principal \`/apps/engineering/product-registration\`: tabela de fila (statuses, busca, tipo, assigned, source), detalhe com tabs \`Request,Technical Draft,Verification,History\` em UI pt-BR. Analista edita draft e seleciona campos apenas quando autorizado, guarda justificativa, submete à análise e usa **Verificar e concluir**. Mostrar por campo estado \`conforme/divergente/sem dado oficial\`, última verificação e código ERP. Sem botão de cadastro automático TOTVS no MVP.

Acesso à ferramenta de teste \`/test-intake\` somente DEV/HML, com permissão específica; usa a **mesma rota POST intake** do produto, e envia requests sintetizadas com IDs de teste, sem contornar AuthZ. Caso não exista canal UI para solicitante, o MVP de backend não depende dele; a tela de teste é apoio de validação, nunca canal produtivo.

Na criação, o formulário de teste usa required do contrato do legado revisado. Na alteração, consultar registro existente, selecionar caminhos autorizados e submeter apenas mudanças com \`baseRevision\`. Sem chat; status/pendências na timeline. \`@delpi/plugin-ui\`, responsivo, deep link, F5, 401/403/409, loader/error/empty e acessibilidade.

## 10. Requisitos/aceites bloqueantes para implementação

- **AC-PRC-MVP-01**: POST intake autenticado cria caso uma vez; replay não duplica; source/actor falsos não passam.
- **02**: \`create\` exige required de entrada v1 e código ERP apenas no fechamento; \`update\` exige 1+ field changes e \`baseRevision\`, sem whole-object replace.
- **03**: atualizar só \`description\` preserva todos os outros campos; rejeitar alteração de path desconhecido/imutável.
- **04**: fila/detalhe só mostram casos autorizados; sem autorização ou Core down = fail-closed.
- **05**: alterações simultâneas de caso/revisão produzem 409, sem lost update.
- **06**: produto não encontrado no ERP não conclui; caso e revisão vigentes inalterados.
- **07**: descrição/campo divergente não conclui e aponta path divergente.
- **08**: fornecedor/Part Number divergente ou indisponível não conclui; não comparar arrays só por ordem.
- **09**: update com uma alteração verifica valor final real do campo e baseline, não somente código; dados não verificáveis impedem conclusão.
- **10**: match real + analista autorizado conclui exatamente uma vez, persiste evidência, snapshot JSONB imutável e diff na mesma UoW.
- **11**: timeout/403/502 em API oficial não publica revisão nem dá sucesso otimista.
- **12**: request rejeitada nunca muda record vigente; duas finalizações concorrentes não geram duas versões.
- **13**: outbound é escopado ao consumer/origem e não vaza dados de outro departamento.
- **14**: EVA candidate não aprova e indisponibilidade não bloqueia usuário humano conforme política.
- **15**: zero chamadas runtime a \`requests-api\`, \`my-requests\`, API Flask ou banco legado no módulo novo; zero escrita ERP.
- **16**: frontend em pt-BR e technical identifiers EN; integração de shared files não altera VAL-01.
- **17**: teste de verificação cobre \`accountingAccount\`, fornecedores \`partNumber\`, alteração seletiva e \`officialCode\` com zeros.
- **18**: nenhuma solicitação real/migração produção antes de contrato de AuthZ, owner approval e cutover próprio.

## 11. Arquivos previstos e execução serializada

**Novos paths candidatos**, sujeitos à verificação de layout vigente:
\`\`\`text
engineering-api/engineering_app/domain/product_registration/
engineering-api/engineering_app/application/product_registration/
engineering-api/engineering_app/application/ports/product_registration_*.py
engineering-api/engineering_app/infrastructure/persistence/product_registration/
engineering-api/engineering_app/infrastructure/gateways/official_product_reader.py
engineering-api/engineering_app/interface/http/routes/product_registration_routes.py
engineering-api/engineering_app/interface/http/schemas/product_registration.py
engineering-api/tests/test_product_registration_*.py
plugins/engineering/src/features/product-registration/
\`\`\`

Arquivos compartilhados (um integrador, sequencial após VAL-01): \`engineering-api/engineering_app/main.py\`, \`engineering-api/engineering_app/config.py\`, \`plugins/engineering/src/App.tsx\`, \`engineeringRoutes.ts\`, \`engineeringRouteCatalog.ts\`, \`HelpPage.tsx\`, manifest/core policies/infra/deploy. Não editar \`drawing\`, \`understanding.py\`, \`perception_contract.py\`, \`paddleocr_adapter.py\`, SLANet, BOM, AnalysisJobStore ou testes correlatos. Antes de codificar: \`origin/main\`, HEAD/status, owner/source/contract tests, migration convention; testar no SHA integrado, residual search, ledger, rollout/rollback.

## 12. Gates finais — decisões estritamente externas, não novo discovery genérico

| Gate | Quem decide/prova | Estado |
|---|---|---|
| A. ownership de solicitações/casos de cadastro técnico no bounded context Engineering | Coordination + owners Engenharia e arquitetura | \`ARCHITECTURE_DECISION_REQUIRED\` |
| B. DB/schema/migration convention, chave produto empresa/filial e retenção de histórico | Eng. API owner + DBA | \`TO_VERIFY_AT_IMPLEMENTATION\` |
| C. campo obrigatório real do create/fornecedores, formatos e valores válidos, Part Number obrigatório, \`customerReference\` vazio | owner funcional Engenharia | \`OWNER_SIGNOFF_PENDING\` |
| D. contrato oficial read-only com cobertura de SB1/SA5/Part Number/conta/fornecedores, IAM e semântica de freshness | owner api-delpi/TOTVS + integração | \`CONTRACT_GAP_TO_PROVE\` |
| E. nova permissão Core process/verify e visibilidade da fila | Core/RBAC + Engenharia | \`AUTHZ_CONTRACT_PENDING\` |
| F. SLA e validade do snapshot ERP no comando de conclusão, estados de erro e política de retenção de evidência | owner funcional + segurança | \`OWNER_SIGNOFF_PENDING\` |

**Quando A–F estiverem aprovados, a implementação pode ser dividida em slices sem reabrir o desenho das 18 rotas ou das sete tabelas.** Sem esses gates, pode-se implementar com mocks/ports **somente em DEV/HML** e não alegar conclusão ERP validada.

## 13. Roteiro de implementação (sem modificar código nesta task)

1. \`PRC-C0\`: registrar ADR de ownership e aprovar contratos A–F; confirmar SHA, migrations e official reader real.
2. \`PRC-C1\`: models, validators, state machine, persistence/migrations \`requests,drafts,events,idempotency\` + testes.
3. \`PRC-C2\`: intake e endpoints 01–10, reference-data e fila/detalhe, teste integrado, sem finalizar.
4. \`PRC-C3\`: \`records,revisions,verifications\`, adapter de leitura oficial, endpoint 11 + testes negativos e concorrentes, após gate D.
5. \`PRC-C4\`: endpoints 12–18, Portal Engineering UI, harness de teste restrito, testes E2E AuthZ e source isolation.
6. \`PRC-C5\`: homologação com casos sintéticos no TOTVS, relatório de cobertura, paridade, build/deploy por SHA e owner Ops. Integrações com origem externa, Requests API, migração do legado e criação ERP por API são **fases posteriores**.

**RESULT:** \`CONTRACT_SPECIFIED\`, \`IMPLEMENTATION_NOT_STARTED\`, \`DEPLOY_NOT_PERFORMED\`, \`ERP_FIELD_COVERAGE_NOT_PROVEN\`.


## Plano transversal de capacidades EVA — Product Registration (2026-11-06)

A paridade **Portal/REST/EVA** integra cada slice deste vertical: para cada capacidade legítima do usuário, conectar uma ação `(entity, action)` ao **mesmo caso de uso** nas **seis tools semânticas existentes**, sem nova tool nem bypass de Core/Domain AuthZ. Matriz das 18 rotas, ações `product_registration.*`, riscos `read/execute`, PREPARE/ACT, confirmação humana para rejeição/conclusão, testes e integração serializada com VAL-01 em [PRODUCT-REGISTRATION-EVA-SEMANTIC-INTEGRATION.md](./PRODUCT-REGISTRATION-EVA-SEMANTIC-INTEGRATION.md). O documento é `TARGET/PLANNED`, não evidência de runtime. EVA não aprova produto nem escreve no TOTVS e não pode contornar a verificação oficial na conclusão. A publicação de uma rota humana requer cobertura semântica testada ou `PARITY_GAP` explicitamente bloqueado/aceito em release governado.


## Regra de integração obrigatória — consulta oficial TOTVS (2026-11-06)

> **Decisão explícita do Product Owner, prevalente para Product Registration:** toda busca, consulta, lookup, conferência de atributos, fornecedores/Part Number e validação de conclusão baseada no TOTVS **deve passar pelo BFF da `engineering-api`, que consome exclusivamente contratos oficiais da `api-delpi`**, com identidade delegada e autorização do usuário. A `api-delpi` é owner da integração/consulta ao TOTVS; a Engineering API adapta o contrato para os casos de uso de Engenharia. Nem `plugins/engineering` nem a EVA acessam diretamente TOTVS, banco SQL/ODBC, API Flask do Controle MP ou `api-delpi` contornando o BFF de Engenharia.

Fluxo autorizado: `Portal ou EVA -> Engineering API (REST ou mesma application use case via ações semânticas) -> OfficialProductReader adapter -> api-delpi /products/* (read-only) -> TOTVS`. Para EVA, usar os mesmos ports/use cases e AuthZ, **sem novas tools MCP**; não duplicar HTTP call no handler semântico. Sem escrita ERP neste MVP: analista realiza criação/alteração manual no TOTVS; `verify-and-complete` lê resultado pela `api-delpi`, compara campos, e só conclui quando todos os campos exigidos são comprovados.

**Gate D / lacuna atual:** o relatório PRC-C3 indica que `B1_CONTA` (`accountingAccount`) não é exposto pela view `engineering` embora outros atributos e SA5/Part Number estejam disponíveis. Resolver **no contrato/owner `api-delpi`**, verificando escopo/autorizações, ou propor view oficial apropriada; não adicionar acesso SQL/TOTVS direto à Engineering API e não relaxar comparação. Enquanto qualquer campo obrigatório não for verificável via `api-delpi`, bloquear `completed` (fail-closed, erro `unverifiable`). Aprovação de novo campo/view é do owner da API e das permissões, não do BFF.

**Critérios de aceite:** busca e verificação usam somente adapter oficial `api-delpi`; autorização humana propagada; ausência/403/timeout/campo omitido produzem status honesto sem revisão publicada; testes REST/EVA usam mesmo caso de uso e demonstram ausência de SQL direto, de escrita ERP e de downstream legado. Qualquer mudança nessa fronteira exige `ARCHITECTURE_DECISION_REQUIRED`. **Documentação apenas; sem deploy, migration ou mudança de código nesta atualização.**


## Decisão aprovada do Product Owner — PRC RBAC, BFF e HML (2026-11-06; vigente)

**Leia antes de implementar:** [PRODUCT-REGISTRATION-PO-DECISIONS-2026-11-06.md](./PRODUCT-REGISTRATION-PO-DECISIONS-2026-11-06.md). Esta decisão **substitui** as propostas anteriores de cinco permissões `engineering.product-registration.*` e a premissa de que `engineering.access` não autoriza o CRUD do módulo. Modelo vigente: `engineering.access` para CRUD/workflow operacional e `engineering.manager` para administração, com AuthZ backend live, escopo/identidade e invariantes de domínio intactos. **Ainda não implementado no PRC/Core; não alegar RBAC pronto.** Engenharia é owner do workflow e `api-delpi` é owner da leitura oficial TOTVS; autorizado estender `B1_CONTA` na `api-delpi` (inclusive SQL interno, sem bypass pela Engenharia). HML autorizada **condicionalmente** à execução por operadores habilitados, gates e testes; produção não autorizada. Merge markers PRODUCTS corrigidos na `main`, porém build/typecheck completos devem ser executados para comprovar integração.


## Decisão PO vigente — SA5 Part Number vazio (2026-11-06)

**Contrato aprovado (SUPERSEDED — PRC-REF-022-FIX-01, 2026-11-10):** a regra PO-D5.4 de `partNumber` opcional foi substituída: **`suppliers[].partNumber` (`A5_CODPRF`) é obrigatório** para registrar ou alterar vínculo de fornecedor (CREATE, UPDATE, `supplierLinkChanges` e correções REF-022). `catalogNumber` (`A5_CODPRCA`) permanece opcional. Validação rejeita ausente/`null`/vazio/espaços e valor acima de 80 caracteres (nunca trunca). Vínculos históricos intocados não são reescritos; vínculo alterado exige PN válido e a conclusão é bloqueada (fail-closed) em caso contrário. Identidade do vínculo continua `(supplierCode, store)`; comparação oficial `Engineering API -> api-delpi -> TOTVS` permanece autoridade — mismatch/unverifiable bloqueia publicação; CAS, revisão imutável, provenance e AuthZ preservados.

**Histórico (PO-D5.4):** [PRODUCT-REGISTRATION-PO-DECISIONS-2026-11-06.md](./PRODUCT-REGISTRATION-PO-DECISIONS-2026-11-06.md#decisão-adicional-aprovada--part-number-opcional-quando-ausente-no-totvs-2026-11-06) — `suppliers[].partNumber` era aceito omitido/`null`/`""` quando a fonte oficial retornava vazio; mantido apenas como rastreabilidade da decisão anterior.


## Gate UX do MFE Product Registration — redesign aprovado (2026-11-07)

**Produção suspensa pelo PO até redesenho e aceite visual.** Wireframes detalhados de **sete áreas da experiência** (fila, nova solicitação, detalhe/workflow, ficha técnica, verificação TOTVS, histórico/revisões, acompanhamento) e regras de layout/fluxos: [MFE-PRODUCT-REGISTRATION-UX-WIREFRAMES.md](./MFE-PRODUCT-REGISTRATION-UX-WIREFRAMES.md). **Matriz de componentes reais do `@delpi/plugin-ui` via `plugins/engineering/src/ui/engineeringUi.ts`, estado dos exports, estados UI, responsividade e plano de QA:** [MFE-PRODUCT-REGISTRATION-COMPONENTS-AND-ACCEPTANCE.md](./MFE-PRODUCT-REGISTRATION-COMPONENTS-AND-ACCEPTANCE.md).

**Gates:** `MFE-PRC-UX0..UX5`. Frontend PRC atual está implementado funcionalmente mas usa majoritariamente HTML básico e **não foi aceito visualmente**; as sete áreas são desenho `TARGET`, não sete rotas implementadas. Reutilizar kit/fáçade, preservar os use cases e seis tools EVA, não inventar componentes/endpoints/novo RBAC, validar screenshots reais DEV/HML e obter aceite PO. **Nenhum deploy em produção autorizado nesta etapa.** A autorização produtiva discutida anteriormente fica substituída por esta suspensão expressa do PO.


## D16 — Bandeiras operacionais no atendimento (PO 2026-11-09)

**Plano canônico:** [D16 — CRUD bandeiras, UI e EVA](./PRODUCT-REGISTRATION-D16-ATTENDANCE-FLAGS-CRUD-EVA-UX-PLAN.md). Escopo **Engineering API**: flags com texto descritivo anexadas à solicitação PRC para o atendente registrar verificações/cobranças futuras, por exemplo revisão da descrição ou solicitar Part Number ao requisitante. Bandeira **não** é campo SB1/SA5, nem verificação TOTVS, nem altera status/revisão técnica; não preenchê-lo com `0` como workaround.

**Implementado (DEV):** tabela `engineering.product_registration_flags` (V015); rotas nested `/v1/product-registration/requests/{requestId}/flags` (GET/POST/PATCH/DELETE + resolve/reopen); eventos `flag.created|updated|resolved|reopened|deleted`; CAS `expectedVersion` + `Idempotency-Key`; AuthZ `engineering.access` + escopo do caso; `FLAG_MUTATION_AFTER_TERMINAL=True` (acompanhamento pós-conclusão sem reabrir cadastro oficial). UI na Ficha técnica (`PrcAttendanceFlags`). EVA: ações semânticas `product_registration.flag_*` nas tools existentes, delete com PREPARE/commit + confirmação humana. Limites: title≤120, description≤1000, subjects `GENERAL|FIELD|SUPPLIER_LINK`.


## D16-REF-01 — Bandeiras por campo e consulta transversal

Decisão PO 2026-11-09: [adendo normativo D16-REF-01](./PRODUCT-REGISTRATION-D16-ATTENDANCE-FLAGS-CRUD-EVA-UX-PLAN.md#d16-ref-01--decisão-po-superveniente-bandeiras-por-campo-experiência-contextual-e-consultas-transversais). O D16 CRUD existente é infraestrutura; a UX principal passa de lista GENERAL a **uma bandeira OPEN por campo da solicitação**, posicionada ao lado do campo e editável inclusive após conclusão, com soft-delete/histórico. FIELD exige targetPath; SUPPLIER_LINK exige supplierCode+store **e targetAttribute** (PN diferente de Catálogo). Unicidade ativa no backend/PG; não alterar SB1/SA5 ou resolver automaticamente após mudança do valor. Novos reads transversais **planejados** para listar solicitações/produtos/campos/atributos sinalizados com paginação, filtros antes da paginação, contagens escopadas e AuthZ por caso. Bandeiras antigas GENERAL permanecem em histórico/legado, sem associação silenciosa. Contrato/impl/testes ainda PENDING.


## PRC-REF-017 — Contrato de conclusão com código CREATE e verificação campo a campo (2026-11-09)

**Planejamento aprovado pelo PO, implementação sujeita ao inventário do HEAD.** Referência [plano consolidado REF-017](./MFE-PRODUCT-REGISTRATION-POST-REDESIGN-REFINEMENT-PLAN.md).

**CREATE:** intake não exige código oficial; \`verify-and-complete\` exige \`officialCode\` informado pelo analista após cadastro manual no TOTVS, confirma existência/identidade oficial e compara o conteúdo requerido do draft, inclusive SA5 verificável. \`officialCode\` deve ser persistido no caso concluído, revisão técnica, verificação, detalhe e resposta autorizada ao solicitante/outbound; não aceitar código apenas digitado sem read-back. Um B1_COD existente sozinho não prova que foi criado neste atendimento: inventariar evidência de criação/proveniência disponível via api-delpi e formalizar com owner se o ERP não disponibiliza, sem inventar timestamp/owner.

**UPDATE:** travar código ao \`request.official_product_code\`; verificar seletivamente **cada caminho alterado** SB1 e cada operação/atributo SA5 efetivos contra leitura oficial atual: antes (baseline), solicitado, observado, result. Match completo necessário para atomic \`completed\`; mismatch/ausência/parcial/ambiguidade/unverifiable bloqueiam com tentativa registrada e erros tipados. Não executar SQL TOTVS direto pela Engineering API. api-delpi pode utilizar SQL internamente no owner para oferecer projeções/read-back oficiais autorizados.

**REVIEW/REST/EVA:** manter rota \`POST /requests/{id}/actions/verify-and-complete\` (body \`officialCode\` CREATE, \`expectedVersion\`, reason quando contrato exigir), \`GET /requests/{id}/verifications\` e ações semânticas EVA existentes. Não duplicar verificador por UI/EVA. Revalidar live AuthZ, CAS, idempotência, retorno de evidência e attempt após mismatch. Acrescentar UI detalhada na aba \`Verificação TOTVS\` com coluna Campo/Antes/Solicitado/Encontrado/Resultado, status de cada item e possibilidade de tentar novamente, sem conclusão parcial ou falso MATCH. Nunca escrever ERP.

**Gates:** matriz CREATE código ausente/not_found/duplicado/identidade divergente, fields match/mismatch/unverifiable, SA5 completo/incompleto, UPDATE scalar-only, SA5-only, PN/catálogo separado, retorno requester, retry, races, regressões. Não confundir dependência de operador manual TOTVS com execução automática de cadastro.

**Execução ENG-PRC-REF-017 (DEV):** `verify_and_complete` reforçado — CREATE exige código normalizado; UPDATE rejeita troca (`fields.officialCode=immutable`); `_compare` emite `previous`/`expected`/`observed`; UI ActionBar + VerificationPanel alinhadas. Identidade CREATE além do match integral: **PENDING_OWNER** (contrato api-delpi sem proveniência de criação amarrada ao request). Sem endpoint/MCP novo. Sem write ERP.



## PRC-REF-019 — Contrato de esclarecimentos do solicitante (2026-11-09)

**PO_APPROVED_TARGET / IMPLEMENTED_DEV (2026-11-09).** Jornada e testes no [PRC-REF-019 consolidado](./MFE-PRODUCT-REGISTRATION-POST-REDESIGN-REFINEMENT-PLAN.md). Owner Engineering API; sem ownership em requests-api/my-requests.

**PROVEN:** `product_registration_info_rounds|questions|answers` (V018+V019); `POST .../request-information` com `questions[]`/`message` (legado reason+pendingFields); `GET .../information-rounds[+/{id}]`; `PATCH .../answers`; `POST .../submit-answers`; `POST .../questions/{id}/actions/accept`; `POST .../request-follow-up`; resume bloqueado com rodada aberta salvo `waiver:`; CAS/idempotência/eventos; UI modal+painel; EVA capabilities proven (request_information, rounds read, accept, follow_up, resume).

**FIX-01 (aditivo, 2026-11-09):** detalhe do caso inclui `informationExchange` (`hasOpenBlocker`, `canRespond`, `canReview`, `activeRoundStatus`, `activeRoundId`). Enquanto houver blocker, `allowedActions` **não** inclui `resume` (mesmo contrato de domínio do 409 `information_round_open`). Capacidades de apresentação; AuthZ efetiva permanece nos use cases.

**FIX-02 (UX, 2026-11-09):** UI contínua sem toggle de papéis. Renderização por estado da rodada + capacidades; retomada principal no cabeçalho. Sem nova superfície de contrato.

**PENDING_NOTIFICATION_OWNER / PENDING_ATTACHMENTS_CONTRACT.** **ARCHITECTURE_DECISION_REQUIRED:** gate HTTP ainda `engineering.access` — solicitante sem essa permissão Core não alcança as rotas.

**Segurança:** AuthZ de objeto no service (`requester_subject`); analista não forja respostas; sem escrita SB1/SA5/TOTVS. HML/PROD não deployados neste ciclo.
## PRC-REF-020 — Contrato normativo: concluir com verificação oficial em uma ação (PO 2026-11-09)

**Status \`IMPLEMENTED_DEV\` (Engineering API + MFE + EVA + V020).** Este adendo **prevalece sobre §7 e descrições anteriores de \`submit_review\` / \`under_review\` como jornada operacional**, sem apagar evidências do contrato legado.

**Workflow implementado:** \`submitted --start--> in_progress --complete (validação + leitura oficial + compare + commit)--> completed\`. \`in_progress --request_information--> needs_information --resume governado--> in_progress\`; \`reject\` permitido nos estados não terminais autorizados. \`under_review\` é **estado legado compatível somente para leitura/migração** (V020 reabre abertos → \`in_progress\` com evento auditável; \`return-to-attendance\` e falha de \`complete\` também reabrem). Ação externa: **Concluir atendimento**. REST canônico: \`POST .../actions/complete\`; alias depreciado \`verify-and-complete\` mapeia o **mesmo** Application use case (\`complete_attendance\`). \`submit-review\` permanece por compatibilidade e **não** entra em \`allowedActions\` do fluxo novo. EVA: \`product_registration.complete\` (PREPARE/ACT) + alias \`verify_and_complete\`; sem 7ª tool MCP.

**Pré-condições:** request \`in_progress\`; principal e Live AuthZ legítimos; versão esperada e chave idempotente; draft consistente; CREATE com \`officialCode\` informado após cadastro manual no TOTVS; UPDATE com código oficial imutável e baseline válido; nenhuma restrição SA5/owner pendente; fonte oficial acessível. Chamadas externas com timeout e limites; não manter transação DB aberta durante network I/O; revalidar CAS/estado/escopo na fase de commit.

**Pós-condição de sucesso:** somente quando **todos os checks obrigatórios aplicáveis = MATCH/APPROVED comprovado** e nenhuma falha bloqueante, persistência atômica de \`completed\`, verificação matched, evento, record e revisão técnica imutável com versão/correlação/provenance. Sem \`completed\` otimista, partial success, auto-write ERP ou skip de campo não verificável. Estado posterior e eventuais notificações devem refletir o commit confirmado, não a intenção da ação.

**Pós-condição de falha:** \`in_progress\` preservado; nenhuma revisão publicada, nenhum novo record vigente declarado, sem \`completed\`. Persistir tentativa de verificação e resultados por campo quando aplicável, com \`previous/expected/observed/result\`, source/correlation/ator/tempo, respeitando dados sensíveis e AuthZ. Divergência (\`mismatch\`), campo obrigatório ausente, projeção/parcial/ambiguidade (\`unverifiable\`), produto inexistente (\`not_found\`), \`forbidden\`, \`timeout\`, \`unavailable\`, erro de contrato, conflito CAS ou integridade **bloqueiam**. Distinção de falha de negócio vs infraestrutura; retries exigem verificação fresca e idempotência sem falsa reutilização de \`matched\` anterior.

**Comparação:** CREATE compara todos os campos aplicáveis entregues e obrigatórios, incluindo SA5 verificável, contra código oficial de cadastro manual; proveniência de criação vinculada à solicitação permanece \`PENDING_OWNER\`, sem afirmar prova que não existe. UPDATE compara todo delta efetivo SB1+SA5 (código+loja, PN e catálogo distintos; zeros à esquerda, operações e vazio legítimo conforme contratos), sem comparar desnecessariamente campos não alterados. SA5 REMOVE permanece bloqueado onde contrato ainda está pendente. Não chamar SQL/ODBC TOTVS pela Engineering API: exclusivamente \`OfficialProductReaderPort -> api-delpi\` read-only.

**Resposta estruturada de falha:** retornar resumo seguro + itens \`targetType/targetPath/supplierKey/targetAttribute/previous/expected/observed/result/reason\` quando aplicável, tentativa/verificationId, retriable quando fundamentado, status de caso preservado. A UI destaca cada campo/linha SA5 e orienta correção autorizada; nenhuma informação de terceiros ou campos de acesso negado é vazada. O código de erro técnico permanece observável em logs e payload estruturado, com mensagem de negócio adequada.

**Migrations:** \`V020__prc_ref020_complete_workflow.sql\` (forward-only). Política legado: casos abertos \`under_review\` → \`in_progress\` + evento \`returned_to_attendance\` (\`system:migration:V020\`), CAS via \`row_version\`; verifications/revisões/histórico preservados. CHECK de status mantém \`under_review\` para leitura histórica. Rollback operacional: não reescrever V020; recuperação = nova migration compensatória + reabertura manual governada — sem rollback destrutivo de eventos.

**Consumers:** MFE ação principal \`Concluir atendimento\`; progresso \`submitted → in_progress → completed\`; painel de verificação com resumo/contagem/destaque SB1+SA5 e histórico de tentativas. REST/EVA compartilham \`complete_attendance\`. REF-019 e D16 preservados. Proveniência CREATE inequívoca e AuthZ de solicitante sem \`engineering.access\` permanecem \`PENDING_OWNER\` / \`ARCHITECTURE_DECISION_REQUIRED\` (Core). **HML/PROD não deployados nesta tarefa.**

## PRC-REF-020-UX-01 — Contrato de diagnóstico acionável de verificação (PO 2026-11-09)

**Status \`IMPLEMENTED_DEV\`.** Regras de apresentação e extensão aditiva do \`detail\` SA5 (\`supplierCode\`/\`store\`/\`attributes[]\`) **sem mudar** autorização, algoritmo de comparação ou o gate de conclusão integral REF-020. Campo observado ausente/não retornado (\`UNVERIFIABLE\`) **não** é o mesmo que string oficialmente vazia e verificável; fonte, categoria e razão só quando suportadas pela evidência oficial. Contagem de problemas = itens tipados (campo SB1 ou atributo/vínculo SA5), sem dupla contagem do agregado \`suppliers\`.

**Modelo de leitura alvo:** identificar \`verificationId\`, requestId, caseVersion/revision associada, result global, checkedAt, officialCode, source, contagem consistente e itens tipados com \`targetType\` \`FIELD|SUPPLIER_LINK\`, \`targetPath\` ou \`supplierKey\` (code+store) + \`targetAttribute\`, \`previous\`, \`expected\`, \`observed\`, \`result\`, \`reasonCode\` e metadados permitidos. Inventariar \`PrcVerificationPanel\`, \`PrcFieldResult\`, \`fieldResults\` de erro transitório, \`verifications\` persistidas e \`supplierDetail\` antes de adicionar qualquer campo. Não duplicar objetos em duas fontes de autoridade, não inventar campos oficiais. GET de verifications deve retornar somente detalhes autorizados; se houver falta de persistência dos resultados para refresh, propor contrato governado com migração **somente se necessária**, imutabilidade do attempt e testes. Recusar agregação de erros gerais como "N campos divergentes" quando não existe lista real.

**UX:** um resumo da tentativa selecionada na aba Verificação TOTVS, sem duplicação verbatim de alertas em detalhe/aba; filtros \`Somente problemas\` (default quando houver) / \`Todos\`; problemas primeiro sem esconder conformes; mensagens de diagnóstico específicas, orientação prudente e botão de navegação para a ficha/campo ou fornecedor/atributo exato; ações autorizadas (editar proposta, pedir esclarecimento, correção manual no TOTVS, concluir novamente com consulta fresca). Problemas de fornecedor não podem se reduzir a uma contagem opaca de itens. Foco, scroll, destaque contextual e URL/estado de navegação devem ser acessíveis e seguros.

**Invariantes:** \`completed\` somente com 100% de validações obrigatórias comprovadas; qualquer divergência, erro técnico ou falta de prova mantém \`in_progress\` sem revisão publicada. Não reexecutar comparador no navegador, não inserir waivers automáticos, não escrever ERP, não mostrar dados sem autorização, não dar permissão por botão. Erros 403/404/409/422/502/503/504 continuam tipados; ao trocar caso, retry, refresh e versão, descartar estado transiente stale. REST/EVA consultam a mesma evidência persistida, sem nova MCP tool e sem payload paralelo.

## PRC-REF-021 — Contrato de decisão sobre divergências e correção governada (PO 2026-11-09)

**\`IMPLEMENTED_DEV\` (parcial quanto à escrita do solicitante).** Engenharia decide, **por item divergente identificado em tentativa oficial** (SB1 FIELD ou SA5 SUPPLIER_LINK+code+store+attribute), se: \`REQUESTER_CORRECTION\` — solicitar correção da ficha ao autor; \`ERP_MANUAL_CORRECTION\` — encaminhar ajuste do TOTVS para operador autorizado; \`NEEDS_CLARIFICATION\` — obter confirmação antes de escolher. Uma verificação \`MISMATCH\` nunca decide sozinha qual valor é correto; a decisão **não** muda \`field_results\` oficial, \`MATCH\`, registro vigente, código ou revisão. Solicitação permanece aberta; **devolução para correção não é \`reject\`**. Nova conclusão sempre relê os dados oficiais e só publica \`completed\` se **todos** os itens obrigatórios comprovados e sem erro.

**Implementado em DEV:**
- REST \`POST /v1/product-registration/requests/{id}/actions/route-divergence\` (\`operationId=prc_action_route_divergence\`) com CAS (\`expectedVersion\`), Idempotency-Key, AuthZ \`engineering.access\`, target tipado e \`decision\` enum.
- Persistência append-only via evento \`divergence_routed\` (sem migration nova); listagem em \`GET .../verifications\` → \`routings[]\`.
- \`allowedActions\` inclui \`route_divergence\` em \`in_progress\` / \`needs_information\` / \`under_review\`.
- Para \`REQUESTER_CORRECTION\`, resposta honesta \`requesterWrite.status=PENDING_OWNER\` + \`code=ARCHITECTURE_DECISION_REQUIRED\` — **sem** botão de escrita estruturada do solicitante e **sem** conceder \`engineering.access\`.
- UX: \`PrcVerificationPanel\` com cabeçalho compacto, **uma** tabela SB1+SA5 (Campo / Solicitado / TOTVS / Situação / Encaminhamento), filtro Problemas/Todos, expansão acessível da linha (sem coluna Observação), histórico recolhível, dialog \`Definir\`.

**Pendente (Core/Coordination):** contrato de proposta/correção estruturada versionada para solicitante sem \`engineering.access\`; vínculo automático rodada REF-019 ↔ encaminhamento; notificações/anexos. Paridade EVA do \`route-divergence\` pode seguir no mesmo contrato REST quando o bridge for estendido.

## PRC-REF-021-REF-01 — Supersessão: encaminhamento não compulsório, fornecedor por lookup oficial (PO 2026-11-09)

**\`IMPLEMENTED_DEV\`.** Prevalece sobre a exigência anterior de \`route_divergence\` como etapa operacional. O PRC continua fail-closed. Frontend sem modal/coluna Encaminhamento; \`allowedActions\` não inclui \`route_divergence\`; endpoint REST permanece \`deprecated=True\` para auditoria/compat (eventos \`divergence_routed\` legíveis em timeline/verifications.routings). Edição estruturada do solicitante sem \`engineering.access\` continua \`ARCHITECTURE_DECISION_REQUIRED\`.

**Consulta de fornecedor (implementada):** \`PrcOfficialSupplierSearchField\` → \`GET /v1/product-registration/reference-data/suppliers/search\` (\`prc_supplier_search\`) → api-delpi SA2. Identidade atômica \`supplierCode\`+\`store\` (strings); sem campos livres; estados loading/vazio/erro; reutiliza \`useSupplierSearch\` da ficha.

**Fila:** \`PrcFlagsOpsPanel compact\` dentro do \`EngineeringPageHero\` de \`PrcQueuePage\` — sem faixa externa; CRUD/AuthZ D16 preservados.

## PRC-REF-022 — Contrato: devolução para correção e edição da ficha pelo solicitante (PO 2026-11-10)

**\`IMPLEMENTED_DEV\` (Engineering API + Portal).** Prevalência: o fluxo operacional principal substitui \`needs_information\`/rodadas abertas como mecanismo padrão de correção e elimina editores paralelos; dados/eventos REF-019 permanecem legados legíveis. **AuthZ solicitante sem \`engineering.access\`:** superfície atual reutiliza \`engineering.access\` + object AuthZ (\`requester_subject\`) — adequado ao intake dual-role; solicitante puro sem \`engineering.access\` = \`ARCHITECTURE_DECISION_REQUIRED\` / \`PENDING_OWNER\` (Core/Coordination). Migration \`V021__prc_ref022_needs_correction.sql\`. REST: \`return-for-correction\`, \`PATCH .../returned-fields\`, \`resubmit-correction\`, \`GET .../correction-returns\`.

**Máquina alvo:** \`submitted --start--> in_progress\`; \`in_progress --return_for_correction--> needs_correction\`; \`needs_correction --save_returned_fields--> needs_correction\`; \`needs_correction --resubmit_correction--> in_progress\` (sem publicação automática, esperando avaliação Engenharia); \`in_progress --complete_attendance--> completed\` somente após fresh official read e zero erros; \`reject\` terminal pelo analista com motivo. Repetir devolução quantas vezes necessário. Não dar edição irrestrita ao autor por ser autor: durante atendimento, a Engenharia edita; durante devolução, o solicitante edita apenas o escopo devolvido; \`completed/rejected\` sem escrita técnica. Política para edição no \`submitted\` somente quando contrato existente for verificado, nunca inferir.

**Contratos a especificar antes do diff:** \`return_for_correction({requestId,targets:[{targetType:'FIELD'|'SUPPLIER_LINK',targetPath|supplierKey+targetAttribute,reason}],expectedVersion,idempotencyKey})\` acionado por analista; \`update_returned_fields({requestId,changes,expectedVersion,idempotencyKey})\` acionado pelo \`requester_subject\` autenticado com allowlist derivada do **servidor** e validação de campos/catálogo, incluindo SA5 por rowId e fornecedor code+store; \`resubmit_correction({requestId,expectedVersion,idempotencyKey})\`, com auditoria de anterior→novo, ator, timestamp, ciclo e correlação. Contrato de leitura de \`correctionRequests\` e capacidades \`canReturnForCorrection/canEditReturnedFields/canResubmit/canEditDraft/canComplete\` derivadas do backend, não só do frontend. Campos não devolvidos são imutáveis nesse estágio, inclusive por payload forjado e em conflitos CAS. Definir se para confirmação sem delta basta nota estruturada por alvo e como o backend valida sua presença; não inferir que texto livre é update SB1/SA5. Respostas não podem alterar produto oficial.

**Transação/persistência:** guardar vínculo entre caso, ciclo de devolução, itens selecionados, motivos, versão inicial, respostas/changes e autoria; eventos append-only; CAS do caso/draft e idempotência por operação/fingerprint. Consultar fontes oficiais antes da verificação, não para aplicar edição do solicitante. Migrations novas forward-only após inventário de versões e checks; preservar V018–V020, \`needs_information\`, rodada/resposta REF-019 e event log histórico. Se coexistência/transformação de casos antigos exigir owner, bloquear somente essa migração com \`ARCHITECTURE_DECISION_REQUIRED\`; nunca SQL em massa silencioso ou drop histórico. REST aliases antigos devem ser controlados/deprecados sem permitir transição indevida.

**AuthN/AuthZ:** Keycloak \`sub\` confiável, Core estabelece acesso à superfície/caso, Engineering API valida objeto e ação em runtime e rejeita tentativa de editar caso de terceiro, campo fora do escopo, usuário errado, etapa errada, replay indevido. Não usar \`engineering.access\` para requester comum, não usar somente equality client-side/JWT como autorização, não ampliar papéis sem owner. Separar \`read\`, \`save\`, \`resubmit\`, \`return\` e \`complete\`, com live permission checks, observabilidade e erros tipados.

**Conformidade técnica:** o componente de ficha \`create/read/edit\` reaproveita catálogo/schema e controles oficiais @delpi/plugin-ui; nenhum segundo editor baseado em inputs genéricos. Em \`needs_correction\`, somente os targets permitidos e respetivos detalhes são editáveis; atualização cria diff real e preserva os demais valores. Em \`completed\`, edição SB1/SA5 bloqueada mesmo com deep link/REST/MCP; bandeiras D16 seguem independentes. \`complete_attendance\` continua condição exclusiva de publicação mediante prova positiva de todos os atributos oficiais aplicáveis; sem escrita TOTVS.

**UX da devolução (PRC-REF-022-FIX-02, 2026-11-10):** o modal **Devolver para correção** apresenta uma lista única e uniforme — todos os campos corrigíveis (SB1 e atributos SA5) seguem o mesmo padrão **checkbox + motivo obrigatório**, sem seções, seletores de fornecedor, pesquisa oficial ou botão «Adicionar vínculo» (a devolução não cadastra vínculos). Por vínculo existente na ficha são derivadas as opções `Fornecedor` (link integral), `Part Number` e `Catálogo`; com mais de um fornecedor, o rótulo carrega a identidade (`Part Number — Fornecedor 000123 / 01`). A identidade técnica `supplierCode`/`store`/`targetAttribute` sai automaticamente da ficha e permanece invisível ao analista — a simplificação visual **não** reduz a granularidade da autorização nem altera o contrato `SUPPLIER_LINK`, CAS, idempotência ou auditoria.

## PRC-REF-023 — Contrato alvo de documentos opcionais de solicitação (decisão PO 2026-11-10)

**Status:** \`PO_APPROVED_FUNCTIONAL_TARGET / CONTRACT_DESIGN_REQUIRED / PLANNED\`. O PO aprovou receber **documentos opcionais** (datasheet, PDF e imagens) nas solicitações PRC de **CREATE e UPDATE**, disponíveis à Engenharia para análise e associados ao caso com autoria/proveniência. **Não existe autorização neste registro para upload em runtime, storage ad hoc, implantação ou acesso por outro bounded context.** Primeiro implementar o contrato governado da Engineering API; depois conectar as interfaces.

**Owner:** Engineering API é dona do vínculo \`request ↔ attachment\`, da elegibilidade de ações, autorização por objeto e histórico; bytes devem usar **storage oficial aprovado**, por port/adapter dedicado, cujo owner, retenção, antivírus/scan e contrato ainda exigem inventário/decisão. \`api-delpi\` e TOTVS continuam exclusivamente fonte oficial de leitura de produtos/fornecedores; anexos **não** viram evidência de MATCH, não geram escrita ERP nem tornam a EVA autoridade documental. \`requests-api\` tem storage próprio, porém **não** autoriza import de seu serviço/repositório/tabelas ou dependência runtime entre contexts. Reuso apenas de padrão ou de serviço documental neutro com contrato e novo owner legitimado.

**Contrato mínimo a especificar antes do código:**
- Registrar \`attachmentId\` opaco, \`requestId\` e escopo de caso, \`originalFileName\` sanitizado, \`mediaType\` validado por conteúdo, \`sizeBytes\`, \`sha256\`, \`storageKey\` privado, \`uploadedBySubject\`, \`createdAt\`, \`state\` (\`PENDING_SCAN|AVAILABLE|REJECTED|QUARANTINED|DELETED\`, nomenclatura sujeita a provider), e correlation/audit. Não expor storageKey/path físico, URL pública ou detalhes de infraestrutura.
- Propor endpoints versionados no namespace PRC: upload \`multipart/form-data\` vinculado ao caso criado com limite server-side; listagem autorizada; download streaming autenticado com \`Content-Disposition\` seguro; exclusão/remoção quando legítima com audit e política de retenção. URL/payload/response/errors, compatibilidade, idempotência, autorização e postconditions serão fechados com owner antes da implementação. Considerar associação atômica ou protocolo de staging/finalize com limpeza de órfãos e retry idempotente; não prometer transação única entre PG e blob storage.
- Permitir **nenhum anexo** sem bloquear criação ou conclusão. Tipos pretendidos: PDF e imagens comuns (PNG/JPEG/WebP); dimensões/quantidades/bytes exatos **não aprovados ainda**: confirmar limites do provider e defesa do gateway; não inferir 25 MB da tela de Minhas Solicitações como contrato de Engenharia. Rejeitar extensões/content-type enganosos, conteúdo ativo/perigoso, tamanho excedido; aplicar política real de malware scan e download seguro. Não realizar OCR/extração/IA por padrão: interpretação futura exige consentimento/contrato/provenance.
- Decidir explicitamente política de anexos durante \`submitted\`, \`in_progress\`, \`needs_correction\`, \`completed\` e \`rejected\`, inclusive se solicitante pode anexar novos documentos na devolução. Padrão seguro: apenas create e UPDATE intake já aprovados funcionalmente; outras ações \`PENDING_OWNER\`. Histórico e anexos antigos imutáveis/retidos segundo contrato; sem vazamento de casos de terceiros.
- Conclusão REF-020 permanece \`MATCH\` dos dados oficiais da Engineering API; anexo é apoio informacional, nunca bypass, fonte oficial ou correção automática de campo. D16 notas e REF-022 devolução continuam independentes. Download/listagem devem aplicar Core + Engineering object/live AuthZ, e não apenas verificar que o usuário conhece ID.

**Gates de implantação da Fase API:** approval de storage/security/retention, backend-first, migrations novas forward-only se necessárias, testes de upload/list/download/scan/error rollback/órfãos/duplicidade/owner/403/404/413/415/CAS quando aplicável, PostgreSQL real, E2E API autenticado, documentação operativa e deploy apenas DEV após permissão. Se owner/storage não estiver aprovado, produzir contrato e marcar \`PENDING_ATTACHMENTS_CONTRACT / ARCHITECTURE_DECISION_REQUIRED\`, sem fake filesystem storage nem PASS simulado.

**Implementação F01 (2026-11-10) — `PROVEN` em DEV:**

- **Storage:** padrão canônico `persistent-upload-storage` — metadado em `engineering.product_registration_attachments` (V022/V023, schema plugins-hub) + bytes em volume dedicado `ENG_PRC_ATTACHMENTS_DIR` (`/app/data/prc-attachments`, espelhado em `DELPI_DATA_HOST_DIR/prc-attachments`, ambos os composes). Port `AttachmentStoragePort` com adapters `LocalVolumeAttachmentStorage` (disk) e `MemoryAttachmentStorage` (testes); zero dependência de internals `requests-api`.
- **Endpoints** (`/v1/product-registration/requests/{id}/attachments`): `POST` multipart (413 >10 MB server-side, 422 tipo/conteúdo inválido, 403 não-solicitante, 409 estado não permitido), `GET` listagem (sem `storageKey`/path), `GET .../{attId}/download` (identidade composta caso+anexo, `Content-Disposition: attachment`, `X-Content-Type-Options: nosniff`, `Cache-Control: private, no-store`, somente `AVAILABLE`). Sem endpoint de exclusão — política de remoção `PENDING_OWNER` (retenção via estado `DELETED`, sem hard delete; `eng_prc` sem grant DELETE).
- **Validação por conteúdo (magic bytes):** PDF/PNG/JPEG/WebP com checagens estruturais mínimas; extensão e Content-Type do cliente nunca são prova; nome sanitizado (sem path traversal); `sha256` + `sizeBytes` reais persistidos.
- **Autorização:** upload exclusivo do `requester_subject` do caso, estados `submitted`/`in_progress` (`needs_correction`/`completed`/`rejected` = `PENDING_OWNER`, rejeitados com 409). Listagem/download seguem o mesmo escopo de leitura do caso (solicitante + analista `engineering.access`); gate `@require_any_permission(engineering.access)` antes do objeto.
- **Idempotência/integridade:** dedup por `(request_id, sha256, original_file_name)` — retry do mesmo arquivo retorna o vínculo existente (`deduplicated: true`), sem duplicar documentos. Estratégia de falha parcial: valida → grava bytes → persiste vínculo; falha no DB remove o blob (sem órfãos por esse caminho); `PENDING_SCAN`/`REJECTED`/`QUARANTINED`/`DELETED` modelados para scanner futuro.
- **Estados:** hoje o scan é validação estrutural síncrona → `AVAILABLE`. **AV/malware scan real: `PENDING_OWNER`** — inexistente na plataforma; o modelo de estados e o port já suportam adapter de inspeção futuro.
- **Limites propostos (pendentes de ratificação PO):** 10 MB/arquivo, 10 documentos/caso, PDF/PNG/JPEG/WebP.
- **Frontend (MFE Engenharia):** seção «Documentos de apoio (opcional)» na etapa Ficha do `PrcCreatePage` — seleção múltipla com pré-validação client-side (lista com nome/tamanho, remoção pré-envio); upload **após** a criação com `requestId` real, falha de anexo não derruba a solicitação e mantém retry com o mesmo `caseId` (sem recriar). Seção «Documentos de apoio» no `PrcDetailPage` com metadados (nome/tipo/tamanho/autor/data/estado) e download autorizado autenticado (Bearer → Blob → `a[download]`), nunca URL pública.
- **Testes:** 22 cenários pytest (upload válido/falso-mime/corrompido/vazio/413/403/404/409/dedup/sanitização/multi/cross-case download 404) + vitest do helper; regressão REF-019/020/021/022/D15/D16 intacta. Playwright autenticado DEV: `TEST_NOT_RUN` (sem harness de sessão no ambiente).

**Adendo F01-FIX-01 (2026-11-10) — padronização plugin-ui + revisão antimalware:**

- **UX padronizada:** o upload do formulário usa exclusivamente o kit oficial via façade `engineeringUi` — `EngineeringFileDropzone` (`createDashboardFileDropzone` + `fileDropzoneBemClasses("engineering","file-dropzone")`) e `EngineeringAttachmentFileList` (`createDashboardAttachmentFileList` + `attachmentFileListBemClasses("engineering")`), classes dual `delpi-ui-*` com CSS canônico do kit. Input nativo visível removido; labels de limite derivam de `PRC_ATTACHMENT_MAX_*` (espelho do contrato da API). Lista marca arquivos como «ainda não enviados» — nunca apresentados como persistidos; falha parcial mantém `caseId` com botão de retry que reenvia só os documentos (não recria solicitação). Sem JSX/CSS copiado de Minhas Solicitações.
- **Inventário antimalware cross-app (evidências):** requests-api valida apenas MIME declarado + tamanho; commercial/transformometro seguem mesmo padrão disco+metadado; baseline DÉLIA registra «Malware scanner (ClamAV etc.): NOT_PROVEN»; doc Controladoria (ciclo3-p2-upload-contract-gate) formaliza a mitigação aprovada: **allowlist MIME+extensão+magic bytes, sem antivírus**. Nenhum serviço corporativo de scan/quarentena existe na plataforma — `PROVEN` por inspeção de código e docs.
- **Semântica honesta:** `AVAILABLE` significa «passou na validação estrutural vigente», **nunca** «scan antimalware aprovado». O DTO do anexo carrega `inspection:"structural"` explicitamente; `PENDING_SCAN|REJECTED|QUARANTINED` permanecem modelados para adapter de inspeção futura. Classificação do gate: **`PENDING_MALWARE_SCAN_OWNER`** — sem criação de serviço/ClamAV sem aprovação.
- **Mitigação vigente (paridade contratual):** magic bytes + estrutura mínima por tipo + nome sanitizado + limite server-side + quarentena por estado — equivalente ou mais forte que os demais apps inventariados.
- **Limites:** proposta v1 (10 MB/arquivo, 10/caso, PDF/PNG/JPEG/WebP) segue `PENDING_RATIFICATION` em DEV — sem ampliação silenciosa.

**Adendo F01-FIX-02 (2026-11-10) — miniaturas e pré-visualização com primitivas oficiais:**

- **Mesmo padrão de Minhas Solicitações** via façade `engineeringUi`: `EngineeringAttachmentPreviewStrip` (`createDashboardAttachmentPreviewStrip` + `attachmentPreviewStripBemClasses("engineering")`) e `EngineeringFilePreviewModal` (`FilePreviewModal` com `portalScopeClassName=portal-engineering`, modal contido no host MFE). Zero JSX copiado de my-requests; zero dropzone/lista paralela.
- **Formulário (create/update):** strip em `mode="manage"` — imagens ganham thumbnail real via object URL local (criada só para `image/*`, revogada na remoção/substituição/desmontagem); PDF e demais usam ícone oficial por tipo. Clique abre modal com `source=File` (loader do kit gerencia object URL internamente). Estados por arquivo no caption: `Selecionado → Enviando… → Enviado | Erro — <motivo>`; enviados não são removíveis.
- **Detalhe:** strip em `mode="preview"`; thumbnails de imagens persistidas via blob autenticado (`GET .../download`) → object URL revogada no cleanup; modal com `source=() => downloadPrcAttachment(...)` — fetch lazy autenticado, sem URL pública nem storageKey; ação «Baixar» usa a mesma rota governada.
- **Retry honesto:** `uploadedIdx` marca arquivos confirmados — retry reenvia somente pendentes/com erro, sem recriar a solicitação (`createdRequestId` preservado).
- **Segurança:** decisão PO de não implementar antimalware nesta etapa **não** altera a classificação `PENDING_MALWARE_SCAN_OWNER` (ausência documentada, mitigação = validação estrutural por conteúdo); `inspection:"structural"` permanece no DTO; AuthZ e headers de download inalterados.

**Consumer futuro Minhas Solicitações:** exibir o mesmo formulário/campos/validações canônicos do PRC, consumindo contrato oficial Engineering API mediante adapter versionado e permissão de solicitante aprovada. Não duplicar persistência de CREATE/UPDATE em \`requests-api\`; a transição entre o stub \`raw-material-creation\` existente e PRC oficial, eventual alias/tipo UPDATE e sincronização com \`/mine\` **exigem decisão Coordination/owners de ambos** antes do cutover. Documento: plano REF-023 no roteiro PRC e evolução Controle MP.

## PRC-REF-023-F02/F03/F04 — Contratos de consumo entre Portal Engenharia e Minhas Solicitações (PO 2026-11-10)

**\`PO_APPROVED_TARGET / PLANNED / ARCHITECTURE_DECISION_REQUIRED\` para conexão entre contexts.** A UI de anexos F01-FIX-02 foi validada visualmente pelo PO em CREATE; **a cobertura UPDATE/detalhe e a integração My Requests ainda dependem de teste/implementação, não presumir concluídas**.

**F02 — contrato documental inalterado:** requestId oficial de caso PRC; \`POST/GET /requests/{requestId}/attachments\` e \`GET /requests/{requestId}/attachments/{attachmentId}/download\` com AuthN/AuthZ por objeto. Visualização dos arquivos autorizados no detalhe/Ficha técnica em \`in_progress\` com mesma \`AttachmentPreviewStrip\` + \`FilePreviewModal\`, Blob autenticado e object URLs liberadas. CREATE e UPDATE (novo caso) compartilham upload pós-intake; 0 arquivo permitido; sucesso parcial não gera case duplicado; retry somente arquivos não confirmados. \`needs_correction\`: consulta conforme policy de leitura existente; novo upload durante correção é \`PENDING_OWNER\`, sem extensão silenciosa de \`ATTACHMENT_UPLOAD_STATUSES\`. Arquivos concluídos/rejeitados não recebem alteração técnica automática. \`inspection:"structural"\` e \`AVAILABLE\` não significam antivírus aprovado; **não implementar AV nesta etapa**, risco/owner permanece pendente. Limites 10MB/10 ainda aguardam ratificação; sem abrir download público.

**F03 — contrato consumer antes de UI:** definir owner oficial, versão, AuthN/AuthZ, catálogo do PRC, DTO CREATE/UPDATE, normalização e field paths, busca SA2/SA5, PN obrigatório/Catálogo opcional, estágio/upload de documentos, erros estruturados, CAS, idempotência, correlator entre request e origem \`my-requests\`, limites, observabilidade e compatibilidade. Minhas Solicitações deverá consumir os **mesmos Application Use Cases da Engineering API via adapter oficial**, com UI/form controls compartilhados de fonte neutra quando Abstraction Gate provar necessidade; sem importar \`PrcCreatePage\` diretamente por runtime acoplado nem replicar validators/backend de PRC no \`requests-api\`. A submissão é um caso Engineering API; não fazer \`requests-api\` e Engineering API gravarem a mesma operação.

**F04 — read model/projeção e correções:** estabelecer contrato \`list_my_prc_requests\` (ou projeção equivalente aprovada) de leitura autorizada para \`/mine\`, com \`source/type/id/status/createdAt/detailUri\` e paginação/filtros, sem consultar DB de Engenharia diretamente. Identidade de solicitante derivada de Keycloak e intake confiável, com object AuthZ Core/Engineering para criar/listar/ler, uploads/downloads, \`save_returned_fields\` e \`resubmit_correction\`; acesso a terceiros negado. O editor de My Requests mostra apenas campos devolvidos pela Engenharia e não altera MATCH, ERP, revisões nem flags internas. Mapeamento de casos legados requests-api e solicitação PRC nova deve ter owner/compatibilidade/links claros, sem migração ou dual-write não governados. Engineering analisa e conclui pelo REF-020 com leitura oficial fresca e falha fechada.

**BLOQUEIO:** integrar solicitante comum sem \`engineering.access\` exige decisão Core e owners dos contexts (não basta \`requester_subject\` ou JWT). Contratos devem especificar permissão efetiva de entrada e consulta da Engineering API, não somente permissão do host My Requests. Não registrar \`PROVEN\` de integração antes de autenticar duas identidades e verificar caso único nos dois portais.

## PRC-REF-023-OWNER-CLARIFICATION — Matriz de acesso por superfície sem novos papéis (PO 2026-11-10)

**Decisão funcional \`PO_APPROVED_TARGET\`:** o mesmo PO exerce ownership de Engenharia, Minhas Solicitações, Core e APIs. Os acessos **existentes** de Minhas Solicitações autorizam a entrada do usuário comum; \`engineering.access\` continua exclusivo para as funcionalidades operacionais do Portal Engenharia. Não inventar ou atribuir \`engineering.access\` ao solicitante; não exigir novo papel para iniciar PRC. **Prevalece** sobre a exigência genérica anterior de nova aprovação funcional multi-owner; o contrato técnico/autorização backend continua obrigatório.

| Operação | Superfície | Controle backend necessário |
|---|---|---|
| Criar CREATE/UPDATE PRC e enviar anexos opcionais | Minhas Solicitações | Permissão efetiva existente de My Requests **a inventariar**, identidade autenticada e autorização da ação/caso na Engineering API |
| Listar, ler, baixar anexo da própria solicitação | Minhas Solicitações | Permissão My Requests existente + isolamento por \`requester_subject\` / objeto |
| Salvar correções e reenviar devolvida | Minhas Solicitações | Permissão My Requests existente, estado \`needs_correction\`, mesmo solicitante e allowlist estrita de FIELD/SA5 |
| Iniciar atendimento, editar ficha de Engenharia, devolver, rejeitar, verificar/concluir | Portal Engenharia | \`engineering.access\`, live AuthZ por ação/caso, CAS/idempotência |
| Ler documentos, bandeiras internas e dados técnicos no atendimento | Portal Engenharia | \`engineering.access\` e escopo de leitura/autorização vigente |

**Implementação:** inventariar nomes concretos das permissões, middleware e routes de My Requests/Core e seus claims confiáveis antes de alterar o gate HTTP da Engineering API. Separar rotas/use cases de solicitante das de analista; backend valida permissão real e object AuthZ para cada operação; não aceitar somente frontend, nome do app, flag \`canEdit\`, string JWT ou \`requester_subject\` no payload. Aplicar menor extensão contratual necessária para o consumer, versionar erros e observabilidade, testar cross-user/403 e duas identidades. Se contrato de permissão existente não puder ser verificado, marcar \`TO_INVENTORY/PENDING_CONTRACT\` apenas a parte faltante — não criar papel fictício e não bloquear o planejamento com um ciclo abstrato de owners.

**Fonte de verdade:** Engineering API PRC para caso/versões/documentos; requests-api permanece dona de seus chamados legados, **sem dual-write** do mesmo PRC. As duas interfaces veem o mesmo caso via contratos; Core mantém RBAC; TOTVS somente leitura oficial na conclusão. Decisão de ownership da jornada não substitui testes, esquema de autenticação, nem permite acesso a casos de terceiros.


## 15. Aditivo de protocolo — solicitação, revisão de produto e proveniência (PO, 14/11/2026)

**Classificação:** `PO_APPROVED_SEMANTIC_TARGET / PROTOCOL_CHANGE_REQUIRES_ARCHITECTURE_DECISION / IMPLEMENTATION_PENDING`. O contrato existente descrito acima continua representando a implementação atual até inventário e ratificação de eventual alteração de campos. Esta seção não constitui autorização de migration ou publicação.

1. **Agregado Solicitação PRC:** tem `requestId`, `caseVersion` (`row_version`, guarda CAS), estado, atores, histórico, proposta e `officialProductCode` quando aplicável. Não possui `revisionNumber` como atributo próprio; `caseVersion` jamais deve ser rotulada revisão de produto.
2. **Produto-alvo ≠ revisão produzida:** UPDATE referencia produto existente para consulta e comparação. A referência técnica de revisão vigente no intake (`baseRevision`/`base_revision_number`) pode ser necessária para impedir lost update; é **baseline de comparação/concorrência**, não autoria ou publicação por aquela solicitação. CREATE pode não ter código oficial nem ficha versionada.
3. **Publicação/linhagem:** a revisão técnica do produto é filha do `record` de produto. `product_registration_revisions.request_id` é proveniência da **solicitação concluída que gerou aquela revisão**, com evidência de verificação oficial e autorização; não atribuir revisão a PRC aberta/rejeitada. Em publicação, transação/CAS/idempotência impedem link/revision duplicado. Não produzir revisão quando uma Vn já existir e não houver diff técnico (R02), nem publicar em erro, mismatch ou conflito.
4. **Primeira baseline:** a primeira conclusão válida de produto ainda sem histórico versionado gera V1 baseline (R01), mesmo com diff técnico vazio, e aponta ao requestId concluído. Não declarar, por isso, “criação de produto no TOTVS”.
5. **Conclusões sem nova Vn:** pedido concluído e auditado pode ter `publishedRevision=null`, `changeKind=no_op` ou outro resultado explícito **somente se já suportado pelo contrato ratificado**; não reaproveitar arbitrariamente `request_id` de Vn anterior. Inventariar modelagem existente de `completed_record_id`, response de conclusão, revision/provenance e downstream consumers antes de alterar payload.
6. **API de leitura e UI:** distinguir `targetProduct`, `concurrencyBaseline`, `publishedRevision` e `caseVersion` em nomenclatura e documentação alvo; não renomear campos públicos atuais sem estratégia compatível. Exibir revision publicada e solicitação-originadora no contexto de Produtos acompanhados após conclusão. `baseRevision` pode permanecer no protocolo por compatibilidade, com semântica expressa e ajuda ao consumidor.
7. **Segurança e ownership:** Keycloak/Core para identidade/RBAC, Engineering API para casos/revisões acompanhadas, TOTVS/Domain API para dados oficiais. Confirmação manual ERP, validação leitura fresca, AuthZ por objeto, guardas de revisão, transação e audit trail seguem fail-closed. Sem dual-write em requests-api nem vínculo por heurística do frontend.

**Gates técnicos obrigatórios antes de mudar protocolo:** inventariar na `main` os contratos GET/POST/DTO/DB/migrations, todos os consumidores (engineering MFE, My Requests, Home, outras capabilities), casos CREATE/UPDATE, saída de `verify-and-complete`, CAS/stale_revision, no-op, V1 baseline, revisions provenance, negativos/AuthZ e rollback. Produzir `ARCHITECTURE_DECISION_REQUIRED` para qualquer alteração de contrato/DB/owner; preservar código existente até aprovação. Após autorização, mudança aditiva/versionada, testes de compatibilidade em memory/Postgres, runtime DEV/HML, sem writes de negócio em PRD.

## 16. Ratificação PO/Coordination — revisão atribuída somente após conclusão (14/11/2026)

**Decisão superveniente e AUTORIZAÇÃO SEMÂNTICA:** o PO autoriza expressamente corrigir protocolo, persistência e UI para **não atrelar uma solicitação aberta a uma revisão de produto**. Uma solicitação UPDATE pode apontar ao código oficial do **produto-alvo** e carregar alterações propostas, mas não possui `baseRevision` de negócio, `publishedRevision` ou referência persistente à revisão como pertencente ao caso enquanto estiver aberta. `caseVersion` permanece somente mecanismo técnico CAS, não revisão de produto. O chip de revisão base e a referência de revisão no popover do detalhe devem desaparecer.

**Regra de conclusão:** reconsultar dados oficiais e estado técnico mais recente sob leitura/autorização governadas, detectar concorrência entre solicitações independentes e confrontar `requestedChanges` com baseline/evidência aplicável antes de qualquer publicação. Não confiar em revisão capturada na abertura como autoridade. Sob concorrência real, exigir revalidação/rebase explícitos ou falhar fechado (`state_conflict`/`stale_revision` compatíveis); não perder alterações de outro caso, não publicar automaticamente a proposta em baseline desatualizada, não gerar duplicata sob retry. Guardas `expectedVersion` do **caso** permanecem; introduzir/verificar guarda de **produto** no fechamento, sem expor revisão de produto no contrato de intake.

**Proveniência transacional após conclusão validada:** se a solicitação produzir **V1 baseline inicial** ou **Vn+1 com diferença técnica real**, persistir vínculo `request_id → record_id + revision_number + evidence` na mesma unidade transacional governada e exibir revisão publicada somente no caso concluído e na timeline de versões do produto. Se concluída com `no_op` após Vn já existir, não gerar Vn+1 nem fingir que a solicitação originou a revisão existente; mostrar resultado de conclusão sem nova revisão. Se não concluída, rejeitada, mismatch ou ERP indisponível, nenhum vínculo com revisão publicada. `officialProductCode` é vínculo com o produto-alvo, não com revisão.

**Transição/compatibilidade:** inventariar consumidores de `baseRevision` em HTTP/DTOs, My Requests, engineering MFE, reports, banco, repositórios memory/Postgres, guards, documentação, testes e dados legados. Especificar transição aditiva e tolerância a consumidores antigos; **não** executar DROP destrutivo nem reescrever histórico sem inventário, migração autorizada e rollback. Uma referência histórica existente em caso aberto deve ser tratada como metadado legado/concorrência, sem ser apresentada como revisão gerada; preservar provenance efetivamente publicada em casos concluídos. Se uma decisão de owner de contrato externo ou nova authority for necessária, retornar `ARCHITECTURE_DECISION_REQUIRED`; a alteração semântica do domínio PRC está ratificada.

**Estado:** `PO_SEMANTIC_CHANGE_APPROVED / IMPLEMENTED / PROVEN_HML / PRD_NOT_AUTHORIZED` — implementação `4788a1efa6` (14/11/2026): read model do detalhe passou a emitir `publishedRevision` (resolvido por `product_registration_revisions.request_id` ↔ `completed_record_id`) e deixou de emitir `baseRevision`; intake UPDATE continua tolerando `baseRevision` como entrada legada, mas o valor é validado e substituído pela baseline vigente no servidor (não há confiança no dado do navegador); UI V3 removeu o chip «Revisão base» e a linha do popover, exibindo «Revisão técnica gerada: Vn» ou «Concluída sem nova revisão técnica» somente em caso concluído; aba Revisões ganhou coluna/link «Solicitação de origem». Guarda de produto no fechamento já existia (`stale_revision` via `current_revision_number` vs baseline persistida, 409 fail-closed) — confirmada por teste de concorrência A/B. As descrições antigas de `baseRevision` como obrigatório no UPDATE são **legado a reconciliar**, não um novo requisito de UX; novo intake não deve depender de vínculo de revisão. Preservar regras R01–R18, incertezas, evidência e fonte oficial TOTVS.

## 17. Política de validação oficial sem escrita TOTVS para testes (PO, 14/11/2026)

**Diretriz superveniente do PO — vinculante:** **não criar massa de teste alterando cadastro no TOTVS**, seja HML ou PRD. A alteração/cadastro oficial de produto é ato de usuário competente diretamente no TOTVS em uso real; a validação operacional ponta a ponta de conclusão+revisão com alteração real ficará para fase final do produto, em produção, sob usuário autorizado e plano de acompanhamento/rollback governado. Isso **não autoriza deploy PRD nem testes de escrita pelo agente**.

**Gate de engenharia antes da liberação:** demonstrar que a Engineering API, como consumer somente de leitura, consegue consultar TOTVS por adapter oficial e comparar campos verificáveis de ficha, atributos e fornecedores; emitir `matched` somente com correspondência integral do escopo autorizado; `mismatched`, `unverifiable`, `not_found`, `forbidden`, `timeout`, `contract_error`, `unavailable` impedem conclusão e publicação, com evidência/observabilidade e estado apropriado. Testes de API/serviço podem usar fixtures e doubles de resposta oficial identificados como simulados, incluindo match/mismatch, missing, fornecedor parcial, 403/503/504, concorrência, CAS, replay/idempotência, sem realizar PUT/POST/PATCH no TOTVS. Leitura real não mutável autorizada pode provar conectividade e mapeamento de campos com produtos existentes, mas **não prova criação de revisão real** nem concede autorização de conclusão em PRD.

**Precisão semântica:** `matched` atesta correspondência com a proposta; não atesta por si só existência de alteração temporal no TOTVS. A transação governada de conclusão decide V1 inicial, Vn+1 somente com diff técnico real, ou no-op sem Vn+1 conforme R01–R03. Nada deve inventar proveniência de cadastro oficial feito por PRC/IA.

**Cobertura/evidência:** matriz `campo PRC → campo TOTVS/adapter → expectativa → valor observado → normalização → resultado → limitação`; comprovar comparação e falhas de cada campo crítico, com cobertura de suppliers SA5 e leitura parcial/unverifiable; testes negativos must-pass. Reportar por gate `PASS/FAIL/INCONCLUSIVE/TEST_NOT_RUN`; `REAL_TOTVS_WRITE_MATCH_E2E=DEFERRED_TO_END_USER_PRD_AFTER_FULL_FLOW`. Não bloquear avanço de implementação pelo cenário deliberadamente fora do escopo; tampouco marcá-lo como PASS.

**Owner:** TOTVS/Domain API governa dados oficiais; Engineering API apenas leitura/verificação e revisões técnicas próprias. Qualquer necessidade de escrita automática no ERP é fora do escopo e requer nova decisão formal.


---

## PRC-TOTVS-AUTOMATION-AND-NORMATIVE-SIMILARITY — Direção vigente 18/11/2026

**TASK_ID de planejamento:** `PRC-TOTVS-AUTOMATION-NORMATIVE-SIMILARITY-MASTER-PLAN-01`  
**Estado:** `PO_DIRECTION_RECORDED / TARGET / CONTRACT_INVENTORY_REQUIRED / IMPLEMENTATION_NOT_AUTHORIZED / NO_TOTVS_WRITE_EXECUTED_BY_THIS_PLAN`  
**Data de decisão:** 18/11/2026  
**Produto/owner de negócio:** Portal Engenharia / Engenharia (PRC). **Engineering API** é owner do caso e das regras do fluxo; **api-delpi** é owner de integração REST/ERP; **TOTVS** é fonte de verdade de produto/fornecedor; **Keycloak/Core** fornecem identidade/RBAC; **EVA** interpreta, compara e recomenda sem aprovar ou publicar; **Plugin UI** e MFEs compõem a experiência.  
**Recurso documental principal para continuar esta trilha:** este capítulo de `docs/12-roadmap-e-evolucao/engineering/PRODUCT-REGISTRATION-MVP-TECHNICAL-CONTRACT.md`. Acrescentar decisões e evidências **aqui** nas próximas rodadas; não criar sucessivos master plans concorrentes. Referenciar normas/contratos já existentes, sem copiá-los.

### 1. Precedência, escopo e mudança de contexto

O documento legado `controle-mp/EVOLUCAO.md` (preservado no histórico Git até o commit de migração) representava migração do antigo iframe/Request Engine e deve ser tratado como **baseline histórica**, não como instrução vigente de criar um novo fluxo `requests-api` para matéria-prima. O PRC operacional atual possui **uma solicitação de Engenharia governada pela Engineering API**, consumida tanto pelo Portal Engenharia quanto por Minhas Solicitações. Não criar segunda autoridade, clone de pedidos, segundo cadastro mestre nem importações cruzadas entre bounded contexts.

O recorte de conversa/UX foi concluído pelo PO em 18/11/2026; evidências, SHAs e resíduos estão em [fechamento consolidado PRC](./PRC-CONVERSATION-UX-PRODUCTION-CLOSURE-2026-11-18.md). Este capítulo é uma **nova evolução**, e não reabre esse aceite.

A regra antiga que descrevia **cadastro/alteração manual no TOTVS, seguido de verificação** permanece descritiva do fluxo anterior. O alvo agora é permitir execução **assistida e automatizada via API**, com confirmação explícita do analista autorizado. A política histórica `TOTVS_WRITE_TEST_FORBIDDEN` em [plano canônico PRC-TRACK](./PRC-TRACK-CANONICAL-PRODUCT-RULES-AND-EXECUTION-PLAN.md) permanece válida para testes comuns do PRC e **não é revogada genericamente** por esta decisão de planejamento. Qualquer ensaio de write em **TST01** requer aprovação técnica/operacional delimitada, massa segura, snapshot/restore, pin de ambiente e evidências; **nenhuma escrita produtiva está autorizada por este documento**.

**Escopo inicialmente proposto:** CREATE e UPDATE de cadastro de produto (SB1), operações de vínculo fornecedor/produto (SA5) a inventariar, pré-análise de possíveis duplicidades com normas técnicas DELPI, read-after-write oficial e conclusão do PRC somente após verificação. DELETE de produto não faz parte da automação proposta.

### 2. Inventário de capacidades já existentes (e lacunas)

| Capacidade | Evidência / fonte no repositório | Classificação |
|---|---|---|
| PRC intake, atendimento, revisão e conclusão por verificação oficial | `engineering-api/.../product_registration/service.py`: `complete_attendance`/`verify_and_complete` | `PROVEN_CODE`; manter como única autoridade de conclusão |
| Consulta produtos/fornecedores e lookup de Part Number | `api-delpi` e [evidência de similaridade DAVI](../../../api-delpi/docs/integrations/evidence/davi-product-detail-similarity-001.md) | `PROVEN_CODE/CONTRACT` na superfície existente; autorização do consumidor PRC a validar |
| Escrita produto UPDATE | `PUT /integrations/protheus/products/{product_code}` no `protheus_router.py`; [playbook](../../../api-delpi/docs/integrations/protheus-write-integration-playbook.md) | `PROVEN_CODE`; ensaio TST01 17/11 documentado; **não integrado ainda ao PRC** |
| Representação completa da ficha UPDATE | `delpiproduto` lê todos os campos B1 no `DLP04I01.PRW`; façade exige 21 campos + código do path | `PROVEN_DOCUMENTED`; PUT parcial pode zerar campos/gerar falha |
| Produto CREATE | Upstream `delpiproduto/v1/IncProduto/incluir` documentado, sujeito à conferência do handler publicado | `TO_INVENTORY` para contrato e operação live; façade `POST` api-delpi **não localizada** em inspeção 18/11 |
| Fornecedor e vínculos SA5 | Lookup SA2 e consulta/edição proposta de vínculos no PRC | `TO_INVENTORY` para existência de **write** SA5 autorizado (ADD/UPDATE/REMOVE); **não** confundir com PUT de SB1 |
| Normas técnicas MP | [normas governadas](../../../api-delpi/docs/api/padroes-totvs/normas-tecnicas-descricao-materias-primas.md) (knowledge freeze-002) | `PROVEN_DOCUMENT` como orientação normativa, não truth de produto |
| Avaliação normativa de descrição | `engineering-api/engineering_app/application/drawing/normative_description.py` (`normative_description.v1`) | `PROVEN_CODE` para avaliação de uma descrição; reuso no PRC condicionado a contrato/owner e testes |
| Composição de similaridade READ | DAVI `search_products` + detalhe + PN + fornecedores + conhecimento técnico | `PROVEN_DOCUMENTED` como referência de reuso; **não** criar dependência runtime no agente DAVI/Chat legado |
| Confirmação pós-escrita | PUT atual retorna `ACKNOWLEDGED`, `persistence_proven=false` | `GAP`: read-after-write e reconciliação autoritativa no fluxo |
| Automatização PRC → ERP | Fluxo PREPARE/ACT e composição de operações | `TARGET`, não declarar deploy |

**Regra de inventário:** contrato e código atuais vencem este quadro quando divergirem; manter `PROVEN`, `TO_INVENTORY`, `TARGET` e teste `PASS/INCONCLUSIVE/TEST_NOT_RUN` separados. Revalidar `HEAD`, `origin/main` e serviço real antes de implementação.

### 3. Jornada alvo do analista no Portal Engenharia

1. **Receber/analisar PRC:** CREATE ou UPDATE, ficha técnica, grupo, descrição, fornecedores e PN, documentos, bandeiras e justificativas, com dados permitidos ao ator.
2. **Analisar correspondências técnicas antes de CREATE:** identificar família, aplicar norma DELPI versionada, extrair atributos conhecidos, buscar candidatos oficiais semelhantes, obter fichas SB1 e vínculos SA5/PN, explicar convergências e diferenças; não exigir correspondência textual exata.
3. **Decisão do analista:** `UTILIZAR_EXISTENTE`, `DEVOLVER_PARA_CORRECAO` (ação governada já existente) ou `PROSSEGUIR_NOVO_CADASTRO` com justificativa; nenhum agente decide sozinho. Reuso de existente exige caminho de negócio explicitamente aprovado (não trocar silenciosamente código ou encerrar sem verificação).
4. **Preparar aplicação no TOTVS:** somente no backend, materializar operação permitida, payload, valores originais, diferenças, identidade do objeto/caso/versão, snapshot oficial, fingerprint, risco e resultado de similaridade. Mostrar ao analista `Antes → Solicitado`, fornecedores e operações; prevenir lost update.
5. **Confirmar autorização:** interação explícita por usuário com permissão live de escrita, ligada a proposta expiráveis/versão/caso, sem confiar em JWT/frontend como authority e sem usar identidade de outro ator. Revalidar semelhanças/cadastro antes de ACT.
6. **Executar escrita governada:** Engineering API invoca a capacidade api-delpi autorizada; api-delpi resolve Core identity, destino pinado, gate, ledger pré-envio; Protheus executa rotina oficial via REST/`MSExecAuto`. **Sem SQL de escrita nem retry automático**.
7. **Confirmar persistência:** ler novamente produto e vínculos pelo contrato oficial, confrontar os campos pretendidos; só evidência de `CONFIRMED` e validação PRC atual permite publicar revisão e concluir. `ACKNOWLEDGED` sozinho não basta.
8. **Tratar falha/indeterminação:** `REJECTED`, `UNKNOWN`, divergência, concorrência ou confirmação parcial deixam solicitação aberta para reconciliação/suporte, sem segunda tentativa cega e sem falsa conclusão.
9. **Auditar/acompanhar:** correlacionar `request_id`, `operation_id`, `actor_subject`, `protheus_user_id`, versão do caso, timestamp, origem normativa, candidatos comparados, justificativa, payload hash, ACK/CONFIRM e revisão publicada. Não registrar tokens/secrets.

O botão de **Concluir atendimento** não deve disparar write implícito. Exibir etapa distinta **Aplicar no TOTVS** (PREPARE → confirmação → ACT → read-back), seguida da conclusão já governada.

### 4. Similaridade normativa — objetivo e escopo

**Decisão PO (18/11/2026):** não basta igualdade da descrição. Uma descrição escrita com abreviações, sequências distintas ou unidades diferentes pode denotar produto próximo. O motor deve aplicar **a norma ratificada da família técnica** e explicar se um produto semelhante já existe. A finalidade é apoiar organização do cadastro, não bloquear automaticamente a análise.

**Pipeline candidato (contrato a ratificar):**

`PRC descrição + dados técnicos + fornecedores/PN` → `norma aprovada por grupo/subtipo + extração/normalização determinística` → `busca limitada por descrição parcial, atributos, grupo e PN` → `detalhe oficial por candidato` → `vínculos de fornecedores` → `comparação explicável pela EVA` → `decisão humana auditada`.

Separar com clareza:
- **Correspondência textual** (descrição normalizada, termos/abreviações) ≠ **correspondência técnica** (atributos normativos) ≠ **correspondência de fornecedor/Part Number**.
- **Grupo 1008 — terminais:** subtipo (PINO, FORQUILHA, ILHÓS/TUBULAR, LINGUETA, FASTON/BANDEIRA, OLHAL/ANZOL, LUVA/EMENDA, outros conforme norma), bitola/faixa do cabo (mm²/AWG), dimensão ou comprimento quando previsto, banho, isolação, variante, embalagem e norma/certificação. Não inferir equivalência quando bitola, geometria ou características críticas divergem.
- **Grupos 1001–1005 — cabos:** material, temperatura, seção (mm²/AWG), cor, tensão, observações e certificações; **1006–1007**: vias, bitola, composição, cores, modelo e plug/comprimento aplicável. Subgrupos adicionais somente pelo documento governado.
- **Dados ausentes:** valor `UNKNOWN/NOT_OBSERVED` e motivo, nunca completar por adivinhação.
- **Fontes:** norma com nome/versão/hash + código/grupo/descrição TOTVS e vínculo fornecedor/PN observados, timestamps; conteúdo externo/datasheet tratado como evidência não confiável até verificação.
- **Resultado:** `POSSIBLE_DUPLICATE`, `POSSIBLE_TECHNICAL_SIMILARITY`, `TECHNICAL_MISMATCH`, `INSUFFICIENT_INFORMATION`, `NO_CANDIDATES_FOUND`. A última classe significa somente “consulta autorizada não retornou candidatos”, **não prova inexistência**.
- **Sem score artificial:** percentuais só com método validado, dataset de referência e limiares aprovados por Engenharia. Preferir matriz `atributo / solicitado / candidato / estado / fonte` e ranking explicável.
- **Consulta restrita:** busca paginada/bounded, AuthZ por ator, campos autorizados somente, sem dump do ERP, índice paralelo ou novo banco vetorial como premissa.
- **Fornecedores/PN:** PN deve ser correlacionado com identidade de fornecedor e loja. Mesmo PN isolado não prova equivalência técnica; PN divergente também não dispensa investigação.

**Decisão de continuidade:** o analista pode prosseguir apesar de candidatos com descrição/técnica próxima, **mediante justificativa e permissão correta**. Isso não dispensa gates de conformidade, conflito real de chave, classificação/atributos obrigatórios ou eventual recusa do próprio ERP. É uma decisão de negócio rastreável, não bypass de validações.

### 5. Contratos e fronteiras a definir antes de codar

**A. Análise de similaridade (READ):** owner da regra, consumers (`Engineering API`, Portal, EVA), entrada autorizada `request_id`/versão/família/contexto, resposta `candidates[]` limitada e explicável com `code, description, group, attributes, supplier_links, part_numbers, evidence, missing_fields, norm_ref/version, comparison_status`; limites de paginação, erros e `not_found/forbidden/unavailable` distintos. Reutilizar `normative_description.v1` **via extração de componente neutro ou porta apropriada se justificado pelo Abstraction Gate**; não importar internals de desenho ou do DAVI.

**B. Decisão humana:** ator, request/case version, candidatos e snapshot analisados, `decision`, `reason` obrigatório para prosseguir com duplicidade possível, resultado auditado imutável e validade contra mudança de contexto; operação não terminal até verificação do ERP.

**C. CREATE SB1:** inventariar `delpiproduto/v1/IncProduto/incluir` e/ou API nativa via `/restall`, fonte `.PRW` e payload `MSExecAuto`, código/geração, representação completa, campos obrigatórios, erros, permissões, idem e reconciliação. Se não existir façade oficial, propor `POST` **somente** na api-delpi com gate default OFF e destination pin. Não afirmar que o contrato de UPDATE vale para CREATE.

**D. UPDATE SB1:** reutilizar `PUT /integrations/protheus/products/{product_code}`; fazer read fresco e representação completa dos campos exigidos (21 `B1_*` + código path no contrato documentado), preservando campos não alterados; tratar `null`, divergência de baseline e concorrência fail-closed; não admitir PATCH parcial que zera campos.

**E. Vínculos SA5:** inventariar ADD/UPDATE/REMOVE e existência de API oficial; cada operação exige identidade fornecedor/loja e Part Number/ catálogo adequados. Se write SA5 não existir, **não** marcar caso com operações SA5 como completamente aplicado. Avaliar falha parcial entre SB1 e SA5, compensação autorizada ou reconciliação manual; não pressupor transação distribuída.

**F. PREPARE/ACT e AuthN/AuthZ:** contrato com expiração, idempotency key por intenção, binding `actor+case+version+official_snapshot+payload_hash+decision`, scopes/permissões live Core, conta Protheus resolvida no backend, S2S restrito `engineering-api`, erros `FORBIDDEN, STALE, CONFLICT, REJECTED, UNKNOWN, UNAVAILABLE`, observabilidade e postconditions. MCP/A2A é meio de interoperabilidade, **nunca autoridade**.

**G. Read-back/reconciliação:** `ACKNOWLEDGED` = REST aceitou; `CONFIRMED` = leitura oficial compatível por operação e atributos; `UNKNOWN` exige investigação antes de retentar. Não concluir nem publicar V1/Vn+1 sem aplicação confirmada e validação já existente do PRC. Eventos de tracker e case devem ser correlacionáveis sem dual-write transacional fictício.

### 6. Pacotes de execução e gates

| Fase | Entrega | Critério de saída | Estado |
|---|---|---|---|
| G0 — Inventário | HEAD/status, owners, contratos/schemas atuais, endpoints REST reais, arquivos ADVPL, normas e testes, matriz SB1/SA5, capability de busca normativa | Matriz `PROVEN/TO_INVENTORY`, riscos e delta por sistema | `PLANNED` |
| G1 — Ratificação | RQ/AC; semântica de duplicidade e decisão; CREATE/UPDATE/SA5; auth; PREPARE/ACT; postconditions e failure modes | Owners Engenharia/API DELPI/Coordination aprovam contratos e baseline | `PLANNED` |
| G2 — Similaridade READ | Pipeline por família, candidatas bounded, confronto técnico/PN, resposta explicável, auditoria da decisão | Evals com duplicatas verdadeiras/falsos positivos, bitola, PN, ausência, autorização | `PLANNED` |
| G3 — CREATE na api-delpi | Capacidade nova somente se não houver equivalente; gate OFF, pin, ExecAuto, ledger | Testes de contrato e POC controlada **TST01**, se autorizada | `PLANNED` |
| G4 — UPDATE/SB1 e SA5 | Reuso de PUT e implementação governada de SA5 apenas com contrato; idempotência e rebase | Testes de payload completo, partial failure, UNKNOWN e concorrência | `PLANNED` |
| G5 — PRC aplicação | PREPARE/ACT Engine API, decisão vinculada, read-back e complete existente | Testes fail-closed, guards, revisão/versão e idempotência | `PLANNED` |
| G6 — Portal/EVA | UI `Analisar duplicidade` → `Aplicar no TOTVS` → `Confirmar`; ações semânticas elegíveis nas **seis tools existentes** | A11y, estados, mensagens, paridade usuário e permission boundaries | `PLANNED` |
| G7 — HML/TST01 | E2E autorizado sem tocar produção, snapshots e restauração, comparação de dados e negative cases | RQ/AC, evidências SHA e técnico owner; bloqueios resolvidos | `PLANNED` |
| G8 — Release | Planejamento de produção, feature gates inicialmente OFF, rollout/rollback/revoke, monitoramento | Aprovação específica de deploy e de **habilitação de write**; smoke seguro | `PLANNED / NOT_AUTHORIZED` |

**Sequência não é licença para implementar todas as fases de uma só vez.** G0 é `READ_ONLY / NO_DEPLOY`; mudança de owner, authority, contrato externo breaking ou novo bounded context: `ARCHITECTURE_DECISION_REQUIRED` e retorno à Coordination. Não executar G3+ ou habilitar gate sem autorização de fase.

### 7. Critérios de aceite iniciais (evolutivos)

| AC | Evidência exigida |
|---|---|
| AC-01 | Busca aproximada retorna candidatos tecnicamente próximos, não apenas descrição exata |
| AC-02 | Terminais 1008: subtipo/bitola/dimensões/banho/isolação comparados segundo norma aplicável |
| AC-03 | Cabos: material/bitola/vias/tensão/temperatura/cor quando aplicáveis |
| AC-04 | Dados oficiais e SA5/PN exibidos somente quando autorizados, com proveniência e ausências |
| AC-05 | PN de fornecedor igual não é confundido com equivalência técnica automática |
| AC-06 | Analista decide usar existente, devolver ou prosseguir com motivo auditável; sem bloqueio arbitrário por similaridade |
| AC-07 | Revalidação de candidatos/contexto e AuthZ antes do ACT; proposta expirada/conflitada falha fechada |
| AC-08 | CREATE não usa contrato PUT por suposição; upstream, ExecAuto e código oficial comprovados |
| AC-09 | UPDATE preserva representação completa e valores não modificados, impedindo lost update |
| AC-10 | Operações SA5 só declaradas aplicadas com contrato e confirmação oficial; falha parcial não conclui |
| AC-11 | ACK e CONFIRMED distintos; timeout/5xx UNKNOWN sem retry cego |
| AC-12 | Caso PRC somente fecha/publica revisão após read-back e verificação oficial íntegra |
| AC-13 | Permissões live Core, pin TST01/PRD, feature gates OFF default, ledger e idempotência testados |
| AC-14 | UI e EVA usam mesmos casos de uso governados; sem novas tools ou acesso direto ao ERP |
| AC-15 | Cenários positivos e negativos executados no SHA e ambiente autorizados; nenhuma escrita PRD de teste |
| AC-16 | O documento evolutivo é atualizado incrementalmente com decisões, ADRs, hashes, resultados e pendências, sem master plans duplicados |

### 8. Matriz de cenários de teste a construir

1. Terminais com mesma bitola e texto abreviado diferente → candidato e atributos explicáveis.
2. Terminal bitola diferente → `TECHNICAL_MISMATCH` no atributo, não declarar duplicidade conclusiva.
3. Mesmo PN + mesmo fornecedor/loja, descrição diferente → recuperar candidato e exigir análise, não equiparar automaticamente.
4. PN idêntico com fornecedores distintos → deixar contexto explícito.
5. Cabo mesma seção mas tensão/material diferente → destacar divergência técnica.
6. Grupo/subtipo fora da norma aplicável → `INSUFFICIENT_INFORMATION` ou `NOT_APPLICABLE`, sem inventar regra.
7. Busca sem candidatos, página parcial, indisponibilidade ou 403 → sem candidato ≠ inexistência; falha de leitura não vira autorização implícita.
8. Analista escolhe prosseguir com justificativa e permissão correta → decisão persistida; sem motivo/sem permissão → bloqueio.
9. Mudança de cadastro/candidato entre análise e PREPARE/ACT → stale/novo review.
10. UPDATE com um campo alterado, demais campos de representação completa preservados.
11. CREATE que recebe ACK mas read-back não confirma → caso aberto, sem revisão publicada.
12. Timeout após envio e possível gravação → UNKNOWN, reconciliação, sem retry automático.
13. SA5 ADD/UPDATE/REMOVE com falha parcial → nenhum falso `complete`; decisão de recuperação governada.
14. Usuário sem permissão e caso de outra identidade → backend nega sem revelar ficha restrita.
15. HML TST01 com snapshot, operação e restore autorizados; PROD read-only, inalterada.

### 9. Registro de decisões e próximos complementos — manter neste capítulo

| Data | Decisão PO / Coordenação | Estado | Próximo complemento |
|---|---|---|---|
| 18/11/2026 | Incorporar criação/edição **assistidas via API** ao fluxo de Engenharia, com decisão humana e confirmação oficial | `PO_DIRECTION_RECORDED` | G0 contratos CREATE/UPDATE/SA5 e segurança |
| 18/11/2026 | Não impedir automaticamente a análise quando há descrição parecida; mostrar cadastro e fornecedores/PN; continuidade justificada por analista | `PO_DIRECTION_RECORDED` | Contrato de decisão e audit trail |
| 18/11/2026 | Similaridade deve ser **aproximada e técnica**, aplicar normas DELPI por família (bitola, cabo, terminais etc.) e reusar inteligência da EVA | `PO_DIRECTION_RECORDED` | G0/G1 norm engine, candidate retrieval e avaliação |
| 18/11/2026 | Concentrar próximos refinamentos no **plano evolutivo já existente**, sem multiplicar master plans | `PO_DIRECTION_RECORDED` | Append-only nesta seção |

**Pendências de decisão ainda abertas (não converter em fato):** owner e lifecycle exato do contrato de análise; campos críticos por família e equivalência admissível; estratégia de código oficial no CREATE; permissões específicas para escritura; API de write SA5; comportamento de `UTILIZAR_EXISTENTE`; transações parciais; expiração da decisão; limites/ranking dos candidatos; disponibilização sem novos scopes. Resolver via inventário e ratificação técnica, sem preencher lacunas por inferência.

**Regra editorial para as próximas rodadas:** acrescentar neste capítulo novas subseções `G0 evidence`, `G1 decisions`, `execution reports`, `residual ledger` com `TASK_ID, SHA, owner, contract_version, environment, PASS/FAIL/PENDING/TEST_NOT_RUN, reversibility`. Atualizar este plano em vez de escrever master plan paralelo; documentação de contrato técnico ratificado pode existir na área do próprio owner e ser referenciada daqui.


### 10. Nova prioridade PO — inventário integral do cadastro e expansão do schema PRC (18/11/2026)

**TASK_ID:** `EVA-PRC-PRODUCT-MASTER-FIELD-INVENTORY-FIRST-01`  
**Status:** `PO_DIRECTION_RECORDED / G0_READ_ONLY_PLANNED / CONTRACT_AND_SCHEMA_RATIFICATION_PENDING / NO_CODE_CHANGE / NO_TOTVS_WRITE`.  
**Decisão superveniente do PO:** **antes** de criar rotas CRUD, ampliar frontend ou automatizar write, inventariar e reconciliar a **totalidade dos campos relevantes do produto no TOTVS** com os payloads reais das operações CREATE e UPDATE e com os campos atualmente rastreados pelo PRC. O catálogo reduzido foi suficiente para o fluxo anterior, mas **não deve ser tratado como contrato completo de criação ou de versionamento de cadastro**.

#### 10.1 Achados de código inspecionado (não extrapolar)

| Camada | Fonte verificada | Evidência / limitação |
|---|---|---|
| PRC domínio | `engineering-api/engineering_app/domain/product_registration/catalog.py` | `PAYLOAD_SCHEMA_VERSION=1`; catálogo `_PRODUCT_FIELDS` contém **10 especificações top-level**: `officialProductCode, description, group, productKind, defaultWarehouse, unit, thirdPartyProduct, accountingAccount, customerReference, suppliers`. `suppliers` representa coleção, não coluna SB1. Campos atuais de CREATE intake e UPDATE são restritos à allowlist `FieldSpec`. |
| api-delpi update | `api-delpi/app/application/services/integrations/protheus_product_payload.py` | `PRODUCT_FIELD_SPECS` exige **21 campos B1 no corpo de UPDATE** + `B1_COD` do path; `FULL_REPRESENTATION_REQUIRED` impede payload parcial. Este contrato não prova requisitos de CREATE, nem todas as colunas SB1. |
| ADVPL criado/alterado | `docs/13-fontes-totvs-protheus/04. Estoque/DLP04I01.PRW` | `WSMETHOD POST incProd` usa `Mata010(..., 3)` e `WSMETHOD PUT incProd` usa `Mata010(..., 4)`. Ambos montam arrays com **22 nomes `B1_*`** (incluindo `B1_COD`); handler observado consome valores incondicionalmente, inclusive conversão `VAL()` em `B1_PICMRET` e `B1_CONV`. **Não comprova** deployment da mesma versão do .PRW no ambiente live, obrigatoriedade por operação ou efeitos de defaults/gatilhos. |
| Leitura Engenharia | `api-delpi/app/application/services/product/protheus_field_normalizer.py` | `PRODUCT_DETAIL_ENGINEERING_FIELDS` é projeção mais ampla, mas não inclui automaticamente todos os B1 de escrita; read path/projection, aliases, permissão e tipagem precisam de inventário campo a campo. |
| Fornecedores | SA5 + contexto PRC `supplierCode/store/partNumber/catalogNumber` | Entidade/vínculo separado; não contar SA5 como campos da SB1 nem presumir que POST/PUT de produto escreva fornecedor. |

**Conjunto inicial de campos no handler ADVPL (ponto de partida, não catálogo final):**

`B1_COD, B1_GRUPO, B1_DESC, B1_REFEREN, B1_REFCANT, B1_CODDES, B1_TIPO, B1_YHOHS, B1_POSIPI, B1_LOCPAD, B1_UM, B1_SEGUM, B1_TE, B1_TS, B1_PICMRET, B1_CONV, B1_TIPCONV, B1_TPMAT, B1_ESPECIE, B1_EX_NCM, B1_EX_NBM, B1_ORIGEM`.

Outras informações presentes no PRC, por exemplo `accountingAccount` (B1_CONTA), **não aparecem nesse array**; não concluir que são dispensáveis ou gravadas. Mapear origem, exigência para cada família, rotina oficial, viabilidade de exposição por adapter e cobertura de read-back. Divergências entre limites atuais (`FieldSpec`, DTO, tabela/dicionário e API) devem ser registradas, **não normalizadas silenciosamente**.

#### 10.2 G0 — entregável obrigatório: matriz de campos rastreável, sem nova documentação mestre

Completar **neste mesmo documento** uma matriz por campo, gerada a partir de fontes técnicas autoritativas (dicionário SX3/SB1, fonte ADVPL real e publicada, catálogo API, projeção READ e PRC `FieldSpec`), incluindo para **cada** atributo:

1. Família e entidade oficial: SB1, SA5 ou outra tabela *somente se validada pelo owner*; nome nativo `B1_*`/`A5_*`, tipo, comprimento, precisão, domínio/enum, validação, padrão/default e obrigatoriedade real de CREATE, UPDATE e leitura.
2. Campo contratual e origem: path REST CREATE, path REST UPDATE, campo no handler `.PRW`, path de resposta READ, path normalizado `FieldSpec`, label e grupo UI; marcar `MISSING`, `UNSUPPORTED`, `READ_ONLY`, `WRITE_SUPPORTED`, `TO_CONFIRM`, nunca inventar mapeamento.
3. Proprietário do preenchimento: **solicitante**, **analista de Engenharia**, **valor controlado pelo sistema/regra ratificada**, **derivado de leitura oficial**, **gerado exclusivamente pelo ERP** ou **somente leitura**. Não preencher campos desconhecidos com vazio/zero para satisfazer contrato.
4. Escopo de negócio: grupo/família de produto, filial/empresa/contexto oficial quando aplicável; campo obrigatório condicional e interdependências (`B1_UM/B1_SEGUM/B1_CONV/B1_TIPCONV`, `B1_TE/B1_TS`, classificação fiscal etc.) **a confirmar nas regras vigentes**, sem presumir valores.
5. Ciclo de vida: permitido editar pelo solicitante? pelo analista? na criação? no UPDATE? valor derivado/protegido? precisa justificativa? exige confirmação adicional? política de máscara e visibilidade conforme AuthZ.
6. Rastreabilidade: `field_path` estável, `source`, `source_field`, `source_revision`, `before`, `requested`, `prepared`, `confirmed_after`, `operation_id`, `actor`, `timestamp`, `status`; campos sensíveis exigem minimização e regras de acesso.
7. Testes e evidência: fonte, commit/hash, endpoint/versão, cenário CREATE/UPDATE/READ, erro e postcondition; `PROVEN | TO_INVENTORY | PLANNED`, `PASS | FAIL | TEST_NOT_RUN | INCONCLUSIVE` separados.

**Artefatos esperados do G0 dentro deste plano:** (a) matriz SB1 integral e SA5 separado; (b) diff `SB1/SX3 × ADVPL POST × ADVPL PUT × api-delpi READ/WRITE × PRC v1 × UI`; (c) gaps e preenchimento por owner; (d) decisões pendentes; (e) versão proposta do novo schema; (f) RQ/AC para execução por fases. A matriz pode ser incorporada aqui como tabelas, ou como **artefato técnico gerado e versionado no owner** apenas quando houver necessidade real de máquina; não abrir outro documento de planejamento concorrente.

#### 10.3 Evolução do rastreamento de produto (não confundir intake, draft, ERP e revisão)

**Direção funcional:** ampliar o catálogo tipado e versionado do PRC para abranger todos os atributos que a Engenharia está autorizada a acompanhar, inclusive aqueles não exibidos inicialmente na ficha simplificada. **Não** transformar automaticamente toda a SB1 em campos editáveis pelo usuário nem replicar indiscriminadamente dados fiscais/comerciais/sensíveis.

- Separar claramente `CREATE_INTAKE` (mínimo legítimo para abrir solicitação), `ENGINEERING_PREPARATION` (complemento governado do analista antes do ACT), `UPDATE_REQUESTED_DIFF` (apenas intenção seletiva), `ERP_FULL_WRITE_REPRESENTATION` (snapshot completo quando contrato upstream exigir), `OFFICIAL_READBACK` (prova de persistência) e `TRACKED_PRODUCT_REVISION` (snapshot técnico autorizado e historicamente comparável).
- Versionar `payload_schema_version`, mapeamentos, DTOs, validações, getters/projeções, snapshots, diffs e eventos. Alterações de schema exigem migration/backfill/compatibilidade a inventariar; casos/revisões antigos devem continuar legíveis, sem reinterpretação indevida.
- No UPDATE, aplicar diff seletivo ao **snapshot oficial fresco**, compor representação completa do PUT no backend, proteger campos não alterados e recusar contexto obsoleto; `full PUT` **não significa** que o solicitante pediu alteração de todos os campos.
- No CREATE, preencher o conjunto completo **conforme regras ratificadas por tipo/família** e pelas fontes verdadeiras; distinguir dado obrigatório do ERP, opcional, calculado, fornecido pela Engenharia e default oficial. Nunca produzir valor de campo técnico/fiscal por inferência de LLM.
- Para rastrear modificações, registrar intenção, valores observados antes/depois e origem por campo, inclusive diferenças normalizadas, sem registrar como `ALTERADO` aquilo que apenas foi enviado intacto no payload completo. A revisão de produto segue causalidade e regras V1/Vn+1/no-op do contrato vigente.
- Garantir read-back dos campos realmente aplicados e suas operações SA5; se o campo for inacessível/unverifiable ao consumidor autorizado, tratar como `CONTRACT_GAP` e não fabricar confirmação.
- Definir UI progressiva: campos principais em primeiro plano, **seções técnicas adicionais por categoria**, campos avançados, metadados e comparação de alterações; front deriva do contrato aprovado e não de arrays paralelos divergentes.
- A EVA pode interpretar as normas de descrição e **sugerir** preenchimento de campos quando houver fonte verificável e permissão, mas suas sugestões permanecem `DRAFT/CANDIDATE`; o profissional autorizado valida antes da aplicação. Modelo e API OpenAI (se utilizados) ficam atrás de adapter governado, não tornam-se owner do cadastro nem acesso autônomo ao ERP.

#### 10.4 Ordem de execução corrigida — esta seção prevalece sobre G0–G8 anteriores

| Ordem | Gate | Entrega e dependência | Estado |
|---|---|---|---|
| **1** | **G0-A — Inventário de campos** | Conferir SB1/SX3, SA5, ADVPL POST/PUT, api-delpi READ/WRITE, `catalog.py`, DTOs, validações, tabelas/snapshots e frontend; matriz integral e gaps **antes de qualquer nova rota** | `NEXT / READ_ONLY / NO_DEPLOY` |
| **2** | G0-B / G1 — Contratos e schema PRC | Aprovar quais campos solicitar, quem complementa, como versionar/rastrear, catálogos/lookups, obrigatórios por operação/família, migração/compatibilidade, segurança e AC | `PLANNED / OWNER_RATIFICATION_REQUIRED` |
| **3** | G2 — API DELPI CRUD delimitado | Inventariar equivalente, criar fachada **CREATE** se faltante, reutilizar/aperfeiçoar **UPDATE** e investigar **SA5**; somente rotas necessárias, sem DELETE de produto no escopo; gates OFF, pin, tracker, sem retry | `PLANNED / NO_WRITE_AUTHORIZATION` |
| **4** | G3 — Engineering API / fluxo PRC | Integrar contratos oficiais, schema expandido, PREPARE/ACT, idempotência, read-after-write, reconciliação, tratamento parcial, conclusão e revisões | `PLANNED` |
| **5** | G4 — Similaridade normativa e EVA/OpenAI | Reutilizar engine governado, candidatos de produto/fornecedores/PN e comparação por normas, sem inventar dados; integrar à Engineering API por interface/adapters, com mesma AuthZ do usuário | `PLANNED` |
| **6** | G5 — Frontend integrado | Evoluir CREATE e UPDATE com campos necessários e seções progressivas; análise de possíveis duplicidades; decisão/justificativa; prévia e confirmação `Aplicar no TOTVS`; estados/erros | `PLANNED` |
| **7** | G6 — E2E HML/TST01 | Cobertura positiva/negativa com identidade autorizada, cenários por campo, schema antigo/novo, fornecedor, partial failure, snapshot/restore e read-back | `PLANNED / SEPARATE_TST01_AUTHORIZATION` |
| **8** | G7 — Release PRD | Rollout separado de schema, API, MFE e habilitação write; gates de segurança/rollback/revoke, testes e aceite por owners | `NOT_AUTHORIZED` |

**Execução incremental:** o **próximo trabalho autorizado conceitualmente é apenas G0-A, READ_ONLY / NO_DEPLOY**. A criação de endpoints e a alteração de schema são consequências de um inventário fechado, não premissas. A expressão “API da Open” usada no direcionamento fica registrada como **integração com capacidade de IA a confirmar no G0/G1**; eventual uso de API OpenAI deve passar pelo adapter/provider aprovado e **não** criar comunicação direta modelo→TOTVS nem uma nova autoridade de escrita.

#### 10.5 RQ/AC adicionais do primeiro gate

| ID | Critério verificável |
|---|---|
| AC-F01 | Inventário completo dos atributos elegíveis SB1/SX3 e relações SA5, com provenance, tipos, limites, defaults e obrigatoriedade conforme owner |
| AC-F02 | Todos os nomes consumidos pelos handlers POST/PUT ADVPL reconciliados com ambos os contratos REST; `VAL()`/nulos/strings/overwrites e campos não expostos documentados |
| AC-F03 | Matriz `oficial × read × write × PRC v1 × UI` com gaps explícitos, incluindo `B1_CONTA` fora do array observado de write |
| AC-F04 | Responsável pelo preenchimento de cada campo e obrigatoriedade CREATE/UPDATE por contexto ratificados; nenhum valor inventado |
| AC-F05 | Schema tipado/versionado proposto, separando intake mínimo, preparação completa, diff, payload ERP e revisão rastreada |
| AC-F06 | Compatibilidade dos casos, revisões, eventos e fornecedores antigos demonstrada por estratégia e testes planejados |
| AC-F07 | Read-back verificável ou `CONTRACT_GAP` em cada campo sujeito a publicação; eventos de alteração não confundem payload completo com diff |
| AC-F08 | Somente após aceite G0/G1 autorizar implementação de rotas CRUD e consumidores, com grants/permissões e gates separados |

**Registro de decisão PO (18/11/2026):** inventário de campos **primeiro**; em seguida contratos/schema, rotas CRUD de produto via API DELPI, integração Engineering API + inteligência EVA/provider, frontend e validação/release. Manter a evolução neste documento único, sem novos planos concorrentes.

#### 10.6 G0-A executado — inventário integral SB1/SX3/SA5 entregue (18/11/2026)

**TASK_ID:** `EVA-PRC-TOTVS-SB1-SX3-SA5-COMPLETE-FIELD-CONTRACT-INVENTORY-01`  
**Estado:** `PROVEN_RUNTIME (metadados SQL+SX3) / DOCUMENTED / NO_CODE / NO_TOTVS_WRITE / NO_DEPLOY`  
**Artefato canônico:** [playbook-cadastro-produto-sb1-sx3-sa5.md](../../../api-delpi/docs/api/padroes-totvs/playbooks/playbook-cadastro-produto-sb1-sx3-sa5.md) em `api-delpi/docs/api/padroes-totvs/playbooks/` — matriz completa por campo; **não copiar a matriz para este plano**.

**Resumo do inventário (contagens comprovadas na base `DELPI` via `delpi-api-delpi`):**

| Camada | Inventário |
|---|---|
| SB1 físico × SX3 | 318 colunas físicas (313 negócio + 5 controle) × 319 campos SX3; 29 customizações Delpi (`X3_PROPRI=U`) |
| SA5 físico × SX3 | 123 físicas × 125 SX3 |
| Handler ADVPL `delpiproduto` | 22 campos `B1_*` — array **idêntico** em CREATE (op3) e UPDATE (op4) |
| Façade api-delpi | UPDATE: 21 campos + `B1_COD` (representação completa); CREATE: **inexistente**; SA5 write: **NOT_IMPLEMENTED** |
| READ | `products.detail` ~76 campos (43 em `view=engineering`); `products.suppliers` 15 propriedades |
| PRC v1 | 10 paths (~9 SB1 + vínculo SA5) — cobertura ~3% do físico SB1 |

**Gaps principais:** (1) PRC rastreia 8 dos 21 campos graváveis — UPDATE não verifica 13 campos que o PUT reescreve; (2) `B1_CONTA` rastreado porém **fora** do array de write — sem caminho de materialização hoje; (3) CREATE sem façade e sem contrato de obrigatórios; (4) SA5 sem qualquer write; (5) `ACKNOWLEDGED` sem read-back `CONFIRMED`; (6) campos fiscais/comerciais/custo fora da view=engineering — `NO_PRC` até decisão de owner.

**Decisões pendentes:** semântica do flag `X3_OBRIGAT` nesta base; obrigatórios CREATE por tipo/família via ensaio TST01; rotina oficial SA5 + triplas `A5_*`; divergência `IncProduto/excluir` (playbook×PRW); regra de geração de `B1_COD`; owners por família de campo.

**Estado RQ/AC:** AC-F01 `PASS` (matriz integral), AC-F02 `PASS` (22 campos reconciliados POST/PUT + efeito `VAL()`/representação completa documentado), AC-F03 `PASS` (matriz oficial×read×write×PRC×UI no playbook), AC-F04 `PARTIAL/TO_INVENTORY` (owners propostos por classe no playbook §10; ratificação por campo pendente — flag SX3 inconclusiva), AC-F05 `PASS` (schema v2 proposto em anéis, não implementado), AC-F06 `PLANNED` (estratégia v1→v2 sem backfill destrutivo), AC-F07 `PASS parcial` (read-back disponível via products.detail; `CONTRACT_GAP` em SA5 write e B1_CONTA materialização), AC-F08 `PENDING` (aguarda aceite PO desta matriz).

**Próximo passo recomendado:** aceite PO da matriz → ensaio TST01 governado (CREATE mínimo + SA5 write + read-back) → ratificação do schema v2 → só então rotas/frontend.

#### 10.7 G0-B executado — inventário RESTALL autenticado e contratos (19/11/2026)

**TASK_ID:** `EVA-PRC-TOTVS-RESTALL-ROUTE-DISCOVERY-AND-CONTRACT-RATIFICATION-01`  
**Estado:** `PROVEN_LIVE_CATALOG / DOCUMENTED / NO_CODE / NO_ERP_WRITE / NO_DEPLOY`  
**Artefato:** playbook canônico §12 — mesma fonte do G0-A.

**Descoberta (catálogo vivo, login de serviço governado):**

| Ambiente | Catálogo | Classes | Relevantes a produto |
|---|---|---|---|
| PRD `192.168.1.231:8061` | `POST /restall` | 527 | todas abaixo |
| TST01 `192.168.1.233:8701` | `POST /rest` | 526 | idênticas (delta: só `ESTABLISHMENT` em PRD) |

**Confirmadas:** `DELPIPRODUTO` custom (POST incluir + PUT alterar — **sem excluir**, corrigindo referência anterior), `MRPPRODUCT`/`MRPPRODUCTINDICATOR` nativas (GET+POST upsert+DELETE, subconjunto MRP), `TSIITEM` nativa (CRUD EAI item — schema `TO_INVENTORY`), `GETITEMSINFORMATION` (READ EAI), `CUSTOMERVENDOR` (CRUD SA1/SA2), `ACCOUNTINGITEMS` (candidata à dimensão contábil — `B1_CONTA` `TO_INVENTORY`).

**Não encontradas:** nenhuma classe SA5/vínculo produto×fornecedor em nenhum ambiente → SA5 ADD/UPDATE/REMOVE = `PROVEN_NOT_PUBLISHED`, exige capacidade nova (rotina oficial .PRW + publicação + façade + gates).

**Recomendações de reuso (sem implementação):** CREATE SB1 → **reuse** `DELPIPRODUTO` POST existente + **nova façade** api-delpi (rota DELPI, não TOTVS); UPDATE → reuse existente; SA5 → **create** (decisão arquitetural pendente); read-back → reuse ODBC api-delpi; `B1_CONTA` → ensaiar `ACCOUNTINGITEMS` antes de propor handler novo; `MRPPRODUCT`/`TSIITEM` → candidatos complementares a campos fora do array de 22, schemas `TO_INVENTORY`.

**Pendentes de contrato:** obrigatórios reais MATA010 op3; schema `TSIITEM`/`ACCOUNTINGITEMS`; rotina oficial SA5; semântica `MRPPRODUCT` (upsert sem PUT).

**Impacto PRC v2/Engineering API:** CREATE não exige handler TOTVS novo — exige façade + contrato de obrigatórios; SA5 é o único gap que impõe rotina Protheus nova.

**Critérios de aceite do próximo gate:** ensaios TST01 conforme protocolo §12.5 do playbook (CREATE mínimo, campo-a-campo, representação completa, B1_CONTA, SA5 pós-decisão, negativos) — `TEST_NOT_RUN` até autorização TST01 explícita com identidade/massa/rollback.

**Próximo gate autorizado:** decisão arquitetural SA5 + autorização de ensaios TST01 → depois façade CREATE api-delpi.

#### 10.8 P0–P2 — recuperação de merge, SA5 e verificação (19/11/2026)

**TASK_ID:** `EVA-PRC-P0-P2-MERGE-RECOVERY-SA5-CONTRACT-AND-VERIFICATION-01`

**P0 — merge Controladoria:** `ALREADY_RESOLVED` — a sessão owner resolveu e evoluiu o WIP; `closing_checklist_repository.py` sem marcadores (o hit anterior era comentário `====`), sintaxe válida; stash autostash preservado. Testes do owner: `TEST_NOT_RUN` neste host (libodbc ausente; suite pg requer DB live). Nenhum código de Controladoria incorporado ao plano PRC.

**P1 — SA5:** rotina oficial **identificada**: `MATA061` (Produto X Fornecedores, MVC Model-2, `Dmata061.prx` DELPI). Chave oficial: `FILIAL+FORNECE+LOJA+PRODUTO+FABR+FALOJA+REFGRD`. **Não é ExecAuto-compatível** — caminhos: (a) EAI `MATI060` via `TOTVSEAI` (`TO_INVENTORY` — adapter ativo?), (b) `.PRW` instanciando modelo oficial. RecLock/SQL direto proibido; precedente legado `AtuSA5XSA2` (IXMLSEF) documentado como anti-padrão não-reutilizável. Decisão de caminho: `ARCHITECTURE_DECISION_REQUIRED` (Integrações TOTVS + ERP).

**P2 — verifier + CREATE:** `devin` CLI instalado, **não autenticado** — bloqueio ambiental requer login interativo do operador (sem credencial improvisada); verificação permanece `INCONCLUSIVE`, pedidos preservados. CREATE: handler encaminha 22 campos incondicionalmente a `MATA010` op3; `B1_COD` manual (sem SXE no handler; geração execauto = `TO_INVENTORY`); mínimos por tipo = `TO_INVENTORY`. Probes TST01 read-only: `MRPPRODUCT` viva (upsert, subconjunto MRP), `ACCOUNTINGITEMS` viva-ish sem evidência de `B1_CONTA`, `TSIITEM` publicada mas path não alcançado. Protocolo de ensaios E1–E9 no playbook §13.4 — `TEST_NOT_RUN`.

**Próximo gate:** decisão SA5 (EAI vs .PRW-modelo) + autorização TST01 com identidade/massa/rollback + login do verificador.

#### 10.9 G0-C — verificação live MATI060/TOTVSEAI (19/11/2026)

**TASK_ID:** `EVA-PRC-G0C-RESTALL-MATI060-SA5-LIVE-CONTRACT-VALIDATION-01` — artefato: playbook §14.

**Prova live (ambos ambientes, GETs read-only):** EAI **não configurado para negócio** — `configurator/v1/integrations` vazio, transações do app host = só `whois`, zero mensagens em TST01 e PRD. `TOTVSEAI` = admin/monitor; catálogo não expõe ingestão de mensagens (recepção EAI é `EAIRecebe`/scheduler, fora do REST publicado). MATI060 = `PROVEN_SOURCE` apenas.

**Decisão candidata SA5:** `EXTEND` — `.PRW` (`delpisa5`/novo método) instanciando o **modelo oficial MATA061** (preserva validações/PEs) + façade api-delpi no padrão gate+pin+ledger+identity. MATI060 descartado como menor caminho (exigiria infra EAI completa). Ratificação pendente: Integrações TOTVS + ERP + Coordination.

**Lacuna nova:** identidade SA5 oficial = `FILIAL+FORNECE+LOJA+PRODUTO+FABR+FALOJA+REFGRD`; read-back ODBC não projeta os 3 últimos → estender `products.suppliers` ou documentar premissa `REFGRD=∅` quando o contrato for ratificado.

**Não comprovados:** ativação exata do modelo Model-2 (`VALIDAR TST01`); URI `TSIITEM`; relação `ACCOUNTINGITEMS↔B1_CONTA`; semântica de `EAIADAPTERTESTREST` (não executada — efeito colateral não comprovado).

**Próximo gate:** ratificação da decisão candidata + autorização TST01 (ensaios §13.4/§14.7) → só então `.PRW` + façade.
