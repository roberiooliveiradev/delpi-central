# Entry audit — Auditoria de entradas (Protheus × XML de NF-e e CT-e)

| Campo | Valor |
|---|---|
| Status | **PLAN_DRAFT** |
| Doc | 168 |
| Produto | Portal Controladoria & Finanças + CLARA |
| Permissão | `controllership-finance.access` (D4) |
| Frequência | sob demanda, em qualquer dia (D10) |
| Origem | skill `auditoria-entradas-nfe-protheus` e painel «Raio-X das Entradas» |

O usuário — ou a CLARA, num comando — escolhe o período e as filiais e executa a auditoria. A BFF busca o Protheus (api-delpi) e os XML (financial-api/Questor), roda o motor de regras e guarda o resultado. O dashboard mostra o que pede ação, onde se concentra e como evoluiu; as ocorrências podem ser marcadas como resolvidas por qualquer pessoa da equipe.

## Conteúdo

| Pasta / arquivo | O que tem |
|---|---|
| [plan.md](./plan.md) | objetivo, AS-IS, decisões D1–D10, arquitetura, ganhos, fases E0–E7, critério de paridade, riscos, registro |
| [backend/](./backend/README.md) | fluxo de uma auditoria; rotas da api-delpi, da financial-api e da BFF; camadas da BFF; worker; dados necessários; persistência |
| [frontend/](./frontend/README.md) | visão geral do dashboard; convenções (dimensionamento, URL, vocabulário); páginas [01 Entrada e execução](./frontend/01-pagina-entrada-e-execucao.md), [02 Dashboard da análise](./frontend/02-pagina-dashboard-da-analise.md), [03 Detalhe da ocorrência](./frontend/03-pagina-detalhe-da-ocorrencia.md); [04 Componentes novos e evoluções do plugin-ui](./frontend/04-componentes-plugin-ui-novos-e-evolucoes.md); [wireframes](./frontend/wireframes-auditoria-entradas.html) |
| [mcp/](./mcp/README.md) | CLARA: capacidades no catálogo, conhecimento (fichas AE-00 a AE-15), diretivas de conduta, perguntas ao owner |
| [reference/](./reference/skill-auditoria-entradas-nfe-protheus/) | cópia da skill (SKILL.md, catálogo de regras, scripts) para o porte e o teste de paridade; sem a cópia da SF4 |
| [planning/](./planning/planejamento-auditoria-entradas.xlsx) | tarefas, dependências, responsáveis e datas |

## Próximos passos

1. Owner: aprovar wireframes e páginas; confirmar D1, D2, D5, D7 e a execução direta pela CLARA; responder as perguntas do [mcp §7](./mcp/README.md).
2. Cursor: E0 — inventário somente leitura (SQL do Protheus, listagem do Questor por período, filiais e volume).
