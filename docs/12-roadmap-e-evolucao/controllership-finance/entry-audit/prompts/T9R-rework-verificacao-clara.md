# Prompt para o Cursor — Entry audit, T9R (rework da verificação pela CLARA em PROD)

```text
PROMPT CURSOR — ENTRY AUDIT · T9R — corrigir os defeitos achados na verificação pela CLARA (PROD)

CONTEXTO
A trilha T0–T9 foi entregue como DONE. A verificação do owner pela CLARA (track.md Parte 7), feita em
14/11/2026 pelo conector MCP de PROD com um usuário que tem só controllership-finance.access, deu
REWORK. O catálogo aparece certo (read entry_audit.*, analyze entry_audit_findings, execute
run/rerun/resolve/reopen). Os defeitos abaixo foram observados em PROD sobre a análise de
12/11/2026, filial 01, NF-e + CT-e (a análise que você criou na T9). Dado real só no report, nunca no repo.

FONTE DE VERDADE
docs/12-roadmap-e-evolucao/controllership-finance/entry-audit/ (track.md, plan.md, backend/, mcp/,
reference/). Autoridade: instruções oficiais do arquiteto e .cursor > ADR-003 > track.md > demais docs.

DEFEITOS (corrigir todos, nesta ordem)

R1 · Alta · Escrita da CLARA bloqueada
  Evidência: execute(entity=entry_audit, action=run, params={date_from:2026-11-12, date_to:2026-11-12,
  document_types:[nfe,cte], branches:[01]}) → 503 {"error_code":"snapshot_unavailable"} ("Snapshot do
  recurso indisponível — operação bloqueada"). O mesmo com phase=prepare. A análise só existe porque
  foi criada pela rota HTTP.
  Provável causa: o pipeline de escrita do MCP lê o estado do recurso antes de escrever (OCC/read-back)
  e não há leitor de snapshot para resource_type entry_audit_analysis nem entry_audit_status (ou ele
  falha em "criar", onde não existe recurso anterior).
  Correção: registrar o snapshot desses dois resource_types no mesmo mecanismo das ações diretas que
  já funcionam (ex.: pendency.create, invoice_posting.comment): para run, snapshot "inexistente" é
  válido; para rerun, o estado da análise; para resolve/reopen, o status da ocorrência pela stable_key.
  Read-back: run/rerun → análise criada/reaberta (status queued|running|done); resolve/reopen → status
  novo da ocorrência.
  Teste: pelo pipeline REAL de execute (sem mock do snapshot), um teste por ação; idempotência
  (mesma chave → mesmo resultado). Explicar no report por que o teste in-process da T7 não pegou.

R2 · Alta · Ocorrência atribuída ao documento errado quando dois documentos têm o mesmo número
  Evidência: no dia há duas NF-e com o mesmo número de documento, de fornecedores e chaves diferentes.
  As 2 ocorrências de cabeçalho da nota A aparecem também ligadas à nota B:
  - read occurrences devolve 7 itens; os 2 de cabeçalho vêm DUPLICADOS (mesma stable_key duas vezes);
  - summary: occurrences 7, high 2 (o certo é 5 e 1);
  - breakdowns.suppliers atribui 4 ocorrências ao fornecedor da nota B e nenhuma ao da nota A;
  - documents: as duas notas aparecem como divergent com divergence_count 2.
  Correção: toda junção entre documento, itens, XML, ocorrências e status usa a chave de acesso (ou,
  sem chave, filial+fornecedor+loja+número+série) — nunca só o número. Listagens deduplicam por
  stable_key. Recalcular contagens e breakdowns a partir das ocorrências únicas.
  Teste: corpus sintético com duas notas de mesmo número e fornecedores diferentes (uma divergente,
  outra limpa) — a limpa fica limpa; KPIs, breakdowns, export e CLARA batem. Reexecutar a análise de
  12/11 em PROD depois do deploy (rerun) e mostrar 5 ocorrências, 1 Alta, nota B limpa.

R3 · Média · Fichas da auditoria de entradas fora do corpus publicado em PROD
  Evidência: knowledge(search, "origem da mercadoria divergente CST primeiro dígito auditoria de
  entradas") devolve só itens do LNF. O corpus publicado em PROD é 38066692-…, publicado em
  2026-11-13 10:49, 100 fontes / 2373 itens. O report da T9 cita 104 fontes / 2517 itens.
  Correção: publicação governada do corpus em PROD com as fichas AE-00..AE-15 (domínio
  controllership). Prova: knowledge(sources) com a versão nova e knowledge(search) devolvendo a ficha
  da regra item.origin_mismatch com citação (fonte, locator). Se a publicação exigir ato do owner,
  parar e dizer exatamente o comando/tela (X8).

R4 · Média · Notas sem par sem os dados que permitem agir
  Evidência: read unmatched devolve issue_date "", amount null, supplier_name/party_name "" e
  series "" em todos os itens (NF-e e CT-e). A aba «Só no XML» da skill traz emissão, emitente, CNPJ,
  UF, natureza, CFOP, CST, valor total, base, ICMS e IPI. Também: breakdowns.tes vem vazio (a nota com
  3 ocorrências usa uma TES) e um documento casado vem com supplier_name vazio.
  Correção: preencher esses campos a partir do XML (lado xml) e da SF1/SA2 (lado sf1); breakdowns.tes
  pela TES dos itens envolvidos; supplier_name pelo SA2 quando o XML não tiver. Atualizar o contrato
  (backend §6) se faltar campo.
  Teste: fixture sintética de «só no XML» e «só na SF1» com todos os campos; asserção no read e no export.

R5 · Evidência pendente (não é defeito ainda)
  a) summary.conformity.unmatched_explained = 32: mostrar no report a contagem por situação
     (Em lançamento (LNF), em trânsito, XML indisponível, outra) com a regra de cada uma. Nos itens
     lidos nenhum veio com lnf_request_id preenchido nem com situação «em trânsito».
  b) Confirmar que «só no XML» emitida a menos de ENTRY_AUDIT_UNMATCHED_GRACE_DAYS do date_to recebe
     Info «em trânsito» (os itens lidos são todos Média).

NÃO MUDAR (decisão do owner pendente — ver report do Claude)
- A janela de 30 dias da listagem do Questor (track.md T5 item 4) e o que entra em «só no XML».
- A regra da skill que gera «Valor das mercadorias diverge» (Alta) junto de «Desconto classificado
  diferente» (Baixa, total confere). A paridade com a skill está correta; mudar a regra é decisão do owner.

REGRAS
As mesmas do prompt T0–T9 (main sem branch; protocolo P1–P9; até 3 ciclos por problema; somente
leitura no Protheus/Questor/LNF; sem tool nova na CLARA; sem permission nova; sem dado real no repo;
suíte comparada ao commit pai). Deploy: HML primeiro (rotas + CLARA in-process + MCP se houver
endpoint), depois PROD com tag rollback-entry-audit-t9r-<serviço>, um serviço por vez (OK do owner
dado). Falha em PROD → rollback e BLOCKED X7.

VERIFICAÇÃO EM PROD (antes de parar)
1. execute entry_audit.run pela CLARA (conector MCP de PROD, usuário com access) para 11/11/2026,
   filial 01, NF-e + CT-e → acompanhar read entry_audit.analysis até done.
2. execute entry_audit.rerun da análise de 12/11 → 5 ocorrências, 1 Alta, nota B limpa.
3. execute entry_audit.resolve e entry_audit.reopen em UMA ocorrência Média de 12/11 (usuário de
   teste, não pessoa real) → status resolved e depois pending, com histórico.
4. knowledge(search) com a ficha citada (R3).
5. read unmatched com os campos de R4 preenchidos.
Se o conector MCP de PROD exigir usuário real, rodar 1–5 pela mesma camada in-process apontada para
PROD e dizer isso no report; o owner refaz pela CLARA.

REPORT
Formato da track.md Parte 9, um bloco por R1–R5, com: causa (arquivo:linha), correção (SHA), teste
(PASS/FAIL), evidência de HML e de PROD, contagens antes/depois, tags de rollback, quadro de status
e registro atualizados. Parar ao concluir (nova verificação do owner pela CLARA).
```
