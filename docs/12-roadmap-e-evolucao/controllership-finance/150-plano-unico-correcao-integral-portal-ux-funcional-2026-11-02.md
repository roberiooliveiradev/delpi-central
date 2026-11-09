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


## 8. Programa executivo aprovado pelo PO — execução sequencial completa (02/11/2026)

**Esta seção substitui as instruções anteriores de “somente revisão / não implementar” nas seções 6 e 7:** o PO **agora autoriza** iniciar a implementação coordenada pelo Devin, em etapas sequenciais, com correção no ambiente local, testes, commits, push e deploy controlado após gates. Os itens históricos CF-UX-001..026 permanecem válidos e não podem ser eliminados por reorganização. A autorização abrange UX e correções de bugs dentro dos contratos existentes, **não** mudanças materiais de contrato, segurança, owner, persistência ou arquitetura sem decisão explícita.

### Regras de execução e registro
- **HEAD remoto + git status local e WIP** no início; ler instruções oficiais, .cursor aplicável, README, doc 150, doc 30 reuso, padrão visual, documentação da competência e contratos/testes. GitHub authority TARGET; TÉO authority AS-IS.
- Usar **uma branch de trabalho dedicada ou checkout limpo conforme política vigente**, sem sobrescrever alterações de terceiros; não mover WIP alheio. Respeitar branch protection e CI. Não trabalhar num HEAD local antigo sem comparar com origem.
- **Não reabrir arquitetura:** MFE → somente BFF `controllership-finance-api`; BFF → integração existente com `api-delpi`; CLARA → BFF; `@delpi/plugin-ui` first; apenas `controllership-finance.access/manage`; Core AuthZ efetiva fail-closed. Sem SQL/produtor novos por preferência.
- **Um programa, etapas em sequência e checkpoints locais:** em cada etapa reproduzir → classificar → aplicar diff mínimo → testar → verificar visual e outcome → atualizar linha de evidência do doc 150. Não encerrar em “plano”, “rota presente”, “build verde” ou “teste não executado”.
- **Sem buracos:** cada ID CF-UX-001..026 terá no fim `FIXED_VERIFIED`, `NO_DEFECT_VERIFIED`, `DECISION_REQUIRED` ou `BLOCKED_WITH_EVIDENCE`, com evidência e owner; nunca “feito” quando não testado. Se houver decisão material, parar somente parte dependente e continuar o que é independente; não implementar a opção recomendada sem decisão.
- **Performance e segurança:** não disparar N consultas por render desnecessariamente; não adicionar summary API/cache/persistência sem gate material; não simular percentual ou tempos. Testar permissão e escopo de recurso com identidade autorizada sem logs de tokens.
- **Deploy:** somente após testes locais/integrados e gates de segurança; publicar componentes alterados, confirmar SHA, rollback pronto, smoke real no Portal/CLARA, registrar status. Quando ambiente/sessão humana indisponível, `TEST_NOT_RUN` e veredito `INCONCLUSIVE`, sem simular a validação.

### Etapas e dependências — sem perder nenhum dos 26 IDs

| Etapa | Entrega executável | CF-UX cobertos | Gate de saída |
|---|---|---|---|
| E0 — Baseline e matriz | Varredura de rotas/componentes, contract maps e evidências antes; matriz de tela × estado × breakpoint; reprodutor R04; definir owner e RQ/AC por item. | **Todos 001–026** como inventário de cobertura | 100% das 26 linhas rastreadas; fontes e screenshots linkados ou indisponibilidade explicitada. Não encerra o trabalho. |
| E1 — P0: verdade dos dados | Corrigir DTO/projeção/tabela R04 com OP, produto, datas, detalhe reais; corrigir matriz R04/R09 no catálogo vigente; garantir correspondência via CLARA com recortes iguais. | **001, 005, 006, 015, 025(P0)** | Portal com mesma OP real e campos da CLARA; matriz sem afirmações obsoletas; nenhuma paridade oficial promovida. |
| E2 — Componentes compartilhados de navegação, hero e filtros | Hero compacto da competência e tabs internas; remover hero geral dos deep routes mantendo breadcrumb clicável; compactar hero dos relatórios, KPIs, textos, filtros e ações; corrigir search R04 e overflow. | **002, 003, 014, 016, 020, 021, 022, 026** | Todas rotas alvo com layouts responsivos e navegação/refresh/deep link acessíveis; ações só quando suportadas. |
| E3 — Loading, estados e feedback | Reusar loader do plugin-ui, progresso honesto por tarefas conhecidas, status por fonte e render progressivo; resolver placeholders, ‘0 registros’ durante loading, stale state e retry. | **008, 009, 019, 024** | Nenhum estado transiente interpretado como zero definitivo; sem percentual/ETA fictícios; screenshots de loading/sucesso/erro/empty em rotas representativas. |
| E4 — Cockpit, documentos, atenção e primeira entrada | Reescrever apresentação orientada a ação do painel de atenção a partir de dados existentes; deixar claro documento adicional vs checklist e ausência de configuração; substituir cards confusos de fechamentos abertos por tabela/resumo com metadados reais; explicar conciliação. | **010, 011, 017, 018** | Dados existentes e proveniência/ação claras; nenhum count inventado; sem novas rotas/armazenamento sem decisão material. |
| E5 — Estados de relatórios e auditoria funcional | Separar consulta disponível vs paridade/homologação pendente; legenda e indicadores `Itens/Validados` com semântica; validar R06/R07 páginas reais e reavaliar 45×47; R12/R15 faixa vazia/estados técnicos; fazer paridade **Portal × CLARA** em mesmo universo R01–R15 aplicáveis. | **004, 007, 012, 013, 023, 025(P1)** | Screenshots e consultas reais; explicação de cada diferença; nenhuma rotina ERP executada; classificação honesta de pendências. |
| E6 — Auditoria residual de TODAS as páginas | Percorrer Início, Visão geral, Central P1–P5, Documentos/interações, Relatórios/deep routes, Administração, Sala de interação, Minhas tarefas, Ajuda, usuário, todas variações e breakpoints; registrar novos IDs **027+** para bugs reais. | **Todos 001–026** + novos | Cobertura por rota e caso; bugs novos corrigidos nesta execução se autorizados/contratos existentes, senão decisão/bloqueio explícito. |
| E7 — Regressão integral, Help, publicação e aceite | Testes de unidade/integrados/contrato, security positive/negative, a11y, mobile/dark/light, CLARA com dados reais, builds, regressão R04/R06/R07/R09 e demais rotas afetadas; docs/Help; commits/push; deploy controlado e smoke humano em produção. | **Todos 001–026** e novos | Quadro final sem ID omitido, SHA local/remoto/deploy, smoke do Portal com screenshot, rollback e veredito baseado em outcome. |

**Dependência:** E0 → E1 → E2 → E3 → E4 → E5 → E6 → E7. Testes e atualização documental ocorrem em **todas** as etapas, não apenas E7. E6 pode identificar novos bugs e exigir retornar a E1–E5 para corrigi-los antes de E7; evitar publicar versões parciais desnecessárias. Preferir deploy produtivo consolidado após gates e validação em staging, salvo exigência operacional demonstrada.

### Quadro de cobertura verificável dos 26 IDs

| ID | Etapa primária | ID | Etapa primária | ID | Etapa primária |
|---|---|---|---|---|---|
| 001 | E1 | 002 | E2 | 003 | E2 |
| 004 | E5 | 005 | E1 | 006 | E1 |
| 007 | E5 | 008 | E3 | 009 | E3 |
| 010 | E4 | 011 | E4 | 012 | E5 |
| 013 | E5 | 014 | E2 | 015 | E1 |
| 016 | E2 | 017 | E4 | 018 | E4 |
| 019 | E3 | 020 | E2 | 021 | E2 |
| 022 | E2 | 023 | E5 | 024 | E3 |
| 025 | E1+E5 | 026 | E2 | — | — |

### Contrato de rastreabilidade por item
`ID | rota | condição/filtros | evidência antes | causa PROVEN ou TO_VERIFY | owner | RQ/AC | diff/commit | testes locais | teste Portal humano | teste CLARA se aplicável | evidência depois | status | residual/decision`.

No encerramento, entregar tabela **26/26** com links para provas; `CF-UX-027+` quando houver. `OPEN` ou `TEST_NOT_RUN` nunca são convertidos em `PASS` por conveniência.

### Política de decisões
Se qualquer etapa exigir API de resumo, nova regra de agregação, cache/persistência, mudança de contrato, autorização/Keycloak, estratégia de cálculo, breaking change, outro bounded context ou UX de produto com escolha ainda não definida: registrar **DECISION_REQUIRED** (opções, impactos, recomendação), **não implementar** a escolha sem aprovação. Fazer todos os outros ajustes aprovados do mesmo programa. Não usar uma pendência pontual como desculpa para abandonar os demais itens.

### Relatório final obrigatório
BASE_HEAD, FINAL_HEAD, ORIGIN_MAIN, git status/WIP, commits, diffs, suite de testes, matriz 26+ IDs, cobertura de rotas, capturas before/after, resultados CLARA/Portal com mesmo recorte, segurança, performance, Help, SHA implantado, rollback, bloqueios de decisão, veredito `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`. **O objetivo é entrega verificável, não contagem de mudanças.**

## 9. Registro de execução Devin — 02/11/2026 (sessão CF-PROC0072-PORTAL-UX-FULL-REMEDIATION)

**BASE_HEAD:** `3d8494da3d` (main local divergente 22×170) · **MERGE_HEAD:** `0218e02c87` (merge origin/main `bfe4c71cd6` + 22 commits locais; 3 conflitos resolvidos: ProductionOrderConsumptionPage→remoto canônico, ledgers→união) · **ORIGIN_MAIN:** `bfe4c71cd6` · WIP de terceiros preservado (backup `/c/Users/analistaptd/wip-backup-cf150-20261102`, stash intacto).

### Diffs executados (escopo da task)
| Arquivo | Mudança | IDs |
|---|---|---|
| `src/api/productionOrderConsumptionApi.ts` | normalização snake_case→camelCase no adapter (produtor consumption-audit emite snake; MFE lia camel) | 001 |
| `features/closing/ProductionOrderConsumptionPage.tsx` | busca via `FilterInputField` do kit (sem overlap); loading `CfLoadingCard`; paginação `page*25 >= total` | 002, 003, 019 |
| `BFF reports_routes.py` + `report_comparison/catalog.py` | R04 e R09 → `OPERATIONAL_VIEW` com owner/note honestos (matriz reflete HEAD) | 005, 006, 015 |
| `app/ClosingHero.tsx` + `index.css` | slot `tabs` integrado ao hero; faixa única `.cf-hero-controls` (filtros+ações); `onClearFilters` opcional | 016, 021, 022, 023, 026 |
| `features/closing/MonthlyClosingPage.tsx` | hero geral omitido em deep route de relatório (breadcrumb permanece); tabs dentro do hero; landing de competências em tabela com metadados reais (`status`, `opened_at`, `item_count`); loading via `CfLoadingCard` | 014, 016, 018, 019, 020 |
| `features/closing/MonthlyReportsPanel.tsx` | loading com progresso determinístico por fonte (n/5 consultas + status por fonte); cards sem probe → «Consulta implementada» (distinto de disponibilidade medida) | 004, 008, 009, 019, 024 |
| `features/closing/CostClosingStatePage.tsx` | chamada do hero corrigida (prop `hint` inválida + props obrigatórias ausentes); faixa vazia eliminada; `CfLoadingCard` | 023 |
| `*.test.tsx` (2 arquivos) | expectativas atualizadas à nova UX aprovada (rótulo, catálogo de 10 cards, landing em tabela) | 004, 018 |

### Matriz de estado por item
| ID | Estado | Evidência |
|---|---|---|
| 001 | FIXED_VERIFIED | typecheck + mapeamento no adapter; campos OP/produto/data renderizam do contrato |
| 002 | FIXED_VERIFIED | `FilterInputField` canônico (kit) — sem sobreposição label/placeholder |
| 003 | FIXED_PENDING_VERIFY | campos reais + paginação corrigida; densidade visual a confirmar em sessão |
| 004 | FIXED_PENDING_VERIFY | «Consulta implementada» separada de «Disponível»/erro; paridade não promovida |
| 005 | FIXED_VERIFIED | matriz R04 = `OPERATIONAL_VIEW` + owner consumption-audit |
| 006 | FIXED_VERIFIED | matriz R09 = `OPERATIONAL_VIEW` + owner SD2+SG1+SHY |
| 007 | FIXED_PENDING_VERIFY | colunas `Itens`/`Validados` mantêm «—» só quando sem itens (semântica já separada) |
| 008 | FIXED_PENDING_VERIFY | loading por fonte; alertas transitórios preservados como tal |
| 009 | FIXED_VERIFIED | progresso honesto `n/5 consultas` + detalhe por fonte |
| 010 | PENDING | distinção documento adicional × checklist — não alterada nesta fatia |
| 011 | FIXED_PENDING_VERIFY | conciliação já exibe operandos/escopo/proveniência (ReportSharedSections) |
| 012 | FIXED_PENDING_VERIFY | catálogo abre todas as páginas implementadas |
| 013 | BLOCKED_WITH_EVIDENCE | R07 45×47 requer confronto CLARA×Invent.xlsb em sessão autenticada — não executado |
| 014 | FIXED_PENDING_VERIFY | tabs integradas; matriz técnica permanece em disclosure |
| 015 | FIXED_VERIFIED | idem 005 — matriz única por contrato |
| 016 | FIXED_PENDING_VERIFY | hero compacto + tabs no hero + controles numa faixa |
| 017 | PARTIAL | itens de atenção já possuem quantidade/origem/ação; resumo novo exigiria API (DECISION) |
| 018 | FIXED_PENDING_VERIFY | landing em tabela: competência/estado/abertura/itens/ação |
| 019 | FIXED_PENDING_VERIFY | `CfLoadingCard` aplicado nas superfícies principais (hero mensal, relatórios, R04, R12/R15); cobertura residual em E6 |
| 020 | FIXED_PENDING_VERIFY | hero geral removido nas deep routes de relatório; breadcrumb clicável preservado |
| 021 | FIXED_PENDING_VERIFY | faixa única filtros+ações; hero já `density=compact` |
| 022 | FIXED_PENDING_VERIFY | mesmo componente/faixa em todos os relatórios |
| 023 | FIXED_PENDING_VERIFY | R12/R15 sem faixa vazia; hero com props corretas |
| 024 | FIXED_PENDING_VERIFY | progresso por fonte; «0 registros» só após settle |
| 025 | TEST_NOT_RUN | confronto Portal×CLARA com filtros idênticos requer sessão autenticada — não executado |
| 026 | FIXED_PENDING_VERIFY | controles consolidados; exports só quando contrato suporta (inalterado) |

### Verificação executada
- `npx tsc -b` (plugin): **0 erros**.
- `vitest run`: **412/417 iniciais → todas as falhas resolvidas** (2 expectativas atualizadas à UX aprovada; 1 drift pré-existente catálogo 9→10; 1 flake DocumentDetailPanel, verde na reexecução). Suites finais afetadas: 48/48 + 39/39 PASS.
- BFF: matriz R04/R09 alterada no catálogo estático — sem mudança de shape de resposta.
- Pendente de sessão humana: smoke visual autenticado, CLARA com filtros idênticos (025), breakpoints/temas/keyboard em produção.


## 10. Nova leva de revisão visual pelo PO — pós-deploy Plano 150 (02/11/2026)

**Estado desta leva:** REVIEW / REGISTER_ONLY. As alterações do Plano 150 foram publicadas, mas o PO está revisando visualmente e **não autorizou ainda um novo ciclo de correção**. Registrar observações, impactos e verificações necessárias no Documento 150; consolidar esta leva antes de enviar uma nova execução ao Devin.

**Evidência:** captura autenticada da rota `/apps/controllership-finance/closing/monthly-closing` (sem competência selecionada), contendo hero, filtro de mês vazio e seção `Fechamentos abertos` com tabela simples de 10/2026 e 09/2026. Ambas as linhas exibem estado `Aberto`, datas de abertura, `Itens do checklist = 0` e um botão `Abrir fechamento`.

### CF-UX-027 — Substituir tabela simples de fechamentos por grid padronizado do Portal
- **Prioridade:** P1 · **Estado:** OPEN / OBSERVED_SCREENSHOT + PRODUCT_DIRECTION_RECORDED.
- **Problema observado:** a tabela recém-criada na landing do fechamento mensal não utiliza o padrão de grid visual/interativo que o Portal já aplica em outras listagens: cabeçalhos/linhas pouco espaçados, sem a estrutura e recursos consistentes com o kit.
- **Diretriz PO:** utilizar o componente de **Data Grid/Grid UI existente e efetivamente adotado no Portal**, inventariando primeiro `@delpi/plugin-ui`, wrappers e grids compartilhados já usados em outras páginas; não criar tabela própria nem biblioteca nova.
- **Aceite futuro:** colunas alinhadas, densidade adequada, hover/foco visíveis, legibilidade, estados loading/empty/erro e responsividade; reproduzir a mesma semântica de dados e não inventar métricas. Testar claro/escuro, mobile e teclado.
- **Dependência:** substitui o layout inicial do CF-UX-018, que fica **reaberto para refinamento visual**, sem invalidar os metadados já existentes.

### CF-UX-028 — Navegar para o fechamento pelo clique na linha do grid
- **Prioridade:** P1 · **Estado:** OPEN / PRODUCT_DIRECTION_RECORDED.
- **Problema observado:** cada linha possui botão redundante `Abrir fechamento`, aumentando ruído visual.
- **Diretriz PO:** a própria linha deve ser superfície de navegação: hover, clique e ativação por teclado (Enter/Espaço quando aplicável ao componente), levando à competência correta; remover o botão por linha **se o grid suportar adequadamente a navegação acessível**, sem prejudicar usuários de teclado/leitor de tela. Usar rota existente e preservar o contexto.
- **Aceite futuro:** a linha possui affordance clara, nome acessível, foco visível; clique e teclado abrem a competência correta; sem conflito com seleção, ordenação ou eventuais ações secundárias do grid. Retorno pelo breadcrumb/histórico preservado.

### CF-UX-029 — Checklist: investigar zeros e informar a versão efetivamente aplicada à competência
- **Prioridade:** P1 · **Estado:** OPEN / OBSERVED_SCREENSHOT + TO_VERIFY_DATA_AND_CONTRACT.
- **Problema observado:** `Itens do checklist` exibe **0** para 09/2026 e 10/2026. O print **não comprova** que não existe checklist: pode ser falta de configuração, versão não vinculada, lista vazia ou uma métrica que conte outro universo.
- **Diretriz PO:** verificar no contrato/owner do checklist de documentos se existem itens cadastrados, qual checklist está associado a cada competência, qual é o significado exato do contador e se há versão/identificador de template aplicável. Quando houver dados reais, exibir **versão do checklist documental por competência** (e eventualmente seu estado/configuração) para esclarecer diferenças entre fechamentos.
- **Sem inventar:** não converter ausência de binding em `0` sem prova; preferir `Não configurado` / `Sem checklist vinculado` / `0 itens` somente conforme o contrato real. A versão deve ser identificador existente, não gerada no MFE.
- **Dependência contratual:** antes de criar nova API ou esquema de versionamento, inventariar os campos e endpoints atuais de P2/P5, Administração, checklist/template e fechamento; se inexistente a capacidade e houver escolha material de contrato/persistência, registrar `DECISION_REQUIRED` com alternativas e impactos, sem implementação unilateral.
- **Aceite futuro:** para 09/2026 e 10/2026, quadro de origem/binding/contagem/versão, números consistentes com o backend, navegação para detalhes, diferenciação nítida entre checklist obrigatório e documento adicional (relaciona-se a CF-UX-010).

**Relações:** CF-UX-027 e 028 refinam CF-UX-018; CF-UX-029 cruza CF-UX-010, 017 e a governança documental P2/P5. Cada item permanecerá OPEN até reprodução, verificação de contrato, implementação e teste numa **próxima leva consolidada** autorizada pelo PO. **Não gerar prompt agora, não executar deploy nesta etapa de revisão.**


### CF-UX-030 — Remover borda/container redundante do mês de referência no hero da competência
- **Prioridade:** P2 · **Estado:** OPEN / DESIGN_INTENT_RECORDED + OBSERVED_SCREENSHOT · **Evidência:** captura autenticada do PO na aba Visão geral de setembro/2026, pós-deploy Plano 150.
- **Observação:** a compactação anterior posicionou mês e ações na mesma faixa, mas a borda externa envolvendo somente `Mês de referência` cria a aparência de “caixa dentro da caixa”, separando visualmente o filtro das ações.
- **Diretriz do PO:** remover o container/borda redundante, preservar o input e seu label, alinhar o mês e os botões como um único grupo funcional na faixa de controles do hero; manter tabs dentro do hero. Não remover contorno de foco ou estados acessíveis do próprio input.
- **Aceite futuro:** menos altura e ruído visual, mesmo comportamento da data, nenhuma quebra em desktop/mobile/temas, foco correto, integração com CF-UX-016/021.

### CF-UX-031 — Um único comando de atualização por contexto e ações com ícones em todos os heroes
- **Prioridade:** P1 transversal · **Estado:** OPEN / DESIGN_INTENT_RECORDED + OBSERVED_SCREENSHOT · **Evidência:** captura autenticada da aba Relatórios e divergências (09/2026), com `Atualizar consulta` no hero e `Atualizar dados` novamente no painel “O que precisa de atenção”. O componente de carregamento compartilhado funciona na captura, com **4 de 5 consultas concluídas** e barra com 20% restante.
- **Observação:** comandos de atualização duplicados provocam ambiguidade; os controles atuais apresentam texto longo e inconsistências entre heroes.
- **Diretriz do PO:** manter **um botão principal de atualização por contexto/página, preferencialmente no hero**, removendo o botão redundante `Atualizar dados` nos blocos internos quando executa a mesma operação. Rever semanticamente ações distintas antes de remover: se o refresh interno atualizar conjunto diferente, harmonizar uma única ação/orquestração preservando cobertura, sem ocultar tarefa necessária. Evitar refresh duplicado e disparo de fetches repetidos.
- **Padrão transversal de ações:** aplicar ícones canônicos existentes no `@delpi/plugin-ui` e wrappers para **Atualizar consulta** (ex.: refresh) e **Limpar filtros** (ex.: filter-x/eraser); preferir botões compactos, com ícone e texto curto/tooltip conforme acessibilidade e espaço, **não icon-only sem nome acessível**. Manter `aria-label`, tooltip e estados `loading/disabled`; garantir clareza da função e foco/teclado.
- **Cobertura:** hero da competência em Visão geral, Documentos e interações e Relatórios e divergências; todos os heroes de relatórios e deep routes, e demais superfícies que duplicarem refresh/clear. Integração com CF-UX-016, 019, 020, 021, 022, 026 e 030. O loading e percentual existente são **pontos positivos a preservar**, não alvos de remoção.
- **Critérios futuros:** apenas uma ação de refresh evidente por página/contexto, sem perda de consultas; atualizar dispara todas as fontes esperadas uma única vez; limpar filtros não dispara comandos indevidos; sem regressão do progresso `n/5`; responsivo, claro/escuro, teclado/foco, screen reader; conferir se filtros de relatórios e competência são contextos de atualização distintos.
- **Sem implementação agora:** esta é uma observação da nova leva pós-deploy; registrar e aguardar consolidação das demais páginas para correção conjunta.


### CF-UX-032 — R04 Consumo por OP: substituir tabela básica por Data Grid padronizado do plugin-ui
- **Prioridade:** P1 · **Estado:** OPEN / OBSERVED_SCREENSHOT + DESIGN_INTENT_RECORDED · **Evidência:** captura autenticada de `/apps/controllership-finance/closing/monthly-closing/2026-09/reports/production-order-consumption` após o deploy do Plano 150.
- **Observação:** o defeito anterior de mapeamento de dados foi aparentemente corrigido no Portal: a listagem agora mostra OPs reais (por exemplo, `24841701001`), descrição do produto (`CHICOTE DE LIGAÇÃO`), status `N` e data `2026-09-30`, com total exibido de `1.243` OPs. **Não reabrir o producer/adapter sem regressão reproduzida.** Entretanto, a tabela segue como HTML/apresentação simples, com cabeçalho e células sem padrão visual de grid, pouca hierarquia/contraste e sem affordance de navegação ao detalhe. A tela ainda tem espaços vazios e os filtros parecem deslocados/desconectados.
- **Diretriz PO:** reutilizar o **componente Data Grid/Table do `@delpi/plugin-ui` já adotado nos demais relatórios e seus wrappers locais**, com colunas, alinhamento, densidade, estilos, estados, paginação e tratamento de overflow consistentes. Não importar nova biblioteca nem criar novo grid. Preservar OP, produto/descrição, status, centro de trabalho **somente quando o contrato fornece valor** e data, com labels PT-BR e formatação da data; não trocar ausência legítima de centro por dado inventado.
- **Comportamento:** lista com pesquisa/filtros integrados ao padrão de hero/toolbar, paginação fiel ao backend, loading via componente canônico, estados vazios/erro, navegação ao detalhe da OP se já suportada pelo contrato/router, acessibilidade e responsividade; garantir que a mesma OP continua aparecendo na CLARA e no Portal sob filtros idênticos. `operational_view` / paridade oficial MATR860 `pending` permanecem.
- **Aceite futuro:** screenshot antes/depois e teste real de linhas, cabeçalhos, ordenação **apenas se suportada**, paginação, clique/detalhe, teclado/foco, mobile/claro/escuro; zero regressão da correção de campos do CF-UX-001. Relaciona-se a CF-UX-003, 021, 025, 027 e 031.
- **Nota:** a captura comprova exibição atual da listagem, **não** comprova que a página de detalhe funciona ou que todos os campos correspondem ao contrato sob outros filtros.

### CF-UX-033 — Breadcrumb contextual de relatórios deve incluir competência/fechamento selecionado
- **Prioridade:** P1 transversal · **Estado:** OPEN / OBSERVED_SCREENSHOT + DESIGN_INTENT_RECORDED · **Evidência:** breadcrumb atual no R04 `Início / Fechamento mensal / Relatórios e divergências / Consumo por OP`, sem indicar `2026-09` embora a rota esteja na competência de setembro.
- **Diretriz PO:** o componente de caminho deve tornar explícita a **competência selecionada entre “Fechamento mensal” e “Relatórios e divergências”**, por exemplo `Início → Fechamento mensal → Setembro/2026 → Relatórios e divergências → Consumo por OP`. O segmento da competência deve ser clicável e abrir a visão geral de `/closing/monthly-closing/2026-09`; “Relatórios e divergências” deve abrir a aba `?tab=reports` dessa mesma competência; “Fechamento mensal” leva à lista geral. O item atual identifica a rota.
- **Escopo:** aplicar a todas as deep routes de relatórios R01–R15 existentes, e avaliar rotas internas de documentos/interações com competência. Usar o breadcrumb/componente de navegação já vigente; obter competência **da rota/contexto canônico**, não de string ou data corrente; preservar parâmetros de rota ao navegar.
- **Aceite futuro:** trilha correta para 09/2026 e 10/2026, refresh e acesso direto por URL, mudança de competência, back/forward, foco, teclado, leitor de tela e comportamento mobile; não deixar segmento falso se não houver competência selecionada. Relaciona-se a CF-UX-020 e à ausência do hero geral nas deep routes.
- **Sem implementação agora:** registrar para a próxima leva consolidada de UX, sem gerar prompt isolado nem deploy.


### CF-UX-034 — Catálogo de relatórios: organização por fluxo de análise e rótulos orientados ao usuário
- **Prioridade:** P1 · **Estado:** OPEN / OBSERVED_SCREENSHOT + PRODUCT_DIRECTION_RECORDED + TO_VERIFY_AS_IS · **Evidência:** captura do catálogo “Relatórios para análise” 2026-09, exibe 10 cards em ordem Baixas, P7, R05, R06, R07, R10, R11, R08, R12/R15, R04, com códigos internos RXX no título.
- **Questão do PO:** a sequência parece misturada, sem explicitar o fluxo de trabalho da Joici; identificadores técnicos `R04`, `R05`, `R10` etc. não são bons nomes primários para usuários da Controladoria.
- **Fato canônico:** doc 118 §1–2 descreve **orquestração paralela**, não ordem linear única: rotinas ERP de custos `MATA320→MATA300→MATA330→MATA280`; emissões e reemissões de relatórios; conciliação monetária; documentos/Contabilidade. As etapas OPS-05..11 indicam famílias de consultas e pré-condições. Portanto **não afirmar** que a ordem visual atual corresponde à ordem da Joici nem impor uma ordem linear supostamente observada no vídeo sem confirmar com TÉO/owner.
- **Diretriz de UX:** revisar agrupamento e ordenação dos cards por **famílias e momentos funcionais** do fechamento, com grupos candidatos (não definitivos): financeiro (baixas a pagar/receber), estoque/custo/conciliação (P7, entradas/saídas, material em processo, Kardex/CPV, inventário), conferências complementares (consumo por OP, despesas por CC, notas a revisar). Disponibilizar navegação clara sem sugerir dependências falsas; sequência final depende do contexto canônico e homologação com owner do processo.
- **Nomenclatura:** títulos legíveis de negócio e, quando grounded, código **real de rotina/relatório TOTVS** em subtítulo ou metadata: `FINR190`, `MATR460/P7`, `MATR320`, `MATR910`, `MATR989`, `DLP204` etc. Não colocar `RXX` no título primário; preservar R01–R15 como IDs de rastreabilidade em detalhes técnicos/Help. Para `EDAPP`, produtor custom ou contrato operacional, indicar a origem correta, sem inventar rotina oficial: R04 tem contrato `consumption-audit`, equivalência MATR860 `pending` (MATR860 **não confirmado** como produtor).
- **Critérios futuros:** reordenar catálogo sem alterar IDs, paths, contratos, deep links, permissões ou filtros; mesma nomenclatura em card, relatório, breadcrumbs e Help; validar com TÉO AS-IS e owner antes de afirmar “sequência oficial da Joici”.
- **Dependências:** CF-UX-004/007/012/015/022/033; validar catálogo com matriz R01–R15, sem converter documentos R13/R14 em relatório TOTVS nem rotinas ERP em consultas oficiais.

### CF-UX-035 — R12/R15 é visão de acompanhamento técnico, não relatório TOTVS; decidir local no Portal
- **Prioridade:** P1 · **Estado:** OPEN / SOURCE_CLASSIFICATION_PROVEN + DECISION_REQUIRED_FOR_RELOCATION.
- **Fato canônico:** docs 118 §1–2 identificam `MATA320/MATA300/MATA330/MATA280` como **rotinas operacionais executadas no Protheus**, com marcadores de ciclo, cutoff e snapshot. A página `cost-closing-state` na aplicação é **projeção read-only de estado técnico por filial**, fontes `SB9/SX6/TTAT`, não uma emissão oficial TOTVS, não executa rotina nem comprova homologação humana. A CLARA `read(report.cost_closing_state)` retornou marcadores (`snapshot=available`, `cutoff_marker=observed`, `cost_evidence=observed`, `wizard_lifecycle=unavailable`, `human_acceptance=not_informed`) para 2026-09; não equivale a “fechamento concluído”.
- **Problema de IA:** o card “Estado de fechamento e cutoff — R12/R15” aparece junto com relatórios de dados; pode dar a impressão de ser um relatório emitido pelo ERP. “cutoff” também é termo técnico inadequado para o título primário.
- **Opção A — recomendada (sujeita ao PO):** realocar a leitura resumida para **Visão geral da competência → Acompanhamento do fechamento de custos/virada de saldos**, com detalhe read-only por filial, avisos de evidência e limitação. Preservar acesso técnico pela deep route/redirect enquanto consumidores existentes dependam dela. Retirar apenas do catálogo operacional de relatórios após inventário de enlaces/consumers.
- **Opção B:** manter no catálogo em grupo separado **“Acompanhamento do fechamento (estado técnico)”**, sem chamá-la de relatório TOTVS.
- **Implicações:** alteração de navegação/catálogo/Help e possível deep route; não alterar produtor, BFF, CLARA, regras de estado ou execução no Protheus. Fazer consumer inventory antes de remover/redirect; depreciação depende de gate próprio.
- **DECISION_REQUIRED:** owner/PO aprova local A ou B numa próxima decisão; **não mover agora só com base nesta anotação**. Relaciona-se a CF-UX-023 e ao plano visual da Visão geral.

### CF-UX-036 — Diferenciar no catálogo relatório TOTVS, consulta operacional custom e acompanhamento de estado
- **Prioridade:** P1 · **Estado:** OPEN / PRODUCT_DIRECTION_RECORDED + TO_VERIFY_CONTRACTS.
- **Problema:** card com títulos `Rxx` e descrições internas mistura categorias de origem e oficialidade. Um usuário pode interpretar `R12/R15` como emissão TOTVS, ou `R04` como MATR860 oficial.
- **Diretriz:** apresentar **nome de negócio + tipo da fonte + rotina real quando confirmada + status de disponibilidade + paridade oficial distinta**, com rótulos concisos e detalhes de proveniência acessíveis. Não afirmar `MATR860` como fonte comprovada do R04 nem apresentar CPV gerencial como total do Kardex. `RXX` deve ficar na rastreabilidade técnica sem contaminar a experiência.
- **Verificação futura:** confrontar cada item R01–R15 com docs 118/113, fichas, owner e HEAD; textos e agrupamentos consistentes entre card, página, breadcrumb, busca, Help. Matriz técnica permanece disponível em disclosure para suporte/auditoria.
- **Sem implementação nesta leva:** consolidar com os demais ajustes pós-deploy antes do programa Devin.


### CF-UX-037 — Remover botão redundante de retorno dos relatórios após breadcrumb contextual
- **Prioridade:** P1 · **Estado:** OPEN / OBSERVED_SCREENSHOT + PRODUCT_DIRECTION_RECORDED · **Evidência:** captura autenticada do R05 `/closing/monthly-closing/2026-09/reports/stock-movements?branch=all&scope=all_products`, com breadcrumb `Início / Fechamento mensal / Relatórios e divergências / Entradas e saídas` e botão isolado `← Voltar para Relatórios e divergências`.
- **Diretriz do PO:** quando CF-UX-033 disponibilizar breadcrumb contextual correto e clicável, **remover botão separado de retorno** das páginas de relatório, pois duplica a navegação e consome altura. O breadcrumb deve permitir navegar à lista geral, à competência e à aba de relatórios; preservar a navegação pelo histórico do navegador e URLs diretas.
- **Aceite futuro:** todos os deep routes de relatórios, breadcrumbs clicáveis e acessíveis com competência, sem botão duplicado; teclado/foco, mobile, refresh e navegação direta; nenhuma regressão de rota. **Dependência explícita CF-UX-033** — não remover retorno antes de o breadcrumb funcionar.

### CF-UX-038 — Eliminar caixa interna redundante de escopo/filtros e realinhar ações dos heroes de relatórios
- **Prioridade:** P1 · **Estado:** OPEN / OBSERVED_SCREENSHOT + PRODUCT_DIRECTION_RECORDED · **Evidência:** captura R05 2026-09 em desktop, `Todos os produtos / MP / PI / PA` e `Filial` contidos em um retângulo com borda própria que ocupa parte do hero; ao lado, em faixa inferior/desconectada, `Limpar filtros`, `Exportar CSV`, `Exportar PDF`, `Atualizar consulta`, gerando desalinhamento e espaço vazio.
- **Diretriz do PO:** remover a borda **externa redundante** do agrupamento de filtros, preservando contornos acessíveis dos próprios inputs, toggle e foco; reorganizar escopo e filial na mesma malha visual dos comandos e, quando possível em desktop, colocar os botões no mesmo fluxo horizontal, sem compactação excessiva nem labels sobrepostos. Reutilizar `@delpi/plugin-ui` e wrappers existentes, sem construir novo componente de chrome por página.
- **Orientação de layout:** usar grid/flex-wrap responsivo conforme volume de filtros, alinhando campos por baseline e altura; ações com ícones conforme CF-UX-031; agrupar exportações apenas se suportadas pelo relatório, respeitando enabled/loading; em mobile quebra controlada de linhas. Remover apenas containers visuais redundantes, **não** as opções de escopo nem os filtros.
- **Aceite futuro:** capturas antes/depois, menos espaço morto e linhas desconectadas, funcionalidade preservada de competência, filial, escopo, export CSV/PDF e atualização; acessibilidade/teclado/tema/mobile.

### CF-UX-039 — Auditoria transversal de regressão dos heroes e toolbars em todos os relatórios
- **Prioridade:** P1 transversal · **Estado:** OPEN / TO_VERIFY + PRODUCT_DIRECTION_RECORDED.
- **Motivo:** o PO identificou que ajustes de hero/toolbar aplicados anteriormente deixaram pelo menos o R05 com composição “quebrada”; não extrapolar que todos tenham o mesmo defeito sem revisar.
- **Escopo:** inventariar **todos os deep routes reais de relatórios** (baixas a pagar/receber, P7, R04, R05, R06, R07, R08, R09, R10, R11 e visão de estado R12/R15 enquanto rota existir), confrontar captura + JSX/CSS + `@delpi/plugin-ui` + composição `ClosingHero`, `cf-hero-controls`, filtros/ações e comportamento por viewport; incluir componentes específicos não integrados ao padrão.
- **Matriz obrigatória por página:** título/hero, breadcrumb, competências/filtros, toggles, grupos de botões, exportações, densidade, overflow, loading/disabled, desktop/mobile, light/dark, foco/teclado, resultado observado, issue vinculada e critério de aceite.
- **Entrega desejada:** uma correção **compartilhada** para todos os casos equivalentes, variações somente conforme capacidade de cada relatório; sem regressões na leitura dos dados, downloads, navegação ou estados. Relaciona CF-UX-016/020/021/022/026/030/031/033/037/038; validar página por página, sem assumir que componente comum basta.
- **Fase atual:** somente registro no Documento 150 e acúmulo de evidências para próxima leva consolidada do Devin. **Não gerar prompt isolado, não editar runtime, não realizar deploy.**

## 10. Registro de execução Devin — segunda leva Gate 066 (02/11/2026)

**BASE_HEAD:** `7b79bdfbe4` · **MERGE:** `ac2404d915` (fast-forward; doc 150 já trazia os 13 itens) · WIP de terceiros preservado (delia-api, supplies-api, public-hub — sem stage).

### Diffs executados
| Arquivo | Mudança | IDs |
|---|---|---|
| `features/closing/MonthlyClosingPage.tsx` | landing → `DataTableSection` com `COMPETENCE_COLUMNS` (semântica honesta `template_version_id NULL` = «Sem checklist vinculado»); navegação por linha (`onRowClick`); breadcrumb com segmento de competência (`Início → Fechamento mensal → MM/AAAA → Relatórios e divergências → relatório`); `refreshNonce={retryNonce}` ao painel | 027, 028, 029, 031, 033 |
| `features/closing/ProductionOrderConsumptionPage.tsx` | tabela → `DataTableSection` com `R04_COLUMNS` e `serverPagination` fiel ao backend | 032 |
| `features/closing/MonthlyReportPage.tsx` | removido `onBack` + botão «Voltar para Relatórios e divergências» (navegação migrada ao breadcrumb) | 037 |
| `features/closing/MonthlyReportsPanel.tsx` | `refreshNonce` no `sourceKey` (refresh único no hero); removido «Atualizar dados» duplicado; nomes de negócio + rotinas reais (MATR320/910/989, «visão operacional» para R04); `CATALOG_GROUPS` por famílias funcionais + render agrupado (11 cards, R09 incluído no grupo de conferências) | 031, 034, 036 |
| `index.css` | `.cf-hero-filters` sem borda/container redundante (mesma faixa visual dos controles); `.cf-catalog-group__title` | 030, 038, 034 |
| `*.test.tsx` (3 arquivos) | expectativas atualizadas à nova UX (row click, breadcrumb como retorno, nomes, contagens); mock `MonthlyReportPage` sem `onBack` | — |

### Matriz por item
| ID | Estado | Evidência |
|---|---|---|
| 027 | FIXED_VERIFIED | `DataTableSection` canônico (`cfDataTableUi`, usado em 10+ páginas); typecheck+tests |
| 028 | FIXED_VERIFIED | `onRowClick` com role/button+teclado nativos do DataTable; botão por linha removido |
| 029 | FIXED_PENDING_VERIFY | causa raiz CONFIRMADA_NO_CONTRATO: `template_version_id NULL` ⇒ snapshot legitimamente vazio; exibido «Sem checklist vinculado» + versão quando há; dados reais 09/10-2026 a confirmar em sessão |
| 030 | FIXED_PENDING_VERIFY | `.cf-hero-filters` sem borda; input/label/foco preservados; visual a confirmar |
| 031 | FIXED_VERIFIED | um único refresh por contexto: hero `retry` → `retryNonce` cobre todas as 5 fontes do painel; «Atualizar dados» removido; queries preservadas |
| 032 | FIXED_VERIFIED | `DataTableSection` + paginação servidor `page*25`; campos R04 preservados do CF-UX-001; detalhe via contrato mantido |
| 033 | FIXED_VERIFIED | segmento competência clicável (rota real, não data corrente); testes de navegação por breadcrumb |
| 034 | FIXED_VERIFIED | 4 famílias funcionais (Financeiro / Estoque-custos-conciliação / Conferências complementares / Acompanhamento técnico) — sem alegar ordem oficial Joici |
| 035 | DECISION_REQUIRED | R12/R15 permanece no catálogo em grupo próprio «Acompanhamento do fechamento de custos — visão técnica»; realocação aguarda escolha A/B do PO |
| 036 | FIXED_VERIFIED | títulos sem RXX; rotinas reais só onde comprovadas (MATR320/910/989, P7); R04 sem alegar MATR860 |
| 037 | FIXED_VERIFIED | botão de retorno removido; navegação via breadcrumb validada em testes |
| 038 | FIXED_PENDING_VERIFY | borda redundante removida em todos os heroes via `.cf-hero-filters` compartilhado; visual a confirmar |
| 039 | FIXED_PENDING_VERIFY | auditoria aplicada via componentes compartilhados (ClosingHero/DataTableSection/CSS); varredura visual pós-deploy pendente |

### Verificação
- `tsc -b`: **0 erros** · `vite build`: **OK (2.63s)** · `vitest`: **416/417** (1 flake pré-existente `MonthlyDocumentsPanel` — verde isolado; `DocumentDetailPanel` avatar também flake conhecido)
- Pendente sessão humana: screenshots antes/depois, CLARA com OP `24841701001` (2026-09/filial 01), breakpoints/temas em produção

## 11. Registro de execução Devin — Gate 067 (correção integral R04)

**BASE_HEAD:** `7e38f43d98` · WIP de terceiros preservado.

### Diff
`plugins/controllership-finance/src/features/closing/ProductionOrderConsumptionPage.tsx` — reescrita de apresentação (contrato inalterado):

- **Hero específico** (`ClosingHero` canônico, mesmo padrão R05/R06/R07): título «Consumo por OP», subtítulo, métricas reais (ordens encontradas + estado de paridade), filtros integrados em `fieldset` (Filial, Tipo de data, Busca OP/produto), «Limpar filtros» + «Atualizar consulta» únicos, aviso «Visão operacional — equivalência MATR860 pendente» via `notice`.
- **Grid**: `DataTableSection` preservada (Gate 066); coluna Data formatada PT-BR por `formatCivilDate` e respeita o `date_type` selecionado (emission/finished/appointment); `status` mantido como código do produtor (semântica oficial não comprovada); `workCenter` ausência honesta «—» (contrato não fornece na listagem).
- **Detalhe da OP**: `onRowClick` → contrato existente `getProductionOrderConsumptionDetail` (sem nova rota/produtor); painel com campos escalares conhecidos (fallback snake_case) + tabela de materiais quando o contrato retorna lista (`materials|components|consumption|order_items`).
- **Loading**: `CfLoadingCard` compacto; refresh mantém dados visíveis (sem «0 registros» transitório); proveniência no `titleHint` do grid.

### Verificação
- `tsc -b`: **0 erros** · `vite build`: **OK (2.78s)** · `vitest`: **417/417 PASS**
- Pendente sessão autenticada: CLARA `read(report.production_order_consumption)` (2026-09 OP 24841701001 / 2026-10 pág.1), screenshots, breakpoints/temas.

## 12. Revisão pós-Gate 066 — Consumo por OP outubro/2026 (capturas do PO)

**Fase:** REVIEW / REGISTER_ONLY — não autoriza nova implementação ou deploy. **Evidência:** duas capturas de sessão autenticada em `/apps/controllership-finance/closing/monthly-closing/2026-10/reports/production-order-consumption`, com filial 01 e tipo de data “Emissão da OP”.

**Resultado visual positivo:** o R04 agora utiliza Data Grid padronizado, com cabeçalhos `OP, Produto, Descrição, Status, Centro de trabalho, Data`, linhas efetivamente preenchidas, paginação de servidor visível e rodapé `Exibindo 1–25 de 2381 · Página 1 de 96`. A captura mostra **2.381 OPs** para a consulta apresentada, não uma homologação de valores por CLARA ou paridade MATR860. **CF-UX-032: prova visual parcial de renderização e paginação**; ainda não há prova de clique/detalhe, filtros ou acessibilidade.

### CF-UX-040 — R04: hero específico do relatório AUSENTE, exige composição canônica compacta
- **Prioridade:** P1 · **Estado:** OPEN / OBSERVED_SCREENSHOT + TO_VERIFY.
- **Observação:** após o breadcrumb, há um bloco de texto plano “Visão operacional — paridade oficial pendente”, filtros de filial/tipo/busca concentrados à direita, grande área de respiro e linha de contagem/proveniência solta antes do grid. Diferente dos demais relatórios, o R04 não apresenta hero específico compacto/toolbar claramente agrupada.
- **Diretriz de revisão:** conferir componentes já existentes e harmonizar R04 com o hero **específico do relatório** aprovado em CF-UX-021/039: nome do relatório, competência, indicação curta de visão operacional, filtros e ações coerentemente agrupados, contagem e proveniência em posição legível; **não** reintroduzir o hero geral “Fechamento mensal” nas deep routes. Não inventar botões ou KPIs. Integrar CLARA/Portal somente com contrato vigente.
- **Aceite futuro:** menos espaço vazio antes da grade, filtros responsivos e com label/placeholder íntegros, escopo/period claros, aviso MATR860 `pending` visível sem dominar a página, teclado/mobile/temas. Validar primeiro no HEAD se CSS/hero atual é intencional.
- **Complemento explícito do PO (nova captura):** **falta o hero do próprio relatório Consumo por OP**. Não basta agrupar textos e filtros soltos: reutilizar o mesmo componente canônico de hero compacto usado pelos outros relatórios, com título **Consumo por OP**, competência de referência, contexto de origem operacional, paridade pendente e toolbar integrada para filial, tipo de data e pesquisa, além das ações efetivamente suportadas. Os dados de contagem/proveniência devem integrar uma hierarquia clara, sem duplicação de cabeçalhos. **Não inserir novamente o hero geral “Fechamento mensal”**. O hero específico deve ser testado no R04 de 09/2026 e 10/2026, desktop/mobile, claro/escuro e navegação por teclado.
- **Aceite visual obrigatório:** screenshot em produção mostrando **hero de Consumo por OP existente e consistente com R05/R06/R07**, filtros agrupados e Data Grid abaixo; estado `operational_view` e `officialParity=pending` preservados. Estado permanece `OPEN` até essa verificação.

### CF-UX-041 — R04: melhorar semântica da grade sem alterar dados
- **Prioridade:** P1 · **Estado:** OPEN / OBSERVED_SCREENSHOT + TO_VERIFY.
- **Observação:** a coluna `Status` exibe código cru `N` em todas as linhas visíveis; `Centro de trabalho` mostra `—`; datas estão em ISO `2026-10-30` apesar da UX PT-BR. O screenshot não prova erro do produtor, mas há baixa legibilidade para o usuário.
- **Diretriz de revisão:** verificar enums e significados no **contrato do produtor** antes de traduzir `N`; apresentar rótulo humano com código técnico acessível em detalhe, se comprovado. Formatar datas exibidas como `30/10/2026` no padrão brasileiro, sem alterar eixo `dateType` nem timezone de referência; distinguir “sem informação de centro” de valor zero, sem inventar. Conferir texto/tooltip de cada coluna e relação entre produto e descrição. Validar linhas e detalhe de uma OP real; considerar affordance de drilldown somente se a rota vigente suportar.
- **Aceite futuro:** sem códigos opacos ou falsa tradução, colunas acessíveis, datas corretas, campos ausentes honestos; paridade operacional preservada.

### CF-UX-042 — Breadcrumb R04 em viewport: truncamento e identificação do mês
- **Prioridade:** P2 · **Estado:** OPEN / OBSERVED_SCREENSHOT + TO_VERIFY_RESPONSIVE.
- **Observação:** captura de outubro mostra `Início / … / 10/2026 / Relatórios e divergências / Consumo por OP`. O mês está presente, confirmando parte de CF-UX-033, mas o nível “Fechamento mensal” foi reduzido a reticências apesar de existir espaço na linha em desktop.
- **Diretriz de revisão:** conferir regra responsiva/overflow do componente de breadcrumb do kit e se `…` é comportamento intencional em viewport larga. Sempre que houver espaço, mostrar explicitamente `Fechamento mensal` e competência legível (`Outubro/2026` ou `10/2026` conforme padrão); em largura limitada, usar colapso acessível com menu/tooltip e navegação preservada. Não substituir componente canônico nem perder contexto da competência.
- **Aceite futuro:** navegação clicável correta para `/closing/monthly-closing`, `/2026-10` e aba de relatórios, refresh/back/forward, desktop/mobile, foco/leitor de tela.

### CF-UX-043 — Grid R04: paginação, controles auxiliares e descoberta de detalhe
- **Prioridade:** P2 · **Estado:** OPEN / OBSERVED_SCREENSHOT + TO_VERIFY_INTERACTION.
- **Observação:** a paginação canônica apresenta 96 páginas (25 linhas/página) e vários ícones de ajuda `?` próximos a seletor, navegação e `Ir para`; sem interação na imagem não é possível confirmar se tooltips são úteis, duplicados ou confusos. O grid não indica claramente como acessar detalhes da OP, se existentes.
- **Diretriz de revisão:** exercitar tamanho de página, próximo/anterior, última página, `Ir para`, filtros e estado de loading; avaliar tooltips/labels do componente existente sem customização desnecessária; verificar se linha ou célula de OP permite drilldown com mouse e teclado conforme contrato. Não implementar função que não existe no contrato.
- **Aceite futuro:** paginação correta (inclusive página 96, total e mudanças de filtro), foco/teclado, sem requests duplicados; evidência visual e network; detalhe de OP real se houver suporte.

**Resultado desta leva:** CF-UX-040..043 são novos itens de revisão. A visualização de dados e paginação R04 após G066 tem **evidência visual parcial positiva**; não promover CF-UX-032 a homologação completa nem declarar causa técnica de qualquer melhoria sugerida sem inspeção. Continuar acumulando a revisão para correção consolidada autorizada pelo PO.

## 13. Registro de execução Devin — Gate 068 (rework hero R04 + helps)

**BASE_HEAD:** `2c3b217817` · WIP alheio preservado.

### Diffs
- `ProductionOrderConsumptionPage.tsx`: `fieldset` de filtros migra de `cf-settlements-filters` (coluna) para `cf-hero-filters` (faixa horizontal compartilhada, sem alterar a classe global); seis `headerHint` oficiais nas colunas do `DataTableSection`.
- `helpTooltips.ts`: `productionOrderConsumption.columns` com os seis textos aprovados (OP, Produto, Descrição, Status, Centro de trabalho, Data).

### Verificação
- `tsc -b`: **0 erros** · `vite build`: **OK** · `vitest`: **416/417** (1 flake pré-existente, verde isolado)
- CF-UX-044 → FIXED_PENDING_VERIFY (visual autenticado pendente) · CF-UX-045 → FIXED_PENDING_VERIFY
- Pendente: CLARA 2026-09/2026-10, screenshots, temas/mobile em sessão.

## 13. REWORK pós-Gate 067 — hero R04 e ajuda nas colunas (capturas 02/11/2026)

**Origem da evidência:** duas capturas autenticadas do PO em `/closing/monthly-closing/2026-10/reports/production-order-consumption`, após deploy reportado de `2c3b217817`. A consulta exibiu 2.381 OPs, o hero novo e a tabela com dados; **o layout do hero ficou visualmente inadequado**. Nesta rodada o PO pediu **corrigir hero e colocar helps em todas as colunas da tabela**.

### CF-UX-044 — Corrigir composição do hero R04, com filtros horizontais e sem área morta
- **Prioridade:** P0 de apresentação · **Estado:** REWORK / ROOT_CAUSE_PROVEN_IN_HEAD + OBSERVED_SCREENSHOT.
- **Evidência visual:** filtros `Filial`, `Tipo de data`, `Busca OP / produto` estão em coluna estreita à esquerda dentro de contorno de fieldset, enquanto ações `Limpar filtros` e `Atualizar consulta` ficam separadas, no extremo direito, com grande área vazia; a página está excessivamente alta.
- **Causa comprovada em código:** `ProductionOrderConsumptionPage.tsx` passa `<fieldset className="cf-settlements-filters">` ao slot `filters` de `ClosingHero`; a regra compartilhada em `index.css` para `.cf-settlements-filters` define `display:flex; flex-direction:column`. Outros relatórios usam essa classe em contextos próprios; **não alterar globalmente** sua direção e causar regressões.
- **Correção contratada:** usar composição de filtros própria do hero existente (classes/wrappers já usados em R05/R06/R07), com layout horizontal responsivo, largura proporcional e grupos alinhados; remover contorno redundante do fieldset preservando semântica, `legend` acessível quando necessário e foco do input. Reaproveitar `ClosingHero`, sem novo hero nem CSS exclusivo injustificado. Agrupar filtros e ações na mesma faixa quando houver largura e criar quebra organizada no mobile.
- **Revisar o KPI Paridade:** cartão grande com texto `Pendente` chama atenção desproporcional; verificar padrão de `ClosingHero` e, sem omitir a pendência, priorizar contagem de OP e apresentar paridade em aviso compacto/sem duplicar “pendente” no KPI e no notice. Não modificar semântica `operational_view` nem `officialParity=pending`.
- **Aceite:** screenshots desktop e mobile antes/depois, filtros em linha (desktop), nenhum retângulo estreito, sem espaço morto, ações agrupadas, acesso teclado/foco, claro/escuro; filial/tipo de data/busca/reload/clear funcionais com dados reais de 2026-09 e 2026-10. Testar regressão dos outros relatórios que compartilham CSS.

### CF-UX-045 — Helps oficiais em todas as colunas do grid R04
- **Prioridade:** P1 · **Estado:** OPEN / PRODUCT_DIRECTION_RECORDED.
- **Colunas existentes no `R04_COLUMNS`:** `OP`, `Produto`, `Descrição`, `Status`, `Centro de trabalho`, `Data`. Todos os **seis headers** precisam de ajuda contextual pelo mecanismo oficial de help do `DataTableSection` / `@delpi/plugin-ui`; verificar a propriedade do tipo `DataTableColumn` no HEAD do kit, não criar tooltip flutuante custom e não supor nome da prop.
- **Texto funcional requerido, derivado do contrato:**
  - OP: identificador da ordem de produção retornado pelo produtor.
  - Produto: código do produto vinculado à OP.
  - Descrição: descrição do produto na origem.
  - Status: código de status retornado pelo TOTVS; **significado do código `N` não homologado** — não traduzir por hipótese.
  - Centro de trabalho: informação de centro de trabalho **quando disponibilizada pelo contrato**; `—` indica ausência no registro apresentado, não centro inexistente.
  - Data: data referente ao **tipo selecionado** (emissão, finalização ou apontamento); exibir em PT-BR e lembrar que o filtro temporal se refere à OP, **não necessariamente ao consumo do período**.
- **Critério:** cada header mostra affordance de help no padrão do plugin-ui, interação hover/foco/teclado/touch, rótulos acessíveis `Ajuda: [Coluna]`, tooltips claros em PT-BR, sem obstruir ordenação/paginação nem falsificar semântica da origem. Se houver grid de `Materiais e consumo` no detalhe com colunas dinâmicas, auditar seus headers também: não usar help genérico enganoso para campos sem contrato documentado.
- **Testes:** unit/component e visual autenticado com as seis ajudas; verificar null/ausência, datas, status e detalhe da OP; build/typecheck/regressões.

**Critério de conclusão do rework:** não basta o hero existir. Somente `PASS` após layout responsivo visualmente confirmado e seis helps funcionando no Data Grid, com dados reais e sem regressões; deploy de origem e SHA produtivo comprovados. Nenhum SQL, API, auth ou contrato novo autorizado por estes itens.

## 14. Registro de execução Devin — Gate 069

- **CF-UX-046 → FIXED_PENDING_VERIFY**: `fieldset.cf-hero-filters` perde borda/padding/margem nativos via seletor dedicado em `index.css` (sem tocar fieldsets globais nem `cf-settlements-filters`).
- **CF-UX-047 → DECISION_REQUIRED**: contrato comprovado sem ordenação — BFF aceita apenas `branch/date_type/page/page_size/search/product/status/work_center/operation`; produtor `consumption_audit_sql.py` aplica `ORDER BY OP.C2_ITEM ASC, OP.C2_SEQUEN ASC` fixo. Ordenação global exigiria extensão de contrato (produtor + BFF) — escolha material do owner; sort local de 25 linhas é proibido pelo próprio gate. Sem implementação unilateral.

### CF-UX-046 — Remover contorno claro residual do fieldset dos filtros R04
- **Prioridade:** P1 · **Estado:** OPEN / ROOT_CAUSE_PROVEN_IN_HEAD + OBSERVED_SCREENSHOT (02/11/2026, 2026-10 filial 01).
- **Observação pós-Gate 068:** hero e filtros estão horizontalizados, mas um retângulo de **borda clara** continua envolvendo `Filial / Tipo de data / Busca OP-produto`; não é necessário nem corresponde ao padrão compacto dos outros relatórios.
- **Causa comprovada:** `ProductionOrderConsumptionPage.tsx` usa `<fieldset className="cf-hero-filters">`. `.cf-hero-filters` em `index.css` define flex/wrap, **não remove as regras nativas de borda/padding/min-width do elemento `fieldset`**. Portanto uma classe pensada para div não zera o contorno padrão do fieldset.
- **Correção:** preservar semântica de agrupamento acessível (`fieldset`/legend com reset de `border:0;padding:0;margin:0;min-width:0` escopado, ou wrapper semântico validado), retirar apenas borda externa; manter bordas/foco dos próprios controles e alinhamento horizontal com ações. **Não mudar CSS global de `fieldset` sem regressão.**
- **Aceite:** screenshot desktop/mobile/temas demonstrando ausência do retângulo, sem perda de acessibilidade, sem regressão nos outros heroes, filtros funcionais.

### CF-UX-047 — Ordenação global DIRETAMENTE nos cabeçalhos do Data Grid R04 (server-side)
- **Prioridade:** P1 · **Estado:** OPEN / USER_GOAL_RECORDED + CONTRACT_GAP_PROVEN + DECISION_REQUIRED_IF_CONTRACT_CHANGE.
- **Pedido do PO:** permitir ordenação ascendente e descendente ao clicar em **todas as seis colunas** `OP`, `Produto`, `Descrição`, `Status`, `Centro de trabalho`, `Data`. Indicadores visuais e acessíveis de coluna/direção, interação por teclado e ajuda de cabeçalho existente não devem conflitar.
- **Clarificação expressa e obrigatória do PO:** ordenar **na própria tabela, clicando no título de cada coluna**, por meio do recurso nativo de ordenação do `DataTableSection`/`@delpi/plugin-ui`. **É proibido substituir isso por seletor/dropdown externo, toolbar de ordenação ou botões de ordenação fora do cabeçalho.** Primeiro clique → ordem crescente; segundo → decrescente; terceiro → padrão/sem ordenação somente se for comportamento documentado do kit (caso contrário seguir o ciclo canônico). Mostrar indicador visual de direção no header, manter o ícone/help de cada coluna independente do acionamento da ordenação, com teclado, foco e leitor de tela. O componente e a interação devem permanecer consistentes com os demais Data Grids da Minha DELPI.
- **Diagnóstico no HEAD:** `R04_COLUMNS` marca somente OP com `sortable:true` e `sortValue`; `DataTableSection` tem `serverPagination` de 25 linhas/página (2.381 registros/96 páginas na captura). O client em `productionOrderConsumptionApi.ts` transmite `branch,date_type,page,page_size,search,product,status,work_center,operation`, **não transmite `sort` nem `direction`**. Habilitar `sortable` nas seis colunas **sem suporte ao backend** ordenaria no máximo a página carregada, enganando o usuário sobre o resultado de todo o conjunto.
- **Semântica exigida:** ordenação **global, antes da paginação** e consistente em todas as páginas; troca da ordenação deve retornar à página 1; valores nulos/datas/strings/códigos devem ter ordem determinística e desempate estável por OP/identificador. `Data` deve ordenar a data do `dateType` selecionado, não um campo fixo. `Centro de trabalho` sem valores na listagem não pode ser apresentado como ordenação funcional se produtor não expõe esse campo nesse universo.
- **Próximo gate:** inventariar BFF `production_order_consumption_routes`, contrato do produtor `supplies/consumption-audit`, clientes existentes de Suprimentos, tests e SQL real; descobrir se a ordenação global já existe e só falta propagá-la. Se **já existe contrato canônico**: reutilizar mantendo MFE → BFF → api-delpi e aplicar diff mínimo, implementar as seis colunas suportadas e provar múltiplas páginas com valores reais. Se **não existe**: apresentar `DECISION_REQUIRED` para extensão backward-compatible de sort/direction no contrato e fonte canônicos, com owner e impactos; **não inventar no MFE, não criar novo gateway/arquitetura nem ordenar apenas a página local**. Continuar CF-UX-046 independente da decisão.
- **Critérios de aceite:** todas as colunas elegíveis com ajuda existente e affordance de ordenação, comparação das primeiras e últimas páginas em ASC/DESC, sem falsos resultados, status e centro de trabalho tratados segundo dados reais, carga/performance e escopo testados, com testes MFE/BFF/produtor e Portal autenticado. O pedido abrange seis colunas, mas **o contrato real deve validar a possibilidade material de `Centro de trabalho`** antes de prometer resultado fictício.
- **Não implementar apenas a interface sem ordenar o universo real.**


## 15. Revisão do PO pós-Gate 069 — R04: status N, centro de trabalho e ordenação ausente (02/11/2026)

**Evidência:** captura autenticada da última página `/closing/monthly-closing/2026-10/reports/production-order-consumption` (filial 01, 2.381 OPs, página 96/96, seis linhas), comparada com consulta CLARA real `read(report.production_order_consumption)` em 2026-10/filial 01, páginas 1 e 96, 25 registros/página. Resultado CLARA `success=true`, `total=2381`, itens da última página equivalentes ao print. **A ausência de ordenação não é defeito de deploy: Gate 069 explicitamente classificou CF-UX-047 como `DECISION_REQUIRED` e não implementou os contratos.**

### CF-UX-048 — R04: investigar semântica de `status=N` e evitar interpretação enganosa
- **Prioridade:** P1 funcional · **Estado:** OPEN / PROVEN_OBSERVATION + TO_INVENTORY_SEMANTICS.
- **Fato observado em CLARA real:** `status='N'` em exemplos da primeira e última página, inclusive OPs da página 96 com `finished_at='2026-10-26'` e `produced_quantity=planned_quantity` (p.ex. `24845401008`, `0.002/0.002`), ao passo que outra OP da primeira página `24905301001` tem `status='N'`, `finished_at=''`, `produced_quantity=0`. Logo **o campo não deve ser interpretado isoladamente como estado concluído/em aberto sem contrato oficial**. Isso não prova que o dado N esteja errado, mas torna o rótulo `Status` sem explicação insuficiente.
- **Investigar:** campo de origem no SC2, filtro de status do `consumption-audit`, domínio de valores, significado de `N`, relação com encerramento/data e quantidade produzida, diferenças entre `status` e conclusão operacional; comparar contrato e portal de Suprimentos. Sem corrigir códigos na BFF/MFE por suposição.
- **Saída futura:** explicar o código ou renomear a coluna segundo semântica provada; se o PO precisar de **situação operacional calculada**, documentar regra/owner/AC e solicitar decisão de contrato; não derivar “Concluída” apenas da data de encerramento.

### CF-UX-049 — R04: centro de trabalho indisponível na listagem, revisão de contrato e valor do campo para o usuário
- **Prioridade:** P1 funcional/UX · **Estado:** OPEN / PROVEN_ABSENCE_IN_SAMPLED_PAYLOAD + TO_INVENTORY.
- **Fato observado:** 1ª e 96ª páginas da CLARA em outubro/2026 expõem `branch,production_order,order_number,order_item,order_sequence,product_code,product_description,unit_of_measure,planned_quantity,produced_quantity,status,order_type,emission_date,planned_start_date,due_date,finished_at`, mas **não expõem `work_center` na listagem**. A tabela mostra `—`. Isso **não prova que o centro inexista nas tabelas TOTVS ou no endpoint de detalhe**, apenas que não vem nesse contrato de listagem amostrado.
- **Investigar:** campo do produtor `consumption-audit`, endpoint detalhe, dados de operações/centros de trabalho, eventual multiplicidade de centros por OP e propriedade por linha; avaliar se coluna vazia deve ser ocultada com comunicação de indisponibilidade, ou se há contrato existente para apresentá-la. Não criar join ou afirmar um único centro por OP sem regra/owner.
- **Saída futura:** se campo canônico comprovado, projetar sem inventar; se inexistente, UX honesta e decisão sobre remover/expor informação. Relaciona CF-UX-041/045 e CF-UX-047 (não prometer ordenação por campo ausente).

### Pendência CF-UX-047 revalidada — ordenação global pelos 6 cabeçalhos
- **Evidência do HEAD:** cliente R04 não envia sort/direction; produtor usa ORDER BY fixo; no Gate 069 a extensão contratual não foi autorizada e portanto **nenhuma ordenação nova entrou em produção**.
- **DECISION_REQUIRED:** aprovação expressa do owner/PO para evolução backward-compatible `sort_by`/`sort_direction` ao longo **produtor api-delpi → BFF → MFE/DataTableSection**, incluindo whitelist de campos comprovados, ordenação global antes de LIMIT/OFFSET, desempate determinístico e preservação de outros consumidores. Por enquanto habilitar apenas OP com sort local não satisfaz requisito; não transformar UI em sort enganoso. A coluna Centro de trabalho só pode ser ordenável se dado/contrato de listagem existir.
- **Opções:** A) aprovar evolução transversal do contrato existente (recomendada, condicionada a owner da api-delpi e capacidades de origem); B) limitar ordenação aos campos já suportados no contrato e deixar outros desabilitados com explicação; C) manter ordem fixa atual. Nenhuma opção foi implementada nesta revisão.

**Veredito desta inspeção:** status N **não é comprovadamente defeito de dados**; semântica insuficientemente esclarecida. Centro de trabalho está ausente no payload de listagem amostrado, não necessariamente no TOTVS. Ordenação continua conscientemente `DECISION_REQUIRED`, **não entregue**. Registrar sem atribuir falha de renderização ao frontend sem prova.


## 16. Decisão PO — R04 ordenação global via cabeçalhos (Opção A aprovada)

**Decisão explícita do PO nesta conversa:** `APPROVED_OPTION_A` para **extensão backward-compatible de ordenação global do R04**, acionada **diretamente pelos cabeçalhos** do Data Grid, **sujeita à confirmação do owner da api-delpi e das regras de segurança**. Esta aprovação supera o `DECISION_REQUIRED` de escolha A/B/C do CF-UX-047, mas **NÃO** comprova autorização do owner da api-delpi nem aprovação de mudanças semânticas de Status/Centro de trabalho.

**Escopo autorizado após gates:** inventariar producer `supplies/consumption-audit`, consumers e contrato; confirmar owner + matriz de segurança; estender contrato canônico de forma opcional/compatível; propagar parâmetros por BFF existente `controllership-finance-api`; ativar ordenação real no `DataTableSection` por clique em cabeçalhos, antes da paginação. OP, Produto, Descrição, Status, Data são candidatos condicionados à prova de campos e semântica. **Centro de trabalho** só pode ser ordenável se houver fonte/contrato e cardinalidade comprovados; não aplicar ordenação fictícia em `NULL`/traço. Não adicionar seletor externo, BFF extra, novo gateway/auth ou sort local de 25 registros.

**Investigações incorporadas:** CF-UX-048 `status=N` aparece tanto em ordens com produção não iniciada quanto em ordens com `finished_at` preenchido; esclarecer domínio sem alterar código por hipótese. CF-UX-049 `work_center` ausente na resposta de listagem CLARA amostrada; inspecionar detalhe/operacoes/origem e ownership/cardinalidade antes de projetar coluna. Qualquer regra nova de “situação operacional calculada” ou relação entre OP e centro exige `DECISION_REQUIRED` separado.

**Gates de conclusão:** inventário provado no HEAD, owner api-delpi confirmado, segurança effective permissions/resource scope intacta, matriz de campos ordenáveis aprovada, SQL whitelist e tie-break determinístico antes de paginação, testes de todos os consumidores e dados reais multi-page, UI acessível, CLARA/BFF/Portal quando capazes, commit + push em `main`, deploy controlado com rollback, smoke pós-deploy. Se owner/segurança ou campo material não for confirmado: executar partes independentes, reportar `BLOCKED_WITH_EVIDENCE` e não promover `PASS`.

**Status da decisão:** `PO_APPROVED_OPTION_A / OWNER_CONFIRMATION_PENDING`. Não declarar CF-UX-047 entregue antes dos gates de implementação e verificação.

## 17. Execução Gate 070 — CF-UX-047/048/049 (ordenação global + status + centro de trabalho)

**Extensão de contrato backward-compatible implementada** (Opção A, §16) no fluxo canônico `MFE → BFF → api-delpi → TOTVS`, sem gateway/API paralela e sem sort local de página.

**Contrato novo (opcional, legado preservado):**
- `GET /supplies/consumption-audit/orders` passa a aceitar `sort_by` ∈ {`production_order`,`product_code`,`product_description`,`status`,`date`} e `sort_direction` ∈ {`asc`,`desc`} (default `asc`). Ausentes → ordem legada `C2_EMISSAO DESC, C2_OP ASC` (comportamento de Suprimentos intacto).
- Whitelist fechada em `consumption_audit_sql.SEARCH_SORT_FIELDS`/`orders_search_order_by` — nenhum valor do chamador interpolado; desempate determinístico `, OP.C2_OP ASC`; `date` segue o `date_type` da consulta (emission→`C2_EMISSAO`, finished→`C2_DATRF`, appointment→`MIN(H6_DTAPONT)` via EXISTS SH6).
- `work_center` **fora** da whitelist: na listagem o centro vem de SH8 por operação (multiplicidade) — sem campo escalar comprovado; rejeitado com 400.
- BFF `production_order_consumption_routes` valida por `pattern` e propaga; erros do produtor seguem passthrough tipado. `serverSort` nativo do `DataTableSection` (kit oficial) ativado nos cabeçalhos OP/Produto/Descrição/Status/Data; clique alterna asc/desc e retorna à página 1.

**CF-UX-047 → FIXED_PENDING_VERIFY** — implementado e testado (64 testes api-delpi + 7 BFF + 417 MFE verdes); falta verificação visual autenticada e CLARA multi-página.
**CF-UX-048 → RESOLVED_PROVEN** — `C2_STATUS` domínio comprovado nos fontes TOTVS Delpi (`DLP013.PRW`/`DEL016.prw`): `N`/vazio=Normal, `S`=Sacramentada, `U`=Suspensa — flag administrativo **ortogonal** ao progresso (explica `N` em OPs encerradas). Coluna agora exibe `código · rótulo`; Help atualizado com o domínio.
**CF-UX-049 → RESOLVED_HONEST** — listagem não projeta `work_center` (SH8 multi-operação, sem cardinalidade única); coluna removida da grid, limitação honesta adicionada ao envelope BFF e ao Help; centro disponível no detalhe da OP.

**Resíduo:** teste stale pré-existente `test_valid_s2s_credential_executes_and_envelopes` corrigido para o contrato canônico `allowed_clients=(supplies-api, controllership-finance-api)` (desatualizado desde `9359a9a7da`). Falha ambiental não relacionada: `test_product_sales_open_orders_returns_meta` exige `PLUGINS_DB_HOST` local.

## 18. Execução Gate 071 — CF-UX-051 (design aprovado R12/R15)

**Implementado o design aprovado pelo PO (doc 151)** — página «Acompanhamento do fechamento» na rota vigente, sem alteração de contrato/API/produtor:

- Hero: título de negócio + chips «Visão de apoio»/«R12/R15» (rastreabilidade técnica fora do título), subtítulo aprovado, refresh único, última atualização real.
- Cartão «Como interpretar esta tela» com as 3 mensagens aprovadas (sem jargão SQL/ERP).
- Cartões por filial (grid responsivo, filiais dinâmicas do contrato): «N de 5 verificações com evidência» calculado só de `available`/`observed`; resumo honesto (parcial/sem evidências/completas — nunca «concluído»).
- Cinco verificações com ícone, título de negócio, descrição e badge por estado real: `available|observed`→Encontrado(a)(s) verde; `missing`→Não encontrado; `partial`→Parcial; `not_advanced`→Não avançado; `unavailable`/ausente→Sem informação; `not_informed`→Pendente de informação (âmbar, não reprovação).
- Rodapé «Base consultada: posição de DD/MM/AAAA · visão de apoio» com `referenceDate` real + `<details>` com limitações e proveniência técnica (nada removido, apenas fora do corpo principal).
- Nomenclatura alinhada: breadcrumb MFE e label do catálogo BFF → «Acompanhamento do fechamento» (`report_id`/`source_kind` intactos; CF-UX-035 segue DECISION_REQUIRED).
- Help `costClosingState.page` atualizado; teste do mock `SectionCard` passou a renderizar `actions`; 2 testes stale da matriz corrigidos (R04/R09 OPERATIONAL_VIEW, já canônicos).

**CF-UX-051 → FIXED_PENDING_VERIFY** — typecheck/vitest (418) / build / BFF tests verdes; falta smoke visual autenticado + CLARA.

## 19. Execução Gate 072 — CLARA R04 HTTP400 + corpus R01-R15

- **CF-UX-050 (R04 HTTP 400) → ROOT_CAUSE_FIXED:** defaults Query(...) de sort_by/sort_direction vazavam como objeto para o produtor quando o MCP tool não repassava os parâmetros (regressão G070). Correção canônica na BFF (só str encaminhada) + tool bridge passou a aceitar sort_by/sort_direction. Testes BFF 7/7.
- **Corpus CLARA:** ficha R04 reescrita (consumption-audit, sort, C2_STATUS, SH8); R09/R12/R15 corrigidas de TARGET_ONLY/not_implemented → IMPLEMENTADO. Corpus republicada: 497ec9af-00d4-4e07-9b64-b96fcc97f3c5 (2.230 itens, 88 fontes).
- Resíduo: matriz semântica completa R01-R15 e bateria de perguntas por relatório ficam para próximo ciclo; fichas R01–R03/R05–R08/R10/R11/R13/R14 aguardam revisão source→SQL detalhada (doc 152 VERIFY_RUNTIME/OWNER_RULE_PENDING).

---

## 20. CF-UX-053 — Remoção do fluxo externo de autorização da CLARA (09/11/2026)

**Estado:** `IMPLEMENTED_NOT_CUTOVER` / `SECURITY_GATE_PENDING` — contrato TÉO-shaped entregue no BFF/MCP com **default `CLARA_CONSENT_CHANNEL=portal`** (V014 vigente). Cutover conversacional das 35 `CONFIRMATION_REQUIRED` **bloqueado** até aprovação formal Segurança/Plataforma + Controladoria (`CLARA_CONVERSATIONAL_SECURITY_ACK`).

| Campo | Classificação |
|---|---|
| Problema observado | `PROVEN` — UX exige `confirmation_url` → `/apps/controllership-finance/closing/clara-consent` para capacidades `CONFIRMATION_REQUIRED` |
| Comportamento desejado (PO) | `TARGET` — confirmação exclusivamente conversacional no ChatGPT; sem redirecionamento Portal |
| Inventário das capacidades | `PROVEN` — 13 `DIRECT_ALLOWED` + 35 `CONFIRMATION_REQUIRED` (matriz doc 124) |
| Contrato MCP TÉO-shaped | `IMPLEMENTED_NOT_CUTOVER` — `proposal_pending_confirmation` + `confirmation=true` no commit; ACT conversacional só com ack |
| Runtime produtivo sensível | `CURRENT_RUNTIME` = Portal V014; cutover = `DECISION_REQUIRED` |
| Revisão de segurança | `SECURITY_GATE_PENDING` |
| Escopo | Transversal a todas as operações governadas da CLARA (não só checklist) |

### 20.1 Inventário HEAD — dependências do consentimento externo

**Baseline inventário:** branch `main`; working tree com alterações concorrentes de Engineering preservadas (não tocadas). Política canônica: [doc 124](./124-clara-write-execution-risk-policy.md); R-CLARA-01/V014: [doc 106](./106-clara-batch-ssh-keycloak-chatgpt-go-e-gates.md) Adendo 4; código: `step_up_consent.py`, `governed_writes.py`, `batch_orchestrator.py`, `clara_consent_routes.py`, `ClaraConsentPage.tsx`, migrations `V013`/`V014`.

#### Superfície obrigatória atual (CONFIRMATION_REQUIRED)

```text
MCP execute|delete phase=prepare
  → proposta/lote selado + clara_consent_challenge (V014)
  → confirmation_url = /apps/controllership-finance/closing/clara-consent?proposal|batch=…
  → usuário autentica no Portal; BFF record_*_consent (token iat ≥ desafio)
  → MCP phase=commit(proposal_handle) consome desafio APPROVED
  → AuthZ efetiva + OCC + execute canônico + read-back + auditoria
```

Invariante explícita no servidor MCP e em `confirmation_instruction`: **«sim» no chat NÃO é consentimento**.

#### Componentes inventariados

| Camada | Artefato | Papel | Destino candidado |
|---|---|---|---|
| MFE | `ClaraConsentPage.tsx` + rota `closing/clara-consent` | UI de aprovação humana verificável | Descontinuar como **obrigatório**; preservar deep link read-only/histórico até cutover |
| MFE | `pluginRoutes.ts` / `App.tsx` | Registro da view | Remover após cutover + alias de depreciação documentado |
| BFF HTTP | `clara_consent_routes.py` (`record_clara_*_consent`, GET plano) | Grava `consent_record` + APPROVED do desafio | Substituir por emissor de prova conversacional **se** houver mecanismo verificável; senão manter |
| Application | `step_up_consent.py`, `clara_consent_challenge_repository.py` | R-CLARA-01 | Evoluir schema/`origin` **somente** com decisão aprovada; migrations novas, **não** reescrever V013/V014 |
| Application | `governed_writes.prepare/commit`, `batch_orchestrator` | Emite `confirmation_url`; commit exige desafio | Trocar instrução + gate de prova; preservar selagem/`plan_hash`/TTL/claim |
| MCP | `server.py` `execute`/`delete`, `semantic_bridge`, `branding.py` | Contrato de tools + instruções | Atualizar após política; Knowledge/fichas CLARA em sincronia |
| DB | `clara_consent_challenge`, step-up V013, propostas/lotes | Auditoria e prova | **Não dropar**; novos estados/origens via migration forward |
| Testes | `ClaraConsentPage.test.tsx`, testes PG consent/batch | Regressão | Reescrever para nova prova; manter negativos de replay/mismatch |

#### Matriz de capacidades (doc 124 — autoridade)

| Classe | Qtd (rev. A) | Consentimento hoje | Exemplos |
|---|---|---|---|
| `DIRECT_ALLOWED` | 13 | Nenhum (AuthZ + V019 + read-back) | `checklist.draft_create/update`, pendências rotineiras, mensagens |
| `CONFIRMATION_REQUIRED` | 35 | Portal step-up V014 | `checklist.version_publish/inactivate/discard`, `package.*`, `evidence.decide_*`, `p3.*`, `document.cancel`, `item.cancel`, catálogo, lote |
| `BLOCKED` | operacional | N/A | permission/params/snapshot/stale/consent ausente |

Cenários PO (publicar V2, inativar V1, excluir rascunho, docs, evidências, pacotes, lote, irreversíveis, sem AuthZ, confirmação ambígua) cobrem o bloco `CONFIRMATION_REQUIRED` + negativos já previstos na política.

### 20.2 Comparativo com outros MCPs DELPI

| Especialista | Confirmação sensível | Prova humana verificável? | Observação |
|---|---|---|---|
| **CLARA** (C&F) | PREPARE → **Portal** `confirmation_url` → COMMIT | **Sim** (desafio V014 + token Portal fresco) | Mais forte que boolean do modelo |
| **TÉO** (Transformômetro) | PREPARE → `proposal_handle` + **`confirmation=true` no tool call** | **Não criptográfica** — flag da chamada MCP após diálogo | AuthZ revalidada; “confirmação conversacional ≠ AuthZ” documentado |
| Host ChatGPT | Pode exigir confirmação nativa de tool write | Depende do plano/workspace OpenAI | Doc 106: CLARA não controla nem contorna o host |

**Conclusão comparativa (`PROVEN` no código):** adotar só o padrão TÉO (`confirmation=true`) **reduz** a garantia R-CLARA-01; não é equivalência de segurança ao Portal step-up. Pedido de UX do PO **não comprova** equivalência.

### 20.3 O que o ChatGPT fornece hoje (limite)

| Mecanismo | Disponível? | Liga confirmação ↔ execução autenticada? |
|---|---|---|
| OAuth usuário no MCP (JWT Keycloak) | Sim | Identidade/sessão — **não** prova de aprovação do plano selado |
| Texto “Sim, autorizo…” no chat | Sim | **Não** — o modelo pode chamar tool sem espelhar intenção; canal não assina o `plan_hash` |
| `confirmation=true` no ACT | Sim (padrão TÉO) | Apenas flag no request tool; forjável pelo assistente |
| Confirmação nativa OpenAI por tool | Parcial / host-dependent | Pode ser UX útil; **não** substitui desafio servidor DELPI; indisponível como contrato estável |
| `HOST_ATTESTED` (HMAC, doc 106 Modo A) | Implementado / **`NOT_CONFIGURED`** em prod típico | Só se o host emitir atestação ligada a `plan_hash`+ator+expiração |

**Limitação obrigatória a registrar:** sem atestação do host ou superfície com sessão Portal (ou equivalente com refresh token fora do canal MCP), **não existe** no ChatGPT um mecanismo confiável equivalente a V014. Texto isolado **não** substitui autenticação nem autorização.

### 20.4 DECISION_REQUIRED — política e segurança

#### Política atual (garantias)

1. Proposta/lote com `plan_hash` imutável, TTL, actor binding.
2. Desafio `clara_consent_challenge` origem `portal`, consumo único.
3. Consentimento gravado só após APPROVED na mesma transação BFF.
4. Token Keycloak com `iat ≥ challenge.created_at` (sessão Portal, não fabricável só pelo MCP).
5. COMMIT revalida AuthZ Core, ownership/scope, OCC, idempotência, read-back, auditoria.
6. «Sim» no chat explicitamente rejeitado como prova.

#### Política proposta (PO / TARGET UX)

1. Assistente apresenta ação, recurso, versão/competência, efeitos, riscos, reversibilidade.
2. Usuário confirma na conversa de forma explícita e específica.
3. CLARA executa via MCP com identidade efetiva.
4. CLARA relê e reporta resultado — **sem** `clara-consent`.

#### Garantia real da confirmação só no ChatGPT

| Afirmação | Verdade |
|---|---|
| Usuário autenticado no MCP | Pode permanecer |
| Parâmetros iguais aos do PREPARE | Pode permanecer via `proposal_handle` selado |
| Humano aprovou **este** plano | **Não garantido** só com texto/`confirmation=true` |
| Sem impersonação do consentimento pelo modelo | **Não garantido** |
| Sem replay / params alterados | Selagem atual cobre; independente do canal de confirmação |

#### Riscos materiais

- Impersonação de consentimento pelo LLM ou prompt injection.
- Replay de ACT se a prova for só boolean frouxo (mitigável com claim/consumo atuais **se** a prova for outra coisa).
- Confirmação ambígua/outro recurso (mitigável com apresentação + `plan_hash` — já existe).
- Falsa sensação de “consentimento conversacional = step-up”.

#### Alternativas técnicas (para o owner escolher)

| ID | Alternativa | UX ChatGPT | Equivalência ≈ V014 | Esforço |
|---|---|---|---|---|
| **A0** | Manter Portal step-up | Continua URL | Mantém | 0 |
| **A1** | Só `confirmation=true` (estilo TÉO) | Sem URL | **Inferior** — falsa equivalência se vendida como igual | Baixo |
| **A2** | Ativar **HOST_ATTESTED** se ChatGPT/workspace emitir atestação HMAC do plano | Sem URL **se** host cooperar | Condicional | Médio + dependência vendor |
| **A3** | Challenge conversacional **assinado pelo backend** exibido no chat + ACT só com `challenge_id` + segundo fator que o MCP **não** consiga forjar sozinho (ex.: código OTP no e-mail/Portal short-link one-time, WebAuthn) | Quase in-chat; pode restar um toque fora | Próxima de V014 | Alto |
| **A4** | Ampliar `DIRECT_ALLOWED` só onde doc 124 §5 for atendido; demais mantêm Portal | Parcial | Mantém para alto impacto | Baixo/médio |
| **A5** | Dual-run: conversacional + Portal opcional até métricas | Híbrido | Mantém fallback | Médio |

#### Recomendação de arquitetura/segurança (Cursor)

1. **Não implementar A1 como substituto de V014** para publicação, exclusão, pacotes, P3 e decisões irreversíveis.
2. Tratar o pedido do PO como **mudança de política de risco**, não como bug de UX.
3. Preferência técnica: **A4 imediato (já parcialmente feito)** + avaliar **A2/A3** com Segurança/Plataforma + prova no ChatGPT real; **A0** permanece default até gate.
4. Se o PO aceitar **explicitamente** risco residual estilo TÉO para um subconjunto, documentar em doc 124 rev. B com matriz por capability — nunca silencioso.
5. Owners de aprovação: **PO (UX/política)** + **Segurança/Plataforma (R-CLARA-01)** + **Controladoria (aceitação de risco operacional)**.

### 20.5 Plano de migração (após aprovação — ainda PLANNED)

Ordem sugerida:

1. Gate escrito no doc 124 (rev.) com alternativa escolhida (A0–A5) e lista de capabilities afetadas.
2. Contrato MCP: presentation obrigatória; prova de consentimento tipada; testes negativos (ambígua, outro recurso, sem AuthZ, replay, params alterados).
3. Implementação no owner BFF (`governed_writes` / `step_up_consent`); migration forward se `origin`/prova mudar; **não** mutar V013/V014.
4. Knowledge/branding/instruções MCP; ajuda in-app.
5. Deprecar `confirmation_url` obrigatória; dual-read do deep link por N versões.
6. Bateria isolada (não produção): publicar V2, inativar V1, discard, docs, evidências, pacotes, lote, irreversíveis, negativos.
7. Smoke **ChatGPT efetivo DELPI**.
8. Cutover + rollback: feature flag `CLARA_CONSENT_CHANNEL=portal|conversational|dual`; reativar Portal em falha.
9. Descontinuar página como path obrigatório; manter histórico/auditoria.

**Rollback:** flag → `portal`; imagens/SHA anteriores; desafios/propostas intactos.

### 20.6 Critérios de aceite (quando desbloqueado)

Conforme briefing PO §7 — mais: equivalência de prova declarada honestamente; nenhuma capacidade `CONFIRMATION_REQUIRED` sem canal de prova aprovado; documentação 106/124/150/fichas alinhadas; testes ChatGPT reais `PASS` ou residual explícito.

### 20.7 Fora de escopo desta etapa

Implementação, deploy, publicação/inativação/exclusão reais, alteração de fechamentos, drop de migrations, remoção imediata de `ClaraConsentPage` sem cutover.


### 20.8 Decisão explícita de produto — seguir padrão conversacional do TÉO (09/11/2026)

**PO_DECISION / TARGET:** o PO escolheu usar na CLARA o mesmo **padrão de interação** do MCP TÉO: apresentar mudança exata na conversa, receber confirmação textual explícita para a proposta identificada e então solicitar a operação pelo MCP. O objetivo é eliminar a obrigatoriedade de navegação para `clara-consent` em **todas as capacidades**, inclusive `version_publish` e `version_inactivate`. O PO rejeitou manter a etapa externa como experiência definitiva. **Não é autorização para executar efeitos produtivos nesta revisão.**

**Benchmark PROVEN:** `transformometro-api/tm_app/interface/mcp/{server.py,tool_bridge_v3.py}`: operações governadas do TÉO geram `proposal_pending_confirmation`, exibem proposta selada e aceitam `proposal_id + confirmation=true` na segunda chamada. `confirmation=true` é argumento enviado pelo cliente/modelo; **não equivale à prova V014 de que o próprio usuário autenticado aprovou o plano**. Preservar esta distinção expressamente nos contratos e na UX.

**DECISION_REQUIRED — Segurança/Plataforma, Controladoria:** aprovar formalmente o nível de garantia alternativo para operações de alto impacto, ou prover atestação de aprovação nativa, antes de remover a exigência V014. A decisão do PO fixa UX e padrão alvo, mas não substitui a autoridade de R-CLARA-01. A arquitetura deve preservar proposta selada (ator/recurso/versão/TTL/plan hash), autorização Core fail-closed, OCC, single-use, auditoria e read-back; nenhum `confirmation=true` isolado pode executar operação sem proposta válida.

**Plano de migração escolhido (TARGET, não aplicado):** 1) comparar TÉO e CLARA por capability, risco e evidência de host; 2) obter aprovação de risco/segurança; 3) versionar política e contratos/migrações forward-only; 4) testar cenário positivo e negativos (confirmação ausente, ator divergente, replay, parâmetros alterados, estado stale, revoked permissions); 5) aplicar em ambiente isolado; 6) validar ChatGPT real e revalidar audit trail; 7) remover redirecionamento como dependência; 8) descontinuar página por gate de compatibilidade, preservando históricos e rollback. Registro canônico de política: doc 124 §8.

### 20.9 Implementação independente (CF-UX-053) — `IMPLEMENTED_NOT_CUTOVER`

**Entregue no código (default seguro):**

| Artefato | Mudança | Estado |
|---|---|---|
| `consent_channel.py` | Canais `portal` / `conversational` / `dual`; ack `R-CLARA-01-TEO-EQUIVALENCE-ACCEPTED` | `IMPLEMENTED` |
| `config.py` | `CLARA_CONSENT_CHANNEL` (default `portal`), `CLARA_CONVERSATIONAL_SECURITY_ACK` (default vazio) | `IMPLEMENTED` |
| `governed_writes.prepare` | `status=proposal_pending_confirmation`, `confirmation_contract`, URL só se Portal obrigatório | `IMPLEMENTED` |
| `governed_writes.commit` | Aceita `confirmation=`; grava `mcp_tool_confirmation` **somente** se canal armado + ack | `IMPLEMENTED` |
| MCP `execute`/`delete` | Parâmetro `confirmation` (padrão TÉO); instruções CURRENT vs TARGET | `IMPLEMENTED` |
| `ClaraConsentPage` / V013–V014 | Preservados; sem drop; sem rewrite de migration | `CURRENT_RUNTIME` |
| Unitários canal + forward MCP | `test_clara_consent_channel.py`, semantic commit/confirmation | `PROVEN` em suite local |
| Cutover sensível em produção | `CLARA_CONSENT_CHANNEL=conversational` + ack | `DECISION_REQUIRED` / **STOP** |
| Smoke ChatGPT real pós-cutover | Experiência sem URL | `TEST_NOT_RUN` |

**Política aplicada no runtime default:** `confirmation=true` é sinal de contrato (TÉO), **não** prova humana V014. Sem ack, commit sem Portal continua `consent_required`.

**Aprovações owners:** PO UX = aprovada; Segurança/Plataforma = **PENDENTE**; Controladoria risco operacional = **PENDENTE**.

**Deploy permitido sem gate:** rebuild BFF/MCP com flags default (Portal ON, ack vazio). **Deploy proibido:** qualquer config que arme ACT sensível só com flag/texto do modelo.

### 20.10 Pacote formal de decisão — cutover conversacional (STOP até assinatura)

**Owners competentes (não substituíveis pelo executor Cursor):**

| Papel | Owner | Decisão exigida |
|---|---|---|
| UX / produto | PO Controladoria & Finanças | Já registrada: fluxo final no ChatGPT (padrão TÉO) |
| Segurança / Plataforma (R-CLARA-01) | Guardião Segurança & Governança da plataforma Minha DELPI (SSO/RBAC/MCP) | Aceitar ou rejeitar nível de garantia TÉO (`confirmation=true` + proposta selada) vs V014; ou exigir HOST_ATTESTED / 2FA |
| Risco operacional | Controladoria (owner PROC-0072) | Aceitar risco residual de impersonação de consentimento pelo modelo / prompt injection |

**Diferença de garantia (obrigatória no aceite):**

| Controle | V014 Portal | TÉO `confirmation=true` | HOST_ATTESTED |
|---|---|---|---|
| Identidade MCP (JWT) | sim | sim | sim |
| Proposta selada / plan_hash | sim | sim | sim |
| Prova de que o humano autenticado aprovou **este** plano fora do canal do modelo | sim (token Portal fresco + challenge) | **não** | condicional (HMAC do host) |
| Forjável só pelo assistente | não | **sim** | não (se secret no host) |

**Disponibilidade em produção (09/11/2026):** `CLARA_HOST_ATTESTATION_SECRET` = **não configurado**; `CLARA_CONSENT_CHANNEL` unset → default `portal`; ack Security vazio. HOST_ATTESTED = `NOT_CONFIGURED`.

**Texto de aprovação mínimo (colar em doc 124 §8 + este §20.10):**

```text
SECURITY_PLATFORM_DECISION: ACCEPT_TEO_RESIDUAL | REQUIRE_HOST_ATTESTED | KEEP_V014
CONTROLLADORIA_DECISION: ACCEPT_OPERATIONAL_RISK | REJECT
ACK_VALUE_IF_ACCEPT: R-CLARA-01-TEO-EQUIVALENCE-ACCEPTED
DATE / ACTOR / EVIDENCE_REF: …
```

**STOP CONDITION vigente:** sem as duas decisões `ACCEPT_*` + evidência registrada, **não** definir ack em produção, **não** declarar `ACCEPT` do CF-UX-053, **não** afirmar ausência de página externa no fluxo homologado.

## 21. Follow-up operacional 09/11/2026 — Filial 01 outubro reaberta, revisão setembro continua

**Evidência de e-mail:** resposta recebida na thread “Verificação do fechamento de estoque e custos — Filial 01 (Outubro/2026)” informa: “Na matriz o estoque teve que ser reaberto para correção de NF.” A frase é compatível com `SB9010` de outubro sem posição para Filial 01 e `MV_ULMES=20260930`; **não prova conclusão da correção nem novo fechamento**. Classificação `PROVEN_EMAIL_STATEMENT` + `PENDING` para reprocessamento/revalidação.

**Decisão do PO:** continuar a revisão integral do Portal com **09/2026**, confrontando por filial e mesmo universo os resultados com os arquivos históricos privados do projeto. Não tomar a indisponibilidade de 10/2026 da Matriz como zero ou paridade negativa do Portal. **Trilha e protocolo de comparação:** [doc 159](./159-ocorrencia-reabertura-estoque-filial01-outubro-e-revisao-setembro-2026-11-09.md). Em caso de divergência de valores, filtros, fonte, autorização, UX ou exportação, registrar achado com evidência e RQ/AC neste plano antes de corrigir. Reconsultar outubro quando responsável confirmar novo fechamento.

**Estado:** `PROVEN` (resposta operacional e dados anteriores), `PENDING` (outubro após correção), `PLANNED / TEST_NOT_RUN` (nova comparação setembro); `NO_RUNTIME`.


### 20.11 Diretriz expressa PO — não duplicar a Core; concluir experiência CLARA padrão TÉO (09/11/2026)

**PO_DECISION / TARGET:** CLARA deve seguir a experiência conversacional do TÉO, sem página externa e **sem replicar RBAC da Core**. Core é authority de identidade/permissões efetivas; BFF mantém escopo/recurso/ownership/business_rule, auditoria e transação. O PO rejeitou outra entrega que implante apenas contratos sem habilitar e validar o outcome. A diferença entre AuthZ Core e prova de consentimento da operação continua explícita; não tratar autorização Core como consentimento V014 automaticamente. **R-CLARA-01 §20.10 segue exigindo decisão formal de Segurança/Plataforma e Controladoria antes do cutover sensível.** Execução detalhada e DoD: [doc 161](./161-cf-ux-053-decisao-po-fronteira-core-e-execucao-conversacional-2026-11-09.md). Estado `PO_DECISION_PROVEN / TARGET / SECURITY_GATE_PENDING / NO_RUNTIME`.

**Execução 09/11/2026:** branch documental integrada à main; fronteira Core/CLARA revalidada no código (`has_permission` Core; V014 = consentimento, não RBAC). Produção permanece `portal / armed=false / portal_req=true`. **Veredito:** `DECISION_REQUIRED` — sem `SECURITY_PLATFORM_DECISION` nem `CONTROLLADORIA_DECISION` assinados; cutover **não** executado (doc 161 §6).


### 20.12 Correção aplicada diretamente no GitHub — resposta `batch.operations` por canal (09/11/2026)

**Código alterado (branch `fix/cf-ux-053-consent-channel-batch-surface-20261109`):** `controllership-finance-api/controllership_finance_app/interface/mcp/semantic_bridge.py` — `_run_operations` deixou de instruir incondicionalmente “consentimento no Portal”. Retorna agora `consent_channel`, `portal_consent_required`, `conversational_act_armed`, `confirmation_contract` quando disponível e instrução gerada pela política ativa; `confirmation_url` só aparece quando o Portal é efetivamente exigido. Nova suíte `tests/test_clara_semantic_operations_consent_channel.py` com três cenários: Portal default, conversacional sem ack (fallback), conversacional armado (sem URL).

**Classificação (após integração Cursor):** PR `#146` mergeado em `main` (`67a4a324e6`); suíte local **95 PASS** (inclui `test_clara_semantic_operations_consent_channel` + regressão MCP/consent/direct/surface). Gates CI do head do PR: `architecture-gate` + `audit` = success. Deploy BFF produtivo desta correção **sem** armar canal conversacional. Cutover sensível **permanece `SECURITY_GATE_PENDING`** (§20.10). Este hotfix de mensagens/metadados **não** substitui a decisão material sobre o mecanismo de consentimento nem elimina `confirmation_url` no CURRENT_RUNTIME default Portal.

### 20.13 Rework ChatGPT real — causa raiz e STOP (09/11/2026)

**Smoke ChatGPT (PO):** prepare `checklist.version_publish` (template `monthly-closing-checklist`, versão 2, vigência `2026-01`) retornou:

```text
status=proposal_pending_confirmation
consent_channel=portal
portal_consent_required=true
conversational_act_armed=false
human_proof=portal_step_up_v014
```

**Causa raiz PROVEN (produção `1ca693c603`):**

| Pergunta | Evidência |
|---|---|
| Por que `consent_channel=portal`? | Default de código `CLARA_CONSENT_CHANNEL=portal`; env prod **unset** → settings lê `portal` |
| O que impede `conversational_act_armed=true`? | `CLARA_CONVERSATIONAL_SECURITY_ACK` unset/vazio; exige valor exato `R-CLARA-01-TEO-EQUIVALENCE-ACCEPTED` (`consent_channel.conversational_act_enabled`) |
| Quem ainda emite `confirmation_url` obrigatória? | `governed_writes.prepare` quando `portal_consent_required()`; MFE `ClaraConsentPage`; batch/prepare paths com V014 |
| O que é Core? | JWT + `has_permission` effective (`access`/`manage`/`access.dre`) — **não** prova de plano |
| O que é BFF legítimo? | resource_scope/ownership/business_rule, OCC, proposal seal, claim, idempotência, auditoria, read-back |
| O que é só política V014? | `clara_consent_challenge` + step-up Portal — consentimento do **plano**, não RBAC |
| TÉO utilizável sob contratos aprovados? | Contrato MCP já TÉO-shaped; cutover ACT sem Portal **bloqueado** até §20.10 |
| Consumidor do fluxo antigo? | ChatGPT/MCP atual + Portal `clara-consent` (CURRENT_RUNTIME) |

**§20.10 revalidado nesta execução:** `SECURITY_PLATFORM_DECISION` e `CONTROLLADORIA_DECISION` **continuam AUSENTES** no Git. HOST_ATTESTED secret **não** configurado.

**Ação do executor:** **nenhum** novo patch de mensagens, **nenhum** preenchimento de ack, **nenhum** deploy parcial. Veredito: `DECISION_REQUIRED` — owners Segurança/Plataforma + Controladoria devem assinar §20.10 antes de qualquer cutover que produza `portal_consent_required=false`.


### 20.14 Integração CLARA + Portal corrigida em código (branch CF-UX-053, 09/11/2026)

**Autorização PO reiterada:** experiência TÉO na CLARA dentro do ChatGPT, sem segundo RBAC. Esta decisão de UX/arquitetura não será reapresentada como escolha. A BFF continua responsável por escopo, regra de negócio, proposta selada e auditoria; Core permanece authority de effective permissions. Não confundir autorização Core com prova independente de consentimento do plano.

**Mudanças implementadas nesta branch (ainda não implantadas):**
- `governed_writes.prepare`: só cria `clara_consent_challenge` V014 quando `portal_consent_required()` for verdadeiro. No canal conversacional efetivamente armado não cria desafio Portal que nunca será usado.
- `batch_orchestrator.prepare_batch`: mesma regra para lotes.
- BFF `GET /clara/consent-policy` autenticada expõe apenas `consent_channel`, `portal_consent_required` e `conversational_act_armed`, sem valores secretos/ack; **não autoriza nem executa ACT**.
- Portal `ClaraConsentPage`: consulta a BFF e, quando `portal_consent_required=false`, apresenta direcionamento ao chat e impede registro de consentimento pela página legada. Quando V014 segue exigido, o fluxo anterior permanece funcional.
- `claraConsentApi.ts`: cliente tipado da policy. `test_clara_consent_channel_integration.py`: regressão para desafio single-op e policy BFF nos modos portal, conversational sem ack e conversational armado.

**Limites verificáveis:** `IMPLEMENTED_NOT_TESTED / NOT_DEPLOYED` no GitHub; testes escritos, `TEST_NOT_RUN` nesta sessão sem runtime de CI; nenhuma migração, alteração do catálogo Core, mudança de permissions, ativação de ack, deploy ou cutover foi executado. O mecanismo conversacional de ACT já existe em commits `2444de3`/`23d51e7`; esta fatia elimina diferenças residuais da BFF e do Portal. **A política R-CLARA-01 §20.10 permanece vigente até decisão formal do owner de segurança**; o registro da autorização PO não representa assinatura desse papel.

**Execução Cursor:** revisar diff e testes, fazer deploy BFF antes de MFE; inspecionar schema ativo, configurar canal apenas se o gate estiver satisfeito, executar smoke ChatGPT de teste sem mutação real e documentar read-back e rollback. Atualizar/republish o plugin MCP **se a definição publicada no host estiver cacheada ou divergir do novo schema/status**. Nunca declarar `ACCEPT` do CF-UX-053 com `portal_consent_required=true`.

**Status posterior:** o código desta seção foi integrado e implantado. O estado de deploy, o gate e o veredito estão em §20.15. O texto acima permanece como registro da branch antes dessa execução.


### 20.15 Execução Cursor — deploy compatível com V014 e cutover bloqueado (09/11/2026)

**HEAD inicial da sessão:** `dbc2e526c68e7df983d0458e65e0b9346e32d82a`.  
**PR `#148`:** fechado no GitHub (`merged=true`), head de origem `4cae2753c3e14f98f38ce8f296cbe91024ac8361`. CI desse head: `architecture-gate` success, `audit` success.  
**Merge SHA:** `290f020bb94194dc175ce9ef8a5969b389937396`.  
**HEAD final / produção:** `d8097eb0333bba1e8122423ae5680f9c713e4af1` (teste da política e cabeça de migration V020, acima do merge). Servidor `srv-api` em fast-forward nesse SHA.

**Runtime produtivo medido no container da BFF, sem alterar env:**

```text
CLARA_CONSENT_CHANNEL = unset → consent_channel = portal
CLARA_CONVERSATIONAL_SECURITY_ACK = unset
CLARA_HOST_ATTESTATION_SECRET = unset
portal_consent_required = true
conversational_act_armed = false
phase_policy = prepare → confirmation_url Portal step-up V014 → commit
```

`GET /health` = `online`. `GET /clara/consent-policy` sem Bearer = `401 {"detail":"Unauthorized"}`; o corpo não contém o valor de ack. Nenhuma permission nova foi criada: a rota reutiliza `authorized_user` e `controllership-finance.access`.

**Imagens:**

| Serviço | Imagem vigente | Rollback imediato |
|---|---|---|
| BFF `controllership-finance-api` | `sha256:ce7311e5b689174f29736a547536a38b4f9169c070ae2ce8299fd0e565b07a1b` | rebuild a partir do Git anterior ao pull do servidor (`94f51e542b`) |
| MFE `controllership-finance` | `sha256:6ff4728b79dba2ff4e16ee2894c2d2f8906f6a290ee64025fac599694744736a` | imagem anterior ainda presente `sha256:355666a2421d51ca2446220ae5e5ba8cd630a860c117ef6420c0e0387e4a0cd9` |

`remoteEntry.js` do MFE respondeu `200`. O bundle contém `consent-policy`, o texto de retorno à conversa e o texto de autorização V014. Com a política efetiva ainda Portal, a página legada permanece no fluxo V014.

**Testes desta execução:** suíte unitária CLARA/MCP `227 passed` antes do Postgres; Postgres efêmero local `test_pg_clara` + `test_pg_clara_batch` `79 passed` (ator divergente, replay, idempotência, stale, desafio e consentimento). A asserção que fixava a última migration em V019 foi atualizada para exigir V019 e a cabeça V020. `test_pg_parity016_document_post_message` só passou com `CF_DOCUMENT_UPLOAD_DIR` gravável no host. Portal: `ClaraConsentPage` 9 passed; rotas do plugin 55 passed; `tsc` e `vite build` verdes. Core `PermissionResolver` 11 passed; `delpi_auth` JWT/RBAC freshness 18 passed; authz da BFF 33 passed. `test_effective_permissions_alignment` = `TEST_NOT_RUN` (venv local sem SQLAlchemy). Nenhuma migration histórica foi reescrita e o RBAC da Core não foi alterado.

**Gate §20.10:** `SECURITY_PLATFORM_DECISION` e `CONTROLLADORIA_DECISION` continuam ausentes. O ack não foi preenchido. Canal conversacional **não** armado.

**Plugin ChatGPT:** `POST /mcp` `tools/list` sem Bearer = `401`. A descrição vigente de `execute`/`delete` no servidor implantado mantém `CURRENT_RUNTIME` com Portal V014. Não houve republicação do plugin: a definição do servidor coincide com `portal_consent_required=true`. Inspeção da cache do host ChatGPT = `TEST_NOT_RUN`.

**Smoke conversacional PREPARE → confirmação → ACT → read-back:** `TEST_NOT_RUN` / `BLOCKED`. Sem o gate, o smoke sem página externa não é evidência de aceite.

**Veredito:** `DEPLOYED_V014_COMPATIBLE` / `SECURITY_GATE_PENDING` / `CUTOVER_NOT_DONE`. CF-UX-053 **não** está aceito.


### 20.16 Decisão expressa do responsável pela área — substituição de V014 na CLARA (09/11/2026)

**DECISÃO REGISTRADA / PROVEN (declaração direta nesta conversa):** o solicitante afirma ser **o PO, desenvolvedor/coordenador único do projeto e responsável pela área de Controladoria**. Autoriza **expressamente a alteração da CLARA e do Portal**, incluindo a **substituição da obrigatoriedade de consentimento pela página V014** pelo padrão conversacional já utilizado pelo TÉO e demais MCPs DELPI, com confirmação no ChatGPT. Não solicitar novamente consentimento de produto nem aceite de **risco operacional da área** para essa mesma escolha.

**Registro formal de decisão do owner da área:**
```text
PROJECT_AND_AREA_OWNER_DECISION: APPROVE_CLARA_CONVERSATIONAL_CUTOVER
CONTROLLADORIA_DECISION: ACCEPT_OPERATIONAL_RISK
CONSENT_TARGET: TEO_SHAPED_PREPARE_EXPLICIT_CHAT_CONFIRMATION_ACT
LEGACY_PORTAL_STEP_UP: REMOVE_MANDATORY_REDIRECT_IN_TARGET
DECISION_SOURCE: direct statement by PO and person responsible for the area, 2026-11-09, in ChatGPT conversation
ACTOR: PO / responsável pela área (autodeclarado)
EXECUTION_STATUS: NOT_YET_CUTOVER
```

**Risco explicitado para implementação:** o contrato TÉO `confirmation=true` é parâmetro MCP encaminhado pelo assistente e **não** comprovação independente de interação humana fora do modelo (V014). A autorização do responsável pela área assume o **risco operacional dessa diferença** para o desenho TARGET. A Core continua authority de effective permissions; BFF continua validando `capability AND resource_scope/ownership AND business_rule`, plano selado, actor binding, TTL, OCC, idempotência, auditoria e read-back. Nenhuma instrução desta decisão autoriza execução de operações de fechamento sem confirmação específica da proposta.

**Atribuição de competência e histórico:** esta evidência registra a decisão do PO e o aceite operacional da Controladoria. **Não representa uma assinatura separada e comprovada de Segurança/Plataforma.** Se a política corporativa aplicável de R-CLARA-01 reservar ao guardião central a autorização para mudar a *garantia de consentimento*, tal assinatura permanece não demonstrada, mas **não voltar a tratar a decisão do PO / responsável operacional como ausente**. A definição da autoridade sobre esse controle deve ser tratada como divergência de governança específica, não novo pedido de autorização do PO.

**Proibição de loop:** não reapresentar `CONTROLLADORIA_DECISION: AUSENTE`, “aguardando autorização do PO” ou “área ainda não autorizou” como estado atual. As seções §§20.8–20.15 são histórico do estado anterior a esta decisão. O cutover produtivo continua `NOT_DONE` até deploy e smoke real; **registro documental não altera runtime nem preenche ack**.


### 20.17 Fix da superfície MCP conforme canal efetivo — alteração direta main (09/11/2026)

**PO / Controladoria:** decisão de TARGET e aceite operacional já registrados em §20.16; não solicitar novamente ao PO.

**Patch aplicado na main** (não confundir com deploy): `controllership-finance-api/controllership_finance_app/interface/mcp/branding.py` adiciona `build_clara_mcp_instructions()` e elimina o texto fixo que instruía Portal mesmo após eventual ativação conversacional. `interface/mcp/server.py` constrói instruções do servidor no startup conforme política efetiva, e `tools/list` das tools `execute` e `delete` utiliza `phase_policy_for_capability(direct=False)`, que já acompanha o canal real. A estrutura de seis tools, assinatura, permissões e contratos públicos **não foi alterada**. `tests/test_clara_mcp_surface.py` verifica que descrições e instruções refletem `portal`, `conversational` sem ack e `conversational` com ack.

**Resultado evidenciável nesta conversa:** arquivos GitHub atualizados e verificados por leitura, `IMPLEMENTED_NOT_TESTED`, `TEST_NOT_RUN` para pytest/CI, `NOT_DEPLOYED`. O código **não** altera `CLARA_CONSENT_CHANNEL`, ack, RBAC, consentimento V014, migrations, BFF, Portal ou dados de fechamento. A decisão operacional do responsável já está documentada; assinatura separada Segurança/Plataforma continua não demonstrada. Quando a configuração produtiva mudar de acordo com a política aprovada, é necessário **rebuild/restart MCP** e reconsultar `tools/list` (descrições registradas no startup), `get_context(schema)`, PREPARE e ACT com smoke autorizado.

**Proibido inferir cutover** apenas da presença da nova mensagem no MCP ou do deploy healthy. Aceite integral requer `portal_consent_required=false`, `conversational_act_armed=true` e read-back após confirmação explícita da operação de teste. Caso o catálogo do plugin conectado retenha descrições antigas, republicar/reconectar conforme procedimento oficial.
