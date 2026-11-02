# 150 — Plano único de auditoria e correção integral do Portal Controladoria & Finanças

**Data-base:** 2026-11-02 · **Processo:** PROC-0072 · **Estado:** BACKLOG DE EVIDÊNCIAS + PLANO DE EXECUÇÃO · **Autoridade:** instruções oficiais > .cursor > ADR/contratos > HEAD > testes > docs.
**Objetivo:** inventariar, reproduzir, corrigir e verificar **todas as páginas e estados** do Portal numa execução coordenada, sem redesign de arquitetura nem duplicação de produtores. Este documento é o **registro central** de achados e verificações; não substitui os contratos nem a matriz canônica R01–R15.

## 0. Fontes e critérios de honestidade
- Evidência inicial: **13 capturas de tela fornecidas pelo PO** em 2026-11-02, sessão autenticada em `minhadelpi.com.br/apps/controllership-finance/closing/monthly-closing/2026-09`, incluindo `?tab=documents`, `?tab=reports` e deep route `/reports/production-order-consumption`. As imagens são anexos de conversa; **não estão neste commit**. Executor deve obter/registrar evidência durável sanitizada e adicionar links em cada item.
- Evidência independente prévia da CLARA (mesmo dia): R04 `read(report.production_order_consumption)` filial 01: **1.243 OPs**, filial 02: **2.892 OPs** (2026-09, `dateType=emission`); R06 `read(report.stock_kardex)` filial 02: **27.709 movimentos**; R07 `read(report.inventory_adjustments)` filial 02: **47 movimentos**. Esses dados **não provam** a renderização do MFE.
- Arquivo `Invent.xlsb` histórico: 45 movimentos efetivos mencionados nas fichas; R07 runtime retornou 47. Duas linhas runtime aparecem no armazém 50; a emissão histórica é descrita para locais 01+99. **Hipótese de diferença de universo**, ainda requer match por identidade/quantidade/valor e filtros; sem alterar SQL por coincidência.
- Status dos achados: `OBSERVED_SCREENSHOT` (observado na captura), `REPRODUCED` (com teste rastreável), `TO_VERIFY`, `RESOLVED_VERIFIED`; evidência técnica: `PROVEN | TO_INVENTORY | PLANNED | TARGET`; resultados `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`.
- URL ou screenshot prova **apresentação naquele instante**, não causa, permanência do erro ou cobertura de outra filial. Não registrar `PASS` com somente build/HTTP 200.

## 1. Achados iniciais por captura — reproduzir e corrigir sem inventar causa

| ID | Pri | Página/trecho | Observação comprovável nas capturas | Investigação/ação e critério de aceite | Estado |
|---|---|---|---|---|---|
| CF-UX-001 | P0 | R04 Consumo por OP | Lista diz **1.243 OPs** filial 01, mas células de **OP/produto/data/centro** mostram travessões e **status N** visível. A CLARA retornou `production_order`, `product_code`, `product_description`, `emission_date` para essa filial. | Comparar raw BFF, mapper `productionOrderConsumptionApi`, tipos, `ProductionOrderConsumptionPage`, formatação e fallback. Renderizar OP, produto e datas do contrato sem perder valores; centro não existente deve ser ausência honesta, não inventado. Testar lista + detalhe da **mesma OP real**. | OBSERVED_SCREENSHOT |
| CF-UX-002 | P0 | R04 filtro | Label **Busca OP/produto** e placeholder/campo visualmente sobrepostos em desktop. | Reproduzir em viewport da captura e mobile, corrigir composição/reflow no padrão `@delpi/plugin-ui`; sem sobreposição, labels associados, foco/teclado. | OBSERVED_SCREENSHOT |
| CF-UX-003 | P1 | R04 tabela | Grande área tabular com muitas células vazias; paginação disponível, mas conteúdo informativo insuficiente. | Depois do fix de mapeamento, revisar densidade e colunas úteis por contrato; estados de ausência claros; responsividade/overflow e acesso ao detalhe. Não ocultar dados por CSS. | OBSERVED_SCREENSHOT |
| CF-UX-004 | P1 | Cartões de relatórios | R04/R06/R07 aparecem **Não verificado**, embora CLARA tenha leitura real positiva; R05/R08 passam a **Disponível** em capturas posteriores. | Auditar contrato de `availability`/freshness vs `officialParity`/reconciliação. Exibir conceitos distintos: disponibilidade operacional, erro, paridade oficial pendente. Não transformar consulta CLARA em homologação visual automática. | OBSERVED_SCREENSHOT |
| CF-UX-005 | P0 | Matriz R01–R15 | Linha **R04** ainda diz fonte/owner não confirmados, captura manual, sem contrato; contradiz produtor e integração operacional R04. | Identificar owner do conteúdo do catálogo/matriz, atualizar **por contrato e HEAD**, com R04 `operational_view`, api-delpi consumption-audit e paridade MATR860 pendente. Confrontar tela e backend. | OBSERVED_SCREENSHOT |
| CF-UX-006 | P0 | Matriz R01–R15 | Linha **R09** ainda afirma fonte/owner não confirmados, captura manual/contrato pendente, apesar de implementação operacional R09/CLARA real documentada. | Reconciliar R09 com ficha/ledger/HEAD, distinguir implementação operacional de custo `source_missing` e paridade oficial pendente; atualizar matriz sem promover a oficial. | OBSERVED_SCREENSHOT |
| CF-UX-007 | P1 | Matriz R01–R15 | Colunas `Itens`/`Validados` mostram travessões para todos, inclusive rotas implementadas; `Consulta=Implementada` e `Cobertura=Pendente` sem explicação visível. | Investigar semântica/owner dos contadores, dados ausentes vs não aplicáveis. Melhorar rótulos/ajuda e estados; nunca preencher números inventados. | OBSERVED_SCREENSHOT |
| CF-UX-008 | P1 | Visão geral setembro/2026 | Alertas **Não foi possível consultar entradas e saídas** e **Não foi possível consultar relatório P7** em capturas; depois R05/P7 constam disponíveis em outras telas. | Reproduzir cenário temporal (loading, cache, erro transitório, origem, stale state, retry, atualização) com network/correlation IDs. Alertas devem refletir estado vigente e distinguir falha transitória de divergência de negócio; sem apagar erro real. | OBSERVED_SCREENSHOT / TO_VERIFY_CAUSE |
| CF-UX-009 | P1 | Relatórios e divergências | Captura mostra `Consultando fontes...` e `Consultando a conciliação analítica...` durante navegação; depois métricas 4 relatórios disponíveis/3 fontes não verificadas. | Medir tempo até settle, deduplicação de requests, stale response, timeout, cancelamento, retries; não classificar loading transitório como travamento sem reprodução temporal. | OBSERVED_SCREENSHOT / TO_VERIFY_CAUSE |
| CF-UX-010 | P1 | Visão geral/documentos | Texto **sem lista de documentos definida** coexistindo com documento adicional `Entradas_e_saidas.pdf` enviado. | Distinguir ausência de checklist obrigatório vs existência de documento adicional; melhorar rótulo para evitar interpretação de ausência total; preservar estado de envio e a governança documental. | OBSERVED_SCREENSHOT |
| CF-UX-011 | P1 | Conciliação P3 | Divergência analítica apresentada **0,00**, enquanto R05/P7/R08 possuem valores e reconciliação formal ainda pendente. | Verificar fórmula/contrato e semântica `composição dos saldos consistente`, não chamar de homologação oficial. Exibir escopo, data-base, origem, limitação e interpretação; testar sem somar universos incompatíveis. | OBSERVED_SCREENSHOT / TO_VERIFY_SEMANTICS |
| CF-UX-012 | P1 | Catálogo de relatórios | Cards R04/R06/R07 presentes, mas sem prova visual de abertura/resultado R06/R07; estados `Não verificado`. | Testar deep route, consulta list/detail/filtros, paginação e status em sessão humana; registrar screenshot por relatório e por estado. Corrigir somente defeitos reais. | TO_VERIFY |
| CF-UX-013 | P1 | P3/R07 dados | R07 47 movimentos runtime vs arquivo histórico 45; dois registros runtime do armazém 50, fora da seleção histórica 01+99 descrita. | Reconciliar com arquivo `Invent.xlsb` e 47 linhas runtime por chave, data, produto, armazém, TES, quantidade/custo; documentar diferença; sem filtro ad hoc para forçar 45. | TO_VERIFY |
| CF-UX-014 | P1 | Navegação/UX geral | Capturas mostram scroll longo e áreas com alta densidade, matriz técnica extensa apresentada ao usuário operacional. | Avaliar hierarquia, navegabilidade, posição de ações, tabela acessível e resumo executivo; manter matriz técnica em disclosure se previsto, sem remover rastreabilidade. Verificar desktop/mobile/teclado. | OBSERVED_SCREENSHOT / TO_VERIFY_IMPACT |
| CF-UX-015 | P1 | Matriz R01–R15 | Inconsistência temporal: R04/R09 figuram como pendentes na matriz mesmo quando R04 aparece no catálogo e consulta 1.243 OPs. | Determinar se matriz tem fonte estática/legada distinta, padronizar leitura de contrato/estado; não criar segundo cadastro de verdade por preferência. | OBSERVED_SCREENSHOT |

## 2. Auditoria integral — inventário page-by-page, não presume defeitos não observados

O executor deve descobrir rotas efetivas via router/manifests/HEAD, percorrer a navegação e **cada deep route**, incluindo estados **loading, empty, erro, sucesso, acesso negado, sem escopo, dados parciais**:

| Área | Páginas/fluxos mínimos | Estado inicial |
|---|---|---|
| Páginas comuns | Início, Visão geral, Sala de interação, Minhas tarefas, Administração, Ajuda, Página do usuário (deep route) | TO_VERIFY |
| Central de Fechamento | Seleção da competência, Cockpit/Visão geral, Documentos e interações, Relatórios e divergências | Capturas parciais |
| Documentos P2/P5 | Lista, busca, estados, upload/download, anexo adicional vs checklist, solicitações/interações, envio à Contabilidade e seus detalhes; não executar writes produtivos sem autorização específica | TO_VERIFY |
| Estoque e conciliação P3 | Conciliação, divergências, cutoff, estados, status e reconciliação analítica, notificações | Capturas parciais |
| Relatórios | R01/R02, R03/P7, R04, R05, R06 Kardex/CPV, R07 Inventários, R08 H02, R09 MOD, R10 centro custo, R11 NF, estados R12/R15 | R04 observado; demais TO_VERIFY |
| Governança | Matriz R01–R15, RQ/AC, fonte/owner/proveniência, help, legendas de disponibilidade vs paridade, auditoria e estados | Capturas parciais |
| Administração | Gestão de checklist/modelos, permissões e operações conforme rotas efetivas | TO_VERIFY |

**Não declarar todas as páginas verificadas** sem matriz de rotas extraída do HEAD e evidência por rota. Toda falha adicional vira ID `CF-UX-016+`, com página, passos, esperado/observado, request id, prioridade, owner, causa comprovada, teste, commit e screenshot antes/depois. Não inventar bugs.

## 3. Regras de execução para Devin

**Pre-flight:** HEAD, `origin/main`, git status/WIP, Project Instructions, instruções oficiais do arquiteto, .cursor aplicável, README, docs 11/113/118/23, `30-plugin-ui-reuse-map.md`, padrão visual; inventariar router/pages e testes. GitHub é authority TARGET, TÉO AS-IS.

**Procedimento por issue:** REPRODUCE (captura + network + console) → TRACE contrato BFF/MFE/produtor → CLASSIFY erro/ausência/limitação/paridade → APPLY MINIMAL DIFF → TEST component/contract/e2e → VERIFY authenticated real Portal + CLARA quando relevante → RECORD owner, RQ/AC, evidence → COMMIT/SHA → próximo. Agrupar correções por componente sem perder IDs.

**Prioridade:** P0 dados renderizados errados R04, matriz R04/R09; P1 UX/filtros/estados, conciliação, demais rotas; P2 apenas polimento de baixo risco. Não alterar SQL/produtor, Keycloak, permissions, arquitetura, regras TOTVS ou estados de homologação sem prova/decisão material.

**Segurança:** Core effective permissions fail-closed `capability AND resource_scope/ownership AND business_rule`; apenas `controllership-finance.access/manage`; MFE → somente BFF; BFF → api-delpi por padrão existente; CLARA → BFF; sem JWT/secret em evidências.

**Visual:** `@delpi/plugin-ui` first, seguir `30-plugin-ui-reuse-map.md`, `docs/11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md`, UX PT-BR, light/dark mesma árvore, desktop/mobile, foco/teclado, Help com o gate. Não duplicar chrome.

## 4. DoD transversal e aceite

- **Uma matriz por rota**: URL/page/component, persona, role/scope, competência/filial, desktop/mobile, light/dark, estados, expected vs observed, screenshots/network, testes, PASS/FAIL.
- **R04**: listar/abrir OP real; código e produto/datas renderizados; filtros sem overlap; mesma OP/valores em CLARA/BFF/Portal; `operational_view` / `pending` visíveis.
- **R06/R07**: páginas reais navegáveis, filtros/linhas/totais; consistentes com CLARA; resolver ou classificar diferença histórica R07 45×47 sem inventar paridade; `pending` oficial preservado.
- **Matriz/catalogo**: R04/R09 e demais linhas reconciliadas com contratos do HEAD, separando implementado, disponível, verificado, paridade/homologação; nenhuma narrativa histórica obsoleta.
- **Visão geral, P2/P3/P5**: alertas não stale, estados não contraditórios, documento adicional vs checklist explícitos, conciliação explicada pelo contrato; sem writes produtivos exploratórios.
- **Regressões**: R01–R15 conforme superfície, CLARA R04/R06/R07/R09, build/typecheck, contratos, segurança pos/neg, acessibilidade; runtime real com usuário autorizado; falhas não executadas `TEST_NOT_RUN`.
- **Entrega**: commits/push, SHA remoto, deploy controlado **somente após gates e testes**, smoke produtivo visual com screenshots, rollback, ledger/fichas/Help atualizados.
- **Classificação final:** `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`. Sem prova da interface autenticada, não declarar aceite visual.

## 5. Controle vivo de execução

| Campo por item | Valor obrigatório |
|---|---|
| ID / prioridade / estado | `CF-UX-NNN` / P0-P2 / OPEN → IN_PROGRESS → FIXED_PENDING_VERIFY → VERIFIED |
| Evidência | Origem, data/hora, screenshot antes/depois, URL, request/correlation ID sanitizado |
| Diagnóstico | Root cause `PROVEN` ou hipótese rotulada |
| Responsável e contrato | Owner, código, producer/consumer, RQ/AC |
| Correção | Arquivos alterados, diff mínimo, testes e regressões |
| Publicação | Commit/SHA, branch/PR, deploy SHA/rollback |
| Aceite | Cenário positivo/negativo, competência, filial, status PASS/FAIL |

**Atualizar este documento no GitHub durante a auditoria e o ciclo de correção; não criar outro plano paralelo.** Itens `TO_VERIFY` viram problemas somente após reprodução. Ao fim entregar quadro aberto/resolvido, evidências verificáveis e resíduos com owner.


## 6. Diretriz do PO — fase de revisão acumulativa, sem implementação (02/11/2026)

**Decisão explícita:** neste momento, o trabalho é **somente revisar todas as páginas e registrar cada observação neste documento**. **Não gerar prompt de execução, não iniciar correções, não realizar deploy, não fracionar o trabalho em pequenos ciclos.** Ao terminar a inspeção integral, consolidar os requisitos e só então preparar um único programa de correção, mediante nova autorização do PO. As descrições abaixo são **intenção de produto/UX registrada**, não contratos técnicos aprovados. Para dados/resumos que necessitem de API, persistência ou semântica nova, registrar `DECISION_REQUIRED` posteriormente, sem antecipar solução.

### CF-UX-016 — Hero compacto e navegação integrada
- **Prioridade:** P1 · **Estado:** OPEN / DESIGN_INTENT_RECORDED · **Evidência:** duas novas capturas do PO, rota `/closing/monthly-closing` sem competência e `/closing/monthly-closing/2026-09` com competência.
- **Situação atual:** hero de “Fechamento mensal” usa altura excessiva: título/descrição, filtro de mês, ações em linha isolada; tabs “Visão geral / Documentos e interações / Relatórios e divergências” aparecem abaixo, fora do hero.
- **Diretriz UX do PO:** compactar hero; em desktop colocar **mês de referência + ações Atualizar consulta e Limpar filtros** (e ação de pesquisa, se existir nesse contexto) **na mesma linha**; organizar fluxo em cerca de **duas faixas**, não três; integrar as **três tabs dentro do hero**, mantendo hero presente e consistente na navegação entre elas.
- **Validação futura:** desktop/mobile, claro/escuro, foco/teclado, troca de abas/deep routes, filtro e refresh; sem overflow nem sobreposição; seguir `@delpi/plugin-ui` e padrão visual, sem duplicar chrome.
- **Nota:** proposta não redefine o shell global nem obriga um layout rígido no mobile.

### CF-UX-017 — Área “O que precisa de atenção” orientada a decisão
- **Prioridade:** P1 · **Estado:** OPEN / PRODUCT_INTENT_RECORDED · **Evidência:** capturas da visão geral de setembro/2026.
- **Situação atual:** lista/cartões mostram textos genéricos como “conferência ainda não finalizada”, “não foi possível consultar ...”, sem dimensão numérica, relatório/escopo/causa ou indicação suficiente do próximo passo; há também resumo de “8 situações”.
- **Diretriz UX do PO:** exibir, **quando sustentado pelo contrato**, quantidade, resumo, relatório/divergência afetada, natureza/status, impacto e ação concreta. Priorizar informação escaneável e navegável em vez de avisos vagos.
- **Pendência contratual futura:** inventariar resumos já disponíveis, custo/performance e origem; **rotas de resumo, pré-cálculo, cache ou persistência são hipóteses, não escolhas aprovadas**. Não inventar contagens nem transformar erro técnico em divergência de negócio.
- **Validação futura:** distinguir pendência, erro de consulta, divergência real e homologação pendente; mostrar proveniência e link correto ao owner.

### CF-UX-018 — Entrada da Central sem competência selecionada
- **Prioridade:** P1 · **Estado:** OPEN / DESIGN_INTENT_RECORDED · **Evidência:** captura da rota `/closing/monthly-closing` sem período, com seleção vazia e cards “Fechamentos abertos: 10/2026 · 0 itens; 09/2026 · 0 itens”.
- **Situação atual:** pequenos cards com mês e “0 itens” não explicam o significado da contagem, o estado do fechamento nem a próxima ação; usuário pode interpretar incorretamente “0” como ausência de pendências.
- **Diretriz UX do PO:** substituir ou complementar cards por **tabela/listagem informativa** com metadados reais e disponíveis: competência, estado, data de abertura, quantidade de pendências, progresso/etapa, responsável **somente se o contrato possuir esse dado**, e ação clara para abrir a competência.
- **Validação futura:** labels e zeros semanticamente corretos, estados vazios, navegação, responsividade e acessibilidade. Sem inventar campos ou criar API antes da revisão contratual consolidada.

### Política de continuidade desta revisão
1. Cada nova observação do PO será registrada neste **mesmo documento 150**, com ID sequencial `CF-UX-019+`, evidência, rota, prioridade e estado de revisão.
2. Durante esta fase, **não produzir prompts de Devin, não codificar, não alterar contrato/runtime, não publicar deploy**. Apenas commits documentais incrementais para conservar as observações.
3. Não classificar intenção UX como defeito técnico provado; separar `OBSERVED_SCREENSHOT`, `TO_VERIFY` e `DESIGN_INTENT_RECORDED`.
4. Ao fim da revisão de **todas** as páginas, produzir consolidação única de dependências, padrões de UX, RQ/AC e decisões materiais para uma execução coordenada, **somente quando o PO determinar**.


### CF-UX-019 — Componente único de carregamento, progresso e transparência por fonte (TODAS AS PÁGINAS)
- **Prioridade:** P1 transversal (impacto de UX/percepção de disponibilidade) · **Estado:** OPEN / DESIGN_INTENT_RECORDED + OBSERVED_SCREENSHOT · **Evidência:** nova captura autenticada da aba Relatórios e divergências, setembro/2026, exibindo textos soltos “Consultando fontes...” e “Consultando a conciliação analítica...”, KPIs como travessões e blocos vazios durante a consulta.
- **Diagnóstico a verificar:** possível regressão do padrão de loading já implementado anteriormente e do componente de carregamento disponível em `@delpi/plugin-ui`. Revisar documentação `30-plugin-ui-reuse-map.md`, exports reais do kit, wrappers locais e todas as ocorrências atuais de loading/skeleton/spinner/texto no Portal. **Não afirmar regressão técnica sem confronto com HEAD e histórico.**
- **Decisão de UX do PO:** padronizar o **mesmo componente visual de carregamento do plugin-ui**, importado pelo padrão de wrappers aprovado, **em todas as páginas e deep routes** do Portal Controladoria & Finanças; substituir textos de espera soltos, spinners improvisados e placeholders inconsistentes. Não duplicar chrome, componente, árvore de temas ou estado de carregamento entre páginas.
- **Progresso requerido:** mostrar **percentual de carregamento real e explicável** e **quais relatórios/fontes já terminaram, estão em execução ou ainda faltam**, com feedback progressivo; por exemplo, card compacto “Carregando informações de setembro/2026 — 2 de 5 consultas concluídas · 40%”, lista “Entradas e saídas — concluído; Estoque P7 — concluído; Material em processo — consultando; Kardex/CPV — aguardando; Inventários — aguardando”. **Exemplo conceitual, não resultado factual de runtime**.
- **Sem progresso fictício:** percentual somente sobre unidades de trabalho determinísticas e conhecidas (tarefas ponderadas conforme contrato ou proporção de consultas concluídas com denominador estável); nunca estimar tempo ou porcentagem de bytes/linhas quando desconhecidos. Se a quantidade/duração de tarefas for desconhecida, mostrar estado indeterminado e contagem comprovada; não deixar artificialmente em 90% nem usar cronômetro para simular progresso. Separar consulta `done` de `PASS` de negócio/homologação.
- **Feedback por fonte:** `pendente / consultando / concluída / falhou / indisponível / ignorada por escopo`; exibir resultados já disponíveis, permitir que falha parcial não bloqueie todas as outras consultas; oferecer retry de item quando permitido e CTA ao relatório. Ao terminar, eliminar barra/transição de loading mantendo mensagens de limitações reais.
- **Escopo de revisão global:** Início, Visão geral, Sala de interação, Minhas tarefas, Administração, Ajuda, Página de usuário, Central sem competência, P1/P2/P3/P4/P5, relatórios R01–R15 que possuam consulta e todos os deep routes; mapear e unificar loading inicial, paginação, mudança de filtro, refresh, upload/download, eventos assíncronos e erro parcial conforme cada contrato.
- **Sem decisão de API nesta fase:** primeiro inspecionar se o progresso por consultas pode ser derivado com segurança do client/orquestração MFE/BFF existentes. Novas rotas de job/status, persistência, cache, streaming ou alteração de contrato **não estão aprovadas**; abrir `DECISION_REQUIRED` somente quando evidência demonstrar necessidade material.
- **Verificação futura:** desktop/mobile, claro/escuro, leitor de tela (`aria-live`, progressbar com valores verdadeiros), foco/teclado, transição loading→sucesso/empty/erro, requisições simultâneas, filtros alterados rapidamente, cancelamento/stale response, timeout/retry e nenhuma animação interminável. Evidência visual antes/depois em páginas representativas e inventário de todas as rotas.
- **Preview UX:** mockup estático gerado na conversa para revisão visual do conceito; não é um layout aprovado nem evidência de componente implementado. Associar imagem ao dossiê de design quando disponibilizada ao executor.
