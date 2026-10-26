# PROC-0076 — R2: decisao de produto sobre fontes publicas e proxima entrega

> **DECISAO DO PRODUCT OWNER: APPROVED DIRECTION (2026-10-26).**
> **Execucao: PLANNED / TEST_NOT_RUN / NOT DEPLOYED.**
> **Baseline inspecionado:** origin/main 25060ff33fa324af24349358ecdcbbde0eac30b4; revalidar HEAD e working tree antes da execucao.
> **Tema:** Transformometro PROC-0076 / GLPI #527 — Inteligencia de Mercado para Compras e Vendas.
> **Esta decisao SUBSTITUI o alvo de fonte primaria Pink Sheet/LME do planejamento P0, NAO reescreve a evidencia historica e NAO altera retroativamente o codigo ou os dados ja coletados.**
> **Plano tecnico e rotas-alvo:** [PROC-0076 R2 — External Data/BFF Contracts](../shared-integrations/PROC-0076-R2-EXTERNAL-DATA-COMEX-IBGE-BCB-CONTRACT-AND-EXECUTION-20261026.md).

## 1. Decisao aprovada

Implementar as fontes **Comex Stat (MDIC), IBGE (IPP/SIDRA) e Banco Central do Brasil (PTAX)** na mesma vertical de Inteligencia de Mercado do novo Portal Suprimentos.

Pipeline obrigatorio:

    Fontes oficiais MDIC + IBGE + BCB
      → external-data-api (acquisition, validation, historical persistence)
      → postgres-plugins / schema external_data (owner exclusivo)
      → external-data-api REST interno, S2S
      → supplies-api Flask (BFF read models, Core AuthZ)
      → plugins/supplies (dashboard kit-first, UI em PT-BR)

A proxima entrega deve **comecar pelo produtor**, comprovando origem, tipo de metrica, historico, deduplicacao e acesso interno antes de implementar os novos read models no BFF; so depois adaptar a pagina e Ajuda. Nao iniciar por mocks no frontend como entrega real.

**Nao criar nova API nem schema supplies para historico externo.** Reutilizar o schema external_data, catalogo tecnico/ingestion_runs e a serie PTAX existente quando seus contratos forem validos. Novas tabelas sao migrations ADITIVAS apenas sob owner external-data-api. Nenhum SELECT cruzado no DB a partir de supplies-api. Nenhuma nova permission: effective Core supplies.access. O MFE consome exclusivamente supplies-api.

## 2. Semantica NAO NEGOCIAVEL das tres fontes

| Fonte | O que mede | Granularidade | Unidade | Rotulo obrigatorio no Portal |
|---|---|---|---|---|
| MDIC / Comex Stat, importacoes NCM | Valor FOB e massa liquida de mercadorias importadas; opcionalmente valor unitario FOB agregado | Mes / ano, com desagregacao por NCM e dimensoes homologadas | US$ FOB, kg; indicador derivado US$/t | Valor medio FOB de importacao, **nao** preco spot/LME, nem preco de compra DELPI |
| IBGE / IPP setor de metalurgia | Variacao/numero-indice dos precos recebidos por produtores nacionais | Mes / ano | Indice (base metodologica vigente) ou percentual de variacao | IPP Metalurgia / tendencia industrial, **nao** US$/t nem cotacao individual de cobre/zinco |
| BCB / PTAX USD/BRL | Cambio oficial com tipo de boletim e compra/venda identificados | Dia; agregacoes mensais/anuais derivadas | BRL por USD | PTAX referencia, com tipo e data; nao spot garantido nem taxa negociada DELPI |

**Proibido:** somar ou comparar escalas de IPP com US$/t num mesmo eixo como se fossem precos equivalentes; converter o indice IPP para BRL; chamar FOB por NCM de cotacao internacional do metal; criar cotacao diaria de metal a partir de agregacao mensal. A granularidade disponivel deve vir do catalogo real.

### Formula Comex Stat, com rastreabilidade

Para o mesmo mes, NCM e dimensoes homologadas, usando somente linhas elegiveis:

    unit_value_usd_per_t = SUM(VL_FOB) / (SUM(KG_LIQUIDO) / 1000)

Quando massa <= 0, resultado e NULL/no_data ou qualidade invalida, nunca zero artificial, infinito ou divisao por zero. Usar Decimal/NUMERIC. Agregar primeiro numerador e denominador; nunca calcular media aritmetica das razoes das linhas. Valor FOB nao inclui automaticamente frete/seguro/impostos e nao deve ser descrito como preco CIF. Se houver diferentes NCM/paises/grades, mostrar cobertura e segmentacao; nao agregar familias heterogeneas sem aprovacao explicita de Joici/Compras.

**Proveniencia:** CO_ANO, CO_MES, CO_NCM, CO_PAIS, SG_UF_NCM e demais dimensoes selecionadas; KG_LIQUIDO, VL_FOB, classificacao NCM vigente e versao/tabela de correlacao, arquivo/URL/revisao e recuperacao, manifest/hash de lote e politicas de selecao. NCM por familia de metal = MAPPING TO_INVENTORY, nunca hardcode inventado.

### Politica IBGE

P0 R2 usa **IPP metalurgia como serie setorial**, sem fingir granularidade por metal. Priorizar SIDRA/API oficial se o codigo de tabela/variavel/atividade corresponder ao IPP atual; tabela 6903 e candidata a validar no catalogo oficial. Se a tabela atual foi substituida/rebaseada, congelar metadata/codigo reais antes de produzir adapter. Armazenar indice com base, classificacao da atividade, variavel, data de referencia, revisao e fonte. Se so existir variacao, nao fabricar numero-indice.

### Politica BCB

Reusar o adapter e a tabela fx_rate_observations ja existentes sempre que o contrato PTAX for confirmado. Preservar rate_kind, boletim de fechamento, compra/venda, data e source_id. **O acesso PTAX da producao teve HTTP 403 reportado**; nao contornar WAF, nem afirmar feed operacional. Executar validacao tecnica em ambiente autorizado e propor caminho oficial (acesso/egress/documentacao) sem trocar silenciosamente o tipo de taxa. A indisponibilidade da PTAX nao pode bloquear consulta em USD do Comex nem o IPP.

## 3. Estado real versus alvo

| Superficie | CURRENT (HEAD examinado) | TARGET R2 |
|---|---|---|
| external-data-api | CNPJ via BrasilAPI + market-data com PTAX e World Bank/Pink Sheet; market observations em external_data, V001–V003 no main | Adapters Comex CSV/IBGE SIDRA, novas tabelas com historico/revisoes e API S2S; PTAX reutilizada |
| supplies-api | /market-intelligence/{filters,summary,series,monthly-averages} com foco em metal USD/BRL | Read models diferenciados por metric_kind/fonte/unidade, sem breaking de consumidores antigos |
| plugins/supplies | Pagina de Inteligencia de Mercado publicada como deep-link, sem link hub; kit-first | Dashboard por modulos/tabs Valor Medio de Importacao, IPP Metalurgia e Cambio, mantendo identidade visual do Portal |
| Direitos Pink Sheet/LME | R1.1/R1.2 e cuarentena no PR #113 (nao incorporados ao main no momento do inventario) | Trilha antiga explicitamente LEGACY/QUARANTINED; nao migrar precos LME para valores Comex, nao apagar historico |
| Runtime | Gate E11 e smoke federado autenticado INCONCLUSIVE segundo README; PTAX HTTP 403 reportado | Nova pagina nao e declarada PASS sem gate, fonte, calculos e smoke |
| Governanca | PR #111 (P0 historico) e PR #113 (quarentena R1.1/R1.2) draft | Manter historia/seguranca; rebase e reconciliacao; nao mesclar PR antigo como contrato R2 |

### EXECUTION_DRIFT / CONTRACT_EVOLUTION_REQUIRED

A decisao do PO altera materialmente o conceito de dashboard: antes valores mensais internacionais de metais da Pink Sheet; agora **valor unitario de importacao + indice industrial + cambio**. Os DTOs antigos de price/quote nao podem receber apenas outra source_id mantendo o mesmo nome/conceito. Criar contratos ou discriminador semantico versionado/novos read models, preservando o caminho antigo em quarentena, sem quebrar os consumidores existentes.

**Prioridade de fonte mudou; risco de vazamento historico nao desapareceu.** A implementacao R1.3/readiness/quarentena discutida no PR #113 continua uma obrigacao de seguranca enquanto dados Pink Sheet/LME existirem no DB. Nao ativar exibição de series legadas. Resolver via trilha delimitada do PR, nao dentro de adapters Comex por conveniencia.

## 4. Requisitos e aceites da proxima entrega

| RQ | Requisito | Etapa | Aceite |
|---|---|---|---|
| R2-01 | Ingestao oficial Comex, modelo NCM/dimensoes e historico | EX1 | Uma competencia + sibling validada com arquivo oficial, checksum, idempotencia e validacao de totais/linhas |
| R2-02 | Indice IBGE IPP Metalurgia | EX1 | Serie oficial com atividade/variavel/base, revisao, data e qualidade rastreadas |
| R2-03 | PTAX reutilizada e degradacao independente | EX1 | USD/IPP funcionam sem PTAX; BRL nao e inventado; bloqueio 403 sinalizado |
| R2-04 | Historico armazenado no schema do owner externo | EX1 | Novas migrations, grants, indices, reprocessamento, recuperacao e segregacao provados em PG descartavel |
| R2-05 | Contratos internos HTTP/S2S autenticados | EX1 | Catalogo mais GET Comex/IPP/FX, 401/403/422, disponibilidade, pagina bounded; sem acesso DB cruzado |
| R2-06 | supplies-api BFF compoe read models | EX2 | DTOs fonte/metric_kind/unit/granularity sem conversao indevida; Core fail-closed |
| R2-07 | Dashboard usa plugin-ui e diferencia fontes | EX3 | Filtros, cards, graficos, tabelas e informacao metodologica compatíveis com metrics |
| R2-08 | Sem regressao antiga/CNPJ e sem leaks LME | TODAS | Testes negativos/sibling e verificacao da quarentena, nenhum merge desautorizado |
| R2-09 | Help + UX + runtime evidenciados | EX3/EX4 | Help sincronizada, URL/F5, mobile, tema, teclado, smoke federado autenticado ou INCONCLUSIVE explicito |
| R2-10 | Go-live e rollback guardados | EX4 | Source rights/compliance, backup/migration, digest, smoke e rollback/kill-switch antes de PASS |

## 5. Wireframe de referencia (TARGET, NAO IMPLEMENTADO)

    INTELIGENCIA DE MERCADO                           [? AJUDA]
    Referencias para Compras e Vendas | Fontes + atualizacao + metodologia

    [ IMPORTACOES MDIC ] [ PREÇOS INDUSTRIAIS IBGE ] [ CAMBIO BCB ]

    A) IMPORTACOES / COMEX STAT
    [NCM / Familia aprovada] [Origem] [UF] [Periodo de/ate] [USD/t | outros valores]
    [FOB US$] [Massa t] [USD/t valor medio] [Variacao do indicador]
    [Grafico mensal] [Tabela por NCM/competencia/pais + cobertura]
    Notas: indicador agregado; nao cotacao LME nem preco de compra DELPI.

    B) IPP / IBGE
    [Atividade: Metalurgia] [Variavel: indice/variacao] [Periodo]
    [Numero-indice] [Variacao mensal %] [Acumulado % quando existir]
    [Grafico mensal] [Tabela metadata da serie, revisoes e base]
    Notas: indice setorial; nao preco por metal.

    C) CAMBIO / BCB
    [PTAX fechamento: compra/venda] [Periodo dia/mes/ano]
    [Taxa] [Media mensal conforme metodo] [Data do ultimo boletim]
    [Grafico FX] [Tabela valores oficiais + faltantes]
    Notas: PTAX pode estar indisponivel por egress 403, sem fallback inventado.

    Em todos os modulos: loading/empty/partial/stale/error/401/403/404;
    mostrar label, unidade, periodo, fonte, ultima publicacao e coleta.

Kit-first: reutilizar @delpi/plugin-ui (PageHero, filtros, KPI, SeriesChart, DataTable, estados); CSS apenas .dashboard-supplies-portal. Nenhuma permission por fonte/aba. O manifesto e a navegacao so evoluem com gate E11 reconciliado.

## 6. Gates e sequencia

1. **EX0 SOURCE/CONTRACT FREEZE:** mapear NCM/familias com Compras, tabela SIDRA IPP com codigo/variavel corretos, URLs oficiais e termos, esquema/retencao. Pode executar levantamento sem deploy.
2. **EX1 external-data-api:** migrations novas aditivas, providers MDIC+IBGE, reuse PTAX, jobs/backfill/rate limits/telemetria, S2S REST, testes PostgreSQL. Nao alterar migrations aplicadas, nao usar scraping do front do Comex.
3. **EX2 supplies-api:** consumers HTTP S2S e contratos de metric_kind, filtros por NCM/atividade/pais/periodo, AuthZ Core, calculos no BFF quando apropriado, testes de positivos/siblings/negativos.
4. **EX3 MFE:** compor abas/cards/chart/tabela com kit existente e sincronizar Ajuda, depois de GATE E11 e autorizacao conforme authorities; deep link/F5, 403/404/partial e mobile/tema/foco.
5. **EX4 E2E/acceptance:** origem→histórico→S2S→BFF→dashboard com dado real permitido; autorizar deploy apenas com gates, prova de rollback e smoke autenticado.

Cada EX* deve devolver BASE HEAD/FINAL HEAD/status, owner, RQ/AC, testes, contrato, residual, gaps, evidencia e SHAs. **Esta decisao autoriza planejamento da proxima entrega, NAO autoriza rodar migrations em producao, ativar feeds, substituir fontes ou declarar PROC-0076 PASS.**

## 7. Fontes oficiais a revalidar pelo implementador

- MDIC dados abertos CSV por NCM, layout de importacao: https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/base-de-dados-bruta (consultado 2026-10-26; meses ate 2026-09). Dados FOB e KG_LIQUIDO, nao preco spot. Confirmar aviso de uso, esquema e NCM vigente por periodo.
- IBGE IPP metodologia/variaveis oficiais e divulgacao SIDRA: https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9282-indice-de-precos-ao-produtor-industrias-extrativas-e-de-transformacao.html (consultado 2026-10-26; divulgacao setembro prevista em 2026-10-27); candidato SIDRA tabela 6903, verificar codigos e base.
- BCB PTAX: https://dadosabertos.bcb.gov.br/dataset/taxas-de-cambio-todos-os-boletins-diarios (consultado 2026-10-26; ODbL no catalogo). Validar endpoint/boletim e egress autorizado.

Os links oficiais demonstram dados publicados, mas direitos exatos de coleta, armazenamento, modificacao e distribuicao devem ser registrados por fonte/uso. Nao concluir "livre de toda restricao" apenas por ser dado aberto.

## 8. Proibicoes

Nao reescrever V001–V004; nao deletar historico LME; nao ativar Pink Sheet; nao passar dados de importacao por endpoint quote com semantica falsa; nao inferir NCM, indice IPP ou taxa FX; nao pular Core AuthZ ou criar grants; nao implementar modulo no legado dashboard-supplies; nao permitir download arbitrario externo (SSRF); nao contornar 403 do BCB; nao ativar menu antes de reconciliar gate; nao chamar importacao do MDIC de compra da DELPI. READ → VERIFY → CLASSIFY → DESIGN CONTRACT → IMPLEMENT OWNER → TEST → DOCUMENT → REPORT.
