# 50 — TARGET UX: Hero, filtros e tabelas da Central de Fechamento (R01/R02 e R03)

> 21/10/2026 — **REWORK TABLE UX IMPLEMENTADO** (pos `7b4c51f883`). Celulas
> das duas tabelas ganharam hierarquia em duas linhas (`cf-cell-primary`/
> `cf-cell-secondary`): documento e codigos em peso 600 + descricao mutada
> (natureza, tipo de movimento, fornecedor/cliente com codigo/loja). Badges
> reais via `CfStatusBadge`: Direcao exibe rotulo do `side` do contrato
> (info/success) + codigo cru `paymentDirection` visivel — sem
> reclassificar BA/ES/VL/CP (doc48 D4); Vinculo `resolved`→success,
> `missing_*`→warning; Tipo de produto R03 em badge neutro. Filial sem
> codigo exibe "Nao identificada" mutada; valores monetarios com
> `cf-cell-amount` (600 + tabular-nums); `mobileLabel` em colunas densas.
> Contagem da toolbar passou a plural real "N registros". KPIs do hero:
> override local em `cf-hero-kpis` remove nowrap/ellipsis de
> `.delpi-ui-kpi-value` (o proprio kit prefere quebra em card estreito) —
> "Parcialmente disponivel" nao trunca mais. Excel/Cards/Board/selecao/
> links permanecem TARGET_FUTURE. Verificacao visual autenticada: pendente.
>
> 21/10/2026 — **REWORK de fidelidade visual IMPLEMENTADO** (commit seguinte a
> 7254eef580). KPIs migraram de `PageHero.highlights` para tiles
> `CfMetricKpiCard` (`createMetricKpiCard` do kit — icone, label, valor
> `<strong>`, hint, `tone`), em grid `cf-hero-kpis` auto-fit dentro do body do
> hero; hints sao dados reais (moeda, competencia, escopo, filiais com/sem
> snapshot). "Atualizar consulta" e unico, `variant="primary"`, na linha de
> acoes do painel de filtros ao lado de "Limpar filtros" (ghost) — o canto
> superior direito passa a exibir somente "Atualizado em DD/MM/AAAA, HH:mm".
> `cf-hero-filters` virou painel delimitado (borda/radius/fundo de tokens).
> `CfFeedbackMessage` ganhou `cf-feedback--<intent>` + icone; `warning`
> recebe borda/fundo amber (--delpi-warning) para `incomplete`/
> `source_missing`. Resumos P7 agrupados em `cf-summary-panels` (grid
> auto-fit minmax 420px — lado a lado so quando comporta, caso contrario
> empilha). Excel/Cards/links de vinculo/percentuais = permanecem
> TARGET_FUTURE. Verificacao visual interativa autenticada: pendente
> (TEST_NOT_RUN).
>
> 21/10/2026 — **IMPLEMENTADO.** Gate G2 liberado pelo PO (rearranjo UI puro,
> contratos vigentes). Adaptador `src/app/ClosingHero.tsx` sobre `CfPageHero`
> (`createDashboardPageHero` do kit, density compact): eyebrow "Central de
> Fechamento", titulo com `CfTitleWithHelp`, subtitulo, `actions` =
> "Atualizado às HH:mm" (timestamp real do fetch) + "Atualizar" (repete a
> consulta vigente — nao submete filtros), `highlights` com KPIs reais e
> `loading` "…", `children` = nota `CfFeedbackMessage` + area de filtros
> delimitada (`cf-hero-filters`, border-top token) + linha de acoes com
> **Limpar filtros** a direita. R01/R02: KPIs Eventos/Movimentacoes por moeda
> (codigo real)/Naturezas/Tipos; "Qualidade dos vinculos" permanece no stack
> de resultados. R03: KPIs Disponibilidade (tone warning quando
> nao-disponivel)/Data-base/Itens/Filiais/Valor total; resumos por tipo e
> armazem permanecem como secoes empilhadas (default do spec). Toolbar: os
> dois `DataTableSection` ganharam `fontSizePreferencesKey` (controle nativo
> de fonte); Colunas ja ativo; **Excel e view Cards = TO_INVENTORY, nao
> implementados**. Auto-query, debounce, concorrencia, stack/gap 24px e
> datas civis preservados. 91/91 vitest + 17/17 estruturais.
>
> 21/10/2026. **DESIGN/TARGET** (original abaixo). Proposta visual do GPT a partir de capturas do PO das paginas de Controladoria e de referencias do Portal Comercial (Pedidos em aberto / Minha carteira). Esta especificacao e a handoff de implementacao para Devin. Os MOCKUPS GERADOS sao **ILUSTRATIVOS**, nao contratos, dados de producao ou autorizacao para novos recursos. Revalidar HEAD e contratos antes de editar.

## 0. Autoridade, contexto e fronteiras

Ordem: instrucoes oficiais do arquiteto, .cursor aplicavel, ADRs/contratos, HEAD, testes, docs tecnicas, roadmap. Ler README deste diretorio, padrao visual da plataforma e doc 30 de reuso plugin-ui. **Nao copiar codigo do Portal Comercial nem implementar visual por mera imitacao**: inventariar os primitives de `@delpi/plugin-ui/index` e seguir o padrao canônico das paginas comuns.

Identidade imutavel: `controllership-finance`, MFE `plugins/controllership-finance`, base `/apps/controllership-finance`, BFF `controllership-finance-api` com base `/apps/controllership-finance-api`. Apenas `controllership-finance.access` e `.manage`; filial e exclusivamente filtro, sem segregacao por filial. Nenhuma mudanca de backend, SQL, RBAC ou contratos de R01/R02/R03 prevista neste design. Se nova API, export, permission, framework ou outro boundary for necessario, retornar `DECISION_REQUIRED`.

## 1. Estado atual comprovado e objetivo

Duas paginas em runtime, com auto-query nos filtros, debounce (~400 ms) para textos, cancelamento/identificacao de requests, `CfLoadingCard`, `CfFeedbackMessage`, `CfQueryErrorBanner`, `CfMetricStrip` e `DataTableSection` via plugin-ui. Espacamento entre secoes usa `cf-page-stack` / `--cf-section-gap` e ja foi corrigido. Formatador de data civil ja foi corrigido. **Preservar tudo isso**.

Problema UX: hierarquia visual pouco parecida com outros portais: titulo discreto, filtros e indicadores distribuidos em blocos separados; acoes nao unificadas; toolbar da tabela pouco destacada. Referencias do PO: heros de Pedidos em aberto e Minha carteira (identidade azul escuro, titulo destacado, indicadores compactos e filtros integrados no hero; tabela em painel independente com barra de ferramentas).

**Outcome**: as paginas R01/R02 e R03 devem compartilhar um `ClosingHero`/composicao equivalente e toolbar de resultados coerente com plugin-ui, mas preservar suas semanticas especificas. Reutilizar componente existente; um adaptador fino local so se justificado e documentado.

## 2. Especificacao transversal do HERO

Ordem visual recomendada **dentro de um unico hero/section chrome**:

1. Eyebrow de contexto: **FECHAMENTO** (ou breadcrumb/plataforma oficial) + titulo principal, grande mas responsivo.
2. Subtitulo curto da finalidade operacional, sem prometer conciliacao ou P7 oficial.
3. Canto superior direito: **ultima atualizacao** somente quando existir timestamp REAL de fetch/result; nao inventar horario de atualizacao, nem dizer dados atualizados quando falha.
4. Linha de KPIs compactos usando `CfMetricStrip` / componente publico aprovado. Respeitar moeda por codigo real da fonte; nao inventar BRL onde a origem diz `moeda 01`.
5. Mensagem informativa/status contextual usando `CfFeedbackMessage` e priorizacao visual equilibrada (erros e parcialidade persistem visiveis; nao duplicar banners/toasts).
6. Area de filtros bem delimitada com controles e labels existentes, incluindo toggles da pagina.
7. Linha de acoes no rodape da area de filtros, alinhada a direita em desktop e com wrapping/mobile; **Limpar filtros** visivel, sem esconder a acao em um overflow.

Hierarquia de layout: hero azul escuro conforme componente oficial; borda e padding do tema, espacamentos pelos tokens; evitar gradiente/css bespoke se plugin-ui ja possui PageHero/SectionCard. Separar hero de bloco de resultados com `cf-page-stack`, sem intercalar div desprovido de stack (`aria-busy` precisa manter o stack). Evitar hero excessivamente alto com filtros de seis colunas no mobile; organizar em linhas e recolher campos secundarios somente se padrao vigente suportar.

Nao copiar menu horizontal especifico do Comercial, pois paginas padrao do Portal precisam preservar menu proprio (Inicio, Visao geral, Sala de interacao, Minhas tarefas, Administracao, Ajuda quando efetivamente implementados). Nao adicionar views nao implementadas so por referencia visual.

## 3. R01/R02 — BAIXAS FINANCEIRAS: blueprint

**Rota vigente** `/apps/controllership-finance/closing/financial-settlements`. Mesmo hero e mesmo component tree ao alternar a pagar / a receber.

Hero:
- titulo **Baixas financeiras**; subtitulo: `Eventos de baixa a pagar e a receber para conferencia do fechamento.`
- KPIs ja disponiveis: **Eventos**, **Movimentacoes registradas — moeda 01** (ou label coerente com contrato), **Naturezas**, **Tipos de movimento**. KPI acompanha filtros aplicados e lado selecionado, sem mostrar taxas de crescimento ou comparacoes do periodo anterior: NAO EXISTEM no contrato atual.
- Banner/nota: resumo bruto de eventos pode incluir baixas, estornos e compensacoes e **nao significa** total liquido pago/recebido nem conciliacao bancaria. Manter nota sobre qualidade dos vinculos, ligada ao resumo; nao ocultar warnings.
- Toggle **Baixas a pagar | Baixas a receber** no inicio da area de filtros.
- Filtros existentes: `Data inicial`, `Data final`, `Natureza financeira` (codigo atual), `Tipo de movimento` (codigo atual), `Ordenar por`, `Direcao da ordenacao`. Nao converter campos de codigo em dropdowns populados sem endpoint comprovado. Validacao de datas/periodo existente permanece.
- Acoes: **Limpar filtros** sempre; **Atualizar**/icone refresh opcional para *forcar nova consulta* (retry/refresh manual), NUNCA requisitar clique para aplicar filtro. Nao chamar botao `Consultar`. Nao criar refresh duplicado no canto superior e no rodape: escolher **um** local consistente para refresh e documentar.
- Nao mover filtros de ordenacao para API nova ou mudar default de lado/data sem decisao.

Abaixo do hero: um unico painel de resultados `Baixas a pagar` ou `Baixas a receber` conforme selecao, com total de registros existente e `DataTableSection` do kit. Preservar colunas e significado atuais: data baixa, documento, parcela, fornecedor/cliente, natureza, tipo mov., direcao, moeda, valor, vencimento, vinculo e filial quando presentes. Nao mostrar links para OP/pedido que o contrato nao fornece. Nao misturar linhas de pagar com receber em uma visao que a API ainda nao suporta.

## 4. R03 — ESTOQUE HISTORICO P7: blueprint

**Rota vigente** `/apps/controllership-finance/closing/stock-inventory`.

Hero:
- titulo **Estoque historico — P7**; subtitulo: `Consulta operacional dos saldos historicos por competencia, filial e classificacao do produto.`
- KPIs existentes: **Disponibilidade** (texto `Disponivel`/`Parcialmente disponivel`/`Snapshot nao encontrado` etc., nao percentual fabricado); **Data-base** `DD/MM/AAAA` civil; **Itens**; **Filiais com dados**; **Valor historico total**. Se `source_missing`, exibir travessao/ausente e contagem legitima conforme contrato; NUNCA `R$ 0` falso. Nao inserir tendencia, comparacao mes a mes ou percentual de crescimento ausentes.
- Nota **consulta operacional nao equivalente a MATR460 oficial**, permanente e discreta.
- `incomplete`: aviso persistente com filiais faltantes; `source_missing`: mensagem especifica, nao silenciosa.
- Alternancia de visao existente **Todos os produtos | MP / PI / PA**, usando `CfSegmentToggle`. O MOCKUP mostrou separadamente MP, PI e PA; **isso NAO esta no contrato atual e nao deve ser implementado silenciosamente**.
- Filtros existentes: `Competencia` (YYYY-MM; ultimo dia do mes para snapshot), `Filial` (01/02/Todas como filtro, jamais permission), `Armazem` (codigo digitavel com debounce vigente). O MOCKUP ilustrou dropdown de armazem; **nao converter sem inventario de valores/endpoint oficial**.
- Acoes: **Limpar filtros** e refresh manual opcional, sem substituir auto-query por submit.
- Snapshot parcial: tot/summary representam apenas filiais com snapshot; aviso deve persistir, inclusive no modo Todas. Preservar `officialP7:false` e `parityStatus:TEST_NOT_RUN`.

Abaixo do hero, duas secoes separadas por gap oficial, **Resumo por tipo de produto** e **Resumo por armazem**. O MOCKUP colocou lado a lado, o que e apenas alternativa condicional: manter **stack vertical como default** quando existirem muitos tipos/armazens (12+ cards etc.), ou layout lado a lado SOMENTE se container comportar sem apertar/minimizar valores; breakpoints determinados pela plataforma. Usar `CfMetricStrip`; nao renderizar apenas MP/PI/PA no resumo quando escopo `all_products`: preservar todos os tipos, incluindo II, EM, MC etc. No resumo de armazem preservar **chave composta filial+armazem**, nao fundir deposito 01 das filiais 01/02.

Painel final **Detalhamento por produto e armazem** com `DataTableSection` real, contagem, paginacao, colunas ja suportadas (produto, descricao, tipo, grupo, unidade, armazem, filial, quantidade, valor historico). Nao adicionar percentual por armazem nem historico comparativo sem verificar contrato e contas.

## 5. Toolbar de tabela — contrato de UX, sem features ficticias

Componente de tabela ja existe (`DataTableSection` via `cfDataTableUi`); **plugin-ui first**. Estruturar toolbar responsiva com:
- titulo da secao a esquerda, contagem total proveniente do payload, respeitando paginacao;
- acoes a direita quando REALMENTE SUPORTADAS pela tabela: **Colunas**, **densidade/fonte**, **itens por pagina**, **ordenacao**, conforme kit e API;
- exportacao **Excel**: exibir somente se a implementacao atual suportar export correto de todo recorte autorizado (nao somente pagina atual, nao mascarar `incomplete` nem expor toda base sem limite). Se o kit possuir botao mas nao houver backend/export validado, **nao prometer export**, marcar `TO_INVENTORY` e pedir gate de feature.
- alternancia **Tabela | Cards**, como nas referencias comerciais, e somente TARGET FUTURO ate confirmar suporte real do kit, mapping de item e custo de manutencao. Nao criar view Cards/Board ficticia nem uma implementacao nova de tabela.
- acao por linha `...`, links, badges, avatares: nao adicionar sem caso de uso, dados/URL permitidos e acao reais. Nada decorativo ou clicavel sem comportamento verdadeiro.
- nao usar `BRL` automaticamente se a origem so fornece `moeda 01`; preservar representacao fiel.
- no mobile toolbar quebra linha, filtros e colunas seguem comportamento suportado pelo kit.

## 6. Componentes, estado e responsabilidades

Reusar do HEAD: `CfSectionCard`, `CfMetricStrip`, `CfSegmentToggle`, `CfFeedbackMessage`, `CfQueryErrorBanner`, `CfLoadingCard`, `DataTableSection`, `FilterInputField`, `FilterSelectField`, `FiltersRow`, `CfTitleWithHelp` e factories oficiais. Inventariar PageHero/hero equivalente no plugin-ui antes de compor; se adaptador `CfClosingHero` for criado, ele deve ter **apenas responsabilidade de layout/composicao** e props tipadas, sem acoplamento a query/HTTP/RBAC/custos. O contrato exato depende das exports HEAD.

Frontend mantém: auto-query ao alterar seletor/data valida, debounce 400 ms em campos de texto, request identity/AbortController contra stale responses, reset pagina quando filtros mudam, `Limpar` restaura defaults e refaz consulta, loading aria-busy, falha/S2S/RBAC com banners tipados, tema claro/escuro mesma arvore.

`Atualizar` (se adicionado) **apenas repete o request vigente**, nao valida filtros via botao nem reinicia filtros. Nao duplicar fetch ao alternar view/filtro e resetar pagina. Mensagem `Atualizado as HH:mm` so com timestamp REAL da consulta concluida; nao simular `lastUpdated` com hora da origem sem campo apropriado.

## 7. Densidade, responsividade e detalhes visuais

- Design system do Portal Comercial e uma referencia de composicao, nao autorizacao para copiar assets/servicos.
- Desktop amplo: hero com maximo de 4 a 5 KPIs, linha de filtros com wrapping; se houver seis filtros, quebrar em 2 linhas antes de comprimir inputs.
- Tablet: 2–3 cards por linha conforme token e largura minima; filtros fluem em 2 colunas.
- Mobile: cards e campos empilham, acoes quebram sem overflow; tabela usa estrategia oficial (scroll horizontal dentro do painel ou alternativa do kit), nao estoura o viewport. Nao mudar automaticamente para Cards sem feature aprov.
- Padding/gaps: reuso tokens e `cf-page-stack` inclusive em wrapper de `aria-busy` (correcao doc 30); nao inventar espacos arbitrarios, evitar blocos grudados.
- Estados e acessibilidade: tab/foco, teclado, role/aria do plugin-ui, contraste, acao limpa e labels PT-BR; `aria-busy` aplicado ao conjunto de resultados, sem roubar foco.
- Nao adicionar indicadores comparativos, porcentagens, contagem de filiais 3/4, valores em reais ou quaisquer linhas demonstrativas copiadas do MOCKUP: sao demonstracoes visuais, nao evidencia TOTVS.

## 8. Fluxo de implementacao autorizado / gates

**ESTE DOCUMENTO EH ESPECIFICACAO TARGET E NAO GO DE RUNTIME.**

G0 READ: HEAD/status, Project Instructions, .cursor, docs oficiais, README, doc 30, doc 49, atualizacao Help, testes. Inventariar hero exports, wrappers, tableau toolbar/acoes e contratos atuais. Produzir matriz `VISUAL_REUSE` e `MISSING_FEATURES`.

G1 DESIGN: apresentar componente hero escolhido, slots, layout de filtros, composicao de KPIs, toolbar atual e limitacoes, mapeamento de cada campo a fonte REAL, breakpoints, acessibilidade. Separar `REUSE`, `LOCAL_ADAPTER`, `TARGET_FUTURE`, `DECISION_REQUIRED`.

G2 GATE: se apenas rearranjo UI reutilizando contratos existentes, pedir autorizacao transversal para runtime por pagina; se adicionar export, Cards, metrics comparativas, opcoes MP/PI/PA isoladas ou novos endpoints, parar em `DECISION_REQUIRED` e nao misturar tais features no diff de layout.

G3 IMPLEMENT minimal diff: preferir **R01/R02 primeiro**, depois **R03**; nao tocar api-delpi/BFF nem menus globais a menos que gate distinto e justificativa. Atualizar Help no mesmo diff.

G4 VERIFY: unitarios/estruturais e2e (auto-query, tab, filtros, debounce, sort/pagination, erro, parciais, sem dados), lint, tsc, build; verificacao visual em claro/escuro, desktop/tablet/mobile; medir gap real entre hero e resultados. Nao declarar test PASS pelo bundle.

G5 DOCUMENT/COMMIT: atualizar README, doc 30 e este 50 com resultado, arquivos, screenshots (somente se autorizado armazenar), testes, gaps; git diff --check, SHA. Push/deploy SSH requer **autorizacao operacional explicita na task de execucao** e runbook, sem inferir permissao deste documento.

## 9. Criterios de aceite por dimensao

- AC01: heros das duas paginas coerentes e diferentes somente nos slots funcionais; titulo legivel e identidade oficial.
- AC02: KPIs mostram exclusivamente metricas existentes no payload, atualizam automaticamente apos filtros; ausencia/parcialidade distinguiveis.
- AC03: filtros dentro do hero, navegaveis em teclado/mobile, labels corretos, sem envio obrigatorio.
- AC04: acao Limpar visivel e operacional; refresh opcional quando realmente implementado, nao cria fetch duplo.
- AC05: `CfFeedbackMessage` persistente para notas/avisos; nao texto cru fora do design system.
- AC06: Secoes/resumos/tabela mantem gap centralizado efetivo `--cf-section-gap` no DOM.
- AC07: toolkit da tabela exibe somente acoes existentes e funcionais, paginacao/totais corretos, sem Excel parcial nem view ficticia.
- AC08: R03 preserva agrupamentos por todos os tipos e por filial+armazem; status `source_missing/incomplete`, data de fechamento civil.
- AC09: R01/R02 preserva diferenca a pagar/a receber, moeda, vinculos e semantics de eventos; nao mistura dados.
- AC10: 2 temas, 3 classes de viewport, acessibilidade e testes autom/foco/resposta obsoleta.
- AC11: nenhuma permission extra/endpoint/backend alterado por estetica; no browser direct api-delpi.
- AC12: veredito separado para design, codigo, teste, deploy e outcome real: `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`.

## 10. Handoff claro ao Devin

**Missao**: redesenhar SOMENTE a composicao das paginas de baixas e estoque para seguir o hero/filtros integrado do Portal, mantendo todas as regras atuais. Primeiro entregar inventario real de componentes `plugin-ui` e plano de arquivos/slots. Em caso de duvida, nao ampliar produto por conta propria. Mockups ilustram **forma e hierarquia**, nao dataset, metricas nem features homologadas. Nao aceitar como PROVEN qualquer item baseado exclusivamente no desenho.

**Resultado G1 esperado**:
```text
HEAD / STATUS:
PLUGIN_UI_HERO_FOUND:
HERO_CHROME_REUSED:
FILTER_COMPONENTS_REUSED:
KPI_COMPONENTS_REUSED:
TABLE_TOOLBAR_CAPABILITIES_PROVEN:
FIELDS_AND_METRICS_REAL:
MOCKUP_ONLY_ELEMENTS_EXCLUDED:
FILES_TO_CHANGE:
AUTH_AND_API_DIFF: NONE
DECISION_REQUIRED:
RUNTIME_GATE: PENDING
```


## 11. REVIEW VISUAL PO - REWORK de fidelidade (21/10/2026)

O PO comparou mockups de referencia com o resultado do commit `7254eef580` e informou que falta parte relevante do visual proposto. **Conclusao do review de fidelidade: REWORK**, distinta do sucesso de build e integracao. A entrega confirmou PageHero/hi ghlights/filtros e toolbar de fonte, mas nao comprovou paridade de hierarquia e acabamento com os mockups. Nao interpretar aceite anterior de estrutura como aceite final do design.

**Gaps visuais que exigem inventario + demonstracao antes/depois**: (1) KPI cards ainda muito textuais, faltam hierarquia de numero/titulo e eventual iconografia nativa do kit; (2) divisao e alinhamento da area de filtros/alternancia/acoes ainda pouco distintos; (3) notas e avisos devem usar feedback semantico com contraste e posicionamento consistente, sem parecer texto bruto; (4) toolbar de resultados precisa organizacao clara, nao prometer funcoes ausentes; (5) resumo P7 exige melhor leitura visual da categoria, valor e quantidade, sem eliminar categorias. Comparar visualmente R01/R02 e R03 em desktop dark/light, tablet e mobile; registrar componentes oficiais reais e screenshot de cada estado.

**Limite funcional**: as referencias geradas contem numeros, percentuais, datas, links, view Cards e botao Excel ilustrativos. Nao criar metrics de variacao, opcoes MP/PI/PA separadas, exportacao, links, badges ou controles inertes sem contrato e decisao do PO. Existe escolha real entre fidelidade exclusivamente visual com componentes atuais e expansao de produto: `DECISION_REQUIRED` para qualquer feature nova. O rework visual pode preparar layout/slots, mas deve manter action-only real, texto correto, auto-query e autorizacao intactos.

**Gates de aceite reforcados**: `VISUAL_DIFF_MATRIX` por secao e pagina (mockup | runtime atual | correcao proposta | componente plugin-ui | origem de dados | teste); `KPI_VISUAL_HIERARCHY=REVIEW_REQUIRED`; `FILTER_ACTION_HIERARCHY=REVIEW_REQUIRED`; `STATUS_BANNER_VISUAL=REVIEW_REQUIRED`; `TABLE_TOOLBAR_HIERARCHY=REVIEW_REQUIRED`; `P7_SUMMARY_CARD_HIERARCHY=REVIEW_REQUIRED`. O executor deve apresentar evidencias visuais autenticadas antes da conclusao; smoke nao executado = `TEST_NOT_RUN`. Deploy/commit nao supre o gate visual.
