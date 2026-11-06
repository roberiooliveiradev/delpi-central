# TÉO — Plano de correção da ficha e autoconhecimento

**Data do levantamento:** 2026-11-06  
**Status:** EXECUTADO 2026-11-06 (commit local; deploy pendente de acesso ao srv-api).

## Resultado da execução (2026-11-06)
| ID | Resultado | Evidência |
|---|---|---|
| Acrônimo | **ALREADY_CORRECT** — `Transformação · Eficiência · Otimização` publicado em `tm_app/content/teo_agent_intelligence.json → identity.acronym`, projetado via `capability_surface.agent_directives.identity` | leitura da fonte + `teo_agent_intelligence_service.agent_directives` |
| TEO-01 | **CORRIGIDO** — `resolve_guide_version` agora aceita os aliases anunciados `v1`/`v2` (`GUIDE_VERSION_ALIASES`); ids canônicos continuam o contrato | `guide_v2.py`; regressão em `test_teo_methodology_v2.py` (`test_resolve_version_advertised_aliases`, `test_alias_v2_returns_v2_guide`) |
| TEO-02 | **INTENCIONAL — sem mudança** — `wire_default_version=v1` documentado: "Post-acceptance cutover: recommendation is V2; wire default stays V1" | `test_teo_methodology_v2.py` (asserção existente) |
| TEO-03 | **CORRIGIDO (descoberta leve)** — `discovery_hint` do `get_context` overview agora aponta `catalog.agent_directives (identity/character)` como morada da identidade; sem duplicar autoridade | `tool_bridge_v3.py` |
| TEO-04 | **CORRIGIDO** — ADR `adr-diagramas-processo.md` recebeu nota de atualização datada: convergência BPMN nativo, `flowchart_v1` legado read-only/fonte de migração; histórico preservado | ADR → `teo-capability-matrix.md` |
| TEO-05 | **PROVEN** — ficha em `tm_app/persona/teo_profile.py` + JSON canônico; nenhuma segunda fonte criada | inventário |
| TEO-06 | **TEST_NOT_RUN** (conversacional GPT real) — testes unitários/de superfície executados: **186 pass, 0 fail** no escopo TÉO; falha pré-existente não relacionada: `test_gpt_validation_error_context.py::test_create_shared_resource_validation_exposes_fields_to_gpt` (falha também no HEAD limpo — residual fora do escopo) | pytest |

**Arquivos alterados:** `tm_app/application/methodology/guide_v2.py`, `tm_app/interface/mcp/tool_bridge_v3.py`, `tests/test_teo_methodology_v2.py`, `docs/architecture/adr-diagramas-processo.md`, este arquivo.

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
## Reconciliação com fontes existentes (GitHub, 2026-11-06)
- **PROVEN (código):** transformometro-api/tm_app/persona/teo_profile.py → tm_app/content/teo_agent_intelligence.json; acrônimo já presente na fonte.
- Contrato já implementado: `shared/delpi_character_profiles` (estrutura), ficha owner-local (conteúdo), projeção no serviço do MCP (consumer). **Não criar uma segunda ficha nem registry em shared.**
- Referência cruzada: [Inventário de fontes existentes](./INVENTARIO-FONTES-EXISTENTES.md). Validação de runtime, deploy e testes permanece **TEST_NOT_RUN/TO_INVENTORY** nesta auditoria.
