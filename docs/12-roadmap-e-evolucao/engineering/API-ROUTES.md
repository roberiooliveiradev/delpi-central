# Portal de Engenharia — contratos e rotas alvo

> **Status:** arquitetura alvo para planejamento.  
> **Implementação:** não autorizada por este documento.  
> **Regra:** paths e DTOs precisam ser revalidados contra código/OpenAPI vigentes antes da execução.

## 1. Boundary obrigatório

Com `plugins/engineering` + `engineering-api`, o MFE nunca chama `/apps/api-delpi` diretamente.

```text
plugins/engineering
      │
      ▼
/apps/engineering-api/*
      │
      ├── api-delpi
      ├── requests-api
      ├── transformometro-api
      ├── Strategic Indicators
      └── Core API
```

## 2. Base proposta

```text
MFE: /apps/engineering
API: /apps/engineering-api/v1
```

A versão final deve seguir o padrão vigente da infraestrutura e manifesto no momento da implementação.

## 3. Contratos de composição do Portal

### 3.1 Home

`GET /v1/home`

Objetivo: reduzir fan-out no browser e entregar composição personalizada.

Resposta conceitual:

```json
{
  "summary": {
    "pending_tasks": 7,
    "critical_lmps": 3,
    "unread_mentions": 2
  },
  "priorities": [],
  "tools": [],
  "recent_activity": [],
  "partial_sources": []
}
```

`partial_sources` permite degradação parcial explícita quando uma integração estiver indisponível.

### 3.2 Visão geral

`GET /v1/overview`

Query proposta:

```text
start_date
end_date
branch
```

Composição:

- scores Strategic Indicators;
- resumo LMP;
- tendências e status;
- TRANSFORMA+;
- atenções relevantes.

Não recalcular score estratégico no MFE.

## 4. Minhas tarefas

### Listagem

`GET /v1/my-tasks`

Filtros:

```text
source
status
priority
search
page
page_size
sort
direction
```

DTO interno conceitual:

```json
{
  "id": "source:123",
  "source": "lmp",
  "title": "Revisar LMP 123456",
  "subtitle": "Cliente XYZ",
  "status": "pending",
  "priority": "high",
  "due_at": null,
  "deep_link": "/apps/engineering/lmps/123456",
  "allowed_actions": []
}
```

### Regra crítica

`engineering-api` agrega tarefas, mas não inventa workflow. `allowed_actions` só pode ser propagado/traduzido quando fornecido pelo owner real e autorizado.

## 5. Sala de interação

A Sala é domínio próprio do Portal Engenharia.

### Rotas alvo

```text
GET    /v1/rooms
POST   /v1/rooms
GET    /v1/rooms/{room_id}
PATCH  /v1/rooms/{room_id}
GET    /v1/rooms/{room_id}/messages
POST   /v1/rooms/{room_id}/messages
PATCH  /v1/rooms/{room_id}/messages/{message_id}
DELETE /v1/rooms/{room_id}/messages/{message_id}
POST   /v1/rooms/{room_id}/messages/{message_id}/reactions
DELETE /v1/rooms/{room_id}/messages/{message_id}/reactions/{reaction}
GET    /v1/rooms/{room_id}/participants
POST   /v1/rooms/{room_id}/participants
DELETE /v1/rooms/{room_id}/participants/{user_id}
GET    /v1/rooms/{room_id}/attachments/{attachment_id}
POST   /v1/rooms/{room_id}/attachments
```

### Contexto de sala

```json
{
  "context_type": "product",
  "context_key": "90262957",
  "context_label": "Produto 90262957",
  "deep_link": "/apps/engineering/tools/products/90262957"
}
```

Tipos iniciais:

```text
general
product
lmp
project
nonconformity
raw_material_request
```

Não usar contexto textual livre como substituto de chave tipada.

### Realtime

Planejar canal websocket/socket já alinhado à infraestrutura vigente. Persistir antes de publicar evento realtime.

Eventos conceituais:

```text
engineering.room.created
engineering.room.updated
engineering.room.message.created
engineering.room.message.updated
engineering.room.message.deleted
engineering.room.reaction.changed
engineering.room.read.changed
```

## 6. LMPs

O `engineering-api` deve compor os contratos existentes do domínio LMP sem reimplementar regra no frontend.

### Rotas alvo do BFF

```text
GET /v1/lmps/summary
GET /v1/lmps/charts
GET /v1/lmps
GET /v1/lmps/{sale_number}
GET /v1/lmps/{sale_number}/history/events
GET /v1/lmps/{sale_number}/history/flow
GET /v1/lmps/{sale_number}/nonconformities
```

Adapters podem consumir os endpoints vigentes de `/engineering/lmps/*` da `api-delpi` enquanto esse for o owner real.

## 7. Produtos

### Pesquisa

`GET /v1/products`

Filtros conceituais:

```text
search
code
description
group_code
supplier_part_number
page
page_size
```

O adapter traduz para os contratos atuais da `api-delpi` (`/products/search`, `/products/by-supplier-part-number`, etc.).

### Ficha

```text
GET /v1/products/{code}
GET /v1/products/{code}/analysis
GET /v1/products/{code}/structure
GET /v1/products/{code}/parents
GET /v1/products/{code}/stock
GET /v1/products/{code}/suppliers
GET /v1/products/{code}/pricing
GET /v1/products/{code}/cost-impact
```

A UI não deve conhecer os paths originais do provider.

### Segurança de preço/custo

Preço/custo deve possuir permissão/escopo próprio ou herdar regra comprovada do owner. Não assumir que acesso geral ao produto autoriza informação financeira/comercial sensível.

## 8. Desenhos

### Catálogo

`GET /v1/drawings`

Filtros devem suportar o conjunto real fornecido hoje pela biblioteca:

```text
code
code_exact
filename
revision
file_kind
has_variant
has_revision
modified_from
modified_to
min_size_bytes
max_size_bytes
page
page_size
sort
direction
```

### Metadados e PDF

```text
GET /v1/products/{code}/drawing
GET /v1/products/{code}/drawing/pdf
```

O `engineering-api` faz proxy/stream controlado do binário ou delega por contrato seguro. Nunca enviar `library_dir` ou path físico do FILESERVER ao browser.

## 9. Documentos técnicos / FILESERVER

Esta capacidade ainda não possui contrato canônico atual e deve nascer no `engineering-api` com adapter de storage allowlisted.

### Bibliotecas

`GET /v1/document-libraries`

Resposta expõe apenas IDs lógicos:

```json
[
  {"id":"lmps","label":"LMPs"},
  {"id":"projects","label":"Projetos"},
  {"id":"technical","label":"Documentos técnicos"}
]
```

### Listagem

`GET /v1/document-libraries/{library_id}/documents`

Filtros:

```text
search
context_type
context_key
file_type
modified_from
modified_to
page
page_size
```

DTO:

```json
{
  "id": "opaque-document-id",
  "name": "RQ-060.docx",
  "extension": "docx",
  "size_bytes": 12345,
  "modified_at": "2026-09-11T10:00:00Z",
  "context": {"type":"lmp","key":"123456"},
  "preview_supported": false,
  "download_allowed": true
}
```

### Arquivo

```text
GET /v1/document-libraries/{library_id}/documents/{document_id}/metadata
GET /v1/document-libraries/{library_id}/documents/{document_id}/content
```

`document_id` deve ser opaco/assinado ou resolvido server-side. Proibido aceitar path absoluto/relativo arbitrário do cliente.

### Proteções

- raízes configuradas em env/config, não request;
- read-only no MVP;
- normalização de path;
- `resolve()` + verificação dentro da raiz;
- allowlist de extensões;
- limite de tamanho;
- content-type correto;
- download/preview por permissão;
- logs sem expor credenciais/path sensível;
- auditoria de acesso quando exigido;
- tratamento explícito de share indisponível.

## 10. Controle de MP

Não criar workflow no `engineering-api`.

### Resumo opcional

`GET /v1/integrations/raw-material-control/summary`

Pode agregar contagens do `requests-api` respeitando o usuário/permissões.

### Deep links

O backend/UI deve gerar rotas canônicas do `my-requests`, por exemplo conceitual:

```text
/apps/my-requests/new?type=raw-material-creation
/apps/my-requests/new?type=raw-material-update
/apps/my-requests/mine?type=raw-material-creation
/apps/my-requests/work-queue?type=raw-material-creation
```

Validar os query params reais antes de implementar; não inventar contrato de rota.

## 11. TRANSFORMA+

### Resumo

`GET /v1/integrations/transforma-plus/summary`

Origem: contratos vigentes do Transformômetro/api-delpi, conforme ownership revalidado.

### Deep link

CTA abre o plugin canônico do Transformômetro.

## 12. Ajuda

Pode ser estática/versionada no MFE quando conteúdo simples, com conteúdo centralizado em arquivos apropriados. Se houver busca full-text, analytics ou edição administrativa futura, criar contrato específico sem misturar conteúdo de Ajuda com regras do domínio.

Rota UI:

```text
/apps/engineering/help
```

## 13. Erros e envelopes

Seguir o contrato padrão vigente do projeto. Não inventar envelope local divergente.

Erros downstream devem ser traduzidos para semântica do Portal, preservando status adequados e sem vazar stack/path/credencial.

## 14. Observabilidade

Cada adapter HTTP deve possuir, quando o padrão vigente exigir:

- timeout explícito;
- correlação/request-id;
- logs estruturados;
- métricas de latência/erro;
- tratamento de 401/403/404/422/5xx;
- política de retry somente para operações idempotentes e erros transitórios adequados;
- degradação parcial nas composições de leitura.

## 15. Contrato de navegação

Rotas de detalhe e filtros importantes devem ser compartilháveis. O frontend não deve depender de estado efêmero para reabrir:

- sala selecionada;
- LMP selecionada;
- produto;
- desenho;
- filtros de listagem;
- origem de tarefa quando necessário.
