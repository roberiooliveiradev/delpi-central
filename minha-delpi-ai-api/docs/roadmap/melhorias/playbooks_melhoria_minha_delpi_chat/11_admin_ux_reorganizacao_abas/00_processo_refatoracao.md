# Processo — refatoração do Admin (pós-revert)

## Por que revertemos

A reorganização em **6 seções + sub-abas + Painel + barra legada** (Playbook 11, commits `5e9b178d`–`be4568bc`) gerou regressões de UX (navegação duplicada, links quebrados, conteúdo escondido, RBAC/inteligência fora do lugar esperado).

O MFE voltou ao modelo **10 abas de primeiro nível** (`ChatAdminPage.tsx` + `AdminShellTopbar`) até concluirmos o desenho.

## Princípio deste ciclo

1. **Não alterar código do admin** até todos os mockups estarem alinhados.
2. **Uma aba por vez** — diagnóstico → mockup Markdown → revisão com você.
3. **Implementação única** no final — uma PR com rotas, shell e migração de componentes.

## Entregáveis por aba

Cada arquivo em [`mockups/`](./mockups/README.md) deve conter:

| Seção | Conteúdo |
|-------|----------|
| Estado atual | O que existe hoje (`Admin*Tab`, endpoints, dores) |
| Jobs do admin | Tarefas frequentes nesta aba |
| Proposta | Layout em ASCII/wireframe Markdown |
| Fora de escopo | O que não entra nesta aba (evitar mistura Métricas × Ferramentas) |
| Rotas | Slug sugerido só para referência (não implementar ainda) |
| Critérios de aceite | Checklist testável na homologação |

## Ordem sugerida de estudo

| # | Aba atual | Mockup | Motivo |
|---|-----------|--------|--------|
| 1 | Conhecimento | [01_conhecimento.md](./mockups/01_conhecimento.md) | Base da curadoria |
| 2 | Diretrizes | [02_diretrizes.md](./mockups/02_diretrizes.md) | Irmã de Conhecimento |
| 3 | Skills | [03_skills.md](./mockups/03_skills.md) | Comportamento global |
| 4 | Agentes | [04_agentes.md](./mockups/04_agentes.md) | Especialização + builder |
| 5 | Simulação | [05_simulacao.md](./mockups/05_simulacao.md) | Teste antes de publicar |
| 6 | Métricas | [06_metricas.md](./mockups/06_metricas.md) | Observabilidade pura |
| 7 | Avaliações | [07_avaliacoes.md](./mockups/07_avaliacoes.md) | Qualidade das respostas |
| 8 | Ferramentas | [08_ferramentas.md](./mockups/08_ferramentas.md) | LLM, actions, health |
| 9 | Segurança | [09_seguranca.md](./mockups/09_seguranca.md) | Anti-injection, scan |
| 10 | Auditoria | [10_auditoria.md](./mockups/10_auditoria.md) | Timeline e export |

Depois das 10 abas: documento **11_painel_e_navegacao.md** (agrupamento final em seções, deep links, mobile).

## Referência técnica (código estável)

- Página: `plugins/minha-delpi-chat/src/ui/pages/ChatAdminPage.tsx`
- Tipos de aba: `plugins/minha-delpi-chat/src/ui/components/admin/shell/adminShellTypes.ts`
- Rotas: `plugins/minha-delpi-chat/src/navigation/chatRoutes.ts` (`/admin`, `/admin/agentes/:id`)
- **DS alinhado ao workspace** (fora do escopo da reorganização em 6 seções): layout `mdc-chat-ws-directory`, topbar `mdc-chat-ws-topbar`, abas no padrão `mdc-chat-project-home__tabs`, tema em `admin-workspace-theme.css` + `admin-shared.css`.

## Quando implementar

- [ ] Mockups 01–10 revisados
- [ ] Mockup 11 (navegação global) aprovado
- [ ] Matriz de migração componente → nova árvore
- [ ] PR única + `npm run build` + homologação manual por aba
