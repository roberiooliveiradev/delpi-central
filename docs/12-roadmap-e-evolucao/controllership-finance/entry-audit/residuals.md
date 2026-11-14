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

## Verificação desta lista

- Filial 02, 12/11/2026, executada pela CLARA: `done`, 19 NF-e casadas, 10 ocorrências (8 Média, 2 Baixa), 85 sem par, 217 lançadas fora do período, 0 XML indisponível. Sem defeito novo além de B6.
- Filial 01, 13/11/2026, executada pela CLARA: `done`, 20 notas, 10 ocorrências, 1 Alta (é o caso A1).
