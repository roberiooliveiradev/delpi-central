# Playbook 20 — status de implementação

**Playbook:** [`PLAYBOOK-20-decomposicao-processo-arvore-mapeamento.md`](../../docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-20-decomposicao-processo-arvore-mapeamento.md)  
**ADR:** [`adr-decomposicao-processo.md`](./adr-decomposicao-processo.md)  
**Última atualização:** jul/2026

## Resumo

| Sprint | Escopo | Status |
|--------|--------|--------|
| S0 | Design lock — playbook, schemas JSON, ADR | ✅ doc |
| S1 | V030 + API árvore + editor processo | ⬜ pendente |
| S2 | Export CSV/Excel planilha | ⬜ pendente |
| S3 | V031 + escopo instância + contexto (`V033`) | ⬜ pendente |
| S4 | V032 + overlay revisão + backup/audit | ⬜ pendente |
| S5 | Vínculo `decomposition_id` + assistente rascunho | ⬜ pendente |
| S6 | Colaboração WS + diff textual | ⬜ pendente |

## Artefatos S0

| Artefato | Path |
|----------|------|
| Playbook | `docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-20-*.md` |
| Schema árvore | `transformometro-api/docs/decomposition_tree_v1.schema.json` |
| Schema overlay | `transformometro-api/docs/decomposition_overlay_v1.schema.json` |
| ADR | `transformometro-api/docs/adr-decomposicao-processo.md` |

## Pendências técnicas (S1+)

- [ ] Migration V030–V032
- [ ] Domain validator `decomposition_tree_v1.py`
- [ ] `DecompositionFlatExportService` + fixture LMP Engenharia
- [ ] Rotas `decomposition_routes.py`
- [ ] MFE `DecompositionTreeEditor` + seções processo/instância/revisão
- [ ] `helpTooltips.ts` — chaves `decomposition.*`
- [ ] Backup JSON — seções novas
- [ ] Testes J1–J10 (playbook §9)
