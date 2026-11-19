# ADR-006 — Ajustes do Fiscal na auditoria de entradas

| Campo | Valor |
|---|---|
| Status | **ACCEPTED** |
| Data | 2026-11-18 |
| Decisor | owner do produto (decisões no chat do arquiteto; transcritas na trilha) |
| Contexto | 5 ajustes pedidos pelo Fiscal sobre a análise de 01–17/11/2026; inventário T14 `79980f8c7b` e complementar T15 |
| Relacionados | [ADR-003](./ADR-003-entry-audit.md) · [trilha dos ajustes](../entry-audit/fiscal-adjustments/track.md) · [inventory](../entry-audit/fiscal-adjustments/inventory.md) · [contrato](../entry-audit/backend/README.md) §7 |

## Decisão

Os cinco ajustes entram na auditoria existente, em **ondas separadas por flag** (FA-18). As decisões FA-1 a FA-18 abaixo são definitivas e não se reabrem; a ordem de execução é T15 → T23 no track.

| Id | Decisão |
|---|---|
| FA-1 | Participante pelo tipo da nota: `F1_TIPO IN ('B','D')` → cliente (SA1); demais → fornecedor (SA2). Leitura canônica na api-delpi (D2). O LNF mantém a sua regra B→SA1 no próprio contexto — a duplicação fica registrada abaixo. |
| FA-2 | Cliente com CNPJ ≠ emitente: Alta com texto «cliente»; `cfop_vs_state` usa a UF do mesmo cadastro; mesma raiz/outro estabelecimento continua Alta. |
| FA-3 | `ENTRY_AUDIT_INPUT_TES` (018, 052, 069, 106, 166, 169, 406): nessas TES não se gera `coherence.ipi_on_consumption` — **exclusão**, não regra nova. |
| FA-4 | Uma ocorrência por causa: itens dentro da causa, acompanhante vira detalhe, resolver/reabrir age na causa, indicadores contam causas. |
| FA-5 | Fila consolidada por chave de acesso + causa, não por análise. |
| FA-6 | Migração de status v1→v2: causa resolvida só se todas as linhas antigas dela estavam resolvidas; histórico preservado; comando explícito com ensaio em HML e backup em PROD. |
| FA-7 | Indicadores em 3 grupos (sem problema / corrigidas / com divergência pendente), recalculados a cada mudança de status; mais Altas e Médias pendentes e diferença em R$ das pendentes. |
| FA-8 | IBS/CBS em todas as entradas, NF-e e CT-e, severidade Alta; lançamento `SD1.D1_IDTRIB = F2D.F2D_IDREL`, regra F2B por `F2D_IDCAD`; imposto por `F2B_TRIB` (CBSFED, IBSEST, IBSMUN); XML pelo grupo `IBSCBS`. |
| FA-9 | Exceções IBS/CBS por `ENTRY_AUDIT_IBSCBS_EXCEPTIONS` (CRT, CFOP ou TES), vazia no início — fornecedor do Simples entra. |
| FA-10 | Tolerância IBS/CBS = `ENTRY_AUDIT_TOLERANCE` (R$ 0,05), por item e por nota. |
| FA-11 | CST/cClassTrib: a T15 confirmou que **não há fonte estruturada no lançamento** (SD1/F2B/F2D sem colunas; só o texto `F2B_DESC`, que não se lê). A 1ª versão compara presença, base, alíquota e valor; CST/cClassTrib ficam residuais para uma tabela de-para regra F2B → CST/cClassTrib mantida pelo Fiscal. A `DKM010` (lado XML importado) existe como referência, mas a BFF lê o XML direto. |
| FA-12 | Livro fiscal IBS/CBS a partir de `ENTRY_AUDIT_IBSCBS_BOOK_FROM=2027-01-01`. A T15 achou fonte estruturada: `CD2010` (livro digital, por item, com `CD2_IMP`/`CD2_CST`/`CD2_BC`/`CD2_ALIQ`/`CD2_VLTRIB`). A SFT não tem colunas de IBS/CBS — o livro da reforma é o CD2. |
| FA-13 | Reverificação **sob demanda** (botão e CLARA); D10 mantida, sem agendamento. Não é nova análise: relê Protheus e XML em cache só das notas com causa pendente ou resolvida à mão. |
| FA-14 | Divergência que não se repete → «resolvida automaticamente» (`resolution_source=auto`, evento com antes/depois); com outro valor → atualiza e registra. `_unusual_nature` e a heurística `seen` não se resolvem automaticamente. |
| FA-15 | Resolvida à mão que ainda aparece: continua resolvida com a marca «divergência persiste». |
| FA-16 | FA-1/FA-2 e FA-3 entram também na skill de referência (cópia `reference/` pelo agente, skill da conta pelo owner). Paridade roda com as ondas 2–4 desligadas. Exportação uma linha por item com coluna «Causa». |
| FA-17 | Sem permission nova; seis tools iguais; `entry_audit.reverify` é escrita direta. |
| FA-18 | Flags por onda (padrão `false`, ligadas em PROD só após HML PASS): onda 1 `ENTRY_AUDIT_PARTICIPANT_BY_TYPE_ENABLED` + `ENTRY_AUDIT_INPUT_TES`; onda 2 `ENTRY_AUDIT_CAUSE_GROUPING_ENABLED`; onda 3 `ENTRY_AUDIT_IBSCBS_ENABLED`; onda 4 `ENTRY_AUDIT_REVERIFY_ENABLED`. Rotas novas de leitura da api-delpi sem flag. |
| FA-19 | IBS/CBS só compara quando o XML traz o grupo (owner, 18/11): lançamento com IBS/CBS e XML sem `IBSCBS` **não** gera ocorrência — não está entre as quatro validações do documento do Fiscal. Valores só se comparam com `document.has_ibscbs` (total da nota, NF-e e CT-e) e `xml_item.has_ibscbs` (item). Sem regra nova; FA-8 a FA-11 intactas. |

## Duplicação registrada — «B/D → SA1»

O conceito «nota tipo B/D tem participante no cadastro de clientes» existe hoje em dois bounded contexts:

- **invoice_posting (LNF, esta BFF):** `infrastructure/invoice_posting/totvs_invoice_posting_sf1_sql.py` resolve `F1_TIPO='B'` → SA1 no fluxo de lançamento.
- **entry audit (api-delpi + esta BFF):** a partir da onda 1, `documents`/`documents_by_access_keys` devolvem `participant_*` por `F1_TIPO` (FA-1).

Decisão: cada contexto mantém a sua leitura — o LNF não muda (fora do escopo dos ajustes) e a auditoria resolve pela api-delpi (D2: owner canônico da leitura TOTVS). O conceito é o mesmo e a implementação permanece por contexto; se um dia o LNF precisar do mesmo campo `participant_*`, o contrato `/financeiro/entry-audit` já o oferece — mas a união das duas leituras num adapter compartilhado ficaria como dívida técnica consciente, não nesta trilha.

## Consequências

- As 10 notas B/D com CNPJ da SA1 ≠ emitente são todas emitidas pela própria empresa (T15 §6.1): a Alta «cliente» cresce de ~6 para ~10 — comportamento previsto pela regra do Fiscal (aviso da Parte 4 do track).
- Ajuste 3 é exclusão por lista de TES: `coherence.ipi_on_consumption` some nas TES configuradas; a T15 mediu 4/4 saídas na análise canônica.
- A regra `ibscbs.book_mismatch` nasce desligada mas **com fonte** (`CD2010`) — a descoberta da T15 mudou o resultado esperado de «sem fonte» para «fonte achada, gate por data».

## Alternativas rejeitadas

- Mudar `F4_CONSUMO` na SF4 para corrigir o ajuste 3: afeta custo e livros — descartado pelo owner (FA-3).
- Agendamento periódico para a reverificação: D10 mantida (FA-13) — fica o gatilho sob demanda.
- Fila por análise: substituída pela fila consolidada por causa (FA-5) porque 12 análises se sobrepõem no período.
- Ler CST/cClassTrib do texto `F2B_DESC`: frágil; FA-11 prefere o de-para mantido pelo Fiscal.
