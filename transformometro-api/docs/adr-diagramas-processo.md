# ADR — Diagramas de processo (Playbook 19)

**Status:** implementado (jul/2026)  
**Contexto:** [`PLAYBOOK-19-diagramas-processo-revisao-escopo.md`](../../docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-19-diagramas-processo-revisao-escopo.md)  
**Status técnico:** [`playbook-19-implementation-status.md`](./playbook-19-implementation-status.md)

## Decisão

1. **Diagrama-macro 1:1 com processo-mestre** — JSON `flowchart_v1` em `processo_diagramas.conteudo`.
2. **Escopo por instância** — subset de `node_id` em `instancia_diagrama_escopo`; default `inherit_all=true`.
3. **Overlay por revisão** — JSON `flowchart_overlay_v1` em `revisao_diagrama_overlays.conteudo`.
4. **Mermaid derivado** — gerado server-side no save; cache em `mermaid_cached`.
5. **Editor MVP** — React Flow no MFE (`FlowchartEditor`, lazy); preview Mermaid; **não** editar Mermaid como fonte.

### Formato `flowchart_v1` (extensões S6)

| Campo | Uso |
|-------|-----|
| `lanes[]` | Swimlanes horizontais (`id`, `label`, `height`, `order`) |
| `nodes[].lane_id` | Faixa do nó (validado contra `lanes`) |
| `edges[].routing` | `straight` \| `step` \| `smoothstep` (default `smoothstep`) |

Layout e posições vivem no JSON; Mermaid é derivado sem swimlanes no MVP.

## Schemas

- [`flowchart_v1.schema.json`](./flowchart_v1.schema.json)
- [`flowchart_overlay_v1.schema.json`](./flowchart_overlay_v1.schema.json)

Validação runtime: `tm_app/domain/diagram/flowchart_v1.py`.

## Migrations

| Versão | Tabela |
|--------|--------|
| V026 | `processo_diagramas` |
| V027 | `instancia_diagrama_escopo` |
| V028 | `revisao_diagrama_overlays` |

## Endpoints

| Método | Path |
|--------|------|
| GET/PUT | `/transformometro/processos/{id}/diagrama` |
| GET/PUT | `/transformometro/instancias/{id}/diagrama-escopo` |
| GET | `/transformometro/revisoes/{id}/diagrama` (merge) |
| GET/PUT | `/transformometro/revisoes/{id}/diagrama/overlay` |
| GET | `/transformometro/revisoes/{id}/diagrama/mermaid` |

Rotas: `tm_app/interface/http/routes/diagram_routes.py`.

## Editor MFE (S6)

- Formas BPMN-lite: início, fim, atividade, decisão (+ paleta documento/dado/subprocesso)
- Swimlanes manuais: adicionar, renomear, remover; snap vertical ao arrastar
- Templates: linear, decisão, BPMN + swimlanes (CRM → Engenharia)
- Auto-layout por rank de fluxo; exclusão com Delete/Backspace
- Tema claro/escuro alinhado ao shell Delpi
- Export PNG (`html-to-image`); revisão pode enviar PNG como evidência V024

## Consequências

- Backup JSON inclui `processo_diagramas`, `instancia_diagrama_escopos`, `revisao_diagrama_overlays`.
- `audit_logs` registra `diagram.macro.updated`, `diagram.escopo.updated`, `diagram.overlay.updated`.
- Macro alterado após overlay: aviso no merge (`warnings` no GET revisão).
- Bundle MFE: chunk separado `FlowchartEditor` (~150 kB gzip) via lazy import.

## Fora de escopo

- BPMN 2.0 XML, simulação, swimlanes automáticas por cadastro, edição colaborativa, LLM → diagrama.
