# 211 — Banco de 28 perguntas compostas para MCPs personalizados DELPI

- **Estado:** PLANNED / TEST_NOT_RUN. Este documento é especificação de bateria, não prova de integração, autorização ou resposta.
- **Data:** 2026-11-01.
- **Origem:** MCPs personalizados visíveis nesta sessão: CAIO, CLARA, SURI, EVA, TÉO, VISTA e DAVI.
- **Owner da avaliação:** DÉLIA; fatos e regras permanecem nas Domain APIs e owners. MCP/A2A = interoperabilidade.
- **Referências:** Documento 210, Documento 83, autoridades canônicas e Execution Ledger. Não altera fase.
- **Modo:** READ-only; nenhuma conexão nova ou deploy autorizados por este registro.

## Protocolo obrigatório da avaliação

**Regras comuns:** Somente leitura, análise e recomendações textuais. Não criar, enviar, editar, excluir, aprovar ou executar ações; não usar tools WRITE. Usar capabilities READ/ANALYZE/KNOWLEDGE efetivamente publicadas, sem presumir nomes de tools. Resolver Core AuthZ e Domain API como autoridades; informar período, fuso, fontes, filtros e limitações. Distinguir FACT, cálculo reproduzível, hipótese e previsão. Não inventar valores, clientes, pedidos, pessoas, documentos ou causas. Ocultar dados sem autorização; se não houver cobertura, concluir parcialmente com lacunas explícitas.

**Preparação:** reancorar HEAD + authorities + ledger; confirmar capabilities e contratos efetivos por owner; escolher snapshots/períodos e criar oráculos autoritativos por cenário antes da execução. Não pressupor que os nomes read/analyze/knowledge existam em todos os MCPs. Para perguntas que cruzam módulos, só consultar outro owner com autorização e vínculo contratual legítimo.

**Avaliação:** registrar cenário, SHA/config/modelo, identity/authz, capabilities consideradas/invocadas, first divergence, evidências com identificadores protegidos, cobertura por requisito, fórmulas, resultado factual, limitações, chamadas LLM, tokens, latência, segurança e Business Outcome. PASS exige conclusão substantiva e correta de todos os requisitos obrigatórios disponíveis; PARTIAL exige explicitar lacunas reais; FAIL inclui resposta genérica, inventada ou seleção incorreta. TEST_NOT_RUN para acesso ausente; não pontuar como falha semântica. Repetir 3 vezes com cenário congelado; separar conhecido de held-out independente.

**Rubrica transversal:** (1) seleção e escopo autorizados, (2) completude factual por subobjetivo, (3) exatidão de números/tempo/cálculos, (4) proveniência/citações, (5) hipótese vs fato, (6) qualidade e viabilidade das recomendações, (7) segurança read-only, (8) custo e latência. Cada item deve ter oráculo explícito; não aprovar só por HTTP 200.

## CAIO — Comercial

### CMP-01 — Análise comercial 360° (90 dias)

**Pergunta integral para a DÉLIA:**

> CAIO, produza um diagnóstico completo da situação comercial da DELPI nos últimos 90 dias com dados oficiais do Portal Comercial. Examine ROL, faturamento e evolução temporal, metas, taxa de fechamento e tendências; concentração por carteira e cliente, clientes que reduziram compras e oportunidades; pedidos em aberto, atrasos, OTD e saldo a faturar; propostas, etapas do funil, oportunidades estagnadas e impacto potencial. Concilie definições, períodos e denominadores antes de comparar. Identifique as cinco prioridades por impacto e urgência; para cada uma inclua números e evidências, entidades autorizadas, impacto financeiro calculável, causa comprovada ou hipótese, ação recomendada, responsável sugerido apenas com fundamento e KPI. Termine com plano de ação textual de 30 dias, dependências e limitações. Não crie tarefas nem execute mudanças.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-02 — Risco de carteira e recuperação de clientes

**Pergunta integral para a DÉLIA:**

> CAIO, investigue os clientes e carteiras com maior queda de compras nos últimos 180 dias, comparando períodos equivalentes e sazonalidade disponível. Separe perda de frequência, redução de ticket, concentração de receita, clientes inativos e migração de mix; confronte pedidos, propostas e histórico de faturamento onde houver vínculo oficial. Produza ranking de até cinco riscos e até cinco oportunidades, com critérios transparentes, cliente/carteira apenas se autorizado, magnitude monetária e lacunas. Para cada item proponha abordagem comercial e indicador de acompanhamento para 30 dias, sem inferir motivos do cliente sem evidência nem disparar contato.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-03 — Funil de propostas e previsão fundamentada

**Pergunta integral para a DÉLIA:**

> CAIO, avalie as propostas e oportunidades abertas dos últimos 120 dias: quantidade, valor, estágios, envelhecimento, conversão histórica por etapa e oportunidades sem avanço. Compare o pipeline com metas e faturamento realizado, explicitando quais indicadores são oficialmente disponíveis e sem converter automaticamente valor bruto em receita provável. Projete cenários conservador/base/otimista somente se houver histórico e premissas defensáveis; mostre fórmulas, intervalos e incerteza. Identifique cinco intervenções prioritárias com justificativa, proprietário sugerido fundamentado e indicadores. Entregue recomendações, sem alterar propostas ou estágios.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-04 — Pedidos, entregas e risco de faturamento

**Pergunta integral para a DÉLIA:**

> CAIO, consolide pedidos abertos, atrasados e previstos para entrega nos próximos 30 dias. Relacione OTD, saldo a faturar, prazo prometido, histórico de entrega e concentração por cliente/carteira conforme as fontes autorizadas. Diferencie atraso confirmado, risco previsto e impedimento cuja causa não esteja documentada; não atribua culpa à produção ou suprimentos sem evidência. Estime exposição financeira sem dupla contagem, liste prioridades com pedidos identificados quando autorizado, proponha mitigação e painel textual de acompanhamento semanal. Nenhuma alteração de pedido nem comunicação externa.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

## CLARA — Controladoria e Finanças

### CMP-05 — Saúde financeira e fechamento trimestral

**Pergunta integral para a DÉLIA:**

> CLARA, analise os últimos três fechamentos mensais disponíveis: receitas, custos, despesas, margem, desvios contra orçamento e pendências de fechamento conforme evidências oficiais acessíveis. Explique a base contábil e os períodos antes de cruzar valores; identifique inconsistências e tarefas com evidência ausente, distinguindo pendência documental de erro contábil. Ordene cinco riscos ou melhorias por materialidade e urgência, com valores, origem, causa comprovada versus hipótese, responsáveis documentados quando houver e ações de controle para 30 dias. Apenas relatório; não fechar tarefas nem lançar ajustes.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-06 — Variação orçamentária e principais drivers

**Pergunta integral para a DÉLIA:**

> CLARA, investigue os maiores desvios orçado versus realizado dos últimos 90 dias, por centro de custo ou rubrica quando disponível. Separe efeito preço, volume, classificação e competência apenas se os dados permitirem, incluindo ponte matemática reproduzível e reconciliação de totais. Mostre os cinco desvios mais relevantes e as fontes de cada valor; assinale insuficiência de evidências sem preencher lacunas por suposição. Recomende verificações e indicadores para os próximos 30 dias, sem lançamentos ou mudanças em orçamento.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-07 — Qualidade de evidências e prontidão de fechamento

**Pergunta integral para a DÉLIA:**

> CLARA, avalie a prontidão do fechamento mensal mais recente e dos dois anteriores: tarefas concluídas, atrasadas, evidências anexadas, responsáveis formalmente designados, dependências e exceções. Cruze a evolução dos atrasos com os registros de controladoria disponíveis, distinguindo falha de processo de ausência de informação. Produza matriz de risco, cinco ações priorizadas com criticidade e evidência, e plano de conferência semanal. Não aprovar, concluir nem modificar tarefas.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-08 — Cenários financeiros com incerteza explícita

**Pergunta integral para a DÉLIA:**

> CLARA, usando somente números oficiais disponíveis, avalie exposição a variações de receitas e custos para os próximos 30–90 dias. Identifique tendência observada, sazonalidade conhecida e os fatores que não podem ser previstos. Se houver base suficiente, calcule três cenários de margem/resultado com premissas e sensibilidades explicitadas; caso contrário apresente apenas diagnóstico das lacunas. Termine com cinco prioridades de monitoramento, responsáveis somente se formalmente vinculados e métricas. Não tratar cenários como fatos nem executar qualquer ajuste financeiro.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

## SURI — Suprimentos

### CMP-09 — Abastecimento crítico e pedidos de compra

**Pergunta integral para a DÉLIA:**

> SURI, investigue a situação dos pedidos de compra em aberto dos últimos 90 dias e das entregas previstas nos próximos 30 dias. Identifique atrasos confirmados, lead times, itens críticos, concentrações por fornecedor, quantidades e valores quando disponíveis. Diferencie falta real de material, risco de abastecimento e indisponibilidade de informação. Priorize cinco casos com IDs autorizados, impacto operacional potencial verificável, evidências, causa ou hipótese, alternativa recomendada e KPI. Sem emitir, cancelar ou modificar pedidos.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-10 — Performance de fornecedores e recorrência de atrasos

**Pergunta integral para a DÉLIA:**

> SURI, compare desempenho de fornecedores em janelas equivalentes dos últimos 180 dias por prazo, quantidade, incidência de atraso e valor das compras, conforme a fonte oficial permitir. Evite rankings sem denominadores comparáveis ou julgamentos não documentados. Apresente padrões de recorrência, cinco riscos e cinco oportunidades de melhoria com evidências de pedidos, premissas e recomendações de acompanhamento em 30 dias. Não enviar cobrança, avaliação formal ou mensagem a fornecedores.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-11 — Demandas futuras e planejamento de compras

**Pergunta integral para a DÉLIA:**

> SURI, examine solicitações e pedidos de compra disponíveis que possam impactar as próximas seis semanas. Agrupe por item, prazo, status e dependência legítima; identifique duplicidades possíveis sem afirmar que são duplicatas sem identificadores e prova. Calcule saldo pendente e exposição de valor somente quando campos oficiais permitirem. Monte uma sequência sugerida de acompanhamento com cinco prioridades, indicadores, limites e dados faltantes. Não criar requisições nem aprovar compras.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-12 — Diagnóstico de gargalos do ciclo de compras

**Pergunta integral para a DÉLIA:**

> SURI, avalie os tempos e estados de um ciclo de compra — solicitação, aprovação, pedido e recebimento — para o período recente, somente nas etapas publicadas pelas APIs autorizadas. Localize possíveis filas, exceções e retrabalhos com timestamps verificáveis; se uma etapa não estiver disponível, marque lacuna. Apresente cinco gargalos priorizados com evidências, cálculo do atraso, hipótese causal separada de fato e plano de melhoria de 30 dias. Nenhuma execução operacional.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

## EVA — Engenharia

### CMP-13 — Portfólio de demandas e backlog técnico

**Pergunta integral para a DÉLIA:**

> EVA, analise as demandas e solicitações de Engenharia dos últimos 90 dias: volumes, status, tempo em aberto, envelhecimento, prioridades registradas, responsáveis autorizados e evidências de conclusão. Investigue dependências e gargalos observáveis sem inferir automaticamente que atrasos são falhas pessoais. Selecione cinco prioridades com IDs, impacto documentado, causa ou hipótese, ação recomendada e indicador semanal. Não alterar demandas ou encaminhar tarefas.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-14 — LMPs, revisões e riscos de documentação

**Pergunta integral para a DÉLIA:**

> EVA, investigue LMPs e documentos de engenharia disponíveis, sua revisão, vinculações com solicitações e inconsistências formalmente registradas. Diferencie revisão vigente, obsoleta e desconhecida conforme contrato e evidências; não deduza conformidade técnica ou segurança física a partir de texto livre. Liste cinco riscos ou melhorias com referência documental, necessidade de validação humana e plano textual de revisão em 30 dias. Não publicar, aprovar ou editar arquivos.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-15 — Bottlenecks e previsibilidade do fluxo de engenharia

**Pergunta integral para a DÉLIA:**

> EVA, investigue a evolução do fluxo de solicitações técnicas ao longo dos últimos 180 dias, calculando throughput, tempo por estágio e demandas paradas apenas quando timestamps e status oficiais permitirem. Segmente por tipo de demanda e prioridade quando cabível; evite estatísticas com amostra insuficiente. Identifique cinco restrições de fluxo, exponha evidências, hipóteses e recomendações, e proponha indicadores de acompanhamento sem redistribuir trabalho automaticamente.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-16 — Dependências de engenharia e impacto no atendimento

**Pergunta integral para a DÉLIA:**

> EVA, avalie demandas técnicas com prazo próximo, atrasadas ou dependentes de documentos, desenhos ou LMPs. Identifique vínculos comprovados, bloqueios e incertezas; não invente relação com produção, compras ou clientes que não esteja publicada. Construa um mapa textual de até cinco cadeias críticas, explique a origem de cada vínculo e sugira mitigação e pontos de verificação nos próximos 30 dias. Não comandar máquinas, publicar desenhos ou executar ações.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

## TÉO — Transformação Digital

### CMP-17 — Panorama das iniciativas e gargalos

**Pergunta integral para a DÉLIA:**

> TÉO, analise iniciativas e processos de transformação digital dos últimos 90 dias com dados oficiais do Transformômetro: andamento, metas, atrasos, benefícios registrados, dependências, riscos e evidências de progresso. Cruze categorias e status somente quando publicados e comparáveis. Identifique cinco prioridades por impacto e urgência, diferenciando benefício realizado, estimativa e hipótese; proponha ações e métricas de 30 dias. Não criar nem modificar iniciativas.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-18 — Maturidade de processos e oportunidades SIPOC

**Pergunta integral para a DÉLIA:**

> TÉO, identifique processos ou iniciativas disponíveis com lacunas de documentação, handoffs ou indicadores. Examine evidências de SIPOC ou modelos processuais apenas quando registrados; não invente etapas do processo. Selecione até cinco oportunidades de padronização, com owner conhecido, lacunas, riscos e propostas práticas de diagnóstico. Produza uma agenda textual de 30 dias e indicadores sem editar o Transformômetro.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-19 — Atrasos recorrentes e causalidade

**Pergunta integral para a DÉLIA:**

> TÉO, investigue iniciativas com atrasos repetidos ou mudanças de prazo nos últimos 180 dias. Compare histórico e dependências; se não houver histórico versionado, declare a impossibilidade de provar reincidência. Separe causa registrada de hipótese e estime impacto apenas quando houver base quantitativa. Apresente cinco prioridades, evidência por iniciativa, responsáveis formalmente associados e plano de acompanhamento não executável.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-20 — Medição de valor da transformação

**Pergunta integral para a DÉLIA:**

> TÉO, avalie se as iniciativas recentes dispõem de baseline, indicador-alvo, data, resultado observado e evidência de benefício. Classifique como benefício comprovado, parcialmente observado, projetado ou não mensurável, sem tratar estimativas como resultado. Identifique cinco lacunas prioritárias de medição e proponha coleta/validação humana e indicadores para 30 dias. Nenhuma atualização de registros.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

## VISTA — Painéis Operacionais

### CMP-21 — Inventário de indicadores e qualidade dos painéis

**Pergunta integral para a DÉLIA:**

> VISTA, apresente um inventário fundamentado dos painéis e indicadores disponíveis para análise operacional, incluindo definição, granularidade, período coberto, fonte e atualização quando publicados. Identifique cobertura ausente, dados desatualizados e métricas com definição ambígua, distinguindo o que o catálogo declara do que foi efetivamente lido. Priorize cinco riscos de interpretação e recomende um plano de validação de 30 dias. Não modificar painéis nem programações.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-22 — Tendências, anomalias e limitações temporais

**Pergunta integral para a DÉLIA:**

> VISTA, selecione indicadores operacionais efetivamente acessíveis com série recente e examine tendências dos últimos 90 dias. Compare períodos equivalentes e evidencie valores observados; não chamar uma variação de anomalia estatística sem base suficiente. Identifique cinco pontos de atenção, cálculos reproduzíveis, possíveis causas somente como hipóteses e ações de investigação. Se só existir catálogo, explique por que não há série para análise.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-23 — Conciliação entre formatos e métricas

**Pergunta integral para a DÉLIA:**

> VISTA, investigue se uma mesma métrica pode ser consultada em diferentes formatos ou painéis publicados. Compare definições, filtros, atualização, unidades, agregações e totalizadores, sem presumir que formatos de exibição diferentes são conjuntos de dados equivalentes. Identifique divergências comprovadas e limites do catálogo, priorizando cinco verificações e indicadores de reconciliação. Não criar ou alterar visualizações.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-24 — Riscos de decisão com dados incompletos

**Pergunta integral para a DÉLIA:**

> VISTA, avalie as métricas disponíveis para uma revisão gerencial mensal, identificando cobertura, atualidade, permissões, filtros possíveis e ausência de denominadores. Proponha um quadro textual de até cinco indicadores prioritários com definição, evidência, risco de uso incorreto, responsável pelo dado somente quando oficialmente identificado e validação recomendada em 30 dias. Não invente KPIs ou resultados ausentes.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

## DAVI — Dados e Informações DELPI

### CMP-25 — Investigação de materiais por descrições variantes

**Pergunta integral para a DÉLIA:**

> DAVI, investigue no cadastro oficial materiais de conexão elétrica descritos como terminal pino, terminal bala, conector e variantes técnicas semelhantes. Descubra capacidades e fontes autorizadas; execute apenas consultas pertinentes e compare códigos, designações, medidas, materiais e variantes sem fundir itens distintos por semelhança textual. Entregue até dez exemplos reais com campos verificáveis, critérios de inclusão, ambiguidades e ausências. Não inventar cadastro nem editar materiais.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-26 — Rastreabilidade de uma entidade empresarial

**Pergunta integral para a DÉLIA:**

> DAVI, com base em um identificador empresarial autorizado fornecido pelo contexto de teste, investigue quais registros oficiais e relações podem ser consultados sobre essa entidade. Diferencie identificação direta, associação comprovada e mera coincidência textual; respeite a fronteira de cada Domain API. Produza linha de evidências com origem, timestamps quando disponíveis, relações encontradas e lacunas; se o identificador não estiver fornecido, não escolha arbitrariamente outro. Nenhuma alteração.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-27 — Comparação de consultas e contradições

**Pergunta integral para a DÉLIA:**

> DAVI, examine duas consultas oficiais relacionadas a um mesmo assunto empresarial conforme fixtures/oráculos previamente preparados, usando discovery e execução governada. Identifique se os resultados são realmente comparáveis em período, unidade, entidade e escopo; explique possíveis divergências e se podem ou não ser conciliadas. Gere tabela de fontes, evidências, conclusões sustentadas e pontos que exigem validação do owner. Não resolver inconsistências inventando uma versão da verdade.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

### CMP-28 — Investigação completa de uma pergunta ambígua

**Pergunta integral para a DÉLIA:**

> DAVI, receba uma solicitação empresarial ambígua com múltiplas entidades homônimas existentes nos dados de teste. Mostre como identifica o objetivo, descobre as superfícies autorizadas e decide quando precisa de esclarecimento, sem escolher um registro sem evidência suficiente. Quando a desambiguação for possível por contexto oficial, conclua a consulta com rastreabilidade; caso contrário apresente alternativas comprovadas e a informação faltante. Não executar writes.

**Oráculo mínimo a preparar:** confirmar ferramentas/superfícies publicadas, períodos e filtros, evidências numéricas ou documentais exigidas, autorizações, casos negativos e ausência legítima, reconciliação/cálculos, origem dos dados, e ausência de writes. Definir critérios específicos de PASS/PARTIAL/FAIL antes de rodar.

## Matriz de execução (preencher com evidência)

| MCP | Casos | Contrato | AuthZ | 3 repetições | Business Outcome | First divergence |
|---|---|---|---|---|---|---|
| CAIO | 4 | TO_INVENTORY | TO_INVENTORY | TEST_NOT_RUN | PENDING | PENDING |
| CLARA | 4 | TO_INVENTORY | TO_INVENTORY | TEST_NOT_RUN | PENDING | PENDING |
| SURI | 4 | TO_INVENTORY | TO_INVENTORY | TEST_NOT_RUN | PENDING | PENDING |
| EVA | 4 | TO_INVENTORY | TO_INVENTORY | TEST_NOT_RUN | PENDING | PENDING |
| TÉO | 4 | TO_INVENTORY | TO_INVENTORY | TEST_NOT_RUN | PENDING | PENDING |
| VISTA | 4 | TO_INVENTORY | TO_INVENTORY | TEST_NOT_RUN | PENDING | PENDING |
| DAVI | 4 | TO_INVENTORY | TO_INVENTORY | TEST_NOT_RUN | PENDING | PENDING |

## Critério de acompanhamento

São 28 perguntas compostas iniciais. Conectar MCPs é task distinta, sujeita a REUSE/ABSTRACTION/SECURITY GATES; avaliar READ antes de qualquer ACT. Não exigir cinco prioridades quando a evidência não sustentar cinco itens; declarar a cobertura e explicitar os faltantes. Atualizar o Documento 210 e o Execution Ledger quando a bateria for executada e houver evidência factual, preservando este banco como versão congelável. Não ajustar perguntas nem oráculos depois de observar respostas sem gerar nova versão e novo held-out.
