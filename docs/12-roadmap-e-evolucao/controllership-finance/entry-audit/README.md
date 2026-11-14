# Entry audit — Auditoria de entradas (Protheus × XML de NF-e e CT-e)

| Campo | Valor |
|---|---|
| Status | **READY** — [trilha de execução](./track.md) |
| Doc | 168 |
| Produto | Portal Controladoria & Finanças + CLARA |
| Permissão | `controllership-finance.access` (D4) |
| Frequência | sob demanda, em qualquer dia (D10) |
| Origem | skill `auditoria-entradas-nfe-protheus` e painel «Raio-X das Entradas» |

O usuário — ou a CLARA, num comando — escolhe o período e as filiais e executa a auditoria. A BFF busca o Protheus (api-delpi) e os XML (financial-api/Questor), roda o motor de regras e guarda o resultado. O dashboard mostra o que pede ação, onde se concentra e como evoluiu; as ocorrências podem ser marcadas como resolvidas por qualquer pessoa da equipe.

## Conteúdo

| Pasta / arquivo | O que tem |
|---|---|
| [track.md](./track.md) | **trilha de execução** T0–T13 para o Cursor: quadro de status, protocolo, paradas, rollback, roteiro de verificação |
| [plan.md](./plan.md) | objetivo, AS-IS, decisões D1–D14, arquitetura, ganhos, critério de paridade, riscos, registro |
| [backend/](./backend/README.md) | fluxo de uma auditoria; rotas da api-delpi, da financial-api e da BFF; camadas da BFF; worker; dados necessários; persistência |
| [frontend/](./frontend/README.md) | visão geral do dashboard; convenções (dimensionamento, URL, vocabulário); páginas [01 Entrada e execução](./frontend/01-pagina-entrada-e-execucao.md), [02 Dashboard da análise](./frontend/02-pagina-dashboard-da-analise.md), [03 Detalhe da ocorrência](./frontend/03-pagina-detalhe-da-ocorrencia.md); [04 Componentes novos e evoluções do plugin-ui](./frontend/04-componentes-plugin-ui-novos-e-evolucoes.md); [wireframes](./frontend/wireframes-auditoria-entradas.html) |
| [mcp/](./mcp/README.md) | CLARA: capacidades no catálogo, conhecimento (fichas AE-00 a AE-15), diretivas de conduta, perguntas ao owner |
| [reference/](./reference/skill-auditoria-entradas-nfe-protheus/) | cópia da skill (SKILL.md, catálogo de regras, scripts) para o porte e o teste de paridade; sem a cópia da SF4 |
| [planning/](./planning/planejamento-auditoria-entradas.xlsx) | tarefas, dependências, responsáveis e datas |

## Próximos passos

1. ~~Cursor: T0 a T9~~ — feito (T9, T9R, T9R2 em PROD, 14/11/2026).
2. ~~Owner + Claude: verificação pela CLARA~~ — feita; os residuais estão em [residuals.md](./residuals.md).
3. Cursor: zerar os residuais do back-end — prompt em [prompts/T9R3-residuais-backend.md](./prompts/T9R3-residuais-backend.md).
4. Cursor: T10–T13 (front-end), **só depois do passo 3** — prompt em [prompts/T10-T13-frontend.md](./prompts/T10-T13-frontend.md).
