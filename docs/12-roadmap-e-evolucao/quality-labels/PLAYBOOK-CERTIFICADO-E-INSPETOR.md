# Playbook — Certificado de Qualidade + Gestão de Inspetor (quality-labels)

> Status: **proposta / pré-implementação**
> Escopo: substituir o Certificado de Qualidade em Word (RQ-032) por um fluxo digital
> dentro do plugin **quality-labels**, com anexo por etiqueta, checklist assinalável,
> assinatura do inspetor e rastreio de cliente a partir da OP.

---

## 1. Objetivo

Hoje o inspetor preenche o **Certificado de Qualidade (RQ-032 – Rev.00 – 21/01/2021)** em
um arquivo Word, imprime, assina à mão e arquiva. Queremos:

1. **Certificado digital anexo à etiqueta** — botão na linha da etiqueta abre um modal onde
   o inspetor preenche o certificado, assinala cada item do checklist como **Aprovado (A) /
   Reprovado (R) / Não aplicável (---)** e pode **adicionar novas linhas** à lista.
2. **Gestão de inspetor** — nova aba onde o inspetor registra a **assinatura** dele, via
   **upload de imagem** (como no Word) **ou desenhando com caneta/tablet digital**.
3. **Dados de produto** — já resolvidos pelo plugin (snapshot da OP).
4. **Dados de cliente** — rastrear via OP quando possível; caso contrário, **campos editáveis**.
5. **Checklist com botões** que facilitem o uso no dia a dia (toques grandes, ações em massa).

---

## 2. Descobertas (pesquisa de viabilidade)

### 2.1 Rastreio de cliente a partir da OP — **parcial, autofill + editável**

- `SC2010.C2_PEDIDO` ("Ped. Venda que gerou a OP") e `C2_ITEMPV` ("Item do Pedido de Venda")
  **existem** no ambiente.
- JOIN validado no TOTVS real: `SC2 → SC5010 (C5_NUM) → SA1010 (A1_COD/A1_LOJA)` retorna o
  nome do cliente corretamente.
- **Porém:** apenas **~14.279 de 719.842 OPs (≈2%)** têm `C2_PEDIDO` preenchido. As OPs da
  DELPI são majoritariamente **make-to-stock** (geradas por MRP/estoque, sem pedido).
  As OPs de teste conhecidas (`24490601001`, `10278501001`, `24627601001`) estão **vazias**.

**Decisão:** autopreencher cliente **quando `C2_PEDIDO` existir**; sempre permitir **edição manual**.
Opcional (fase 2): sugerir clientes prováveis a partir do histórico produto→cliente
(`SA7010` / notas de saída `SD2010+SA1010`) já existente na api-delpi (`GET /products/{code}/customers`).

SQL de referência (a encapsular em repositório/use case novo, **não** SQL solto no use case):

```sql
SELECT
    RTRIM(OP.C2_PEDIDO)  AS sales_order,
    RTRIM(OP.C2_ITEMPV)  AS sales_order_item,
    RTRIM(C5.C5_CLIENTE) AS customer_code,
    RTRIM(C5.C5_LOJACLI) AS customer_store,
    RTRIM(A1.A1_NOME)    AS customer_name
FROM SC2010 OP WITH (NOLOCK)
LEFT JOIN SC5010 C5 WITH (NOLOCK)
    ON C5.D_E_L_E_T_ = '' AND C5.C5_FILIAL = OP.C2_FILIAL
   AND RTRIM(C5.C5_NUM) = RTRIM(OP.C2_PEDIDO)
LEFT JOIN SA1010 A1 WITH (NOLOCK)
    ON A1.D_E_L_E_T_ = '' AND A1.A1_COD = C5.C5_CLIENTE
   AND A1.A1_LOJA = C5.C5_LOJACLI
WHERE OP.D_E_L_E_T_ = '' AND RTRIM(OP.C2_OP) = ?
```

### 2.2 Storage persistente (assinatura/anexo) — padrão canônico existente

- Regra obrigatória: **metadado no Postgres + binário em volume Docker** (`persistent-upload-storage.mdc`).
- Modelos a copiar:
  - **Assinatura PNG** → `QualityLabelsQrService` (mesmo plugin) + `PhotoStorage` do customer-experience.
  - **Anexo/PDF** (se necessário) → `PacEvidenceStorage` (subdir por entidade, `FileResponse`).
- Base de host: `DELPI_DATA_HOST_DIR` (dev `${HOME}/.delpi`, prod `/var/lib/delpi`).
- Novos diretórios propostos:
  - `QUALITY_LABELS_SIGNATURE_DIR = /app/data/quality-labels/signatures`
  - (fase 2, se PDF server-side) `QUALITY_LABELS_CERTIFICATE_DIR = /app/data/quality-labels/certificates`

### 2.3 Estrutura atual do plugin (reuso)

- Frontend `plugins/quality-labels`: shell com abas (`App.tsx`), `QualityLabelsAdminPage`,
  `QualityLabelsAuditPage`, `AuditMetadataModal`, `qualityLabelsApi.ts`, `httpClient.ts`
  (já tem GET/POST/PATCH/DELETE; falta `postForm` multipart), `types/qualityLabels.ts`,
  `utils/labelPrint.ts` (modelo de impressão HTML/CSS a reaproveitar para o certificado).
- Backend api-delpi: `quality_labels_router.py`, `quality_labels_service.py`,
  `postgres_quality_labels_repository.py`, `postgres_quality_labels_audit_repository.py`,
  `quality_labels_composer.py`, migrations em `migrations/plugins/quality-labels`.
- Identidade do inspetor: `GET core-api/me` → só `id`, `name`, `email` (sem cargo/matrícula).
  Logo, a **gestão de inspetor** precisa de tabela própria (`inspectors`) para a assinatura.
- Permissões: `quality-labels.view` (leitura) e `quality-labels.write` (escrita).

---

## 3. Modelo de dados (novas migrations)

Schema `quality_labels`. Uma migration por incremento.

### V004 — Inspetores (assinatura)

```sql
CREATE TABLE IF NOT EXISTS quality_labels.inspectors (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            TEXT NOT NULL UNIQUE,          -- sub do Core API
    display_name       TEXT NOT NULL,
    role_title         TEXT,                          -- cargo livre (ex.: "Inspetor da Qualidade")
    signature_filename TEXT,                          -- PNG no volume
    signature_mime     TEXT,
    signature_updated_at TIMESTAMPTZ,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### V005 — Template do checklist (RQ-032 padrão, gerenciável)

```sql
CREATE TABLE IF NOT EXISTS quality_labels.checklist_template_items (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position    INTEGER NOT NULL,
    description TEXT NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Seed com os 17 itens do RQ-032 (ver anexo A).
```

### V006 — Certificado (1:1 com etiqueta) + itens

```sql
CREATE TABLE IF NOT EXISTS quality_labels.certificates (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label_id           UUID NOT NULL UNIQUE
                       REFERENCES quality_labels.inspection_labels(id) ON DELETE CASCADE,
    doc_ref            TEXT NOT NULL DEFAULT 'RQ-032 – Rev.00 – 21/01/2021',
    sample_type        TEXT NOT NULL DEFAULT 'fornecimento',  -- amostra | lote_piloto | fornecimento
    quantity           TEXT,                                  -- "10 peças" (texto livre p/ unidade)
    sample_quantity    TEXT,                                  -- "10 peças"
    -- Cliente (autofill via C2_PEDIDO quando houver; sempre editável)
    customer_code      TEXT,
    customer_store     TEXT,
    customer_name      TEXT,
    customer_item      TEXT,      -- "ITEM CLIENTE: 2229-07/1"
    customer_item_rev  TEXT,      -- "REV:00"
    customer_source    TEXT NOT NULL DEFAULT 'manual',        -- totvs | manual
    delpi_notes        TEXT,
    customer_notes     TEXT,
    inspector_user_id  TEXT NOT NULL,
    inspector_name     TEXT NOT NULL,
    status             TEXT NOT NULL DEFAULT 'draft',          -- draft | issued
    issued_at          TIMESTAMPTZ,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quality_labels.certificate_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    certificate_id  UUID NOT NULL
                    REFERENCES quality_labels.certificates(id) ON DELETE CASCADE,
    position        INTEGER NOT NULL,
    description     TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'A',   -- A (aprovado) | R (reprovado) | NA (---)
    is_custom       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ql_cert_items_cert
    ON quality_labels.certificate_items (certificate_id, position);
```

> **Nota:** os itens são **copiados do template no momento da criação** (snapshot), permitindo
> adicionar linhas custom e preservar o histórico mesmo que o template mude depois.

---

## 4. Backend (api-delpi)

### 4.1 Storage de assinatura

- `app/config.py`: `QUALITY_LABELS_SIGNATURE_DIR` (default `/app/data/quality-labels/signatures`).
- `infra/docker-compose.yml` + `docker-compose.dev.yml`: volume
  `${DELPI_DATA_HOST_DIR}/quality-labels/signatures:/app/data/quality-labels/signatures`.
- `infra/env.local.example` + `infra/README-ambiente.md`: documentar.
- `app/application/services/quality_labels/quality_labels_signature_storage.py`:
  classe `QualityLabelsSignatureStorage` (whitelist `image/png`, limite ~2 MB, `{user_id}.png`
  ou `{uuid}.png`, `write_bytes`, `read`, `delete`, proteção path traversal). Teste unitário
  `tests/**/test_quality_labels_signature_storage.py`.

### 4.2 Rastreio de cliente

- Port/repositório novo (produção): `fetch_sales_order_customer_by_op` no
  `production_orders_repository.py` (ou repositório dedicado `production_sales_link_repository.py`),
  encapsulando o SQL da §2.1 com `WITH (NOLOCK)` e cache curto.
- Use case `GetOrderCustomerByOpUseCase` + composição.
- Exposto **internamente** ao `QualityLabelsService` (chamada em processo, como já é feito com
  `GetProductionOrderByOpUseCase`), retornando `customer_*` + `customer_source='totvs'` ou `None`.

### 4.3 Repositórios (plugins)

- `postgres_quality_labels_inspector_repository.py`: upsert por `user_id`, get, set signature.
- `postgres_quality_labels_certificate_repository.py`: create/update certificate, replace items,
  get by label_id / id, payload admin/público.
- `postgres_quality_labels_checklist_template_repository.py`: list ativos, CRUD (fase 2).

### 4.4 Serviço

Estender/compor no `QualityLabelsService` (ou serviço dedicado `QualityLabelsCertificateService`
para não inflar o principal — preferir **serviço dedicado** por SRP):

- `get_or_init_certificate(label_id)` → certificado existente **ou** rascunho pré-preenchido
  (produto/OP da etiqueta + cliente via OP + itens do template).
- `save_certificate(label_id, payload, actor)` → upsert certificado + itens; grava evento de
  auditoria (`certificate_saved` / `certificate_issued`).
- `get_inspector(user_id)` / `save_inspector(user_id, display_name, role_title)` /
  `set_inspector_signature(user_id, png_bytes)` / `read_inspector_signature(user_id)`.

### 4.5 Rotas (`quality_labels_router.py`)

| Método | Path | Perm | operationId |
|---|---|---|---|
| GET | `/labels/{id}/certificate` | read | `get_quality_label_certificate` |
| PUT | `/labels/{id}/certificate` | write | `save_quality_label_certificate` |
| GET | `/labels/{id}/order-customer` | write | `get_quality_label_order_customer` (autofill) |
| GET | `/inspectors/me` | read | `get_quality_label_inspector` |
| PUT | `/inspectors/me` | write | `save_quality_label_inspector` |
| POST | `/inspectors/me/signature` (multipart) | write | `upload_quality_label_inspector_signature` |
| GET | `/inspectors/me/signature` | read | PNG binário |
| GET | `/checklist-template` | read | `list_quality_label_checklist_template` |

- Contratos em `route_contract_registry.py` (entities: `quality_label_certificate`,
  `quality_label_inspector`, `quality_label_checklist_item`, `quality_label_order_customer`).
- Auditoria: novos `event_type` (`certificate_saved`, `certificate_issued`, `signature_updated`).

### 4.6 Exposição pública (opcional, fase 2)

- `GET /public/quality-labels/certificate/{token}` para o cliente ver o certificado completo
  (não só o selo atual). Reusar `public-hub`. **Decisão pendente** (ver §8).

---

## 5. Frontend (plugins/quality-labels)

### 5.1 Infra

- `httpClient.ts`: adicionar `httpPutJson` (se faltar) e `httpPostForm` (multipart, sem setar
  `Content-Type`), espelhando o customer-experience.
- `qualityLabelsApi.ts`: `getCertificate`, `saveCertificate`, `getOrderCustomer`,
  `getInspector`, `saveInspector`, `uploadInspectorSignature`, `inspectorSignatureUrl`,
  `listChecklistTemplate`.
- `types/qualityLabels.ts`: `Certificate`, `CertificateItem`, `Inspector`, `OrderCustomer`.

### 5.2 Modal de Certificado (`components/CertificateModal.tsx`)

Aberto por botão **"Certificado"** (ícone `FileCheck`/`ScrollText`) na linha da etiqueta.

Layout, seguindo o RQ-032:

- **Cabeçalho:** logo Delpi + "CERTIFICADO DE QUALIDADE" + `doc_ref`.
- **Tipo de fornecimento:** três botões-seleção (Amostra / Lote Piloto / Fornecimento).
- **Bloco cliente/produto:** cliente (autofill/editável), item cliente + rev, item Delpi
  (= product_code), OP, quantidade, quantidade amostral.
  - Ao abrir: chamar `getOrderCustomer`; se `source=totvs`, preencher e marcar "via TOTVS"
    (badge), mantendo editável; se vazio, campos livres.
- **Checklist assinalável** (foco em uso diário):
  - Cada linha: nº, descrição e um **grupo de 3 botões segmentados**:
    **A** (verde) · **R** (vermelho) · **---** (cinza/N-A). Toque único alterna o status.
  - Barra de ações em massa: **"Tudo Aprovado"**, **"Limpar"**.
  - Botão **"+ Adicionar linha"** (descrição livre, `is_custom=true`); linha removível.
  - Itens carregados do template (via rascunho do backend) na primeira abertura.
- **Observações:** Delpi e Cliente (validação do projeto).
- **Assinatura:** exibe a assinatura do inspetor logado (se cadastrada); se não houver, aviso
  com atalho para a aba **Inspetor**.
- **Rodapé de ações:** Salvar rascunho · Emitir · **Imprimir/Exportar**.

### 5.3 Impressão do certificado (`utils/certificatePrint.ts`)

- Reaproveitar a técnica de `labelPrint.ts` (HTML+CSS, iframe, sem `about:blank`).
- Layout A4 fiel ao RQ-032 (tabela de itens com coluna Status A/R/---, blocos de assinatura).
- Assinatura do inspetor embutida como `<img>` (data-URL vinda do endpoint).
- Fase 2 (opcional): PDF server-side para arquivo imutável.

### 5.4 Aba "Inspetor" (`pages/QualityLabelsInspectorPage.tsx`)

- Nova aba no `App.tsx` (ao lado de Etiquetas / Auditoria), ícone `PenLine`/`UserCheck`.
- Formulário: nome de exibição, cargo (livre).
- **Assinatura** — dois modos numa mesma área:
  1. **Desenhar** (caneta/tablet): `<canvas>` com Pointer Events (suporta mouse, toque e
     caneta), botões **Limpar** e **Salvar**; export via `canvas.toBlob('image/png')`.
  2. **Upload de imagem** (PNG/JPG) → normaliza para PNG.
- Preview da assinatura atual + data de atualização.
- Envio via `uploadInspectorSignature` (multipart).

---

## 6. Anexo A — Itens padrão do checklist (RQ-032)

Seed de `checklist_template_items` (position, description):

1. Identificação e Embalagem do Produto
2. Dados Específicos do Desenho
3. Bitola dos Cabos (mm / AWG)
4. Coloração dos Cabos
5. Gravação / Numeração dos Cabos
6. Concentricidade dos Cabos
7. Aspecto / Aparência da Isolação
8. Comprimento total
9. Comprimento dos Decapes
10. Marcas ou Cortes no Condutor
11. Tipo e Aplicação do Terminal / Termostato
12. Fixação dos Terminais / Termostatos / Termistores
13. Aspecto de solda
14. Pontas Estanhadas
15. Aplicação do Conector
16. Teste de tração – (terminal do cliente, sem parâmetros)
17. Aspecto do Tubo Isolante / Termoencolhível

Legenda: **A** = Aprovado · **R** = Reprovado · **---** = Não aplicável.

---

## 7. Faseamento

**Fase 1 (MVP):**
- V004 (inspetores + assinatura) e aba Inspetor com canvas + upload.
- V005 (template) + seed dos 17 itens.
- V006 (certificado + itens).
- Autofill de cliente via `C2_PEDIDO` (editável).
- Modal de certificado com checklist A/R/--- e adição de linhas.
- Impressão HTML do certificado (RQ-032).

**Fase 2 (incrementos):**
- Sugestão de cliente por histórico produto→cliente.
- Gerenciamento do template de checklist na aba Inspetor/Admin.
- PDF server-side + exposição pública do certificado completo pelo QR.

---

## 8. Decisões (definidas)

1. **Certificado público via QR:** **NÃO** — o QR continua mostrando só o selo de inspeção
   atual. O certificado é interno/impresso (PDF).
2. **Assinatura do cliente:** **só campo de texto** ("Observações do Cliente") no MVP.
3. **Relação certificado × etiqueta:** **1:1** (um certificado por etiqueta).
4. **Numeração do certificado:** **referência fixa** `RQ-032 – Rev.00 – 21/01/2021`.
5. **PDF imutável:** **SIM no MVP** — PDF server-side (reportlab) gerado na emissão e
   armazenado no volume `QUALITY_LABELS_CERTIFICATE_DIR`.
6. **Escopo:** implementar **todo o MVP (Fase 1)** de uma vez.

---

## 9. Checklist de conformidade (regras do repo)

- [ ] Upload em disco → volume nos **dois** composes + `env.local.example` + `README-ambiente.md`
      (`persistent-upload-storage.mdc`).
- [ ] SQL novo (cliente por OP) medido (latência) + `WITH (NOLOCK)` + teste de repositório
      (`sql-query-development.mdc`).
- [ ] Rotas novas com `operation_id` + contrato no `route_contract_registry` + permissões
      (`new-api-route-checklist.mdc`).
- [ ] Texto PT / limites em conteúdo declarativo quando aplicável (api-delpi tem menos rigor
      que o chat, mas evitar mágicos).
- [ ] Domain sem infra; use case fino; serviço dedicado por SRP.
- [ ] Testes: storage de assinatura, repositório de certificado, autofill de cliente.
- [ ] Migrations idempotentes (`IF NOT EXISTS`) aplicadas no startup.

---

## 10. Referências

- Mapa do plugin e backend: pesquisa interna (quality-labels).
- Padrão de storage: `.cursor/rules/persistent-upload-storage.mdc`, `infra/README-ambiente.md`.
- Rastreio OP→cliente: validado via `POST /data/sql` (SC2→SC5→SA1) e `/system` (SX3 da SC2010).
- Playbook base do plugin: `docs/12-roadmap-e-evolucao/quality-labels/PLAYBOOK-EXCELENCIA.md`.
