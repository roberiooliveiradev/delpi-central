# Homologação manual — apresentação de dados (jun/2026)

Checklist amostral para validar a generalização de apresentação **antes de release**. Complementa a suíte automatizada (Fase 6).

**Roteiro copiável (playbook + apresentação):** [`perguntas-teste-chat-jun2026.md`](perguntas-teste-chat-jun2026.md).

## Pré-requisitos

- Gateway + api-delpi + minha-delpi-ai-api em homologação
- Usuário de teste com acesso às rotas operacionais
- Produtos de referência: `10080001` (MP), `90261255` (PA), `90269002` (playbook fabril)

## Métricas alvo (amostra manual)

| Métrica | Meta | Como medir |
|---------|------|------------|
| Preferência respeitada | ≥ 95% | Toolbar Tabela/Gráfico/Árvore/Texto/Documento → `presentationDecision.selected` coerente |
| Rotas tier B+ com apresentação útil | ≥ 90% | Resposta com texto ou tabela/gráfico não vazio |
| Layout stack vs single | documentar | `presentationDecision.layoutMode` em rotas multi-seção (analyser, estoque) |

Baseline automatizada: `scripts/audit_presentation_coverage.py` → `tierBPlusRatio`, `tierABProfileMappedRatio`.

## Amostra por domínio (10 rotas cada)

Marque **OK** / **Falha** / **N/A** após exercitar no chat (modo Automático + preferência explícita).

### Produto (10)

| # | Pergunta exemplo | Rota esperada | Auto | Tabela | Gráfico |
|---|------------------|---------------|------|--------|---------|
| 1 | estoque do produto {code} | `/stock` | | | |
| 2 | estrutura do produto {code} | `/structure` | | | |
| 3 | analyser produto {code} | `/analyser` | | | |
| 4 | status fabril {code} hoje | `/factory-status` | | | |
| 5 | análise preço MP {code} | `/raw-material-price-intelligence` | | | |
| 6 | impacto custo PA {code} | `/cost-impact-simulation` | | | |
| 7 | fornecedores do produto {code} | `/suppliers` | | | |
| 8 | compras do produto {code} | `/purchases` | | | |
| 9 | onde é usado {code} | `/parents` | | | |
| 10 | resumo cadastral {code} | `/summary` | | | |

### Suprimentos / Financeiro / Comercial (10)

| # | Pergunta exemplo | Entidade | Auto | Tabela | KPI |
|---|------------------|----------|------|--------|-----|
| 1 | CPV suprimentos | `supplies_cpv` | | | |
| 2 | OTD suprimentos | `supplies_otd` | | | |
| 3 | ROL financeiro | `financial_rol` | | | |
| 4 | taxa de fechamento comercial | `sales_conversion_rate` | | | |
| 5 | série ROL comercial | `commercial_rol_series` | | | |
| 6 | novos clientes média | `new_clients_average` | | | |
| 7 | propostas comerciais | `commercial_proposal` | | | |
| 8 | custo MOD produção | `direct_labor_cost_pct` | | | |
| 9 | OEE produção | `overall_equipment_effectiveness` | | | |
| 10 | eficiência fabril dashboard | `eficiencia_fabril_dashboard` | | | |

### RH / Qualidade / Engenharia (10)

| # | Pergunta exemplo | Entidade | Auto | Texto | Tabela |
|---|------------------|----------|------|-------|--------|
| 1 | snapshot RH | `hr_snapshot` | | | |
| 2 | filiais RH | `hr_branch` | | | |
| 3 | PDI ativos | `hr_active_pdi_count` | | | |
| 4 | série não conformidades | `nonconformity_series` | | | |
| 5 | resumo kaizen | `kaizen_summary` | | | |
| 6 | resumo auditoria 5S | `audit_5s_summary` | | | |
| 7 | PPM interno série | `ppm_internal_series` | | | |
| 8 | dashboard LMP | `lmp_dashboard` | | | |
| 9 | itens LMP | `lmp_dashboard_items` | | | |
| 10 | transforma mais processos | `transforma_mais_process` | | | |

## Critérios de aceite por rota

1. `execute_external_action` com `metadata.ok=true`
2. `presentationDecision.selected` ∈ `availableViews`
3. Preferência explícita (toolbar) altera `selected` e `presentation.type` no mesmo turno
4. Textos visíveis vêm de JSON (sem string nova hardcoded na API)
5. Chips pós-resposta coerentes com perfil (`interactivity.json`)

## Comandos

Comando útil (smoke local):

```bash
# Auditoria + gate perfis
cd minha-delpi-ai-api && PYTHONPATH=. python scripts/audit_presentation_coverage.py --check-profiles

# Perguntas manuais (roteiro jun/2026)
# Ver docs/testing/perguntas-teste-chat-jun2026.md
```

## Registro de execução

| Data | Ambiente | Responsável | Preferência OK % | Tier B+ OK % | Observações |
|------|----------|-------------|------------------|--------------|-------------|
| | homolog | | | | |
