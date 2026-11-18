# Entry audit — Ajustes do Fiscal — TRILHA DE EXECUÇÃO (T15 → T23)

| Campo | Valor |
|---|---|
| Status | **READY** (decisões do owner tomadas em 2026-11-18) |
| Origem | documento do Fiscal «Auditoria de Entradas (CLARA) — Ajustes solicitados pelo Fiscal», análise de 01–17/11/2026 (fora do repositório) |
| Inventário | T14 `79980f8c7b` — [inventory.md](./inventory.md) |
| Autoridade | instruções oficiais do arquiteto, `AGENTS.md` e `.cursor` aplicáveis > [ADR-003](../../adr/ADR-003-entry-audit.md) (+ ADR-006, criado na T15) > **esta trilha** > [entry-audit/track.md](../track.md) (regras gerais) > reference |
| Ordem | T15 → T16 → T17 → T17H → T18 → T19 → T20 → **PARADA de verificação pela CLARA** → T22 → T23 |

---

## PARTE 0 — Como executar

1. Comece pela primeira etapa do QUADRO (Parte 2) que não esteja DONE. Siga a ordem; não pule nem antecipe etapa. Ao terminar uma etapa, atualize QUADRO e REGISTRO (Parte 5), faça commit e push e siga **sem esperar o owner**, exceto nas paradas da Parte 4 e na PARADA DE VERIFICAÇÃO após a T20.
2. Valem integralmente a Parte 0 e o protocolo P1–P9 de [entry-audit/track.md](../track.md): direto na `main`, sem branch, sem stash/reset/clean; preservar trabalho de outros agentes; commits só dos arquivos da etapa; até 3 ciclos de correção por problema; documentação técnica atualizada no mesmo commit; autorização permanente de HML (regra 9).
3. **`AGENTS.md` — verificação:** toda etapa que altera código, configuração, migration, contrato ou teste passa pelo ciclo A do `delpi-verifier` **antes do commit/push** (`PEDIDO DE VERIFICAÇÃO` em `<git-dir>/delpi-verifier/requests/`, `python ~/.delpi-agent-kit/verify.py --request-file <arquivo>`, até 3 rodadas, veredito sem edição no report). `DECISION_REQUIRED` ou `EXECUTION_DRIFT` do verificador = parada.
4. **`AGENTS.md` — deploy:** todo push na `main` segue do deploy canônico em `srv-api` dos serviços afetados. Por isso **cada onda entra desligada por flag** (FA-18) e a migração de dados da onda 2 é um passo explícito, nunca efeito do deploy. Sequência de cada onda: push → deploy canônico (flag desligada, PROD sem mudança de comportamento) → ensaio em HML com a flag ligada → HML PASS → ligar a flag em PROD (regra do owner, entry-audit/track.md Parte 0 regra 8) → rerun de 01–17/11 → registro. Migrations de schema são **aditivas** (tabelas/colunas novas; nada removido ou renomeado). Antes de cada ensaio em HML, reconstruir os serviços afetados (`up-hml-sequential.sh --build`) e provar no container o SHA do código e o valor das flags; ensaio sem essa prova = INCONCLUSIVE.
5. **Repositório público:** nenhum CNPJ, nome de fornecedor/cliente, número ou valor de nota real em commit, log ou documento. As notas do Fiscal aparecem aqui como NF-A … NF-D; os números reais ficam só no report do chat.
6. Protheus, Questor e LNF: somente leitura (X4).
7. Mensagens: `feat|fix|docs(entry-audit): <etapa> — <resumo>`.

---

## PARTE 1 — Decisões (não reabrir)

| ID | Decisão |
|---|---|
| FA-1 | **Participante pelo tipo da nota:** `F1_TIPO IN ('B','D')` → cliente (SA1); demais → fornecedor (SA2). Critério é o tipo, não lista de TES (entram sem manutenção 085, 159, 120, 201). A leitura canônica fica na **api-delpi** (D2). O LNF mantém a sua regra B→SA1 no próprio contexto; a duplicação fica registrada no ADR-006. |
| FA-2 | Com participante cliente: CNPJ do cliente ≠ emitente do XML continua **Alta**, com texto «cliente»; «CFOP de entrada incompatível com a UF» usa a UF do **mesmo cadastro**. Mesma raiz de CNPJ com estabelecimento diferente continua Alta (o SPED leva o participante pelo CNPJ completo); o texto orienta a conferir código/loja. |
| FA-3 | **TES de insumo:** `ENTRY_AUDIT_INPUT_TES=018,052,069,106,166,169,406` (configurável, gravado na análise). Nessas TES não se gera `coherence.ipi_on_consumption`. É exclusão, não regra nova: «Crédito de IPI acima do XML» e «IPI escriturado sem destaque» continuam para todas as TES. A alternativa de mudar `F4_CONSUMO` foi descartada (afeta custo e livros). |
| FA-4 | **Uma ocorrência por causa:** uma por nota e causa; itens listados dentro dela (valor por item e total); cabeçalho + item da mesma divergência = uma só; acompanhante («Acompanha…») vira detalhe da principal; resolver/reabrir age sobre a causa; indicadores contam causas. |
| FA-5 | **Fila consolidada** por chave de acesso + causa, não por análise (12 análises sobrepostas em 01–17/11). |
| FA-6 | **Migração de status** (chave por item → por causa): a causa fica resolvida só se **todas** as linhas antigas dela estavam resolvidas; histórico preservado na causa nova. |
| FA-7 | **Indicadores em 3 grupos**, recalculados a cada mudança de status (manual ou automática): **sem problema** (nunca teve causa), **corrigidas** (todas as causas resolvidas), **com divergência pendente**; mais Alta e Média pendentes e diferença em R$ das pendentes. |
| FA-8 | **IBS/CBS em todas as entradas, NF-e e CT-e**, severidade **Alta**. Lançamento: `SD1.D1_IDTRIB = F2D.F2D_IDREL`, regra em F2B (`F2D_IDCAD = F2B_ID`; imposto por `F2B_TRIB`: CBSFED, IBSEST, IBSMUN). XML: grupo `IBSCBS` do item (NF-e) e do imposto (CT-e). A ocorrência diz a TES e a regra do configurador usadas no item. |
| FA-9 | **Exceções do IBS/CBS:** `ENTRY_AUDIT_IBSCBS_EXCEPTIONS` (por CRT do emitente, CFOP ou TES), **vazia** no início: fornecedor do Simples entra. |
| FA-10 | **Tolerância do IBS/CBS:** a mesma `ENTRY_AUDIT_TOLERANCE` (R$ 0,05), por item e por nota. |
| FA-11 | **CST/cClassTrib:** se a T15 achar fonte estruturada no lançamento, compara. Se não, a 1ª versão compara presença, base, alíquota e valor de CBS, IBS UF e IBS Mun; CST/cClassTrib viram residual registrado, para uma tabela de-para regra F2B → CST/cClassTrib mantida pelo Fiscal. **Não** ler o texto `F2B_DESC`. |
| FA-12 | **Livro fiscal IBS/CBS** só a partir de `ENTRY_AUDIT_IBSCBS_BOOK_FROM=2027-01-01` (parâmetro). A SFT não tem colunas de IBS/CBS: sem fonte achada na T15, a regra do livro nasce desligada com residual registrado (não bloqueia). |
| FA-13 | **Reverificação só sob demanda** (botão «Reverificar» e CLARA). **D10 mantida** (sem agendamento). Reverificar não é nova análise: relê no Protheus (SF1, SD1, SFT, F2D) e o XML do cache só das notas com causa pendente ou resolvida à mão. |
| FA-14 | Divergência que não se repete → «resolvida automaticamente» (`resolution_source=auto`), evento com data e valor antes/depois. Continua com outro valor → atualiza a ocorrência e registra a mudança. `_unusual_nature` e a heurística `seen` (dependem do período) **não** se resolvem automaticamente. |
| FA-15 | Resolvida **à mão** que ainda aparece na reverificação: **continua resolvida** e ganha a marca «divergência persiste», visível na leitura, no front e na CLARA. |
| FA-16 | **Paridade:** FA-1/FA-2 e FA-3 entram também na skill `auditoria-entradas-nfe-protheus` (cópia `reference/` pelo agente; skill da conta pelo owner). FA-4, FA-5, FA-7 a FA-15 são melhorias da BFF: o teste de paridade roda com elas desligadas (como a D11). A exportação mantém uma linha por item, com coluna nova «Causa». |
| FA-17 | Sem permission nova (`controllership-finance.access`, D4); seis tools da CLARA iguais (D6); `entry_audit.reverify` é escrita **direta**, como run/rerun. |
| FA-18 | **Flags por onda** (padrão `false`, ligadas em PROD só após HML PASS): onda 1 `ENTRY_AUDIT_PARTICIPANT_BY_TYPE_ENABLED` e `ENTRY_AUDIT_INPUT_TES` vazio = desligado; onda 2 `ENTRY_AUDIT_CAUSE_GROUPING_ENABLED` (a migração de dados v1 → v2 roda por comando explícito antes de ligar); onda 3 `ENTRY_AUDIT_IBSCBS_ENABLED`; onda 4 `ENTRY_AUDIT_REVERIFY_ENABLED`. Rotas novas de leitura da api-delpi não precisam de flag (só leitura, sem consumidor até a flag da BFF ligar). |

---

## PARTE 2 — QUADRO DE STATUS

| Etapa | Onda | Nome | Status | Ambiente | SHA(s) | Data | Evidência |
|---|---|---|---|---|---|---|---|
| T14 | — | Inventário (só leitura) | DONE (ACCEPT_WITH_RESIDUAL) | leitura PROD | 79980f8c7b | 2026-11-18 | premissas PROVEN; F2D/F2B; IBSCBS no XML; linha de base |
| T15 | — | Inventário complementar + contrato + ADR-006 | DONE | leitura + docs | | 2026-11-18 | 10/10 B/D divergentes = emitida pela própria empresa; 4/4 ipi_on_consumption saem; CD2=livro, DKM=lado XML; contrato §7; ADR-006 |
| T16 | 1 | Participante pelo tipo da nota | DONE | DEV | | 2026-11-18 | api-delpi com participant_* por F1_TIPO; BFF com flag default false; flag off = comportamento atual |
| T17 | 1 | TES de insumo | DONE | DEV | | 2026-11-18 | `ENTRY_AUDIT_INPUT_TES` exclui `ipi_on_consumption` nos dois caminhos; IPI acima/sem destaque intactos; snapshot grava a lista |
| T17H | 1 | Onda 1 em HML e PROD + CLARA | DONE | HML/PROD | | 2026-11-18 | onda 1 ativa nos dois ambientes; regras-alvo zeradas no rerun 01–17/11 (163 ocorrências); corpus republicado |
| T18 | 2 | Uma ocorrência por causa + fila + indicadores | DONE | DEV/HML/PROD | | 2026-11-18 | flag on em HML e PROD; 163 linhas v1 → 146 causas nos dois ambientes; migração 18 v1 → 13 causas (11 resolvidas/2 pendentes), idempotente; corpus republicado |
| T19 | 3 | IBS/CBS | DONE | DEV/HML/PROD | | 2026-11-18 | api-delpi `/tax-items`+`/tax-book` (F2D/F2B, CD2; período/filial e por chave); parser `IBSCBS`/`IBSCBSTot` NF-e+CT-e; 4 regras `ibscbs.*` Alta por causa; AE-16 publicada; flag OFF em PROD; HML 01–17/11 (nova análise `24089d66`): `value_mismatch` 133 notas, `posting_missing` 108, `xml_not_posted` 48, `book_mismatch` 0 (BOOK_FROM vazio) |
| T20 | 4 | Reverificação sob demanda | TODO | DEV/HML/PROD | | | |
| — | — | **PARADA: verificação do owner pela CLARA (critérios 1–5)** | — | PROD | | | |
| T22 | — | Front-end | TODO | DEV/HML | | | |
| T23 | — | Front-end em PROD | TODO | PROD | | | |

Status: TODO · IN_PROGRESS · BLOCKED · DONE.

---

## PARTE 3 — Etapas

### T15 — Inventário complementar + contrato + ADR-006 (só leitura e docs)

1. Corrigir [inventory.md](./inventory.md) §5: ajuste 3 é exclusão, não regra nova. ([plan.md](./plan.md) já aponta para este track.)
2. **Participantes B/D** (as 10 de 27 com CNPJ da SA1 ≠ emitente): classificar em (a) formulário próprio; (b) emitente = própria empresa; (c) mesma raiz, outro estabelecimento; (d) raiz diferente; para (c)/(d), se existe outro código/loja na SA1 com o CNPJ do emitente. Projetar quantas Alta «cliente» e quantos `cfop_vs_state` sobram com FA-1/FA-2 (hoje 6 + 6).
3. **IPI em consumo:** TES e CFOP das 4 `ipi_on_consumption` da análise canônica; quantas saem com FA-3.
4. **CST/cClassTrib e livro:** procurar fonte estruturada (SX3/SX2 e INFORMATION_SCHEMA: F2B, F2D, tabelas de cClassTrib e perfis, CD2, SFT, SF3, campos `D1_*`). Reportar o critério da busca (search miss != ausência). O resultado decide FA-11/FA-12.
5. **Volume IBS/CBS em notas:** notas com item sem F2D, por TES; matriz XML com IBSCBS × lançamento com F2D (NF-e e CT-e separados); NF-e sem IBSCBS de emitente do Simples.
6. **Contrato** ([backend/README](../backend/README.md) rotas e schema; [mcp/README](../mcp/README.md)): campos novos da api-delpi (`participant_kind`, `participant_name`, `participant_tax_id`, `participant_state`), rota de tributos por item (período/filial e por chave), rotas de itens e livro por chave; ocorrência por causa (`cause_id`, `items[]`, `total_difference`, `followers[]`), chave estável v2, `resolution_source`, `persists_after_manual`, `last_checked_at`; `GET /entry-audit/pending`; `POST /entry-audit/reverify` (escopo: análise, período+filiais ou uma ocorrência); capability `entry_audit.reverify` e leitura `pending`; KPIs FA-7; regras `ibscbs.*`; flags FA-18.
7. **ADR-006** com FA-1 a FA-18 e a duplicação B/D com o LNF. [entry-audit/plan.md](../plan.md): decisões D17+ apontando para cá.

### T16 — Participante pelo tipo da nota (onda 1)

- **api-delpi:** `documents_sql` e `documents_by_access_keys_sql` com `participant_*` de SA1 (`A1_COD/A1_LOJA`, `A1_NOME`, `A1_CGC`, `A1_EST`) quando `F1_TIPO IN ('B','D')`, senão SA2; `supplier_*` preservados; testes.
- **BFF:** `ProtheusHeader.invoice_type` e `participant_kind`; `_header` lê os campos; com a flag, `_view` usa o participante; `_supplier_keys`: heurística `seen` com chave `(participant_kind, code, store)`; texto da Alta com «cliente» quando for SA1; `cfop_vs_state` com UF do participante e título neutro («…com a UF do participante») **sem mudar o `rule_id`**; leitura e sem par com o participante certo.
- **Testes:** N, B e D; cliente com CNPJ igual (sem Alta); cliente com CNPJ diferente (Alta «cliente»); mesmo código/loja em SA1 e SA2 não se misturam; `cfop_vs_state` com UF do cliente; flag desligada = comportamento atual.

### T17 — TES de insumo (onda 1)

- `ENTRY_AUDIT_INPUT_TES` em `AuditConfig.input_tes` e na configuração gravada da análise.
- `_internal`: sem `coherence.ipi_on_consumption` nas TES da lista (pelo livro e pela TES).
- **Testes:** 052 com IPI igual ao XML → sem ocorrência; 052 com crédito acima → «Crédito de IPI acima do XML» continua; 052 com IPI e XML sem IPI → «IPI escriturado sem destaque» continua; TES fora da lista com `F4_CONSUMO=S` → regra continua; lista vazia = comportamento atual.

### T17H — Onda 1 em HML e PROD + CLARA

- Paridade: aplicar FA-1/FA-2 e FA-3 na cópia [reference/](../reference/skill-auditoria-entradas-nfe-protheus/) (scripts e regras.md) e atualizar o teste de paridade.
- Fichas AE-03 (TES de insumo) e AE-06 (participante cliente/fornecedor) + corpus republicado (HML e PROD).
- Sequência da Parte 0 regra 4; tags `rollback-entry-audit-fa1-*` (api-delpi, BFF).
- Registro: Alta «fornecedor/cliente» e `cfop_vs_state` antes × depois; `ipi_on_consumption` antes × depois (contagens).
- Avisar no report: owner atualiza com o Claude a skill da conta `auditoria-entradas-nfe-protheus` e a skill `clara-auditoria`.

### T18 — Uma ocorrência por causa + fila + indicadores (onda 2)

- **Domain:** consolidação depois das regras: mapa `rule_id → cause_id` (cabeçalho e item da mesma divergência na mesma causa; acompanhantes, como `header.icms_base_mismatch` «Acompanha…», viram `followers` da principal); `Occurrence` com `items[]` (item, Protheus, XML, diferença) e total; severidade da causa = maior dos itens.
- **Chave v2:** `branch + identidade da nota (chave de acesso ou nº/série/participante) + cause_id`.
- **Migração (FA-6):** migration de schema aditiva; script idempotente v1 → v2 sobre status e eventos, executado por **comando explícito**; ensaio em HML com cópia dos status de PROD; em PROD, backup da tabela de status antes, executar o comando, conferir, ligar `ENTRY_AUDIT_CAUSE_GROUPING_ENABLED`. Falha no ensaio = X9.
- **Leitura:** occurrences/occurrence com `items[]` e `followers[]`; `GET /entry-audit/pending` (período, filiais, severidade; consolidado por chave de acesso + causa, ocorrência da análise mais recente); KPIs FA-7 em `summary`, `trend` e `pending`.
- **Exportação:** uma linha por item, coluna «Causa» (FA-16).
- **CLARA:** catálogo (`pending`), `analyze entry_audit_findings` contando causas, fichas AE-13 e AE-14, corpus. Avisar no report: `clara-auditoria` e `clara-bom-dia` passam a ler `pending`.
- Tags `rollback-entry-audit-fa2-*`. Registro: NF-A (TES 085), NF-B (crédito de ICMS sem destaque no cabeçalho e no item + base acompanhante) e NF-C (TES 052, dois itens) com uma ocorrência por causa (contagens antes × depois); resolvidas antes × depois da migração.

### T19 — IBS/CBS (onda 3)

- **api-delpi:** rota de tributos calculados por item (`SD1.D1_IDTRIB = F2D_IDREL`; F2B por `F2D_IDCAD`), por período/filial e por chave: tributo (CBSFED/IBSEST/IBSMUN), regra (`F2B_REGRA`), base, alíquota, valor; CST/cClassTrib se a T15 achou fonte.
- **BFF:** parser `IBSCBS` (NF-e por item; CT-e no imposto; `IBSCBSTot`); modelo; regras, todas Alta, com TES e regra do configurador no texto:
  - `ibscbs.xml_not_posted` — XML com IBS/CBS e item sem F2D;
  - `ibscbs.posting_missing` — item sem F2D e XML sem IBS/CBS (só quando a anterior não se aplica);
  - `ibscbs.value_mismatch` — base, alíquota ou valor de CBS, IBS UF ou IBS Mun fora da tolerância (FA-10), por item e na nota; CST/cClassTrib conforme FA-11;
  - `ibscbs.book_mismatch` — só a partir de `ENTRY_AUDIT_IBSCBS_BOOK_FROM` e se houver fonte (FA-12).
- Exceções FA-9 (lista vazia). Todas nascem por causa (T18).
- Ficha AE-16 (IBS/CBS) + corpus. Avisar no report: `clara-auditoria`.
- HML com a flag ligada: medir em 01–17/11 (causas por regra, notas afetadas) e registrar. Tags `rollback-entry-audit-fa3-*`.

### T20 — Reverificação sob demanda (onda 4)

- **api-delpi:** itens e livro por chave de acesso (se a T19 não cobriu tudo).
- **Application:** use case `reverify` (escopo FA-13); relê só notas com causa pendente ou resolvida à mão; roda o motor por nota com as regras reverificáveis (FA-14); aplica FA-14 e FA-15; eventos com ator (`user` / `mcp/clara`) e antes/depois; KPIs recalculados.
- Execução assíncrona pelo worker existente (mesma fila, tipo de job novo), sem agendador (D10).
- **Interface:** `POST /entry-audit/reverify` (`controllership-finance.access`); MCP `entry_audit.reverify` (direta) com read-back.
- Ficha AE-17 (reverificação e indicadores) + corpus. Avisar no report: `clara-auditoria` e `clara-bom-dia` (sugerir «reverificar» quando houver pendências antigas).
- HML: ensaio com nota corrigida (simulada) e com resolvida à mão persistente. Tags `rollback-entry-audit-fa4-*`.

### PARADA — verificação do owner pela CLARA (PROD)

Owner + Claude, pela CLARA, na análise de 01–17/11:

1. notas da TES 085 sem «fornecedor errado» e sem «CFOP × UF», salvo cliente com CNPJ divergente;
2. NF-D (TES 052, filial 02) e NF-C sem «Crédito de IPI em uso e consumo»;
3. NF-A, NF-B e NF-C com uma ocorrência por causa;
4. NF-e e CT-e com IBS/CBS no XML e sem no lançamento como Alta;
5. nota corrigida no Protheus fecha com «Reverificar» e os indicadores mudam, sem nova análise.

Residuais vão para `residuals.md` desta pasta; o agente corrige antes da T22.

### T22 — Front-end (DEV/HML)

`@delpi/plugin-ui` first. Página 02: indicadores FA-7; fila consolidada; tema IBS/CBS nos filtros; botão «Reverificar» com andamento. Página 03: itens da causa (valor por item e total), acompanhantes, selos «resolvida automaticamente» e «divergência persiste», histórico antes/depois. Ajuda no mesmo gate. Desktop, mobile, teclado, foco, claro/escuro. Playwright em HML.

### T23 — Front-end em PROD

Tags de rollback do front; remoteEntry HML = PROD; smoke.

---

## PARTE 4 — Paradas (BLOCKED, reportar, não contornar)

X1–X8 de [entry-audit/track.md](../track.md), mais:

| ID | Quando |
|---|---|
| X9 | Ensaio da migração de status (T18) não preserva as resoluções conforme FA-6. |
| X10 | `delpi-verifier` devolve `DECISION_REQUIRED` ou `EXECUTION_DRIFT`, ou não aprova em 3 rodadas. |
| Aviso (não para) | Projeção da T15 mostra que FA-1/FA-2 **aumentam** as Altas de participante: registrar no report e seguir (a regra do Fiscal prevê Alta «cliente»). |

---

## PARTE 5 — Registro

| Data | Etapa | O que foi feito | SHA | Observações |
|---|---|---|---|---|
| 2026-11-18 | T14 | inventário | 79980f8c7b | plano reconstruído sem o original; substituído por ponteiro para este track |
| 2026-11-18 | — | trilha e decisões FA-1 a FA-18 publicadas | (este commit) | decisões do owner no chat do arquiteto |
| 2026-11-18 | T15 | inventário complementar + contrato + ADR-006 | (este commit) | 10/10 B/D divergentes emitidas pela própria empresa (SA1 tem o emitente 10/10); projeção Alta «cliente» ~10 e `cfop_vs_state` ~0 (aviso Parte 4: Altas de participante sobem); 4/4 `ipi_on_consumption` são TES 052 → saem com FA-3; CST/cClassTrib sem fonte no lançamento (residual FA-11 mantido) mas `DKM010` existe no lado XML; **livro achou fonte: `CD2010`** (FA-12); matriz XML×F2D: `xml_not_posted` ≈138, `posting_missing` ≈13, `value_mismatch` ≤172; NF-e sem IBSCBS: 63 de 83 são Simples; contrato em backend §7 e mcp §4; ADR-006 ACCEPTED; plan.md D17 |
| 2026-11-18 | T16 | participante pelo tipo da nota (onda 1) | 9c6b8b6cc2 (merge 2effae6c45) | api-delpi `documents`/`documents_by_access_keys` com `participant_*` (SA1 em B/D, SA2 senão; `supplier_*` intactos); BFF `_view`/`seen`/`supplier_mismatch`/`cfop_vs_state` por `participant_kind` atrás de `ENTRY_AUDIT_PARTICIPANT_BY_TYPE_ENABLED` (default false; HML true); snapshot da análise grava a flag; testes api-delpi 15/15 e BFF 151+4 novos (flag off reproduz o atual); verifier ACCEPT_WITH_RESIDUAL r1 (cursor); falha `t9r4::test_e5` pré-existente provada no HEAD; deploy PROD api-delpi + BFF healthy com flag off |
| 2026-11-18 | T17 | TES de insumo (onda 1) | 1614050887 | `AuditConfig.input_tes` + `ENTRY_AUDIT_INPUT_TES` (PROD vazio, HML lista FA-3); `_internal` suprime `coherence.ipi_on_consumption` nos caminhos livro e TES; `item.ipi_credit_mismatch`/`ipi_without_tes_decision` intactos; snapshot grava a lista; 4 testes novos (exclusão ×2 caminhos, sibling IPI, fora da lista); pytest 15/15 + suite 154; verifier ACCEPT_WITH_RESIDUAL r1 (cursor) — resíduo cobertura SFT fechado na mesma entrega |
| 2026-11-18 | T17H | paridade onda 1 skill × motor | 6d8862bcc3 | FA-1/FA-2/FA-3 portados na cópia `reference/` (`analisar` com `sa1`+`tes_insumo`; participante por tipo; títulos «Cliente…»/«…participante»; exclusão IPI consumo nos dois caminhos); `--sa1`/`--tes-insumo` no auditoria.py; SKILL.md + regras.md + relatorio.py atualizados; teste de paridade com fixture B/D + SA1 + TES insumo (motor flag-on + input_tes canônico); coverage corpus com flag da onda 1; fichas AE-03/AE-06 v1.1; pytest 86 passed (coverage+parity+engine) com skill rodando de fato; verifier ACCEPT_WITH_RESIDUAL r1 (cursor) — sem ordens; resíduo `relatorio.py` fechado na mesma entrega |
| 2026-11-18 | T17H | HML: rebuild api-delpi+BFF, flags on, ensaio | runtime HML | imagens HML estavam pré-T16; rebuild via `up-hml-sequential.sh --build` (api-delpi e BFF); `ENTRY_AUDIT_PARTICIPANT_BY_TYPE_ENABLED=true` + `ENTRY_AUDIT_INPUT_TES=018,052,069,106,166,169,406` confirmados no container; análise 01–17/11 `6853195c-ff09-4d60-a838-8a07a129e47b`: **179→163 ocorrências** — `key.supplier_mismatch` 6→0, `coherence.cfop_vs_state` 6→0, `coherence.ipi_on_consumption` 4→0; sem novas regras «Cliente…» (emissões próprias caem em `own_form`/company_tax_id); corpus HML republicado (`clara-corpus-ingestion`, AE-03: 7 PUBLISHED/8 SUPERSEDED, AE-06: 10/10) |
| 2026-11-18 | T17H | PROD: flags on + rerun 01–17/11 + corpus | runtime PROD | tags `rollback-entry-audit-fa1-api-delpi` e `rollback-entry-audit-fa1-controllership-finance-api` em `1614050887`; `infra/.env` com backup + as 2 vars; BFF recriado healthy; análise `6bf91317-40d2-4a53-8cdd-719f7beb00ed`: **183→163 ocorrências**, Alta 21→5 — as 3 regras-alvo zeradas (idem HML); corpus PROD republicado (`4bdbaf36`, AE-03: 7/8, AE-06: 10/10) |
| 2026-11-18 | RESIDUAIS-1 | residuais da onda 1 (revisão do arquiteto) | (este commit) | R1 `test_e5` stale × contrato U12: teste reescrito com análise anterior compatível + caso «sem anterior → previous None»; suíte BFF 1439 passed, 0 failed; R2 diff por regra canônica×rerun: −16 alvo + −8/+4 não-alvo, tudo correção ou lançamento novo no Protheus entre as execuções (SF1/SD1) — sem drift de código; R3 Parte 0 regra 4 ganha «rebuild + prova de SHA/flags antes de todo ensaio HML»; `residuals.md` criado e linkado no README |
| 2026-11-19 | T18 | uma ocorrência por causa + fila + indicadores (onda 2, DEV) | (este commit) | domínio: RULE_CAUSE_IDS/cause_id_for + _consolidate (items[]/followers[], severidade=máxima, órfão promovido, flag off=v1); acompanhante ancorado no hit icms_amount do lote; chave v2 `branch\|key44\|cause:id`/`doc:`; V037 aditiva + `migrate_entry_audit_status_v2.py` plan/apply idempotente e conservador (v1 «Acompanha»→icms_base); GET/read `entry_audit.pending` consolidado por (filial,nota,causa) latest-wins; KPIs FA-7 `groups` em summary/trend/pending só com linhas v2; occurrence detail com items/total_difference/followers; export «Causa» + linha por item; analyze conta nota+causa; fichas AE-13/AE-14 v1.1; flags PROD false/HML true; testes novos 9/9 + suíte no container 135 passed/2 skipped + MCP 57; verifier ACCEPT_WITH_RESIDUAL r1 (cursor), 0 ordens |
| 2026-11-18 | T18 | HML: rebuild --build + prova SHA/flags + ensaio de migração | runtime HML | imagem em `bf8cfd511a` (script de migração em `6d39cda37f` via docker cp para o ensaio); flags `ENTRY_AUDIT_*` 4× true no container; V037 aplicada no boot; status de PROD copiados (18 linhas: 16 resolved + 2 pending); `plan`=13 grupos (11 resolved/2 pending); `apply` insere 13 + 13 eventos `ENTRY_AUDIT_STATUS_MIGRATED_V2`; 2º apply = 0 inseridos (idempotente); análise `d0af6769` 01–17/11: **146 causas** (163 linhas v1 no rerun anterior); fila `pending`: 146 causas, 143 pending/3 resolved, high 2, medium 127, diff R$ 832,99; 4 ocorrências casam status migrados (3 resolved + 1 pending); corpus `ab85ba5c` (AE-13/14 v1.1) |
| 2026-11-18 | T18 | PROD: backup + flag + migração + rerun | runtime PROD | tag `rollback-entry-audit-fa2-controllership-finance-api` em `de1954a00c`; backup `entry_audit_status` em `/tmp/backup-entry-audit-status-fa2-202611181704.sql`; `.env` com backup + `ENTRY_AUDIT_CAUSE_GROUPING_ENABLED=true`; checkout `6d39cda37f`, rebuild via `up-prod-sequential.sh --build`, container healthy, código novo provado (`cause_id_for`); migração `apply` idêntica ao ensaio (13 inseridas); rerun `0f085369` 01–17/11: **146 causas** (idem HML; 163 linhas v1 antes); status migrados anexados (3 resolved + 1 pending); corpus `5c4548ba` (AE-13: 6 PUB/2 SUP, AE-14: 4/3) |
| 2026-11-18 | T19 | IBS/CBS (onda 3, DEV+HML+PROD) | df95d5d4c6 (merge 256bac7dbf) | api-delpi `/tax-items`+`/tax-book` read-only (SD1→F2D→F2B e CD2; período/filial e por chave, operationIds `list_entry_audit_tax_items`/`tax_book` no registry+metadata); BFF: parser `IBSCBS`/`IBSCBSTot` NF-e+CT-e com CST/cClassTrib, modelos Reform*, gateway, snapshot; motor `ibscbs.xml_not_posted`/`posting_missing` (exclusivas) + `value_mismatch` (item+nota, tolerância, TES+regra no texto) + `book_mismatch` (gate BOOK_FROM+fonte), todas Alta por causa; flags FA-18 (PROD false, HML true); AE-16 + manifest + READMEs; testes api-delpi 17, BFF 335+9 novos; verifier INCONCLUSIVE por indisponibilidade externa (devin sem auth, cursor sem cota até 12/02) |
| 2026-11-18 | T19 | HML: rebuild + prova + ensaio 01–17/11 | runtime HML | `up-hml-sequential.sh --build` api-delpi+BFF; container com `IBSCBS_ENABLED=true`, EXCEPTIONS/BOOK_FROM vazios e ondas 1–2 mantidas; rerun na análise antiga `d0af6769` = 0 `ibscbs.*` (esperado: snapshot FA-18 congela a config); análise nova `24089d66-fbd9-4911-be51-3c53b3ae73c4` 01–17/11: **435 causas** — `ibscbs.value_mismatch` 133 notas, `ibscbs.posting_missing` 108, `ibscbs.xml_not_posted` 48, `ibscbs.book_mismatch` 0 (BOOK_FROM vazio); consolidação por causa (1 causa/nota, até 16 itens); corpus HML `bbe519fd` |
| 2026-11-18 | T19 | PROD: deploy com flag OFF + corpus | runtime PROD | tags `rollback-entry-audit-fa3-api-delpi`/`…-controllership-finance-api` em `ff6e029455`; rebuild `up-prod-sequential.sh --build` dos dois serviços, healthy; `ENTRY_AUDIT_IBSCBS_ENABLED=false` provado no container (ondas 1–2 on); análises existentes seguem v1/v2 sem `ibscbs.*` até nova análise + flag; corpus PROD `8784c0e6` (AE-16, 2653 itens) |
