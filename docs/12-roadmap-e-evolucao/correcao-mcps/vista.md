# VISTA — Plano de correção da ficha e autoconhecimento

**Data do levantamento:** 2026-11-06  
**Status:** EXECUTADO 2026-11-06.

## Resultado da execução (2026-11-06)
| ID | Resultado | Evidência |
|---|---|---|
| VISTA-01 | **CORRIGIDO** — `persona.acronym = "Visão Inteligente de Sistemas, Telas e Apresentações"` publicado na fonte canônica e projetado em `persona_context().identity.acronym` → `agent_directives.character.identity.acronym` (chave aditiva owner-local, mesmo padrão de `avatar_distribution`; contrato compartilhado não alterado) | `vista_agent_intelligence.json` + `vista_agent_intelligence_service.py`; regressão `test_persona_context_projects_approved_acronym` |
| Acrônimo antigo | **CORRIGIDO** — expansão anterior `Visualização · Inteligência · Síntese · Telas · Apresentação` substituída pela aprovada em `specialist-instructions.md` (tabela + blocos MCP/Actions) e `gpt-builder-go-live.md`; residual search limpo | sed + grep residual |
| VISTA-02 | **MANTIDO** — identidade em `agent_directives.character` (projeção compacta da ficha canônica); acrônimo agora alcançável ali sem duplicar autoridade | service |
| VISTA-03 | **SEM MUDANÇA** — escopo do guia de produto confirmado como produto, não identidade; rota correta de leitura da identidade = `get_context(action=catalog) → agent_directives.character` | inventário |
| VISTA-04 | **CORRIGIDO (drift real)** — `semantic_delete` aceitava 8 entidades (`block,section,slide,data_model,playlist_share,edit_invite,playlist,slide_template`) mas tool/enum OpenAPI anunciavam só 3; descrição MCP e enum OpenAPI alinhados ao conjunto aprovado + artefato `openapi-gpt-actions.json` regerado | `server.py`, `openapi_builder.py`, artefato regerado |
| Defeito pré-existente | **CORRIGIDO** — `upsert_block.block.kpiOptions.colorRules` declarava `{"type":"array"}` sem `items`, quebrando `build_gpt_actions_openapi` no HEAD (sync e 7 testes de facade falhavam antes do diff) | `presentation_ops_content.json` |
| VISTA-05/06 | **TEST_NOT_RUN** conversacional GPT real; ficha owner localizada: `tv_app/persona/vista_profile.py` + JSON canônico | inventário |
| Falhas residuais pré-existentes | **NÃO RELACIONADAS** — 9 testes falham igualmente no HEAD limpo (`test_vista_execute_delete` 5, `test_gpt_actions_catalog_budget` 2, `test_vista_display_format_bridge` 1, `test_generate_tv_data_routes_from_openapi` 1) | stash + rerun |

**Arquivos alterados:** `tv_app/content/vista_agent_intelligence.json`, `tv_app/application/gpt_actions/vista_agent_intelligence_service.py`, `tv_app/interface/mcp/server.py`, `tv_app/application/gpt_actions/openapi_builder.py`, `tv_app/content/presentation_ops_content.json`, `docs/gpt-actions/openapi-gpt-actions.json` (regerado), `docs/gpt-actions/specialist-instructions.md`, `docs/gpt-actions/gpt-builder-go-live.md`, `tests/test_vista_builder_instructions_budget.py`, `tests/test_vista_agent_intelligence.py`, este arquivo.

**Ação manual GPT Builder:** recolar o bloco Instructions atualizado (`specialist-instructions.md`, variante do conector em uso) e o campo **Acrônimo** do Builder.

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
