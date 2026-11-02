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


### CF-UX-020 — Remover hero duplicado do Fechamento nos deep routes de relatórios
- **Prioridade:** P1 · **Estado:** OPEN / DESIGN_INTENT_RECORDED + OBSERVED_SCREENSHOT · **Evidência:** capturas autenticadas 02/11/2026 de `/closing/monthly-closing/2026-09/reports/financial-settlements` e `/closing/monthly-closing/2026-09/reports/stock-inventory`.
- **Problema observado:** a página de relatório apresenta o hero geral **“Fechamento mensal”** (competência, botões Limpar filtros/Atualizar consulta) e, abaixo, um segundo hero específico **“Baixas financeiras”** ou **“Estoque histórico — P7”**. A duplicação consome altura e repete controles/contexto.
- **Diretriz PO:** ao entrar em um **relatório/deep route**, **não renderizar o hero geral do Fechamento mensal**. Preservar o **componente de caminho/breadcrumb existente** como navegação contextual clicável `Início → Fechamento mensal → Relatórios e divergências → [Relatório]`; navegar ao fechamento/competência e à lista de relatórios pelos segmentos reais do router. O breadcrumb substitui o hero geral para orientação, sem duplicar título ou filtro global.
- **Consistência:** em páginas de competência com tabs, permanece CF-UX-016 (hero compacto e tabs integradas). **Somente a deep route de relatório perde o hero do fechamento**. Não alterar o shell global e não remover o hero específico.
- **Aceite futuro:** todos os relatórios reais; refresh/deep link, URL/query params, botão voltar/browser history, foco teclado, breadcrumb sem caminhos inexistentes, desktop/mobile, temas; filtros de competência preservados conforme contrato. Antes/depois visual.

### CF-UX-021 — Compactar hero próprio e reunir filtros + ações nos relatórios
- **Prioridade:** P1 · **Estado:** OPEN / DESIGN_INTENT_RECORDED + OBSERVED_SCREENSHOT · **Evidência:** cards/KPIs e filtros de `Baixas financeiras` e `Estoque histórico — P7` mostram altura elevada e linha extra dedicada a ações.
- **Diretriz PO:** compactar **hero do relatório** preservando identidade/título, subtítulo curto, contexto da competência e KPIs relevantes, mas reduzindo grandes áreas/padding/separadores redundantes. **Agrupar no mesmo container/linha em desktop os filtros (por exemplo filial, armazém, período, natureza, ordenação) e as ações** `Limpar filtros`, `Exportar CSV`, `Exportar PDF`, `Atualizar consulta` — conforme as ações que cada relatório realmente suporta. Não exibir exports fictícios.
- **Layout responsivo:** em desktop, ações alinhadas ao conjunto de filtros com flex-wrap ou grid; mobile pode reflow em linhas acessíveis. Não impor que campos numerosos caibam em uma única linha causando compressão, perda de rótulo ou overflow; preferir organização compacta coerente com o kit.
- **Reuso:** usar `@delpi/plugin-ui` e wrappers canônicos; inventariar variantes de `PageHero`, `FilterBarShell`, `DataTableSection`, grupos de ações já existentes antes de compor. Não construir novo chrome.
- **Escopo transversal:** Baixas R01/R02, P7/R03, R04, R05, R06, R07, R08, R09, R10, R11, status R12/R15 e demais deep routes de relatórios presentes no HEAD; aplicar mesma linguagem e variações necessárias por número de filtros.
- **Critério de aceite futuro:** redução perceptível de scroll antes dos dados; títulos/contadores legíveis, competência preservada, CTA claro, sem controle duplicado, filtros/exports funcionais, loading CF-UX-019 integrado, layout mobile/claro/escuro, teclado/foco, regressões.

**Relação entre itens:** CF-UX-016 trata da competência e das tabs; CF-UX-020 elimina a repetição do hero geral nos relatórios; CF-UX-021 compacta o hero específico e consolida os controles. Essas são **diretrizes de UX registradas**, não implementação aprovada nesta fase.


## 7. Revisão visual dos oito deep routes restantes + contraste CLARA (02/11/2026)

**Decisão da fase:** apenas registro de UX/defeitos candidatos no plano único; **sem código, prompt, contrato novo ou deploy**. Capturas do PO cobrem: R05 `stock-movements`, R06 `stock-kardex`, R07 `inventory-adjustments`, R08 `work-in-process`, R10 `cost-center-expenses`, R11 `billing-exclusion-roster`, R12/R15 `cost-closing-state`, R04 `production-order-consumption`. Os novos itens são complementares a CF-UX-001..021, não os substituem. Todos precisam de prova após carregamento antes de classificar como defeito permanente.

### Matriz de revisão por relatório

| Relatório | Evidência visual capturada | Consulta CLARA no mesmo contexto ou próximo | Verificação necessária |
|---|---|---|---|
| R05 | Disponível; 14 tipos produto; saldo atual **14.469.584,01**; filtros filial/escopo e ações em linha separada; composição saldo inicial **14.620.961,79**, movimento líquido **-151.377,78** | `read(report.stock_movements)` 2026-09/filial 01 retornou **success** e fonte MATR320 com paridade PENDING; sem igualdade quantitativa ainda demonstrada porque print usa `branch=all` | Comparar `branch=all` com agregação autorizada por filial, sem somar dimensões diferentes; verificar a equação do saldo e data-base. |
| R06 | Em captura intermediária: `Disponibilidade ...`, `Data-base ...`, botões temporariamente desabilitados e “0 registros” na seção de movimento; painel CPV mostra **2.193.940,70** | `read(report.stock_kardex)` 2026-09/filial 02 PASS, **27.709 movimentos**, openingValue **9.219.415,573**, closingValue **3.393.778,054** | Reproduzir após settle; não chamar “0 registros” defeito consolidado sem saber se a tela terminou loading; distinguir CPV gerencial (SD2) do Kardex MATR910; testar filial `all`. |
| R07 | Disponível; **305 ajustes**, 277 produto/armazém; valor líquido **-87.265,43** com `branch=all`; valores positivos/negativos | `read(report.inventory_adjustments)` 2026-09/filial 02 PASS, **47 movimentos**, netValue **-30.083,631**, 46 blocos | Universos diferentes (`all` vs filial 02): **não há contradição provada**; comparar mesma filial/filtro; reconciliar histórico 45 e locais 01/99 vs 50 separadamente. |
| R08 | Disponível; **754 linhas alocadas**; total em processo **871.416,33**, dividido físico **702.287,87** + alocado **169.128,46** | `read(report.work_in_process)` 2026-09/filial 01 PASS, paginação **549 itens**; não é o mesmo universo da tela `all` | Testar agregação e total por filial, sem confundir linhas com produtos ou OPs. |
| R10 | Disponível; **929 linhas**, **523.546,07**, 66 CC, 19 possíveis divergências (universo apuração, `all`) | `read(report.cost_center_expenses)` 2026-09/filiais default/all PASS, **929 linhas**, same summary universe; primeira amostra contém dados reais; homologação histórica **353 linhas / 169.704,12 filial 01** é outro recorte | PASS preliminar da contagem geral (929); comparar totais exatos e tipagem de achados, sem chamar “possíveis” de erros confirmados. |
| R11 | Disponível; **11 linhas**, **97.462,71**, **3 possíveis divergências**, vista candidatas; tela usa `all` | `read(report.billing_exclusion_roster)` 2026-09/default PASS, 11 linhas; sample real, valor histórico documentado 97.462,71 | Confirmar filtros usados e summary; manter aviso “lista investigativa — não excluir NF automaticamente”; 3 achados não são 3 erros confirmados. |
| R12/R15 | Hero largo contém **barra/container de filtros completamente vazio**, com botões separados; limitações técnicas em bullets simples e dois blocos de filial sem hierarquia visual forte | `read(report.cost_closing_state)` 2026-09/filial 01 PASS — `branches.01.snapshot.state=available`, `cutoff_marker=observed`, `cost_evidence=observed`, `wizard_lifecycle=unavailable`, `human_acceptance=not_informed` | Verificar componente vazio/controle condicional ausente, refinar visual por filial e categorias; nunca prometer execução ERP ou homologação humana. |
| R04 | Duplicação do hero geral, aviso e busca com label/placeholder colidindo; **1.243 OPs** filial 01 mas tabela OP/produto/data renderiza “—”, só status `N` | `read(report.production_order_consumption)` 2026-09/filial 01 PASS, total 1.243; sample OP `24841701001`, product `90262129`, emission `2026-09-30` | **P0 confirmado de apresentação** na captura: comparar camelCase/snake_case e mapping real; não alterar produtor sem prova. Vinculado a CF-UX-001/002/003. |

**R01/R02 e R03/P7** já aparecem nas capturas anteriores e permanecem em CF-UX-020/021; o executor deve aplicar o mesmo padrão de compactação a **todos** os deep routes, inclusive R09 e páginas não demonstradas nesta leva. CLARA validou transporte real para diversos relatórios, mas não substitui o teste visual/autenticado do MFE nem prova equivalência de filtros.

### Novos itens específicos (IDs sequenciais)

**CF-UX-022 — Painéis e KPIs de relatório: densidade/consistência transversal.** P1 · OPEN / DESIGN_INTENT_RECORDED + OBSERVED_SCREENSHOT. R05/R06/R07/R08/R10/R11 mostram heros com título grande, KPIs altos, texto de limitação longo e segunda linha de filtros/ações, repetindo a oportunidade de compactação do CF-UX-021. Revisar hierarquia (título, competência, KPI, paridade, filtros, CTA); texto longo de limitações pode usar seção de detalhes acessível mantendo aviso curto visível. A seleção de KPIs **não pode esconder alertas materiais**; não misturar valor líquido, saldo, movimento, eventos ou medidas gerenciais. Validar consistência visual desktop/mobile/escuro/claro sem modificar dados.

**CF-UX-023 — R12/R15: faixa vazia e apresentação técnica pouco acionável.** P1 · OPEN / OBSERVED_SCREENSHOT + TO_VERIFY_CAUSE. Captura mostra barra escura de filtros sem conteúdo entre subtítulo e ações. Investigar se container renderiza vazio por condição/branch, se tem controles invisíveis ou placeholder; eliminar espaço morto apenas se confirmado. Reorganizar estados técnicos por filial em grupos de leitura clara: snapshot de estoque, marcador cutoff, evidência de custos, ciclo do wizard, aceite humano; distinguir `Disponível`, `Observado`, `Indisponível`, `Não informado`, com contexto e limitações. **Não representar execução do wizard TOTVS nem homologação oficial; é somente observação de estado.**

**CF-UX-024 — R06: estado de carregamento e “0 registros” transitório.** P1 · OPEN / OBSERVED_SCREENSHOT + TO_VERIFY_PERSISTENCE. A captura exibe KPIs em “...” e seção de movimentos com 0, apesar de a CLARA retornar dados na filial 02. Testar espera até settle, branch `all`, paginação, eventual timeout, request race e o CF-UX-019; mostrar estado carregando em vez de zero conclusivo enquanto query está pendente; ao terminar atualizar estado e habilitar ações apenas quando semanticamente válidas. **Não concluir erro permanente a partir de uma única captura.**

**CF-UX-025 — Auditoria de correspondência Portal × CLARA com filtros idênticos.** P0 para validação do R04; P1 transversal. OPEN / TO_VERIFY. Por relatório capturar rota, competência, filial, escopo, universo, visão, status, totais, paginação, proveniência, unidades, timezone, `asOf`; repetir por CLARA com os **mesmos filtros exatos**, respeitando casos em que `branch=all` na UI não é equivalente a `branch=01/02`. Criar matriz campo-a-campo com PASS/FAIL/INCONCLUSIVE e evitar equivalência forçada entre 929 vs 353, 305 vs 47, 754 vs 549; confirmar R05/08 sums, R10/R11 quantidades/valores e R12/15 marcadores. Paridade oficial TOTVS distinta de correspondência entre consumers.

**CF-UX-026 — Filtros e ações consistentes em relatórios com capacidades diferentes.** P1 · OPEN / DESIGN_INTENT_RECORDED. Aplicar CF-UX-021 a R05/R06/R07/R08/R10/R11/R12/R15 e R04; apenas exibir CSV/PDF se contrato suportar; não manter linha vazia; status de ação disabled deve explicar porquê (ex. R06 loading), sem perda de filtro ao navegar/refrescar. Testar layout com 2 e 7 campos, wrap responsivo e label sem overlap.

### Condições para uma futura execução única
- **Não implementar agora**. O PO ainda está em revisão de todas as páginas.
- O executor futuro não poderá resolver divergências de valores antes de igualar filtros/grão/universo, nem alterar SQL para obter números iguais aos screenshots.
- Todo item deve ter captura, resultado funcional, causa demonstrada, owner/RQ/AC, teste, patch, SHA e pós-verificação real.
- Não duplicar CF-UX-001..021: aplicar os padrões compartilhados uma única vez e validar cada consumidor, evitando pequenas intervenções e deploys repetidos.
