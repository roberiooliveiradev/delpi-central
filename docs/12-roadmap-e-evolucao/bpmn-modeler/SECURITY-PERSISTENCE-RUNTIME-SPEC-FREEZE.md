# BPMN Modeler — Security / Persistence / Runtime Spec Freeze (Prompt 6/7)

> **Status:** `FROZEN`
> **Escopo:** segurança, autenticação, autorização, persistência física, banco de dados, dependências exatas, runtime, deploy, observabilidade, migrações e CI da V1.
> **Natureza:** freeze de especificação. **Nenhuma linha de código de produção é autorizada por este documento.**

Este documento fecha todas as decisões de infraestrutura, segurança e runtime que os Prompts 1–5 declararam como `DELEGATED_TO_PROMPT_6`. Após este freeze, o implementador **não escolhe** stack, versão, schema físico, permissão, limite de segurança, política de deploy ou gate de CI.

Autoridade documental (em ordem de precedência para este contexto):

```text
1. V1-SCOPE-FREEZE.md                    (produto/escopo)
2. BACKEND-DOMAIN-SPEC-FREEZE.md         (domínio/aplicação)
3. BPMN-INTEROPERABILITY-SPEC-FREEZE.md  (BPMN/validação/artefato canônico)
4. FRONTEND-EDITOR-UX-SPEC-FREEZE.md     (editor/UX/estado)
5. LAYOUT-BPMN-DI-SPEC-FREEZE.md         (layout/BPMN-DI/worker)
6. ESTE DOCUMENTO                        (segurança/persistência/runtime)
```

Em conflito, o documento anterior vence para o seu domínio; este documento vence para segurança, persistência física, versões, runtime e operação.

---

## 1. Unidades de deployment e topologia

`FROZEN`:

| Unidade | Tipo | Localização | Runtime |
|---|---|---|---|
| `bpmn-modeler` | Backend API (bounded context dono) | `bpmn-modeler/` (raiz do repo; skeleton `bpmn_modeler/` já existente) | Python 3.11, FastAPI, uvicorn |
| `plugins/bpmn-modeler` | Frontend MFE | `plugins/bpmn-modeler/` | Node 20, React, Vite, Module Federation |
| `postgres-plugins` | Banco compartilhado de plugins | serviço Docker `postgres-plugins` | PostgreSQL 15 |
| gateway | nginx | `gateway/` | rotas `/apps/bpmn-modeler-api/*` |

Regras de fronteira:

- O backend é o **único dono** do schema `bpmn_modeler` e de todo dado persistente do contexto.
- O MFE comunica-se apenas via HTTP com `bpmn-modeler` API — nunca acesso direto a banco, nunca reutilização de API de outro contexto como atalho.
- **Nenhuma** dependência de banco do Transformômetro (`transformometro` schema/DB). `flowchart_v1` é conceito legado do Transformômetro e não é modelo de persistência BPMN (decisão herdada do Prompt 2).
- Não existe endpoint de layout no backend: layout é 100% frontend via Web Worker (decisão herdada do Prompt 5).

### 1.1 Identidade de serviço

`FROZEN`:

| Propriedade | Valor |
|---|---|
| Docker service name | `bpmn-modeler-api` |
| Dockerfile | `bpmn-modeler/Dockerfile` (base `python:3.11-slim`) |
| ASGI target | `bpmn_modeler.main:app` |
| Root path | `/apps/bpmn-modeler-api` |
| Porta interna | `8000` (sem bind de host; gateway é a única porta externa) |
| Healthcheck | `curl -f http://localhost:8000/health` |

---

## 2. Backend runtime — versões exatas

`FROZEN` — pins literais em `bpmn-modeler/requirements.txt` (sem ranges flutuantes; `mcp`, SDKs e deps fora deste catálogo são proibidos sem nova decisão):

| Dependência | Versão exata | Razão |
|---|---|---|
| Python (imagem) | `python:3.11-slim` | convenção monorepo de APIs FastAPI |
| `fastapi` | `0.118.0` | pin já adotado no monorepo (`delpi-mes-api`) |
| `uvicorn[standard]` | `0.37.0` | pin já adotado (`delpi-mes-api`) |
| `pydantic` | `2.11.9` | pin já adotado (`delpi-mes-api`) |
| `psycopg[binary]` | `3.3.4` | driver Postgres psycopg3, pin já adotado |
| `python-multipart` | `0.0.32` | upload multipart do `.bpmn` |
| `python-dotenv` | `1.1.1` | config local, convenção |
| `lxml` | `6.1.3` | parser/validator XML/XSD canônico (Prompt 3) |
| `httpx` | `0.28.1` | cliente de teste |
| `pytest` | `8.4.2` | testes backend |
| `shared` (delpi_auth) | `-e /shared[fastapi]` | auth transversal canônica do monorepo — resolve `python-jose[cryptography]` internamente; **proibido** reimplementar jwt/JWKS/require_permission localmente |

Versões avaliadas no registry oficial (PyPI/Docker Hub) na data deste freeze; todas anteriores a 7 dias do freeze. Mudança de versão exige revisão deste documento + justificativa.

---

## 3. Frontend runtime — versões exatas

`FROZEN`:

| Item | Valor | Fonte |
|---|---|---|
| Node | `20` (imagem `node:20-alpine` no build; CI `node-version: 20`) | convenção monorepo |
| Package manager | `npm` com `package-lock.json` commitado | convenção |
| React | `19.2.7` | mesma versão do Portal/plugins |
| React DOM | `19.2.7` | paridade com React |
| Vite | `7.3.1` | convenção plugins |
| `@module-federation/vite` | `1.4.1` | packaging MFE canônico |
| TypeScript | `5.9.3` | convenção plugins |
| Testing | `vitest` + `@testing-library/react` (versões transitórias do kit plugins) | convenção |

### 3.1 Dependências de domínio — locks exatos

`FROZEN` — estas são as únicas dependências BPMN/layout autorizadas; versões avaliadas no npm registry:

| Pacote | Versão exata | Licença | Papel |
|---|---|---|---|
| `bpmn-js` | `18.30.1` | MIT (conforme registry) | editor/modeler/renderer |
| `bpmn-moddle` | `10.2.0` | MIT | modelo semântico / serialização |
| `bpmn-js-properties-panel` | `5.65.1` | MIT | properties panel |
| `@bpmn-io/properties-panel` | `3.40.6` | MIT | primitives do panel |
| `elkjs` | `0.12.0` | EPL-2.0 OR GPL-3.0-or-later → **EPL-2.0 selecionada** | auto-layout (Prompt 5) |

Regras:

- Versões pinadas exatas em `plugins/bpmn-modeler/package.json` (sem `^`, `~`, `latest`).
- `package-lock.json` obrigatório e verificado em CI via `npm ci`.
- Licenças: MIT permitido; `elkjs` consumido sob o branch **EPL-2.0** da dual-license — GPL-3.0 não é aceito. Qualquer nova licença fora de {MIT, Apache-2.0, BSD-2/3, ISC, EPL-2.0} exige aprovação antes de uso.

---

## 4. Banco de dados

`FROZEN`:

| Propriedade | Valor |
|---|---|
| Engine | PostgreSQL 15 (imagem `postgres:15`, serviço `postgres-plugins`) |
| Database | `${PLUGINS_DB_NAME}` (banco compartilhado de plugins) |
| Schema | `bpmn_modeler` — ownership exclusivo deste contexto |
| Runtime role | `${PLUGINS_DB_USER}` (role compartilhada de plugins, por convenção da plataforma) |
| Isolamento | `search_path = bpmn_modeler` por conexão; **proibido** ler/escrever em schema de outro contexto |
| Extensão | `pgcrypto` (para `gen_random_uuid()`), criada no init do postgres-plugins |
| Tabela de controle | `bpmn_modeler.schema_migrations` (checksum SHA-256 por arquivo) |

Justificativa do schema-compartilhado: é o padrão canônico de plugins do monorepo (`transformometro` usa schema próprio dentro de `postgres-plugins`). Ownership é definido por schema + aplicação dona, não por database separado.

### 4.1 Schema físico — `models`

`FROZEN` (DDL de referência normativa — o SQL final da migration deve ser semanticamente equivalente):

```sql
CREATE TABLE bpmn_modeler.models (
    id                  uuid PRIMARY KEY,
    display_name        varchar(120) NOT NULL,
    working_copy_xml    text NOT NULL,
    working_copy_sha256 char(64) NOT NULL,
    version             bigint NOT NULL CHECK (version >= 1),
    created_at          timestamptz NOT NULL,
    created_by          text NOT NULL,
    updated_at          timestamptz NOT NULL,
    updated_by          text NOT NULL,
    archived_at         timestamptz NULL,

    CHECK (btrim(display_name) <> '' AND char_length(display_name) <= 120),
    CHECK (octet_length(working_copy_xml) <= 10485760),
    CHECK (working_copy_sha256 ~ '^[0-9a-f]{64}$')
);

CREATE INDEX idx_bpmn_models_list
    ON bpmn_modeler.models (archived_at, updated_at DESC);
CREATE INDEX idx_bpmn_models_name
    ON bpmn_modeler.models (lower(display_name));
```

Notas:

- `version` começa em `1` na criação (postcondition do Prompt 2) — `DEFAULT` não substitui o envio explícito pela Application.
- `created_by`/`updated_by` = `sub` do JWT (texto opaco; formato é contrato do IdP, não do modelo).
- Não existe `deleted_at`/`deleted` — **hard delete não existe na V1**; lifecycle é archive/unarchive (Prompt 2).
- Índice parcial/nome: `lower(display_name)` suporta a busca por nome de `ListModels`; o índice composto cobre listing por ativo/arquivado + ordenação por atualização.

### 4.2 Schema físico — `revisions`

`FROZEN`:

```sql
CREATE TABLE bpmn_modeler.revisions (
    id               uuid PRIMARY KEY,
    model_id         uuid NOT NULL REFERENCES bpmn_modeler.models(id) ON DELETE RESTRICT,
    revision_number  integer NOT NULL CHECK (revision_number >= 1),
    artifact_xml     text NOT NULL,
    artifact_sha256  char(64) NOT NULL CHECK (artifact_sha256 ~ '^[0-9a-f]{64}$'),
    origin           varchar(16) NOT NULL CHECK (origin IN ('explicit', 'restore')),
    created_at       timestamptz NOT NULL,
    created_by       text NOT NULL,

    CHECK (octet_length(artifact_xml) <= 10485760),
    UNIQUE (model_id, revision_number)
);

CREATE INDEX idx_bpmn_revisions_model
    ON bpmn_modeler.revisions (model_id, revision_number DESC);
```

Notas:

- `UNIQUE(model_id, revision_number)` é a garantia física de ordering monotônico por model.
- Revisions são **append-only**: `UPDATE`/`DELETE` em `revisions` são proibidos por contrato de aplicação (não há use case que os emita). `ON DELETE RESTRICT` é redundância de segurança — nunca deve disparar na V1.
- `origin` tem exatamente dois valores na V1: `explicit` (UC-REV-003) e `restore` (UC-REV-004 cria revisão de efeito).

### 4.3 Artifact storage — decisão e rationale

`FROZEN`: XML BPMN persistido como **`text` UTF-8** (canonical artifact do Prompt 3), não como tipo `xml` do Postgres.

Rationale:

- O artefato canônico deve ser preservado byte-a-byte (round-trip garantido, Prompt 3). O tipo `xml` do Postgres pode normalizar whitespace/encoding e violar `checksum(read) == sha256(input)`.
- `sha256` das colunas de checksum é computado em **Application** (stdlib) sobre o artefato canônico exato — o banco apenas armazena e verifica formato via `CHECK`.
- Limite físico `octet_length <= 10485760` espelha `MAX_CANONICAL_UTF8_BYTES` (§7) — defesa em profundidade, não substitui a rejeição na entrada.

### 4.4 IDs

`FROZEN`:

- `models.id` e `revisions.id`: `uuid`, gerados **server-side** via `IdGeneratorPort` (Prompt 2) → `gen_random_uuid()` do `pgcrypto` ou UUID4 stdlib — a Application injeta o valor; o adapter não usa `DEFAULT gen_random_uuid()` como fonte primária para manter testes determinísticos.
- `revision_number`: `integer` sequencial por model, calculado como `MAX(revision_number)+1` dentro da transação com lock de linha no agregado (ver §5).

### 4.5 Concorrência — CAS físico

`FROZEN`: optimistic concurrency via coluna `version` com compare-and-swap no UPDATE:

```sql
UPDATE bpmn_modeler.models
   SET <colunas_mutadas>, version = version + 1, updated_at = :now, updated_by = :actor
 WHERE id = :model_id
   AND version = :expected_version;
```

- `rowcount == 0` → `CONFLICT` (versão stale) ou `MODEL_NOT_FOUND` — o adapter distingue com um `SELECT 1 ... WHERE id` subsequente quando necessário.
- Mutations que apendem revision (`CreateRevision`, `RestoreRevision`) fazem `SELECT ... FOR UPDATE` na linha de `models` dentro da mesma transação para serializar `revision_number`.
- `RestoreRevision` = **uma** transação: `FOR UPDATE` na model → replace WC → bump version → append revision (Prompt 2 §25).
- Não existe modo de force overwrite. `expected_version` é obrigatório em todas as mutations sobre agregado existente.
- Isolation level: `READ COMMITTED` (default do Postgres) é suficiente porque a unicidade e o CAS são garantidos por constraints + row locking.

### 4.6 Audit metadata

`FROZEN`:

- `models`: `created_at/created_by/updated_at/updated_by/archived_at` — a arquivação mantém `updated_*` do evento de archive (o actor do archive é `updated_by` da versão em que `archived_at` foi setado).
- `revisions`: `created_at/created_by` — revision é imutável; não há `updated_*`.
- Actor = `sub` do JWT validado (string opaca). Não há tabela de audit log separada na V1 — a trilha de revisões + `updated_*` + logs estruturados de mutations (§9) cobrem o requisito.
- Timestamps: `timestamptz`, gerados por `ClockPort` (Application), não por `now()` do banco — o adapter recebe o valor.

---

## 5. Migrations

`FROZEN` — convenção canônica do monorepo:

| Propriedade | Valor |
|---|---|
| Diretório | `bpmn-modeler/migrations/` |
| Naming | `VNNN__descricao.sql` (ex.: `V001__create_bpmn_modeler_schema.sql`) |
| Executor | runner Python próprio do contexto (`bpmn_modeler` startup/CLI), mesmo padrão de `schema_migrations`+SHA-256 do monorepo |
| Tracking | `bpmn_modeler.schema_migrations` (`version`, `name`, `checksum` SHA-256, `executed_at`) |
| Imutabilidade | arquivo aplicado nunca é editado — checksum divergente = falha (`migrations-immutable-checksum.mdc`) |
| Startup | `BPMN_MODELER_RUN_MIGRATIONS_ON_STARTUP` (default `false`); quando `true`, migrations rodam no boot e abortam o start em falha |
| Produção | apenas `up`; nunca reset destrutivo (`plugins-migrations-no-reset-prod.mdc`) |
| Migrations da V1 | `V001` (schema + extensão), `V002` (tabelas + constraints + índices). XSD bundle **não** é migration — é artefato de código versionado |

---

## 6. Autenticação

`FROZEN` — Keycloak/OIDC via shared `delpi_auth` (owner transversal: `platform-security-identity-authorization.mdc`):

- **Fluxo:** Authorization Code + PKCE no frontend (Portal já autentica); o MFE propaga o access token Bearer para a API.
- **Validação backend:** `shared/delpi_auth/jwt_validator.py` — assinatura via JWKS (`KEYCLOAK_JWKS_URL`), `iss == KEYCLOAK_ISSUER`, `aud` contém `KEYCLOAK_AUDIENCE`, `exp`/`nbf`, algoritmo assimétrico do JWKS (RS256). Qualquer config ausente → **fail closed** (não inicializa / não valida).
- **Proibido:** aceitar claims de permissão do token como autorização final, `is_admin` do frontend, `superadmin` ad hoc, fail-open quando o Permission Resolver/Core estiver indisponível.
- **Actor identity:** `sub` (ID opaco estável) → `created_by`/`updated_by`; `preferred_username`/`email` apenas para exibição/log sanitizado quando necessário.
- **Autorização efetiva:** permissões resolvidas via Core RBAC / `delpi_auth` (`require_permission`, `require_all_permissions`, `has_permission`) — decisão no handler (decorator) e/ou use case conforme `platform-security-identity-authorization.mdc` modelo A/C.

### 6.1 Permissões exatas

`FROZEN` — três strings, padrão `<plugin>.<verb>`:

```text
bpmn-modeler.view
bpmn-modeler.edit
bpmn-modeler.manage
```

Implicação (configurada no Core RBAC, não em código):

```text
bpmn-modeler.manage  ⊃  bpmn-modeler.edit  ⊃  bpmn-modeler.view
```

- A API exige exatamente a permission code primária do UC via `require_permission`; a implicação é resolvida na atribuição de papéis (Keycloak/Core).
- Onde o UC precisa de duas capacidades (duplicar: MANAGE + VIEW na origem), a Application verifica ambas via `require_all_permissions`/`has_permission` — o backend não assume que `manage` cobre `view` em checagem de recurso cruzado sem garantia de grant.
- Frontend espelha permissões apenas para UX (mostrar/ocultar); nunca é autoridade (decisão herdada do Prompt 4).

### 6.2 AuthZ coverage — 17/17 use cases

`FROZEN` — mapeamento completo (capability do Prompt 2 → permission code):

| UC | Operação | Capability | Permission code | Notas |
|---|---|---|---|---|
| UC-MODEL-001 | CreateModel | EDIT | `bpmn-modeler.edit` | |
| UC-MODEL-002 | ImportModel | EDIT | `bpmn-modeler.edit` | + intake validation (§7) antes do write |
| UC-MODEL-003 | GetModel | VIEW | `bpmn-modeler.view` | |
| UC-MODEL-004 | ListModels | VIEW | `bpmn-modeler.view` | |
| UC-MODEL-005 | RenameModel | MANAGE | `bpmn-modeler.manage` | |
| UC-MODEL-006 | DuplicateModel | MANAGE+VIEW | `bpmn-modeler.manage` **+** `bpmn-modeler.view` | view checada sobre o model de origem |
| UC-MODEL-007 | ArchiveModel | MANAGE | `bpmn-modeler.manage` | |
| UC-MODEL-008 | UnarchiveModel | MANAGE | `bpmn-modeler.manage` | |
| UC-WC-001 | GetWorkingCopy | VIEW | `bpmn-modeler.view` | |
| UC-WC-002 | SaveWorkingCopy | EDIT | `bpmn-modeler.edit` | |
| UC-WC-003 | ExportWorkingCopy | VIEW | `bpmn-modeler.view` | |
| UC-WC-004 | ValidateWorkingCopy | VIEW | `bpmn-modeler.view` | leitura do artefato corrente |
| UC-REV-001 | ListRevisions | VIEW | `bpmn-modeler.view` | |
| UC-REV-002 | GetRevision | VIEW | `bpmn-modeler.view` | |
| UC-REV-003 | CreateRevision | MANAGE | `bpmn-modeler.manage` | |
| UC-REV-004 | RestoreRevision | MANAGE | `bpmn-modeler.manage` | confirmação UX (Prompt 4) |
| UC-REV-005 | ExportRevision | VIEW | `bpmn-modeler.view` | |

Total: **8 VIEW + 3 EDIT + 5 MANAGE + 1 MANAGE+VIEW = 17/17**. Nenhum UC sem permissão; nenhuma rota nova sem mapeamento nesta tabela.

Comportamentos transversais `FROZEN`:

- Token ausente/inválido/expirado → `401` (unauthenticated).
- Token válido sem permissão → `403`/`UNAUTHORIZED_OPERATION` (classe rejection do Prompt 2).
- `MODEL_ARCHIVED`/`CONFLICT`/`NO_CHANGES` seguem a taxonomia de erros do Prompt 2 — AuthZ não as substitui.
- Rotas públicas intencionais: apenas `/health` e `/ready` (§10), explicitamente liberadas pelo auth middleware.

---

## 7. Limites de segurança de entrada

`FROZEN` — valores literais como **constantes de código** (não env vars; evitar enfraquecimento em runtime):

| Constante | Valor | Aplicação |
|---|---|---|
| `MAX_INPUT_BYTES` | `10_485_760` (10 MiB) | bytes originais do upload (`InputSafetyEvidence.original_byte_length`) |
| `MAX_CANONICAL_UTF8_BYTES` | `10_485_760` (10 MiB) | bytes do artefato canônico UTF-8 (`canonical_utf8_byte_length`) |
| `MAX_XML_DEPTH` | `64` | profundidade máxima de elementos |
| `MAX_XML_ELEMENTS` | `100_000` | total de elementos XML no documento |
| `MAX_ATTRIBUTES_PER_ELEMENT` | `128` | por elemento |
| `MAX_TEXT_NODE_BYTES` | `1_048_576` (1 MiB) | valor de texto/atributo individual |
| `ELK_LAYOUT_TIMEOUT_MS` | `30_000` | timeout do worker de layout (§12) |
| `DB_STATEMENT_TIMEOUT_MS` | `30_000` | statement_timeout da sessão da aplicação |
| `DB_CONNECT_TIMEOUT_S` | `5` | timeout de conexão (convenção do runner) |

Parser (lxml) — `FROZEN`:

```text
resolve_entities = False
no_network       = True
dtd_validation   = False
load_dtd         = False
huge_tree        = False
```

- Doctype/DTD/external entity → rejeição `INPUT_REJECTED_SECURITY` (classificação Prompt 3), nunca `NON_XML`.
- Os dois limites de tamanho são **independentes**: `original_byte_length` mede o upload bruto; `canonical_utf8_byte_length` mede a string canônica — nunca inferidos um do outro (Prompt 3 §InputSafetyEvidence).
- `InputSafetyEvidence` é produzido **no adapter de intake HTTP** (lê o body raw antes de qualquer decode), entregue à Application junto ao `CanonicalBpmnArtifact`. Contém: `original_byte_length`, `canonical_utf8_byte_length`, `decode` (ok/rejected), `doctype_present`, `external_entity_evidence`, `depth_observed`, `expansion_evidence`.
- `XML_WELL_FORMEDNESS` é avaliável sobre o artefato canônico mesmo com `INPUT_SAFETY=NOT_EVALUATED` por falta de evidência (Prompt 3 corrigido) — mas rejeição de segurança antes da criação do artefato bloqueia o pipeline inteiro.

---

## 8. Validation runtime — XSD bundle

`FROZEN`:

- `lxml==6.1.3` é o único parser/validator XML/XSD do backend.
- Bundle XSD **vendored no repo**: `bpmn-modeler/bpmn_modeler/infrastructure/validation/xsd/` com os XSDs BPMN 2.0 oficiais OMG (paths-fonte `spec/BPMN/20100501/*.xsd`, `spec/BPMN/20100501/DC.xsd`, `spec/BPMN/20100501/DI.xsd`, `semantic.xsd`, `bpmndi.xsd` etc.) + manifest com `sha256` por arquivo.
- `20100501` é permitido **apenas** nos paths dos XSDs-fonte OMG; namespaces XML finais permanecem `.../20100524/...` (Prompt 3).
- **Zero runtime schema download**: nenhum `xsi:schemaLocation` externo, nenhum resolver de rede, `no_network=True` em todo `etree.XMLSchema`/`XMLParser`.
- Bundle carregado uma vez no startup; falha de checksum/carregamento → startup aborta (§10).

---

## 9. Logging, privacidade e observabilidade

`FROZEN` — conformidade com `observability-standards.mdc` e regra de dados sensíveis:

- Framework: `logging` stdlib, `LOG_LEVEL` env (default `INFO`).
- Formato: linha única estruturada (chave=valor/JSON) com `request_id`/`correlation_id`, `actor_sub` (ou hash), `uc_id`, `model_id`/`revision_number` quando aplicável, `outcome`, `latency_ms`, `error_code`, `artifact_sha256`, `artifact_bytes`.
- **Nunca** logar: conteúdo XML do artefato (full XML), tokens/JWT, secrets, body bruto de request, connection string com senha. O artefato é representado apenas por `sha256`+`bytes`.
- Mutations logam `actor_sub`, UC, `expected_version`/`version` resultante, outcome (`success|conflict|no_op|rejected`), `error_code` quando houver.
- Métricas mínimas: contadores por UC/outcome e histograma de latência por operação (`save`, `import`, `restore`, `validate`). Sem tracing distribuído obrigatório na V1; `request_id` propagado em logs é suficiente.
- Redaction obrigatória de segredos conforme `observability-standards.mdc`.

---

## 10. Health, readiness e startup

`FROZEN`:

| Endpoint | Tipo | Comportamento |
|---|---|---|
| `GET /health` | liveness, público | processo vivo; `200` sem dependência de DB |
| `GET /ready` | readiness, público | `SELECT 1` no DB + XSD bundle carregado → `200`/`503` |

- Ambas são rotas públicas intencionais, explicitamente liberadas pelo `auth_middleware` (contrato de `platform-security-identity-authorization.mdc`).
- **Startup validation (fail-closed):** presença de `KEYCLOAK_JWKS_URL`, `KEYCLOAK_ISSUER`, `KEYCLOAK_AUDIENCE`, `PLUGINS_DB_*`; carregamento do XSD bundle com checksum; se `BPMN_MODELER_RUN_MIGRATIONS_ON_STARTUP=true`, migrations + validação de histórico rodam no boot e abortam em falha.
- `docker-compose` healthcheck: `curl -f http://localhost:8000/health` (padrão do monorepo).

---

## 11. Environment variables — matriz

`FROZEN`:

| Variável | Obrigatória | Secret | Padrão / exemplo |
|---|---|---|---|
| `KEYCLOAK_URL` | sim | não | `http://keycloak:8080/auth` |
| `KEYCLOAK_REALM` | sim | não | `delpi` |
| `KEYCLOAK_JWKS_URL` | sim | não | `.../protocol/openid-connect/certs` |
| `KEYCLOAK_ISSUER` | sim | não | `.../realms/delpi` |
| `KEYCLOAK_AUDIENCE` | sim | não | audience do client da API |
| `PLUGINS_DB_HOST` | sim | não | `postgres-plugins` |
| `PLUGINS_DB_PORT` | sim | não | `5432` |
| `PLUGINS_DB_NAME` | sim | não | `plugins` |
| `PLUGINS_DB_USER` | sim | **secret** | role compartilhada de plugins |
| `PLUGINS_DB_PASSWORD` | sim | **secret** | via env/secret store — nunca versionado |
| `BPMN_MODELER_ROOT_PATH` | sim | não | `/apps/bpmn-modeler-api` |
| `BPMN_MODELER_RUN_MIGRATIONS_ON_STARTUP` | não | não | `false` |
| `LOG_LEVEL` | não | não | `INFO` |

- Nenhuma variável controla limites de segurança (§7), namespaces BPMN ou permission codes — são constantes de código/contrato.
- `env.*.example` documenta placeholders, nunca valores reais.

---

## 12. ELK worker — packaging e política de falha

`FROZEN` (complementa Prompt 5, que delegou os limites operacionais):

- **Packaging:** `elkjs` em Web Worker dedicado; o bundle do MFE inclui `elk-worker.min.js` servido como asset do próprio plugin (mesma origem do bundle MFE, via `worker-src 'self'`).
- **Timeout:** `ELK_LAYOUT_TIMEOUT_MS = 30_000` por execução de layout.
- **Falha:** timeout/erro do worker → aborta a execução, descarta o resultado parcial, restaura o estado anterior de DI, e o layout preview **não** é aplicado; mensagem de erro não bloqueante na UX.
- **Fallback:** **não há** fallback para main-thread — política fail-closed (evita bloquear o editor com layout pesado). O resultado de `Accept` só existe com layout completo no worker.
- Retry de layout é ação explícita do usuário, nunca automático.
- Layout continua sendo operação **somente-DI** (Prompt 5); semântica BPMN nunca é mutada por timeout/falha/retry do worker.

### 12.1 CSP

`FROZEN` — diretivas mínimas que o bundle exige:

```text
default-src 'self';
script-src  'self';
worker-src  'self';
connect-src 'self';
img-src     'self' data:;
style-src   'self' 'unsafe-inline';
```

- `worker-src 'self'` é **mandatório** para o ELK worker.
- `'unsafe-inline'` em `style-src` é aceito pelo CSS inline do bpmn-js/diagram-js; `'unsafe-eval'` é **proibido**.
- `connect-src 'self'` porque a API é same-origin atrás do gateway (`/apps/bpmn-modeler-api`).
- A CSP final é aplicada no gateway/Portal (owner transversal); este freeze define apenas o **mínimo exigido** pelo plugin — relaxar além disso exige decisão transversal.

---

## 13. Docker / Compose

`FROZEN`:

```text
bpmn-modeler-api:
  build: bpmn-modeler/Dockerfile (python:3.11-slim)
  env:   PLUGINS_DB_*, KEYCLOAK_*, BPMN_MODELER_*, LOG_LEVEL
  root:  /apps/bpmn-modeler-api
  port:  8000 (interno)
  deps:  postgres-plugins (healthy)
  healthcheck: curl -f http://localhost:8000/health
```

- Mesma receita dos demais `*-api` do monorepo (`uvicorn` + `--root-path`).
- Gateway nginx recebe location para `/apps/bpmn-modeler-api/` → `bpmn-modeler-api:8000` (Prompt 7 congela o contrato HTTP/OpenAPI exposto; o mount path já está congelado aqui).
- MFE `plugins/bpmn-modeler` segue o pipeline padrão de plugin (build Vite + federation, servido como estático via Portal/gateway).

---

## 14. Backup / Recovery

`FROZEN` — expectativa operacional:

- Persistência em `postgres-plugins` → coberto pela política de backup do serviço compartilhado da plataforma (snapshot/volume do `postgres_plugins_data`); **não** há backup separado por plugin na V1.
- Revisions append-only + `sha256` permitem verificação de integridade em restore (checksum de cada artefato relido).
- RPO/RTO: herdados da infra compartilhada — este contexto não define números próprios na V1.
- Recuperação: migrations são forward-only e idempotentes via `schema_migrations`; reconstrução = deploy + migrations aplicadas.

---

## 15. CI — contrato

`FROZEN` — o contexto BPMN Modeler passa pelos gates canônicos do monorepo + gates específicos:

| Gate | Ferramenta | Bloqueia |
|---|---|---|
| Backend unit/integration | `pytest` (Python 3.11) | sim |
| Architecture enforcement | `.github/workflows/architecture-enforcement.yml` existente | sim |
| Migrations | checksum/immutability + dry-run em banco vazio | sim |
| Offline XSD validation | teste que carrega o bundle sem rede (`no_network`) | sim |
| Frontend build | `npm ci` + `vite build` (worker asset presente) | sim |
| Lock integrity | `package-lock.json` + `npm ci` sem resolução de ranges | sim |
| Secret scan | gate canônico do repo (secrets literals/logs) | sim |
| License scan | allowlist §3.1 | sim |
| Workflow dedicado | `.github/workflows/bpmn-modeler-api.yml` (padrão `*-api-routes.yml`) | sim |

- Nenhum teste pode depender de rede externa para XSD/schema — a validação offline é testada explicitamente.
- Nenhum gate existente pode ser enfraquecido para acomodar a implementação (`architecture-ci-enforcement.mdc`).

---

## 16. Supply chain e licenças

`FROZEN`:

- Todas as dependências pinadas em versão exata (backend `requirements.txt`, frontend `package.json`+`package-lock.json`).
- Ranges `latest`, `*`, `>=` solto proibidos em dependências de produção.
- Allowlist de licenças: `MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC`, `EPL-2.0`. `elkjs` consumido sob `EPL-2.0`. Qualquer licença fora da lista exige aprovação antes do merge.
- Dependências transitivas são travadas via lockfile; CVE conhecido em pin exige bump revisado, não silenciamento.

---

## 17. Proibições explícitas

`FROZEN` — sem exceção na V1:

- ❌ persistir `flowchart_v1`/visual JSON/moddle JSON como modelo — XML BPMN é o único artefato canônico.
- ❌ banco/schema do Transformômetro ou qualquer outro contexto.
- ❌ endpoint genérico de SQL/proxy (`/query`, `/exec`) ou ORM genérico para o modelo.
- ❌ log de XML completo, tokens, secrets ou body bruto.
- ❌ force overwrite / ignorar `expected_version`.
- ❌ hard delete (V1 não tem delete; archive/unarchive apenas).
- ❌ runtime schema download / resolver de rede no parser.
- ❌ fallback main-thread do ELK worker.
- ❌ autorização por ocultação de UI; AuthZ é backend-first.
- ❌ reimplementar jwt/JWKS/permissions quando `shared/delpi_auth` provê a primitiva.
- ❌ dependência de produção com range flutuante.
- ❌ alterar migrations aplicadas.

---

## 18. Residual review — achados

`FROZEN` — executado sobre os 6 documentos do contexto:

| Busca | Resultado | Ação |
|---|---|---|
| `TODO`/`TBD`/`a decidir`/`talvez`/`maybe` | nenhum remanescente em decisão crítica | ok |
| `latest`/`*.x`/`version TBD`/`permission TBD`/`schema TBD`/`limit TBD`/`worker fallback TBD` | nenhum | ok |
| `Transformômetro DB` | referências legadas apenas como **proibição** (correto) | ok |
| `visual JSON`/`moddle JSON persistence` | apenas como proibição | ok |
| `generic SQL`/`generic proxy` | apenas como proibição | ok |
| `full XML log`/`force overwrite`/`hard delete`/`runtime schema download` | apenas como proibição | ok |

---

## 19. Delegado ao Prompt 7

`FROZEN` — único escopo restante (não abre nada do que este documento fechou):

- contrato HTTP/OpenAPI (paths, DTOs, códigos de erro, paginação);
- E2E e acceptance criteria executáveis;
- benchmark/timeout numérico de layout por tamanho de modelo (performance, não segurança);
- freeze final de documentação e integração do pacote.

---

## 20. Status

```text
BPMN / SECURITY / PERSISTENCE / RUNTIME SPEC STATUS: FROZEN
```

Todas as decisões de runtime, segurança, persistência física, versões, limites numéricos, autenticação, autorização (17/17 use cases mapeados), deploy, migrações e CI estão fechadas. Nenhuma decisão crítica resta aberta para o implementador.
