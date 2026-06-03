# Backlog ativo — roadmap melhorias (03/06/2026)

Itens **ainda não fechados** após sincronização com o código (revisão **03/06/2026**). Concluídos estão em [STATUS_ROADMAP_MELHORIAS.md](./STATUS_ROADMAP_MELHORIAS.md).

**Memória e contexto:** playbook [`playbook-memoria-e-contexto.md`](../playbook-memoria-e-contexto.md) **fechado** (Fases 1–9 + contexto livre/Q&A jun/2026).

**Pacote playbooks 01–10:** fechados como **MVP** ou **Concluído** no STATUS — não reabrir fases sem novo playbook.

## Bloqueado por produto

| # | Item | Playbook | Notas |
|---|------|----------|-------|
| 1 | **Admin UX mockup 11** — navegação 6 seções, drawer auditoria, layout 3 colunas simulação | [11](./playbooks_melhoria_minha_delpi_chat/11_admin_ux_reorganizacao_abas/mockups/11_painel_e_navegacao.md) | Mockups 01–10 no MFE; PR global após aprovação |
| 2 | Polish E2E Playwright admin (opcional) | [11](./playbooks_melhoria_minha_delpi_chat/11_admin_ux_reorganizacao_abas.md) | Médio |

## Evolução técnica (ondas)

| # | Item | Doc | Notas |
|---|------|-----|-------|
| 3 | **Onda 12** — cotas, checklist normas, paridade legado | [playbook](./playbook_skill_analise_desenhos_delpi.md) · [onda-12](../inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md) | MVP `drawing-analysis-delpi` + smoke |
| 4 | **Onda 13** — Docling/VLM, OCR avançado | [playbook](./playbook_skill_visao_documentos_ocr_delpi.md) · [onda-13](../inteligencia-chat-onda-13-skill-visao-documentos-ocr.md) | MVP Tesseract/PyMuPDF no chat base |

## Refinamentos baixos (não bloqueiam release)

| # | Item | Área |
|---|------|------|
| 5 | Export PNG multi-painel dashboard | Gráficos / Playbook 09 |
| 6 | Materiais PDF/vídeo + analytics finos de adoção | Onboarding 10 |
| 7 | Extração OCR imagem (refinamentos) | Anexos 07 |
| 8 | Personalidade / starters descontraídos | [playbook_chat_interativo_descontraido_minha_delpi.md](./playbook_chat_interativo_descontraido_minha_delpi.md) |

## Infra / homologação

| # | Item | Doc |
|---|------|-----|
| 9 | SQL Server TOTVS acessível no dev (`TOTVS_DB_HOST`) | [smoke-system-metadata](../../testing/smoke-system-metadata-homologacao.md) |

## Recém-concluído (referência)

- Playbook memória Fases 1–9 + contexto livre + Q&A (`fd551470`, `c351312f`, changelog `2026-06-contexto-manual-e-roadmap.md`)
- Migrations automáticas `minha-delpi-ai-api` no boot (`ceb8366c`)
- Editor de textos F1–7 (`playbook-especialista-editor-textos.md`, T1–T32)
- Onboarding MVP — tour, perfis, marcos (`ChatOnboardingService`, MFE)
- Apresentação rica Playbook 09 F1–6; gráficos ampliados F1–4 + `AgentMiniDashboard`
- Pacote melhorias 01–10 sincronizado no STATUS (03/06/2026)
