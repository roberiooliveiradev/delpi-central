# Playbook de Excelência — Etiquetas da Qualidade (Quality Labels)

> **Arquivo:** `docs/12-roadmap-e-evolucao/quality-labels/PLAYBOOK-EXCELENCIA.md`
> **Versão:** 2.0
> **Data:** 2026-07-02
> **Status:** proposta (pré-implementação)
> **Base:** requisito «etiqueta de qualidade por produto/OP com QR público» + convenções do monorepo `delpi-central`.
>
> **Mudança v2.0 (decisão do produto):** o plugin **não** tem API própria. O **CRUD vive dentro da `api-delpi`** (módulo novo no PostgreSQL de plugins), reaproveitando o banco gravável, o storage, o RBAC e — em processo — o use case de OP→produto. Só o **MFE admin** e a **página pública no `public-hub`** ficam fora da api-delpi.
>
> **Convenção de nomes:** identificadores técnicos em **inglês**; textos ao usuário em **pt-BR**.

**Relacionado:**
- `docs/12-roadmap-e-evolucao/customer-experience/PLAYBOOK-EXCELENCIA.md` — irmão (QR + public-hub + etiqueta)
- `api-delpi/app/infrastructure/persistence/plugins/README` — regras do PostgreSQL de plugins
- `api-delpi/docs/api/13-producao-operacional.md` — OP → produto (SC2 → SB1)
- `api-delpi/app/interface/http/routes/quality/` — módulos CRUD de referência (5S, PAC, Cultura)
- `plugins/public-hub/README.md` — registrar página pública
- `.cursor/rules/persistent-upload-storage.mdc` · `.cursor/rules/api-delpi-response-contract.mdc` · `.cursor/rules/new-api-route-checklist.mdc`

---

## 1. North Star — o que é excelência aqui

A Delpi produz cabos. Ao final da inspeção da qualidade, o inspetor precisa **rastrear e comunicar a aprovação** de forma simples e confiável. Excelência aqui **não** é «gerar mais um QR»: é dar ao cliente que recebe o cabo uma **prova de qualidade escaneável** e à Delpi um **registro rastreável** de cada inspeção.

1. O inspetor digita a **OP** (ordem de produção) no plugin.
2. A **api-delpi** resolve automaticamente os dados do produto da OP (código, descrição, unidade) — **em processo**, reusando o use case de produção — grava a **data da inspeção** (momento do registro) e o **nome do inspetor** (identidade do portal).
3. Gera uma **etiqueta imprimível** (QR + logo Delpi + selo «APROVADO QUALIDADE»), colada no cabo — mesma ideia da etiqueta do customer-experience.
4. Ao escanear, **o cliente** (sem login) vê uma página pública: produto, OP, data da inspeção, inspetor responsável e selo de aprovação.
5. **Desacoplado sem inflar serviços:** CRUD dentro da api-delpi (banco de plugins), MFE no padrão do portal, página pública no `public-hub` (fora do portal autenticado), tabelas próprias no schema `quality_labels`.

### Definição operacional (métricas de sucesso)

| Métrica | Meta | Como medir |
|---|---|---|
| Tempo para registrar inspeção + gerar etiqueta | ≤ 30 s | cronometragem no chão de fábrica |
| OP digitada → produto resolvido | ≥ 98% | taxa de sucesso do use case `by-op` |
| Etiquetas escaneadas pelo cliente | ≥ 40% | `view_count` por token |
| Página pública carrega | ≤ 2 s em 4G | medição real |
| Zero QR em filesystem efêmero | 100% | volume persistente homologado |
| Acesso indevido por adivinhação de URL | 0 | token opaco ≥ 128 bits |

---

## 2. Escopo e decisões de arquitetura

| Decisão | Escolha | Racional |
|---|---|---|
| **API** | **Sem API dedicada.** CRUD como módulo novo **dentro da `api-delpi`** | Reusa banco de plugins, storage, RBAC e o use case de produção; não cria mais um serviço |
| **Banco** | PostgreSQL de plugins da api-delpi (`PLUGINS_DB_*`, container `postgres-plugins`), schema **`quality_labels`** | Padrão dos módulos 5S/PAC/Cultura |
| **OP → produto** | Chamar **em processo** `build_get_production_order_by_op_use_case()` | Mesma app: sem HTTP self-call, sem repasse de token, sem exigir `api-delpi.access` |
| **Snapshot do produto** | Copiar `product_code`/`product_description`/`unit` para a tabela local no registro | Etiqueta/página imutáveis, independentes de mudanças futuras na OP |
| **Data da inspeção** | `inspected_at = now()` no registro | Requisito: «a data que o inspetor gerou a etiqueta» |
| **Nome do inspetor** | `get_current_user().id` + `.name` (delpi_auth ← `GET /core-api/me`) | Nome autoritativo; sem parse manual de JWT |
| **Página pública sem login** | **`public-hub`** — app `quality-labels`, view `inspection` (`/p/quality-labels/inspection/{token}`) | Sem novo container público, sem nova `location` no gateway (já cobre `^~ /p/`) |
| **Endpoint público** | Nova rota **pública por token na api-delpi** (`/public/quality-labels/inspection/{token}`) via exceção no middleware | api-delpi hoje não tem rota pública por token — adicionar wrapper igual ao do customer-experience |
| **Geração do QR** | Backend (api-delpi) gera + persiste PNG no volume; **novo** serviço + dep `qrcode` | api-delpi ainda não tem QR — adicionar `qrcode` ao `requirements.txt` |
| **Etiqueta física** | MFE reusa o padrão `qrLabelPrint.ts` do customer-experience (QR + logo preta + selo, frente/verso) | Consistência visual e DRY |
| **Privacidade do link** | Token opaco (`secrets.token_urlsafe(32)`), sem expiração | Anti-enumeração |
| **Front admin** | MFE `plugins/quality-labels` (React 19 + Vite + Module Federation), `backend` → api-delpi | Padrão do portal |
| **Storage QR** | Volume `${DELPI_DATA_HOST_DIR}/quality-labels/qr` na api-delpi | Regra `persistent-upload-storage` |

### Nomenclatura adotada

| Componente | Identificador (inglês) | Rótulo/usuário (pt-BR) | Referência |
|---|---|---|---|
| Plugin admin (MFE) | `quality-labels` | «Etiquetas da Qualidade» | `cultura-delpi`, `auditoria-5s` |
| Módulo CRUD (na api-delpi) | rotas `/quality/labels` | — | `/quality/action-plans`, `/quality/audit-5s` |
| Schema Postgres (plugins) | `quality_labels` | — | `cultura_delpi`, `quality` |
| Slug de migrations | `quality-labels` → `migrations/plugins/quality-labels/` | — | `cultura-delpi`, `quality-action-plans` |
| Rota pública | `/apps/api-delpi/public/quality-labels/inspection/{token}` | — | (nova; padrão CX) |
| Página pública (public-hub) | app `quality-labels`, view `inspection` | — | `customer-experience/thanks` |
| Prefixo CSS admin/público | `ql-` / `qlp-` | — | `plugins-visual-design-system` |
| Permissões RBAC | `quality-labels.read/write/manage` | descrições pt-BR no manifesto | `cultura-delpi.*` |

---

## 3. Arquitetura alvo

```text
┌───────────────────────── PORTAL (login Keycloak obrigatório) ─────────────────────────┐
│  Inspetor da qualidade                                                                 │
│      │ digita a OP                                                                     │
│      ▼                                                                                 │
│  Plugin MFE (plugins/quality-labels)  ──JWT──►  api-delpi  /apps/api-delpi/quality/labels
│                                                     │                                  │
│   No mesmo processo da api-delpi:                   │                                  │
│     • OP→produto: get_production_order_by_op (SC2→SB1, SQL Server, leitura)            │
│     • inspetor = get_current_user().name/.id  (delpi_auth ← /core-api/me)             │
│     • data = now()                                                                     │
│     • grava em PostgreSQL de plugins (schema quality_labels) + gera token opaco + QR   │
└───────────────────────────────────────────────────────────────────────────────────────┘

                        (fora do portal, SEM login)
Cliente escaneia QR ─► GET /p/quality-labels/inspection/{token}  ──►  public-hub (app quality-labels)
                                    │                         │
                                    │      fetch por token    ▼
                                    └──► GET /apps/api-delpi/public/quality-labels/inspection/{token}
                                              (rota PÚBLICA da api-delpi — só leitura, token opaco)
```

**Regra de ouro:** o TOTVS/SQL Server continua **somente leitura**; a gravação vai para o **PostgreSQL de plugins**. A rota pública só lê por token. O admin nunca é servido sem login.

### 3.1 OP → produto (em processo, sem HTTP)

- Use case existente: `build_get_production_order_by_op_use_case()` (`api-delpi/app/composition/production_operational_composer.py`), SQL `ProductionOrdersRepository.fetch_order_by_production_order` (`SC2010 ⨝ SB1010 ON B1_COD = C2_PRODUTO`).
- Campos usados: `product_code` (`C2_PRODUTO`), `product_description` (`B1_DESC`), `unit` (`B1_UM`); opcionais `branch`, `order_number`.
- O módulo `quality-labels` **importa e chama** esse use case diretamente — **não** faz HTTP para si mesmo e **não** exige `api-delpi.access` do inspetor (RBAC do módulo é `quality-labels.*`).
- Falha na OP (não encontrada) → `422` com mensagem pt-BR; **não** cria etiqueta sem produto.

### 3.2 Identidade do inspetor

- `get_current_user()` (`delpi_auth.request_context`) já traz `id` (sub) e `name` (via `/core-api/me`). Padrão dos routers PAC: `_creator_identity_kwargs()`.
- Persistir `inspector_sub` (estável) **e** `inspector_name` (snapshot para etiqueta/página).

---

## 4. Modelo de dados (schema `quality_labels` no banco de plugins)

Migration `migrations/plugins/quality-labels/V001__create_quality_labels.sql` (rodada on startup pelo runner de plugins da api-delpi; slug `quality-labels` → schema `quality_labels`).

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE SCHEMA IF NOT EXISTS quality_labels;

CREATE TABLE IF NOT EXISTS quality_labels.inspection_labels (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  public_token         TEXT NOT NULL UNIQUE,          -- secrets.token_urlsafe(32)

  -- OP e snapshot do produto (via use case de produção no momento do registro)
  production_order     TEXT NOT NULL,                  -- C2_OP digitada
  branch               TEXT,                           -- filial (opcional)
  product_code         TEXT NOT NULL,                  -- C2_PRODUTO / B1_COD
  product_description  TEXT NOT NULL,                  -- B1_DESC
  product_unit         TEXT,                           -- B1_UM
  order_number         TEXT,                           -- C2_NUM (opcional)

  -- Inspeção
  inspected_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  inspector_user_id    TEXT NOT NULL,                  -- sub/id (core-api)
  inspector_name       TEXT NOT NULL,                  -- snapshot do nome
  result               TEXT NOT NULL DEFAULT 'approved',    -- approved | rejected (futuro)
  notes                TEXT,

  -- QR / ciclo de vida
  qr_filename          TEXT,
  view_count           INTEGER NOT NULL DEFAULT 0,
  is_active            BOOLEAN NOT NULL DEFAULT TRUE,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_quality_labels_op      ON quality_labels.inspection_labels (production_order);
CREATE INDEX idx_quality_labels_product ON quality_labels.inspection_labels (product_code);
CREATE INDEX idx_quality_labels_date    ON quality_labels.inspection_labels (inspected_at DESC);
```

- **`public_token`**: única chave da página pública.
- **Snapshot** de produto e inspetor: a etiqueta impressa já circulou; os dados exibidos não podem mudar depois.

---

## 5. Página pública sem login (via `public-hub` + rota pública da api-delpi)

### 5.1 Novo app no `public-hub`

- Criar `plugins/public-hub/src/apps/quality-labels/`:
  - `api.ts` — `fetchPublicLabel(token)` → `GET /apps/api-delpi/public/quality-labels/inspection/{token}` (envelope `{success,message,data}`; 404 → `null`).
  - `InspectionPage.tsx` (+ `inspection.css`, prefixo `qlp-`).
  - `pages.tsx` — `qualityLabelsPages: AppPublicPages`:
    ```ts
    export const qualityLabelsPages: AppPublicPages = {
      inspection: {
        documentTitle: "Qualidade Delpi — Inspeção do produto",
        notFoundMessage: "Esta etiqueta de qualidade não está mais disponível.",
        load: ({ token }) => fetchPublicLabel(token),
        render: (data) => <InspectionView label={data as PublicLabel} />,
      },
    };
    ```
- Registrar em `plugins/public-hub/src/shell/registry.ts`:
  ```ts
  export const publicRegistry: PublicRegistry = {
    "customer-experience": customerExperiencePages,
    "quality-labels": qualityLabelsPages,
  };
  ```
- Rota resultante: `/p/quality-labels/inspection/{token}` (o `routing.ts` já parseia `/p/{app}/{page}/{token}`).

### 5.2 Rota pública na api-delpi (nova exceção de auth)

A api-delpi hoje **não** tem rota pública por token. Adicionar:

1. **Middleware:** estender `api-delpi/app/middleware/auth_middleware.py` com um wrapper que isenta o prefixo `/public/quality-labels/` do JWT (padrão de `customer-experience-api/cx_app/middleware/auth_middleware.py`, que usa `PUBLIC_PREFIXES` + `_strip_root_path`).
2. **Handler sem `@require_permission`**, validando o token no Postgres:
```
GET /apps/api-delpi/public/quality-labels/inspection/{token}
→ 200 {
    productCode, productDescription, productUnit,
    productionOrder, branch,
    inspectedAt, inspectorName,
    result,                       // "approved"
    companyName: "Delpi Conexões Elétricas"
  }
→ 404 se token inexistente ou is_active = false
```
- Incrementa `view_count` (best effort).
- **Nunca** devolve `inspector_user_id`, `id` ou lista — só o registro do token.
- Rate limit no gateway (reuso de `limit_req_zone`).

### 5.3 Conteúdo da página (pt-BR)

- Selo **APROVADO** em destaque, produto (código + descrição), OP e filial, data da inspeção e inspetor. Marca Delpi; mobile-first.

---

## 6. Contrato do módulo na api-delpi (admin — JWT do portal)

Envelope `api_delpi_success(data, operation_id=...)` + `route_contract_registry`. RBAC via `@require_any_permission`. Router em `app/interface/http/routes/quality/quality_labels_router.py` (incluir em `quality_router.py`).

| Método | Rota (sob `/apps/api-delpi`) | `operationId` | Permissão | Descrição |
|---|---|---|---|---|
| `GET` | `/quality/labels/lookup-op/{op}` | `lookup_quality_label_production_order` | `quality-labels.read` | **Preview** do produto da OP (chama o use case `by-op` em processo) antes de confirmar |
| `POST` | `/quality/labels` | `create_quality_label` | `quality-labels.write` | Registra inspeção: `{ productionOrder, branch?, notes? }` → resolve produto, grava data/inspetor, gera token + QR |
| `GET` | `/quality/labels` | `list_quality_labels` | `quality-labels.read` | Lista/pagina (filtro por OP, produto, data, inspetor) |
| `GET` | `/quality/labels/{id}` | `get_quality_label` | `quality-labels.read` | Detalhe |
| `PATCH` | `/quality/labels/{id}` | `update_quality_label` | `quality-labels.write` | Edita observação / resultado |
| `POST` | `/quality/labels/{id}/deactivate` | `deactivate_quality_label` | `quality-labels.manage` | Desliga link público |
| `GET` | `/quality/labels/{id}/qr` | `download_quality_label_qr` | `quality-labels.read` | Baixa o QR (PNG) para impressão |
| `GET` | `/public/quality-labels/inspection/{token}` | `get_public_quality_label` | pública | Dados da página pública |

- Registrar cada `operationId` em `route_contract_registry.py` (`RouteContract(entity, shape)`), ex.: `create_quality_label → RouteContract("quality_label", "scalar")`; lista → `paged_list`.
- **QR:** gerado no `POST` a partir de `{PUBLIC_BASE_URL}/p/quality-labels/inspection/{token}`; novo `QualityLabelsQrService` (copiar `customer-experience-api/.../qr_service.py`), dep `qrcode[pil]` no `api-delpi/requirements.txt`, env `QUALITY_LABELS_QR_DIR`.
- **Etiqueta física:** o MFE monta a etiqueta frente/verso no cliente (QR + logo preta + selo APROVADO QUALIDADE), reusando `plugins/customer-experience/src/utils/qrLabelPrint.ts` — só usa o download `/quality/labels/{id}/qr`. Avaliar extrair o util para pacote compartilhado (3º consumidor).
- **Camadas (padrão api-delpi):**
  ```
  migrations/plugins/quality-labels/V001__create_quality_labels.sql
  app/infrastructure/persistence/plugins/repositories/quality_labels/postgres_quality_labels_repository.py   (PluginBaseRepository)
  app/application/use_cases/quality_labels/                (create/lookup/get_public)
  app/composition/quality_labels_composer.py
  app/interface/http/routes/quality/quality_labels_router.py
  app/interface/http/route_contract_registry.py           (operationIds)
  app/application/security/api_delpi_permissions.py        (QUALITY_LABELS_*_PERMISSIONS)
  app/middleware/auth_middleware.py                        (isentar /public/quality-labels/)
  app/config.py + requirements.txt                        (QUALITY_LABELS_QR_DIR, qrcode)
  ```

---

## 7. Storage persistente (obrigatório desde o 1º commit)

Regra `persistent-upload-storage.mdc`. Volume **na api-delpi** (mesmo padrão de PAC/5S).

| Item | Container | Host |
|---|---|---|
| QR codes | `/app/data/quality-labels/qr` | `${DELPI_DATA_HOST_DIR}/quality-labels/qr` |

- Env `QUALITY_LABELS_QR_DIR` em `api-delpi/app/config.py`.
- Volume no serviço `api-delpi` dos **dois** composes (`infra/docker-compose.yml` + `docker-compose.dev.yml`).
- Documentar em `infra/README-ambiente.md` + `env.local.example`.
- Homologar: `up -d --force-recreate api-delpi` → QR ainda no host.

---

## 8. Segurança, RBAC e LGPD

- **Token opaco** ≥ 128 bits, não sequencial.
- Endpoint público **só leitura por token**; sem listagem; `is_active=false` → 404.
- Rate limit no gateway para `/public/`.
- **RBAC:** inspetor precisa só de `quality-labels.write` (o OP→produto é chamada interna; **não** exige `api-delpi.access`). Constantes em `api_delpi_permissions.py`; declarar no manifesto do MFE.
- **Dados pessoais:** único PII é o **nome do inspetor** exposto ao cliente. Validar com jurídico; alternativa: flag para exibir «Equipe Qualidade Delpi» guardando o nome só internamente.
- Sem PII em logs (nível INFO).

---

## 9. Roadmap por ondas

### Onda 0 — Fundação (MVP)
**Objetivo:** inspetor digita OP → produto resolvido → etiqueta com QR → página pública.

| # | Entrega | Onde | Esforço |
|---|---|---|---|
| 0.1 | Migration `V001__create_quality_labels.sql` (schema + tabela + índices) | `api-delpi/migrations/plugins/quality-labels/` | S |
| 0.2 | `PostgresQualityLabelsRepository` (INSERT/UPDATE/SELECT por token/OP) | api-delpi (plugins repo) | M |
| 0.3 | Use cases: create (chama `by-op` em processo, snapshot, token, QR), lookup-op, get_public | api-delpi (use_cases) | M |
| 0.4 | `QualityLabelsQrService` + dep `qrcode` + env `QUALITY_LABELS_QR_DIR` | api-delpi | S |
| 0.5 | Router `/quality/labels` (CRUD) + rota pública `/public/quality-labels/inspection/{token}` + exceção no middleware | api-delpi | M |
| 0.6 | `route_contract_registry` + `api_delpi_permissions` (`quality-labels.*`) + `include_router` | api-delpi | S |
| 0.7 | Volume QR no serviço api-delpi (dois composes) + README | `infra/` | S |
| 0.8 | Plugin MFE admin: campo OP + preview do produto + lista + download QR + **imprimir etiqueta** | `plugins/quality-labels` | M |
| 0.9 | App `quality-labels` no `public-hub` (view `inspection`) + registro | `plugins/public-hub` | S |
| 0.10 | Manifesto do MFE (`backend` → api-delpi) + RBAC + `register-manifest.sh` | plugin + Core API | S |

**Critério de aceite Onda 0:**
- [ ] Inspetor digita OP válida → produto preenchido automaticamente (código + descrição).
- [ ] Ao registrar: grava data (agora) + nome do inspetor + snapshot do produto e gera QR imprimível.
- [ ] Escanear o QR abre `/p/quality-labels/inspection/{token}` **sem login** e mostra produto + inspeção + selo.
- [ ] OP inexistente → 422 claro, **sem** criar etiqueta.
- [ ] Recreate do api-delpi **não** perde QR. Token errado → 404.
- [ ] Gates `new-api-route-checklist.mdc` (registry + contrato) verdes para os novos `operationId`.

### Onda 1 — Etiqueta e experiência
| # | Entrega | Esforço |
|---|---|---|
| 1.1 | Etiqueta física calibrada ao rótulo real (frente/verso) | S |
| 1.2 | Página pública encantadora (branding, animação do selo, OG) | M |
| 1.3 | Impressão em lote (várias etiquetas por página) | M |
| 1.4 | Resultado `rejected` (etiqueta «REPROVADO») | M |
| 1.5 | Extrair `qrLabelPrint` para pacote compartilhado (DRY) | S |

### Onda 2 — Governança e rastreabilidade
| # | Entrega | Esforço |
|---|---|---|
| 2.1 | Anexos/fotos da inspeção (volume, padrão 5S/PAC) | M |
| 2.2 | Vínculo com `inspecoes-entrada` / certificado de qualidade | M |
| 2.3 | Flag LGPD de exibição do nome do inspetor | S |
| 2.4 | Auditoria de acessos (primeiro/último scan) | M |

### Onda 3 — Analytics
| # | Entrega | Esforço |
|---|---|---|
| 3.1 | Dashboard: inspeções por período/produto/inspetor, taxa de scan | M |
| 3.2 | Exportar relatório (Excel/PDF) | M |
| 3.3 | Status da OP/OTD no público | L |

---

## 10. Gates e testes (antes do merge)

| Escopo | Comando |
|---|---|
| api-delpi (módulo) | `pytest api-delpi/tests/ -q -k quality_labels` |
| Migration | `docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin quality-labels` |
| Contrato de rota | `new-api-route-checklist.mdc` § 4 (`route_contract_registry` + gates) |
| Plugin admin | `cd plugins/quality-labels && npm run build` |
| Shell público | `cd plugins/public-hub && npm run build` |
| Storage | Recreate do api-delpi → QR presente no host |
| Público sem login | `curl` em `/p/quality-labels/inspection/{token}` e `/apps/api-delpi/public/quality-labels/inspection/{token}` sem Authorization → 200 |
| OP→produto | teste com OP mock → produto resolvido; OP inválida → 422 |
| Segurança | token inválido → 404; sem listagem no público; rota admin sem JWT → 401 |

Testes mínimos: token único, snapshot correto do `by-op`, `inspected_at`/`inspector_name` gravados, público retorna só o registro do token, `is_active=false` → 404, falha do use case não cria etiqueta.

---

## 11. Checklist de entrega (referência)

1. **Migration** `migrations/plugins/quality-labels/V001__*.sql` (schema `quality_labels`).
2. **Repositório** `PluginBaseRepository` (nunca `BaseRepository` do TOTVS).
3. **Use cases** + **composer** + **router** `/quality/labels` (incluir em `quality_router.py`).
4. **OP→produto**: reusar `build_get_production_order_by_op_use_case()` em processo.
5. **Rota pública** + exceção no `auth_middleware.py` (prefixo `/public/quality-labels/`).
6. **QR**: `qrcode` no requirements + `QualityLabelsQrService` + env/volume nos dois composes.
7. **Contratos/RBAC**: `route_contract_registry.py` + `api_delpi_permissions.py` (`quality-labels.*`).
8. **MFE** `plugins/quality-labels`: manifesto (`id: quality-labels`, `basePath: /apps/quality-labels`, `backend.serviceName: api-delpi`, permissões, menu «Etiquetas da Qualidade»), build, `register-manifest.sh`.
9. **public-hub**: app `quality-labels` + registro no `registry.ts` (sem novo container/gateway).
10. **Gateway**: só `location ^~ /apps/quality-labels/` (MFE). API usa o `/apps/api-delpi/` existente; público usa o `^~ /p/` existente.
11. **RBAC**: atribuir `quality-labels.*` ao papel Inspetor da Qualidade.

---

## 12. Riscos e pontos de atenção

| Risco | Mitigação |
|---|---|
| Inflar a api-delpi (god service) | Módulo isolado (schema próprio, repo próprio, use cases finos); seguir camadas do repo |
| Rota pública fura o RBAC global da api-delpi | Exceção **explícita** só para `/public/quality-labels/`; handler valida token; nunca `@require_permission` ausente por engano em rota admin |
| OP não resolve no TOTVS | 422 claro; não criar etiqueta sem produto |
| Dado do produto muda após imprimir | Snapshot no registro (não reconsultar por token) |
| Nome do inspetor exposto (LGPD) | Flag de exibição (Onda 2); validar jurídico |
| QR em disco efêmero | Volume persistente no api-delpi desde o 1º commit |
| Enumeração de etiquetas | Token opaco ≥ 128 bits + rate limit + 404 genérico |
| Dep nova `qrcode` na api-delpi | Registrar em requirements; testar geração no CI |
| Duplicar util de etiqueta entre plugins | Extrair `qrLabelPrint` (Onda 1.5) |

---

## 13. Resumo executivo

1. **MVP (Onda 0):** inspetor digita a OP → api-delpi resolve o produto **em processo** → registra data + inspetor → gera etiqueta com QR → cliente escaneia e vê a **prova de qualidade** sem login. Sem novo serviço: CRUD dentro da api-delpi (banco de plugins), página no `public-hub`, etiqueta reusada do customer-experience.
2. **Onda 1:** etiqueta/página impecáveis, lote, reprovado.
3. **Ondas 2–3:** anexos/rastreabilidade, LGPD do nome, analytics.

A excelência chega quando o cliente que recebe um cabo Delpi escaneia a etiqueta e vê — em 2 segundos, sem login — **qual produto, qual OP, quando foi inspecionado e por quem**, com o selo de aprovação da Delpi, enquanto a qualidade mantém cada inspeção rastreável e segura, **sem criar mais um serviço** para manter.
