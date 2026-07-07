# Experiência do Cliente — plugin Minha DELPI

Microfrontend (Module Federation) para o **programa de recepção de visitantes**: cadastro de participantes com foto, QR de agradecimento, etiqueta para cabo e **formulários personalizáveis** (estilo Google Forms).

Documentação de produto: [docs/12-roadmap-e-evolucao/customer-experience/](../../docs/12-roadmap-e-volucao/customer-experience/) · API: [customer-experience-api/docs/forms-api.md](../../customer-experience-api/docs/forms-api.md) · Página pública: [plugins/public-hub/README.md](../public-hub/README.md).

---

## Visão geral

| Camada | Responsabilidade |
|--------|------------------|
| **MFE** `customer-experience` | Admin: participantes + formulários + dashboard de respostas + prévia |
| **API** `customer-experience-api` | CRUD JWT + endpoints públicos por token |
| **Shell** `public-hub` | Páginas sem login: agradecimento e formulário do visitante |
| **Postgres** `customer_experience` | Participantes, formulários, perguntas, respostas |

```text
Portal (login) → /apps/customer-experience/…
                    ↓ Module Federation (remoteEntry.js)
                  MFE customer-experience
                    ↓ JWT
Gateway → /apps/customer-experience-api/*
                    ↓
                  customer-experience-api → Postgres + volumes (foto/QR/imagens de formulário)

Visitante (sem login) → /p/customer-experience/{thanks|form}/{token}
                    ↓ public-hub
                    ↓ GET /apps/customer-experience-api/public/…
```

---

## Funcionalidades

### Participantes

- Cadastro com foto, empresa, data da visita e mensagem de agradecimento opcional
- Lista, edição, desativação de link público
- Download do QR e **impressão de etiqueta frente/verso** para cabo (`qrLabelPrint.ts`)

### Formulários (jul/2026)

- CRUD de formulários com tipos de pergunta: nota (estrelas), texto curto/longo, escolha única/múltipla, sim/não
- **Modo passo a passo** (`oneQuestionPerPage`): uma pergunta por etapa com barra de progresso
- **Páginas** com título, fundo e imagem ilustrativa (modo scroll ou uma etapa por pergunta)
- Imagem de fundo do formulário; imagens ilustrativas por página ou pergunta
- Publicar / despublicar; QR e link público próprios por formulário
- Dashboard de respostas (resumo por pergunta + lista de envios)
- **Prévia** no admin (lista e editor): visualização local como o visitante verá, sem gravar respostas — inclui rascunhos e alterações não salvas
- **Rotas na URL** do plugin (deep link e voltar do navegador)

---

## Rotas da UI (admin)

Base: `/apps/customer-experience`

| Path | Tela |
|------|------|
| `/participantes` | Lista e cadastro de participantes (padrão) |
| `/formularios` | Lista de formulários |
| `/formularios/{id}` | Editor de perguntas e layout |
| `/formularios/{id}/respostas` | Dashboard / respostas do formulário |

Implementação: `src/constants/routes.ts`, `src/hooks/useCxRouterPath.ts`, `src/utils/navigation.ts` (`pushState` + evento `cx-route`).

---

## API (gateway)

Base HTTP: **`/apps/customer-experience-api`**

| Área | Prefixo | Autenticação |
|------|---------|--------------|
| Participantes | `/participants` | JWT + permissões `customer-experience.participants.*` |
| Formulários (admin) | `/forms` | JWT + permissões `customer-experience.forms.*` |
| Público | `/public/participants`, `/public/forms` | Token opaco na URL (sem JWT) |

Tabela completa de formulários: [forms-api.md](../../customer-experience-api/docs/forms-api.md).

### Exemplo — listar formulários

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"

curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost/apps/customer-experience-api/forms" \
  | jq '.success, .data | length'
```

---

## Permissões (Portal / Keycloak)

| Código | Escopo |
|--------|--------|
| `customer-experience.access` | Abrir o módulo |
| `customer-experience.participants.read` | Ver participantes e QR |
| `customer-experience.participants.write` | Cadastrar e editar |
| `customer-experience.participants.manage` | Desativar / excluir |
| `customer-experience.forms.read` | Ver formulários e respostas |
| `customer-experience.forms.write` | Criar e editar perguntas |
| `customer-experience.forms.manage` | Publicar, despublicar, excluir |

Contexto no MFE: `src/context/CxPermissionsContext.tsx`.

---

## Prévia de formulário (admin)

A prévia **não** depende do formulário estar publicado:

| Origem | Comportamento |
|--------|---------------|
| Lista | Carrega `GET /forms/{id}` e abre modal com render local |
| Editor | Monta modelo a partir do estado atual (textos, layout, imagens pendentes via blob URL) |

Arquivos:

- `src/FormPreviewView.tsx` — render espelhado do `public-hub` (sem POST de resposta)
- `src/components/FormPreviewModal.tsx` — modal fullscreen
- `src/utils/formPreviewModel.ts` — mapper `FormDetail` / editor → `PreviewForm`
- `src/form-preview.css` — estilos do formulário público (tema claro)

A API serve imagens de rascunho via `_require_public_row` (token válido, sem exigir `is_active`) nos endpoints `GET /public/forms/{token}/…/background` e `…/point-image`.

---

## Build e desenvolvimento

```bash
cd plugins/customer-experience
npm install
npm run build    # tsc -b && vite build
```

Registro na Core API: `scripts/register-manifest.sh` (manifesto `customer-experience.manifest.json`).

Smoke:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost/apps/customer-experience/assets/remoteEntry.js
```

---

## Estrutura `src/` (principal)

```text
src/
  api/              formsApi, participantsApi, httpClient
  components/       PhotoDropzone, FormPreviewModal, …
  constants/        routes, permissions
  context/          CxPermissionsContext
  pages/            CustomerExperiencePage, FormsPanel, ParticipantsPanel
  utils/            formPreviewModel, navigation, qrLabelPrint
  FormPreviewView.tsx
  form-preview.css
```

---

## Páginas públicas (visitante)

Servidas pelo `public-hub` — **não importar** esse pacote no build do admin.

| Página | URL |
|--------|-----|
| Agradecimento | `/p/customer-experience/thanks/{token}` (alias `/welcome/{token}`) |
| Formulário | `/p/customer-experience/form/{token}` |

O formulário público inclui layout centralizado (~640px), fundo em viewport, ilustrações hero no wizard, barra de progresso e suporte a **modo escuro** (`data-theme` no shell). Ver `plugins/public-hub/src/apps/customer-experience/`.

---

## Storage persistente

| Dado | Variável | Path container |
|------|----------|----------------|
| Fotos participantes | `CUSTOMER_EXPERIENCE_PHOTO_UPLOAD_DIR` | `/app/data/customer-experience/photos` |
| QR codes | `CUSTOMER_EXPERIENCE_QR_DIR` | `/app/data/customer-experience/qr` |
| Imagens de formulário | `CUSTOMER_EXPERIENCE_FORM_IMAGE_UPLOAD_DIR` | `/app/data/customer-experience/form-images` |

Volumes no Compose: `infra/README-ambiente.md` § customer-experience.
