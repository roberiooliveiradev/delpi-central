# Contratos de integração — maintenance-api → api-delpi

Leitura **TOTVS / Protheus** para mini-aplicadores passa **exclusivamente** pela api-delpi. Este documento espelha o padrão [transformometro-api/docs/integration-contracts.md](../../transformometro-api/docs/integration-contracts.md), invertendo o fluxo: somos **consumidor**, não exportador.

**Status:** jun/2026 — contratos **propostos** (Playbook 01).

---

## 1. Quem consome o quê

```text
                    ┌─────────────────────────────────────────┐
                    │  api-delpi  (contrato público TOTVS)     │
                    │  GET /engineering/mini-applicators/*     │
                    │  envelope: success, message, data, meta  │
                    └─────────────────┬───────────────────────┘
                                      │
                                      │ DelpiApiClient + JWT usuário
                                      ▼
                    ┌─────────────────────────────────────────┐
                    │  maintenance-api              │
                    │  DelpiMiniAplicadoresGateway             │
                    │  + CRUD Postgres                         │
                    └─────────────────┬───────────────────────┘
                                      │
                                      │ JWT
                                      ▼
                    ┌─────────────────────────────────────────┐
                    │  plugins/maintenance (MFE)      │
                    └─────────────────────────────────────────┘
```

| Consumidor | Cliente | Nunca chama |
|------------|---------|-------------|
| MFE | `maintenanceApi.ts` → API dedicada | api-delpi, SQL Server |
| maintenance-api | `DelpiApiClient` → api-delpi | SQL Server direto |
| Chat / SI (futuro) | api-delpi fachada S2S (Fase 4+) | Postgres do plugin direto |

---

## 2. Contrato público (api-delpi)

**Dono:** `api-delpi` — OpenAPI, `route_contract_registry.py`, testes smoke.

| Rota pública | operationId (proposta) | Registry |
|--------------|------------------------|----------|
| `GET /engineering/mini-applicators/ferramentas` | `list_mini_applicators_ferramentas` | `mini_applicators_ferramenta` / `paged_list` |
| `GET /engineering/mini-applicators/ferramentas/{codigo}` | `get_mini_applicators_ferramenta` | `mini_applicators_ferramenta` / `scalar` |
| `GET /engineering/mini-applicators/ferramentas/{codigo}/pecas` | `list_mini_applicators_pecas` | `mini_applicators_peca` / `list` — grupo TOTVS **3019** |
| `GET /engineering/mini-applicators/ferramentas/{codigo}/golpes` | `get_mini_applicators_golpes` | `mini_applicators_golpes` / `scalar` |
| `GET /engineering/mini-applicators/ferramentas/{codigo}/componentes` | `list_mini_applicators_componentes` | `mini_applicators_componente` / `list` — árvore completa (estoque) |

A API dedicada reforça o filtro **3019** em `GET /maintenance/mini-aplicadores/ferramentas/{codigo}/pecas` (select de reposição), derivando da **mesma árvore vigente** de `/componentes`. A rota `/componentes` lista todos os itens amarrados — **sem** filtro 3019.

**Implementação api-delpi (alvo):**

| Camada | Arquivo (alvo) |
|--------|----------------|
| Rotas HTTP | `app/interface/http/routes/engineering/mini_applicators_router.py` |
| Repositório TOTVS | `app/infrastructure/persistence/totvs/mini_applicators_repository.py` |
| Composer | registrar em `engineering_composer` ou equivalente |

Detalhe de payloads: [PLAYBOOK-01](../../docs/12-roadmap-e-evolucao/maintenance/PLAYBOOK-01-fronteiras-api-delpi.md).

---

## 3. Gateway interno (maintenance-api)

| Camada | Arquivo (alvo) |
|--------|----------------|
| Port | `maint_app/domain/ports/mini_applicators_totvs_port.py` |
| Gateway | `maint_app/infrastructure/gateways/delpi_mini_applicators_gateway.py` |
| Client | `shared/delpi_api_client/client.py` |

### Exemplo de uso no service

```python
# application/services/reposicao_service.py (conceitual)
async def preencher_golpes_sugeridos(self, filial: str, codigo_ferramenta: str, codigo_peca: str) -> int:
    ultima = await self._reposicao_repo.obter_ultima_data(filial, codigo_ferramenta, codigo_peca)
    return await self._totvs.obter_golpes(
        filial=filial,
        codigo_ferramenta=codigo_ferramenta,
        data_inicial=ultima,
        data_final=date.today(),
    )
```

---

## 4. Variáveis de ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| `DELPI_API_URL` | `http://delpi-api-delpi:8000` | Base api-delpi |
| `DELPI_API_TIMEOUT` | `30` | Timeout segundos |

---

## 5. Ordem de implementação recomendada

1. api-delpi: `list_mini_applicators_ferramentas` + teste contrato.
2. Gateway + teste mock.
3. Endpoint API dedicada `GET /mini-aplicadores/ferramentas` (orquestra gateway + RBAC).
4. Repetir para peças, golpes, componentes.
5. CRUD reposições Postgres (sem TOTVS).

---

## 6. Referências legado (somente leitura humana)

Queries WinForms — **não copiar** para `maint_app`:

- `MiniAplicadores/Infrastructure/Queries/FerramentaQueries.sql`
- `MiniAplicadores/Infrastructure/Queries/PecaQueries.sql`
- `MiniAplicadores/Infrastructure/Queries/FerramentaPecaQueries.sql`
- `MiniAplicadores/Infrastructure/Queries/ObterGolpes.sql`
- `MiniAplicadores/Infrastructure/Queries/ReposicaoQueries.sql` → Postgres na API dedicada

---

## 7. Playbook envelope

Todas as rotas api-delpi novas devem seguir [playbook-10-contrato-respostas-api-delpi.md](../../minha-delpi-ai-api/docs/roadmap/playbook-10-contrato-respostas-api-delpi.md).

Gateway da API dedicada lê **somente** `data` do envelope ao mapear para entidades de domínio.
