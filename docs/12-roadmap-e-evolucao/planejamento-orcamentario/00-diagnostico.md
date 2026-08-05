# 00 — Diagnóstico (Fase 0)

**Produto:** Planejamento Orçamentário 2027  
**Branch:** `feat/planejamento-orcamentario`  
**Data da inspeção:** 2026-08-04  
**Escopo desta etapa:** descoberta apenas — **sem** plugin, migrations, Compose, Gateway, RBAC em código ou commit.

---

## 1. Estado do repositório

| Item | Valor |
|------|-------|
| Branch | `feat/planejamento-orcamentario` (criada a partir de `main`) |
| Working tree | limpa (nada a commitar no início da Fase 0) |
| HEAD observado | merge `feat/portal-fornecedor` em `main` (`d934adc6f`) |
| Monorepo | portal, gateway, core-api, api-delpi, várias `*-api`, `plugins/*`, `shared/`, `infra/` |

**Não** foi feito stash, reset, alteração de produção nem commit nesta fase.

---

## 2. Arquivos de regra e documentação lidos

### 2.1 Instruções oficiais e legado (`documentos/`)

| Arquivo | Implicação relevante |
|---------|----------------------|
| `documentos/instrucoes_oficiais_gpt_arquiteto_delpi_central.md` | Papel de arquiteto; SSO Keycloak; JWT **sem** lista completa de permissões; RBAC via Core API; Clean Architecture FE/BE; manifesto de plugins; proibição de bypass de RBAC. |
| Demais arquivos em `documentos/` (arquitetura JWT, manifesto v2, microfrontends “oficial”, fases 0–3) | Visão histórica. **Divergência:** stack cita Flask como padrão; APIs de domínio atuais usam **FastAPI**. Manifesto schema 1.1.0 documentado, mas implementação vigente é **1.0.0** em `docs/05-plugin-system/`. Inventário de apps desatualizado vs. dezenas de MFEs atuais. |

**Fonte da verdade em conflito:** código + `docs/` + `.cursor/rules/` prevalecem sobre `documentos/`.

### 2.2 Regras Cursor aplicáveis (`.cursor/rules/`)

| Regra | Implicação para o orçamento |
|-------|-----------------------------|
| `development-standards-index.mdc` | Índice: novo plugin → checklist MFE + docs; CRUD com TOTVS → api-delpi; migrations imutáveis; só `up` em plugins. |
| `plugins-migrations-no-reset-prod.mdc` | Schema Postgres do plugin: **nunca** `reset` em prod. |
| `migrations-immutable-checksum.mdc` | Arquivo `V00N` aplicado = imutável. |
| `persistent-upload-storage.mdc` | Anexos (Carta, PDFs) exigem volume Compose + path em config. |
| `new-api-route-checklist.mdc` / `api-delpi-openapi-route-standards.mdc` / `api-delpi-response-contract.mdc` | Toda rota: envelope `api_delpi_success`, `operationId`, registry, RBAC constantes, locale EN/pt-BR, smoke. |
| `sql-query-development.mdc` / `totvs-product-patterns.mdc` | SQL TOTVS só com bind, `D_E_L_E_T_`, medição; não inventar convenção. |
| `infra-sequential-container-startup.mdc` | Deploy via `up-*-sequential.sh`; remote `plugin-ui` antes de MFE. |
| `plugins-reusable-components.mdc` / `plugins-visual-design-system.mdc` / `plugins-frontend-build.mdc` | UI via `@delpi/plugin-ui`; zero CSS espelho do kit no MFE. |
| `plugins-documentation.mdc` | README + inventário obrigatórios (fase de implementação). |
| `mf-federation-patch-safety.mdc` | Não alterar patch MF sem testes anti-ReDoS. |
| `test-and-commit.mdc` | Testes no escopo; commit só se pedido. |
| Regras de chat/apresentação | Aplicáveis se rotas forem expostas ao chat; **fora do MVP** do orçamento (adiável). |

### 2.3 Documentação canônica `docs/`

| Doc | Implicação |
|-----|------------|
| `docs/05-plugin-system/novo-plugin-mfe-checklist.md` | Scaffold MF federado; `preparePluginUiRemote`; Compose `*plugin-ui-federated`; registro Core API. |
| `docs/05-plugin-system/manifesto-plugin.md` | Contrato manifesto 1.0.0. |
| `infra/README-ambiente.md` | Volumes, scripts sequenciais, env. |
| `api-delpi/docs/api/openapi-bilingue-catalogo-canonico.md` | Como construir rotas futuras. |
| `api-delpi/docs/api/financeiro-despesas-centro-custo.md` | Padrão de leitura CC via view TOTVS. |
| `docs/12-roadmap-e-evolucao/maintenance/PLAYBOOK-01-fronteiras-api-delpi.md` | Fronteira canônica: SQL Protheus **só** na api-delpi; API dedicada orquestra Postgres + gateway HTTP. |

---

## 3. Stack e padrões técnicos observados

| Tecnologia | Versão / padrão |
|------------|-----------------|
| React / React DOM | 19.2.7 (plugins recentes) |
| Vite | ^7.3.1 |
| Module Federation | `@originjs/vite-plugin-federation` ^1.4.1; remote `@delpi/plugin-ui` |
| TypeScript | ~5.9.x |
| Node (Docker MFE) | node:20-alpine |
| Python APIs | 3.11-slim; FastAPI |
| Excel/PDF na api-delpi | openpyxl, reportlab, pandas |
| Auth | Keycloak → Portal `getAccessToken` → MFE `Authorization: Bearer` + `X-Delpi-Caller-App` → `shared/delpi_auth` + Core API permissões |
| Design system | `import { … } from "@delpi/plugin-ui/index"` + dual-class `delpi-ui-*` |
| Infra | `infra/scripts/up-dev-sequential.sh`, `up-prod-sequential.sh` |

---

## 4. Padrão backend no monorepo

| Abordagem | Quando o repo usa | Exemplos |
|-----------|-------------------|----------|
| **Módulo em `api-delpi` + schema `postgres-plugins`** | CRUD médio, workflow, anexos, export, leitura TOTVS no mesmo serviço | LNF, PAC, Auditoria 5S, reports, canal-denúncia |
| **API dedicada `*-api`** | Domínio grande / lifecycle próprio; MFE **não** fala TOTVS; SQL via client → api-delpi | transformometro, cipa, CEC, maintenance, SI, TV, CX |

Migrations de plugins: `api-delpi/migrations/plugins/{slug}/` + `run_plugins_migrations.py` (prod: só `up`).

---

## 5. Materiais do processo orçamentário

| Material | Local | Status da análise |
|----------|-------|-------------------|
| Orçamento de Pessoal 2027 | `Downloads/Orcamento Pessoal - 2027.xlsx` (cópia local `.local/po-materials/`) | Analisado (template zerado) |
| CAPEX / Investimentos 2027 | `Downloads/Orçamento de Investimentos - 2027.xls` | SST + abas; células BIFF parcialmente ilegíveis sem xlrd; estrutura confirmada via SST + planilha TI 2026 |
| Carta do Orçamento | `Downloads/Carta Orcamento - 2027.doc` | Texto extraído; **conteúdo refere-se a 2026** |
| Previsão de Receita (apresentação) | — | **Não encontrada** no repo nem em Downloads/Desktop sob nomes óbvios |
| Protótipo `Projeto-orcamento` | Desktop | Domínio **diferente** (solicitação de orçamento interno / OS) — **não** reutilizar como base do planejamento anual |

Detalhamento: `01-especificacao-funcional-consolidada.md` e inconsistências em `10-riscos-pendencias-e-decisoes.md`.

---

## 6. ERP — resumo executivo

| Dado | Situação |
|------|----------|
| ROL / faturamento | **Confirmado no código** (`GET /financial/rol`, SD2/SD1) |
| Pedidos / carteira | **Confirmado** (`pedidos-venda-abertos`, SC5/SF2) |
| Clientes / vendedores / fornecedores | **Confirmado** (SA1, SA3, SA2) |
| Filiais 01/02 | **Confirmado** |
| Centros de custo / conta contábil | **Parcial** — via `dbo.vw_fin_despesas_centro_custo` (não há SQL direto `CTT010` no repo) |
| Grupos econômicos | **Não encontrado** no código |
| Quadro de pessoal / cargos TOTVS | **Não encontrado** (RH da api-delpi lê Portal RH Postgres, não SRV/SRJ) |
| CAPEX histórico TOTVS | **Não encontrado** |

**Docker/TOTVS live:** daemon Docker indisponível nesta sessão — **nenhum SELECT** executado no banco. Classificações “confirmado no banco” ficam pendentes de homologação.

---

## 7. Diagnóstico executivo

1. O produto cabe como **plugin MFE federado** + **domínio em api-delpi** com schema Postgres próprio (padrão LNF/PAC), com leituras TOTVS reutilizando rotas/view existentes e novas queries só após descoberta documentada.
2. API dedicada **não** é a escolha default: aumenta Compose/Gateway/deploy sem benefício claro enquanto o volume de regras e o acoplamento a TOTVS forem os de um processo anual colaborativo.
3. Planilhas atuais são o contrato de negócio implícito, mas há **lacunas e inconsistências** (Carta 2026 vs arquivo 2027; Carta pede cargo/CC e nacional/importado; Pessoal só agrega áreas; Receita sem material).
4. Autorização precisará de **duas dimensões** (RBAC funcional + escopo unidade/área/CC) — padrão de filial existe; escopo por CC **ainda não** tem modelo canônico no Core e deverá nascer no domínio do plugin (com enforcement na API).
5. Prazo (lançamento 01/10/2026) exige MVP enxuto: exercício + Carta/confirmação + CAPEX + Pessoal agregado + workflow simples + consolidação + export Excel; receita detalhada e integração profunda ERP são risco se não priorizadas.

---

## 8. Comandos e consultas executados (Fase 0)

- `git status`, `git branch`, `git log`
- Leitura de docs/regras e exploração de plugins/APIs (grep/read)
- Cópia dos materiais para `.local/po-materials/` (artefato local de análise; **não** é código de produção)
- Parse XML de `.xlsx` (pessoal, CAPEX TI 2026) e extração de texto da Carta `.doc`
- Parse parcial BIFF do CAPEX 2027 (SST/abas); células numéricas não recuperadas sem biblioteca xlrd
- Tentativa de Docker (`docker ps` / `docker run`) — **falhou** (socket indisponível)
- **Nenhum** `INSERT`/`UPDATE`/`DELETE`/DDL no ERP

---

## 9. Confirmação de não-implementação

- Nenhum plugin criado  
- Nenhuma migration criada  
- Nenhum manifesto registrado  
- Compose / Gateway / RBAC de produção **não** alterados  
- Nenhum commit criado  
