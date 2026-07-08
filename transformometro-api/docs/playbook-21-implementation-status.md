# Playbook 21 — status de implementação

**Playbook:** [`PLAYBOOK-21-matriz-impacto-esforco-revisao.md`](../../docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-21-matriz-impacto-esforco-revisao.md)  
**Schema:** [`revisao_matriz_impacto_esforco_v1.schema.json`](./revisao_matriz_impacto_esforco_v1.schema.json)  
**Wireframe:** [`plugins/transformometro/docs/wireframes/matriz-impacto-esforco.md`](../../plugins/transformometro/docs/wireframes/matriz-impacto-esforco.md)  
**Última atualização:** jul/2026

## Resumo

| Sprint | Escopo | Status |
|--------|--------|--------|
| S0 | Design lock — playbook, contrato API, schema, wireframe, `ImpactEffortMatrix` plugin-ui | ✅ doc + componente headless |
| S1 | `RevisaoImpactEffortMatrixService` + GET instância/revisão | ⏳ pendente |
| S2 | PUT overrides + migration V038 + audit | ⏳ pendente |
| S3 | Seção no `RevisaoCadastroPanel` + API client | ⏳ pendente |
| S4 | Badge árvore workspace + scatter instância | ⏳ pendente |
| S5 | Visão processo multi-melhoria + export PNG | ⏳ backlog |

## Entregas S0

### Documentação

- Playbook 21 com fórmulas, quadrantes, contrato HTTP completo
- Schema JSON persistido na revisão
- Wireframe MFE (cadastro, instância, árvore)

### `@delpi/plugin-ui`

- `ImpactEffortMatrix` — scatter SVG headless + quadrantes
- `ImpactEffortMatrixLegend`
- Helpers BEM `impactEffortMatrixBemClasses` / `impactEffortMatrixTransformometroClasses`
- Estilos base em `styles.css` (`delpi-ui-impact-effort-matrix__*`)

## Próximo passo (S1)

1. `RevisaoImpactEffortMatrixService` consumindo `DashboardCalculatorService` + comparativo
2. Rotas em `crud_routes.py` ou `matrix_routes.py` dedicado
3. `test_revisao_impact_effort_matrix_service.py` com fixture 3 revisões
