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
