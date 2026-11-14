# Prompt para o Cursor — Entry audit, T9R4 (residuais da verificação da T9R3)

```text
PROMPT CURSOR — ENTRY AUDIT · T9R4 — fechar os residuais achados na verificação da T9R3 pela CLARA

CONTEXTO
A T9R3 foi conferida pela CLARA em PROD (conector MCP real, não in-process) em 14/11/2026: REWORK.
A lista está em docs/12-roadmap-e-evolucao/controllership-finance/entry-audit/residuals.md, seção
«Verificação da T9R3 pela CLARA», com evidência e correção por item, e as decisões do owner para
B9, D2 e D3. O front-end continua parado até esta lista zerar. Dado real só no report.

FONTE DE VERDADE
entry-audit/residuals.md · track.md (protocolo, paradas, rollback) · backend/README.md §6 ·
mcp/README.md · reference/ (skill). Autoridade: instruções oficiais do arquiteto e .cursor > ADR-003 >
track.md > residuals.md > demais docs.

MISSÃO
Corrigir sem parar entre itens, nesta ordem: E1, E2, E3, B9, E4, E5, E6, D2.
Não reabrir: A1 (regra da skill), D1 (escopo emprestado), D3 (aceito sem o teste), janela de 30 dias.

REGRA NOVA DE PROVA (motivo: E1 passou in-process e falhou pela CLARA)
Todo item que mexe em leitura ou análise é provado também pelo CAMINHO MCP — semantic bridge +
catálogo + schema publicado da tool, com os mesmos parâmetros que a CLARA envia (filters/ref/refs) —
num teste automatizado, além do teste de serviço. Report mostra os dois.

POR ITEM (detalhe em residuals.md)
E1 documents: padrão = notas recebidas no período; situation (clean | divergent | posted_outside_period)
   aceito na ponte e aplicado; summary inalterado. Revisar todos os filtros declarados no schema de
   cada read entry_audit.* — cada filtro aceito precisa chegar ao serviço (teste paramétrico pelo MCP).
E2 difference só para campos numéricos; null para código (CST, origem, CFOP, NCM, chave, série,
   espécie, CNPJ, UF). Mapa de tipo por campo no vocabulário; teste.
E3 tabela regra → causa para todas as regras do catálogo; teste que percorre o catálogo inteiro e
   falha se alguma regra não tiver causa ou cair no padrão.
B9 persistir o comparativo item a item e as notas agrupadas (migration aditiva, sem reescrever V023–V027);
   export com as 11 abas da skill na mesma ordem e colunas; teste de layout contra a skill
   (reference/.../scripts/relatorio.py) com fixture sintética; conferência em PROD do arquivo da
   análise de 12/11 filial 01 (abas, contagem de linhas de cada aba).
E4 nome do fornecedor: SA2 por código+loja; sem a loja, nome do XML.
E5 summary.previous com os mesmos campos de kpis.
E6 CT-e: preencher fiscal_code ou removê-lo do contrato (atualizar backend §6).
D2 as 18 falhas anteriores da suíte da BFF (contexto MCP sem usuário; flag destrutivo de
   invoice_posting.cancel): corrigir a causa, sem afrouxar asserção nem pular teste. Se uma falha
   revelar comportamento errado do produto (não do teste), corrigir o produto e dizer no report.
   Meta: suíte da BFF verde.

REGRAS
As do prompt T0–T9 (main sem branch; commits só da etapa; protocolo P1–P9; até 3 ciclos; somente
leitura no Protheus, no Questor e no LNF; sem tool nova na CLARA; sem permission nova; sem dado real
no repo; suíte comparada ao commit pai). Contrato aditivo, salvo E6 (remoção documentada). HML
primeiro; PROD com tag rollback-entry-audit-t9r4-<serviço>, um serviço por vez (OK do owner dado).
Falha → rollback e BLOCKED X7.

FECHAMENTO
Reexecutar em PROD as análises de 12/11 (filiais 01 e 02) e 13/11 (filial 01). Atualizar residuals.md
(cada item FIXED com SHA | ACCEPTED_RESIDUAL | BLOCKED), quadro e registro do track.md.

REPORT
Formato da track.md Parte 9, um bloco por item: causa (arquivo:linha), correção (SHA), teste de
serviço e teste pelo caminho MCP (PASS/FAIL), evidência PROD, tags. Parar ao concluir.
```
