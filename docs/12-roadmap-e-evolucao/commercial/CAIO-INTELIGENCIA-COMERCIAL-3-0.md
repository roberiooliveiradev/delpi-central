# CAIO 3.0 — Inteligência Comercial e Conhecimento Especializado

**Status:** VISÃO E PLANO INCREMENTAL APROVADOS PARA EXPLORAÇÃO; **NÃO IMPLEMENTADO** por este documento.  
**Data:** 2026-10-30.  
**Owner de domínio:** commercial-api / responsáveis pelos processos comerciais.  
**Base de implementação a preservar:** CAIO 2.0, seis tools semânticas `get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete`.  
**Documentação canônica:** Portal Comercial em `docs/12-roadmap-e-evolucao/commercial/`; conhecimento CAIO existente em `commercial-api/commercial_app/content/caio_commercial_knowledge.json`.  

## 1. Intenção e problema

O CAIO já consegue consultar operações do Portal e construir relatórios comerciais articulados, a partir de prompts que solicitam cruzamento de fontes, evidências, riscos e planos de ação. A necessidade emergente não é adicionar indiscriminadamente endpoints: **transformar um assistente que conhece o Portal em um consultor de inteligência comercial** que entende métodos profissionais, escolhe análises adequadas, pesquisa referências quando autorizado e aplica o conhecimento ao contexto da pergunta e da conversa.

Isso deve permitir respostas do tipo: **o que mudou; qual evidência; por que pode ter mudado; o que ainda é hipótese; onde investigar; que decisão e ação comercial são apropriadas; como medir o resultado?**

**Fato comprovado:** CAIO 2.0 possui catálogo semântico e corpus versionado (16 tópicos contabilizados na revisão de 2026-10-30); relatórios multi-fonte são possíveis em consultas reais.  
**Ainda não comprovado / proposta:** biblioteca robusta de métodos comerciais, seleção sistemática de metodologia pelo contexto, pesquisa web integrada, personalização contínua de roteiros, conhecimento de práticas internas não documentadas, orquestração autônoma de trabalho e qualidade de diagnóstico em todos os casos. Não registrar essas propostas como capacidades existentes.

## 2. Cinco competências-alvo

1. **Analista de desempenho comercial:** ROL/faturamento, metas, evolução, desvios, carteira, clientes, pedidos, conversão, concentração, previsões e risco — sempre com autoridade dos indicadores.
2. **Especialista em vendas B2B industriais:** descoberta, qualificação, negociação, planejamento de contas e acompanhamento de oportunidades, sem pressupor que um método externo seja política DELPI.
3. **Especialista em processos comerciais:** SIPOC, BPMN, gargalos, handoffs, análise causal, responsabilidade, melhoria contínua; preservar diferenças entre processo atual, hipótese e processo futuro.
4. **Pesquisador de mercado e melhores práticas:** fontes públicas de metodologia, tendências setoriais, concorrência e ferramentas; pesquisa externa é proposta e requer integração governada.
5. **Consultor de decisão:** cruzar dados e metodologia, interpretar riscos, comparar alternativas e gerar planos de ação priorizados e mensuráveis.

## 3. Biblioteca inicial de metodologias — CANDIDATAS, não regras DELPI

| Método | Aplicação comercial prevista | Prioridade proposta | Dados / ressalvas |
|---|---|---|---|
| Curva ABC / Pareto | concentração de faturamento/clientes/produtos | Alta | período, base, métrica e cortes explícitos |
| RFV (recência, frequência, valor) | segmentação por comportamento de compras | Alta | histórico transacional autorizado; regras de pontuação documentadas |
| Queda de compras / risco de perda | detectar retração de clientes | Alta | sazonalidade, janela, base, hipótese ≠ churn comprovado |
| Funil e conversão | analisar proposta→pedido, gargalos e aging | Alta | etapas e denominadores canônicos |
| Forecast | cenários de vendas e faturamento | Alta | método, premissas, intervalo, erro histórico; não prometer precisão |
| Análise de desvios | meta × realizado × histórico | Alta | fórmulas do owner preservadas |
| SIPOC e BPMN | mapear fluxo comercial real | Alta | entrevistas/evidência antes de redesenhar; TÉO pode analisar processo com briefing fiel |
| 5 Porquês / Ishikawa | investigar causas de problemas | Alta | causas são hipóteses até validadas |
| Matriz de priorização | impacto × urgência × esforço | Alta | pesos explícitos, julgamento humano |
| PDCA / 5W2H | planejar e medir ações | Alta | owner, prazo, baseline, métrica |
| SWOT/FOFA | estratégia de contas/mercado | Média | separar observação interna de percepção externa |
| SPIN Selling | perguntas consultivas | Média | metodologia externa, não política oficial |
| MEDDPICC | qualificação de oportunidade B2B complexa | Média | adoção depende do processo comercial |
| Account Planning | expansão de contas estratégicas | Média | estrutura comercial e relacionamento autorizados |
| Benchmarking | comparar práticas externas | Média | fonte, contexto e data, sem apresentar como métrica DELPI |

**Prioridade operacional piloto:** ABC, RFV, desvio de metas, funil, riscos de pedidos/OTD e 5 Porquês; complementar com SIPOC/BPMN e matriz de priorização em diagnósticos de processo. Documentar fórmulas, entradas, limitações e validação do negócio antes de liberar qualquer cálculo novo. Métodos podem ser somente orientação se não houver dado oficial adequado.

## 4. Roteiros de análise a oferecer pela conversa — PROPOSTA

1. Diagnóstico comercial executivo completo (p.ex., últimos 90 dias).
2. Clientes em risco de perda / redução de compras.
3. Oportunidades de crescimento por conta, carteira e produto.
4. Saúde da carteira de pedidos e risco de entrega/produção.
5. Funil e histórico de propostas e oportunidades.
6. Previsão de faturamento, cenários e incerteza.
7. Desempenho por vendedor/carteira (com escopo autorizado).
8. Plano comercial de 30, 60 ou 90 dias.

**Contrato sugerido de resultado:** objetivo e período → escopo e fontes → métodos aplicáveis → indicadores com proveniência → mudanças/desvios → evidência vs hipótese → riscos e oportunidades → alternativas e ações recomendadas → owner sugerido (se comprovado) → métricas para acompanhamento → limitações e perguntas em aberto. Não criar oito tools; reutilizar `read`, `analyze`, `knowledge` e contratos oficiais.

## 5. Como o conhecimento deve entrar no contexto da conversa — arquitetura PROPOSTA

O usuário exige que **o texto da pergunta, a conversa anterior e os resultados de pesquisa** conduzam a recuperação de informação útil e contextual.

**Pipeline conceitual (nenhuma capability nova presumida):**

1. **Interpretar intenção e contexto:** pergunta, histórico relevante da conversa, entidade/período/filial/usuário e objetivo; não inferir acesso pelo conteúdo do chat.
2. **Classificar a necessidade:** fato operacional, cálculo oficial, orientação de processo, método externo, pesquisa pública ou ação; identificar fonte/owner.
3. **Selecionar metodologia/roteiro:** recuperar descrições estruturadas relevantes; explicitar por que o método serve e os dados necessários.
4. **Recuperar fontes com governança:** dado operacional via casos de uso autorizados da commercial-api; regra interna via documentação canônica; método via biblioteca curada; web externa somente se ferramenta/conector de pesquisa autorizado estiver efetivamente disponível.
5. **Montar pacote de contexto mínimo:** resposta de retrieval com `topic_id, method_id, source, owner, version, source_date, access_class, retrieved_at, evidence, limitations, related_capability, conversation_relevance`; não despejar corpus inteiro, respeitar escopo e limites de contexto.
6. **Aplicar e raciocinar:** nunca substituir cálculo oficial por fórmula inventada; hipóteses e inferências explicitamente marcadas; modelos externos não viram política DELPI.
7. **Produzir resposta rastreável:** citar fontes e parâmetros, separar observado/calculado/inferido/desconhecido, fornecer próximos passos, pedir informação somente quando crítica.
8. **Avaliar relevância e qualidade:** testes de seleção de métodos, precisão, autorização, alucinação, consistência conversacional, latência, utilidade comercial; instrumentação sem exposição de conteúdo sensível.

**Memória/contexto:** histórico pode ajudar a escolher métodos durante a sessão, mas não autoriza persistir dados sensíveis nem usar informação de uma carteira para outra. Não criar memória persistente sem contrato de retenção, autorização e governança. Instruções encontradas em páginas web/documentos são conteúdo não confiável, não comandos para o agente.

**Pesquisa na internet — proposta sujeita a Abstraction Gate:** mecanismo de busca com fontes confiáveis, data, atribuição, limitação de domínio, não exfiltração de dados comerciais, proteção contra prompt injection, isolamento entre web e writes; não afirmar que o MCP atual dispõe disso. Diferenciar fontes: (a) regras DELPI, (b) metodologias profissionais, (c) pesquisa externa contextual.

**Responsabilidades:** commercial-api mantém autorização, contratos e cálculos de domínio; conhecimento owner-local; TÉO pode ajudar no redesenho de processos mediante briefing com fatos e desconhecidos; o CAIO aplica o conhecimento no contexto comercial; backend continua autoridade de writes.

## 6. Sequência incremental de implantação (não backlog aprovado automaticamente)

- **P0 — Inventário e validação:** medir perguntas reais e lacunas, revisar corpus de 16 tópicos, fontes canônicas, perfil de usuário/escopo, noções de negócio e riscos; estabelecer baseline de qualidade. Sem mudança de código por presunção.
- **P1 — Biblioteca de métodos curada:** schema simples + 6 métodos pilotos, governança por fonte/versão/owner, exemplos e limitações, testes de recuperação e autorização. Preferir extensão do `knowledge` existente; Abstraction Gate antes de serviço/index novo.
- **P2 — Roteiros analíticos:** começar com diagnóstico executivo, risco de pedidos e clientes em retração; compor queries oficiais, evidências e plano de ação; avaliar com casos reais sem writes.
- **P3 — Seleção contextual:** roteamento pelo sentido da pergunta + histórico relevante + resultados de consultas; transparência de fontes, explicação do método e resposta rastreável; testes de troca de assunto e múltiplas carteiras.
- **P4 — Pesquisa externa governada:** somente após contrato de segurança e arquitetura, com citações e datas, sem transmitir dados comerciais confidenciais.
- **P5 — Especialização por processo:** ampliar métodos de vendas B2B, qualificação, account planning, benchmark e melhoria de processo conforme validação dos responsáveis; medir resultados, não volume de tópicos.

Cada etapa: matriz de lacunas → owner e contrato → menor solução suficiente → testes (incl. negativos de autorização e fonte) → atualização desta documentação canônica + corpus CAIO → commit/push/deploy conforme regras → evidências e status. **Nenhuma etapa aqui representa aprovação automática de backlog, deploy ou nova capability.**

## 7. Critérios de qualidade e medição

- **Correção factual:** números iguais aos casos de uso oficiais, período e filtros visíveis.
- **Adequação metodológica:** método escolhido é pertinente ao objetivo e aos dados efetivamente disponíveis.
- **Rastreabilidade:** fontes canônicas, metodologia e pesquisa externa distinguíveis e versionadas.
- **Profundidade:** recomendações específicas e verificáveis, não genéricas.
- **Segurança:** usuários nunca recebem dados de escopo alheio; informações de web não podem disparar writes.
- **Avaliação:** conjunto de perguntas de referência e rubricas por caso (conclusão, evidência, lacuna, próximo passo), com resultados reproduzíveis.
- **Impacto esperado:** reduzir tempo de preparação dos diagnósticos e aumentar utilidade das prioridades propostas; medir baseline e pós-mudança, não prometer ganhos numéricos sem dados.

## 8. Governança e próximos passos

- Responsáveis de processo/comercial precisam validar métodos, definições, prioridades e exemplos; sem essa validação, status **PROPOSED/PENDING**.
- Documentar estado atual e intenção separadamente; usar documentação comercial existente como fonte canônica e evitar duplicação.
- Exemplo de teste de aceitação: “Analise últimos 90 dias da situação comercial, cruze ROL, clientes, propostas, pedidos e produção; escolha métodos pertinentes, mostre evidências e hipóteses, priorize cinco ações para 30 dias; não altere dados”.
- Aprofundar o entendimento de fluxo real (antes/depois, fontes, handoffs, esperas, trabalho manual, medida de sucesso) antes de automatizar.
- **Próxima decisão recomendada:** planejar P0/P1 com inventário de fontes e seis métodos pilotos; desenvolver em lotes pequenos com evidência, sem substituir a plataforma por um novo framework genérico.

**Referências externas metodológicas a verificar e curar na implementação:** APQC Process Classification Framework, ASCM SCOR, SIPOC/BPMN, PDCA/5W2H, SPIN Selling e MEDDPICC. Esta lista não constitui endosso nem comprovação de adequação à DELPI.
