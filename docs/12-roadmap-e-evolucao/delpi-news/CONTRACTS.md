# DELPI News — contratos conceituais (Etapa 1)

> **Natureza:** proposta documentada para contratos futuros.  
> **Não** criar operações OpenAPI, schemas Alembic nem Action Catalog nesta etapa.  
> Identificadores e campos de contrato em **inglês**; labels de UI em pt-BR.

Quando a API for criada, estes conceitos devem virar schemas OpenAPI canônicos do BC `delpi-news-api`, com envelope `{ success, message, data }` alinhado à plataforma.

---

## 1. `RssSource` — fontes RSS

Entidade de configuração da coleta.

| Campo | Tipo conceitual | Obrigatório | Descrição |
|---|---|---|---|
| `id` | UUID / ULID | sim | Identificação estável da fonte |
| `name` | string | sim | Nome editorial (ex.: «Agência Brasil») |
| `feed_url` | URI https | sim | Endereço do feed RSS/Atom |
| `category_id` | UUID \| null | não | Categoria padrão atribuída aos itens |
| `language` | BCP-47 | sim | Ex.: `pt-BR`, `en` |
| `is_active` | boolean | sim | Fonte ativa/inativa para coleta |
| `poll_interval_sec` | int ≥ 60 | sim | Intervalo alvo entre coletas |
| `last_collected_at` | timestamptz \| null | não | Última coleta com parse bem-sucedido |
| `last_attempt_at` | timestamptz \| null | não | Última tentativa (sucesso ou falha) |
| `last_attempt_status` | enum | sim | `never` \| `success` \| `partial` \| `failed` |
| `last_error_code` | string \| null | não | Código estável (ex.: `http_429`, `parse_error`, `ssrf_blocked`) |
| `last_error_message` | string \| null | não | Mensagem sanitizada (sem secrets/URLs internas) |
| `availability` | enum | sim | `available` \| `degraded` \| `unavailable` |
| `etag` / `last_modified` | string \| null | não | Condicionais HTTP para coleta eficiente |
| `created_at` / `updated_at` | timestamptz | sim | Auditoria básica |
| `created_by` / `updated_by` | user id \| null | não | Ator admin |

### Estados e invariantes

- Fonte `is_active=false` não entra no scheduler.
- `availability=unavailable` após N falhas consecutivas (limiar da API futura); não remove itens já publicados.
- `feed_url` só https (exceto localhost em dev); validação anti-SSRF no BC.

### Histórico de coleta (conceitual)

Tabela ou append-only `rss_source_fetch_events`:

| Campo | Descrição |
|---|---|
| `id` | Evento |
| `source_id` | FK fonte |
| `attempted_at` | Momento |
| `status` | `success` \| `partial` \| `failed` |
| `http_status` | int \| null |
| `items_seen` / `items_upserted` | contagens |
| `error_code` / `error_message` | opcional |
| `duration_ms` | observabilidade |

---

## 2. `NewsItem` — notícias normalizadas

Item canônico após parse + dedupe, antes ou depois da curadoria.

| Campo | Tipo conceitual | Obrigatório | Descrição |
|---|---|---|---|
| `id` | UUID / ULID | sim | Identificador estável interno |
| `source_id` | UUID | sim | Fonte de origem |
| `external_id` | string | sim | Id do item no feed (`guid`/`id`) ou hash estável da URL |
| `title` | string | sim | Título normalizado |
| `summary` | string \| null | não | Resumo/snippet (texto limpo, sem HTML perigoso) |
| `canonical_url` | URI | sim | URL da matéria original |
| `image_url` | URI \| null | não | Imagem quando política permitir |
| `image_allowed` | boolean | sim | Se a imagem pode ser exibida (direitos/política) |
| `category_id` | UUID \| null | não | Categoria efetiva (fonte default ou override) |
| `published_at` | timestamptz \| null | não | Data de publicação no feed |
| `collected_at` | timestamptz | sim | Momento da coleta que materializou/atualizou o item |
| `editorial_state` | enum | sim | Ver §2.1 |
| `duplicate_of_id` | UUID \| null | não | Se for duplicata, aponta para o item canônico |
| `fingerprint` | string | sim | Hash de dedupe (URL normalizada e/ou título+fonte) |
| `language` | BCP-47 \| null | não | Herdado/detectado |
| `is_featured` | boolean | sim | Destaque editorial |
| `published_board_at` | timestamptz \| null | não | Quando entrou no board público |
| `created_at` / `updated_at` | timestamptz | sim | |

### 2.1 `editorial_state`

| Valor | Significado |
|---|---|
| `collected` | Ingerido; aguarda triagem |
| `approved` | Aprovado para publicação |
| `rejected` | Rejeitado (não aparece no público) |
| `published` | Visível no board público ativo |
| `archived` | Removido da rotação; retido para histórico |

Transições válidas (conceitual):

```text
collected → approved | rejected
approved → published | rejected
published → archived | rejected
rejected → approved (reabertura)
```

### 2.2 Deduplicação

- Chave primária de negócio: `(source_id, external_id)`.
- `fingerprint` cobre cross-source (mesma URL canônica).
- Duplicata secundária: `editorial_state` pode permanecer `collected` com `duplicate_of_id` preenchido; só o canônico pode ir a `published`.

---

## 3. Contratos auxiliares (para etapas seguintes)

Documentados aqui para fechar o desenho; **sem** implementação na E1.

### 3.1 `NewsCategory`

`id`, `slug`, `name`, `sort_order`, `is_active`.

### 3.2 `PublicNewsBoard` (payload da página pública)

Contrato de leitura por token opaco (futuro `GET …/public/boards/{token}`):

| Campo | Descrição |
|---|---|
| `board_id` | Identificador do board |
| `title` | Título exibido (ex.: «DELPI News») |
| `subtitle` | Opcional |
| `is_demo` | Se true, UI marca conteúdo como demonstração (E1 fixture) |
| `rotation_interval_sec` | Intervalo de autoavanço na TV |
| `items[]` | Lista ordenada de itens **publicados** (subset seguro) |

Cada item público (subset):

| Campo | Notas |
|---|---|
| `id` | Id interno |
| `title` | |
| `summary` | |
| `canonical_url` | Opcional na TV (pode ocultar clique) |
| `image_url` | Só se `image_allowed` |
| `category_name` | Label pt-BR resolvido |
| `source_name` | Nome da fonte |
| `published_at` | |
| `is_featured` | |

**Não** expor no público: estados internos, erros de coleta, `fingerprint`, atores admin, tokens de outras fontes.

### 3.3 Admin (esboço)

Operações futuras (JWT + permissions `delpi-news.*`): CRUD fontes, listagem/filtro de itens, transição editorial, configurar board/token, regenerar token.

---

## 4. Alinhamento com a prova visual (E1)

A fixture em `plugins/public-hub/src/apps/delpi-news/` materializa **apenas** o shape de `PublicNewsBoard` + items públicos, com dados estáticos. Quando a API existir, `load` do hub troca a fixture por HTTP sem alterar o contrato visual dos campos acima.
