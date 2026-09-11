# Etiquetas da Qualidade — `/quality/labels`

Inspeção por ordem de produção (OP), etiqueta com QR e certificado RQ-032.
CRUD **dentro da api-delpi** (schema `quality_labels`); MFE autenticado e
página pública no `public-hub`.

**Plugin:** [plugins/quality-labels/README.md](../../../plugins/quality-labels/README.md)  
**Página pública:** `/p/quality-labels/inspection/{token}`  
**Ajuda in-app:** `plugins/quality-labels/src/content/helpTooltips.ts`

## Contrato

Envelope `{ success, message, data, meta }` via `api_delpi_success`.
Binários (QR PNG, assinatura PNG, PDF) saem do envelope — `FileResponse`.

Três superfícies, três papéis (não misturar):

| Superfície | Conteúdo |
|---|---|
| Etiqueta 100×30 mm (frente) | QR + rótulo **CLIENTE** + `B1_REFEREN` (ou item do certificado) + OP · data |
| Etiqueta (verso) | Logo + selo + **DELPI** + código do produto |
| Página pública / metadados | Nome do cliente, código do cliente, `B1_CODDES`, OP, unidade, data, inspetor |

| Campo público | Origem | Notas |
|---|---|---|
| `customerReference` | `SB1.B1_REFEREN` | Item do certificado (`customerItem`) vence na etiqueta e no QR |
| `drawingCode` | `SB1.B1_CODDES` | Só QR/metadados; **não** vai para a etiqueta |
| `customerName` | Pedido da OP (`SC2→SC5→SA1`) ou última NF (`SD2+SA1`) | Display `COALESCE(A1_NREDUZ, A1_NOME)`; certificado vence no QR |

Etiquetas antigas **sem a chave** no snapshot: *live fetch* de `customerReference`/`drawingCode` no GET admin `/{id}` e no GET público; `customerName` só no GET público. O JSON persistido **não** é regravado.

O PDF do certificado **não** é exposto no QR.

## Permissões

| Código | Rotas |
|---|---|
| `quality-labels.view` | leitura (listagem, detalhe, QR, certificado, auditoria, inspetor) |
| `quality-labels.write` | escrita (também lê) |

`GET /customers/search` (SA1, usado no certificado) exige `api-delpi.access`.

## Admin (JWT)

Prefixo: `/quality/labels`

| Método | Path | operationId | Perm. |
|--------|------|-------------|-------|
| GET | `/search-ops` | `search_quality_label_ops` | write |
| GET | `/lookup-op/{production_order}` | `lookup_quality_label_op` | write |
| GET | `/checklist-template` | `list_quality_label_checklist_template` | view |
| GET | `/inspectors/me` | `get_quality_label_inspector` | view |
| PUT | `/inspectors/me` | `save_quality_label_inspector` | write |
| POST | `/inspectors/me/signature` | `upload_quality_label_inspector_signature` | write |
| GET | `/inspectors/me/signature` | `get_quality_label_inspector_signature` | view (PNG) |
| POST | `/` | `create_quality_label` | write |
| GET | `/` | `list_quality_labels` | view |
| GET | `/audit-events` | `list_quality_label_audit_events` | view |
| GET | `/{id}` | `get_quality_label` | view |
| GET | `/{id}/qr` | `get_quality_label_qr` | view (PNG) |
| PATCH | `/{id}/active` | `set_quality_label_active` | write |
| DELETE | `/{id}` | `delete_quality_label` | write |
| GET | `/{id}/certificate` | `get_quality_label_certificate` | view |
| PUT | `/{id}/certificate` | `save_quality_label_certificate` | write |
| GET | `/{id}/certificate/pdf` | `get_quality_label_certificate_pdf` | view (PDF) |

## Público (sem JWT)

Liberado em `auth_middleware` pelo prefixo `/public/quality-labels/`.

| Método | Path | operationId |
|--------|------|-------------|
| GET | `/public/quality-labels/inspection/{token}` | `get_public_quality_label_inspection` |

`data` (camelCase): `productCode`, `productDescription`, `productUnit`,
`productionOrder`, `branch`, `branchName`, `inspectedAt`, `inspectorName`,
`result`, `companyName`, `customerReference`, `customerName`, `drawingCode`.

```bash
curl -fsS http://localhost/apps/api-delpi/public/quality-labels/inspection/<token>
```

## Persistência

| Peça | Onde |
|------|------|
| Metadados | schema `quality_labels` (postgres-plugins) |
| QR PNG | `QUALITY_LABELS_QR_DIR` → `/app/data/quality-labels/qr` |
| Assinatura PNG | `QUALITY_LABELS_SIGNATURE_DIR` → `/app/data/quality-labels/signatures` |
| Certificado PDF | `QUALITY_LABELS_CERTIFICATE_DIR` → `/app/data/quality-labels/certificates` |

Não resetar o schema em produção. Aplicar só `up`.
