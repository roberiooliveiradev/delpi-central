# Playbook 19 — status de implementação (API + MFE)

Referência: [`docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-19-diagramas-processo-revisao-escopo.md`](../../docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-19-diagramas-processo-revisao-escopo.md)

Última atualização: **jul/2026**

## Sprints concluídos

| Sprint | Migrations / entrega | Status |
|--------|----------------------|--------|
| **S0 — Design lock** | ADR, JSON Schema `flowchart_v1` / `flowchart_overlay_v1` | ✅ |
| **S1 — Macro + API** | V026, `GET/PUT /processos/{id}/diagrama`, editor macro no MFE | ✅ |
| **S2 — Escopo instância** | V027, `GET/PUT /instancias/{id}/diagrama-escopo`, UI escopo | ✅ |
| **S3 — Overlay revisão** | V028, merge `GET /revisoes/{id}/diagrama`, overlay CRUD | ✅ |
| **S4 — Backup + audit** | Bundles JSON + `audit_logs` (`diagram.*.updated`) | ✅ |
| **S5 — Diff + export** | Diff baseline vs melhoria, PNG client-side, PNG → evidência V024 | ✅ |
| **S6 — Editor BPMN-lite** | Swimlanes, tema claro/escuro, auto-layout, gestão de faixas | ✅ |

## Migrations

**V026–V028** (diagramas) aplicadas após V025 no boot com `TM_RUN_MIGRATIONS_ON_STARTUP=true`.

| Versão | Tabela |
|--------|--------|
| V026 | `processo_diagramas` — macro `flowchart_v1` (JSONB + `mermaid_cached`) |
| V027 | `instancia_diagrama_escopo` — `node_ids`, `inherit_all` |
| V028 | `revisao_diagrama_overlays` — overlay `flowchart_overlay_v1` |

Ver [migrations/README.md](../migrations/README.md).

## Módulos canônicos (API)

| Responsabilidade | Arquivo |
|------------------|---------|
| Validação `flowchart_v1` / overlay / escopo | `tm_app/domain/diagram/flowchart_v1.py` |
| Export Mermaid | `tm_app/application/services/diagram_mermaid_export_service.py` |
| Merge macro + escopo + overlay | `tm_app/application/services/revisao_diagram_merge_service.py` |
| Rotas HTTP | `tm_app/interface/http/routes/diagram_routes.py` |
| Persistência | `processo_diagram_repository.py`, `instancia_diagram_escopo_repository.py`, `revisao_diagram_overlay_repository.py` |
| Backup JSON | `json_backup_service.py` — chaves `processo_diagramas`, `instancia_diagrama_escopos`, `revisao_diagrama_overlays` |

## Módulos canônicos (MFE)

| Tela | Componente |
|------|------------|
| Diagrama macro (processo) | `ProcessoDiagramSection.tsx` → `FlowchartEditor` (lazy) |
| Escopo por instância | `InstanciaDiagramEscopoSection.tsx` |
| Overlay por revisão | `RevisaoDiagramSection.tsx` |
| Tipos + templates | `src/types/diagram.ts` |
| Swimlanes / layout | `src/utils/diagramSwimlanes.ts` |
| Preview Mermaid | `DiagramMermaidPreview.tsx` |
| Client API | `src/data/api/transformometroDiagramApi.ts` |

Integração UI: `ProcessoDetailPage`, `InstanciaDetailPage`, `RevisaoCadastroPanel` (seção editável).

## Editor visual (S6)

| Recurso | Detalhe |
|---------|---------|
| Formas BPMN-lite | Início, fim, atividade (ícone manual), decisão (gateway ×), documento/dado/subprocesso |
| Swimlanes | Faixas horizontais (`lanes[]`, `lane_id`); snap ao arrastar |
| Conexões | `smoothstep` ortogonal; rótulo via duplo clique na aresta |
| Templates | Linear, com decisão, **BPMN + swimlanes** (CRM → Engenharia) |
| Tema | Claro/escuro via `useTransformometroDarkMode` + `colorMode` React Flow |
| Faixas | Adicionar, renomear (toolbar ou duplo clique no cabeçalho), remover (realoca nós) |
| Auto-layout | Rank por ordem do fluxo; posicionamento horizontal por faixa |
| Exclusão | `Delete` / `Backspace` em nó ou aresta selecionados |
| Export PNG | `html-to-image` no macro e na revisão; revisão pode anexar como evidência |

Validação API: `lanes`, `lane_id`, `routing` (`straight` \| `step` \| `smoothstep`) — ver `tests/test_flowchart_v1.py`.

## Testes

| Arquivo | Cobertura |
|---------|-----------|
| `tests/test_flowchart_v1.py` | Validação JSON, swimlanes, routing |
| `tests/test_diagram_mermaid_export_service.py` | Export Mermaid |
| `tests/test_revisao_diagram_merge_service.py` | Merge + escopo + overlay |
| `tests/test_json_backup_service.py` | Round-trip bundles de diagrama |

## Pós-deploy (1ª vez com V026–V028)

1. Rebuild + recreate `transformometro-api` e `transformometro` (migrations automáticas).
2. Conferir `migrations_runner status` até **V028**.
3. Smoke: processo → editar diagrama macro → salvar → preview Mermaid.
4. Instância → marcar escopo de nós → revisão → overlay as-is/to-be → salvar.
5. Backup JSON export → conferir chaves `processo_diagramas` / escopos / overlays.

## Pendente (fase futura)

| Item | Notas |
|------|-------|
| BPMN 2.0 XML | Fora do escopo Playbook 19 |
| Swimlanes automáticas por unidade/departamento | Manual + template hoje |
| Action OpenAPI chat (`mermaid_cached`) | Integração api-delpi |
| Simulação / tempos no diagrama | Fora de escopo |

## Referências

- [adr-diagramas-processo.md](./adr-diagramas-processo.md)
- [flowchart_v1.schema.json](./flowchart_v1.schema.json)
- [json-backup.md](./json-backup.md) — bundles de diagrama
- [status-atual.md](../../docs/12-roadmap-e-evolucao/transformometro-app/status-atual.md)
