# Inventário das fichas canônicas já existentes — auditoria de reuso

**Data da consulta:** 2026-11-06  
**Repositório:** `roberiooliveiradev/delpi-central`, branch `main`  
**Escopo:** inspeção de código e documentação no GitHub; **não executa testes/deploy nem prova runtime**.

## Decisão arquitetural PROVEN

O contrato já existe em [`shared/delpi_character_profiles/README.md`](../../../shared/delpi_character_profiles/README.md): **“Shared owns the structure. MCP owns the character.”**

- `shared/delpi_character_profiles/models.py`: `Identity`, `CharacterProfile`, aparência, personalidade, comunicação, experiência, narrativa, relacionamentos e conduta; **não** declara operações, RBAC ou autorização.
- `projection.py`: `project_persona_context`, `project_public_profile`, `project_identity_summary`.
- `serialization.py`, `validation.py`, `versioning.py`: serialize/validate/version.
- `shared/delpi_mcp`: infraestrutura técnica comum do MCP; `identity.py` transporta o contexto de usuário autenticado, **não** o perfil narrativo.
- Cada domínio mantém sua ficha local, seu conteúdo e o adaptador de publicação. Não criar registry central nem cópias das fichas em `shared`.

## Localização do código — PROVEN

| MCP | Dono / fonte narrativa | Builder da ficha | Evidência adicional |
|---|---|---|---|
| TÉO | `transformometro-api/tm_app/content/teo_agent_intelligence.json` | `transformometro-api/tm_app/persona/teo_profile.py` | `tm_app/application/gpt_actions/teo_agent_intelligence_service.py`; `tm_app/content/teo_public_profile.json`; `tests/test_teo_character_profile.py` |
| VISTA | `tv-dashboard-api/tv_app/content/vista_agent_intelligence.json` | `tv-dashboard-api/tv_app/persona/vista_profile.py` | `tv_app/application/gpt_actions/vista_agent_intelligence_service.py`; `tv_app/content/vista_public_profile.json`; `tests/test_vista_persona_001_character_integration.py` |
| CLARA | `controllership-finance-api/controllership_finance_app/content/clara_agent_intelligence.json` | `controllership-finance-api/controllership_finance_app/persona/clara_profile.py` | `controllership_finance_app/application/clara/agent_intelligence_service.py`; `controllership_finance_app/content/clara_public_profile.json`; `tests/test_clara_character_profile.py` |
| CAIO | `commercial-api/commercial_app/persona/caio_profile.py` (conteúdo e builder no mesmo arquivo) | Mesmo módulo Python | `tests/test_caio_character.py`; artefato `caio_public_profile.json` não encontrado na listagem recursiva consultada; não inferir ausência de outras projeções |
| SURI | `supplies-api/app/content/suri_agent_intelligence.json` | `supplies-api/app/persona/suri_profile.py` | `app/content/suri_public_profile.json`; `tests/persona/test_suri_profile.py`; avatar `avatar-preview-v1.png` |
| EVA | `engineering-api/engineering_app/content/eva_agent_intelligence.json` | `engineering-api/engineering_app/persona/eva_profile.py` | `engineering_app/application/eva/agent_intelligence_service.py`; `engineering_app/content/eva_public_profile.json`; `tests/test_eva_character_profile.py` |
| DAVI | `api-delpi/app/content/davi_agent_intelligence.json` | `api-delpi/app/persona/davi_profile.py` | `app/application/external_capabilities/davi_agent_intelligence_service.py`; `app/content/davi_public_profile.json`; `tests/test_davi_persona_003_character_integration.py` |

**Nota:** os caminhos de arquivos auxiliares acima estão relativos à raiz de cada API quando indicados após ponto-e-vírgula.

## Acrônimos — reconciliação de fonte

| MCP | Achado no código já existente | Mudança necessária |
|---|---|---|
| TÉO | `identity.acronym = Transformação · Eficiência · Otimização` no conteúdo | Preservar; validar consumo conversacional |
| VISTA | Ficha criada e `display_name=VISTA — Painéis Operacionais DELPI`; expansão aprovada pelo usuário não identificada na fonte | Incorporar **Visão Inteligente de Sistemas, Telas e Apresentações** no owner e projetar sem duplicação |
| CLARA | **`identity.acronym = Controladoria · Leitura · Análise · Resultados · Acompanhamento` já existe no conteúdo canônico** | **Não criar acrônimo nem refazer ficha**. Verificar sua projeção no MCP e GPT; `project_persona_context` atualmente não possui campo `acronym` |
| CAIO | `display_name=CAIO — Consultor de Análise e Inteligência Operacional` no builder | Reconciliar com definição aprovada **Consultor de Análise e Inteligência de Oportunidades**; corrigir teste que fixa texto antigo |
| SURI | Ficha e JSON existem, mas expansão aprovada não localizada | Incorporar **Suprimentos Unificados, Resultados e Inteligência** no owner e testar projeção |
| EVA | `identity.acronym = Engenharia Virtual Assistida` no conteúdo | Preservar; validar exposição ao usuário |
| DAVI | Ficha e JSON existem, expansão aprovada não localizada | Após refatoração, incorporar **Dados, Análises e Visão Inteligente** na fonte do owner |

## Observações de desenho e riscos
1. O modelo compartilhado `Identity` contém `display_name`, `title`, `role`, `short_introduction`, mas **não possui campo `acronym`**. A projeção `project_persona_context` também não transporta `acronym`. O conteúdo de TÉO/CLARA/EVA já o inclui em `identity.acronym`, então conferir adaptadores/consumer antes de propor extensão do contrato. Não adicionar campo só por uniformidade.
2. `agent_intelligence.json` em seis domínios preserva a narrativa declarativa; o CAIO usa perfil Python direto, documentado como apenas fatos aprovados. **Não migrar CAIO para JSON sem necessidade comprovada.**
3. `tests/` encontrados: **TEST_NOT_RUN** nesta auditoria; o código e os asserts encontrados são evidências de implementação de testes, não de resultado atual.
4. A anterior divergência de `suri.boundaries` (Knowledge S1 somente leitura) versus catálogo com `execute` deve ser investigada como possível orientação histórica desatualizada; não refazer ficha de personagem para solucioná-la.
5. O escopo deste inventário é fonte e integração do **personagem**. Capabilities técnicas pertencem ao catálogo operacional do domínio, não à ficha narrativa.

## Gate para revisar os planos existentes
Para cada ticket do roadmap, primeiro confirmar se o recurso já existe no owner e se falha **somente** na publicação/consumer. O alvo é corrigir drift e testes, não criar abstrações paralelas.

**Status geral:** fontes e builders encontrados: PROVEN no código GitHub; existência de testes: PROVEN; execução de testes: TEST_NOT_RUN; versão efetivamente implantada: TO_INVENTORY.
