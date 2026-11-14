# Prompt para o Cursor — Entry audit, T9R2 (nota «sem par» conferida na SF1 pela chave)

```text
PROMPT CURSOR — ENTRY AUDIT · T9R2 — «só no XML» precisa ser conferida na SF1 pela chave

CONTEXTO
A T9R foi verificada pela CLARA em PROD em 14/11/2026: R1 (escrita pela CLARA), R2 (mesmo número),
R3 (corpus) e R4 (campos do sem par) PASS. A CLARA executou entry_audit.run para 13/11/2026 e a
análise chegou a done. Ficaram os itens abaixo. Dado real só no report, nunca no repo.

FONTE DE VERDADE
docs/12-roadmap-e-evolucao/controllership-finance/entry-audit/ (track.md, plan.md D11, backend/, mcp/).
Autoridade: instruções oficiais do arquiteto e .cursor > ADR-003 > track.md > demais docs.

R6 · Alta · «Não escriturada na SF1» afirmado sem consultar a SF1
  Evidência: application/entry_audit/service.py — execute() lê a SF1 só por recebimento entre
  date_from e date_to; _xml_payloads() lista o Questor por emissão de date_from − 30 dias até date_to.
  Todo XML desses 30 dias cuja nota foi lançada FORA do período auditado vira «Recebida de terceiro e
  ainda não escriturada na SF1» (Média) ou «Entrada com formulário próprio autorizada e sem lançamento
  na SF1» (Alta). Em 12/11, filial 01: 290 sem par em aberto e 21 Alta de formulário próprio emitidas
  três semanas antes. A frase é falsa para toda nota lançada antes do período.
  D11 diz que a listagem com folga serve «só para achar o que não foi lançado» — a implementação não
  confere se foi lançado. Não é mudança de decisão; é cumprir D11.
  Correção:
  1. api-delpi: a rota existente GET /financeiro/entry-audit/documents aceita também uma lista de
     chaves de acesso (ex.: access_keys, em lote, POST de leitura se o tamanho exigir — seguir o
     padrão da api-delpi), sem filtro de data, devolvendo filial, chave, número, série, fornecedor,
     data de digitação/recebimento e espécie. Só leitura. Considerar notas excluídas
     (D_E_L_E_T_) como não lançadas.
  2. BFF: depois de listar o Questor, consultar na SF1 pela chave todas as chaves «só no XML».
     - Encontrada na SF1 (outra data): NÃO é sem par. Não grava ocorrência. Contar à parte em
       summary.conformity como «lançada fora do período» (nome de campo no contrato) e mostrar a data.
     - Não encontrada: continua sem par, com a situação de hoje (LNF, em trânsito, formulário próprio…).
  3. Formulário próprio (emitente = CNPJ da filial): a mesma consulta vale. Só é Alta se não estiver
     na SF1 com nenhuma data.
  Teste: corpus sintético com XML emitido 20 dias antes, lançado 10 dias antes (fora do período) →
  não aparece em sem par; XML emitido 20 dias antes sem SF1 → aparece; formulário próprio lançado
  → não aparece. Contrato e backend §6 atualizados. Paridade com a skill preservada (a skill trabalha
  com SF1 e XML do mesmo recorte; registrar que a melhoria é D11).
  PROD: rerun de 12/11 e 13/11, filial 01 — mostrar sem par antes/depois e as Alta de formulário
  próprio antes/depois.

R7 · Média · «Em trânsito» fora do que a trilha especifica
  Evidência: report T9R — a folga usa a maior emissão dos XML baixados e a severidade continua Média.
  track.md (T5 item 4): «só no XML» emitida há menos de ENTRY_AUDIT_UNMATCHED_GRACE_DAYS = Info
  «em trânsito».
  Correção: referência = date_to da análise; severidade Info; frase «em trânsito». Teste com a data
  na borda (date_to − 3, date_to − 4).

R8 · Média · Trilha de auditoria das escritas da CLARA não grava
  Evidência: report T9R — closing_audit_event não grava run/rerun/resolve/reopen porque entity_id e
  actor_subject são UUID e a stable_key da ocorrência não é.
  Correção: gravar o evento com o id da análise (run/rerun) e com o id persistido da linha de status
  (resolve/reopen) em entity_id, guardando a stable_key no payload. Sem migration de tipo em tabela
  compartilhada, salvo se for o padrão vigente. Teste: os quatro eventos aparecem com ator, canal
  (mcp/clara ou portal) e idempotency_key.

R9 · Baixa · Acompanhar uma análise pelo id
  Evidência: read entry_audit.analysis com ref=<id> → 400 «Parâmetros desconhecidos: analysis_id».
  A diretiva manda a CLARA «acompanhar read entry_audit.analysis até done», mas hoje ela precisa
  listar e filtrar por datas.
  Correção: aceitar ref/analysis_id e devolver a análise com status, estágio, contagens por filial e
  erro, quando houver. Teste de catálogo/schema.

NÃO MUDAR (decisão do owner pendente)
- A janela de 30 dias (ENTRY_AUDIT_XML_LOOKBACK_DAYS).
- A regra da skill «Valor das mercadorias diverge» + «Desconto classificado diferente».

REGRAS
As do prompt T0–T9 (main sem branch; protocolo P1–P9; até 3 ciclos; somente leitura no Protheus,
no Questor e no LNF; sem tool nova na CLARA; sem permission nova; sem dado real no repo; suíte
comparada ao commit pai). HML primeiro; PROD com tag rollback-entry-audit-t9r2-<serviço>, um serviço
por vez, api-delpi antes da BFF (OK do owner dado). Falha em PROD → rollback e BLOCKED X7.

REPORT
Formato da track.md Parte 9, um bloco por R6–R9: causa (arquivo:linha), correção (SHA), teste,
evidência HML e PROD, contagens antes/depois (sem par, Alta de formulário próprio, lançadas fora do
período), tags de rollback, quadro de status e registro. Parar ao concluir.
```
