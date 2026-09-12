# Minha DELPI Copilot — Decision Gates e What-if Simulation

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Foundation:** Decision Gate contracts nascem em C0; engine em C4; Simulation em C7.

## 1. Decision Gate

O produto usa um único modelo de decisão proporcional ao risco:

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Não manter confirmation booleana como authority paralela.

## 2. Inputs de policy

Podem incluir:

- action/capability risk;
- sensitivity/data class;
- financial/operational impact;
- volume/scope;
- reversibility;
- arguments final;
- Evidence refs/freshness;
- user/approver permissions;
- autonomy level;
- business criticality.

O LLM pode ajudar a preparar preview, mas gate level é determinado por policy/owner governado.

## 3. Contracts compartilhados

Usar `DecisionGateRequest` e `DecisionGateDecision` C0.

Request conceitual:

```text
decisionId
action/capability ref
argumentsHash
impactSummary
evidenceRefs[]
risk/sensitivity
requiredGate
expiresAt
```

Decision conceitual:

```text
decisionId
decision/status
actor/approver ref
decidedAt
```

Não criar `DecisionGateV1` local com lifecycle incompatível.

## 4. Invalidation

Pode invalidar decisão anterior:

- arguments hash materialmente diferente;
- evidence crítica mudou/stale;
- permission/policy alterada;
- entity version/precondition mudou;
- expiry;
- approver perdeu autoridade.

Sempre revalidar antes de execute.

## 5. Approval workflow

```text
Decision request
→ pending approval
→ approved | rejected | expired
→ current-state revalidation
→ execute | block
```

Approval não substitui backend authorization.

## 6. What-if / Simulation

C7 pode introduzir simulações somente quando existe modelo/cálculo owner e reproduzível.

Exemplos:

- atraso adicional de fornecedor;
- priorização de OP;
- alteração de estoque de segurança;
- impacto de capacidade;
- cenários financeiros com modelo aprovado.

## 7. Simulation state

Uma simulação pode registrar semanticamente:

```text
simulationId
baseline Source/Evidence refs
assumptions
inputs
model/rule ref + version
outputs
limitations
createdAt
```

Isso não cria automaticamente um foundation global se um domínio já possuir contrato de simulação. Reutilizar/adapter antes de criar schema transversal.

## 8. Fontes de cálculo

Preferência:

1. domain simulation API/use case;
2. deterministic versioned rules;
3. governed analytical/optimization model;
4. LLM para estruturar/explain, não inventar números.

## 9. Simulate != Apply

```text
simulate
→ projected outcome
→ user reviews
→ separate Business Action intent
→ current RBAC/policy/Decision Gate
→ execute
→ verify actual outcome
```

Resultado simulado não é autorização nem outcome real.

## 10. Epistemic UX

Separar:

- observed baseline;
- user-provided input;
- assumption;
- model/calculation;
- projected result;
- confidence/uncertainty se metodologicamente suportada;
- limitations.

Simulation output nunca é FACT atual.

## 11. Security

- no hidden write;
- source RBAC;
- owner/version do modelo;
- sensitive assumptions redacted in logs;
- stale baseline handling;
- provider/data policy quando model/LLM envolvido.

## 12. Tests

Decision:

- each gate level;
- args changed;
- evidence changed;
- expired;
- approver unauthorized;
- revalidation.

Simulation:

- correct baseline;
- explicit assumptions;
- reproducible model;
- unsupported scenario;
- stale baseline;
- no hidden write;
- Apply requires new gate.

## 13. Mapping

```text
C0 → Decision contracts/semantics
C4 → Decision Gate Engine before production writes
C5 → wait_approval durability
C7 → Simulation pilots and autonomy-selected gates
```

## 14. Gate

- nenhum write material bypassa required Decision Gate;
- Simulation só é chamada assim quando existe cálculo/modelo governado;
- análise qualitativa sem modelo permanece hipótese/cenário, não simulação quantitativa.