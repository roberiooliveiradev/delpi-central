# 117 — ANALYSIS-001 — Inventário do Processo Real de Fechamento de Joyce (AS-IS)

**EXECUTION_ID:** `CF-PROC0072-ANALYSIS-INVENTORY-001`
**Produto:** Portal Controladoria & Finanças — Minha DELPI
**Processo:** PROC-0072 — Gestão do Fechamento Mensal da Controladoria
**Etapa:** ANALYSIS-001 — Reconstrução AS-IS (documentação e inventário somente; nenhuma alteração de runtime)
**Data de execução:** 2026-10-28
**Executor:** Joyce = **Joici Motta** (Controladoria; usuário Protheus `JOICI`, gestora do processo no TÉO). A grafia "Joyce" do pedido e "Joici" dos registros referem-se à mesma pessoa, confirmado pela tela de login e pelos participantes da gravação.

---

## 1. Resumo executivo

O fechamento mensal executado por Joyce foi reconstruído com evidência primária verificada: gravação de 54:44 (transcrição integral própria + 18 quadros inspecionados), 19 arquivos operacionais da competência 09/2026 e o corpus documental do PROC-0072 no TÉO/Transformômetro (43 documentos, R01–R42, C01–C10, CH01–CH04).

O processo é uma **orquestração manual de processamentos ERP, relatórios e planilhas**, conduzida em paralelo para otimizar tempo, com uma **conciliação tripla central** (`Entradas/Saídas − P7 − Saldo em Processo = R$ 0,00`, paridade exata conforme doc TÉO 06.2), investigação de divergências por grupo de material, classificação manual de centros de custo na SD1, consolidação de um pacote por destinatário (Fiscal/Contábil/Contabilidade/DRE) e tratamento de dúvidas até o encerramento do ciclo.

Na demonstração, a conciliação apresentou divergência residual de **R$ 48.660,78** (fala registrada como 48.660,77; ver §11), localizada preliminarmente no grupo matéria-prima/material em processo, e a sacramentação foi **deliberadamente adiada** porque o faturamento ainda estava ativo — comportamento correto do AS-IS.

O Portal atual cobre a **orquestração** (competência, checklist, P3 declarativo, R01–R15 como matriz de cobertura) mas **nenhuma das fontes oficiais está contratualmente conectada**: P7/MATR460, Entradas/Saídas, H02/MATR989, Kardex SD3, FINR190 e extratos bancários permanecem `MANUAL_EVIDENCE` ou `PENDING_CONTRACT`.

## 2. Escopo e autoridades

| Autoridade | Uso nesta etapa |
|---|---|
| TÉO/Transformômetro | AS-IS, proveniência, regras R01–R42, exceções C01–C10, diagnósticos CH01–CH04, decisões |
| GitHub `roberiooliveiradev/delpi-central` | TARGET, contratos, código, testes, SHAs |
| Gravação MP4 + arquivos operacionais | Evidência observacional primária (verificada diretamente nesta execução) |
| Joyce/owner | Validação pendente dos pontos listados em §18 |

Limite de produto já decidido no TÉO e respeitado aqui: **o Portal/CLARA é READ-only sobre o Protheus** — consultar, consolidar, comparar, explicar; nunca compensar títulos, corrigir cadastros, recalcular saldos, sacramentar ou enviar em nome do usuário.

## 3. Fontes examinadas

### 3.1 Gravação (primária, verificada nesta execução)

`Acompanhamento do Processo do Fechamento Mensal de Estoques e Custos-20260930_143151-Gravação de Reunião (1) (1).mp4`

- SHA-256 `bfa4ec3d1868596912adad7ba9e68ee613d64498c781b478f32628ff15b1227a`; 126.313.027 bytes; duração real **00:54:44,13**; H.264 1920×1080; AAC mono 16 kHz.
- Transcrição integral produzida nesta execução (583 segmentos, pt-BR, faster-whisper `small`; artefato de análise, não anexado ao repo por conter dados sensíveis; citações pontuais abaixo).
- 18 quadros extraídos e inspecionados visualmente (00:03–00:54). **Os quadros nos timestamps documentados pelo TÉO (00:25, 00:27, 00:30, 00:35, 00:50) conferem com as descrições do TÉO** — reabilita parcialmente o alinhamento de timecodes que o doc 04.1 marcava `STALE_EVIDENCE`; a divergência declarada era de duração em extrações derivadas (NotebookLM), não dos quadros SRC-07.
- Participantes: Joici Motta (executor/tela), Robério Teixeira de Oliveira, Michael Marotto. Relógio do sistema 14:34→15:25 em 30/09/2026; timer da reunião atinge 01:00:05 ao final.

### 3.2 Arquivos operacionais (`C:\Users\analistaptd\Downloads\fechamento\`, competência 09/2026)

19 arquivos primários inspecionados estruturalmente (abas, dimensões, cabeçalhos, amostras) — inventário em §9/§10. Artefatos derivados pré-existentes na mesma pasta (`analise_cm.json`, `kardex_cods.txt`, `kardex_headers.json`, `kardex_final.json`, `_parity_rows.json`) são **produto de análise anterior**, não evidência primária do processo de Joyce — classificados `DERIVED_ANALYSIS`.

### 3.3 TÉO/Transformômetro (43 documentos do PROC-0072)

Consultados: 01 (AS-IS reconciliado), 02 (decomposition tree 70 nós / diagrama 20 nós VERIFIED), 03 (entrevista Q22–Q30+), 04/04.1 (evidências e addendum), 05 (inventário de sistemas/rotinas/relatórios), 06/06.1/06.2 (regras R01–R42 + paridade monetária), 07 (responsabilidades/handoffs), 08 (gaps), 09 (exceções C01–C10), 10/10.1/10.2 (diagnóstico/Ishikawa/5-Whys), 20 (procedimento CC), 31.14–31.19 (TARGET P3–P6), 32.x/33 (decisões), 34 (backlog E01–E06/T01–T03).

Baseline TÉO: processo `21f70cd0-d513-46f5-bfcf-29ae5573f2f6`, instância `fa3074bd-c852-44d1-b145-72a2f17043d6`, revisão `1.0.0` (`85358475-3fbf-4bec-9f48-56ec15706b34`), medição `fcb0e063-105e-426a-8f98-4329d62c7f51`, vigente desde 2025-01-01, referência 960 min/fechamento (INFORMED, não medido).

### 3.4 Repositório (TARGET/implementação)

- BFF `controllership-finance-api`: `interface/http/routes/p3_routes.py` (P3 state/events/cutoff/reconciliations `ENTRADAS_SAIDAS|P7|H02`/revalidations), `reports_routes.py` (`GET /closing/competences/{period}/reports`, catálogo R01–R15), `closing_routes.py`.
- `api-delpi`: `interface/http/routes/financeiro/` — `stock_inventory_router.py` (SB9), `settlements_router.py` (SE5 payables/receivables), `despesas_centro_custo_router.py` (análise SD1 por CC — sobreposição parcial com ANL-026); scripts/evidências `investigate_matr460_inventory.py`, `run_matr460_approximation.py`, `reconcile_stock_value.py`, `docs/roadmaps/evidencias/matr460-investigacao-totvs.{json,md}`.
- Docs do ciclo: 112, 113 (§27 fontes P3/P7/H02 pendentes), 114, 115, 116.

## 4. Fontes indisponíveis ou limitadas

| Fonte | Situação | Impacto |
|---|---|---|
| Extratos BB/Sicoob/Nordeste reais | Apenas Bradesco demonstrado na gravação; demais MENTIONED | cobertura bancária TO_INVENTORY |
| Extrato XP | Dependente de Dennis (R04); não acessado | TO_INVENTORY |
| `Material em processo.xlsb` | Extração estrutural truncada (~3.001 linhas) | cabeçalhos comprovados; totalização TO_INVENTORY |
| `_F190C` (relação de baixas custom) | Falha de compilação/licença durante a gravação | saída não observada; conteúdo conhecido por relato + arquivos `pagos/recebidos` existentes |
| Filial 02 | Bloco estoque/custos não executado na gravação | RESOLVED_BY_INFORMED_EVIDENCE (R05) |
| `NF a desconsiderar.xlsb`, `Analise.xlsx`, `Invent.xlsb` | Presentes e inspecionados; uso no vídeo não demonstrado | TO_INVENTORY |
| Procedimento `Relatórios enviados à Contabilidade.docx` | Citado no TÉO; arquivo não localizado na pasta de evidências | conteúdo conhecido via doc 04.1 E-02 |
| `cpv 09 26 matriz.xlsb` | Listado no pedido; **não encontrado** na pasta — o que existe é `Invent.xlsb` + extrações anteriores; o frame 00:25 mostra `cpv 09 26 matriz` aberto no Excel | arquivo existe no contexto da gravação; cópia local não disponível |
| Canal de envio do pacote | Não demonstrado (E04 do doc 34) | TO_INVENTORY — não assumir e-mail/pasta/Teams |

## 5. Proveniência e qualidade das evidências

- **PROVEN (observação direta nesta execução):** telas/quadros listados em §7, sequência narrada na transcrição, estrutura dos arquivos, valores lidos na tela do P7 (R$ 3.776.994,69 = TOTAL GERAL visível no quadro 00:35 — confere com o exemplo documentado no TÉO).
- **PROVEN_FROM_DOCUMENT:** checklist oficial (doc 04.1 E-01), procedimento escrito (E-02), árvore/diagrama TÉO.
- **INFORMED:** gatilho, encerramento, handoffs, filial 02, sacramentação, responsáveis.
- **INFERRED:** causas das divergências e das classificações pendentes (sempre rotuladas).
- **STALE_EVIDENCE superada em parte:** timecodes — verificação própria confirmou os quadros citados pelo TÉO; a transcrição nova é a referência temporal desta análise.
- Divergência de 1 centavo entre fala (48.660,77) e aritmética documentada (48.660,78) preservada, não reconciliada por edição.
- Dados comerciais/pessoais dos arquivos não replicados; documento usa campos, faixas e o exemplo já publicado no TÉO.

## 6. Linha do tempo do processo (gravação, `HH:MM:SS`)

Legenda: **[D]** demonstrado · **[M]** mencionado/relatado · **[T]** também corroborado por documento TÉO.

| # | Tempo | Etapa | Evidência |
|---|---|---|---|
| 1 | 00:00:01–00:01:17 | Contexto: divisão fiscal × "todo o resto"; contabilidade já gera SPED/XML sozinha | [M][T: Q23] |
| 2 | 00:01:17–00:01:42 | Estratégia: iniciar pelos processamentos longos e paralelizar | [D][T: R06] |
| 3 | 00:01:42–00:02:53 | **Acompanha Custos**: novo fechamento; data-base = último dia do mês; apropriação **diária** (nunca mensal); lança cálculo | [D; quadro 00:15 = wizard "Novo fechamento de custo" 100%; T: R17/R18] |
| 4 | 00:02:57–00:03:39 | **Custo de Reposição — MP/consumo**: último dia do mês; "material de consumo até matéria-prima"; último custo de compra líquido de tributações | [D; T: R20] |
| 5 | 00:03:39–00:04:24 | **Custo de Reposição — PA/PI**: via estrutura; "recalcular estruturas" desmarcado (responsabilidade da Engenharia) | [D; T: R21] |
| 6 | 00:04:24–00:05:04 | **Refaz Saldos**: todos os materiais; corrige falhas de processamento/movimentação; termina ~00:06:50 | [D; T: R22] |
| 7 | 00:04:59–00:05:49 | **Refaz Poder de Terceiros**: esporádico; **isolado** (bloqueia faturamento); coordenar com faturamento antes | [M; T: R23] |
| 8 | 00:05:49–00:06:44 | **Faturamento × MOD**: Análises→Movimentações→Kardex→Faturamento por MOD; "custo que deveria ter acontecido de MOD vs. o que aconteceu"; 01/09–30/09/2026; **ambas as filiais** | [D; T: kp04_t06/R13] |
| 9 | 00:07:09–00:07:49 | **Gate de dependência**: Kardex 01/99 e saldo de estoque **só após** Acompanha Custos finalizar | [D; T: R19] |
| 10 | 00:07:49–00:09:48 | **Compensações financeiras**: PA/devoluções ("matar positivo com negativo"); exemplo Tecmaster R$ 1.761,66; comum em Mercado Livre | [D; T: R41] |
| 11 | 00:09:48–00:11:27 | **Títulos a pagar**: tudo em aberto, ~01/01/2020→2049, data-base hoje, Excel, suprimir linhas em branco | [D; gera `A pagar.xlsb`] |
| 12 | 00:10:58–00:12:40 | **Títulos a receber**: idem, **matriz + filial** | [D; gera `A Receber.xlsb`] |
| 13 | 00:11:37–00:12:20 | **Pasta mensal**: `FILESERVER > Fechamentos > Componentes > Matriz > 2026 > 09 Set` (+ subpasta `financeiro`); salva em formato binário | [D; quadro 00:12 "Salvar como" mostra a árvore e arquivos finr150/mata103/mata610/mata650/dlp34r01] |
| 14 | 00:12:40–00:15:57 | **Relação de baixas `_F190C` (DLP)**: erro de compilação/licença; print; chamado a Michael/TI; explica conteúdo (todas as baixas, fornecedor/cliente + CNPJ para importação pela contabilidade) e as **5 saídas**: Excel pagar+receber; PDF receber por data; PDF pagar por data e por natureza | [D incidente + M conteúdo; T: C03/R37] |
| 15 | 00:15:57–00:16:52 | **Análise custo inicial × final** (relatório do Acompanha Custos): hoje pouca atenção a PA/PI — apontamento não nivelado; melhoria futura = parâmetro de custo nivelado | [D; T: R19] |
| 16 | 00:17:00–00:18:38 | **P7 padrão**: saldo valorizado; **exclui poder de terceiros**; data último dia; **P7 Bloco H** como layout separado para contabilidade | [D; quadro 00:18 = diálogo MATR460 "Registro de Inventário - Modelo P7"; T: R24] |
| 17 | 00:18:29–00:19:47 | **Kardex 01 e 99**: "do nada até o ZZZ" (todos os produtos), 01/09–30/09/26, Excel, suprimir linhas em branco | [D; T: kp04_t04/t05] |
| 18 | 00:19:47–00:20:07 | Inventários: só armazéns com inventário (99 principal); demais valor irrisório → omite | [M→critério de materialidade informal] |
| 19 | 00:20:07–00:21:58 | **Material em processo** (quadro 00:30 = `matr989`, Dt.Ref 30/09/2026, armazém 99) e **Entradas e Saídas** (módulo financeiro, 01/09–30/09/26; PDF `SIGA/MATR320.prt`) | [D; T: R27] |
| 20 | 00:21:48–00:23:52 | **Kardex 99**: filtra linhas `INVENT`, copia para outra aba, autosoma entradas−saídas → "prejuízo de R$ 57 mil" (exemplo falado); salva na pasta da Controladoria | [D; T: R26] |
| 21 | 00:23:52–00:24:46 | **Sanity check Kardex 01**: verifica item conhecido / valor de terceiros; resíduo ~R$4–5 do mês anterior tolerado ("não é isso que vai fazer meu CPV ficar errado") | [D; T: C09 — tolerância prática, não formal] |
| 22 | 00:24:46–00:25:45 | **Prévia CPV**: filtra coluna CF → `501, 524, 601, 624`; "já consigo ter uma ideia do CPV"; salva `cpv 09 26 matriz` | [D; quadro 00:25 = filtro C.F aberto; T: R25/GAP-RULE-02] |
| 23 | 00:25:45–00:26:20 | Salva títulos a receber (histórico completo) | [D] |
| 24 | 00:26:20–00:29:24 | **Tratamento Fat × MOD**: relatório com problema conhecido (células mescladas); desmesclar + converter para número; manter só linhas MOD; resultado falado **R$ 172 mil** de MOD; destino Fabiano/DRE | [D; quadro 00:27 = `scagprn0` com componentes MODxxx; T: R14/R15/R16] |
| 25 | 00:29:24–00:29:54 | Autocrítica: "o certo era eu ter feito uma outra conferência antes [dos Kardex]" — ordem ideal ≠ ordem executada | [D — insight de sequência] |
| 26 | 00:30:31–00:33:06 | **Conciliação tripla**: E/S = 3.890.247,1x; P7 = 3.776.994,69; "tem que fechar na vírgula"; H02 = 64.591,71; 113.xxx − 64.xxx → **diferença R$ 48 mil**; investigação = re-tirar relatórios e varrer movimentações; hipóteses faladas: materiais de consumo, parâmetro errado no relatório, resíduo do mês passado (→ reabrir estoque e recalcular) | [D; T: R07/R09; doc 06.2] |
| 27 | 00:33:30–00:34:05 | Contexto: nova versão do Protheus a havia impedido de fechar; relatórios reativados agora | [M] |
| 28 | 00:34:05–00:35:36 | **Drill-down da divergência**: compara resumo P7 (registro de inventário) × E/S por grupo; insumos 266.321,45 vs ,46 (redondo); **matéria-prima diverge** (3.087.025,94 + em processo) → diferença localizada em MP/material em processo | [D; quadros 00:33/00:35 = resumo P7 com subtotais EM ESTOQUE 3.428.511,09 e EM PROCESSO ~349 mil; T: kp07] |
| 29 | 00:35:36–00:36:08 | Caveat: fechamento ainda processando; fábrica ainda aponta/baixa — números podem se mover | [D; T: R10] |
| 30 | 00:36:08–00:37:52 | **Decisão de não sacramentar**: sai da tela de fechamento porque faturamento/meta do Fabiano ainda ativo; aguarda custo de reposição PA/PI terminar | [D; T: R10/R11/C06] |
| 31 | 00:36:27–00:37:23 | Regra da contabilidade: P7/Bloco H final só com **MP, PA, PI**; materiais de consumo são descarregados conforme NF lançada (regra deles, "não mudam") | [M→regra do destinatário] |
| 32 | 00:37:52–00:39:04 | Volta ao financeiro; pendente: `_F190C`; Michael acionado, chamado aberto ao consultor | [D; T: C03] |
| 33 | 00:38:25–00:42:06 | **Bancos**: Bradesco (conta em encerramento) — extrato 30 dias → PDF na pasta `09\financeiro`; Invest Fácil (movimentação de investimentos); fatura de cartão (venc. 05/09); lista falada: Bradesco, Sicoob, Banco do Brasil, Banco do Nordeste; **XP via Dennis** | [D Bradesco; M demais; quadro 00:42 = extrato de cartão Bradesco; T: R35/R36/R04] |
| 34 | 00:42:06–00:42:41 | **Filial 02**: todo o bloco estoque/custos repetido por filial; financeiro é consolidado | [M; T: R05] |
| 35 | 00:42:41–00:44:25 | **Dúvidas da contabilidade**: NF faturada sem movimento de estoque não aparece no Kardex → questionamento recorrente; explicação: vendas a terceiros faturadas em 2 CFOPs (5.101/5.124) e códigos 9026/9035 — 9035 fatura sem baixar estoque (custo embutido no 9026 via apontamento); consulta SD2 para responder | [M; T: kp09/R40] |
| 36 | 00:44:25–00:52:26 | **Custos por centro de custo (por filial)**: módulo 04 → Consultas→Cadastros→Genéricos → tabela **SD1** → filtro `data de digitação` ≥01/09/26 e ≤30/09/26 → exporta XML → Excel. Expurga tipos: 01, 02, 030 (telefonia), 040 (MP), 083/080/085 (remessa/material de terceiro), 120 (devolução), 204 (transferência MP), 318 (importados); remove matéria-prima/MP ("MP não conta"); avalia CC em branco; classifica **adm (02xx — direção/vendas), indireto (03xx — PCP/almoxarifado), direto (04xx — CTs)**; coparticipação de saúde sem CC é legítima (despesa do colaborador); 0407/0413 = CCs problemáticos conhecidos; consulta Protheus para itens desconhecidos; salva `CC matriz` | [D; quadros 00:45 (seleção de base)/00:48/00:50/00:52 = SD1 XML + preenchimento da coluna CC; T: doc 20, R28–R34] |
| 37 | 00:52:26–00:53:18 | Dia a dia tem intervenções: rejeições, estornos, relançamentos; acertos hoje executados por **Gustavo** | [M; T: doc 07] |
| 38 | 00:53:18–00:54:41 | **Conferência de extratos**: verificar extrato vs. sistema "igualzinho"; operação **diária** (não só fechamento); BB disponibiliza TXT para confronto; existia ferramenta de conciliação dentro do Protheus (incerta após atualização) | [M; T: R42] |

## 7. Etapas executadas por Joyce — lógica operacional

O fluxo real **não é linear**: Joyce dispara os processamentos longos primeiro (Acompanha Custos, Custo de Reposição ×2, Refaz Saldos) e preenche as janelas de espera com emissão de relatórios financeiros, tratamento de planilhas e coleta bancária. As dependências duras observadas:

```text
Acompanha Custos CONCLUÍDO
  → Kardex 01 (CPV) / Kardex 99 (inventário) / relatório de saldo
Encerramento das movimentações/faturamento
  → revalidação → sacramentação do estoque (postergada na demo)
Refaz Poder de Terceiros
  → somente isolado e após alinhar com faturamento (bloqueia faturamento)
Conciliação tripla
  → depende de E/S + P7 + H02 da mesma competência/filial
```

Ordem observada ≠ ordem ideal: a própria Joyce registra (00:29:24) que a conferência de fechamento deveria preceder a emissão dos Kardex.

## 8. Catálogo de relatórios utilizados

| Relatório | Rotina/fonte | Competência/filial | Filtros observados | Saída | Destinatário | Evidência |
|---|---|---|---|---|---|---|
| Posição títulos a pagar | financeiro (FINR150 associado) | consolidado; "tudo desde o início"→2049 | data-base atual; suprimir brancos | `.xlsb` | Contabilidade | 00:09:48–00:11:27 |
| Posição títulos a receber | idem | matriz + filial | idem | `.xlsb` | Contabilidade | 00:10:58; `A Receber.xlsb` |
| Relação de baixas | **`_F190C` (custom, falhou) + FINR190** | competência | 5 variantes: Excel pagar/receber; PDF receber-por-data, pagar-por-data, pagar-por-natureza | `.xlsb` + PDFs | Contabilidade (importa pelo CNPJ) | 00:12:40–00:15:57; `Recebidos.xlsb`, `Pagos por dt.pdf`, `Pagos por nat.pdf`, `Recebidos.pdf`, `pagos 09 26.xlsb` |
| Acompanha Custos (relatório de variação de custo) | fechamento de custo | por filial | apropriação diária | relatório interno | uso próprio | 00:15:57–00:16:52; `Analise.xlsx`? (ver §18-Q) |
| **P7 padrão** | **MATR460** (quadro 00:18) | por filial; exclui poder de terceiros | data último dia | impresso/PDF | conferência interna | 00:17:00–00:18:38; `Resumo Estoque.pdf`/`Estoque.pdf` |
| **P7 Bloco H** | MATR460 layout H | por filial | só MP/PA/PI (regra da contabilidade) | PDF | Contabilidade | 00:18:12–00:18:38 |
| Kardex Físico-Financeiro | movimentações/kardex | armazém 01 | CF `501,524,601,624` | `cpv 09 26 matriz.xlsb` | **Fiscal** (checklist) | 00:18:29–00:25:45; quadro 00:25 |
| Kardex Físico-Financeiro | idem | armazém 99 | marcador `INVENT` | `Invent.xlsb` | Contábil | 00:21:48–00:23:52; quadro 00:22 |
| Entradas e Saídas | MATR320 (PDF `SIGA/MATR320.prt/v.12`) | 01/09–30/09/2026, MATRIZ | período | PDF 1 pág. | Contabilidade + conciliação | 00:21:09–00:21:58; `Entradas e saidas.pdf` |
| Saldo em Processo (H02) | **MATR989** (quadro 00:30) | Dt.Ref 30/09/2026, por filial | — | `.xlsb` | Contábil + conciliação | 00:20:07–00:21:19; `Material em processo.xlsb` |
| Faturamento × MOD | DLP204 (custom, c/ defeito conhecido de mesclagem) | 01/09–30/09/2026, **ambas filiais** | período | `Fat x MOD.xlsb` | Fabiano/DRE; Contábil | 00:05:49–00:06:44; 00:26:20–00:29:24 |
| Itens NF por centro de custo | Consulta genérica SD1 (módulo 04) | por filial; data de **digitação** da competência | expurgos + classificação (§11) | `CC matriz.xlsb` | Contabilidade (divide dir./ind./adm.) | 00:44:25–00:52:26 |
| Extratos bancários | net empresas (Bradesco demo; BB, Sicoob, Nordeste citados; XP=Dennis) | consolidado | últimos 30 dias / mês fechado | PDF | Contabilidade | 00:38:25–00:42:06 |
| Invest Fácil + faturas de cartão | portal bancário | consolidado | mês/vencimento | PDF | Contabilidade | 00:40:12–00:41:28 |
| Consumo por OP | MATR860 (ref. técnica a confirmar) | mensal | — | planilha | — | INFORMED (E-02); não demonstrado |
| NF a desconsiderar | — | — | — | `NF a desconsiderar.xlsb` | — | TO_INVENTORY |

## 9. Catálogo de planilhas (arquivos operacionais)

| Arquivo | Estrutura observada | Uso provável comprovado | Limite |
|---|---|---|---|
| `A pagar.xlsb` | 1 aba `01-01 - Posicao dos Titulos a`, 663×15 | saída de títulos a pagar | uso no vídeo: PROVEN |
| `A Receber.xlsb` | 1 aba `01-01 - Posicao dos Titulos a`, 574×17 | saída de títulos a receber | PROVEN |
| `pagos 09 26.xlsb` | baixas a pagar | 1 das 5 saídas da relação de baixas | PROVEN (família); emissora _F190C falhou na demo |
| `Recebidos.xlsb` | `01-01 - Relacao de Baixas`, 686×22 | baixas a receber | idem |
| `Pagos por dt.pdf` / `Pagos por nat.pdf` / `Recebidos.pdf` | 33 / 35 / 36 págs.; `nat.prt`/`DLP06R01.prt` | variantes PDF da relação de baixas | PROVEN (família) |
| `Analise.xlsx` | aba `Relatorio`, 1.995×26; campos filial/produto/tipo/grupo/armazém/custo médio inicial | candidato = relatório de variação de custo do Acompanha Custos | TO_INVENTORY (vínculo não demonstrado) |
| `CC matriz.xlsb` | `SCAGQGA0.XML`, ~356×235 (SD1 export) | análise de despesas por CC | PROVEN (quadros 00:48–00:52 exibem `scagpou0`, mesmo padrão de export) |
| `Fat x MOD.xlsb` | `1-Fl01` ~2.461×11; `2-Fl02` ~2.019×11; colunas PA/Seq Comp/Produto/Qtd Fat/Custo/Hora | consolidação de MOD mensal | PROVEN |
| `Material em processo.xlsb` | `01-01 - Saldo em Processo`, ~3.001×8 | H02 da conciliação | PROVEN; extração truncada |
| `Invent.xlsb` | `Planilha2`, 50×12; campos de Kardex + ref. `P.V.,FOR, CC, PJ, OP ou OS` | filtro de movimentos INVENT (armazém 99) | PROVEN como resultado parcial |
| `NF a desconsiderar.xlsb` | `Planilha2`, 14×184 (layout SD2) | exclusões de NF (motivo não documentado) | TO_INVENTORY |
| `Arquivos de envio - contabil para fechamento mensal.xlsx` | `Eletronico` 46×10, `Fisico` 42×10, `Planilha1` 71×14 | **checklist oficial** de entregáveis por destinatário | PROVEN_FROM_DOCUMENT (E-01) |
| `Contabilidade liberações.xlsx` | `Fiscal Jhenifer` 15×15; `Contabil Ravana` 10×5; rotinas: MATA080, MATA540, DEL002, COMXCOL, MATA103, EDAPP, MATA010, MATR460, MATR989, DLP204, FINR150, FINR130, FINR190 | permissões/rotinas liberadas à contabilidade | DOCUMENTED |
| `Entradas e saidas.pdf` / `Estoque.pdf` / `Resumo Estoque.pdf` | 1 pág.; `MATR320.prt`, DELPI/MATRIZ, 30/09/2026 | fontes da conciliação tripla | PROVEN |
| `cpv 09 26 matriz.xlsb` | citado no pedido; **ausente na pasta**; visto na tela (00:25) | CPV via CF 501/524/601/624 | arquivo não localizado localmente |

Artefatos derivados `analise_cm.json` (variação de custo médio por item, campos `cm_i/cm_f/var`), `kardex_headers.json`, `kardex_final.json`, `kardex_cods.txt`, `_parity_rows.json` (linhas de baixas) = trabalho analítico prévio sobre os mesmos dados; úteis como referência, **não** como evidência do AS-IS.

## 10. Matriz de análises e conciliações (`ANL-xxx`)

| ID | Análise/verificação | Pergunta respondida | Entradas & filtros | Regra/comparação | Divergência/ação | Evidência | Grau | Equivalente Portal |
|---|---|---|---|---|---|---|---|---|
| ANL-001 | Acompanha Custos (custo médio) | "Custos do mês apurados?" | data-base último dia; apropriação diária | processamento ERP; relatório de variação CM inicial×final | processamento em erro → refaz; decisão de não processar antes das conferências | 00:01:42; R17–R19 | PROVEN | sem equivalente (rotina ERP; Portal READ-only) |
| ANL-002 | Custo de Reposição MP/consumo | "Custo de reposição atualizado p/ comprados?" | último dia; MC→MP; último custo de compra líquido | ERP | — | 00:02:57; R20 | PROVEN | sem equivalente |
| ANL-003 | Custo de Reposição PA/PI | idem p/ fabricados | estrutura; sem recalcular estrutura (Engenharia) | ERP | — | 00:03:39; R21 | PROVEN | sem equivalente |
| ANL-004 | Refaz Saldos | "Saldos consistentes?" | todos materiais | recálculo corretivo | falhas de histórico corrigidas pela rotina | 00:04:24; R22 | PROVEN | sem equivalente |
| ANL-005 | Refaz Poder de Terceiros | "Retorno de terceiros íntegro?" | esporádico; isolado; pós-faturamento | ERP; bloqueia faturamento | coordenar antes de rodar | 00:04:59; R23 | MENTIONED | sem equivalente |
| ANL-006 | Faturamento × MOD | "MOD real ≈ MOD embutida no faturamento?" | período; ambas filiais; desmesclar+converter; só linhas MOD | soma das linhas MOD → valor consolidado (ex. falado R$ 172 mil) | relatório com mesclagem defeituosa → tratamento manual | 00:05:49; 00:26:20; R13–R16; EV-MOD-01..05 | PROVEN | R09 (PENDING_CONTRACT) |
| ANL-007 | Gate de dependência de custos | "Posso emitir Kardex/estoque?" | estado do Acompanha Custos | só emite relatórios dependentes após término | esperar | 00:07:09; R19 | PROVEN | conceito de source-state do P3 (parcial) |
| ANL-008 | Compensações financeiras | "Há PA/devolução a compensar?" | contas a pagar/receber; casos Mercado Livre | casar positivo×negativo | compensar no financeiro (write no ERP — fora do Portal) | 00:07:49; R41 | PROVEN | sem equivalente (write) |
| ANL-009/010 | Posições a pagar / a receber | "Posição completa de títulos?" | tudo em aberto (~2020→2049); Excel | export integral | — | 00:09:48/00:10:58 | PROVEN | R01/R02 (view operacional SE5 existe; não é a saída oficial) |
| ANL-011 | Organização do pacote | "Onde guardar?" | `Fechamentos\<Unid>\<Filial>\<AAAA>\<MM Mês>` | convenção de pastas + .xlsb | — | 00:11:37; quadro 00:12 | PROVEN | sem equivalente (P5 TARGET) |
| ANL-012 | Relação de baixas (5 saídas) | "Baixas do mês para importação da contabilidade?" | `_F190C`/FINR190; variantes data/natureza | export | rotina quebrada → chamado TI | 00:12:40; C03/R37; E-02 | PROVEN (c/ incidente) | R01/R02 adjacente; saída oficial sem contrato |
| ANL-013 | Variação custo médio inicial×final | "Muita alteração de custos?" | relatório pós-Acompanha Custos | inspeção de discrepâncias; PA/PI hoje pouco confiável (apontamento não nivelado) | análise limitada declarada | 00:15:57 | PROVEN | gap (artefato `analise_cm.json` mostra análise análoga) |
| ANL-014/015 | P7 padrão / P7 Bloco H | "Estoque valorizado oficial?" | MATR460; data último dia; **exclui poder de terceiros**; Bloco H p/ contabilidade | subtotais EM ESTOQUE/EM PROCESSO/TOTAL | — | 00:17:00; quadros 00:18/00:35; R24 | PROVEN | R03 é SB9 operacional — **não é P7**; gap central |
| ANL-016 | CPV via Kardex 01 | "Prévia do CPV?" | Kardex arm. 01; filtro CF `501,524,601,624` | soma das saídas de faturamento | resíduo ~R$4–5 tolerado na prática | 00:24:46; quadro 00:25; R25 | PROVEN | R06 (PENDING_CONTRACT) |
| ANL-017 | Inventário via Kardex 99 | "Ganho/prejuízo de inventário?" | Kardex arm. 99; marcador `INVENT` | Σ entradas − Σ saídas (ex. falado −R$57 mil) | valor irrisório em outros armazéns → omite | 00:21:48; R26 | PROVEN | R07 (PENDING_CONTRACT) |
| ANL-018 | Sanity check Kardex | "Movimentos coerentes?" | item conhecido; poder de terceiros | comparação pontual | resíduo pequeno tolerado | 00:23:52 | PROVEN | gap |
| ANL-019 | Saldo em Processo (H02) | "O que ficou pendente de apontamento em valor?" | MATR989; Dt.Ref último dia | componente da conciliação | — | 00:20:07; quadro 00:30; R27 | PROVEN | R08 (MANUAL_EVIDENCE) |
| ANL-020 | Entradas e Saídas | "Saldo do período pelo financeiro/estoque?" | MATR320; competência | total do relatório | — | 00:21:09; `Entradas e saidas.pdf` | PROVEN | R05 (MANUAL_EVIDENCE) |
| ANL-021 | **Conciliação tripla** | "Estoque fecha?" | E/S − P7 − H02 (mesma competência/filial) | **= R$0,00 exato** (doc 06.2; sem tolerância formal) | divergir → investigar total→grupo→item | 00:30:31–00:32:36; R07; doc 06.2 | PROVEN | P3 reconciliations (declarativo, sem cálculo automático) |
| ANL-022 | Investigação por grupo | "Onde está a diferença?" | resumo P7 × E/S por grupo de material | comparação grupo a grupo; insumos ok; MP divergente | localizado MP/em processo; próximos passos: varrer movimentações | 00:34:05–00:35:36 | PROVEN | gap (drill-down divergências) |
| ANL-023 | Decisão de (não) sacramentar | "Posso fechar o estoque?" | estado do faturamento (meta Fabiano) | só sacramenta após encerramento + revalidação | adiar — deixar período aberto | 00:35:36–00:37:52; R10/R11; C06 | PROVEN | P3 cutoff/revalidation (TARGET implementado em UI/estado, sem ato ERP) |
| ANL-024 | Extratos + aplicações + cartões | "Documentos bancários do mês?" | 4 bancos + XP(Dennis); extrato 30d; Invest Fácil; fatura | coleta PDF p/ pasta | sem movimento → ainda assim emitir (R36) | 00:38:25–00:41:57; R04/R35/R36 | PROVEN (Bradesco) / MENTIONED (demais) | R13 (EXTERNAL_SOURCE) |
| ANL-025 | Repetição Filial 02 | "Mesmo bloco na outra filial?" | todas rotinas/relatórios de estoque-custos | duplicação do trabalho por filial | — | 00:42:06; R05 | INFORMED | branch scope existe no Portal |
| ANL-026 | Despesas por centro de custo (SD1) | "Despesas dir./ind./adm. corretas por CC?" | SD1 por **data de digitação** da competência; export XML→Excel | expurgos de tipos (01,02,030,040,080,083,085,120,204,318) + retirar MP; classificação 02xx/03xx/04xx + julgamento por material/fornecedor/área | CC em branco/errado → corrigir na planilha; consultar área; exceção coparticipação | 00:44:25–00:52:26; doc 20; R28–R34 | PROVEN | R10 (MANUAL_EVIDENCE); `despesas_centro_custo` routes na api-delpi são base candidata parcial |
| ANL-027 | Resposta a dúvidas (NF s/ movimento) | "Por que NF faturada não está no Kardex?" | consulta SD2; regra 9026/9035 + CFOP 5.101/5.124 | custo do 9035 embutido no 9026 | explicar à contabilidade; ciclo só fecha após dúvidas | 00:42:41–00:44:25; R12/R40 | PROVEN | P5 esclarecimentos (parcial) |
| ANL-028 | Conferência de extratos (diária) | "Extrato bate com o sistema?" | extrato vs. financeiro; BB TXT | "fechar na vírgula", feito diariamente | diferença → investigar | 00:53:18; R42 | PROVEN | gap (fora do escopo mensal atual) |
| ANL-029 | Checklist de entregáveis | "O que devo a quem?" | planilha checklist por destinatário | completude do pacote | faltante → cobrar/preparar | E-01; R02/R39 | PROVEN_FROM_DOCUMENT | P2 checklist (implementado) |
| ANL-030 | NF a desconsiderar | ? | `NF a desconsiderar.xlsb` (layout SD2) | desconhecido | — | arquivo apenas | TO_INVENTORY | — |
| ANL-031 | Consumo por OP | "Consumo do período por OP?" | MATR860? | — | — | E-02; kp04_t02 | TO_INVENTORY | R04 (PENDING_CONTRACT) |
| ANL-032 | Importações (SWIFT/câmbio/ACSI) | "Dossiês de importação?" | planilhas de fechamento/internalização + dossiês | rastreio planilha×documentos | — | checklist; kp03 | INFORMED | R14 (EXTERNAL_SOURCE) |

## 11. Matriz de problemas do fechamento (`PRB-xx`)

| ID | Problema | Sintoma (proven) | Hipóteses de causa (não fatos) | Causa comprovada | Tratamento AS-IS | Evidência |
|---|---|---|---|---|---|---|
| PRB-01 | Divergência na conciliação tripla | Δ = R$ 48.660,78 (fala 48.660,77); localizada em MP/material em processo | materiais de consumo; parâmetro errado de relatório; resíduo do mês anterior (→ reabrir e recalcular) | **não determinada** na gravação | investigar total→grupo→item; revalidar pós-encerramento | 00:30:31–00:35:36; C04; kp07 |
| PRB-02 | CC ausente/inadequado/descontinuado | registros SD1 sem CC; 0407/0413 seguem aparecendo | origem em SC/PC; SB1/SBZ; cadastro | UNKNOWN (doc 20 §9; CH01) | classificação/correção manual na planilha | 00:46:01–00:51:31; C07/C08 |
| PRB-03 | `_F190C` não compilada | erro de compilação/licença na emissão | — | falha técnica (custom report) | chamado TI; seguir outras frentes | 00:12:55–00:13:30; C03 |
| PRB-04 | Custo PA/PI não nivelado | análise de variação de custo pouco confiável para PA/PI | parâmetro de apontamento por processo | parâmetro pendente (mudança futura citada) | menor atenção a esse bloco | 00:16:20–00:16:51 |
| PRB-05 | NF faturada sem movimento de estoque | contabilidade questiona recorrentemente | — | **explicada**: códigos 9026/9035, CFOP 5.101/5.124; 9035 não baixa estoque (custo via apontamento do 9026) | resposta via consulta SD2 | 00:42:41–00:44:25 |
| PRB-06 | Dependência de pessoa | "se me der dor de barriga, tenho alguém?" — conhecimento na cabeça da Joyce | — | característica AS-IS (Q28–Q30) | gravação serve como legado | 00:28:42; CH02 |
| PRB-07 | Dependência de terceiro (XP/Dennis) | extrato XP não acessível por Joyce | — | INFORMED | Dennis envia; Joyce incorpora | 00:41:48; C02 |
| PRB-08 | Resíduos de centavos/reais | insumos ΔR$0,01; exemplos R$0,25; resíduo R$3–4 Kardex | arredondamento de sistema | prática tolera; **regra formal = paridade exata** (06.2) | ignorar na prática; regra formal exige R$0,00 | 00:24:16; 00:34:32; C05/C09; doc 06.2 |
| PRB-09 | Fragmentação de fontes | Protheus + Excel + bancos + pastas + exportações XML | — | PROVEN (CH04) | orquestração manual | todo o fluxo; CH04 |
| PRB-10 | Drift de lista bancária | checklist × procedimento divergem (CEF/Viacredi) | — | BANK_SCOPE_DRIFT (doc 04.1 §2) | lista não hardcoded; confirmar seed | doc 04.1; E01 |
| PRB-11 | Retrabalho/revalidação | re-tirar relatórios após divergência; possível reabertura de estoque | resíduo de competência anterior | não comprovada | repetir emissões e recalcular | 00:32:49–00:33:30; CH03 |

Separação mantida: sintoma ≠ hipótese ≠ causa. Nenhuma tolerância numérica foi inventada; a regra corrente é paridade exata (doc 06.2), enquanto a prática de centavos permanece evidência histórica.

## 12. Regras demonstradas (síntese PROVEN)

- Período-base: **último dia da competência** como data-base para estoque/custos; relatórios do período usam intervalo 01→último dia; filtro SD1 usa **data de digitação** (não emissão).
- Apropriação de custo: **diária**, nunca mensal.
- Paralelismo deliberado de processamentos; Kardex/estoque bloqueados até o fim do Acompanha Custos.
- P7 exclui poder de terceiros; Bloco H é layout separado para a contabilidade e só com MP/PA/PI no entregável final.
- Conciliação tripla com **paridade monetária exata**; divergência → investigação total→grupo→item.
- CPV ≈ saídas Kardex 01 com CF `501, 524, 601, 624` (lista parcial — GAP-RULE-02).
- Inventário ≈ movimentos `INVENT` no Kardex 99; entradas−saídas = ganho/prejuízo.
- SD1→CC: expurgo dos tipos listados + exclusão de MP; classificação adm/ind./dir. com exceção de coparticipação; gestor/solicitante é autoridade oficial do CC.
- Financeiro consolidado entre empresas; estoque/custos por filial (trabalho duplicado).
- Não sacramentar com faturamento ativo; após encerrar → revalidar → sacramentar.
- Sem movimentação bancária → extrato ainda é exigido (comprovação de ausência).

## 13. Hipóteses não comprovadas (não promover)

- Códigos técnicos não demonstrados: MATA330 (Acompanha Custos), MATA280 (Refaz Saldos), MATR860 (consumo por OP) — referências a confirmar. **MATR460→P7 e MATR989→saldo em processo passam a PROVEN** pelos quadros 00:18 e 00:30 desta execução (antes UNKNOWN no TÉO).
- Lista completa de CFOPs/tipos de expurgo: as duas extrações divergem (doc 06 §10 GAP-RULE-01); a fala do vídeo lista 01, 02, 030, 040, 080, 083, 085, 120, 204, 318 — confirmar campo (Tipo E vs. Cod. F) e valores.
- Fórmula/agregação exata de MOD (GAP-RULE-03), aritmética de CPV/inventário (GAP-RULE-02), taxonomia formal de CC (GAP-RULE-04), tolerância monetária formal (GAP-RULE-05 — resolvida como "não existe; paridade exata" por 06.2), detalhes pós-corte (GAP-RULE-06).
- Causa técnica de 0407/0413; causa da divergência de R$ 48 mil; geração bem-sucedida das 5 saídas de baixas naquela tentativa.
- Lista vigente de bancos; canal de envio; reabertura pós-sacramentação (E02/E04 do doc 34).

## 14. Comparação com o Portal atual (AS-IS × TARGET/runtime)

| AS-IS | Portal hoje | Classificação |
|---|---|---|
| Orquestração da competência e checklist | P1 cockpit + P2 checklist/documentos implementados | PROVEN (parcial ao escopo P2) |
| Conciliação tripla | P3 com `ENTRADAS_SAIDAS/P7/H02` declarativos + cutoff/revalidation; sem cálculo automático nem fonte oficial conectada | TARGET implementado como casca; dados `MANUAL_EVIDENCE` |
| Relatórios (matriz R01–R15) | `GET /closing/competences/{period}/reports` — cobertura derivada de snapshots do checklist; R01–R03 views operacionais; R05/R08/R10/R11 evidência manual; R04/R06/R07/R09/R12/R15 PENDING_CONTRACT; R13/R14 EXTERNAL_SOURCE | PLANNED→parcial; nenhum relatório oficial conectado |
| Fontes api-delpi | SB9 (estoque operacional), SE5 settlements, `despesas_centro_custo` (SD1/CC); investigação MATR460 documentada (SB9≈P7 EM ESTOQUE ~99–104%; EM PROCESSO ≠ SC2 simples) | PROVEN como infraestrutura; **SB9 ≠ P7 oficial**; H02/ENTRADAS_SAIDAS sem fonte |
| Divergências drill-down | não existe | PLANNED |
| Bancos/extratos | fora do Portal; fonte externa configurável pendente (E01 doc 34) | TO_INVENTORY |
| Envio do pacote / dúvidas | P5 especificado (doc 12/31.16); canal E04 pendente | TARGET/PENDING |
| CLARA | identidade aprovada (doc 94); nenhuma tool de fechamento implementada | PLANNED |

Divergências centrais AS-IS→TARGET: (1) fonte oficial do P7 (MATR460) não tem contrato — investigação mostra que SB9 só aproxima e EM PROCESSO do P7 não é SC2 direto; (2) H02/MATR989 sem fonte; (3) ENTRADAS_SAIDAS (MATR320) sem fonte; (4) classificação CC é hoje planilha manual com julgamento humano — candidato a semântica assistida, não a automação cega; (5) writes do AS-IS (compensação, sacramentação, refaz) ficam **fora** do Portal por decisão READ-only.

## 15. Lacunas de fontes e contratos (para ANALYSIS-002)

1. **P7/MATR460** — definir contrato canônico (API ou extração governada) com competência/filial/exclusão de poder de terceiros e subtotais; investigação prévia em `api-delpi/docs/roadmaps/evidencias/matr460-investigacao-totvs.md` é o ponto de partida.
2. **H02/MATR989** — mapear produtor e campos (produto/OP/tipo/qtd/valor em processo).
3. **ENTRADAS_SAIDAS/MATR320** — mapear produtor e total oficial.
4. **Kardex SD3 (arm. 01/99, CF, INVENT)** — Joyce: "é só pegar a tabela SD3" (00:22:19) — fonte tabular direta candidata.
5. **Baixas financeiras** — `_F190C` quebrada; decidir correção TOTVS vs. reconstrução via SE5 na api-delpi (settlements já existem; as 5 ordenações são apresentação).
6. **SD1/CC** — `despesas_centro_custo` na api-delpi como base; pendente: catálogo de tipos de expurgo, taxonomia e exceções homologadas com Joyce.
7. **Bancos** — lista vigente (drift), escopo por unidade, XP/Dennis.
8. **NF a desconsiderar / consumo por OP / importações** — inventariar finalidade real.

## 16. Conhecimento necessário à CLARA (sem presumir implementação)

CLARA **explica** resultados produzidos por serviços determinísticos; **não recalcula** nem executa ERP. Precisa conhecer:

- glossário: competência, P7/Bloco H, H02, Entradas/Saídas, Kardex, CPV, MOD, CC adm/ind./dir., poder de terceiros, INVENT, sacramentação;
- a fórmula documentada `E/S − P7 − H02` e por que H02 ≠ subtotal "EM PROCESSO" do P7;
- estados de fonte (`UNAVAILABLE` ≠ zero; snapshot vs. oficial);
- causas possíveis vs. provadas para cada divergência (PRB-xx);
- precondições (faturamento ativo → não sacramentar; Acompanha Custos → gate dos relatórios);
- limites: não inferir crédito tributário, não combinar listas conflitantes de CFOP, não declarar pacote entregue.

Perguntas-alvo (necessidades, não capacidade atual): "Quais relatórios ainda não foram conciliados?" / "Onde surgiu a diferença de estoque desta competência?" / "Quais notas precisam de revisão?" / "Essa diferença vem de movimentação ou valorização?" / "Qual conferência ainda falta?" — respostas seguras exigem resultado calculado + evidência citável; quando faltar fonte, CLARA declara a limitação (padrão dos EVAL-01..10 do doc 06).

## 17. Perguntas pendentes para Joyce/PO (priorizadas)

1. Lista **vigente** de bancos/contas e quais extratos são obrigatórios (drift checklist × procedimento).
2. Lista homologada de **tipos/CFOPs de expurgo** da análise SD1 e o campo correto (Tipo E vs. Cod. Fiscal).
3. Taxonomia oficial de CC (adm/ind./dir.), destino de 0407/0413 e quais exceções além de coparticipação.
4. Critério exato de agregação do Fat × MOD (intervalo, quais linhas somam, tratamento de totais).
5. Finalidade e uso de `NF a desconsiderar.xlsb` e de `Analise.xlsx`/`Invent.xlsb` na rotina.
6. Consumo por OP: relatório/rotina real, campos e destinatário.
7. Detalhes pós-corte: quem sacramenta, quando, o que reemite, o que acontece se houver movimento após corte (E02/E03 doc 34).
8. Canal/formato de envio do pacote por destinatário (E04 doc 34).
9. Regra da contabilidade para Bloco H/última página — confirmar escopo MP/PA/PI por escrito.
10. Divergência de R$ 48 mil da demo: desfecho real (investigada depois? causa encontrada?).

## 18. Priorização sugerida para ANALYSIS-002 (sem score numérico)

Critérios: importância ao fechamento, dependência, disponibilidade de fonte, clareza de regra, risco de erro manual, benefício CLARA, necessidade de validação.

| Ordem | Frente | Justificativa |
|---|---|---|
| 1 | **Fontes da conciliação tripla** (E/S MATR320, P7 MATR460, H02 MATR989) | decisão central do fechamento; regra provada; P3 já tem casca; investigação MATR460 pré-existente; desbloqueia divergências e CLARA |
| 2 | **Kardex SD3 → CPV (01) e Inventário (99)** | fonte tabular indicada pela própria Joyce; alimenta investigação da tripla; regra parcialmente provada (lista CF a confirmar — Q2) |
| 3 | **SD1/despesas por CC** | rota `despesas_centro_custo` já existe; falta regra homologada de expurgo/classificação; alto esforço manual hoje |
| 4 | **Baixas financeiras (5 saídas)** | SE5/settlements existente; saída oficial quebrada no ERP cria urgência e oportunidade; escopo de ordenações é simples |
| 5 | **Fat × MOD** | fonte custom com defeito conhecido; contrato novo; benefício DRE direto |
| 6 | **Bancos/extratos** | fonte externa; depende de decisão de configuração (E01) e de Dennis |
| 7 | **Checklist→pacote→dúvidas (P5) + NF a desconsiderar/consumo por OP/importações** | orquestração depende das anteriores; itens TO_INVENTORY |

## 19. RQ/AC candidatos (para ledger 23 — PROPOSED, sujeitos ao gate)

| RQ | Escopo | AC-chave |
|---|---|---|
| RQ-ANL-01 | Contrato canônico P7/MATR460 (competência/filial, excl. terceiros, subtotais) | API devolve totais = P7 oficial da competência em fixture real sanitizada; SB9 jamais servido como P7 |
| RQ-ANL-02 | Contrato H02/MATR989 e ENTRADAS_SAIDAS/MATR320 | idem; `UNAVAILABLE` propagado, nunca convertido em zero |
| RQ-ANL-03 | Motor de conciliação tripla determinístico | Δ = E/S−P7−H02 com paridade exata R$0,00; versão de regra; evidências citáveis |
| RQ-ANL-04 | Drill-down de divergência por grupo de material | reproduz localização MP demonstrada em fixture |
| RQ-ANL-05 | Kardex SD3 arm. 01/99 com filtros CF/INVENT | lista CF homologada por Joyce antes de parametrizar |
| RQ-ANL-06 | Análise SD1 por CC com regras homologadas | expurgos/taxonomia versionados; exceções declaradas |
| RQ-ANL-07 | Relação de baixas (5 ordenações) via SE5 | paridade com saídas oficiais do período de referência |
| RQ-ANL-08 | Fat × MOD contrato + consolidação | intervalo e soma homologados |
| RQ-ANL-09 | Config de bancos/extratos por unidade | seed validada; ausência de movimento exige comprovante |
| RQ-ANL-10 | Conhecimento CLARA versionado (glossário/regras/limites) | evals estilo EVAL-01..10; fail-closed sem fonte |

## 20. Riscos e dependências

- Divergência de R$ 48 mil demonstrada indica que **reprocessamento/reabertura** faz parte da vida real — o Portal precisa de `REVALIDATION_REQUIRED` (já previsto no TARGET P3).
- Listas de expurgo/CC vivem na cabeça da Joyce → cada contrato depende de sessão de validação com ela (gate de ANALYSIS-002/003).
- `_F190C` quebrada pode forçar decisão: corrigir custom no Protheus ou assumir via api-delpi.
- Filial 02 só INFORMED — inventário de diferenças por filial necessário antes de parametrizar.
- Dados sensíveis nos arquivos: documentação sanitizada; fixtures para testes devem ser anonizadas.
- Transcrição é artefato de análise (ASR); citações críticas foram conferidas contra quadros, mas segmentos sem quadro devem ser tratados como MENTIONED até revisão humana.

## 21. Evidências e referências

- Vídeo: SHA-256 `bfa4ec3d…f32628ff15b1227a`; quadros verificados 00:03/08/12/15/18/22/25/27/30/33/35/38/42/45/48/50/52/54; transcrição `/tmp/transcript_proc0072.txt` (artefato local, não versionado).
- Arquivos: `C:\Users\analistaptd\Downloads\fechamento\` (19 primários + derivados).
- TÉO: documentos 01–34 do PROC-0072 (IDs internos nos cabeçalhos); processo `21f70cd0…`, revisão `85358475…`, baseline 960 min INFORMED.
- Repo: `controllership-finance-api/.../p3_routes.py`, `reports_routes.py`, `closing_routes.py`; `api-delpi/app/interface/http/routes/financeiro/*`; `api-delpi/docs/roadmaps/evidencias/matr460-investigacao-totvs.md`; docs 112–116; BASE_HEAD no início desta execução `1f34403767` (worktree incluía alterações concorrentes de `delia-api` e untracked pré-existentes, não tocados).

## 22. Conclusão do inventário

O AS-IS está reconstruído com granularidade de timestamp, arquivo/aba e registro TÉO suficiente para decidir ANALYSIS-002. **32 análises catalogadas** (24 PROVEN, 2 MENTIONED/INFORMED com suporte documental, 6 TO_INVENTORY), **11 problemas catalogados** com separação sintoma/hipótese/causa, e a tripla conciliação — coração do fechamento — tem regra formal provada (paridade exata) e gap claro de fontes. Gate para ANALYSIS-002: revisão PO/Joyce das perguntas do §17 e dos RQ/AC do §19 antes de mapear contratos.

```
ANALYSIS_001 = COMPLETED_WITH_RESIDUAL
RUNTIME_CHANGES = NONE
PROVEN_ANALYSES = 24
INFORMED_OR_MENTIONED = 2
TO_INVENTORY = 6
PROBLEMS_CATALOGUED = 11
UNAVAILABLE_SOURCES = ver §4
GATE_NEXT = PO/Joyce review + owner de fontes oficiais
```
