# SURI — Catálogo de Métodos e Ferramentas de Suprimentos (Knowledge V2 · Inventário V1)

**Data:** 2026-11-01 · **Estado:** `RESEARCHED / PLANNED` · **Owner da curadoria:** Suprimentos / Product Owner, com suporte técnico supplies-api.  
**Escopo:** competência de gestão de suprimentos aplicável à assistência sobre **Portal Suprimentos** e serviços autorizados. **Fora do escopo:** mapeamento e governança de processos do Transformômetro (owner TÉO), BI/legados sem contrato, domínios próprios de Financeiro/Qualidade/PCP.  
**Objetivo:** formar base verificável de domínio para explicar conceitos, selecionar métodos, interpretar dados, comparar cenários, elaborar diagnósticos, relatórios e recomendações. **Não é autorização de implementar novas APIs, calcular KPIs sem contrato ou escrever dados.**

## 1. Fundamentação e status de evidência

- **PROVEN (Portal atual):** o MCP SURI V15 publica cinco tools (`get_context,read,analyze,knowledge,execute`) e a matriz oficial enumera 45 famílias de capacidade implementadas. A presença de um método neste documento **não** demonstra que os dados, campos, cálculos ou operações necessários estão disponíveis.
- **RESEARCHED (métodos externos):** práticas e conceitos descritos em fontes de referência (APQC, Institute for Supply Management). São referências conceituais, não contratos DELPI.
- **PLANNED (adoção SURI):** proposta de conhecimento, análise ou relatório, condicionada a inventário de dados, definição de fórmulas, owner e aprovação de produto. **Sem alterações de runtime nesta entrega.**
- Toda conclusão deve distinguir `OBSERVED/FACT`, `CALCULATED`, `INFERRED`, `RECOMMENDATION`, `UNKNOWN`; não atribuir causalidade sem evidência, não inventar risco, preço, benchmark, savings ou lead time.

### Fontes de referência pública consultadas em 2026-11-01

1. APQC — *Understanding Sourcing and Procurement Processes* (2026-06-08): https://www.apqc.org/resource-library/resource/understanding-sourcing-and-procurement-processes
2. APQC — *Sourcing and Procurement: 2024 Blueprint for Success*: https://www.apqc.org/resource-library/resource-listing/sourcing-and-procurement-2024-blueprint-success
3. APQC — *Process Frameworks (PCF)*: https://www.apqc.org/process-frameworks
4. APQC — *How Should Procurement And Sourcing Performance Be Benchmarked?*: https://www.apqc.org/How-Should-Procurement-And-Sourcing-Performance-Be-Benchmarked
5. APQC — *How Should Procure-to-Pay And Accounts-Payable Performance Be Measured And Improved?*: https://www.apqc.org/How-Should Procure-to-Pay-And-Accounts-Payable-Performance-Be-Measured-And-Improved (verificar URL antes de usar como link automatizado)
6. ISM — *Category Management in Procurement Essentials*: https://www.ism.ws/supply-chain/category-management-in-procurement/
7. ISM — *Procurement Analytics for Category Managers*: https://www.ismworld.org/supply-management-news-and-reports/news-publications/inside-supply-management-magazine/blog/2024/2024-05/procurement-analytics-for-category-managers/
8. ISM — *Tools & Templates Library*: https://sg.ismworld.org/for-individuals/member-tools-resources/tools--templates-library/

Essas referências apoiam a **taxonomia e o uso típico**; as fórmulas e limiares abaixo são exemplos educacionais, nunca números normativos ou indicadores oficiais da DELPI. Conteúdo protegido das fontes não deve ser copiado integralmente para o corpus.

## 2. Catálogo ampliado de ferramentas

Legenda: **P1** explicação prioritária, com aplicação potencial sobre dados já associados às páginas; **P2** depende de enriquecimento ou definição de método; **P3** exige fontes, contrato ou qualidade de dados adicionais. `DATA` abaixo = requisitos mínimos potenciais, **não disponibilidade comprovada**.

### A. Compras estratégicas e gestão de categorias

| ID | Método / ferramenta | Finalidade e uso | DATA potencial | Prioridade |
|---|---|---|---|---|
| ST-01 | Matriz de Kraljic | Segmentar categorias por impacto econômico × risco de suprimento; escolher estratégia por quadrante | spend por categoria, risco mensurado/justificado | P2 |
| ST-02 | Análise ABC / Pareto | Priorizar materiais, fornecedores ou gastos por valor acumulado | valor comparável, período, base de itens | P1 |
| ST-03 | Spend Analysis | Analisar gastos por fornecedor, categoria, unidade e tempo | preço/quantidade, natureza da despesa, períodos | P2 |
| ST-04 | Category Management | Estratégia, metas, pipeline e governança por categoria | taxonomia de categorias, spend, demanda, risco | P2 |
| ST-05 | Strategic Sourcing | Estruturar investigação, mercado, opções, seleção e acompanhamento | demanda, fornecedores, propostas e critérios | P2 |
| ST-06 | TCO (Total Cost of Ownership) | Comparar custo total de aquisição e operação; não só preço | preço, frete, impostos, qualidade, manutenção, descarte | P2 |
| ST-07 | Should-Cost | Estimar faixa plausível de custos com estrutura de insumos | BOM, índices, produtividade, custos confiáveis | P3 |
| ST-08 | RFx (RFI/RFQ/RFP) | Definir requisitos e critérios para informação, cotação e proposta | especificação, critérios, fornecedores | P2 |
| ST-09 | Mapa comparativo de propostas / weighted scoring | Comparar ofertas com critérios e pesos declarados | cotação, prazo, qualidade, impostos, pesos aprovados | P2 |
| ST-10 | BATNA e ZOPA | Preparar alternativas e faixa negociável, sem impor preços | propostas verificadas, objetivos e restrições | P3 |
| ST-11 | Make-or-Buy | Avaliar produzir internamente vs comprar | capacidade, custos, risco, qualidade e lead time | P3 |
| ST-12 | Sourcing portfolio / dual sourcing | Estudar diversificação e dependência de fornecedores | dependência, volume, capacidade alternativa | P2 |
| ST-13 | Price Variance / PPV | Medir diferença de preço frente a baseline definido | preços comparáveis, quantidades, referência homologada | P2 |
| ST-14 | Cost Avoidance vs Realized Savings | Distinguir custos evitados de economias efetivas | baseline aprovado, preço realizado, período, volume | P2 |
| ST-15 | Benchmarking de Compras | Comparar medidas normalizadas entre unidades/períodos e pares compatíveis | métricas consistentes, peer set, normalização | P2 |

### B. Desempenho, relacionamento e risco de fornecedores

| ID | Ferramenta | Finalidade e uso | DATA potencial | Prioridade |
|---|---|---|---|---|
| SU-01 | Supplier Scorecard | Painel ponderado de prazo, qualidade, custo, atendimento e conformidade | entregas, incidentes, contratos e pesos aprovados | P1 |
| SU-02 | SRM (Supplier Relationship Management) | Segmentar relacionamento e planos de melhoria | fornecedores, histórico, criticidade, planos | P2 |
| SU-03 | Supplier Preferencing | Modelar atratividade como cliente para o fornecedor | dados qualitativos validados, entrevistas | P3 |
| SU-04 | Matriz de risco de fornecimento | Probabilidade × impacto × mitigação, com justificativas | histórico, capacidade, riscos e owner | P1 |
| SU-05 | Concentração / Single-Source Exposure | Quantificar dependência por fornecedor/material/categoria | volume por fornecedor, item, período | P1 |
| SU-06 | OTD e OTIF | Monitorar pontualidade; OTIF requer comprovação de completude | datas acordadas/reais, quantidades solicitadas/recebidas | P1 |
| SU-07 | Supplier Development Plan | Ações com responsável, prazo e evidências de melhora | desvios, metas, owners e check-ins | P2 |
| SU-08 | Early Warning Indicators | Alertas de desvios de prazo, concentração e risco | séries históricas, limites homologados | P2 |
| SU-09 | Vendor Qualification / Onboarding Checklist | Verificar elegibilidade documental, técnica e de compliance | documentação e requisitos autorizados | P2 |
| SU-10 | Supply Chain Risk Register | Registrar risco, responsável, controle, residual e revisão | inputs validados por owners | P2 |
| SU-11 | Supply Resilience / Scenario Analysis | Simular atrasos, bloqueio de fornecedor ou alteração de demanda | consumo, cobertura, alternativas, hipóteses | P2 |

### C. Planejamento de materiais, estoques e abastecimento

| ID | Ferramenta | Finalidade e uso | DATA potencial | Prioridade |
|---|---|---|---|---|
| IN-01 | Giro de Estoques | Interpretar renovação por custo de consumo e estoque médio (mesmo critério contábil) | custo do consumo, estoque médio e período | P1 |
| IN-02 | Cobertura / Days of Supply (DOS) | Estimar dias cobertos por saldo e consumo médio compatível | saldo útil, demanda/consumo, janela | P1 |
| IN-03 | Estoque de Segurança | Explicar proteção para variabilidade e objetivos de serviço; comparar política ao cálculo owner | demanda, lead time, variabilidade, política | P1 |
| IN-04 | Ponto de Pedido (ROP) | Momento de reposição: demanda durante prazo + proteção; depende de hipótese adotada | lead time, consumo e estoque segurança | P1 |
| IN-05 | ABC-XYZ | Valor econômico × variabilidade/previsibilidade do consumo | consumo temporal, valor comparável | P2 |
| IN-06 | EOQ / Lote Econômico | Compensar custo fixo do pedido e custo de manutenção; pressupõe demanda relativamente estável | demanda, custo pedido, manutenção, restrições | P2 |
| IN-07 | Lead Time Analysis | Separar pedido, confirmação, trânsito, recebimento e variabilidade | carimbos temporais e eventos confiáveis | P1 |
| IN-08 | Ruptura / Stockout Rate | Mensurar ocorrências e duração de indisponibilidade | eventos de ruptura ou demanda não atendida | P2 |
| IN-09 | Obsolescência / Slow-Moving | Identificar sem giro e risco de obsolescência | última movimentação, saldo, validade/política | P2 |
| IN-10 | MRP / Net Requirements | Explicar necessidades líquidas e dependências de BOM/carteira | BOM, demanda, estoques e lead time do owner PCP | P3 |
| IN-11 | Min-Max / Replenishment Policy | Definir gatilhos e níveis planejados com regras aprovadas | consumos, prazos, lotes, políticas | P2 |
| IN-12 | Inventory Accuracy / Cycle Counting | Avaliar diferenças físico × sistema | contagens físicas auditadas e registros | P3 |
| IN-13 | S&OP / IBP interface | Interpretar impactos dos planos autorizados, sem assumir planejamento de PCP | cenários agregados, forecasts aprovados | P3 |
| IN-14 | Excess & Shortage Exposure | Estimar exposição a excesso/ruptura com horizonte explícito | estoque, demanda, inbound, parametrização | P1 |

### D. Compras operacionais e execução

| ID | Ferramenta | Finalidade e uso | DATA potencial | Prioridade |
|---|---|---|---|---|
| OP-01 | Purchase Requisition Aging | Listar SCs abertas por idade/etapa | SC status, datas e unidade | P1 |
| OP-02 | Open PO Aging / Overdue PO | Quantificar PC por prazo e atraso | PC, promised dates, status | P1 |
| OP-03 | Purchase-to-Receipt Lead Time | Medir emissão até recebimento e dispersão | PC/recebimento, eventos confiáveis | P1 |
| OP-04 | Procure-to-Pay (P2P) Scorecard | Análise ponta a ponta por owners, sem invadir Financeiro | pedidos, recebimento, invoice/payment autorizados | P3 |
| OP-05 | Maverick Buying / Contract Compliance | Detectar compras fora de política/contrato | contrato, aprovações e transações | P3 |
| OP-06 | Procurement Cycle Time | Medir requisição→PC e etapas com timestamps | SC/PC relacionados, eventos | P2 |
| OP-07 | Exception / Backlog Analysis | Priorizar filas por criticidade, tempo e impacto | alertas e dados operacionais | P1 |
| OP-08 | Supplier Delivery Root-Cause | Combinar 5 Porquês, Ishikawa e fatos verificados | atrasos, histórico, entrevistas e ocorrências | P2 |

### E. Inteligência de mercado, custos e decisão

| ID | Ferramenta | Finalidade e uso | DATA potencial | Prioridade |
|---|---|---|---|---|
| MK-01 | Market Index Tracking | Monitorar índices/cotações por período, base e moeda | fonte autorizada, cotação e metodologia | P1 |
| MK-02 | FX Exposure / Currency Scenario | Avaliar sensibilidade cambial com premissas explícitas | moeda, volume, datas e taxas autorizadas | P2 |
| MK-03 | Commodity Price Benchmark | Comparar preço contratual vs índice normalizado | preços homologados, índice compatível e defasagem | P2 |
| MK-04 | Trend / Variance / Seasonality | Descrever séries, dispersão e tendência sem previsão implícita | séries suficientes, granularidade | P1 |
| MK-05 | Scenario & Sensitivity Analysis | Testar hipóteses de prazo, preço e demanda, sem afirmar previsão | baseline, intervalos e parâmetros | P2 |
| MK-06 | NCM / Import Governance Checklist | Verificar estado e exceções de governança Comex | NCM, homologação fiscal, status | P1 |
| MK-07 | Landed Cost Analysis | Estimar custo posto com frete, taxas e impostos aplicáveis | preço, Incoterm, tributos, frete e jurisdição | P3 |

### F. Melhoria contínua, desempenho gerencial e relatórios

| ID | Ferramenta | Finalidade e uso | DATA potencial | Prioridade |
|---|---|---|---|---|
| MG-01 | Procurement KPI Scorecard / Balanced Scorecard | Combinar custos, prazos, produtividade, qualidade e riscos | KPIs aprovados com períodos e owners | P1 |
| MG-02 | 5 Porquês | Estruturar hipóteses de causas com evidências | incidente, fatos e validação humana | P1 |
| MG-03 | Ishikawa / Causa-Efeito | Organizar categorias de causas potenciais | evidências, entrevistas | P2 |
| MG-04 | FMEA aplicado ao abastecimento | Riscos por severidade/ocorrência/detecção, escalas definidas | critérios aprovados, incidentes | P2 |
| MG-05 | PDCA / A3 | Planejar, testar e documentar ações de melhoria | problema, baseline, owner e metas | P2 |
| MG-06 | 5W2H | Plano de ação objetivo com responsável, prazo e custo | decisão/owners | P1 |
| MG-07 | Pareto de Causas de Atraso | Priorizar causas registradas, não causas inferidas | taxonomia consistente de incidentes | P2 |
| MG-08 | Supplier/Inventory Executive Report | Produzir narrativa, indicadores, evidência, riscos e decisões | dados read + metodologias aprovadas | P1 |
| MG-09 | Benchmarking de Performance Operacional | Comparar unidades/períodos e padrões de mercado, normalizando diferenças | métricas comuns, comparáveis e autorização | P2 |
| MG-10 | Risk Heatmap + Action Register | Visualizar impacto/probabilidade e ações | avaliação humana/owner e critérios | P2 |

**Total inicial do catálogo: 65 entradas** (ST 15 + SU 11 + IN 14 + OP 8 + MK 7 + MG 10). O cadastro de uma ferramenta **não significa** que a SURI já a executa, que seus dados existem no Portal ou que a metodologia foi aprovada pela DELPI.

## 3. Relação com o Portal Suprimentos — somente capacidades conhecidas

| Página / família atual | Métodos mais diretamente aplicáveis | O que validar antes de ativar análises |
|---|---|---|
| Início / Overview | MG-01, OP-07, MG-08 | KPI owner, denominador, janelas, parcialidade e metas |
| Solicitações de Compra | OP-01, OP-06, OP-07 | transições e timestamps canônicos PR-api |
| Pedidos de Compra | OP-02, OP-03, ST-02, ST-03, ST-13 | valores, datas, grãos (linha vs pedido), deduplicação |
| Entregas / Atrasos | SU-06, SU-01, IN-07, MG-07 | contrato de OTD e data/quantidade; não chamar OTIF sem dados |
| Controle de Estoques | IN-01, IN-02, IN-05, IN-09, IN-14 | consumo histórico, custo, warehouse, unidades de medida |
| Estoque de Segurança | IN-03, IN-04, SU-04, IN-14 | parâmetros de segurança e fórmula canônica owner |
| Fornecedores | SU-01..SU-11, ST-01, ST-12 | chaves, avaliação qualidade e dados de riscos |
| Consumo OP | IN-05, IN-07, OP-08, MG-04 | owner PCP para BOM/produção, sem importar domain |
| Inteligência de Mercado | MK-01..MK-05, ST-07 | status da fonte, data, licença, unidade e FX |
| Comex | MK-06, MK-07 | status fiscal/owner e campos do contrato |
| Usuários / Preferências / Ajuda | apoio ao uso e interpretação, sem inventar KPI | manual e RBAC efetivo |

## 4. Modelo de cada ficha de conhecimento da SURI

Criar ficha versionada por método com:
- `method_id`, `name_pt_br`, `aliases`, `category`, `objective`, `when_to_use`, `when_not_to_use`.
- `explanation_basic`, `explanation_advanced`, `workflow`, `inputs_required`, `input_units`, `data_quality_checks`.
- `formula_or_algorithm`, `assumptions`, `interpretation`, `limitations`, `examples_synthetic` (claramente rotulados).
- `portal_pages`, `suri_operations`, `canonical_owner`, `authority_sources`, `source_locators`, `reviewed_at`, `reviewed_by`.
- `capability_status` (`KNOWLEDGE_ONLY|DATA_GAP|ANALYSIS_PLANNED|IMPLEMENTED|RUNTIME_PROVEN`), `security_notes`, `expected_outputs`, `test_questions`, `acceptance_evidence`.

## 5. Regras de aplicação e interpretação

1. **Método não é fato:** conceitos e fórmulas são orientação; cada cálculo produtivo deve ser congelado pelo owner do indicador. Por exemplo, a fórmula de OTD do Portal prevalece sobre a definição genérica.
2. **Dado faltante não vira zero:** distinguir inexistência, ausência de permissão, indisponibilidade da fonte e zero legítimo.
3. **ABC:** ordenar valor econômico comparável por período e somar participação acumulada; cortes A/B/C são parâmetros negociados e **não** padrões universais.
4. **OTIF:** não inferir a parcela `in full` só a partir de pontualidade OTD.
5. **Kraljic:** impacto pode ser estimado economicamente, mas risco de suprimento exige critérios externos/qualitativos aceitos; não classificar automaticamente com dados incompletos.
6. **TCO/should-cost:** resultado é modelo condicional com premissas, não custo observado da DELPI.
7. **Forecast/scenario:** cenários identificados como hipóteses e não previsão oficial.
8. **Qualidade, Financeiro, PCP e outros contextos:** não importar regras nem consultar banco diretamente; usar dados/contratos autorizados, sinalizar lacunas.
9. **IA como explicadora:** texto deve separar dado, cálculo, interpretação e recomendação, mencionar recorte, data, fonte, unidade, limitações e próximo passo.
10. **Relatórios:** permitir versões executiva e analítica, com apêndice de metodologia, proveniência e perguntas não respondidas; artefato editável/export só quando o canal suportar ou o produto oferecer contrato homologado.
11. **Segurança:** Core effective permissions, `capability AND unit_scope AND resource_scope/ownership AND business_rule`, fail-closed. Nunca usar knowledge para escalar AuthZ.
12. **Cinco tools:** `get_context,read,analyze,knowledge,execute`. O catálogo de 65 métodos **não** cria 65 endpoints ou novas MCP tools.

## 6. Exemplos de jornadas de análise (futuras, sem prometer dados)

**J1 — Atrasos e risco de abastecimento:** perguntas → unidade/período → `deliveries.late` + PC + estoque segurança → scorecard condicionado a qualidade → fatos, hipóteses, principais fornecedores, plano 5W2H. Se não houver identificação confiável de fornecedor/material em ambas as fontes, não fazer join inferido.

**J2 — Diagnóstico de estoque:** `inventory.summary/items` + consumo autorizado → ABC, giro/cobertura só se houver custo do consumo e baseline temporal → exposição a ruptura/excesso → relatório executivo + analítico. Não confundir estoque instantâneo com estoque médio.

**J3 — Performance de fornecedores:** cadastro+OTD+compras → scorecard (pesos aprovados) → diferenciação de risco, concentração e desempenho → propostas de ação, não decisões automáticas.

**J4 — Inteligência de mercado:** `market` + Comex → séries por fonte autorizada → variação e cenários, com moeda e periodicidade corretas → riscos de preço. Se fonte estiver `pending_fiscal_review` ou indisponível, sinalizar.

**J5 — Gestão de SC/PC:** atrasos de etapas, backlog, pendências e variação de preço, respeitando owners de SC/PC, chaves corretas e SLA homologado.

## 7. Curadoria e critérios de qualidade

Para cada ficha, exigir:
- Explicação para iniciante, especialista e gestor; exemplos sintéticos; perguntas adversariais sobre dados ausentes, unidade/CC, divergência entre KPIs e fonte em quarentena.
- Resposta da SURI citando fonte interna, data, versão e status `PROVEN / TO_INVENTORY / PLANNED`.
- Testes de retrieval relevantes, ausência de alucinação sobre páginas inexistentes, autorização negativa (403) e uso de fórmula aprovada.
- Revisão de domínio por responsável de Suprimentos antes de ativação como orientação oficial; revisão técnica por owner do cálculo antes de implementar análise.
- Sincronização com Help e alterações reais das páginas; evitar conteúdo que pareça authority maior que contrato/HEAD.

## 8. Backlog de adoção — ciclos seguintes, NÃO EXECUTAR AGORA

| Ciclo | Entrega | Gate / evidência |
|---|---|---|
| K0 | Inventário da Help, glossário, schemas, endpoints, 45 capacidades e campos disponíveis por página | matriz página→capability→método→input→owner |
| K1 | Curadoria P1: 22 métodos (ST-02, SU-01/04/05/06, IN-01/02/03/04/07/14, OP-01/02/03/07, MK-01/04/06, MG-01/02/06/08) | fichas + validação PO + testes de compreensão |
| K2 | Expansão knowledge corpus com fonte/locator/hash, versionamento e testes | `knowledge(search|get|sources)`, 5 tools |
| K3 | Análises determinísticas P1, uma por contrato, somente se houver inputs e fórmula suficientes | positive+sibling+negative, AuthZ, dados-fonte e parcialidade |
| K4 | Relatórios e jornadas compostas; templates, proveniência, export adequado a cada canal | smoke real, revisão de qualidade e usuário |
| K5 | P2/P3 por viabilidade e valor, sem pressupor novas páginas/APIs | backlog reavaliado e autorização do lote |

**Não misturar conhecimento do Transformômetro, não adicionar integrações TÉO; não modificar runtime neste ciclo documental.**

## 9. Critérios de aceite desta documentação

- Taxonomia ampla, IDs estáveis, prioridades e requisitos de dados; fronteira clara entre conhecimento conceitual e dados PROVEN do Portal.
- Referências externas com links e indicações de authority; referências internas só após inventário do HEAD.
- Lista explícita de pressupostos, limites, exemplos de jornadas e plano de governança.
- Documento aprovado como **inventário de pesquisa / planejamento**, não como implementação de knowledge no MCP.
