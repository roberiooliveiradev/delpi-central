# Playbook 20 — status de implementação

**Playbook:** [`PLAYBOOK-20-decomposicao-processo-arvore-mapeamento.md`](../../docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-20-decomposicao-processo-arvore-mapeamento.md)  
**ADR:** [`adr-decomposicao-processo.md`](./adr-decomposicao-processo.md)  
**Última atualização:** jul/2026

## Resumo

| Sprint | Escopo | Status |
|--------|--------|--------|
| S0 | Design lock — playbook, schemas JSON, ADR | ✅ doc |
| S1 | V030 + API árvore + editor processo | ✅ |
| S2 | Export CSV planilha | ✅ |
| S3 | V031/V033 + escopo instância + contexto | ✅ |
| S4 | V032 + overlay revisão + backup/audit | ✅ |
| S5 | Vínculo `decomposition_id` + assistente rascunho | ✅ parcial (validar + sugerir) |
| S6 | Colaboração WS + diff textual | ✅ parcial (seções WS + baseline_diff API) |

## Entregas

### API (`transformometro-api`)

- Migrations V030–V033
- Domain: `tm_app/domain/decomposition/decomposition_tree_v1.py`
- Repositories: processo / instância escopo / revisão overlay
- Services: merge, flat export CSV, link validator
- Routes: `decomposition_routes.py`
- Backup JSON: bundles `processo_decomposicao`, `instancia_decomposicao_escopos`, `revisao_decomposicao_overlays`
- Testes: `test_decomposition_tree_v1.py`, `test_decomposition_services.py`

### MFE (`plugins/transformometro`)

- `DecompositionTreeEditor`, `DecompositionFlatPreview`
- Seções: processo, instância (escopo + contexto), revisão
- API client: `transformometroDecompositionApi.ts`
- Checklist de preenchimento inclui item «Mapeamento»

## Backlog pós-MVP

- Export Excel (.xlsx) endpoint
- Import assistido planilha legado
- Medição por processo-chave (FK futura)
- Diff visual textual dedicado na UI revisão
