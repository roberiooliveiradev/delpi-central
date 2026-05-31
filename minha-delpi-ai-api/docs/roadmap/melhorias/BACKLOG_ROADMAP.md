# Backlog ativo — roadmap melhorias (31/05/2026)

Itens **ainda não fechados** após sincronização com o código. Concluídos estão em [STATUS_ROADMAP_MELHORIAS.md](./STATUS_ROADMAP_MELHORIAS.md).

## Prioridade alta (produto + chat base)

| # | Item | Playbook | Esforço |
|---|------|----------|---------|
| 1 | **Admin UX** — polish E2E Playwright, unificar builder no admin (futuro) | [11](./playbooks_melhoria_minha_delpi_chat/11_admin_ux_reorganizacao_abas.md) | Médio |
| 2 | ~~Anexos OCR imagem~~ (feito) — refinamentos de extração | [07](./playbooks_melhoria_minha_delpi_chat/07_anexos_e_arquivos.md) | Baixo |
| 3 | ~~Router pendências ativas~~ (feito) — refinamentos de roteamento | [01](./playbooks_melhoria_minha_delpi_chat/01_roteamento_inteligente_de_intencoes.md) | Baixo |

## Prioridade média (UX)

| # | Item | Playbook | Notas |
|---|------|----------|-------|
| 5 | ~~Mini dashboards por agente~~ (feito) — refinamentos de recomendações | [gráficos](./playbook_ampliacao_graficos_minha_delpi_chat.md) Fase 4 | Baixo |
| 6 | ~~Gráficos Fase 5 — lousa + export CSV dashboard~~ (feito) — refinamentos PNG multi-painel | Gráficos Fase 5 | Baixo |
| 7 | ~~Onboarding guiado~~ (feito) — materiais treinamento, analytics adoção | [10](./playbooks_melhoria_minha_delpi_chat/10_onboarding_e_adoção_de_usuarios.md) | Baixo |
| 8 | Admin textos — Fase 3 parcial (home Textos + modelos +); Fases 4–5 | [textos](./playbook_assistente_administrativo_textos_minha_delpi_chat.md) | MFE + chat base |

## Infra / homologação

| # | Item | Doc |
|---|------|-----|
| 9 | SQL Server TOTVS acessível no dev (`TOTVS_DB_HOST`) | [smoke-system-metadata](../../testing/smoke-system-metadata-homologacao.md) |
| 10 | **Onda 12** — skill análise de desenhos PDF | [playbook](./playbook_skill_analise_desenhos_delpi.md) · [onda-12](../inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md) |

## Recém-concluído (referência)

- Metadados Protheus `/system` + smoke E2E (`db38c4ed`, `f311dd43`, `c2ec8179`)
- Interatividade Fase 4 — menus tabela/árvore/gráfico + **chip de contexto** (MFE)
- Interatividade Fase 5 — fluxos guiados (`ChatGuidedFlowService`)
- Gráficos Fases 1–3 + alternância de tipo no MFE
- Autoajuda Fases 1–5; pesquisa web Fases 1–5
- Smoke api-delpi por domínio (mock + amostra chat) — `smoke_api_delpi_domain_routing.py`
