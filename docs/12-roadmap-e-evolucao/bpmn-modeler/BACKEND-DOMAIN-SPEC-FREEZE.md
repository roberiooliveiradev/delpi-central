# BPMN MODELER — V1 BACKEND / DOMAIN / APPLICATION SPEC FREEZE

> **Status:** FROZEN (set/2026)
> **Produto:** Meu Modelador de Processos / BPMN Modeler
> **Bounded context:** `bpmn-modeler/` (package `bpmn_modeler`)
> **Base canônica:** `V1-SCOPE-FREEZE.md` (FROZEN, commit `1fa64cbe38`)
> **Natureza:** contrato funcional de backend (WHAT). Persistência física → Prompt 6; transporte HTTP → Prompt 7; regras BPMN/validação concretas → Prompt 3.
> **AMENDMENT G0 (out/2026):** freeze histórico. Decisões substituídas após implementação estão marcadas `SUPERSEDED (G0)` com o texto original preservado. Estado vigente: [`CURRENT-STATE.md`](CURRENT-STATE.md); divergências: [`DOCUMENTATION-DRIFT-LEDGER.md`](DOCUMENTATION-DRIFT-LEDGER.md).

Vocabulário de decisão:

| Estado | Significado |
|---|---|
| `FROZEN` | Decisão fechada neste documento. |
| `DELEGATED_TO_PROMPT_3` | Regra de validação/interoperabilidade BPMN — dono: Prompt 3. |
| `DELEGATED_TO_PROMPT_6` | Persistência física, security, runtime — dono: Prompt 6. |
| `DELEGATED_TO_PROMPT_7` | Transporte HTTP/OpenAPI/E2E — dono: Prompt 7. |

Capabilities conceituais usadas em todo o documento: `VIEW` (ler/exportar/validar), `EDIT` (criar/importar/editar/salvar/auto-layout), `MANAGE` (renomear, duplicar, arquivar, revisionar, restaurar). Mapeamento para permissões reais → Prompt 6.

---

## 1. Purpose

Fechar integralmente o contrato funcional de backend da V1: domain model, use cases, lifecycle, working copy, revisions, save, restore, duplicate, archive, concorrência, checksum, erros, ports, postconditions e read-back. Após este freeze, o implementador não escolhe nenhuma regra de negócio backend.

## 2. Baseline / Frozen Inputs

| Fonte | Estado |
|---|---|
| `V1-SCOPE-FREEZE.md` | FROZEN — scope de produto não se altera neste prompt |
| `Model → WorkingCopy → CanonicalBpmnArtifact(content: str)` | FROZEN — artefato opaco no Domain |
| `BpmnArtifactValidationPort → ValidationReport` (`ValidationIssue`, `ValidationStage`, `ValidationSeverity`, `RuleSource`) | FROZEN — evidência, não policy |
| `bpmn-modeler/tests/test_architecture.py` (domain/application sem fastapi/flask/sqlalchemy/lxml/xmlschema/transformometro/flowchart_v1/reactflow/mermaid/bpmn-js/bpmn-moddle) | FROZEN — enforcement vigente |
| Autosave | OUT_OF_V1 (Prompt 1) — save é sempre explícito |
| Restore append-only; história nunca reescrita | FROZEN (Prompt 1), formalizado na seção 12 |

> **SUPERSEDED (G0):** `Autosave OUT_OF_V1` — a V1 implementada possui autosave do **working copy** (frontend `AutosaveController` → `SaveWorkingCopy` use case + If-Match + read-back verify). Do ponto de vista do backend nada mudou: não existe endpoint de "autosave", o write continua sendo o `PUT working-copy` governado; o que mudou é quem dispara o save (debounce automático além do gesto manual). `AUTOSAVE != REVISION` permanece invariante. Ver `CURRENT-STATE.md` §4.

## 3. Aggregate Boundary

`FROZEN`:

- **Aggregate root: `Model`.** O agregado contém: identidade e metadata do modelo, exatamente uma `WorkingCopy`, e a coleção append-only de `Revision`.
- **`Revision` não é aggregate root.** Existe somente dentro de um `Model`; sua sequência (`revision_number`) é per-Model e sua criação participa da mesma fronteira transacional do agregado.
- **`WorkingCopy` não é aggregate root.** É parte obrigatória do `Model`.
- Não existem outros agregados na V1.
- Justificativa da fronteira única: save, create-revision e restore exigem atomicidade entre working copy, sequência de revisões e token de versão — tudo pertence ao mesmo agregado.

## 4. Domain Model

Conceitos do domain da V1 (sem fields de infraestrutura):

| Conceito | Papel | Conteúdo |
|---|---|---|
| `ModelId` | value object | identificador opaco do modelo |
| `RevisionId` | value object | identificador opaco de revisão |
| `Model` | aggregate root | `id`, `display_name`, `working_copy`, `archived_at`, `version`, `revisions` |
| `WorkingCopy` | entity (do agregado) | `artifact: CanonicalBpmnArtifact` |
| `CanonicalBpmnArtifact` | value object | `content: str` — opaco, sem parsing no Domain |
| `Revision` | entity (do agregado, imutável) | `revision_id`, `revision_number`, `artifact`, `checksum`, `created_at`, `created_by`, `origin`, `restored_from_revision_id` |

> **SUPERSEDED (G0):** `Revision` ganhou metadata vigente via `V002`/`V003` + implementação: `name` (1–120), `description` (≤500), `created_by_name` (display name sanitizado do autor). Opcionais; append-only/imutabilidade inalteradas. Ver `CURRENT-STATE.md` §5 e `domain/entities/revision.py`.

Campos de auditoria (`created_at`, `created_by`, `updated_at`, `updated_by`) e o token `version` são mantidos pela camada Application/persistência no registro do agregado; **não participam de invariantes de Domain** e não são editáveis por regra de domínio. O Domain só enforça: id não-vazio/imutável, display_name não-vazio, exatamente uma working copy, revisões imutáveis.

## 5. Identity Contract

`FROZEN`:

- `ModelId` e `RevisionId`: **server-generated opaque identifiers**. Cliente nunca fornece nem sugere IDs.
- IDs são imutáveis após atribuição.
- `create model`, `import`, `duplicate` sempre geram `ModelId` novo.
- `create revision` e `restore` sempre geram `RevisionId` novo.
- `restore` nunca reaproveita `ModelId` ou `RevisionId` existentes.
- BPMN element IDs nunca são usados como `ModelId`/`RevisionId`.
- Representação física do ID (uuid, ulid, sequence): `DELEGATED_TO_PROMPT_6`.

## 6. Model Metadata Contract

| Campo | Tipo lógico | Obrigatório | Definido por | Alterável por | Mutável | Camada |
|---|---|---|---|---|---|---|
| `id` | `ModelId` | sim | servidor | ninguém | imutável | Domain |
| `display_name` | string | sim | cliente (input) | rename (MANAGE) | sim | Domain |
| `working_copy` | `WorkingCopy` | sim | servidor | save/restore (EDIT/MANAGE) | sim | Domain |
| `archived_at` | timestamp \| null | sim (null = ativo) | servidor | archive/unarchive (MANAGE) | sim | Domain |
| `version` | int ≥ 1 | sim | servidor | mutations internas | sim | Application (concurrency token do agregado) |
| `revisions` | coleção `Revision` | sim (pode ser vazia) | servidor | create-revision/restore | append-only | Domain |
| `created_at` | timestamp | sim | servidor | ninguém | imutável | Application/persistência |
| `created_by` | principal identity | sim quando autenticado | servidor | ninguém | imutável | Application/persistência |
| `updated_at` | timestamp | sim | servidor | qualquer mutation | sim | Application/persistência |
| `updated_by` | principal identity | sim quando autenticado | servidor | qualquer mutation | sim | Application/persistência |

Decisões fechadas:

- `archived state` é representado por `archived_at` (timestamp ou null). **Não** existe `archived: bool` paralelo — fonte única: `archived_at is not null`.
- `revision indicator` da UI **não** é campo do agregado: `latest_revision` é derivado (maior `revision_number`); `selected_revision` é estado de navegação da UI. Ver seção 10.
- Nenhum metadado de produto é injetado dentro do XML BPMN.

> **AMENDMENT G0 (out/2026) — resource ownership:** este freeze especificou `created_by` como campo de auditoria; a implementação P0 promoveu `created_by` a **resource owner V1**. Todas as precondições de UC que leem/escrevem um Model existente passam a incluir: `caller.subject == Model.created_by` (além da permissão RBAC context-wide). Foreign resource → `MODEL_NOT_FOUND`/404 (sem leak); listagem exige `owner_subject` (sem caminho global); superadmin recebe as capabilities mas **não** atravessa `created_by`. Contrato vigente: `CURRENT-STATE.md` §3; ledger: DRIFT-BPMN-001.

## 7. Working Copy Contract

`FROZEN`:

- `WorkingCopy` = estado canônico **mutável** corrente de um `Model`.
- Existe **exatamente uma** working copy por `Model`. Um `Model` nunca existe sem working copy.
- `WorkingCopy` contém somente `CanonicalBpmnArtifact`. Identidade e versão vivem no `Model`.
- `save` substitui o artefato da working copy **integralmente** (replace total).
- Não existe save parcial.
- Não existe API de patch de XML.
- Não existe autosave.
  - **SUPERSEDED (G0):** existe autosave do working copy na V1 implementada (frontend orquestra; backend recebe `PUT working-copy` normal). O que permanece verdade: não existe save parcial nem write que crie revisão automaticamente.

## 8. Save Contract

`SAVE WORKING COPY` — semântica fechada:

```text
INPUT: model_id, artifact_content (string completa do .bpmn), expected_version

1. READ CURRENT    → carregar Model autoritativo
2. PRECONDITIONS   → model existe; model ativo (não arquivado); caller tem EDIT
3. CONCURRENCY     → expected_version == model.version, senão CONFLICT
4. NO-OP CHECK     → artifact_content byte-identical ao atual → NO_OP_SUCCESS (sem write, sem bump)
5. VALIDATION      → executar BpmnArtifactValidationPort → ValidationReport (evidência)
6. POLICY          → operation policy decide se issues bloqueiam (regras → Prompt 3)
                     bloqueado → VALIDATION_BLOCKED + evidência, sem write
7. WRITE           → working_copy.artifact = CanonicalBpmnArtifact(content=input)
                     version += 1; updated_at/updated_by = servidor
8. READ-BACK       → reler agregado autoritativo
9. VERIFY          → artifact.content == input esperado (checksum igual) e version == esperado+1
                     divergência → OUTCOME_VERIFICATION_FAILED
```

`FROZEN`: **save != create revision.** Save atualiza apenas a working copy. Revision é snapshot explícito via `create revision` (capability `MANAGE`). Justificativa: Prompt 1 separou working copy de revision snapshot explícito e atribuiu a criação de revisão ao Model Manager; save implícito criando revisão tornaria o histórico ruído de keystroke e removeria o gesto governado.

Validation é **sempre** executada no pipeline de save (a evidência acompanha a resposta). Save **não** pode persistir sem validation report; falha de infraestrutura do validator aborta o write (`INFRASTRUCTURE_FAILURE`). Quais issues bloqueiam = `DELEGATED_TO_PROMPT_3`.

## 9. Revision Contract

`FROZEN` — `Revision` = snapshot imutável da `WorkingCopy` no momento da criação:

| Campo | Tipo lógico | Obrigatório | Notas |
|---|---|---|---|
| `revision_id` | `RevisionId` | sim | opaco, server-generated |
| `revision_number` | int ≥ 1 | sim | sequência monotônica per-Model (seção 10) |
| `artifact` | `CanonicalBpmnArtifact` | sim | cópia exata do artefato da working copy no snapshot |
| `checksum` | SHA-256 hex | sim | computado no write, verificado no read-back (seção 20) |
| `created_at` | timestamp | sim | server-side clock |
| `created_by` | principal identity | sim quando autenticado | servidor |
| `origin` | enum: `manual` \| `restore` | sim | proveniência do snapshot |
| `restored_from_revision_id` | `RevisionId` \| null | quando `origin=restore` | aponta a revisão restaurada |

Sem `label`, `status`, `approval`, `comment thread` — não existem requirements V1 (Abstraction Gate). `origin`/`restored_from_revision_id` existem porque a semântica de restore (Prompt 1) exige proveniência registrada.

Invariantes (seção 34): artefato de revisão não muda; metadata de revisão não é reescrita; revisão não pode ser deletada na V1; `revision_number` nunca é reutilizado.

## 10. Revision Numbering

`FROZEN`:

- Identificador funcional exibido na V1: `revision_number` (ex.: "Rev 3") + `revision_id` para endereçamento técnico.
- `revision_number`: inteiro por `Model`, **começa em 1**, incremento estritamente +1 a cada revisão criada (manual ou restore).
- Nunca reutilizado; archive/unarchive não afeta a sequência; restore cria número novo (próximo da sequência).
- Sem SemVer — snapshot de modelagem não tem semântica de release.
- Terminologia oficial (ambiguidade eliminada):
  - `latest_revision` = revisão com maior `revision_number` (derivado);
  - `selected_revision` = estado de navegação da UI, **não** pertence ao agregado;
  - `working_copy` = estado mutável corrente;
  - o termo "current revision" está proibido em contratos.
- `RevisionSelector` para reads/restore: aceita `revision_id` **ou** `revision_number` — ambos resolvem unicamente dentro do Model.

## 11. Create Revision Contract

```text
INPUT: model_id, expected_version

1. READ CURRENT    → Model autoritativo
2. PRECONDITIONS   → existe; ativo; caller tem MANAGE
3. CONCURRENCY     → expected_version == version, senão CONFLICT
4. NO-OP CHECK     → artifact idêntico (checksum) ao da latest_revision → NO_CHANGES (rejeição; nenhuma revisão criada)
5. SNAPSHOT        → artifact = cópia exata do working_copy.artifact
                     revision_id novo; revision_number = next; checksum computado; origin=manual
6. WRITE           → append revision; version += 1; updated_at/updated_by = servidor
7. READ-BACK       → revisão relida; checksum e conteúdo iguais ao snapshot; número correto
```

`FROZEN`:

- Revision é snapshot **exato** da working copy (mesmos bytes).
- Validação **não bloqueia** create revision — snapshot registra o estado como ele é (checkpoints de estados inválidos são legítimos). Evidência de validação pode ser retornada, nunca exigida.
- `expected_version` é exigido: snapshot registra "o que o caller viu"; se a working copy mudou, CONFLICT força refresh.
- Create revision **não** altera o artefato da working copy.
- Create revision altera `updated_at` do Model e bumpa `version` — é uma mutation do agregado como qualquer outra.
- Revisão idêntica à latest → `NO_CHANGES` (rejeição, não no-op silencioso): o gesto "criar snapshot" só tem sentido quando há novo estado a capturar.

## 12. Restore Contract

Ambiguidade do Prompt 1 ("cria nova working copy/revisão") eliminada. Semântica única `FROZEN`:

```text
RESTORE revision N:
INPUT: model_id, RevisionSelector(N), expected_version

1. READ            → Model autoritativo + revisão N
2. PRECONDITIONS   → model existe; ativo; caller tem MANAGE;
                     N pertence a este model, senão REVISION_OWNERSHIP_MISMATCH
3. CONCURRENCY     → expected_version == version, senão CONFLICT
4. NO-OP CHECK     → artifact de N idêntico (checksum) ao working copy atual
                     → NO_OP_SUCCESS (sem write, sem revisão nova)
5. WRITE (single transaction):
   a. working_copy.artifact = cópia exata do artifact de N
   b. append NEW Revision: snapshot do novo estado da working copy,
      origin=restore, restored_from_revision_id=N.revision_id,
      revision_number = next, revision_id novo, checksum computado
   c. version += 1; updated_at/updated_by = servidor
6. READ-BACK       → working copy checksum == checksum de N;
                     nova revisão existe com proveniência correta;
                     version == esperado+1; revisões antigas intactas
```

`FROZEN`:

- Restore é atômico: replace da working copy + append de revisão + version bump em **uma** transação.
- Restore do `latest_revision`: permitido quando a working copy divergiu dele; se artefato já é igual → NO_OP_SUCCESS.
- Restore de revisão de **outro** Model: `REVISION_OWNERSHIP_MISMATCH`.
- Restore em Model arquivado: `MODEL_ARCHIVED`.
- Validação não bloqueia restore (conteúdo já existia no sistema); evidence on demand.
- Restore não é idempotente-creativo: repetir com mesmo `expected_version` stale → CONFLICT; com versão corrente e artefato já igual → NO_OP_SUCCESS.

## 13. Duplicate Contract

`FROZEN` (Prompt 1 + refinamento):

- Fonte: **working copy atual** do model de origem (artefato canônico corrente — não latest revision).
- Cria `Model` novo: `ModelId` novo, `version=1`, `archived_at=null`, **zero** revisions.
- **Não** copia revisions. **Não** copia archive state. **Não** cria revisão inicial automática.
- `display_name`: input obrigatório explícito do caller (mesmas regras de validação de nome; sem auto-sufixo server-side — sugestão "cópia de X" é decisão de UX, Prompt 4).
- Origem pode estar arquivada (duplicate é read-semantics sobre a origem).
- Sem vínculo permanente source→duplicate (nenhum `source_model_id` persistido — sem requirement).
- Sem token de concorrência sobre a origem (read de snapshot corrente); novo agregado nasce com version=1.

## 14. Import Contract

`FROZEN`:

- `import != save`: import **sempre cria novo `Model`** — nunca substitui model existente na V1 (replace-import = FUTURE).
- INPUT: `artifact_content` (bytes/string do arquivo), `display_name` explícito obrigatório. Filename do upload é detalhe de transporte (Prompt 7), não fonte de display_name no contrato Application.
- Artefato é armazenado **exatamente como recebido** — nenhuma resserialização ou normalização no intake (regras de preservação/parsing → Prompt 3).
- Intake executa validation pipeline → ValidationReport; quais condições bloqueiam a criação do model = operation policy → Prompt 3. Se bloqueado: `VALIDATION_BLOCKED`, nenhum model criado.
- `ModelId` novo, `version=1`, `archived_at=null`, zero revisions, sem revisão automática.
- Resultado: model criado abre diretamente na working copy importada.

## 15. Archive / Unarchive Contract

`FROZEN`:

- `archive != delete`. Hard delete não existe na V1.
- `archive` não altera `artifact` nem revisions: apenas `archived_at = now()`.
- `unarchive` limpa `archived_at` e devolve o model ao estado ativo integral (nada é perdido).
- Archived model = **read-only + unarchive + duplicate-source** (matriz completa na seção 30).
- Ambas são mutations: exigem `expected_version`, bumpam `version`, atualizam `updated_at/by`.
- Default de listagem exclui arquivados (seção 18).

## 16. Rename Contract

`FROZEN`:

- `rename` altera somente `display_name` (metadata de produto).
- Rename **não** altera: `bpmn:process.name`, `bpmn:definitions.name`, qualquer byte do artefato canônico, filename persistido.
- Mutation normal: `expected_version` exigido, `version+1`, `updated_at/by`.
- Rename para o mesmo nome (após trim) → `NO_OP_SUCCESS` (sem write, sem bump).

## 17. Read Contracts

| Use case | Retorna | Token? |
|---|---|---|
| `GetModel` | metadata do model (id, display_name, archived_at, version, created/updated audit, latest_revision_number) | não |
| `ListModels` | itens de listagem (metadata, sem artefato) + paginação | não |
| `GetWorkingCopy` | `CanonicalBpmnArtifact` atual + `version` + checksum | não |
| `ListRevisions` | metadata das revisions (id, number, origin, created_at/by, checksum) ordenado por `revision_number` desc | não |
| `GetRevision` | metadata + artefato snapshot de uma revisão | não |
| `ExportWorkingCopy` | conteúdo exato do artefato corrente | não |
| `ExportRevision` | conteúdo exato do snapshot da revisão | não |
| `ValidateWorkingCopy` | `ValidationReport` do **artefato candidato** fornecido pelo caller (evidência efêmera; nunca persiste) | não |

`search models` **não** é use case separado — é filtro de `ListModels` (mesma semântica de leitura).

## 18. Search / Pagination Contract

`FROZEN` (Prompt 1 + refinamento, independente de HTTP/SQL):

- Filtro `query`: **case-insensitive, contains** sobre `display_name`; match **exato** sobre `id`.
- Filtro `archived`: `active` (default — exclui arquivados), `archived`, `all`.
- Sort: `updated_at` (default, desc — "recentes primeiro"), `created_at`, `display_name` (asc; desc permitido).
- Paginação: wire resolvido em `API-E2E-ACCEPTANCE-SPEC-FREEZE` §18 (offset page-based, `page`/`page_size`, `has_more`); Application recebe `page_size` + posição e retorna `items` + `has_more`. `total_count` **não** é exigido na V1 (não inventar count caro sem requirement).
- Resultado contém apenas metadata (nunca artefato) — listagem não carrega XML.

## 19. Export Contract

`FROZEN`:

- `ExportWorkingCopy` retorna o conteúdo **exato** (bytes UTF-8) do `CanonicalBpmnArtifact` corrente — sem resserialização.
- `ExportRevision` retorna o conteúdo **exato** do snapshot persistido da revisão — V1 exporta revisão histórica (Prompt 1: Viewer abre revisões e exporta `.bpmn`).
- Filename exportado deriva de `display_name` sanitizado (`<display_name>.bpmn`; revisão: `<display_name>-rev<number>.bpmn`) — filename é derivado de apresentação, nunca fonte de verdade. Sanitização/wire format → Prompt 7.
- Export não altera estado, não exige token, não roda validation policy (exporta o que está persistido).

## 20. Checksum / Artifact Identity

`FROZEN`:

- `checksum` = **SHA-256, lowercase hex, dos bytes UTF-8 exatos** de `CanonicalBpmnArtifact.content`.
- **Sem canonicalização/normalização XML** — checksum representa identidade de conteúdo exato, não equivalência semântica.
- Usos: verificação de read-back, evidência de identidade de revisão, detecção de no-op (save/restore/create-revision idênticos), suporte a concorrência.
- Dois artefatos com checksum igual = mesmo conteúdo byte-a-byte. Checksum **não** prova equivalência semântica BPMN.

## 21. Optimistic Concurrency Contract

`FROZEN` — estratégia única:

- `Model.version` = inteiro monotônico, inicia em 1 na criação do agregado.
- **Toda** mutation recebe `expected_version` do caller.
- `expected_version != version` autoritativo → `CONFLICT`, nenhum write.
- Toda mutation bem-sucedida → `version += 1` (save, restore, create revision, rename, archive, unarchive).
- Um único token por agregado — sem separação metadata-version vs working-copy-version (não há requirement que justifique dois tokens).
- Mecanismo físico (coluna/ETag/lock): `DELEGATED_TO_PROMPT_6`/`DELEGATED_TO_PROMPT_7`.

## 22. Audit Metadata

`FROZEN`:

- `created_at`, `updated_at`, `revision.created_at`: server-side clock (`ClockPort`).
- `created_by`, `updated_by`, `revision.created_by`: principal autenticado resolvido server-side; cliente **não** pode forjar campos de auditoria.
- Ausência de identidade (ex.: migration futura) não é inventada — campo pode ficar vazio somente por decisão do Prompt 6, nunca por input do cliente.
- Não existe event sourcing na V1.

## 23. Repository Ports

`FROZEN` — boundary aggregate-oriented, menor separação que preserva atomicidade:

| PORT_ID | NAME | PURPOSE | OPERATIONS (lógicas) |
|---|---|---|---|
| PORT-STORE-001 | `ModelRepositoryPort` | persistência do agregado `Model` inteiro (metadata + working copy + revisions) | `create_aggregate`, `get_aggregate`, `list_summaries(filters, sort, page)`, `get_revision(model_id, selector)`, `mutate` (mutation atômica versionada do agregado) |

Decisões:

- **Uma** port cobre model + working copy + revisions: save/restore/create-revision exigem atomicidade dentro do mesmo agregado — port separada de Revision criaria fronteira transversal sem dono.
- `mutate` recebe `expected_version` e aplica a mutation de forma atômica; adapter implementa o compare-and-swap físico (Prompt 6).
- `NO PORT` para: `GenericRepository`, `CrudRepository`, `UnitOfWork`, `RevisionRepository` separado — sem requirement.
- `ClockPort` (`now()`): **APROVADA** — toda mutation grava timestamps; testes de Application exigem tempo determinístico. Application-owned, não vaza infraestrutura (recebe/adere a `datetime`, não a SDK).
- `IdGeneratorPort` (`new_model_id()`, `new_revision_id()`): **APROVADA** — IDs server-generated por contrato; testes determinísticos exigem injeção.
- `HashPort`: **NO PORT** — SHA-256 é função pura stdlib em Application; sem variabilidade nem infraestrutura.
- `BlankArtifactFactoryPort` (`new_blank_artifact() -> CanonicalBpmnArtifact`): **APROVADA** — create model precisa do XML BPMN mínimo; Domain é opaco e não constrói XML; Application pede ao port, adapter implementa (tecnologia → Prompt 3/5).
- `BpmnArtifactValidationPort`: já existente, FROZEN.

## 24. Application Use Case Catalog

Lista autoritativa — nenhum use case adicional sem requirement:

| UC_ID | NAME | CAPABILITY | PURPOSE |
|---|---|---|---|
| UC-MODEL-001 | `CreateModel` | EDIT | criar model em branco com working copy inicial |
| UC-MODEL-002 | `ImportModel` | EDIT | criar model a partir de arquivo `.bpmn` |
| UC-MODEL-003 | `GetModel` | VIEW | ler metadata + estado do model |
| UC-MODEL-004 | `ListModels` | VIEW | listar/buscar/ordenar/paginar models |
| UC-MODEL-005 | `RenameModel` | MANAGE | alterar display_name |
| UC-MODEL-006 | `DuplicateModel` | MANAGE | criar model novo a partir da working copy de origem |
| UC-MODEL-007 | `ArchiveModel` | MANAGE | arquivar model |
| UC-MODEL-008 | `UnarchiveModel` | MANAGE | desarquivar model |
| UC-WC-001 | `GetWorkingCopy` | VIEW | ler artefato canônico corrente + version + checksum |
| UC-WC-002 | `SaveWorkingCopy` | EDIT | substituir artefato da working copy (seção 8) |
| UC-WC-003 | `ExportWorkingCopy` | VIEW | exportar `.bpmn` corrente |
| UC-WC-004 | `ValidateWorkingCopy` | VIEW | obter ValidationReport do **artefato candidato** enviado pelo editor (estado visível, possivelmente dirty); sem persistência; não altera version nem escreve revision |
| UC-REV-001 | `ListRevisions` | VIEW | listar metadata de revisions |
| UC-REV-002 | `GetRevision` | VIEW | ler revisão (metadata + snapshot) |
| UC-REV-003 | `CreateRevision` | MANAGE | snapshot imutável explícito da working copy |
| UC-REV-004 | `RestoreRevision` | MANAGE | restaurar revisão (append-only, seção 12) |
| UC-REV-005 | `ExportRevision` | VIEW | exportar `.bpmn` de revisão histórica |

### Contratos por use case (mutations)

| UC | INPUT | PRECONDITIONS | VALIDATION | CONCURRENCY | WRITE | POSTCONDITION | READ-BACK | ERRORS |
|---|---|---|---|---|---|---|---|---|
| UC-MODEL-001 | display_name | caller EDIT | display_name válido | n/a (agregado novo) | agregado + blank artifact | model ativo, version=1, 0 revisions | get: nome/versão/artefato presentes | INVALID_DISPLAY_NAME, UNAUTHORIZED_OPERATION, INFRASTRUCTURE_FAILURE, OUTCOME_VERIFICATION_FAILED |
| UC-MODEL-002 | artifact_content, display_name | caller EDIT | display_name válido; intake validation → policy (P3) | n/a | agregado com artefato importado exato | model ativo, version=1, conteúdo == input | get: checksum == sha256(input) | INVALID_DISPLAY_NAME, VALIDATION_BLOCKED, UNAUTHORIZED_OPERATION, INFRASTRUCTURE_FAILURE, OUTCOME_VERIFICATION_FAILED |
| UC-MODEL-005 | model_id, display_name, expected_version | existe, ativo, MANAGE | display_name válido; mesmo nome → NO_OP_SUCCESS | expected_version | display_name | version+1, updated_at/by | get: nome novo, version+1 | MODEL_NOT_FOUND, MODEL_ARCHIVED, INVALID_DISPLAY_NAME, CONFLICT, UNAUTHORIZED_OPERATION, OUTCOME_VERIFICATION_FAILED |
| UC-MODEL-006 | source_model_id, display_name | origem existe (ativo ou arquivado), caller MANAGE + VIEW na origem | display_name válido | n/a | agregado novo, artefato = working copy da origem | novo model ativo, version=1, 0 revisions | get novo: checksum == origem | MODEL_NOT_FOUND, INVALID_DISPLAY_NAME, UNAUTHORIZED_OPERATION, OUTCOME_VERIFICATION_FAILED |
| UC-MODEL-007 | model_id, expected_version | existe, ativo (já arquivado → NO_OP_SUCCESS), MANAGE | — | expected_version | archived_at=now | version+1 | get: archived_at set | MODEL_NOT_FOUND, CONFLICT, UNAUTHORIZED_OPERATION, OUTCOME_VERIFICATION_FAILED |
| UC-MODEL-008 | model_id, expected_version | existe, arquivado (ativo → NO_OP_SUCCESS), MANAGE | — | expected_version | archived_at=null | version+1 | get: archived_at null | MODEL_NOT_FOUND, CONFLICT, UNAUTHORIZED_OPERATION, OUTCOME_VERIFICATION_FAILED |
| UC-WC-002 | seção 8 | existe, ativo, EDIT | validation pipeline + policy (P3); idêntico → NO_OP_SUCCESS | expected_version | working_copy.artifact | version+1, updated_at/by | artefato+checksum+version | MODEL_NOT_FOUND, MODEL_ARCHIVED, CONFLICT, VALIDATION_BLOCKED, UNAUTHORIZED_OPERATION, OUTCOME_VERIFICATION_FAILED |
| UC-REV-003 | seção 11 | existe, ativo, MANAGE | não bloqueia; idêntico à latest → NO_CHANGES | expected_version | append revision | version+1, revision_number=next | revisão relida íntegra | MODEL_NOT_FOUND, MODEL_ARCHIVED, CONFLICT, NO_CHANGES, UNAUTHORIZED_OPERATION, OUTCOME_VERIFICATION_FAILED |
| UC-REV-004 | seção 12 | existe, ativo, MANAGE, revisão pertence ao model | não bloqueia; idêntico → NO_OP_SUCCESS | expected_version | WC replace + append revision (1 tx) | version+1, nova revisão origin=restore | checksum WC == revisão N; nova revisão existe | MODEL_NOT_FOUND, MODEL_ARCHIVED, REVISION_NOT_FOUND, REVISION_OWNERSHIP_MISMATCH, CONFLICT, UNAUTHORIZED_OPERATION, OUTCOME_VERIFICATION_FAILED |

## 25. Transaction Boundaries

`FROZEN` — postconditions indivisíveis:

| Operação | Unidade atômica |
|---|---|
| SaveWorkingCopy | WC replace + version+1 + audit |
| CreateRevision | leitura da WC + append revision + version+1 + audit |
| RestoreRevision | WC replace + append revision + version+1 + audit — **uma** transação |
| DuplicateModel | criação do agregado novo inteiro (metadata + WC) |
| ImportModel | criação do agregado novo inteiro |
| CreateModel | idem |
| Rename/Archive/Unarchive | mutation de metadata + version+1 + audit |

Nenhuma operação cruza dois agregados numa mesma transação (duplicate/import só escrevem o agregado novo). Tecnologia de transação → Prompt 6.

## 26. Prepare / Confirm Matrix

| Operação | PREPARE (evidência/preview) | CONFIRM UX |
|---|---|---|
| SaveWorkingCopy | sim — validation evidence + version check precedem write | save explícito já é a confirmação |
| ImportModel | sim — intake validation evidence exibida antes de concluir | implícito no fluxo de import (Prompt 4) |
| RestoreRevision | sim — apresentar revisão alvo | **sim** — sobrescreve working copy; UX deve pedir confirmação (Prompt 4) |
| ArchiveModel | não | não exigido |
| UnarchiveModel | não | não |
| DuplicateModel | não | não |
| RenameModel | não | não |
| CreateRevision | não (snapshot direto) | não |

> **SUPERSEDED (G0):** `SaveWorkingCopy` — na implementação vigente o gesto explícito é substituído pelo autosave do working copy (debounce → `PUT working-copy` → read-back verify); `Ctrl+S` permanece como flush manual. A coluna CONFIRM UX continua correta: nenhuma confirmação modal adicional foi adicionada ao save.

Fluxo geral de writes: `READ CURRENT → PREPARE quando aplicável → VALIDATE → CONFIRM quando aplicável → WRITE → AUTHORITATIVE READ-BACK → VERIFY`.

## 27. Authoritative Read-back Matrix

| Operação | Postcondition | Read-back verifica |
|---|---|---|
| CreateModel | agregado existe, version=1, WC com blank artifact | get: id, nome, version, artefato presente |
| ImportModel | agregado com artefato exato | checksum(read) == sha256(input) |
| RenameModel | display_name novo | get: nome == input, version+1 |
| DuplicateModel | novo agregado com artefato da origem | checksum(novo) == checksum(origem) |
| ArchiveModel | archived_at set | get: archived_at != null, version+1 |
| UnarchiveModel | archived_at null | get: archived_at == null, version+1 |
| SaveWorkingCopy | artefato substituído | checksum == sha256(input), version+1 |
| CreateRevision | revisão appended | get_revision: artifact==WC snapshot, number=esperado, checksum ok |
| RestoreRevision | WC == artefato de N + nova revisão | checksum(WC)==checksum(N); nova revisão origin=restore; version+1 |

Qualquer divergência de read-back → `OUTCOME_VERIFICATION_FAILED`: write **não** é considerado bem-sucedido pelo retorno do adapter.

## 28. Application Error Taxonomy

`FROZEN` — catálogo lógico (mapeamento HTTP → Prompt 7):

| Erro | Classe | Causa |
|---|---|---|
| `MODEL_NOT_FOUND` | rejection | model_id inexistente |
| `REVISION_NOT_FOUND` | rejection | seletor de revisão inexistente no model |
| `REVISION_OWNERSHIP_MISMATCH` | rejection | revisão pertence a outro model |
| `MODEL_ARCHIVED` | rejection | mutation em model arquivado (exceto unarchive/duplicate-source) |
| `INVALID_DISPLAY_NAME` | rejection | nome vazio/após-trim ou > 120 chars |
| `CONFLICT` | rejection | expected_version stale |
| `NO_CHANGES` | rejection | create-revision sem mudança desde latest |
| `VALIDATION_BLOCKED` | rejection | operation policy bloqueou write por issues (regras → P3) |
| `UNAUTHORIZED_OPERATION` | rejection | capability conceitual insuficiente (enforcement → P6) |
| `OUTCOME_VERIFICATION_FAILED` | verification failure | read-back diverge do postcondition |
| `INFRASTRUCTURE_FAILURE` | infrastructure failure | persistência/validator indisponível etc. — não é erro de domínio |

`NO_OP_SUCCESS` é resultado de sucesso, não erro. Não existe `INTERNAL_ERROR` de domínio.

## 29. No-op / Idempotency Matrix

`FROZEN`:

| Caso | Resultado |
|---|---|
| rename para mesmo nome | `NO_OP_SUCCESS` (version verificada; sem write/bump) |
| save com artefato idêntico | `NO_OP_SUCCESS` (version verificada; sem write/bump) |
| archive já arquivado | `NO_OP_SUCCESS` |
| unarchive model ativo | `NO_OP_SUCCESS` |
| restore cujo artefato == WC atual | `NO_OP_SUCCESS` (sem revisão nova) |
| create revision idêntico à latest | `NO_CHANGES` (rejeição) |
| duplicate / import | sempre criam novo agregado — sem no-op |

Idempotência de transporte (retry de cliente, idempotency-key HTTP): resolvido em `API-E2E-ACCEPTANCE-SPEC-FREEZE` §19 — `Idempotency-Key` é `OUT_OF_V1`; frontend nunca auto-retenta writes. Semanticamente: mutations com `expected_version` são naturalmente protegidas — retry com versão stale → `CONFLICT`; retry que encontra estado final idêntico → `NO_OP_SUCCESS` onde definido.

## 30. Archived Model Operation Matrix

| Operação | Active | Archived |
|---|---|---|
| get/open read-only | permitido | permitido |
| export working copy | permitido | permitido |
| export revision | permitido | permitido |
| list revisions / get revision | permitido | permitido |
| validate working copy | permitido | permitido |
| rename | permitido | `MODEL_ARCHIVED` |
| save working copy | permitido | `MODEL_ARCHIVED` |
| create revision | permitido | `MODEL_ARCHIVED` |
| restore | permitido | `MODEL_ARCHIVED` |
| duplicate (como origem) | permitido | permitido |
| archive | permitido | `NO_OP_SUCCESS` |
| unarchive | `NO_OP_SUCCESS` | permitido |

Regra única: archived = read-only + unarchive + duplicate-source.

## 31. WorkingCopy / Revision Relationship Matrix

| Concept | Mutable | Canonical artifact | Own identity | Historic | Exportable |
|---|---|---|---|---|---|
| `Model` | sim (metadata/estado/WC) | não diretamente — contém WC e revisions | `ModelId` | não | via artefatos |
| `WorkingCopy` | sim | sim — artefato corrente | não pública (vive sob o Model) | não | sim |
| `Revision` | não | sim — snapshot exato | `RevisionId` + `revision_number` | sim | sim |

Cardinalidades `FROZEN`: `Model` 1→1 `WorkingCopy`; `Model` 1→N `Revision` (N ≥ 0); `Revision` → exatamente 1 `Model`.

## 32. Validation Evidence Storage Policy

`FROZEN`:

- `ValidationReport` é **evidência efêmera**: produzida por `ValidateWorkingCopy` e no pipeline de save/import; **não** é persistida como fonte de verdade, não faz parte do agregado `Model`, não vira autoridade paralela.
- Cache/auditoria de relatórios: fora da V1 (`FUTURE` se surgir requirement).

## 33. Derived Artifact Policy

`FROZEN`:

- SVG/PNG são gerados **on demand** (renderização do artefato canônico); **não** são persistidos como fonte de verdade na V1.
- Derivados nunca são necessários para reconstruir o modelo canônico.
- Nenhum campo de thumbnail/preview no agregado na V1.

## 34. Domain Invariants

Lista final e completa — somente invariantes reais do Domain:

1. `Model.id` não-vazio e imutável.
2. `Model.display_name` não-vazio após trim, máx. 120 caracteres.
3. `Model` possui exatamente uma `WorkingCopy` (nunca zero, nunca duas).
4. `WorkingCopy` contém exatamente um `CanonicalBpmnArtifact`.
5. `Revision` é imutável: artefato e metadata nunca mudam após criação.
6. `Revision` pertence a exatamente um `Model`.
7. `revision_number` é positivo, estritamente crescente por Model, nunca reutilizado.
8. Histórico é append-only: revisões nunca são reescritas ou deletadas.

Explicitamente **não** são invariantes de Domain: "XML deve ser BPMN válido", "DI presente", "elementos do profile" — vivem na fronteira de validação (Application + Prompt 3).

## 35. Application Invariants

`FROZEN`:

1. Toda mutation exige `expected_version` igual ao autoritativo; divergência → `CONFLICT`, sem write.
2. Model arquivado rejeita qualquer mutation exceto unarchive (e serve de origem para duplicate).
3. Snapshot de revisão é byte-igual ao artefato da working copy no instante da transação.
4. Restore preserva história: sempre appends, nunca rewrites.
5. Todo write só é reportado como sucesso após read-back autoritativo igual ao postcondition.
6. Campos de auditoria são gerados server-side; input de cliente nunca os define.
7. Import e duplicate produzem sempre `ModelId` novo.
8. Export retorna bytes exatos persistidos; nenhuma transformação no caminho de export.
9. Nenhum metadata de produto é escrito dentro do XML BPMN.
10. ValidationReport nunca é persistido como fonte de verdade.

## 36. Decision Delegation Map

| Para | Decisões delegadas |
|---|---|
| `DELEGATED_TO_PROMPT_3` | regras de validação por stage; quais issues bloqueiam import/save/export (operation policy); parser/preservation/round-trip; tratamento de extensions; implementação do `BlankArtifactFactoryPort` (tecnologia) e intake de BPMN sem DI (com P5) |
| `DELEGATED_TO_PROMPT_6` | representação física de IDs; schema/tables/indexes/migrations; implementação de `ClockPort`/`IdGeneratorPort`/`ModelRepositoryPort`; mecanismo físico de compare-and-swap; RBAC/códigos de permissão para VIEW/EDIT/MANAGE; resolução de principal; runtime |
| `DELEGATED_TO_PROMPT_7` | rotas HTTP, request/response, status codes, OpenAPI, mapeamento `version`↔ETag, idempotency-key de transporte, sanitização de filename no header, paginação wire (cursor/offset), E2E |

## 37. Open Questions

Nenhuma questão funcional de backend aberta. As pendentes são exclusivamente HOW técnico com dono já atribuído (seção 36): parser/validator/policy (P3), storage físico/security/runtime (P6), transporte/API (P7).

## 38. Specification Freeze Status

- [x] Aggregate boundary fechado (Model único; WC e Revision dentro do agregado)
- [x] Campos conceituais decididos campo a campo
- [x] Identity contract fechado (server-generated opaque IDs)
- [x] Save semantics fechado (save != create revision; pipeline completo)
- [x] Revision semantics fechada (imutável, append-only, numeração per-Model)
- [x] Restore fechado (semântica única, transação atômica, proveniência)
- [x] Concurrency lógico fechado (`version` único por agregado)
- [x] Checksum fechado (SHA-256 UTF-8 exato, sem normalização)
- [x] Lifecycle inteiro fechado (create/import/rename/duplicate/archive/unarchive/save/revision/restore)
- [x] Use case catalog completo (17 UCs)
- [x] Repository ports decididas (1 store port + Clock + IdGen + Validation existente + BlankArtifactFactory)
- [x] Error taxonomy fechada
- [x] No-op behavior fechado
- [x] Archived behavior fechado
- [x] Read-back/postconditions fechados para todo write
- [x] Nenhuma regra backend crítica deixada para inferência

```text
BACKEND / DOMAIN SPEC STATUS:
FROZEN
```
