# 103 — Gate contratual P2-Upload: inventário, contratos TARGET e readiness

**Task:** `CF-C3-P2-UPLOAD-CONTRACT-GATE-001` · **Fase:** Ciclo 3 — gate **documental** P2-Upload · **Baseline:** `a9e43b339d` (rework R4, `ACCEPT_WITH_RESIDUAL`)

> **Tipo de documento:** especificação TARGET proposta + inventário + decisões pendentes. **Nada aqui está implementado nem autorizado para runtime.** Contrato físico vira definitivo somente após revisão do GPT Arquiteto e GO próprio do PO. `IMPLEMENTATION_AUTHORIZED=NO` · `DEPLOY_PRODUCTION_AUTHORIZED=NO`.

---

## 1. Inventário real (A) — o que a plataforma já tem

### 1.1 Padrão canônico de storage — PROVEN (inventariado)

A plataforma **já possui padrão canônico**, codificado em `.cursor/rules/persistent-upload-storage.mdc` + `infra/README-ambiente.md`, repetido por ~13 serviços:

> **Metadados no Postgres do bounded context + binário em filesystem com bind mount `${DELPI_DATA_HOST_DIR}/<subdir>` + download somente via endpoint autenticado (`FileResponse`/`StreamingResponse`).**

| Fato verificado | Evidência |
|---|---|
| Volume canônico por produto | `${DELPI_DATA_HOST_DIR:-/var/lib/delpi}/<subdir>:/app/data/<subdir>` nos dois composes |
| Metadados no schema próprio | `requests-api` `migrations/V004__attachments_artifacts_events.sql` — `original_name, stored_name, storage_key, mime_type, size_bytes, checksum_sha256, uploaded_by_user_id` |
| Storage service por bounded context | `pac_evidence_storage.py`, `receipt_storage.py`, `guide_media_storage.py` — `validate_upload` (MIME allowlist + size) + UUID filename + `resolve` com containment anti-traversal |
| Upload multipart FastAPI | `requests_routes.py:365–479`; `action_plans_read_router.py:1592–1661` (inclui rollback do binário se persistência falhar) |
| Download autenticado | `FileResponse(path, media_type, filename=original_name)` — sempre atrás de `request.state.user` + policy |
| Checksum de binário | `checksum_sha256` em `request_attachments`/`request_artifacts` |
| Hash de versão semântica | `ContentHashService` (cipa/comité) — SHA-256 de payload canônico |
| Validação por magic bytes | `SignatureStorageService` (cipa) — rejeita não-PNG pelo header; único exemplo de conferência de conteúdo real |
| AuthZ por objeto | `requests` `actor_for`/`has_record_branch_access` — imutabilidade por status de workflow |
| Upload chunked >100 MB | `tv-dashboard` `media_chunked_upload_service.py` — sessão + chunks (Cloudflare ~100 MB) |
| Export/import de pacote com binários | `transformometro` `json_backup_routes.py` — `.tmbackup.zip` |

### 1.2 Gaps reais da plataforma — TO_INVENTORY (não bloqueiam o desenho)

- **Sem object storage** (S3/MinIO/Azure/presigned URL) — download é streaming autenticado; doc 91 já preferia stream a signed URL permanente.
- **Sem antivírus** (ClamAV) — mitigação contratual: allowlist MIME+extensão+magic bytes por tipo.
- **Sem retenção central** — política por domínio; para CF é DECISION_REQUIRED.
- **Sem backup de arquivos** por padrão — só TM tem export/import de pacote.
- **controllership-finance-api tem ZERO capability de arquivo hoje** — nenhum `UploadFile`, storage ou volume no compose (verificado).

### 1.3 MFE — componentes reutilizáveis existentes (PROVEN)

`@delpi/plugin-ui` já fornece: `FileDropzone`, `AttachmentFileList`, `AttachmentPreviewStrip` (`forms/`), `DocumentReader`/`DocumentReaderToolbar` (`document/`). Consumidores reais: `my-requests` (AttachmentsPanel/StagedAttachmentsField/RequestFilePreviewModal), `commercial` (TaskAttachmentsBlock), `customer-experience` (PhotoDropzone), `kaizometro` (KaizenEvidenceDropzone). **Nenhum componente novo de UI é necessário** para o primeiro slice.

## 2. Estado real P2-READ (baseline verificado)

| Conceito | Real no HEAD |
|---|---|
| Competência | `monthly_competence(period UNIQUE)` — abertura idempotente |
| Itens esperados | `competence_checklist_item(competence_id, item_key UNIQUE)`, `state='EXPECTED'` (CHECK — único estado válido hoje) |
| Auditoria | `closing_audit_event` append-only, `actor_subject UUID NOT NULL` |
| Rotas | `access`: list/open/get/items/item · `manage`: admin templates · envelope `{success,data,error.code}` |
| Filial | `branch_scope MATRIX\|BRANCH\|BOTH` — **dimensão de dado**, nunca permission (doc-14/T05) |
| Identidade de ator | `actor_subject` = `user.id` UUID validado, fail-closed (hardening R2) |
| Testes PG | banco efêmero com prova de ownership (rework R4) |

## 3. Modelo conceitual (B) — contrato funcional TARGET

### 3.1 Conceitos e owners

| Conceito | Owner | Notas |
|---|---|---|
| `closing_document` (evidência de negócio) | `controllership_finance` | registro vinculado a `(competence_id, snapshot_item_id?)` — evidência de item OU documento de competência (nível competência, ex.: memorial) |
| `document_version` | `controllership_finance` | linha de versão imutável: `(document_id, version_no)`, `file_id`, `supersedes_version_id`, estado documental, `uploaded_by`, `checksum_sha256`, `original_name`, `size_bytes`, `mime_type` — V004: `state` removido (derivado de `current_version_no`), `idempotency_key`/`request_hash` da mutação (§J) |
| `document_file` (metadado do binário) | `controllership_finance` | identidade estável do arquivo físico + `storage_key` + hash; **arquivo físico ≠ registro de evidência** |
| binário | `CfDocumentStorageService` (adapter local, padrão plataforma) | path `<dir>/<competence_id>/<file_uuid><ext>`; sem semântica de negócio |
| estado documental | domínio CF | `ATTACHED \| SUPERSEDED \| CANCELLED` — **upload cria `ATTACHED`, nunca `VALIDATED`** |
| estado do item | snapshot (`EXPECTED` hoje) | upload **não muta** `competence_checklist_item.state` neste slice; derivação de "entregue" é responsabilidade da validação futura (C05) — `ATTACHED != VALIDATED` preservado |
| `attachment_role` (E05) | P6 catalog | pendente — ver §8 |

### 3.2 Invariantes preservados + novos propostos

Preservados verbatim (docs 09/12/96): `ATTACHED != VALIDATED` · `CANCELLED != DELETED` · `CANCELLED != NOT_APPLICABLE` · `EXPECTED != DELIVERED/VALIDATED` · `PACKAGE_SUBMITTED_FOR_REVIEW = IMMUTABLE` · `ACCESS != MANAGE` · `Finalizar != Enviar` · `source absence != zero`.

Novos (TARGET): `FILE_STORED != EVIDENCE_REGISTERED` (falha na gravação do metadado ⇒ rollback do binário) · `SUPERSEDED_VERSION != DELETED` (substituição cria versão nova; anterior permanece referenciável) · `DOWNLOAD != APPROVAL` · `UPLOADED_BY != VALIDATED_BY` (mesmo ator produz dois eventos distintos — doc 93 CP05).

## 4. Contrato técnico TARGET (C) — propostas, não aprovadas

Prefixo `POST/GET /closing/competences/{period}/documents*` — mesmo envelope e mapeamento de erros dos contratos P2-READ vigentes. **`CF-` prefixo de decisão: operationIds são PROPOSTAS.**

### 4.1 Operações propostas

| # | Capability (proposta) | Método/path (proposta) | AuthZ | Idempotência | Erros novos |
|---|---|---|---|---|---|
| U1 | `upload_competence_document` | `POST /closing/competences/{period}/documents` multipart (`file`, `snapshot_item_id?`, `title?`, `attachment_role?`) | `access` + scope + business_rule | idempotência `UNIQUE(<aggregate>, key)`+`request_hash`+409 tipado (padrão supplies-api); transporte/escopo/TTL **D-U7 pendente** — Adendo §B | `file_too_large` 422, `unsupported_media_type` 415, `item_not_found` 404, `competence_not_opened` 404, `competence_closed` 409 (futuro) |
| U2 | `list_competence_documents` | `GET .../documents?item=&state=` | `access` + scope | — | filtros = dimensão de dado |
| U3 | `get_competence_document` | `GET .../documents/{document_id}` | `access` + scope | — | `document_not_found` 404 |
| U4 | `download_document_version` | `GET .../documents/{document_id}/versions/{version}/content` → `FileResponse` | `access` + scope + recipient rule | — | `document_not_found` 404, `forbidden` 403, `file_missing` 503 (`persistence_unavailable`-like) |
| U5 | `replace_document_version` | `POST .../documents/{document_id}/versions` multipart | `access` + scope + uploader-or-admin rule (ver §5, DECISION) | `revision` OCC + `idempotency_key` da mutação (`UNIQUE(document_id, key)`+`request_hash` — D-U7=A estendida por §J/V004) | `stale_revision` 409, `idempotency_conflict` 409, `version_locked` 409 (pacote P5) |
| U6 | `list_document_versions` | `GET .../documents/{document_id}/versions` | `access` + scope | — | — |
| U7 | `cancel_document` | `POST .../documents/{document_id}/cancel` | `access` + scope + owner/admin | — | `document_locked` 409 |
| U8 | `list_document_audit` | `GET .../documents/{document_id}/events` | `access` + scope | — | — |

Para cada operação vale o contrato de plataforma: **AUTHN** JWT+Core RBAC (fail-closed, `rbac_unavailable` 503) · **RESOURCE_SCOPE** competência × filial-contexto do request · **CONCURRENCY** `revision` OCC no `closing_document` · **AUDIT** `closing_audit_event` por mutação (`DOCUMENT_UPLOADED`, `VERSION_ADDED`, `DOCUMENT_CANCELLED`, `DOCUMENT_DOWNLOADED`? — download-audit = DECISION, ver §8) · **TIMEOUT** padrão BFF · **RETRY** seguro apenas com `idempotency_key` (transporte = D-U7) · **PAGINATION** `limit/offset` ≤ 100.

### 4.2 Ciclo de vida proposto

`upload (U1) → document ATTACHED v1 → replace (U5) → v2 ATTACHED + v1 SUPERSEDED → cancel (U7) → CANCELLED (terminal, sai da listagem ativa; histórico íntegro)`. Item snapshot **permanece `EXPECTED`** — completude real é decisão de C05 (validação), não deste slice. `attachment_role` por item fica pendente de E05; sem role ⇒ `generic` explícito, nunca inventado.

### 4.3 Transferência e integridade — recomendação TARGET

- **Transporte:** multipart único `await file.read()` para o v1 (documentos de fechamento ≪ 100 MB); chunked da TV fica como alternativa documentada caso pacotes grandes apareçam — **DECISION** se limites exigirem.
- **MIME:** allowlist fechada `application/pdf`, `image/jpeg|png|webp`, `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `text/csv` — + conferência de magic bytes por tipo (padrão cipa). Extratos OFX/QIF? **DECISION_REQUIRED** (fonte não comprova formatos bancários exatos).
- **Tamanho:** 25 MB por arquivo (padrão PAC/TM/planning) — recomendado; DECISION do GO.
- **Hash:** `checksum_sha256` do binário gravado no metadado (padrão requests) + verificação opcional no download? — recomendado não verificar (streaming confia no FS; hash é registro de integridade/auditoria).
- **Layout disco:** `${DELPI_DATA_HOST_DIR}/cf-closing-documents/{competence_id}/{file_uuid}{ext}` — novo `CF_DOCUMENT_UPLOAD_DIR` + volumes nos dois composes + README-ambiente + env.example (checklist da rule).
- **Rollback:** se persistência do metadado falhar, binário é removido (padrão PAC).
- **Órfãos:** `document_file` sem referência de versão > 7d ⇒ varredura housekeeping (PLANNED, fora do v1).
- **Retenção:** **DECISION_REQUIRED** — sem política inventada; v1 não deleta nada.

## 5. Matriz de segurança (D) — `capability AND resource_scope AND business_rule`

| Cenário | Regra proposta | Decisão |
|---|---|---|
| Upload com `access` | permitido — doc 14 já lista "anexar evidências" em ACCESS | fechado |
| Download com `access` | permitido dentro do scope filial/competência visível; URL sempre atrás de `access` efetivo (nunca link público) | fechado |
| Substituir evidência de outro usuário | uploader OU `manage` — DECISION_REQUIRED (doc 14 não congela owner-editability) | **aberto** |
| Cross-competence | documento pertence à competência do path; `document_id` de outra competência ⇒ 404 (não 403 — sem vazamento de existência) | recomendado |
| Cross-branch | `branch_scope` filtra itens; documento herda escopo do item — documento de competência sem item usa `branch_scope=BOTH` | recomendado |
| Recipient-restricted (`recipient_area`) | CONTABIL/FISCAL é metadado de destino, **não** permission — download adicional restrito por elegibilidade é P5; v1: `access` lê | recomendado |
| Competência "encerrada" | estado futuro; `competence_closed` 409 já reservado | aberto |
| Pacote P5 submetido | evidência referenciada ⇒ `version_locked` 409 na substituição/cancelamento; histórico imutável | fechado (doc 12/37) |
| `manage` sem `access` | **não** autoriza — `MANAGE != ACCESS` | fechado |
| Service principal | 403 (padrão vigente) | fechado |
| Core indisponível | `rbac_unavailable` 503 — fail-closed | fechado |
| Usuário sem permission | 401/403 middleware | fechado |

## 6. Integração futura com P5 — boundary

- Evidência e pacote relacionam-se por **referência de versão** (`document_version_id`), nunca por cópia de bytes.
- Uma `PackageVersion` referencia o conjunto `(document_id, version_no)` no momento do envio — substituição posterior cria v_n+1 **sem** alterar a referência do pacote enviado (`PACKAGE_SUBMITTED_FOR_REVIEW = IMMUTABLE`).
- Upload/validação/disponibilização/envio são estágios distintos — este slice não toca `competence_checklist_item.state` nem monta pacote.
- Destinatários autorizados P5 resolvem por elegibilidade Core + assignment (doc 37 §6) — fora do escopo.

## 7. UX — especificação TARGET (sem mudança de runtime)

- Entrada: por item da checklist (linha → "anexar") + ação de competência ("documentos da competência"); `FileDropzone` + `AttachmentFileList` existentes.
- Estados: `INITIAL/LOADING/REFRESHING/SUCCESS/EMPTY/PARTIAL/ERROR/FORBIDDEN/NOT_FOUND` — reuse do padrão vigente da página; `UPLOADING` progresso por arquivo; erro de transferência com retry manual.
- `ATTACHED` exibido como "anexado — aguardando validação" **nunca** como entregue/validado (RQ-P2-13 já PROVEN, manter).
- Download via client autenticado (blob → save-as) — sem URL pública.
- Help contextual: novo bloco explicando anexo vs validação **somente quando o slice for implementado** (proibido neste gate).
- A11y: dropzone com alternativa de botão (teclado), `aria-describedby` em erros, foco gerenciado — padrão plugin-ui.

## 8. Registro de decisões (F)

### Já congeladas
CP-D01=A (schema próprio) · CP-D04=A (DRAFT seed) · CP-D05=A (admin por API) · `P2-Upload ≠ validação` (doc 102 §8) · `PACKAGE_SUBMITTED_FOR_REVIEW = IMMUTABLE` · `BRANCH = dimensão` (T05) · ACCESS inclui "anexar evidências" (doc 14) · metadado-Postgres + binário-volume (rule canônica) · `EMAIL_ATTACHMENT_DELIVERY = NO` (E04).

### DECISION_REQUIRED

| # | Tópico | Opções | Recomendação | Owner |
|---|---|---|---|---|
| D-U1 | **Owner-editability na substituição** | A: só uploader ou `manage` · B: qualquer `access` | A — trilha auditável e consistente com "uploader ≠ validator" | GPT/PO |
| D-U2 | **Limite/tipos de arquivo** | A: 25 MB, allowlist PDF/img/XLS(X)/CSV · B: + formatos bancários (OFX/QIF/TXT retorno) | A + investigar OFX com TÉO/Controladoria | PO/Controladoria |
| D-U3 | **Audit de download** | A: auditar `DOCUMENT_DOWNLOADED` · B: só mutações | A — doc 91 pede download auditável; volume de eventos pequeno | GPT |
| D-U4 | **Retenção** | A: indefinida v1, housekeeping só de órfãos · B: política de prazo por competência | A + decisão PO de retenção em trilho próprio | PO |
| D-U5 | **attachment_role por item (E05)** | catálogo em P6 seed vs `generic` v1 | `generic` explícito v1; E05 bloqueia validação C05, não upload | Controladoria |
| D-U6 | **Documento de competência vs de item** | A: dois tipos (item / competência) · B: sempre vinculado a item | A — fiscais/memoriais existem no AS-IS | GPT |

### Dependências abertas herdadas
CP-D02 (responsável/validador/regra por item — `TO_INVENTORY`) · CP-D03 (CK-E-27 R-ID) · E06 (motivos de rejeição — núcleo já decidido) · reconciliação TÉO `RQ-P2-039` × ledger (doc 90 §67) · destinatário `recipient_area=NULL` honesto.

## 9. Revisão adversarial obrigatória — respostas

| Risco | Mitigação contratual | Teste futuro |
|---|---|---|
| Download cross-competence | `document_id` pertence ao path; fora do escopo ⇒ 404 | sibling cross-competence |
| Acesso cross-branch | scope filial do request × `branch_scope` herdado | negative filial distinta |
| Upload lido como validação | `ATTACHED` único estado criado; item segue `EXPECTED` | positive + UI assert |
| Substituição altera pacote enviado | `version_locked` 409 pós-submissão; pacote referencia versão | negative locked |
| Arquivo órfão | rollback do binário em falha de persistência; housekeeping PLANNED | fault-injection |
| Metadado aponta para binário inexistente | `file_missing` 503 no download | negative fs |
| Conteúdo inválido aceito | allowlist MIME+ext+magic bytes | negative por tipo |
| URL temporária expõe restrito | sem URL pública — stream autenticado | negative sem token |
| Concorrência perde versão | `version_no` UNIQUE por documento + OCC `revision` | concurrent replace |
| Core down ⇒ acesso indevido | `rbac_unavailable` 503 fail-closed | negative Core |
| Storage falha ⇒ sucesso falso | metadado só após write; erro ⇒ rollback | fault-injection |
| Replay duplica evidência | `idempotency_key` + `request_hash` + `UNIQUE(<aggregate>, key)` (padrão supplies-api); dedup por hash **não** colapsa evidências; transporte/escopo = D-U7 | replay idempotente |
| Auditoria perde ator | `actor_subject` UUID-only já hardened | audit assert |
| Duplicar ownership | storage é adapter do próprio CF; metadado no schema CF | boundary check |
| Contrato viola decisão PO | §8 registra congelados × abertos; nada implementado | review GPT |

## 10. Readiness assessment (G) — para o futuro GO de implementação

| Pré-condição | Estado |
|---|---|
| Inventário storage/owner | **PROVEN** — padrão canônico identificado; owner = CF bounded context |
| Contrato TARGET proposto | **PROVEN** — §4 (pendente aceite GPT) |
| AuthZ model | **PROVEN** conceitualmente; D-U1 aberto |
| Storage/retention | **TARGET** — D-U2/D-U4 abertos |
| UX/estados | **TARGET** — §7 |
| RQ/AC | **TARGET** — doc 23 atualizado com RQ-P2-15..22 |
| Decisões PO | **PENDING** — D-U1..U6 requerem resposta antes do GO |
| Smoke/deploy | não autorizados |

**Bloqueadores para GO:** respostas D-U1/D-U2/D-U3 (mínimas); D-U4..U6 podem ser decididas no próprio GO com default recomendado. E05/E06/CP-D02 **não bloqueiam** upload (bloqueiam validação C05).

## 11. Next gate brief (H)

`CF-C3-P2-UPLOAD-IMPL-GO-001` — GO de implementação do **primeiro slice**: U1 upload + U2 list + U4 download + metadados/hash + storage adapter + audit (sem substituição/cancelamento/UI de validação). Saída: evidência anexada em competência, persistente pós-recreate, íntegra (sha256), autorizada e auditada — item permanece `EXPECTED`. Dependências: aceite GPT deste gate + respostas D-U1..U3 + GO do PO. **Sem autorização automática.**

---

## Adendo — Fechamento de decisões PO e lacunas contratuais (`CF-C3-P2-UPLOAD-DECISIONS-CONTRACT-CLOSURE-001`)

`DECISION_SOURCE=PO_EXPLICIT` · `DECISION_STATUS=PO_APPROVED` · `DOCUMENTATION_STATUS=TO_CONSOLIDATE` · `IMPLEMENTATION_AUTHORIZED=NO` · `DEPLOY_PRODUCTION_AUTHORIZED=NO`. As propostas das seções anteriores permanecem como histórico; esta seção registra o estado consolidado.

### A. Decisões do PO — PO_APPROVED (literal)

| Decisão | Valor | Consequência contratual |
|---|---|---|
| **D-U1=A** | Substituição só pelo uploader original ou `manage` elegível; MANAGE não é bypass — vale `capability AND scope AND business_rule` | U5/U7 exigem `actor == uploaded_by` OR `manage` efetivo; demais ⇒ 403 `forbidden` |
| **D-U2=A** | 25 MB/arquivo; allowlist V1 = PDF, imagens, XLS/XLSX/CSV; OFX/QIF/TXT bancário **não** aprovados; validação por conteúdo real + extensão + MIME (nunca só declaração) | §C3 abaixo; formatos bancários seguem `TO_INVENTORY` com TÉO/Controladoria |
| **D-U3=A** | `DOCUMENT_DOWNLOADED` auditado: ator UUID, recurso, versão, competência, resultado, timestamp, contexto de autorização; separar tentativa/autorização/entrega; sem bytes/tokens | download (U4) emite evento após autorização com `result=AUTHORIZED|DENIED|FAILED`; entrega interrompida não registra sucesso |
| **D-U4=A** | Sem exclusão automática de evidências na V1; sem prazo inventado; retenção corporativa definitiva = pendência própria; órfãos/temp ≠ retenção de evidências válidas | housekeeping cobre **apenas** `.part` >24h e binários sem metadado — nunca evidências registradas; nada é deletado na V1 |
| **D-U5=A** | `attachment_role=generic` explícito na V1; E05 (catálogo/obrigatoriedade) permanece pendente e não bloqueia upload | `attachment_role` default `generic`; roles reais chegam com E05 antes de C05 |
| **D-U6=A** | Dois níveis de vínculo: `competence` OU `competence_item` | `closing_document.link_kind IN ('competence','competence_item')`; item deve pertencer à competência do path — item de outra competência ⇒ 404 |

### B. C1 — Idempotência do upload (U1) — origem por autoridade

**Determinado por padrão vigente** — precedente implementado `supplies-api` (`V002__supplier_enrichment_reviews.sql`, `supplier_enrichment_repository.py`, `supplier_enrichment_routes.py`), inventariado e ratificado como padrão de referência no doc 96:

- `idempotency_key` transportada no **body** do request (campo JSON, 1–128 chars, **obrigatório** no precedente);
- `request_hash` persistido junto ao registro de operação;
- `UNIQUE (<aggregate>, idempotency_key)` — concorrência resolve no banco: um vencedor persiste; o perdedor lê o registro do vencedor se `request_hash` confere, senão conflito;
- mesma key + hash divergente ⇒ `IdempotencyConflictError` tipado ⇒ 409 `idempotency_conflict`;
- registros append-only — **sem TTL** no precedente;
- replay com hash idêntico retorna a entidade já criada, sem duplicar.

**Não determinado por autoridade vigente** — nenhum PO, regra `.cursor` ou precedente cobre: transporte (body field do padrão vs header HTTP `Idempotency-Key` sem precedente na plataforma); obrigatoriedade da key (opcional deixa retry cego criar duplicata); escopo (`<aggregate>` do padrão → análogo `competence_id`, vs incluir `actor_subject`); status do replay (200 `deduplicated:true` vs 201); TTL (nenhuma vs janela). Registrado como **`DECISION_REQUIRED` D-U7** no doc 17 — **recomendação, opção A:** aderir integralmente ao supplies-api (body field obrigatório, `UNIQUE (competence_id, idempotency_key)`, sem TTL, replay idêntico retorna o `document` com `deduplicated: true`). `NO_CHANGE_APPLIED` — decisão do PO pendente antes do GO de implementação. A versão anterior deste adendo apresentava header/TTL-24h/escopo-com-ator como consolidado sem autoridade — corrigido neste rework (`CF-C3-P2-UPLOAD-CONTRACT-CLOSURE-REWORK-001`).

**Fixo independentemente de D-U7:** se a key for ausente/opcional, cada chamada cria um `closing_document` novo — dedup por hash de conteúdo **não** colapsa evidências (o mesmo extrato pode vincular-se a itens diferentes); hash serve integridade/auditoria, não deduplicação. `document_id` UUID na criação; `version_no=1`.

### C. C2 — Consistência Postgres × filesystem — consolidado TARGET

Sequência obrigatória (sem afirmar transação atômica DB×FS):

1. Validar envelope/metadados (AuthZ, scope, tamanho anunciado).
2. Gravar binário em `<upload_dir>/.tmp/{uuid}.part` **em chunks limitados** — exceder 25 MB aborta mid-stream e remove o `.part`.
3. Computar `sha256` durante a gravação; conferir assinatura/estrutura por tipo (§D).
4. `rename()` atômico (mesmo FS) para `<upload_dir>/{competence_id}/{file_uuid}{ext}` — publicação visível.
5. Transação Postgres única: `document_file` + `closing_document` + `document_version(v1)` + `closing_audit_event(DOCUMENT_UPLOADED)` — tudo ou nada.
6. Falha em (5) ⇒ **compensação**: `unlink` do arquivo final → `persistence_unavailable` 503. Nunca metadado sem binário nem sucesso falso.
7. Falha em (2)–(4) ⇒ nada persistido; `.part` removido ou elegível a housekeeping.

**Matriz de falha — controle SLICE-1 vs resíduo honesto:**

| Falha | Controle SLICE-1 | Resíduo (sem garantia) |
|---|---|---|
| Falha normal em (2)–(4) | `.part` removido; nada persistido | — |
| Erro de persistência em (5) | `unlink` do binário + `persistence_unavailable` 503 | — |
| Erro **na compensação** (`unlink` falha) | `persistence_unavailable` 503 + log | **binário órfão sem metadado** — indetectável pela API |
| Crash entre rename (4) e commit (5) | — | binário órfão; **nenhuma limpeza garantida em SLICE-1** |
| Crash após commit (5) | par consistente | — |
| Metadado sem binário (qualquer causa) | download ⇒ `file_missing` 503 | nunca sucesso falso |

**SLICE-1 vs housekeeping futura:** SLICE-1 cobre compensação, `.part` e erro tipado. Housekeeping de órfãos/finais-sem-metadado é **PLANNED** e exige especificação própria (varredura, janela de segurança >24h, dry-run) — D-U4=A não autoriza rotina produtiva de limpeza neste gate. Nenhuma atomicidade distribuída nem limpeza garantida é reivindicada.

### D. C3 — Validação de conteúdo (D-U2=A) — três camadas TARGET

| Camada | Objetivo | Verificações por tipo |
|---|---|---|
| **Assinatura** | tipo real do conteúdo | PDF `%PDF-`; JPEG `FF D8`; PNG `89 50 4E 47`; WebP `RIFF`+`WEBP`@8; XLS CFB `D0 CF 11 E0`; XLSX `PK\x03\x04`; CSV sem magic — exige texto decodificável |
| **Estrutura** | arquivo íntegro e do tipo declarado | PDF: trailer `%%EOF` nos últimos bytes, >1 KB; imagem decodifica com codec declarado; XLS abre no parser CFB; **XLSX: ZIP estrutural válido contendo `xl/workbook.xml` e `[Content_Types].xml`** — ZIP genérico não conta como planilha; CSV decodifica UTF-8/Latin-1 sem NUL, não vazio; truncado/inconsistente ⇒ `invalid_file_content` |
| **Segurança** | abuso operacional | cap 25 MB **mid-stream**; `original_name` sanitizado (basename, sem separadores/NUL), stored name UUID — traversal impossível; **sem antivírus** — capability inexistente na plataforma, lacuna registrada, não proteção |

**Riscos explicitamente documentados:**

- **ZIP malicioso/bomb em XLSX** — a camada estrutural exige ZIP válido com `workbook.xml`, mas limites de entradas/tamanho descompactado e parser streaming são **requisitos de implementação** (especificados no GO, não decisão de produto).
- **Planilha inválida** — ZIP íntegro sem `xl/workbook.xml`, workbook corrompido ou XLS com CFB truncado ⇒ `invalid_file_content`.
- **Conteúdo poliglota** (válido como PDF+script) — mitigado parcialmente (assinatura+estrutura exigem ambos); resíduo aceito **sem AV**.
- **CSV adversarial** — formula injection (`=`,`-`,`+`,`@`) é risco do **consumidor** da planilha, não do storage; documentado, sem sanitização de conteúdo na V1.
- **Extensão divergente do conteúdo** ⇒ `content_type_mismatch`; **vazio** ⇒ `empty_file`; formato fora da allowlist ⇒ `unsupported_media_type` 415; tamanho ⇒ `file_too_large` 422.

Erros tipados: `file_too_large` 422 · `unsupported_media_type` 415 · `invalid_file_content`/`empty_file`/`content_type_mismatch` 422.

### E. C4 — Rastreabilidade RQ/AC (ledger doc 23)

`RQ-P2-15..22` mantidos `TARGET`; `AC-P2-UP-01..24` com escopo **SLICE-1** (U1 upload, U2 list, U3 get, U4 download+audit — invariantes AC-23/24 obrigatórios já neste slice) vs **SLICE-2** (U5 replace, U6 histórico de versões, U7 cancel, U8 events). Detalhe e cobertura por requisito no doc 23 §P2-Upload.

### F. Decisões ainda abertas (não encerradas)

**D-U7** (idempotência: transporte/obrigatoriedade/escopo/TTL/status do replay — `DECISION_REQUIRED` no doc 17, recomendação A aderir ao supplies-api) · retenção corporativa definitiva · inventário OFX/QIF com TÉO/Controladoria · E05 roles/obrigatoriedade · E06 motivos · CP-D02 · CP-D03 · reconciliação TÉO `RQ-P2-039` · antivírus (capability inexistente).

## Adendo — GO de implementação SLICE-1 e D-U7=A (`CF-C3-P2-UPLOAD-IMPL-GO-001`)

`GO_STATUS=PO_AUTHORIZED` · `IMPLEMENTATION_AUTHORIZED=YES` · `SCOPE=SLICE-1_ONLY` · `PRODUCTION_DEPLOY_AUTHORIZED=NO` · `PRODUCTION_MIGRATIONS_AUTHORIZED=NO` · `SLICE-2_AUTHORIZED=NO`. As seções anteriores (inclusive `DECISION_REQUIRED` D-U7 no §B e §F) permanecem como histórico do processo; este adendo registra a decisão que os substitui e o estado de implementação.

### G. D-U7=A — decisão PO (substitui a pendência do §B/§F)

O PO adotou a recomendação A do rework **sem alterações** — padrão `supplies-api` integral:

- `idempotency_key` **obrigatória** no corpo do request — campo `idempotency_key` do multipart, nunca header HTTP;
- `UNIQUE(competence_id, idempotency_key)` + `request_hash` persistido;
- replay idêntico ⇒ o `document` original com `deduplicated: true` (HTTP 200); divergente ⇒ `idempotency_conflict` 409;
- **sem TTL** — registros de idempotência persistentes;
- hash de conteúdo não deduplica — mesma key + payload divergente = 409; mesmo binário em itens diferentes = documentos distintos;
- corrida concorrente resolvida pelo UNIQUE no banco (`ON CONFLICT DO NOTHING` + re-leitura do vencedor).

### H. Estado de implementação SLICE-1 (runtime, commit no `main`)

| Contrato | Implementação | Evidência |
|---|---|---|
| U1 upload | `POST /closing/competences/{period}/documents` multipart (`file`, `idempotency_key`, `snapshot_item_id?`, `title?`, `branch_scope?`) — `access` + humano + scope; item fora do filial-contexto declarado = `item_not_found` 404; estado `ATTACHED`, `version_no=1`; item permanece `EXPECTED` | `test_closing_documents_routes.py`, `test_pg_closing_documents.py` |
| U2 list | `GET .../documents` (`snapshot_item_id`, `link_kind`, `state`, `branch_scope?`, `limit/offset` ≤100) — competência do path × contexto declarado (escopo herdado do item; BOTH = irrestrito, dataset compartilhado doc 49) | idem |
| U3 get | `GET .../documents/{document_id}` (`branch_scope?`) — associação documento↔competência; cross-competence e cross-branch = 404; sem `storage_key` | idem |
| U4 download | `GET .../documents/{document_id}/versions/{version_no}/content` (`branch_scope?`) — `FileResponse` autenticado; `DOCUMENT_DOWNLOADED` registra **decisão de autorização** (`result=AUTHORIZED\|DENIED\|FAILED` + `phase=authorization\|delivery`), nunca entrega concluída — `FileResponse` não prova transmissão; scope-denied audita DENIED; `file_missing` audita FAILED + 503 sem sucesso falso | idem |
| Persistência | `V003__create_closing_documents.sql`: `document_file`, `closing_document` (UNIQUE competence+key, FK composta item↔competência — D-U6), `document_version`; auditoria em `closing_audit_event` na mesma transação | suíte PG em banco efêmero (ownership provado) |
| Storage | `.part` em chunks com cap 25 MB mid-stream → sha256 durante write → magic/estrutura → `os.replace` atômico → tx Postgres → compensação `unlink` — sem atomicidade distribuída declarada | `test_closing_document_storage.py`, `test_closing_document_service.py` |
| Validação | assinatura + estrutura + MIME/extensão convergentes; XLSX = ZIP com `xl/workbook.xml`+`[Content_Types].xml` e limite de expansão; PDF header+trailer; CSV decodificável sem NUL; nome sanitizado, stored UUID, traversal impossível | `test_closing_file_validation.py` |
| MFE | `ClosingDocumentsPanel` na página de checklist (competência e detalhe do item) — FileDropzone + AttachmentFileList do `@delpi/plugin-ui`, retry com mesma key, Help sincronizado | `ClosingDocumentsPanel.test.tsx` |

**Rework CF-C3-P2-UPLOAD-SLICE1-REWORK-001 aplicado:** R-W1 escopo efetivo (`branch_scope` declarado × herdado — `access` sozinho não alcança recurso fora do contexto; não existe membership de filial por usuário — doc 49 §8 dataset compartilhado, permission por filial proibida) · R-W2 `discard_temp()` garantido em toda rejeição pós-`write_temp` · R-W3 auditoria classificada por fase (authorization/delivery; DENIED e FAILED quando auditáveis) · R-W4 erros de download com feedback acessível no MFE (sem catch silencioso).

**Implementado após SLICE-1 (ver §J):** U5–U8 no GO `CF-C3-P2-UPLOAD-SLICE2-IMPL-GO-001`. **Permanece não implementado:** validação humana, P5, antivírus (capability inexistente — residual mantido), housekeeping de órfãos (PLANNED).

## Adendo — GO de implementação SLICE-2 (`CF-C3-P2-UPLOAD-SLICE2-IMPL-GO-001`)

`GO_STATUS=PO_AUTHORIZED` · `IMPLEMENTATION_AUTHORIZED=YES` · `SCOPE=P2_UPLOAD_SLICE_2` · `PRODUCTION_DEPLOY_AUTHORIZED=NO` · `PRODUCTION_MIGRATIONS_AUTHORIZED=NO`. Baseline: SLICE-1 aceito `ACCEPT_WITH_RESIDUAL` em `7d5e0402e0c8345623f64c828dcbf5d7ee275263`.

### J. Estado de implementação SLICE-2 (runtime)

| Contrato | Implementação | Evidência |
|---|---|---|
| U5 replace | `POST .../documents/{id}/versions` multipart (`file`, `idempotency_key` obrigatória **da mutação**, `revision` OCC, `branch_scope?`) — uploader original **ou** `manage` elegível (D-U1), `access` obrigatório, scope, humano; v anterior `SUPERSEDED` (derivada), nova `ATTACHED`, `FOR UPDATE`+revision ⇒ perdedor `stale_revision` 409; mesma sequência `.part`→sha256→`os.replace`→tx→compensação; `VERSION_ADDED` na tx; binário antigo nunca reescrito | `test_pg_closing_documents.py` (concorrência 4 threads → 1 vencedor; corrida mesma-key → dedup), `test_closing_document_service.py` |
| U6 versions | `GET .../documents/{id}/versions` — histórico imutável com metadados + `checksum_sha256`, sem `storage_key`; persiste após `CANCELLED`; paginação ≤100 | idem |
| U7 cancel | `POST .../documents/{id}/cancel` (`revision` OCC) — mesma regra de ator do U5; `CANCELLED != DELETED`: sai da listagem ativa, consultável via U3/U6/U8, arquivos/versões/auditoria preservados; duplo cancel = conflito tipado | idem |
| U8 events | `GET .../documents/{id}/events` — `DOCUMENT_UPLOADED`/`DOCUMENT_DOWNLOADED`/`VERSION_ADDED`/`DOCUMENT_CANCELLED` de `closing_audit_event` (append-only), scope autorizado, sem dados sensíveis | idem |
| Persistência | `V003` + **`V004__document_version_idempotency.sql`** (rework pós-revisão SLICE-2): `document_version` ganha `idempotency_key`/`request_hash` + `UNIQUE(document_id, key)` — D-U7=A aplicada ao aggregate da mutação (v1 herda a key do upload; replaces trazem key própria) — e perde a coluna `state`: a linha volta a ser **imutável de fato**, estado derivado de `current_version_no` | suíte PG em banco efêmero R4 |
| MFE | `ClosingDocumentsPanel` evoluído: substituir (file picker + OCC), histórico de versões com download por versão, cancelar com `ConfirmModalPanel`, histórico de auditoria — `createHostContainedModalShell` + `AttachmentFileList itemActions` do `@delpi/plugin-ui`; erros tipados (403/404/409) com retry seguro; Help sincronizado | `ClosingDocumentsPanel.test.tsx` |

**Boundary P5:** nenhum runtime de submissão de pacote existe no HEAD — `version_locked`/`document_locked` ficam reservados no contrato; a trava será ativada quando a fonte canônica P5 existir (AC-P2-UP-20 `TEST_NOT_RUN`, sem permissividade inventada).

### I. Pendências que permanecem abertas após D-U7=A

Retenção corporativa definitiva · inventário OFX/QIF/TXT com TÉO/Controladoria · E05 roles/obrigatoriedade · E06 motivos · CP-D02 · CP-D03 · reconciliação TÉO `RQ-P2-039` · antivírus (capability inexistente na plataforma) · housekeeping de `.part`/órfãos (PLANNED, exige especificação própria).
