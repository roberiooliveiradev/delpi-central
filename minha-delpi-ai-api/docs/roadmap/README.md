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
| [inteligencia-chat-onda-10.md](./inteligencia-chat-onda-10.md) | Inteligência do chat — Onda 10 (concluída: novas rotas api-delpi, 100% route selection, títulos contextuais, vocabulário expandido). |
| [inteligencia-chat-onda-11-paridade-assistentes.md](./inteligencia-chat-onda-11-paridade-assistentes.md) | **Onda 11 (concluída):** paridade ChatGPT/Gemini — roteamento determinístico, velocidade, assertividade; interações básicas PT-BR. |
| [inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md](./inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md) | **Onda 12 (parcial/MVP):** skill `drawing-analysis-delpi` — [playbook](./melhorias/playbook_skill_analise_desenhos_delpi.md). |
| [inteligencia-chat-onda-13-skill-visao-documentos-ocr.md](./inteligencia-chat-onda-13-skill-visao-documentos-ocr.md) | **Onda 13 (MVP):** skill `document-vision-delpi` — [playbook OCR/visão](./melhorias/playbook_skill_visao_documentos_ocr_delpi.md); anexos, desenho e profile `vision` opcional. |
| [../changelog/2026-05-inteligencia-chat-entregas.md](../changelog/2026-05-inteligencia-chat-entregas.md) | **Maio/2026:** SQL produção (G1–G3), download fontes/anexos, bundle agente, Normas global, catálogo api-delpi, utility/small talk. |
| [../changelog/2026-06-playbook-inteligencia.md](../changelog/2026-06-playbook-inteligencia.md) | **Jun/2026:** playbook inteligência — typos, gate de turno simples, fallback honesto, preferências de sessão, métricas de eficiência, feedback, starters, streaming humanizado, avisar/contornar erros. |
| [api-delpi-chat-intelligence-audit.md](./api-delpi-chat-intelligence-audit.md) | Auditoria maio/2026: cobertura api-delpi, heurísticas de seleção, typos, regressão e backlog. |
| [playbook-04-autoajuda-chat.md](./playbook-04-autoajuda-chat.md) | **Playbook 04:** autoajuda — manual vivo do chat (catálogo, ajuda contextual, regressão A1–A12). |
| [playbook-05-anexos-lousa.md](./playbook-05-anexos-lousa.md) | **Playbook 05:** anexos e lousa — welcome, chips, ambiguidade, metadata de versão (L1–L12). |
| [playbook-11-clean-architecture-chat-api.md](./playbook-11-clean-architecture-chat-api.md) | **Playbook 11:** clean architecture — revisão, roadmap por fases, checklist de PR, baseline de auditoria. |
| [../architecture/adr/README.md](../architecture/adr/README.md) | **ADRs** do chat — decisões de camadas, JSON, ports e CI (Fase 6). |
| [playbook-06-erros-resultados-vazios.md](./playbook-06-erros-resultados-vazios.md) | **Playbook 06:** erros e vazios — classificação, templates, chips de recuperação (E1–E15). |
| [playbook-07-interatividade-botoes.md](./playbook-07-interatividade-botoes.md) | **Playbook 07:** interatividade — consolidação de chips, Mais opções, apresentação (I1–I15). |
| [melhorias/README.md](./melhorias/README.md) | Playbooks pós-Onda 11: status, smokes e índice. |
| [melhorias/BACKLOG_ROADMAP.md](./melhorias/BACKLOG_ROADMAP.md) | Backlog ativo priorizado (admin 11, anexos, heatmap, onboarding). |
| [../testing/smoke-system-metadata-homologacao.md](../testing/smoke-system-metadata-homologacao.md) | Homologação `/system` (SX2). |
| [../changelog/2026-05-contexto-memoria-assertividade.md](../changelog/2026-05-contexto-memoria-assertividade.md) | **Maio/2026:** memória de turno, score de assertividade, chips com produto, correções presenter/estrutura. |
| [../changelog/2026-05-melhorias-playbooks.md](../changelog/2026-05-melhorias-playbooks.md) | **Maio/2026:** referências/follow-up, contextChips UI, modo textual admin, chips pós-texto. |
| [rag-context-min-score-calibracao.md](./rag-context-min-score-calibracao.md) | Calibração `RAG_CONTEXT_MIN_SCORE` e checklist de latência. |
| [notificacoes-minha-delpi.md](./notificacoes-minha-delpi.md) | Notificações de plataforma: broadcast, integrações e UI no chat. |
| [agentes-gestao-melhorias.md](./agentes-gestao-melhorias.md) | Gestão de agentes — melhorias (ondas 1–7 concluídas). |

## Regra operacional

Antes de criar funcionalidades, alterar layout, endpoints, migrations ou comportamento do agente, consultar estes documentos e a documentação da API em `docs/api/`.

**Inteligência do chat:** ondas 1–11 concluídas ([paridade ChatGPT/Gemini + interações básicas PT-BR](./inteligencia-chat-onda-11-paridade-assistentes.md)). Entregas adicionais maio/2026: [changelog](../changelog/2026-05-inteligencia-chat-entregas.md). **Onda 12 (backlog):** [análise de desenhos PDF](./inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md). Onda 10 entregou novas rotas na api-delpi (`/products/{code}`, `/products/{code}/summary`), títulos contextuais no presenter, vocabulário expandido para detecção de intent, fix na seleção de OVs, e alcançou 100% de acerto em suite de 36 cenários reais. Onda 9 entregou apresentação rica de dados: tabelas interativas com sort/CSV, gráficos Recharts com toggle tabela↔gráfico, cards KPI com tendência, canvas expandível com exportação XLSX/PDF/PNG.
