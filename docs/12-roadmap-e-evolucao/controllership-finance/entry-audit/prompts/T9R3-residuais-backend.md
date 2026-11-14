# Prompt para o Cursor — Entry audit, T9R3 (zerar os residuais do back-end e da CLARA)

```text
PROMPT CURSOR — ENTRY AUDIT · T9R3 — zerar os residuais do back-end e da CLARA antes do front-end

CONTEXTO
O owner decidiu: o front-end (T10–T13) só começa sem residual de back-end. A lista completa,
levantada pela CLARA em PROD e pela leitura do código em 14/11/2026, está em
docs/12-roadmap-e-evolucao/controllership-finance/entry-audit/residuals.md.
Cada item tem severidade, evidência e correção esperada. Dado real só no report.

FONTE DE VERDADE
entry-audit/residuals.md (lista e critério) · track.md (protocolo, paradas, rollback) ·
backend/README.md §6 (contrato) · mcp/README.md · reference/ (skill). Autoridade: instruções oficiais
do arquiteto e .cursor > ADR-003 > track.md > residuals.md > demais docs.

MISSÃO
Corrigir, nesta ordem, sem parar entre itens: A2 → A7, B1 → B9, C1, D2, D3, D4, D5, D6, D1.
A1 só entra se residuals.md tiver a decisão D-R1 registrada pelo owner; sem ela, não tocar.
Parar SOMENTE numa regra X1–X8, num DECISION_REQUIRED real (escolha de produto) ou ao concluir.

POR ITEM (detalhe em residuals.md)
A2 field/field_label das ocorrências de origem; sem quebrar a stable_key (se mudar, migrar o status).
A3 projeção de leitura com supplier_name, series, tes, difference (e o que mais for persistido).
A4 portar o dicionário de leitura da skill (relatorio.py): why = leitura, action = o que fazer.
A5 analyze entry_audit_findings com a causa real por regra (TES, cadastro do produto, fornecedor,
   lançamento) e a TES da ocorrência.
A6 natOp do XML no sem par.
A7 histórico da ocorrência = lista de eventos com ator e data (trilha gravada na R8).
B1 daily.previous com o período anterior de mesmo tamanho.
B2 trend com um ponto por análise (datas, filiais, documentos, ocorrências, altas, pendentes,
   resolvidas) e agregação mensal opcional.
B3 KPIs de valor: valor bruto conferido e diferença das Altas.
B4 posted_outside_period agrupado [{date, count}]; analyze só com o resumo.
B5 filtro situation (clean/divergent) em documents.
B6 andamento incremental na leitura do XML (lidos / a ler) e etapa atual; sem percentual inventado.
B7 rota da BFF para o XML pela chave (financial-api, credencial de serviço) e DANFE/DACTE quando
   houver; links no detalhe e no sem par. Autorização: controllership-finance.access + filial da nota.
B8 aba CT-e com os campos da aba CT-e da skill.
B9 teste do export contra o layout da skill (abas, colunas, ordem) e conferência em PROD do arquivo
   da análise de 12/11 filial 01.
C1 analyze: aceitar refs[0] e parameters.ref; entry_audit_findings e compare_to no enum e na
   descrição publicados da tool; teste pelo schema publicado (sem tool nova).
D2 39 falhas pré-existentes da suíte da BFF: corrigir; o que não for corrigível nesta trilha, marcar
   com motivo e owner do teste. Meta: suíte verde.
D3 HML com o caminho real: api-delpi de HML lendo o banco de leitura já usado; usuário de teste no
   Keycloak de HML (D15) e teste MCP ponta a ponta run → analysis → analyze → occurrence → resolve →
   reopen contra o endpoint MCP de HML. Nunca em PROD.
D4 conferir em PROD o ACT do run feito pela CLARA em 14/11 (filial 01 13/11 e filial 02 12/11,
   canal mcp/clara).
D5 cache do XML autorizado por chave (não muda), com limpeza; medir um mês real em PROD antes/depois.
D6 calendário de remoção das tags de rollback no track.md (rollback-f6-* em 20/11; demais após janela
   sem incidente). Não remover nada agora.
D1 escopo S2S próprio da auditoria (ex.: entry-audit.read): criar e usar em HML (D15). Em PROD a
   mudança no Keycloak não está autorizada: entregar o runbook pronto e parar em X8 só neste item.

REGRAS
As do prompt T0–T9 (main sem branch; commits só da etapa; protocolo P1–P9; até 3 ciclos; somente
leitura no Protheus, no Questor e no LNF; sem tool nova na CLARA; sem permission de usuário nova;
sem dado real no repo; suíte comparada ao commit pai). Mudança de contrato aditiva, com backend §6 e
mcp/README atualizados no mesmo commit. HML primeiro; PROD com tag rollback-entry-audit-t9r3-<serviço>,
um serviço por vez, api-delpi → financial-api → BFF (OK do owner dado). Falha → rollback e BLOCKED X7.
A janela de 30 dias não muda.

FECHAMENTO
Atualizar residuals.md: cada item com status (FIXED com SHA | ACCEPTED_RESIDUAL com motivo |
BLOCKED com o que falta). Reexecutar em PROD as análises de 12/11 (filiais 01 e 02) e 13/11 (filial
01) e mostrar, pela leitura da BFF, cada item corrigido.

REPORT
Formato da track.md Parte 9, um bloco por item: causa (arquivo:linha), correção (SHA), teste
(PASS/FAIL), evidência HML e PROD, tags, quadro de status e registro atualizados. Parar ao concluir.
```
