# Handoff Ciclo 2 — Pacote de Evidências para Owners

**Documento:** `81-ciclo2-handoff-pacote-evidencias-owners.md`
**Origem:** `80-ciclo2-registro-vivo-investigacao-devin.md` §25 (Rodada 13, `4577c8c5e4`)
**Escopo:** PROC-0072 — estoque histórico, MOD, baixas financeiras, fechamento SB9
**Estado:** `DECISION_REQUIRED` (MOD, ver §3) · `NO_GATE_CHANGE` (Doc 47)

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

#### E1 — Produtor das baixas a receber (`DLP06R01`)

| Campo | Conteúdo |
|---|---|
| Evidência atual | Artefato de 657 baixas (set/2026) reconciliado row-level; produtor não-FINR190 comprovado por comparação de WHERE (doc 80 §17). `DLP06R01` ausente do acervo `docs/13-fontes-totvs-protheus/` |
| Lacuna objetiva | identidade do executável que gera a relação de baixas a receber |
| Fonte esperada | fonte AdvPL/PRX de `DLP06R01` (ou nome da rotina real) + confirmação da versão compilada no RPO |
| Impacto PROC-0072 | fecha a trilha do relatório de recebidos; sem ela, paridade é só estrutural |
| Critério de aceite | `SOURCE_AVAILABLE` + `CODE_DEPLOYED`; idealmente `EXECUTION_OBSERVED` (log/schedule set/2026) |

#### E2 — Produtor e parâmetros do P7 / MATR460

| Campo | Conteúdo |
|---|---|
| Evidência atual | `SB9 = snapshot mensal de SB2` no recorte (96% identidade, doc 80 §21–§22); SX1 **sem** grupo `MATR4%`; MP7/TRB provados não-proxy (§17/§19); `Dmatr320` consumidor, não produtor |
| Lacuna objetiva | rotina oficial que emite o P7 e seus parâmetros efetivos (empresa, filial, data, produto, armazém, tipo) |
| Fonte esperada | nome/versão da rotina oficial (custom ou MATR460 padrão), prints/arquivo de parâmetros (SX1), e um export oficial sanitizado de uma competência |
| Impacto PROC-0072 | é a base do gate R03 e da distinção "consulta operacional × relatório oficial" |
| Critério de aceite | `SOURCE_AVAILABLE` + export oficial confrontável com SB9 |

#### E5 — Rotina que grava SB9 (fechamento)

| Campo | Conteúdo |
|---|---|
| Evidência atual | inserção em janela comum por filial (`I_N_S_D_T_`: f02 02/10 17h, f01 21/10 19h); hook `MA330OK` chama `STP_DELPI_OP_TERCEIRO_01` e `STP_PROTHEUS_DELPI_AJUSTA_OP` (fonte, doc 80 §22.D); execução não observada |
| Lacuna objetiva | qual rotina/schedule efetivamente grava as linhas SB9 (MATA330? custom? job externo?) |
| Fonte esperada | confirmação da rotina + evidência de execução (log do schedule, appserver, ou extrato do job) da competência 09/2026 |
| Impacto PROC-0072 | transforma "snapshot observado" em "produtor identificado" — destrava R12/R15 |
| Critério de aceite | `EXECUTION_OBSERVED` (log/schedule datado) + `CODE_DEPLOYED` |

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

#### E6 — Decisão sobre apresentação do resultado MOD — `DECISION_REQUIRED`

Contexto (doc 80 §23–§25): a view aplica o `BZ_CUSTD` **corrente retroativamente**; revalorização de out/2026 moveu ~8–9% do resultado de set/2026 (f01 +489,72; f02 −2.465,53). Não existe congelamento: indicadores são recalculados ao vivo.

| Opção | Significado | Exige | Limitação |
|---|---|---|---|
| **A — Histórico homologado** | resultado com o rate da competência | rate-por-data (TTAT ≥abr/26 ou tabela nova) + snapshot no fechamento | pré-abr/26 irreconstruível; diverge da view atual |
| **B — Recalculado corrente** | resultado sempre ao custo atual | nada (status quo da view) | série histórica muda a cada revalorização |
| **C — Ambos** | as duas leituras lado a lado | mesma fonte de A | maior complexidade de explicação |

| Campo | Conteúdo |
|---|---|
| Fonte esperada | escolha de opção (A/B/C) + homologação do valor-base set/2026 (f01 +5.918,90 / f02 −32.694,32, ótica corrente) + owner da manutenção de `BZ_CUSTD` MOD |
| Impacto PROC-0072 | define semântica dos indicadores MOD em qualquer superfície (view, relatório, portal) |
| Critério de aceite | `FUNCTIONAL_ACCEPTANCE` registrado com versão e data |

> **Bloqueio deliberado:** nenhuma opção será implementada sem manifestação do owner.

---

## §3 — Estado do ciclo e marcações preservadas

| Item | Estado |
|---|---|
| Reconstrução DEL100 vigente | 3.058/421/242 — query §24.E, validada (SF4 compartilhada ≡ `xFilial`, reproduzida 2×) |
| 724/672 e derivadas (§19.C, §20.A, §21.C) | `STALE_EVIDENCE` — `EXECUTION_DRIFT` registrado em §23.A |
| Pagar FINR190 | paridade estrutural PROVEN (948, 5/5 motivos, `FINR190_DLP`); sem paridade monetária/registro |
| MOD fórmula/rate | PROVEN; decisão de apresentação `DECISION_REQUIRED` |
| SB9 | snapshot SB2 PROVEN no recorte; produtor `BLOCKED` (E4/E5) |
| DLP06R01, P7 | `BLOCKED`/`TO_INVENTORY` (E1/E2) |
| Doc 47 | `NO_GATE_CHANGE` — evidências mapeadas em §25.E |

---

## §4 — Referências

- Registro vivo: `80-ciclo2-registro-vivo-investigacao-devin.md` §17–§25
- Tracker de gates: `47-t01-report-column-audit-tracker-v1.md` (G1–G6)
- Acervo de fontes: `docs/13-fontes-totvs-protheus/` (`DEL100.PRW`, `MA330OK.PRW`, `FINR190_DLP.PRX`, `matr860`, `DLP34R01.PRW`)
- Commits-âncora: `9281aa9f09` (R5), `a1f2e47f18` (R6), `4fea4c09b3` (R7), `dd2ea700ee`+`b7cc80c246` (R8), `c06826af9d` (R9), `287f94a2aa` (R10), `f7c899fffe` (R11), `f95c7213eb` (R12), `4577c8c5e4` (R13)

**Última atualização:** 2026-10-23 · preparado por Devin
