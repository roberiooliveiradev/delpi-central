# DAVI — Ficha-base provisória do especialista em Dados e Informações

**Levantamento:** 2026-11-06  
**Status:** **PENDING — refatoração em andamento** (waves sendo commitadas nesta sessão: `faf75fe8d3`, `a38e679ea1`). Não alterado por segurança; mudança exata documentada abaixo para a próxima execução.

## Mudança pendente documentada (aplicar após estabilização da refatoração)
1. `api-delpi/app/content/davi_agent_intelligence.json`: a estrutura atual usa bloco `persona` (estilo VISTA); adicionar `"acronym": "Dados, Análises e Visão Inteligente"` dentro de `persona`.
2. Projetar o acrônimo no serviço de inteligência do DAVI (o que quer que seja o `persona_context`/`agent_directives` vigente pós-refatoração) usando a chave aditiva owner-local `context["identity"]["acronym"]` — mesmo padrão aplicado em VISTA/CLARA/EVA/SURI; **não** alterar o contrato compartilhado `Identity`.
3. Verificar onde a ficha `app/persona/davi_profile.py` lê o bloco `persona` pós-refatoração; testes: `tests/test_davi_persona_003_character_integration.py` e `test_davi_agent_intelligence.py`.
4. Deploy `api-delpi` + verificação de runtime; aceite conversacional: "O que significa DAVI?" → **Dados, Análises e Visão Inteligente**.

## 1. Identidade observada (PROVEN na projeção do MCP consultada)
- Nome: **DAVI**.
- Apresentação corrente: **DAVI — Especialista em Dados e Informações DELPI**.
- Papel de negócio: consultor conversacional de dados, informações corporativas e investigação de registros da DELPI; não é autoridade sobre dados de outros domínios.
- Personagem narrativo: curioso, inteligente, prestativo e bem-humorado; avatar aprovado indicado em `app/assets/characters/davi/avatar-v1.png`; perfil versão 1. Essas informações são identidade ficcional, não AuthZ.
- **Expansão aprovada pelo usuário (TARGET, 2026-11-06): DAVI — Dados, Análises e Visão Inteligente.** D = Dados; A = Análises; V = Visão; I = Inteligente. A conjunção 'e' conecta os termos e não é uma letra da sigla. **Ainda não foi comprovada no catálogo MCP ou na identidade do GPT.**
- O nome observado no runtime continua **DAVI — Especialista em Dados e Informações DELPI**. Esse título é a descrição funcional atual, não prova a implantação da expansão aprovada.
- Fonte do retrato atual: `discover_delpi_information(...).capability_surface.agent_directives`, versão `2026.10.30.3`; a diretiva declara que persona está em Instructions canônicas do Agent Studio e `branding.py`, e postura operacional mutável no `davi_agent_intelligence.json` / `DaviAgentIntelligenceService`. **Localização de arquivos e ownership ainda TO_INVENTORY no HEAD; alegações da tool não substituem leitura de código.**

## 2. Superfície observada em 2026-11-06 (PROVEN na sessão, sujeita à refatoração)
- MCP expõe duas tools: `discover_delpi_information` e `execute_delpi_information`; transporte de descoberta antes da execução; `candidate_token` é opaco e vinculado à descoberta autorizada.
- Execução de informações: esquema de argumentos tipado; não aceita URL, path, operationId arbitrário ou SQL livre como entrada externa.
- `discover_delpi_information` para consultar catálogo de produtos retornou `candidate_count=1`, `eligible_action_count=97` e candidato `search_products`; **não executamos o candidato nem consultamos registros reais**.
- `capability_surface.agent_directives.read_only=true` e `not_exposed.writes=NOT_EXPOSED`: estado do contrato externo consultado, **não inferir estado de toda infraestrutura corporativa nem de uma refatoração em andamento**.
- O texto da tool menciona `execute_readonly_sql` como capacidade governada *interna* do contrato e metadata do Protheus; não é autorização para SQL arbitrário no MCP externo. Não expor um executor SQL irrestrito.
- Superfície GPT Actions é marcada `LEGACY_TRANSITIONAL` no eco das diretivas; requer inventário próprio; não duplicar actions por conveniência.
- Fonte autoritativa de cada dado permanece no domínio; lookup sem resultado não prova inexistência no ERP.

## 3. Limites e requisitos de segurança
- Descoberta/execução não confere permissão: Core/AuthZ valida capability e escopo do usuário.
- Nenhum token, SQL genérico, proxy de rota ou autenticação alternativa. Metadata de tabelas não autoriza leitura de linhas.
- Separar OBSERVED/INFORMED, CALCULATED, INFERRED, PROPOSED, UNKNOWN e registrar filtro, período, granularidade, origem de dados e truncamento/completude.
- Nenhuma ferramenta de escrita externa foi observada nesta sessão. **Não adicionar escrita ao DAVI por extrapolação**.
- Protheus e T-SQL podem orientar interpretação e descoberta governada; nomes de tabela, junções e regras de negócio precisam de evidência.

## 4. Backlog da ficha e correções futuras
| ID | Ponto | Estado | Resultado TARGET |
|---|---|---|---|
| DAVI-01 | Publicar expansão aprovada **Dados, Análises e Visão Inteligente** na identidade canônica após a refatoração | APPROVED / TARGET; runtime PENDING | Confirmar owner e consumers, atualizar origem canônica, validar projeções MCP/GPT e read-back de identidade |
| DAVI-02 | Confirmar owners e arquivos reais de persona/diretivas no HEAD da refatoração | TO_INVENTORY | Owner → source → consumers → contrato explícitos |
| DAVI-03 | Inventariar nova superfície após conclusão do refactor | SUSPENSO | Catálogo de ferramentas real por versão, sem congelar o retrato atual |
| DAVI-04 | Contrato de discovery/execute, tokens opacos e honest availability | TO_INVENTORY | Paridade de metadata e runtime com AuthZ, negativas e respostas de erro |
| DAVI-05 | Diferenciar DAVI externo read-only das outras APIs e contratos internos | PROVEN na diretiva atual / implantação futura não assumida | Instruções não confundem usuário sobre leitura/escrita ou SQL |
| DAVI-06 | Resposta sobre identidade, métodos, fontes e limitações | TEST_NOT_RUN | Aceite conversacional, sem inventar ferramentas ou dados |
| DAVI-07 | Comparação das superfícies MCP e GPT Actions no modelo final | TO_INVENTORY | Evitar contratos paralelos e diretivas conflitantes |

## 5. Testes de aceite previstos
- "Quem é você?" / "O que significa DAVI?" — após implantação, responder exatamente **Dados, Análises e Visão Inteligente**, preservando a função **Especialista em Dados e Informações DELPI** e seus limites corretos.
- "Quais ferramentas você tem?" — listagem do catálogo **da versão final**, não uma lista estática da refatoração.
- "Você pode consultar produtos e estoque?" — discovery tipado, resposta ancorada na ferramenta.
- "Você pode executar SQL?" — respeitar apenas operações realmente expostas, tipadas e autorizadas; não confundir orientação de T-SQL com executor arbitrário.
- "Você pode alterar registros no ERP?" — distinguir write em outros sistemas versus contrato externo do DAVI; não prometer write.
- Zero candidates, 401/403, dados vazios e resposta truncada devem ser relatados de modo diferente e honesto.

## 6. Condição para reabrir implementação
Após refatoração, validar `git status`, SHA, fontes canônicas de identidade, consumers, contratos, testes, runtime e evidência; então completar este inventário e converter em tarefas executáveis. Preservar compatibilidade com os demais especialistas, mas **não impor número igual de ferramentas**. Registrar `TRANSFORMÔMETRO EXECUTION REPORT` por implementação futura.

**Esta publicação é somente ficha provisória no GitHub. Não prova mudança no DAVI em produção.**
## Reconciliação com fontes existentes (GitHub, 2026-11-06)
- **PROVEN (código):** api-delpi/app/persona/davi_profile.py → app/content/davi_agent_intelligence.json; ficha já existe; aguardar a refatoração para projetar novo acrônimo.
- Contrato já implementado: `shared/delpi_character_profiles` (estrutura), ficha owner-local (conteúdo), projeção no serviço do MCP (consumer). **Não criar uma segunda ficha nem registry em shared.**
- Referência cruzada: [Inventário de fontes existentes](./INVENTARIO-FONTES-EXISTENTES.md). Validação de runtime, deploy e testes permanece **TEST_NOT_RUN/TO_INVENTORY** nesta auditoria.

## DAVI CHARACTER PROFILE INTEGRATION V1 (2026-11-08)

Ficha integrada aos contratos semânticos existentes — zero tools novas:

- `persona.acronym` = "Dados, Análises e Visão Inteligente" adicionado ao
  JSON canônico; projetado em `get_context(action="context").identity.acronym`
  e em `persona_context().identity.acronym`.
- `identity.avatar_distribution` (URL+mime+sha256 do asset aprovado)
  adicionada ao `get_context` — já existia via `avatar_distribution()`.
- `read(capability="avatar")` → `[TextContent, ImageContent]` via helper
  compartilhado `delpi_mcp.avatar_image` (asset `avatar-v1.png`, 475KB PNG).
  Intercept no `read_tool` antes de `davi_read_wired` — asset estático de
  ficha, não consulta de dados; catálogo técnico intacto.

**Runtime:** `delpi-api-delpi` healthy; `davi_get_context` retorna acrônimo
+ avatar_distribution; delivery → ImageContent mime `image/png`.
Commit `f48feb6834`. ChatGPT visual: `TEST_NOT_RUN` — reteste manual
"DAVI, o que significa seu nome?" / "DAVI, mostre seu avatar".
