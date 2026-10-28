# PROC-0076 — Guia das perspectivas e validação Comex com Compras

> **Data:** 2026-10-27 · **Tipo:** documentação funcional e registro de homologação visual · **Escopo:** Portal Suprimentos → Inteligência de Mercado (`/apps/supplies/market-intelligence`).
>
> **Classificação:** `PROVEN` para comportamentos observados nas capturas e contratos já inspecionados; `TO_INVENTORY` para confirmação de runtime fora das capturas; `PLANNED` para seleção de materiais/NCMs com Compras e Fiscal. **Este registro não constitui homologação de nenhuma NCM, autorização de novo feed nem aceite mobile/tema claro.**

## 1. Objetivo e navegação

A Inteligência de Mercado reúne **três perspectivas na mesma página**: **Metais**, **Câmbio** e **Indicadores** (subperspectivas **IPP/IBGE** e **Comex/NCM**). Filtros de período e de granularidade (Dia, Semana, Mês, Ano, conforme suporte da fonte) conduzem gráfico, tabela e indicadores. A fonte e a unidade devem ficar explícitas. Exportações usam apenas observações disponíveis e autorizadas. Ausência de observação não equivale a valor zero.

O Portal apresenta informações e compõe a experiência em `plugins/supplies`; `supplies-api` é o BFF e executa AuthZ server-side com permissions efetivas da Core; `external-data-api` é o owner das integrações de mercado. Não há acesso direto do MFE a provedores externos.

## 2. Explicação de cada tela

| Tela | Pergunta de negócio | Fonte / dado | Unidade e frequência | Evidência e estado |
|---|---|---|---|---|
| **Metais** | Como se movimentam as referências internacionais recentes dos metais? | MetalCharts: alumínio, cobre, chumbo, níquel e zinco; estanho sem cobertura homologada | Alumínio/níquel/chumbo/zinco em **US$/t**; cobre COMEX **US$/lb**; observações diárias e agregações derivadas, conforme disponibilidade | `PROVEN` em screenshot desktop escuro: cards selecionáveis, KPIs, unidades e gráfico. Fonte/tempo de expiração exigem atenção |
| **Câmbio** | Qual é o histórico do dólar oficial PTAX para referência de custos? | Banco Central do Brasil, compra/venda de fechamento | **R$/US$**, com agregações diária/semanal/mensal/anual de observações oficiais | `PROVEN` em screenshot desktop escuro: último valor, média, variação, cobertura e gráfico real |
| **Indicadores → IPP (IBGE)** | Como evolui o preço recebido pela indústria de metalurgia? | IBGE/SIDRA: número-índice e variação mensal | **Índice** (com base explicitada na série) ou **%**, conforme opção; publicação mensal | `PROVEN` em screenshot desktop escuro: último valor, média, mínimo, máximo, cobertura e gráfico do número-índice, incluindo aviso honesto de competências sem observação |
| **Indicadores → Comex (NCM)** | Quanto, em valor e volume, o Brasil importa dos produtos classificados nas NCMs relevantes para a DELPI? | Comex Stat/MDIC: valor FOB e peso líquido, mediante NCM homologada; valor médio indicativo derivado de FOB/peso quando metodologicamente válido | Valores **US$ FOB**, peso **kg/t** e unidade indicativa **US$/t**; estatísticas mensais | `PROVEN` apenas o **estado de configuração pendente** em screenshot desktop escuro; **nenhuma NCM homologada, nenhum dado ou gráfico real Comex demonstrado** |

### 2.1 Metais — interpretação

- A seleção dos seis cards é visual e permite seleção múltipla; selecionar **estanho** não significa que a fonte esteja homologada.
- Cobre **COMEX** não é intercambiável com fechamento **LME** físico. Não misturar séries com bases diferentes sem explicitar metodologia.
- O gráfico e a comparação devem separar unidades incompatíveis, especialmente **US$/lb** versus **US$/t**.
- **Último valor, média do período, variação e cobertura** referem-se apenas às observações realmente recebidas dentro do filtro. Janela de 13 meses com apenas 2 competências disponíveis é parcial, não um histórico anual completo.
- A MetalCharts está sob política de cache operacional temporário; não há autorização presumida para retenção permanente. Atualização recorrente depende de conectividade homologada (bloqueio Sophos reportado para `api.metalcharts.org`).

### 2.2 Câmbio — interpretação

- **Venda (fechamento)** e **Compra (fechamento)** são séries distintas; o valor `R$/US$` representa reais por dólar.
- Médias/variações dos agrupamentos são derivados das observações oficiais válidas. Finais de semana e feriados não geram zeros.
- Um KPI de **cobertura 13/13** na visão mensal significa presença de competência nos 13 meses, **não 100% dos dias úteis cobertos**.
- Backfill PTAX foi reportado como concluído; o feed habilitado **não prova agendamento automático**. Scheduler diário permanece `PENDING` até evidência operacional.

### 2.3 IPP (IBGE) — interpretação

- **Número-índice** e **variação mês/mês (%)** têm semânticas diferentes: índice não é cotação em US$/t e variação percentual não é nível do índice.
- Para o **número-índice**, o BFF passou a preencher média, menor e maior valor usando observações válidas da janela selecionada (`mean_of_valid_observations/v1`, `extremes_of_valid_observations/v1`). Para a **variação %**, aplicar os KPIs aprovados da série, sem inventar percentual sobre percentual.
- Competências ainda não publicadas ou não coletadas são lacunas legítimas; o aviso de dados parciais deve mencionar **a própria série**, não câmbio.

### 2.4 Comex (NCM) — interpretação

- **Comex Stat** é a base oficial de estatísticas de comércio exterior do MDIC, não uma tabela de cotações spot dos metais.
- **FOB total** representa o valor declarado das importações na métrica do conjunto filtrado; **peso líquido total** mede a massa declarada; **valor médio indicativo** exige método e unidade explícitos (por exemplo, FOB USD dividido pela massa em toneladas), com cuidados de escopo e qualidade.
- A seleção de NCM é essencial: uma família de materiais pode possuir várias NCMs e uma mesma NCM pode abranger especificações distintas. **Uma NCM não é sinônimo de um metal**, nem preço FOB/t equivale à MetalCharts ou LME.
- Na captura de 2026-10-27, a aba mostra **“Configuração pendente”**, sem NCM homologada, e três indicadores sem valores. Isso é um **estado vazio honesto**, não falha de carregamento comprovada.
- Refinamento de UX residual: reduzir repetição “Próximos passos: Próximo passo...” e preferir estado vazio compacto em vez de cards com traços enquanto não houver NCM autorizada (`PLANNED`, sem execução autorizada por esta nota).

## 3. Validação necessária com Compras e Fiscal — Comex

**Decisão de produto:** a lista de monitoramento **não será construída por adivinhação de NCMs**. Compras escolhe relevância, aplicação e prioridade; Fiscal valida a classificação oficial; Suprimentos homologa escopo e indicadores; Integrações verifica disponibilidade/contrato MDIC antes de ativação.

### 3.1 Dados mínimos para homologar um item

| Campo | Definição / regra | Responsável proposto |
|---|---|---|
| Família/material monitorado | Nome de negócio realmente usado pela DELPI | Compras |
| Descrição interna e especificação | Produto, forma, liga, bitola/qualidade quando relevante | Compras |
| Código NCM | **8 dígitos**; originar de cadastro/documento válido, não inferir por similaridade | Fiscal valida; Compras identifica |
| Descrição oficial e abrangência | Texto oficial e ressalvas quanto à representatividade do produto | Fiscal |
| Objetivo da consulta | FOB total, peso, valor médio indicativo, evolução, países de origem etc. | Compras |
| Unidade e metodologia | US$ FOB, kg/t, US$/t indicativo (se aplicável); comparar apenas grupos compatíveis | Suprimentos + Integrações |
| Prioridade e justificativa | Alta/média/baixa; relevância para custo/volume/risco | Compras |
| Histórico desejado | Sugestão inicial: 36 meses, sujeito à cobertura do MDIC | Compras |
| Responsável e decisão | Nome/função, data, evidência de validação e estado | Compras + Fiscal + Suprimentos |
| Status | `PENDING` / `APPROVED` / `REJECTED` com trilha de decisão | Owner da homologação |

### 3.2 Perguntas obrigatórias na reunião

1. Quais materiais e famílias realmente comprados pela DELPI mais afetam custo, volume ou risco?
2. Quais são as NCMs **efetivamente utilizadas** nos cadastros e documentos fiscais? Há mais de uma para cada família?
3. A DELPI precisa acompanhar **importações brasileiras** ou **preço internacional**? Quais decisões serão tomadas com cada indicador?
4. Quais dimensões fazem sentido: FOB, peso, valor médio indicativo, país de origem e histórico? Quais comparações seriam enganosas?
5. Quem aprova a lista e quem a revisa quando NCM, especificação ou necessidade de Compras mudar?

### 3.3 Lista de candidatos — NÃO homologada

| Família candidata | Produto real comprado pela DELPI | NCM | Prioridade | Estado |
|---|---|---|---|---|
| Cobre | A identificar | Não informada | A definir | `TO_INVENTORY` |
| Alumínio | A identificar | Não informada | A definir | `TO_INVENTORY` |
| Zinco | A identificar | Não informada | A definir | `TO_INVENTORY` |
| Níquel | A identificar | Não informada | A definir | `TO_INVENTORY` |
| Chumbo | A identificar | Não informada | A definir | `TO_INVENTORY` |
| Estanho | A identificar | Não informada | A definir | `TO_INVENTORY` |

**A lista reflete os seis metais hoje exibidos no Portal; não prova que a DELPI compra cada metal diretamente e não constitui cadastro NCM.** Começar por três a cinco itens reais prioritários, a definir com Compras.

### 3.4 GATE-COMEX-NCM (ainda não fechado)

| Critério | Estado atual |
|---|---|
| Inventário real de materiais e necessidade de negócio | `TO_INVENTORY` |
| NCMs oficiais confirmadas pelo Fiscal | `PENDING` |
| Priorização e owner de Compras definidos | `PENDING` |
| Metodologia e unidades validadas para cada indicador | `PENDING` |
| Disponibilidade/saúde da fonte Comex Stat MDIC | `PENDING` (feed não operacional nas evidências) |
| AuthZ, BFF, contrato, testes e smoke com dados reais | `TEST_NOT_RUN` para NCMs futuras |
| Autorização para ativação | `PENDING` |

**Condição de saída:** inventário aprovado + validação Fiscal + homologação Suprimentos + fonte/contrato saudáveis + autorização de execução. Esta documentação **não autoriza** cadastrar NCMs de exemplo, ativar feed ou modificar schemas.

## 4. Registro de validação visual pelo Product Owner

**Evidência:** capturas fornecidas pelo PO na conversa em 2026-10-27, no domínio `minhadelpi.com.br`. As capturas comprovam **apresentação desktop no tema escuro**, não smoke automatizado nem autorização de fonte.

| Perspectiva | Resultado da revisão de screenshot | Limitação |
|---|---|---|
| Metais | `PASS` visual desktop/escuro — cards, unidade, seleção e KPIs observados | Atualização MetalCharts recorrente, mobile/tema claro e exportação ainda não provados |
| Câmbio | `PASS` visual desktop/escuro — cards e gráfico PTAX com valores | Scheduler e execução recorrente não provados |
| IPP | `PASS` visual desktop/escuro — média/mínimo/máximo corrigidos, série e gráfico | Não prova todas as séries, mobile, tema claro e exports |
| Comex | `PASS_WITH_RESIDUAL` do **estado pendente** desktop/escuro; nenhum valor inventado | Nenhuma NCM homologada nem dado real Comex; texto redundante |

**Aceite global da revisão por captura:** `ACCEPT_WITH_RESIDUAL`. Não declarar `GATE-FEATURE PASS` integral apenas com screenshots. Permanecem `INCONCLUSIVE` mobile, tema claro, teclado/foco, exportações; `PENDING` scheduler PTAX, egresso Sophos MetalCharts e NCMs Comex.

## 5. Referências canônicas

- [README Suprimentos](./README.md)
- [Contrato de comportamento UX R4](./PROC-0076-R4-UX-BEHAVIOR-CONTRACT.md)
- [Contratos e wireframes BFF de Inteligência de Mercado](./PROC-0076-MARKET-INTELLIGENCE-BFF-CONTRACTS-AND-WIREFRAMES-20261026.md)
- [Evidências técnicas R5 (MetalCharts, PTAX, IPP e smoke)](../shared-integrations/PROC-0076-R5-METALCHARTS-IMPLEMENTATION-AND-EVIDENCE-20261027.md)
- [Direitos de uso de fontes](../shared-integrations/PROC-0076-SOURCE-RIGHTS-EVIDENCE-20261027.md)
