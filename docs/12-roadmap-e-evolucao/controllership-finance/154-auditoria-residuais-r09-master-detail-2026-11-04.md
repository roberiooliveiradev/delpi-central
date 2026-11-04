# 154 — R09: auditoria dos resíduos do redesign master/detail, plano de correção e critérios de aceite

**Produto:** Portal Controladoria & Finanças · **Processo:** PROC-0072 · **Relatório:** R09 — Faturamento × MOD · **Data:** 2026-11-04.
**Tipo:** review técnico-documental, sem alterações de runtime. **Estado:** `REWORK_REQUIRED / DECISION_REQUIRED / NO_DEPLOY`.
**Base do review:** `main` em `3496551f30a57af0d5d82d516bf5e8480375abf7`, implementação `b3435e7ec10d7541f3eed77f832bd6e3a0a19428` e [plano/wireframes 153](./153-design-r09-faturamento-mod-wireframes-frontend-2026-11-04.md). Revalidar HEAD, git status, regras `.cursor` e contrato antes de executar.
**Escopo:** exclusivamente R09 e suas superfícies de Ajuda/teste/reuso. Não abrir uma nova reforma dos outros dez relatórios.

> **Regra de evidência:** `PROVEN` significa fato visto no código/contrato ou na captura indicada; `TO_INVENTORY` significa que ainda falta prova; `PLANNED` e `TARGET` não são comportamento implementado. `PASS`, `FAIL`, `PENDING`, `INCONCLUSIVE`, `TEST_NOT_RUN` e `STALE_EVIDENCE` não são intercambiáveis. Capturas do localhost comprovam renderização local, não publicação produtiva. Relatório de testes do executor não é reexecução independente.

## 0. Decisão executiva

**Aprovar a direção visual, NÃO aprovar o release atual.** As capturas locais do PO para **09/2026** mostram que o layout deixou de ter cartões gigantes por âncora e passou a mostrar hero compacto, **521 âncoras produto/filial, 4.659 linhas MOD retornadas, 11 âncoras sem linhas** e tabela master do kit. Isso é *evidência de renderização local* e de consulta eventualmente concluída, **não** evidência de completude dos dados, paridade DLP204, comportamento da busca, seleção de detalhe, mobile, produção ou smoke.

O review independente localizou dois defeitos de alta prioridade no código: **campo `costProduct` omitido no detalhe** e **busca sem indexação do produto/descrição**. Existem outras lacunas de estados, governança e validação listadas abaixo. Não reescrever o design nem implementar um kit paralelo.

**Deployment:** `BLOCKED` até corrigir P1, fechar decisões materiais e demonstrar os critérios abaixo. Nenhuma operação de infraestrutura, alteração de BFF ou reingestão é autorizada por este documento.

## 1. Contexto, cadeia e autoridades

Leitura em ordem: `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md` → regras `.cursor` aplicáveis (sobretudo `evidence-driven-execution`, `plan-construction`, `plugins-reusable-components`, `plugins-visual-design-system`, `feature-help-sync`) → ADR/contrato → código/produtor/consumidor → testes → docs 153/143/144 → histórico.

```text
Rota MonthlyReportPage / reportContext.period
  -> BillingModBreakdownPage (MFE; estado de filial, consulta, KPIs, seleção)
     -> billingModBreakdownApi.getBillingModBreakdown()
        -> controllership-finance-api (BFF) -> fontes canônicas via contexto autorizado
     -> ClosingHero / CfPageHero / CfMetricKpiCard / CfSelectField
     -> cfDataTableUi.DataTableSection -> @delpi/plugin-ui DataTableSection
     -> CfSectionCard / CfStateBanner / CfEmptyState / Ajuda
```

**Contratos inalteráveis sem decisão transversal:** MFE consulta somente sua BFF; `controllership-finance.access` / `.manage` são as únicas permissions do produto; autorização real no backend. Paridade oficial DLP204 `PENDING`, custos sem taxa comprovada não são estimados. Evidência do estudo **09/2026** não é selo de outras competências.

### 1.1 Inventário dos arquivos e owners

| Caminho (prefixo `plugins/controllership-finance/src/` exceto docs/kit) | Papel |
|---|---|
| `features/closing/BillingModBreakdownPage.tsx` | UI R09: consulta, hero, master table, detalhe, estados e histórico |
| `api/billingModBreakdownApi.ts` | Types de `BillingModAnchor`, `BillingModLine`, `TypedNumber`, `ParityEvidence` e BFF client |
| `app/cfDataTableUi.tsx` | Adapter oficial de `createDashboardDataTableKit` + paginação |
| `app/ClosingHero.tsx` e `app/controllershipFinanceUi.ts` | Layout/adapter oficial dos heros e KPI |
| `features/closing/MonthlyReportPage.tsx` / `reportQueryParams.ts` | Route/família e contrato de URL |
| `features/closing/BillingModBreakdownPage.test.tsx` | Sete testes focados; usam mock de `plugin-ui` |
| `test/pluginUiMock.tsx` | Mock de componentes; não substitui teste do kit real |
| `content/helpTooltips.ts` | Ajuda R09 e afirmações visíveis sobre busca/completude |
| `plugins/plugin-ui/src/components/data/DataTableSection.tsx` e `src/utils/dataTableSearch.ts` | Owner de busca/paginação/semântica real do kit |
| `docs/12-roadmap-e-evolucao/controllership-finance/153-...md` | Plano/wireframes; permanece `PLAN_ONLY/PENDING_PO_VISUAL_APPROVAL` |

**Owner de implementação:** MFE R09. **Owner de contrato/semântica:** BFF/fonte canônica/Controladoria, quando necessário. **Owner de decisões:** PO + authority responsável. Reuso `@delpi/plugin-ui` primeiro; nunca escrever CSS interno/espelho de componentes do kit no MFE.

## 2. Registro completo dos resíduos: corrigir, inventariar ou decidir

### 2.1 P1 — Correções objetivas antes do release

| ID | Problema e evidência | Estado | Correção mínima e prova |
|---|---|---|---|
| **R09-01** | `BillingModLine.costProduct?: TypedNumber` existe no contrato; `AnchorDetail.columns` não contém `costProduct`. A documentação/comentário do executor diz que todos os campos foram preservados, mas não foram | **PROVEN / FAIL** | Expor **Custo do produto** no detalhe com `fmtTyped`; cobrir valor, null, zero e estado desconhecido. Verificar no kit a disposição responsiva; não estimar custo |
| **R09-02** | `DataTableSection` recebe as colunas e `rows`, mas **não** recebe `getSearchText`. A coluna Produto retorna JSX e não declara `sortValue`; o `buildDataTableSearchText` do kit só indexa retorno primitivo de `render` ou `sortValue`. Logo, código/descrição do produto **não entram no haystack padrão** | **PROVEN / FAIL** | Passar `getSearchText` baseado em `product`, `productDescription` e `branch` (e campos adicionais autorizados); testar busca por código e descrição no **kit real**, com paginação; não confiar apenas no mock |
| **R09-03** | Hero/tooltip dizem “universo completo retornado”, “busca cobre todo o universo” e “nenhum registro omitido”. O contrato cliente contém `anchors[]`, sem marcador explícito de total/completude; BFF não paginar **não prova** ausência de truncamento/filtros internos | **PROVEN claim / INCONCLUSIVE completeness** | Retirar afirmação categórica até inventário real de produtor BFF, SQL/limits e cardinalidade; comprovar total e escopo por competência/filial com evidência sanitizada. Se conjunto parcial, impedir busca/paginação com semântica universal |
| **R09-04** | Doc 153 segue `TARGET / PLAN_ONLY / PENDING_PO_VISUAL_APPROVAL`, enquanto `b3435e7ec1` implementou decisões de master/detail, filtros e client pagination antes de gate de decisão formal registrado | **EXECUTION_DRIFT / DECISION_REQUIRED** | Reconciliar ledger do doc 153: decisão explícita do PO/owners para detalhe inline, filtros, paginação, histórico e URL; conservar como `TARGET` até autorizado. Não converter recomendação do arquiteto em autorização implícita |
| **R09-05** | A implementação com dados reais **não** foi validada integralmente no navegador durante a execução: o executor reportou timeout da consulta. Capturas seguintes do PO comprovam a master table local com 521 registros, mas **não** seleção/detalhe, paginação, busca, 16 variações de viewport/tema ou smoke produtivo | **PARTIAL_VISUAL / TEST_NOT_RUN** | Capturar master + detalhe selecionado com custo tipado e `costProduct`; verificar filtros, busca, página 1/última página, 8 viewports × 2 temas, 125%/200%, teclado; guardar evidência acessível e SHA |

### 2.2 P2 — Comportamentos, estados e qualidade de apresentação

| ID | Problema e evidência | Estado | Ação/prova |
|---|---|---|---|
| **R09-06** | Loading inicial é um `<p aria-live>Carregando...`, não `CfLoadingCard` do plano; no screenshot local loading ocupou a tela sem esqueleto da tabela | **PROVEN / GAP** | Reusar estado de loading do kit; manter hero/filtro visíveis, indicar progresso sem inventar percentual, tratar refresh, timeout real e retry |
| **R09-07** | O error state interpola `state.error.message` diretamente em texto user-facing. Essa mensagem pode ser técnica ou sensível, dependendo da origem | **PROVEN CODE / RISK** | Mensagem pública PT-BR genérica por classe/HTTP status, detalhes apenas em log governado; retry; testar 401/403/5xx/timeout sem expor informações internas |
| **R09-08** | `updatedAt` é mantido do último sucesso, mesmo quando `setState(null)` inicia nova consulta de filial/competência ou quando ocorre erro. Pode parecer timestamp da nova consulta sem êxito | **PROVEN CODE / TO_VERIFY UX** | Separar `lastSuccessfulAt` do status da consulta atual ou limpar/sinalizar “dados anteriores”; testar mudança de filial, erro e refresh |
| **R09-09** | `fmtTyped` mostra número sempre que `value != null` sem validar estados, e pode mostrar rótulo “disponível” se `state=AVAILABLE` + `value=null`; `TypedNumber.state` é string aberta | **PROVEN CODE / NEEDS_STATE_INVENTORY** | Inventariar estados reais do produtor, mapear combinações legítimas, detectar inconsistências, fallback neutro; jamais `null→0` e jamais gerar preço/taxa |
| **R09-10** | `fmtNumber` usa `maximumFractionDigits: 4` para todas as grandezas; valores pequenos de tempo/horas podem arredondar para um “0” visual falso | **PROVEN CODE / PRECISION_RISK** | Definir precisão por campo com authority/contrato (não alterar valor), incluir `0.00001`, valores negativos, `0` real, unidades e formato PT-BR |
| **R09-11** | O detail row key concatena `level/product/operation/resource/modItem` e não inclui identificador de sequência ou `sourceOp`; duas operações com atributos iguais podem colidir. A master key `branch::product` também supõe unicidade não evidenciada | **PROVEN CODE / TO_INVENTORY UNIQUENESS** | Verificar unicidade de ambos os grãos em payload representativo e na fonte. Se colisão real, propor chave estável com owner/contrato; não usar índice para identidade funcional persistente |
| **R09-12** | Seleção `selectedKey` limpa ao trocar filial, mas não é reconciliada explicitamente em mudança de `reportContext.period`, busca da tabela ou alteração de página; detalhe pode ficar associado a item não visível | **PROVEN CODE / UX_RISK** | Testar competência, busca, troca de página e refresh. Definir seleção limpa/reconciliada, sem renderizar detalhe incoerente; respeitar decisão do PO sobre retenção de seleção |
| **R09-13** | `aria-expanded` no botão Ver/Ocultar não aponta para região controlada (`aria-controls` ausente) e o foco do detalhe/retorno não é demonstrado | **PROVEN CODE / A11Y_GAP** | Implementar relacionamento acessível quando adequado ao kit, identificar região do detalhe e testar Tab/Enter/foco/leitor; não usar apenas badge/cor |
| **R09-14** | Histórico renderiza `parityEvidence.semantics` e `homologationStatus` brutos; antes do redesign a captura produtiva mostrava inglês e `PENDING` | **PROVEN CODE / LOCALE_GAP** | Traduzir apresentação a partir de estados conhecidos, manter texto/fonte original preservados; formatar `measuredAt` em PT-BR; nunca apresentar 82,5% como paridade atual |
| **R09-15** | `sourceMissing` de âncora e payload aparece como códigos brutos, `payload.provenance` não é renderizado; outras métricas de `ParityEvidence` não estão explicitamente expostas. Ausências não têm explicação de origem por célula | **PROVEN CODE / PRESENTATION_GAP** | Inventariar proveniência e informações permitidas; mostrar códigos/causas em ajuda ou detalhe acessível, sem esconder confidencialidade; decidir escopo da evidência expandida |
| **R09-16** | Tipos/colunas quantitativas não expõem unidades verificadas de tempo/horas e valores potencialmente muito precisos; tabela detalhe com 12 colunas requer inspeção em mobile/zoom | **PROVEN LAYOUT / VALIDATION_PENDING** | Garantir títulos, largura, scroll **local** e unidade aprovada; não cortar campos em 360/390 px; nenhuma rolagem horizontal da página |
| **R09-17** | `branch` é `useState("all")`; não persiste na URL. A rota R09 está mapeada como família `settlements` e `SETTLEMENT_PARAMS` não inclui `branch`; mudar o contrato global afeta outros relatórios | **PROVEN / DECISION_REQUIRED** | Decisão PO: manter comportamento para V1 ou criar contrato contextual específico R09; se escolher URL, revisar contrato de query params e regressão de retorno/deep-link |
| **R09-18** | Há 7 testes dedicados, mas nenhum teste de busca por código/descrição, paginação 50/última página, colisão, foco, `costProduct`, precisão e concorrência de respostas. No mock, o default de busca difere do kit real | **PROVEN / COVERAGE_FAIL** | Testes de comportamento com `@delpi/plugin-ui` real + integração de browser; fixtures com >50 e >500 âncoras e estados tipados; não validar só presença do input |
| **R09-19** | Executor reportou suite `430/431` e falha `DocumentDetailPanel.test.tsx` ligada a avatar/blob URL; não há reprodução independente estabelecendo baseline/ambiente | **TEST_REPORTED / INCONCLUSIVE** | Reexecutar em isolamento HEAD-base e HEAD-candidato sob mesmo ambiente, classificar causa por diff/dependência, resolver ou registrar bloqueio fundamentado; não declarar suite inteira PASS |
| **R09-20** | Latência/volume R09 não foram medidos até conclusão nos probes iniciais; depois o PO exibiu consulta local carregada, sem cronômetro/bytes. Client pagination reduz DOM visível, **não** payload da BFF | **SCREENSHOT_PROVEN / PERFORMANCE_TO_INVENTORY** | Medir payload em bytes, duração BFF, tempo render/interação, memória e número de nós DOM para 01/02/all; se limite/volume incompatível, `DECISION_REQUIRED` para server pagination |

### 2.3 P3 — Refinamentos que só entram se forem necessários para o aceite

| ID | Item | Estado / regra |
|---|---|---|
| **R09-21** | Mensagem “Âncoras sem linhas” deve continuar estritamente factual; não afirmar “produto sem roteiro” sem evidência de `sourceMissing` ou produtor | **GUARDRAIL PROVEN / REGRESSION_TEST** |
| **R09-22** | Tabela master possui filtro de busca próprio do kit, mas não deve prometer busca por descrição/identificador até implementar `R09-02` e testar a real indexação; preferência de colunas não pode apagar a identificação do produto sem tratamento | **TO_VERIFY** |
| **R09-23** | Estado do detalhe sem linhas, empty master, no-permission e erro devem continuar coerentes com a classificação da fonte, sem dados fictícios, sem “consulta homologada” | **REGRESSION_GUARD** |
| **R09-24** | Ajuda `CF_HELP.billingModBreakdown` hoje descreve completude e paginação universal como fatos; o doc 153 não reflete implantação parcial nem evidências do commit | **PROVEN / DOC_HELP_DRIFT** — sincronizar no mesmo gate da correção |

## 3. Matriz de paridade do contrato — cada campo deve ter decisão explícita

| Âmbito | Campo(s) | Estado atual |
|---|---|---|
| Âncora master | `branch`, `product`, `productDescription`, `billedQty`, `modLines.length` | **PROVEN** exibidos; validar precisão e busca |
| Âncora detalhe | `sourceMissing` | **PROVEN** exibido em códigos brutos; traduzir com evidência |
| Operação MOD | `level`, `product`, `productDescription`, `operation`, `operationDescription`, `resource`, `modItem`, `modDescription`, `modUnit`, `propagatedQty`, `stdTime`, `hours`, `costUnit`, `costTotal`, `sourceOp` | **PROVEN** consumidos no detalhe; testar cada um com conteúdo não vazio |
| Operação MOD | **`costProduct`** | **FAIL**: contratado, mas não renderizado. Corrigir `R09-01` |
| Payload | `report`, `reportId`, `period`, `branch` | Parte usada implicitamente; verificar consistência com rota/filtro |
| Payload | `officiality`, `officialParity` | **TO_INVENTORY**: UI usa banner estático; verificar exposição honesta sem inventar status |
| Payload | `limitations`, `sourceMissing`, `provenance` | Limitações e fontes ausentes parcialmente mostradas; proveniência não renderizada |
| Paridade histórica | `scope.referencePeriod`, `artifact`, `measuredAt`, `gate`, `homologationStatus`, `branches` | Parte mostrada sem tradução/formatação; rastrear valores e contexto |
| Métricas históricas | `artifactLines`, `calculatedLines`, `matchedKeys`, `keyCoveragePct`, `qtdFatCorrectPct`, `stdTimeCorrectPct`, `hoursCorrectPct`, `missingLines`, `extraLines` | Parte disponível no contrato, mas não mostrada. **DECISION_REQUIRED** quanto ao nível de detalhe exibido; nunca tratar como KPI atual |
| Texto histórico | `semantics` | Mostrado bruto; renderização PT-BR e proveniência pendentes |

Não interpretar “campo no contrato” como “campo preenchido em toda resposta”; teste `null`, `undefined`, fonte indisponível, zero real e valor pequeno. Não incluir informações potencialmente sensíveis sem checar escopo.

## 4. Revisão do wireframe após screenshots do PO

### 4.1 Estrutura **aceita visualmente como direção**, não como homologação completa

```text
[breadcrumb: Relatórios e divergências / 09/2026 / R09]
[faixa curta: Visão operacional; paridade oficial pendente]
[HERO — Faturamento × MOD — R09]
  [KPI âncoras:521] [KPI linhas MOD:4.659] [KPI sem linhas:11]
  [Filial v]                                   [Limpar] [Atualizar]
[TABELA MASTER — 521 registros — busca real por produto/descrição/filial]
 Produto + descrição | Filial | Qtd faturada | Linhas MOD | Situação | Ver
 ...                         [página N de M]
[DETALHE ÚNICO — seleção demonstrada e acessível]
 Nível | Componente | Operação | Recurso | Item MOD | Un. | Qtd |
 Tempo padrão | Horas | Custo unit. | Custo total | CUSTO PRODUTO | OP ref.
[Histórico DLP204 — recorte 09/2026 — disclosure datado]
[Limitações e proveniência — disclosure legível]
```

**Observação:** os valores 521 / 4.659 / 11 vêm apenas de screenshot local de **09/2026**; não devem aparecer codificados no produto. A captura com “Carregando faturamento × MOD...” antecedeu outra já carregada; não prova spinner infinito.

### 4.2 Estados que exigem captura individual

```text
A) Local 1600x900 — R09 com dados; pesquisa por produto com resultado
B) Local 1600x900 — item com linhas MOD, detalhe expandido; costProduct visível
C) Local 1600x900 — item sem linhas MOD, mensagem factual
D) Local 1600x900 — pesquisa sem resultados, limpar, página final
E) Local — 401/403, erro recuperável, falha BFF, loading longo, refresh
F) Desktop/tablet/mobile — 8 viewports x claro/escuro, zoom 125%/200%
G) Produtivo autenticado — rota/contexto; somente após gate release
```

## 5. Plano de correção mínima — sem reescrever R09

| Gate | Prioridade | Entrega | Evidência de saída / parada |
|---|---|---|---|
| **G0 — reconciliação de autoridade** | P1 | Fechar a matriz do `11 do doc 153 e inventariar grão, completude e `TypedNumber.state` com owner | Aprovação explícita/`DECISION_REQUIRED`; sem mudança contratual não aprovada |
| **G1 — correções confirmadas** | P1 | Incluir `costProduct` no detalhe; fornecer `getSearchText` do master; retirar promessa não comprovada de completude na UI/Ajuda | Testes reais de custo e busca; nenhum valor/registro perdido |
| **G2 — seleção, estados e precisão** | P2 | Reconciliar seleção, IDs e foco; loading/erro/lastSuccessfulAt; precisão e status; ausência e proveniência | Testes com branch, period, paginação, erro/timeout e valores pequenos |
| **G3 — linguagem, histórico e documentação** | P2 | PT-BR para histórico, separar competência corrente de estudo, sync Ajuda e status doc153 | Conferência de texto + visual + ledger atualizado |
| **G4 — QA abrangente** | P1/P2 | Kit real + 7 testes R09 ampliados, suíte completa/causa da falha `DocumentDetailPanel`, browser, perf e responsivo | Matriz AC completa; qualquer teste crítico não rodado = não autorizar deploy |
| **G5 — release futuro** | Condicional | GPT REVIEW, SHA verificado, decisão de produção, deploy MFE por `main`/SSH operador, rollback e smoke autenticado | Só após aprovação transversal; nunca inferir smoke de build/401 |

**Foco:** reutilizar `ClosingHero`, `CfMetricKpiCard`, `DataTableSection`, `CfSectionCard`, `CfStateBanner`, `CfLoadingCard`, `CfEmptyState`, `CfActionButton`, `CfStatusBadge`. Não criar `TableV2`, CSS de `delpi-ui` ou componentes clones.

## 6. Critérios de aceite verificáveis

| AC | Resultado obrigatório | Prova |
|---|---|---|
| **AC-01** | Master mostra grão produto/filial corretamente e não há tabela/card por âncora inteira | Inspeção DOM + screenshot |
| **AC-02** | Busca por código e por descrição funciona, inclusive após filtro, ordenação e paginação | Teste com kit real e browser; `getSearchText` |
| **AC-03** | Paginação cliente navega todo universo efetivamente comprovado, sem omissões | Contrato BFF/produtor, 50/51/521 linhas, última página |
| **AC-04** | Ao abrir produto com MOD, todas as colunas e **`costProduct`** aparecem | Fixture com campos preenchidos e nulos + screenshot do detalhe |
| **AC-05** | Distinção `null`/zero/estado desconhecido/ausência tipada e precisão real | Testes por campo, `0.00001`, estado contraditório |
| **AC-06** | Seleção/master/detail consistentes sob branch, period, busca, nova página, refresh | Testes RTL + browser; unicidade de IDs |
| **AC-07** | Erro seguro e retry, loading/refresh claros e sem “atualizado” enganoso | 401/403/5xx, timeout, concorrência de requests |
| **AC-08** | Histórico datado em PT-BR; sem paridade corrente inventada | Referência 09/2026 versus 10/2026; screenshot |
| **AC-09** | Fonte/proveniência/limitações e campos do contrato tratados com honestidade | Ledger de campo, owner e testes |
| **AC-10** | Responsividade: 1920/1600/1440/1280/1024/768/390/360, ambos os temas, zoom 125/200 | Capturas, bounding boxes, teclado, foco, sem overflow de página |
| **AC-11** | Ajuda e doc153 reconciliados com runtime testado e decisões | Diff e revisão de Help; evitar `PLAN_ONLY` como selo do runtime |
| **AC-12** | TypeScript, lint, build, Vitest, estrutural e browser; falha de terceiro classificada por prova | Logs completos, baseline sob mesmo ambiente; sem PASS inferido |
| **AC-13** | Performance mensurada em dados representativos; seleção/paginação sem regressão severa | Bytes BFF, timings, perfil DOM e comparação baseline |
| **AC-14** | Sem novo contrato, fonte, custo/taxa, permission, acesso direto à `api-delpi` ou import entre contextos | Diff de arquitetura + tests |
| **AC-15** | Release somente após novo gate explícito e smoke produtivo real | SHA, deploy/rollback e evidência pós-release |

## 7. DECISION_REQUIRED (não confundir com defeito já comprovado)

1. **Detalhe:** manter **inline** (já implementado) ou drawer. Recomendação: inline, após prova de navegação/teclado.
2. **Busca/filtros:** manter filial + busca local sobre **universo realmente completo**, ou abrir contrato de backend para filtros/paginação. Recomendação: manter client-side somente se o produtor provar completude.
3. **Histórico:** disclosure datado (implementado) ou bloco fixo. Recomendação: manter disclosure; status atual de paridade sempre visível.
4. **URL filial:** manter `useState("all")` para V1 ou criar parâmetro R09 específico com compatibilidade. Recomendação: manter até decisão de owner/contrato, sem alterar a família inteira `settlements`.
5. **Detalhamento da evidência histórica e de proveniência:** quais campos da comparação 09/2026 são necessários ao usuário final? Exibir o essencial e um detalhe datado; owner valida sensibilidade e legibilidade.
6. **Paginação server-side:** só considerar depois das medidas de tamanho, tempo e limites. Seria contrato novo com owner BFF; fora do escopo automático deste rework.

**Nenhuma recomendação é autorização tácita.** Decisões já tomadas formalmente devem ser referenciadas com evidência de owner; o Documento 153 não pode ser promovido a `APPROVED` sem isso.

## 8. Ledger de cobertura (pedido do PO: “documente tudo que precisa corrigir”)

| Requisito | Onde está coberto | Estado |
|---|---|---|
| Todos os defeitos confirmados por código/contrato | `2.1`, `2.2`, `3` | ATENDIDO_NO_PLANO |
| Riscos e hipóteses sem fingir PASS | `2.2–2.3`, `6–7` | ATENDIDO_NO_PLANO |
| Screenshots e regressão de UI | `0`, `4`, `6` | ATENDIDO_NO_PLANO |
| Reuso de componentes oficiais existentes | `1.1`, `5` | ATENDIDO_NO_PLANO |
| Testes, QA, Ajuda, performance, deploy gate | `5–6` | ATENDIDO_NO_PLANO |
| Autorizações de produto/contrato ainda abertas | `2.1/R09-04`, `7` | BLOQUEADO_COM_EVIDENCIA |
| Implementação / execução de suíte / smoke produtivo | Fora do escopo documental deste commit | FORA_DO_ESCOPO_COM_JUSTIFICATIVA |

## 9. Referências e evidências de origem

- [Documento 153 — design/wireframes e reuso](./153-design-r09-faturamento-mod-wireframes-frontend-2026-11-04.md).
- [R09 — Gate 041](./143-g041-r09-recuperacao-shy-op-bzcustd-paridade.md) e [Gate 042](./144-g042-r09-temporal-shy-op-taxa-paridade.md) (paridade datada e limites).
- [Mapa oficial de reuso](./30-plugin-ui-reuse-map.md) e [padrão visual dos Portais](../../11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md).
- Código: `plugins/controllership-finance/src/features/closing/BillingModBreakdownPage.tsx` e testes; `src/api/billingModBreakdownApi.ts`; `src/app/cfDataTableUi.tsx`; `src/content/helpTooltips.ts`; `src/features/closing/reportQueryParams.ts`.
- Kit: `plugins/plugin-ui/src/components/data/DataTableSection.tsx` e `plugins/plugin-ui/src/utils/dataTableSearch.ts`; implementação de busca que indexa retorno primitivo de `render` ou `sortValue`.
- **Capturas do PO** na conversa: 09/2026, estado loading, hero com 521/4.659/11 e master table local. Não presumir outros datasets nem timing produtivo.
- **Relatório do executor** `CF-PROC0072-R09-VISUAL-IMPLEMENTATION-001`: informou `430/431` e a falha `DocumentDetailPanel`; não foi reexecutado neste review.

**Próximo passo:** aprovar/ajustar decisões `7`, executar G0 e G1 com minimal diff, validar G2–G4; solicitar novo GPT REVIEW antes de qualquer deploy. Sem esse gate, **`NO_DEPLOY`**.
