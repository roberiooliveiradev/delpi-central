# CAIO 3.0 — Trilha autônoma P0–P5: implementação e diário de resultados

> **Status inicial: PLANNED / NOT_IMPLEMENTED.** Este documento é a trilha de execução que Devin deve atualizar **durante cada etapa**, distinguindo intenção, implementação, teste e uso produtivo. Não marque uma etapa como concluída sem evidência.
>
> **Visão canônica:** [CAIO-INTELIGENCIA-COMERCIAL-3-0.md](CAIO-INTELIGENCIA-COMERCIAL-3-0.md).  
> **Owner:** commercial-api (contratos, cálculos, autorização); responsáveis comerciais validam métodos/processos; Portal Comercial é consumer.  
> **Base observada na criação:** `main 2aa736eabf13cf3bb52d420891991a786e70046a` — **obrigatório reancorar no início e entre etapas.**

## Missão e autonomia

Implemente **sequencialmente P0, P1, P2, P3, P4 e P5**, incluindo levantamento, código, testes, documentação, commit, push, implantação canônica e verificação segura de produção para incrementos aprovados pela governança vigente. **Não pare para perguntas técnicas rotineiras**: busque evidência, selecione o menor diff correto, execute a etapa, registre o resultado e prossiga. Não espere todas as etapas para salvar evidências.

**Não há autorização para:** ampliar permissões/escopo, criar processos ou dados de negócio fictícios, habilitar acesso web não aprovado, exfiltrar dados comerciais para terceiros, criar integrações pagas/credenciais, efetuar writes/destrutivas produtivas para testar, alterar a branch/worktree alheia, operar produção fora do runbook ou declarar pesquisa/funcionalidade implementada sem prova. **Se houver bloqueio material, registre `BLOCKED_EXTERNAL` com evidências e continue as etapas independentes.** Nunca implemente substituto inseguro para forçar 100%.

## E0 — Reancoragem obrigatória

- Verificar `git rev-parse HEAD`, `git branch --show-current`, `git status --short`, `git worktree list`, `git fetch origin`, `origin/main` e commits concorrentes.
- Ler `AGENTS.md` e regras aplicáveis em `.cursor/rules/` (arquitetura, segurança, agentes/MCP, testes, entrega).
- Confirmar conteúdo e consumidores de `commercial-api/commercial_app/content/caio_commercial_knowledge.json`, `application/caio/semantic_registry.py`, `interface/mcp/`, módulos `plugins/commercial/src/features`, documentação comercial e testes existentes.
- Inventariar a maneira real de compor dados, conhecimento e ferramentas no fluxo ChatGPT↔CAIO; **não presumir memória persistente, buscador web, RAG ou roteamento de conversa já existentes**.
- Rodar baseline; separar `CURRENT`, `PROPOSED`, `TO_INVENTORY`, `PENDING`. Manter as **seis tools públicas**: `get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete`.

## Contrato mínimo do conhecimento contextual (proposto, implementar apenas após verificar contratos)

Usar preferencialmente extensão simples do mecanismo `knowledge` existente. Cada fonte/método/roteiro deve permitir identificar `id, tipo, objetivo, applicability, prerequisitos, owner, canonical_source, version/date, access_classification, methods, related_capabilities, evidence, limitations, status`. Validar campos contra os modelos existentes; **não impor um novo repositório/indexer sem Abstraction Gate**.

Fluxo que deve ser demonstrado nos testes: **pergunta + contexto conversacional relevante → intenção/tema/entidades/período → método e roteiro adequados → recuperação mínima de conteúdo autorizado → consultas a casos de uso oficiais quando pertinentes → resposta com fonte, evidência, hipótese, lacunas e recomendações**. Não presumir que o MCP recebe todo o histórico do chat: onde isso não existe, usar contexto explicitamente recebido no schema existente ou contrato mínimo implementável; documentar o que é realmente transportado. O modelo não vira autoridade sobre escopo, autorização ou persistência.

### Matriz de execução — atualizar continuamente

| Etapa | Entrega verificável | Status | Commit | Testes/evidência | Deploy/SHA | Gaps |
|---|---|---|---|---|---|---|
| P0 | Inventário de fontes, perguntas, lacunas e baseline | DEPLOYED_VERIFIED | `447218e365` | [CAIO-3-0-INVENTORY.md](CAIO-3-0-INVENTORY.md) — 16 tópicos mapeados, 10 perguntas + rubrica, baseline 656/1224 | `447218e365` | nenhum novo |
| P1 | Biblioteca inicial curada de 6 métodos + recuperação | DEPLOYED_VERIFIED | `447218e365` | corpus v3.0 `methods` (6) + contrato de campos testado | `447218e365` | validação comercial pendente |
| P2 | Roteiros de diagnóstico e análises reutilizáveis | DEPLOYED_VERIFIED | `447218e365` | corpus v3.0 `playbooks` (8) + contrato testado | `447218e365` | — |
| P3 | Seleção contextual e composição da resposta | DEPLOYED_VERIFIED | `447218e365` | `knowledge` com `query` seleciona método+roteiro; testes de seleção/vazamento/404 honesto | `447218e365` | sem histórico do host (contrato mínimo documentado) |
| P4 | Pesquisa externa governada quando autorizada | BLOCKED_EXTERNAL | `447218e365` (offline) | gate: nenhum conector/buscador autorizado existe — verificação de código | N/A | contrato de integração proposto no diário P4 |
| P5 | Especialização B2B e processos comerciais reais | DEPLOYED_VERIFIED | `447218e365` | +8 métodos externos `pending_business_validation` testados | `447218e365` | PENDING_BUSINESS_VALIDATION |

`Status`: NOT_STARTED / IN_PROGRESS / IMPLEMENTED / TESTED / DEPLOYED_VERIFIED / BLOCKED_EXTERNAL / PARTIAL. Não trocar para DEPLOYED_VERIFIED sem evidência de SHA e smoke.

## P0 — Inventário e critérios de avaliação

**Executar:** mapear os 16 tópicos do corpus atual, fontes, proprietários, cobertura e limitações; mapear perguntas reais (diagnóstico executivo, riscos de clientes, pedidos, propostas, metas, processos); conferir escopos e permissão; mapear lacunas para método, contexto, pesquisas, responsabilidades e dados. Elaborar conjunto reproduzível de perguntas de referência e rubrica (fatos, fontes, método adequado, hipótese, autorização, próximo passo, tempo/resposta). **Entregável:** inventário e baseline em seção ou artefato canônico ligado aqui; não copiar conteúdo comercial desnecessariamente.

**Aceite:** inventário auditável com source/owner/status e testes baseline, sem afirmar capacidades novas implementadas.

## P1 — Biblioteca profissional de métodos comerciais

**Executar em primeira onda:** ABC/Pareto, RFV, desvio meta×realizado, funil e conversão, risco de pedidos/OTD e 5 Porquês. Para cada um: propósito, quando não usar, dados necessários, fórmula/etapas, limitações, exemplos sintéticos, origem das definições, perguntas que o acionam, capacidades CAIO relacionadas e validação comercial pendente quando aplicável. Método externo **não** é regra DELPI.

Integrar com `knowledge` tipada/versionada, sem duplicar calculadora/owner. Se os dados necessários não estiverem disponíveis, oferecer método qualitativo com lacuna explícita em vez de inventar indicador.

**Aceite:** seis métodos recuperáveis por tema/intenção, teste de source/version, controles de autorização, consultas de método desconhecido e conteúdo externo não confiável.

## P2 — Roteiros de análises aplicadas

**Executar:** adicionar gradualmente oito roteiros (diagnóstico executivo, clientes em retração, oportunidades de expansão, saúde dos pedidos, funil de propostas, previsão com cenários e incerteza, desempenho por vendedor/carteira, plano 30/60/90 dias). Priorizar a integração dos primeiros três: diagnóstico executivo, risco de pedidos e clientes em retração. Restantes entram na mesma trilha, sem inventar dados ou cálculos.

Cada roteiro define: objetivo, entradas, permissões, ferramentas semânticas existentes, fonte/indicador canônico, condições de dados insuficientes, formato de resposta e critérios de teste. Aplicar **conclusão → evidência → gap → próximo passo**. Respostas não podem confundir projeção com fato nem criar tarefas por conta própria.

**Aceite:** oito roteiros versionados, testes de seleção/referência e pelo menos três cenários de integração sem escrita; métodos e fontes transparentes.

## P3 — Inteligência contextual na conversa

**Executar:** seleção relevante baseada na pergunta, referências explícitas e contexto **realmente disponível** ao CAIO. Definir contrato mínimo de contexto sem depender de poderes não comprovados do host. Recuperar apenas métodos/fontes pertinentes; deduplicar, estabelecer precedência de fonte canônica, limites de tamanho, fallback honesto e relevância rastreável. Testar mudança de assunto, continuidade, filtros por período, carteiras diferentes, ambiguidade e ausência de histórico.

**Aceite:** testes demonstram seleção do conteúdo correto, sem vazamento cross-user/carteira nem exposição de fonte restrita. Diferenciar automaticamente resposta operacional de orientação metodológica.

## P4 — Pesquisa externa governada

**Primeiro, gate obrigatório:** descobrir se existe conector/buscador autorizado e contrato de segurança/privacidade para o CAIO. Revisar fontes, termos, autorização, proteção contra prompt injection, controle de consulta, logging, citações e data; **jamais enviar dados internos a motores externos sem contrato apropriado**.

**Se aprovado e disponível:** implementar o menor caminho que pesquisa metodologias públicas, tendências e benchmarking; devolver fonte, data, confiabilidade e distinção explícita de regras DELPI, sem passar instruções web para execução. Testes negativos de exfiltração, manipulação de instruções e URL maliciosa; não disparar writes com base em conteúdo externo.

**Se gate não atendido:** marcar `BLOCKED_EXTERNAL` e entregar biblioteca curada offline + contrato/proposta de integração, sem criar ferramenta de pesquisa fictícia. Continuar P5.

## P5 — Especialização em vendas B2B e processos reais

**Executar:** estruturar orientações de SPIN, MEDDPICC, Account Planning, benchmarking, SIPOC/BPMN, Ishikawa, PDCA/5W2H, SWOT e matriz de priorização, respeitando o processo industrial de cliente→proposta→pedido→produção→faturamento/entrega. Confirmar quais métodos são aplicáveis à DELPI e quais são apenas referências externas. Entrevistas não disponíveis: evidência documental e `PENDING_BUSINESS_VALIDATION`, nunca afirmar fluxo real não demonstrado.

Para diagnóstico de processo, registrar problema, atores, sistemas, etapas antes/depois, handoffs, esperas, métricas, desconhecidos e hipóteses; TÉO pode receber briefing fiel quando autorizado, sem mover ownership de regras comerciais.

**Aceite:** testes por pergunta real, fontes e limites; método correto selecionado; processo atual/proposta separados; nenhuma afirmação sem suporte.

## Testes transversais por etapa

- Baseline e regressão de CAIO/commercial-api e consumidores afetados; tests de contratos, seleção de método, fonte, filtros, datas, perfil admin/vendedor/sem acesso, ambiguidade, desconhecidos, falhas downstream, prompt injection, conteúdo externo.
- Avaliação com rubrica por cenário: fidelidade dos números oficiais, pertinência do método, rastreabilidade, conteúdo útil, recusa de dados fora do escopo e transparência de incerteza.
- Não usar produção para writes/exclusões de homologação. Em produção, apenas health, MCP discovery e chamadas read/analyze/knowledge com dados autorizados. Capturar deployed SHA.
- A cada etapa que gere código: revisar diff e consumidores, residual search, commit, push e deploy canônico **somente com gates**. Preservar working trees alheias, sem force push.

## Documentação obrigatória

Atualizar a cada etapa:
1. **Este documento:** linha da matriz + diário abaixo (data, HEAD inicial/final, files, síntese da implementação, teste, evidência, owner, status e gaps).
2. **Documento de visão:** `CAIO-INTELIGENCIA-COMERCIAL-3-0.md` (estado atual vs proposta).
3. **Documentação do Portal Comercial:** seção aplicável em `plugins/commercial/README.md` e docs de `docs/12-roadmap-e-evolucao/commercial/`, preferindo fonte canônica existente.
4. **Conteúdo e contratos CAIO:** corpus, matrizes de paridade/homologação conforme capacidade alterada.

Não criar documentação duplicada; registrar implantação e utilização real somente com prova.

## Diário de execução — Devin deve preencher após cada etapa

### P0 — Registro
- Data/owner: 2026-10-30 · commercial-api
- Base HEAD / branch / worktree: `b453b0981c` / `main` / `.worktrees/caio-homolog-125`
- Fontes inventariadas / lacunas: 16 tópicos mapeados com fonte/owner/status; lacunas = métodos, roteiros, seleção contextual, pesquisa externa, validação de negócio → `CAIO-3-0-INVENTORY.md`
- Evidências de baseline: suíte CAIO 656 passed/58 skipped; commercial-api 1224 passed/3 failed (baseline preexistente); `knowledge` = lookup exato por topic (sem seleção, sem histórico host — contrato real documentado)
- Arquivos e commit: `docs/12-roadmap-e-evolucao/commercial/CAIO-3-0-INVENTORY.md` (novo artefato canônico)
- Status/veredito: IMPLEMENTED
- Próximo passo: P1 corpus `methods` + recuperação tipada

### P1 — Registro
- Base HEAD: `b453b0981c`
- Métodos incorporados (IDs e fontes): `abc_pareto`, `rfv`, `desvio_meta`, `funil_conversao`, `risco_pedidos_otd`, `cinco_porques` — corpus `methods` v3.0, todos `external_reference: true` (curadoria externa, não regra DELPI)
- Contratos/arquivos alterados: `caio_commercial_knowledge.json` v2.0→v3.0 (`methods` dict com id/type/objective/applicability/required_data/formula/limitations/when_not_to_use/keywords/trigger_questions/related_capabilities/owner/version/source_date/access_classification/status); `semantic_bridge.tool_knowledge` resolve `method.<id>` e bare id
- Testes positivos e negativos: contrato de campos por método; `external_reference` obrigatório; bare-id resolution; 404 honesto com `available_ids`; source/version auditáveis
- Commit/push/deployed SHA: PENDING (deploy junto a P1–P3)
- Gaps/validação de negócio: métodos são referência externa; adequação aos processos DELPI = validação pendente dos responsáveis
- Status/veredito: TESTED

### P2 — Registro
- Base HEAD: `b453b0981c`
- Roteiros incorporados: 8 — `executive_diagnosis`, `customers_retraction`, `expansion_opportunities`, `order_health`, `proposal_funnel`, `forecast_scenarios`, `seller_portfolio_performance`, `plan_30_60_90` (corpus `playbooks` v3.0)
- Fontes e operações relacionadas: cada roteiro declara `semantic_steps` com capabilities reais (portfolio.*, customer.*, proposal.* com branch, open_order.*, production.*, analyze, worklist.*), `canonical_sources`, `permissions`, `insufficient_data`, `response_format` (conclusão→evidência→gap→próximo passo), `test_criteria`
- Evidência dos relatórios e testes: contrato de campos por roteiro; `semantic_steps`/`response_format`/`insufficient_data`/`permissions` obrigatórios; nenhum roteiro cria tool nova — compõe tools existentes
- Commit/push/deployed SHA: PENDING (deploy junto a P1–P3)
- Gaps: execução ponta a ponta dos roteiros é composição do agente — validação de saída completa depende de rodada autenticada
- Status/veredito: TESTED

### P3 — Registro
- Base HEAD: `b453b0981c`
- Contrato de contexto efetivo: MCP recebe apenas `topic`/`task`/`query` explícitos — sem histórico do chat, sem memória persistente, sem RAG/buscador (comprovado em código e documentado no inventário P0); seleção opera sobre o query recebido
- Recuperação e seleção testadas: `topic` vazio/`*`/`select`/`search` + `query` → seleção por score sobre title/keywords/trigger_questions, top-5 com provenance (`id/type/title/objective/source/owner/version/access_classification/external_reference/status/related_capabilities/limitations/conversation_relevance`)
- Casos de vazamento/autorização negativos: service principal → 403; seleção retorna só orientação interna (`access_classification: internal`) — sem dados de carteira/registros, logo sem vazamento cross-scope; consulta sem match → 404 honesto com ids disponíveis
- Commit/push/deployed SHA: PENDING
- Gaps: seleção por keyword simples (sem embeddings) — adequada ao corpus atual; reavaliar quando corpus crescer
- Status/veredito: TESTED

### P4 — Registro
- Base HEAD: `b453b0981c`
- Conector/gate autorizado (evidência): **nenhum conector/buscador web autorizado existe** — busca no código (commercial-api, plugins/commercial, docs CAIO) não encontra web_search/conector externo; a própria visão marca pesquisa externa como proposta sujeita a gate
- Fonte pública, data e trust boundary: N/A — gate não atendido
- Tests de segurança: N/A — nada implementado; nenhum dado interno foi transmitido a terceiros
- Commit/push/deployed SHA OU motivo BLOCKED_EXTERNAL: `BLOCKED_EXTERNAL` — entrega alternativa conforme a trilha: biblioteca curada offline implementada (P1/P5 `methods`, com `external_reference` marcado) + contrato proposto já descrito na visão §5 (fontes confiáveis, data, atribuição, limitação de domínio, não exfiltração, proteção contra prompt injection, isolamento web↔writes). Próxima ação: submeter contrato ao security gate antes de qualquer implementação
- Status/veredito: BLOCKED_EXTERNAL

### P5 — Registro
- Base HEAD: `b453b0981c`
- Métodos de vendas/processos e fontes: `spin_selling`, `meddpicc`, `account_planning`, `sipoc_bpmn`, `ishikawa`, `pdca_5w2h`, `swot`, `matriz_priorizacao` — corpus `methods` v3.0 (14 métodos totais), referências externas citadas na visão (SPIN, MEDDPICC, SIPOC/BPMN, PDCA/5W2H, SWOT, matriz de priorização)
- Validação com owner do negócio ou PENDING: `status: pending_business_validation` em todos — responsáveis comerciais devem validar adequação DELPI; nenhum método é apresentado como política interna
- Cenários e resultados: recuperação `method.<id>`/bare id; seleção por query ("qualificar oportunidade b2b" → meddpicc); campo `external_reference`+`status` auditáveis por teste
- Commit/push/deployed SHA: PENDING
- Gaps: validação de negócio pendente (documentado, não contornável); TÉO briefing apenas quando autorizado
- Status/veredito: TESTED (com validação de negócio pendente declarada)

## Relatório final e encerramento

Apresentar `INITIAL_HEAD, FINAL_HEAD, BRANCH, WORKTREE, COMMITS, PUSH, DEPLOYED_SHA`, matriz P0–P5 com evidências, cobertura de métodos/roteiros, fontes e versões, testes/regressão, segurança, gaps, dados não comprovados e `FINAL_VERDICT: ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`.

**Término correto:** completar todas as etapas tecnicamente executáveis e registrar as etapas legitimamente bloqueadas; não encerrar cedo por questões triviais; não prometer 100% quando P4/validações de negócio não têm autoridade ou acesso. Nenhum documento muda o estado do runtime apenas por declarar implementação.
