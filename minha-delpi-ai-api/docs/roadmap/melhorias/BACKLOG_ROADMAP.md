# Backlog ativo — roadmap melhorias (31/05/2026)

Itens **ainda não fechados** após sincronização com o código. Concluídos estão em [STATUS_ROADMAP_MELHORIAS.md](./STATUS_ROADMAP_MELHORIAS.md).

## Prioridade alta (produto + chat base)

| # | Item | Playbook | Esforço |
|---|------|----------|---------|
| 1 | **Admin UX mockup 11** — aprovação produto + PR única (6 seções) | [11](./playbooks_melhoria_minha_delpi_chat/11_admin_ux_reorganizacao_abas.md) | Grande (MFE) |
| 2 | **Indexação anexos** — PDF/XLSX no upload + resposta automática | [07](./playbooks_melhoria_minha_delpi_chat/07_anexos_e_arquivos.md) | Médio |
| 3 | **Router `resolvedParams`** + pendências ativas | [01](./playbooks_melhoria_minha_delpi_chat/01_roteamento_inteligente_de_intencoes.md) | Médio |
| 4 | **E2E api-delpi mock** por domínio | [auditoria](../api-delpi-chat-intelligence-audit.md) | Médio |

## Prioridade média (UX)

| # | Item | Playbook | Notas |
|---|------|----------|-------|
| 5 | **Heatmap** + dashboard multi-card | [gráficos](./playbook_ampliacao_graficos_minha_delpi_chat.md) Fase 4 | MFE + presenter |
| 6 | Filtros/zoom/comparar períodos no gráfico | Gráficos Fase 5 | Parcial (toggle tipo ✅) |
| 7 | **Onboarding** guiado (primeiro uso) | [10](./playbooks_melhoria_minha_delpi_chat/10_onboarding_e_adoção_de_usuarios.md) | Produto |
| 8 | Admin textos Fases 3–5 | [textos](./playbook_assistente_administrativo_textos_minha_delpi_chat.md) | MFE admin |

## Infra / homologação

| # | Item | Doc |
|---|------|-----|
| 9 | SQL Server TOTVS acessível no dev (`TOTVS_DB_HOST`) | [smoke-system-metadata](../../testing/smoke-system-metadata-homologacao.md) |
| 10 | **Onda 12** — skill drawing-analyser PDF | [onda-12](../inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md) |

## Recém-concluído (referência)

- Metadados Protheus `/system` + smoke E2E (`db38c4ed`, `f311dd43`, `c2ec8179`)
- Interatividade Fase 4 — menus tabela/árvore/gráfico + **chip de contexto** (MFE)
- Interatividade Fase 5 — fluxos guiados (`ChatGuidedFlowService`)
- Gráficos Fases 1–3 + alternância de tipo no MFE
- Autoajuda Fases 1–5; pesquisa web Fases 1–5
