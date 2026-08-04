# Playbook — reorganizar APIs em `apis/` (exceto core e api-delpi)

> **Status:** planejado / **não implementado** (ago/2026)  
> **Tipo:** melhoria de estrutura do monorepo (paths)  
> **Produto:** Minha DELPI  
> **Escopo:** mover 8 APIs de domínio para `apis/`; manter `core-api` e `api-delpi` na raiz  
> **Doc relacionada:** [estrutura-de-repositorio.md](../01-arquitetura/estrutura-de-repositorio.md)

---

## 1. Objetivo

Limpar a raiz do monorepo, alinhando APIs de domínio à pasta `apis/` (simetria com `plugins/`), **sem** alterar runtime Docker (nomes de serviço, DNS, URLs `/apps/*`).

**Não executar** este playbook sem reler a § 2 (retomada) — o inventário abaixo foi levantado em **ago/2026** e o código pode ter mudado.

---

## 2. Checklist obrigatório ao retomar (antes de qualquer `git mv`)

O inventário deste documento **envelhece**. Na retomada:

1. Confirmar que `core-api/` e `api-delpi/` continuam na raiz e que as 8 APIs listadas na § 3 ainda existem na raiz (nenhuma nova API na raiz? nenhuma já movida?).
2. Reexecutar inventário de **paths de filesystem** (não nomes de serviço):

```bash
# A partir da raiz do monorepo
APIS='minha-delpi-ai-api|transformometro-api|tv-dashboard-api|strategic-indicators-api|maintenance-api|cipa-api|customer-experience-api|comite-etica-conduta-api'

# Compose / Docker
rg -n "dockerfile: (${APIS})/|context: \.\./(${APIS})|volumes:.*\.\./(${APIS}):" infra/

# COPY nos Dockerfiles
rg -n "COPY (${APIS})/" --glob 'Dockerfile*'

# Scripts e Python com path de pasta
rg -n "ROOT.*/(\"|')(${APIS})|/\$ROOT/(${APIS})|parents\[[0-9]+\].*/(\"|')(${APIS})" scripts/ api-delpi/ .github/

# Relativos a partir de plugins
rg -n "\.\./\.\./(${APIS})/" plugins/ --glob '*.{json,ts,tsx,sh,md}'

# parents[N] apontando para api-delpi / shared / scripts a partir das APIs candidatas
for d in minha-delpi-ai-api transformometro-api tv-dashboard-api strategic-indicators-api \
         maintenance-api cipa-api customer-experience-api comite-etica-conduta-api; do
  [ -d "$d" ] || continue
  echo "=== $d ==="
  rg -n 'parents\[[0-9]+\]' "$d" --glob '*.py' | head -80
done
```

3. Diffar o resultado com as tabelas deste playbook (§ 5–9): **adicionar** arquivos novos; **remover** linhas obsoletas; **ajustar** `parents[N]` se a profundidade do arquivo mudou.
4. Atualizar este playbook (data da revalidação + inventário) **antes** ou **no mesmo PR** da migração.
5. Só então seguir a ordem da § 4.

### O que NÃO confundir no grep

| Tipo | Exemplo | Ação na migração |
|------|---------|------------------|
| Path de filesystem | `dockerfile: minha-delpi-ai-api/...`, `ROOT / "tv-dashboard-api"` | Prefixar `apis/` ou ajustar `../` / `parents[N]` |
| Nome de serviço Compose / DNS | `minha-delpi-ai-api:`, `http://transformometro-api:8000` | **Não alterar** |
| URL gateway | `/apps/tv-dashboard-api`, `*_API_ROOT_PATH` | **Não alterar** |
| `container_name` | `delpi-minha-delpi-ai-api` | **Não alterar** |
| Scripts sequenciais | listas em `up-*-sequential.sh` | **Não alterar** (batem no nome do serviço) |

Replace cego `minha-delpi-ai-api` → `apis/minha-delpi-ai-api` **quebra** gateway e Compose.

---

## 3. Decisão de layout (alvo)

```text
delpi-central/
  api-delpi/                 # permanece na raiz
  core-api/                  # permanece na raiz
  apis/
    minha-delpi-ai-api/
    transformometro-api/
    tv-dashboard-api/
    strategic-indicators-api/
    maintenance-api/
    cipa-api/
    customer-experience-api/
    comite-etica-conduta-api/
  plugins/
  infra/
  portal/
  shared/
  gateway/
  scripts/
  docs/
```

- **Sem symlinks** na raiz após o move.
- `portal/`, `shared/`, `gateway/`, `infra/` **não** entram em `apis/`.

### Movimentação (`git mv`)

| De (raiz) | Para |
|-----------|------|
| `minha-delpi-ai-api/` | `apis/minha-delpi-ai-api/` |
| `transformometro-api/` | `apis/transformometro-api/` |
| `tv-dashboard-api/` | `apis/tv-dashboard-api/` |
| `strategic-indicators-api/` | `apis/strategic-indicators-api/` |
| `maintenance-api/` | `apis/maintenance-api/` |
| `cipa-api/` | `apis/cipa-api/` |
| `customer-experience-api/` | `apis/customer-experience-api/` |
| `comite-etica-conduta-api/` | `apis/comite-etica-conduta-api/` |

---

## 4. Ordem de execução

```text
git mv → Dockerfiles COPY → Compose (dockerfile/context/volumes)
       → Python parents[N] / ROOT paths → CI + scripts raiz
       → MFE sync/test → Cursor/docs → validação
```

PR dedicado, sem misturar feature. Homologação com scripts sequenciais (`infra/scripts/up-*-sequential.sh`), não `docker compose up --build` em lote.

---

## 5. Inventário — Dockerfiles (snapshot ago/2026)

Build context típico: raiz do monorepo (`context: ..` a partir de `infra/`). Exceção: `minha-delpi-ai-api` em **dev** usa context na pasta da API.

| Arquivo (path atual na raiz) | Alteração esperada |
|------------------------------|--------------------|
| `minha-delpi-ai-api/Dockerfile.prod` | `COPY minha-delpi-ai-api/…` → `COPY apis/minha-delpi-ai-api/…`; `COPY shared/delpi_auth` inalterado |
| `transformometro-api/Dockerfile` | `COPY transformometro-api/…` → `COPY apis/transformometro-api/…`; `COPY shared` inalterado |
| `tv-dashboard-api/Dockerfile` | Idem + `COPY scripts/generate_tv_data_routes_from_openapi.py` inalterado |
| `strategic-indicators-api/Dockerfile` | Idem padrão `apis/<api>/` + `shared` |
| `maintenance-api/Dockerfile` | Idem |
| `cipa-api/Dockerfile` | Idem |
| `customer-experience-api/Dockerfile` | Idem |
| `comite-etica-conduta-api/Dockerfile` | Idem |
| `minha-delpi-ai-api/Dockerfile.dev` / `Dockerfile.vision.dev` | Paths internos OK; só context no Compose |

`core-api` e `api-delpi` Dockerfiles: **sem mudança**.

---

## 6. Inventário — Compose / infra (snapshot ago/2026)

### `infra/docker-compose.yml`

- `dockerfile: minha-delpi-ai-api/Dockerfile.prod` → `apis/minha-delpi-ai-api/Dockerfile.prod`
- Sete serviços (`strategic-indicators-api` … `tv-dashboard-api`): `dockerfile: <api>/Dockerfile` → `apis/<api>/Dockerfile`
- `core-api` / `api-delpi`: **não tocar**

### `infra/docker-compose.dev.yml`

- `context: ../minha-delpi-ai-api` → `../apis/minha-delpi-ai-api`
- volume `../minha-delpi-ai-api:/app` → `../apis/minha-delpi-ai-api:/app`
- Sete× `dockerfile:` + sete× volumes `../<api>:/app` → `../apis/<api>/…`
- volumes `../shared:/shared` inalterados

### Outros compose

| Arquivo | Ação |
|---------|------|
| `infra/docker-compose.prod.vision.yml` | `dockerfile: apis/minha-delpi-ai-api/Dockerfile.prod` |
| `infra/docker-compose.vision.yml` | herda context do dev |
| `infra/docker-compose.minimal.yml` / `prod.cpu.yml` | só nomes de serviço — nada |
| `infra/scripts/up-*-sequential.sh` | nada |

### Docs/env em infra

- `infra/README-ambiente.md` — links/comandos com path de pasta
- Comentários PATH em `env.local.example`, `.env.dev.example`, `.env.prod.example`

---

## 7. Inventário — Python / scripts / CI (snapshot ago/2026)

### Dentro das APIs a mover

| Arquivo | Correção típica |
|---------|-----------------|
| `transformometro-api/pytest.ini` | `../shared` → `../../shared` |
| `minha-delpi-ai-api/scripts/sync_openapi_route_contract_shapes.py` | `parents[2]/api-delpi` → `parents[3]` |
| `minha-delpi-ai-api/scripts/audit_openapi_delpi_metadata.py` | idem |
| `minha-delpi-ai-api/scripts/audit_api_delpi_pac_onda1.py` | idem |
| `minha-delpi-ai-api/scripts/sync_transformometro_openapi.py` | path → `apis/transformometro-api` (+1 nível de raiz) |
| `minha-delpi-ai-api/scripts/generate_chat_feedback_reasons_ts.py` | raiz + path `apis/minha-delpi-ai-api` |
| `minha-delpi-ai-api/scripts/check_help_pr_gate.py` | prefixes git `apis/minha-delpi-ai-api/…` |
| `minha-delpi-ai-api/app/domain/services/chat_presentation_coverage_service.py` | `parents[4]/api-delpi` → `parents[5]` |
| `tv-dashboard-api/.../tv_data_openapi_catalog_service.py` | `parents[5]/api-delpi` → `parents[6]` |
| `tv-dashboard-api/.../tv_openapi_catalog_sync_service.py` | `parents[4]/scripts` → `parents[5]` |
| `tv-dashboard-api/tests/test_m_query_phase0_baseline.py` | raiz = `parents[3]`; path `apis/tv-dashboard-api` |

### `api-delpi` (permanece na raiz) apontando para APIs movidas

| Arquivo | Correção |
|---------|----------|
| `api-delpi/scripts/audit_openapi_operation_ids.py` | `REPO_ROOT / "apis" / "tv-dashboard-api" / …` |
| `api-delpi/scripts/apply_stable_operation_ids.py` | `apis/tv-dashboard-api` + `apis/minha-delpi-ai-api` |
| `api-delpi/scripts/validate_drawing_library.py` | `… / "apis" / "minha-delpi-ai-api"` |

### Scripts na raiz

| Arquivo | Correção |
|---------|----------|
| `scripts/ci-transformometro-api.sh` | `$ROOT/apis/transformometro-api` |
| `scripts/ci-maintenance-api.sh` | `$ROOT/apis/maintenance-api` |
| `scripts/generate-weekly-quality-report.sh` | `$ROOT/apis/minha-delpi-ai-api` |
| `scripts/homologacao/run_onda1_gate.sh` | idem |
| `scripts/check_tv_data_routes.py` | `ROOT / "apis" / "tv-dashboard-api" / …` |
| `scripts/generate_tv_data_routes_from_openapi.py` | idem |
| `scripts/check_tv_openapi_catalog_parity.py` | idem |
| `scripts/sync_tv_data_param_catalog.py` | idem |
| `scripts/enrich_tv_data_routes_pt.py` | idem |

### GitHub Actions

| Workflow | Alteração |
|----------|-----------|
| `.github/workflows/minha-delpi-ai-api-presentation.yml` | `paths`, `working-directory`, `cache-dependency-path` → `apis/minha-delpi-ai-api` |
| `.github/workflows/minha-delpi-ai-api-docie.yml` | idem |
| `.github/workflows/transformometro-api-routes.yml` | WD → `apis/transformometro-api`; `../shared` → `../../shared` |

---

## 8. Inventário — plugins / Cursor (snapshot ago/2026)

### Build-break

| Arquivo | Alteração |
|---------|-----------|
| `plugins/minha-delpi-chat/package.json` | scripts `sync:*` → `../../apis/minha-delpi-ai-api/…` |
| `plugins/minha-delpi-chat/src/ui/onboardingStarterModal.test.ts` | import JSON → `…/apis/minha-delpi-ai-api/…` |
| `plugins/minha-delpi-chat/scripts/capture-admin-baseline.sh` | path docs |

### Docs-only (links)

READMEs dos plugins pareados: `maintenance`, `cipa`, `comite-etica-conduta`, `customer-experience`, `transformometro`, `strategic-indicators`, `minha-delpi-chat` — `../../<api>/` → `../../apis/<api>/`.

### Sem mudança

Manifests `serviceName`, fetches `/apps/*-api`, vite/tsconfig dos MFEs, `portal/`, `shared/` (hostnames), `gateway/nginx*.conf`.

### Cursor

| Arquivo | Alteração |
|---------|-----------|
| `.cursor/rules/si-consolidated-department-idd.mdc` | `globs: apis/strategic-indicators-api/**` |
| `.cursor/rules/new-api-route-checklist.mdc` | `cd apis/minha-delpi-ai-api` |
| `.cursor/rules/development-standards-index.mdc` | links `../apis/minha-delpi-ai-api/docs/…` |
| `.cursor/rules/assistant-content-json.mdc` | path exemplo de sync MFE |

---

## 9. Validação pós-migração

1. Grep anti-regressão: zero paths de filesystem antigos das 8 pastas na raiz (`dockerfile: minha-delpi-ai-api/`, `ROOT / "tv-dashboard-api"`, volumes `../transformometro-api:`, etc.).
2. `docker compose -f infra/docker-compose.dev.yml config`
3. Build pontual via `./infra/scripts/up-dev-sequential.sh` (amostra: chat-api, api-delpi, tv-dashboard-api, uma API plugin).
4. Pytest amostra: transformômetro com `PYTHONPATH=.:../../shared`; gates chat que leem `api-delpi`.
5. Scripts TV na raiz (`check_tv_openapi_catalog_parity.py --check`) se o ambiente permitir.
6. Sync MFE chat (`npm run sync:*` relevantes).

---

## 10. Fora de escopo

- Renomear serviços Compose ou URLs `/apps/…`
- Mover `core-api` ou `api-delpi`
- Reescrever docs que só citam o **nome** do produto sem path de pasta
- Refatoração de código além de paths

---

## 11. Riscos

1. `parents[N]` errado — CI ok e script local falha (ou o contrário).
2. Replace cego de nome de API — corrompe nginx / `depends_on`.
3. Volume bind de dev esquecido — hot-reload aponta para pasta vazia na raiz.
4. CI transformômetro — com novo WD, `../shared` vira `../../shared`.

---

## 12. Histórico

| Data | Evento |
|------|--------|
| ago/2026 | Inventário inicial e playbook documentado; implementação **adiada** |
| _(retomada)_ | Preencher: data da revalidação do inventário + delta vs este snapshot |

### Plano Cursor (referência de trabalho)

Plano de trabalho associado (não substitui este playbook):  
`.cursor/plans/mover_apis_para_apis_*.plan.md` — marcar como adiados os todos até a retomada.
