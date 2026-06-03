# Status — roadmap `docs/roadmap/melhorias` (03/06/2026)

Índice de **fechamento documental** dos 40 arquivos desta pasta.  
**Concluído** = implementado no código ou arquivado como referência estável. **Parcial** = entregas iniciais + backlog explícito. **Aguardando** = depende de aprovação de produto.

Arquitetura transversal: [`../../architecture/chat-intelligence-base.md`](../../architecture/chat-intelligence-base.md) · Changelog: [`../../changelog/2026-05-melhorias-playbooks.md`](../../changelog/2026-05-melhorias-playbooks.md).

---

## Raiz (`melhorias/`)

| Arquivo | Status | Notas |
|---------|--------|-------|
| [README.md](./README.md) | Concluído | Índice vivo; smokes e serviços |
| [STATUS_ROADMAP_MELHORIAS.md](./STATUS_ROADMAP_MELHORIAS.md) | Concluído | Este arquivo |
| [playbook_memoria_sessao_preferencias_minha_delpi_chat.md](./playbook_memoria_sessao_preferencias_minha_delpi_chat.md) | Concluído | Fases 1–5 — `ChatConversationMemoryService` |
| [playbook-memoria-e-contexto.md](../playbook-memoria-e-contexto.md) | Fases 1–7 concluídas | Contexto avançado (F7) · Fases 8–9 backlog |
| [playbook_contexto_assertividade_minha_delpi_chat.md](./playbook_contexto_assertividade_minha_delpi_chat.md) | Concluído | Fases 1–5 (memória, assertividade, avaliação) |
| [playbook_interatividade_botoes_minha_delpi_chat.md](./playbook_interatividade_botoes_minha_delpi_chat.md) | Concluído | Fases 1–5 + menus contextuais (tabela, árvore, gráfico, chip) |
| [playbook_assistente_administrativo_textos_minha_delpi_chat.md](./playbook_assistente_administrativo_textos_minha_delpi_chat.md) | Parcial (UI) | Menu Textos MFE; inteligência textual → editor **Concluído** (`playbook-especialista-editor-textos.md`) |
| [playbook_correcao_texto_minha_delpi_chat.md](./playbook_correcao_texto_minha_delpi_chat.md) | Concluído | Fases 1–6 + lousa bidirecional; agregado §23 backlog |
| [playbook_escrita_emails_minha_delpi_chat.md](./playbook_escrita_emails_minha_delpi_chat.md) | Concluído | Fases 1–5 + preferências de sessão |
| [playbook_chat_interativo_descontraido_minha_delpi.md](./playbook_chat_interativo_descontraido_minha_delpi.md) | Parcial | `personality_playbook.json`, starters |
| [playbook_melhoria_pesquisa_web_minha_delpi_chat.md](./playbook_melhoria_pesquisa_web_minha_delpi_chat.md) | Concluído | Fases 1–5 + salvar fontes no projeto |
| [playbook_autoajuda_autoconhecimento_chat_minha_delpi.md](./playbook_autoajuda_autoconhecimento_chat_minha_delpi.md) | Concluído | Fases 1–5 (catálogo, painel ?, personalização, identity sync) |
| [playbook_ampliacao_graficos_minha_delpi_chat.md](./playbook_ampliacao_graficos_minha_delpi_chat.md) | Parcial | Fases 1–4 (heatmap + dashboard); mini dashboards por agente backlog |
| [playbook_skill_analise_desenhos_delpi.md](./playbook_skill_analise_desenhos_delpi.md) | Parcial | MVP Onda 12; Fase 3 cotas/OCR → Onda 13 |
| [playbook_skill_visao_documentos_ocr_delpi.md](./playbook_skill_visao_documentos_ocr_delpi.md) | Parcial | MVP Onda 13 — OCR PDF/imagem, métricas admin, profile `vision` |
| [sugestoes_perguntas_minha_delpi_chat_ia.md](./sugestoes_perguntas_minha_delpi_chat_ia.md) | Concluído | Referência de homologação |

### Análises (`analise_*.md`)

| Arquivo | Status |
|---------|--------|
| [analise_column_labels_minha_delpi_chat_ia.md](./analise_column_labels_minha_delpi_chat_ia.md) | Concluído (referência) → `ExternalActionColumnLabelService` |
| [analise_external_action_responses_minha_delpi_chat_ia.md](./analise_external_action_responses_minha_delpi_chat_ia.md) | Concluído (referência) → `external_action_responses.json` |
| [analise_identity_minha_delpi_chat_ia.md](./analise_identity_minha_delpi_chat_ia.md) | Concluído (referência) → `identity.json`, «quem sou eu» |
| [analise_operational_parameters_minha_delpi_chat_ia.md](./analise_operational_parameters_minha_delpi_chat_ia.md) | Concluído (referência) → refinamento filial/armazém |
| [analise_small_talk_minha_delpi_chat_ia.md](./analise_small_talk_minha_delpi_chat_ia.md) | Concluído (referência) → `ChatSmallTalkService` |
| [analise_stream_minha_delpi_chat_ia.md](./analise_stream_minha_delpi_chat_ia.md) | Concluído (referência) → streaming / atividades |
| [analise_utility_answers_minha_delpi_chat_ia.md](./analise_utility_answers_minha_delpi_chat_ia.md) | Concluído (referência) → respostas utilitárias |

---

## Pacote `playbooks_melhoria_minha_delpi_chat/`

| Playbook | Status | Código / smoke principal |
|----------|--------|---------------------------|
| [01 — Roteamento](./playbooks_melhoria_minha_delpi_chat/01_roteamento_inteligente_de_intencoes.md) | Parcial | Ver Playbook 02 (evolução) |
| [02 — Roteamento intenção](./playbook_roteamento_intencao_minha_delpi_chat.md) | Implementado | R1–R15, desambiguação produto, admin `/metrics/intent-routing/summary`, chips MFE |
| [03 — Especialista textos](./playbook_especialista_textos_minha_delpi_chat.md) | **Concluído** (F1–7) | Spec: [`playbook-especialista-editor-textos.md`](../playbook-especialista-editor-textos.md) · T1–T32 · commit `171d73cd` · pós-MVP: TextArtifact, E2E LLM |
| [02 — Operacional](./playbooks_melhoria_minha_delpi_chat/02_respostas_operacionais_delpi.md) | Parcial | Actions, presenter, vendas/estoque, smokes operacionais |
| [03 — Agentes](./playbooks_melhoria_minha_delpi_chat/03_agentes_especialistas.md) | Parcial | Agentes, providers, especialização |
| [04 — RAG](./playbooks_melhoria_minha_delpi_chat/04_rag_e_conhecimento_interno.md) | Parcial | RAG, skill company-knowledge |
| [05 — Feedback](./playbooks_melhoria_minha_delpi_chat/05_feedback_e_melhoria_continua.md) | Parcial | Avaliações admin, thumbs |
| [06 — Canvas](./playbooks_melhoria_minha_delpi_chat/06_lousa_canvas_area_de_trabalho.md) | Parcial | `ChatCanvasIntentService`, lousa MFE |
| [07 — Anexos](./playbooks_melhoria_minha_delpi_chat/07_anexos_e_arquivos.md) | Parcial | Index PDF/XLSX/CSV + preview colunas no welcome; `smoke_attachment_index_welcome.py` |
| [08 — Segurança](./playbooks_melhoria_minha_delpi_chat/08_seguranca_permissoes_confianca.md) | Parcial | SQL safety, trust badges, confirmação escrita |
| [09 — Gráficos](./playbooks_melhoria_minha_delpi_chat/09_dashboards_graficos_apresentacao_rica.md) | Parcial | Fase 1 PB09: `ChatPresentationDecisionService` + P1–P15 — ver [`playbook-09-apresentacao-rica.md`](../playbook-09-apresentacao-rica.md) |
| [10 — Onboarding](./playbooks_melhoria_minha_delpi_chat/10_onboarding_e_adoção_de_usuarios.md) | Backlog | Documentação de produto; pouca implementação dedicada |
| [11 — Admin UX](./playbooks_melhoria_minha_delpi_chat/11_admin_ux_reorganizacao_abas.md) | Parcial | 10 abas + DS workspace; refatoração 6 seções **aguardando** mockup 11 |

---

## Playbook 11 — mockups (`11_admin_ux_reorganizacao_abas/`)

| Arquivo | Status |
|---------|--------|
| [00_processo_refatoracao.md](./playbooks_melhoria_minha_delpi_chat/11_admin_ux_reorganizacao_abas/00_processo_refatoracao.md) | Parcial — processo definido; PR global após mockup 11 |
| [mockups/README.md](./playbooks_melhoria_minha_delpi_chat/11_admin_ux_reorganizacao_abas/mockups/README.md) | Concluído |
| [mockups/01–10](./playbooks_melhoria_minha_delpi_chat/11_admin_ux_reorganizacao_abas/mockups/) | Concluído (incrementos no MFE + KPI strips) |
| [mockups/11_painel_e_navegacao.md](./playbooks_melhoria_minha_delpi_chat/11_admin_ux_reorganizacao_abas/mockups/11_painel_e_navegacao.md) | Aguardando aprovação produto |

Itens explicitamente **fora do escopo** até mockup 11: drawer auditoria, layout 3 colunas simulação, gráficos interativos métricas, navegação em 6 seções.

---

## Smokes relacionados

| Script | Playbook / tema |
|--------|-----------------|
| `smoke_intent_route.py` | 01 |
| `smoke_operational_routing.py` | 02 |
| `smoke_product_sales_routing.py` | 02 (vendas) |
| `smoke_follow_up_chips.py` | Contexto + interatividade |
| `smoke_context_assertiveness_multiturn.py` | Contexto |
| `smoke_session_memory_persist.py` | Contexto Fase 4 |
| `smoke_sql_safety.py` | 08 |
| `smoke_admin_endpoints.py` | 11 |
| `smoke_identity_profile.py` | Identity |
| `run_onda11_validation.sh` | Regressão pacote |
| `smoke_system_table_routing.py` | Metadados Protheus `/system` |
| `smoke_attachment_index_welcome.py` | 07 — upload + welcome + summaries |
| `smoke_api_delpi_domain_routing.py` | Auditoria api-delpi — 9 domínios mock |

**Backlog ativo:** [BACKLOG_ROADMAP.md](./BACKLOG_ROADMAP.md).

---

## Regra de encerramento

Nenhum arquivo desta pasta exige reimplementação completa do escopo original dos playbooks — o fechamento é:

1. **Código** nas fases acordadas (chat base primeiro).
2. **Status** neste índice e no README.
3. **Backlog** explícito nos playbooks 10–11 e fases 2+ de pesquisa web / gráficos.

Última revisão em lote: **31/05/2026** (vendas produto, admin mockups 01–10, `resolvedFromMemory`).
