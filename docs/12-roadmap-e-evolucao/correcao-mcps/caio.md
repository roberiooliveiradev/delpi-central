# CAIO — Plano de correção da ficha técnica e autoconhecimento

**Inventário:** 2026-11-06  
**Estado:** EXECUTADO 2026-11-06.
**Fonte observada:** `mcp__CAIO___Especialista_Comercial_DELPI__get_context`, `knowledge` e validação de roteamento `read`.

## Resultado da execução (2026-11-06)
| ID | Resultado | Evidência |
|---|---|---|
| CAIO-01 | **CORRIGIDO** — `Inteligência Operacional` → `Inteligência de Oportunidades` em todas as superfícies: `caio_profile.py` display_name, `branding.py` (`CAIO_FULL_NAME`, `CAIO_MCP_INSTRUCTIONS`), comentário em `constants.py`, assert em `test_caio_character.py`; `character_id=caio` e especialidade preservados | sed + residual search limpo |
| Acrônimo na projeção | **ADICIONADO** — `persona_context` ecoa `identity.acronym` derivado do sufixo do `display_name` (fonte única; chave aditiva owner-local, mesmo padrão de `avatar_distribution`) | `caio_agent_service.py` |
| CAIO-02/03/04 | **SEM MUDANÇA** — projeções de contexto/catálogo existentes adequadas; guide `caio.usage` cobre explicação de ferramentas | inventário |
| CAIO-05/07 | **TEST_NOT_RUN** — paridade de operações governadas e aceite conversacional pendente | — |
| CAIO-06 | **PROVEN** — ficha canônica em `commercial_app/persona/caio_profile.py` (approach Python válido, sem migração para JSON) | inventário |
| Residual | **NÃO RELACIONADO** — `test_portfolio_customer_coverage_passes_tuple_pairs_not_dataclasses` falha igualmente no HEAD limpo | stash + rerun |

**Arquivos alterados:** `commercial_app/persona/caio_profile.py`, `commercial_app/interface/mcp/branding.py`, `commercial_app/interface/mcp/constants.py`, `commercial_app/application/caio/caio_agent_service.py`, `tests/test_caio_character.py`, este arquivo.

## 1. Identidade proposta e evidência atual
- **TARGET aprovado pelo usuário em 2026-11-06:** **CAIO = Consultor de Análise e Inteligência de Oportunidades**; C = Consultor, A = Análise, I = Inteligência, O = Oportunidades. Definição com aderência explícita ao domínio Comercial.
- **PROVEN no runtime consultado antes da mudança:** **CAIO — Consultor de Análise e Inteligência Operacional**. Está em `assistant` e `agent_directives.character.identity.display_name`. **Não tratar o nome aprovado como já implantado.**
- Papel: Especialista Comercial da DELPI.
- Apresentação curta: "Olá! Eu sou o CAIO, especialista Comercial da DELPI. Gosto de conversar, entender necessidades e ajudar a transformar informações em oportunidades. Pode ficar à vontade comigo!"
- Especialidades narrativas: vendas, relacionamento com clientes, carteiras, pedidos em aberto e indicadores comerciais.
- Identidade narrativa: `profile_version=1`; persona ficcional, não autoridade operacional.
- Catálogo semântico informado: `catalog_version=2.0`; 6 tools (`get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete`).
- `get_context(topic=catalog)` retornou 29 grupos de entidades; `get_context()` retornou inventário mais amplo de ações. A projeção `topic=catalog` tinha 4 ações exemplificadas: a diferença de projeções NÃO prova falta de capabilities.
- `knowledge(topic=caio.usage)` respondeu versão `4.1.1` com guia de operação; `knowledge(topic=commercial.glossary)` respondeu glossário comercial e conceitos (OV/PV/OP/ROL/OTD).
- `read(entity=caio,action=usage)` foi rejeitado com validação clara, informando que a ação pertence a `knowledge`; comportamento correto da fronteira entre tools.

## 2. Contratos e limites
- Fontes operacionais pertencem à commercial-api e aos demais owners dos dados. CAIO não inventa ou recalcula indicadores.
- `read` consulta entidades via allowlist tipada; `analyze` distingue OBSERVED/CALCULATED/INFERRED/UNKNOWN; `knowledge` é orientação, não fonte de verdade operacional.
- Criações/atualizações autorizadas usam `execute` com regras do owner; exclusões destrutivas usam proposta selada `prepare → commit`; confirmação do chat não substitui autorização efetiva.
- Catálogo informa operações, mas AuthZ e escopo de carteira são verificados no backend; o acesso efetivo é específico do usuário/recurso.

## 3. Lacunas e propostas de correção
| ID | Diagnóstico | Evidência | Estado/ação TARGET |
|---|---|---|---|
| CAIO-01 | Acrônimo atual com 'Operacional' diverge do novo significado comercial aprovado ('Oportunidades') | PROVEN no catálogo antigo; novo nome APPROVED/TARGET | Localizar owner e atualizar identidade canônica, projeções e consumidores; testar "Quem é você?" e "O que significa CAIO?" sem prompt auxiliar |
| CAIO-02 | Descoberta de identidade compartilha payload de catálogo operacional potencialmente amplo | `get_context` lista múltiplas entidades e ações | Avaliar projeção pública compacta `self/identity` pelo mesmo owner, sem nova autoridade |
| CAIO-03 | Catálogo `topic=catalog` apresenta projeção compacta (4 ações observadas) versus conjunto amplo no tópico padrão | Comportamento observado, não defeito confirmado | Documentar projeções e verificar se consumidores sabem quando pedir inventário completo |
| CAIO-04 | Conjunto de ferramentas e capabilities precisa ser explicado em linguagem de negócio | Guide `caio.usage` existe | Resposta curta + detalhamento on demand derivado do catálogo vivo, sem overclaim |
| CAIO-05 | Paridade de catálogo, implementação e runtime de operações governadas não foi testada neste levantamento | Sem mutações executadas | Inventory de owner/consumer/contrato; regressões de erros, scopes, consentimento e read-back |
| CAIO-06 | Ficha institucional compartilhada e vínculo com caracterização do personagem não identificados | Fonte MCP encontrada; arquivo canônico não inventariado | Localizar arquivo owner, não duplicar identidade entre GitHub, MCP e GPT |
| CAIO-07 | Apresentação conversacional e limitações precisam de aceite | GPT isolado não testado | Matriz de QA positiva/negativa em GPT real e ambientes autorizados |

## 4. Matriz de aceite (TARGET)
- "Quem é você?" — retorna nome completo, área e missão, sem biografia inventada.
- "O que significa CAIO?" — responde **Consultor de Análise e Inteligência de Oportunidades** após implantação; até lá, divergência do runtime é esperada e deve ser reportada.
- "Quais ferramentas MCP você tem?" — apresenta seis ferramentas corretas e distingue suas funções.
- "O que você sabe fazer?" — explica pedidos, clientes, carteira, propostas, indicadores, tarefas e colaboração somente quando suportados por catálogo vivo e escopo do usuário.
- "Você pode excluir uma carteira?" — não promete exclusão automática; explica `prepare → commit` com proposta vinculada a alvo e confirmação governada.
- "Você consegue acessar qualquer cliente?" — não; escopo e autorização efetivos seguem backend.
- "Quais métodos e guias conhece?" — consulta a fonte `knowledge`; não inventa playbooks.
- Critérios: contrato correto, negativa honesta, AuthZ, postcondition/read-back em writes, fidelidade da documentação ao runtime.

## 5. Diretriz transversal de acrônimos
O significado precisa ter conexão explícita com a especialidade e com os processos de negócio do MCP. Revisar desvios de nomes excessivamente genéricos sem sobrescrever identidade atual antes da aprovação e migração governada.

## 6. Instruções de execução futura
Antes de qualquer código: `git status`, HEAD, fontes canônicas, owner, consumer, runtime, Abstraction Gate. Corrigir o menor diff com testes e residual search. Alterar Builder/Knowledge/OpenAPI somente quando o artefato correspondente mudar; documentar `TRANSFORMÔMETRO EXECUTION REPORT`. Não confundir **plano registrado** com **melhoria implementada**.
## Reconciliação com fontes existentes (GitHub, 2026-11-06)
- **PROVEN (código):** commercial-api/commercial_app/persona/caio_profile.py é fonte local preenchida em Python; display_name antigo e assert associado em tests/test_caio_character.py deverão ser reconciliados.
- Contrato já implementado: `shared/delpi_character_profiles` (estrutura), ficha owner-local (conteúdo), projeção no serviço do MCP (consumer). **Não criar uma segunda ficha nem registry em shared.**
- Referência cruzada: [Inventário de fontes existentes](./INVENTARIO-FONTES-EXISTENTES.md). Validação de runtime, deploy e testes permanece **TEST_NOT_RUN/TO_INVENTORY** nesta auditoria.
