# Etiquetas da Qualidade (quality-labels)

Microfrontend do portal Minha DELPI para o inspetor da qualidade registrar a
inspeção de um produto a partir da **ordem de produção (OP)** e gerar uma
**etiqueta com QR code**. O cliente lê o QR e acessa os dados da inspeção numa
página pública (sem login) servida pelo `public-hub`.

## Arquitetura

- **Frontend (este plugin):** React 19 + Vite + Module Federation. Exposto em
  `/apps/quality-labels`. Consome a `api-delpi`.
- **Backend (CRUD):** vive **dentro da `api-delpi`** (não há API dedicada).
  - Módulo HTTP: `app/interface/http/routes/quality/quality_labels_router.py`
    (admin, prefixo `/quality/labels`) e `quality_labels_public_router.py`
    (público, prefixo `/public/quality-labels`).
  - Dados: PostgreSQL de plugins, schema `quality_labels`
    (migration `api-delpi/migrations/plugins/quality-labels`).
  - OP → produto: chamada **em processo** ao use case
    `get_production_order_by_op` (TOTVS), sem HTTP interno.
  - Identidade do inspetor: `get_current_user()` (delpi_auth / Core API).
  - QR: `QualityLabelsQrService`, PNG persistido em `QUALITY_LABELS_QR_DIR`.
- **Página pública:** `public-hub` app `quality-labels`, view `inspection`,
  rota `/p/quality-labels/inspection/{token}`.

## Rotas da API (api-delpi)

| Método | Rota | Permissão | operationId |
|--------|------|-----------|-------------|
| GET | `/quality/labels/lookup-op/{op}` | `quality-labels.write` | `lookup_quality_label_op` |
| POST | `/quality/labels` | `quality-labels.write` | `create_quality_label` |
| GET | `/quality/labels` | `quality-labels.view` | `list_quality_labels` |
| GET | `/quality/labels/{id}` | `quality-labels.view` | `get_quality_label` |
| GET | `/quality/labels/{id}/qr` | `quality-labels.view` | (PNG) |
| PATCH | `/quality/labels/{id}/active` | `quality-labels.write` | `set_quality_label_active` |
| GET | `/public/quality-labels/inspection/{token}` | pública (token) | `get_public_quality_label_inspection` |

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
