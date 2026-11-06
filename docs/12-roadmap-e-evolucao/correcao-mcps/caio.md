# CAIO — Plano de correção da ficha técnica e autoconhecimento

**Inventário:** 2026-11-06  
**Estado:** levantamento documentado; **sem alteração de runtime, Instructions ou API**.
**Fonte observada:** `mcp__CAIO___Especialista_Comercial_DELPI__get_context`, `knowledge` e validação de roteamento `read`.

## 1. Identidade comprovada pelo catálogo MCP (PROVEN)
- **CAIO = Consultor de Análise e Inteligência Operacional.** Significado já está em `assistant` e `agent_directives.character.identity.display_name`.
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
| CAIO-01 | Acrônimo está publicado e é recuperável no catálogo, porém resposta final no GPT não foi avaliada | Identidade presente em `get_context` | Testar "Quem é você?" e "O que significa CAIO?" sem prompt auxiliar; preservar fonte única |
| CAIO-02 | Descoberta de identidade compartilha payload de catálogo operacional potencialmente amplo | `get_context` lista múltiplas entidades e ações | Avaliar projeção pública compacta `self/identity` pelo mesmo owner, sem nova autoridade |
| CAIO-03 | Catálogo `topic=catalog` apresenta projeção compacta (4 ações observadas) versus conjunto amplo no tópico padrão | Comportamento observado, não defeito confirmado | Documentar projeções e verificar se consumidores sabem quando pedir inventário completo |
| CAIO-04 | Conjunto de ferramentas e capabilities precisa ser explicado em linguagem de negócio | Guide `caio.usage` existe | Resposta curta + detalhamento on demand derivado do catálogo vivo, sem overclaim |
| CAIO-05 | Paridade de catálogo, implementação e runtime de operações governadas não foi testada neste levantamento | Sem mutações executadas | Inventory de owner/consumer/contrato; regressões de erros, scopes, consentimento e read-back |
| CAIO-06 | Ficha institucional compartilhada e vínculo com caracterização do personagem não identificados | Fonte MCP encontrada; arquivo canônico não inventariado | Localizar arquivo owner, não duplicar identidade entre GitHub, MCP e GPT |
| CAIO-07 | Apresentação conversacional e limitações precisam de aceite | GPT isolado não testado | Matriz de QA positiva/negativa em GPT real e ambientes autorizados |

## 4. Matriz de aceite (TARGET)
- "Quem é você?" — retorna nome completo, área e missão, sem biografia inventada.
- "O que significa CAIO?" — responde **Consultor de Análise e Inteligência Operacional**.
- "Quais ferramentas MCP você tem?" — apresenta seis ferramentas corretas e distingue suas funções.
- "O que você sabe fazer?" — explica pedidos, clientes, carteira, propostas, indicadores, tarefas e colaboração somente quando suportados por catálogo vivo e escopo do usuário.
- "Você pode excluir uma carteira?" — não promete exclusão automática; explica `prepare → commit` com proposta vinculada a alvo e confirmação governada.
- "Você consegue acessar qualquer cliente?" — não; escopo e autorização efetivos seguem backend.
- "Quais métodos e guias conhece?" — consulta a fonte `knowledge`; não inventa playbooks.
- Critérios: contrato correto, negativa honesta, AuthZ, postcondition/read-back em writes, fidelidade da documentação ao runtime.

## 5. Instruções de execução futura
Antes de qualquer código: `git status`, HEAD, fontes canônicas, owner, consumer, runtime, Abstraction Gate. Corrigir o menor diff com testes e residual search. Alterar Builder/Knowledge/OpenAPI somente quando o artefato correspondente mudar; documentar `TRANSFORMÔMETRO EXECUTION REPORT`. Não confundir **plano registrado** com **melhoria implementada**.
