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
| `ChatInteractivityBlock` (MFE) | UI unificada com confirmação e botões desabilitados |
| `ChatFollowUpChips` | Contrato expandido (`id`, `group`, `kind`, `disabledReason`, …) |
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
| I1 | chips de produto no primário |
| I3 | grupo formatar |
| I5 | recuperação após erro |
| I6 | chips de apresentação (tabela) |
| I10 | anexo na consolidação |
| I11 | overflow em «Mais opções» |

Arquivos: `tests/fixtures/interactivity_cases.py`, `tests/unit/application/services/test_chat_interactivity.py`, `scripts/smoke_interactivity.py`.

Menus por linha/ponto/nó: já em `ChatRichTable`, `ChatRichChart`, `ChatRichTree` (Fase 3 legado).

---

## Roadmap

| Fase | Status |
|------|--------|
| 1 — Chips básicos | Concluída (consolidação + contrato expandido) |
| 2 — Contexto e memória | Concluída (`contextBar` no bloco; `ChatInteractivityQueryResolver`; preferência por sessão em `interactivityUsage`) |
| 3 — Menus contextuais | Concluída (tabela/gráfico/árvore/contexto) |
| 4 — Ações avançadas | Parcial (apresentação, lousa, export nos menus) |
| 5 — Métricas | Parcial (log + clique persistido; CTR admin pendente) |

---

## Resumo executivo

O chat passa a consolidar sugestões em um bloco único, respeitando limite visual, permissões e confirmação em ações sensíveis. Evoluções futuras: ranking por uso de sessão e dashboard de CTR.
