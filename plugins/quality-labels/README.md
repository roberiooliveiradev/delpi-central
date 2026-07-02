# Etiquetas da Qualidade (quality-labels)

Microfrontend do portal Minha DELPI para o inspetor da qualidade registrar a
inspeção de um produto a partir da **ordem de produção (OP)**, gerar uma
**etiqueta com QR code** e emitir o **certificado de qualidade (RQ-032)**. O
cliente lê o QR e acessa os dados da inspeção numa página pública (sem login)
servida pelo `public-hub`.

## Funcionalidades

- **Etiquetas + QR code:** registra a inspeção por OP (busca automática do
  produto/unidade no TOTVS), gera a etiqueta e o QR público.
- **Certificado de qualidade (RQ-032):** modal com checklist conforme/não
  conforme (A/R/NA), linhas customizáveis, dados do cliente e observações.
  Ao emitir, gera um **PDF imutável** no servidor (1 certificado por etiqueta).
  - Pode ser aberto pela lista **ou** direto do formulário de registro
    (botão "Registrar e gerar certificado").
  - **Busca de cliente TOTVS (SA1)** por proximidade no campo de cliente
    (autocomplete via `GET /customers/search`); dados continuam editáveis.
  - "Quantidade amostral" é pré-preenchida com a quantidade de peças
    inspecionadas informada no registro.
- **Aba Inspetor:** perfil (nome/cargo) e **assinatura** (desenho em canvas com
  mouse/caneta-tablet ou upload de imagem). Perfil e assinatura são
  **vinculados ao login** — cada inspetor só edita a própria.
- **Auditoria:** aba dedicada com toda a trilha (criação, emissão de
  certificado, exclusão, etc.).

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
  - OP → cliente (best-effort): `get_order_customer_by_op` (SC2 → SC5 → SA1).
  - Busca de cliente: rota canônica `GET /customers/search` (SA1).
  - Identidade do inspetor: `get_current_user()` (delpi_auth / Core API).
  - QR: `QualityLabelsQrService`, PNG persistido em `QUALITY_LABELS_QR_DIR`.
  - Assinatura: PNG persistido em `QUALITY_LABELS_SIGNATURE_DIR`.
  - Certificado: PDF (reportlab/svglib) persistido em
    `QUALITY_LABELS_CERTIFICATE_DIR`.
- **Página pública:** `public-hub` app `quality-labels`, view `inspection`,
  rota `/p/quality-labels/inspection/{token}`. O certificado é uso
  interno/impresso (PDF), **não** é exposto no QR público.

## Rotas da API (api-delpi)

| Método | Rota | Permissão | operationId |
|--------|------|-----------|-------------|
| GET | `/quality/labels/search-ops` | `quality-labels.write` | `search_quality_label_ops` |
| GET | `/quality/labels/lookup-op/{op}` | `quality-labels.write` | `lookup_quality_label_op` |
| GET | `/quality/labels/checklist-template` | `quality-labels.view` | `list_quality_label_checklist_template` |
| GET | `/quality/labels/inspectors/me` | `quality-labels.view` | `get_quality_label_inspector` |
| PUT | `/quality/labels/inspectors/me` | `quality-labels.write` | `save_quality_label_inspector` |
| POST | `/quality/labels/inspectors/me/signature` | `quality-labels.write` | `upload_quality_label_inspector_signature` |
| GET | `/quality/labels/inspectors/me/signature` | `quality-labels.view` | (PNG) |
| POST | `/quality/labels` | `quality-labels.write` | `create_quality_label` |
| GET | `/quality/labels` | `quality-labels.view` | `list_quality_labels` |
| GET | `/quality/labels/audit-events` | `quality-labels.view` | `list_quality_label_audit_events` |
| GET | `/quality/labels/{id}` | `quality-labels.view` | `get_quality_label` |
| GET | `/quality/labels/{id}/qr` | `quality-labels.view` | (PNG) |
| PATCH | `/quality/labels/{id}/active` | `quality-labels.write` | `set_quality_label_active` |
| DELETE | `/quality/labels/{id}` | `quality-labels.write` | `delete_quality_label` |
| GET | `/quality/labels/{id}/certificate` | `quality-labels.view` | `get_quality_label_certificate` |
| PUT | `/quality/labels/{id}/certificate` | `quality-labels.write` | `save_quality_label_certificate` |
| GET | `/quality/labels/{id}/certificate/pdf` | `quality-labels.view` | (PDF) |
| GET | `/public/quality-labels/inspection/{token}` | pública (token) | `get_public_quality_label_inspection` |
| GET | `/customers/search` | `api-delpi.access` | `search_customers` |

## Armazenamento persistente

Metadado no PostgreSQL + binário em volume Docker (ver
`persistent-upload-storage.mdc` e `infra/README-ambiente.md`):

| Conteúdo | Variável | Padrão no container |
|----------|----------|---------------------|
| QR code (PNG) | `QUALITY_LABELS_QR_DIR` | `/app/data/quality-labels-qr` |
| Assinatura do inspetor (PNG) | `QUALITY_LABELS_SIGNATURE_DIR` | `/app/data/quality-labels-signatures` |
| Certificado (PDF) | `QUALITY_LABELS_CERTIFICATE_DIR` | `/app/data/quality-labels-certificates` |

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

Depois, atribua a permissão `quality-labels.write` ao perfil dos inspetores.

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
