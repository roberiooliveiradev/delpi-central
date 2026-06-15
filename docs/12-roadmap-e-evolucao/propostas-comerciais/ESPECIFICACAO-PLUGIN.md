# Especificação funcional — Plugin Propostas Comerciais (estado atual)

> **Versão do plugin:** `0.1.0` (manifesto)  
> **Última revisão:** 2026-06-15  
> **Escopo:** comportamento implementado em `plugins/propostas-comerciais` + rotas `api-delpi` `/propostas-comerciais/*`.

Dados TOTVS: [ESPECIFICACAO-DADOS-TOTVS.md](./ESPECIFICACAO-DADOS-TOTVS.md).

---

## 1. Visão geral

Microfrontend (Module Federation) para o time comercial consultar **propostas comerciais ativas** no Protheus, visualizar detalhe operacional (cliente/prospect, contato, condições, itens) e **emitir PDF** com possibilidade de revisão editável antes da exportação.

**Características:**

- Consulta **read-only** — sem gravação no Protheus.
- Inteligência de formatação e resolução cliente/prospect **centralizada na API** (MFE consome JSON pronto).
- Suporte a oportunidades ligadas a **prospect** (`SUS010`) quando não há cliente em `SA1010`.

**URL base:** `/apps/propostas-comerciais`  
**Permissão:** `propostas-comerciais.view` (aceita também `api-delpi.access` e `dashboard-commercial.view` na API).

---

## 2. Arquitetura

```text
Portal (AppHost federado)
  → plugins/propostas-comerciais (React + Vite MF)
  → Gateway /apps/api-delpi/propostas-comerciais/*
  → api-delpi (use cases + formatter + PDF ReportLab)
  → SQL Server Protheus (ADY/AD1/ADZ/SA1/SUS/…)
```

| Camada | Responsabilidade |
|--------|------------------|
| MFE | Listagem, busca local, detalhe, modal de revisão PDF |
| Application | Use cases finos (`list`, `get`, `generate_pdf`) |
| Domain | `PropostaComercialFormatter`, overrides PDF, ports |
| Infrastructure | `queries.py`, `PropostaComercialRepository`, `PropostaComercialPdfRenderer` |

---

## 3. Rotas do Portal

| Rota | Página | Descrição |
|------|--------|-----------|
| `/apps/propostas-comerciais` | `PropostasComerciaisListPage` | Tabela de propostas recentes + busca |
| `/apps/propostas-comerciais/{proposta_interna}` | `PropostaComercialDetailPage` | Detalhe + botão «Emitir PDF» |

Roteamento client-side: `src/utils/route.ts` + `usePropostasComerciaisRouterPath`.

---

## 4. API (api-delpi)

Base no gateway: `/apps/api-delpi/propostas-comerciais`

| Método | Rota | `operationId` | `meta.shape` | Resposta |
|--------|------|---------------|--------------|----------|
| `GET` | `/` | `list_propostas_comerciais` | `paged_list` | JSON envelope |
| `GET` | `/{proposta_interna}` | `get_proposta_comercial` | `composite_analysis` | JSON envelope |
| `GET` | `/{proposta_interna}/pdf` | `export_proposta_comercial_pdf` | `document_export` | PDF inline |
| `POST` | `/{proposta_interna}/pdf` | `export_proposta_comercial_pdf` | `document_export` | PDF inline + body de overrides |

### 4.1 Listagem

**Query:** `limit` (1–200, default 100)

**`data`:**

```json
{
  "items": [
    {
      "proposta_interna": "004836",
      "numero_ov": "OV003590",
      "oportunidade": "003590",
      "versao": "01",
      "data": "12/06/2026",
      "cliente": "KRAH-ICE-BRASIL LTDA",
      "filial": "01",
      "quantidade_itens": 3
    }
  ],
  "total": 1
}
```

Critério SQL: propostas com `ADY_STATUS = 'A'`, ordenadas por data decrescente.

### 4.2 Detalhe

**`data`** — objeto com seções:

| Seção | Conteúdo |
|-------|----------|
| `cabecalho` | Proposta, OV, versão, datas, validade, filial, status, soma valores |
| `empresa` | Dados DELPI (filial emissora via `SYS_COMPANY`) + `site` configurável |
| `cliente` | Cadastro resolvido (cliente ou prospect) + `tipo_cadastro`, `is_prospect` |
| `contato` | Nome, e-mail, telefone, departamento |
| `condicoes` | Pagamento, ICMS, IPI, frete, embalagem |
| `vendedor` | Nome, cargo, contatos |
| `observacoes` | Texto memo normalizado |
| `itens[]` | Linhas com produto, NCM, preços, prazo, lote mínimo |

**Cliente / prospect** (`cliente`):

| Campo | Tipo | Notas |
|-------|------|-------|
| `codigo`, `loja`, `nome` | string | |
| `nome_fantasia` | string \| null | |
| `cnpj`, `cep`, `telefone` | string \| null | Formatados na API |
| `ie`, `email` | string \| null | |
| `tipo_cadastro` | `"cliente"` \| `"prospect"` \| null | |
| `is_prospect` | boolean | |

Erros: `404` + `PROPOSTA_COMERCIAL_NOT_FOUND` quando proposta inexistente ou inativa.

### 4.3 PDF

- **GET:** gera PDF com dados íntegros do Protheus (após formatter).
- **POST:** mesmo fluxo, aplicando `PropostaComercialPdfExportOverridesService` antes do render.
- Filename: `proposta-{numero_ov}.pdf` (ex.: `proposta-OV003590.pdf`).
- Logo opcional: env `PROPOSTAS_COMERCIAIS_PDF_LOGO_PATH`.

---

## 5. Regras de negócio

### 5.1 Escopo de propostas

| Regra | Detalhe |
|-------|---------|
| Status | Apenas `ADY_STATUS = 'A'` (ativa) |
| Escrita | Nenhuma alteração no Protheus |
| Identificador UI | `proposta_interna` (`ADY_PROPOS`) |

### 5.2 Cliente vs prospect

Ver [ESPECIFICACAO-DADOS-TOTVS.md §4](./ESPECIFICACAO-DADOS-TOTVS.md#4-cliente-vs-prospect).

Casos de regressão documentados:

| Proposta | OV | Expectativa |
|----------|-----|-------------|
| `004836` | OV003590 | KRAH-ICE-BRASIL LTDA, `tipo_cadastro = prospect` |
| `004839` | OV003591 | WEG LINHARES, `tipo_cadastro = cliente` |
| `004845` | OV003581 | AHT, `tipo_cadastro = cliente` |

### 5.3 Condições comerciais (labels)

| Código Protheus | Exibição |
|-----------------|----------|
| Frete `C` | CIF — frete por conta do vendedor |
| Frete `F` | FOB — frete por conta do comprador |
| Embalagem `1` | Embalagem padrão DELPI |

### 5.4 Valores

- Totais no cabeçalho: soma de `ADZ_TOTAL` dos itens da revisão ativa.
- Valores monetários formatados em BRL no JSON (`R$ …`) + campos `*_numerico` para cálculos/UI.

---

## 6. UI — listagem

| Elemento | Comportamento |
|----------|---------------|
| Cabeçalho | Título, subtítulo, botão Atualizar |
| Busca | Filtro **local** por OV, oportunidade, proposta interna ou nome do cliente |
| Tabela | Colunas: OV, proposta, data, cliente, filial, qtd. itens |
| Clique na linha | Navega para detalhe |
| Estados | Loading, erro (retry), vazio (com/sem busca) |

Limite fixo na API: `limit=100` (hook `usePropostasComerciaisList`).

---

## 7. UI — detalhe

Cards informativos:

- **Destaques:** OV, data, validade, soma valores, status.
- **Empresa DELPI:** razão social, CNPJ, IE, endereço, telefone, site.
- **Cliente:** nome, código, CNPJ, telefone, endereço, cidade/UF (dados já resolvidos API-side).
- **Contato comercial**
- **Condições comerciais**
- **Vendedor**
- **Observações** (texto multilinha)
- **Tabela de itens** (`ItensTable`)

Ação principal: **Emitir PDF** → abre `PropostaComercialPdfExportModal`.

---

## 8. Emissão de PDF — revisão editável

Fluxo:

1. Usuário abre modal «Revisão antes da exportação».
2. Campos editáveis pré-preenchidos com dados da API.
3. **Pré-visualizar** → `POST …/pdf` com overrides → iframe/blob URL.
4. **Exportar PDF** → download/abertura em nova aba.

### Campos editáveis (overrides)

| Grupo | Campos |
|-------|--------|
| Geral | `observacoes` |
| Contato | `nome`, `departamento`, `email`, `telefone` |
| Condições | `descricao`, `icms`, `ipi`, `frete`, `embalagem` |
| Vendedor | `nome`, `cargo`, `email`, `telefone` |

**Não editáveis** via overrides: cabeçalho, empresa, cliente, itens, `numero_ov`. Alterações afetam **somente o PDF exportado**, não o Protheus.

Implementação backend: `PropostaComercialPdfExportOverridesService` + schema Pydantic `PropostaComercialPdfExportRequest`.

---

## 9. Permissões

| Código | Onde | Descrição |
|--------|------|-----------|
| `propostas-comerciais.view` | Manifesto + RBAC | Acesso ao plugin e API |
| `api-delpi.access` | API (legado) | Acesso amplo api-delpi |
| `dashboard-commercial.view` | API (legado) | Dashboard comercial |

Registro do manifesto exige JWT com `apps.manage` ou superadmin.

Após registro, associar `propostas-comerciais.view` ao perfil comercial desejado.

---

## 10. Variáveis de ambiente (api-delpi)

| Variável | Default | Uso |
|----------|---------|-----|
| `PROPOSTAS_COMERCIAIS_EMPRESA_SITE` | `www.delpi.com.br` | Campo `empresa.site` no detalhe/PDF |
| `PROPOSTAS_COMERCIAIS_PDF_LOGO_PATH` | — | Caminho opcional para logo no PDF |
| `TOTVS_DB_*` | — | Conexão SQL Server (via `DB_*` no container) |

Alias legado aceito: `PROPOSTA_COMERCIAL_EMPRESA_SITE`.

---

## 11. Deploy e operação

| Item | Valor |
|------|--------|
| Manifesto | `plugins/propostas-comerciais/propostas-comerciais.manifest.json` |
| Container | `delpi-propostas-comerciais` |
| Compose dev | `infra/docker-compose.dev.yml` |
| Compose prod | `infra/docker-compose.yml` (target `production`) |
| Registro | `plugins/propostas-comerciais/scripts/register-manifest.sh` |
| Caller app header | `X-Delpi-Caller-App: propostas-comerciais` |

### Deploy típico (produção)

```bash
cd /opt/delpi-central
git pull --ff-only origin main

cd infra
docker compose -f docker-compose.yml up -d --build api-delpi propostas-comerciais
docker exec delpi-api-delpi curl -sf http://localhost:8000/health
curl -sI http://localhost/apps/propostas-comerciais/assets/remoteEntry.js | head -3
```

**Nota:** alterações só no backend exigem rebuild/restart de `api-delpi`; alterações só no MFE exigem rebuild de `propostas-comerciais`. Não é necessário `sync-api-delpi-openapi` para mudanças de payload sem novas rotas.

Ver também: [plugins/propostas-comerciais/README.md](../../../plugins/propostas-comerciais/README.md).

---

## 12. Estrutura do código (MFE)

```text
plugins/propostas-comerciais/src/
  api/              # propostasComerciaisApi.ts, httpClient.ts
  components/       # tabela, modal PDF, cards, busca
  hooks/            # listagem, detalhe, PDF, roteamento
  pages/            # list + detail
  types/            # contratos TypeScript espelhando API
  utils/            # rotas, navegação, busca local
```

Prefixo CSS: `dashboard-propostas-comerciais` / `pc-*` — tokens do portal (`--primary`, `--surface`, …).

---

## 13. Estrutura do código (api-delpi)

```text
api-delpi/app/
  application/propostas_comerciais/use_cases/
  domain/propostas_comerciais/
    services/       # formatter, pdf overrides
    ports/
  infrastructure/
    totvs/propostas_comerciais/   # queries + repository
    pdf/propostas_comerciais/     # ReportLab renderer
  interface/http/
    propostas_comerciais_controller.py
    schemas/proposta_comercial_pdf_schemas.py
tests/test_propostas_comerciais.py
```

---

## 14. Testes

```bash
# No container api-delpi ou venv local
pytest api-delpi/tests/test_propostas_comerciais.py -v
```

Cobertura: formatter (CNPJ, telefone, prospect), use cases, PDF renderer, rotas HTTP, overrides.

Build MFE:

```bash
cd plugins/propostas-comerciais && npm run build
```

---

## 15. Pendências / evoluções

- Documentação OpenAPI dedicada em `api-delpi/docs/api/` (rotas já no baseline OpenAPI).
- Exibir badge «Prospect» na UI quando `is_prospect === true` (dado já disponível na API).
- Filtros server-side (filial, vendedor, período) além da busca local.
- Integração chat IA para consulta de propostas (rotas já catalogadas no OpenAPI agent metadata).
- CI/smoke script dedicado (`check-propostas-comerciais.sh`) — hoje validação manual via curl.
