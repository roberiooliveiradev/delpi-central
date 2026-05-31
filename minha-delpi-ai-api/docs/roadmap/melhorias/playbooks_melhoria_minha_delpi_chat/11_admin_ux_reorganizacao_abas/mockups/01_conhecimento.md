# Mockup — Conhecimento (aba legada)

## Estado atual

- **Componente:** `AdminKnowledgeTab`
- **Conteúdo:** ingestão, listagem paginada, filtros (status, categoria, namespace, domínio, tag, tipo de fonte), metadados curadoriais, teste RAG por documento.
- **Dores:** admin não sabe se a base está saudável sem ir em Métricas; upload e curadoria competem com a mesma tela densa.

## Jobs do administrador

1. Enviar documento / URL para a base global.
2. Filtrar e encontrar documento por domínio ou tag.
3. Corrigir metadados (domínio, visibilidade, expiração).
4. Testar se um trecho responde no RAG antes de publicar para usuários.

## Wireframe (proposta — mesma aba, layout)

```
┌─────────────────────────────────────────────────────────────┐
│ Conhecimento                          [Atualizar] [Ingestão]│
├─────────────────────────────────────────────────────────────┤
│ KPI strip: Total │ Indexados │ Pendentes │ Falhas (24h)     │
├─────────────────────────────────────────────────────────────┤
│ Filtros (linha 1): busca │ status │ domínio │ tag           │
│ Filtros (linha 2): categoria │ namespace │ tipo fonte        │
├─────────────────────────────────────────────────────────────┤
│ Tabela documentos                                           │
│  nome │ domínio │ status │ atualizado │ ações (⋯)          │
├─────────────────────────────────────────────────────────────┤
│ Painel lateral (opcional): detalhe + teste RAG do selecionado │
└─────────────────────────────────────────────────────────────┘
```

## Componentes / API

- `GET/POST` documentos admin, ingestão, `testAdminRag`
- Manter pasta `knowledge/`; extrair `KnowledgeFiltersBar`, `KnowledgeTable`, `KnowledgeDetailDrawer` se necessário na implementação final.

## Fora de escopo nesta aba

- Diretrizes de comportamento → aba Diretrizes (mockup 02).
- Skills Markdown → aba Skills (mockup 03).
- Configuração de inteligência global → futura seção Plataforma (mockup 11).

## Rotas (futuro — não implementar agora)

- Legado: aba `knowledge` em `/apps/minha-delpi-chat/admin`
- Futuro possível: `/admin/curadoria/documentos`

## Critérios de aceite

- [x] KPI strip visível sem rolar em desktop 1280px (`KnowledgeSummaryStrip`, maio/2026).
- [ ] Ingestão abre fluxo sem esconder filtros.
- [ ] Teste RAG no documento selecionado com resultado legível.
- [x] Nenhum link para mockup 11 quebrado enquanto em 10 abas planas.

## Implementado (incremental, 10 abas planas)

- API: `summary` em `GET /admin/knowledge/documents` (`total`, `active`, `inactive`, `pendingIndex`).
- MFE: `KnowledgeSummaryStrip` no topo da aba; clique em Total/Indexados/Inativos aplica filtro de status.
