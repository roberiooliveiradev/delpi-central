# Product Registration — contrato técnico do MVP Engineering-only

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
| 15 | GET | \`/technical-records/{recordId}/revisions/{revisionNumber}\` | resource read | Snapshot histórico imutável + diff por campo |
| 16 | GET | \`/reference-data\` | read/create/process | Enum de tipos, campos, allowedPaths, schema version e requisitos por operação; valores oficiais apenas se disponíveis |
| 17 | GET | \`/outbound/requests/{requestId}\` | authorized consumer + resource scope | Contrato externo de status, tipo, resultado, verifiedAt, official code, revision link e provenance |
| 18 | GET | \`/outbound/requests\` | authorized consumer + source scope | Consulta paginada/filtrada dos pedidos da origem identificada; polling controlado sem ler fila global |

**Opcional somente se necessário no fluxo real:** \`GET /technical-records?officialCode=...\` para localizar ficha por código em update. Caso o lookup existente da ferramenta Produtos cubra a descoberta e o ID, não criar rota redundante. Sem endpoint de escrita em \`technical-records\` fora da decisão de \`verify-and-complete\`.

Contratos por rota:
- \`POST intake\` → \`201\` \`{requestId,caseStatus:"submitted",createdAt,source,requestType,links}\`; replay idempotente com mesma key/fingerprint retorna mesma operação sem duplicar; mesma key com payload distinto = 409.
- \`GET requests\` → \`{items:[{id,type,status,requester,source,createdAt,assignedTo,officialCode,version}],page,pageSize,total}\`; resumo escopado.
- \`GET detail\` → \`{id,requestType,source,requester,requestedChanges,technicalDraft,baseRevision,caseVersion,status,allowedActions,verificationSummary}\`; \`allowedActions\` vem do backend.
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
| \`base_revision_number\` | INTEGER | NULL para create, required update se technical record já gerenciado |
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

**Contrato aprovado:** [PRODUCT-REGISTRATION-PO-DECISIONS-2026-11-06.md](./PRODUCT-REGISTRATION-PO-DECISIONS-2026-11-06.md#decisão-adicional-aprovada--part-number-opcional-quando-ausente-no-totvs-2026-11-06). `suppliers[].partNumber` (`SA5.A5_CODPRF`) **não é required não-vazio** quando a fonte oficial TOTVS retorna Part Number vazio; qualquer regra histórica contrária deste documento está substituída. Aceitar no intake/draft `partNumber` omitido, `null` ou `""` e normalizar de forma consistente. **Não confundir campo oficial ausente (unverifiable) com valor oficial vazio (verificável).** Quando informado não vazio ou explicitamente selecionado para alteração, comparar o valor final exato com SA5 via `Engineering API -> api-delpi -> TOTVS`; mismatch continua bloqueando publicação. Remoção explícita para vazio é delta auditável, distinta de omissão de alteração. Comparar identidade do vínculo por supplierCode/store, sem ignorar PN informado ou ambiguidade/duplicata; preservar CAS, revisão imutável, provenance e AuthZ. **Status: decisão aprovada, implementação/testes ainda pendentes; não declarar deploy ou HML PASS.**


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

