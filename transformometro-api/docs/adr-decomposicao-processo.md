# ADR — Decomposição de processo (Playbook 20)

**Status:** proposto (jul/2026)  
**Contexto:** [`PLAYBOOK-20-decomposicao-processo-arvore-mapeamento.md`](../../docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-20-decomposicao-processo-arvore-mapeamento.md)  
**Status técnico:** [`playbook-20-implementation-status.md`](./playbook-20-implementation-status.md)

## Decisão

1. **Dois mapas por processo-mestre** — árvore `decomposition_tree_v1` (WBS / planilha) **+** fluxo `flowchart_v1` (Playbook 19).
2. **Árvore 1:1 com processo-mestre** — JSON em `processo_decomposicao.conteudo`.
3. **Escopo por instância** — subset de `node_id` em `instancia_decomposicao_escopo`; default `inherit_all=true`.
4. **Instâncias operacionais preservadas (PB18)** — timeline de revisões/medições/investimentos permanece na instância; árvore no mestre **não substitui** instância.
5. **Contexto instância (S3+)** — JSON `instancia_contexto_v1` em `processo_instancias.contexto` — metadados operacionais além de rotulo/status.
6. **Overlay por revisão** — JSON `decomposition_overlay_v1` em `revisao_decomposicao_overlays.conteudo`.
7. **Export tabular derivado** — CSV/Excel gerado por `DecompositionFlatExportService`; filtrado por instância/escopo.
8. **Vínculo fluxo ↔ árvore** — `flowchart_v1.nodes[].meta.decomposition_id` → `node_id` da árvore (opcional; validado com warnings).

### Níveis da árvore

| `level` | Papel |
|---------|--------|
| `processo_chave` | Filho direto da raiz (macroprocesso) |
| `tarefa` | Filho de processo-chave (opcional) |
| `sub_tarefa` | Folha operacional; filho de tarefa ou processo-chave |

## Schemas

- [`decomposition_tree_v1.schema.json`](./decomposition_tree_v1.schema.json)
- [`decomposition_overlay_v1.schema.json`](./decomposition_overlay_v1.schema.json)

Validação runtime prevista: `tm_app/domain/decomposition/decomposition_tree_v1.py`.

## Migrations (previstas)

| Versão | Tabela |
|--------|--------|
| V030 | `processo_decomposicao` |
| V031 | `instancia_decomposicao_escopo` |
| V032 | `revisao_decomposicao_overlays` |
| V033 | coluna `processo_instancias.contexto` JSONB (`instancia_contexto_v1`) |

## Endpoints (previstos)

| Método | Path |
|--------|------|
| GET/PUT | `/transformometro/processos/{id}/decomposicao` |
| GET | `/transformometro/processos/{id}/decomposicao/export.csv` |
| GET/PUT | `/transformometro/instancias/{id}/decomposicao-escopo` |
| GET/PUT | `/transformometro/instancias/{id}/contexto` |
| GET | `/transformometro/revisoes/{id}/decomposicao` (merge) |
| GET/PUT | `/transformometro/revisoes/{id}/decomposicao/overlay` |
| POST | `/transformometro/processos/{id}/decomposicao/validar-vinculos-fluxo` |

## Consequências

- Backup JSON inclui decomposição + escopos + overlays (Playbook 20 S4).
- `audit_logs`: `decomposition.updated`, `decomposition.scope.updated`, `decomposition.overlay.updated`.
- Playbook 19 permanece válido; nó `subprocess` ganha semântica via `decomposition_id`.
- **Instâncias (PB18) intactas** — escopo WBS + contexto enriquecem a instância; cálculo continua por revisão.
- UI distingue **Macroprocesso** (mestre) de **Processo-chave** (nível árvore).

## Fora de escopo

- Medição por processo-chave; import Excel como fonte; LLM → árvore; substituir fluxo por árvore.
