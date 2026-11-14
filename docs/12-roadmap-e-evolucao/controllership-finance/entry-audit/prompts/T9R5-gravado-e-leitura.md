# Prompt para o Cursor — Entry audit, T9R5 (o que foi corrigido tem que aparecer na CLARA)

```text
PROMPT CURSOR — ENTRY AUDIT · T9R5 — análises gravadas em PROD refletindo a T9R4

CONTEXTO
A T9R4 foi conferida pela CLARA em PROD em 14/11/2026. E1, E3 e E5 PASS pelo MCP. E2, E4 e E6
continuam visíveis pela CLARA nas análises gravadas: a análise de 12/11 filial 01 ainda mostra os
contadores da T9R3 (xml_cache_hits 325 / xml_downloaded 16), ou seja, a reexecução do report não
ficou gravada ou a leitura devolve o valor antigo. Itens F1–F5 em
docs/12-roadmap-e-evolucao/controllership-finance/entry-audit/residuals.md
(seção «Verificação da T9R4 pela CLARA»). Dado real só no report.

MISSÃO (sem parar entre itens)
F1 regra de E2 (difference null em campo de código) aplicada também na projeção de leitura.
F3 fiscal_code fora da leitura do CT-e (e do gravado).
F2 nome do fornecedor: SA2 por código+loja; sem a loja, nome do XML.
F4 cobertura da analyze com filtro: declarar o filtro; não dizer «0 notas» da análise.
F5 rodar a suíte INTEIRA da BFF (todas as pastas de teste) no HEAD e no commit pai; reportar comando e
   totais. Falha nova = corrigir.
Depois: rerun GRAVADO em PROD (pelo caminho normal, o mesmo da CLARA: execute entry_audit.rerun) das
análises de 12/11 filial 01, 12/11 filial 02 e 13/11 filial 01. Prova pelo caminho MCP (semantic bridge,
mesmos parâmetros da CLARA) de: origem sem difference; fornecedor 000001/13 com nome; CT-e sem
fiscal_code; contadores da análise com data da reexecução nova.

REGRAS
As da trilha (main sem branch; commits só da etapa; protocolo P1–P9; até 3 ciclos; somente leitura no
Protheus/Questor/LNF; sem tool nova; sem permission nova; sem dado real no repo). HML primeiro; PROD com
tag rollback-entry-audit-t9r5-controllership-finance-api (e api-delpi se tocar), um por vez. Falha →
rollback e BLOCKED X7. Não reabrir A1, D1, D3 nem a janela de 30 dias.

FECHAMENTO
residuals.md (F1–F5 com status e SHA), quadro e registro do track.md. Parar ao concluir.
```
