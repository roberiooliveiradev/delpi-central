# Roadmap — Minha DELPI Chat

Documentação de evolução do painel administrativo e da API `minha-delpi-ai-api`.

| Documento | Conteúdo |
|---|---|
| [admin-minha-delpi-chat.md](./admin-minha-delpi-chat.md) | Roadmap detalhado por item (status, entregas, evidências). |
| [melhorias-futuras.md](./melhorias-futuras.md) | Melhorias pós-roadmap admin (implementadas; RBAC core externo pendente). |
| [inteligencia-chat-onda-1.md](./inteligencia-chat-onda-1.md) | Inteligência do chat — Onda 1 (concluída). |
| [inteligencia-chat-onda-2.md](./inteligencia-chat-onda-2.md) | Inteligência do chat — Onda 2 (concluída). |
| [inteligencia-chat-onda-3.md](./inteligencia-chat-onda-3.md) | Inteligência do chat — Onda 3 (concluída). |
| [inteligencia-chat-onda-4.md](./inteligencia-chat-onda-4.md) | Inteligência do chat — Onda 4 (concluída). |
| [inteligencia-chat-onda-5.md](./inteligencia-chat-onda-5.md) | Inteligência do chat — Onda 5 (concluída). |
| [inteligencia-chat-onda-6.md](./inteligencia-chat-onda-6.md) | Inteligência do chat — Onda 6 (concluída: modelo 1.5b + pipeline + regressão). |
| [inteligencia-chat-onda-7.md](./inteligencia-chat-onda-7.md) | Inteligência do chat — Onda 7 (concluída: templates, OpenAPI, regressão, calibração RAG, homologação latência). |
| [inteligencia-chat-onda-8.md](./inteligencia-chat-onda-8.md) | Inteligência do chat — Onda 8 (concluída: sub-rotas structure/parents, despacho por intent, scoring dedicado). |
| [apresentacao-rica-chat-onda-9.md](./apresentacao-rica-chat-onda-9.md) | Inteligência do chat — Onda 9 (concluída: tabelas ricas, gráficos, cards KPI, canvas expandível, export XLSX/PDF/PNG). |
| [rag-context-min-score-calibracao.md](./rag-context-min-score-calibracao.md) | Calibração `RAG_CONTEXT_MIN_SCORE` e checklist de latência. |
| [notificacoes-minha-delpi.md](./notificacoes-minha-delpi.md) | Notificações de plataforma: broadcast, integrações e UI no chat. |
| [agentes-gestao-melhorias.md](./agentes-gestao-melhorias.md) | Gestão de agentes — melhorias (ondas 1–7 concluídas). |

## Regra operacional

Antes de criar funcionalidades, alterar layout, endpoints, migrations ou comportamento do agente, consultar estes documentos e a documentação da API em `docs/api/`.

**Inteligência do chat:** ondas 1–9 concluídas. Onda 9 entregou apresentação rica de dados: tabelas interativas com sort/CSV, gráficos Recharts com toggle tabela↔gráfico, cards KPI com tendência, canvas expandível com exportação XLSX/PDF/PNG, e refinamentos de acessibilidade. Onda 8 entregou sub-rotas dedicadas (structure, parents/onde é usado), despacho explícito por intent e scoring dedicado no ranking de actions.
