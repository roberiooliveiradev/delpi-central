# Entry audit — Residuais do back-end e da CLARA (antes do front-end)

| Campo | Valor |
|---|---|
| Data | 2026-11-14 |
| Base | HEAD `6268a2e0fd` (T9R2 em PROD) |
| Como foi levantado | CLARA em PROD (conector MCP, usuário com `controllership-finance.access`): análises da filial 01 de 11, 12 e 13/11/2026 e da filial 02 de 12/11/2026; leitura do código da BFF; ADR-003, track.md, mcp/README.md |
| Regra | o front-end (T10–T13) só começa com esta lista zerada ou com cada item aceito como resíduo pelo owner |

Dado real fica fora deste arquivo (repositório público). As evidências citam a análise e o campo.

## A — Resultado errado ou incompleto

| # | Sev. | Residual | Evidência | Correção |
|---|---|---|---|---|
| A1 | — | «Valor das mercadorias diverge» (Alta) junto da Baixa «Desconto classificado diferente» quando o total confere | 12/11 e 13/11, filial 01. Regra da skill (`regras.py` 327/329) | **DECIDIDO (owner, 2026-11-14): manter como a skill.** Não é residual; a CLARA explica com a ficha que o total confere |
| A2 | Média | `field` e `field_label` = «field» nas ocorrências de origem | `read occurrences`: `item.origin_mismatch` com `field:"field"`, `field_label:"field"`; a `stable_key` traz «CST (origem)» | mapear o código do campo (ex.: `origin`) e o rótulo «CST (origem)» sem mudar a `stable_key` (ou migrar o status junto) |
| A3 | Média | leitura descarta campos que a análise grava | `_persistable` grava `supplier_name`, `series`, `tes`, `difference` na ocorrência; `read occurrences`/`occurrence` não devolvem | projeção de leitura com todos os campos persistidos |
| A4 | Média | «Por quê» igual a «O que fazer» | `header.total_mismatch` e `header.accessory_field`: `why == action`. A skill tem o texto de leitura por ocorrência (`relatorio.py`, dicionário de 31 em diante) | portar o dicionário de leitura; `why` = leitura, `action` = o que fazer |
| A5 | Média | `analyze entry_audit_findings` agrupa tudo como causa «tes» com TES vazia | achados com `cause:"tes"` e «TES —» para regras de cabeçalho e de item | causa real (TES, cadastro do produto, fornecedor, lançamento) por regra; TES vinda da ocorrência (A3) |
| A6 | Baixa | natureza da operação vazia no sem par | `read unmatched`: `nature:""` | ler `natOp` do XML |
| A7 | Baixa | histórico da ocorrência é só o último estado | `occurrence.history` = um item; não guarda quem reabriu | histórico como lista de eventos (resolve/reopen com ator e data), lendo a trilha de auditoria gravada na R8 |

## B — Dados que o dashboard e a CLARA precisam e a BFF não entrega

| # | Sev. | Residual | Evidência | Correção |
|---|---|---|---|---|
| B1 | Média | série «período anterior» sempre vazia | `service.daily`: `"previous": []` fixo | série do período anterior de mesmo tamanho (mesma regra de `_previous_kpis`) |
| B2 | Média | evolução entre análises inutilizável | `read trend`: três análises com `month:"2026-11"`, sem datas | um ponto por análise com `date_from`, `date_to`, filiais, documentos, ocorrências, altas, pendentes, resolvidas; agregação mensal opcional |
| B3 | Média | sem KPIs de valor | `summary.kpis` só tem contagens; doc 02 pede «Valor conferido» e «Diferença nas altas» | somar valor bruto das notas casadas e a diferença das ocorrências Alta |
| B4 | Média | datas de «lançadas fora do período» em lista crua | `summary.conformity.posted_outside_period.received_dates` com 250 datas repetidas; repetido dentro de `analyze` | `[{date, count}]` ordenado; `analyze` traz só o resumo |
| B5 | Média | aba Notas casadas sem filtro por situação | `read documents` com `situation` → 400 | filtro `situation` (`clean`/`divergent`) |
| B6 | Média | andamento não avança durante a leitura do XML | filial 02: `stage:"reading_xml"`, `xml_downloaded:0` por mais de 1 min, até o fim | contadores incrementais (XML lidos / a ler) e etapa atual; percentual só se derivável |
| B7 | Média | detalhe sem link para o documento | `occurrence.links` = null salvo quando há solicitação no LNF (`_links`) | rota da BFF para baixar o XML pela chave (financial-api) e, se houver, a DANFE/DACTE; links no detalhe e no sem par |
| B8 | Média | aba CT-e rasa | `read cte`: só `icms` e `gross`; `fiscal_code:""` | campos da aba CT-e da skill (emitente, tomador, notas vinculadas, CFOP, CST, base, ICMS, crédito pela TES, situação) |
| B9 | Média | exportação não conferida | ninguém comparou a planilha exportada com a da skill | teste com o layout da skill (abas e colunas) e verificação em PROD do arquivo da análise de 12/11 |

## C — CLARA

| # | Sev. | Residual | Evidência | Correção |
|---|---|---|---|---|
| C1 | Média | `analyze entry_audit_findings` inacessível pelo contrato da tool | o schema da tool `analyze` não lista `entry_audit_findings` no enum nem na descrição; `refs:[id]` → 422 `MISSING_REF`; só funciona com `parameters.ref` (não documentado) | aceitar `refs[0]` e `parameters.ref`; enum e descrição atualizados; `compare_to` documentado; teste pelo schema publicado |
| C2 | Baixa | «Quem corrige» `TO_INVENTORY` nas fichas; AE-15 fora do corpus; AE-11 sem texto das normas | fichas AE-xx com P2 aberta; R3 da T9R | P2 decidida: **equipe fiscal/contábil** corrige tudo e aciona as outras áreas → atualizar o campo em todas as fichas e republicar o corpus. AE-15 e textos das normas: ACCEPTED_RESIDUAL (P6, P7) |

## D — Governança, testes e operação

| # | Sev. | Residual | Evidência | Correção |
|---|---|---|---|---|
| D1 | — | escopo S2S emprestado | ADR-003: a api-delpi aceita a BFF em `/financeiro/entry-audit/*` pelo escopo `stock-inventory.read` | **DECIDIDO (owner, 2026-11-14): manter o emprestado** — ACCEPTED_RESIDUAL; a dívida segue registrada no ADR-003 |
| D2 | Média | 39 falhas pré-existentes na suíte da BFF | registro T5: docs ausentes no container, `test_registry_direct_count_is_thirteen` (15 × 13), `LNF_MIGRATIONS_MODE` | corrigir ou marcar com motivo; suíte verde para o gate valer |
| D3 | Média | HML não prova o fluxo real | api-delpi de HML não alcança o Protheus; grant de senha desligado; provas de PROD foram in-process com ator técnico | HML com Protheus de leitura (mesmo banco já usado) e usuário de teste no Keycloak de HML (D15) para teste MCP ponta a ponta |
| D4 | Baixa | evento de auditoria do `run` provado só em teste | registro T9R2 | conferir em PROD o ACT do `run` desta verificação (filial 01 13/11 e filial 02 12/11, canal `mcp/clara`) |
| D5 | Média | toda análise baixa todos os XML da janela | 12/11: 341 XML para 19 notas; filial 02: 321; um mês baixa ~30 dias + o mês, a cada execução | **DECIDIDO (owner, 2026-11-14): guardar o XML autorizado por chave** em tabela do schema `controllership_finance`, reaproveitado entre auditorias; limpeza do XML sem uso há **90 dias**; medir um mês real em PROD antes/depois |
| D6 | Baixa | tags de rollback acumuladas | `rollback-f6-*` (remover em 20/11), `rollback-entry-audit-*`, `-t9r-*`, `-t9r2-*` | calendário de remoção após janela sem incidente |

## E — Decisões do owner (2026-11-14)

| # | Pergunta | Decisão |
|---|---|---|
| D-R1 | Regra de mercadorias com desconto (A1) | manter como a skill (Alta + Baixa) |
| P2 | Quem corrige cada tipo de erro | a equipe fiscal/contábil corrige tudo e aciona as outras áreas |
| P4 | Regras da empresa que a skill não tem | não há outras |
| P5 | TES de frete; TES 036 | seguir as regras da skill: frete pelo CFOP final 352, crédito pelo cadastro da TES (SF4) |
| P6 | Casos reais para a AE-15 | deixar para depois (ACCEPTED_RESIDUAL) |
| P7 | Textos oficiais das normas | ficar `TO_INVENTORY`: a CLARA cita a norma pelo nome e diz que o texto vigente não está anexado |
| Janela | busca de XML no Questor | manter 30 dias |
| D5 | cache do XML | guardar por chave, limpeza após 90 dias sem uso |
| D1 | escopo S2S próprio | manter o emprestado (`stock-inventory.read`) |

## F — Estado depois da T9R3 (`1fa58c3dfc`)

A1, D1 e a janela de 30 dias não mudaram. A verificação de PROD foi in-process (ator técnico); o grant de senha do portal continua desligado. A CLARA reconfere.

| # | Estado | Prova |
|---|---|---|
| A1 | mantido | decisão do owner; o motor não foi alterado nessa regra |
| A2 | FIXED | código `origin`, rótulo «CST (origem)», chave estável com o texto antigo. PROD: 3, 6 e 7 ocorrências de origem nas três análises |
| A3 | FIXED | as ocorrências lidas trazem fornecedor, série, TES e diferença |
| A4 | FIXED | nas três análises, nenhuma ocorrência ficou com a leitura igual à ação |
| A5 | FIXED | `analyze` da filial 01 em 13/11: causas `cadastro` e `lançamento`; 6 achados citam a TES que a ocorrência tem |
| A6 | FIXED | natureza preenchida em todas as sem par (72, 85 e 79) |
| A7 | FIXED | resolver e reabrir na filial 01 de 13/11 gravaram dois eventos; a leitura devolveu os dois e o estado final `pending` |
| B1 | FIXED | `daily.previous` com 1 dia, o tamanho do período |
| B2 | FIXED | o ponto da tendência leva datas, filiais e as contagens; `group=month` agrega |
| B3 | FIXED | o resumo passou a ter `gross_checked` e `high_difference` |
| B4 | FIXED | lançadas fora do período em grupos por data: 21, 22 e 19 |
| B5 | FIXED | `situation=clean` e `situation=divergent` filtram |
| B6 | FIXED | a filial 02 avançou `reading_xml` de 45/329 até 329/329 |
| B7 | FIXED | o detalhe aponta `/entry-audit/xml/{chave}`. DANFE/DACTE continuam no pedido do LNF, quando existe |
| B8 | FIXED | o CT-e da filial 01 traz emitente, tomador, CFOP, CST, base, ICMS, TES e notas vinculadas. A filial 02 nesse dia não teve CT-e |
| B9 | FIXED | T9R4: 11 abas da skill; V028 persiste item_comparison/grouped_note/excluded; 12/11 filial 01 PROD: Itens Comparativo 13, Itens Agrupados 2, Itens Excluídos 7 |
| C1 | FIXED | a tool `analyze` publica o enum com `entry_audit_findings`; `refs[0]` e `parameters.ref` chegam no handler; teste do schema publicado PASS |
| C2 | FIXED | fichas com «Equipe fiscal/contábil (aciona as outras áreas)». Corpus HML `c10c8b3f-63ca-477d-bea5-0aae6bcf3d0d` e PROD `1c8d5014-3a4e-41f0-8698-bd55f777214c`: 104 ingeridas, 0 falhas, 2517 itens, 115 fontes. P2 sumiu das fichas AE. AE-15 não foi ingerida. P7 continua TO_INVENTORY |
| D1 | ACCEPTED_RESIDUAL | escopo emprestado, como o owner decidiu |
| D2 | FIXED | T9R4: fixtures MCP com `has_cf_access`; `invoice_posting.cancel` no conjunto destrutivo; gate `access` exige CF e devolve `{}`; suíte focada 321 PASS |
| D3 | BLOCKED | a api-delpi de HML lê pelas variáveis `ENTRY_AUDIT_DB_*` e devolveu 2 filiais (01 e 02). `DB_HOST` segue `totvs-disabled.hml.invalid`. Falta o usuário de teste do Keycloak de HML para o MCP ponta a ponta. Não foi executado em PROD |
| D4 | FIXED | canal `mcp/clara`: `entry_audit.run` na filial 02 de 12/11; `entry_audit.rerun` na filial 01 de 12/11 e de 13/11. Não há `run` gravado para a filial 01 de 13/11 |
| D5 | FIXED | V027 (`last_used_at`, `cancelled`), limpeza em 90 dias. Filial 02, 12/11: primeira execução baixou 321 XML; a seguinte baixou 0 e reaproveitou 321. A filial 01 de 12/11, no meio, baixou 16 e reaproveitou 325 |
| D6 | FIXED | calendário no track.md. Nenhuma tag foi apagada |

## Verificação desta lista

- Filial 02, 12/11/2026, executada pela CLARA: `done`, 19 NF-e casadas, 10 ocorrências (8 Média, 2 Baixa), 85 sem par, 217 lançadas fora do período, 0 XML indisponível. Sem defeito novo além de B6.
- Filial 01, 13/11/2026, executada pela CLARA: `done`, 20 notas, 10 ocorrências, 1 Alta (é o caso A1).

## Verificação da T9R3 pela CLARA (2026-11-14, PROD) — REWORK

Conferido pelo conector MCP de PROD nas análises de 12/11 (filiais 01 e 02) e 13/11 (filial 01).
PASS: A2, A3, A4, A6, A7 (estrutura), B1, B2, B3, B4, B6 (relatado), B7 (links), B8, C1, C2.

| # | Sev. | Residual | Evidência (CLARA, PROD) | Correção |
|---|---|---|---|---|
| E1 | Alta | `read documents` mistura as «lançadas fora do período» com as notas da análise e ignora `situation` | análise de 12/11 filial 01: `documents` devolve `total: 269` (19 da análise + 250 fora do período); com `situation=divergent` devolve as mesmas 269, com `clean` e `posted_outside_period` misturadas. O in-process do report filtrou; pelo MCP o filtro é aceito e não chega ao serviço | padrão = só as notas recebidas no período (19); `situation` aceito na ponte semântica e aplicado (`clean`, `divergent`, `posted_outside_period`); contagens do summary inalteradas; teste pelo caminho MCP |
| E2 | Média | `difference` calculada em campo de código | ocorrências de origem com `protheus_value 090`, `xml_value 200`, `difference -110.00` (e `-1012.00`, `-2012.00`, `100.00` em 13/11) | `difference` só para campo monetário/quantidade/percentual; `null` para CST, origem, CFOP, NCM, chave, série, espécie, CNPJ, UF; teste por tipo de campo |
| E3 | Média | causa da `analyze` errada em parte das regras (A5 incompleto) | `simples.near_sublimite` sai com causa `lançamento` (é do fornecedor) | tabela regra → causa para TODAS as regras do catálogo (cadastro, lançamento, fornecedor, TES), com teste que percorre o catálogo inteiro |
| E4 | Baixa | nome do fornecedor vazio em nota lançada fora do período | `documents`: fornecedor de código `000001`, loja `13`, `supplier_name: ""` | mesma leitura do SA2 das notas casadas; se o SA2 não tiver a loja, cair para o nome do XML |
| E5 | Baixa | `summary.previous` sem os campos novos | `previous` tem `documents`, `occurrences`, `high`, `pending`; faltam `resolved`, `gross_checked`, `high_difference` | mesmos campos de `kpis` |
| E6 | Baixa | `fiscal_code` vazio no CT-e ao lado de `cfop` preenchido | `read cte`: `cfop: 6353`, `fiscal_code: ""` | preencher ou remover o campo duplicado (contrato) |
| B9 | Média | planilha com 9 das 11 abas | report T9R3 | **DECIDIDO (owner, 2026-11-14): completar as 11 abas.** Guardar na análise o comparativo item a item e as notas agrupadas (o motor já calcula: `grouped_notes: 2` em 12/11); export com «Itens Comparativo» e «Itens Agrupados» no layout da skill |
| D2 | Média | 18 falhas anteriores na suíte da BFF | report T9R3 | **DECIDIDO (owner, 2026-11-14): entram.** Corrigir sem afrouxar asserção; suíte verde |
| D3 | — | MCP ponta a ponta em HML | report T9R3 | **DECIDIDO (owner, 2026-11-14): aceitar sem o teste** — ACCEPTED_RESIDUAL; provas in-process e pela CLARA em PROD |

## Verificação T9R4 (2026-11-14) — FIXED

Código `adaeafe2ea` (+ follow-up null em `difference`). Tags `rollback-entry-audit-t9r4-api-delpi` e `rollback-entry-audit-t9r4-controllership-finance-api` em `dd43e9617f`. HML imagens api `378f8d1100e9`, BFF `f515f20b8bbd`. PROD api `98dc8f26ad1c`, BFF `4b6f0bd9e0a2`. A1, D1, D3 e a janela de 30 dias não reabertos.

| # | Estado | Causa (arquivo) | Serviço | MCP | PROD |
|---|---|---|---|---|---|
| E1 | FIXED | `_LIST_FILTERS` omitia `situation`; default sem `period` — `entry_audit_bridge.py`, `service.documents` | PASS | PASS (`situation=divergent` 11; default 38; outside 467 na análise 01+02) | 12/11 fil01: default 19, outside 250, divergent aplicado |
| E2 | FIXED | `_difference` sem mapa de tipo — `vocabulary.difference_allowed` | PASS | PASS | origem `090`/`200` com `difference` null/vazio (não mais −110) |
| E3 | FIXED | fallback genérico «lançamento» — `domain/entry_audit/causes.py` | PASS | PASS (`cause_for` + analyze) | tabela completa; `simples.near_sublimite` → fornecedor |
| E4 | FIXED | SA2 sem loja exata em by-key — `entry_audit_sql.documents_by_access_keys_sql` + fallback XML | PASS | — | outside page: 0 nomes vazios |
| E5 | FIXED | `_previous_kpis` incompleto — `service._previous_kpis` | PASS | — | `previous` = chaves de `kpis` |
| E6 | FIXED | `fiscal_code: ""` no CT-e — removido de `_cte_comparison`; README §6 | PASS | — | CT-e sem `fiscal_code` |
| B9 | FIXED | abas faltantes sem persistência — V028 + xlsx 11 abas | PASS | — | 12/11 fil01: 11 abas; Comparativo itens 13; Agrupados 2; Excluídos 7 |
| D2 | FIXED | identidade MCP sem `has_cf_access`; DESTRUCTIVE_CAPS sem cancel | 321 PASS focado | — | — |

## Verificação da T9R4 pela CLARA (2026-11-14, PROD) — REWORK pequeno

PASS pelo MCP: E1 (padrão 19; `divergent` 2; `posted_outside_period` filtra), E3 (`simples.near_sublimite` → fornecedor),
E5 (`previous` com os campos de `kpis`). B9: aceito pelo report (11 abas; itens 13, agrupadas 2, excluídos 7) — a CLARA não lê o xlsx.

| # | Sev. | Residual | Evidência (CLARA, PROD) | Correção |
|---|---|---|---|---|
| F1 | Média | E2 não aparece nas análises existentes | 12/11 filial 01: origem `090`/`200` ainda com `difference: "-110.00"`. A análise mostra `xml_cache_hits 325` / `xml_downloaded 16`, os números da T9R3: a reexecução da T9R4 não ficou gravada (ou o valor gravado não é recalculado na leitura) | aplicar a regra de E2 também na leitura (vale para análise antiga); reexecutar e gravar 12/11 (01 e 02) e 13/11 (01) |
| F2 | Baixa | E4 idem | 12/11 filial 01, nota lançada fora do período de fornecedor `000001` loja `13`: `supplier_name: ""` | reexecução gravada; se o SA2 não tiver a loja, nome do XML |
| F3 | Baixa | E6 idem | `read cte` de 12/11 e de 13/11 ainda com `fiscal_code: ""` | remover na leitura e no gravado; reexecução gravada |
| F4 | Baixa | cobertura da `analyze` com filtro diz «0 notas» | `entry_audit_findings` com `theme=simples` em 13/11: «0 notas, 1 ocorrências» | com filtro, o FACT de cobertura diz o filtro aplicado e não zera as notas da análise (ou é omitido) |
| F5 | — | D2 sem prova de suíte inteira | report: «321 PASS»; a suíte inteira da BFF tinha ~1.300 testes | report com o comando e o total da suíte inteira (PASS/FAIL/skip) contra o commit pai |

## Verificação T9R5 (2026-11-14) — FIXED

Código `18cc94e0c9` + V029 `e9481483b5`. Tag `rollback-entry-audit-t9r5-controllership-finance-api` em `fb7defce8d`. HML BFF `29e74bef9d07`. PROD BFF `c533f3146afc`. Causa da T9R4 sem gravar: `difference` NOT NULL na V023 — write com null caía em `NotNullViolation`; V029 torna a coluna nullable. A1, D1, D3 e a janela de 30 dias não reabertos. T10 não começou.

| # | Estado | Causa (arquivo) | Serviço | MCP | PROD |
|---|---|---|---|---|---|
| F1 | FIXED | `_public_occurrence` devolvia `difference` gravada — `service._public_occurrence` + `difference_allowed` | PASS | PASS | 12/11 01: 3 origens com `difference` null; contadores `cache 341` / `dl 0` (não mais 325/16) |
| F2 | FIXED | SA2 sem loja → nome vazio — `_posted_outside` + fallback XML/`party_name` | PASS | PASS | 12/11 01 outside 250, `000001/13` com nome; 0 vazios na página |
| F3 | FIXED | JSON antigo com `fiscal_code: ""` — strip em `service.ctes` | PASS | PASS (`read cte`) | 12/11 01: 7 CT-e sem `fiscal_code`; 13/11 01: 1 CT-e sem |
| F4 | FIXED | `theme` zerava documentos no summary — `_FILTERS_BY_KIND` + cobertura declara filtro | PASS | PASS | 13/11: «20 notas (filtro: theme=simples), 1 ocorrências» |
| F5 | FIXED | suíte focada ≠ suíte inteira | HEAD: `docker … pytest tests` → **1354 PASS, 1 FAIL, 280 skip**; pai `fb7defce8d`: **1349 PASS, 1 FAIL, 280 skip**. A FAIL (`test_avatar_read_returns_image_content_block`) é pré-existente nos dois | — | — |

Reexecução PROD via `execute entry_audit.rerun`: `b75deca4…` (12/11 01), `942763cb…` (12/11 02), `76d55935…` (13/11 01) — todas `done`.

