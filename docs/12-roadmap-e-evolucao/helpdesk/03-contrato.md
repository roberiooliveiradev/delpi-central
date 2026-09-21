# 03 — Contrato

> **Status:** contrato implementado; leitura ao vivo `PROVEN` em 21/09/2026
> **Arquitetura:** [`02-arquitetura.md`](./02-arquitetura.md)

O MFE consome só este contrato. Campos do GLPI não vazam quando o BFF consegue traduzir. Onde a tradução ainda não existe, o nome no JSON do BFF é o deste documento, não o nome cru do schema GLPI.

## 1. Convenções

- Paths do BFF em inglês, kebab-case.
- JSON em snake_case.
- Autenticação do MFE: JWT da Minha DELPI, como nas outras APIs de módulo.
- Sem JWT válido: 401.
- Com JWT e sem `helpdesk.access`: 403 do portão da plataforma, antes de chamar o GLPI.
- Com portão ok e sem sessão OAuth do GLPI: 409 `glpi_link_required`, com `authorize_url` para o navegador seguir.
- GLPI 403 no token da pessoa: 403 `glpi_forbidden`. A tela não esconde o motivo com uma lista vazia.
- Escrita sem `Idempotency-Key`: 400.
- POST de abertura e de acompanhamento: sem retry automático.

Base do MFE: `/apps/helpdesk-api`.

## 2. Sessão

| Método | Path | Função |
|---|---|---|
| GET | `/auth/glpi/start` | Responde 302 para `api.php/authorize` (PKCE S256, `state` ligado ao sujeito do JWT) |
| GET | `/auth/glpi/callback` | Troca o código em `api.php/token`, grava a sessão, redireciona para `/apps/helpdesk` |
| GET | `/auth/glpi/session` | `{ "linked": true }` ou `{ "linked": false }` |
| DELETE | `/auth/glpi/session` | Apaga o vínculo local. Não revoga a sessão SAML do GLPI |

`state` é de uso único e expira em 10 minutos. O código de autorização do GLPI também expira em 10 minutos. Access token do GLPI expira em 1 hora; o BFF renova com o refresh token no servidor.

## 3. Leitura

| Método | Path | Função |
|---|---|---|
| GET | `/ticket-categories` | Categorias que o token da pessoa pode usar |
| GET | `/urgencies` | Urgências do GLPI |
| GET | `/tickets` | Chamados visíveis para esse token |
| GET | `/tickets/{id}` | Detalhe + linha do tempo |

`GET /tickets` devolve:

```json
{
  "items": [
    {
      "id": 1234,
      "title": "string",
      "status": "string",
      "category": "string",
      "urgency": "string",
      "updated_at": "2026-09-21T12:00:00Z"
    }
  ]
}
```

Lista vazia com sessão válida é `200` e `items: []`. Não é erro.

`GET /tickets/{id}` inclui `description` e `timeline[]` com `id`, `kind` (`followup` na primeira entrega), `content`, `created_at`, `author_display_name`.

## 4. Escrita

`POST /tickets`

Cabeçalho `Idempotency-Key` obrigatório, gerado na intenção de envio e reutilizado se a mesma intenção for repetida. Chave nova só para um novo envio.

```json
{
  "title": "string",
  "description": "string",
  "category_id": 1,
  "urgency_id": 3
}
```

Não existe campo de solicitante nem de entidade. O BFF não reenvia esses campos ao GLPI. O chamado nasce na entidade padrão do usuário do token.

Resposta `201`:

```json
{ "id": 1234 }
```

Repetir a mesma chave depois de sucesso devolve o mesmo `id`, sem segundo chamado.

`POST /tickets/{id}/followups`

```json
{ "content": "string" }
```

Também exige `Idempotency-Key`. Resposta `201` com `{ "id": 1 }`.

## 5. Mapa para o GLPI

Chamadas com `Authorization: Bearer` do access token da pessoa e cabeçalho `GLPI-API-Version: 2.2.0`.

| Caso de uso | GLPI 11.0.5 |
|---|---|
| Autorizar | `GET /api.php/authorize` |
| Token e refresh | `POST /api.php/token` |
| Listar e criar chamado | `GET` e `POST /api.php/v2.2/Assistance/Ticket` |
| Detalhe | `GET /api.php/v2.2/Assistance/Ticket/{id}` |
| Linha do tempo | `GET /api.php/v2.2/Assistance/Ticket/{id}/Timeline` |
| Acompanhamento | `POST /api.php/v2.2/Assistance/Ticket/{id}/Timeline/Followup` |

Categoria: `GET /api.php/v2.2/Dropdowns/ITILCategory`, usando `completename`. Urgência é o enum 1–5 do schema de Ticket (Muito baixa, Baixa, Média, Alta, Muito alta), não um dropdown.

Fora do mapa, mesmo que o escopo `api` permita: `Change`, `Problem`, ativo, inventário, GraphQL, tarefa de técnico, validação e solução. O BFF não publica rota para isso.

## 6. Erros

| Situação | HTTP do BFF |
|---|---|
| GLPI indisponível ou timeout | 502 `glpi_unavailable` |
| GLPI 401 no token, refresh também falhou | 409 `glpi_link_required` |
| GLPI 403 | 403 `glpi_forbidden` |
| GLPI 404 no chamado | 404 |
| Validação (título vazio, categoria inexistente) | 422 com os campos |

Timeout de conexão e de leitura são explícitos no cliente HTTP. POST não é repetido. GET pode ser repetido no máximo duas vezes, com backoff, só em 502/503/504 e timeout.
