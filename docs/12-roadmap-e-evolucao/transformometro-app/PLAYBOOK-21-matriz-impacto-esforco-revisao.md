# Playbook 21 — Matriz impacto × esforço por revisão (melhoria)

**Status:** S0 design lock (jul/2026) — S1–S4 pendentes  
**Decisões fechadas (S0):**

- **Unidade de análise = revisão** (`revisao_id`), não instância nem processo-mestre isolado.
- **Baseline** não entra no scatter de priorização (é referência); opcionalmente exibida como marcador fixo `(0,0)` ou oculta.
- **Modo padrão = `auto`** — scores derivados de `calc_rules` + cadastro existente (medição, investimentos, recursos, comparativo).
- **Override manual** por revisão em JSON (`revisao_matriz_impacto_esforco_v1`) — não duplica regra financeira no MFE.
- **Normalização por escopo** — percentil 0–100 entre revisões **da mesma instância** (melhoria); visão processo = agregação opcional fase 2.
- **Componente visual canônico** — `@delpi/plugin-ui` `ImpactEffortMatrix` (headless SVG + BEM); Transformômetro só consome + estiliza.
- **Cálculo na API** — serviço de domínio único; MFE render-only (sem reimplementar ROI/economia).

**Parent:** [`PLAYBOOK-MODELAGEM.md`](./PLAYBOOK-MODELAGEM.md) · [`PLAYBOOK-18`](./PLAYBOOK-18-instancias-filial-setor-escopo.md) · [`regras-de-calculo.md`](../../../transformometro-api/docs/regras-de-calculo.md)  
**Wireframe:** [`plugins/transformometro/docs/wireframes/matriz-impacto-esforco.md`](../../../plugins/transformometro/docs/wireframes/matriz-impacto-esforco.md)  
**Schema:** [`revisao_matriz_impacto_esforco_v1.schema.json`](../../../transformometro-api/docs/revisao_matriz_impacto_esforco_v1.schema.json)  
**Status implementação:** [`playbook-21-implementation-status.md`](../../../transformometro-api/docs/playbook-21-implementation-status.md)

---

## 1. Problema observado

| Sintoma | Impacto |
|---------|---------|
| `prioridade` na instância é qualitativa (`baixa`/`media`/`alta`) | Não reflete ROI, payback nem custo de implantação **por revisão** |
| Comparativo financeiro existe (tabela/gráfico barras) | Gestor não vê **quick wins** vs. projetos pesados num único quadro |
| Dados para impacto/esforço já estão no cadastro | Falta **agregação semântica** e visualização na árvore do workspace |
| Priorização manual desconectada do motor | Risco de priorizar melhoria cara com baixo retorno |

**Princípio:** cada **revisão comparável** da melhoria recebe coordenadas **impacto** (benefício) e **esforço** (custo/complexidade), calculadas preferencialmente a partir do que já foi medido — com ajuste manual auditável quando o algoritmo não captura o contexto.

---

## 2. Modelo de domínio

### 2.1 Hierarquia

```text
processo_instancias (melhoria)
  └── revisoes[]
        ├── medicoes / investimentos / recursos  → insumos do cálculo
        ├── revisao_referencia_id                → delta vs. baseline/melhoria anterior
        └── matriz_impacto_esforco (JSONB, opcional)
              ├── modo: auto | manual | hibrido
              ├── inputs_manuais (qualitativos 1–5)
              └── overrides { impacto?, esforco? }
```

### 2.2 Eixos (definição de negócio)

| Eixo | Significado | Alto = |
|------|-------------|--------|
| **Impacto** | Benefício esperado/realizado da revisão | Mais economia líquida, horas, ROI, redução de erro/retrabalho |
| **Esforço** | Custo e complexidade de implantar/sustentar | Mais investimento, opex, recursos, HH, dependências |

### 2.3 Quadrantes (UI)

| `quadrante` | Impacto | Esforço | Ação sugerida |
|-------------|---------|---------|---------------|
| `quick_win` | ≥ limiar | < limiar | Priorizar |
| `strategic` | ≥ limiar | ≥ limiar | Planejar com cuidado |
| `fill_in` | < limiar | < limiar | Quando sobrar capacidade |
| `rethink` | < limiar | ≥ limiar | Reavaliar escopo ou adiar |

Limiar padrão: **50** (escala 0–100). Configurável por resposta API (`threshold: 50`).

### 2.4 Confiança do score

| `confianca` | Critério |
|-------------|----------|
| `alta` | Medição + referência + ≥1 investimento ou recurso; janela de vigência ativa |
| `media` | Medição + referência; investimentos/recursos parciais |
| `baixa` | Só inputs manuais ou cadastro incompleto |
| `indisponivel` | Baseline ou revisão não comparável |

---

## 3. Cálculo (modo `auto`)

**Serviço canônico:** `RevisaoImpactEffortMatrixService` (`transformometro-api/tm_app/domain/services/` ou `application/services/`).

**Fontes (sem SQL novo na v1):**

- `DashboardCalculatorService.build_dashboard_rows` — economia, investimento, horas (12m ou média mensal × 12)
- `ProcessRevisionCompareService` — totais por revisão
- Contagens: investimentos, vínculos recurso, nós overlay WBS/diagrama (peso leve de complexidade)
- Medição vs. referência — Δ `% erro`, `% retrabalho`

### 3.1 Componentes normalizados (0–1) → score 0–100

**Impacto (pesos v1):**

```text
impacto_raw =
  0.40 × norm(economia_liquida_anual)
+ 0.20 × norm(horas_economizadas_anual)
+ 0.15 × norm(roi_cap_24m)
+ 0.15 × norm(Δ_retrabalho + Δ_erro)
+ 0.10 × norm(escopo_overlays)    # contagem nós alterados (cap)
```

**Esforço (pesos v1):**

```text
esforco_raw =
  0.45 × norm(investimento_total_anual)
+ 0.25 × norm(custo_recursos_anual)
+ 0.20 × norm(horas_internas + treinamento)
+ 0.10 × norm(complexidade_cadastro)  # #investimentos + #recursos + overlays
```

`norm(x)` = percentil entre revisões comparáveis da **mesma instância** (exclui baseline). Empate → 50.

### 3.2 Modo `hibrido`

```text
impacto_score = clamp(0.7 × auto + 0.3 × manual_impacto × 20, 0, 100)
esforco_score = clamp(0.7 × auto + 0.3 × manual_esforco × 20, 0, 100)
```

Campos manuais: escala 1–5 em `inputs_manuais`.

### 3.3 Modo `manual`

Somente `inputs_manuais` + overrides; `confianca = baixa` até medição existir.

### 3.4 Regras de exclusão

- `cenario_tipo = baseline` → `incluir_na_matriz: false` (referência)
- Revisão fora da vigência 12m e inativa → `incluir_na_matriz: false` ou badge «expirada»
- `status_aprovacao = rejeitada` → ocultar por padrão (query `?incluir_rejeitadas=false`)

---

## 4. Persistência (migration S1)

**Opção recomendada:** coluna JSONB na revisão (sem tabela filha na v1).

```sql
-- V038__revisao_matriz_impacto_esforco.sql (proposta)
ALTER TABLE transformometro.revisoes
  ADD COLUMN IF NOT EXISTS matriz_impacto_esforco JSONB;

COMMENT ON COLUMN transformometro.revisoes.matriz_impacto_esforco IS
  'Overrides e inputs manuais da matriz impacto×esforço (schema revisao_matriz_impacto_esforco_v1). Scores auto são calculados; não persistir auto-only.';
```

**O que persistir:** `modo`, `inputs_manuais`, `overrides`, `atualizado_por`, `atualizado_em`.  
**O que não persistir:** scores `auto` (sempre recalculados).

---

## 5. Contrato API

Envelope padrão Transformômetro: `{ success, message, data }`.

### 5.1 GET `/transformometro/instancias/{instancia_id}/matriz-impacto-esforco`

Matriz da **melhoria** (todas as revisões comparáveis da instância).

**Query:**

| Param | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `competencia` | `YYYY-MM` | mês corrente | Competência para economia |
| `horizonte_meses` | int | `12` | Anualização |
| `incluir_rejeitadas` | bool | `false` | |
| `incluir_baseline` | bool | `false` | Ponto de referência no scatter |

**Response `data`:**

```json
{
  "instancia_id": "uuid",
  "processo_id": "uuid",
  "competencia": "2026-07",
  "horizonte_meses": 12,
  "threshold": 50,
  "eixos": {
    "impacto": { "label": "Impacto", "min": 0, "max": 100 },
    "esforco": { "label": "Esforço", "min": 0, "max": 100 }
  },
  "quadrantes": {
    "quick_win": { "label": "Quick wins" },
    "strategic": { "label": "Estratégicos" },
    "fill_in": { "label": "Complementares" },
    "rethink": { "label": "Reavaliar" }
  },
  "pontos": [
    {
      "revisao_id": "uuid",
      "versao_revisao": "1.1.0",
      "cenario_tipo": "melhoria",
      "label": "v1.1.0 · Melhoria de processo",
      "revisao_ativa": true,
      "impacto": 72.4,
      "esforco": 41.2,
      "quadrante": "quick_win",
      "confianca": "alta",
      "modo": "auto",
      "incluir_na_matriz": true,
      "metricas": {
        "economia_liquida_anual": 188784.0,
        "horas_economizadas_anual": 320.5,
        "roi_medio": 2.4,
        "payback_meses": 8,
        "investimento_total_anual": 45000.0
      },
      "componentes": {
        "impacto": { "economia": 0.82, "horas": 0.65, "roi": 0.91, "qualidade": 0.55, "escopo": 0.40 },
        "esforco": { "investimento": 0.48, "recursos": 0.32, "hh": 0.25, "complexidade": 0.38 }
      }
    }
  ],
  "ativo": {
    "revisao_id": "uuid",
    "impacto": 72.4,
    "esforco": 41.2,
    "quadrante": "quick_win"
  }
}
```

**Erros:** `404` instância não encontrada.

---

### 5.2 GET `/transformometro/revisoes/{revisao_id}/matriz-impacto-esforco`

Detalhe de **uma revisão** (card no cadastro + destaque no scatter da instância).

**Query:** `competencia`, `horizonte_meses` (mesmos defaults).

**Response `data`:** objeto `ponto` (mesma forma de item em `pontos[]`) + `vizinhos` (outros pontos da instância, ids + coordenadas apenas) + `inputs_persistidos` (JSONB salvo).

---

### 5.3 PUT `/transformometro/revisoes/{revisao_id}/matriz-impacto-esforco`

Salva overrides / inputs manuais (não recalcula nem grava scores auto).

**Body:**

```json
{
  "modo": "hibrido",
  "inputs_manuais": {
    "impacto_qualitativo": 4,
    "esforco_qualitativo": 3,
    "alinhamento_estrategico": 5,
    "dependencias_externas": 2,
    "pessoas_afetadas": 120,
    "observacao": "Piloto Q3 — adoção ainda incerta."
  },
  "overrides": {
    "impacto": null,
    "esforco": null
  }
}
```

**Response:** `data` = resultado de GET single (scores recalculados com novo modo).

**Validação:** schema `revisao_matriz_impacto_esforco_v1`; `modo` enum; escalas 1–5; audit `revisao.matrix.updated`.

---

### 5.4 GET `/transformometro/processos/{processo_id}/matriz-impacto-esforco` (fase 2)

Todas as instâncias do processo; `pontos[].instancia_id` + cor por melhoria.

---

### 5.5 Integração com rotas existentes

| Rota existente | Relação |
|----------------|---------|
| `GET /processos/{id}/comparativo` | Fonte de totais; matriz **não** duplica payload |
| `GET /revisoes/{id}/diagnostico-rateio` | Banner de alerta permanece; matriz pode exibir chip «rateio > ganho» |
| `DashboardLiveService` | Mesma competência/horizonte que dashboard quando `competencia` omitida |

---

## 6. UI / MFE (`plugins/transformometro`)

Ver wireframe dedicado. Resumo:

| Superfície | Componente |
|------------|------------|
| Cadastro revisão | `RevisaoMatrizImpactoSection` — `ChartCard` + `ImpactEffortMatrix` |
| Instância | scatter todas revisões + tabela ranking |
| Árvore workspace | badge cor por `quadrante` no nó `revisao:*` |
| Help | `TM_HELP_TOOLTIPS.matriz.*` (plugin local; textos PT) |

**Classes BEM:** `tm-impact-effort-*` via `impactEffortMatrixTransformometroClasses()` helper no plugin.

**Não fazer:** scatter Recharts só no Transformômetro; cálculo de score no TS.

---

## 7. `@delpi/plugin-ui` (componentes compartilhados)

| Export | Responsabilidade |
|--------|------------------|
| `ImpactEffortMatrix` | SVG scatter + quadrantes + pontos clicáveis |
| `ImpactEffortMatrixLegend` | Legenda quadrantes + confiança |
| `impactEffortMatrixBemClasses` | BEM `delpi-ui-impact-effort-matrix__*` |
| `impactEffortMatrixTransformometroClasses` | Alias `tm-impact-effort-matrix__*` |
| Tipos `ImpactEffortPoint`, `ImpactEffortQuadrant` | Contrato estável API ↔ UI |

Catálogo: [`plugins/plugin-ui/docs/component-catalog.md`](../../../plugins/plugin-ui/docs/component-catalog.md) § Matriz impacto×esforço.

Reuso futuro: `cadastro-kaizen` (priorização de ideias), `quality-action-plans`.

---

## 8. Sprints

| Sprint | Entrega | Repo |
|--------|---------|------|
| **S0** | Playbook, schema JSON, wireframe, componente plugin-ui (headless) | docs + plugin-ui |
| **S1** | `RevisaoImpactEffortMatrixService` + GET instância/revisão | transformometro-api |
| **S2** | PUT overrides + migration V038 + audit | transformometro-api |
| **S3** | `RevisaoMatrizImpactoSection` + API client + seção no cadastro | transformometro |
| **S4** | Badge na árvore + scatter na instância + testes regressão | transformometro |
| **S5** | Visão processo multi-melhoria + export PNG (plugin-ui export) | ambos |

---

## 9. Testes e gates

| Teste | Onde |
|-------|------|
| Normalização percentil entre 3 revisões | `test_revisao_impact_effort_matrix_service.py` |
| Baseline excluída | idem |
| Modo hibrido/manual | idem |
| Fixture → quadrante esperado | `fixtures/cadastro/` ou inline |
| `ImpactEffortMatrix` render + a11y | `plugin-ui` vitest |
| Regressão API smoke | `scripts/ci-transformometro-api.sh` |

---

## 10. Checklist antes de merge (S1+)

- [ ] Cálculo só em serviço canônico (sem duplicar `calc_rules`)
- [ ] Textos PT em `helpTooltips` / JSON assistant — não strings em Python de regra
- [ ] MFE render-only (`ImpactEffortMatrix` do plugin-ui)
- [ ] Migration + backup JSON inclui `matriz_impacto_esforco` quando persistido
- [ ] Teste com revisão real (medição + investimento) da fixture cadastro
