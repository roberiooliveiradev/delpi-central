# Playbook 07 — Interatividade com Botões

Projeto: Minha DELPI Chat IA  
Escopo: chips, menus contextuais, sugestões de próximos passos e interface guiada.

> **Princípio:** toda resposta útil deve sugerir uma próxima ação útil — menos digitação, mais descoberta.

---

## Implementação (jun/2026)

| Componente | Responsabilidade |
|------------|------------------|
| `interactivity.json` | Grupos, prioridades, fontes de metadata, chips de apresentação |
| `ChatInteractivitySuggestionService` | Consolida sugestões → `metadata.interactivity` (até 4 primários + «Mais opções») |
| `ChatPresentationInteractivityService` | Chips pós-tabela/gráfico/árvore |
| `ChatOperationalRefinementInteractivityService` | Chips de refinamento (paginação, estoque, período) |
| `ChatAssistantMessageMenu` (MFE) | Menu «Mais ações» na resposta (formato, lousa) |
| `ChatInteractivityBlock` (MFE) | UI unificada com confirmação e botões desabilitados |
| `ChatFollowUpChips` | Contrato expandido (`id`, `group`, `kind`, `disabledReason`, …) |
| `ChatInteractivityQueryResolver` / `ChatInteractivityPreferenceService` | Placeholders + ranking por uso na sessão |
| `ChatInteractivityAdminMetricsService` | CTR admin (`interactivityMetrics`, `chat.interactivity.clicked`) |
| `AdminInteractivityMetrics` (MFE) | Painel Métricas — impressões vs cliques |
| Legado | `ChatContextBar`, `ChatRichTable`/`Chart`/`Tree` menus, `ChatGuidedFlowService`, starters na home |

---

## Contrato `metadata.interactivity`

```json
{
  "interactivity": {
    "consolidated": true,
    "maxPrimary": 4,
    "suggestions": [{ "id": "…", "label": "Ver estoque", "query": "…", "group": "consultar", "kind": "primary" }],
    "moreSuggestions": { "formatar": [{ "label": "…", "query": "…" }] },
    "contextBar": { "items": [], "summary": "…" },
    "sourceIntent": "product_lookup",
    "suggestionsShown": ["Ver estoque", "…"]
  }
}
```

Quando `consolidated: true`, o MFE usa `ChatInteractivityBlock` em vez de várias fileiras de chips duplicadas.

---

## Testes

| Caso | Esperado |
|------|----------|
| I1–I16 | produto, estoque, texto, e-mail, erro, tabela/gráfico/lousa, overflow, confirmação, desabilitado, contexto, placeholder, preferência |

Arquivos: `tests/fixtures/interactivity_cases.py`, `tests/unit/application/services/test_chat_interactivity.py`, `scripts/smoke_interactivity.py`.

Menus por linha/ponto/nó: já em `ChatRichTable`, `ChatRichChart`, `ChatRichTree` (Fase 3 legado).

---

## Roadmap

| Fase | Status |
|------|--------|
| 1 — Chips básicos | Concluída (consolidação + contrato expandido) |
| 2 — Contexto e memória | Concluída (`contextBar` no bloco; `ChatInteractivityQueryResolver`; preferência por sessão em `interactivityUsage`) |
| 3 — Menus contextuais | Concluída (tabela/gráfico/árvore/contexto) |
| 4 — Ações avançadas | Concluída (refinamento operacional, menu da mensagem, apresentação/lousa/export) |
| 5 — Métricas | Concluída (`interactivityMetrics` + `chat.interactivity.clicked`, `GET /admin/metrics/interactivity/summary`, painel `AdminInteractivityMetrics`) |

---

## Resumo executivo

O chat consolida sugestões em um bloco único, com contexto, preferência por sessão e painel admin de CTR. Evolução futura opcional: A/B de ranking e feedback agregado além do CTR.
