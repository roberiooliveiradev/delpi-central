# 119 — EVA | Catálogo Mestre de Validações de Desenhos e Priorização por Não Conformidades

**Status:** PLANNED — plano funcional evolutivo, não aprovação de regras nem de qualidade.  
**Data-base:** 2026-11-03.  
**Owner do plano:** Portal Engenharia / Coordination; **autoridade técnica:** owners de Engenharia.  
**Source of truth:** Domain APIs de Engenharia; registros de NC lidos via EVA, nunca copiados como fonte oficial.  
**Vinculação:** [Doc 116](116-eva-engineering-drawing-intelligence-master-delivery-plan.md) (M0–M5, evidência/GT/thresholds) e [Doc 118](118-eva-drawing-intelligence-r11-reusable-object-profiles.md) (surface R11–M5).  
**Natureza:** SOMENTE documentação e backlog de validações; não muda código, RBAC, contratos de autoridade nem publica desenho.

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
| E0 | Catálogo, NC, regras, escopo por família, corpus e rastreabilidade | Documento no GitHub + decisão owner sobre corpus/contratos | Coordination / Engenharia | PLANNED (este documento) |
| **E1** | **VAL-01 Estrutura** | 10 AC VAL-01 comprovados por testes, GT, E2E e owner | Engineering API + Engenharia | PLANNED |
| E2 | VAL-02/05 Carimbo, revisão, documentos | checks aplicáveis, contratos oficiais e GT | Engineering API / owner documental | PLANNED |
| E3 | VAL-03 Cotas | atribuição geométrica, tolerância/units, regras e GT | Engenharia | PLANNED |
| E4 | VAL-04 Balões | cadeia item-balão-geometria rastreável, GT | Engenharia | PLANNED |
| E5 | VAL-06/07/13 Notas, material, cliente×DELPI | contratos e GT por família | Domain owners / Engenharia | PLANNED |
| E6 | VAL-08–11 Vistas/símbolos/processos/inspeção | catálogo suportado e fontes autorizadas | Engineering owners | PLANNED |
| E7 | Consolidação por desenho | checks obrigatórios completos, decisão de revisão humana | Portal Engenharia + Engenharia | PLANNED |

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
