# ADR — Diagramas de processo (Playbook 19)

**Status:** aprovado (jul/2026)  
**Contexto:** [`PLAYBOOK-19-diagramas-processo-revisao-escopo.md`](../../docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-19-diagramas-processo-revisao-escopo.md)

## Decisão

1. **Diagrama-macro 1:1 com processo-mestre** — JSON `flowchart_v1` em `processo_diagramas.conteudo`.
2. **Escopo por instância** — subset de `node_id` em `instancia_diagrama_escopo`; default `inherit_all=true`.
3. **Overlay por revisão** — JSON `flowchart_overlay_v1` em `revisao_diagrama_overlays.conteudo`.
4. **Mermaid derivado** — gerado server-side no save; cache em `mermaid_cached`.
5. **Editor MVP** — React Flow no MFE; preview Mermaid lazy (padrão chat).

## Schemas

- [`flowchart_v1.schema.json`](./flowchart_v1.schema.json)
- [`flowchart_overlay_v1.schema.json`](./flowchart_overlay_v1.schema.json)

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

## Consequências

- Backup JSON inclui as três tabelas de diagrama.
- `audit_logs` registra `diagram.macro.updated`, `diagram.escopo.updated`, `diagram.overlay.updated`.
- Export PNG client-side pode virar evidência V024 (`tipo=diagrama_export`).
