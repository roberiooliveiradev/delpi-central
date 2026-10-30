# CAIO 2.0 — Trilha de execução autônoma: paridade funcional + conhecimento comercial

**Status:** EXECUTED — E0→E9 concluídos; matriz em `CAIO_PARITY_MATRIX.md`; deploy `361d09da9` em produção.
**Base observada ao planejar:** `main = 701c15dd9f9dd2db9f56d816fb1451910085fd0f` (revalidar no início e por etapa).
**Execução:** baseline `0e69bcdb52` → commits `062ab28a61` + `361d09da96` → produção `361d09da9` (srv-api, `delpi-commercial-api` healthy).
**Owner de domínio:** `commercial-api`. **Consumer operacional:** CAIO MCP em `commercial-api/commercial_app/interface/mcp`; Portal em `plugins/commercial`.
**Propósito:** Devin inventariar todas as funcionalidades elegíveis do Portal Comercial, implementar paridade semântica do CAIO, dotá-lo de conhecimento confiável de processos e domínio, testar, commitar, dar push e implantar em produção, com verificação real. **Executar autonomamente as escolhas técnicas rotineiras; não inventar autoridade nem romper regras de segurança.**

## 0. Definição exata de sucesso

**Paridade = operações de negócio elegíveis do Portal cuja equivalência via CAIO foi demonstrada** para o mesmo usuário, escopo, dados, filtros, erros, efeitos e permissões. Não confundir tela com operação; não é quantidade de rotas ou tools. Tarefas de UI puramente visuais, arquivos binários ou experiências de tempo real podem demandar representação semântica adequada, handoff legítimo ao Portal, ou classificação `NOT_SEMANTICALLY_ELIGIBLE` fundamentada. **Nunca chamar de 100% se houver operações elegíveis sem implementação/teste.**

Manter as **seis tools públicas**: `get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete`. Expandir operações enumeradas e tipadas no registry existente, não criar tool por endpoint, generic HTTP, SQL genérico, introspecção arbitrária, novo RBAC ou novo serviço sem Abstraction Gate.

**Conhecimento ≠ payload de API:** CAIO deve entender conceitos, processos antes/depois, regras de negócio, fontes, responsabilidades, vocabulário, status, exceções, métricas e navegação do Portal com documentação canônica e citações/proveniência. Não inferir regras de negócio apenas por nomes de componentes/colunas. Conhecimento deve ser versionado owner-local e distinto de dados operacionais de usuário.

## 1. Sources of truth e inventário

Antes de qualquer diff: `git fetch origin`, `git rev-parse HEAD`, `git rev-parse origin/main`, `git branch --show-current`, `git status --short`, `git worktree list`; identificar concorrência, não trocar/criar branch/worktree sem autorização específica, não sobrescrever arquivos alheios. Ler `AGENTS.md`, `.cursor/rules/development-standards-index.mdc`, `evidence-driven-execution.mdc`, `plan-construction.mdc`, `plan-execution.mdc`, `openai-plugin-mcp-integration.mdc`, `platform-architecture-boundaries.mdc`, `platform-security-identity-authorization.mdc`, `platform-quality-testing.mdc`, `platform-delivery-runtime-operations.mdc`, `test-and-commit.mdc`, regras relevantes de API/observability/knowledge.

Inspecionar fontes **com consumidores**:
- Frontend `plugins/commercial/src/features`: `administration`, `analytics`, `customers`, `help`, `home`, `interaction-rooms`, `my-day`, `open-orders`, `overview`, `proposals`, `seller-portfolios`, `users`; `src/api`, rotas, navegação, hooks, schemas, testes.
- Backend `commercial-api/commercial_app/interface/http/routes`: `administration_routes`, `analytics_routes`, `attachment_routes`, `customer_routes`, `group_routes`, `home_favorites_routes`, `integration_jobs_routes`, `interaction_room_routes`, `open_orders_routes`, `production_bff_routes`, `proposal_documents_routes`, `realtime_routes`, `seller_portfolio_routes`, `settings_routes`, `user_profile_routes`, `worklist_routes`, além das demais rotas atuais.
- `commercial-api/commercial_app/application/{use_cases,services,security}`, composição, testes, docs, API specs, integrações autorizadas (ex. api-delpi/TOTVS), permissões e observabilidade; `commercial-api/commercial_app/application/caio/{semantic_registry,caio_agent_service}.py`, `interface/mcp`, `content`, `persona`.
- Docs canônicos `docs/initiatives/caio-mcp/{README.md,IMPLEMENTATION_PLAN.md,KEYCLOAK_CHATGPT_HANDOFF.md}` e documentação comercial operacional existente. Se documento em PR antigo, não integrar branch implicitamente; identificar versão vigente.
- Quando funcionalidade envolver outro owner (produção, financeiro, suprimentos, dados): conservar integração oficial do commercial-api; não acessar tabelas/rotas de terceiros por bypass.

**Artefato obrigatório de E1:** `docs/initiatives/caio-mcp/CAIO_PARITY_MATRIX.md`, tabela por **operação**, com campos:
`feature_id, processo, usuário/ator, before/after, UI surface, API operationId/route, application use case, data source/owner, authorization, scope, input/output schema, risk, side effects, audit, semantic tool, entity/action, current status, tests, evidence, blockers`.
Cada linha classificada `PROVEN_CURRENT`, `PARTIAL`, `TO_IMPLEMENT`, `NOT_SEMANTICALLY_ELIGIBLE`, `BLOCKED_EXTERNAL` ou `TO_INVENTORY`. Busca de texto é descoberta, não prova de ausência. Inventariar trabalho manual/handoffs quando documentados, marcar como hipótese quando não comprovados.

## 2. Metodologia de trabalho autônomo

**E0 — Baseline:** realizar reancoragem, capturar baseline de testes existentes, registrar dependências e regras; reportar apenas bloqueio real. Não usar perguntas para decisões que o código/contrato responde.

**E1 — Matriz completa:** varrer frontend, APIs, consumidores e testes até cobrir todas as funcionalidades; decompor em operações significativas e separar READ, ANALYZE, KNOWLEDGE, CREATE/UPDATE, DELETE, multietapa e real-time; verificar permissões reais por ator/carteira/filial; calcular denominador elegível. Nenhuma meta numérica inventada.

**E2 — Registry & contratos:** preservar seis tools; especificar operação `(entity, action)` enum allowlisted, schema de request/resposta, filtros, paginação, versão, proveniência, limites, class de risco, política de execução, mapeamento use case, erros, disponibilidade. Preferir adapter owner-local e reuso de serviços e validadores reais. Nenhuma operação `proven` antes de testes.

**E3 — Leituras e análises:** implementar toda operação elegível de consulta/insight que já possui contrato seguro; reutilizar cálculo e regras do owner; escopo sempre resolvido no backend; suportar zero resultado, parcial, timeout, downstream unavailable, timezone/datas, ordenação/paginação. Provar equivalência UI↔MCP com mesmos filtros/usuário.

**E4 — Escritas governadas:** ativar CREATE/UPDATE e outras operações **somente** se houver contrato canônico, autorização por recurso, validação, auditoria, controle de concorrência/idempotência e read-back. Executar diretamente quando política permite, sem confirmação conversacional ritual. Operações materiais que exigem consentimento/aprovação por norma mantêm gate formal; confirmação do chat nunca substitui backend. Multietapa: orquestrar na mesma solicitação, respeitar dependências, falha parcial, compensação suportada (não alegar transação distribuída). `delete`: PREPARE imutável e limitado/expirável, mostrar alvo e efeitos; única confirmação explícita referente à proposta selada; COMMIT com autenticação/autorização revalidada e read-back. Se risco ou contrato não permitem: `BLOCKED_EXTERNAL`, sem bypass.

**E5 — Conhecimento comercial:** inventariar documentos e fontes oficiais de processos, regras, perfil de cliente, carteira, ciclo de pedido, propostas, ROL/indicadores, prazos e entregas, atividades/Meu Dia, interações, administração e integrações. Para cada tema registrar `owner, source_uri/path, version/commit/date, scope, canonicality, access_classification, factual claims, uncertainties, related feature_ids`. Reutilizar mecanismo de conhecimento existente de CAIO; conteúdo dentro do owner, nada de corpus duplicado sem justificativa. Projetar `knowledge` com seleção por tema/processo, síntese em linguagem de negócio, fontes e limites, distinção entre explicação geral e consulta de dados pessoais. Não copiar documentos confidenciais para projeção pública; autorização de leitura de conteúdo deve ser preservada. Testar perguntas reais: como fazer, por quê, antes/depois, quem decide, de onde vem dado, exceções, próximos passos, como medir. Respostas sem fonte confiável: admitir não comprovado. Não inventar fluxos manuais nem ensinar workaround de autorização. Medir cobertura de conhecimento por tema e qualidade de evidência.

**E6 — Comportamento conversacional:** preservar persona CAIO aprovada; responder diretamente; não pedir confirmação para READ/ANALYZE nem escrita direta autorizada; apenas exclusão ou política oficial; contextualizar capacidade e bloqueios. Testes multi-intent/multi-turn, seleção correta tool/operation, recuperação de erro sem repetir write, separação de hipótese/fato e não confundir acesso administrativo com carteira irrestrita.

**E7 — Segurança e testes:** tabela completa requisito→testes. Positivos, negativos, sibling, mismatch de identidade, 401/403, escopo multiusuário, filial/carteira, request inválido, IDOR, concorrência, idempotência, partial failure, deduplicação, no-secret logging, HTTP/MCP discovery, 6 tools estáveis, backward compatibility, conhecimento autorizado. Testes de regressão da `commercial-api` e dos consumers. Comparações de paridade para amostra representativa por operação; nenhuma passagem baseada só em mock sem prova de wiring. Investigar 3 falhas históricas, não descartar automaticamente como preexistentes.

**E8 — Publicação incremental disciplinada:** seguir `AGENTS.md`: commit/push em `main` apenas se branch autorizada e working tree verificada, fast-forward sem force, preservar concorrentes. Executar `git pull --ff-only` e deploy canônico `./infra/scripts/up-prod-sequential.sh --build <serviços afetados>` no `srv-api`, com evidência de ambiente, deployed SHA, health, checks de tráfego, MCP and avatar. Implantar **incrementos completos** após seus gates, não esperar 100% para encontrar erro e não ampliar escopo para serviços externos sem necessidade. Feature gates de writes sensíveis desligados até autorização aplicável. Se deploy falhar, executar recuperação canônica permitida ou STOP-THE-LINE; não marcar COMPLETE.

**E9 — Validar resultado total e documentação:** atualizar matriz com executado e provas, catálogo de operações/knowledge, guia user-facing, changelog e status de implantação; demonstrar proporção de paridade, segregando `NOT_SEMANTICALLY_ELIGIBLE` e `BLOCKED_EXTERNAL`; não declarar 100% se houver cobertura elegível faltante. Executar verificação host ChatGPT quando acesso for possível; senão `TEST_NOT_RUN`, nunca simular. Manter `KEYCLOAK_CHATGPT_HANDOFF.md` coerente sem recadastrar client existente.

## 3. Gates obrigatórios de cada etapa

`READY_TO_EXECUTE`: HEAD/branch/working tree, owner e contrato atuais, requisitos, limites e testes de base conhecidos.

`READY_TO_COMMIT`: menor diff correto, autorização preservada, contrato versionado, testes positivos/negativos, regressão, residual search, documentação factual ajustada.

`COMPLETE_GATE`: commit identificado, push confirmado, deployed SHA, health/discovery, resultado esperado demonstrado por evidência; sem gate não avançar dependências.

Quando aparecer premissa inválida: `EXECUTION_DRIFT` com `PLAN_SAID / CURRENT_EVIDENCE / INVALIDATED_DECISION / AFFECTED_STEPS / SAFE_ACTION`; preservar avanços válidos. Não usar interrupção apenas por dúvidas triviais; STOP-THE-LINE quando exigido por governança, credenciais, permissão, fonte canônica, efeito irreversível, conflito de branch ou owner externo.

## 4. Decisões fechadas / autonomia do Devin

- Seis tools fixas; expansões só por `entity.action` tipadas.
- Commercial API e demais owners continuam autoridade. MCP nunca inventa dado, regra, permissão ou automação.
- Não criar novo banco/serviço/registry global, nem refatorar arquitetura inteira para obter paridade.
- Usar testes e padrões provados dos MCPs existentes, sem copiar policy incorreta.
- Decisões rotineiras de código, implementação de contrato existente, testes, paginação e mensagens: **executar sem perguntar**.
- Decisões não delegadas: mudanças de autorização/role, criação de novas capabilities de domínio não existentes, habilitar operação sensível sem aprovação do owner, alteração de Keycloak/ChatGPT, troca de branch/worktree, migração destrutiva, exclusão produtiva e mudanças com risco irreversível.
- Se funcionalidade depende de processo manual não especificado ou regra ainda não formalizada, entregar inventário + lacuna, não codificar hipótese como fato.

## 5. Relatório final e critérios de aceite

Entregar:
- `BASE_HEAD, FINAL_HEAD, BRANCH, origin/main, WORKTREE, DEPLOYED_SHA`
- inventário: `NUM_OPERATION_TOTAL, NUM_ELIGIBLE, NUM_IMPLEMENTED_TESTED, NUM_EXCLUDED_WITH_RATIONALE, NUM_BLOCKED`
- matriz por operação, tool/registry, schema, owner, autorização, evidência de paridade e testes
- cobertura de conhecimento: temas, fontes, versões, revisões, evidência, gaps
- novos arquivos, diff real, regressão, segurança, incidentes, logs sanitizados
- produção: host/container/SHA, health, OAuth, tool discovery, chamadas autorizadas/negativas, knowledge
- `PARITY_PERCENT` calculado apenas com denominador elegível verificado
- `PASS / FAIL / PENDING / INCONCLUSIVE / TEST_NOT_RUN / STALE_EVIDENCE`
- `FINAL_VERDICT: ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`.

**Aceite integral** só quando operações elegíveis inventariadas estiverem implementadas e testadas com paridade por processo, conhecimento confiável cobrir assuntos do domínio, segurança comprovar controles, commits/push/deploy e validação de produção forem demonstrados. Resultado menor é parcial, nunca “100%” por linguagem.

**Prompt para iniciar Devin:** “Execute integralmente `docs/initiatives/caio-mcp/CAIO_2_PARITY_EXECUTION_TRAIL.md`, seguindo E0→E9, sem perguntas rotineiras; inventarie, implemente, teste, commit/push e deploy canônico incremental. Preserve owners, branch, segurança e fonte canônica. Registre e prove resultado real; reporte apenas bloqueios materiais.”
