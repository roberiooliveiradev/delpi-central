# 13 — Decisão do Product Master: intenção e limite de execução como princípio de produto

**TASK:** `DELIA-C3-STAGE-02-B2-PRODUCT-PRINCIPLE-DECISION-01`
**DATA:** 2026-10-16
**BASE_HEAD REMOTO CONSULTADO:** `8786b605ae2ca3b108c31d64cc1cf32748a13c5f`
**TIPO:** decisão de produto/guardrail, documentação apenas.
**STATUS:** `PRODUCT_PRINCIPLE=APPROVED`; `TECHNICAL_CONTRACT=TO_DESIGN`; `ARCHITECTURE_DECISION_REQUIRED` permanece para D1/D2/D3.
**SOURCE OF APPROVAL:** concordância explícita do Product Master na coordenação com o princípio explicado: DÉLIA pode executar diretamente quando legitimamente permitido, mas não pode converter um pedido de preparação sem aplicação em ACT por erro de interpretação do LLM. A concordância também apoia **estudar e formalizar** evidência explícita e estruturada da intenção para execução; não escolhe nem autoriza uma solução de implementação.

## 1. Direção aprovada

1. DÉLIA continua capaz de entender solicitações em linguagem natural, investigar, orientar, preparar e conduzir ações governadas por MCP/Domain APIs, com o mínimo de perguntas necessárias e sem perda da proatividade aprovada.
2. A distinção `READ != PREPARE != ACT` é vinculante. Uma solicitação limitada a preparar/pré-visualizar/avaliar **não deve ser promovida a ACT** por classificação incorreta, incompleta ou excessivamente permissiva do LLM.
3. ACT legítimo pode prosseguir diretamente **quando o contrato e os gates aplicáveis permitirem**. Não foi aprovada confirmação universal nem proibição geral de continuação direta prevista em ledger §6.140.
4. A proposta de intenção do modelo (`goal_class`, `execution_bound`, outras saídas) é HYPOTHESIS e **não pode, sozinha, constituir evidência suficiente para ampliar execução**. Estudar a forma contratual de preservar evidência explícita e verificável do escopo de execução indicado pelo usuário, sem atribuir autorização Core/Domain a frontend, modelo ou provider.
5. A proteção precisa ser provider-neutral, usar os mecanismos existentes e falhar de forma segura na incerteza relevante; sem copiar regras de negócio de MCPs nem criar um segundo planner.
6. Segurança contratual deve preservar a experiência conversacional: o sistema pergunta quando uma decisão necessária não estiver legitimamente estabelecida, não por formalidade em toda interação.

**Cláusula interpretativa:** isto é uma **direção de produto aprovada**, não uma alegação de capacidade técnica atual, nem a decisão de exigir confirmação estruturada para todo ACT. Uma garantia absoluta de interpretação do texto natural não está comprovada e não deve ser prometida. A forma de prova positiva/escopo da execução requer solução validada e revisão arquitetural.

## 2. Contexto e evidência que motivaram o princípio

- [11 — Diagnóstico de Stage 02R2](./11-stage-02r2-execution-bound-diagnosis.md), commit `4a0027863b0116f5d9e9353b8ad9d8080495be6d`, ledger §6.177: FakeProposalModel/FakeProvider reproduziram 10 falhas conhecidas (`xfail(strict=True)`) quando texto proíbe aplicar e modelo retorna `unrestricted`, omite ou invalida bound; 6 controles positivos; suíte 1091 PASS + 10 XFAIL reportada pelo executor.
- [12 — Revisão independente](./12-stage-02r2-independent-review-and-decision-request.md), ledger §6.178: `ACCEPT_WITH_RESIDUAL` apenas para o diagnóstico; etapa 02 **não aceita**, B1 PASS estrutural, B2 REWORK.
- `max_execution_stage='prepare'` já existe como teto reduction-only e impede ACT mesmo com bound LLM incorreto; ausência de evidência confiável do limite no request não é solucionada por adicionar outro prompt.
- A continuação direta com `confirmation_requirement.explicit_user_confirmation=false` é mecanismo congelado de §6.140 e continua exigindo todos os outros gates de autoridade, Policy/Decision, execução, audit e Outcome.

## 3. O que NÃO foi decidido nesta aprovação

| Item | Estado |
| --- | --- |
| D1 — Quem fornece e como validar evidência estruturada do escopo/consentimento de ACT, incluindo pedidos em linguagem livre e continuação owner-direct | `ARCHITECTURE_DECISION_REQUIRED` — contract-first, owners e consumers a inventariar |
| D2 — Precedência quando `confirmation.decision=CONFIRM` contradiz a mensagem no mesmo turno (`não aplique`) | `ARCHITECTURE_DECISION_REQUIRED`; nenhum bypass/exploit produtivo afirmado |
| D3 — Autorizar mitigação C (bound ausente/inválido → clarificação/fail-closed) como correção parcial | `TO_DECIDE`; C não corrige classificação positiva errada de `unrestricted` |
| Novo segundo LLM/gate semântico, regex de comandos, parser, novo planner, confirmação universal ou exigência indiscriminada de clique | `NOT_AUTHORIZED`; necessidade/efeitos não comprovados |
| Alterar owner confirmation policy §6.140, Core/Domain AuthZ, limites de fase ou source of truth | `NOT_AUTHORIZED` |
| Etapa 02 concluída; Etapa 03 iniciada; implantação/rollout | `NOT_AUTHORIZED` |

## 4. Próxima etapa documental bounded (sem implementação)

Revalidar HEAD/git status, Project Instructions/.cursor, autoridades 16→50→17→49→51→52→21→20→25→arquitetura técnica→24→60/tema→ledger. Inventariar especificamente o contrato `InteractiveTurnRequest.max_execution_stage`, a origem de qualquer sinal estruturado do usuário, consumers do teto, `_understand_goal`, `_attempt_prepare`, `_attempt_confirmation` e Core/Domain/Policy/Decision.

Produzir **uma proposta de contrato para a coordenação**, preservando alternativas e tradeoffs: origem de evidência, semântica `PREPARE`/`ACT`, redução de teto, representação de ausência/negação/conflito, compatibilidade com owner-direct §6.140, fluxo de CONFIRM contraditório, backward compatibility, rollback, autorização e testes de segurança. Demonstrar `EXISTING_EQUIVALENT` e `REUSE_DECISION`; não construir capability/engine/interface por presunção.

STOP em conflito: `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED` antes de contrato/implementação. Qualquer contrato material passa por aprovação explícita, teste RED/holdout/generalização e revisão independente no SHA/config.

## 5. Estado de execução inalterado

`B1=PASS_STRUCTURAL` (harness, não real-model acceptance); `B2=REWORK`; `STAGE_02_ACCEPTED=NO`; `STAGE_03_AUTHORIZED=NO`; `C3_EXECUTED=NO`; `C4_AUTHORIZED=NO`; `C5_AUTHORIZED=NO`; `NEXT=RETURN_TO_ARCHITECTURE_COORDINATION`.

**Não há alteração de runtime, policy, permission, contrato produtivo, testes ou fase nesta decisão documental.**