# 12 — Revisão independente da Etapa 02R2: diagnóstico B2 e decisão pendente

**TASK:** `DELIA-C3-CONVERSATIONAL-INTELLIGENCE-GAP-CLOSURE-01-STAGE-02R2-DIAG-INDEPENDENT-REVIEW`
**DATA:** 2026-10-16
**REVIEWED_SHA/BASE_REMOTE_HEAD:** `4a0027863b0116f5d9e9353b8ad9d8080495be6d`
**VERDICT:** `ACCEPT_WITH_RESIDUAL` **somente para o diagnóstico**; `STAGE_02_ACCEPTED=NO`, `B2=REWORK`, `STAGE_03_AUTHORIZED=NO`, `ARCHITECTURE_DECISION_REQUIRED` continua pendente.
**EVIDENCE_MODE:** leitura independente do commit, harness e contracts publicados no GitHub. **INDEPENDENT_TEST_EXECUTION=TEST_NOT_RUN**, working tree local TO_INVENTORY, nenhum runtime/write/deploy alterado.

## 1. Reancoragem e decisões superiores

Consultados Project Instructions/.cursor como regras de reanchor, 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → 02 → 24 → specs 60/69/70, personality/02 e ledger §§6.126/6.130/6.133/6.140/6.141/6.145/6.171–6.177; plano C3 02/03/05/10/11. Verificações restritas às cláusulas pertinentes; fase/NEXT seguem 16 + ledger no HEAD.

Preservar: uma DÉLIA provider-neutral; owner/Domain como autoridade de negócio; Core live AuthZ; Policy/Decision; PREPARE != ACT; teto reduction-only; confirmação owner-sealed (§6.140); modelo HYPOTHESIS nunca permission/FACT; sem planner/registry/MCP-specific branches ou prosa factual livre (§6.145).

## 2. Evidence review

Commit 4a002786 contém exatamente: um test harness adicional `delia-api/tests/test_stage02r2_execution_bound_diagnosis.py`, relatório 11, README e ledger §6.177. Nenhum arquivo `delia-api/app` foi modificado pelo commit.

O harness contém 16 cenários coletados em 11 funções, incluindo 6 parametrizações do DIAG-07; 10 testes usam `xfail(strict=True)` para registrar violação da assertiva de segurança `ACT não deve ocorrer quando o texto proíbe aplicar`, e 6 controles não-xfail. **O executor reportou** `1091 passed + 10 xfailed (exit 0)` na suite completa, não reexecutada pelo revisor. XFAIL é FAIL de segurança conhecido, não sucesso funcional.

### PROVEN por inspeção de runtime/harness

- Para texto `Prepare um cadastro, mas não aplique`, proposal `goal_class=create_or_modify, execution_bound=unrestricted`, ceiling request None, owner READY e owner `explicit_user_confirmation=false`, o caminho direto de ACT é elegível, incluindo `commit_record` nas fakes. Mesmo defeito com bound ausente ou inválido, e com capabilities renomeadas.
- `_understand_goal` interpreta o `execution_bound` a partir da proposta LLM; ausente/inválido normaliza para `unrestricted`, sem diferenciar valor afirmado e não interpretado.
- `max_execution_stage='prepare'` no request continua vinculante mesmo quando o modelo produz `unrestricted` — `PASS` estrutural do teto reduction-only.
- Com texto de ação sem limitação, `unrestricted` e owner direct, a continuação governada segue disponível no cenário scripted; §6.140 continua válido.
- O path `confirmation is not None` retorna antes da chamada `_understand_goal`, e `_attempt_confirmation` não recebe `input_text`; DIAG-08 demonstra precedência operacional atual de confirmação estruturada, mas a precedência **normativa** do texto contraditório não está especificada. Não alegar exploit real.

### Limites de evidência

Todos os defeitos demonstrados são com FakeProposalModel/FakeProvider. Não há taxa medida de classificação do modelo real, autorização live do Core/Domain, writes reais nem task outcome empresarial. `REAL_MODEL=TEST_NOT_RUN`; `INDEPENDENT_TEST_EXECUTION=TEST_NOT_RUN`. Nenhum PASS de segurança completo.

## 3. Revisão das alternativas (decisões NÃO aprovadas)

| Alternativa | Correção comprovada pelo diagnóstico | Limite/riscos | Estado |
| --- | --- | --- | --- |
| A — teto estruturado reduction-only | Bloqueia ACT quando request já contém `max_execution_stage=prepare`; reutilização PROVEN | Não transforma automaticamente texto livre em campo estruturado; frontend/model inference não é authority | EXISTING_EQUIVALENT=YES, REUSE |
| B — segunda leitura semântica antes de ACT | Poderia detectar contradição positiva (hipótese) | Outro modelo também pode errar; não é prova independente nem safety gate determinístico, aumenta custos/latência | TARGET/ADR se pretendida; NÃO APROVADA |
| C — campo ausente/inválido não vira `unrestricted` | Mitiga DIAG-02/03 com clarificação fail-closed (proposta plausível) | NÃO fecha DIAG-01/07/09 onde o modelo afirma positivamente `unrestricted` errado | EXTEND candidata; NÃO implementada/autorizada |

**Conclusão de segurança:** não é justificável afirmar que C resolve B2. Nem segunda chamada LLM elimina o problema de confiança; ela seria outro sinal falível, não fonte de autorização.

## 4. Perguntas de decisão ao Product Master / coordenação

**D1 — Qual é a condição explícita autorizada para ACT proveniente de pedido em linguagem livre?** Hoje o contrato só tem teto estruturado (request) e bound inferido pelo modelo. Para garantir segurança mesmo com misclassification positiva, é necessária prova da intenção de executar fora da simples proposta LLM, ou restringir o fluxo à preparação na ausência dessa prova. Esta é escolha de produto/contrato, não mero ajuste de prompt. Um controle user-facing explícito e escopado para executar poderia ser investigado como candidata, desde que o dado represente ação direta do usuário e NÃO estado inferido do frontend. Isso pode restringir os caminhos de owner-direct, portanto necessita ADR/aceite contra §6.140. Nenhuma alteração foi autorizada.

**D2 — Como tratar texto 'não aplique' que acompanha `confirmation.decision=CONFIRM`?** Confirmar o PREPARE selado e ignorar texto é o comportamento de hoje; o contrato precisa escolher precedência e tratar contradição de forma não ambígua. Recomendação para avaliação: operação contraditória não deve executar silenciosamente; preservar o teto do request. Não alterar confirmation lifecycle até decisão.

**D3 — A mitigação C deve ser autorizada como correção parcial separada?** Recomendação: pode ser aprovada futuramente como fail-closed de contrato, mas não deve desbloquear Etapa 03 enquanto o DIAG-01 permanecer sem política aprovada e testes completos.

É impossível demonstrar uma garantia semântica absoluta sobre texto natural arbitrário somente com saídas potencialmente erradas de LLM. Proposta de contrato com sinal de intenção explícito/reduction-only e UX/consumer legítimos deve passar ownership/Abstraction Gate, avaliação de §6.140, segurança e acceptance. Não aprovar por conveniência novo parser regex, superprompt, segundo planner ou confirmação universal.

## 5. Veredicto e NEXT

`STAGE_02R2_DIAG=ACCEPT_WITH_RESIDUAL` — evidência diagnóstica adequada ao problema bounded; conclusões sobre solução permanecem PLANNED/TO_INVENTORY. `B1=PASS_STRUCTURAL`, `B2=REWORK`, `STAGE_02_ACCEPTED=NO`, `STAGE_03_AUTHORIZED=NO`.

`ARCHITECTURE_DECISION_REQUIRED`: D1 condição de execução em linguagem natural com falha do modelo, D2 precedência CONFIRM↔texto, D3 ordem/alcance da mitigação C. Aguardar decisão explícita do Product Master e posterior task bounded. Sem fase, rollout, execução real, novo prompt ou implementação autorizados por este review.

NEXT = RETURN_TO_ARCHITECTURE_COORDINATION
