# Playbook de Excelência — Customer Experience DELPI

> **Arquivo:** `docs/12-roadmap-e-volucao/customer-experience/PLAYBOOK-EXCELENCIA.md`  
> **Versão:** 1.2  
> **Data:** 2026-07-07  
> **Status:** Onda 0 e formulários avançados (jul/2026) **implementados**; ondas 2–3 em backlog

**Relacionado:**

- [plugins/customer-experience/README.md](../../../plugins/customer-experience/README.md) — plugin admin (rotas, prévia, build)
- [customer-experience-api/docs/forms-api.md](../../../customer-experience-api/docs/forms-api.md) — contrato HTTP de formulários
- [ROADMAP-FORMULARIOS-JUL2026.md](./ROADMAP-FORMULARIOS-JUL2026.md) — entregas jul/2026
- [plugins/public-hub/README.md](../../../plugins/public-hub/README.md) — shell público
- [docs/08-plugins/README.md](../../08-plugins/README.md) — inventário de plugins

---

## 1. North Star

Programa de **recepção de visitantes** com momento memorável e rastreável:

1. Cadastro rápido (foto, empresa, data) no portal autenticado.
2. QR personalizado e imprimível (agradecimento + formulários).
3. Páginas públicas sem login (`public-hub`).
4. API dedicada desacoplada da `api-delpi`, com token opaco e volumes persistentes.

---

## 2. Arquitetura

```text
Portal (JWT) → plugins/customer-experience → /apps/customer-experience-api/
                                              ↓
                                    Postgres customer_experience
                                    + volumes (photos, qr, form-images)

Visitante → /p/customer-experience/{thanks|form}/{token}
         → public-hub → GET /apps/customer-experience-api/public/…
```

| Componente | Identificador |
|---|---|
| Plugin admin | `customer-experience` |
| API | `customer-experience-api` |
| Shell público | `public-hub` |
| Schema | `customer_experience` |

---

## 3. Páginas públicas (`public-hub`)

| Página | URL | API `load` |
|---|---|---|
| Agradecimento | `/p/customer-experience/thanks/{token}` (alias `/welcome/{token}`) | `GET /public/participants/{token}` |
| Formulário | `/p/customer-experience/form/{token}` | `GET /public/forms/{token}` |

Formulário público (jul/2026): wizard opcional, páginas com imagens, barra de progresso, layout centralizado, modo escuro.

---

## 4. API — resumo

### Participantes (admin JWT)

`POST/GET/PATCH /participants`, `GET /participants/{id}/qr`, `POST /participants/{id}/deactivate`.

### Participantes (público)

`GET /public/participants/{token}`, `GET /public/participants/{token}/photo` — 404 se token inválido ou `is_active=false`.

### Formulários

Tabela completa: [forms-api.md](../../../customer-experience-api/docs/forms-api.md).

Público:

- `GET /public/forms/{token}` — exige formulário **publicado**
- `GET /public/forms/{token}/…` (imagens) — token válido (suporta prévia de rascunho no admin)
- `POST /public/forms/{token}/responses` — exige formulário **publicado**

---

## 5. Storage persistente

| Dado | Path container | Variável |
|---|---|---|
| Fotos participantes | `/app/data/customer-experience/photos` | `CUSTOMER_EXPERIENCE_PHOTO_UPLOAD_DIR` |
| QR | `/app/data/customer-experience/qr` | `CUSTOMER_EXPERIENCE_QR_DIR` |
| Imagens de formulário | `/app/data/customer-experience/form-images` | `CUSTOMER_EXPERIENCE_FORM_IMAGE_UPLOAD_DIR` |

Ver [infra/README-ambiente.md](../../../infra/README-ambiente.md).

---

## 6. Admin — rotas UI

| Path | Tela |
|---|---|
| `/apps/customer-experience/participantes` | Participantes |
| `/apps/customer-experience/formularios` | Lista de formulários |
| `/apps/customer-experience/formularios/{id}` | Editor |
| `/apps/customer-experience/formularios/{id}/respostas` | Dashboard |

**Prévia:** botão na lista e no editor; modal local sem `POST` de respostas. Ver README do plugin § Prévia.

---

## 7. Roadmap — status

### Onda 0 — Fundação ✅

Participantes, QR, página de agradecimento, API, gateway, volumes, plugin admin, `public-hub`.

### Onda 1 — Experiência memorável (parcial) ✅

- Página de agradecimento com hero e animação
- Etiqueta frente/verso para cabo (`qrLabelPrint.ts`)

### Onda 1.6 — Formulários avançados (jul/2026) ✅

Detalhe em [ROADMAP-FORMULARIOS-JUL2026.md](./ROADMAP-FORMULARIOS-JUL2026.md):

- Páginas, imagens, wizard, dashboard
- Rotas URL no admin
- Prévia local (rascunho + não salvo)
- Layout público + modo escuro

### Ondas 2–3 — backlog

LGPD (`consent_at`), analytics, retenção, integração com agenda.

---

## 8. Gates antes do merge

| Escopo | Comando |
|---|---|
| API | `cd customer-experience-api && pytest tests/ -q` |
| Plugin admin | `cd plugins/customer-experience && npm run build` |
| Shell público | `cd plugins/public-hub && npm run build` |
| Storage | Recreate → arquivos no host |

---

## 9. Permissões RBAC

`customer-experience.access`, `participants.read/write/manage`, `forms.read/write/manage`, `admin` — ver `customer-experience.manifest.json`.
