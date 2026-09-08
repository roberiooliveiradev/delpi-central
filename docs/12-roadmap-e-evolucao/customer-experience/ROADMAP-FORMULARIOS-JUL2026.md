# Formulários CX — entregas jul/2026

> **Módulo:** Experiência do Cliente (`customer-experience` + `customer-experience-api` + `public-hub`)  
> **Status:** entregue em produção (jul/2026)  
> **Playbook geral:** [PLAYBOOK-EXCELENCIA.md](./PLAYBOOK-EXCELENCIA.md)

Este documento registra a evolução do módulo de **formulários personalizáveis** além do MVP da migration `V004`.

---

## 1. Escopo entregue

| # | Entrega | Onde |
|---|---------|------|
| 1 | Páginas com título, fundo e ilustração (`form_pages`, migration `V006`) | API + admin + público |
| 2 | Modo **uma pergunta por página** (wizard + barra de progresso) | API `oneQuestionPerPage` + `FormPage.tsx` |
| 3 | Upload/remoção de imagens (formulário, página, pergunta) | `form_routes.py`, `PhotoDropzone` |
| 4 | Layout público estilo Google Forms (coluna ~640px, fundo full viewport) | `public-hub/form.css` |
| 5 | Ilustrações hero grandes no wizard | `FormPage.tsx` + CSS |
| 6 | Modo escuro na página pública do formulário | `public-hub` tokens + scrim adaptativo |
| 7 | Enter no wizard não envia antes da última etapa | `FormPage.tsx` |
| 8 | Rotas na URL do admin (`/formularios`, `/formularios/{id}`, `/respostas`) | `routes.ts`, `useCxRouterPath` |
| 9 | **Prévia** no admin (lista + editor), sem gravar respostas | `FormPreviewView`, `FormPreviewModal` |
| 10 | Assets de imagem para rascunho (token válido, sem `is_active`) | `FormService._require_public_row` |
| 11 | Modo de fundo: fixo / escalável / repetir (`backgroundFit`) | migration `V007` + editor + CSS público |

---

## 2. Fluxos

### Visitante (formulário publicado)

```text
QR / link → /p/customer-experience/form/{token}
         → GET /public/forms/{token}
         → preenche (scroll ou wizard)
         → POST /public/forms/{token}/responses
```

### Admin — prévia

```text
Lista: Prévia → GET /forms/{id} → buildPreviewFormFromDetail → modal
Editor: Prévia → buildEditorPreview (estado local + blob URLs) → modal
```

A prévia **não** chama `POST /responses`. Imagens já salvas usam URLs públicas da API; imagens pendentes no editor usam `URL.createObjectURL`.

---

## 3. Commits de referência (jul/2026)

| Commit | Tema |
|--------|------|
| `4173a023e` | Rotas na URL para formulários e abas |
| `bb7986a7f` | Modo escuro + remover imagens no editor |
| `c603ebb35` | Fundo full viewport + ilustrações grandes |
| `9c323d2ab` | Layout coluna central ~640px |
| `d5f16bad3` | Wizard: Enter não envia antes da última etapa |
| `0e2e24b34` | Prévia de formulário na lista e no editor |

---

## 4. Documentação relacionada

| Documento | Conteúdo |
|-----------|----------|
| [plugins/customer-experience/README.md](../../../plugins/customer-experience/README.md) | Plugin admin: rotas, permissões, prévia, build |
| [customer-experience-api/docs/forms-api.md](../../../customer-experience-api/docs/forms-api.md) | Contrato HTTP de formulários |
| [plugins/public-hub/README.md](../../../plugins/public-hub/README.md) | Shell público e registro de views |
| [infra/README-ambiente.md](../../../infra/README-ambiente.md) | Volumes persistentes (foto, QR, form-images) |

---

## 5. Backlog (não entregue)

- Templates de mensagem em JSON de conteúdo (Onda 1.1 do playbook)
- Consentimento LGPD explícito (`consent_at`)
- Exportação Excel/PDF de respostas
- Extração de `qrLabelPrint.ts` para pacote compartilhado (se 3º consumidor)
