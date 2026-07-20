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
| S4 | Badge árvore workspace + scatter instância | ✅ |
| S5 | Visão processo multi-melhoria + export PNG | ✅ |

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

- `RevisaoImpactEffortMatrixService` — percentil entre peers com variância; **escala absoluta** quando há 1 revisão (ou componente empatado), para não colapsar em 50×50
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

## Entregas S4

### MFE

- `InstanciaMatrizRevisoesSection` — scatter + tabela ranking na melhoria
- Badge quadrante na árvore (`processoWorkspaceNav`, `ProcessoWorkspaceShell`, sidebar)
- Subpastas de revisão na árvore (`#matriz`, `#vigencia`, …) — `RevisaoWorkspaceSectionPanel`
- `fetchInstanciaMatrizImpactoEsforco` + `matrizImpactoPoints.ts`

## Entregas S5

### API

- `RevisaoImpactEffortMatrixService.build_for_processo()` — percentil entre todas as revisões comparáveis do processo
- `GET /transformometro/processos/{processo_id}/matriz-impacto-esforco`
- Testes: `test_build_for_processo_aggregates_melhorias` em `test_revisao_impact_effort_matrix_service.py`

### MFE

- `ProcessoMatrizImpactoSection` — scatter multi-melhoria + ranking + legenda por série
- Seção workspace `#priorizacao` em `ProcessoDetailPage`
- Export PNG (`exportImpactEffortMatrixPlotPng`) nas três visões: revisão, melhoria e processo
- `matrizImpactoSeriesColors.ts` + `accentColor` em `ImpactEffortPoint` (plugin-ui)

## Concluído (Playbook 21)

Sprints S0–S5 entregues. Evoluções futuras (fora do escopo original): filtros por cenário, comparação entre processos, export PDF.
