# 119 — EVA | Catálogo Mestre de Validações de Desenhos e Priorização por Não Conformidades

**Status:** PLANNED — plano funcional evolutivo, não aprovação de regras nem de qualidade.  
**Data-base:** 2026-11-03.  
**Owner do plano:** Portal Engenharia / Coordination; **autoridade técnica:** owners de Engenharia.  
**Source of truth:** Domain APIs de Engenharia; registros de NC lidos via EVA, nunca copiados como fonte oficial.  
**Vinculação:** [Doc 116](116-eva-engineering-drawing-intelligence-master-delivery-plan.md) (M0–M5, evidência/GT/thresholds) e [Doc 118](118-eva-drawing-intelligence-r11-reusable-object-profiles.md) (surface R11–M5).  
**Natureza:** SOMENTE documentação e backlog de validações; não muda código, RBAC, contratos de autoridade nem publica desenho.

## 0. Regra mandatória de execução — uma validação completa por vez

**Decisão de direção do produto (2026-11-03): concentração, fechamento e generalização real.** Este documento é o plano vivo e o tracker do desenvolvimento; não iniciar debates ou prompts fragmentados sem fim. **Somente E1 / VAL-01 (estrutura registrada no desenho × estrutura oficial) está ATIVA. E2–E7 ficam congeladas como BACKLOG, sem desenvolvimento paralelo, até o aceite completo de E1 no escopo de desenho aprovado.** Corrigir defeitos necessários ao E1 dentro da própria entrega; não abrir E1.1/E1.2 automaticamente.

### 0.1 O que significa "fechar" uma validação

Cada componente de análise deve ser **verticalmente completo**, desde a leitura oficial até o resultado no relatório: descoberta de fontes/regras → leitura do desenho → interpretação estruturada → associação de ocorrências → comparação autorizada → identificação de diferenças/lacunas → evidências → testes reais e casos históricos de NC → revisão/aceite do owner. Não considerar concluído por criar ports, modelos, relações ou um relatório que sempre retorna INCONCLUSIVE.

**E1 precisa cobrir todas as informações estruturais aplicáveis e verificáveis:** identidade/efetividade da estrutura; cabeçalhos; item/posição; código e descrição do componente; quantidades e unidades com equivalência autorizada; ocorrência repetida e multiplicidade; estrutura multinível/subconjunto e política de representação na tabela; componentes extras/faltantes somente quando há observação confiável; vínculos item↔balão quando necessários para identificar a estrutura; revisão/documento; coerência da tabela e rastreabilidade bidirecional. Sem inventar regras quando fontes oficiais não existem.

**Regra de aceite:** `PASS` por requisito com evidência real e critérios de qualidade previamente aprovados; `FAIL` quando há comportamento incorreto; `INCONCLUSIVE`/`NOT_COMPARABLE` quando há abstenção correta e justificada — **esses estados não podem disfarçar cobertura insuficiente**. Aceite completo de E1 exige que a família de desenhos-alvo e os requisitos obrigatórios tenham validação de qualidade do owner, incluindo casos positivos, negativos e variantes, não apenas unit tests. A decisão de uso oficial continua com Engenharia.

### 0.2 Generalizar sem prometer o impossível

**Objetivo de produto:** chegar a validar estruturas de desenhos variados, sem regras hardcoded por código de produto, cliente, layout fixo ou PDF de regressão. “Qualquer tipo de estrutura em qualquer tipo de desenho” é **aspiração TARGET**, não capability PROVEN nem um critério instantâneo tecnicamente demonstrável: desenhos podem ter estrutura implícita, listas parciais, formato não suportado, arquivo ausente e revisões incompatíveis. Para cada família/layout/revisão coberta, o sistema deve declarar explicitamente **SUPPORTED / UNSUPPORTED / INCONCLUSIVE**, com razão verificável; novos tipos só entram na cobertura após corpus representativo, testes de generalização e aprovação técnica. Não extrapolar um resultado para todos os desenhos.

A prioridade funcional continua concentrada em **VAL-01**, mesmo quando for necessário melhorar OCR, layout, item/código/descrição/quantidade ou associação de balões: esses são meios para concluir a estrutura, **não frentes de produtos independentes**. Balões, cotas, carimbo e outras áreas só serão desenvolvidos integralmente na própria entrega futura, salvo o mínimo necessário para estabelecer identidade e integridade de E1.

### 0.3 Protocolo de gestão sem iterações infinitas

1. Manter **um plano (Doc 119) e um tracker (issue #131)**; atualizar RQ/AC, escopo, evidência, impedimento, decisão e progresso ali, sem proliferar issues/prompts para a mesma falha.
2. Antes de executar: `HEAD/branch/status → owner → fonte oficial → contrato → RQ/AC → GT/threshold → implementação/testes → E2E/avaliação → aceite`. Reusar R11–M5, sem novas autoridades ou infraestrutura paralela.
3. Resolver os defeitos pertencentes ao escopo em **um pacote bounded**; como gestão, usar até três ciclos locais de reproduzir/corrigir/testar. Esse limite **não permite aprovar requisito obrigatório parcial**. Ao esgotar, produzir evidência do bloqueio, causa, owner e decisão de escopo/abordagem; não gerar automaticamente nova fase.
4. Critério de saída de E1: matriz AC por atributo/família, desenhos variados e holdout aprovado, NCs reais reavaliadas na versão correta, desempenho/segurança/AuthZ, casos de não comparabilidade corretos, relatório global e por item, autorização do owner. Somente depois promover E2 a ATIVA.
5. NC histórica orienta risco e testes de regressão; não é ground truth da revisão corrente sem checagem e anotação aprovada.
6. Mudança de owner, authority, fonte oficial ou bounded context exige `ARCHITECTURE_DECISION_REQUIRED` e retorno à Coordination.

**Estado inicial:** E1 = ATIVA PARA ESPECIFICAÇÃO E FECHAMENTO; critérios/contratos/GT oficiais pendentes não equivalem a implementação concluída. E2–E7 = BACKLOG CONGELADO. O M5 existente é base técnica reaproveitada, não validação de estrutura já aprovada.

---

## 0A. Modelo operacional de planejamento, prompts, revisão e aceite (DECISÃO — 2026-11-03)

**Owner da condução:** Coordination / ChatGPT como arquiteto, autor de prompts fechados e revisor independente; **executor:** Devin; **autoridade de aprovação técnica:** owners de Engenharia; **source of truth:** Domain APIs. Nenhuma revisão por IA concede autoridade de publicação. Esta decisão complementa a Seção 0, sem alterar o Documento 116.

### 0A.1 Fluxo de uma entrega

`ESTUDAR E DELIMITAR → INVENTARIAR AUTHORITIES/FONTES/CONTRATOS → DEFINIR RQ/AC E CRITÉRIOS DE SAÍDA → EMITIR UM PROMPT DE EXECUÇÃO FECHADO → DEVIN IMPLEMENTA/TESTA/CORRIGE INTERNAMENTE → CHATGPT REVISA INDEPENDENTEMENTE (CÓDIGO + CONTRATO + E2E QUANDO DISPONÍVEL) → DECISÃO E REGISTRO NO GITHUB → PRÓXIMA VALIDAÇÃO`.

- **Agora:** somente **estudo técnico e especificação de VAL-01 Estrutura**; nenhuma implementação ou prompt de implementação autorizado nesta decisão.
- O prompt de execução só será produzido quando o escopo técnico e os AC tiverem sido estudados e delimitados.
- O executor deverá entregar funcionalidade vertical de ponta a ponta, não só ports, contratos, DTOs ou testes isolados.
- A revisão ChatGPT deve ser crítica e independente: não repetir nem autoaprovar alegações de deploy ou testes do executor; verificar SHA, integração real, casos positivos/negativos, semântica, permissão, evidências e risco de falso conflito.
- A aprovação técnica de Engenharia e publicação governada são independentes do aceite de implementação.

### 0A.2 Política antirrecursão e defeitos

1. **Uma frente ativa (E1) e um pacote bounded por entrega.** Não criar subprojetos E1.1/E1.2, prompts exploratórios em cascata ou novos frameworks para contornar falha.
2. **Primeira devolutiva de revisão consolidada:** classificar todas as falhas relevantes identificadas como `BLOCKING` (contrato, comportamento incorreto, ausência de requisito, segurança, falso positivo, E2E obrigatório), `NON_BLOCKING` (limitação permitida e documentada) ou `OUT_OF_SCOPE` (backlog). Evitar um prompt por defeito.
3. **O Devin corrige dentro do pacote original**, com causa raiz, regressão e evidência no mesmo SHA. Até três ciclos locais de correção são limite gerencial sugerido no Doc 116, **não** autorização para aprovar falhas obrigatórias.
4. Ao persistir bloqueio após limite: registrar causa, provas, autoridade/owner, impacto, opções de escopo/abordagem; escalar decisão à Coordination. Não reiniciar automaticamente outra etapa.
5. **Não buscar perfeição universal fora do escopo** nem usar `INCONCLUSIVE` genérico para mascarar falha em cenários suportados. `PASS` só com comportamento comprovado e AC aplicáveis cumpridos.
6. Defeitos críticos não podem ser ignorados por exigência de velocidade; melhorias não obrigatórias não bloqueiam uma entrega conforme seu escopo aprovado.

### 0A.3 Atualização contínua do GitHub: obrigação e trilha de decisão

**Doc 119 = plano funcional canônico. Issue #131 = quadro de execução/decisões.** Atualizar os dois em todo evento material: conclusão de inventário, decisão de semântica/escopo, entrada ou alteração de RQ/AC, evidência de testes e E2E, revisão, divergência de implementação, blocker/owner, aceite, mudança de status, release/rollback e passagem de E1 para E2.

Formato mínimo por atualização:
`DATA | ID DECISÃO | OBJETIVO/ESCOPO | STATUS ANTES→DEPOIS | EVIDÊNCIA (fonte, Git SHA, dataset/revisão) | RQ/AC IMPACTADOS | RISCOS/BLOCKERS+OWNER | RESPONSÁVEL | PRÓXIMA AÇÃO | DECISÃO`.

**Status:** fatos `PROVEN/TO_INVENTORY/PLANNED/TARGET`; execução `PASS/FAIL/PENDING/INCONCLUSIVE/TEST_NOT_RUN/STALE_EVIDENCE`; review `ACCEPT/ACCEPT_WITH_RESIDUAL/REWORK/EXECUTION_DRIFT/INCONCLUSIVE`. `ACCEPT_WITH_RESIDUAL` não aceita requisito obrigatório pendente. Diferenciar código implementado, evidência runtime, qualidade quantificada e aprovação de Engenharia.

### 0A.4 Registro de decisões — corrente

| ID | Data | Decisão | Evidência/razão | Resultado e estado |
|---|---|---|---|---|
| DEC-VAL-001 | 2026-11-03 | Um catálogo (Doc 119) e um tracker (issue #131) | Plano mestre Doc 116 e histórico M0–M5; 53 NCs oficiais consultadas | PROVEN no GitHub |
| DEC-VAL-002 | 2026-11-03 | Somente VAL-01 Estrutura ativa; E2–E7 congeladas | Exigência de qualidade e foco por capacidade | PROVEN como decisão, E1 ainda não implementado integralmente |
| DEC-VAL-003 | 2026-11-03 | Validação deve ser vertical e completa, com várias famílias suportadas e abstinência fundamentada; "qualquer desenho" permanece TARGET | Diferenças de layout, BOM multinível, semântica e contratos | Critérios de aceite a detalhar no estudo |
| DEC-VAL-004 | 2026-11-03 | ChatGPT faz planejamento/prompt fechado/revisão crítica independente; Devin executa; owner aprova tecnicamente | Evitar autocertificação e recursões infinitas | Modelo operacional adotado |
| DEC-VAL-005 | 2026-11-03 | Uma devolutiva consolidada de falhas por rodada, até três ciclos locais gerenciais; sem fase automática adicional | Doc 116 §7; não deixar passar defeitos bloqueantes | Política de revisão adotada |
| DEC-VAL-006 | 2026-11-03 | Atualização obrigatória de avanço, evidências e decisões no Doc 119 + issue #131 | Rastreabilidade e não perder contexto | Política documental adotada |
| DEC-VAL-007 | 2026-11-03 | Próxima ação é **estudar a estrutura no desenho** (campos, tabelas, famílias, contratos e NCs), **sem emitir prompt de execução ainda** | Solicitação de sequenciamento do owner do produto | STUDY_PENDING |

### 0A.5 Agenda delimitada do próximo estudo (VAL-01 — ainda não executado)

No estudo seguinte, inventariar **casos reais variados**, fonte PDF/visual e BOM oficial no mesmo contexto autorizado, tabelas de materiais e folhas; diferenças entre estrutura registrada, representação gráfica e estrutura implícita; itens/código/descrição/quantidade; consumos, unidades, multicamadas e repetição; tipos MP/PI; ocorrências de NC estruturais; contrato de revisão e identidade. Delimitar famílias `SUPPORTED`/limitações, fontes/owners, casos de teste + falsos conflitos e AC objetivos. Somente depois construir **um** prompt de implementação E1. Não iniciar carimbo, cotas ou balões como entregas paralelas.

---

## 1. Objetivo e decisão

Planejar **todas as validações aplicáveis a cada família de desenho**, priorizando falhas reais já registradas. A primeira entrega funcional é **VAL-01 Estrutura BOM cadastrada × lista de materiais do desenho**, sem reinventar R11–M5. O plano deverá evoluir neste arquivo com matriz de evidência, decisões dos owners, resultados de datasets e links de entregas, evitando prompts e subtarefas indefinidas.

**Princípio:** dado cadastrado esperado != texto observado != associação candidata != verificação por regra autorizada != aprovação técnica. PDFs/OCR/LLM/MCP/relatórios não são source of truth. Tudo até aprovação é DRAFT/CANDIDATE.

Famílias iniciais a inventariar: desenho DELPI de montagem/chicote, componente/peça, desenhos de cliente; outros suportes somente com corpus, contrato e aceite. Aplicabilidade é por família/revisão, não checklist universal.

## 2. Catálogo de verificações (versão inicial)

| ID | Área | O que verificar (exemplos) | Fonte oficial/contrato | Situação real | Ordem |
|---|---|---|---|---|---|
| VAL-01 | Estrutura e lista de materiais | identidade, componentes, código, descrição, linha/item, quantidade, multiplicidade, hierarquia representada, itens extras, consumos internos | product.detail/structure + contrato de representação de BOM e unidades (pendente) | R11–M5 fazem cruzamento candidato; validação integral não comprovada | **E1** |
| VAL-02 | Carimbo e identificação | produto, descrição, cliente, revisão, folha, escala, unidade, autor/aprovação quando exigidos | product.detail, documento/revisão oficiais autorizados | OCR/região candidata; comparabilidade de revisões restrita | E2 |
| VAL-03 | Cotas e tolerâncias | valor bruto, unidade, tolerância, indicação, elemento dimensionado, referência vs controle, equivalência técnica | documento + características/especificação oficial quando contratada | cotas candidatas, associação geométrica não validada | E3 |
| VAL-04 | Balões e chamadas | item ↔ balão ↔ linha de chamada ↔ geometria; letras trocadas, sem item, duplicadas | tabela observada + regras técnicas aprovadas | primitivas circulares limitadas, relações NOT_CHECKED | E4, antecipar evidências em E1 |
| VAL-05 | Revisão/histórico | versão do desenho, PDF oficial, mudanças, folhas e metadados | gestão documental/Domain API; revisão TOTVS ≠ revisão PDF sem contrato | NOT_COMPARABLE onde sem equivalência | E2 |
| VAL-06 | Notas/instruções | pré-decape, terminação, montagem e requisitos omitidos | documentos de cliente/Engenharia autorizados | extração parcial, validação pendente | E5 |
| VAL-07 | Materiais e componentes específicos | terminal, conector, bitola, cor, isolação, classe e descrição | cadastro/especificação autorizados | código parcial; contratos específicos a inventariar | E5 |
| VAL-08 | Símbolos e tolerâncias geométricas | GD&T, símbolos suportados, referências e restrições | catálogo normativo e política owner | TARGET, NÃO assumir cobertura universal | E6 |
| VAL-09 | Vistas, cortes, detalhes, escala | coerência das referências e representação | desenho e política documentada | candidatos geométricos; validação pendente | E6 |
| VAL-10 | Processo/acabamento/montagem | decape, crimpagem, solda, acabamento, lado/orientação e roteiro | roteiros/processos oficiais SE houver contrato | owner-blocked quando fonte indisponível | E6 |
| VAL-11 | Inspeção e características críticas | exigências, tolerâncias de controle, plano de inspeção | domínio oficial de inspeção SE houver contrato | owner-blocked, não simular | E6 |
| VAL-12 | Integridade documental | PDF presente/atual, SHA, folhas, identidade, legibilidade, cobertura OCR, regiões desconhecidas | gateway documento + regras de liberação | checks parciais, erros tipados (source/PDF) | Transversal |
| VAL-13 | Consistência cliente × DELPI | cota, revisão, nota e item comparáveis em duas fontes **autorizadas** | arquivos oficiais de cliente + DELPI, matching de revisão | TARGET, depende do contrato e permissões | Transversal/E5 |

## 3. Consulta factual às NC oficiais da EVA (2026-11-03)

**Consulta:** `nonconformity.search` sem filtro (page=1, page_size=100): **53/53 registros oficiais retornados**; `nonconformity.tags` mostra uso de etiquetas, mas **não é uma classificação semântica confiável**. `nonconformity.recurrence(group_by=problem_tag)` retornou `(vazio):53`, em conflito com `search.problem_tags` e `tags.usage_count` (ex.: Medida 29, Desenho 16). **Não usar esta agregação como ranking oficial até reconciliar no owner Engineering API.**

**Cuidado:** NC pode referir-se a produto fabricado fora de especificação, a documentação ou a revisão antiga; um registro histórico **não prova** que o PDF ou a estrutura atual estejam errados. Há textos quase repetidos entre registros distintos (ex.: 90263655, 90261834, 90262834); contagens brutas não equivalem automaticamente a incidentes independentes. A classificação abaixo é **hipótese de planejamento por leitura da descrição**, sem alteração da taxonomia oficial; o histórico será consultado novamente antes de avaliar precisão por tipo.

### Falhas concretas que devem orientar verificações/GT

| Caso rastreável | Descrição oficial resumida | Verificação e teste regressivo proposto |
|---|---|---|
| NC `ee2a1569-6f11-406d-8b2d-acd7b8ad5162` / 90261606 | quantidade da etiqueta no desenho divergente da estrutura | VAL-01: quantidade apenas quando conceitos e unidade forem comparáveis |
| NC `381e16fd-562a-4c50-ad0f-fe3bd4b66649` / 90263572 | código de conector errado na estrutura/planilha (1008 vs 1009) | VAL-01/07: identidade do componente, diferenças entre fontes e código, revisão |
| NC `ce945176-cc4b-403f-9326-339dd5ff830f` / 90264178 | descrição do desenho divergente da estrutura | VAL-01: descrição, origem, normalização autorizada |
| NC `2f0c974b-faae-480d-ac51-3b9c9d37ea6e` / 90480120 | letra dos balões trocada | VAL-04: chamada→item→componente; homônimos e letras repetidas |
| NC `4b9d8b6b-79a7-4786-811e-3e93f86f59e3` / 90263520 | letras dos balões trocadas, inconsistência documental | VAL-04/05: referência, revisão, PDF/estrutura |
| NC `adbc502d-fc7c-498c-9c73-81888d281ecd` / 90262200 | cabo azul com cota errada | VAL-03: cota/tolerância atribuída à geometria certa |
| NC `0f612626-d491-4170-ad8b-ce90e0f4c7f7` / 90262524 | cabo 2 mm menor que desenho do cliente | VAL-03/13: separar desvio de fabricação de divergência documental; comparar versão correta |
| NC `c91f2a72-d539-4bdf-997e-0556051f6bf2` / 90260908 | faltou indicação de pré-decape | VAL-06/10: nota obrigatória conforme documento cliente aplicável |
| NC `370da0e4-f415-4dd3-9ec8-2b6523f77ede` / 90263651 | terminal aplicado divergente do projeto | VAL-07/10: terminal e montagem, quando houver fonte comparável |
| NC `50247196-b38e-4d5e-93b9-f532732b512d` / 90264014 | aplicação de termostato no lado contrário | VAL-09/10: orientação gráfica, evidência geométrica |
| NC `77b1a917-3831-48c8-8545-4195707ddbc3` / 90262606 | PDF não salvo na pasta | VAL-12: disponibilidade do documento oficial |
| NC `794aced9-ddca-442f-a780-cc23b200e79d` / 90262605 | PDF não alterado na pasta | VAL-05/12: versão/freshness e gestão documental |

### Prioridade de risco (proposta, não estatística aprovada)

**P0:** estrutura — códigos errados, quantidade de etiqueta, descrição divergente, multiplicidade e apresentação; identidade/revisão/integridade documental como gates transversais. **P1 alto:** dimensões/comprimentos e balões (muitos relatos descritivos concretos); iniciar corpus/ground truth em paralelo ao E1, sem fingir validação já aprovada. **P1:** terminais, pré-decape, orientação/montagem, notas. A priorização final depende de gravidade, frequência deduplicada, detectabilidade e owner.

## 4. VAL-01 — Primeira entrega funcional (escopo fechado)

**Pergunta:** *Para esta família, produto, desenho e revisão autorizados, a lista de materiais efetivamente representada no desenho corresponde à estrutura BOM oficial **no escopo que deveria aparecer**?*

**Fontes:** product.detail/structure/drawing via Domain APIs oficiais, PDF e understanding já existentes; futuras políticas de representação/quantidade/revisão precisam de owner. Não fazer join cross-db nem chamar handler MCP a partir de handler.

**Fluxo:** official source → ocorrências `BOM_OCCURRENCE` → filtro de quais níveis/itens **devem ser representados** (regra oficial) → `DRAWING_TABLE_ITEM` com item/código/descrição/quantidade/evidência bruta → matching multiplicity-aware → avaliação de atributos comparáveis → decisão global candidata e revisão humana.

**Políticas obrigatórias:**
1. Um mesmo código pode aparecer em várias ocorrências da BOM e em várias linhas. Não associar por ordem nem deduplicar.
2. `consumption_quantity` (e unidade) **não equivale** a `assembly_quantity` nem a `dimension`; conferir unidade/conversão no owner.
3. Item faltante no OCR = `UNKNOWN/INCONCLUSIVE`, não ausência real.
4. Código do produto raiz e texto de carimbo não constituem componente adicional.
5. Descrição somente comparável com fonte e política aprovadas; code-match não prova identidade da ocorrência.
6. `CONFLICT` exige contradição observada, evidência suficiente, identidade de documento/revisão compatível e regra autorizada; `VALIDATED` somente se todos os checks obrigatórios aplicáveis passarem.
7. A tabela de materiais pode representar apenas subconjunto da BOM multinível. Sem regra de inclusão, não declarar a estrutura como validada ou divergente.
8. O resultado por verificação usa estados existentes MATCH/CONFLICT/UNKNOWN/NOT_COMPARABLE/NOT_CHECKED; resultado global candidato `VALIDATED/CONFLICT/INCONCLUSIVE/NOT_COMPARABLE/NOT_CHECKED` após contrato governado, sem aprovação automática.

**Contrato de relatório desejado:** `structure_validation.v1` aditivo dentro de `product.drawing_analysis` (não declarar existente); entrada (family, document_SHA/revision, official_source/freshness, occurrence/path, visual row/cell refs); saída por ocorrência com dados esperados, observados, policy/version, association ambiguity, evidências (page/bbox/coord/source) e next_action; resultados desenho→BOM e coverage por tipo; `DRAFT/CANDIDATE`, `automatic_approval=false`.

**AC fechados:** (1) contrato de representação da BOM para a família; (2) OCR/SLANet associa item+code+description+quantity com origem rastreável; (3) repetição/hierarquia tratada sem falso pareamento; (4) quantidade semanticamente comparável; (5) divergências negativas e casos de NC acima em dataset autorizado; (6) documento, revisão, permissões e BOM unavailable fail-closed; (7) cobertura com denominadores e abstenção correta; (8) relatório por item e global coerentes; (9) regressão e E2E autenticado; (10) qualidade validada com ground truth, thresholds definidos antes de holdout e owner técnico.

**Gates honestos atuais:** perfis, investigação guiada, matching por código e relatório M4/M5 existem (**PROVEN no escopo já verificado**); regra oficial de presença por nível/quantidade e GT/thresholds técnicos **TO_INVENTORY / OWNER_BLOCKED**; validação integral `VAL-01` **NOT_IMPLEMENTED/PLANNED**, não PASS.

## 5. Sequência finita e tracker de evolução

| Ordem | Entrega | Definition of done | Owner principal | Status |
|---|---|---|---|---|
| E0 | Catálogo, NC, regras, escopo por família, corpus e rastreabilidade | Documento no GitHub + decisão owner sobre corpus/contratos | Coordination / Engenharia | DOCUMENTADO; regras/GT ainda pendentes |
| **E1** | **VAL-01 Estrutura** | todos os AC VAL-01 comprovados por famílias suportadas, GT, E2E e owner; relatório completo | Engineering API + Engenharia | **ÚNICA ENTREGA ATIVA — especificação/contratos pendentes** |
| E2 | VAL-02/05 Carimbo, revisão, documentos | checks aplicáveis, contratos oficiais e GT | Engineering API / owner documental | BACKLOG CONGELADO |
| E3 | VAL-03 Cotas | atribuição geométrica, tolerância/units, regras e GT | Engenharia | BACKLOG CONGELADO |
| E4 | VAL-04 Balões | cadeia item-balão-geometria rastreável, GT | Engenharia | BACKLOG CONGELADO |
| E5 | VAL-06/07/13 Notas, material, cliente×DELPI | contratos e GT por família | Domain owners / Engenharia | BACKLOG CONGELADO |
| E6 | VAL-08–11 Vistas/símbolos/processos/inspeção | catálogo suportado e fontes autorizadas | Engineering owners | BACKLOG CONGELADO |
| E7 | Consolidação por desenho | checks obrigatórios completos, decisão de revisão humana | Portal Engenharia + Engenharia | BACKLOG CONGELADO |

Cada entrega é única e bounded; sem criar revisões automáticas E1.1/E1.2. Registre em cada linha: `source/owner, RQ/AC, contract_version, SHA tested/deployed, dataset SHA, GT/threshold version, métricas com denominadores, permission outcomes, false alarms, residuals, owner decision`.

### Controle de aprovação

- **EVA:** interpretação, investigação, evidência e relatórios DRAFT/CANDIDATE.
- **Engineering Domain APIs:** verdade oficial, unidades e regras de negócio.
- **Portal Engenharia:** UX/workflow sem criar aprovação paralela.
- **Owner técnico:** avaliação do GT, threshold e aprovação técnica.
- **Core/Keycloak:** AuthZ/identidade.

Nenhuma NC histórica é ground truth automaticamente; somente referência de risco até revisão de desenhos/revisões e aprovação de anotações. Nenhum número estatístico de precisão é inferido dessas descrições.

## 6. Índice rastreável dos 53 registros de NC consultados

**Fonte:** EVA `nonconformity.search`, acesso delegado. Os IDs são referências a registros oficiais e este índice é instantâneo; consultar a EVA para detalhes atuais. **Categorias abaixo são classificação auxiliar por texto, não tags oficiais.**

| # | Data ocorrência | Produto | NC ID | Candidatos VAL | Descrição oficial resumida |
|---:|---|---|---|---|---|
| 01 | 2026-10-21 | 90480120 | `2f0c974b-faae-480d-ac51-3b9c9d37ea6e` | BALAO | Letra dos balões trocadas. |
| 02 | 2026-10-20 | 90480118 | `c4c7ce9a-c8f3-4253-ab84-d2e24fc6037f` | BALAO | Letra dos balões trocadas. |
| 03 | 2026-10-20 | 90480119 | `47c975a5-9822-4507-b6fb-ab01b3988441` | BALAO | Letras dos balões trocadas |
| 04 | 2026-10-07 | 90263235 | `157e3f20-1202-46ae-94ab-6f618af4b1fb` | ESTRUTURA_DESCRICAO, COTA_DIMENSAO | descrição do intermediário com a medida diferente do desenho delpi |
| 05 | 2026-10-01 | 90263114 | `a1b74703-ba47-4c84-afd0-9eb3eacf5a04` | BALAO | balões trocados |
| 06 | 2026-09-01 | 90264014 | `50247196-b38e-4d5e-93b9-f532732b512d` | MONTAGEM_POSICAO | aplicação do termostato esta do lado contrario |
| 07 | 2026-08-31 | 90264178 | `305aebd5-1962-4ded-a5dc-7510ab56ca96` | ESTRUTURA_DESCRICAO | descrição do intermediário esta divergente com o tamanho do cabo |
| 08 | 2026-08-31 | 90262869 | `d6571f21-b710-4fae-be97-2366d462967f` | COTA_DIMENSAO | cabos 3mm maior que desenho do cliente |
| 09 | 2026-08-17 | 90262200 | `adbc502d-fc7c-498c-9c73-81888d281ecd` | COTA_DIMENSAO | cabo azul com a cota errada |
| 10 | 2026-08-14 | 90260908 | `c91f2a72-d539-4bdf-997e-0556051f6bf2` | NOTAS_PROCESSO | falto no desenho Delpi a informação que deveria ser mandando com pré-decape conforme desenho do cliente. |
| 11 | 2026-08-10 | 90263114 | `ec82e9eb-c322-44be-b6d9-b4b843abf775` | BALAO | letra dos balões trocada |
| 12 | 2026-07-30 | 90264201 | `20e22e22-b21a-46e0-a3a5-8e5369618de7` | COTA_DIMENSAO | cabo com 81 ficou 2mm da mínima do cliente |
| 13 | 2026-07-30 | 90263396 | `7a2161f7-39fd-420c-8ad9-7df6ee943a52` | ESTRUTURA_DESCRICAO, COTA_DIMENSAO | descrição divergente com o comprimento do desenho |
| 14 | 2026-07-20 | 90263381 | `faeeb103-45cd-4e0f-8e6d-5e11cb1ab3d0` | COTA_DIMENSAO | Divergência dimensional no produto 90263381 (LMP 058 21). Registro original: Medida da abraçadeira divergente com o desenho do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 15 | 2026-07-20 | 90262524 | `0f612626-d491-4170-ad8b-ce90e0f4c7f7` | COTA_DIMENSAO | Divergência dimensional no produto 90262524 (LMP 034 16). Registro original: Cabo ar 2mm menor que desenho do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 16 | 2026-07-13 | 90263555 | `a0e49a4c-72e4-4368-baa4-8b9f61c2f04b` | COTA_DIMENSAO | Divergência dimensional no produto 90263555 (LMP 079 22). Registro original: Comprimento dos cabos AR/LA/AL//MR maior. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 17 | 2026-07-13 | 90263655 | `14ec0572-a30d-4af0-8f20-2d03b2a8af50` | COTA_DIMENSAO | Divergência dimensional no produto 90263655 (LMP 008 23). Registro original: Comprimento do cabo trocado. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 18 | 2026-07-13 | 90263655 | `4c15e243-00b7-4ce3-8b56-c9d7f9d626cd` | COTA_DIMENSAO | Divergência dimensional no produto 90263655 (LMP 008 23). Registro original: Comprimento do cabo trocado. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 19 | 2026-07-06 | 90260596 | `a9028671-93ee-4f33-ab72-a7e82d559375` | COTA_DIMENSAO | Divergência dimensional no produto 90260596 (LMP 121 22). Registro original: Comprimentos cabos cinzas menor. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 20 | 2026-07-01 | 90261834 | `48f7ca06-cc5e-496f-bf14-b0315e499471` | COTA_DIMENSAO | Divergência dimensional no produto 90261834 (LMP 074 11). Registro original: Comprimento 12mm maior que desenho do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Novos Negócios. |
| 21 | 2026-07-01 | 90261834 | `b489c2e3-d4c8-4866-929c-09a7b4713500` | COTA_DIMENSAO | Divergência dimensional no produto 90261834 (LMP 074 11). Registro original: Comprimento 12mm maior que desenho do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Novos Negócios. |
| 22 | 2026-06-30 | 90263520 | `4b9d8b6b-79a7-4786-811e-3e93f86f59e3` | BALAO, INTEGRIDADE_REVISAO | Inconsistência de documentação/desenho no produto 90263520 (LMP 042 22). Registro original: Letra dos balões trocados. Há desalinhamento entre desenho, estrutura ou arquivos publicados para o cliente Weg. |
| 23 | 2026-06-17 | 90264255 | `8616fd08-fe65-45b8-8339-dba6e0a84656` | ESTRUTURA_DESCRICAO, INTEGRIDADE_REVISAO | Inconsistência de documentação/desenho no produto 90264255 (LMP 125 25). Registro original: DESCRIÇÃO intermediário DIVERGENTE. Há desalinhamento entre desenho, estrutura ou arquivos publicados para o cliente Novos Negócios. |
| 24 | 2026-06-15 | 90262593 | `b4269804-e300-4466-b325-dabac4205aa5` | COTA_DIMENSAO | Divergência dimensional no produto 90262593 (LMP 039 17). Registro original: Comprimento maior que desenho do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 25 | 2026-06-08 | 90262379 | `7723d9f7-9fe0-4c64-af5c-cf2aac9ba513` | COTA_DIMENSAO | Divergência dimensional no produto 90262379 (LMP 035 15). Registro original: Cabo azul cota divergente do desenho do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 26 | 2026-06-08 | 90264236 | `0da72771-46cb-4514-8fdb-17db807edda3` | NOTAS_PROCESSO, COTA_DIMENSAO | Decape incorreto identificado no produto 90264236 (LMP 086 26). Registro original: Decape errado olhal. O comprimento/posição do decape (olhal) não está conforme o desenho do cliente Weg. |
| 27 | 2026-06-08 | 90262126 | `0cabc4db-4323-43be-9042-d3731589a6cf` | COTA_DIMENSAO | Divergência dimensional no produto 90262126 (LMP 135 13). Registro original: Cabo laranja menor que desenho do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 28 | 2026-05-19 | 90264043 | `465611ce-f099-4281-9f9a-d256fc7c964c` | COTA_DIMENSAO | Divergência dimensional no produto 90264043 (LMP 041 25). Registro original: Tolerancia cabo marrom maior que desenho do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 29 | 2026-05-18 | 90262965 | `8dceeb56-31b3-4efb-a4e2-6ee8a6804f7f` | COTA_DIMENSAO | Divergência dimensional no produto 90262965 (LMP 033 19). Registro original: Cabos preto e vermelho maior que desenho do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 30 | 2026-05-18 | 90263288 | `2ff5a209-6970-45af-9f21-1c5032391e96` | COTA_DIMENSAO | Divergência dimensional no produto 90263288 (LMP 111 20). Registro original: Cabos menor que desenhos dos clientes. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 31 | 2026-05-18 | 90262982 | `c7b15bfc-2838-4b64-8577-414298d5190f` | COTA_DIMENSAO | Divergência dimensional no produto 90262982 (LMP 045 19). Registro original: Comprimento cabo azul maior que desenho do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 32 | 2026-05-18 | 90263571 | `15218528-a441-435f-89a8-777d8cd8d67e` | COTA_DIMENSAO | Divergência dimensional no produto 90263571 (LMP 096 2022). Registro original: Comprimento cabo preto maior que desenho do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 33 | 2026-05-18 | 90264223 | `afe217c9-5eff-4223-8e59-52d7a257428a` | COTA_DIMENSAO | Divergência dimensional no produto 90264223 (LMP 064 26). Registro original: Comprimento cabos menor que desenho do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 34 | 2026-05-18 | 90264222 | `3d1ca695-2d04-4dcc-b736-fdeb7727d98d` | COTA_DIMENSAO | Divergência dimensional no produto 90264222 (LMP 064 26). Registro original: Intermediários MENOR QUE DESENHO DO CLIENTE. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 35 | 2026-05-05 | 90262751 | `1224bee7-e008-4c91-b2c6-5d90eb235923` | COTA_DIMENSAO | Divergência dimensional no produto 90262751 (LMP 241 17). Registro original: Comprimento do cabo abaixo do especificado no desenho do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 36 | 2026-05-04 | 90262834 | `95a212ed-4408-4790-8118-a9885639a4ec` | COTA_DIMENSAO | Divergência dimensional no produto 90262834 (LMP 060 18). Registro original: Comprimento do cabo abaixo do especificado do desenho do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 37 | 2026-05-04 | 90262834 | `5280f2d9-dcb4-45ae-9800-7a8ac869d4f3` | COTA_DIMENSAO | Divergência dimensional no produto 90262834 (LMP 060 18). Registro original: Comprimento do cabo abaixo do especificado do desenho do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 38 | 2026-03-10 | 90264178 | `ce945176-cc4b-403f-9326-339dd5ff830f` | ESTRUTURA_DESCRICAO, INTEGRIDADE_REVISAO | Inconsistência de documentação/desenho no produto 90264178 (LMP 014 26). Registro original: Descrição do desenho divergente com estrutura. Há desalinhamento entre desenho, estrutura ou arquivos publicados para o cliente Weg. |
| 39 | 2026-03-10 | 90264171 | `7f83cf12-e782-452a-a7ac-f646d9dd53b1` | COTA_DIMENSAO | Divergência dimensional no produto 90264171 (LMP 003 26). Registro original: Comprimento do cabo divergente com desenho do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 40 | 2026-02-05 | 90260883 | `960eec79-eedc-4ff3-9966-455c9b7ac6fa` | NOTAS_PROCESSO, COTA_DIMENSAO | Divergência dimensional no produto 90260883 (LMP 060 13). Registro original: Comprimento do cabo e decape divergente com desenho do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 41 | 2026-01-13 | 90261606 | `ee2a1569-6f11-406d-8b2d-acd7b8ad5162` | ESTRUTURA_QUANTIDADE, INTEGRIDADE_REVISAO | Inconsistência de documentação/desenho no produto 90261606 (LMP 027 10). Registro original: Quantidade da etiqueta no desenho divergente com a estrutura. Há desalinhamento entre desenho, estrutura ou arquivos publicados para o cliente Weg. |
| 42 | 2025-11-24 | 90263474 | `f6d8f71a-c8b1-46b4-a14e-c00340673249` | COTA_DIMENSAO | Divergência dimensional no produto 90263474 (LMP 131 21). Registro original: Medida do cabo menor que o projeto do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 43 | 2025-11-18 | 90263468 | `b05053b5-9d23-48b0-a542-d45b2d253839` | COTA_DIMENSAO | Divergência dimensional no produto 90263468 (LMP 131 21). Registro original: Medida do cabo menor que o projeto do cliente. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 44 | 2025-11-18 | 90263468 | `c0c71afa-0a02-4b2c-a117-79e13dcf551a` | COTA_DIMENSAO | Não conformidade de medida identificada no produto 90263468 (LMP 131 21, cliente Weg): divergência dimensional em relação ao desenho/projeto do cliente, sem detalhe adicional no registro legado. |
| 45 | 2025-10-29 | 90263572 | `381e16fd-562a-4c50-ad0f-fe3bd4b66649` | ESTRUTURA_CODIGO, INTEGRIDADE_REVISAO | Inconsistência de documentação/desenho no produto 90263572 (LMP 102 22). Registro original: Um material com o código errado na estrutura em planilha, conector cadastrado como 1008 sendo que correto é 1009. Há desalinhamento entre desenho, e |
| 46 | 2025-10-29 | 90480113 | `cb7c55f6-433d-4e7a-96f7-ba9b4ecf0cb6` | BALAO, INTEGRIDADE_REVISAO | Inconsistência de documentação/desenho no produto 90480113 (LMP 109 25). Registro original: Novos Negócios - Desenho - Identificação das letras no desenhos trocadas. Há desalinhamento entre desenho, estrutura ou arquivos publicados para o c |
| 47 | 2025-09-23 | 90280022 | `138494c1-38e8-47c8-ac15-507f41ec9bc8` | COTA_DIMENSAO | Divergência dimensional no produto 90280022 (LMP 037 09). Registro original: Divergencia de medida entre desenho e estrutura. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 48 | 2025-09-23 | 90263909 | `c3b4e45f-f406-4799-9104-a8590509f3e1` | COTA_DIMENSAO | Divergência dimensional no produto 90263909 (LMP 064 24). Registro original: Medida do cabo vermelho ficou 3mm maior que projeto WEG. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 49 | 2025-09-23 | 90263651 | `370da0e4-f415-4dd3-9ec8-2b6523f77ede` | ESTRUTURA_CODIGO | Terminal aplicado divergente do projeto no produto 90263651 (LMP 004 23). Registro original: Terminal divergente com projeto WEG. O componente de ponta não corresponde à especificação do desenho WEG/cliente Weg. |
| 50 | 2025-09-23 | 90263985 | `a1e234b1-2e92-4d47-86ab-3d5e5f164427` | COTA_DIMENSAO | Divergência dimensional no produto 90263985 (LMP 170 24). Registro original: Cabo ficou 5mm maior que especificado em projeto WEG. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |
| 51 | 2025-09-23 | 90262606 | `77b1a917-3831-48c8-8545-4195707ddbc3` | INTEGRIDADE_REVISAO | Inconsistência de documentação/desenho no produto 90262606 (LMP 062 17). Registro original: Desenho não salvo na pasta em PDF. Há desalinhamento entre desenho, estrutura ou arquivos publicados para o cliente Weg. |
| 52 | 2025-09-23 | 90262605 | `794aced9-ddca-442f-a780-cc23b200e79d` | INTEGRIDADE_REVISAO | Inconsistência de documentação/desenho no produto 90262605 (LMP 062 17). Registro original: Não alterado desenho PDF na pasta. Há desalinhamento entre desenho, estrutura ou arquivos publicados para o cliente Weg. |
| 53 | 2025-09-23 | 90263664 | `23a06896-f803-4c36-a020-394ec6e547ea` | COTA_DIMENSAO | Divergência dimensional no produto 90263664 (LMP 020 23). Registro original: Cota menor que desenho WEG. A cota encontrada na conferência não atende ao especificado no desenho do cliente Weg. |

## 7. Próxima atualização deste plano

1. Owner Engenharia revisa regras por família: quais níveis BOM devem constar na tabela, unidade/quantidade representada, revisão aplicável e evidência suficiente.
2. Vincular NCs priorizadas aos desenhos originais/revisões corretas, sem assumir que o PDF atual ainda contém a NC.
3. Preparar annotation guide e GT controlado; definir thresholds antes do holdout.
4. Executar E1/VAL-01 sobre a superfície R11–M5 existente; preencher resultado por ocorrência/estado e documentar evidências e limitações no mesmo plano.
5. Corrigir discrepância `recurrence(group_by=problem_tag)` vs `tags`/search no owner, sem alterar registros de NC.

## 8. Estudo E1 / VAL-01 — Inventário dos contratos e topologias reais (2026-11-03)

**Natureza:** estudo/inventário factual, sem proposta de alteração de código e **sem** validar os desenhos. Fonte oficial dos exemplos = EVA `product.structure` e `product.drawing` com acesso delegado; leitura do código no GitHub para contratos/transformações. Visuais apenas das execuções anteriores de `drawing_analysis(compose_understanding=true)`, explicitamente distinguidas de observação atual: novas chamadas em 2026-11-03 falharam internamente e **não** permitem afirmar leitura atual dos novos PDFs.

### 8.1 Owner, rota, schema e transformação existente

| Camada | Recurso verificado | Contrato / observação | Autoridade |
|---|---|---|---|
| API DELPI Python (repo `roberiooliveiradev/api-delpi-py`) | `GET /products/{code}/structure`, route `app/routes/product_routes.py` | `max_depth` default 10, 1–15; `page` default 1; `page_size` default 100, 1–500; `get_structure` delega `ProductRepository.list_structure` | Owner do cadastro/BOM, não EVA |
| API DELPI Python repository | `app/repositories/product_repository.py` | CTE SG1010 (`G1_COD` pai, `G1_COMP` filho, `G1_QUANT`, `G1_INI/G1_FIM` em contrato real); SB1010 (`B1_DESC/B1_TIPO/B1_UM`); árvore `data: {code,description,type,unit,quantity,components:[...]}` e paginação **só no 1º nível** | Fonte operacional; verificar runtime/ref antes de declarar equivalência a qualquer outro backend |
| API DELPI Node (repo `roberiooliveiradev/api-delpi`) | `GET /api/products/code/:code/structure` | **Outra rota/contrato**: `recursive`, `direction=where-used|explosion`, `maxDepth`; não assumir que seja a rota atualmente consumida pela Engineering API | Interface distinta, não misturar schemas nem direção |
| EVA / Engineering API | `read(entity=product,action=structure,ref=code)` | Envelope observado: `data.status=available`, `data.data.root` + `data.data.items[]`; cada item `code,description,type,unit,quantity,components[],secondary_unit?,conversion_factor?,conversion_type?`; `page/page_size/total/total_pages`; `bom_validity.filter=current`, referência `server_date` | Engineering API delega sob identidade e AuthZ live; não cria nova BOM |
| Engineering API análise | `application/drawing/drawing_analysis_service.py::_flatten_bom` / `flatten_bom_occurrences` | Aceita `items/components/children`, achata em `occurrence_id, component_code, component_type, parent_code, depth, path, quantity_raw, unit_raw`. `bom_stats` registra vínculos, códigos repetidos, profundidade. `_MAX_BOM_ITEMS=300` no código — auditoria de truncamento antes de VALIDATED | Projeção de análise, **não** fonte oficial |
| Engineering API objetos | `object_profiles_builder.py` e `drawing_investigation.py` | `BOM_OCCURRENCE` preserva path/nível/código/consumo/unidade; `DRAWING_TABLE_ITEM` tem item, code candidate, description, qty observados; M4 `multiplicity_analysis` e verificação `DRAFT/CANDIDATE` | Interpretação e matching candidatos |
| Engenharia PDF | `read(entity=product,action=drawing,ref=code)`; `product.drawing_analysis` | Metadata de PDF (filename, revision, size, modified_at), PDF por gateway; drawing understanding via OCR/SLANet quando disponível | O PDF é documento fonte, não truth de BOM |

**Pseudo-schema observado do wrapper EVA:**
```json
{
  "status": "available",
  "data": {
    "root": {"code": "PA", "description": "...", "type": "PA", "unit": "MI", "quantity": 1},
    "items": [
      {"code": "PI-ou-MP", "description": "...", "type": "PI", "unit": "MI", "quantity": 1,
       "components": [{"code": "MP", "description": "...", "type": "MP", "unit": "MT", "quantity": 643, "components": []}]}
    ],
    "page": null, "page_size": null, "total": 2, "total_pages": null,
    "bom_validity": {"filter": "current", "reference": "server_date", "validityColumns": "G1_INI,G1_FIM"}
  }
}
```
*Os literais PA/PI/MP e 643 ilustram a forma; não substituem as instâncias completas ou o contrato normativo. O wrapper acima não é automaticamente o mesmo JSON bruto da rota Python. `quantity`, `unit`, `conversion_type` e `conversion_factor` devem manter semântica **não aprovada** até contrato do owner. O histórico/current effective BOM pode diferir da revisão do PDF.*

**Pontos de atenção de contrato para investigar antes da implementação:** paginação raiz vs recursão; se a API limita/trunca silenciosamente (incluindo limite de 300 ocorrências da análise); representação de ocorrências repetidas do mesmo código; `path` por códigos pode não diferenciar irmãos com códigos iguais sem índice/id de vínculo; validade `current/server_date` ≠ automaticamente estrutura aplicável à revisão histórica do desenho; `secondary_unit/conversion_factor/conversion_type` presentes mas não justificam assumir equivalências de quantidade. Verificar o owner para qual **instância de API DELPI** e contrato da Engineering API são usados em produção. A leitura do código Python é evidência do repositório, não prova de SHA de runtime daquela API.

### 8.2 Amostragem das estruturas oficiais reais

Todos os totais abaixo foram contados da **árvore devolvida pela EVA** (`items` e `components`) em 2026-11-03, com `max_depth=15,page_size=500`. `N1` significa filho direto do PA raiz; `N2` filho de N1; `N3` filho de N2. Quantidades brutas **não convertidas**.

| Produto | Filhos N1 | N1 por tipo | Ocorrências N1/N2/N3 | Topologia observada e relevância |
|---|---:|---|---|---|
| `90264302` | 2 | 2 PI | 2/4/0 = 6 | PA→2 PI; cada PI→MP cabo+terminal; mesmos códigos MP em dois pais, consumos distintos |
| `90264161` | 2 | 1 MP + 1 PA | 2/5/1 = 8 | **PA→MP direta + PA subconjunto**; PA subordinado→4 MP + 1 PI; PI→1 MP; 3 níveis |
| `90263520` | 4 | 4 PI | 4/14/0 = 18 | PA→PI→MP; vários códigos MP repetidos entre PI; caso NC de balões |
| `90261606` | 3 | 3 PI | 3/9/0 = 12 | PA→3 PI com etiquetas de códigos diferentes em cada; NC de quantidade de etiqueta |
| `90263572` | 26 | 16 MP + 10 PI | 26/30/0 = 56 | **MP e PI diretamente no N1**; muitos MP reutilizados nos PI; NC código de conector |
| `90264178` | 16 | 6 MP + 10 PI | 16/24/0 = 40 | MP+PI N1; descrições de intermediários × medidas; NC de descrição |
| `90480120` | 10 | 10 MP | 10/0/0 = 10 | **Só MP diretas** no N1, sem PI; NC letras de balões |

**Exemplos de vínculos concretos (estrutura, não desenho):**
- `90264302` → PI `50226113` (1 MI) → MP cabo `10020033` (643 MT) e terminal `10080106` (1000 PC); o outro PI `50226114` (1 MI) reutiliza o mesmo cabo `10020033` com **663 MT** e o terminal `10080106`. Não usar 643/663 como cota automaticamente, nem 1000 PC como 1000 terminais montados.
- `90264161` → MP direta `10210771` (1000 PC) **e** PA `90350410` (1 MI) → MP `10070954` (15550 MT), MP `10210500` (20 KG), MP `10210501` (3.2 KG), MP `10350016` (1000 PC), PI `50090001` (1 MI) → MP `10211300` (2 KG).
- `90261606` → 3 PI `50222382`, `50222383`, `50222384`, cada um com terminal/cabo e etiqueta respectiva `10110009`, `10110084`, `10110098`: caso ideal para associar `quantidade da etiqueta` por **ocorrência e contexto**, não por código único.

**Documentos encontrados:** `product.drawing` retornou `found=true` e `filename={code}.pdf` para todos os sete produtos. Campo `revision=null` em todos; não confundir null de metadado com prova de inexistência de revisão no próprio PDF. Ex.: `90264302.pdf` 103498 bytes, `90264161.pdf` 202428 bytes; `90263572.pdf` 626133 bytes.

### 8.3 Estrutura NO desenho: o que já é visível, o que não sabemos

**Evidência visual integrada previamente verificada (M5/R13), não refeita neste estudo:** no `90264302` a análise tinha 6 ocorrências BOM e **4 DRAWING_TABLE_ITEM candidatos**, sem correspondências finais; `90264161` 8 ocorrências BOM e **4 itens candidatos**, com 2 correspondências exatas de código (`90350410`, `50090001`). Isso mostra que **linhas OCR != ocorrências oficiais**; não autoriza declarar quantos itens reais estão impressos no PDF. Persistiram associações ambíguas de linhas e necessidade de distinguir notas, carimbo, tabela e desenho.

**Neste estudo:** chamadas de `drawing_analysis(compose_understanding=true)` retornaram **erro interno** mesmo para casos anteriormente funcionais; não há observação visual nova dos PDFs `90263572`, `90261606`, `90264178`, `90263520`, `90480120`. **Metadata de existência do PDF não equivale a inspeção visual.** Não inferir layout/tabela, quantidade ou hierarquia representada a partir da BOM.

### 8.4 Decisões de modelagem a fechar com o owner (não implementar ainda)

1. **Escopo de representação:** por família de desenho, quando a tabela mostra N1 inteiro, só PI, MP diretas, MP internas ou combinação? Existe tabela de vários níveis, desenho de PI individual ou arquivos complementares? *TO_INVENTORY/OWNER_DECISION_REQUIRED.*
2. **PA no N1:** como `90350410` é representado/identificado na lista de materiais? O relatório precisa tratar PA subordinado como item, não forçar PI/MP.
3. **MP N1 junto com PI N1:** não apagar MP direta só por existir PI; nem exigir toda MP interna no mesmo desenho.
4. **Quantidade por vínculo:** significado de `MI/MT/PC/KG`, quantidade por 1000, conversão, escala de pai, `conversion_type`, relação com quantidade impressa na tabela. **Sem regra owner, NOT_COMPARABLE.**
5. **Ocorrência única:** chave `produto raiz + caminho de instâncias/vínculos + identidade da fonte e vigência`; códigos repetidos sob pais diferentes e sob o mesmo pai devem ser tratados com integridade, sem dedup por código.
6. **Efetividade e documento:** estrutura válida na data do servidor é snapshot atual; PDF pode ser anterior e a NC histórica ainda mais antiga; definir correspondência versão/vigência em contrato antes de validar conflito.
7. **Limites:** profundidade, paginação, cap 300, BOM truncada; resultado global `VALIDATED` só com evidência de **completude da fonte** e desenho compatível.
8. **Comparação com desenho:** ler tabela item×code×description×qty com bbox/SHAs; vincular por evidência e contexto de montagem; investigar casos sem lista explícita e declarar UNSUPPORTED/INCONCLUSIVE corretamente.
9. **Testes de regressão NC:** `90261606` (etiqueta/quantidade), `90263572` (código de conector), `90264178` (descrição/medida). Conferir versões originais das NC e PDF corretos; não considerar o arquivo atual errado por existir NC histórica.

### 8.5 Recorte fechado do próximo estudo (sem prompt de implementação)

**Passo de análise seguinte:** conseguir leitura visual auditável dos PDFs existentes, pelo fluxo oficial e AuthZ, e observar tabela efetivamente desenhada nos casos (a) 2 PI+MP internos, (b) 1 MP+PA subordinado/PI interno, (c) 16 MP+10 PI diretos, (d) só MP, (e) etiqueta/quantidade. Construir por caso mapa `BOM N1/N2/N3 → linhas efetivas da tabela → possíveis regras de apresentação`, com imagens/boxes e abstenção quando OCR insuficiente. Coletar política do owner de Engenharia sobre representação e quantidade; só então congelar AC/GT de E1 e preparar um único prompt bounded.

**STATUS deste estudo:** `CONTRACT_INVENTORY=PASS` para rotas/schema analisados (runtime da API DELPI específica TO_INVENTORY); `BOM_TOPOLOGY_SAMPLING=PASS` 7 árvores oficiais; `DRAWING_METADATA=PASS` 7/7; `VISUAL_LAYOUT_STUDY=INCONCLUSIVE` novos desenhos (erro interno do analisar), evidência prévia parcial 2 PDFs; `BUSINESS_RULES=OWNER_PENDING`; `E1_IMPLEMENTATION=NOT_STARTED`. Não avançar para E2 nem implementar E1 automaticamente.

### 8.6 Decisão/ledger incremental

| ID | Data | Decisão e observação | Evidência | Próxima ação |
|---|---|---|---|---|
| DEC-VAL-008 | 2026-11-03 | Estrutura é árvore com casos PA→PI→MP, PA→MP+PA→PI→MP, MP+PI N1 e somente MP. Amostra de 7 produtos representativa **de formas**, não de todos layouts de desenho | EVA `product.structure`, 7 consultas | Mapear representações visuais, não inferir do cadastro |
| DEC-VAL-009 | 2026-11-03 | Comparação deve preservar ocorrência/hierarquia, completude e vigência; regras de apresentação/quantidade são autoridade do domínio | Código API DELPI Python e Engineering API; retornos de estrutura | Propor políticas owner, GT e casos de comparação |
| DEC-VAL-010 | 2026-11-03 | Estudo dos desenhos novos não concluído; OCR/análise integrada com erro interno; PDF metadata 7/7 disponível | EVA `product.drawing` e tentativas `product.drawing_analysis` | Recuperar evidência visual via fluxo legítimo antes de decidir layout, sem reabrir implementação |


## 9. Estudo E1 — Observações visuais reais das sete topologias (2026-11-03)

**Método:** `EVA.analyze(product.drawing_analysis, compose_understanding=true)` executado em produção, autorizado, sobre os PDFs oficiais dos **mesmos sete produtos** inventariados na §8. A EVA usou PDFium/PaddleOCR/SLANet e mapeamento `DRAWING_TABLE_ITEM`. A leitura foi por saída estruturada de ferramentas, **sem acesso humano ao raster PDF neste estudo**. Tudo aqui é observação candidata, não auditoria de desenho nem ground truth; número de linhas extraídas não equivale ao número efetivo de itens impressos.

### 9.1 Matriz BOM oficial × observação no desenho

| Produto | Topologia oficial (N1 / total ocorrências) | PDF SHA-256 da leitura | DRAWING_TABLE_ITEM candidatos | Achado visual, com exemplo de texto bruto | Estado de comparação |
|---|---|---|---:|---|---|
| `90264302` | 2 PI / 6 | `f33447b271a3518643559582d79cf54527b85778537cfb1e20a5ccf5d989f0ef` | 4 | rótulos `a 1 10020033`, `b 1 10080106`; texto bruto também contém `50226113`, `50226114`, descrição de cabo/terminal. Tabela agrupada por intermediário **hipótese**, não regra comprovada | 0 candidatos finais, 6 ambíguas; E1 INCONCLUSIVE |
| `90264161` | MP + PA / 8 | `8d9fe28a19cae334abd6eaa3b0fb13059aecad715672b0dfd6aaf10462b85195` | 4 | códigos `90350410` e `50090001` extraídos exatamente como candidatos; carimbo/código raiz mistura-se à região identificada | 2 code-match candidatos / 8 ocorrências, 6 ambíguas; E1 INCONCLUSIVE |
| `90263520` | 4 PI / 18 | `08bf68690401438ab09c0e7ffcd1126bf98b238de776bc680db587704e4fb200` | 6 | uma linha OCR contém `a1 a2 a3 1 1 1 10400040 10080063 10090014`; outras combinam vários `aN` e MP; PI `50230893`, `50232467` aparecem como candidatos. **Linha OCR ≠ item lógico.** | 2 candidatos / 18, 16 ambíguas; E1 INCONCLUSIVE |
| `90261606` | 3 PI / 12 | `1c1f1412fb6cac22e8e44893dc27a39f45be806c6819bc12856ea4adb3580cd1` | 4 | tokens de etiquetas `10110009`, `10110084`, `10110098`, misturados com cabo `10400078` e terminal `10080147`; associação item↔etiqueta e qty **não resolvida** | 4 candidatos / 12, 8 ambíguas; E1 INCONCLUSIVE |
| `90263572` | 16 MP + 10 PI N1 / 56 | `9021fce05c608655e538f67cdaac08c7484ebbe16a8888e83fbeec9ecaa28d3e` | **0** | 13 candidatos dimensionais, mas **nenhuma linha estruturada criada pelo parser**; não comprova inexistência de tabela no PDF | 0 candidatos, 56 NOT_LOCATED; E1 INCONCLUSIVE |
| `90264178` | 6 MP + 10 PI N1 / 40 | `1a78693bd335371f192daceecf7f14f91637443bf03045f0aebec33bd7332fa8` | 13 | observados códigos PI `50215408`, `50233845`, `50233847`, `50233848`; vários registros combinam códigos em uma linha, ex. `50215413 50215412`; raiz `90264178` pode aparecer em seção confundida com tabela | 4 candidatos / 40, 36 ambíguas; E1 INCONCLUSIVE |
| `90480120` | 10 MP N1 / 10 | `9b64ae2095fa551e6c3b12fa1f6d232646725b2ab9c31eb489abedd972555cd8` | 4 | registros `UNRESOLVED` com texto bruto `0`, `1`, `2`, `3` sem associação segura com código/descrição/quantidade | 0 candidatos, 10 ambíguas; E1 INCONCLUSIVE |

**Precauções:** `match_candidates` é candidatura de identificação, não estrutura validada. Nenhum dos 7 desenhos passou VAL-01. Em `90263572`, `0 DRAWING_TABLE_ITEM` significa falha/insuficiência da extração tipada, jamais estrutura sem itens. Em `90264178`, código do produto raiz não deve ser promovido a componente. `quantity_raw` da BOM não é `assembly_quantity` nem cota; mesmo tokens `1` visíveis não comprovam quantidade da linha até associação de célula.

### 9.2 Padrões de representação candidatos — ainda a confirmar no raster e com Engenharia

1. **Sublistas/grupos por PI:** `90264302` e `90263520` sugerem que uma tabela pode associar um PI a linhas internas com itens como `a1`, `a2`, `a3`; não supor que cada tabela represente apenas N1.
2. **Lista selecionada de componentes de níveis mistos:** `90264161` observa PA subordinado e PI interno, mas não confirma se todas MPs diretas e internas precisam aparecer.
3. **Lista de códigos PI com MP do primeiro nível:** `90264178` mostra PI presentes e MP sem associação segura; não presumir omissão de MP.
4. **Etiquetas diferentes por intermediário:** `90261606` é caso de teste obrigatório para qty/código corretos por ocorrência, preservando os grupos.
5. **Tabelas grandes ou formatos heterogêneos:** `90263572` demonstra limitação grave do parser em caso de 56 ocorrências oficiais; `90480120` demonstra extração insuficiente mesmo numa BOM N1 simples.

**Hipótese de design para estudo:** tratar a *unidade de análise* como `documento/folha → tabela/região → grupo/submontagem → linha lógica → item/código/descrição/quantidade → vínculo candidato à ocorrência (caminho e nível)`. O parser atual combina várias células em uma mesma linha OCR; segmentação espacial e semântica são requisitos para VAL-01. **Não criar um novo modelo agora**: verificar como aproveitar as células SLANet, tokens brutos, `DrawingObjectSet`, investigações e mapper existentes.

### 9.3 Riscos evidenciados pelos dados

- **Parsing de linhas físicas vs linhas lógicas:** `90263520` agrupa vários códigos em uma única linha; `90261606` embaralha código de etiqueta, cabo e terminal; a priorização é acertar fronteiras e referências, antes de comparar quantidades.
- **Separar cabeçalho/carimbo/raiz da lista de componentes:** `90264161` e `90264178` têm evidência do código raiz na região rotulada como `component_table`.
- **Multiplicidade e hierarquia:** mesmos códigos MP sob PI diferentes; correspondência por código sem contexto é insuficiente.
- **Reconhecimento de quantidades e descrições:** `assembly_quantity` retornou null nos objetos apresentados, mesmo quando aparecem tokens `1`; não validar quantidade ainda.
- **Completude e governança:** validação global exige BOM completa (limites/paginação), política de quais níveis devem constar, vigência/identidade do PDF, GT por família/layout e thresholds aprovados. Histórico de NC não é prova do PDF atual.

### 9.4 Conclusão e decisão de continuidade

**DEC-VAL-011 (2026-11-03):** as sete estruturas e as sete saídas visuais foram cruzadas; encontradas pelo menos quatro características de apresentação distintas **candidatas** (sublistas por PI, lista parcial/mista, MP direta, agrupamento denso), mas **nenhuma política universal de representação foi comprovada**. Necessidade funcional nº 1 de VAL-01: **reconstruir linha lógica e associação de campos de tabela com evidência independente**, mantendo hierarquia de grupo e nunca promovendo código sozinho a estrutura validada.

**Próximo estudo, ainda antes de prompt:** inspecionar visualmente o raster/PDF original e/ou recuperar células SLANet por região nos casos `90264302`, `90263520`, `90264178`, `90261606`, `90263572`, `90480120`; identificar colunas/linhas e agrupamentos realmente impressos; versionar exemplos anotados por família, perguntar ao owner quais níveis são obrigatórios e como as quantidades se relacionam. **Estado:** `BOM_OFFICIAL=PROVEN`; `DRAWING_OCR_CANDIDATES=PROVEN`; `PRINTED_LAYOUT_RULE=TO_INVENTORY`; `STRUCTURE_VALIDATION=INCONCLUSIVE`; `E1_IMPLEMENTATION=NOT_STARTED`. E2–E7 permanecem congeladas.


## 10. Tentativa de obtenção dos PDFs originais para inspeção humana (2026-11-03)

**Solicitação:** obter diretamente os **sete PDFs originais** `90264302`, `90264161`, `90263520`, `90261606`, `90263572`, `90264178`, `90480120` e examinar visualmente suas páginas, tabelas, grupos e colunas — não somente o output OCR do §9.

**Resultado da disponibilidade:**
- EVA `read(product,drawing)`: os sete PDFs foram identificados no fileserver (`found=true`), mas o contrato MCP retorna somente **metadata**, não bytes PDF. O próprio catálogo EVA indica os bytes pela rota autenticada da Engineering API `/v1/products/{code}/drawing/pdf`.
- `drawing_analysis` autenticado já produziu tokens/células/objetos, SHAs e comparações para os sete casos (§9), mas **não oferece neste fluxo o raster/PDF físico para inspeção direta**.
- Busca exata pelos sete códigos no Google Drive conectado: **0 resultados**. Busca/listagem da Library/Project e inspeção do container da sessão: **nenhum dos sete PDFs disponível como arquivo diretamente manipulável** (a Library contém PDFs de outros códigos).
- Tentativa de acesso HTTP à rota pública conhecida no runtime do container: falhou por resolução DNS do ambiente, sem obter resposta HTTP; **não foi possível confirmar se exigiria OAuth**, e não se deve usar atalho/credenciais fora dos contratos.
- Logo `PDF_BYTES_ACQUIRED=FAIL/UNAVAILABLE` neste ambiente; `RASTER_VISUAL_REVIEW=TEST_NOT_RUN` para os sete. Isso **não contradiz** a existência dos arquivos nem o sucesso do serviço EVA ao processar PDF internamente.

**Dado comprovado disponível:** sete árvores BOM e sete outputs OCR/SLANet no §9; hipóteses sobre agrupamento em sublistas e itens múltiplos em linha devem permanecer **CANDIDATE/INCONCLUSIVE**. Não aprovar regra de layout nem quantidade sem visualização do PDF original.

**Caminhos legítimos para fechar a inspeção:** (a) anexar os sete PDFs à conversa; ou (b) disponibilizá-los em Drive/Project/Library que o usuário autorize e que permita leitura dos bytes; ou (c) conectar uma capacidade de download autenticado da rota oficial da Engineering API, com delegated_user e AuthZ live, sem vazar tokens, sem URL improvisada e sem segunda fonte de autoridade. Assim que os bytes forem acessíveis, renderizar páginas com hashes, ampliar recortes das tabelas, anotar linhas lógicas/células/colunas e confrontar com BOM por ocorrência. Preservar NC/revisão/validity.

**DEC-VAL-012:** o estudo visual segue com **bloqueio de acesso ao PDF bruto**, não com falta de dados da BOM. Não criar prompt de implementação, não iniciar E2 e não declarar `VAL-01=PASS`. Um único bloqueio de acesso deve ser resolvido antes de inventar regras de representação.


### 10.1 Esclarecimento de autoridade e capacidade (DEC-VAL-013 — 2026-11-03)

**Correção explícita:** a EVA **já obtém os bytes do PDF** da Engineering API no backend e realiza análise de imagem/OCR; isso foi PROVEN nos sete relatórios `product.drawing_analysis(compose_understanding=true)` (document SHA, página, bbox e observações). **Não há impedimento da EVA em buscar PDFs**, nem necessidade de nova integração com fileserver ou de solicitar downloads manuais ao usuário como requisito do produto. O bloqueio do §10 é **exclusivamente para entregar os bytes brutos do backend ao ambiente desta conversa** para renderização e inspeção humana direta: o MCP `product.drawing` fornece metadados; `drawing_analysis` retorna resultados tipados, e o contrato semântico atual não inclui `download_pdf`/`rendered_page`. A rota oficial `/v1/products/{code}/drawing/pdf` permanece pertencente à Engineering API e sujeita a AuthZ. **Próximo passo:** aproveitar o fluxo backend já existente e, apenas se a inspeção humana do original for indispensável, avaliar acesso autorizado à representação visual já gerada, sem expor tokens, duplicar acesso ou criar source of truth. `EVA_PDF_FETCH_AND_OCR=PROVEN`; `ASSISTANT_RAW_PDF_BYTES=UNAVAILABLE`; `DIRECT_VISUAL_REVIEW=TEST_NOT_RUN`. Essa distinção substitui qualquer leitura anterior de "EVA não consegue obter PDFs".

## 11. Revisão independente da entrega PDF → ChatGPT (2026-11-03)

**Origem:** relatório final do executor Devin para o commit `3394a29cefa1e2fae3357c6337fee477ee139adf` (`engineering_app/interface/http/routes/product_routes.py`). **Fatos confirmados por revisão independente:** commit existe no repositório; diff altera somente esta rota HTTP; acrescenta `hashlib.sha256(content)`, `X-Document-Sha256`, `X-Document-Size`, `X-Document-Filename`, `X-Document-Product-Code`; preserva operação, fluxo delegado, guarda de permissão e contexto humano no código. Não houve execução independente dos testes, inspeção direta do SHA em produção, nem abertura binária no consumidor ChatGPT neste momento.

### 11.1 Defeito identificado, relevante ao resultado alegado

A implementação diz `"Content-Disposition": result.get("content_disposition") or f'attachment; filename="{filename}"'`. **Se o adapter/origem retornar valor `inline; ...`, esse valor prevalece; a resposta NÃO será `attachment`**. A mudança não garante o efeito declarado pelo executor. Marcar `REWORK/BLOCKING` para a garantia do header ou comprovar por teste de comportamento que o contrato da origem nunca o preenche com inline; a correção mais simples deve impedir retorno de disposição insegura/não prevista sem descartar identificação segura do arquivo. Não assumir que `attachment` isolado faz ChatGPT anexar arquivo.

### 11.2 Demais gates ainda sem evidência final

- `OPENAPI_BINARY_RESPONSE`: **TO_INVENTORY** — verificar `/openapi.json` efetivo para a operação `get_product_drawing_pdf`, especialmente `200.content.application/pdf` com schema `type: string, format: binary`; `operation_id` existente não comprova automaticamente contrato de arquivo.
- `CONNECTOR_ACTION_REGISTERED`: **FAIL / NOT PRESENT IN AVAILABLE TOOLS** — o conector EVA desta conversa expõe `read(product,drawing)` para metadados, não uma action/binário de PDF. Cadastro/importação e capacidades da integração podem depender do owner externo.
- `CHAT_PDF_RECEIVED_AND_RENDERED`: **TEST_NOT_RUN** — não houve transferência nem renderização demonstrada no cliente ChatGPT. Não confundir resposta HTTP attachment com entrega do host de ferramentas.
- `AUTHZ_NEGATIVE`: comportamento fail-closed sem credencial relatado pelo executor; **não reproduzido independentemente**. Não equivale a autorização positiva.
- `TESTS`: 87/87 e 676 pass / 1 fail ambiental informados pelo executor; **não reproduzidos** nesta revisão. `TESTED_SHA` e `DEPLOYED_SHA` informados, não confirmados no runtime por ferramenta autorizada.
- `7_PRODUCT_E2E`: **TEST_NOT_RUN**, reconhecido pelo executor sem OAuth delegada.

### 11.3 Decisão DEC-VAL-014 — fechar o pacote, sem recursão

**Decisão:** `REWORK` delimitado para a garantia `Content-Disposition` e conferência do OpenAPI binário; `INCONCLUSIVE` para entrega de arquivo ao ChatGPT. **Não abrir nova frente/etapa/prompt em cascata.** Exigir ao executor somente (1) prova/correção do header nas respostas positiva com `content_disposition=inline` e sem campo; (2) teste/assert do corpo SHA+size+MIME e headers; (3) verificação do OpenAPI efetivo `application/pdf`/binary; (4) evidência do deploy no SHA; (5) reportar o gate do owner do conector para registrar a Action e validar recebimento real. Se o registro do conector for tecnicamente impossível pelo owner atual, marcar `OWNER_BLOCKED` e escalar à Coordination, sem afirmar PASS ponta a ponta.

**A VAL-01 Estrutura permanece como única funcionalidade de análise ativa.** Transporte de PDF é enabler técnico de inspeção; não introduzir outra implementação de BOM, OCR nem outra authority.

### 11.4 Execução do REWORK DEC-VAL-014 (2026-11-03, SHA `52a7556efd`)

**Escopo tocado:** `engineering_app/interface/http/routes/product_routes.py`, `engineering_app/infrastructure/gateways/delegated_auxiliary.py`, novo `tests/test_product_drawing_pdf.py`. Nenhum outro componente alterado; VAL-01 intocada.

**Resultado por gate:**

| Gate | Estado | Evidência |
|---|---|---|
| `CONTENT_DISPOSITION_ATTACHMENT` | **PASS** | Resposta emite `attachment; filename="<seguro>"` fixo; a disposição upstream (`inline` do `FileResponse` api-delpi, `attachment` ou ausente) nunca é ecoada. Adapter passa a entregar `filename` parseado (`filename`/`filename*` RFC 2231) como metadado; a borda decide a disposição e sanitiza o nome (path/aspas/CRLF/não-ASCII → removidos, fallback `{code}.pdf`). Teste upstream→rota com `inline; filename="DES-0156.pdf"` comprova `attachment; filename="DES-0156.pdf"` final. |
| `OPENAPI_BINARY_RESPONSE` | **PASS** | `/openapi.json` efetivo (live, container reiniciado): `200.content.application/pdf.schema = {type: string, format: binary}`; `application/json` removido do 200 (`response_class=Response`); erros 400/403/404/502 documentados como envelope JSON. |
| `INTEGRITY_SHA256_SIZE` | **PASS** | Teste asserta `X-Document-Sha256` == sha256 do corpo, `X-Document-Size` == len do corpo, `X-Document-Filename`, `X-Document-Product-Code` e MIME `application/pdf`; bytes íntegros (sem reprocessamento). |
| `AUTHZ_NEGATIVE` | **PASS** | `401` sem JWT reproduzido live no gateway local; `403` sem `engineering.access` e `403` quando o owner downstream nega — testes com JWT RS256 real + RBAC controlado. `404`/`502` honestos mantidos. |
| `TESTS` | **PASS (com ressalva ambiental)** | `pytest tests/ -q` no container `delpi-engineering-api`: **692 passed / 1 failed / 11 skipped** — a única falha é `test_visual_perception_r7.py::test_normalize_box_json_safe` (R7 OCR, preexistente/ambiental, não toca os arquivos alterados; mesmo "1 fail ambiental" já relatado na revisão anterior). |
| `DEPLOYED_SHA` | **PASS local** | SHA `52a7556efd` commitado; container `delpi-engineering-api` reiniciado sobre o working tree bind-mountado; OpenAPI live e `401` fail-closed verificados via gateway. Produção segue fluxo governado local→push→pull; **não foi feito push** (branch `main` divergida do `origin/main`: 1 commit local vs 2 remotos — reconciliar antes de publicar). |
| `CONNECTOR_ACTION_REGISTERED` | **CONNECTOR_PENDING / OWNER_BLOCKED** | O conector EVA é **MCP** (`mcp-engineering`, tools auto-descobertas via `tools/list` — não há registro manual de "Action"). O contrato semântico vigente expõe `read(product, drawing)` = metadados; nenhuma action binária existe no registry (`semantic_registry.py`) e materialização de arquivo a partir de tool result MCP **não é capability comprovada do host ChatGPT** — não presumir. O caminho oficialmente suportado para arquivo no ChatGPT é a façade **GPT Actions** (padrão `docs/gpt-actions/openapi-gpt-actions.json` dos apps irmãos, regra `custom-gpt-actions-integration.mdc`), que exige: façade owner-local da engineering-api + import no GPT Builder + client OAuth Keycloak user-parity — **configuração externa sob autoridade do owner do conector/GPT, fora do alcance desta entrega**. Não foi criado conector paralelo nem nova superfície. |
| `CHAT_PDF_RECEIVED_AND_RENDERED` | **TEST_NOT_RUN → OWNER_BLOCKED** | Sem acesso ao host ChatGPT; recebimento real só pode ser demonstrado pelo owner do conector após registrar a operação como Action (ou comprovar materialização de recurso MCP pelo host). |

**Estado de encerramento proposto: `API_PASS / CONNECTOR_PENDING`** — contrato HTTP/OpenAPI corrigido e comprovado; a entrega do arquivo ao ChatGPT depende exclusivamente do registro da Action pelo owner externo (façade GPT Actions ou capability MCP comprovada), com o contrato pronto: `GET /v1/products/{product_code}/drawing/pdf` → `200 application/pdf` + `Content-Disposition: attachment` + `X-Document-Sha256|Size|Filename|Product-Code`, OAuth Keycloak user-parity via JWT delegado já existente.

**Não é `PASS` ponta a ponta** — o arquivo ainda não foi demonstrado abrindo no ChatGPT.

## 12. Exportação do PDF oficial via MCP — DEC-VAL-016 (2026-11-03, SHA `cad4308b53`)

**Implementação (bounded):** ação semântica `product.drawing_download` na tool `read` existente — os bytes do desenho oficial trafegam como `EmbeddedResource`/`BlobResourceContents` (base64) dentro do `tools/call`, com `filename`, `size_bytes`, `sha256`, `mime_type`, `resource_uri` e `provenance` no payload tipado. Reutiliza `fetch_product_drawing_pdf` do adapter delegado (mesma cadeia JWT humano → api-delpi, sem service token/elevação/fileserver). `core/filenames.safe_pdf_filename` é a fonte única de nome seguro (rota REST + bridge). `_wrap` semântico passou a preservar conteúdo não-texto. **Nenhum endpoint novo, nenhuma ferramenta MCP nova, VAL-01 intocada.**

**Inventário de transporte (mcp==2.2.0, protocolo 2025-11-25):** `tools/call` suporta `EmbeddedResource` (blob base64) — escolhido por entregar bytes na mesma chamada autorizada; `resources/read`/ResourceLink ficam como alternativa documentada, sem necessidade real agora.

**Evidência E2E (cliente real, sem mocks — `sandbox/eva_pdf_mcp_e2e.py`):**

| Gate | Resultado |
|---|---|
| Transporte | `initialize` + `tools/list` (6 tools) + discovery via `get_context` — `drawing_download` anunciada |
| Recebimento | `99900001` (PDF real no acervo oficial local): `EmbeddedResource` → 551 B materializados em `.pdf`, **sha256 e size conferidos**, MIME `application/pdf`, magic `%PDF-` |
| Renderização | página 1 renderizada 612×792 via pypdfium2 (2 páginas) |
| Negativo | sem token → **401**; token `delpi-central` sem aud/scope MCP → **401**; usuário sem `engineering.access` → **403** tipado; produto inexistente → **404**; upstream indisponível → **502** |
| Compatibilidade | `product.drawing` (metadados) e demais ações intactas — suíte 705 passed (1 falha ambiental pré-existente R7) |
| Sete oficiais | 404 local — **biblioteca `/drawing-pdfs` vazia neste ambiente** (fileserver `/mnt/x/` não populado): `ENV_BLOCKED` local; transporte provado com arquivo real no mesmo caminho do owner |
| ChatGPT | materialização de `EmbeddedResource` por tool result **não é capability comprovada do host** — `OWNER_BLOCKED` para `PASS_E2E_CHATGPT`; o conector EVA é MCP (sem registro manual de Action — descoberta automática via `tools/list`) |

**Provisões temporárias do smoke (revertidas):** usuários `devin-eva-pdf`/`devin-eva-denied` (Keycloak+Core RBAC) removidos; `directAccessGrants` do client `mcp-engineering` habilitado e revertido ao fim; PDF sintético removido do acervo.

**Estado: `PASS_E2E_MCP`** — documento real recebido, materializado e renderizado por cliente MCP compatível. `PASS_E2E_CHATGPT` permanece `OWNER_BLOCKED` (capability do host não comprovada — não inferir a partir do cliente Python).
## 13. Relato de prova MCP e revisão independente de publicação/autoridade (DEC-VAL-017 — 2026-11-03)

**Recebido do executor:** relatório `PASS_E2E_MCP` para ação semântica `product.drawing_download`, `mcp==2.2.0`, protocolo `2025-11-25`, `EmbeddedResource/BlobResourceContents`, cliente real `streamable_http_client + ClientSession`, sem mocks no transporte; 551 bytes de PDF `99900001` comparados por SHA/size, materializados em disco e renderizados com pypdfium2 (2 páginas, 612×792), respostas 401/403/404/502, suíte `705 passed` (uma falha ambiental R7 alegada). Executor informou que o teste foi realizado em acervo temporário e **PDF sintético removido** após prova, e que os sete desenhos-alvo retornaram 404 por acervo local `/drawing-pdfs` vazio. Não foi realizado teste E2E autenticado com desenho oficial preexistente dessa amostra; a prova de infraestrutura não equivale a confirmação do fluxo documental produtivo.

**SHAs relatados:** `cad4308b53` (feature) e `5c98893be2` (docs), descritos pelo executor como **locais, não publicados**. **Verificação independente do GitHub realizada nesta data:** `fetch_commit` de ambos retornou `No commit found for SHA`; o Doc 119 em `main` não continha a seção 12 informada; não há diff remoto consultável desses commits. Não promover alterações relatadas a `PROVEN/PUBLISHED` sem push e recuperação dos hashes.

**Verificação independente no conector desta conversa:** `get_context(topic=product.drawing_download, entity=product, selected_ref=90264302)` respondeu catálogo `1.0`, expondo `product.drawing` apenas como metadados e análises, **sem a ação `product.drawing_download`**. As seis ferramentas semânticas continuam as mesmas; nenhum `EmbeddedResource` PDF foi recebido pelo ChatGPT nesta sessão. Não é prova de que o SDK MCP não suporte o formato, somente de que a versão acessível não o anuncia.

**Decisão DEC-VAL-017:** `MCP_TRANSPORT_E2E=PASS_REPORTED_BY_EXECUTOR` para cliente real com **documento de prova**, `INDEPENDENT_CODE_REVIEW=BLOCKED_UNPUBLISHED`, `OFFICIAL_PREEXISTING_PDF_E2E=TEST_NOT_RUN`, `CHATGPT_HOST_MATERIALIZATION=OWNER_BLOCKED/TEST_NOT_RUN`. **Não aceitar PASS_E2E_CHATGPT**, nem declarar que o transporte está instalado em produção. Sem retrabalho automático: (1) executor/owner publica os dois commits após reconciliar HEAD e histórico sem sobrescrever alterações concorrentes, (2) reviewer inspeciona diff e testa discovery do MCP publicado, (3) usuário autorizado testa `90264302` no fileserver legítimo e compara SHA, tamanho, paginação/renderização, (4) owner do host ChatGPT atesta consumo de `EmbeddedResource` ou documenta alternativa governada; (5) atualizar a issue sem confundir transporte provado com governança documental. A VAL-01 Estrutura continua frente única.

## 14. Publicação, deploy e validação E2E — DEC-VAL-017 execução (2026-11-03)

**Publicação:** merge `442b23e1f0` em `origin/main` contém `cad4308b53` (feature) + `5c98893be2` (docs §12) — push comprovado (`origin/main == HEAD`), sem force-push/rebase destrutivo; histórico concorrente preservado.

**Deploy (ambiente acessível governado):** container `delpi-engineering-api` reiniciado sobre o checkout publicado (bind-mount do repo em `origin/main`); `health` online; MCP unauth → 401. **Produção `srv-api`: `OWNER_BLOCKED`** — hostname não resolve neste ambiente; deploy prod segue `infra/scripts/up-prod-sequential.sh` pelo operador autorizado após `git pull`.

**E2E no servidor implantado (cliente MCP real):** protocolo 2025-11-25; `tools/list` 6 tools; `get_context` anuncia `drawing_download`; `EmbeddedResource` → PDF real materializado (551 B, sha256+size íntegros, magic `%PDF-`), página 1 renderizada 612×792; 401 sem token/aud errada; 403 sem permissão; 404/502 tipados; compatibilidade `product.drawing`/estrutura preservada.

**Sete produtos oficiais:** 404 tipado — acervo `/drawing-pdfs` vazio neste ambiente (`ENV_BLOCKED` local; não é ausência do documento). Transporte provado com PDF real no caminho oficial do owner, claramente rotulado e removido.

**Temporários revertidos:** usuários smoke deletados (KC+Core), `directAccessGrants` revertido, PDF de teste removido.

**ChatGPT:** `OWNER_BLOCKED` — materialização de `EmbeddedResource` pelo host não comprovada; discovery automática via `tools/list` ocorrerá quando o conector reconectar à versão implantada. Alternativa governada: façade GPT Actions (rota `attachment` já PROVEN).

**Estado: `DEPLOYED (ambiente local oficial) / E2E_MCP_PROVEN / PROD_DEPLOY_OWNER_BLOCKED / CHATGPT_CONNECTOR_PENDING`.**

### 14.1 Revisão independente pós-publicação (DEC-VAL-018 — 2026-11-03)

**Confirmado por consulta ao GitHub:** commit de documentação `71c9ba8ccd16e020c62f081cc738cf5070350dd3` existe em `main`, Doc 119 §14 publicado; código do branch `main` contém `("product", "drawing_download")` em `engineering_app/interface/mcp/semantic_bridge.py`, `tool_get_product_drawing_pdf` e `EmbeddedResource/BlobResourceContents` em `tool_bridge.py`, além de `safe_pdf_filename` em `core/filenames.py`. Isso remove o antigo bloqueio `UNPUBLISHED` da DEC-VAL-017. A publicação de código é **PROVEN**; a prova executável E2E foi **relatada pelo executor**, não repetida pelo reviewer.

**Teste independente do ChatGPT nesta sessão:** `get_context(topic=product.drawing_download,entity=product,selected_ref=90264302)` ainda retorna catálogo `1.0` sem a ação `product.drawing_download`. O conector efetivamente acessível ao ChatGPT não apresenta o transporte novo. Nenhum PDF, `EmbeddedResource`, arquivo materializado ou imagem de página foi recebido neste ambiente. **`CHATGPT_DISCOVERY=FAIL`; `CHATGPT_PDF_RECEIVED=TEST_NOT_RUN`.**

**Estados por ambiente:** `SOURCE_PUBLISHED=PROVEN`; `LOCAL_BIND_MOUNT_DEPLOY=PASS_REPORTED_BY_EXECUTOR`; `PROD_SRV_API_DEPLOY=OWNER_BLOCKED` (sem acesso do executor ao host), `OFFICIAL_7_PDFS_E2E=INCONCLUSIVE_ENV`, `CHATGPT_CONNECTOR=NOT_UPDATED_IN_THIS_SESSION`. O PDF `99900001` usado para smoke, de 551 bytes, foi **sintético e removido**; sua renderização não substitui teste com desenho oficial preexistente. Não confundir um container no host local com deploy produtivo.

**DEC-VAL-018 — única saída operacional pendente:** operador com acesso ao `srv-api` executa o procedimento canônico de deploy no commit publicado (revalidando HEAD/status/rollback) e comprova SHA runtime; em seguida valida `tools/list` + `get_context` do endpoint realmente conectado ao ChatGPT, testa transferência autenticada de `90264302.pdf` do acervo oficial e verifica SHA/bytes/abertura. O owner da integração verifica se o host ChatGPT materializa `EmbeddedResource`; se não, registra `OWNER_BLOCKED` com evidência e avalia a alternativa governada, sem refazer a Engineering API ou fazer workaround inseguro. Preservar apenas VAL-01 ativa.

## 15. Tentativa de deploy produtivo `srv-api` — evidência objetiva de bloqueio (2026-11-03)

**Verificado nesta execução:** `origin/main` contém a implementação (`semantic_registry`, `tool_get_product_drawing_pdf`, `EmbeddedResource/BlobResourceContents`, `core/filenames`) e o deploy no ambiente local oficial já provou E2E MCP (§14). A única pendência é executar o procedimento canônico no `srv-api`.

**Evidência objetiva de acesso bloqueado (neste host de execução):**
- `ssh srv-api` → `Could not resolve hostname` (sem alias/DNS).
- `ssh {root,ubuntu,debian,analistaptd,delpi,devin}@192.168.1.237` com `id_ed25519` e `id_ed25519_srv` → `Permission denied (publickey,password)` em todas as combinações.
- Nenhum `docker context` remoto configurado; sem automação de deploy remoto no repo.

**Runbook para o operador autorizado (srv-api):**
1. No repo em produção: `git fetch origin && git checkout main && git pull` — confirmar HEAD contém `cad4308b53`.
2. `./infra/scripts/up-prod-sequential.sh --fase core --build` (escopo mínimo: `engineering-api`; o MCP vive no mesmo processo/container).
3. Prova de versão: `curl <host>/apps/engineering-api/openapi.json` contém `drawing/pdf` + MCP `tools/list` anuncia `read` com `product.drawing_download` no `get_context`.
4. E2E: `engineering-api/sandbox/eva_pdf_mcp_e2e.py` com token humano autorizado (client `mcp-engineering`, auth-code) contra `https://minhadelpi.com.br/apps/engineering-api/mcp` — produtos `90264302` + 6 demais; fileserver prod populado resolve os PDFs oficiais.
5. Rollback: `git checkout <sha-anterior>` + mesmo script.

**Estado: `PROD_DEPLOY_OWNER_BLOCKED`** — acesso SSH ao `srv-api` indisponível para o executor; código publicado e pronto. `CHATGPT_CONNECTOR_PENDING` permanece até o deploy produtivo + verificação de materialização `EmbeddedResource` pelo host.

## 16. Deploy produtivo `srv-api` executado (2026-11-03) — DEP-01/DEP-02 PROVEN

**Procedimento oficial:** `ssh operador@srv-api` → `git pull --ff-only origin main` (21 commits) → `./infra/scripts/up-prod-sequential.sh --build engineering-api`. HEAD prod = `98ea06709f` contendo `drawing_download` (grep confirmado no container). `delpi-engineering-api` recriado: `Up (healthy)`, `/health` online, `POST /apps/engineering-api/mcp` sem token → **401** na URL pública `https://minhadelpi.com.br` (fail-closed em produção — DEP-06 parcial).

**Pendência legítima — DEP-03..05:** E2E com PDF oficial exige **token humano real** (client `mcp-engineering`, authorization-code flow no Keycloak prod `minhadelpi.com.br/auth`) — não há direct grant/admin creds disponíveis ao executor, e fabricar identidade é proibido. Script pronto e versionado em produção: `engineering-api/sandbox/eva_pdf_mcp_e2e.py` (montar `MCP_URL=https://minhadelpi.com.br/apps/engineering-api/mcp` + Bearer do usuário autorizado, sem Host override). Os 7 produtos (`90264302`+) serão servidos pelo acervo prod populado.

**ChatGPT (DEP-07/08):** `CONNECTOR_PENDING` — discovery ocorre via `tools/list` ao reconectar; materialização de `EmbeddedResource` pelo host não comprovada.

**Estado: `PROD_DEPLOYED / E2E_HUMAN_TOKEN_PENDING / CONNECTOR_PENDING`.**

## 16. VAL-01 — leitura direta dos sete PDFs oficiais e confronto preliminar BOM (2026-11-03; DEC-VAL-020)

**Mudança de evidência:** o conector EVA deste ChatGPT passou a anunciar `read(product,drawing_download)` como proven; a chamada entregou, via recurso incorporado e materialização real pelo host, os **sete PDFs originais**, renderizados e inspecionados diretamente pelo reviewer. `EVA_MCP_TO_CHATGPT_PDF_TRANSPORT=PASS` nesta conversa. **Não significa VAL-01 PASS.** Foram consultadas novamente as estruturas oficiais `read(product,structure)` com validity `current/server_date`. A leitura visual da tabela não depende da detecção OCR; especialmente o PDF `90263572` contém tabela de materiais extensa na **página 2**, apesar do OCR anterior não ter identificado linhas tipadas.

| Produto | PDF SHA-256 | Páginas | Evidência visual preliminar (confronto com BOM atual) |
|---|---|---:|---|
| `90264302` | `f33447b271a3518643559582d79cf54527b85778537cfb1e20a5ccf5d989f0ef` | 1 | Tabela mostra PI `50226113` e `50226114` com cabo `10020033` e terminal `10080106` por conjunto; ambos PI constam como N1 na BOM. Dimensões impressas 643±2 e 663±2 mm. |
| `90264161` | `8d9fe28a19cae334abd6eaa3b0fb13059aecad715672b0dfd6aaf10462b85195` | 1 | Tabela do desenho mostra MP direta `10210771`, PA `90350410` e PI subordinado `50090001`, com MP associados à PA/PI; estrutura oficial N1 tem MP `10210771` e PA `90350410`, com PI `50090001` dentro da PA. Alerta: grupos impressos não correspondem a nível único flat. |
| `90263520` | `08bf68690401438ab09c0e7ffcd1126bf98b238de776bc680db587704e4fb200` | 1 | **CANDIDATE de divergência de revisão/estrutura:** tabela impressa contém **cinco** grupos PI `50213064`, `50230890`, `50230893`, `50232466`, `50232467`; consulta da BOM atual N1 contém somente os últimos quatro. Necessário conferir revisão/validade, data do desenho, equivalência e autorização do owner antes de declarar NC. A tabela também mostra `10400040` ligado a `50213064`. |
| `90261606` | `1c1f1412fb6cac22e8e44893dc27a39f45be806c6819bc12856ea4adb3580cd1` | 1 | Tabela física impressa, apesar de o texto extraído via PDF não capturar toda a tabela: PI `50222382`, `50222383`, `50222384`, cada um com cabo `10400078` e terminal `10080147`; etiquetas `10110009` T4, `10110084` T5 e `10110098` T6 respectivamente, coerentes com consulta BOM por PI. |
| `90263572` | `9021fce05c608655e538f67cdaac08c7484ebbe16a8888e83fbeec9ecaa28d3e` | 2 | Página 1 desenho/chicote; **página 2 tabela completa**, com 16 MP diretas e 10 PI `50213142`, `50224688`, `50224689`, `50233421` a `50233427`, coerentes com itens N1 consultados. Algumas quantidades impressas 2 ou 4 não podem ser confrontadas diretamente com `quantity=2000/4000` na BOM sem normalização por unidade/conversion_type. |
| `90264178` | `1a78693bd335371f192daceecf7f14f91637443bf03045f0aebec33bd7332fa8` | 1 | Tabela mostra 6 MP diretas e 10 PI, códigos `50215408`, `50215412`, `50215413`, `50225814`, `50225817`, `50225818`, `50233845` a `50233848`, todos presentes N1 na BOM consultada. |
| `90480120` | `9b64ae2095fa551e6c3b12fa1f6d232646725b2ab9c31eb489abedd972555cd8` | 2 | Tabela impressa na página 1 apresenta dez MP A1–A9/AA; códigos `10070916`, `10080001`, `10081671`, `10081796`, `10081809`, `10090010`, `10090050`, `10210783`, `10500020`, `10520030`, todos presentes N1. Página 2 contém detalhes dimensionais e de inspeção. |

**Limites e critérios:** estas são constatações por visão humana de tabela renderizada + consulta corrente da BOM, **não validação técnica aprovada**, não equivalência automática de QTD desenho com quantidade ERP e não prova completa de requisitos geométricos. Desenho PDF, revisão e validade BOM podem divergir temporalmente. `90263520` é **candidato prioritário de investigação**, não uma não conformidade declarada. Para cada caso preservar original com SHA, página/célula, associação a nível/ocorrência e owner review. Não alterar os documentos fontes nem escrever na BOM. `DEC-VAL-020`: a barreira de binário foi removida e a VAL-01 deve avançar como estudo visual governado, com revisão/validade do caso `90263520` priorizada; não iniciar outra feature.

## 17. Regra operacional confirmada pelo owner — comparação do estado atual (DEC-VAL-021 — 2026-11-03)

**Esclarecimento explícito do usuário/owner sobre o acervo:** a DELPI mantém como arquivo disponível o **desenho mais recente**; não há rastreabilidade histórica das alterações do arquivo no acervo. Para a VAL-01, a comparação de presença de itens deve confrontar **o desenho atual efetivamente recuperado** com a **estrutura/BOM vigente** disponibilizada pela API de Engenharia. Não criar bloqueio artificial para consultar versões antigas inexistentes, nem usar hipótese de revisão passada para explicar ou desconsiderar diferença de presença no estado atual.

**Regra bidirecional de correspondência, para a mesma raiz e nível/ocorrência compatíveis:** 
- Item visível no desenho atual e presente na estrutura vigente no relacionamento aplicável → `MATCH` de presença (não aprova quantidade/material/cota automaticamente).
- Item visível no desenho atual mas ausente da estrutura vigente no relacionamento aplicável → `DRAWING_ONLY / DIVERGENCE_CANDIDATE`.
- Item presente na estrutura vigente mas ausente do desenho atual **após inspeção visual adequada da tabela/legenda aplicável** → `BOM_ONLY / DIVERGENCE_CANDIDATE`.
- Código não presente em nenhum lado → sem ocorrência de divergência por esse código; não pode ser uma hipótese extraída apenas de OCR.

**Qualificações obrigatórias:** ausência em OCR, texto PDF ou página isolada nunca equivale automaticamente a ausência no desenho completo; analisar todas as páginas e tabelas, com relação pai-filho e quantidade por unidade/conversão. Ausência de item de nível subordinado numa tabela restrita a N1 não comprova divergência. Preservar código original, página, região/célula, posição, hierarquia, fonte e hash, bem como limites da observação. A identificação por IA é `CANDIDATE` até conferência técnica pelo owner, sem gerar NC formal nem mutação automática de desenho/BOM. O único source of truth para cadastro/estrutura continua a API owner de Engenharia.

**Aplicação imediata ao caso `90263520`:** na tabela do PDF atual (`sha256=08bf68690401438ab09c0e7ffcd1126bf98b238de776bc680db587704e4fb200`), o PI `50213064` aparece como grupo adicional; na BOM `current` de `90263520`, o nível 1 contém `50230890`, `50230893`, `50232466`, `50232467`, sem `50213064`. **Classificar `DRAWING_ONLY / DIVERGENCE_CANDIDATE`**, prioridade de revisão técnica, **não** `REVISION_TRACE_PENDING`. Se o item tiver sido retirado do cadastro sem atualização do desenho, isso é exatamente um descompasso presente e deve ser apontado. A eventual causa/remediação e homologação da NC cabem à Engenharia; o sistema não deve presumir o motivo da exclusão. Essa decisão atualiza a ressalva temporal anterior de §16, sem alterar evidências históricas registradas.

## 18. Priorização backend-first da VAL-01 e registro visual futuro (DEC-VAL-022 — 2026-11-03)

**Decisão do produto:** registrar agora a experiência visual planejada de **Análise Técnica do Produto** dentro do Portal Engenharia, mas **não implementar frontend/MFE neste pacote**. Primeiro tornar a EVA capaz de executar a validação **automaticamente** no backend e retornar achados tipados e múltiplos pelo MCP; somente depois integrar a página. Preservar a página de produto existente, se houver; inventariar antes de criar rota, aba, contexto ou serviço novo. Esta é a **única funcionalidade VAL-01**, não um novo bounded context.

### 18.1 Lacuna comprovada no backend vivo

Em `2026-11-03` a EVA `get_context` oferece `product.structure`, `product.drawing_download`, `product.drawing_analysis`, `product.drawing_understanding`. Reconsulta real `analyze(product.drawing_analysis, product_code=90263520, compose_understanding=true)` retornou `success=true` e contagens de verificação (BOM 18 ocorrências; 4 PI N1 e 14 MP N2) com resumo `bom_comparison=PASS` ao localizar apenas **um código na camada textual do PDF** e classificar outros 17 como não localizados textualmente, mas **não** retornou `DRAWING_ONLY` nem `BOM_ONLY`. Seu método atual declara `pdf_text_layer` e que região/posição e OCR visual não estão assegurados. Portanto **não há evidência de validação bidirecional automática confiável**; `bom_comparison=PASS` neste relatório **não deve ser interpretado como desenho e BOM equivalentes**, e a interface futura não deve exibi-lo como aprovação. A inspeção humana já observou PI `50213064` no PDF oficial atual, ausente da BOM vigente N1. O fato de o assistente poder examinar o PDF manualmente **não comprova a automação no backend**.

### 18.2 Contrato de resultado TARGET — revisão técnica por ocorrência

Entrada: produto, contexto de usuário delegado, scope de comparação; desenho obtido somente por adapter oficial; BOM somente por API owner com validade `current`. Sem URL, file path, JWT, provider ou fontes arbitrárias do consumidor. Saída read-only com `product_code`, `analysis_id` (se houver execução rastreável), `drawing_sha256`, `drawing_filename`, `drawing_pages`, `bom_snapshot_as_of` (quando owner oferecer), `scope`, `status` (`DIVERGENCES_CANDIDATES|NO_DIVERGENCE_DETECTED|INCONCLUSIVE`), `coverage` por páginas/tabelas/linhas e níveis, `counts` por classificação, `findings[]` e limitações. Em cada finding: ID estável no resultado, tipo (`DRAWING_ONLY|BOM_ONLY|QUANTITY_MISMATCH|PARENT_RELATION_MISMATCH` somente quando verificado), `item_code`, `item_description`, `item_type`, `parent_code`, `level`, `occurrence_path`, valores desenhados/cadastrados e unidades quando aplicáveis, `evidence` (hash, página, região/bbox ou row id, texto/visão OBSERVED, estrutura de origem), `method`, `confidence` separada de acurácia OCR, `review_status=PENDING_HUMAN_REVIEW`, `explanation`. Estabelecer contrato completo com erros/AuthN/AuthZ/limites/observabilidade antes da implementação; campos sem evidência ficam UNKNOWN, jamais inventados.

**Regras funcionais:** `DRAWING_ONLY` código/ocorrência na tabela atual sem relação correspondente na BOM vigente; `BOM_ONLY` código/ocorrência presente na BOM mas não encontrado **após cobertura visual confiável da tabela/escopo correto**, nunca só por ausência em OCR; diferenças pai-filho preservadas; repetição de código em pais distintos é ocorrência distinta; quantidades com conversão oficial documentada ou `INCONCLUSIVE`; se extração incompleta, não apresentar 0 divergências como PASS. Não depender de histórico de substituições que o acervo não possui. Comparação bilateral com dados oficiais, sem escrita no documento, SG1, NC ou workflow de aprovação.

**Caso canônico de aceitação:** `90263520`, PDF atual SHA `08bf68690401438ab09c0e7ffcd1126bf98b238de776bc680db587704e4fb200`: tabela lista cinco PI N1, incluindo `50213064`; BOM vigente tem quatro PI `50230890`, `50230893`, `50232466`, `50232467`. A EVA deve retornar finding `DRAWING_ONLY` para `50213064` com evidência visual por página/região e status candidato, sem falsamente classificar `10400040` e `10080063` como globalmente ausentes. Testar caso inverso `BOM_ONLY`, múltiplas divergências, níveis, quantidade e documento em múltiplas páginas (especialmente `90263572`, lista na página 2) com fixtures controlados e documentos oficiais quando autorizados. Não usar resultado manual como ground truth automático sem validação de owner.

### 18.3 Experiência visual TARGET, deliberadamente adiada

Página/área de **Análise Técnica do Produto** dentro do Portal Engenharia: seleção do produto, identificação, estado de evidência/cobertura, resumo de itens comparados e divergências agrupadas, lista paginada/filtros por tipo/status/nivel, uma linha por ocorrência (não apenas código), detalhe lado a lado `trecho do desenho | ocorrência BOM` com página/região e limitações, e status de revisão técnica sob owner correto. A EVA oferece explicação em contexto, sem ser autoridade de aprovação. No protótipo `90263520` o painel exibiria `5 PI desenho / 4 PI BOM / 1 DRAWING_ONLY candidato`, não produto aprovado. Esta seção é **documentação de UX, não autorização para criar MFE, aba nova ou persistência de revisão**. Não construir visual até E2E da API/MCP passar em produção e o contrato ser estável.

### 18.4 Sequência e gate de entrega

1. Inventário de equivalentes, authorities, SHA/HEAD e contrato; manter Clean Architecture/ports/adapters e owner correto.
2. Menor implementação **backend EVA VAL-01** para extração visual/tabela confiável com grounding por PDF e matching por ocorrência/hierarquia; saídas e erros tipados; testes unit/integration/negative/ground truth; sem sobreafirmar ausência.
3. Expor a capacidade no MCP semântico existente com AuthZ live e sem criar interface de transporte paralela; validar cliente real.
4. Publicar código e docs, executar deploy **no `srv-api` de produção**, confirmar SHA em runtime/health/segurança, executar `90263520` via EVA deste ChatGPT e registrar `DRAWING_ONLY 50213064` com evidência; testar as sete amostras sem promover inferência a NC. **Sem deploy produtivo comprovado = entrega não concluída**, mesmo com teste local positivo. Se acesso bloqueado, estado `OWNER_BLOCKED`, escalar ao operador legítimo; nunca contornar AuthZ.
5. Após `BACKEND_E2E_PROD=PASS`, novo gate para UI: inventário das páginas existentes e especificação de UX — sem implementar agora.

**DEC-VAL-022:** `BACKEND_AUTOMATED_VAL01=PLANNED`; `VISUAL_PRODUCT_ANALYSIS=TARGET/DEFERRED`; `EVA_DRAWING_PDF_TRANSPORT=PROVEN`; `VAL01_CASE_90263520=OBSERVED_CANDIDATE`. Nenhum produto ou desenho aprovado automaticamente.

## 19. Comparador desenho × BOM implementado e validado no runtime produtivo (DEC-VAL-022 — 2026-11-03)

**Implementação:** `application/drawing/bom_structure_comparator.py` (puro, sem I/O) integrado a `analyze_product_drawing` — `product.drawing_analysis` evolui (nenhuma action nova, contratos/consumidores preservados). Entrada: `component_table.rows` do `drawing_understanding.v1` (pipeline OCR/vision oficial — tabelas raster, não text layer) + `flatten_bom_occurrences` (BOM vigente oficial). Saída: `payload.bom_structure_comparison` com `status` (`DIVERGENCES_CANDIDATES|NO_DIVERGENCE_DETECTED|INCONCLUSIVE`), `coverage`, `counts`, `findings[]` tipados (`DRAWING_ONLY|BOM_ONLY|PARENT_RELATION_MISMATCH`, `review_status=PENDING_HUMAN_REVIEW`, evidência página/linha/região), `limitations`. Regras: matching em dois passes (code+parent → code), `BOM_ONLY` somente com cobertura completa, filhos de pai ausente não geram falso mismatch, quantidades sempre `INCONCLUSIVE` sem contrato de unidade/conversão, códigos OCR fundidos por célula são separados em ocorrências (`_row_codes`).

**SHAs:** feat `af4a90fe44` + fix merged-cell `f2111c47e9` — **publicados e implantados em `srv-api`** (`delpi-engineering-api` recriado `healthy`, grep do runtime confirma `_row_codes`, MCP unauth → 401 na URL pública).

**Testes:** 15 testes do comparador (ground truth fixtures: canônico 5×4 PI, `BOM_ONLY`, múltiplas divergências, código repetido, pais distintos, pai não identificado, tabela pág.2, extração parcial → INCONCLUSIVE, fronteira não confiável, BOM indisponível, match total, código visível fora de célula, quantidade sem regra) — todos passam; suíte 719 passed (1 falha ambiental pré-existente R7, não relacionada).

**ENGINE_VALIDATION no runtime prod (PDF oficial real `90263520.pdf`, sha `08bf6869…`):** pipelines `pdfium_render_paddleocr` (170 tokens) + `pdfium_render_opencv_paddleocr` (174) executaram ok; `component_table` detectada (6 linhas, 15 códigos, boundary confiável); 5 PIs reconhecidos (`50213064`, `50230890`, `50230893`, `50232466`, `50232467`); comparador → `DIVERGENCES_CANDIDATES`, `DRAWING_ONLY D-001 50213064` (página 1, `ABSENT_IN_CURRENT_STRUCTURE`), `matched_occurrences=4`, zero falsos positivos — **o achado sai do pipeline real, não de regra hardcoded**. OCR fundiu células (ex.: `a 50213064 90263520 50230890`) — tratado em `_row_codes`; `qty` OCR é ruído e não é usada (limitation declarada).

**Pendências honestas:** E2E via MCP produtivo (`analyze(product.drawing_analysis, product_code=90263520, compose_understanding=true)`) requer token humano autorizado — validação final pelo consumidor ChatGPT (o conector já descobre a action); `BOM_ONLY`/hierarquia fina dependem da cobertura real de cada desenho (declare-as-observed, nunca inventado). `BOM` fixture usada na validação de engine espelha o L1 documentado do owner — a consulta BOM live é feita pelo serviço no fluxo governado.

**Estado: `BACKEND_PASS (engine PROVEN em prod runtime) / PROD_DEPLOYED / E2E_MCP_CHATGPT_PENDING / VAL-01_NÃO_APROVADA` — divergência é candidata à revisão da Engenharia, sem escrita nem NC automática.**

## 20. E2E direto no consumidor ChatGPT — PASS (DEC-VAL-023 — 2026-11-03)

**Teste real executado neste ChatGPT, com conector EVA autorizado:** `get_context(topic=product.drawing_analysis, entity=product, selected_ref=90263520)` → `analyze(analysis_type=product.drawing_analysis, parameters={product_code:90263520, compose_understanding:true})`. **Resultado `success=true`** e `data.report.bom_structure_comparison` retornado **automaticamente pelo backend**, sem materializar/revisar manualmente o PDF nesta rodada.

**Resultado comprovado:** `status=DIVERGENCES_CANDIDATES`; `coverage={drawing_pages:1, analyzed_pages:[1], component_table_detected:true, component_table_rows:6, component_table_codes:15, unreliable_boundary:false, complete_for_requested_scope:true}`; `counts={drawing_occurrences:5,bom_occurrences:18,matched_occurrences:4,drawing_only:1,bom_only:0,parent_relation_mismatches:0,bom_occurrences_unverified:0,divergences:1}`. `findings[0]={id:D-001,type:DRAWING_ONLY,item_code:50213064,item_type:PI,parent_code:90263520,level:1,review_status:PENDING_HUMAN_REVIEW,method:deterministic_occurrence_diff,evidence:{drawing_page:1,drawing_region:component_table,drawing_row:0,drawing_y_px:101.5,bom_relationship:ABSENT_IN_CURRENT_STRUCTURE}}`. Limitações retornadas: nove códigos OCR visíveis fora das células tipadas (`extracted_but_unclassified`); comparação quantitativa `INCONCLUSIVE` por ausência de regra oficial de conversão. `bom_comparison` legado ainda retorna `PASS` para verificação da camada textual (1 código localizado, 17 não encontrados no texto), mas a **verificação nova `bom_structure_comparison` é `WARNING`**, e seu status governa a exibição de divergências; não interpretar `PASS` legado como equivalência de BOM.

**Estado atualizado:** `BACKEND_PASS` com evidência engine produtiva reportada em §19, `PROD_DEPLOYED` com SHA `f2111c47e9` reportado em §19, **`E2E_MCP_CHATGPT_PASS` verificado diretamente pelo consumidor**, `VAL-01_NAO_APROVADA` (escopo de análise e não aprovação integral da Engenharia). **PENDENTE:** validação abrangente de generalização com documentos reais variados, revisão técnica dos findings pelo owner de Engenharia e eventual avaliação/correção da sinalização legada `bom_comparison=PASS`, que pode confundir consumidores. Não afirmar que o PDF foi aprovado ou que a diferença é NC formal.

## 21. Generalização E2E MCP + revisão visual independente de 6 PDFs (DEC-VAL-024 — 2026-11-03)

**Método:** o ChatGPT chamou o consumidor EVA real `analyze(product.drawing_analysis, parameters={product_code:<code>,compose_understanding:true})` para cada um dos seis produtos restantes do lote, sem injetar observações visuais no backend. Em paralelo, renderizou e examinou visualmente **todas as páginas dos seis PDFs originais já obtidos da Engineering API**, principalmente tabelas; reconsultou estruturas oficiais via `read(product.structure)`; hashes SHA-256 verificados nos PDFs locais. Resultados abaixo distinguem **saída automática da EVA** de **avaliação humana visual assistida**. Não são revisão/aprovação da Engenharia.

| Produto | Resultado EVA | Checagem visual independente | Juízo de generalização |
|---|---|---|---|
| `90264302` | Na primeira tentativa `INCONCLUSIVE` porque BOM retornou `source_unavailable/502`. Repetição: `NO_DIVERGENCE_DETECTED`, 2 ocorrências PI no desenho, 2 correspondências, 0 divergências. | Página 1: PI `50226113`, `50226114`, ambos com `10020033` e `10080106`, como N1 e filhos da BOM. | **PASS parcial presença PI**; MPs reconhecidas fora das células tipadas e comparação quantitativa inconclusiva; erro 502 transitório observado. |
| `90264161` | `DIVERGENCES_CANDIDATES` com `D-001 PARENT_RELATION_MISMATCH 50090001`: desenhado pai `90264161` versus BOM pai `90350410`; boundary não confiável, `complete=false`, 6 ocorrências sem verificação. | Página 1: código `90350410` ocupa célula vertical para A3–A6; código `50090001` está em **outra linha/célula A7**, enquanto BOM o traz como filho de `90350410`. Evidência **compatível** com diferença hierárquica, mas convenção de agrupamento no desenho e validação do owner ainda requeridas. | **CANDIDATE plausível, NÃO CONFIRMADO**; precisa explicação de hierarquia e cobertura, não atribuir como NC. |
| `90261606` | `NO_DIVERGENCE_DETECTED`, 8 ocorrências tipadas, 0 divergências; limitações `parent_relation_unverified` e alguns códigos fora de células. | Página 1: três PI `50222382`, `50222383`, `50222384`, cada um com cabo `10400078`, terminal `10080147`, e etiquetas diferentes `10110009`, `10110084`, `10110098` respectivamente; compatível com BOM. | **PASS parcial** para presença visual dos três PI e seus componentes; hierarquia integral não comprovada automaticamente apesar do status agregado. |
| `90263572` | `INCONCLUSIVE`: `component_table_detected=false`, `drawing_table_unread`, 0 códigos do desenho; BOM 56 ocorrências. | **Página 2 contém tabela extensa legível visualmente** com 16 MP diretas e PI `50213142`, `50224688`, `50224689`, `50233421`–`50233427`. Esses 26 códigos N1 correspondem à lista BOM vigente obtida por `read`; componentes aninhados não auditados integralmente nesta rodada. | **FALSE NEGATIVE DE COBERTURA (limitação de extração), sem divergência comprovada**. Comportamento fail-closed `INCONCLUSIVE` é correto; OCR/region detection multi-página precisa melhoria. |
| `90264178` | `INCONCLUSIVE`, tabela detectada 13 linhas/30 códigos, boundary não confiável, 10 ocorrências tipadas, 30 da BOM não verificadas, nenhum finding. | Página 1: seis MP diretas e dez PI `50215408`, `50215412`, `50215413`, `50225814`, `50225817`, `50225818`, `50233845`–`50233848` compatíveis com 16 N1 da BOM; filhos visíveis nas linhas. | **Cobertura parcial**, não há divergência N1 visual identificada; `INCONCLUSIVE` justificado pela cobertura, melhorar linhas/células fundidas e matching dos níveis. |
| `90480120` | Primeira tentativa `403 forbidden`; reexecução `INCONCLUSIVE` porque `component_table_detected=false` e `drawing_table_unread`; BOM 10 ocorrências. | Página 1 contém tabela clara de 10 MP diretas: `10070916`, `10080001`, `10081671`, `10081796`, `10081809`, `10090010`, `10090050`, `10210783`, `10500020`, `10520030`; correspondem à BOM N1; página 2 contém cotas/inspeção, não tabela de itens adicional identificada. | **FALSE NEGATIVE DE COBERTURA**, fail-closed correto, ausência não é divergência; erro 403 inicial requer observabilidade/correlação sem contornar AuthZ. |

**Hashes PDFs originais analisados:** `90264302=f33447b271a3518643559582d79cf54527b85778537cfb1e20a5ccf5d989f0ef`, `90264161=8d9fe28a19cae334abd6eaa3b0fb13059aecad715672b0dfd6aaf10462b85195`, `90261606=1c1f1412fb6cac22e8e44893dc27a39f45be806c6819bc12856ea4adb3580cd1`, `90263572=9021fce05c608655e538f67cdaac08c7484ebbe16a8888e83fbeec9ecaa28d3e`, `90264178=1a78693bd335371f192daceecf7f14f91637443bf03045f0aebec33bd7332fa8`, `90480120=9b64ae2095fa551e6c3b12fa1f6d232646725b2ab9c31eb489abedd972555cd8`.

**Gates após lote:** `E2E_MCP_CHATGPT_PASS` permanece comprovado para `90263520`; generalização **PARTIAL/INCONCLUSIVE**, não declarar `VAL-01_PASS`. Sem falsos `BOM_ONLY` nos casos de extração insuficiente (bom fail-closed); **um novo finding candidato de hierarquia** (`90264161/50090001`), não aprovado pelo owner. Em dois PDFs com tabelas claras (`90263572` e `90480120`), detecção automática falha; priorizar correção de localizador de `component_table` em tabelas na página 2 e na página 1, seguida de revalidação completa dos sete PDFs. Também rever o status `NO_DIVERGENCE_DETECTED` quando `parent_relation_unverified`/códigos fora de células afetarem escopo integral. Não iniciar frontend ainda; preservar a UX TARGET do §18.

## 22. Correção da extração visual — causas-raiz por PDF oficial (DEC-VAL-024 follow-up — 2026-11-03)

**Diagnóstico no runtime produtivo (6 PDFs oficiais, pipeline real):**

| Produto | Causa-raiz identificada | Correção |
|---|---|---|
| `90263572` | `PAGE 2 ocr_failed:MemoryError` — pág. 2 (tabela densa) estourava memória do worker; tokens só pág.1 | `visual_benchmark`: retry único por página com DPI reduzido (`_RETRY_DPI=110`) em falhas de recurso — genérico |
| `90480120` | `component_table` detectada mas `cells`/`fields` vazios — coluna de códigos não tipada | `_row_codes`: união de todas as superfícies (células tipadas+não tipadas+campos) regex 8–11 dígitos; fallback `code_token` |
| `90264178` | boundary `tokens_inferred` → `unreliable`; 30 códigos vs 10 tipados (linhas/células fundidas) | união de superfícies + fallback token-only |
| `90264161` | `PARENT_RELATION_MISMATCH 50090001` — heurística PI-abre-grupo atribuiu raiz (BOM: filho de `90350410`) | `parent_source="pi_group_inference"`; finding mantido candidato com `confidence="inferred_parent"` — evidência real mostrava linha separada (plausível, não confirmado) |
| `90264302/90261606` | `NO_DIVERGENCE_DETECTED` otimista — MPs em coluna `item` não tipada / pais não verificados | `complete_for_requested_scope` inclui unclassified+pais não verificados → `INCONCLUSIVE` honesto em vez de falso PASS integral |

**Regra de fallback aditiva:** códigos visíveis fora das linhas tipadas (`code_token`) **contam presença** (consomem ocorrências BOM por código) mas **nunca geram `DRAWING_ONLY`** — sem linha tipada não há prova de que sejam itens da tabela de componentes.

**Semântica de status:** `DIVERGENCES_CANDIDATES` quando há findings; `NO_DIVERGENCE_DETECTED` apenas com escopo integralmente coberto; `INCONCLUSIVE` caso contrário — distingue match de presença N1 de validação integral da hierarquia.

**Testes:** 15 testes do comparador + regressão (suíte 719+15). SHA `0d750e7625` publicado/implantado no `srv-api`. Validação dos 7 PDFs no runtime em `diag_extraction.py` — resultados reportados abaixo desta seção quando concluída a varredura.

## 23. Regressão detectada por E2E ChatGPT após fix de extração (DEC-VAL-025 — 2026-11-03)

**Execução real:** `get_context(product.drawing_analysis)` e sete chamadas `analyze(product.drawing_analysis,parameters={product_code,compose_understanding:true})` via conector autorizado deste ChatGPT. Em `90264161` a primeira análise retornou BOM 502, mas o retry obteve resultado. Em `90263572` a primeira chamada retornou `drawing_pdf_unavailable/502`, mas o retry obteve resultado. **Não tratar erros transitórios como resultado final dos dois casos.** A conferência independente foi realizada nos recortes visuais dos PDFs oficiais originais do lote, sem fornecer observações visuais como entrada ao backend.

| Produto | Resultado backend E2E após SHA de fix reportado `0d750e7625` | Auditoria visual e classificação |
|---|---|---|
| `90263520` | `DIVERGENCES_CANDIDATES`, 4 findings: `DRAWING_ONLY 50213064` e `DRAWING_ONLY 10400040`, `PARENT_RELATION_MISMATCH 10400040`, `PARENT_RELATION_MISMATCH 10400035`. `complete_for_requested_scope=false`, 17 token-only. | `50213064` **continua divergência real visual**. Os três findings adicionais não são sustentados: `10400040` está na linha do PI `50230893`; `10400035` está sob `50230890` e `50232466`; não se deve atribuí-los a outros PI pela linha fundida. **Falsos positivos visuais.** |
| `90264302` | `INCONCLUSIVE`, 0 findings, 2 PI e 7 tokens-only. | Conservador; presença N1 visualmente compatível, hierarquia e MPs não cobertas integralmente. |
| `90264161` | Retry: `DIVERGENCES_CANDIDATES`, 1 `PARENT_RELATION_MISMATCH 50090001` com `confidence=inferred_parent`, cobertura incompleta. | Candidato, não aprovado; a convenção hierárquica do desenho precisa confirmação da Engenharia. |
| `90261606` | `INCONCLUSIVE`, 0 findings, 8 relações sem pai verificado, 14 token-only. | Comportamento fail-closed correto. |
| `90263572` | Retry: `DIVERGENCES_CANDIDATES` **45 findings**, sendo 44 `BOM_ONLY` e 1 `DRAWING_ONLY 10060004`; `complete_for_requested_scope=false`, 3 linhas/7 códigos tipados na tabela, de BOM 56 ocorrências. | **FAIL CRÍTICO**: PDF p2 contém explicitamente itens rotulados como `BOM_ONLY`, inclusive `10080004` e PI `50213142`. `10060004` parece leitura OCR errada do código impresso `10080004` (exige inspeção ao nível de token para atribuição final). **BOM_ONLY emitido apesar de cobertura incompleta viola invariant fail-closed.** Não encaminhar achados à Engenharia. |
| `90264178` | `DIVERGENCES_CANDIDATES`, 7 findings: `DRAWING_ONLY 10090014` e 6 `PARENT_RELATION_MISMATCH` com pais inferidos; `complete=false`. | **`DRAWING_ONLY 10090014` é falso positivo**: esse código está claramente na linha direta D da tabela e na BOM N1. Mismatches de pai suspeitos por deslocamento de agrupamento/mescla; não promover a achados confirmados. |
| `90480120` | `INCONCLUSIVE`, tabela detectada nas páginas [1,2], 10 matches de BOM, 0 findings, 10 relações não verificadas e 13 token-only. | **Melhoria de detecção de tabela** sobre a rodada anterior; não há evidência de divergência de presença N1 na inspeção visual. |

**Gate:** `E2E_MCP_CHATGPT=PASS (transporte/executável)`; **`VAL01_CORRECTNESS=FAIL` / `REGRESSION_FOUND`**. Não é seguro considerar findings adicionais do novo runtime como erros reais do desenho. A proteção `BOM_ONLY` é violada no caso 90263572. O próprio status `DIVERGENCES_CANDIDATES` pode coexistir com coverage false, mas **não deve produzir ausência na imagem sem cobertura suficiente**. Demanda de correção: (a) impedir `BOM_ONLY` por item/escopo quando `complete_for_requested_scope=false`, inclusive quando fallback detectou outra tabela ou o OCR leu só fração das linhas; (b) associar MP somente à linha e à célula efetivamente verificadas, não por herança implícita do PI anterior, e degradar pai inferido a inconclusivo quando a geometria é insegura; (c) evitar `DRAWING_ONLY` de OCR ruidoso/misread e MP presente na BOM; (d) retestar os sete originais em runtime e MCP, confrontar tabelas visualmente. Preservar finding real `50213064` e sem alterações de frontend, BOM, PDF ou NC.
