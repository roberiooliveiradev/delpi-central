# Playbook de Excelência — Customer Experience DELPI

> **Arquivo:** `docs/12-roadmap-e-evolucao/customer-experience/PLAYBOOK-EXCELENCIA.md`
> **Versão:** 1.1
> **Data:** 2026-07-01
> **Status:** proposta (pré-implementação)
> **Base:** requisito «programa de recepção de visitantes de empresas clientes» + convenções do monorepo `delpi-central` (plugins MFE, APIs FastAPI de plugin, upload persistente, gateway nginx)
>
> **Convenção de nomes:** identificadores técnicos (plugin, API, rotas, schema, env, permissões) em **inglês**; textos voltados ao usuário (rótulo de menu, mensagens, descrições) em **pt-BR**.

**Relacionado:**
- `docs/05-plugin-system/manifesto-plugin.md` — contrato de registro de plugin
- `docs/08-plugins/README.md` — checklist de novo plugin
- `docs/12-roadmap-e-evolucao/quality-action-plans/PLAYBOOK-EXCELENCIA.md` — modelo de playbook de produto
- `.cursor/rules/persistent-upload-storage.mdc` — foto/QR em volume persistente
- `.cursor/rules/plugins-visual-design-system.mdc` — UI nativa do portal
- `.cursor/rules/plugins-frontend-build.mdc` — build antes do commit

---

## 1. North Star — o que é excelência aqui

A Delpi recebe **pessoas de empresas clientes** num programa de visitas/experiência. Excelência aqui **não** é «uma tela que gera QR code». É criar um **momento memorável e rastreável** para o visitante:

1. O usuário Delpi (recepção / comercial / RH) cadastra o visitante em segundos: foto, empresa, data e informações da visita.
2. O sistema gera um **QR code personalizado e imprimível** por participante.
3. Ao escanear, **qualquer pessoa** (sem login) vê uma página bonita com a **foto do participante** e uma **mensagem impactante de agradecimento** pela participação no programa.
4. Tudo com **contrato desacoplado**: API própria (separada da `delpi-api`), plugin no padrão MFE do portal, página pública servida fora do portal autenticado.
5. Dados de pessoas tratados com cuidado (LGPD): foto + nome atrás de **token opaco**, sem exposição sequencial.

### Definição operacional (métricas de sucesso)

| Métrica | Meta | Como medir |
|---|---|---|
| Tempo para cadastrar 1 visitante + gerar QR | ≤ 60 s | cronometragem recepção |
| QR gerados que resultam em acesso à página pública | ≥ 70% | contador de views por token |
| Página pública carrega (foto + mensagem) | ≤ 2 s em 4G | Lighthouse / medição real |
| Zero foto de visitante em filesystem efêmero | 100% | volume persistente homologado |
| Acesso indevido por adivinhação de URL | 0 | token opaco ≥ 128 bits |

---

## 2. Escopo e decisões de arquitetura (fechadas)

| Decisão | Escolha | Racional |
|---|---|---|
| **Onde fica a API** | Novo serviço **FastAPI no monorepo** `customer-experience-api`, atrás do gateway em `/apps/customer-experience-api/` (padrão `maintenance-api`) | Separada da `delpi-api`, mas integrada ao ecossistema (JWT do portal, Postgres plugins, deploy compose) |
| **Página pública sem login** | **Shell público genérico** (`public-hub`, container `delpi-public-hub`) servido pelo gateway em rota pública `/p/{app}/{page}/{token}` (alias legado `/welcome/{token}`), **fora** do catch-all `/` do portal | Irmão público do portal: um SPA único que vários apps customizam (evita 1 container por app); único jeito de ter página sem Keycloak sem furar o gate global |
| **Geração do QR** | **No backend**: API gera + persiste PNG/SVG do QR por participante | Durável, imprimível, uma fonte de verdade |
| **Privacidade do link** | **Token opaco** aleatório (≥ 128 bits, ex.: `secrets.token_urlsafe(32)`), sem expiração | Simples e suficiente contra enumeração; sem sessão |
| **Front admin** | MFE em `plugins/customer-experience` (React 19 + Vite + Module Federation) | Padrão do portal |
| **Storage foto + QR** | Volume persistente `${DELPI_DATA_HOST_DIR}/customer-experience` | Regra `persistent-upload-storage` |
| **Banco** | Schema dedicado `customer_experience` no `postgres-plugins` (migrations on startup, padrão `maintenance-api`) | Isola dados do programa |

### Nomenclatura adotada

| Componente | Identificador (inglês) | Rótulo/usuário (pt-BR) | Padrão de referência |
|---|---|---|---|
| Plugin admin (MFE) | `customer-experience` | «Experiência do Cliente» | `auditoria-5s`, `cadastro-kaizen` |
| Shell público (estático) | `public-hub` (view `customer-experience/thanks`) | — | novo padrão (ver §5) |
| API dedicada | `customer-experience-api` | — | `maintenance-api`, `strategic-indicators-api` |
| Rota gateway API | `/apps/customer-experience-api/` | — | `/apps/maintenance-api/` |
| Rota gateway pública | `/p/customer-experience/thanks/{token}` (alias `/welcome/{token}`) | — | **nova** (ver §5) |
| Schema Postgres | `customer_experience` | — | schema plugins |
| Prefixo CSS / caller app | `customer-experience` (prefixo curto `cx-`) | — | `plugins-visual-design-system` |
| Permissões RBAC | `customer-experience.read/write/manage/admin` | ver descrições pt-BR no manifesto | `quality-action-plans.*` |

> Os identificadores são a nomenclatura oficial deste playbook. Textos exibidos (menu, botões, mensagens) permanecem em pt-BR.

---

## 3. Arquitetura alvo

```text
┌─────────────────────────── PORTAL (login Keycloak obrigatório) ───────────────────────────┐
│  Usuário Delpi (recepção/comercial/RH)                                                     │
│        │                                                                                   │
│        ▼                                                                                   │
│  Plugin MFE  ──JWT──►  customer-experience-api  ──►  Postgres (schema customer_experience) │
│  (plugins/customer-experience)   /apps/customer-experience-api/     + volume foto/QR       │
└───────────────────────────────────────────────────────────────────────────────────────────┘

                         (fora do portal, SEM login)
Visitante escaneia QR ─► GET /p/customer-experience/thanks/{token}  ──►  shell público public-hub
                         (alias legado: /welcome/{token})
                                    │                         │
                                    │      fetch dados        ▼
                                    └──► GET /apps/customer-experience-api/public/participants/{token}
                                              (endpoint público — só leitura, por token opaco)
```

**Regra de ouro:** o app público **só** lê dados por token, nunca escreve; o plugin admin **nunca** é servido sem login. As duas superfícies compartilham a mesma API, mas por caminhos e permissões distintos (JWT para admin, token opaco para público).

### Fluxo do gateway (nginx) — o ponto sensível

Hoje `location /` manda tudo para o portal (que força login). Para a página pública, adicionar **antes** do catch-all uma location dedicada:

```nginx
# =============================
# CUSTOMER EXPERIENCE — PÁGINA PÚBLICA (sem login)
# =============================
location ^~ /p/ {
  set $service delpi-public-hub;
  proxy_pass http://$service;
  proxy_http_version 1.1;
  proxy_set_header Host $host;
}
# Alias legado (QR já impressos)
location ^~ /welcome/ {
  set $service delpi-public-hub;
  proxy_pass http://$service;
  proxy_http_version 1.1;
  proxy_set_header Host $host;
}

# API dedicada (admin JWT + endpoint público por token)
location ^~ /apps/customer-experience-api/ {
  set $upstream_cx_api customer-experience-api:8000;
  rewrite ^/apps/customer-experience-api/?(.*)$ /$1 break;
  proxy_pass http://$upstream_cx_api;
  proxy_http_version 1.1;
  proxy_set_header Host $host;
  add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0" always;
  proxy_no_cache 1;
  proxy_cache_bypass 1;
}
```

> A location `/welcome/` **precisa** vir antes de `location /` (portal). O app público serve seu próprio HTML/JS e faz `fetch` no endpoint público da API. O middleware de auth da API deve tratar `/public/*` como rota pública (padrão `is_public_path`).

---

## 4. Modelo de dados (schema `customer_experience`)

Tabela única inicial — expandir depois conforme ondas.

```sql
CREATE SCHEMA IF NOT EXISTS customer_experience;

CREATE TABLE customer_experience.participants (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  public_token      TEXT NOT NULL UNIQUE,          -- secrets.token_urlsafe(32)
  full_name         TEXT NOT NULL,
  company_name      TEXT NOT NULL,
  visit_date        DATE NOT NULL,
  participant_info  TEXT,                           -- cargo/observações/mensagem específica
  photo_filename    TEXT,                           -- nome do arquivo no volume
  qr_filename       TEXT,                           -- PNG/SVG do QR no volume
  thank_you_message TEXT,                           -- opcional; senão usa template padrão
  view_count        INTEGER NOT NULL DEFAULT 0,
  is_active         BOOLEAN NOT NULL DEFAULT TRUE,  -- desligar link sem apagar registro
  created_by        TEXT,                           -- sub/preferred_username do JWT
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_participants_visit_date ON customer_experience.participants (visit_date DESC);
CREATE INDEX idx_participants_company ON customer_experience.participants (company_name);
```

- **Migrations:** `customer-experience-api/.../migrations/` rodadas on startup (padrão `maintenance-api` `run_migrations_on_startup`).
- **`public_token`**: único, indexado, gerado no backend. É a única chave usada pela página pública.

---

## 5. Página pública sem login (padrão novo — detalhar bem)

Como **não existe precedente** de página pública no portal, este playbook define o padrão:

### 5.1 Shell público genérico `public-hub`

> **Generalização (jul/2026):** o antigo `customer-experience-public` virou o **shell público genérico** `public-hub` — o **irmão público do portal**. Um único SPA estático (Vite, sem Module Federation, sem Keycloak) que roteia páginas públicas de **vários apps**, para não criar um container por app.
>
> **Guia para apps futuros:** `plugins/public-hub/README.md` — passo a passo de como registrar uma nova página pública (view + `pages.tsx` + `registry.ts`), o contrato `PublicPageDefinition` e o que fica no shell vs no app.

- Container único `delpi-public-hub`, servido pelo gateway em rota pública, **fora** do catch-all `/` do portal.
- **Roteamento** (`src/shell/routing.ts`): canônico `/p/{app}/{page}/{token}`; alias legado `/welcome/{token}` → `customer-experience/thanks` (QR já impressos).
- **Config-driven** (`src/shell/registry.ts`): cada app expõe `AppPublicPages` com `load(token)` + `render(data)`. O shell (`PublicShell.tsx`) cuida do transversal (marca DELPI, loading, not-found, erro, `noindex`).
- **Adicionar um novo app público:** criar `src/apps/<app>/pages.tsx` (+ views/CSS/`api.ts`) e registrar em `registry.ts`. Sem novo container, sem novo location no gateway (já cobre `/p/`).
- Cada view só faz `GET` no endpoint público da sua API. Nenhuma escrita nem token de sessão.
- **Formulários personalizáveis (estilo Google Forms, jul/2026):** página `form` do app `customer-experience` (`/p/customer-experience/form/{token}`), **página pública independente** da de agradecimento — cada formulário tem seu **QR próprio**. O visitante informa nome/empresa e responde perguntas customizáveis (rating, texto, escolha, sim/não). Prova de que o shell **não** muda ao ganhar página: só entrou uma view em `src/apps/customer-experience/` + registro no `pages.tsx`. O antigo feedback fixo por participante foi **removido** (migration `V005`) em favor deste módulo.

### 5.2 Endpoint público da API (só leitura, por token)
```
GET /apps/customer-experience-api/public/participants/{token}
→ 200 { fullName, companyName, visitDate, photoUrl, thankYouMessage }
→ 404 se token inexistente ou is_active = false
```
- Registrado em `is_public_path()` (não exige JWT).
- Rate limit no gateway (reuso de `limit_req_zone`).
- Incrementa `view_count` (best effort, sem bloquear resposta).
- **Nunca** devolve `id`, `created_by`, `public_token` de outros nem lista — só o registro do token.
- `photoUrl` aponta para outro endpoint público de imagem: `GET /public/participants/{token}/photo` (stream do volume).

**Formulários (estilo Google Forms) — leitura/escrita pública por token:**
```
GET  /apps/customer-experience-api/public/forms/{token}
→ 200 { title, description, questions[] }   # perguntas ativas do formulário
→ 404 se token inexistente ou is_active = false

POST /apps/customer-experience-api/public/forms/{token}/responses
     body { respondentName, respondentCompany?, answers[] }
→ 201 · 404 token inexistente/inativo · 422 resposta inválida
```
- Tabelas `customer_experience.forms`, `form_questions`, `form_responses`, `form_answers` (migration `V004`). Perguntas têm soft-delete (`is_active`) para preservar histórico de respostas.
- Serviços `FormService` / `FormResponseService` (unit-testados com repos fake): validam tipo de pergunta, obrigatoriedade e agregam o dashboard.
- Anti-abuso: `limit_req` do gateway na rota `/apps/customer-experience-api/`.

**QR de agradecimento (página separada):**
- QR de **agradecimento** → `/welcome/{token}` (alias) / `/p/customer-experience/thanks/{token}`; download admin `GET /participants/{id}/qr`. Admin expõe `qrUrl`/`publicUrl`.
- **Etiqueta do cabo (impressão):** o admin também imprime uma etiqueta frente/verso (QR + logo Delpi + selo APROVADO QUALIDADE, monocromática) montada no cliente (`qrLabelPrint.ts`) a partir do mesmo `GET /participants/{id}/qr` — sem endpoint adicional.
- O feedback fixo por participante (tabela `feedback`, coluna `feedback_qr_filename`, migrations `V002`/`V003`) foi **removido** pela migration `V005`; use o módulo de Formulários.

### 5.3 Conteúdo da página (texto ao usuário: pt-BR)
- Foto do participante em destaque.
- Mensagem impactante de agradecimento em pt-BR (template padrão + `thank_you_message` opcional por participante).
- Marca Delpi, empresa e data da visita.
- Responsiva (mobile-first — visitante abre no celular).

---

## 6. Contrato da API (admin — JWT do portal)

Envelope padrão do ecossistema (`success`, `message`, `data`, `meta`). Permissões RBAC no manifesto. Mensagens (`message`) em pt-BR.

| Método | Rota (sob `/apps/customer-experience-api`) | Permissão | Descrição |
|---|---|---|---|
| `POST` | `/participants` | `customer-experience.write` | Cria participante (multipart: dados + foto) → gera token + QR |
| `GET` | `/participants` | `customer-experience.read` | Lista/pagina participantes (filtro por data/empresa) |
| `GET` | `/participants/{id}` | `customer-experience.read` | Detalhe |
| `PATCH` | `/participants/{id}` | `customer-experience.write` | Edita dados / mensagem / troca foto |
| `POST` | `/participants/{id}/deactivate` | `customer-experience.manage` | Desliga link público (`is_active=false`) |
| `GET` | `/participants/{id}/qr` | `customer-experience.read` | Baixa o QR (PNG/SVG) para impressão |
| `GET` | `/health` | pública | Healthcheck |
| `GET` | `/public/participants/{token}` | pública | Dados da página pública |
| `GET` | `/public/participants/{token}/photo` | pública | Stream da foto |

- **Upload de foto:** multipart, whitelist de MIME (jpeg/png/webp), limite (ex.: 10 MB), validação de imagem real. Padrão `PacEvidenceStorage.save`.
- **QR:** gerado no `POST /participants` a partir da URL pública final `{{PUBLIC_BASE_URL}}/welcome/{token}`; persistido no volume; dependência nova (ex.: `qrcode[pil]` no Python — **sem precedente no repo**, registrar em `requirements`).

---

## 7. Storage persistente (obrigatório desde o 1º commit)

Regra `persistent-upload-storage.mdc`.

| Item | Container | Host |
|---|---|---|
| Fotos | `/app/data/customer-experience/photos` | `${DELPI_DATA_HOST_DIR}/customer-experience/photos` |
| QR codes | `/app/data/customer-experience/qr` | `${DELPI_DATA_HOST_DIR}/customer-experience/qr` |

- Variáveis `CUSTOMER_EXPERIENCE_PHOTO_UPLOAD_DIR` / `CUSTOMER_EXPERIENCE_QR_DIR` em `config.py`.
- Volume nos **dois** composes (`docker-compose.yml` + `docker-compose.dev.yml`).
- Documentar em `infra/README-ambiente.md` + `env.local.example`.
- Homologar: `docker compose ... up -d --force-recreate` → foto e QR ainda no host.

---

## 8. Segurança e LGPD

- **Token opaco** ≥ 128 bits (`secrets.token_urlsafe(32)`), não sequencial, não derivado de dados pessoais.
- Endpoint público **só leitura por token**; sem listagem, sem enumeração.
- `is_active=false` desliga o link sem apagar histórico.
- Rate limit no gateway para `/welcome/` e `/public/`.
- **Consentimento:** capturar consentimento do visitante para uso da foto (campo `consent_at` — adicionar na Onda 2 se exigido pelo jurídico).
- **Retenção:** política de expurgo de fotos após N meses (Onda 3).
- Sem PII em logs (não logar nome/empresa em nível INFO).

---

## 9. Roadmap por ondas

Estimativa: **S** ≤ 1 sprint, **M** 2–3 sprints, **L** 1 trimestre.

### Onda 0 — Fundação (MVP funcional)
**Objetivo:** cadastrar visitante, gerar QR, ver página pública sem login.

| # | Entrega | Repo/pasta | Esforço |
|---|---|---|---|
| 0.1 | Scaffold `customer-experience-api` (FastAPI, config, health, migrations on startup) | `customer-experience-api/` | M |
| 0.2 | Schema + migration `V001__participants.sql` | api | S |
| 0.3 | `POST/GET/PATCH /participants` + upload foto (storage persistente) | api | M |
| 0.4 | Geração + persistência do QR no `POST /participants` | api | S |
| 0.5 | Endpoints públicos `/public/participants/{token}` + `/photo` | api | S |
| 0.6 | Plugin MFE admin: form cadastro + lista + download QR + imprimir etiqueta | `plugins/customer-experience` | M |
| 0.7 | Shell público `public-hub` (view `customer-experience/thanks`: foto + mensagem) | `plugins/public-hub` | M |
| 0.8 | Gateway: locations `/p/` + `/welcome/` (alias) e `/apps/customer-experience-api/` | `gateway/nginx*.conf` | S |
| 0.9 | Serviços no `docker-compose.dev.yml` + volumes | `infra/` | S |
| 0.10 | Manifesto do plugin + RBAC + registro na Core API | plugin + Core API | S |

**Critério de aceite Onda 0:**
- [ ] Usuário logado cadastra visitante com foto e baixa o QR para impressão.
- [ ] Escanear o QR abre `/welcome/{token}` **sem pedir login** e mostra foto + mensagem.
- [ ] Recreate do container **não** perde foto nem QR.
- [ ] URL adivinhada (token errado) retorna 404.

### Onda 1 — Experiência memorável
**Objetivo:** página pública encantadora e cadastro rápido.

> **Entregue (jul/2026):** página pública com foto grande em destaque (hero), revelação animada em cascata e mensagem-surpresa temática — o visitante monta um cabo na visita e, ao ler o QR, recebe um agradecimento personalizado (primeiro nome + empresa). Mensagem padrão gerada no app público quando o cadastro não define texto próprio.
>
> **Entregue (jul/2026) — etiqueta para o cabo (item 1.5):** botão **«Imprimir etiqueta»** no card do participante gera uma etiqueta **frente/verso para colar no cabo**: QR de agradecimento de um lado, marca Delpi + selo **APROVADO QUALIDADE** do outro, com faixa central de dobra em volta do cabo. Layout **monocromático** (logo e selo em preto). Implementação **100% client-side** em `plugins/customer-experience/src/utils/qrLabelPrint.ts` (janela de impressão + fallback iframe, espera imagens antes de `print()`), reusando o download `GET /participants/{id}/qr` — **sem novo endpoint**. A logo (`src/assets/logoDelpi.svg`, importada com `?raw` e forçada a preto via CSS) fica embutida no bundle; o selo é um SVG inline (não há asset oficial — trocar `QUALITY_SEAL_SVG` se a marca fornecer o definitivo).

| # | Entrega | Esforço |
|---|---|---|
| 1.1 | Templates de mensagem de agradecimento (pt-BR, em JSON de conteúdo) | S |
| 1.2 | Página pública com animação/branding, OG tags para compartilhar | M |
| 1.3 | Captura de foto pela câmera no cadastro (mobile) | M |
| 1.4 | Personalização por empresa (logo do cliente, cor) | M |
| 1.5 | ✅ QR imprimível em etiqueta frente/verso para o cabo (logo + selo, monocromático) | S |

### Onda 2 — Governança e privacidade
| # | Entrega | Esforço |
|---|---|---|
| 2.1 | Consentimento LGPD do visitante (`consent_at`) | S |
| 2.2 | Desativar/expirar link em lote (por data de visita) | M |
| 2.3 | Auditoria de acessos (view_count, primeiro/último acesso) | M |
| 2.4 | Permissões granulares (`read`/`write`/`manage`/`admin`) | S |

### Onda 3 — Analytics e ecossistema
| # | Entrega | Esforço |
|---|---|---|
| 3.1 | Dashboard: visitas por período/empresa, taxa de scan | M |
| 3.2 | Política de retenção + expurgo automático de fotos | M |
| 3.3 | Exportar relatório de visitas (Excel/PDF) | M |
| 3.4 | Integração com agenda/recepção (`central-agendamento`) | L |

---

## 10. Gates e testes (antes do merge)

| Escopo | Comando |
|---|---|
| API | `cd customer-experience-api && pytest tests/ -q` |
| Plugin admin | `cd plugins/customer-experience && npm run build` |
| Shell público | `cd plugins/public-hub && npm run build` |
| Storage | Recreate do container → foto + QR presentes no host |
| Público sem login | `curl` em `/p/customer-experience/thanks/{token}` (e alias `/welcome/{token}`) e `/public/participants/{token}` sem Authorization → 200 |
| Segurança | token inválido → 404; sem listagem no público |

Testes mínimos: geração de token único, geração de QR, upload/stream de foto, endpoint público retorna só o registro do token, `is_active=false` → 404.

---

## 11. Checklist de novo plugin (referência)

De `docs/05-plugin-system/manifesto-plugin.md` §35 e `docs/08-plugins/README.md` §7:

1. Copiar esqueleto de plugin existente (`plugins/quality-action-plans` para admin com API própria).
2. Manifesto `schemaVersion: "1.0.0"`, `basePath: /apps/customer-experience`, `entry` remoteEntry, bloco `backend` apontando para `customer-experience-api`, permissões RBAC (código em inglês, `name`/`description` em pt-BR), rota de menu (label «Experiência do Cliente»).
3. `npm run build` → registrar na Core API (`scripts/register-manifest.sh`).
4. Serviços `delpi-customer-experience`, `delpi-public-hub` e `customer-experience-api` no `docker-compose.dev.yml`.
5. Validar `http://localhost/apps/customer-experience/assets/remoteEntry.js` e `http://localhost/p/customer-experience/thanks/{token}` (alias `/welcome/{token}`).
6. Atribuir permissões RBAC aos perfis (recepção/comercial/RH).
7. Design system: tokens do portal, prefixo CSS `cx-`, responsivo (`plugins-visual-design-system.mdc`).

---

## 12. Riscos e pontos de atenção

| Risco | Mitigação |
|---|---|
| Página pública fura o gate de auth do portal | Location dedicada **antes** de `/`; app estático isolado sem Keycloak |
| Foto de pessoa em disco efêmero | Volume persistente desde o 1º commit (regra obrigatória) |
| Enumeração de visitantes | Token opaco ≥ 128 bits + rate limit + 404 genérico |
| Dependência QR nova no ecossistema | Registrar em requirements; testar geração no CI |
| LGPD (imagem de pessoa) | Consentimento + retenção + desativação de link |
| Duplicar auth/contrato entre admin e público | Uma API, dois caminhos (`/participants` JWT vs `/public/*` token) |

---

## 13. Resumo executivo

1. **MVP (Onda 0):** cadastrar visitante + foto → QR imprimível → página pública de agradecimento sem login. Já entrega o valor central do programa.
2. **Onda 1:** transformar a página em experiência memorável (branding, câmera, compartilhável).
3. **Ondas 2–3:** privacidade/LGPD, governança e analytics.

A excelência chega quando o visitante de uma empresa cliente, ao escanear o QR do próprio crachá, vê a **própria foto** e um **obrigado genuíno da Delpi** — em 2 segundos, sem instalar nada e sem login — enquanto a Delpi mantém tudo rastreável, seguro e desacoplado.
