# Aceite funcional MCP — 2026-11-06 (sem DAVI)

**Tipo:** testes diretos de descoberta, projeção de identidade, Knowledge e validação de roteamento no MCP conectado ao ChatGPT.  
**Escopo:** TÉO, VISTA, CLARA, CAIO, SURI e EVA. DAVI não foi chamado.  
**Escritas:** nenhuma. **Suítes automatizadas, deployments e GPTs individuais:** não executados por esta auditoria.  
**Resultado:** 4 PASS limitados à leitura, SURI FAIL de paridade, EVA INCONCLUSIVE por erro interno.

## Matriz
| MCP | Discovery/Identidade | Conhecimento e contrato | Resultado |
|---|---|---|---|
| TÉO | `get_context(section=catalog)`: `agent_directives.identity.acronym=Transformação · Eficiência · Otimização` | `knowledge(methodology,guide_version=v1)` e `v2` responderam; v2 resolve `teo-method-playbooks-v2`; v1 permanece wire default | PASS leitura |
| VISTA | `get_context(action=catalog)` retornou `capability_surface.agent_directives.character.identity.acronym=Visão Inteligente de Sistemas, Telas e Apresentações` | `knowledge(get)` trouxe índice; `knowledge(search,KPI)` trouxe guias | PASS leitura |
| CLARA | `get_context(topic=persona)` retornou `character.identity.acronym=Controladoria · Leitura · Análise · Resultados · Acompanhamento` | `knowledge(search,fechamento mensal)` retornou conteúdo; `get_context(topic=schema,entity=pendency,action=list)` retornou schema tipado | PASS leitura |
| CAIO | `get_context(topic=catalog)` retornou novo `assistant` e `character.identity.acronym=Consultor de Análise e Inteligência de Oportunidades` | `knowledge(caio.usage)` respondeu; `read(catalog.capabilities)` rejeitou corretamente com `expected_tool=get_context` (teste negativo esperado) | PASS leitura e negativa |
| SURI | `get_context(action=catalog)` respondeu, porém `mcp.acronym` **ausente** | `knowledge(get,suri.boundaries)` ainda diz 'somente leitura' / `OWNER_REPORTED`; `knowledge(sources)` retornou **corpus_version 3** | **FAIL paridade GitHub/runtime** |
| EVA | `get_context(topic=catalog)`, `get_context()`, `knowledge(eva.usage)` | Todas falharam com 'The tool failed internally' | **INCONCLUSIVE** |

## SURI — discrepância comprovada
Na branch `main` do GitHub, arquivos inspecionados:
- `supplies-api/app/interfaces/mcp/tool_bridge.py` injeta `SURI_ACRONYM` em `mcp.acronym`;
- `supplies-api/app/content/suri_knowledge.json` contém `corpus_version: 4`, descrição atualizada de `suri.boundaries` com `execute`.

Na instância da SURI conectada nesta conversa:
- catálogo `mcp` retorna `name`, `persona`, `mission`, `catalog_version=16` mas **sem** `acronym`;
- Knowledge retorna `corpus_version=3` e descrição antiga declarando zero operações de escrita.

**Diagnóstico:** `EXECUTION_DRIFT` entre código `main` e instância consultada. **Causa: TO_INVENTORY.** Pode ser SHA antigo no deploy, réplica/instância não atualizada, roteamento/conexão para ambiente diverso ou cache/artefato. Não escolher causa sem logs, SHA e configuração.

**Próximo teste:** descobrir endpoint/ambiente/instância da conexão; verificar SHA de build e serviço em execução; inspecionar balanceamento/replicas/cache; realinhar via deploy canônico se necessário; chamar novamente `get_context(catalog)`, `knowledge(sources)`, `knowledge(get,suri.boundaries)`. Aceite: acrônimo exato, Knowledge v4, limites não contraditórios. **Não criar nova ficha nem editar novamente o JSON sem provar causa.**

## EVA — bloqueio de transporte/runtime
Chamadas `get_context` e `knowledge` retornaram falha interna, sem dados ou status autoritativo de domínio. Classificação `INCONCLUSIVE`, não `FAIL` de implementação. Investigar conexão autenticada, serviço, gateway, saúde do endpoint MCP e logs correlacionados; depois executar discovery e Knowledge e validar `character.identity.acronym=Engenharia Virtual Assistida`. Não prometer solução sem evidência.

## Limites do aceite
- PASS significa só os cenários de leitura efetivamente executados; nenhuma escrita, exclusão, consentimento, postcondition, alteração de ERP ou teste do GPT individual.
- Nenhum percentual da suíte unitária do Cursor foi reproduzido neste teste.
- DAVI excluído explicitamente da rodada.
- Não divulgar dados de usuário, tokens nem dados operacionais de respostas do catálogo em artefatos públicos.

## Status de remediação
SURI: FAIL / `EXECUTION_DRIFT` — investigação e novo aceite necessários.  
EVA: INCONCLUSIVE — recuperação de disponibilidade e novo aceite necessários.  
TÉO/VISTA/CLARA/CAIO: PASS limitado — GPT conversacional real `TEST_NOT_RUN`.
