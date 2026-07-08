# Customer Experience API — Formulários

> **Serviço:** `customer-experience-api`  
> **Gateway:** `/apps/customer-experience-api`  
> **Schema:** `customer_experience`  
> **Migrations:** `V004__forms.sql`, `V006__form_layout_pages.sql`

Envelope padrão: `{ success, message?, data, meta? }`. Mensagens ao usuário em pt-BR.

---

## Admin (JWT)

Permissões: `customer-experience.forms.read` | `.write` | `.manage`.

### CRUD e publicação

| Método | Rota | Permissão | Descrição |
|--------|------|-----------|-----------|
| `POST` | `/forms` | write | Cria formulário (título, descrição, `oneQuestionPerPage`, `backgroundFit`) |
| `POST` | `/forms/{id}/duplicate` | write | Duplica estrutura (páginas, perguntas, imagens); **sem** respostas; novo token/QR; nasce como rascunho |
| `GET` | `/forms` | read | Lista resumos (`publicUrl`, `isActive`, `responseCount`, `backgroundFit`, …) |
| `GET` | `/forms/{id}` | read | Detalhe com `questions[]`, `pages[]` e `backgroundFit` |
| `PATCH` | `/forms/{id}` | write | Atualiza metadados (incl. `backgroundFit`: `fixed` \| `scale` \| `tile`) |
| `PUT` | `/forms/{id}/questions` | write | Substitui perguntas e páginas (ordem, tipos, opções) |
| `POST` | `/forms/{id}/activate` | manage | Publica (`is_active=true`) |
| `POST` | `/forms/{id}/deactivate` | manage | Despublica |
| `DELETE` | `/forms/{id}` | manage | Exclui formulário e respostas |
| `GET` | `/forms/{id}/qr` | read | PNG do QR (`/p/customer-experience/form/{token}`) |

### Respostas e dashboard

| Método | Rota | Permissão | Descrição |
|--------|------|-----------|-----------|
| `GET` | `/forms/{id}/responses` | read | Lista paginada de envios |
| `GET` | `/forms/{id}/dashboard` | read | Agregados por pergunta (média, distribuição, amostras) |

### Imagens (upload multipart)

Armazenamento: `CUSTOMER_EXPERIENCE_FORM_IMAGE_UPLOAD_DIR` (volume persistente).

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/forms/{id}/background-image` | Fundo do formulário |
| `DELETE` | `/forms/{id}/background-image` | Remove fundo |
| `POST` | `/forms/{id}/pages/{page_id}/background-image` | Fundo da página |
| `DELETE` | `/forms/{id}/pages/{page_id}/background-image` | Remove fundo da página |
| `POST` | `/forms/{id}/pages/{page_id}/point-image` | Ilustração da página |
| `DELETE` | `/forms/{id}/pages/{page_id}/point-image` | Remove ilustração da página |
| `POST` | `/forms/{id}/questions/{question_id}/point-image` | Ilustração da pergunta |
| `DELETE` | `/forms/{id}/questions/{question_id}/point-image` | Remove ilustração da pergunta |

Respostas de detalhe incluem URLs públicas resolvidas (`backgroundImageUrl`, `pointImageUrl`) apontando para os endpoints abaixo.

Em `PUT /forms/{id}/questions`, páginas e perguntas aceitam `pointImageFit` (`fixed` | `scale` | `tile`) — mesmos modos do fundo do formulário (`backgroundFit`), aplicados à área da imagem ilustrativa.

Também aceitam `pointIcon` (nome Lucide em kebab-case, ex.: `eye`). Ícone e imagem ilustrativa são mutuamente exclusivos.

---

## Público (sem JWT)

Token opaco do formulário na URL. **Submissão** exige `is_active=true`. **Assets de imagem** aceitam token válido mesmo em rascunho (prévia no admin).

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/public/forms/{token}` | Metadados + perguntas ativas + páginas → **404** se inativo ou token inválido |
| `GET` | `/public/forms/{token}/background` | Stream do fundo do formulário |
| `GET` | `/public/forms/{token}/pages/{page_id}/background` | Fundo da página |
| `GET` | `/public/forms/{token}/pages/{page_id}/point-image` | Ilustração da página |
| `GET` | `/public/forms/{token}/questions/{question_id}/point-image` | Ilustração da pergunta |
| `POST` | `/public/forms/{token}/responses` | Envia respostas → **404** se inativo |

### Payload de resposta (`POST`)

```json
{
  "respondentName": "Maria Silva",
  "respondentCompany": "Empresa X",
  "answers": [
    { "questionId": "uuid", "rating": 5 },
    { "questionId": "uuid", "text": "Ótima visita" },
    { "questionId": "uuid", "choices": ["Opção A", "Opção B"] }
  ]
}
```

Validação por tipo: obrigatoriedade, opções válidas, rating 1–5.

---

## Modelo de dados (resumo)

| Tabela | Campos relevantes (jul/2026) |
|--------|------------------------------|
| `forms` | `public_token`, `is_active`, `one_question_per_page`, `background_image_filename`, `background_fit` (`fixed` \| `scale` \| `tile`) |
| `form_pages` | `position`, `title`, `background_image_filename`, `point_image_filename` |
| `form_questions` | `type`, `label`, `page_id`, `point_image_filename`, `is_active` (soft-delete) |
| `form_responses` / `form_answers` | Respostas do visitante |

---

## Testes

```bash
cd customer-experience-api
pytest tests/test_form_service.py tests/test_form_response_service.py -q
```

---

## Referências

- Playbook: `docs/12-roadmap-e-volucao/customer-experience/PLAYBOOK-EXCELENCIA.md`
- Entregas jul/2026: `docs/12-roadmap-e-volucao/customer-experience/ROADMAP-FORMULARIOS-JUL2026.md`
- Plugin admin: `plugins/customer-experience/README.md`
- Página pública: `plugins/public-hub/src/apps/customer-experience/`
