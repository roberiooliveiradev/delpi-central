# 52 - Blueprint detalhado das duas tabelas (R01/R02 e R03)

**Data:** 2026-10-21. **Estado:** TARGET / RUNTIME_GATE=PENDING / DESIGN_REVIEW_REQUIRED. **Origem visual:** duas imagens de mockup fornecidas pelo PO nesta conversa: (A) Estoque historico P7 com hero e resumo, barra de resultados com Excel/Colunas/Fonte/Tabela/Cards, tabela de produtos; (B) Baixas financeiras com toolbar similar, tabela de eventos financeiros. As imagens sao propostas, NAO amostras do ERP ou provas de capacidade do sistema. **Baseline de codigo:** documentos 30/48/49/50/51 e fonte das paginas `FinancialSettlementsPage.tsx`, `StockInventoryPage.tsx` e `cfDataTableUi.ts` no main consultado. Nao foi realizado deploy nesta atividade.

## 1. Resultado esperado e fronteira

A tabela deve ficar visualmente proxima do painel inferior dos mockups, nao apenas receber pill, divisor e quebra de texto. Aceite requer **comparacao lado a lado entre mockup e browser autentico**. Preservar consultas automaticas, debounce, paginacao/ordenacao pelo servidor, BFF, permissoes exclusivamente `controllership-finance.access/manage`, filial apenas filtro/dimensao, duas views pagar/receber, `source_missing` distinto de zero, `officialP7:false`. Sem copia do codigo do Comercial, sem novas rotas por estetica, plugin-ui first.

Separar escopo: **V1 DESIGN-ONLY** = hierarquia visual, espacamentos, tipografia, icones oficiais, distribuicao toolbar e celulas reais; **V2 FEATURE GATES** = Excel integral, Tabela/Cards, novos sorts, filtros de tipos individuais, badge semantico colorido por classificacao, links/menus por linha, nomes de grupo e mapa BRL. V2 so com decisao explicita, endpoints/producers/consumers e testes.

## 2. Estrutura exata do painel de resultados - comum

**Linha 1: Header**
- Esquerda: icone discreto e semanticamente neutro SOMENTE se existir iconografia oficial no kit; titulo `Baixas a pagar`/`Baixas a receber` ou `Detalhamento por produto e armazem`; ao lado **chip** `N registros`, com total proveniente da API para todos os filtros, nunca apenas os itens da pagina.
- Direita: toolbar primaria em desktop com acao REAL de `Colunas`, controle `Fonte [-] 13px [+]`, outras acoes existentes, sem repetir controles. `Excel` apenas no gate posterior, com contrato de export completo; `Tabela/Cards` apenas com renderizacao de cards aprovada.
- Layout: padding, gap e altura conforme tokens do plugin-ui; nao redesenhar ou duplicar a toolbar proprietaria `DataTableSection`. Revisar suporte de `headerActions`, `toolbarLeading`, `toolbarExtra` e labels do HEAD; criar adaptador local somente se permitido.

**Linha 2: controles secundarios**
- `Itens por pagina [50]` perto da tabela e acessivel, nao escondido.
- Em desktop, preferir toolbar coesa em 1 ou 2 faixas justificadas; em mobile quebrar a linha sem overlap, sem mover botoes para fora do painel.
- Indicacao de pagina atual / total e `anterior/proximo` no rodape pelo kit. Nao posicionar tudo na primeira linha se gera truncamento.

**Tabela**
- Header azul escuro oficial, distincao titulo/cabecalho, contraste acessivel, sem icone de sort clicavel sem ordenacao global do backend.
- Linhas com alinhamento vertical consistente, densidade suficiente para celula de 2 linhas, hover/focus do kit, borders, espacos de coluna; evitar altura variavel descontrolada.
- **Largura:** descricao/contraparte e natureza ganham espaco, codigos curtos perdem; campos numéricos alinhados a direita e `tabular-nums`; scroll horizontal dentro do container em largura estreita, nao na pagina. Verificar colunas congeladas apenas se o kit oficial suportar: senao TARGET_FUTURE.
- Tooltip/accessibility: truncar so se houver forma acessivel de consultar texto integral; preferir wrap controlado. `mobileLabel`, headerHint e keyboard/focus conforme kit. Nunca ocultar valor ou status importante apenas por estetica.
- Estados: loading skeleton/placeholder oficial; erro e parcialidade banner contextual; legitimo zero -> empty state; snapshot inexistente -> banner sem tabela vazia; sem exibir falso total zero.

## 3. Blueprint completo R01/R02 - Baixas financeiras

O mockup apresenta header `Resultados` + `1.284 registros` e valores BRL. Esses dados sao ilustrativos; no runtime atual o resultado por lado e 529 eventos/valor 4.322.781,87 moeda 01 para o recorte observado. **Nao trocar a contagem, moeda, agrupamento ou lado por valores do mockup.** O titulo contextual pode continuar `Baixas a pagar`/`Baixas a receber` (mais claro que `Resultados`).

| Coluna/elemento | Exibicao aceita | Ajuste visual solicitado | Regra que nao pode quebrar |
|---|---|---|---|
| Data da baixa | DD/MM/AAAA civil | coluna compacta, cabecalho legivel | calendario, nao UTC drift |
| Documento | identificador original forte | destaque sans bold e min-width para NF/FT | sem link inexistente |
| Parcela | codigo original | alinhamento centrado; travessao p/ ausente | nao criar 1/1 ficticio |
| Fornecedor/Cliente | nome forte + codigo/loja secondary se realmente retornados | largura principal, duas linhas, sem avatar aleatorio | nao expor novos campos |
| Natureza | codigo forte + descricao muted quando existem | duas linhas, wrap e bom respiro | sem transformar em chips arbitrarios |
| Tipo mov. | codigo real BA/VL/CP/ES + descricao | duas linhas, largura media | nao atribuir ao evento semantica nao provada |
| Direcao | badge do lado selecionado + codigo cru | cores do badge ja homologadas, posicionar sem cobrir codigo | payout/receipt != paymentDirection cru |
| Moeda | codigo da fonte, ex. 01 | compacto, legivel | nao rotular BRL sem mapping |
| Valor | formatacao numero atual | alinhar direita e enfatizar, numeros tabulares | sem prefixo R$ nao provado |
| Vencimento | DD/MM/AAAA ou ausente | largura suficiente e right/center coerente | sem modificar datas |
| Vinculo | status real, badge resolved/missing etc. | badges menores e com contraste | valores missing diferenciados |
| Filial | Filial ## se efetiva; ausente -> Nao identificada | nao truncar `Nao identificada` ao estreitar viewport | dado, nao permission |
| Linha/acoes | nenhuma acao adicional aprovada | hover/selecionabilidade visual neutra | nunca menu ..., link Pedido/OP ou navegação falsa |

**Filtros / sort** permanecem no hero, atualizam tabela automaticamente, sem clique obrigatório. Se uma das views nao tem categoria, label e preferencia de colunas devem acompanhar o lado. `columnPreferencesKey` e `fontSizePreferencesKey` preservadas; trocar versao apenas com estrategia para prefs.

## 4. Blueprint completo R03 - Estoque historico P7

O mockup apresenta 12.845 registros, grupos nomeados, tipo por cores, `R$`, competencia por linha e menu de acoes. Sao **ilustrativos e NAO autorizados**. Pagina real no recorte conhecido mostra 7.813 itens no ago/2026 conjunto 01/02; set/2026 3.117 da filial 02, com ausencia filial 01. Recalcular a partir da resposta real, nunca usar essas contagens para mock.

| Coluna/elemento | Exibicao aceita | Ajuste visual solicitado | Regra |
|---|---|---|---|
| Produto | B9_COD/SB1 codigo atual, forte | largura minima suficiente para codigo, hover/foco do kit | sem link inventado |
| Descricao | descricao cadastrada, texto integral | ocupar coluna mais ampla e wrap com limite acessivel | nao perder texto em ellipsis |
| Tipo | B1_TIPO, badge neutro MP/PI/PA/II etc. | chip consistente com altura de linha | cor diferente por tipo requer gate |
| Grupo | codigo B1_GRUPO | legibilidade, largura compacta | nao inventar nome de grupo |
| UM | codigo da fonte | compacto | nao normalizar unidades por heuristica |
| Armazem | codigo B9_LOCAL | facilitar correlacao visual com filial | NAO somar depositos homonimos |
| Filial | codigo da origem (01/02) + label | compacta mas completa | filtro, nao RBAC |
| Quantidade | historicalQuantity com precisao existente | alinhamento direito, numeros tabulares | nao reduzir arbitrariamente casas |
| Valor historico | historicalStockValue numerico | coluna importante, negrito moderado/direita | sem R$ nao comprovado |
| Competencia | mostrada no hero/filtros atualmente | nao adicionar em cada linha sem justificativa | gate de produto |
| Linha/acoes | nenhuma operacao real | nao incluir ... ou download por item | somente TARGET_FUTURE |

Quando `report_scope=all_products`, todos os tipos permanecem, inclusive II, EM, MC, MH etc. `mp_pi_pa` agrupa MP/PI/PA no contrato vigente. Manter sumarizacao por tipo e por filial+armazem fora da tabela e seus totais completos, nao apenas pagina exibida.

## 5. Matriz de fidelidade e criterios AC especificos

**AC-T01** Hierarquia title+contador no mesmo header: contagem real, atualização com filtros, sem duplicar badge. **AC-T02** Toolbar demonstra agrupamento proximo do mockup, mas SOMENTE botoes funcionais; controle `Colunas`, fonte, itens/pagina. **AC-T03** densidade e larguras comparadas em screenshot side-by-side; resultado SUBSTANCIAL, nao so CSS divisor. **AC-T04** descricao/documento sem truncamento acidental; scroll limitado ao container. **AC-T05** status badges semanticamente honestos; fornecedor sem avatar falso. **AC-T06** numeros e datas iguais aos dados retornados (ex.: moeda 01, filial não identificada). **AC-T07** R03 snapshot ausente apresenta mensagem e nao tabela; `no_matching_items` apresenta empty legitimo. **AC-T08** resultados paginados corretos e ordenacao global apenas se backend suporta. **AC-T09** clear/dark, 3 viewports + teclado + zoom; nao declarar PASS nao executado. **AC-T10** nenhum elemento so decorativo aparentando ser acionavel. **AC-T11** doc51 matriz T01-T19 atualizada com resultado comprovado; doc52 evidencia antes/depois. **AC-T12** sem alteracao em API/RBAC/segredo/filial como authorization.

## 6. Itens que NAO podem ser copiados dos mockups sem decisao

| Referencia | Por que bloqueado | Proxima evidencia necessaria |
|---|---|---|
| Excel | endpoint/contrato export do recorte completo, volume, authz | DECISION_REQUIRED, owner e limites |
| Tabela / Cards / Board | model/renderCard e navegacao aprovados, query/pagination | DECISION_REQUIRED |
| Sort por header | API deve aceitar sort por chave de coluna global | contrato e producer |
| Avatar / logo / fornecedor | nenhuma fonte de imagem/cadastro comprovada | contrato e privacidade |
| Link Pedido/OP/duplicata | rota, ownership, id e authorization | contrato entre contextos |
| Menu ... por linha | operacoes reais, sem permissao extra | RQ/AC + autorizacao |
| Badges coloridos MP/PI/PA | cores nao sao regra de negocio homologada | design tokens e owner |
| R$ / BRL | precisa comprovacao mapeamento de moeda/saldo | contrato canonical |
| % crescimento/participacao | nao consta no payload atual | formula, fontes, reconciliacao |
| Grupo nominal / Competencia por linha | fora do payload/necessidade definida | avaliacao PO |
| Itens ilustrativos 1.284 / 12.845 | nao sao dados de runtime | nunca hardcode |

## 7. Plano de implementacao e gates

**G0 READ**: HEAD/status, authorities, .cursor, docs 30/48/49/50/51/52, codigo R01/R02/R03, kit, Comercial, testes. **G1 INVENTORY**: API e slots reais, medidas atuais de DOM (width/scroll/wrap) desktop/tablet/mobile, estado da view por lado/snapshot. **G2 VISUAL DESIGN**: preparar mock HTML ou preview React com dados claramente sintéticos e capturas ANTES de runtime; matriz do mockup para elementos REUSE/KEEP/NEW VISUAL/FEATURE GATE. **GATE TRANSVERSAL**: se o necessario requer mexer em `DataTableSection` compartilhado, adicionar novo componente, rota ou contrato, apresentar `DECISION_REQUIRED` e aguardar; se rearranjo com props existentes, pedir GO minimo. **G3 IMPLEMENT**: R01/R02 primeiro, depois R03, help sync, minimal diff, nada de refazer hero. **G4 VERIFY**: suites e **screenshot comparativo autenticado**, medir melhoria por seções; se browser indisponivel, INCONCLUSIVE quanto ao visual e nao afirmar que fidelidade foi concluida. **G5**: doc51/52/readme, commit/SHA; push/deploy SSH somente com autorizacao operacional expressa para a execucao.

A maior limitacao atual: `DataTableSection` fornece controles e slots, mas talvez nao permita replicar sem composicao maior a posicao de toolbar ou toggle do mockup. **Nao contornar com uma tabela nova por conta propria**: demonstrar limite concreto e alternativas com impacto e recomendacao.

## 7b. Resultado da execucao V3 (pos `3b7aa14a07`)

Implementado somente com slots publicos do `DataTableSection` + CSS escopado
`.dashboard-controllership-finance` — zero alteracao em componente
compartilhado, contrato ou feature:

- **Banda unica header+toolbar (§2)**: a `<section>` do kit passa a
  `display:flex; flex-wrap` — header (titulo + pill `N registros`) a
  esquerda e toolbar nativa (Itens/pagina + Fonte + Colunas) a direita
  na mesma linha; em largura estreita a toolbar quebra para a linha
  seguinte dentro do painel. Demais filhos (loading, tabela, paginacao)
  seguem em linha propria 100%.
- **Proporcoes de coluna (§2 "Largura")**: classes do kit via
  `className: "cf-table__col--*"` — `compact` (datas, parcela, moeda,
  filial, grupo, UM, armazem), `wrap`/`wide` (fornecedor, natureza,
  tipo de movimento, descricao), `status` (direcao, vinculo, tipo de
  produto), `numeric` (valor, quantidade, valor historico);
  `Parcela` com `align:"center"`. Densidade sutil via
  `--delpi-ui-table-cell-pad-y: 8px`.
- Mantido: pill de contagem, `source_missing` sem tabela (V2/T18),
  badges semanticos reais, moeda de origem, sem R$.

Verificacao: Vitest 91/91, estruturais 17/17, lint 0 erros, tsc, build.
Deploy `35b554975c` (srv-api, apenas MFE) verificado: remoteEntry 200,
bundle contem `.cf-table-section{display:flex`. **Capturas autenticadas
de producao fornecidas pelo PO (21/10/2026, tema escuro desktop)**:
- R03: banda unica com pill "7.813 registros", controles a direita na
  mesma linha; badges neutros de tipo; numeric a direita; sem R$.
- R01/R02: pill "529 registros", fornecedor/natureza/tipo em 2 linhas,
  badge direcao + codigo cru, moeda 01, "Nao identificada" legivel.
AC-T01/T02/T03/T05/T06/T07 parcialmente comprovados (dark desktop).
Pendentes: tema claro, tablet, mobile, teclado, zoom, comparacao
lado a lado com mockup (AC-T04/T09 nao fecham sem isso).

**V4 - auditoria de estabilidade (22/10/2026)**: RCA dos seletores flex
da `cf-table-section` sobre todos os filhos possiveis do
`DataTableSection` (header, toolbar, toolbarFilters, loading/refresh
sticky, table-wrap, cards, paginacao, footer): o catch-all `> *` e a
propriedade defensiva correta - qualquer filho novo do kit ocupa linha
propria (SAFE default). Defeito real reproduzido: <=768px o kit pede
`pageSize{width:100%}` mas a toolbar V3 era `flex:0 0 auto` (largura
indefinida) comprimindo os controles - corrigido com media query
`toolbar{flex:1 1 100%; justify-content:space-between}`. Contrato da
composicao protegido por `closingTablePanel.structural.test.mjs`
(estruturais 25/25). Demais verificacoes (temas claro, viewports,
teclado, zoom) seguem TEST_NOT_RUN.

**V5 (22/10/2026) - correcao AC01**: codigo de direcao cru (`P`) nao e
mais renderizado como segunda linha solta; badge permanece o elemento
principal e o codigo fica em `title` tooltip + span `.cf-visually-hidden`
para auditoria/leitor de tela. Contrato e modelo inalterados.

**V6 (22/10/2026) - capacidades do kit ativadas**: `resizableColumns`
nas duas tabelas (handles do kit com estado interno, sem prop
controlada); densidade alinhada ao modo `--compact` do kit
(`cell-pad-y: 6px`); icone lucide "table" no titulo do painel de
resultados e icones "package"/"warehouse" nos resumos P7 via
`::before` com mask-image em currentColor (tema-agnostico). O
cabecalho azul dos mockups ja e o padrao nativo do kit
(gradiente `--delpi-ui-title` no claro, tint accent no escuro) —
mantido. Excel/Cards/sort por coluna seguem DECISION_REQUIRED.

**V7 (22/10/2026) - evidencia autenticada e % do total**: capturas de
producao (PO, dark desktop) confirmam runtime: banda unica com icone
de tabela + pill, header azul, densidade compacta, handles de resize
visiveis nos headers, sem "P" solto. Resumos P7 agora exibem
"N itens · X,X% do total" (share derivado de `totalStockValue`/
`historicalTotal` do contrato — nao e dado inventado; omitido quando
o total e nulo). Lacunas restantes do mockup sao TODAS decision-gated:
Excel do universo completo (exige endpoint ou fan-out server-side),
Tabela/Cards (kit suporta, falta decisao de produto), sort por coluna
(backend nao ordena o universo), links Pedido/OP/Duplicata (rotas
inexistentes), "..." por linha, avatares (vedado pelo spec), badges
coloridos de natureza/tipo (sem mapa homologado), nome do grupo (so
ha codigo), R$ em valor (sem mapa de moeda), coluna competencia
(redundante com filtro), "% vs periodo anterior" (sem serie
historica), chips por tipo de produto (contrato so tem mp_pi_pa
combinado).

## 8. Relatorio inicial exigido do Devin

```text
HEAD_STATUS:
DATA_TABLE_HEAD_CAPABILITIES:
REAL_BROWSER_BASELINE_SCREENSHOTS:
TABLE_BLUEPRINT_R01_R02:
TABLE_BLUEPRINT_R03:
T01_T19_RECONCILIATION:
VISUAL_DIFFERENCES_CAN_BE_DONE_WITH_KIT:
FUNCTIONAL_MOCKUP_ONLY_EXCLUSIONS:
DECISION_REQUIRED:
OWNER_RQ_AC:
GATE_TRANSVERSAL:
TEST_AND_SCREENSHOT_PLAN:
```
