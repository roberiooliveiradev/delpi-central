# 153 — R09 Faturamento × MOD: plano de reorganização visual, wireframes e reuso do plugin-ui

> **Adendo de revisão (04/11/2026):** houve implementação parcial no commit `b3435e7ec1`, sem deploy autorizado. A auditoria independente e o backlog de correções estão no [Documento 154](./154-auditoria-residuais-r09-master-detail-2026-11-04.md). Este documento 153 permanece o **plano de design**, não um registro de aceite ou homologação.

**Produto:** Portal Controladoria & Finanças · **Processo:** PROC-0072 · **Página:** R09 — Faturamento × MOD · **Data:** 2026-11-04.
**Estado:** `TARGET / PLAN_ONLY / PENDING_PO_VISUAL_APPROVAL`. Este documento **não** atesta implementação, homologação, testes, smoke ou deploy; nenhum contrato foi alterado.
**Owner proposto:** Portal Controladoria & Finanças (experiência MFE); contrato e semântica operacional permanecem com os respectivos owners BFF/TOTVS/Controladoria.
**Local de trabalho futuro:** `main`, com HEAD e alterações concorrentes revalidados antes de qualquer execução. Sem branch extra por padrão do PO.

## 0. Resultado desejado e fronteira

Transformar a longa lista de `CfSectionCard` por produto em uma **consulta gerencial navegável**:

1. Identidade do relatório, competência, filial e classificação honesta logo no início;
2. poucos indicadores estritamente derivados de dados disponíveis;
3. filtros compactos e busca local somente quando o payload for completo;
4. tabela principal paginada por **âncora produto + filial**, com seleção acessível;
5. detalhe das operações MOD da âncora selecionada, em seção de largura útil;
6. comparação histórica e limitações em seções secundárias explicitamente datadas;
7. estados loading/erro/vazio/parcial, mobile, teclado, claro/escuro e Ajuda coerentes.

**Não fazer:** recalcular DLP204, inferir custos/taxas ausentes, prometer paridade oficial, inserir um KPI monetário inventado, criar nova permission, criar API exclusiva, importar domínios de outro contexto, consultar `api-delpi` do browser ou duplicar `@delpi/plugin-ui`.

## 1. Autoridades e evidências

Precedência: [instruções oficiais](../../11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md) → `.cursor` aplicável (`evidence-driven-execution`, `plan-construction`, `platform-frontend-mfe-experience`, `plugins-reusable-components`, `plugins-visual-design-system`, `feature-help-sync`) → contratos e ADRs → código no HEAD → testes → documentação vigente → planos/histórico.

| ID | Evidência / constatação | Classificação |
|---|---|---|
| EV-01 | Capturas produtivas fornecidas pelo PO mostram cards muito extensos por produto, tabela MOD espremida à esquerda, cabeçalhos sem largura, repetição de “indisponível” e longas seções históricas antes dos registros | `OBSERVED_SCREENSHOT`; não prova causa de backend |
| EV-02 | `BillingModBreakdownPage.tsx` usa `CfStateBanner`, `CfSectionCard`, `CfSelectField`, `CfEmptyState` e `anchors.map(AnchorCard)` com `<table className="cf-data-table">` e `overflowX: auto` | `PROVEN` no código |
| EV-03 | `billingModBreakdownApi.ts` já define `BillingModBreakdownPayload`, `BillingModAnchor`, `BillingModLine`, `TypedNumber(value,state)`, `sourceMissing`, `limitations`, `parityEvidence` | `PROVEN` no contrato cliente; não implica todos os campos populados |
| EV-04 | `cfDataTableUi.tsx` oferece `DataTableSection` com `createDashboardDataTableKit` e paginação, já usado por R10/R11 | `PROVEN` em código consumidor |
| EV-05 | `ClosingHero.tsx` compõe `CfPageHero`, `CfMetricKpiCard` e `CfActionButton`; `controllershipFinanceUi.ts` exporta adapters do kit | `PROVEN`; não usado hoje pelo R09 |
| EV-06 | Gate R09 143/144 registra referência histórica DLP204 de **2026-09**, 3.694/4.476 chaves (82,5%) no recorte do estudo e paridade oficial `PENDING`; taxa MOD histórica não comprovada | `PROVEN` como estudo datado, **não** como KPI de 2026-10 |
| EV-07 | Quantidade real de âncoras por competência/filial, estabilidade da chave, volume de payload e estados possíveis retornados agora em produção | `TO_INVENTORY` — exige sample sanitizado e teste |
| EV-08 | HEAD remoto observado na elaboração: `349b1660d22809a379acc318aa0d5498647f967e`; a API GitHub não informa `git status` de worktrees locais | `PROVEN` para ref remoto; status local `TO_VERIFY` antes da execução |

### 1.1 Cadeia consumidor/produtor

```mermaid
flowchart TD
  H[Shell Minha DELPI / rota contextual] --> P[MonthlyReportPage]
  P --> V[BillingModBreakdownPage — R09]
  V --> C[billingModBreakdownApi / httpGet]
  C --> B[controllership-finance-api — BFF]
  B --> D[Integração autorizada com fontes canônicas / api-delpi]
  V --> K[@delpi/plugin-ui via adapters cf]
  V --> U[cfDataTableUi — DataTableSection]
```

Rota atual: `/apps/controllership-finance/closing/monthly-closing/{period}/reports/billing-mod-breakdown`. API atual: `GET /closing/competences/{period}/billing-mod-breakdown?branch={all|01|02}` via BFF; não propor endpoint novo neste gate.

## 2. Ledger do pedido e rastreabilidade

| RQ | Requisito | Solução planejada | Prova/AC | Estado no plano |
|---|---|---|---|---|
| RQ-R09-UX-01 | Relatório organizado, gerencial | Hero + indicadores + tabela master + detalhe | AC-01, 02, 05 | ATENDIDO_NO_PLANO |
| RQ-R09-UX-02 | Wireframes editáveis desktop/tablet/mobile | Seção 4 | AC-08 | ATENDIDO_NO_PLANO |
| RQ-R09-UX-03 | Componentes reais do kit, já usados no Portal | Matriz de reuso `5` | AC-09 | ATENDIDO_NO_PLANO |
| RQ-R09-UX-04 | Preservar dados reais, nulidade, proveniência | Matriz de campos `6` | AC-03, 04 | ATENDIDO_NO_PLANO |
| RQ-R09-UX-05 | Escalabilidade, busca e paginação | Client mode apenas com payload completo; gate de volume | AC-06 | ATENDIDO_NO_PLANO |
| RQ-R09-UX-06 | Ajuda/segurança/tema/acessibilidade | `8–10` | AC-07, 08, 10 | ATENDIDO_NO_PLANO |
| RQ-R09-UX-07 | Não mudar regra de negócio / contratos por suposição | `7` + DECISION_REQUIRED `11` | AC-11 | ATENDIDO_NO_PLANO |

## 3. Diagnóstico AS-IS do frontend (não confundir com backend)

| Problema | Ponto de origem no frontend | Consequência |
|---|---|---|
| Um painel por âncora sem limite visual | `AnchorsSection → payload.anchors.map(AnchorCard)` | DOM extenso; navegação e comparação difíceis |
| Tabelas de dez colunas dentro dos painéis | `AnchorCard` com tabela HTML local, sem `DataTableSection` | Colunas comprimidas, ordenação/busca/paginação ausentes |
| Sem visão consolidada | R09 não utiliza `ClosingHero` nem `CfMetricKpiCard` | Usuário começa pela justificativa e listas antes de entender volume |
| Custos sem motivação específica | `fmtTyped` ignora `TypedNumber.state` | Estados distintos aparecem como a mesma palavra “indisponível” |
| Mensagem potencialmente conclusiva | `modLines.length === 0` gera “produto sem roteiro/recurso MOD mapeado” | Ausência de linhas não prova isoladamente a causa; `sourceMissing` não é consultado |
| Texto em inglês em evidência histórica | `payload.parityEvidence.semantics` repassado diretamente | Mistura de idiomas, sem tradução validada |
| Comparação histórica anterior ao período selecionado | `parityEvidence.scope.referencePeriod` exibido sem isolamento visual forte | Risco de interpretar 2026-09 como selo para 2026-10 |
| Estado inicial e erro pouco orientativos | `state === null` → parágrafo loading; `CfEmptyState` para erro sem retry | Recuperação difícil; ausência de telemetria de progresso na superfície |
| Filtro filial não persistido | `useState("all")` sem integração URL | F5/compartilhamento perde escolha de filial |

**Hipóteses que devem ser testadas, não assumidas:** o maior custo de renderização pode vir do grande DOM de âncoras, do volume transferido pela BFF ou de ambos; uma tabela paginada no cliente reduz DOM, mas não reduz payload. Instrumentar antes/depois.

## 4. Wireframes alvo (TARGET, não screenshots implementados)

### 4.1 Desktop ≥ 1280 px — resumo e tabela, sem cards gigantes

```text
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│ ← Relatórios e divergências  / 10/2026  /  Faturamento × MOD                             │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│ CENTRAL DE FECHAMENTO                                                                     │
│ Faturamento × MOD — R09                        [Paridade oficial pendente]                │
│ Competência 10/2026 • Visão operacional • Origem Protheus                                 │
│ Não representa o DLP204 oficial; custos sem fonte histórica permanecem indisponíveis.    │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│ [Âncoras produto/filial: —]  [Linhas MOD: —]  [Âncoras sem linhas: —]                     │
│ Valores apurados apenas do payload ativo; sem total monetário presumido.                 │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│ FILTROS                                                                                   │
│ [Filial: 01+02  v] [Buscar produto / descrição                  ] [Situação MOD: Todas v]│
│                                                     [Limpar] [Atualizar consulta]         │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│ PRODUTOS FATURADOS                                                 [Exibindo X de Y]    │
│ Produto / descrição       Filial   Qtd faturada    Linhas MOD    Situação         Detalhe│
│ 10070988                  01          0               0          Sem linhas        [Ver]│
│ 10090211                  01        100               0          Sem linhas        [Ver]│
│ 80014579                  01          0,01            5          Com linhas        [Ver]│
│ ...                                                                                       │
│ [Itens por página v]                                        [Anterior]  Página 1 [Próx.]│
├───────────────────────────────────────────────────────────────────────────────────────────┤
│ DETALHE DA ÂNCORA SELECIONADA: Produto 80014579 · Filial 01 · Qtd 0,01                   │
│ Nível  Produto  Operação        Recurso  Item MOD  Qtd prop.  Tempo  Horas  Custos/state│
│ 02     —        INSPECIONAR     CT-70    MOD349    ...         ...    ...    Ausente (?)  │
│ ...                       [origem/ausência tipada e unidade em ajuda contextual]           │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│ ▸ Evidência HISTÓRICA 09/2026 — DLP204 (não comprova 10/2026)                             │
│ ▸ Limitações, fontes ausentes e divergências conhecidas                                  │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

Regras: a tabela master **não contém tabelas aninhadas por produto**; uma seleção controla **um** painel de detalhe. O rodapé de paginação aparece conforme contrato do kit. A faixa histórica fica abaixo da área principal e mantém rótulo explícito de período.

### 4.2 Desktop — detalhe com dez campos legíveis e ausência tipada

```text
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│ OPERAÇÕES MOD — Produto 80014579 / Filial 01                                              │
│ Nível | Produto componente | Operação          | Recurso | Item MOD / descrição           │
│ 02    | —                  | INSPECIONAR        | CT-70   | MOD349                        │
│ 04    | —                  | CORTAR...          | CT-19   | MOD254                        │
│                                                                                           │
│ Qtd propagada | Tempo padrão (estado) | Horas (estado) | Custo unit. | Custo total         │
│ 0,01          | 0,01                 | 0,0001         | Indisp. (?) | Indisp. (?)         │
│                                                                                           │
│ [?] Explicação de ausência: state e sourceMissing, sem converter null em zero.            │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

O desenho indica agrupamentos lógicos de colunas; a implementação pode usar **uma tabela com scroll horizontal intencional** e cabeçalhos agrupados, desde que nenhuma coluna essencial seja omitida. Não impor layout em duas tabelas desconectadas sem prova de acessibilidade/ordenamento.

### 4.3 Tablet (768–1279 px)

```text
┌───────────────────────────────────────────────┐
│ R09 · 10/2026        [Paridade pendente]       │
│ [Âncoras: —]       [Linhas MOD: —]             │
│ [Sem linhas: —]                               │
│ [Filial v]         [Buscar produto       ]     │
│ [Situação v]      [Atualizar]                  │
│                                               │
│ Tabela master rolável somente se necessário   │
│ Produto | Filial | Qtd | Linhas | [Ver]        │
│ ...                                           │
│ [Paginação]                                   │
│                                               │
│ Detalhe abaixo, largura total, scroll local   │
│ ▸ Evidência histórica / limitações            │
└───────────────────────────────────────────────┘
```

### 4.4 Mobile (360–430 px)

```text
┌────────────────────────────────────┐
│ ← Voltar                           │
│ Faturamento × MOD — R09             │
│ 10/2026 · Visão operacional        │
│ [Paridade pendente]                 │
│ [Âncoras: —]  [Linhas MOD: —]       │
│ [Sem linhas: —]                     │
│ Filial                             │
│ [Filiais 01+02               v]    │
│ Buscar produto                     │
│ [Código ou descrição          ]    │
│ Situação MOD                       │
│ [Todas                     v]      │
│ [Limpar] [Atualizar]               │
│                                    │
│ PRODUTOS                           │
│ 80014579 · Filial 01               │
│ Qtd 0,01 · 5 linhas MOD            │
│ [Ver operações]                    │
│ ──────────────────────────────     │
│ 10090211 · Filial 01               │
│ Qtd 100 · sem linhas retornadas    │
│ [Ver situação]                     │
│                                    │
│ DETALHE DO PRODUTO SELECIONADO     │
│ campos completos em área própria   │
│ ▸ Evidência de 09/2026             │
│ ▸ Limitações                       │
└────────────────────────────────────┘
```

Mobile pode usar variante responsiva oficial do `DataTableSection` ou representação compacta comprovadamente suportada pelo `plugin-ui`; não criar duas fontes de lógica de seleção/ordenação. Conteúdo e CTA precisam continuar acessíveis por teclado e toque.

### 4.5 Estados especiais

```text
LOADING:  [Hero e filtro visíveis] → [CfLoadingCard / estado acessível] → sem texto solto infinito
EMPTY:    [Nenhuma âncora para filial/competência] [Limpar filtros] / [Atualizar]
ERROR:    [Falha ao obter R09] [Tentar novamente] — sem renderizar sucesso vazio
PARTIAL:  [Registros presentes] + [Aviso de fonte/valor tipado ausente]
FORBIDDEN: [Acesso não autorizado] — sem fallback para fonte alternativa
NO MOD:   [Âncora sem linhas retornadas] + causa somente se sourceMissing/state provar
```

## 5. Componentes: o que existe no R09, no Portal e no plugin-ui

### 5.1 As-is e proposta de reuso (sem criar kit paralelo)

| Componente/factory oficial | Adapter/uso existente | R09 agora | Uso planejado |
|---|---|---|---|
| `createDashboardStateBanner` | `CfStateBanner` em `controllershipFinanceUi.ts` | Sim | Aviso essencial de paridade e limites, curto |
| `createDashboardSectionCard` | `CfSectionCard` no Portal/R09 | Sim | Filtros, detalhe MOD, histórico e limitações |
| `createDashboardSelectField` | `CfSelectField` | Sim | Filial; outros selects apenas após gate de semântica |
| `EmptyState` | `CfEmptyState` | Sim | Vazio / forbidden / erro com ação de recuperação validada |
| `createDashboardPageHero` | `CfPageHero`, composto em `ClosingHero.tsx` nas páginas irmãs | Não | Cabeçalho R09 conforme padrão do Portal |
| `createMetricKpiCard` | `CfMetricKpiCard` usado por `ClosingHero` | Não | No máximo 3 indicadores derivados sem monetização inventada |
| `ActionButton` | `CfActionButton` usado por `ClosingHero` e outras páginas | Não | Atualizar / Limpar / Ver detalhe conforme padrão e sem duplicidade |
| `createDashboardDataTableKit` | `DataTableSection` em `cfDataTableUi.tsx`; usado por R10/R11 | Não | Tabela master; paginação/search/toolbar oficiais |
| `createDashboardPaginationKit` | Já integrado no `cfDataTableUi.tsx` | Indireto não | Reuso via `DataTableSection`, não reimplementar |
| `createDashboardLoadingActivityCard` | `CfLoadingCard` já no Portal e no kit de tabelas | Não | Loading/refresh sem spinner artesanal |
| `createDashboardStatusBadge` | `CfStatusBadge` no Portal | Não | Status tipado, sem confundir ausência com erro |
| `createDashboardTextField` / `createDashboardFiltersKit` | `CfTextField` / `FiltersRow` e `FilterInputField` nas páginas irmãs | Não | Busca local / filtros caso suportados e aprovados |
| `createDashboardPagePath` | `CfPagePath` na rota pai do fechamento | Indireto | Manter breadcrumb existente, não duplicar |
| `createDashboardSegmentToggle` | `CfSegmentToggle` disponível e usado em outras páginas | Não | **Não necessário no escopo base**; só usar se houver seleção funcional real |

**Contrato de arquitetura:** importar via adapter atual do Portal e `@delpi/plugin-ui/index`; não criar `ReportTable`, `KpiCard`, `SectionCard`, CSS `.delpi-ui-*` nem sobrescritas do interior do kit no MFE. CSS local limita-se à disposição da página (stack/gap/grid) quando necessário, com escopo `.dashboard-controllership-finance`.

### 5.2 Componentes existentes a preservar/alterar no R09

| Elemento atual | Decisão proposta |
|---|---|
| `BillingModBreakdownPage` | Manter como entrypoint e orquestrador dos estados |
| `AnchorsSection` | Substituir composição de cards em massa por tabela master + detalhe + blocos de evidência |
| `AnchorCard` | Remover da árvore principal **após** equivalência funcional testada; nenhum dado de operação pode desaparecer |
| `fmtNumber` / `fmtTyped` | Reavaliar precisão/unidades e apresentar `state`; null não é zero |
| `CfSectionCard` histórico/limitações | Preservar conteúdo datado; tornar secundário e legível |
| `CfSelectField` filial | Preservar valores `all/01/02` e contrato BFF |
| `getBillingModBreakdown` | Não mudar endpoint/contrato; verificar tamanho do retorno antes de optar por paginação cliente |

### 5.3 Gate de integração com tabela (obrigatório antes da implementação)

Verificar `DashboardDataTableSectionProps` real no kit, estratégias de detalhe de linha, `rowKey`, ordenação, search, paginação client/server, colunas custom, estados loading, expansão e responsividade. Reutilizar `cfDataTableUi.tsx`. Se não houver slot adequado para seleção de linha/detalhe, escolher a composição de página mais simples suportada pelo kit e registrar a lacuna; **não duplicar chrome de tabela**.

## 6. Mapeamento de dados e semântica (contrato vigente, sem novas fontes)

| Elemento de UI | Campo / origem | Regra de apresentação |
|---|---|---|
| Competência | `payload.period` / `reportContext.period` | Mostrar `MM/AAAA`; nunca confundir com `parityEvidence.scope.referencePeriod` |
| Filial | `anchor.branch` e seleção `branch` | Grão visual = âncora produto + filial; não unir filiais silenciosamente |
| Produto e descrição | `anchor.product` / `productDescription` | Código preservado; descrição só se disponível |
| Quantidade faturada | `anchor.billedQty` | Formatação `pt-BR`; não atribuir moeda |
| Linhas MOD | `anchor.modLines.length` | Contagem do payload; zero linhas retornadas **não prova** ausência definitiva de roteiro |
| Ausências da âncora | `anchor.sourceMissing` | Explicar somente códigos/situações mapeados e validados |
| Operação/recurso/item | `modLines[].operationDescription/operation/resource/modItem/modDescription` | Preservar identificadores e descrições; não omitir campos por economia visual |
| Nível/produto de componente | `level, product, productDescription` | Distinguir componente da âncora faturada |
| Qtd. propagada | `propagatedQty` | Formatação e precisão compatíveis com contrato |
| Tempo padrão, horas, custo | `stdTime/hours/costUnit/costTotal/costProduct` como `TypedNumber` | Mostrar `value` quando legítimo; explicar `state` para indisponível; unidades só se comprovadas |
| Unidade MOD e OP | `modUnit, sourceOp` | Mostrar no detalhe quando realmente preenchidos |
| Status/paridade | `officiality`, `officialParity`, `parityEvidence.scope.homologationStatus` | Separar status da visão corrente e avaliação histórica |
| Evidência histórica | `parityEvidence.scope, metrics, semantics` | Cabeçalho **“Referência 09/2026”** quando for o mês real; nunca usar como KPI da competência atual |
| Limitações | `limitations, provenance, sourceMissing` | Manter contexto e proveniência sem blocos dominando a página |

### KPIs permitidos neste gate (somente se payload completo)

- **Âncoras retornadas:** `anchors.length`; apresentar “âncoras produto/filial” (não chamar de produtos únicos sem deduplicação validada).
- **Linhas MOD retornadas:** soma de `modLines.length` sobre as âncoras carregadas.
- **Âncoras sem linhas MOD retornadas:** contagem de `modLines.length === 0`; não traduzir automaticamente como “sem roteiro”.
- *Opcional e dependente de owner:* contagem de ausências tipadas por campo, com semântica validada. **Não** adicionar total financeiro de custos indisponíveis, “% de paridade atual” ou quantias inferidas.

Antes de renderizar números agregados, provar completude do payload, ausência de duplicidade no grão, universo da filial, estabilidade da coleta e tratamento de `null`. Quando parciais, identificar o subconjunto apresentado em vez de sugerir total universal.

### Chave e seleção

A API expõe `branch` e `product` por âncora, mas não há um `anchorId` explícito no contrato cliente. Investigar se `(branch, product)` é único no payload real. **Se não for**, registrar necessidade de chave estável e reconciliar owner/contrato antes de consolidar linhas. Não usar índice de array como identidade funcional persistida após busca/ordenação.

### Ausência tipada

`TypedNumber.state` não possui enum tipado no cliente hoje (`string`). Inventariar valores reais e seu significado antes de criar textos ou badges; manter fallback neutro “Não informado pela fonte” para estado desconhecido, com detalhe técnico acessível quando permitido. `SOURCE_MISSING` ≠ zero; `NOT_APPLICABLE` ≠ falha; um `value=0` real continua sendo zero.

### Evidência de paridade

O exemplo **3.694 / 4.476 = 82,5%** é **histórico de 09/2026** nos docs 143/144 e na captura. Não reaproveitar como percentual do mês de referência sem novo cálculo oficial. Tradução do texto `semantics` deve ser feita por apresentação versionada a partir de estados/campos conhecidos; não alterar o conteúdo bruto ou omitir a proveniência.

## 7. Interações e comportamento (TARGET)

1. Ao entrar na rota, competência fixa vem de `reportContext.period`; filtro filial default atual `all`.
2. Alterar filial executa `getBillingModBreakdown(period, branch)` pela BFF; bloquear/ignorar resultados obsoletos de requests concorrentes; preservar tratamento de erros.
3. Busca produto/descrição e filtro de situação **podem** ser client-side se o payload for completo e o universo recuperado for adequado. Deixar como `PLANNED / PENDING_VOLUME_GATE`; não mostrar busca que ignore registros não carregados.
4. Paginação local preferida inicialmente para carga comprovadamente completa; opção server-side exige contrato, owner e autorização específicos.
5. Tabela master seleciona **uma âncora**; exibe painel de operações abaixo. Foco/scroll do teclado deve ir para o detalhe de forma previsível, sem auto-scroll agressivo.
6. Seleção troca detalhe; filtro que remova âncora selecionada limpa/reseleciona segundo comportamento explicitamente testado.
7. Voltar ao catálogo, F5 e deep link continuam funcionando. Persistência de `branch` na URL **a avaliar** com `reportQueryParams` e contrato de família; não modificar query params global por preferência.
8. Histórico de paridade e limitações como disclosures/seções secundárias do kit quando disponíveis; paridade pendente visível no topo em todos os estados.
9. Não mostrar ações CSV/PDF até provar produtor/contrato; não inventar export e não copiar a interface R10 sem funcionalidade real.
10. Renderizar somente os registros necessários para a página/seleção; medir DOM, latência, memória e tamanho da resposta antes de autorizar volume produtivo.

## 8. Layout, conteúdo e estados

- **Desktop:** hero compacto; 3 KPIs reais no máximo; filtros horizontais; tabela master com colunas essenciais; detalhe em área própria; seções históricas após os dados.
- **Tablet:** 2 colunas de indicadores/filtros quando couber; tabela em espaço útil; detalhe abaixo.
- **Mobile:** 1 coluna nos filtros; master responsiva acessível; detalhe completo com scroll local intencional ou representação oficial; nada cortado.
- **Claro/escuro:** mesma árvore e tokens; sem cores hardcoded. Status não depende só de cor.
- **Teclado:** foco em filtro → tabela → selecionar detalhe → histórico; `aria-label` da tabela, labels, estado `aria-busy`, loading `aria-live`, retry e botão “Ver operações” com nome do produto.
- **Linguagem:** PT-BR para rótulos, help, estados e aviso de histórico; códigos técnicos intactos. Evitar textos conclusivos como “sem roteiro” quando apenas ausência de linhas foi observada.
- **Datas:** não apresentar `measuredAt` ou data de histórico como timestamp de atualização da consulta atual.
- **Limites:** cabeçalho apresenta nota curta “Visão operacional; paridade oficial pendente; custos dependentes de taxa não comprovada permanecem indisponíveis”. Detalhes de proveniência preservados em seção secundária.

## 9. Plano de execução por gate, depois de aprovação de design

| Gate | Owner principal | Entrega mínima | Testes/evidência | Stop condition |
|---|---|---|---|---|
| G0 — design/contrato | PO + arquiteto | Aprovação da composição master/detail, filtros e estratégia para histórico; inventário real de contrato/estados/cardinalidade | Matriz de decisões e amostra sanitizada BFF | `DECISION_REQUIRED` não resolvida |
| G1 — composição visual | MFE | Hero, cards, banner e tradução de rótulos; sem mexer na BFF | TypeScript/Vitest/a11y/visual desktop/mobile | Regressão de paridade/semântica |
| G2 — tabela master/detalhe | MFE | `DataTableSection` reutilizado; chave estável, busca/paginação conforme G0; detalhe completo | Testes de seleção, paginação, ranking, chaves e regressão sem perda de campo | Payload incompleto / custo de DOM sem solução |
| G3 — ausência e histórico | MFE + owner semântico | Apresentação honesta do `TypedNumber.state`, `sourceMissing`, `parityEvidence` | Estados null/0, enum desconhecido, histórico vs mês corrente | Texto inventado ou taxa/custo presumidos |
| G4 — UX, Ajuda e verificação | MFE + QA | `helpTooltips` e Ajuda atualizados; responsivo, tema, F5, loading, erro, forbidden, paridade | Suíte frontend, browser real, 8 viewports x 2 temas, zoom 125%/200% | `TEST_NOT_RUN` material |
| G5 — gate transversal e release | PO + responsável deploy | Revisão GPT, commit `main`, deploy MFE por fluxo autorizado somente após GO explícito | SHA testado, health + smoke autenticado e rollback | Sem autorização ou smoke inacessível sem classificação |

**Regra:** fechar documentação e contratos antes de execução; depois implementar por etapas mínimas. Não alterar `api-delpi`, BFF, SQL ou persistência para acomodar apenas a apresentação.

### 9.1 Arquivos prováveis (inventário, não autorização irrestrita)

- `plugins/controllership-finance/src/features/closing/BillingModBreakdownPage.tsx` — owner da composição R09.
- `plugins/controllership-finance/src/api/billingModBreakdownApi.ts` — tipos/cliente, apenas se inventário de contrato exigir ajuste compatível e aprovado.
- `plugins/controllership-finance/src/app/ClosingHero.tsx`, `controllershipFinanceUi.ts` e `cfDataTableUi.tsx` — **reutilizar sem editar** inicialmente.
- `plugins/controllership-finance/src/content/helpTooltips.ts` — Ajuda no mesmo gate de UX.
- Testes R09 dedicados (inventariar nomes atuais primeiro), testes de rota e cenários de tabela.
- `plugins/controllership-finance/src/index.css` — somente layout de página se comprovadamente necessário; jamais CSS interno de `plugin-ui`.
- Documentação em `docs/12-roadmap-e-evolucao/controllership-finance/` — evidência e relatório de execução.

## 10. Aceite: RQ → AC → prova

| AC | Critério objetivo | Prova mínima |
|---|---|---|
| AC-01 | Header traz competência e aviso “paridade oficial pendente” | Screenshot + teste semântico |
| AC-02 | Primeira região analítica contém tabela de âncoras; não há card/tabela repetido para cada item | Browser DOM + screenshot |
| AC-03 | Custo `null` não vira 0, valores `state` distintos têm explicação correta | Teste com payloads de ausência e zero real |
| AC-04 | Histórico 09/2026 não é confundido com competência 10/2026 | Teste de dois períodos + render de `parityEvidence` |
| AC-05 | Detalhe preserva todos os campos vigentes de `BillingModLine` e identidade filial/produto | Teste de seleção e linhas com/sem MOD |
| AC-06 | Busca/paginação mostram todo o universo autorizado, sem perda silenciosa de registros | Contrato de completude + teste com grandes volumes |
| AC-07 | Loading, retry, empty, partial e forbidden explicitados; sem spinner infinito | Teste por estado + observação browser |
| AC-08 | 1920/1600/1440/1280/1024/768/390/360, claro e escuro, sem overflow ou truncamento | Capturas e bounding boxes reais |
| AC-09 | Reuso `plugin-ui` verificado, sem classes espelho nem CSS `.delpi-ui-*` no MFE | Inventário import/CSS + revisão de diff |
| AC-10 | Ajuda R09 em PT-BR sincronizada; teclado, foco e nomes acessíveis válidos | Teste de teclado + revisão Ajuda |
| AC-11 | Sem nova API/permission/cálculo/paridade; testes irmãos não regressam | Diff + suite relevante + contrato |
| AC-12 | Renderização medível com dataset representativo, sem DOM proporcional a todas as tabelas de MOD | Profiling baseline vs candidate |

Sem screenshot autenticada, não atribuir `PASS` visual. HTTP 200, build ou container healthy não comprovam outcome funcional. Testes não executados = `TEST_NOT_RUN`; ausência de evidência = `INCONCLUSIVE`.

## 11. DECISION_REQUIRED antes do primeiro commit de runtime

| Decisão | Opção A | Opção B | Recomendação |
|---|---|---|---|
| Organização do detalhe | **Inline abaixo da tabela** com uma seleção | Drawer/modal de detalhe | **A**: menor risco, melhor contexto e reuso |
| Filtros adicionais | Somente filial existente + busca local comprovadamente completa | Novos filtros na BFF | **A** para V1, sem adicionar situação se enum/volume não estiverem comprovados |
| Paginação | Client-side para payload completo e volume aceitável | Server-side com novo contrato | **A condicional**; se volume for alto/incompleto, voltar ao PO com evidências e B |
| Paridade histórica | Collapsible datado e separado do período corrente | Quadro permanente no topo | **A**; status da paridade **atual** permanece no topo |
| Estado dos custos | Labels derivados dos estados reais, sem cálculo monetário | Acrescentar regra/taxa | **A**, B proibida sem authority e DR-3 |
| Persistência filial | Seguir contrato atual até inventariar URLs | Integrar branch à URL após contrato aprovado | Preferir URL compartilhável **após** verificação de query params |

Essas recomendações **não** autorizam implementação por si só. Sem decisão de produto ou contrato onde necessária, devolver `DECISION_REQUIRED` com opções, impacto, evidência e owner.

## 12. Riscos e limites

- **Desempenho:** paginação no navegador não reduz transferência; medir tamanho da resposta por filial e tempo total de render. Se necessário paginação BFF, abrir gate de contrato.
- **Chaves duplicadas:** não colapsar registros entre filial/produto sem demonstrar o grão físico.
- **Precisão:** números com várias casas, especialmente `billedQty` e horas, exigem avaliação de formato e arredondamento; apresentação não altera cálculo.
- **Ausências:** `TypedNumber.state` é string aberta; não interpretar valores desconhecidos como erro ou zero.
- **Evidência histórica:** métricas 2026-09 não são KPI 2026-10 e não justificam selo de paridade.
- **Acessibilidade:** tabela principal e detalhe selecionável exigem navegação completa teclado/mobile; testar com navegação real.
- **Governança:** `controllership-finance.access/manage` permanecem as únicas permissions; BFF autoriza efetivamente.
- **Rollback:** após implementação eventual, restaurar somente commit(s) do MFE R09 e redeploy do MFE por procedimento canônico; preservar alterações concorrentes na `main`.

## 13. Referências canônicas e de uso real

- [Padrão visual Portais Minha DELPI](../../11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md).
- [Mapa de reuso plugin-ui](./30-plugin-ui-reuse-map.md); [catálogo do kit](../../../plugins/plugin-ui/docs/component-catalog.md).
- [Wireframes da Central de Fechamento](./112-design-visual-fechamento-mensal-wireframes.md).
- [Auditoria integral de UX](./150-plano-unico-correcao-integral-portal-ux-funcional-2026-11-02.md).
- [R09 Gate 041 — modelo/ausências/paridade](./143-g041-r09-recuperacao-shy-op-bzcustd-paridade.md).
- [R09 Gate 042 — temporal e histórico](./144-g042-r09-temporal-shy-op-taxa-paridade.md).
- Código: `plugins/controllership-finance/src/features/closing/BillingModBreakdownPage.tsx`; `src/api/billingModBreakdownApi.ts`; `src/app/ClosingHero.tsx`; `src/app/controllershipFinanceUi.ts`; `src/app/cfDataTableUi.tsx`; consumidores R10/R11; `src/content/helpTooltips.ts`.

**Gate atual:** `PLAN_RECORDED`. **Próximo passo:** PO validar o wireframe e as decisões `11`; em seguida inventário de cardinalidade/estados e elaboração do GPT BRIEF por gate. **Nenhum código executado ou deploy realizado por este documento.**

---

## 14. Estado de implementação (2026-11-04, RW02)

**Implementado em `main`:** `b3435e7ec1` (master/detail) + `8ab969db27` (rework P1) + correções RW02 em seguida. Documento permanece `PLAN_ONLY / PENDING_PO_VISUAL_APPROVAL` — a implementação **não** constitui aprovação formal das decisões §11.

| Decisão §11 | Estado |
|---|---|
| Detalhe inline (A) | Implementado — aguarda autorização formal |
| Filtros: filial + busca local (A) | Implementado sobre «registros retornados»; completude universal não declarada |
| Paginação client-side (A condicional) | Implementada — 521 âncoras / página 50 comprovados em browser real |
| Histórico em disclosure datado (A) | Implementado — data civil corrigida (bug de fuso), rótulos PT-BR |
| Estados de custo sem regra nova (A) | Implementado — labels por estados reais do produtor, null nunca vira zero |
| URL de filial | Não implementado — `DECISION_REQUIRED` (contrato `settlements`) |

**Evidências RW02:** 12 testes com mock + 6 testes no `DataTableSection` real (busca/paginação), suíte 442/442 + 25 estruturais, capturas `/tmp/cf-cards-verify/out/r09-rw2/` (dados reais: 521 âncoras, 4.659 linhas MOD, 11 sem linhas — competência 09/2026), zero overflow de página em 1600px e 390px, 932 nós DOM (vs. DOM proporcional a todas as âncoras na versão cards).

**Resíduos:** inventário fechado no doc 154 §10 — `R09-04/17` DECISION_REQUIRED, `R09-20` performance bytes/tempo `TO_INVENTORY`, `costProduct` nunca emitido pelo produtor (campo só de contrato, renderiza «—»).

> **Adendo 2 (04/11/2026):** decisão visual do PO (`CF-PROC0072-R09-ROW-DETAIL-MODAL-001`) — o detalhe inline é substituído por **linha clicável + modal de operações MOD** (`CfWideDialog`, variante `wide`, host-contained). Coluna «Detalhe»/botão «Ver» removidos. Ver [doc 154 §13](./154-auditoria-residuais-r09-master-detail-2026-11-04.md).
