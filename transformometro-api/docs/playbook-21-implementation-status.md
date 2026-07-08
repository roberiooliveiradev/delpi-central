# Playbook 21 — status de implementação

**Playbook:** [`PLAYBOOK-21-matriz-impacto-esforco-revisao.md`](../../docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-21-matriz-impacto-esforco-revisao.md)  
**Schema:** [`revisao_matriz_impacto_esforco_v1.schema.json`](./revisao_matriz_impacto_esforco_v1.schema.json)  
**Wireframe:** [`plugins/transformometro/docs/wireframes/matriz-impacto-esforco.md`](../../plugins/transformometro/docs/wireframes/matriz-impacto-esforco.md)  
**Última atualização:** jul/2026

## Resumo

| Sprint | Escopo | Status |
|--------|--------|--------|
| S0 | Design lock — playbook, contrato API, schema, wireframe, `ImpactEffortMatrix` plugin-ui | ✅ doc + componente headless |
| S1 | `RevisaoImpactEffortMatrixService` + GET instância/revisão | ✅ |
| S2 | PUT overrides + migration V038 + audit | ✅ |
| S3 | Seção no `RevisaoCadastroPanel` + API client | ✅ |
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

## Entregas S1

### API

- `RevisaoImpactEffortMatrixService` — percentil por instância, quadrantes, confiança
- `GET /transformometro/instancias/{instancia_id}/matriz-impacto-esforco`
- `GET /transformometro/revisoes/{revisao_id}/matriz-impacto-esforco`
- Testes: `tests/test_revisao_impact_effort_matrix_service.py`

## Entregas S2

### API

- Migration **V038** — coluna `revisoes.matriz_impacto_esforco` JSONB
- Validação domínio `validate_revisao_matriz_impacto_esforco_v1` / `build_persisted_matriz_payload`
- `PUT /transformometro/revisoes/{revisao_id}/matriz-impacto-esforco` + audit `revisao.matrix.updated`
- `RevisaoRepository.update_matriz_impacto_esforco`
- Testes: `tests/test_revisao_matriz_impacto_esforco_v1.py`

## Entregas S3

### MFE (`plugins/transformometro`)

- `transformometroMatrixApi.ts` — GET/PUT matriz revisão
- `RevisaoMatrizImpactoSection` — scatter, modo, ajustes manuais, resumo métricas
- Integração em `RevisaoCadastroPanel` (oculta baseline)
- `TM_HELP_TOOLTIPS.matriz` + `matrizImpactoLabels.ts`
- Estilos `.tm-impact-effort-section` em `index.css`

## Próximo passo (S4)

1. `InstanciaMatrizRevisoesSection` — scatter + tabela ranking na melhoria
2. Badge quadrante em `processoWorkspaceNav.ts`
