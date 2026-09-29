# BPMN Modeler — Security / Persistence / Runtime Spec Freeze (Prompt 6/7)

> **Status:** `FROZEN` (corrigido pelo Corrective Gate de Prompt 6 — database isolation, least privilege, dependency lock e contratos de runtime ausentes)
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
| `postgres-plugins` | PostgreSQL **server** compartilhado | serviço Docker `postgres-plugins` | PostgreSQL 15 |
| `bpmn_modeler` (database) | **Logical database dedicado** dentro de `postgres-plugins` | provisionado pelo bootstrap de infra | ver §4 |
| gateway | nginx | `gateway/` | rotas `/apps/bpmn-modeler-api/*` |

Regras de fronteira:

- O backend é o **único dono** do database `bpmn_modeler` e de todo dado persistente do contexto.
- O MFE comunica-se apenas via HTTP com `bpmn-modeler` API — nunca acesso direto a banco, nunca reutilização de API de outro contexto como atalho.
- **Nenhuma** dependência de banco do Transformômetro ou de qualquer plugin (`plugins` database, `transformometro` schema). `flowchart_v1` é conceito legado do Transformômetro e não é modelo de persistência BPMN.
- Não existe endpoint de layout no backend: layout é 100% frontend via Web Worker (Prompt 5).

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

`FROZEN` — pins literais em `bpmn-modeler/requirements.txt` (sem ranges flutuantes; deps fora deste catálogo são proibidos sem nova decisão):

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

`psycopg-pool` **não** é dependência: o pool é o padrão de pool limitado in-process já comprovado no monorepo sobre psycopg3 puro (§15).

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
| Testing | `vitest` + `@testing-library/react` (versões do kit plugins) | convenção |

### 3.1 Dependency compatibility matrix — locks exatos (prova por resolução real)

`FROZEN` — conjunto provado com `npm install --package-lock-only` (npm 10.8.2, Node 20) em scratch isolado, **sem** `--force` e **sem** `--legacy-peer-deps`. `PEER DEPENDENCY STATUS: PASS`.

| Pacote | Versão exata | Direct/Transitive | Peer requirements (registry) | Licença | Result |
|---|---|---|---|---|---|
| `bpmn-js` | `18.30.1` | direct | — | **bpmn.io License** (`SEE LICENSE IN LICENSE`) | resolvido |
| `bpmn-moddle` | `10.3.1` | direct | — | MIT | resolvido — deduplica com o `bpmn-moddle@10.3.1` transitivo de `bpmn-js` (cópia única no graph) |
| `bpmn-js-properties-panel` | `5.65.1` | direct | `bpmn-js >= 11.5`, `diagram-js >= 11.9`, `@bpmn-io/properties-panel >= 3.42.0`, `camunda-bpmn-js-behaviors >= 0.4` | MIT | resolvido — `3.55.0` satisfaz `>= 3.42.0` |
| `@bpmn-io/properties-panel` | `3.55.0` | direct | — | MIT | resolvido |
| `elkjs` | `0.12.0` | direct | — | EPL-2.0 OR GPL-3.0-or-later → **EPL-2.0** | resolvido |
| `diagram-js` | `15.27.1` | transitive (via `bpmn-js`/`bpmn-js-properties-panel`) | — | MIT | resolvido — satisfaz `>= 11.9` |
| `camunda-bpmn-js-behaviors` | `1.18.0` | transitive (peer auto-instalado) | — | MIT | resolvido — satisfaz `>= 0.4` |

Regras:

- Versões pinadas exatas em `plugins/bpmn-modeler/package.json` (sem `^`, `~`, `latest`) para os 5 pacotes direct; transitivas travadas pelo `package-lock.json`.
- `package-lock.json` obrigatório e verificado em CI via `npm ci`.
- Nenhum `--force`/`--legacy-peer-deps` em qualquer pipeline — o conjunto congelado resolve nativamente.

### 3.2 License matrix

`FROZEN` — classificação corrigida:

| Pacote | Licença | Obrigação material |
|---|---|---|
| `bpmn-js` | **bpmn.io License** (source-available custom; **não é MIT**) | watermark "Powered by bpmn.io" **visível e inalterado** — proibido remover, ocultar, estilizar ou cobrir por overlay (Prompt 4 §properties panel/banner deve respeitar) |
| `bpmn-moddle` | MIT | notice retido |
| `bpmn-js-properties-panel` | MIT | notice retido |
| `@bpmn-io/properties-panel` | MIT | notice retido |
| `diagram-js` (transitivo) | MIT | notice retido |
| `elkjs` | EPL-2.0 OR GPL-3.0-or-later | consumido **somente** sob `EPL-2.0`; EPL-2.0 notice retido conforme exigido |

### 3.3 Third-party notices

`FROZEN`:

- O plugin deve criar `plugins/bpmn-modeler/THIRD_PARTY_NOTICES.md` listando pacote, versão exata, licença e obrigações (artefato exigido na implementação — o repo não possui processo transversal de notices).
- Watermark bpmn.io visível em todo uso do editor/viewer — teste de UI deve evidenciá-lo.
- Licenças de produção permitidas: `MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC`, `EPL-2.0`, `bpmn.io License` (exclusiva para pacotes bpmn.io desta stack). Fora disso: aprovação antes do uso.

---

## 4. Database — isolation, ownership e roles

`FROZEN` — direção arquitetural: **shared server ≠ shared database**.

| Propriedade | Valor |
|---|---|
| PostgreSQL server | `postgres-plugins` (mesmo servidor físico da plataforma — aceitável) |
| **Logical database** | **`bpmn_modeler`** — dedicado, autoridade exclusiva do BPMN Modeler |
| Schema | `public` (database dedicado não precisa de schema-per-context; hierarquia duplicada de isolamento é proibida) |
| `search_path` | `public` (setado explicitamente na sessão — ver §15) |
| Extensões | **nenhuma** — `pgcrypto` **NOT_REQUIRED** (§8) |
| Runtime role | `bpmn_modeler_app` — least privilege (§4.2) |
| Migration role | `bpmn_modeler_admin` — owner do database, executa migrations (§4.2) |
| Bootstrap | superuser da plataforma (`POSTGRES_USER`) via init script de infra cria database + roles + grants — contrato de provisionamento; **não** é runtime nem migration role |

Justificativa: `${PLUGINS_DB_NAME}` como database compartilhado violaria "nunca compartilhar banco". O padrão de naming dedicado `<CTX>_DB_*` já existe no monorepo (`PORTAL_RH_DB_*`).

### 4.1 Cross-context DB coupling

`FROZEN`:

- O database `bpmn_modeler` **não tem FK** para Transformômetro nem para qualquer outro contexto.
- `bpmn_modeler_app` **não possui** grants em `plugins`, `core`, Transformômetro ou qualquer outro database/schema.
- `transformometro` runtime role **não possui** grants no database `bpmn_modeler`.
- Integração futura entre contextos: **somente** via API/contrato explícito — nunca SQL cross-database.
- `BPMN Modeler DB ≠ Transformômetro DB ≠ plugins DB`, mesmo coexistindo no mesmo PostgreSQL server.

### 4.2 Grants — capability matrix

`FROZEN`:

| Capability | Runtime `bpmn_modeler_app` | Migration `bpmn_modeler_admin` |
|---|---|---|
| CONNECT (`bpmn_modeler`) | ✅ | ✅ |
| SELECT `models`, `revisions` | ✅ | ✅ |
| INSERT `models`, `revisions` | ✅ | ✅ (migrations/seed se necessário) |
| UPDATE `models` | ✅ | ✅ |
| UPDATE `revisions` | ❌ (append-only) | ✅ (owner técnico, não usado em runtime) |
| DELETE (qualquer tabela) | ❌ | ❌ em runtime; ✅ técnico do owner, **não usado** — V1 não tem delete |
| SELECT/INSERT/UPDATE/DELETE `schema_migrations` | ❌ | ✅ |
| CREATE TABLE / CREATE INDEX / ALTER / DROP | ❌ | ✅ (database owner) |
| CREATE EXTENSION | ❌ | ❌ (nenhuma extensão exigida) |
| CREATE SCHEMA | ❌ | ❌ (usa `public`) |
| SUPERUSER / CREATEDB / CREATEROLE | ❌ | ❌ (CREATEDB não é necessário — database já provisionado pelo bootstrap) |
| Grants em outros databases/schemas | ❌ | ❌ |

Bootstrap (superuser) executa, em init script de infra:

```sql
CREATE ROLE bpmn_modeler_app LOGIN PASSWORD '<secret>';
CREATE ROLE bpmn_modeler_admin LOGIN PASSWORD '<secret>';
CREATE DATABASE bpmn_modeler OWNER bpmn_modeler_admin;
-- no database bpmn_modeler:
GRANT CONNECT ON DATABASE bpmn_modeler TO bpmn_modeler_app;
GRANT USAGE ON SCHEMA public TO bpmn_modeler_app;
```

Grants por objeto são aplicados **pela migration que cria o objeto** (executada por `bpmn_modeler_admin` — §22), nunca por `ALTER DEFAULT PRIVILEGES` amplo. `FROZEN` — concessões exatas da V1:

```sql
-- aplicadas pela migration que cria as tabelas (role: bpmn_modeler_admin)
GRANT SELECT, INSERT, UPDATE ON TABLE public.models    TO bpmn_modeler_app;
GRANT SELECT, INSERT         ON TABLE public.revisions TO bpmn_modeler_app;
```

Denials explícitos do runtime role:

```text
NO UPDATE  ON revisions
NO DELETE  ON models
NO DELETE  ON revisions
NO grants  ON schema_migrations
NO DDL     (CREATE/ALTER/DROP em qualquer objeto)
```

**`ALTER DEFAULT PRIVILEGES ... GRANT SELECT, INSERT, UPDATE ON TABLES` é proibido na V1** — `future table ≠ automatically authorized runtime resource`; cada migration que criar objeto concede explicitamente apenas os privileges necessários daquele objeto (least privilege opt-in por objeto).

O DDL acima é **contrato normativo** — o script init real deve ser semanticamente equivalente. `REVOKE CREATE ON SCHEMA public FROM PUBLIC` é default em PG15 e permanece.

### 4.3 Schema físico — `models`

`FROZEN` (DDL de referência normativa, objetos em `public`):

```sql
CREATE TABLE public.models (
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

CREATE INDEX idx_models_list
    ON public.models (archived_at, updated_at DESC);
CREATE INDEX idx_models_name_lower
    ON public.models (lower(display_name));
```

- `version` começa em `1` na criação — valor enviado explicitamente pela Application (postcondition Prompt 2).
- `created_by`/`updated_by` = `sub` do JWT (texto opaco).
- Sem `deleted_at`/`deleted` — **hard delete não existe na V1**.
- `idx_models_name_lower` acelera `ORDER BY lower(display_name)` e busca exata por `lower(display_name) = lower(:q)`; **não** acelera `%contains%` (ver §5).

### 4.4 Schema físico — `revisions`

`FROZEN`:

```sql
CREATE TABLE public.revisions (
    id               uuid PRIMARY KEY,
    model_id         uuid NOT NULL REFERENCES public.models(id) ON DELETE RESTRICT,
    revision_number  integer NOT NULL CHECK (revision_number >= 1),
    artifact_xml     text NOT NULL,
    artifact_sha256  char(64) NOT NULL CHECK (artifact_sha256 ~ '^[0-9a-f]{64}$'),
    origin           varchar(16) NOT NULL CHECK (origin IN ('explicit', 'restore')),
    created_at       timestamptz NOT NULL,
    created_by       text NOT NULL,

    CHECK (octet_length(artifact_xml) <= 10485760),
    UNIQUE (model_id, revision_number)
);

CREATE INDEX idx_revisions_model
    ON public.revisions (model_id, revision_number DESC);
```

- `UNIQUE(model_id, revision_number)` = ordenação monotônica física por model.
- Append-only: `UPDATE`/`DELETE` proibidos por contrato (runtime role sequer recebe esses grants — ver §4.2).
- `origin` ∈ `{explicit, restore}` (UC-REV-003 / UC-REV-004).
- `ON DELETE RESTRICT` é redundância de segurança — nunca dispara na V1 (não há delete).

### 4.5 Artifact storage — decisão e rationale

`FROZEN`: XML BPMN persistido como **`text` UTF-8** (canonical artifact do Prompt 3), não como tipo `xml`.

- O tipo `xml` do Postgres pode normalizar whitespace/encoding e violar `checksum(read) == sha256(input)` — round-trip byte-exato exige `text`.
- `sha256` é computado em Application (stdlib) sobre o artefato canônico; banco verifica apenas formato via `CHECK`.
- `octet_length <= 10485760` espelha `MAX_CANONICAL_UTF8_BYTES` (§7) — defesa em profundidade.

---

## 5. Search e pagination — contrato físico

`FROZEN` — fecha o "how" deixado pelo Prompt 2:

### 5.1 Contains search (display_name)

```sql
WHERE lower(display_name) LIKE '%' || lower(:query) || '%'
```

- `:query` **parametrizado** via psycopg — escape de `%`/`_`/`\\` feito na camada de repository (`ESCAPE '\'`), nunca por concatenação.
- **Estratégia V1:** `LIKE %...%` com scan sequencial aceito — o volume inicial de models por catálogo não justifica `pg_trgm`. Registrado explicitamente: `contains search may use sequential scan in V1`; o btree `idx_models_name_lower` **não** é fingido como acelerador de contains (serve ao sort por nome, §4.3).
- `pg_trgm` **não** será introduzido sem requirement/evidência de volume — criar extensão por hábito é proibido.

### 5.2 Search by id

- Application tenta `UUID(query)`; se parse ok → `id = :uuid_param` combinado (OR) com o contains conforme contrato de `ListModels`.
- Parse falho → apenas contains por display_name. **Nenhum cast no SQL** que gere erro para query textual — o branch é decidido em código, ambos parametrizados.

### 5.3 Filtro `archived`

```text
active (default)  → archived_at IS NULL
archived          → archived_at IS NOT NULL
all               → sem filtro
```

### 5.4 Pagination ownership

`FROZEN`: **mecanismo físico de paginação = `DELEGATED_TO_PROMPT_7`** junto ao wire contract. Prompt 7 escolhe `cursor` vs `offset` e produz a query/index compatibility correspondente. Prompt 7 **está autorizado** a adicionar **somente** o índice estritamente necessário à escolha (ex.: cursor por `updated_at, id`), sem reabrir o restante da persistência. Sem paginação ilimitada — o mecanismo escolhido deve ter `LIMIT`/bound explícito.

### 5.5 Sort allowlist

`FROZEN` — `ORDER BY` é mapping de allowlist, nunca string do cliente:

| Sort key (contrato) | SQL |
|---|---|
| `updated_at` (default, desc) | `ORDER BY updated_at DESC, id DESC` |
| `created_at` | `ORDER BY created_at DESC, id DESC` |
| `display_name` | `ORDER BY lower(display_name), id` |

`id` como tie-breaker garante ordenação estável para qualquer mecanismo de paginação.

---

## 6. SQL injection — controles

`FROZEN`:

- Todos os valores passam por bind parameters do psycopg (`%s`/named) — concatenação de input em SQL **proibida** em qualquer camada.
- Identificadores fixos (tabela/coluna) são literais do código do repository — nunca derivados de request.
- `ORDER BY`/`filter`/`sort` resolvidos por allowlist mapping (§5.5) — `ORDER BY <raw client string>` proibido.
- `LIMIT`/paginação: parâmetros tipados int, nunca interpolados.
- Gate CI: revisão estática sobre `execute(`/cursor usage no contexto (mesma família de gates arquiteturais do monorepo).

---

## 7. Limites de segurança de entrada

`FROZEN` — constantes de código (não env vars):

| Constante | Valor | Aplicação |
|---|---|---|
| `MAX_INPUT_BYTES` | `10_485_760` (10 MiB) | bytes originais do upload (`original_byte_length`) |
| `MAX_CANONICAL_UTF8_BYTES` | `10_485_760` (10 MiB) | bytes do artefato canônico (`canonical_utf8_byte_length`) |
| `MAX_XML_DEPTH` | `64` | profundidade de elementos |
| `MAX_XML_ELEMENTS` | `100_000` | total de elementos |
| `MAX_ATTRIBUTES_PER_ELEMENT` | `128` | por elemento |
| `MAX_TEXT_NODE_BYTES` | `1_048_576` | texto/atributo individual |
| `ELK_LAYOUT_TIMEOUT_MS` | `30_000` | timeout do worker de layout |
| `DB_STATEMENT_TIMEOUT_MS` | `30_000` | aplicado na sessão via `options` (§15) |
| `DB_CONNECT_TIMEOUT_S` | `5` | `connect_timeout` na DSN |

Parser (lxml) — `FROZEN`:

```text
resolve_entities = False
no_network       = True
dtd_validation   = False
load_dtd         = False
huge_tree        = False
```

- Doctype/DTD/external entity → `INPUT_REJECTED_SECURITY` (nunca `NON_XML`).
- Os dois limites de tamanho são independentes — nunca inferidos um do outro (Prompt 3 `InputSafetyEvidence`).
- `InputSafetyEvidence` é produzido **no adapter de intake HTTP** (lê body raw antes de decode): `original_byte_length`, `canonical_utf8_byte_length`, `decode`, `doctype_present`, `external_entity_evidence`, `depth_observed`, `expansion_evidence`.
- `XML_WELL_FORMEDNESS` avaliável mesmo com `INPUT_SAFETY=NOT_EVALUATED` por falta de evidência; rejeição de segurança antes do artefato bloqueia o pipeline.

---

## 8. IDs e geração de identidade

`FROZEN` — **uma única estratégia**:

- `ModelId`, `RevisionId` = **UUIDv4 gerados por `uuid.uuid4()` (Python stdlib)** atrás de `IdGeneratorPort`, produzidos pela Application **antes** do repository write.
- `DEFAULT gen_random_uuid()` **não é usado** como autoridade — a PK não tem default de geração; o valor chega do use case (testes determinísticos por injeção).
- **`pgcrypto`: NOT_REQUIRED** — existia apenas para `gen_random_uuid()`; sem outro requirement comprovado, a extensão **não** é criada no database `bpmn_modeler`.
- `revision_number`: `MAX(revision_number)+1` dentro da transação com `FOR UPDATE` na linha do agregado (§9).

---

## 9. Transaction matrix — todas as mutations

`FROZEN` — `READ COMMITTED`; CAS físico = `UPDATE ... WHERE id=:id AND version=:expected_version`; rowcount `0` → authoritative existence check (`SELECT 1 FROM models WHERE id=:id` na mesma tx): existe → `CONFLICT`; não existe → `MODEL_NOT_FOUND`. Como V1 não tem delete, `rowcount=0` + row existe ⇒ conclusivamente stale version (não há race que transforme inexistência em falso CONFLICT).

| Use case | Tables | Lock/CAS | Atomic write | Read-back |
|---|---|---|---|---|
| CreateModel | `models` | n/a (id novo) | 1 INSERT (version=1, WC blank) | SELECT id: nome/version=1/artefato presente |
| ImportModel | `models` | n/a | 1 INSERT (version=1, artefato exato) | checksum == sha256(input) |
| RenameModel | `models` | CAS version | UPDATE display_name, version+1, updated_* | nome == input, version+1 |
| DuplicateModel | `models` (novo) | n/a (id novo; read da origem sem lock) | 1 INSERT com WC da origem | checksum(novo) == checksum(origem) |
| ArchiveModel | `models` | CAS version | UPDATE archived_at=now, version+1 | archived_at set |
| UnarchiveModel | `models` | CAS version | UPDATE archived_at=null, version+1 | archived_at null |
| SaveWorkingCopy | `models` | CAS version | UPDATE wc_xml+sha256, version+1, updated_* | checksum == sha256(input), version+1 |
| CreateRevision | `models` + `revisions` | `SELECT ... FOR UPDATE` em `models` + CAS | UPDATE version+1 **+** INSERT revision (1 tx) | revisão relida íntegra: artefato == WC snapshot, number esperado |
| RestoreRevision | `models` + `revisions` | `FOR UPDATE` em `models` + CAS | UPDATE wc_xml+sha256+version+1 **+** INSERT revision origin=restore (1 tx) | checksum(WC) == checksum(revisão N); nova revisão existe |

- `FOR UPDATE` na linha de `models` serializa `revision_number` e elimina races de append concorrente.
- Nenhuma mutation cruza dois agregados na mesma transação de escrita (duplicate só escreve o novo — Prompt 2 §25).
- Idempotência de transporte = `DELEGATED_TO_PROMPT_7`; semanticamente `expected_version`+`NO_OP_SUCCESS` já dão proteção (Prompt 2 §29).

---

## 10. Autenticação e autorização

`FROZEN` — Keycloak/OIDC via shared `delpi_auth`:

- Fluxo: Authorization Code + PKCE no frontend (Portal autentica); MFE propaga Bearer token para a API.
- Validação backend: `shared/delpi_auth/jwt_validator.py` — assinatura via JWKS (`KEYCLOAK_JWKS_URL`), `iss == KEYCLOAK_ISSUER`, `aud` contém `KEYCLOAK_AUDIENCE`, `exp`/`nbf`, RS256. Config ausente → **fail closed**.
- Proibido: claims de permissão do token como autorização final, `is_admin` do frontend, `superadmin` ad hoc, fail-open com Permission Resolver indisponível.
- Actor identity: `sub` → `created_by`/`updated_by`/audit; `preferred_username`/`email` apenas para exibição sanitizada.
- Autorização efetiva: Core RBAC via `delpi_auth` (`require_permission`, `require_all_permissions`, `has_permission`) — modelo A/C de `platform-security-identity-authorization.mdc`.

### 10.1 Permissões exatas

`FROZEN` — três strings, padrão `<plugin>.<verb>`:

```text
bpmn-modeler.view
bpmn-modeler.edit
bpmn-modeler.manage
```

Implicação (no Core RBAC, não em código): `manage ⊃ edit ⊃ view`. UC-006 exige checagem explícita das duas (`manage` + `view` na origem) — a API não assume cobertura implícita em recurso cruzado.

### 10.2 AuthZ coverage — 17/17 use cases

| UC | Operação | Permission code |
|---|---|---|
| UC-MODEL-001 | CreateModel | `bpmn-modeler.edit` |
| UC-MODEL-002 | ImportModel | `bpmn-modeler.edit` |
| UC-MODEL-003 | GetModel | `bpmn-modeler.view` |
| UC-MODEL-004 | ListModels | `bpmn-modeler.view` |
| UC-MODEL-005 | RenameModel | `bpmn-modeler.manage` |
| UC-MODEL-006 | DuplicateModel | `bpmn-modeler.manage` **+** `bpmn-modeler.view` (origem) |
| UC-MODEL-007 | ArchiveModel | `bpmn-modeler.manage` |
| UC-MODEL-008 | UnarchiveModel | `bpmn-modeler.manage` |
| UC-WC-001 | GetWorkingCopy | `bpmn-modeler.view` |
| UC-WC-002 | SaveWorkingCopy | `bpmn-modeler.edit` |
| UC-WC-003 | ExportWorkingCopy | `bpmn-modeler.view` |
| UC-WC-004 | ValidateWorkingCopy | `bpmn-modeler.view` |
| UC-REV-001 | ListRevisions | `bpmn-modeler.view` |
| UC-REV-002 | GetRevision | `bpmn-modeler.view` |
| UC-REV-003 | CreateRevision | `bpmn-modeler.manage` |
| UC-REV-004 | RestoreRevision | `bpmn-modeler.manage` |
| UC-REV-005 | ExportRevision | `bpmn-modeler.view` |

Total: 8 VIEW + 3 EDIT + 5 MANAGE + 1 MANAGE+VIEW = **17/17**. Transversal: token ausente/inválido → `401`; sem permissão → `403`/`UNAUTHORIZED_OPERATION`; `/health` e `/ready` são as únicas rotas públicas intencionais (§16).

---

## 11. Resource ownership matrix

`FROZEN` — autoridade por recurso (anti-drift de implementação):

| Resource | Owner | Authority |
|---|---|---|
| identity | Keycloak | authentication |
| RBAC / permissões efetivas | Core API | permissions |
| canonical BPMN artifact | BPMN Modeler | XML + DI (único modelo persistido) |
| BPMN Modeler DB | BPMN Modeler | persistence — database `bpmn_modeler` dedicado |
| revisions | BPMN Modeler | immutable history |
| validation | BPMN Modeler | evidence (rules/catalog do Prompt 3) |
| layout proposal | BPMN Modeler frontend | derived only — nunca autoridade semântica |
| Transformômetro process/data | Transformômetro | external context — acesso só via contrato API |
| plugins DB / outros contextos | respectivos owners | fora de alcance do `bpmn_modeler_app` |

---

## 12. Threat model

`FROZEN`:

| # | Threat | Control | Owner | Verification |
|---|---|---|---|---|
| T01 | unauthorized read | `require_permission(view)` em todo read | backend | negative test 401/403 |
| T02 | unauthorized write | `require_permission(edit/manage)` + AuthZ no use case | backend | negative test por UC |
| T03 | unauthorized arbitrary model-id access | permissão `bpmn-modeler.*` context-wide exigida **antes** de resolver/retornar dado do recurso; **V1 authorization scope = catalog/context-wide — sem per-model ACL** (per-model ACL = `OUT_OF_V1`/`FUTURE`) | backend | principal sem `bpmn-modeler.view` + model id válido arbitrário → `403`; principal com `bpmn-modeler.view` pode ler qualquer model do escopo catálogo V1 |
| T04 | stale write | CAS `version` + `expected_version` obrigatório | backend | teste de CONFLICT |
| T05 | SQL injection | bind parameters + allowlist sort + nenhuma concatenação | backend | static gate + teste com payload malicioso |
| T06 | XXE | `resolve_entities=False`, doctype/DTD → `INPUT_REJECTED_SECURITY` | intake/validation | fixture FX-SEC-* (P3) |
| T07 | DTD/entity expansion | `load_dtd=False`, `expansion_evidence`, limites de elemento/texto | validation | fixture expansion |
| T08 | oversized upload | `MAX_INPUT_BYTES` medido no raw body antes de decode | intake | teste >10 MiB |
| T09 | XML resource exhaustion | `MAX_XML_DEPTH/ELEMENTS/ATTRS/TEXT_NODE` + `huge_tree=False` + `statement_timeout` | validation+DB | teste de profundidade/fan-out |
| T10 | malformed XML | `XML_WELL_FORMEDNESS` stage → classificação `MALFORMED_XML` (texto XML + parse tentado + well-formedness failure). `NON_XML` é restrito a input que não produz texto XML utilizável (binário/não-decodável/sem XML text) — estados distintos do Prompt 3 | validation | fixture FX-BADXML-* (P3) |
| T11 | stored script-like BPMN text | BPMN names/documentation = texto não confiável; escape as text; `dangerouslySetInnerHTML` proibido; vendor renderiza labels como SVG text | frontend | teste com `<script>`/`on*` em nome; evidence de render como texto |
| T12 | log leakage | somente metadata segura; nunca XML/token/body; redaction | backend | scan de logs em teste |
| T13 | token leakage | Bearer não persistido/logado; `sub` opaco em audit | full stack | redaction gate |
| T14 | cross-context DB access | database dedicado + role sem grants externos + nenhuma FK cross-context | DB | teste de conexão negando outra base; revisão de grants |
| T15 | worker/CSP abuse | `worker-src 'self'`, sem `unsafe-eval`, worker timeout, sem fallback main-thread | frontend+gateway | CSP header test + timeout test |
| T16 | dependency compromise | pins exatos + lockfiles + license allowlist + provenance (npm/PyPI) | supply chain | `npm ci` + pip pin check + scan |
| T17 | artifact corruption | `sha256` por artefato + read-back checksum em todo write | backend | read-back divergence → `OUTCOME_VERIFICATION_FAILED` |
| T18 | revision tampering | append-only + `UNIQUE(model_id, revision_number)` + runtime role sem UPDATE/DELETE em `revisions` | DB | grant test + constraint test |

---

## 13. Audit events

`FROZEN` — mutations auditáveis (metadata segura apenas; **nunca** XML/token/body). Campos por evento: `actor_sub`, `model_id`, `revision_id`/`revision_number` quando aplicável, `operation` (UC), `outcome`, `timestamp` (ClockPort), `request_id`, `expected_version`/`version` resultante, `artifact_sha256` quando útil.

| Evento | Campos mínimos |
|---|---|
| CreateModel | actor, model_id, uc, outcome, ts, request_id, version=1, sha256(blank) |
| ImportModel | + sha256(input), original_byte_length, validation outcome summary |
| RenameModel | + expected_version→version |
| DuplicateModel | + source_model_id, new model_id, checksum |
| ArchiveModel / UnarchiveModel | + expected_version→version |
| SaveWorkingCopy | + expected_version→version, artifact_sha256, artifact_bytes |
| CreateRevision | + revision_number, artifact_sha256, origin=explicit |
| RestoreRevision | + revision_number restaurada, nova revision_number, origin=restore |

Sem event sourcing; sem audit table separada na V1 (revision trail + `updated_*` + logs cobrem).

---

## 14. Logging, privacidade e observabilidade

`FROZEN`:

- `logging` stdlib, `LOG_LEVEL` env (default `INFO`), linha única estruturada com `request_id`, `actor_sub`, `uc_id`, `model_id`/`revision_number`, `outcome`, `latency_ms`, `error_code`, `artifact_sha256`/`artifact_bytes`.
- **Nunca** logar: XML do artefato, tokens/JWT, secrets, body bruto, connection string com senha. Redaction conforme `observability-standards.mdc`.
- Métricas mínimas: contadores UC/outcome + histograma de latência (`save`, `import`, `restore`, `validate`); `request_id` propagado. Sem tracing distribuído obrigatório na V1.

---

## 15. Connection pool e session safety

`FROZEN`:

- **Pool:** implementação in-process de pool limitado sobre psycopg3 puro, seguindo o padrão comprovado `plugins_postgres_connection.py` (bounded pool, contextmanager de lease, thread-safe). `psycopg-pool` **não** é adicionado — a convenção real do monorepo não o usa.
- Parâmetros: `BPMN_MODELER_DB_POOL_MAX_SIZE` default `5`; `BPMN_MODELER_DB_POOL_ACQUIRE_TIMEOUT` default `30`s; `application_name = 'bpmn-modeler-api'`.
- Uma instância de pool por processo (lazy singleton com lock); `Connection` obtida por operação/transação via context manager — **proibido** criar conexão ad hoc por request.
- **Session safety** aplicada na DSN/`options` da conexão do pool:

```text
options = -c statement_timeout=30000 -c TimeZone=UTC -c search_path=public
connect_timeout = 5
application_name = bpmn-modeler-api
```

- `statement_timeout=30000` chega à sessão via `options` (não é apenas constante); `TimeZone=UTC` garante `timestamptz` coerente; `search_path=public` explícito por defesa em profundidade.

---

## 16. Health, readiness e startup

`FROZEN`:

| Endpoint | Tipo | Comportamento |
|---|---|---|
| `GET /health` | liveness, público | processo vivo; `200` sem DB |
| `GET /ready` | readiness, público | ver abaixo |

Rotas públicas intencionais, explicitamente liberadas pelo `auth_middleware`.

**Readiness (`/ready`) — `FROZEN`:**

- **Nunca** executa migrations.
- Verifica somente, conectando como `bpmn_modeler_app`:
  - runtime DB connectivity (`SELECT 1` via pool);
  - XSD bundle carregado (checksum ok);
  - runtime config obrigatória presente (Keycloak + `BPMN_MODELER_DB_*` de runtime);
  - **migration version compatible** — verificada pela existência dos objetos exigidos pela última migration esperada (`to_regclass('public.models')`, `to_regclass('public.revisions')`; metadata de `pg_catalog` não depende de grant em `schema_migrations`). Objeto ausente → `READINESS = FAIL` (`503`); a API **não** tenta corrigir — correção é o migration job de §22.

**Startup validation (fail-closed):** presença de `KEYCLOAK_JWKS_URL`, `KEYCLOAK_ISSUER`, `KEYCLOAK_AUDIENCE`, `BPMN_MODELER_DB_HOST/PORT/NAME/USER/PASSWORD`; XSD bundle carrega e passa checksum. **Não existe flag de run-migrations-on-startup**: o processo `bpmn-modeler-api` nunca recebe credencial DDL nem executa migration (§22).

---

## 17. Environment variables — matriz

`FROZEN`:

| Variável | Obrigatória | Secret | Padrão / exemplo |
|---|---|---|---|
| `KEYCLOAK_URL` | sim | não | `http://keycloak:8080/auth` |
| `KEYCLOAK_REALM` | sim | não | `delpi` |
| `KEYCLOAK_JWKS_URL` | sim | não | `.../protocol/openid-connect/certs` |
| `KEYCLOAK_ISSUER` | sim | não | `.../realms/delpi` |
| `KEYCLOAK_AUDIENCE` | sim | não | audience do client da API |
**Runtime API env** (`bpmn-modeler-api` process — produção recebe somente isto):

| Variável | Obrigatória | Secret | Padrão / exemplo |
|---|---|---|---|
| `KEYCLOAK_URL` | sim | não | `http://keycloak:8080/auth` |
| `KEYCLOAK_REALM` | sim | não | `delpi` |
| `KEYCLOAK_JWKS_URL` | sim | não | `.../protocol/openid-connect/certs` |
| `KEYCLOAK_ISSUER` | sim | não | `.../realms/delpi` |
| `KEYCLOAK_AUDIENCE` | sim | não | audience do client da API |
| `BPMN_MODELER_DB_HOST` | sim | não | `postgres-plugins` |
| `BPMN_MODELER_DB_PORT` | sim | não | `5432` |
| `BPMN_MODELER_DB_NAME` | sim | não | `bpmn_modeler` |
| `BPMN_MODELER_DB_USER` | sim | **secret** | `bpmn_modeler_app` |
| `BPMN_MODELER_DB_PASSWORD` | sim | **secret** | via env/secret store |
| `BPMN_MODELER_DB_POOL_MAX_SIZE` | não | não | `5` |
| `BPMN_MODELER_DB_POOL_ACQUIRE_TIMEOUT` | não | não | `30` |
| `BPMN_MODELER_ROOT_PATH` | sim | não | `/apps/bpmn-modeler-api` |
| `LOG_LEVEL` | não | não | `INFO` |

**Migration job env** (step de deploy separado — §22; **nunca** injetado no processo da API):

| Variável | Obrigatória | Secret | Padrão / exemplo |
|---|---|---|---|
| `BPMN_MODELER_DB_HOST` | sim | não | `postgres-plugins` |
| `BPMN_MODELER_DB_PORT` | sim | não | `5432` |
| `BPMN_MODELER_DB_NAME` | sim | não | `bpmn_modeler` |
| `BPMN_MODELER_DB_ADMIN_USER` | sim | **secret** | `bpmn_modeler_admin` |
| `BPMN_MODELER_DB_ADMIN_PASSWORD` | sim | **secret** | via env/secret store |

`FROZEN` — admin credential isolation:

- `BPMN_MODELER_DB_ADMIN_*` **não existe** no ambiente do processo `bpmn-modeler-api` em produção — o runtime não conhece credencial DDL.
- `BPMN_MODELER_RUN_MIGRATIONS_ON_STARTUP` **removido do contrato** — não há migration pelo startup da API. Conveniência local/dev futura usa processo/container de migration separado, nunca eleva o processo API.
- Nenhuma variável controla limites de segurança, namespaces BPMN ou permission codes.
- `env.*.example` documenta placeholders apenas.

---

## 18. ELK worker — packaging e política de falha

`FROZEN` (complementa Prompt 5):

- `elkjs` em Web Worker dedicado; `elk-worker.min.js` servido como asset do próprio plugin (mesma origem, `worker-src 'self'`).
- Timeout `ELK_LAYOUT_TIMEOUT_MS = 30_000`; falha/timeout → aborta execução, descarta resultado parcial, restaura DI anterior; preview não aplicado; erro não bloqueante.
- **Sem** fallback main-thread (fail-closed). Retry só por ação explícita do usuário.
- Layout é operação somente-DI; semântica BPMN nunca é mutada por falha/timeout/retry.

### 18.1 CSP

`FROZEN` — mínimo exigido pelo plugin (aplicado pelo gateway/Portal, owner transversal):

```text
default-src 'self';
script-src 'self';
worker-src 'self';
connect-src 'self';
img-src 'self' data:;
style-src 'self';
style-src-attr 'unsafe-inline';
```

- `worker-src 'self'` mandatório (ELK worker). `script-src 'self'`; `'unsafe-eval'` **proibido**.
- `style-src-attr 'unsafe-inline'`: **necessário e verificado** — diagram-js/bpmn-js setam atributos `style` em runtime (transform do viewport, posicionamento de overlays/palette/popup, cursores); CSP bloqueia `style=` attributes sem esta fonte. Escopo reduzido a `style-src-attr` (não `style-src` inteira) — stylesheets continuam exigindo `'self'`. `'unsafe-hashes'` inviável (valores dinâmicos). Residual risk: injeção CSS via atributos apenas — sem vetor de script; aceito e documentado. Owner da diretiva: platform gateway.
- `connect-src 'self'` (API same-origin via gateway).
- A CSP final é aplicada pelo gateway/Portal; este é o **mínimo** que o plugin exige — relaxamento adicional exige decisão transversal.

---

## 19. Web security — CORS, CSRF, headers, rate limiting

`FROZEN` — decisões baseadas na topologia congelada (MFE e API same-origin atrás do gateway; auth por Bearer):

| Tema | Decisão |
|---|---|
| CORS | **Same-origin default** — a API não emite `Access-Control-Allow-Origin`; wildcard **proibido**. Não há cross-origin legítimo na V1. |
| CSRF | **Token CSRF não exigido** — autenticação é Bearer header (não cookie); navegador não anexa credencial automaticamente. Se algum dia cookies participarem da auth da API, CSRF passa a ser obrigatório — hoje não. |
| `X-Content-Type-Options` | `nosniff` nas respostas da API — aplicado via `add_header` na location do gateway (evidência: gateway atualmente não emite; implementação adiciona no mount `/apps/bpmn-modeler-api/`). |
| `Referrer-Policy` | `strict-origin-when-cross-origin` nas respostas da API (mesmo owner). |
| `frame-ancestors` | `'self'` para páginas/MFE (plugin embutido no Portal same-origin); `'none'` aceitável em respostas JSON da API. Owner: gateway/Portal. |
| Rate limiting | **Gateway-owned** — `limit_req_zone` dedicada `bpmn_modeler_api_zone:10m rate=60r/s` + `limit_req ... burst=100 nodelay` na location (espelha `tm_api_zone` comprovado; `limit_req_status 429` já global). Classes caras (`import`, `validate`) cobertas pela mesma zone na V1; nenhum limiter duplicado no backend. |

---

## 20. Docker / Compose

`FROZEN`:

```text
bpmn-modeler-api:
  build: bpmn-modeler/Dockerfile (python:3.11-slim)
  env:   BPMN_MODELER_DB_HOST/PORT/NAME/USER/PASSWORD (app role only), KEYCLOAK_*, BPMN_MODELER_ROOT_PATH, LOG_LEVEL
  port:  8000 (interno)
  deps:  postgres-plugins (healthy)
  healthcheck: curl -f http://localhost:8000/health
```

- O env do serviço contém **somente** credenciais `bpmn_modeler_app` — `BPMN_MODELER_DB_ADMIN_*` nunca é injetado no container da API (§17).
- Migration roda como step/job separado com `bpmn_modeler_admin` antes do rollout (§22).

- Receita dos demais `*-api` (`uvicorn` + `--root-path`).
- Gateway: location `/apps/bpmn-modeler-api/` → `bpmn-modeler-api:8000`, com `limit_req` zone dedicada e headers de §19.
- MFE `plugins/bpmn-modeler` segue pipeline padrão (Vite + federation, servido estático via Portal/gateway).

---

## 21. Validation runtime — XSD bundle

`FROZEN`:

- `lxml==6.1.3` único parser/validator XML/XSD do backend.
- Bundle XSD **vendored**: `bpmn-modeler/bpmn_modeler/infrastructure/validation/xsd/` com XSDs BPMN 2.0 oficiais OMG (paths-fonte `spec/BPMN/20100501/*.xsd` etc.) + manifest `sha256` por arquivo.
- `20100501` só nos paths dos XSDs-fonte; namespaces finais `20100524` (Prompt 3).
- **Zero runtime schema download**: nenhum `xsi:schemaLocation` externo, nenhum resolver de rede, `no_network=True`.
- Bundle carregado no startup; checksum/carregamento falho → aborta (§16).

---

## 22. Migrations

`FROZEN`:

| Propriedade | Valor |
|---|---|
| Diretório | `bpmn-modeler/migrations/` |
| Naming | `VNNN__descricao.sql` |
| Executor | runner do contexto sob role **`bpmn_modeler_admin`** (migration role — §4.2); runtime role nunca executa migration |
| Tracking | `public.schema_migrations` (`version`, `name`, `checksum` SHA-256, `executed_at`) — runtime role sem grants nela |
| Imutabilidade | arquivo aplicado nunca editado; checksum divergente = falha |
| Execução | **dedicated deploy/migration step** (job/CLI separado) executado **antes** do backend rollout; nunca pelo startup da API em produção — `BPMN_MODELER_RUN_MIGRATIONS_ON_STARTUP` removido do contrato |
| Produção | apenas `up`; nunca reset destrutivo |
| Grants | a migration que cria objeto aplica os GRANTs exatos de §4.2 (opt-in por objeto; sem `ALTER DEFAULT PRIVILEGES` amplo) |
| Migrations V1 | `V001` (tabelas + constraints + índices em `public` + GRANTs §4.2). Database/roles **não** são migration — são bootstrap de infra (§4.2) |

**Sequência de deploy `FROZEN`:**

```text
bootstrap database/roles (init script infra, quando requerido)
→ migration job/CLI com bpmn_modeler_admin
→ verify migration history (checksums, objetos criados, grants aplicados)
→ backend rollout com bpmn_modeler_app apenas
→ frontend rollout
```

---

## 23. Backup / Recovery

`FROZEN`:

- Persistência no server `postgres-plugins` → coberto pelo backup do serviço compartilhado (volume `postgres_plugins_data`); database dedicado `bpmn_modeler` é incluído nesse backup por estando no mesmo server — **não** há backup separado por plugin na V1.
- Revisions append-only + `sha256` permitem verificação de integridade em restore.
- RPO/RTO herdados da infra compartilhada.
- Recuperação: migrations forward-only + init script de bootstrap (database/roles) — reconstrução reproduzível.

---

## 24. CI — contrato

`FROZEN`:

| Gate | Ferramenta | Bloqueia |
|---|---|---|
| Backend unit/integration | `pytest` (Python 3.11) | sim |
| Architecture enforcement | workflow canônico existente | sim |
| Migrations | checksum/immutability + dry-run em database vazio (role admin) | sim |
| Offline XSD validation | teste `no_network` | sim |
| Frontend build | `npm ci` + `vite build` (worker asset presente) | sim |
| Lock integrity | `package-lock.json` + `npm ci` (sem `--force`/`--legacy-peer-deps`) | sim |
| Grants/role test | acceptance explícito como `bpmn_modeler_app` — PASS: `SELECT`/`INSERT`/`UPDATE` em `models`; `SELECT`/`INSERT` em `revisions`. FAIL: `UPDATE revisions`, `DELETE models`, `DELETE revisions`, `SELECT schema_migrations`, `CREATE TABLE`, `ALTER TABLE`, acesso a outro database de contexto | sim |
| Secret scan | gate canônico | sim |
| License scan | allowlist §3.3 | sim |
| Workflow dedicado | `.github/workflows/bpmn-modeler-api.yml` | sim |

Nenhum teste depende de rede externa para XSD; nenhum gate existente é enfraquecido.

---

## 25. Supply chain

`FROZEN`:

- Todas as dependências pinadas em versão exata; ranges `latest`/`*`/`>=` solto proibidos em produção.
- Peer graph frontend provado instalável sem flags de relaxamento (§3.1).
- License allowlist §3.3; `THIRD_PARTY_NOTICES.md` obrigatório; CVE em pin exige bump revisado.

---

## 26. Proibições explícitas

`FROZEN` — sem exceção na V1:

- ❌ persistir `flowchart_v1`/visual JSON/moddle JSON como modelo — XML BPMN é o único artefato canônico.
- ❌ database/schema do Transformômetro ou `plugins` DB compartilhado como autoridade do Modelador.
- ❌ SQL cross-database / FK cross-context.
- ❌ endpoint genérico de SQL/proxy (`/query`, `/exec`) ou ORM genérico.
- ❌ concatenação de input em SQL; `ORDER BY` de string crua.
- ❌ log de XML completo, tokens, secrets ou body bruto.
- ❌ force overwrite / ignorar `expected_version`.
- ❌ hard delete (nem grant de DELETE no runtime role).
- ❌ runtime schema download / resolver de rede no parser.
- ❌ fallback main-thread do ELK worker.
- ❌ `'unsafe-eval'`; `unsafe-inline` fora de `style-src-attr`.
- ❌ `dangerouslySetInnerHTML` com conteúdo BPMN.
- ❌ autorização por ocultação de UI; AuthZ backend-first.
- ❌ reimplementar jwt/JWKS/permissions fora de `shared/delpi_auth`.
- ❌ dependência de produção com range flutuante.
- ❌ alterar migrations aplicadas.
- ❌ DDL no runtime role para "facilitar" migration.
- ❌ credencial admin/migration injetada no processo da API (`BPMN_MODELER_DB_ADMIN_*` ausente do env runtime).
- ❌ migration executada pelo startup da API em produção — sempre step de deploy separado.
- ❌ `ALTER DEFAULT PRIVILEGES` amplo — grants são opt-in por objeto via migration.
- ❌ `pgcrypto`/`pg_trgm` ou qualquer extensão sem requirement.

---

## 27. Residual review — achados

`FROZEN` — executado sobre os 6 documentos do contexto (§41 do corrective gate):

| Busca | Resultado | Ação |
|---|---|---|
| `TODO`/`TBD`/`a decidir`/`talvez`/`maybe` | nenhum remanescente em decisão crítica | ok |
| `latest`/`*.x`/`version TBD`/`permission TBD`/`schema TBD`/`limit TBD`/`worker fallback TBD` | nenhum | ok |
| `PLUGINS_DB_NAME`/`PLUGINS_DB_USER` como DB do Modelador | **removido** — substituído por `BPMN_MODELER_DB_*` dedicado | corrigido |
| `gen_random_uuid`/`UUID4` | estratégia única `uuid.uuid4()` via `IdGeneratorPort`; `pgcrypto` NOT_REQUIRED | corrigido |
| `3.40.6` | **removido** — `@bpmn-io/properties-panel` congelado em `3.55.0` (peer `>=3.42.0` satisfeito) | corrigido |
| `bpmn-js` como `MIT` | **corrigido** — bpmn.io License + watermark | corrigido |
| `least privilege`/`GRANT`/`REVOKE` | grants matrix §4.2 explícita | fechado |
| `pagination`/`SQL injection`/`parameterized`/`threat`/`resource ownership`/`unsafe-inline`/`CORS`/`CSRF`/`rate limit`/`connection pool` | contratos explícitos §5, §6, §12, §15, §18.1, §19 | fechado |
| `Transformômetro DB`/`visual JSON`/`moddle JSON`/`generic SQL`/`generic proxy`/`full XML log`/`force overwrite`/`hard delete`/`runtime schema download` | apenas como proibição | ok |
| `GRANT SELECT, INSERT, UPDATE ON TABLE public.models, public.revisions` (conjunto único) | **removido** — grants separados por tabela (§4.2); `UPDATE revisions` negado ao runtime | corrigido |
| `ALTER DEFAULT PRIVILEGES` | **removido** — sem grants default amplos; opt-in por objeto via migration | corrigido |
| `BPMN_MODELER_DB_ADMIN_*` / `BPMN_MODELER_RUN_MIGRATIONS_ON_STARTUP` no runtime | **removido** do env da API; migration = step separado (§17, §22) | corrigido |
| `horizontal`/`per-model` | T03 corrigido — autorização context-wide; per-model ACL = `OUT_OF_V1` | corrigido |
| `NON_XML` em malformed XML | T10 corrigido — `MALFORMED_XML` ≠ `NON_XML` (Prompt 3) | corrigido |
| `schema_migrations` | acesso negado ao runtime; readiness verifica compatibilidade via `to_regclass` (§16) | consistente |

---

## 28. Delegado ao Prompt 7

`FROZEN` — único escopo restante:

- contrato HTTP/OpenAPI (paths, DTOs, códigos de erro, wire pagination);
- mecanismo físico de paginação (`cursor` vs `offset`) + índice estritamente necessário (§5.4);
- E2E e acceptance criteria executáveis;
- benchmark/timeout numérico de layout por tamanho de modelo (performance, não segurança);
- freeze final de documentação e integração do pacote.

---

## 29. Status

```text
SECURITY / PERSISTENCE / RUNTIME SPEC STATUS:
FROZEN
```

- DATABASE AUTHORITY: **BPMN MODELER DEDICATED DATABASE** (`bpmn_modeler` em `postgres-plugins`).
- RUNTIME DB ROLE: **`bpmn_modeler_app` — BPMN MODELER ONLY** (least privilege; sem DDL, sem DELETE, sem outros databases).
- RUNTIME REVISION UPDATE PRIVILEGE: **DENIED**
- RUNTIME DELETE PRIVILEGE: **DENIED**
- RUNTIME DDL: **DENIED**
- RUNTIME SCHEMA_MIGRATIONS ACCESS: **DENIED**
- API RUNTIME ADMIN CREDENTIAL: **ABSENT**
- PRODUCTION MIGRATION EXECUTION: **SEPARATE DEPLOY STEP**
- PER-MODEL ACL: **NOT IN V1** (context-wide Core RBAC)
- MALFORMED XML CLASSIFICATION: **MALFORMED_XML** (≠ `NON_XML`)
- CROSS-CONTEXT BUSINESS DB ACCESS: **NONE**.
- PEER DEPENDENCY STATUS: **PASS** (conjunto §3.1 resolvido sem `--force`/`--legacy-peer-deps`).
- Todas as 9 mutations têm contrato de transação (§9); search persistence explícita (§5); threat model e resource ownership explícitos (§11–§12); AuthZ 17/17 (§10.2); nenhuma decisão de runtime/segurança resta aberta.
