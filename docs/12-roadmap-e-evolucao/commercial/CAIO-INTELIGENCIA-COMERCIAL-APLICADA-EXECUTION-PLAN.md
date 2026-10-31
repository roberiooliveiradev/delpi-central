# CAIO — Inteligência Comercial Aplicada | Plano executivo e trilha de evidências

**Status inicial:** PROPOSED / NOT_IMPLEMENTED (a ser atualizado com evidência). **Data:** 2026-10-31.  
**Referências:** [Visão CAIO 3.0](CAIO-INTELIGENCIA-COMERCIAL-3-0.md), [Trilha 3.0 P0–P5](CAIO-3-0-EXECUTION-TRAIL.md), `docs/initiatives/caio-mcp/CAIO_PARITY_MATRIX.md`, `CAIO_HOMOLOGATION_MATRIX.md`.  
**Base observada ao preparar este plano:** `origin/main`/GitHub `02cf82fce434032814759d59588330da327bf2d7`; revalidar HEAD, branch, working tree e worktrees antes de executar.

## 1. Missão e limites de verdade

Transformar o CAIO de operador autorizado do Portal em **consultor comercial assistido por evidências**: conhecer o negócio DELPI, investigar causas, cruzar dados de clientes/produtos/propostas/pedidos/produção/ROL/OTD, reconhecer oportunidades, produzir alternativas e planos de ação mensuráveis. **Não prometer resultado comercial, não executar automaticamente sugestões nem criar novos indicadores oficiais sem owner.**

**Baseline conhecido (não provar outra coisa por inferência):** catálogo CAIO 127 operações (6 tools), corpus 3.1 com 17 termos, 16 métodos, 8 roteiros e `products.guide`; smoke de leitura e conhecimento autenticado realizado. Cobertura de operações elegíveis ≠ prova de execução de cada operação com todo perfil e integração; diferenças de escopo e autorização são legítimas. Pesquisa externa via CAIO ainda `BLOCKED_EXTERNAL` sem autorização/conector. Verificar fatos atuais novamente.

## 2. Princípios de arquitetura e segurança

- `commercial-api` é autoridade de domínio, casos de uso, permissões e indicadores comerciais; TOTVS/api-delpi e Engenharia/Products preservam ownership sobre produto/produção; TÉO não recebe regras de negócio; DÉLIA somente candidata quando evento/risco/recorrência reais o justificarem.
- Priorizar **reuso** de `read`, `analyze`, `knowledge` e 8 playbooks; manter seis tools. Não criar serviço/index/vector DB/orquestrador sem Abstraction Gate, justificativa e teste. Separar orientação do conhecimento de operação/dado vivo.
- Segurança backend-first por usuário, carteira, filial, tenant e permission scope; negar explicitamente acesso indevido. Nunca usar JWT isolado, frontend ou LLM como autorização final. Não consultar fornecedor externo com dado comercial sensível sem contrato aprovado.
- Novo cálculo só em owner que tenha autoridade; CAIO reutiliza séries/aggregates e, quando permitido, deriva resultados **claramente rotulados CALCULATED** com fórmula/denominador/janela e validação do owner. Se faltarem dados: `UNKNOWN`, `PENDING` ou `BLOCKED_EXTERNAL`, sem improvisar.
- Produção: smoke apenas read/analyze/knowledge. Writes/deletes só em fixture isolada. Alterações reais dependem autorização final, validação/auditoria/resultado; deletes também de confirmação humana verificável.
- Concorrência: worktree isolada; nunca incluir staged alheios em commit, reset destrutivo ou force push. Rebase/merge com revisão.

## 3. Entregas sequenciais W0–W8

### W0 — Inventário real, baseline e lacunas
Reconstruir contrato e uso atuais dos 8 playbooks, 16 métodos, 17 conceitos e operações CAIO; examinar testes, docs, rotas consumidoras, formulas oficiais, perfil e escopo. Catalogar perguntas comerciais reais, origem dos dados, autoridades, handoffs, trabalho manual, gaps de qualidade e falhas de entrega. Preparar fixtures e rubrica: fidelidade ao owner, pertinência do método, profundidade, ação verificável, escopo, fonte, tempo/resposta. Não confundir código com processo real. **Gate:** matriz de fontes, contratos e testes baseline reproduzíveis.

### W1 — Conhecimento profundo DELPI e glossário técnico-comercial
Evoluir fontes versionadas, sem copiar grandes tabelas de produto, cobrindo OV, PV, OP, LMP, revisões, pedidos, proposta, ROL, OTD, lead times, cliente/centro/carteira, chicotes e componentes, cadastro SB1, produto acabado/matéria-prima, desenho e BOM apenas quando permitidos, prazos e processo proposta→pedido→produção→faturamento→entrega. Para cada entrada: termo, definição validada, exemplos, fonte/owner, relações, limites e situação. Confirmar práticas reais com owner; lacunas `PENDING_BUSINESS_VALIDATION`. Perguntas sobre um produto real devem consultar API oficial; não inventar aplicações, compatibilidade ou engenharia. **Gate:** testes de precisão + fontes e limites visíveis.

### W2 — Inteligência de clientes e crescimento
Oferecer investigação estruturada de retração, inatividade, concentração, ABC, RFV, oportunidades de expansão por família/produto e account planning. Roteiro: descobrir carteira autorizada → comparar períodos/sazonalidade → evidência em billing/ROL/order/proposal → identificar hipóteses → rankear por impacto e confiança → recomendar recuperação. Diferenciar perda de cliente de queda de compra e oportunidade inferida. Não derivar margem ou LTV sem dados oficiais. **Gate:** casos com queda, sem queda, sem histórico, multi-carteira e autorização negativa; evidência financeira rastreável.

### W3 — Pedidos, produção, OTD e risco comercial
Cruzar pedidos em aberto, datas prometidas, saldo, vinculação OP, apontamentos, disponibilidade e OTD oficial; classificar `RISK` apenas com regras/evidências explícitas, separar risco previsto de atraso confirmado, sem calcular SLA/OTD alternativo. Preparar investigação com próximos passos e responsáveis fundamentados, não notificar automaticamente. **Gate:** casos pedido no prazo, atraso confirmado, dado fabril indisponível, OP sem vínculo, múltiplas filiais e perfil não autorizado.

### W4 — Propostas, funil, negociação e previsibilidade
Aprofundar aging por etapa, conversão com denominadores, perda/ganho somente quando status oficial sustentar, investigação de histórico/revisões e causas não comprovadas, forecast cenários com premissas/erro; aplicar SPIN/MEDDPICC como referência externa, não política DELPI. Produzir análise de próximos passos de oportunidade, sem editar propostas ou fazer contato sem consentimento. **Gate:** propostas reais autorizadas + casos sintéticos de conversão sem dados suficientes, histórico faltante e diferentes revisões.

### W5 — Inteligência técnico-comercial de chicotes e produtos
Estender `products.guide` e os 4 reads existentes **apenas quando necessário**, identificando catálogo/famílias, histórico e clientes do produto com escopo, linhas/famílias de compra, concentração e cross-sell sob hipótese. Quando for preciso estrutura BOM/desenho/especificação, usar contrato do owner com permissões e declarar indisponibilidade; não duplicar Engenharia/EVA ou expor desenho restrito. **Gate:** exemplo oficial de chicote com cadastro, ausência de cliente vinculado tratada como vazio válido, exceções e perfis distintos.

### W6 — Motor de investigação guiada e seleção contextual
Aprimorar o mecanismo atual de recuperação `knowledge` (keywords/top-5) para selecionar **objetivo + playbook + métodos + operações oficiais + perguntas de investigação + evidências + próximos passos**, sem prometer execução automática indisponível. Histórico da conversa só pode ser usado se de fato transmitido pelo host: verificar transport e criar contrato mínimo *opcional* de contexto, com governança, evitando memória persistente presumida. Planejar custo/limites/timeouts, explicabilidade da seleção, fallback, prevenção de prompt injection, testes de mudança de assunto e intenção ambígua. Não transformar CAIO em owner dos fluxos de negócio. **Gate:** resultados reproduzíveis com frases distintas e fontes corretas, nenhum vazamento entre carteiras.

### W7 — Entregáveis comerciais e preparação de ação
Entregar relatórios estruturados para diagnóstico executivo, carteira/clientes, pedidos/OP, funil, forecast, oportunidade por produto, reunião/visita e plano 30/60/90 dias. Saída: escopo/período, resumo executivo, fatos OBSERVED, cálculos auditáveis, hipóteses INFERRED, desconhecidos UNKNOWN, impacto quantificável ou não, top prioridades, alternativas, owner recomendado quando comprovado e KPI para medir. Opcionalmente **preparar** rascunhos de tarefa ou mensagem em resposta ao pedido; execução requer aprovação específica e contrato oficial. Não criar agenda, alerta ou monitoramento sem solicitação/gate. **Gate:** 8 roteiros testados com casos reais read-only + fixtures; comparar ao usuário referência para utilidade.

### W8 — Homologação, documentação, deploy e mensuração
Testar cenários integrados A–J: A glossário/OV→OP, B produtos/chicotes, C cliente em retração, D expansão, E pedido em risco, F proposta envelhecida, G forecast, H plano comercial, I processo comercial/SIPOC, J seleção contextual e segurança. Usar real data somente autorizados, sem writes produtivos; fixtures isoladas para mutações. Avaliar com rubrica e baselines de tempo, número de consultas, qualidade factual, recomendações acionáveis e incidentes de segurança. Publicar apenas incrementos que passem gates, identificar deployed SHA e teste autenticado quando possível. Atualizar documentação e orientar rodadas humanas sobre processos.

## 4. Ferramentas e metodologias: mapa de decisão

| Ferramenta | Uso/resultado esperado | Situação inicial |
|---|---|---|
| ABC/Pareto, RFV, segmentação e retração | priorizar contas e oportunidades | existente, aprofundar aplicação |
| Análise de desvios ROL/meta, séries e sazonalidade | explicar movimento e desvios | existente, owner do indicador preservado |
| Funil, aging, conversão, forecast com cenários | propostas, previsibilidade | existente, melhorar calibração |
| Risco de pedidos/OTD, análise de causa | antecipar exceções de entrega | existente, contextualizar |
| Account Planning, SPIN, MEDDPICC | vendas B2B industriais | referência externa pendente de validação |
| SIPOC/BPMN, 5 Porquês, Ishikawa, PDCA/5W2H | análise e melhoria de processo | referência externa; validar fluxo real |
| SWOT, matriz de priorização | decisões e planos | existente; pesos/regras explícitos |
| Benchmarking | comparar práticas e referências verificadas | método cadastrado; pesquisa web bloqueada até gate |
| Product guide + consultas oficiais | identificar chicotes, famílias e oportunidades | base existente; validar aplicações técnicas |
| Processos e atores comerciais | entender handoffs e trabalho manual | informação parcial; inventariar com negócio |

**Pesquisa externa:** trabalho opcional, somente após security gate; caso contrário `BLOCKED_EXTERNAL` e prosseguir. **DÉLIA:** somente documentar candidatos comprovados de evento recorrente, sem alegar automação existente.

## 5. Contrato para cada investigação e relatórios

Cada roteiro deve declarar `id, problema, intenção, perguntas de descoberta, fontes/owners, entidades, dados mínimos, filtros/janela, methods, official_actions, access_requirements, expected_evidence, transformations_permitted, failure_states, output_schema, quality_tests, status/version`. Reusar schema e registro já existentes, sem nova abstração injustificada.

Resultado demonstrável: **conclusão → evidência → causa confirmada ou hipótese → necessidade/alternativas → recomendação menor suficiente → owner/dependências/risco → KPI e verificação → limitações**.

## 6. Registros atualizados durante execução

| Fase | Status | HEAD / commit | Testes | Fontes/owner | Deployed SHA | Gaps |
|---|---|---|---|---|---|---|
| W0 Inventário | TESTED | — | — | — | N/A | — |
| W1 Conhecimento | TESTED | — | — | — | — | — |
| W2 Clientes | TESTED | — | — | — | — | — |
| W3 Pedidos | TESTED | — | — | — | — | — |
| W4 Propostas | TESTED | — | — | — | — | — |
| W5 Produtos | TESTED | — | — | — | — | — |
| W6 Contexto | TESTED | — | — | — | — | — |
| W7 Relatórios | TESTED | — | — | — | — | — |
| W8 Homologação | PARTIAL | — | — | — | — | — |

Diário 2026-10-31 (execução W0–W8): base dc0d34641e; CAIO 3.1 já continha glossário 17 termos, 16 métodos, products.guide, 4 product.*, seleção contextual — W1/W5 reutilizados; delta executado = corpus v3.2 com os 8 playbooks no contrato de investigação §5 (intent, investigation_questions, expected_evidence, failure_states, official_actions, output_schema OBSERVED/INFERRED/UNKNOWN→limitações) + teste de mapa de seleção A–J + contract fields; suíte CAIO 651 passed. Autenticado produção = TEST_NOT_RUN (credencial indisponível). W8 = PARTIAL até rodada autenticada A–J.

Status válidos: `NOT_STARTED`, `IN_PROGRESS`, `IMPLEMENTED`, `TESTED`, `DEPLOYED_VERIFIED`, `PARTIAL`, `BLOCKED_EXTERNAL`, `PENDING_BUSINESS_VALIDATION`.

### Diário de progresso — adicionar entrada por fase
Usar: `Data | fase | HEAD inicial/final | arquivos/diff | contratos/owners | problema e solução | provas de testes | smoke/deployed SHA | limitações | status | próxima fase`. Registrar também regressão baseline conhecida vs falha nova. Atualizar a matriz **imediatamente ao terminar cada fase** e realizar commits documentais incrementais; não deixar relatório só no chat.

## 7. Entrega técnica e gates

1. Reancorar HEAD, branch, worktree, upstream, owners, testes e documentos antes de alterações relevantes.
2. **Allowed diff**: `commercial-api/commercial_app/application/caio/`, `commercial-api/commercial_app/content/caio_commercial_knowledge.json`, `commercial-api/commercial_app/interface/mcp/`, testes de CAIO; adaptadores comerciais existentes apenas se contrato oficial e consumidores forem comprovados; docs acima. Outras áreas (api-delpi, Engenharia, frontend, banco, Keycloak, infra) **somente** se estritamente necessárias e autorizadas por contrato, com justificativa específica; nunca refactor amplo.
3. Revisar alterações por workstream, rodar testes unitários, contrato, auth, integração, regressão, análise de exposição de dados e residual search.
4. Commit/push por fase testada, sem sobrescrever concorrência. Deploy canônico de serviços afetados após gates, nunca trocar binário de serviço não afetado, evidenciar SHA realmente implantado.
5. Relatório final: BASE/FINAL HEAD, commits, diff, 6 tools/ops preservadas, conhecimento/metodologias/roteiros, resultados A–J, níveis de prova, auth, deploy SHA, gaps, backlog proposto separado, verdict `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`.

**Regra de autonomia:** percorrer W0–W8 sem parar por dúvidas rotineiras; pesquisar e decidir em limites do contrato. Se dependência material exigir aprovação (dado restrito, novo fornecedor, gasto, permissão, produção destrutiva, negócio não documentado), documentar a impossibilidade e continuar etapas independentes; não inventar fatos nem criar bypass.

**Critério último:** comprovar se a mudança melhora a investigação e decisão comercial **sem violar owner, segurança ou arquitetura**. Mais conteúdo no corpus, isoladamente, não é sucesso.
