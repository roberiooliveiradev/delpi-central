# Etiquetas da Qualidade (quality-labels)

Microfrontend do portal Minha DELPI para o inspetor da qualidade registrar a
inspeção de um produto a partir da **ordem de produção (OP)**, gerar uma
**etiqueta com QR code** e emitir o **certificado de qualidade (RQ-032)**. O
cliente lê o QR e acessa os dados da inspeção numa página pública (sem login)
servida pelo `public-hub`.

## Funcionalidades

- **Etiquetas + QR code:** registra a inspeção por OP (busca automática do
  produto/unidade no TOTVS), gera a etiqueta e o QR público. A etiqueta física
  100×30 mm usa o rótulo **CLIENTE** e a **referência do cadastro**
  (`SB1.B1_REFEREN`). Nome do cliente, código do desenho (`SB1.B1_CODDES`) e
  demais detalhes ficam nos **metadados de auditoria** e na **página pública do
  QR**. Se o certificado tiver item preenchido à mão, esse valor prevalece na
  etiqueta. O **código Delpi** fica só no verso. Sem referência no cadastro, a
  frente sai só com OP e data.
- **Certificado de qualidade (RQ-032):** seção expansível no formulário de registro
  (collapse) e painel inline na lista de etiquetas — **sem modal**. Checklist A/R/NA,
  linhas customizáveis, busca de cliente TOTVS (SA1) e observações. Ao registrar com
  a seção aberta, o rascunho é salvo automaticamente; edições posteriores (rascunho
  ou emissão de PDF) geram eventos na aba **Auditoria** (`certificate_saved` /
  `certificate_issued`).
- **Aba Inspetor:** perfil (nome/cargo) e **assinatura** (desenho em canvas com
  mouse/caneta-tablet ou upload de imagem). Perfil e assinatura são
  **vinculados ao login** — cada inspetor só edita a própria.
- **Auditoria:** aba dedicada com toda a trilha (criação, emissão de
  certificado, exclusão, etc.).

## Contrato vigente — etiqueta × QR × metadados

Três superfícies, três papéis. Não misturar.

| Superfície | O que o usuário vê |
|---|---|
| **Etiqueta física 100×30 mm (frente)** | QR + rótulo **CLIENTE** + referência (`SB1.B1_REFEREN`, ou item manual do certificado) + OP · data |
| **Etiqueta física (verso)** | Logo Delpi + selo + **DELPI** + código do produto |
| **Página pública do QR** | Produto, **nome do cliente**, **código do cliente**, **código do desenho** (`SB1.B1_CODDES`), OP, unidade, data, inspetor |
| **Metadados de auditoria** | Snapshot da OP, produto (`customerReference`, `drawingCode`) e cliente (`name`, `legalName`, `source`) |

| Dado | Origem TOTVS | Etiqueta | QR / metadados |
|---|---|---|---|
| Referência do cliente | `SB1.B1_REFEREN` | sim (rótulo CLIENTE) | sim («Código do cliente») |
| Código do desenho | `SB1.B1_CODDES` | não | sim («Código do desenho») |
| Nome do cliente | pedido da OP (`SC2→SC5→SA1`) ou, se a OP for para estoque, última NF (`SD2+SA1`); display `COALESCE(A1_NREDUZ, A1_NOME)` | não | sim («Cliente») |

Item do certificado (`customerItem`) vence `B1_REFEREN` só na etiqueta e no «Código do cliente» público. Nome do certificado vence o snapshot no QR.

Etiquetas antigas **sem a chave** no JSON recebem *live fetch* **sem regravar** o snapshot:

| Campo | GET admin (`/{id}`) | GET público |
|---|---|---|
| `customerReference` / `drawingCode` | sim | sim |
| `customerName` | não | sim (se a chave nunca foi capturada) |

Ajuda in-app: `src/content/helpTooltips.ts`. Doc da API: [quality-labels.md](../../api-delpi/docs/api/quality-labels.md). Índice do roadmap: [docs/12-roadmap-e-evolucao/quality-labels/README.md](../../docs/12-roadmap-e-evolucao/quality-labels/README.md).

## Arquitetura

- **Frontend (este plugin):** React 19 + Vite + Module Federation. Exposto em
  `/apps/quality-labels`. Consome a `api-delpi`.
- **Backend (CRUD):** vive **dentro da `api-delpi`** (não há API dedicada).
  - Módulo HTTP: `app/interface/http/routes/quality/quality_labels_router.py`
    (admin, prefixo `/quality/labels`) e `quality_labels_public_router.py`
    (público, prefixo `/public/quality-labels`).
  - Dados: PostgreSQL de plugins, schema `quality_labels`
    (migrations em `api-delpi/migrations/plugins/quality-labels`).
  - OP → produto: chamada **em processo** ao use case
    `get_production_order_by_op` (TOTVS), sem HTTP interno.
  - Produto → referência do cliente e código do desenho:
    `ProductRepository.fetch_product_by_code` (`SB1.B1_REFEREN` /
    `SB1.B1_CODDES`), persistidos no snapshot `audit_metadata`.
  - Cliente (QR/metadados): pedido da OP (`get_order_customer_by_op`, SC2 → SC5 →
    SA1) ou, se a OP não tiver pedido, última NF do produto (`SD2` + SA1).
    Nome de exibição: `COALESCE(A1_NREDUZ, A1_NOME)`.
  - Busca de cliente: rota canônica `GET /customers/search` (SA1).
  - Identidade do inspetor: `get_current_user()` (delpi_auth / Core API).
  - QR: `QualityLabelsQrService`, PNG persistido em `QUALITY_LABELS_QR_DIR`.
  - Assinatura: PNG persistido em `QUALITY_LABELS_SIGNATURE_DIR`.
  - Certificado: PDF (reportlab/svglib) persistido em
    `QUALITY_LABELS_CERTIFICATE_DIR`.
- **Página pública:** `public-hub` app `quality-labels`, view `inspection`,
  rota `/p/quality-labels/inspection/{token}`. O certificado é uso
  interno/impresso (PDF), **não** é exposto no QR público.
- **HTTP client:** header `X-Delpi-Caller-App: quality-labels`.

## Rotas da UI

O MFE é uma única rota de portal (`/apps/quality-labels`) com abas internas
(não são paths HTTP separados):

| Aba | Conteúdo |
|---|---|
| Etiquetas | Registrar OP, lista, imprimir, página pública, certificado inline, snapshot |
| Inspetor | Perfil e assinatura do login atual |
| Auditoria | Trilha de eventos (`certificate_saved`, `certificate_issued`, etc.) |

Página pública (sem login): `/p/quality-labels/inspection/{token}`.

## Permissões (Portal)

| Código | Uso |
|---|---|
| `quality-labels.view` | Menu, listagem, detalhe, QR, certificado, auditoria, perfil |
| `quality-labels.write` | Registrar, desativar, excluir, salvar certificado/inspetor (também lê) |

A busca SA1 do certificado (`GET /customers/search`) exige `api-delpi.access`.

## Rotas da API (api-delpi)

| Método | Rota | Permissão | operationId |
|--------|------|-----------|-------------|
| GET | `/quality/labels/search-ops` | `quality-labels.write` | `search_quality_label_ops` |
| GET | `/quality/labels/lookup-op/{op}` | `quality-labels.write` | `lookup_quality_label_op` |
| GET | `/quality/labels/checklist-template` | `quality-labels.view` | `list_quality_label_checklist_template` |
| GET | `/quality/labels/inspectors/me` | `quality-labels.view` | `get_quality_label_inspector` |
| PUT | `/quality/labels/inspectors/me` | `quality-labels.write` | `save_quality_label_inspector` |
| POST | `/quality/labels/inspectors/me/signature` | `quality-labels.write` | `upload_quality_label_inspector_signature` |
| GET | `/quality/labels/inspectors/me/signature` | `quality-labels.view` | `get_quality_label_inspector_signature` |
| POST | `/quality/labels` | `quality-labels.write` | `create_quality_label` |
| GET | `/quality/labels` | `quality-labels.view` | `list_quality_labels` |
| GET | `/quality/labels/audit-events` | `quality-labels.view` | `list_quality_label_audit_events` |
| GET | `/quality/labels/{id}` | `quality-labels.view` | `get_quality_label` |
| GET | `/quality/labels/{id}/qr` | `quality-labels.view` | `get_quality_label_qr` |
| PATCH | `/quality/labels/{id}/active` | `quality-labels.write` | `set_quality_label_active` |
| DELETE | `/quality/labels/{id}` | `quality-labels.write` | `delete_quality_label` |
| GET | `/quality/labels/{id}/certificate` | `quality-labels.view` | `get_quality_label_certificate` |
| PUT | `/quality/labels/{id}/certificate` | `quality-labels.write` | `save_quality_label_certificate` |
| GET | `/quality/labels/{id}/certificate/pdf` | `quality-labels.view` | `get_quality_label_certificate_pdf` |
| GET | `/public/quality-labels/inspection/{token}` | pública (token) | `get_public_quality_label_inspection` |
| GET | `/customers/search` | `api-delpi.access` | `search_customers` |

## Armazenamento persistente

Metadado no PostgreSQL + binário em volume Docker (ver
`persistent-upload-storage.mdc` e `infra/README-ambiente.md`):

| Conteúdo | Variável | Padrão no container |
|----------|----------|---------------------|
| QR code (PNG) | `QUALITY_LABELS_QR_DIR` | `/app/data/quality-labels/qr` |
| Assinatura do inspetor (PNG) | `QUALITY_LABELS_SIGNATURE_DIR` | `/app/data/quality-labels/signatures` |
| Certificado (PDF) | `QUALITY_LABELS_CERTIFICATE_DIR` | `/app/data/quality-labels/certificates` |

## Desenvolvimento

```bash
npm install
npm run dev      # servidor Vite local
npm run build    # tsc + vite build (gera dist/)
npm run lint
```

## Registro do plugin no portal

```bash
BASE_URL=http://localhost TOKEN=<jwt-admin> ./scripts/register-manifest.sh
```

Depois, atribua `quality-labels.view` e `quality-labels.write` ao perfil dos inspetores.

## Smoke

```bash
curl -fsS http://localhost/apps/quality-labels/assets/remoteEntry.js | head
curl -fsS http://localhost/apps/api-delpi/public/quality-labels/inspection/<token>
```

Rebuild sequencial do MFE: `./infra/scripts/up-dev-sequential.sh --build quality-labels`.

## Estrutura `src/`

```text
App.tsx                         abas Etiquetas / Inspetor / Auditoria
content/helpTooltips.ts         Ajuda in-app (fonte dos textos)
pages/QualityLabelsAdminPage.tsx
pages/QualityLabelsInspectorPage.tsx
pages/QualityLabelsAuditPage.tsx
utils/labelPrint.ts             imprime via @delpi/plugin-ui (delpiCableLabel.ts)
components/CertificateEditor.tsx + CertificateFormFields.tsx
components/AuditMetadataModal.tsx
```

## Migrations

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin quality-labels
```

Migrations do schema `quality_labels`:

- `V001` — etiquetas de inspeção (`inspection_labels`).
- `V002` — metadados de auditoria.
- `V003` — trilha de eventos de auditoria.
- `V004` — perfis de inspetor (`inspectors`).
- `V005` — template do checklist do certificado (`checklist_template_items`).
- `V006` — certificados e itens (`certificates`, `certificate_items`).
- `V007` — quantidade de peças inspecionadas (`inspected_quantity`).
