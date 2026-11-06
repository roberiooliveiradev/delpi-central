# VISTA — Plano de correção da ficha e autoconhecimento

**Data do levantamento:** 2026-11-06  
**Status:** acrônimo **APROVADO PELO USUÁRIO**, publicação no MCP **PENDING**. Fonte: MCP VISTA `get_context(context|catalog)`, `knowledge`.

## Identidade
- Nome: VISTA — Painéis Operacionais DELPI.
- **Acrônimo definido pelo usuário nesta revisão:** **Visão Inteligente de Sistemas, Telas e Apresentações**. **TARGET para catálogo/documento canônico; não afirmar já implantado.**
- Atuação observada: especialista em painéis digitais, dashboards, indicadores, apresentações digitais e visualização de dados.
- Perfil narrativo oficial: `agent_directives.character`, profile_version 3; avatar `tv_app/content/characters/vista/avatar-v2.jpg`; diretivas `2026.10.16.4`.
- Ferramentas MCP: `get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete`; 40 effectiveCapabilities em contexto (14 read, 3 analyze, 2 knowledge, 15 execute, 6 delete); 36 tipos de operação no catálogo; 12 tópicos de guia de produto.

## Problemas e correções
| ID | Achado | Classificação | Target |
|---|---|---|---|
| VISTA-01 | Catálogo não expõe significado formal do acrônimo | PROVEN em consultas realizadas | Publicar expansão aprovada na fonte canônica de identidade e projeção MCP |
| VISTA-02 | Identidade detalhada aninhada em `catalog.capability_surface.agent_directives.character`, não em `context.assistant` | PROVEN | Descoberta leve e inequívoca |
| VISTA-03 | `knowledge(action=search, query=identidade/acrônimo)` retornou zero; `get(topic=identity)` retornou `RESOURCE_NOT_FOUND` | PROVEN; escopo do guia é produto, não identidade | Definir rota correta de leitura da identidade, **sem necessariamente ampliar** o guia de produto |
| VISTA-04 | Descrição de `delete` enumera block/section/slide, enquanto catálogo também lista data_model/playlist_share/edit_invite | TO_INVENTORY, drift potencial | Conferir semântica real e atualizar contrato ou metadata conforme owner |
| VISTA-05 | Sem teste isolado de apresentação no GPT | TEST_NOT_RUN | Perguntas de identidade/limites/tools/capabilities e negativas |
| VISTA-06 | Fonte compartilhada e caminho de publicação ainda não reconciliados com identidade owner | TO_INVENTORY | Localizar owner e sincronizar sem duplicação |

## Aceite TARGET
Perguntas "Quem é você?", "O que significa VISTA?", "O que sabe fazer?", "Que tools pode usar?", "O que não pode fazer?" devem produzir resposta alinhada à identidade oficial e ao catálogo de operações autorizadas. O nome deve ser exposto exatamente como **Visão Inteligente de Sistemas, Telas e Apresentações**. Catalogar limites de dados/preview/design: representação esquemática ≠ verificação visual de pixels. Nunca tratar o catálogo como autorização ou dizer que um write foi salvo sem read-back.

## Implementação futura
Confirmar owner, source e consumers (MCP, GPT, UI), smallest diff, testes e relatório de execução; alterar documentação compartilhada + publicação correta no catálogo; GPT Builder só se houver mudança em Instructions/Knowledge/OpenAPI correspondente.
## Reconciliação com fontes existentes (GitHub, 2026-11-06)
- **PROVEN (código):** tv-dashboard-api/tv_app/persona/vista_profile.py → tv_app/content/vista_agent_intelligence.json; ficha já existe; só a nova expansão aprovada carece de publicação.
- Contrato já implementado: `shared/delpi_character_profiles` (estrutura), ficha owner-local (conteúdo), projeção no serviço do MCP (consumer). **Não criar uma segunda ficha nem registry em shared.**
- Referência cruzada: [Inventário de fontes existentes](./INVENTARIO-FONTES-EXISTENTES.md). Validação de runtime, deploy e testes permanece **TEST_NOT_RUN/TO_INVENTORY** nesta auditoria.
