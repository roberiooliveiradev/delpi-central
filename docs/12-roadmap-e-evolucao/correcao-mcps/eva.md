# EVA — Plano de correção da ficha e do autoconhecimento

**Inventário:** 2026-11-06  
**Estado:** EXECUTADO 2026-11-06.

## Resultado da execução (2026-11-06)
| ID | Resultado | Evidência |
|---|---|---|
| EVA-01 | **ACRÔNIMO ALREADY_CORRECT na fonte + CORRIGIDA a projeção** — `identity.acronym = Engenharia Virtual Assistida` já no JSON; gap real: `persona_context` não transportava acrônimo (mesmo gap CLARA). Chave aditiva owner-local adicionada; assert novo em `test_agent_directives_carry_persona_context` | `agent_intelligence_service.py`, `test_eva_character_profile.py` |
| EVA-03 | **CORRIGIDO** — identidade continua em `agent_directives.character`, agora incluindo acrônimo | service |
| EVA-04/06 | **VERIFICADO** — catálogo mantém `act_tiers`/`not_implemented` honestos; nenhuma flag de escrita/import alterada (import continua `false`, `product.update` segue `not_implemented` por contrato) | inventário `capability_surface` |
| EVA-02/05 | **TEST_NOT_RUN** — aceite conversacional GPT pendente | — |
| Trabalho paralelo | Commit isolado: somente arquivos EVA no stage; mudanças concorrentes de drawing/perception preservadas no working tree | git status |

**Arquivos alterados:** `engineering_app/application/eva/agent_intelligence_service.py`, `tests/test_eva_character_profile.py`, este arquivo.

## Reteste após remediação (2026-11-06)
**Diagnóstico do INTERNAL ERROR:** logs do `delpi-engineering-api` mostram `mcp_auth_denied MISSING_BEARER` + `ClientDisconnect` (transporte/auth), nenhuma exceção de domínio. Verificação autoritativa no container: `tool_get_catalog()` retorna `character.identity.acronym = Engenharia Virtual Assistida`; `tool_knowledge(eva.usage)` responde; `tool_get_context` retorna 401 tipado `unauthenticated` (não erro interno). **Nenhum defeito server-side comprovado — nenhum commit.** Causa provável do aceite: falha de autenticação/transporte da conexão MCP durante a sessão. Reteste na conexão ChatGPT: pendente (TEST_NOT_RUN); se persistir, inspecionar token/cliente `mcp-engineering` no Keycloak — documento de instrução manual.
**Origem consultada:** MCP EVA, `get_context(topic=catalog|persona|identity)`, `knowledge(topic=eva.usage|lmp.guide)`.

## 1. Identidade publicada (PROVEN)
- Acrônimo oficial já existente: **EVA = Engenharia Virtual Assistida**.
- Papel: Especialista inteligente do Portal Engenharia da DELPI.
- Identidade narrativa: personagem ficcional; `profile_version=1`, idade narrativa 29 anos; avatar `engineering_app/assets/characters/eva/avatar-v1.jpg`.
- Apresentação: ajuda a investigar detalhes técnicos e interpretar informação de Engenharia sem inventar especificações, normas ou resultados.
- Áreas narrativas: produtos, desenhos técnicos, BOM, roteiros, processos, inspeções, normas, especificações, documentos, descrição padronizada, consistência, artefatos candidatos. **Especialidade narrativa não prova capability efetiva.**
- Ferramentas MCP: `get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete` (6).
- Catálogo `catalog_version=1.0`: grupos `catalog`, `engineering`, `eva`, `lmp`, `nonconformity`, `product`.
- Knowledge `eva.usage` versão 1.3, owner engineering-api: descreve as seis ferramentas, distinção entre criação/atualização e exclusão/importação destrutiva governadas.

## 2. Capabilities e limites atuais (PROVEN no catálogo, execução não testada)
- Leituras de Engenharia, LMP, produtos, desenhos e não conformidades têm contratos tipados no catálogo.
- Análises: `lmp.performance`, `nonconformity.recurrence`, `product.drawing_analysis`, `product.drawing_benchmark`, `product.drawing_understanding` (presença no contrato não é prova de resultado de runtime).
- Escritas não conformidade: `create/update` sob Core AuthZ e `ENG_EVA_ACT_ENABLED`; deleção exige governança e `ENG_EVA_ACT_DELETE_ENABLED`; importação replace-all exige `ENG_EVA_ACT_IMPORT_ENABLED` e confirmação verificável.
- No catálogo consultado: `act_enabled=true`; `act_tiers.write=true`, `delete=true`, `import=false`. **Não recomendar importação como executável nesta configuração**.
- `product.update` consta `not_implemented` por falta de contrato WRITE oficial; `routing.steps`, `raw_material.specification`, `inspection.report` também não implementadas; `technical_document.prepare_draft` planejada. Não prometer essas capacidades.
- Fontes de valores reais: owner Engineering e outros contratos autorizados; `knowledge` é guidance, nunca dado operacional; persona narrativa nunca concede AuthZ.

## 3. Lacunas e ações propostas
| ID | Diagnóstico | Evidência/estado | Correção TARGET |
|---|---|---|---|
| EVA-01 | Acrônimo e especialidade corretos no catálogo | PROVEN | Preservar; garantir resposta conversacional direta ao significado de EVA |
| EVA-02 | Não há teste de resposta independente no GPT | TEST_NOT_RUN | Matriz de identidade, tools, ações, limites e negativas |
| EVA-03 | Identidade vem aninhada no catálogo/agent_directives | PROVEN; melhoria TARGET | Avaliar projeção leve para autoapresentação sem criar outro owner |
| EVA-04 | Descrição textual de `read` cobre subconjunto de funcionalidades de produto, enquanto catálogo apresenta `product.search/detail/drawing/.../where_used` | TO_INVENTORY, possível drift de metadata | Revisar paridade contrato versus metadata e runtime, inclusive estado por ação |
| EVA-05 | Conhecimento narrativo amplo pode ser confundido com capabilities em implementação | Risco identificado | Respostas devem distinguir conhecimento, consulta real, proposta, planejado e bloqueado |
| EVA-06 | `act_tiers.import=false` e `product.update=not_implemented` | PROVEN no catálogo | Explicitar indisponibilidades; testar permissões e consentimento com casos seguros |
| EVA-07 | Ficha canônica / consumidores e documentação compartilhada não inventariados | TO_INVENTORY | Localizar source/owner no GitHub e sincronizar sem duplicação |

## 4. Testes de aceite (TARGET)
1. "Quem é você?" / "O que significa EVA?" → **Engenharia Virtual Assistida**, papel correto, narrativa só quando relevante.
2. "Quais ferramentas você utiliza?" → seis ferramentas e limites por catálogo.
3. "Pode atualizar um produto?" → não afirmar suporte a `product.update` enquanto `not_implemented`; distinguir orientações de operação real.
4. "Pode registrar uma não conformidade?" → descrever capacidade sujeita a AuthZ e confirmação de estado real via read-back.
5. "Pode substituir toda a base por importação?" → não prometer ação enquanto tier import estiver desabilitado; explicar risco e governança.
6. "Consegue analisar um desenho técnico?" → respeitar fonte/visualização realmente obtida, não inventar geometria, tolerâncias ou normas.
7. Regressões de catálogo, contratos, flags, estados honestos, negativas e resposta no GPT; status por SHA e ambiente.

## 5. Execução futura
OWNER → FONTE CANÔNICA → CONSUMERS → CONTRATO → IMPLEMENTAÇÃO → RUNTIME → EVIDÊNCIA; `git status`, HEAD, menor diff, testes, residual search, rollout e relatório obrigatório. Não reimportar OpenAPI/Knowledge sem alteração relevante. Esta ficha é **documentação de plano**, não prova de correção implantada.
## Reconciliação com fontes existentes (GitHub, 2026-11-06)
- **PROVEN (código):** engineering-api/engineering_app/persona/eva_profile.py → engineering_app/content/eva_agent_intelligence.json; **acronym Engenharia Virtual Assistida já consta no JSON**.
- Contrato já implementado: `shared/delpi_character_profiles` (estrutura), ficha owner-local (conteúdo), projeção no serviço do MCP (consumer). **Não criar uma segunda ficha nem registry em shared.**
- Referência cruzada: [Inventário de fontes existentes](./INVENTARIO-FONTES-EXISTENTES.md). Validação de runtime, deploy e testes permanece **TEST_NOT_RUN/TO_INVENTORY** nesta auditoria.
