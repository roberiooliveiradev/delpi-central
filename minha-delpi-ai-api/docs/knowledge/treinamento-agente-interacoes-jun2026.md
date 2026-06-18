# Treinamento ao vivo — 6 interações com o agente Minha DELPI Chat

Roteiro **copiar e colar** para sessões de treinamento, demo ou homologação com usuários.

**Agente:** Minha DELPI Chat (`minha-delpi-chat`)  
**Pré-requisitos:** gateway + **api-delpi** no ar; provider OpenAPI `api-delpi` habilitado no agente  
**Duração estimada:** ~20 minutos

---

## Produtos de referência (homologados)

| Código | Uso |
|--------|-----|
| `10080022` | Estoque / apresentação tabela-gráfico |
| `10080001` | Matéria-prima — preço de compra, NF, ICMS, orçamento |
| `90261255` | PA — simulador de impacto de custos (BOM multinível); **preferir também para demo fabril** se `90269002` não existir no Totvs |
| `90269002` | Playbook fabril — produção, expedição, status integrado (**validar cadastro no ambiente**) |

> **Nota (jun/2026):** follow-ups «desse produto» e «e a expedição?» dependem de contexto da sessão (`operationalFocus`). Ver playbook [`playbook-follow-up-operacional-desacoplado-jun2026.md`](../roadmap/melhorias/playbook-follow-up-operacional-desacoplado-jun2026.md).

---

## Interação 1 — Operacional básico + refinamento visual

**Objetivo:** consulta REST real e mudança de formato na mesma conversa.

| Turno | Cole no chat | Rota / efeito esperado |
|-------|--------------|------------------------|
| 1 | `estoque do produto 10080022` | `GET /products/{code}/stock` — tabela ou gráfico (Automático) |
| 2 | `mostre em gráfico` | Refinamento de **formato**; mesma consulta, sem rota errada |

**Fala sugerida (instrutor):** *“Primeiro uma consulta operacional simples; depois refinamos só a apresentação.”*

---

## Interação 2 — Modificação do produto (visão fabril)

**Objetivo:** status na fábrica, MPs exclusivas, produção e expedição.

| Turno | Cole no chat | Rota / efeito esperado |
|-------|--------------|------------------------|
| 1 | `status fabril do produto 90269002 hoje` | `GET /products/{code}/factory-status` — visão consolidada |
| 2 | `quais matérias-primas exclusivas existem na estrutura desse produto?` | `GET /products/{code}/structure/exclusivity` |

**Fala sugerida:** *“Para modificação do produto na fábrica, preferimos a rota integrada; exclusividade é consulta granular.”*

---

## Interação 3 — Análise de preço de matéria-prima

**Objetivo:** último fornecedor, NF, ICMS, orçamento e histórico — desambiguar compra × venda.

| Turno | Cole no chat | Rota / efeito esperado |
|-------|--------------|------------------------|
| 1 | `análise de preço da matéria-prima 10080001` | `GET /products/{code}/raw-material-price-intelligence` |
| 2 | `qual o preço de venda do produto 10080001?` | `GET /products/{code}/pricing` — **não** rota de compra MP |

**Fala sugerida:** *“Preço de compra da MP e preço de venda são rotas diferentes.”*

---

## Interação 4 — Simulador de impacto de custos (PA)

**Objetivo:** ranking das MPs que mais impactam o custo + simulação de reajuste.

| Turno | Cole no chat | Rota / efeito esperado |
|-------|--------------|------------------------|
| 1 | `quais materiais mais impactam o custo do PA 90261255?` | `GET /products/{code}/cost-impact-simulation` |
| 2 | `simule aumento de 10% nos materiais desse produto` | Mesma rota; parâmetro `adjustment_percent=10` |

**Fala sugerida:** *“O simulador aceita produto acabado (PA), não matéria-prima isolada.”*

---

## Interação 5 — Follow-up na mesma sessão

**Objetivo:** memória de contexto — produto mantido entre turnos.

| Turno | Cole no chat | Rota / efeito esperado |
|-------|--------------|------------------------|
| 1 | `situação de produção do 90269002 hoje` | `GET /products/{code}/production-status` |
| 2 | `e a expedição?` | `GET /products/{code}/shipping-status` — mesmo produto implícito |

**Fala sugerida:** *“Não é obrigatório repetir o código em todo turno.”*

---

## Interação 6 — Fontes do projeto

**Objetivo:** inventário de arquivos do projeto (resposta direta, sem “não tenho acesso”).

**Pré-requisito:** conversa vinculada a um **projeto** com pelo menos um arquivo em *Fontes do projeto*.

| Turno | Cole no chat | Rota / efeito esperado |
|-------|--------------|------------------------|
| 1 | `o que tem nas suas fontes?` | Resposta direta (lista nome, tamanho, chunks); stage `project_sources_inventory`; **skip RAG** |
| 2 | `resuma o conteúdo do primeiro arquivo` | RAG/`project_source` se indexado; aviso se pendente de indexação |

**Fala sugerida:** *“Listar arquivos do projeto é diferente de buscar semanticamente no texto.”*

---

## Checklist do instrutor

| # | Tema | OK? | Observação |
|---|------|-----|------------|
| 1 | Estoque + refinamento visual | ☐ | |
| 2 | Status fabril + MPs exclusivas | ☐ | |
| 3 | Preço MP vs preço venda | ☐ | |
| 4 | Simulador PA + reajuste 10% | ☐ | |
| 5 | Follow-up produção → expedição | ☐ | |
| 6 | Fontes do projeto | ☐ | |

---

## Dica para demo técnica (admin)

Com perfil admin, abra **adminDebug** nas interações 2 ou 3 e mostre:

- `intelligence.selectedExternalAction` / `operationId`
- `pipeline.stages` e `skipRag`
- `rag.retrievedSourceCount` vs `rag.visibleSourceCount` (quando aplicável)

---

## Referências

| Documento | Conteúdo |
|-----------|----------|
| [api-delpi-rotas-agente.md](./api-delpi-rotas-agente.md) | Mapa intenção → rota |
| [../testing/perguntas-teste-chat-jun2026.md](../testing/perguntas-teste-chat-jun2026.md) | Roteiro ampliado (fabril, MP, apresentação) |
| [../roadmap/playbook-chat-preco-mp-simulador-custos-pa.md](../roadmap/playbook-chat-preco-mp-simulador-custos-pa.md) | Preço MP + simulador PA |
| [../../../api-delpi/docs/api/11-guia-agente-chat.md](../../../api-delpi/docs/api/11-guia-agente-chat.md) | Guia api-delpi para agentes |

**Smoke automatizado (opcional):**

```bash
cd minha-delpi-ai-api
SMOKE_MP_CODE=10080001 SMOKE_PA_CODE=90261255 SMOKE_PRODUCT_CODE=90269002 \
  SMOKE_BASE_URL=http://localhost PYTHONPATH=. python scripts/smoke_playbook_product_routes.py
```
