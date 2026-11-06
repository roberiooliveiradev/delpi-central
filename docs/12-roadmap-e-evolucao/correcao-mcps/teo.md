# TÉO — Plano de correção da ficha e autoconhecimento

**Data do levantamento:** 2026-11-06  
**Status:** TO_INVENTORY / implementação PENDING. Fonte consultada: MCP TÉO, `get_context(section=catalog)` e `knowledge`.

## PROVEN: dados publicados no catálogo vivo
- Nome: **TÉO — Especialista em Transformação Digital**.
- Acrônimo oficial: **Transformação · Eficiência · Otimização**.
- Organização/ecossistema: DELPI / Minha DELPI / Transformômetro.
- Slogan: **Transforme problemas em processos melhores.**
- Identidade ficcional: Jovem Gênio da Inovação; idade narrativa 16 anos; sem inventar biografia humana.
- Diretivas do catálogo: `2026.10.29.4`; superfície `teo-capabilities-v3`.
- Tools MCP: `get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete`.
- Conhecimento: `teo-method-playbooks-v1` (13 métodos) e `teo-method-playbooks-v2` (31 métodos, incluindo Yellow/Green/Black Belt, DMAIC, MSA, FMEA, Pareto); 25 tópicos de guia de produto.
- Autoridade: MCP não concede permissões próprias; consultar catálogo vivo e AuthZ real; operações gravadas exigem postcondition/read-back.

## Problemas e evidência
| ID | Achado | Evidência/classificação | Correção sugerida |
|---|---|---|---|
| TEO-01 | Alias `guide_version=v2` anunciado na descrição da tool, mas rejeitado com erro 400; identificador completo `teo-method-playbooks-v2` funciona | **FAIL reproduzido** | Revisar contrato; aceitar aliases ou corrigir metadata/documentação e cobrir com regressão |
| TEO-02 | V2 recomendada, mas `wire_default_version` é V1 | **PROVEN; intenção a decidir** | Inventariar consumers e política de versionamento; não trocar default silenciosamente |
| TEO-03 | `get_context(overview)` prioriza usuário/workspace, enquanto identidade fica em `catalog.agent_directives.identity` | **PROVEN; UX TARGET** | Fornecer leitura de identidade acessível sem duplicar autoridade |
| TEO-04 | Docs anteriores afirmam `flowchart_v1` canônico; catálogo/guia vivo dizem BPMN nativo para novos diagramas, flowchart legado read-only/migração | **divergência documental observada** | Reconciliar com implementação, owner e decisão arquitetural; atualizar documentos corretos |
| TEO-05 | Localização da ficha compartilhada/autoria no GitHub | **TO_INVENTORY** | Localizar owner e doc canônico, publicar somente após revisão |
| TEO-06 | Respostas no GPT sobre identidade, ferramentas, limites e métodos não testadas diretamente | **TEST_NOT_RUN** | Matriz de aceitação conversacional e negativa em ambiente do agente |

## Testes de aceite (TARGET)
- "Quem é você?" / "O que significa TÉO?" / "Qual sua missão?": respostas estáveis, curtas e alinhadas ao owner.
- "Que ferramentas tem? O que consegue alterar?": catálogo vivo, operação/limites reais, sem prometer AuthZ.
- "Você conhece Yellow Belt e Green Belt?" / "Quando usar DMAIC?": selecionar versão/metodologia apropriadas; belts ≠ certificação.
- `knowledge`: alias/identificadores documentados e default sem regressão.
- Diagramas: documentação, contratos e comportamento sem conflito.
- Não alegar implantação nem autorização com base em conversa.

## Gates para implementação
Inventariar repositório, arquivos responsáveis, consumidores e SHA antes do diff; usar menor alteração; testes, residual search e relatório `TRANSFORMÔMETRO EXECUTION REPORT`. Não editar GPT Builder/OpenAPI/Knowledge por reflexo: apenas quando seu artefato realmente mudou.
