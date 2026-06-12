# Playbook 01 — Fronteiras api-delpi × maintenance-api

**Contrato vivo** — define o que fica em cada serviço e como evitar duplicação de código TOTVS.

**Status:** jun/2026 — rotas api-delpi **propostas**; implementação na Fase 0/1.

---

## 1. Princípio

| Camada | Responsabilidade |
|--------|------------------|
| **api-delpi** | Única implementação de SQL Protheus; contrato público `{ success, message, data, meta }`; OpenAPI + `route_contract_registry` |
| **maintenance-api** | CRUD operacional Postgres; orquestração; **gateways HTTP** para TOTVS |
| **MFE** | UI; chama **somente** a API dedicada (JWT) |

```text
Browser → maintenance-api → DelpiApiClient → api-delpi → SQL Server
Browser → maintenance-api → Postgres
```

**Proibido:**

- Copiar queries de `MiniAplicadores/Infrastructure/Queries/*.sql` para `maintenance-api`.
- MFE chamar `/apps/api-delpi/...` para mini-aplicadores (exceto se no futuro houver dashboard read-only sem API dedicada — **não** é o caso deste produto).
- Segundo client SQL Server no plugin.

---

## 2. Mapa de dados

| Conceito | Persistência | Leitura TOTVS |
|----------|--------------|---------------|
| Reposição | Postgres | — |
| Motivo | Postgres | — |
| Status preventivo | Postgres | — |
| Ferramenta (cadastro) | — | api-delpi |
| Peça | — | api-delpi |
| Amarração ferramenta×peça | — | api-delpi |
| Golpes no período | — | api-delpi |
| Componentes / estoque | — | api-delpi |

---

## 3. Rotas públicas propostas (api-delpi)

**Prefixo:** `/engineering/mini-applicators`  
**Dono:** `api-delpi` — DTOs, testes de contrato, smoke CI.

| Rota | operationId (proposta) | Registry kind | Descrição |
|------|------------------------|---------------|-----------|
| `GET /engineering/mini-applicators/ferramentas` | `list_mini_applicators_ferramentas` | `paged_list` | Lista SB1010 grupos 23/24; query `codigo`, `descricao`, `filial` |
| `GET /engineering/mini-applicators/ferramentas/{codigo}` | `get_mini_applicators_ferramenta` | `scalar` | Detalhe por código |
| `GET /engineering/mini-applicators/ferramentas/{codigo}/pecas` | `list_mini_applicators_pecas` | `list` | Peças amarradas (SG1010) |
| `GET /engineering/mini-applicators/ferramentas/{codigo}/golpes` | `get_mini_applicators_golpes` | `scalar` | Query params: `filial`, `data_inicial`, `data_final` |
| `GET /engineering/mini-applicators/ferramentas/{codigo}/componentes` | `list_mini_applicators_componentes` | `list` | Árvore + estoque; query `filial` |

### 3.1 Exemplo envelope — listagem ferramentas

**Request (gateway interno):**

```http
GET /engineering/mini-applicators/ferramentas?descricao=23-
Authorization: Bearer <jwt-usuario>
```

**Response:**

```json
{
  "success": true,
  "message": "Ferramentas listadas.",
  "data": {
    "total": 2,
    "items": [
      {
        "id": 123456,
        "codigo": "23-001",
        "descricao": "Mini aplicador XYZ"
      }
    ]
  },
  "meta": {
    "operation_id": "list_mini_applicators_ferramentas"
  }
}
```

### 3.2 Exemplo — golpes

**Request:**

```http
GET /engineering/mini-applicators/ferramentas/23-026/golpes?filial=01&data_inicial=2025-12-18&data_final=2026-06-12
```

**Response `data`:**

```json
{
  "codigo_ferramenta": "23-026",
  "filial": "01",
  "data_inicial": "2025-12-18",
  "data_final": "2026-06-12",
  "total_golpes": 8420
}
```

SQL de referência (legado — **implementar só na api-delpi**): `MiniAplicadores/Infrastructure/Queries/ObterGolpes.sql`.

---

## 4. Gateway na API dedicada

**Arquivo alvo:** `maint_app/infrastructure/gateways/delpi_mini_applicators_gateway.py`

**Port alvo:** `maint_app/domain/ports/mini_applicators_totvs_port.py`

| Método port | Chama api-delpi |
|-------------|-----------------|
| `listar_ferramentas(filtro)` | `GET .../ferramentas` |
| `obter_ferramenta(codigo)` | `GET .../ferramentas/{codigo}` |
| `listar_pecas(codigo_ferramenta)` | `GET .../ferramentas/{codigo}/pecas` |
| `obter_golpes(filial, codigo, ini, fim)` | `GET .../ferramentas/{codigo}/golpes` |
| `listar_componentes(codigo, filial)` | `GET .../ferramentas/{codigo}/componentes` |

**Cliente:** `shared/delpi_api_client.DelpiApiClient` — mesmo padrão SI.

**Headers:**

- `Authorization: Bearer` — JWT propagado do request MFE.
- **Não** usar `X-Delpi-Caller-App` server-to-server aqui (fluxo usuário autenticado).

---

## 5. Rotas da API dedicada (CRUD — não passam pela api-delpi)

**Prefixo:** `/maintenance`

| Grupo | Exemplos |
|-------|----------|
| Reposições | `GET/POST /reposicoes`, `PUT/DELETE /reposicoes/{id}` |
| Motivos | `GET/POST /motivos`, … |
| Status | `GET /status-peca`, `PUT /status-peca/{id}` |
| Preventiva | `GET /preventiva/alertas`, `GET /preventiva/medias` |
| Options | `GET /options` — filiais permitidas (RBAC) |

Estas rotas leem/escrevem **Postgres** e **compõem** respostas chamando gateways quando precisam de TOTVS (ex.: `POST /reposicoes` valida peça via gateway).

---

## 6. Checklist ao adicionar nova leitura TOTVS

1. [ ] Existe rota na api-delpi com `operation_id` registrado?
2. [ ] DTO documentado em `api-delpi/docs/api/`?
3. [ ] Teste de contrato / smoke na api-delpi?
4. [ ] Port + gateway na `maintenance-api`?
5. [ ] Nenhum SQL Protheus fora da api-delpi?
6. [ ] MFE consome só API dedicada?

---

## 7. Evolução futura — fachada para terceiros

Se chat, SI ou outro módulo precisar de **resumo preventivo** sem falar com a API do plugin:

- Criar rotas **api-delpi** espelhadas (padrão Transforma+ / `integration-contracts.md` do Transformômetro).
- Implementação api-delpi → S2S `maintenance-api` com `X-Delpi-Service-Token`.
- **Não** antecipar na Fase 0–2.

---

## 8. Referências

- Legado queries: `/home/analistaptd/projetos/MiniAplicadores/Infrastructure/Queries/`
- SI gateways: `strategic-indicators-api/si_app/infrastructure/gateways/`
- Playbook envelope: `minha-delpi-ai-api/docs/roadmap/playbook-10-contrato-respostas-api-delpi.md`
- Transformômetro contratos: `transformometro-api/docs/integration-contracts.md`
