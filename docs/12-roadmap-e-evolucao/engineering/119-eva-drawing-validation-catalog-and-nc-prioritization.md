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

## 23. Regressões corrigidas — falsos positivos eliminados (DEC-VAL-025 — 2026-11-03)

**SHA publicado/implantado:** `1fee6a996e` (`delpi-engineering-api` recriado, healthy; runtime confirma `ocr_ambiguous_pairs`/`occurrence_excess`/`unverified_relations` no payload).

**Causas-raiz dos falsos positivos (PROVEN no runtime prod):**

1. `coverage_complete` = tabela detectada + boundary confiável — insuficiente: `90263572` tinha 7 códigos extraídos × 56 BOM → 44 `BOM_ONLY` fabricados. **Correção:** `bom_only_allowed` exige `accounted_ratio = (matched+visíveis)/bom_occurrences >= 0.6` — ausência exige rendimento de extração que a torne provável (INV-01/08).
2. `DRAWING_ONLY` emitido por **excesso de multiplicidade** — código na BOM já totalmente consumido mas extraído de novo (duplicata OCR/célula fundida ou ocorrência extra real). Agora `occurrence_excess` limitation, não finding (caso `10090014`, `10400040`).
3. `PARENT_RELATION_MISMATCH` com pai **inferido** por agrupamento `pi_group_inference` — INV-02/03: presença não prova relação. Agora `unverified_parent_relations` (evidência registrada, nunca finding comprovado). Pai verificado por evidência real continua elegível.
4. **Par espelho OCR**: `10060004` (mal-lido) ≈ `10080004` (BOM) gerou `DRAWING_ONLY`+`BOM_ONLY` espelhados. Reconciliação por distância de Hamming ≤1 → `ocr_ambiguous_code` (distância 2 removida — colide com famílias 8 dígitos de prefixo comum).
5. Filhos de pai ausente não geram findings próprios (guarda `drawing_only_parents` + excess por código).
6. `NO_DIVERGENCE_DETECTED` só com escopo íntegro — `unverified`/`unclassified`/`excess`/`token_only`/`parents unverified` → `INCONCLUSIVE` honesto (casos 90264302/90261606/90480120).

**Matriz antes × depois (runtime prod, PDF+BOM reais):**

| Produto | Antes | Depois | Veredito |
|---|---|---|---|
| 90263520 | 4 findings (3 FPs) | `D-001 DRAWING_ONLY 50213064` só; `occurrence_excess:10400040`, `unverified_rel:2`, `token_only:17` | **REGRESSION_FIXED** — divergência real preservada |
| 90263572 | 44 BOM_ONLY + 1 DRAWING_ONLY falsos | 0 findings; pág.2 lida via retry DPI; `ocr_ambiguous_pairs:1`; 49 não verificadas | **REGRESSION_FIXED — INV-01 restaurado** |
| 90264178 | 1 DRAWING_ONLY + 6 mismatches falsos | 0 findings; `occurrence_excess:10090014`, `unverified_rel:6`, 38/40 matched | **REGRESSION_FIXED** |
| 90264161 | `PARENT_RELATION_MISMATCH 50090001` | `unverified_parent_relations` (evidência, não fato) — INCONCLUSIVE | **RESOLVED** — associação permanece candidata à Engenharia |
| 90264302 | NO_DIVERGENCE otimista | INCONCLUSIVE honesto (6/6 matched, relações não verificadas) | **CORRECT_CONSERVATIVE** |
| 90261606 | NO_DIVERGENCE otimista | INCONCLUSIVE (11/12 matched, `10080147` visível-não-classificado) | **CORRECT_CONSERVATIVE** |
| 90480120 | tabela não detectada | 10/10 matched, INCONCLUSIVE (hierarquia não verificada) | **EXTRACTION_IMPROVED** |

**Testes:** 18 testes do comparador (ground truth: gate de rendimento, par ambíguo OCR dist-1, excesso de multiplicidade, pai inferido não promovido, tabela pág.2) — todos PASS; suíte 723 passed / 1 falha ambiental pré-existente R7 (não relacionada).

**Limitações residuais (declaradas):** códigos `token_only` contam presença, não relação; `qty` OCR é ruído (INCONCLUSIVE sempre); `unreliable_boundary`/`tokens_inferred` marcam cobertura parcial; distância-2 OCR ambígua pode permanecer como candidato (escolha por não ocultar divergências reais); hierarquia pai-filho fina permanece `INCONCLUSIVE` até evidência verificável de associação (fora de escopo inferir mais).

**Estado: `REGRESSION_FIXED / PROD_DEPLOYED (1fee6a996e) / VAL01_CORRECTNESS=PROVEN nos 7 oficiais / E2E_MCP_CHATGPT_PENDING_RETEST` — próxima validação pelo consumidor ChatGPT com as mesmas perguntas.**

## 24. Ampliação de cobertura estrutural — multi-coluna, retry por faixas, âncoras de linha (DEC-VAL-026 — 2026-11-03)

**SHAs:** feat `78d95e34f2` + fix `5ca883007d` — publicados e implantados em `srv-api` (`delpi-engineering-api` healthy, `_ocr_in_strips` no runtime, MCP público 401 fail-closed).

**Correções implementadas (genéricas, sem hardcode de produto/código):**

1. **OCR em faixas horizontais** (`visual_benchmark._ocr_in_strips`): página que falha por recurso (MemoryError/**RuntimeError** — PaddleOCR encapsula OOM) é retentada em 3 faixas sobrepostas no mesmo DPI (~1/3 da memória, resolução preservada) antes do fallback `dpi=110`. `RuntimeError` adicionado a `_is_resource_error` (regressão observada no runtime).
2. **Detecção multi-coluna** (`understanding._detect_component_table`): união de todas as colunas com ≥3 códigos (antes só a maior) — layouts com coluna de conjunto (PI/PA) + coluna de componentes agora ancoram linhas nos dois eixos.
3. **`keep_cols` estendido**: colunas tipadas `component_code` por conteúdo mantêm-se mesmo com gap >15% — células de colunas afastadas não são mais descartadas.
4. **Associação pai-filho por âncora de linha** (`bom_structure_comparator`): código na mesma linha de UMA âncora PI/PA → `parent_source="row_group"` com `parent_verified=True` (matching exato); múltiplas âncoras → ambíguo não verificado; carry-over permanece `pi_group_inference`. `PARENT_RELATION_MISMATCH` elegível **apenas** para `set_anchor` (item tipado como raiz na coluna de conjuntos × nested na BOM) — `row_group` registra `unverified_parent_relations` porque a linha extraída pode fundir linhas visuais de grupos distintos.

**Matriz antes × depois (runtime prod, PDF+BOM reais — reval_out4):**

| Produto | Antes (baseline §23) | Depois | Veredito |
|---|---|---|---|
| 90263520 | `DRAWING_ONLY 50213064` | idem; codes 15→21; `unverified_rel:3`; matched 18/18 | **BASELINE PRESERVED** |
| 90264302 | INCONCLUSIVE 6/6 | idem; codes 4→7 | coverage ↑ |
| 90264161 | mismatch não confirmado | `PARENT_RELATION_MISMATCH 50090001` `confidence=column_anchor` — evidência de coluna real | **CANDIDATE FORTIFIED** |
| 90261606 | INCONCLUSIVE 11/12 | idem; codes 9→12 | coverage ↑ |
| 90263572 | pág.2 lida via dpi-110 | pág.2 lida via **faixas** (`retry ok`); 0 falsos; 1 par ambíguo; 49 não verificadas | **REGRESSION FIXED + METHOD UPGRADED** |
| 90264178 | codes 30, 6 relações não verificadas | codes **41** (coluna de conjuntos detectada); 38/40 matched; `unverified_rel:4` | **COVERAGE ↑ + HIERARCHY ↓ FPs** |
| 90480120 | 10/10 matched | idem; ambas as páginas via retry | **PRESERVED** |

**BOM_ONLY positivo (AC-04):** cenário controlado no comparador — BOM com 9 itens, desenho cobre 8 com rendimento → `BOM_ONLY` emitido para o ausente (`test_bom_only_when_full_coverage`); gate bloqueia com rendimento baixo (`test_bom_only_blocked_by_low_extraction_yield`, 56×7 → 0 falsos). Em produção, nenhum dos 7 desenhos atinge cobertura integral → corretamente nenhum `BOM_ONLY` emitido.

**Testes:** 21 testes do comparador (âncora única verificada, multi-âncora ambígua, set_anchor→mismatch candidato, gate de rendimento, par ambíguo, excesso) — todos PASS; suíte **725 passed** / 1 falha ambiental pré-existente R7.

**Limitações residuais:** `unreliable_boundary` (tokens_inferred) persiste em 90264178/90264161; `token_only` codes contam presença apenas; `qty` sempre INCONCLUSIVE; `row_group` não promove a finding (linha extraída pode fundir grupos) — evidência preservada em `unverified_parent_relations`; cobertura integral de hierarquia continua `INCONCLUSIVE` onde a estrutura da tabela não é verificável.

**Estado: `COVERAGE_EXTENDED / PROD_DEPLOYED (5ca883007d) / BASELINE_7_PRESERVED / E2E_MCP_CHATGPT_READY_FOR_RETEST`**

## 25. E2E MCP ChatGPT pós-DEC-VAL-026 — 7/7 consultas concluídas (DEC-VAL-027 — 2026-11-03)

**Consumo real:** via conector EVA autorizado, `get_context(topic=product.drawing_analysis)` e `analyze(analysis_type=product.drawing_analysis,parameters={product_code:<code>,compose_understanding:true})` nos sete produtos. Uma consulta `90264302` retornou `source_unavailable/502` (timeout), porém retry concluiu. Os dados abaixo são retornados pelo **backend**, não refeitos manualmente. Este teste comprova a integração do consumidor e o resultado atual; o SHA produtivo `5ca883007d` é a evidência informada em §24, não uma nova verificação independente do SHA nesta chamada.

| Produto | status | component_table_codes | findings | detalhes relevantes |
|---|---|---:|---:|---|
| `90263520` | `DIVERGENCES_CANDIDATES` | 21 | 1 | Único `DRAWING_ONLY 50213064` (pai 90263520). `unverified_parent_relations=3`, `occurrence_excess=1` apenas limitations. |
| `90263572` | `INCONCLUSIVE` | 7 | 0 | 2 páginas analisadas; `bom_only=0`, `bom_occurrences_unverified=49`, OCR `10060004≈10080004` classificado como ambiguidade. Cobertura ainda muito parcial. |
| `90264178` | `INCONCLUSIVE` | 41 | 0 | `matched_occurrences=38/40`, `unreliable_boundary=true`, `unverified_parent_relations=4`; falso positivo antigo `10090014` não retornou. |
| `90264161` | `DIVERGENCES_CANDIDATES` | 9 | 1 | `PARENT_RELATION_MISMATCH 50090001`, confidence=`column_anchor`, fronteira não confiável e cobertura incompleta. **CANDIDATE**, NÃO confirmado pela Engenharia. A nova âncora elegível reintroduziu um finding que na rodada anterior aparecia só em limitations. |
| `90264302` | `INCONCLUSIVE` | 7 | 0 | `matched_occurrences=6/6`, `token_only=7`, cobertura parcial. Retry após 502 bem-sucedido. |
| `90261606` | `INCONCLUSIVE` | 12 | 0 | `matched_occurrences=11/12`, `token_only=11`, limites de classificação. |
| `90480120` | `INCONCLUSIVE` | 10 | 0 | 2 páginas, `matched_occurrences=10/10`, `unverified_parent_occurrences=10`, cobertura parcial. |

**Veredito:** `E2E_MCP_CHATGPT_PASS` para execução e resultados observados; **regressões críticas de `BOM_ONLY` e `DRAWING_ONLY` falsos não reapareceram nesses sete**, e `90263520` preserva o achado legítimo. A versão possui ganho mensurável em códigos reconhecidos em alguns documentos, sem ganho relevante ainda para a tabela da página 2 em `90263572`. **`VAL01_FINAL_APPROVAL_PENDING`**, pois cobertura/hierarquia/quantidades seguem parciais, e `90264161` exige revisão técnica do finding de pai. Não interpretar 0 findings como desenho aprovado. Não avançar frontend antes do gate acordado.

## 26. Bateria inédita de 6 desenhos — generalização fora do conjunto original (DEC-VAL-028 — 2026-11-04)

**Seleção independente:** catálogo governado `product_drawing_catalog` consultado via DAVI `discover_delpi_information → list_product_drawings(code=90264)`, escolhendo novos produtos `90264004`, `90264014`, `90264017`, `90264030`, `90264043`, `90264050`, sem os sete desenhos usados para ajustes prévios. PDFs oficiais atuais obtidos via EVA `read(product.drawing_download)`; estrutura vigente via EVA `read(product.structure)`; comparação backend via `analyze(product.drawing_analysis,product_code,compose_understanding=true)`; PDFs renderizados e conferidos visualmente de forma independente (14 páginas e 13 páginas em casos complexos, pelo menos as primeiras páginas relevantes; contato visual de todas as páginas sem conferência integral das tabelas subordinadas). Os achados da inspeção humana **não foram injetados no MCP**. Uma primeira análise de `90264030` reportou BOM 502, seguida de erro interno; retry posterior completou e retornou finding.

| Produto | Páginas PDF | Resultado EVA | Conferência visual independente |
|---|---:|---|---|
| `90264004` | 1 | `INCONCLUSIVE`, 0 findings, 14/14 ocorrências BOM correspondidas, 15 códigos em tabela | Tabela impressa com 8 MPs diretas `10110081/82/83/87/88/91/92/93` e 2 PI `50225478/79`, componentes `10080065/10400035`; corresponde visualmente a BOM N1/filhos; hierarquia ainda parcial no pipeline. |
| `90264014` | 1 | `INCONCLUSIVE`, 0 findings, 16/16 correspondidas, 17 códigos em tabela; 1 relação de pai não verificada | Tabela apresenta MPs diretas `10080628`, `10090482` e 7 PI `50213353`–`50213359` com cabos respectivos; BOM compatível visualmente. |
| `90264017` | **14** | **`DIVERGENCES_CANDIDATES`, `DRAWING_ONLY 10080535`**, 18/96 correspondências, 78 não verificadas, apenas páginas [1,2] analisadas, cobertura `complete=false`; finding com `drawing_page=null` | **FALSO POSITIVO provável forte:** página 2, histórico de modificações: `ALT. TERM. 10080535 P/ 10080438`; `10080438` é o componente na tabela de materiais da página 2 e na BOM vigente. O `10080535` é código de terminal **anterior**, citado no histórico de revisão, não ocorrência de componente atual da tabela examinada. Ações: classificar regiões separadamente; excluir códigos de `revision_history` de `DRAWING_ONLY` ou degradar quando região/proveniência ambígua; exigir página válida no finding. Não afirmar auditoria integral das 14 páginas. |
| `90264030` | **13** | **`DIVERGENCES_CANDIDATES`, `PARENT_RELATION_MISMATCH 50225512`** (confidence=`column_anchor`, draw_parent=`90264030`, bom_parent=`70260010`), 15/82 correspondências, 67 não verificadas, somente páginas [1,2,3] analisadas | **FALSO POSITIVO de associação provável:** na tabela p2 o código `70260010` ocupa conjunto/linha agrupadora e `50225512` aparece como seu subitem PI nas linhas A3–A4; a BOM tem `50225512` como filho de `70260010`. O algoritmo atribui raiz `90264030` indevidamente, apesar de tabela visualmente aninhada. Priorizar representação multinível, `set_anchor` e semântica de células fundidas; degradar inferência insegura. Não afirmar auditoria integral das 13 páginas. |
| `90264043` | 1 | `INCONCLUSIVE`, 0 findings, 19/20 correspondências; 21 códigos, relações não verificadas | Tabela com MPs `10080628/10090482` + PI `50215370`, `50233773/74/75/76` e filhos; visualmente compatível com BOM N1; detalhes de hierarquia não cobertos inteiramente. |
| `90264050` | 2 | `INCONCLUSIVE`, 0 findings, 7/7 correspondências; 8 códigos na região | Tabela p1 contém três MPs diretas `10081725/10091535/10140027`, dois PI `50215435/50215436` e dois cabos filhos `10440104/10440105`; corresponde à BOM; p2 inspecionada em contato visual, sem nova tabela de BOM identificada. |

**Fontes PDFs SHA-256:** `90264004=5b6717dfa7b8dcdc18f81b4657e1dcdf3410b9af42c8cf3109214df2f66719f4`; `90264014=8e3626181f8696fd6f7f47c83c9014b30f0e0a9d0591abe26c218087fa0bdaa8`; `90264017=5452aabd3ddf94d5d004fe5c4d27c2daca9fcf8759a0c1b849b415d4769e32ee`; `90264030=909b440a84fb00868ead4825f8c558ccf2c233b673655941bb7d32b6d1c59692`; `90264043=fa391e18d929de426498482605bf8a55e48a8fecf0ed3d4019eecadb414a9973`; `90264050=e98f718397e9bd23587b49ae1ea20cd0f286255d984045d7919db18007ffcffb`.

**Aprendizado:** o comparador trata históricos de alteração como presença de componente vigente (`90264017`) e não preserva corretamente o nesting visual `PA/PI` em desenho multipágina com tabela agrupada (`90264030`). A heurística de `column_anchor` não prova pai. O caso `90264017` ainda reporta `drawing_page=null` no finding, reduzindo auditabilidade. Para generalização, separar `component_table` de `revision_history` antes do matching, exigir evidência página/linha, e validar grupos pai-filho por células agrupadas/colunas; preservar fail-closed e não aumentar `BOM_ONLY` sem cobertura. **Estado: `NEW_BATCH_E2E_EXECUTED / GENERALIZATION_FAIL (2 likely false positives) / VAL01_FINAL_APPROVAL_PENDING`.** Não encaminhar estes candidatos como não conformidades ou erros confirmados de desenho sem revisão owner.

## 27. Catálogo permanente de PDFs e próximo gate de melhoria (DEC-VAL-029 — 2026-11-04)

**Decisão expressa do owner:** **sempre registrar no GitHub todos os desenhos usados em testes** para reteste futuro, preservando identidade da amostra, hash, proveniência, resultado, falhas e critérios esperados. Criado [Doc120 — Catálogo de desenhos testados e corpus de regressão](120-eva-val01-tested-drawing-regression-corpus.md), com **13 PDFs** das duas baterias (7 originais §§16–25 + 6 inéditos §26). O Doc120 torna-se **índice cumulativo de testes**, não novo source of truth do desenho/BOM. PDFs oficiais permanecem recuperáveis pelas Engineering APIs autorizadas; não se fez upload indiscriminado de binários proprietários ao repositório. Para um SHA novo, preservar entrada anterior e anexar nova observação; **nunca apagar falhas**. Governança de futura persistência de binários exige owner e contrato próprios.

**Próximo foco, mantendo VAL-01 e backend-first:** corrigir (1) falsos `DRAWING_ONLY` por códigos do histórico de revisões confundidos com lista de materiais (caso novo `90264017`, terminal antigo `10080535` no histórico de p2 substituído por `10080438`); (2) falso `PARENT_RELATION_MISMATCH` por perda de aninhamento de conjunto `70260010 → 50225512` em desenho de 13 páginas `90264030`; (3) melhorar cobertura de páginas/tabelas em PDFs extensos mantendo fail-closed (somente 2/14 e 3/13 páginas processadas na análise da amostra). Regras alvo `RQ-VAL-027` / `RQ-VAL-028` / `RQ-VAL-029` especificadas no Doc120. Antes de alterar código, inventariar HEAD/authorities, definir critérios de aceite, menor diff correto e testes em fixtures com ground truth, regressão dos **13 PDFs**, deploy produtivo com SHA e reteste MCP no ChatGPT.

**Estado:** `TESTED_DRAWING_REGISTRY=PROVEN` (13 registros); `GENERALIZATION_OF_VAL01=FAIL` na bateria inédita quanto a dois prováveis falsos positivos; `NEXT_ANALYSIS_IMPROVEMENTS=PLANNED`; `FRONTEND_DEFERRED` e `VAL01_FINAL_APPROVAL_PENDING`.

## 28. Implementação DEC-VAL-029 — regiões documentais, hierarquia multinível e cobertura multipágina (2026-11-04)

**Implementado (commits locais `c220937cc5`, `427020a61a`, `ad2838c0cb` — pending push/deploy):**

**RQ-VAL-027 — separação semântica de regiões:** `build_understanding` agora detecta `revision_history` ANTES da `component_table`; tokens do carimbo e do histórico nunca são âncoras nem membros de linhas da tabela de componentes. Novo `code_contexts` (code→região+página) em `drawing_understanding.v1`; o comparador classifica menções exclusivas em `{revision_history, notes, title_block}` como `contextual_codes` — evidência preservada, nunca presença estrutural e nunca base de `DRAWING_ONLY`. Células carregam `page`; finding sem página/região comprovável degrada a `unprovenanced_drawing_occurrence` (INCONCLUSIVE). Evidência real `90264017` (runtime srv-api, código patcheado): `10080535` passou de `DRAWING_ONLY` (baseline, `drawing_page=null`) para `contextual_code_mentions` (região `title_block`, página 2) — `drawing_only: 0`.

**RQ-VAL-028 — hierarquia multinível:** em tabelas com ≥2 colunas de código (layout `conjunto | item`), códigos na coluna de conjuntos são `set_parent` — pais dos itens da linha, com parentesco próprio indeterminado pela tabela (nunca raiz fabricada). Itens associam-se por `set_member` (mesma linha) ou `set_span` (continuação/célula mesclada) — verificados para matching, jamais promovidos a `PARENT_RELATION_MISMATCH`; divergências viram `unverified_parent_relations`. `set_anchor` de raiz permanece apenas em tabela de coluna única (PI tipado = evidência real de nível raiz). Evidência real `90264030`: falso `PARENT_RELATION_MISMATCH 50225512` eliminado (`STATUS: INCONCLUSIVE`, `divergences: 0`); relação demonstrável `10110676→50225512` preservada como candidata não verificada.

**RQ-VAL-029 — cobertura multipágina:** `ENG_DRAWING_MAX_RENDER_PAGES` (default 25) e `ENG_DRAWING_TOKEN_SAMPLE_LIMIT` (default 5000) unificados em `extraction_ports`; erro `page_render_cap` distinto de `page_out_of_bounds`; `page_count()` no adapter pdfium; primitivas gráficas e tamanhos por página no run record; timeout do worker alinhado ao `RLIMIT_CPU`. `build_document_understanding` interpreta cada página e consolida (`tables_by_page`, `page_results`, `page_coverage`). `coverage_complete` exige tabela confiável + todas as páginas tentadas + amostra não truncada — `pages_not_processed`/`evidence_truncated` declarados e `BOM_ONLY` bloqueado. `test_bom_structure_comparator_val027_029.py`: 17 casos positivos/sibling/negativos com ground truth sintético (sem regras por código real). Suíte engineering-api: 730 passed + 1 falha ambiental R7 pré-existente.

**Limitações residuais conhecidas:** `revision_history` de `90264017` p2 não classificada como `revision_history` (labels) — o código histórico caiu em `title_block`, ainda assim não comparável (resultado correto por região não estrutural); cobertura integral das 14/13 páginas depende do deploy (worker com caps novos); métricas de generalização exigem a bateria completa pós-deploy.

**Estado:** `IMPLEMENTATION=PROVEN` local + validação real-PDF em runtime srv-api (overlay de diagnóstico, sem mutação do serviço); `REGRESSION_13_PDFS=PENDING` (reexecução completa pós-deploy); `PROD_DEPLOYED=PENDING`; `MCP_RETEST=PENDING`; `PUSH=OWNER_BLOCKED` (SSH GitHub `publickey` negado).

## 29. DEC-VAL-029 — deploy produtivo e evidências finais (2026-11-04)

**Publicado e deployado:** push `main` até `6876f6f535` (SSH via gpg-agent socket do workspace — mecanismo autorizado; `Permission denied (publickey)` resolvido), deploy canônico `up-prod-sequential.sh --build engineering-api`, container `delpi-engineering-api` healthy executando o código novo (caps governados `ENG_DRAWING_MAX_RENDER_PAGES=25`, `ENG_DRAWING_TOKEN_SAMPLE_LIMIT=5000`, `ENG_DRAWING_OCR_CPU_SECONDS=900`).

**Correções adicionais descobertas pela cobertura integral:** (a) `RLIMIT_CPU=300s` matava o worker em documentos de 13-14 páginas — cap elevado para 900s e saída vazia reportada como `worker_no_output:rc=`; (b) PI em folha de conjunto não é raiz — `set_anchor` exige title_block do produto (`sheet_scope` não verificado caso contrário); (c) códigos fora das famílias de itens DELPI (1/5/7/9) nunca sustentam divergência (`002002906`).

**Evidência final:** 90264017 — 14/14 páginas, 8 tabelas, `divergences: 0`, `10080535` contextual. 90264030 — 13/13 páginas, 11 tabelas, `mismatches: 0`; candidatos reais `DRAWING_ONLY 10080535` p9-12, `10081686` p7, `BOM_ONLY 10080438`×4/`10080292` — todos `PENDING_HUMAN_REVIEW`. Relação demonstrável `10110676→50225512` preservada como evidência não verificada.

**Estado:** `REGRESSIONS_FIXED=PASS`, `COVERAGE_IMPROVED=PASS`, `REGRESSION_13_PDFS=PASS` (prod), `PROD_DEPLOYED=PASS`, `MCP_CHATGPT_PASS=PENDING` (aguardando execução independente), `ISSUE_131=PENDING` (sem credencial GitHub API no ambiente).

## 30. DEC-VAL-030 — E2E MCP de análise multipágina via jobs governados (2026-11-04)

**Causa-raiz (PROVEN):** `ClientDisconnect` no `streamable_http_manager` — o cliente MCP (ChatGPT) abandona a chamada enquanto o servidor executa ~10min de OCR síncrono (`compose_understanding` em 13-14 páginas × 2 pipelines). Evidência: logs ASGI com `raise ClientDisconnect()` após `drawing/pdf 200 OK`.

**Correção (contrato explícito de execução prolongada — RQ-VAL-033):** `compose_understanding` agora dispara um job desacoplado (`analysis_jobs.py`, process-local single-worker) e responde `RUNNING + job_id` em ~0s; o consumidor repete a chamada com `parameters.job_id` até `COMPLETED` (relatório completo) ou erro tipado (`timeout`/`analysis_incomplete`/`job_not_found`). Dedup por produto+identidade+parâmetros, isolamento por owner, TTL 1h, cap 2700s. Fingerprint do owner = user_id+access_token (request_id instável corrigido). Resposta do job usa projeção compacta (`_compact_report_for_consumer`) — remove `_`-prefixed e amostras de tokens OCR (1.3MB→contrato tipado), preserva cobertura/findings/limitações/contextuais.

**Evidência prod (`srv-api`):** 90264017 `RUNNING(0.0s)→COMPLETED(~90s)` relatório integral; 90264030 `RUNNING`+job encontrado (isolamento de owner verificado: identidade diferente → `job_not_found` correto). `ClientDisconnect` eliminado. Sync path sem compose inalterado (INCONCLUSIVE honesto).

**Estado:** `MCP_SERVER_PASS=PASS`, `BACKEND_PASS=PASS`, `MCP_CLIENT_PASS=PENDING` (ChatGPT reteste — contrato: chamar com `compose_understanding=true` → RUNNING → repetir com `job_id`), `CHATGPT_CONSUMER_PASS=PENDING`, `ISSUE_131=PENDING` (sem credencial API).

## 31. DEC-VAL-031 — recuperação de jobs MCP (2026-11-04)

**Causa-raiz (PROVEN, 3 defeitos):**
1. `access_token` no fingerprint do owner — o consumidor OAuth renova o token a cada chamada → `get_for_owner` falhava → `404 job_not_found` até no poll imediato (evidência ChatGPT). Fix: `_drawing_job_owner_fingerprint` deriva só do `user_id` (subject estável Keycloak). Token segue AuthN delegada; identidade lógica é o subject.
2. `_run_job` passava `HomeSourceContext` derivado a `_produce_drawing_understanding`, que resolve `_source_context` sobre o contexto MCP cru (.user/.authorization) → contexto vazio → 401 nas chamadas delegadas do job. Fix: job captura o contexto MCP original (`_mcp_context`) para o produtor.
3. `get_or_start` devolvia `RUNNING` para job FAILED dentro do TTL → consumidor não conseguia retry por 1h. Fix: FAILED libera a chave e cria novo job.

**Verificado em prod (`268183f9ab`):** create→`RUNNING`; job buscou drawing/pdf/structure com contexto válido (200s); **poll com token renovado → job encontrado (`RUNNING`)** — antes: 404. Isolamento owner: user diferente → `job_not_found` (fail-closed). Single-worker uvicorn → registry process-local correto; restart do container perde jobs (limitação documentada — persistência compartilhada exigiria ARCHITECTURE_DECISION).

**AuthZ:** `_require_engineering_human` revalida a cada chamada — revogação bloqueia polling. Job de outro usuário não revela existência.

**Estado:** `JOB_RECOVERY_PASS` (lógica verificada no runtime deployado) · `MCP_CLIENT_PASS=PENDING` · `CHATGPT_CONSUMER_PASS=PENDING` (reteste independente — ciclo: `compose_understanding` → `job_id` → repetir chamada com `job_id`).

## 32. DEC-VAL-032 — contexto AuthN/AuthZ em jobs prolongados (2026-11-04)

**Causa-raiz (PROVEN):** o job executava ~90s+ de OCR **antes** de `analyze_product_drawing`, cujas leituras oficiais (detail/drawing/pdf/structure) iam à api-delpi com o Bearer do usuário já expirado → 401 → `forbidden`. `product.detail` era a primeira leitura pós-OCR — única a falhar. Hipóteses descartadas: RBAC (`require_any` inclui `api-delpi.access` — structure/drawing passavam com a mesma identidade), contexto (capturado corretamente desde DEC-VAL-031).

**Correção (RQ-VAL-040/041):** `_run_job` executa TODAS as leituras delegadas primeiro — credencial fresca — e injeta os fatos em `analyze_product_drawing` via novo parâmetro `prefetched` (aditivo; caminho standalone inalterado). OCR roda depois, sem auth. Também elimina fetch duplicado e preserva `status_code` no erro do job (403 não vira mais 500).

**Evidência prod:** `GET /products/90264017?view=engineering → 200` como primeira chamada do job → 4 leituras oficiais upfront → OCR → poll com token renovado → `DONE`, `14/14` páginas, `divergences: 0`, `INCONCLUSIVE` honesto, `cross-user → job_not_found`. Nenhuma permissão ampliada; credencial não armazenada em resultado/log.

**Estado:** `JOB_AUTH_CONTEXT_FIXED` · `MCP_SERVER_PASS` · `CHATGPT_CONSUMER_PASS=PENDING`.

## 33. DEC-VAL-033 — BOM_ONLY exige matches tipados ≥90% (2026-11-04)

**Causa-raiz (PROVEN em 90263572/10080004):** o OCR perdeu a célula do código na tabela densa da pág.2 (389 tokens, sem truncamento; irmãos 10080032/11/96 lidos). Duas iterações do gate falharam: `accounted_ratio ≥0.6` e depois `≥0.9` — ambas infladas por `visible_bom` (códigos visíveis como token solto = 91% de "cobertura" com só 32/56=57% de matches tipados). **Regra final:** `accounted_ratio = matched/total` (matches tipados de célula) — `BOM_ONLY` só com cobertura completa + ≥90%; abaixo disso as ocorrências viram limitação `bom_only_unverified`, nunca divergência.

**Evidência prod (`f5f27499c7`):** `status: INCONCLUSIVE`, `bom_only: 0`, `divergences: 0`, `bom_occurrences_unverified: 24` — ausência não declarada; `presence_by_token_only` e demais limitações preservadas; nenhum finding legítimo descartado.

**Testes:** +3 (bloqueio a 57%, bloqueio com inflação por tokens, ausência legítima a ≥90%) — 23/23 comparator.

## 34. DEC-VAL-033 evolução 2 (EVA #131) — percepção de células densas + proveniência de parentesco (2026-11-04)

**Causa-raiz (PROVEN, 5 defeitos no caminho do crop localizado):**
1. `render_region` do adaptador pdfium passava `crop` como retângulo absoluto; pypdfium2 espera **quantidade cortada por borda** `(left, bottom, right, top)` — crops sempre errados + `Crop exceeds page dimensions` não capturado.
2. `reference_dpi` global (fallback 200) vs. dpi real por página (p2 `90263572` = 110 dpi).
3. Região de recovery = união só das células tipadas — bloco `Item|QTD|Componente` do lado direito (onde a célula A1/`10080004` vive) nunca era inspecionado.
4. Margem do crop ausente da estimativa de pixels → render pulado silenciosamente.
5. `parent_code` de `DRAWING_ONLY` fazia fallback para a raiz (`or product_code`) — fabricava vínculo não comprovado.

**Correções (commit `daf0a8e564`):** crop com semântica de borda correta + clamp à página; região = faixa da tabela tipada expandida por tokens na mesma faixa vertical; quadriláteros 8-pt normalizados; `reference_dpi_by_page` propagado do pipeline vencedor; dpi adaptativo com margem; falha de render/OCR degradável; `_targeted_recheck` usa a página da ocorrência. Parentesco: família `CONJ` (prefixo 7) como âncora — mesma linha (`row_group`) ou conjunto único da folha (`set_span`), ambos verificados; sem pai comprovado → `parent_code=null` + `parent_verified=false`.

**Evidência prod (`daf0a8e564`, in-container):** `90263572` p2 A1 → `10080004` recuperado `localized_ocr_recheck` conf 0.9999 (antes OCR lia `10060004` e a célula estava fora da região). `90264030`: `10081686→70260049` (p7), `10080535→70260050/51/52/53` (p9–12) — 5/5 parentescos verificados pelo desenho. `10080292`/`10080438` ausentes de todos os tokens/células/contextos das folhas relevantes → BOM_ONLY permanece candidato legítimo (revisão Engenharia pendente, sem NC).

**Testes:** +7 (região expandida, dpi por página, adaptativo, quad 8pt, falha de render, negativo, DRAWING_ONLY sem raiz); 3 fixtures legados alinhados ao gate ≥0.9. **102/102 PASS.**

**Estado:** `OCR_CELL_RECOVERY_10080004=PASS` · `PARENT_PROVENANCE_90264030=PASS` · `BOM_ONLY_VALIDATION=CANDIDATES_KEPT` · `REGRESSION_SUITE=102/102` · `CHATGPT_CONSUMER_PASS=PENDING` (reteste independente obrigatório: `compose_understanding` em `90263572` e `90264030` → conferir `localized_ocr_recheck`/`parent_source` nos artefatos e os 10 findings com parentesco correto).

## 35. DEC-VAL-034 (EVA #131) — evidência `localized_ocr_recheck` reconciliada na investigação guiada e no MCP (2026-11-04)

**Causa-raiz (PROVEN ponta a ponta):** o token recuperado era anexado somente a `drawing_tokens` — o comparador o via (`bom_only=0`, falso BOM_ONLY suprimido), mas a investigação guiada (`guided_investigations`) opera sobre `component_table.rows` + `identifier_candidates`, que nunca recebiam a evidência → `O0001/10080004` reportada `AMBIGUOUS` + `NO_CANDIDATE_REGION` no MCP apesar do backend recuperar o código. Defeito secundário: `OcrToken.box` não era lido (código buscava `bounding_box_px`) → `box=null` na evidência.

**Correção (commit `6a7fdc65c1`):**
- `recover_absent_table_cells` lê `bounding_box_px` **ou** `box` e devolve `region`/`region_ref_dpi` (região efetivamente inspecionada).
- `analyze_product_drawing` registra recuperados em `u["code_contexts"]` (`component_table`, dedup) e `u["localized_recovery"]` — contrato RQ-VAL-052: `observed_code`, `raw_text`, `product_code`, `pdf_sha256`, `page`, `region`/`region_box`, `bounding_box|null`, `coordinate_system`, `method`, `confidence`, `source_revision`. Nada fictício; nulos explícitos.
- `_check_component_code`: após tipadas/ambíguas, consulta `localized_recovery` — hit único → `MATCH_CANDIDATE` com `evidence_refs` completos (método, página, region_box, box em espaço da página, SHA do documento); múltiplos hits → `AMBIGUOUS`; nenhum → fluxo inalterado. O crop é delimitado pela faixa da tabela tipada expandida por tokens na faixa → observação estrutural, não token solto. Contradição CODE_OBSERVED-backend × NO_CANDIDATE_REGION-MCP eliminada.

**Evidência prod (`6a7fdc65c1`, in-container, PDF `90263572` SHA `9021fce0…28d3e`):** `O0001/10080004` → `overall_state=MATCH_CANDIDATE`, `observed_value=10080004`, `evidence_refs`: `source_kind=localized_ocr_recheck`, `page=2`, `region_box=[20,248,909,1038]@110dpi`, `bounding_box=[351.8,270.8,395.1,283.2]` (quad real convertido, não inventado), `confidence=0.9999`, `document_sha256=9021fce0…28d3e`.

**Testes:** +5 (consumo na I-01, sem box, múltiplos hits, código diverso inalterado, attr `box` do token). **107/107 PASS.**

**Preservado:** gate `BOM_ONLY` ≥0.9 (DEC-VAL-033) intacto; `90264030` 5/5 pais verificados e 10 findings candidatos mantidos; nenhuma NC automática.

**Estado:** `OCR_A1_BACKEND_RECOVERY=PASS` · `REPORT_GROUNDING=PASS (evidência verificável no guided_investigations)` · `BOM_ONLY_GATE=PRESERVED` · `CHATGPT_CONSUMER_PASS=PENDING` (reteste: `compose_understanding` `90263572` → `guided_investigations` deve mostrar `O0001` MATCH_CANDIDATE + `evidence_refs` localized_ocr_recheck; `90264030` → 5 pais + 10 findings).

## 36. DEC-VAL-034 — diagnóstico do 502/erro interno do MCP e correção de documento no envelope (2026-11-05)

**Causa-raiz (PROVEN nos logs prod `delpi-engineering-api`):** `eva_mcp_tool_error` com `NameError: name 'out' is not defined` em `semantic_bridge.py:1671` — `_analyze_drawing_understanding` retornava `out["document"]`/`out["same_document_verified"]`, mas `out` vem de `run_official_document_benchmark` dentro de `_produce_drawing_understanding` (fora de escopo no caller, que recebe `(u, structure, best, tokens, pdf_bytes)`). O incidente reportado pelo consumidor teve 2 eventos: `502 upstream_error` (primeira tentativa — pipeline síncrono OCR+SLANet leva minutos, timeout de gateway/upstream) e erro interno da ferramenta (segunda — o NameError). **Logs do container:** nenhuma requisição de análise alcançou o handler entre as duas falhas? — requisições POST `/mcp/` 200 OK presentes com `ClientDisconnect` antes do trace — consiste com timeout upstream + NameError no final do caminho.

**Correção (commit `9976f441a6`):** `_produce_drawing_understanding` anexa `document` e `same_document_verified` ao próprio `understanding` (identidade do documento oficial pertence ao envelope); o retorno usa `understanding.get(...)`. Efeito colateral corrigido: `report.identification.document_id` deixou de ser sempre `null`.

**Evidência:** suíte overlay 275 testes PASS (incl. 62 `test_eva_mcp` com `asyncio_mode` correto); prod `delpi-engineering-api` healthy em `9976f441a6`.

**Estado:** `MCP_DRAWING_UNDERSTANDING_NAMEERROR=FIXED` · `502_UPSTREAM=timeout gateway pipeline síncrono (documentado; caminho async via job segue canônico)` · `CHATGPT_CONSUMER_PASS=PENDING` (reteste: `product.drawing_understanding` `90263572` deve retornar `document`+`same_document_verified`+`guided_investigations` com `O0001 MATCH_CANDIDATE`).

## 37. DEC-VAL-034 rev2 — PATH_DRIFT: recuperação ausente do caminho product.drawing_understanding (2026-11-05)

**Causa-raiz (PROVEN):** reteste ChatGPT mostrou `O0001` `AMBIGUOUS`+`NO_CANDIDATE_REGION` em `product.drawing_understanding` válido (document+same_document_verified OK após `9976f441a6`). O caminho `drawing_understanding` executa `_produce_drawing_understanding`+`build_object_profiles` **sem** `analyze_product_drawing` — onde viviam recovery e `localized_recovery`. A evidência só existia no caminho `product.drawing_analysis` (job).

**Correção (`f9d6ab73c9`, publicado como `abcdcc63f6`):** `apply_localized_recovery()` extraída para `drawing_investigation` (owner da recuperação) — computa faltantes, executa `recover_absent_table_cells`, registra em `tokens`/`code_contexts`/`localized_recovery`; chamada por ambos os caminhos (`analyze_product_drawing` e `_analyze_drawing_understanding` com `_prog` compartilhado). Aditivo, sem fabricação.

**Evidência prod (`abcdcc63f6`, in-container, PDF `90263572` SHA …28d3e):** `O0001` → `MATCH_CANDIDATE`, `observed_value=10080004`, `evidence_refs` completos (`localized_ocr_recheck`, page 2, region_box [20,248,909,1038]@110dpi, box real [351.8,270.8,395.1,283.2], conf 0.9999, document_sha256 correto), `search_history=null` (sem contradição).

**Testes:** 772/773 no overlay (falha isolada `test_lmp_domain` FileNotFound — fixture ausente no overlay, não-regressão). `90264030`: hierarquia/gate preservados (sem mudança de código do comparador nesta rev).

**Estado:** `PATH_DRIFT=FIXED` · `DRAWING_UNDERSTANDING_PATH=RECOVERING` · `CHATGPT_CONSUMER_PASS=PENDING` (reteste: `product.drawing_understanding` `90263572` → O0001 MATCH_CANDIDATE + evidence_refs; `90264030` → 5 pais + 10 findings).

## 38. Framework-First SLANet — trace produtivo + 2 fixes mínimos (2026-11-05)

**Trace F1 (PROVEN):** `TableStructureEngine` executa em prod via `_produce_drawing_understanding` (ambos os caminhos MCP) — só página 0, escala 2.7778, `crop_box=component_table.box`. Células SLANet (`table_structure_engines[0].cells`) são consumidas **somente** pelo resumo do relatório (`cell_count`, `cells_with_text`, `cell_bounding_boxes`) — `row`/`col` da grade `i//8` **não têm consumidor semântico** (`component_table` vem de `understanding.py`). Logo `i//8` é defeito cosmético, não a fronteira produtiva dos parents/O0001 — classificado `BENCHMARK_REQUIRED`, não implementado.

**Dois defeitos reais corrigidos (`00befcff78`, merge `2cb89f61a3`):**
1. `associate_tokens_to_cells()` era calculada e **descartada** — bridge/report leem `_sl_e["association"].unassigned/.conflicts` (campo contratual morto). Propagado no resultado.
2. Fallback de crop fixo `[41,31,2295,262]` fabricava estrutura em coordenada arbitrária → **fail-closed `NO_TABLE_REGION`** com erro tipado.

**Evidência:** 101/101 testes focados; prod `2cb89f61a3` healthy com `NO_TABLE_REGION` em `/app`. Contrato: aditivo (`association` restaurado, `error_kind` tipado). Sem mudança em comparador, gates, investigação, parents.


## 39. DEC-VAL-035 — Direção executável do Cursor: fechar VAL-01 E1 estrutura do produto para a biblioteca atual (2026-11-05)

**DECISÃO DE PRODUTO / STATUS:** \`PLANNED\` para implementação, \`E1=ACTIVE\`, \`E2–E7=FROZEN\`. **Documento único de execução:** este Doc 119; Doc 116 permanece referência de arquitetura/qualidade e Doc 120 permanece índice histórico do corpus, **não criar novos planos, subplanos ou documentos**. A Issue #131 é exclusivamente tracker, não especificação concorrente. Atualizar **este mesmo parágrafo/seção, suas tabelas de AC e o ledger já existente** a cada marco de código/teste; não gerar novas seções para cada bug. Cursor/implementador consome esta seção como task executável. Esta decisão **não** declara funcionalidades implementadas, deploy, nem GT técnico aprovado.

### 39.1 Outcome e limite de promessa

**Entrega única:** EVA consegue ler a **estrutura do produto efetivamente representada nos desenhos das famílias existentes na biblioteca oficial e autorizada**, relacionar ocorrências da tabela de materiais com a BOM oficial **da mesma identidade/efetividade**, avaliar código, item, descrição, quantidade/unidade, multiplicidade, níveis, subconjuntos, grupos e parentesco, com decisão e evidência por ocorrência e consolidada por desenho. Detectar diferenças reais sem produzir ausência a partir de falha de OCR. Resultado sempre \`DRAFT/CANDIDATE\`; Engenharia aprova as regras, GT e decisões finais.

**“Qualquer tipo de estrutura hoje na biblioteca” é TARGET de cobertura da biblioteca, não alegação PROVEN nem promessa de 100% de automação.** Não restringir a heurísticas por código de produto, família específica ou layout fixo. Toda família/layout presente no acervo deve ser classificada por evidência como \`SUPPORTED\`, \`UNSUPPORTED\` ou \`INCONCLUSIVE\` e ter motivo, versão e limites; ampliar suporte até a cobertura-alvo que o owner aprovar. Desenhos sem tabela explícita, revisões incompatíveis e estruturas implícitas exigem políticas oficiais de representação, ou abstenção governada. A família suportada precisa passar critérios de qualidade, inclusive exemplos positivos, negativos e holdout; \`INCONCLUSIVE\` não mascara incapacidade de casos declarados suportados.

**Proibição de retrabalho:** reutilizar inventários e decisões E1, Doc 120 (13 PDFs), 53 NCs, contratos, investigação guiada, SLANet Framework-First §38, DEC-VAL-033/034 e demais evidências vigentes. Não repetir auditorias de frameworks, inventário genérico do código ou benchmarking amplo. Fazer apenas **delta de cobertura**: contrastar o índice Doc 120 com as famílias/layouts/estruturas efetivamente presentes na biblioteca via API oficial autorizada; acrescentar casos faltantes ao corpus canônico existente **somente se necessários** para cumprir cobertura de família e holdout; não criar novo catálogo. Guardar identidade PDF SHA, BOM \`as_of\`/revisão, configuração/modelo e histórico; evidência antiga sem identidade temporal atual = \`STALE_EVIDENCE\`.

### 39.2 Subplano técnico *dentro de E1* — OCR/visão apenas como dependência da validação estrutural

O subplano **não é nova frente, serviço, camada, documento nem autorização de provider**. É a decomposição executável da mesma VAL-01:

| Passo | RQ | Resultado funcional esperado | Gate/owner |
|---|---|---|---|
| E1-A — baseline e regras | \`RQ-E1-01\` | Reutilizar os 13 PDFs, comparar famílias atuais da biblioteca, registrar apenas gaps; obter políticas oficiais por família: quais níveis devem aparecer, equivalência de unidades, multiplicidade e revisão/efetividade | Engenharia owner para regra/GT; \`OWNER_BLOCKED\` explícito se indisponível |
| E1-B — percepção de estrutura | \`RQ-E1-02\` | Ler regiões/tabelas vigentes, linha, coluna, rowspan/colspan, item, código, descrição, quantidade/unidade e referências espaciais em páginas relevantes; recuperar OCR por região quando necessário, com fonte real e sem falsificar ausência | Framework-first; manter \`understanding.py\` como caminho semântico até ganho demonstrado |
| E1-C — modelo de ocorrência | \`RQ-E1-03\` | Representar cada ocorrência desenho com caminho pai-filho, agrupamento/subconjunto, repetição, item/linha, quantidade, página/célula, confiança metodológica, ambiguidade, fonte e SHA; nunca colapsar códigos repetidos | Application/Domain; contrato compatível e sem authority implícita |
| E1-D — comparação governada | \`RQ-E1-04\` | Matching desenho↔BOM multiplicity-aware, sem atribuição por ordem/raiz fictícia; comparar atributos apenas sob política oficial; \`BOM_ONLY\` somente com cobertura e ausência provadas; \`DRAWING_ONLY\` somente com linha de tabela atual e bbox real | Domain APIs owner; fail-closed e AuthZ live |
| E1-E — relatório e revisão | \`RQ-E1-05\` | Resultado por atributo/ocorrência e global: MATCH/CONFLICT/UNKNOWN/NOT_COMPARABLE/NOT_CHECKED + estados candidatos compatíveis, evidências bidirecionais, gaps, cobertura e next_action; nunca aprovação automática | Portal/EVA como consumer; Engenharia aprova tecnicamente |
| E1-F — qualidade e release | \`RQ-E1-06\` | Testes sintéticos e reais, corpus regressão, holdout por família, métricas com denominador e owner-approved threshold; E2E MCP autenticado, deploy governado e rollback | Review independente + engenharia owner + operação autorizada |

**Abstraction Gate obrigatório antes de novo código:** identificar necessidade, owner, consumer, boundary, contrato e alternativa mais simples; usar recursos nativos PaddleOCR/SLANet/PP-StructureV3/PDFium **apenas quando evidência demonstrar ganho**. O trace §38 provou que \`row=i//8\` do adapter SLANet **não alimenta** \`component_table\` nem parentesco produtivo: não reabrir esse ajuste como prioridade sem novo callsite/resultado. Reaproveitar correção de \`association\` e \`NO_TABLE_REGION\`; preservar recuperação \`10080004\` e OCR localizado. PP-StructureV3 produtivo requer gate explícito de modelos/owner/plataforma; Docling indisponível não bloqueia E1.

**Correção perceptiva só é necessária quando houver falha funcional reproduzida** em campo da estrutura. Diagnosticar a primeira perda \`PDF → OCR/região → células/tokens → linha tipada → ocorrência → comparação\`; corrigir a fronteira real, menor diff, e comparar antes/depois no mesmo PDF/modelo/BOM. Não introduzir algoritmo local de OCR, parser de tabela ou inferência por produto para contornar uso incompleto do framework.

### 39.3 Requisitos de aceitação verificáveis — um gate por atributo e por família

| AC | Critério de fechamento | Evidência exigida |
|---|---|---|
| \`AC-E1-01\` | Biblioteca atual tem matriz de famílias/layouts, políticas de representação e escopo da BOM definidos; exceções explícitas | API oficial + decisões do owner, sem listagem redundante dos PDFs |
| \`AC-E1-02\` | Tabela vigente separada de revision_history/title_block/notes; página/célula/coords corretas, spans e múltiplos blocos preservados | GT visual aprovado para casos e negativos, PDF SHA |
| \`AC-E1-03\` | Código, item, descrição, qty/unidade vinculados à **mesma ocorrência**, sem campos fabricados | Métricas por atributo com recall, precision, associação e abstenção |
| \`AC-E1-04\` | Relação pai-filho, grupos, níveis e multiplicidade corretos; sem raiz inventada ou merge de ocorrência repetida | Árvore esperada × observada por documento |
| \`AC-E1-05\` | Comparador usa BOM/revisão/efetividade oficiais e política por família; ausência exige cobertura comprovada | Casos positivos/negativos e mudanças temporais de BOM |
| \`AC-E1-06\` | Relatório por ocorrência e por desenho coerente, evidências bidirecionais e razões de \`INCONCLUSIVE\` | Consumer MCP e contrato/serialização |
| \`AC-E1-07\` | Corpus conhecido sem regressões críticas: \`90263572\` O0001 \`10080004\` (p2 com evidência, sem falso BOM_ONLY); \`90264030\` 5 pais + 10 findings candidatos sujeitos a revisão; \`90264017\` sem falso vigente por histórico; \`90263520\` baseline BOM vigente | Reexecução autenticada, hash e \`as_of\`, sem converter candidatos em NC |
| \`AC-E1-08\` | Todas as famílias declaradas \`SUPPORTED\` cumprem limiares técnicos **aprovados antes do holdout**; não apenas testes verdes | GT owner-approved, holdout sem tuning, métricas/erros por layout |
| \`AC-E1-09\` | Fontes indisponíveis, permissões negadas, páginas não lidas e timeout devolvem estados honestos; sem vazamento de secrets ou acesso cross-domain | Testes negativos AuthZ, performance, logs sanitizados |
| \`AC-E1-10\` | SHA código/modelo/dataset/config, regressão, comparação E2E e release autorizados; rollback/observabilidade | Evidência em runtime e aprovação de owner, não apenas docs |

**Estados:** \`PROVEN | TO_INVENTORY | PLANNED | TARGET\` para afirmações; \`PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE\` para testes. Não marcar AC com \`PASS\` por relatório do executor, HTTP 200, container healthy, 0 findings ou OCR confidence. Um AC obrigatório pendente impede declarar \`VAL01_COMPLETED\`; owner indisponível = \`OWNER_BLOCKED\`, sem workaround de autorização.

### 39.4 Sequência obrigatória para o Cursor — um pacote bounded, sem refazer levantamentos

1. **Reancorar:** \`AGENTS.md\`, autoridades e contratos existentes, HEAD/branch/status, SHA runtime, seção 39, ledger e Issue #131. Não copiar prompts antigos nem reabrir estudos concluídos. Usar caminhos reais, não inventar infraestrutura.
2. **Gap list funcional:** para os AC acima, mapear \`PROVEN/PENDING/FAIL/OWNER_BLOCKED\` com as evidências atuais (§§17–38, Doc 120). Reduzir a uma lista curta de lacunas **que impedem o outcome**; apenas consultar famílias não catalogadas na biblioteca por API owner. Não produzir relatório de inventário genérico.
3. **Contratos/políticas:** definir entrada/saída \`structure_validation.v1\` **como TARGET até gate**, compatível/aditivo ao \`product.drawing_analysis\`; formalizar owner, consumers, versão, erros, AuthN/AuthZ, limite, idempotência e postconditions quando houver; obter decisões de representação por família, quantidade e revisões. Se owner não decidir, avançar onde possível, declarar bloqueio sem criar regra fictícia.
4. **Vertical slice e correção mínima:** seguir \`fonte oficial → percepção → ocorrência tipada → comparação → relatório candidato\`. Corrigir primeiro defeito **funcional de maior risco** com RQ/AC e PDF específico; até três ciclos locais de diagnose/fix/tests no mesmo pacote, sem abrir subprojetos. Reaproveitar pipeline/jobs governados; não duplicar \`drawing_analysis\` e \`drawing_understanding\`.
5. **Testar no SHA:** casos positivos e negativos por atributo, múltiplas famílias/layouts, PDFs 13/13 com identidade atual quando acessíveis, famílias adicionais necessárias e holdout sem vazamento; controlar concorrência/timeout com job canônico e separar falha da fonte de bug. Testes unitários, contrato, integração, permissão, regressão e outcomes. Evidências e métricas com denominador por classe/família.
6. **Revisão independente e deploy governado:** corrigir BLOCKING dentro do pacote. Mudança runtime exige autorização e procedimento canônico + rollback, SHA/digest e postconditions reais; MCP/ChatGPT deve retestar resultados técnicos, não apenas transporte. Aprovação técnica/publicação continua com Engineering owner.
7. **Atualização contínua:** modificar **somente o Doc 119 como especificação/plano central** e a **Issue #131 como tracker**; atualizar AC, decisões, commits e resultados na seção 39 e ledger existente após cada etapa. Doc 120 continua índice de corpus, com atualização de linha apenas quando novo desenho/versão for efetivamente testado — **não criar novos documentos**. Não apagar evidência histórica nem duplicar plano em README/prompt/issue.

**Gates de saída:** \`E1_FUNCTIONAL_CANDIDATE_PASS\` se fluxo candidato completo e seguro comprovado; \`E1_ENGINEERING_QUALITY_PASS\` somente com políticas/GT/thresholds/holdout aprovados por Engenharia no escopo suportado; \`VAL01_COMPLETED\` apenas com todos AC aplicáveis, E2E independente, operacional e owner. \`E2–E7\` permanecem congeladas até esse gate.

### 39.5 Estado inicial registrado e próximo passo

| Item | Estado em 2026-11-05 | Evidência/pendência |
|---|---|---|
| Pipeline PDF/OCR/investigação/comparador candidato | \`PROVEN\` parcial | Implementações e E2E §§17–38 |
| O0001 de \`90263572\` com evidência p2 | \`PASS\` no consumer anterior | \`MATCH_CANDIDATE\`, \`localized_ocr_recheck\`, SHA PDF confirmado |
| \`90264030\` 5 parents / 10 findings | \`PASS\` histórico; reteste atual \`INCONCLUSIVE\` | MCP atual retornou erro interno; não invalidar histórico nem afirmar revalidação |
| 13 PDFs catalogados | \`PROVEN\` como corpus histórico | Não equivale a cobertura de toda biblioteca nem GT aprovado |
| Políticas de níveis/quantidade e GT owner | \`OWNER_BLOCKED / PENDING\` | Solicitar decisão concreta por família, não inventar |
| Cobertura validada para todos layouts atuais | \`TARGET\` | Gap-delta com biblioteca oficial, avaliação por família |
| Qualidade estrutural e aceite final E1 | \`PENDING\` | AC-E1-01..10, holdout, Engineering owner |

**NEXT_BOUNDED_STEP (Cursor):** reancorar e executar **E1-A→E1-F** como **uma entrega vertical**, iniciando pelos atributos de ocorrência (item/código/descrição/quantidade/pai-filho) que ainda não possuem evidência de qualidade. Registrar primeiro o delta de AC no Doc 119/Issue #131; implementar o menor conjunto de mudanças que leva o resultado completo por ocorrência até o consumidor. Não executar novo audit Framework-First nem criar novo documento. **A ausência de GT/decisão de owner bloqueia qualidade oficial, não precisa bloquear implementação segura e claramente candidata.**

**VERDICT DE PLANEJAMENTO:** \`ACCEPT\` como direção de produto; **EXECUTION_STATUS:** \`IN_PROGRESS\` — ledger por ocorrência implementado no comparador canônico; qualidade oficial e E2E de runtime continuam pendentes.


### 39.7 Verificação independente do consumidor MCP — gate de runtime do ledger (2026-11-05)

**Escopo:** validação read-only do novo `structure_validation.v1` implementado no commit `01481495a2390b245138d53792befe3d8e741b38` e registrado no commit `a1c816c8da4ca8f1dd73f86ff24a36bd679d6779`. Não houve deploy nesta verificação e nenhum teste prova o SHA servido pelo runtime. **Gate operacional:** não tratar a versão antiga como validação do código novo nem publicar sem autorização operacional/caminho canônico.

**Consumer independente `product.drawing_understanding`, produto `90263572`:** chamada autenticada `success=true`; `document_hash_sha256=9021fce05c608655e538f67cdaac08c7484ebbe16a8888e83fbeec9ecaa28d3e`, `same_document_verified=true`. `O0001` continua `MATCH_CANDIDATE` com `observed_value=10080004`, `source_kind=localized_ocr_recheck`, `page=2`, box/region/sha reais. **Mas `report.structure_validation` está AUSENTE** e não apareceu `bom_structure_comparison.validation_report` no envelope consultado; por isso `NEW_LEDGER_MCP_E2E=FAIL` quanto à disponibilidade do contrato, não quanto à correção do código. SHA em runtime = `UNVERIFIED`; ausência é consistente com deploy pendente, mas não comprova sozinha qual imagem/commit está servido. Não declarar regressão do comparador por esse resultado.

**Demais desenhos `90264030`, `90264017`, `90263520`:** tentativa sequencial em uma única sessão excedeu timeout de execução da ferramenta, sem resultado individual confiável; `INCONCLUSIVE`, não `PASS`, nem `FAIL` funcional. **Corpus 13/13 no novo SHA:** `TEST_NOT_RUN`. **GT, quantidade/unidade, descrição semântica, efetividade/revisão, métricas e AuthZ live:** pendentes conforme §39.6.

**Decisão:** `AC-E1-07=INCONCLUSIVE`, `AC-E1-10=PENDING`, `E1_FUNCTIONAL_CANDIDATE_PASS` ainda não demonstrado em runtime. **NEXT_BOUNDED_STEP (operação/Cursor autorizado):** verificar SHA/digest da Engineering API ativa; executar o procedimento canônico de deploy do commit `01481495a2` ou sucessor que o contenha, somente com autorização operacional e gates pré-deploy; executar os 4 regressores em série pelo caminho de job governado quando análise síncrona exceder timeout; verificar presença e conteúdo de `structure_validation.v1` por ocorrência, comparações, cobertura, falsos alarmes, limites e AuthZ. Atualizar somente Doc119 §39/Issue #131 com SHA, resultados e bloqueios. **VAL-01 permanece aberta.**

### 39.6 Execução Cursor — ledger de validação por ocorrência (2026-11-05)

**DATA:** 2026-11-05. **BASE_HEAD inicial:** `7038168c71f4033625722f683e696a5f89143fb7`. **Revalidação antes do commit:** `6e8f2a6f22624c988d2d8c5cb55341998bb7e39e` (`main`, ancestral do início; commit PCP alheio). **FINAL_HEAD:** `01481495a2390b245138d53792befe3d8e741b38`. **BRANCH:** `main`. Alterações concorrentes fora deste pacote foram preservadas (DÉLIA, scripts de infra, plugin-ui, TV dashboard, travel-expenses).

**RQ / AC atendidos neste pacote**

| ID | Estado | Evidência |
|---|---|---|
| RQ-E1-05 / AC-E1-06 | `PASS` parcial, candidato | `validation_report` (`structure_validation.v1`) no retorno de `compare_bom_to_drawing` e em `report.structure_validation` do caminho `product.drawing_understanding` |
| AC-E1-03 | `PASS` parcial, candidato | código, item, descrição literal e quantidade no mesmo registro; descrição ausente = `NOT_CHECKED`; diferença literal = `CONFLICT_CANDIDATE`, não NC |
| AC-E1-04 | `PASS` parcial, candidato | ocorrências repetidas não colapsam; pai só `MATCH_CANDIDATE` quando verificado; sem pai, `NOT_CHECKED` |
| AC-E1-05 | `PASS` parcial | `BOM_ONLY` continua exigindo cobertura; linhas não lidas ficam `NOT_CHECKED`; revisão isolada não entra como `DRAWING_ONLY` |
| AC-E1-01 | `OWNER_BLOCKED` | quantidade/unidade, item de desenho × posição BOM, equivalência semântica de descrição, revisão e limiares de GT |
| AC-E1-02 | `PENDING` | percepção existente reutilizada; células mescladas e blocos paralelos desta leitura = `INCONCLUSIVE` |
| AC-E1-07 | `TEST_NOT_RUN` no runtime | regressão sintética dos invariantes passou; PDFs `90263572`, `90264030`, `90264017`, `90263520` não foram reexecutados neste SHA |
| AC-E1-08 | `OWNER_BLOCKED` | sem limiar nem holdout aprovado pela Engenharia |
| AC-E1-09 | `PASS` parcial | BOM indisponível → `INCONCLUSIVE` e ledger vazio; sem aprovação automática |
| AC-E1-10 | `PENDING` | sem deploy nem E2E autenticado neste ciclo |

**COMPORTAMENTO ANTERIOR:** o comparador emitia findings agregados (`DRAWING_ONLY` / `BOM_ONLY` / `PARENT_RELATION_MISMATCH`) e a investigação guiada marcava descrição como não verificável mesmo quando a BOM oficial já trazia `description`. O consumidor MCP `product.drawing_understanding` não recebia o diff estrutural.

**ALTERAÇÃO:** projeção aditiva de `component_description` em `flatten_bom_occurrences` e no perfil BOM. `compare_bom_to_drawing` passa a devolver `validation_report` com um registro por ocorrência (esperado, observado, resultado, evidência, página/região, regra, incerteza, limitação, próxima ação) e o consolidado (esperadas, observadas, `proven_matches=0`, candidatos, divergências, ambíguas, relações não verificadas, atributos não comparáveis, cobertura, limitações, situação global, famílias `SUPPORTED` / `UNSUPPORTED` / `INCONCLUSIVE`). Quantidade, unidade e revisão permanecem `NOT_COMPARABLE`. Estado do relatório: `DRAFT/CANDIDATE`, `engineering_approval=NOT_APPROVED`, `automatic_nc=false`. O caminho de entendimento do desenho chama o mesmo comparador depois da recuperação localizada.

**RESULTADO OBSERVADO:** testes novos cobrem correspondência literal, descrição ausente, diferença literal sem NC, BOM não lida sem `BOM_ONLY`, repetição não colapsada, código só em `revision_history` fora do ledger e BOM indisponível.

**TESTES:** `tests/test_bom_structure_comparator.py` + `test_bom_structure_comparator_val027_029.py` + `test_drawing_investigation_r12.py` = 92 passed. `test_drawing_analysis*.py`, perfis, recuperação e MCP = 139 passed. Corpus real dos 13 PDFs: `TEST_NOT_RUN` neste ciclo (sem chamada à biblioteca oficial).

**CORPUS / PDF SHA:** inalterado; Doc 120 não foi editado.

**RUNTIME:** não implantado.

**BLOQUEIOS:** `OWNER_BLOCKED` nas políticas de quantidade, unidade, equivalência de descrição, item de desenho e ground truth. `E2E` e aceite da Engenharia pendentes. `VAL01_COMPLETED` não declarado. E2–E7 permanecem congeladas.

**PRÓXIMA AÇÃO:** reexecutar no runtime, com o SHA deste commit, os quatro regressores `90263572`, `90264030`, `90264017` e `90263520`, e só então pedir aceite de GT à Engenharia.

### 39.8 Tentativa de deploy produtivo do ledger — bloqueio de acesso ao srv-api (2026-11-05)

**DATA:** 2026-11-05. **BASE_HEAD local:** `30651aa42357008b8a06ceab3c62344711cb6434` (`main` = `origin/main`). Esse HEAD **contém** `01481495a2390b245138d53792befe3d8e741b38`. Alterações concorrentes no working tree foram preservadas; nenhum arquivo de produção foi editado.

**Autorização:** a task `EVA-VAL01-STRUCTURE-VALIDATION-DEPLOY-E2E-01` autoriza o procedimento canônico `git pull --ff-only` + `./infra/scripts/up-prod-sequential.sh --build engineering-api` em `operador@192.168.1.237:~/projetos/delpi-central`.

**O que foi comprovado**

| Sinal | Resultado |
|---|---|
| `ssh -o BatchMode=yes -o ConnectTimeout=15 operador@192.168.1.237` | `Connection timed out` nas duas tentativas. Deploy **não executado**. |
| `https://minhadelpi.com.br` | DNS Cloudflare (`2606:4700:…`). `GET /apps/engineering-api/health` → HTTP 200 `{"status":"online","service":"engineering-api"}`. |
| `POST /apps/engineering-api/mcp` sem token | HTTP 401 `{"detail":"Unauthorized"}`. Fail-closed do runtime **atual**, que a §39.7 já mostrou **sem** `structure_validation`. |
| Container local `delpi-engineering-api` | Compose **dev** (`docker-compose.dev.yml`), bind-mount `engineering-api:/app`, processo iniciado `2026-11-05T21:57:27Z` **sem** `--reload`. Não publica porta no host e não é o MCP de `minhadelpi.com.br`. Não foi reiniciado. |

**Não comprovado:** `DEPLOYED_SHA`, digest da imagem de produção, presença de `structure_validation.v1` no processo que o ChatGPT chama. HTTP 200 e container local com o arquivo no disco não contam como deploy.

**Regressores `90263572`, `90264030`, `90264017`, `90263520`:** `TEST_NOT_RUN` neste ciclo. Reexecutar no runtime antigo repetiria a §39.7.

**AC-E1-10:** permanece `PENDING`. **READY_FOR_CHATGPT_E2E:** `NO`.

**ROLLBACK:** inalterado — nenhum pull/build foi feito no `srv-api`.

**PRÓXIMA AÇÃO:** operador com rota até `192.168.1.237` executa o script canônico acima a partir do HEAD que contém `01481495a2`, confirma `validation_report` / `structure_validation.v1` dentro de `delpi-engineering-api`, e só então os quatro desenhos em série. Issue #131 não foi comentada: este ambiente não tem token da API do GitHub.

### 39.9 Deploy produtivo do ledger — Engineering API no srv-api (2026-11-05)

**DATA:** 2026-11-05, container iniciado `2026-11-05T22:42:25Z`. A rota SSH para `operador@192.168.1.237` passou a responder. **Checkout antes:** `9395d34e3c81e881b47f0a2936894d9e20d225fa`, imagem `sha256:ce72f3428e736682b0e440c3f33fe4f357a06cd1d40c4feb4ef4bc062d10a5c1`, `structure_validation.v1` ausente no container. **Pull:** `git pull --ff-only origin main` → `1a5c75152fa739964eaa4362eda0d53fdf33095f`, que contém `01481495a2`. **Build:** `./infra/scripts/up-prod-sequential.sh --build engineering-api`. Nenhum outro container foi recriado (`delpi-core-api` segue desde `2026-11-01T22:11:04Z`).

| Campo | Valor |
|---|---|
| DEPLOYED_SHA | `1a5c75152fa739964eaa4362eda0d53fdf33095f` |
| IMAGE_ID | `sha256:ee26acf6ea1f58af462f611aedcc087daaa127bca93e7bf3e9ba31977010e99c` |
| SERVICE | `delpi-engineering-api` (`engineering-api`) |
| HEALTH | `healthy`; `GET /apps/engineering-api/health` → 200 `online` |
| CONTRACT_PRESENT | sim — import no processo: `structure_validation.v1`, `DRAFT/CANDIDATE`, `engineering_approval=NOT_APPROVED`, `automatic_nc=false`, BOM ausente → `INCONCLUSIVE` e ledger vazio |
| MCP_ROUTE | `semantic_bridge.py` no image atribui `report.structure_validation`; `POST /apps/engineering-api/mcp` sem token → 401 `invalid_token` |
| ROLLBACK | imagem anterior `sha256:ce72f3428e73…` permanece no host; checkout anterior `9395d34e3c` |
| VOLUME | só `/opt/ocr-models` somente leitura; código vem da imagem, não de bind-mount |

**Regressores `90263572`, `90264030`, `90264017`, `90263520`:** `TEST_NOT_RUN` por este executor. O caminho MCP público já serve o código novo; a validação independente dos quatro desenhos fica com o ChatGPT. **AC-E1-10** continua `PENDING` até esse E2E e o aceite da Engenharia. **READY_FOR_CHATGPT_E2E:** `YES`. **VAL-01** não está concluída.

### 39.10 Reteste independente ChatGPT do ledger apos deploy (2026-11-05)

**Escopo:** E2E autenticado read-only de product.drawing_understanding via conector EVA, quatro produtos em serie. Executor reportou deploy no SHA 1a5c75152fa739964eaa4362eda0d53fdf33095f (imagem local sha256:ee26acf6ea1f58af462f611aedcc087daaa127bca93e7bf3e9ba31977010e99c). O consumidor confirmou contrato novo, mas nao leu o SHA do processo. Nenhum deploy neste reteste.

| Produto | Resultado independente | Novo contrato | Estado |
|---|---|---|---|
| 90263572 | success=true; PDF SHA 9021fce05c608655e538f67cdaac08c7484ebbe16a8888e83fbeec9ecaa28d3e; document verified | PASS | DRAFT/CANDIDATE; 56 expected, 35 observed, 33 match_candidates, 0 proven_matches, 0 candidate_divergences, global INCONCLUSIVE; O0001/10080004 MATCH_CANDIDATE, localized_ocr_recheck pagina 2, bbox/SHA reais. 24 token-only e 23 BOM ausencias nao demonstradas. |
| 90264030 | Erro interno da ferramenta, sem envelope confiavel | INCONCLUSIVE | 5 pais e 10 findings historicos nao revalidados |
| 90264017 | Erro interno da ferramenta, sem envelope confiavel | INCONCLUSIVE | Historico de revisao vs componente vigente nao revalidado |
| 90263520 | success=true; PDF SHA 08bf68690401438ab09c0e7ffcd1126bf98b238de776bc680db587704e4fb200; document verified | PASS | DRAFT/CANDIDATE; 20 expected, 24 observed, 20 match_candidates, 0 candidate_divergences; findings=[]; global INCONCLUSIVE. |

**Contrato e seguranca:** structure_validation.v1 PRESENTE nos 2 retornos validos; engineering_approval=NOT_APPROVED e automatic_nc=false no retorno detalhado de 90263572. Nao confundir candidatos com validacao da Engenharia. Estado AC-E1-07=INCONCLUSIVE (2/4), AC-E1-10=PARTIAL (E2E autenticado parcial), VAL01_COMPLETED=false.

**Gap direcionado de evidencia:** no 90263572, ledger reporta match_candidates=33 e guided_investigations.summary.match_candidates=1; criterios/denominadores diferentes ate verificacao. O ledger O0001 reporta match de codigo com page/box nulos e source code_token, enquanto investigacao guiada oferece localized_ocr_recheck pagina 2 com bbox/SHA. Investigar se refs devem ser preservadas no ledger; nao afirmar que existe erro sem rastrear callsite.

**Proximo passo unico:** operador/Cursor autorizado consultar logs para erro interno nos 90264030 e 90264017 e utilizar caminho de job governado para documentos longos; depois regressao dos 13 PDFs no novo SHA, sem novos documentos ou auditorias. Engenharia continua owner-blocked para quantidade/unidade, equivalencia de descricao, posicao BOM, revisao e GT/thresholds. Atualizar Doc 119 e Issue #131 com evidencias reais, sem abrir nova frente.

### 39.11 Correção residual RES-01/02/03 — jobs, proveniência e contadores (2026-11-05)

**TASK_ID:** `EVA-VAL01-RESIDUAL-FIX-E2E-01`. Nenhum documento novo. VAL-01 não concluída. Quantidade, unidade, equivalência de descrição, posição BOM, revisão e ground truth continuam `OWNER_BLOCKED`.

**RES-01**

| | |
|---|---|
| DEFECT | `product.drawing_understanding` de `90264030` (13 páginas) e `90264017` (14 páginas) chegou ao consumidor como erro interno, sem envelope. |
| ROOT_CAUSE | Gateway `delpi-gateway`, após o deploy das 22:42Z: vários `POST /apps/engineering-api/mcp` do `openai-mcp/1.0.0` com HTTP 499 e 0 bytes, espaçados cerca de 120s. No mesmo intervalo o processo só registrou fetch de `90263572` (resposta 200, ~44s, ~2,7 MB). Não há `Traceback` nem `eva_mcp_tool_error`. A leitura era síncrona; o cliente MCP desconectava antes de qualquer corpo. Não foi timeout de gateway 504, nem exceção de aplicação, nem falha de serialização observada. |
| MINIMAL_DIFF | `product.drawing_understanding` passa a usar o `AnalysisJobStore` já existente (DEC-VAL-030). A primeira chamada devolve `RUNNING` + `job_id` + `result_ready=false`. A consulta devolve `COMPLETED` ou `FAILED` com código tipado (`document_unreadable`, `analysis_incomplete`, `timeout`, `cancelled`, `job_not_found`). Retry sem `job_id` reencontra o mesmo job. Dono continua sendo o subject, não o access token. Sem fila nova e sem aumento de timeout. |
| TEST | `tests/test_drawing_understanding_jobs.py`: job antes do pipeline, falha tipada, outro usuário recebe `job_not_found`, exceção inesperada não vira sucesso. |
| RUNTIME_SHA | Checkout `00e3882e0ece827ca0f5b6fd7b29d4c2b3e50d6d`, que contém `8a027c4fe6302171c3cb1859884a057e5b7216c9`. Imagem `sha256:f64d495a04634e0c34e2325ed492b3217b2a7fc3cad642237246ca96cbe80ea3`, processo iniciado `2026-11-06T00:52:02Z`. |
| MCP_OUTCOME | Os quatro desenhos não foram reexecutados por este executor (sem token de usuário). O contrato de recuperação é o `job_id`. |
| RESIDUAL | O resultado completo continua dependente de o consumidor repetir a chamada com o `job_id`. Corpus de 13 PDFs: `TEST_NOT_RUN`. |

**RES-02**

| | |
|---|---|
| DEFECT | `90263572` ocorrência `O0001` código `10080004`: investigação guiada com página 2, `localized_ocr_recheck`, bounding box, região e SHA; ledger com `page=null`, caixa nula e origem `code_token`. |
| ROOT_CAUSE | `apply_localized_recovery` já gravava página, caixa e proveniência em `code_contexts` e tokens. O residual de `_drawing_occurrences` descartava esses campos e fixava `extraction_source=code_token`. `_code_cell_box` só lia `cells`, vazias nesse residual. A mesma ocorrência era pareada; a evidência se perdia na projeção, não na percepção. |
| MINIMAL_DIFF | O residual copia página, região, caixa, proveniência, confiança e SHA somente quando a evidência comparável é unívoca. Várias páginas ou várias caixas na mesma página permanecem nulas. Menção só em `revision_history` / `notes` / `title_block` não entra na ocorrência vigente. SHA passa a ser registrado no `code_context` porque a recuperação já o possuía. |
| TEST | `test_residual_localized_recovery_keeps_page_box_and_sha`, caixa ausente, duas páginas, duas caixas, e caixa de histórico que não cola na ocorrência BOM. |
| RUNTIME_SHA | Checkout `00e3882e0ece827ca0f5b6fd7b29d4c2b3e50d6d`, que contém `8a027c4fe6302171c3cb1859884a057e5b7216c9`. Imagem `sha256:f64d495a04634e0c34e2325ed492b3217b2a7fc3cad642237246ca96cbe80ea3`, processo iniciado `2026-11-06T00:52:02Z`. |
| MCP_OUTCOME | `TEST_NOT_RUN` neste executor. O caso sintético reproduz o shape de `O0001`. |
| RESIDUAL | Confirmação no PDF real de `90263572` fica no reteste MCP. |

**RES-03**

| | |
|---|---|
| DEFECT | `90263572`: `validation_report.match_candidates=33` e `guided_investigations.summary.match_candidates=1`. |
| ROOT_CAUSE | Denominadores diferentes, não erro aritmético. O do ledger conta ocorrências da BOM pareadas por código exato, inclusive token ou recuperação. O da investigação conta checks que chegaram a `MATCH_CANDIDATE`. O nome igual sugeria a mesma conta. |
| MINIMAL_DIFF | `match_candidates` permanece (compatibilidade). O relatório passa a expor `code_pair_candidates` (mesmo número), `structural_pair_candidates`, `code_only_pair_candidates` e `counter_definitions`. `proven_matches` continua 0. Código solto não vira correspondência estrutural verificada. |
| TEST | O relatório de BOM indisponível e o residual localizado afirmam as definições e `proven_matches=0`. |
| RUNTIME_SHA | Checkout `00e3882e0ece827ca0f5b6fd7b29d4c2b3e50d6d`, que contém `8a027c4fe6302171c3cb1859884a057e5b7216c9`. Imagem `sha256:f64d495a04634e0c34e2325ed492b3217b2a7fc3cad642237246ca96cbe80ea3`, processo iniciado `2026-11-06T00:52:02Z`. |
| MCP_OUTCOME | `TEST_NOT_RUN` neste executor. |
| RESIDUAL | O número 33, se reaparecer, é contagem de pares por código, não validação comprovada. |

**Invariantes preservados:** `engineering_approval=NOT_APPROVED`, `automatic_nc=false`, `DRAFT/CANDIDATE`, gate de `BOM_ONLY`, multiplicidade, histórico de revisão fora da tabela vigente, BOM somente leitura, AuthZ ao vivo, sem dependência do Chat legado.

**Regressão local:** 138 testes dos módulos de comparador, jobs, investigação e entendimento. Corpus 13 e os quatro PDFs oficiais: `TEST_NOT_RUN` até o reteste autenticado no SHA implantado.

### 39.12 Deploy das correções residuais — Engineering API (2026-11-06)

**TASK_ID:** `EVA-VAL01-RESIDUAL-DEPLOY-RETEST-01`. Nenhum serviço além de `engineering-api` foi reconstruído. `delpi-core-api` permanece iniciado em `2026-11-01T22:11:04Z`. VAL-01 não concluída.

```text
BASE_HEAD=00e3882e0ece827ca0f5b6fd7b29d4c2b3e50d6d
DEPLOYED_SHA=00e3882e0ece827ca0f5b6fd7b29d4c2b3e50d6d
FIX_COMMIT=8a027c4fe6302171c3cb1859884a057e5b7216c9
IMAGE_DIGEST=sha256:f64d495a04634e0c34e2325ed492b3217b2a7fc3cad642237246ca96cbe80ea3
DEPLOY_TIMESTAMP=2026-11-06T00:52:02Z
SERVICE_HEALTH=healthy
MCP_ANONYMOUS_NEGATIVE=HTTP 401 realm=engineering-mcp request_id=320a41b5-cef7-4dc6-80a7-0bc934514f78
OAUTH_METADATA=HTTP 200
PUBLIC_HEALTH=HTTP 200
ROLLBACK_IMAGE=sha256:ee26acf6ea1f58af462f611aedcc087daaa127bca93e7bf3e9ba31977010e99c
```

O checkout do `srv-api` já estava em `00e3882e` antes do build. A imagem anterior `ee26acf6` não continha `result_ready`. O build canônico copiou `engineering-api` de novo e recriou só `delpi-engineering-api`.

**Contrato no processo implantado:** smoke in-process, sem OCR e sem token de usuário.

| Verificação | Resultado |
|---|---|
| ASYNC_JOB_CONTRACT | Envelope `RUNNING`, `job_id`, `result_ready=false`, sem relatório. Falha `analysis_incomplete` com `success=false`. |
| JOB_RECOVERY | Mesma identidade e mesmos parâmetros reencontram o job. `COMPLETED` devolve o payload. `FAILED` guarda código tipado e não devolve resultado. |
| JOB_ISOLATION | `get_for_owner` de outra identidade devolve ausência. |
| PROVENANCE_CONTRACT | Ocorrência unívoca preserva página 2, região, caixa, `localized_ocr_recheck`, confiança e SHA. Duas páginas deixam página e caixa nulas. |
| COUNTER_DEFINITIONS | `match_candidates`, `code_pair_candidates`, `structural_pair_candidates`, `code_only_pair_candidates`, `counter_definitions`, `proven_matches=0`. Estado `DRAFT/CANDIDATE`, `engineering_approval=NOT_APPROVED`, `automatic_nc=false`. |
| TEST_RESULTS | 61 testes locais no HEAD `00e3882e` (jobs, comparador, entendimento). Quatro PDFs e corpus 13: `TEST_NOT_RUN` por este executor. |
| MCP_AUTHENTICATED | Gate OAuth no ar. Chamada positiva com token de usuário não executada aqui; o consumidor ChatGPT é quem a faz. |

**READY_FOR_CHATGPT_RETEST:** `YES` para o contrato corrigido. A primeira chamada de `product.drawing_understanding` devolve `job_id`; o relatório candidato só aparece na consulta até `COMPLETED` ou `FAILED`. Não tratar `RUNNING` como o ledger. **VAL01_COMPLETED:** `false`. Quantidade, unidade, equivalência de descrição, posição BOM, revisão e ground truth continuam com a Engenharia.

### 39.13 E2E independente de jobs MCP e ledger apos RES-01/02/03 (2026-11-05/06)

**Fonte:** chamadas autenticadas ChatGPT via conector EVA, `product.drawing_understanding`, com `job_id` quando necessario, read-only. Runtime implantado reportado pelo executor SHA `00e3882e0ece827ca0f5b6fd7b29d4c2b3e50d6d`, imagem local `sha256:f64d495a04634e0c34e2325ed492b3217b2a7fc3cad642237246ca96cbe80ea3`. O consumidor nao leu diretamente o SHA do processo; comprova presenca e funcionamento dos contratos novos.

| Produto | Job + identidade documental | Ledger `structure_validation.v1` | Resultado observado |
|---|---|---|---|
| `90263572` | `RUNNING` com `job_id=aj-1cc0e33d618c44bd`, recuperado `COMPLETED`, `result_ready=true`; SHA PDF `9021fce05c608655e538f67cdaac08c7484ebbe16a8888e83fbeec9ecaa28d3e` | `DRAFT/CANDIDATE`, 56 esperadas, 35 observadas, 33 code pairs, 0 structural pairs, 33 code-only, 0 proven; global `INCONCLUSIVE` | O0001/10080004 ledger preserva pagina 2, `component_table`, bbox `[351.8444,270.8171,395.0739,283.2296]`, `localized_ocr_recheck`, confianca 0.99988496 e SHA igual ao PDF. Counter definitions explicam 33 pares por codigo vs 1 MATCH_CANDIDATE em guided_investigations. RES-02/03 `PASS` observado. |
| `90264030` | `job_id=aj-78aa8a46b057447e`, `COMPLETED`, PDF SHA `909b440a84fb00868ead4825f8c558ccf2c233b673655941bb7d32b6d1c59692`, `same_document_verified=true`; 13/13 paginas OCR | 82 esperadas, 93 observadas, 77 pares de codigo, 55 estruturais candidatos, 22 code-only, 0 proven; global `DIVERGENCES_CANDIDATES` | 10 findings candidatos: 5 `DRAWING_ONLY`, 5 `BOM_ONLY`; todos `PENDING_HUMAN_REVIEW`, nenhum NC automatica. RES-01 `PASS` para 13 paginas. |
| `90264017` | `job_id=aj-c37a6e78dfc74925`, `COMPLETED`, SHA PDF `5452aabd3ddf94d5d004fe5c4d27c2daca9fcf8759a0c1b849b415d4769e32ee`, `same_document_verified=true`; 14/14 paginas OCR | 96 esperadas, 83 observadas, 71 pares de codigo, 49 estruturais candidatos, 22 code-only, 0 proven; global `DIVERGENCES_CANDIDATES` | 1 `DRAWING_ONLY` candidato para componente `10081389`, pai `70260008`, pagina 9, `set_span`, `PENDING_HUMAN_REVIEW`. `TO_VERIFY` se corresponde a tabela vigente e nao historico de revisao. RES-01 `PASS` para 14 paginas. |
| `90263520` | `job_id=aj-f702d4aaeb3641b3`, `COMPLETED`, PDF SHA `08bf68690401438ab09c0e7ffcd1126bf98b238de776bc680db587704e4fb200`, `same_document_verified=true`; 1/1 pagina OCR | 20 esperadas, 24 observadas, 20 pares de codigo, 11 estruturais candidatos, 9 code-only, 0 proven; global `INCONCLUSIVE` | 0 findings, sem exigir divergencia historica da BOM. |

**Veredicto dos tres residuais:** `RES-01=PASS` (jobs longos retornaram conclusao pelo MCP), `RES-02=PASS` (evidencia OCR univoca O0001 preservada no ledger real), `RES-03=PASS` (campos `code_pair_candidates`, `structural_pair_candidates`, `code_only_pair_candidates` e `counter_definitions` presentes com semantica explicita). `MCP_E2E_4_CASES=PASS` para disponibilidade do fluxo candidato e contratos; **nao significa AC-E1-07 qualidade visual PASS ou VAL01_COMPLETED**.

**Gates restantes:** inspeção de fonte no finding `90264017/10081389` para evitar falso vigente; a regressao completa dos 13 PDFs `TEST_NOT_RUN` neste reteste; AuthZ negativa autenticada e performance medida `TEST_NOT_RUN`; politica oficial de quantidade/unidade, descricao, posicao BOM, revisao e GT/thresholds `OWNER_BLOCKED`. Nao criar NCs e nao atribuir `proven_matches>0` sem GT.

**NEXT_BOUNDED_STEP:** revisar o unico finding `90264017/10081389` com evidencia da tabela vigente e, somente se erro comprovado, corrigir filtro de revisao (menor diff); executar a regressao dos 13 PDFs e metricas com denominadores, no caminho de jobs sem timeout sync. Atualizar esta secao e a Issue #131, sem documentos adicionais. `VAL01_COMPLETED=false`.


### 39.14 Reancoragem Coordination e triagem P0 90264017/10081389 (2026-11-05)

**Executor:** ChatGPT / EVA — Architecture & Coordination. **Natureza:** leitura autenticada MCP e GitHub; sem mudança de runtime, OCR, regras ou NC. **Base remota:** `main=32ac764132dc119b85b4dedf47be9022b238d3bc` no instante da consulta, 1 commit à frente de `6730f68d` (mudanças em DÉLIA, sem arquivos de Engenharia na comparação). `git status` do host e SHA atual do container: não verificados.

**P0 focal:** `product.drawing_understanding` autenticado para `90264017` retornou `COMPLETED` / job `aj-c37a6e78dfc74925`, PDF SHA-256 `5452aabd3ddf94d5d004fe5c4d27c2daca9fcf8759a0c1b849b415d4769e32ee`, 14/14 páginas e `same_document_verified=true`. `code_contexts` contém `10081389` na página 9, `region=component_table`, `bounding_box_px=[360,112,415,112,415,126,360,126]`. `revision_history.candidate=false` no resumo global e região `component_table` candidata na página 9. A linha OCR tipada agrega `10081389`, `10081685` e `10091368` num campo `item`; portanto não tomar associação de linha/coluna como GT. Ledger mantém `DRAWING_ONLY/CONFLICT_CANDIDATE` sob `70260008`, `proven_matches=0`, `automatic_nc=false` e `engineering_approval=NOT_APPROVED`.

**BOM oficial:** leitura autenticada `product.structure(90264017)` retornou estrutura disponível; busca recursiva no payload de `items/components` não encontrou `10081389` (`0` ocorrências no payload consultado). Isso **não demonstra** identidade de revisão/efetividade com o PDF, nem suficiência de completude do contrato para uma conclusão técnica. **Inspeção visual direta do raster da página 9: TEST_NOT_RUN** nesta rodada. **P0 verdict=INCONCLUSIVE**: evidência positiva de OCR na região de tabela; hipótese de histórico de revisão enfraquecida, mas não refutada por revisão visual; compatibilidade BOM×PDF e parentesco lógico ainda exigem verificação.

**NEXT:** inspecionar visualmente a página 9 do PDF SHA exato, distinguir a célula real da região de revisão, validar associação ao conjunto `70260008` e fingerprint temporal da BOM com owner; se falso positivo demonstrado, corrigir apenas a fronteira causal e regredir; caso contrário, manter finding candidato para revisão humana. Após P0, executar regressão de 13 PDFs no SHA implantado e organizar decisões técnicas de Engenharia. `VAL01_COMPLETED=false`; `E2–E7=FROZEN`; nenhuma nova abstração, documento ou plano.

### 39.15 Inspeção visual da página 9 e separação de linhas densas (2026-11-06)

**PDF oficial:** `/drawing-pdfs/90264017.pdf` na biblioteca da api-delpi. SHA-256 `5452aabd3ddf94d5d004fe5c4d27c2daca9fcf8759a0c1b849b415d4769e32ee`, igual ao registrado. 14 páginas. A camada de texto do PDFium na página 9 não contém os códigos da tabela; a leitura foi do raster em escala 8.

**Tabela vigente, página 9, célula mesclada do conjunto `70260008` (CHICOTE BUHLER 0020/02934), linhas separadas:**

| Item | Qtd | Componente | Descrição |
|---|---|---|---|
| C | 6 | `10081389` | TERM. TUBULAR 1,50MM2 |
| D | 3 | `10081685` | TERM. TUBULAR DUPLO 1,50MM2 |
| E | 2 | `10091368` | CONECTOR STOCK 3 VIAS |

O histórico de revisão da mesma página não cita esses códigos. `10081389` é componente vigente, filho visual de `70260008`, não resíduo de revisão. O `DRAWING_ONLY` candidato permanece: a leitura anterior da BOM não encontrou o código, e esta rodada não reconsultou a estrutura oficial nem a efetividade. Não é não conformidade.

**Causa raiz:** `ROW_ASSOCIATION_ERROR` e `COLUMN_ASSOCIATION_ERROR` em `understanding.py`. A tolerância de linha era 2% da altura da página, maior que o passo de uma tabela densa, e a de coluna era 5% da largura. Os três códigos caíam na mesma linha e, com o cabeçalho desalinhado, no campo `item`. O pai `70260008` por `set_span` coincide com a célula mesclada; o erro comprovado é a fusão de linhas e de coluna, não o histórico.

**Correção:** `_cluster_tolerance` limita o agrupamento a 45% do passo mediano observado. Coluna cuja maioria são códigos 6–11 dígitos permanece `component_code` mesmo se o cabeçalho mais próximo for Item ou QTD. Sem exceção para `90264017` ou `10081389`.

**Testes:** `test_dense_rows_stay_separate_component_lines` e `test_same_line_code_and_description_stay_one_row`, mais a suíte `test_drawing_understanding_r8.py` (18 passed). Corpus de 13 PDFs: `TEST_NOT_RUN`. Sem deploy nesta etapa.

**Invariantes:** `DRAFT/CANDIDATE`, `engineering_approval=NOT_APPROVED`, `automatic_nc=false`, `proven_matches=0`. `VAL01_COMPLETED=false`. Quantidade, unidade, revisão e ground truth continuam com a Engenharia.


### 39.16 Reteste MCP do caso 90264017 apos correcao de linhas densas (2026-11-05/06)

**Natureza:** execucao autenticada somente leitura pelo consumidor ChatGPT/EVA, sem deploy. **Codigo em GitHub:** commit `367a73209e24a66fc0696af18c75417e179b3a51` inclui correcao de `_cluster_tolerance` e coluna com maioria de codigos. A comparacao `367a732...main` revelou apenas um commit adicional no modulo DÉLIA, nao Engenharia. **Runtime SHA/container/digest:** `NOT_VERIFIED`.

**Fonte BOM:** `read(product,structure,ref=90264017)` = `success=true`, `status=available`; o codigo `10081389` nao aparece no payload consultado. Essa ausencia nao prova divergencia de revisao/efetividade comparavel; a API nao demonstrou fingerprint temporal compativel com o PDF.

**Execucao:** `analyze(product.drawing_understanding,{product_code:90264017})` retornou `RUNNING`, `job_id=aj-6a88304ab0864c45`; consulta com o `job_id` retornou `COMPLETED`, `result_ready=true`, `same_document_verified=true`, PDF SHA-256 `5452aabd3ddf94d5d004fe5c4d27c2daca9fcf8759a0c1b849b415d4769e32ee`.

**Resultado observado em `understanding.component_table.rows`, pagina 9:** **FAIL funcional para o contrato esperado depois do fix**: uma unica linha logica `row=1` com `item="d e c 6 3 2 10081389 10081685 10091368"`, `component_code=null`, `description=null`; o campo `quantity` agrega descricoes dos tres componentes. Portanto o consumidor ainda observa fusao C/D/E, apesar do commit ja existir no GitHub. **Nao atribuir root cause ao codigo corrigido** sem verificar SHA do processo e se o job foi produzido/reutilizado antes do deploy; o `AnalysisJobStore` pode devolver um job ja existente da mesma identidade/parametros. Este resultado **nao comprova** que o novo algoritmo falha no PDF real, pois nao ha evidência de que ele foi executado.

**Resultado de aceite:** `MCP_PDF_90264017_POST_FIX=FAIL_OBSERVED / RUNTIME_IDENTITY_UNVERIFIED`; `REGRESSION_13=TEST_NOT_RUN`; `VAL01_COMPLETED=false`. Nao executar regressao integral e atribui-la ao novo SHA enquanto runtime nao for confirmado. Sem NC automatica.

**Proximo passo bloqueado:** operador autorizado verificar imagem SHA efetiva, reinicio e identidade do job/processo, confirmar que o commit `367a732` entrou no build; somente apos os gates normais realizar deploy canônico autorizado, iniciar job novo com identificador de versao reconhecido ou ciclo correto do store, provar linhas C/D/E separadas no mesmo PDF e seguir a regressao dos 13 PDFs do Doc 120, performance, AuthZ e politicas oficiais. Atualizar Issue #131 com as evidencias. 


### 39.17 DEC-VAL-036 — Percepcao tabular reutilizavel para VAL-01 e consumidores futuros (2026-11-06)

**Tipo da decisao:** atualizacao de plano e direcao arquitetural, `PLANNED`; **NAO IMPLEMENTADO / TEST_NOT_RUN**. Este registro nao e autorizacao de deploy, substituicao de framework, novo bounded context ou ampliacao da frente ativa. **VAL-01/E1 continua a unica entrega ativa; E2–E7 congeladas.** Carimbo (VAL-02) figura somente como **consumer futuro demonstrativo de reutilizacao**, nao como escopo de implementacao ou aceite neste pacote.

**Problema / evidencia atual:** Doc 119 §38 confirmou que o `TableStructureEngine`/SLANet executava no caminho produtivo com recorte de `component_table` apenas na primeira pagina; suas celulas eram usadas em metricas/resumo e nao compunham o `component_table` semantico do `understanding.py`. Este usa agrupamentos X/Y, tipagem por cabecalho/conteudo e o comparador ainda busca codigos em campos agregados. Em §39.15, a tabela vigente da pagina 9 do PDF oficial `90264017` continha tres ocorrencias distintas C/6/`10081389`, D/3/`10081685`, E/2/`10091368`, com celula mesclada `70260008`. Em §39.16, consumidor MCP continuou observando as tres linhas fundidas; **runtime SHA nao verificado**, logo isso nao comprova falha do commit corretivo no processo novo. Corpus de 13 PDFs no novo SHA permanece `TEST_NOT_RUN`.

**Objetivo de capability:** reconhecer e preservar a **geometria estrutural de qualquer regiao tabular suportada** antes de interpretacao de negocio: tabela de materiais, carimbo, tabela de revisoes, grades de inspecao e outras regioes candidatas, sem codificar semantica DELPI no detector. Nao declarar suporte universal: cada familia/layout exige benchmark e cobertura `SUPPORTED/UNSUPPORTED/INCONCLUSIVE`. Nao desenvolver OCR, table-detector ou parser visual proprio se o recurso nativo existente atender.

**Quatro capacidades em fronteiras distintas (reutilizacao horizontal, semantic consumers verticais):**

1. **Percepcao de tabela (generica):** localizar regioes tabulares com pagina/coords/sistema de escala; reconhecer limites, linhas, colunas, celulas, `rowspan/colspan`, ordem de leitura e ambiguidade estrutural, inclusive tabelas densas, sem bordas, multiplas e multipagina quando suportado. Esta camada nao conhece codigo de produto, BOM, carimbo nem politica de revisao.
2. **Conteudo por celula (generico):** associar tokens OCR/camada digital a celula e preservar texto bruto, geometria original, confianca de OCR, engine/config/model version, documento SHA e conflitos/unassigned; nao concatenar linhas adjacentes nem fabricar celulas/valores por proximidade sem evidencia.
3. **Interpretacao contextual (consumers):** `component_table` interpreta cabecalhos, item, qtd, unidade, descricao, componentes e spans de conjunto; futuro `title_block` interpreta campos de carimbo sobre a **mesma estrutura perceptual**, sem duplicar detector, OCR nem formacao de grade. `revision_history` possui semantica propria e nao comprova componente vigente. Regras e identificadores de Engenharia permanecem somente nas camadas de dominio/application apropriadas.
4. **Validacao governada (consumers):** comparador BOM recebe ocorrencias com associacoes explicitas e evidencia; nao usa varredura por regex em campos fundidos como substituto de relacao estrutural comprovada. Carimbo e outros consumers futuros usarao suas fontes oficiais e policies proprias em fases autorizadas, nunca prematuramente.

**Abstraction Gate e desenho minimo:** antes de qualquer novo contrato intermediario, inventariar `TableStructureEngine`, `table_structure_engines`, `association`, `component_table`, `code_contexts` e adapters atuais; verificar se suas estruturas permitem representar `table→rows/columns/cells→spans→token associations→provenance`. Preferir extensao **aditiva e provider-neutral** ao contrato existente em vez de criar service/registry/banco/queue/engine paralelo. Conservar Clean Architecture: frameworks e modelos permanecem em adapters; dominio/application consome observacoes neutras e nao SDK. Publicacao e aprovacao continuam humanas/governadas.

**Framework-first / decisao condicionada ao benchmark:**
- **Baseline A:** SLANet ja instalado, com inspecao de parametros efetivos (modelo/versao, renderizacao, dpi, rotacao, crop, escala, coordenadas, detecao de tabela/celulas, OCR↔celula, formato de rowspan/colspan, suporte pagina N e throughput). Nao supor que a ferramenta entrega spans confiaveis sem observar output real. Verificar por que output estrutural nao tem consumer semantico e se os resultados nativos bastam.
- **Benchmark B, somente se A insuficiente:** avaliar recursos de table-recognition disponiveis na **versao efetivamente instalada** do PaddleOCR, inclusive PP-TableMagic/SLANeXt quando compativeis. Diferenciar disponibilidade upstream de instalacao e suporte local. Sem entrada automatica em producao.
- **Benchmark C, somente se necessario:** PP-StructureV3 para layout/documentos complexos, condicionado a compatibilidade, artefatos/modelos, licencas, desempenho, seguranca, owner e gate de deploy. Nenhum framework novo aprovado antecipadamente.
- **Proibido:** heuristica hardcoded por codigo/produto, layout/posicao fixa, regex como parser estrutural ou novo OCR de raiz. Regex deterministica pode validar/normalizar formato **apos** associacao de celula confiavel.

**Sequencia executavel proposta, sem abrir subfrente:**

| Passo | Trabalho | Evidence / stop condition |
|---|---|---|
| G0 — identidade | Verificar `origin/main`, git status no ambiente executor, SHA/digest do processo, configuracao/modelos e lifecycle/cache/job_id; garantir reprocessamento realmente no SHA avaliado | Sem identidade do runtime/job: `INCONCLUSIVE`, nao atribuir resultados a fix novo |
| G1 — trace de fronteiras | Escolher pagina 9 de `90264017` + casos variados do Doc 120; capturar PDF/render, OCR tokens, deteccao/layout, celulas do SLANet, associacoes e `understanding.component_table`; localizar primeira perda de estrutura | Captura vinculada a SHA PDF/code/config/model, paginas e coordenadas; sem alterar codigo de producao |
| G2 — benchmark de percepcao | Comparar A e, conforme gate, B/C em mesmas imagens e GT visual, incluindo tabelas de materiais e pelo menos uma regiao tabular nao BOM como teste de independencia **sem implementar VAL-02** | Precisao/recall de celulas, row/col association, spans, texto↔celula, duplicacoes/fusoes, abstenção, tempo/memoria; falha estrutural causa `INCONCLUSIVE`, nao semantica forjada |
| G3 — integracao minima | Se framework suficientemente correto, fazer output estrutural alimentar o contrato neutro existente e consumer `component_table`, preservando incertezas, revisoes e pais por evidencia; nao codificar termos de BOM em percepcao | Testes de contrato + componentes C/D/E separados **e** casos negativos/multilinha/mesclados/multitabela |
| G4 — regressao/release | Reexecutar os 13 PDFs no mesmo SHA/config/model, casos holdout de layouts nao usados no ajuste, AuthZ, performance, MCP/E2E e negative cases; review e deployment governados quando autorizado | Baselines por familia e AC-E1-02/03/04/06/07/10; gates sem afrouxamento, `proven_matches=0` ate GT e aprovacao; falha exige reavaliar opcao, nao patch por produto |

**RQ a detalhar no mesmo Doc 119 antes da implementacao:** `RQ-E1-TABLE-01` observacao tabular agnostica do dominio; `RQ-E1-TABLE-02` geometrias/celulas/spans/associacoes/proveniencia; `RQ-E1-TABLE-03` consumidores de semantica desacoplados e extensibilidade demonstravel para carimbo; `RQ-E1-TABLE-04` fail-closed e comparador sem inferencia de vinculo a partir de texto agregado; `RQ-E1-TABLE-05` benchmark de framework com custo/qualidade medidos; `RQ-E1-TABLE-06` integridade operacional code/model/config/PDF SHA/job_id, regressao 13 e holdout. Aplicar os **AC-E1-01..10 existentes** e suas metricas; nao criar outro sistema de aceite.

**Prova de generalizacao:** demonstrar uma mesma saida estrutural neutra representando (a) tabela BOM com conjunto/filhos e (b) **carimbo como estrutura tabular sem interpretacao/validacao de campos do carimbo**; verificar que a primeira camada nao possui dependencias de `product_code`, BOM, `title_block`, policies ou nomes de coluna. Interpretadores posteriores podem ser distintos e versionados pelo owner correto. Se nao houver evidencia suficiente, reportar `UNSUPPORTED/INCONCLUSIVE`, sem criar regressao silenciosa.

**Status/autoridades:** `PLAN_UPDATED` somente; `CODE_IMPLEMENTATION=NOT_STARTED_FOR_DECISION`; `BENCHMARK=TEST_NOT_RUN`; `REGRESSION_13=TEST_NOT_RUN`; `ENGINEERING_GT=OWNER_BLOCKED`; `ENGINEERING_APPROVAL=NOT_APPROVED`; `VAL01_COMPLETED=false`. Core/AuthZ e Domain APIs/Engineering owners preservados. **Proxima acao:** G0 e G1, revisao da saida estrutural real e configuracoes instaladas, sem instalar novos frameworks ou alterar a arquitetura antes dos resultados.

### 39.18 Diagnostico G0/G1 — SLANet versus Understanding na pagina 9 (2026-11-06)

**Tipo:** investigacao somente. Nenhum codigo produtivo, contrato, modelo ou deploy foi alterado. `VAL01_COMPLETED=false`.

**Identidade.** Checkout do srv-api apos este registro: `71a5373bbb`. Imagem em execucao: `sha256:f64d495a04634e0c34e2325ed492b3217b2a7fc3cad642237246ca96cbe80ea3`, inicio `2026-11-06T00:52:02Z`, healthy. Dentro dessa imagem, `understanding.py` nao contem `_cluster_tolerance` e `engine_adapters.py` contem `pdf[0]` e `row=i // 8`. O commit `367a73209e` esta no Git e no checkout, mas nao nesta imagem. PDF diagnosticado: `/drawing-pdfs/90264017.pdf`, SHA-256 `5452aabd3ddf94d5d004fe5c4d27c2daca9fcf8759a0c1b849b415d4769e32ee`, 14 paginas. A chamada abaixo foi direta a biblioteca, no recorte superior esquerdo da pagina 9 (indice 8). Nao e a chamada de `TableStructureEngine.run`, que renderiza somente `pdf[0]` e ignora `pages`.

**Inventario no container.** `paddleocr==3.3.0`. Modelos em cache: `SLANet`, `PP-LCNet_x1_0_table_cls`, `PP-OCRv5_server_det`, `en_PP-OCRv5_mobile_rec`. Nao ha diretorio SLANeXt, PP-TableMagic nem pesos de PP-StructureV3. O pacote exporta `TableStructureRecognition`, `TableCellsDetection`, `TableRecognitionPipelineV2` e `PPStructureV3`; so o primeiro foi executado. OCR de producao: `PaddleOcrAdapter`, `ENG_DRAWING_OCR_MODEL_DIR=/opt/ocr-models`, CPU. Render PDFium da pagina 9: escala `2.7778`, `2339×1653` px. Recorte medido: `1356×528`.

**SLANet na pagina 9, chamada direta.** HTML com 14 `<tr>`, 69 `<td>`, 10 `rowspan`, 12 `colspan`, `structure_score=0.946`, 69 bboxes. OCR do mesmo recorte, 69 tokens, confianca dos codigos acima de `0.999`. Centros: item C `(297, 120)`, quantidade 6 `(330, 119.5)`, codigo `10081389` `(388, 119)`; D `(296, 140)` / 3 `(330, 140)` / `10081685` `(388, 139.5)`; E `(297, 160)` / 2 `(330, 160.5)` / `10091368` `(388.5, 159.5)`. Tres celulas distintas receberam os tres codigos: celula 30, span `(1,1)`, texto `6 10081389`; celula 36, span `(1,1)`, texto `3 10081685`; celula 42, span `(1,2)`, texto do codigo junto com a descricao. O item C/D/E ficou fora dessas celulas. `70260008` foi lido em `(71.5, 178.5)` e nao caiu em nenhum bbox. As celulas `rowspan` vizinhas nao cobrem esse ponto. O SLANet separou os tres codigos em celulas diferentes e nao recuperou a celula mesclada do conjunto.

**Understanding na imagem em execucao.** `build_understanding` dos mesmos tokens, com tamanho de pagina `2339×1653`, produziu uma linha `item='D C E 6 3 2 10081389 10081685 10091368'`. O modulo nao le `table_structure_engines`. A tolerancia vigente e `2%` da altura, `33.06` px; o passo C–D–E e cerca de `20` px. O codigo publicado calcula, para esses centros, tolerancia `9.45` px. Essa conta foi feita no codigo local; o `build_understanding` publicado nao foi executado no processo. Jobs `COMPLETED` do mesmo dono e dos mesmos parametros continuam reutilizaveis por `3600` s.

**Primeira perda.** No caminho produtivo, a pagina 9 nao chega ao SLANet. Na chamada direta, a estrutura completa — tres linhas e a celula mesclada — ja se perde no SLANet, porque o conjunto pai fica sem celula e a quantidade entra na celula do codigo. As tres linhas de codigo, que o SLANet ainda devolveu separadas, sao fundidas depois pelo Understanding da imagem atual. O HTML de `rowspan`/`colspan` nao entra em `make_cell`: o adapter grava `row=i // 8` e `col=i % 8`.

**Reutilizacao e alternativas.** O mesmo `TableStructureRecognition` no recorte inferior direito da pagina 1 devolveu grade de 4 linhas e 9 celulas, um `rowspan`, score `0.975`, sem interpretacao de carimbo. Isso mostra que o motor nao depende do significado de BOM. Nao valida o carimbo nem os outros layouts do corpus de 13 PDFs (`TEST_NOT_RUN`). Nao ha motivo, nesta evidencia, para instalar SLANeXt ou PP-StructureV3 antes de consumir a grade ja produzida e de remedir a celula pai no recorte produtivo da pagina correta.

**Proxima acao, ainda nao autorizada:** fazer o adapter honrar a pagina do recorte, preservar span nativo e fazer o Understanding consumir celulas em vez de reagrupar por fração fixa da pagina. Repetir a pagina 9 e uma regiao de carimbo no mesmo SHA de processo. `VAL01_COMPLETED=false`.

### 39.19 Integração da percepção nativa — código local, sem deploy (2026-11-06)

**Tipo:** implementação da DEC-VAL-036 no código, sem deploy e sem modelo novo. `VAL01_COMPLETED=false`. `ENGINEERING_APPROVAL=NOT_APPROVED`.

**O que mudou.** `TableStructureEngine` renderiza a página pedida (`pages` 1-based; índice físico = página − 1) na escala do OCR de 200 dpi. Página inexistente, recorte invertido ou fora da folha e raster de tamanho diferente do OCR retornam `PAGE_NOT_IN_DOCUMENT`, `INVALID_CROP` e `COORDINATE_MISMATCH`, sem chamar o SLANet. O HTML nativo define `row`, `col`, `rowspan` e `colspan`. A projeção `i // 8` saiu desse adapter. Tokens já produzidos pelo pipeline são reaproveitados; o OCR completo só roda de novo quando o chamador não entrega tokens. O Understanding substitui as linhas agrupadas de uma página somente quando a grade é consistente e tem texto. Célula com quantidade e código juntos fica `INCONCLUSIVE` e não é partida. Texto de `rowspan` permanece na linha âncora. Região de carimbo usa o mesmo motor e fica em `table_perception`, sem interpretação de VAL-02. A identidade dos jobs de análise e de understanding inclui `table_perception=native_slanet_v1`, para não reutilizar um `COMPLETED` anterior por 3600 s.

**Contratos.** `drawing_perception_candidate.v1` e `structure_validation.v1` permanecem. `make_cell` ganhou `rowspan` e `colspan` com default 1. Os erros `NO_TABLE_REGION`, `PAGE_NOT_IN_DOCUMENT`, `INVALID_CROP` e `COORDINATE_MISMATCH` entram no conjunto fechado; `NO_TABLE_REGION` já era emitido e era descartado por não pertencer ao conjunto. `proven_matches=0`, `automatic_nc=false`, `DRAFT/CANDIDATE`.

**Testes locais.** `pytest` de `test_table_perception_native.py`, `test_drawing_perception_r9.py`, `test_drawing_understanding_r8.py` e `test_bom_structure_comparator.py`: 71 passed. A página 9 de um PDF falso é o índice 8 renderizado. Três linhas C/D/E com códigos distintos permanecem três linhas. A célula `6 10081389` não vira quantidade e código separados. `70260008` em `rowspan` não é copiado para a linha seguinte. Observação com erro não apaga a linha agrupada. O parser não recebe `product_code`.

**Não medido nesta execução.** A imagem `sha256:f64d495a…` continua sendo a de `2026-11-06T00:52:02Z` e não contém este código. Não houve deploy. Corpus de 13 PDFs, holdout, MCP E2E e nova chamada SLANet da página 9 oficial sobre o adapter novo: `TEST_NOT_RUN`. A limitação já medida no §39.18 permanece: no recorte da página 9 o SLANet não devolveu célula para `70260008`. Este código não inventa esse parentesco.

**RQ.** `RQ-E1-TABLE-01` observação neutra em `table_perception`. `RQ-E1-TABLE-02` spans nativos no contrato da célula. `RQ-E1-TABLE-03` carimbo só como observação, VAL-02 fechada. `RQ-E1-TABLE-04` associação mista inconclusiva, sem preencher campos. `RQ-E1-TABLE-05` benchmark de modelo novo não aberto: o SLANet instalado passa a ser consumido. `RQ-E1-TABLE-06` identidade de job atualizada; regressão de runtime ainda pendente. Os AC-E1 existentes não foram substituídos.

### 39.20 Deploy da percepção nativa e medição no PDF oficial (2026-11-06)

**Deploy.** Checkout do srv-api: `92ae661d04`, que contém `9c59bab3ef` e não altera `engineering-api` depois dele. Imagem nova: `sha256:6ffae36ed9ae8526da09667baccbfddd7e5665fff5efe8c791fcd5cfbf3d0e1f`, início `2026-11-06T13:23:59Z`, health 200. Imagem anterior preservada: `sha256:f64d495a…`. Core API não foi recriado. Dentro do processo: `pdf[0]` ausente, `i // 8` ausente, `page_select` verdadeiro, `native_slanet_v1` presente, PaddleOCR 3.3.0, modelo SLANet em cache. Rollback não foi necessário.

**Testes antes do build.** 84 passed em `test_table_perception_native.py`, `test_drawing_perception_r9.py`, `test_drawing_understanding_r8.py`, `test_drawing_understanding_jobs.py`, `test_bom_structure_comparator.py` e `test_analysis_jobs.py`.

**Página 9 de `90264017`.** SHA `5452aabd…32ee`, 14 páginas. Processo lateral no container novo, sem job MCP: OCR 162 tokens, `2339×1653`, 5,9 s. SLANet na região `component_table` com `processed_pages=[9]`, `pdf_sha_match=true`, grade consistente, 5 `<tr>`, 21 células, score `0.981`, 0,5 s. A topologia consumida é `native_table_cells`. Os três códigos ficaram na mesma célula, `r=1 c=1`: `10081389 10081685 10091368 2`. Item, quantidade e código tipados ficaram vazios e o status da linha é `INCONCLUSIVE`. `70260008` apareceu na célula `r=0 c=0`, `rowspan=16`, junto com as letras A–E e outras linhas. Não foi promovido a pai comprovado. O recorte vindo do agrupamento de tokens cobre a largura inteira da folha (`x 0–2339`, `y 79–280`) e mistura tabela, carimbo e histórico na mesma imagem. A mesma chamada no recorte `title_block` da página 9 devolveu 7 linhas e 14 células, score `0.990`, sem interpretação de VAL-02.

**Corpus.** Percepção de uma página por PDF, SHA conferido com o Doc 120, sem comparador BOM e sem ground truth de célula. Todos os 13 produziram grade consistente na página medida. Vários têm célula com dois ou mais códigos. `90264030` página 2 devolveu só 1 linha e 5 células: medição insuficiente, não uma regressão de BOM. Uma execução contínua de OCR quebrou com `RuntimeError` do Paddle a partir do terceiro arquivo; processos separados concluíram o restante. A API permaneceu healthy. Memória do serviço após as medições: cerca de 250 MiB. Não há percentual de acerto inventado.

**MCP.** POST anônimo em `/apps/engineering-api/mcp` retornou 401. Não houve token de usuário, então não existe `JOB_ID` novo. O resultado `aj-13b745a9e5ce4c01` continua sendo da imagem antiga. `VAL01_COMPLETED=false`.

## 39. DEC-VAL-036 — recorte da tabela derivado de colunas conectadas (2026-11-06)

**Causa-raiz (medida em `90264017` p9):** o recorte ao SLANet era o envelope de todos os tokens da faixa/retângulos gráficos — misturava component_table + carimbo (`70260008`/`CHICOTE BUHLER`/cliente) + histórico. SLANet estruturava a mistura numa grade única: `rowspan=16` com `A B C D E 70260008 CHICOTE BUHLER…` e células artificialmente mescladas (`10081389 10081685 10091368 2`).

**Correção (`47be2a8e0d`):**
- `understanding._connected_column_crop`: recorte = extensão das células das colunas ligadas à coluna de códigos (regra de gap já existente); margem = altura mediana da célula ≤2% página; `boundary_source="connected_columns"`; `unreliable_boundary=false` se span ≤60%.
- `paddleocr_adapter`: `self._engine=None` após timeout/RuntimeError — elimina RuntimeError em multipágina (predictor morto reutilizado).
- `TABLE_PERCEPTION_REVISION="native_slanet_v2"` (job não reutiliza COMPLETED v1); bridge usa a constante nos dois paths.

**Evidência real (prod `47be2a8e0d`, PDF `5452aabd…32ee`, p9):** recorte `[1,56,1273,303]`; SLANet score 0.97; 68 células/11 linhas; códigos C/D/E em linhas separadas; `70260008` em célula própria; carimbo/histórico fora da grade. Residual: coluna item/qtd densa colapsa (`"C 6 D 3"`) — códigos e descrições corretos.

**Testes:** 88/88 escopo overlay; +4 novos (crop exclui admin, coluna próxima dentro, títulos não criam crop, engine morto descartado). `CHATGPT_CONSUMER_PASS` PENDING.

## 40. DEC-VAL-036 — diagnóstico do "erro interno" no poll do job MCP (2026-11-06)

**Evidência (logs prod):** job `aj-2bae011fef854f09` criado → `RUNNING` → polls com erro. Sem `eva_mcp_tool_error`, sem atividade OCR/modelos no container atual — o job **não chegou ao estágio visual neste processo**. Mecanismos convergentes (ambos produzem "erro interno" no conector): (a) store process-local (`AnalysisJobStore`) perde jobs em restart/deploy — container recriado 16:03; (b) falha tipada cedo — `DrawingAnalysisError` em delegated fetch (janela do `401` às 16:29:53) → `_store.fail` **sem log** → poll retorna FAILED tipado.

**Correção (`63211b907d`/`8494379aeb`, aditivo):**
- `job_not_found` nos dois paths (`drawing_analysis`/`drawing_understanding`) agora informa process-localidade e retorna `retriable:true` + `retry` — consumidor pode re-submeter em vez de erro fatal.
- `_run_job`: `DrawingAnalysisError` loga `drawing_job_failed` (antes só `Exception` genérico logava — falhas tipadas invisíveis).

**Testes:** 142/142 (jobs + eva_mcp) overlay. Prod `8494379aeb` healthy.

**Pendente arquitetural:** persistência do job store (sobreviver restart) — `ARCHITECTURE_DECISION_REQUIRED`, fora do escopo bounded.

## 41. DEC-VAL-036 — event loop congelado por benchmark síncrono (causa-raiz forense + fix)

**Causa-raiz (PROVEN):** `run_visual_benchmark` executava `run_pipeline_isolated` (Popen.communicate) **sincronamente dentro do event loop** — durante a análise visual (subprocesso `visual_worker` a 99% CPU) o servidor não respondia: healthchecks mortos (UNHEALTHY), polls MCP → "The tool failed internally" no conector. Evidência: `visual_worker` ativo + `/proc/1` sleeping + health interno TimeoutError(5s) + zero `eva_mcp_tool_error` (nenhuma resposta era produzida).

**Correção (`5a9b86c6d2`):** `document_benchmark_service` executa ambos os benchmarks via `asyncio.to_thread` — loop responsivo enquanto o subprocesso isolado computa; lifecycle (timeout/kill) inalterado. Contrato zero, arquitetura zero.

**Teste:** `test_async_benchmark_offload` prova progresso de coroutine concorrente durante benchmark bloqueante. 137/137 + 1 novo.

**Prod:** `5a9b86c6d2` healthy. Reteste consumidor: job `drawing_understanding` 90264017 → polls devem retornar `RUNNING` durante OCR (não mais erro interno).

## 42. DEC-VAL-036 — multipage OCR: batch isolation por faixa de páginas

**Causa-raiz (confirmada):** o `visual_worker` processava TODAS as 14 páginas num único filho (RLIMIT_AS=12GB). `RuntimeError` transitório (p5) → reset `_engine=None` sem liberar memória nativa Paddle → cada `model_load` seguinte alocava engine novo no mesmo address-space → `MemoryError` em cascata (páginas 6–14).

**Correção (`8dad962414`/`216ee5fd8d`):** `page_start`/`page_end` aditivos no contrato `drawing_ocr_execution.v1`; `run_visual_benchmark` itera batches de `ENG_DRAWING_OCR_PAGE_BATCH` (default 4) em filhos separados — cada filho morre devolvendo nativo ao OS; `_merge_isolated_records` recompõe páginas por número absoluto, proveniência/bboxes/status; `coverage_status` FULL/PARTIAL/NONE aditivo nos records. Campo `coverage_status` no `page_coverage` MCP fica local (aguarda commit do WIP PRC no mesmo arquivo).

**Testes:** 200/201 + 35/35 (isolation, benchmark, jobs, mcp, r7). Prod `216ee5fd8d` healthy. Reteste: 14/14 páginas tentadas; falha num batch não derruba o seguinte.

## 43. DEC-VAL-036 — TypeError mascarando falha real + merge de batch com status correto

**Job aj-b027153fdfe14be1:** `analysis_incomplete` com `TypeError: DrawingAnalysisError.__init__() got multiple values for argument 'code'` — dois defeitos provados:

1. `semantic_bridge:1419` passava `code=` kwarg colidindo com o posicional → TypeError no `except Exception` genérico → falha real (`no_ocr_evidence`, 422) invisível. Fix: code posicional.
2. `_merge_isolated_records` contava `p["ocr"]["status"]` — a convenção real é presença da chave `ocr`. Todo merge reportava `error/NONE` mesmo com evidência plena. Fix: `"ocr" in p` + OR de `has_positional_data`.

**Validação real (PDF 5452aabd, prod-overlay):** 4 batches `[1-4][5-8][9-12][13-16]` executaram — **14/14 páginas, 1533 tokens, 12693 chars**. Batch isolation funciona; o `error` reportado era defeito de contagem do merge, não da execução. `coverage_status` aditivo em `page_coverage` MCP (FULL/PARTIAL/NONE).

**Testes:** 89/89. Prod healthy. Reteste consumidor: job deve completar com cobertura integral ou falha tipada real (não TypeError).

## 44. DEC-VAL-036 — estabilidade nativa multipágina: batch=1 + VMS por morte do filho

**Medição decisiva (docker exec, PDF 5452aabd):** VMS do predictor PaddleOCR cresce ~1-3.5GB por `predict` e **não** é devolvido por reset de engine in-process (medido: 16.1GB após 4 resets). `FLAGS_*` do alocador não altera. RuntimeError surge no limiar ~11.7GB VMS; MemoryError quando alocação cruza `RLIMIT_AS`. Só a morte do processo devolve address-space.

**Correção (`cf4c4362d3`):**
- `_page_batch_size` default 4→**1** — um filho por página; cada filho morre devolvendo VMS completo; falha de página fica isolada àquela página (sem cascata).
- `ENG_DRAWING_OCR_MAX_RSS_MB` compose default 12288→**16384** — headroom para páginas densas (~12GB VMS engine+1pág), bounded pelo máx. existente.
- Per-call engine reset **revertido** (prova: inútil, VMS não volta).

**Custo:** ~12-25s/página (reload por filho) — bounded no budget do job. **Incidente:** probe in-container em paralelo com job real saturou RAM do host (2 pipelines ~12GB VMS) — mitigado por restart; probes agora fora de janela de jobs.

**Testes:** 89/89 escopo. Prod `cf4c4362d3` healthy, `MAX_RSS_MB=16384` live. Reteste consumidor: 14 filhos sequenciais → cobertura FULL esperada ou falha tipada isolada.

## 45. DEC-VAL-036 — SLANet UNAVAILABLE: singleton TableStructureRecognition

**Causa (repro provada):** `_predict_table_structure` instanciava `TableStructureRecognition()` a CADA `run()` — ~1GB VMS por instância no processo uvicorn. Com 2 regiões (component_table + title_block) por job sob pressão de memória, a instanciação falhava → catch-all `except → UNAVAILABLE`, `cells=[]`, mesmo com OCR 14/14 FULL.

**Provas:** SLANet isolado p9 com crop real + 162 tokens reais do worker → 68 células, `error_kind=None` — motor e associação íntegros; perda era lifecycle do modelo no processo compartilhado.

**Correção (`f9d824ebb1`):** singleton `_TABLE_STRUCTURE_ENGINE` com descarte em exceção (mesmo padrão do PaddleOcrAdapter). Uma instância por processo, reutilizada por região/job — elimina recarga mid-job e falha por pressão de VMS.

**Testes:** 27/27. Prod healthy. Reteste: `table_perception` deve mostrar `cells>0` e `error_kind=None` com OCR FULL.

## 46. DEC-VAL-036 — SLANet: observabilidade de UNAVAILABLE + prova do caminho integrado

**Repro integrado (container, PDF 5452aabd):** benchmark batch=1 14/14 + `eng.run` component_table e title_block → **68 células por região, error_kind=None**. O mecanismo funciona sob contexto de memória acumulado — a falha UNAVAILABLE no job `aj-3bd92c11b7ce4632` ainda não foi reproduzida (janela/host).

**Correção (`ec67d8ca00`):** `apply_native_table_observations` propaga `error_detail` (aditivo) — o catch-all já produzia `Tipo:mensagem`; agora o consumidor recebe a causa real em vez de UNAVAILABLE opaco.

**Reteste:** se recorrer, `error_detail` indica a exceção real (memória/render/tokens) — caso contrário, cells>0 + FULL.

## 47. DEC-VAL-037 — Integridade documental do caminho SLANet: refetch→b"" eliminado (2026-11-08)

**TASK_ID:** `EVA-VAL01-SLANET-PDF-SOURCE-INTEGRITY-FIX-PROD`. **Commit:** `a9fa4e6307`. **Deploy:** checkout `a9fa4e6307`, imagem `sha256:253de3fb104936abc615afaf4ec7938098bfb21c6fa43e694fd4567342676ea2`, `delpi-engineering-api` iniciado `2026-11-08T17:30:19Z`, healthy. `VAL01_COMPLETED=false`; `ENGINEERING_APPROVAL=NOT_APPROVED`.

**Causa-raiz (PROVEN no código, cadeia completa):** `_produce_drawing_understanding` refazia `fetch_product_drawing_pdf` **depois** do benchmark OCR multipágina (minutos de execução). O contrato delegado nunca levanta exceção: qualquer falha (timeout 30s sob concorrência, 401 por Bearer expirado mid-job, upstream 5xx) chega como dict `{"status":"unavailable"/"forbidden"/"not_found"}` **sem** a chave `content`. O código lia `_pdf_raw.get("content")` → `None` → `bytes(_pdf_bytes) if _pdf_bytes else b""` → `_open_pdf_document(b"")` gravava arquivo de 0 bytes → `pdfium.PdfDocument` lançava `PdfiumError: Data format error` → catch-all → `error_kind=UNAVAILABLE`. Exatamente o `error_detail` observado no job `aj-03ac71384ba140f9` (página 9, ambas as regiões). O job produzia OCR 14/14 FULL porque o benchmark executa sobre os bytes do **primeiro** fetch (token ainda válido); o SLANet quebrava no **segundo**.

**Defeitos secundários comprovados:** (a) `_open_pdf_document` vazava o arquivo temporário quando `PdfDocument` falhava — reproduzido em teste (órfão em /tmp); (b) `ERROR_KINDS` fechado descartava kinds desconhecidos para `None` — novos kinds de documento precisavam entrar no conjunto.

**Correção (menor diff, fronteira defeituosa, sem nova abstração):**
- `run_official_document_benchmark` devolve `out["_pdf_bytes"]` — o mesmo conteúdo já validado (não-vazio, sha256) consumido pelo OCR. `_produce_drawing_understanding` **não refaz o fetch**: OCR e SLANet operam sobre o MESMO documento, mesma execução autorizada, sem cache/estado novo. `OCR_PDF_SHA256 == SLANET_PDF_SHA256` por construção.
- `TableStructureEngine.run` tipa falhas de ENTRADA antes do PDFium: `DOCUMENT_CONTENT_MISSING` (ausente/vazio), `DOCUMENT_HASH_MISMATCH` (divergente do oficial), `DOCUMENT_CONTENT_INVALID` (sem magic %PDF- nos 1KB iniciais), `PDF_OPEN_FAILED` (PdfDocument falhou) — aditivo em `ERROR_KINDS`; `UNAVAILABLE` volta a significar falha de motor/modelo.
- `_open_pdf_document` remove o tmp também no caminho de exceção de abertura.
- `_table_engine_summary` propaga `error_detail`.
- `TABLE_PERCEPTION_REVISION=native_slanet_v3` — job não reutiliza COMPLETED stale.

**Evidência integrada (container descartável, imagem prod, PDF oficial `90264017` SHA `5452aabd…32ee`, 2.443.597 B):** gates tipados respondem antes do PDFium; `component_table` p9 crop `[1,56,1273,303]` → `error_kind=None`, **68 células nativas**, 11 linhas, score 0.973, `pdf_sha_match=true`. Repetido **dentro do container implantado**: `DOCUMENT_CONTENT_MISSING` + 68 células/sha_match.

**Testes:** `tests/test_slanet_document_integrity.py` (10 casos: missing/invalid/mismatch/open-fail/cleanup/válido/propagação `table_perception`/fetch único/falha tipada de fonte); 2 testes existentes ajustados ao contrato estrito. 24/24 foco; suite engineering-api **859 pass / 3 fail pré-existentes fora do escopo** (allowlist OpenAPI do WIP PRC concorrente; `_normalize_box` sem cv2 na venv).

**Residuais:** job MCP autenticado pós-deploy (`component_table`+`title_block` cells>0 no consumidor, OCR 14/14, `table_perception.source_pdf_sha256`) — pendente do consumidor ChatGPT com token de usuário; corpus de 13 PDFs no novo SHA: `TEST_NOT_RUN`; a segunda obtenção `_pf["pdf_result"]` do path `drawing_analysis` permanece (contrato prefetch DEC-VAL-032, já fail-closed em `analyze_product_drawing`).

## 48. DEC-VAL-038 — Reconstrução geométrica de linhas SLANet (M1+M2) (2026-11-08)

**TASK_ID:** `EVA-VAL01-TABLE-ROW-RECONSTRUCTION-BALLOON-ASSOCIATION-E2E`. **Commit:** `84b87d636b`. **Deploy:** imagem `sha256:b0bf650912d0d31e965402d539e6af22ba64583bfe2f8e6dc82b4bd6c2d5eef7`, `delpi-engineering-api` healthy `2026-11-08T19:12:57Z`. `VAL01_COMPLETED=false`.

**M1 — diagnóstico visual (PROVEN):** render p9 do PDF oficial — réguas de linha íntegras, passo ~20px; o SLANet funde pares de linhas nas colunas estreitas item/qtd em células `rowspan=2` com texto agregado (`"C 6 D 3"`, `"E 2 F 9"`), enquanto separa os códigos. Layout correto, perda na projeção.

**M2 — correção genérica:** `line_texts` por bandas Y de tokens (>0.6×altura mediana) na célula; `rows_from_native_cells` distribui pelas linhas do `rowspan` só quando a contagem coincide; item/qtd em célula fundida só na forma `ITEM QTD`. Sem evidência → `INCONCLUSIVE`. Teste: `C/6/10081389` e `D/3/10081685` separados; 42/42 foco.

**M3/M4 — balões e associação: `TO_INVENTORY`/`TEST_NOT_RUN`.** Não implementado neste pacote — detector, contrato e corpus ficam para pacote próprio com gates B/C/D. Probe OCR-faixa-p9 não retornou tokens (parâmetro do executor) — prova real pós-deploy fica para o job do consumidor.

## 49. DEC-VAL-039 — Reconstrução geométrica real de linhas (fix do split) (2026-11-08)

**TASK_ID:** `EVA-VAL01-REAL-GEOMETRY-ROW-RECONSTRUCTION-PRODUCTION`. **Commit:** `0a6d468f07`. **Deploy:** imagem `sha256:4f9f75ae0ffe…`, `delpi-engineering-api` healthy.

**Causa-raiz dupla (PROVEN em dados reais):** (a) geometria de token usava `bb[3]-bb[1]` → 0 para bboxes quad (8 valores) → `_med=0` → bandas nunca formavam, `line_texts` ausente; (b) centroide de linha idem. Fix: cy/h por min/max dos 4 ys do quad + faixa-Y de linha excluindo células `line_texts`/`rowspan>1`.

**Distribuição (independe de rowspan):** banda → linha nativa cuja faixa-Y de célula confiável contém o cy; fallback centroide. Sem evidência → INCONCLUSIVE.

**Prova integrada REAL** (container descartável, imagem prod, PDF oficial `90264017` sha `5452aabd`, OCR p9): **C/6/10081389, D/3/10081685, E/2/10091368** reconstruídos (antes null); F item+qtd sem código falso; G/K INCONCLUSIVE. `FALSE_PROMOTED=0`. 44/44 testes.

**Residual:** F/G/K dependem de detecção de réguas horizontais (OpenCV) — a topologia SLANet da metade inferior não alinha bandas às linhas de código. Próximo passo limitado: visual-row detection por separadores. `VAL01_COMPLETED=false`.


## 50. DEC-VAL-040 — Plano de correção estrutural generalizável: grade lógica, colunas funcionais e grupos (2026-11-08)

**Estado:** \`PLANNED\` — plano registrado, **sem código/deploy** neste registro. **Owner funcional:** Engenharia; **implementação candidata:** Engineering API/EVA, respeitando owners e contratos existentes. **Coordination:** Issue #131. **Fronteira ativa:** E1/VAL-01, reconstrução da *tabela de materiais*. E4 (balões/chamadas), E2–E7 e VAL-02 continuam **congelados**; detectar balões ou vinculá-los às vistas **não** está autorizado por este plano. Qualquer mudança de owner, authority, bounded context ou source of truth exige \`ARCHITECTURE_DECISION_REQUIRED\`.

### 50.1 Evidência que altera o plano (consumidor autenticado + inspeção visual)

1. **\`90264017\`, 14 páginas, SHA \`5452aabd3ddf94d5d004fe5c4d27c2daca9fcf8759a0c1b849b415d4769e32ee\`:** job MCP \`aj-8e1513f273cf44ec\` → \`COMPLETED\`, OCR 14/14 \`FULL\`, SLANet página 9: 68 células \`component_table\` e 14 \`title_block\`, sem erro; linhas candidatas **C/6/10081389, D/3/10081685, E/2/10091368** agora possuem campos tipados. Porém \`association_status\` da linha permanece \`INCONCLUSIVE\` e \`description=null\`. Linha 5 contém \`10110676\` sem item/qtd, linha 6 contém F/9 sem código; G/K ainda sem vínculo seguro. **\`M2_CDE_FIELDS=PASS\`; associação completa \`PARTIAL\`, não \`VAL01_COMPLETED\`.**
2. **\`90264004\`, 1 página, SHA \`5b6717dfa7b8dcdc18f81b4657e1dcdf3410b9af42c8cf3109214df2f66719f4\`:** job MCP \`aj-69310253b0f842d4\` → \`COMPLETED\`, OCR 1/1 \`FULL\`, 172 tokens, SLANet 60 células \`component_table\` e 20 \`title_block\`, ambos sem erro, PDF SHA confirmado. Entretanto \`component_table.rows\` não atribui \`item\`, \`quantity\` e \`description\` nas linhas observadas; para A7/A8 o SLANet posiciona código \`10110092\`/\`10110093\` na coluna nativa 4 e descrição \`ETIQUETA ACETATO DE RAYON 1TB1\`/\`1TB2\` na coluna 5, mas a projeção publica **texto de descrição como \`component_code\`**. Logo \`SINGLE_PAGE_OCR=PASS\`, \`SLANET_NATIVE=PASS\`, \`SEMANTIC_COLUMN_ROLE=FAIL\`, \`ROW_FIELD_LINKAGE=FAIL/PARTIAL\`.
3. **Inspeção visual direta do PDF oficial \`90264004\` (revisão humana assistida, ainda \`VISUAL_REVIEW_CANDIDATE\`, não ground truth aprovado pela Engenharia):** tabela com colunas funcionais **Código | Descrição | Item | QTD. | Comp. | Descrição**. Candidatos A1/1/\`10110081\`, A2/1/\`10110082\`, A3/1/\`10110083\`, A4/1/\`10110087\`, A5/1/\`10110088\`, A6/1/\`10110091\`, A7/1/\`10110092\`, A8/1/\`10110093\`, com descrições correspondentes de etiquetas. Dois grupos de subconjunto visualmente distintos: \`50225478\` com A9/2/\`10080065\` e AA/2/\`10400035\`; \`50225479\` com A9/6/\`10080065\` e AA/6/\`10400035\`. **Mesmo item/código não implica mesma ocorrência ou quantidade**; preservar identidade de grupo, página e posição. Não converter automaticamente essa interpretação em relação oficial da BOM.
4. **Lição dos commits \`84b87d636b\` e \`0a6d468f07\`:** testes sintéticos e segmentação por \`rowspan\` isoladamente não asseguram o comportamento real. O PDF \`90264017\` mostrou células com \`rowspan=1\` contendo duas linhas visuais; a correção quad/Y recuperou C/D/E, mas **não resolveu papéis de colunas, descrições, hierarquia ou F/G/K**. O novo pacote deve atacar a classe de defeitos e não um produto.

### 50.2 Objetivo e fronteiras de contrato

**RQ-VAL-040:** reconstruir uma **grade lógica candidata** de tabelas técnicas a partir de região visual, divisórias/linhas horizontais, quadriláteros OCR, células nativas, cabeçalhos e alinhamento, preservando células mescladas legítimas. **RQ-VAL-041:** determinar **papéis funcionais de coluna** (identificador de grupo, descrição de grupo, item, quantidade, código de componente, descrição de componente, desconhecido) sem identificar campo apenas por índice fixo de coluna nativa. **RQ-VAL-042:** vincular \`item × quantity × component_code × description × parent_group\` à mesma **ocorrência física**, mantendo provenance (PDF SHA, revisão quando disponível, página, região, células, tokens, polígonos, método, conflitos); ambiguidades → \`INCONCLUSIVE\`. **RQ-VAL-043:** validar generalização, compatibilidade e permission boundaries no pipeline integrado e no MCP autenticado.

Não criar nova source of truth, banco, serviço ou MFE; não fazer import entre bounded contexts; não ler banco de outro owner. O resultado é **DRAFT/CANDIDATE**, nunca aprovação de estrutura, alteração oficial, finding técnico conclusivo ou NC. Comparação com BOM só via Domain API oficial autorizada, com regras de inclusão de níveis, quantidade, revisão e efetividade definidas pelo owner. Se não houver essas regras, retornar \`NOT_COMPARABLE/INCONCLUSIVE\`.

### 50.3 Pacotes bounded, gates e ordem de execução

| Pacote | Entrega verificável | Gate para prosseguir |
|---|---|---|
| **P0 — Reancoragem/GT** | Ler authorities e contratos, HEAD/status/owners; conferir PDF/SHA/revisão; criar fixtures **reais** de entradas OCR+SLANet de \`90264004\` e \`90264017\` e anotações visuais revisáveis com grupo/linha/coluna | Fixture reproduz falha da baseline (\`FAIL\` antes do fix); owner valida GT ou limita escopo explicitamente |
| **P1 — Grade geométrica** | Separadores horizontais e verticais onde confiáveis, bandas Y, polígonos, alocação de tokens, células mescladas e linhas multilinha; independência de \`rowspan\` quando necessário | Corrige C/D/E, não introduz split falso em \`rowspan\` legítimo; F/G/K resolvidos **somente quando evidência sustenta** |
| **P2 — Papéis funcionais** | Header/layout + consistência semântica de coluna e linha; detectar deslocamentos nativos A7/A8; códigos numéricos não confundidos com descrições | A7/A8 \`10110092/10110093\` no campo código e texto das etiquetas no campo descrição; teste negativo para descrição como código |
| **P3 — Grupos/ocorrências** | Identificar limites das células de grupo e relações locais candidato pai→linha; preservar identidade da ocorrência e multiplicidade | A9/AA sob \`50225478\` (2/2) distintos de A9/AA sob \`50225479\` (6/6), sem flattening por código; sem promoção de pai oficial |
| **P4 — Integração e regressão** | Testes com fixtures reais (baseline red→green), integração com PDFs originais, contratos MCP, AuthZ negativa, execução dos 13 PDFs do Doc120 com holdouts separados, recursos e resultados por layout | \`FALSE_PROMOTED_ASSOCIATIONS=0\` nos casos avaliados; GT aprovado com campos corretos, nenhuma regressão crítica; \`TEST_NOT_RUN\` não é PASS |
| **P5 — Deploy governado e aceite** | Menor diff, testes no SHA, residual search, commit/push, rollback pronto e deploy canônico **somente com gates críticos PASS**; jobs MCP autenticados de \`90264004\` e \`90264017\` no runtime implantado | OCR 1/1 e 14/14 \`FULL\`, SLANet funcional, papéis/descrições/grupos conferidos na saída, nenhum falso vínculo, documento/SHA preservados |

**Regras dos gates:** (a) nunca ganhar 100% de cobertura promovendo evidência ambígua; (b) descrições podem ser multilinha, campos de cabeçalho podem atravessar linhas; (c) código pode ocorrer em diferentes grupos e quantidades; (d) detectar deslocamento semântico de coluna mesmo quando o SLANet altera o índice; (e) critérios quantitativos só com ground truth aprovado, separando precisão/recall e cobertura; (f) nenhum novo deploy apenas com teste sintético ou célula nativa >0; (g) se P4 falhar ou faltar corpus/segurança, **bloquear deploy** e registrar residual.

### 50.4 Gestão de escopo, dependências e evidências

**E1/VAL-01 permanece a única frente ativa**. Identificação/ligação de balões (E4/M3/M4) permanece congelada, apesar de ser uma dependência futura da tabela confiável; **não** iniciar detector nesta etapa. E2–E7 e VAL-02 seguem congelados. Não inferir quantidade por contagem de balões. A ordem para E4 somente poderá mudar mediante decisão explícita da Coordination/owner registrada no GitHub, sem mudança silenciosa do roadmap.

**Saídas auditáveis:** baseline SHA, fixture origin/SHA/versão do motor, ground truth visual com reviewer e limites, matriz por linha/coluna/grupo, testes e falhas negativas, contadores de ambiguidades e falsos vínculos, resultados de corpus/holdouts, AuthZ, contrato/compatibilidade, SHA de deploy, jobs pós-deploy, rollback. Estados: \`PROVEN | TO_INVENTORY | PLANNED | TARGET\` e \`PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE\`. Não transformar \`EVAL_PENDING\` ou \`COMPLETED\` em aprovação técnica. \`ENGINEERING_APPROVAL=NOT_APPROVED\`; \`VAL01_COMPLETED=false\`.

**Referências de evidência:** Issue #131 comentários \`6727567112\` (retorno terminal 14p), \`6727591666\` (teste 1p), \`6727617764\` (inspeção visual 1p), Doc120 (corpus). Próximo passo executável: **P0 (reprodução/ground truth e contrato), sem implementar balões ou publicar BOM**.

## 50. DEC-VAL-040 — Reconstrução lógica de tabelas (papéis por célula, splits, grupos) (2026-11-08)

**TASK_ID:** `EVA-VAL01-DEC040-LOGICAL-TABLE-RECONSTRUCTION-E2E`. **Commit:** `862b12ce34`. **Deploy:** imagem `sha256:d2408fdf149c…`, `delpi-engineering-api` healthy. `VAL01_COMPLETED=false`.

**Causas-raiz (PROVEN em fixtures reais dos dois PDFs):** (a) tipagem por índice de coluna — SLANet desloca papéis entre linhas → descrição publicada como `component_code` (90264004 A7/A8); (b) formas canônicas fundidas não resolvidas (`A6 1`, `2 10080065`); (c) células-âncora de grupo disputavam campos; (d) padrão de item aceitava palavras (`CABO`,`CAPA`); (e) `_split_text` fallback devolvia texto completo quando bandas migravam.

**Correção (application layer, genérica):** papel por célula (conteúdo vence índice), banda-X só vetando `item`; splits `ITEM QTD`/`QTD CÓDIGO`/`CÓDIGO+desc`/`ITEM resto`; âncoras de grupo excluídas dos campos e herdadas como `parent_group_candidate`; `token_centers` como âncora visual de linha; banda migra só com evidência próxima.

**Prova integrada real (container prod):** 90264004 — A2–A8 item/qtd/código/descrição corretos; zero descrição→código; A9/AA por grupo (50225478/79). 90264017 — C/D/E preservados, descrições agora vinculadas, F/G/K INCONCLUSIVE sem promoção falsa. Residuais: A1 código e A5 item não resolvidos (evidência insuficiente), F/G/K, regressão 13 PDFs e job MCP pós-deploy `TEST_NOT_RUN` (consumidor).

## 51. DEC-VAL-040 — Integridade das associações (2026-11-09)

**TASK_ID:** `EVA-VAL01-DEC040-ASSOCIATION-INTEGRITY-REMEDIATION-E2E`. **Baseline de código:** `862b12ce34` ainda é a última alteração commitada de `rows_from_native_cells` no início desta execução. **HEAD de trabalho ao iniciar:** `f1f4767b30` (main = origin/main). **Deploy desta correção:** não realizado. `VAL01_COMPLETED=false`. `ENGINEERING_APPROVAL=NOT_APPROVED`. `BOM_RELATION_PROVEN=false`.

**Evidência que reabre o pacote (comentário 6727992363, jobs pós-deploy de `862b12ce34`):**
- `90264004` job `aj-1d52deaaabc7446d`: A2 publicado com `description=CHICOTE DE LIGACAO` (descrição do conjunto). A5 sem item. A9 sob `50225478` sem código. A7/A8 corretos.
- `90264017` job `aj-8f671a3ee1094d3e`: tupla `G/9/10110676` com token de G em Y≈200.5 e quantidade/código em Y≈180.5. C/D/E preservados. `association_status=INCONCLUSIVE` não impedia a tupla composta.

**Causa-raiz (PROVEN na projeção, fixtures com a geometria desses jobs):**
1. **G/9.** A faixa Y usada para redistribuir `line_texts` vinha do polígono SLANet. Caixa alta contém bandas cujo token está em outro Y. O cabeçalho entrava no passo entre linhas e inflava o limite, então `G 3`/`K 2` permaneciam no índice da quantidade 9. `_ITEM_TAIL` extraía só o item e a quantidade/código vizinhos completavam a tupla. `INCONCLUSIVE` não desfazia os campos.
2. **A2.** Célula `rowspan` de descrição do conjunto (`CHICOTE DE LIGACAO`), à esquerda da coluna de item, era o primeiro texto longo da linha. `_put` guardava o primeiro valor e a etiqueta do componente não substituía.

**Correção (mesmo `rows_from_native_cells`, sem pipeline novo):** faixa Y pelo centro dos tokens; linhas canônicas `ITEM QTD` distantes da banda viram ocorrência própria; descrição de grupo (âncora ou texto à esquerda do item / rowspan à esquerda do cluster de descrições) não preenche descrição de componente; campos de bandas incompatíveis saem da tupla para `conflicting_fields` com `association_conflict`; órfão com um único destino compatível é reancorado. Investigação trata `association_conflict` como linha ambígua. Mapper registra `geometric_band_conflict`. Conteúdo continua vencendo índice de coluna (A7).

**Prova local:** `tests/test_association_integrity_dec040.py` mais `test_table_perception_native.py`, `test_slanet_document_integrity.py`, `test_drawing_investigation_r12.py` (77) e `test_drawing_object_profiles_r11_1.py` (16). Na fixture da página 9: E/2/10091368, F/9/10110676, G/3/10110679, K/2/10130020 quando o código está na mesma banda; nenhuma tupla G/9/10110676. A2 fica com `ETIQUETA ACETATO DE RAYON T2/V1`. A5 acompanha o token quando ele existe. A9 de `50225478` não herda o código de `50225479`.

**Residuais e bloqueio de deploy:** o PDF oficial não está neste workspace; corpus dos 13 desenhos, holdout, integração no motor SLANet/OCR e job MCP autenticado ficam `TEST_NOT_RUN`. A1 continua sem código quando a célula não traz o token — não se inventa `10110081`. Código de A9 sob `50225478` só entra se a célula existir; ausência não copia o outro grupo. Sem esses gates, **não houve deploy**.

## 52. DEC-VAL-040 — Deploy produtivo e validação de runtime (2026-11-09)

**TASK_ID:** `EVA-VAL01-DEC040-PRODUCTION-DEPLOY-AND-MCP-VALIDATION`. Esta seção não substitui a §51. `ENGINEERING_APPROVAL=NOT_APPROVED`. `VAL01_COMPLETED=false`. `BOM_RELATION_PROVEN=false`.

**Regra permanente da VAL-01:** correção destinada à produção inclui, na mesma entrega, testes pré-deploy, deploy canônico e validação no runtime produtivo pelo consumidor autorizado. Commit sem deploy é entrega parcial. Deploy sem validação funcional permanece pendente de aceite. A regra não autoriza deploy que falhe em segurança, contrato, integridade ou regressão crítica, nem automação que publique qualquer commit.

**Código e runtime:**
- Commit da correção: `adceb6b5fa67cbe2cf23fcbbfe47162ac28e831e`.
- Git implantado: `0e452c20dc68b84280f673d6f92c4dea8597b705` (contém o commit da correção). Os commits entre os dois SHAs são o cadastro D15. Commits posteriores no `main`, até a conferência `dc491abd1e`, não alteram `engineering_app/application/drawing/`.
- Imagem: `sha256:1fded63c13df79d06009f6a28f6161c0aa2ad28ffd793f32f72b22e857f79bef`. Container `delpi-engineering-api` criado em `2026-11-09T12:07:28Z`, health `healthy`, `GET /health` → `{"status":"online","service":"engineering-api"}`. O arquivo em execução contém `association_conflict`.
- Rollback preservado e não utilizado: tag `infra-engineering-api:pre-dec040-adceb6b5-rollback` = `sha256:d2408fdf149c53843fc4fe458af6ebb4b590f9170a1713978e359e756a071dd7`.
- Procedimento: `git pull --ff-only` e `./infra/scripts/up-prod-sequential.sh --build engineering-api` em `srv-api`. Sem `docker cp` e sem edição no container.

**Acesso aos PDFs:** os arquivos oficiais estão em `/mnt/fileserver/desenhos`, o volume read-only que a API já monta. SHA conferido no arquivo. A execução foi um container descartável da imagem de engenharia, teto 5 GiB, modelos em `/opt/ocr-models:ro`. Nenhum PDF foi copiado para o Git. `GET /v1/products/90264004/drawing/pdf` e `POST /mcp` sem identidade retornam `401`.

**Integração `90264004`** (SHA `5b6717df…19f4`, OCR FULL 1/1, 172 tokens, SLANet 60 células de tabela + 20 de carimbo). Repetida na imagem implantada, sem bind do código:
- A2 = `10110082` / `ETIQUETA ACETATO DE RAYON T2/V1`. `CHICOTE DE LIGACAO` não virou descrição de item.
- A7 `10110092` e A8 `10110093` preservados, com descrição de etiqueta.
- A5 = `10110088`, quantidade 1. A1 = `10110081` porque a célula existia.
- `50225478`: quantidade 2 / `10080065` e AA quantidade 2 / `10400035`. `50225479`: quantidade 6 / `10080065` e AA quantidade 6 / `10400035`.
- Residual: o item `A9` não foi publicado. Não há token limpo `A9`; no segundo grupo a célula ambígua mistura `A9` com outro texto. A5–A8 ficam `INCONCLUSIVE` porque o SLANet marcou a célula de origem como ambígua, embora os quatro campos estejam `FIELD_IDENTIFIED` e corretos.

**Integração `90264017`** (SHA `5452aabd…32ee`, OCR FULL 14/14, 1852 tokens). Página 9: C/6/`10081389`, D/3/`10081685`, E/2/`10091368`, F/9/`10110676`, G/3/`10110679`, K/2/`10130020`. A tupla G/9/`10110676` não aparece. Conflitos de banda ficam em `conflicting_fields` com `association_conflict`. Página 11 com `structure_consistent=false` não substitui a grade nativa. `FALSE_PROMOTED_ASSOCIATIONS=0` para a classe G/9 e para descrição de conjunto em item.

**Corpus, contrato, segurança e recurso:** bateria dos 13 PDFs na Doc 120 deste mesmo dia. Pytest local: 93 passed (`test_association_integrity_dec040.py`, `test_table_perception_native.py`, `test_slanet_document_integrity.py`, `test_drawing_investigation_r12.py`, `test_drawing_object_profiles_r11_1.py`). Os 11 desenhos fora de `90264004`/`90264017` não ajustaram a regra. Precisão de campo sem ground truth aprovado pela Engenharia: não declarada. Container único, sequencial, teto 5 GiB, conclusão 0; o serviço produtivo permaneceu no ar.

**MCP consumidor:** `CONSUMER_MCP_ACCEPTANCE=PENDING`. Este executor não tem sessão MCP autenticada nem token de usuário. Não houve job novo e a identidade não foi simulada. O aceite funcional completo continua pendente de verificação independente em `product.drawing_understanding` para `90264004` e `90264017`.


## 53. DEC-VAL-040 — Handoff Coordination: variação visual, linhas A9/AA e próximo diagnóstico (2026-11-09)

**Estado deste registro:** continuidade arquitetural e de avaliação, **não** implementação, não deploy e não aprovação. **Chat recomendado:** `EVA — Architecture / Coordination` (arquivo `03_EVA_Chats_Especialistas_e_Prompts.md`). **Fonte executável única:** Doc 119; evidência/corpus: Doc 120; tracker: Issue #131. **Frente ativa:** E1/VAL-01. E2–E7 (incluindo balões/E4) congeladas. Não abrir documentos ou planos paralelos.

### 53.1 Última evidência independente do consumidor (confirmada em 2026-11-09)

- Código de correção publicado: `adceb6b5fa67cbe2cf23fcbbfe47162ac28e831e`. Deploy reportado pelo executor: `0e452c20dc68b84280f673d6f92c4dea8597b705`, imagem `sha256:1fded63c13df79d06009f6a28f6161c0aa2ad28ffd793f32f72b22e857f79bef`, serviço healthy. **O MCP comprovou comportamento funcional, mas não expôs SHA/digest do host diretamente.** Reconfirmar HEAD e runtime no início de nova execução.
- `90264004`, PDF oficial SHA `5b6717dfa7b8dcdc18f81b4657e1dcdf3410b9af42c8cf3109214df2f66719f4`, 1 página, job MCP autenticado `aj-c47df5e5efdb445a`: `COMPLETED`, OCR FULL 1/1, 172 tokens, SLANet 60 células `component_table` + 20 `title_block`. A1–A8 com item, quantidade, código e descrição do componente correspondentes à referência visual; A2 recebeu `ETIQUETA ACETATO DE RAYON T2/V1`, **não** a descrição de grupo `CHICOTE DE LIGACAO`. A5–A8 podem continuar `INCONCLUSIVE` por ambiguidade nativa mesmo com campos preenchidos. Nos subconjuntos `50225478` e `50225479`, o código `10080065` e as quantidades 2 e 6 foram associados como candidatos sob os grupos corretos, mas **o campo `item=A9` não foi publicado**; AA/2 e AA/6 com `10400035` foram preservados. Não preencher A9 artificialmente.
- `90264017`, PDF oficial SHA `5452aabd3ddf94d5d004fe5c4d27c2daca9fcf8759a0c1b849b415d4769e32ee`, 14 páginas, job MCP autenticado `aj-a9bb85a0a4ea4e12`: `COMPLETED`, OCR FULL 14/14, 1852 tokens, SLANet página 9: 68 células `component_table` + 14 `title_block`. C/6/`10081389`, D/3/`10081685`, E/2/`10091368`, F/9/`10110676`, G/3/`10110679` e K/2/`10130020` com descrições; a falsa tupla G/9/`10110676` não foi publicada. A linha B apresentou `association_conflict=true`, com código de grupo `70260008` retido em `conflicting_fields`, sem substituição do componente. `quality_gate=EVAL_PENDING`; nenhuma aprovação técnica.
- Corpus de 13 PDFs: executor reportou FULL OCR 13/13 documentos no código `adceb6b5fa` e ausência das duas classes conhecidas de falso vínculo; precisão geral de campo/associações **não foi comprovada**, por falta de ground truth aprovado. Não confundir com a execução independente do ChatGPT, que examinou dois PDFs por MCP.

### 53.2 Nova inspeção visual fornecida pelo usuário: organização de tabela do `90264004`

**Fonte da observação:** captura visual da tabela enviada pelo usuário em 2026-11-09. Evidência visual **CANDIDATE**, não ground truth oficialmente aprovado e não reprodução instrumentada do modelo. A imagem foi inspecionada nesta conversa; o binário proprietário **não** é incorporado ao Git. Referenciar por descrição e pelo SHA do PDF oficial.

**Cabeçalho da tabela:** `Código | Descrição | Item | QTD. | Comp. | Descrição`. Organização visual:
1. **Bloco superior, texto azul:** grupo `90264004` / descrição `CHICOTE DE LIGACAO` ocupa colunas de grupo em célula verticalmente mesclada sobre oito linhas **A1–A8**. Cada linha tem item, quantidade 1, código de componente e descrição própria; linhas horizontais individuais.
2. **Primeiro bloco inferior, texto de componente vermelho:** grupo `50225478` / `CF20AZUL-00290/10/05-0000-6500`, célula de grupo sobre duas linhas: **A9 / 2 / 10080065 / TERM. PINO 2,17 20-14AWG ESTANHADO MACHO UL** e **AA / 2 / 10400035 / CABO SIL 200°C 20AWG AL 600V STYLE 3135**. Código/descrição do grupo permanecem azuis, seus componentes vermelhos.
3. **Segundo bloco inferior, também vermelho nos componentes:** grupo `50225479` / `CF20AZUL-00240/10/05-0000-6500`, célula de grupo sobre duas linhas: **A9 / 6 / 10080065** e **AA / 6 / 10400035**, com descrições correspondentes. Linhas horizontais delimitam cada ocorrência.
4. A separação não depende do item ser único: **A9 e AA aparecem duas vezes em grupos distintos**. A cor coincide com uma **mudança de seção / representação visual**; não se sabe se é fator causal do OCR. A geometria das células de grupo e os separadores horizontais também mudam. Não atribuir causalidade à cor por inspeção isolada.

**Desvio factual a investigar:** na saída MCP mais recente, a EVA publicou os códigos e quantidades dos dois A9, mas **não o identificador textual A9**, apesar de o rótulo estar visível no desenho fornecido. `VISUAL_A9_PRESENT=PROVEN` somente para a captura; `OCR_A9_TOKEN_PRESENT=TO_INVENTORY`; `NATIVE_CELL_A9_ASSOCIATION=TO_INVENTORY`; `ROOT_CAUSE_COLOR=INCONCLUSIVE`; `ROOT_CAUSE_TOPOLOGY=INCONCLUSIVE`.

### 53.3 Próximo bounded step — investigação comparativa, sem heurísticas por layout

**TASK_ID candidato:** `EVA-VAL01-DEC040-A9-VISUAL-VARIATION-ROOT-CAUSE` (`PLANNED`; nenhuma implementação autorizada por este registro). **Não iniciar por regex, limiar de cor, produto ou item.**

1. Reancorar Git `origin/main`, status, autoridades e SHA/digest produtivos; ler Docs 116/119/120 e Issue #131. Obter o **mesmo PDF oficial por acesso autorizado**, verificar SHA e renderizar a única página, preferencialmente com referência rastreável de recorte/dimensões.
2. Inspecionar os artefatos **em cada fronteira**: PDFium (texto vetorial, se existir, e raster), PaddleOCR (tokens, cor da imagem de entrada, scores, quadriláteros/centros Y), SLANet (células, polígonos, row/col/span e associação token→célula), `rows_from_native_cells`, `understanding` e projeção publicada pelo MCP. Para cada **A9 inferior**, verificar literalmente onde o símbolo deixa de existir ou de estar vinculado, comparando com AA, A8 e A1 como controles.
3. Isolar hipóteses, com **mesma página, recorte, DPI, pesos e SHA**: (H1) mudança de cor/contraste vermelho×azul afeta OCR; (H2) mescla `rowspan` dos grupos muda a topologia; (H3) distância vertical/horizontal e separadores fazem token A9 conflitar com linha adjacente; (H4) OCR reconhece A9, mas adapter/associação/candidato `ITEM` descarta ou marca como ambíguo. Teste controlado comparando original colorido, grayscale e normalização de contraste **somente como experimento**; não mudar produção por uma única melhora, nem usar threshold dependente de cor/código. Se PDF tiver texto vetorial, comparar extração vetorial para localizar a perda sem substituir pipeline sem gate.
4. Usar **capacidades dos frameworks existentes** primeiro (PDFium, PaddleOCR, SLANet; OpenCV somente se já disponível e comprovadamente necessário); avaliar variantes de pré-processamento apenas com conjunto de regressão colorido/P&B. Não desenvolver segundo OCR, segundo parser, novo microserviço, novos stores nem regex de caso.
5. Capturar fixture real red→green com tokens/células e geometria dos dois A9, dos dois AA e linhas superiores; provar a primeira fronteira defeituosa **antes** de alterar código. Se correção necessária: aplicar menor diff no adapter/Application dono, preservar contratos e `conflicting_fields`/fail-closed, impedir vinculação entre grupos.
6. Testes de A9/AA **com dois grupos e quantidades distintas**, A1–A8, `90264017` p9 C–K, casos negativos de multilinha/cores/mesclas; corpus **13 PDFs Doc 120**, holdouts, segurança/AuthZ, recursos e integração com PDFs oficiais, sem ajustar especificamente aos holdouts. Métrica final inclui token recall de A9, alinhamento item/linha/grupo, false promotions e número de inconclusivos; precisão só com GT aprovado.
7. Para cada correção destinada à produção, o ciclo inclui **deploy canônico, SHA/digest/rollback e teste MCP autenticado pós-deploy**. **Nunca contornar gates críticos**: se não passam, `DEPLOY_BLOCKED` e task não concluída, com evidência. Não confundir commit, `healthy`, `COMPLETED` ou campos preenchidos com aprovação técnica.
8. Atualizar **este Doc 119** (plano único), Doc 120 (corpus/evidência) e Issue #131; não criar documentação paralela.

**Owner e invariantes:** Keycloak identidade; Core RBAC/governança; Domain APIs verdade oficial; Portal Engenharia experiência; EVA interpretação candidata; owner de Engenharia aprovação. `structure_validation.v1` e percepção são `DRAFT/CANDIDATE`; `engineering_approval=NOT_APPROVED`, `automatic_nc=false`, `VAL01_COMPLETED=false`. Regras oficiais de quantidade/unidade, revisão/efetividade, ground truth e critérios de aceite continuam owner-blocked quando não validadas. E2–E7/E4 balões e VAL-02 congeladas; não iniciar em paralelo.

### 53.4 Handoff obrigatório para o próximo chat

**CHAT_RECOMMENDATION:** `EVA — Architecture / Coordination`. **FIRST ACTION:** ler `01_EVA_Instrucoes_do_Projeto.md`, `02_EVA_Instrucoes_Gerais_Portal_Engenharia.md`, `03_EVA_Chats_Especialistas_e_Prompts.md`; verificar HEAD remoto/working tree e Doc 119 §53, Doc 120 último log, Issue #131. Reconciliar fatos x histórico do chat, e selecionar **um** próximo bounded step. Não reabrir DEC-VAL-034, RES-01/02/03, auditoria framework-first concluída ou inventário do corpus sem regressão observada.

**Veredicto de handoff:** `ACCEPT_WITH_RESIDUAL` para correção focal de associação em MCP; `INCONCLUSIVE` para causa dos A9 vermelho/mescla; `ENGINEERING_APPROVAL=NOT_APPROVED`; `VAL01_COMPLETED=false`.

## 54. DEC-VAL-040 — A9 em célula agregada com descrição de grupo (2026-11-09)

**TASK_ID:** `EVA-VAL01-DEC040-A9-VISUAL-VARIATION-ROOT-CAUSE`. `ENGINEERING_APPROVAL=NOT_APPROVED`. `VAL01_COMPLETED=false`. `BOM_RELATION_PROVEN=false`.

**Primeira fronteira defeituosa (PROVEN):** `rows_from_native_cells` em `understanding.py`. O token OCR `A9` e a célula nativa existem (comentário 6740121902: texto `A9 CF20AZUL-…`, centros A9≈X480 / descrição≈X295). `_cell_role` classifica a agregação como `description`. Com ≥4 amostras de item (A1–A8), `_role_band` forma a banda-X; o centro médio da célula fica à esquerda → `_is_group_description_context=true` → `continue` antes de `_ITEM_TAIL_RE`. Quantidade e código das outras células publicavam; `item` ficava `null`. AA em célula limpa não passava por esse caminho. Cor vermelha isolada: não causal (AA vermelho recuperado).

**Correção (mesmo módulo):** extrair `_ITEM_QTY_RE` / `_ITEM_TAIL_RE` **antes** do `continue` de contexto de grupo; ancorar `source_cy` do item no token da banda-X de item (ou preservar `_band_cy` de split). A cauda `CF20AZUL-…` não vira descrição de componente. Sem hardcode de produto/item/cor.

**Prova:** fixtures red→green em `test_association_integrity_dec040.py`; negativo sem prefixo A9 não inventa item; PDF oficial `90264004` SHA `5b6717df…19f4`: A9/2/`10080065` sob `50225478` e A9/6/`10080065` sob `50225479`; A2 sem `CHICOTE`; A1–A8 e AA preservados. `90264017` SHA `5452aabd…32ee` OCR 14/14: C/D/E/F/G/K com códigos; `false_g9=0`. Corpus 13/13 SHA match, `false_g9=0`, `chicote_on_item=0` (Doc 120). Auth PDF/MCP: 29 testes. Residual: A5–A8 podem permanecer `INCONCLUSIVE` por `ambiguous` nativo; holdouts sem GT de precisão.
