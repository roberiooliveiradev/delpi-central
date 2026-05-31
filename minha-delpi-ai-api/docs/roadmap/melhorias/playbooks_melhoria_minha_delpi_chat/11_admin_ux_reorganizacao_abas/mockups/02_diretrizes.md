# Mockup — Diretrizes

## Estado atual

- `AdminGuidelinesTab` — CRUD, versionamento, teste RAG, editor + lista + versões.

## Jobs do administrador

1. Criar rascunho de diretriz de comportamento global.
2. Publicar ou arquivar diretriz existente.
3. Filtrar por status (ativa, rascunho, arquivada).
4. Testar impacto no RAG antes de publicar.

## Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│ KPI: Total │ Ativas │ Rascunhos │ Arquivadas    [Nova diretriz]│
├─────────────────────────────────────────────────────────────┤
│ Lista filtrada (cards)                                        │
├─────────────────────────────────────────────────────────────┤
│ Editor (aside) │ Teste RAG (main)                             │
├─────────────────────────────────────────────────────────────┤
│ Histórico de versões                                          │
└─────────────────────────────────────────────────────────────┘
```

## Fora de escopo

- Documentos da base → 01_conhecimento.

## Critérios de aceite

- [x] KPI strip + filtro por status (maio/2026).
- [x] Botão «Nova diretriz» no topo da aba.
- [ ] Teste RAG com resultado legível (validar na homologação).
- [x] Lista vazia com mensagem contextual quando filtro não retorna itens.

## Implementado (10 abas planas)

- `GuidelinesSummaryStrip` + `guidelinesSummary.ts` (contagens client-side).
- Lista recebe diretrizes filtradas conforme KPI clicado.
