# Handoff Ciclo 2 — Pacote de Evidências para Owners

**Documento:** `82-ciclo2-handoff-pacote-evidencias-owners.md` (renumerado de `81-` em 2026-10-23 para resolver colisão com o documento de decisão)
**Origem:** `80-ciclo2-registro-vivo-investigacao-devin.md` §25 (Rodada 13, `4577c8c5e4`)
**Escopo:** PROC-0072 — estoque histórico, MOD, baixas financeiras, fechamento SB9
**Estado:** E6 `APPROVED / PRODUCT_DIRECTION_ONLY` (opção C — `81-decisao-e6-historico-monetario-mod-opcao-c.md`, `e68ae2d63129`) · `IMPLEMENTATION_AUTHORIZED = NO` · `NO_GATE_CHANGE` (Doc 47)

> Nenhum item deste pacote pede permissões amplas ou acesso privilegiado genérico.
> Cada solicitação pede **a evidência específica** e, quando possível, **extrato/resultado sanitizado** no lugar do acesso.

---

## §1 — Protocolo de recebimento de respostas

Para cada resposta recebida, classificar **separadamente** (uma resposta pode cobrir vários planos, mas nenhum plano deve ser presumido):

| Plano | Pergunta que responde | Aceite |
|---|---|---|
| `SOURCE_AVAILABLE` | a fonte/código existe no acervo ou foi entregue? | arquivo/fonte/DDL recebido e legível |
| `CODE_DEPLOYED` | o código recebido é o efetivamente implantado no RPO/DB de produção? | versão/RPO/data de compilação ou confirmação do owner |
| `EXECUTION_OBSERVED` | há evidência de execução em produção (log, schedule, timestamp)? | artefato de execução datado |
| `FUNCTIONAL_ACCEPTANCE` | o resultado foi homologado pelo negócio? | aceite do owner funcional (Controladoria) |

Referência vigente das reconstruções DEL100: **3.058 chaves / 421 valor / 242 quantidade** (query sanitizada no doc 80 §24.E). Contagens anteriores (724/672 e derivadas) estão `STALE_EVIDENCE`; a trilha preserva `EXECUTION_DRIFT` — não reutilizar os números antigos.

---

## §2 — Solicitações por responsável

### 2.1 — Owner TI/ERP (fontes e execução Protheus)

#### E1 — Produtores das baixas — **parcialmente respondido em 23/10; receber segue pendente**

| Campo | Conteúdo |
|---|---|
| Evidência atual | `Pagos por dt.pdf`/`Recebidos.pdf` trazem `SIGA/DLP06R01.prt/v.12` — **layout compartilhado, não produtor**. **Pagar:** produtor = FINR190 provado — fonte `FINR190_DLP.PRX` (commit `0df96daafe`) com TRCell→`E5_*` e WHERE que reproduz população oficial 948+motivo 5/5 (doc 80 §17.B/C; G4 PASS doc 47 §11.1). **Receber:** WHERE do FINR190 gera 649/690 ≠ 657 oficial (§17.D, PROVEN) — produtor = `DLP06R01` **custom, fonte ausente do acervo**; `DLP06P01/F01/F02/F03` verificados = utilitários não relacionados |
| Lacuna objetiva | (a) **fonte do `DLP06R01` custom** (receber) — nome da rotina, mapeamento coluna→campo e filtros (incl. regra de inclusão/exclusão dos movimentos sem título e do VO `FINA750`); (b) confirmar versão RPO do `FINR190_DLP.PRX`; (c) identidade do subconjunto do "log de inconsistências" de ambos os relatórios; ~~paridade monetária integral~~ **respondida 23/10 — G5 PASS ambos (doc 84)** |
| Fonte esperada | fonte AdvPL/PRX do `DLP06R01` (ou nome da rotina efetiva do relatório de recebidos) + confirmação de compilação no RPO + o arquivo de log de inconsistências emitido junto ao relatório |
| Impacto PROC-0072 | fecha G4 de R02 e a trilha receber; sem o fonte, G4 segue PENDING (paridade do artefato já provada em G5) |
| Critério de aceite | `SOURCE_AVAILABLE` + `CODE_DEPLOYED`; idealmente `EXECUTION_OBSERVED` |

#### E2 — Produtor e parâmetros do P7 / MATR460

| Campo | Conteúdo |
|---|---|
| Evidência atual | **Resolvido em 23/10:** rotina **"Registro de Inventário Modelo P7"** observada em preview no vídeo (35:00/37:00, MATRIZ, 30/09/2026); artefatos `Estoque.pdf` (completo, TOTAL 3.946.431,87, folha 101) e `Resumo Estoque.pdf` (escopo MP/PA/PI, 2.976.967,56, folha 74 — **emissão distinta, mesma data-base 30/09**); roster vincula "Estoque P7"→**MATR460**; SPEDFISCAL gera Bloco H. **Rodada 15 (doc 80 §33.D):** binding de totalização **provado** — `EM ESTOQUE` = saldo físico ex-`MV_LOCPROC='99'` no `as_of` da emissão e `EM PROCESSO` = MATR989. **Rodada 17 (doc 80 §35):** grupo SX1 **`MTR460` (25 perguntas) catalogado**; resumo = mesmo estado de custo (PA/PI bit a bit) + **escopo MP/PA/PI + exclusão poder3-MP** — `QTNP@emissão>0` explica 99,987 % do estoque (Δ76,43) e ~97,5 % do processo (Δ+1.942,62); MTR460 **não** tem parâmetro de tipo |
| Lacuna objetiva | (1) parâmetros efetivos da emissão resumida — print das perguntas/mv_par; (2) linhas de produto da emissão resumida (folha 74 completa) para fechar Δ76,43/Δ1.942,62; (3) fonte `matr460.prx`/RPO (semântica `Saldo em Poder 3º?` + mecanismo de escopo de tipos, ausente no SX1); (4) versão P7 homologada pela Controladoria |
| Fonte esperada | print/tela de parâmetros da emissão resumida + PDF completo da folha 74 + identificação do fonte (MATR460 padrão ou custom) |
| Impacto PROC-0072 | é a base do gate R03 e da distinção "consulta operacional × relatório oficial" |
| Critério de aceite | `CODE_DEPLOYED` (rotina identificada) + export oficial confrontável com SB9 |

#### E5 — Rotina que grava SB9 (fechamento)

| Campo | Conteúdo |
|---|---|
| Evidência atual | **Execução observada em 23/10:** vídeo 14:47 mostra o wizard "Acompanha Custo → Novo fechamento de custo" (4 etapas) sendo executado em produção por JOICI/Matriz na competência 09/2026. Porém `B9_I_N_S_D_T_` marca inserções f02=02/10 17h e f01=21/10 19h — **divergentes da execução de 30/09 14:47** (reexecuções? etapa distinta?). Hooks `MA330OK`/`STP_DELPI_*` = capacidade de fonte (§22.D) |
| Lacuna objetiva | qual passo/rotina efetivamente grava as linhas SB9 e por que os timestamps de inserção divergem da execução observada; papel das SPs pós-fechamento |
| Fonte esperada | log de execução do fechamento (wizard/Event Viewer/appserver) da competência 09/2026 + identificação do passo que escreve SB9 |
| Impacto PROC-0072 | transforma "snapshot observado" em "produtor identificado" — destrava R12/R15 |
| Critério de aceite | `EXECUTION_OBSERVED` (log/schedule datado da escrita SB9) + `CODE_DEPLOYED` |

---

### 2.2 — Owner DBA (objetos de banco)

#### E3 — DDL das views criptografadas

| Campo | Conteúdo |
|---|---|
| Evidência atual | `vw_Apontamentos_Eficiencia` homologada empiricamente: `RESULTADO_MOD = (TEMPO_PREVISTO − TEMPO_REAL) × SBZ010.BZ_CUSTD` (85.904/85.904); `OBJECT_DEFINITION` retorna `NULL` (WITH ENCRYPTION) |
| Lacuna objetiva | definição interna: joins exatos, origem de `TEMPO_PREVISTO_HORAS`/`PRODUTO_MOD`, semântica de `STATUS_MOD`, e se há filtro temporal de rate |
| Fonte esperada | DDL das views `vw_Apontamentos_Eficiencia`, `VW_PROTHEUS_CUSTO_ANALITIC_01/_05`, `VW_PROTHEUS_CUSTO_SINT_01/_05`, `vw_fin_despesas_centro_custo` (script ou `sp_helptext`) |
| Impacto PROC-0072 | confirma bindings físicos (G4) e a proveniência do rate; elimina dependência de inferência |
| Critério de aceite | `SOURCE_AVAILABLE`; confrontado com o contrato empírico já provado |

#### E4 — Jobs SQL Agent e SPs DELPI

| Campo | Conteúdo |
|---|---|
| Evidência atual | `SELECT` em `msdb.dbo.sysjobs` **negado**; `STP_DELPI_OP_TERCEIRO_*`/`STP_PROTHEUS_DELPI_AJUSTA_OP` ausentes das bases acessíveis (`DELPI`, `DELPI_TST01`, `DELPI_TST_WS`, `IntranetDelpiDev`) |
| Lacuna objetiva | existência e agendamento de jobs de fechamento; código e localização real das SPs chamadas pelo `MA330OK` |
| Fonte esperada | extrato sanitizado de `msdb.dbo.sysjobs`/`sysjobschedules` (nomes, schedule, última execução) + `sp_helptext` das duas SPs na base onde residem |
| Impacto PROC-0072 | prova/elimina a hipótese do job mensal SB9 e revela o pós-processamento do fechamento |
| Critério de aceite | `EXECUTION_OBSERVED` (job + histórico) ou `SOURCE_AVAILABLE` (código SP) |

---

### 2.3 — Owner Controladoria (decisão de negócio)

#### E6 — Histórico monetário MOD — `APPROVED / PRODUCT_DIRECTION_ONLY` (opção C)

**Decisão registrada:** `E6_OPTION = C` (duas leituras: histórico homologado + recalculado corrente) em `81-decisao-e6-historico-monetario-mod-opcao-c.md` (`e68ae2d63129`, 2026-10-23). Classificação `APPROVED / PRODUCT_DIRECTION_ONLY` — **não é GO de implementação**: `IMPLEMENTATION_AUTHORIZED = NO`; não autoriza contratos, tabelas, migrations, APIs, UI, jobs, alteração na view ou runtime, e não promove gates do doc 47.

Contexto (doc 80 §23–§25): a view aplica o `BZ_CUSTD` **corrente retroativamente**; revalorização de out/2026 moveu ~8–9% do resultado de set/2026 no subconjunto alterado (f01 +489,72; f02 −2.465,53). Não existe congelamento: indicadores são recalculados ao vivo.

**O que se solicita agora à Controladoria (e owners indicados no doc 81):** não uma escolha A/B/C — já decidida — e sim:

| Item | Solicitação | Responsável candidato |
|---|---|---|
| E6-D1 | O que constitui o **valor homologado**: relatório oficial, pacote do fechamento ou outro artefato; grão e moeda | Controladoria |
| E6-D2 | Definição do cutoff, versões, correções, reaberturas e momento de congelamento | Controladoria + TI/ERP |
| E6-D3 | Fonte e confiabilidade de rate por competência, logs, DDL da view e artefatos históricos | TI/ERP + DBA |
| E6-D4 | Owner da persistência de evidências, retenção, contratos, DTOs e integrações | Product owner + arquitetura |
| E6-D5 | Tolerâncias monetárias, rótulos, comparação de variação e aceites por competência e filial | Controladoria |
| E6-D6 | Escopo e propriedade da competência, acesso às evidências e auditabilidade | Segurança/owner |

Mais:

1. **Homologação dos valores-base set/2026** (ótica corrente): f01 `+R$5.918,90` / f02 `−R$32.694,32` — e da leitura por rate anterior no subconjunto alterado (f01 `+R$5.429,18` / f02 `−R$30.228,79`).
2. **Validação dos critérios AC-E6-01..AC-E6-10** do doc 81 §4 (hoje `TARGET_DRAFT / PENDING_OWNER_VALIDATION`): duas leituras rotuladas, trilha humana de homologação, recálculo identificável com `as_of`, paridade por grão oficial, comparação justa, tratamento de rate ausente, histórico incompleto (<27/04/2026), cutoff/republicação, boundary de segurança e evidência de testes.

| Campo | Conteúdo |
|---|---|
| Impacto PROC-0072 | transforma a direção aprovada (duas leituras) em semântica homologada de indicadores MOD |
| Critério de aceite | `FUNCTIONAL_ACCEPTANCE` registrado com versão e data + `DECISION_REQUIRED` de E6-D1..D6 respondidos pelos owners |

> **Bloqueio deliberado:** a direção está aprovada, mas `IMPLEMENTATION_AUTHORIZED = NO` — nada será implementado antes dos detalhamentos e das homologações acima.

---

## §3 — Estado do ciclo e marcações preservadas

| Item | Estado |
|---|---|
| Reconstrução DEL100 vigente | 3.058/421/242 — query §24.E, validada (SF4 compartilhada ≡ `xFilial`, reproduzida 2×) |
| 724/672 e derivadas (§19.C, §20.A, §21.C) | `STALE_EVIDENCE` — `EXECUTION_DRIFT` registrado em §23.A |
| Pagar FINR190 | **paridade row-level PROVEN** (948/948 chaves, TB=`E5_VALOR`, VO=`E2_VALOR`+regras aglutinado, resumos/componentes exatos — doc 84); residual: subconjunto do log + versão RPO |
| Receber DLP06R01 | **paridade row-level do artefato PROVEN, Δ R$0,00** (649 SE5×SE1 + 8 `PA`/`FINA750` sem título; TB=`E5_VALOR`, VO=`E1_VALOR` 649 + VO=provisão `'P'` espelhada MATA121/FINA050 8/8 — doc 84, errata doc 80 §30); residual: fonte do produtor (G4) + regra geral do sem-título (3 excluídos identificados) — **pende de TI/ERP** |
| MOD fórmula/rate | PROVEN; direção de apresentação `APPROVED / PRODUCT_DIRECTION_ONLY` (opção C, doc 81) · `IMPLEMENTATION_AUTHORIZED = NO` · detalhamentos E6-D1..D6 e AC-E6 pendentes |
| SB9 | snapshot SB2 PROVEN no recorte; produtor `BLOCKED` (E4/E5) — **reforço 23/10:** onda retificadora de ~20-21/10 confirmada por RECNO (SD1 doc `<NF-RETIF-A>` sanitizado reclassificado 001→085 + SB9 f01 inserido 21/10 19:13) — corrobora "reexecução/etapa distinta" sem identificar o writer |
| MATR320 (R05) | **fonte localizado 23/10:** `matr320.prx` padrão TOTVS (execução via SP `MAT056`; variante `DLPR320` descartada por poder3 zerado no fonte × não-zerado no PDF). Colunas MP reconciliadas 12/13 ao centavo em estado de emissão (doc 84 §4.2, doc 80 §31, regras doc 85 §5); residual: MovInt ~R$0,48 e `as_of` do saldo |
| DLP06R01, P7 | **parcialmente resolvidos 23/10** — DLP06R01.prt=layout compartilhado (pagar: produtor FINR190 provado; receber: custom `DLP06R01` sem fonte — E1 pendente); P7="Registro de Inventário Modelo P7"/MATR460 + artefatos; residuais estreitados (E1/E2) |
| Doc 47 | crosswalk doc 83 + §11/§11.1/§11.2: **39/60 = 65,0% coleta · 41/90 = 45,6% auditoria** — 37 gates 23/10 (rework) + G5 de R01/R02 (paridade row-level, doc 84) |

---

## §4 — Referências

- Registro vivo: `80-ciclo2-registro-vivo-investigacao-devin.md` §17–§26
- Decisão E6: `81-decisao-e6-historico-monetario-mod-opcao-c.md` (`e68ae2d63129`)
- Crosswalk evidências: `83-ciclo2-crosswalk-evidencias-r01-r15.md` (23/10)
- Tracker de gates: `47-t01-report-column-audit-tracker-v1.md` (G1–G6)
- Acervo de fontes: `docs/13-fontes-totvs-protheus/` (`DEL100.PRW`, `MA330OK.PRW`, `FINR190_DLP.PRX`, `matr860`, `DLP34R01.PRW`)
- Commits-âncora: `9281aa9f09` (R5), `a1f2e47f18` (R6), `4fea4c09b3` (R7), `dd2ea700ee`+`b7cc80c246` (R8), `c06826af9d` (R9), `287f94a2aa` (R10), `f7c899fffe` (R11), `f95c7213eb` (R12), `4577c8c5e4` (R13)

**Última atualização:** 2026-10-23 · preparado por Devin
