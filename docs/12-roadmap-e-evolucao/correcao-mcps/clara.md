# CLARA — Plano de correção da ficha técnica e autoconhecimento

**Data:** 2026-11-06  
**Estado:** EXECUTADO 2026-11-06.

## Resultado da execução (2026-11-06)
| ID | Resultado | Evidência |
|---|---|---|
| CLARA-01 | **CORRIGIDO** — acrônimo já existia no JSON canônico (`identity.acronym`), mas `agent_directives.character` (projeção `project_persona_context`) não o transportava; chave aditiva owner-local em `persona_context` agora ecoa `identity.acronym` no MCP/GPT — mesmo padrão de `avatar_distribution`, contrato compartilhado não alterado | `agent_intelligence_service.py`; assert em `test_agent_directives_integrate_character_on_mcp` |
| CLARA-02/05 | **PROVEN** — fonte canônica: `controllership_finance_app/content/clara_agent_intelligence.json` + `persona/clara_profile.py`; consumo via `capability_surface.agent_directives` | inventário |
| CLARA-03 | **VERIFICADO** — superfície MCP/catálogo coberta pela suíte existente (283 pass no escopo clara/mcp/character) | pytest |
| CLARA-04 | **TEST_NOT_RUN** — aceite conversacional no GPT real pendente de ambiente do agente | — |

**Arquivos alterados:** `controllership_finance_app/application/clara/agent_intelligence_service.py`, `tests/test_clara_character_profile.py`, este arquivo. Nenhuma mudança em OpenAPI/Actions/Knowledge/Instructions.

## Definição institucional aprovada pelo usuário (não é prova de runtime)
- **CLARA = Controladoria, Leitura, Análise, Resultados e Acompanhamento.**
- **C** — Controladoria.
- **L** — Leitura.
- **A** — Análise.
- **R** — Resultados.
- **A** — Acompanhamento.
- Classificação: **APPROVED FOR DOCUMENTATION / TARGET para identidade canônica do agente**. Não afirmar que a sigla já está presente no MCP, no GPT Builder ou nas APIs.

## PROVEN no MCP durante o inventário
- Nome publicado: **CLARA — Especialista em Controladoria & Finanças**.
- Apresentação: auxilia a compreender números, acompanhar fechamento mensal, investigar divergências e encontrar evidências para decisões.
- Identidade narrativa consultável por `get_context(topic=persona)`, em `agent_directives.character`; a expansão acima ainda não foi observada nessa projeção.
- Ferramentas MCP expostas: `get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete`.
- Catálogo `clara-semantic-v1`: 42 ações de `read`, 2 de `analyze`, 3 de `knowledge`, 48 operações governadas — listagem não equivale a autorização sobre recurso.
- Corpus de conhecimento: 2.203 itens, 88 fontes, metadados de publicação em 2026-11-03; não comprova conteúdo sobre identidade.

## Questões / plano de correção
| ID | Questão | Classificação | Direção de correção |
|---|---|---|---|
| CLARA-01 | Expansão oficial do nome não foi observada no MCP | **Acrônimo aprovado pelo usuário; runtime PENDING** | Propagar o significado exato à fonte canônica de identidade e à projeção pública governada, com testes |
| CLARA-02 | Em qual fonte canônica mora a identidade e como consultá-la com escopo mínimo? | TO_INVENTORY | Localizar owner, fonte, consumidores, catálogo, contrato e runtime; evitar duplicar autoridade |
| CLARA-03 | Tools, execution policies e operações do catálogo correspondem à implementação? | TO_INVENTORY | Auditar read/write, confirmação governada e postconditions |
| CLARA-04 | O GPT apresenta missão, nome/acrônimo, capabilities, ferramentas e limites fielmente? | TEST_NOT_RUN | Implementar matriz de perguntas conversacionais positivas/negativas |
| CLARA-05 | Qual documento compartilhado do GitHub é consumido pelas superfícies do agente? | TO_INVENTORY | Identificar documentação principal e sincronização com as projeções oficiais |

## Resposta conversacional de referência (TARGET)
"Eu sou a CLARA, especialista em Controladoria e Finanças da DELPI. Meu nome significa **Controladoria, Leitura, Análise, Resultados e Acompanhamento**. Ajudo a acompanhar fechamentos, analisar relatórios e pendências, investigar divergências e apresentar evidências para apoiar decisões. Para consultar ou executar operações, respeito as ferramentas disponíveis e suas permissões."

Não interpretar essa redação proposta como resposta comprovada de GPT.

## Critérios de aceite (TARGET)
1. `get_context` ou superfície canônica equivalente permite recuperar o nome e o acrônimo exatos.
2. Perguntas "Quem é você?", "O que significa CLARA?", "Qual sua atuação?", "Quais ferramentas possui?" produzem respostas coerentes sem narrativa inventada.
3. Capabilities são derivadas do catálogo vivo, distinguindo explicar/ler/analisar/preparar/escrever sob AuthZ, sem permissão autoconcedida.
4. Conhecimento, instruções, contratos e runtime estão alinhados; regressões e casos negativos testados.
5. Writes governados seguem contrato e postcondition verificada, não apenas sucesso técnico.

## Gates de implementação
Antes de qualquer mudança: inventariar `git status`, HEAD, owner, source, consumers, contrato, implementação e runtime; escolher menor diff; testar e fazer residual search. Publicar o acrônimo na origem correta; modificar GPT Builder/OpenAPI/Knowledge somente se seus artefatos mudarem. Retornar relatório de execução completo. **Nenhum código, MCP ou GPT Builder foi alterado nesta revisão documental.**
## Reconciliação com fontes existentes (GitHub, 2026-11-06)
- **PROVEN (código):** controllership-finance-api/controllership_finance_app/persona/clara_profile.py → controllership_finance_app/content/clara_agent_intelligence.json; **acronym já consta no JSON** com o texto aprovado; não cadastrar novamente.
- Contrato já implementado: `shared/delpi_character_profiles` (estrutura), ficha owner-local (conteúdo), projeção no serviço do MCP (consumer). **Não criar uma segunda ficha nem registry em shared.**
- Referência cruzada: [Inventário de fontes existentes](./INVENTARIO-FONTES-EXISTENTES.md). Validação de runtime, deploy e testes permanece **TEST_NOT_RUN/TO_INVENTORY** nesta auditoria.

**Retificação do backlog CLARA-01:** a tarefa de 'publicar acrônimo na fonte canônica' já está atendida no JSON. A única verificação residual pertinente é se o campo já é transportado e respondido corretamente pelas superfícies MCP/GPT; não implementar mudança sem falha comprovada no consumer.
