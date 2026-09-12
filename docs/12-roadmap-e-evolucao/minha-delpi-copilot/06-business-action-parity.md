# 06 — Business Action Parity

## 1. Objetivo

Garantir que toda operação material disponível na UI possua um use case/API reutilizável pelo Copilot sob as mesmas regras de negócio e autorização.

> Se a UI consegue executar uma ação de negócio, o Copilot deve conseguir usar o mesmo contrato quando o usuário estiver autorizado — sem automatizar a tela.

## 2. Anti-padrão

```text
Copilot
→ abre tela
→ procura botão/input
→ preenche DOM
→ clica salvar
```

Não é arquitetura padrão. Se não existir API/use case, o gap deve ser tratado no domínio; browser/DOM workaround exige decisão excepcional explícita e não torna a operação AI-ready.

## 3. Padrão correto

```text
UI ──────────────┐
                 ▼
           Use Case/API
                 ▲
Copilot ─────────┘
```

## 4. Requisitos Copilot-ready

Uma operação deve possuir, conforme aplicável:

- business owner;
- use case/contract claro;
- HTTP/API ou internal capability tipada;
- OpenAPI quando HTTP;
- input/output schema;
- errors;
- RBAC;
- risk/sensitivity;
- Decision Gate policy;
- idempotency/concurrency semantics;
- correlation/audit para writes;
- tests;
- outcome verificável;
- entity/source metadata suficiente para presentation/evidence.

## 5. Reads

C3 libera generic reads somente após gates OpenAPI-first aplicáveis.

Reads devem:

- validar schema/args;
- revalidar authorization;
- normalizar outcome;
- registrar source/freshness/evidence quando material;
- não mutar estado inesperadamente.

## 6. Writes

C4 libera writes após Decision Gate foundation existir.

Fluxo:

```text
intent
→ allowed action
→ grounded arguments
→ schema validation
→ RBAC/policy
→ impact preview
→ Decision Gate
→ revalidation
→ execute
→ verify outcome
→ evidence/audit/deep link
```

## 7. Decision Gate

Não usar um booleano `requiresConfirmation` como modelo final.

Policy pode resultar em:

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Decision deve estar vinculada a arguments/evidence/impact relevantes e expirar/invalidate conforme contrato.

## 8. Destructive/high-risk

Ações como:

```text
cancelar
excluir
rejeitar irreversivelmente
aprovar alto impacto
alterar dado financeiro sensível
```

podem exigir gate mais forte, approver e audit reforçado.

## 9. Formulário não é contrato

O schema vem do use case/API.

Exemplo:

```text
User: “Crie uma solicitação de matéria-prima para o item X, prioridade alta.”

API requires:
item
reason
priority
unit

Grounded:
item + priority
Missing:
reason + unit
→ clarify somente missing required
→ Decision Gate quando policy exigir
→ execute
```

## 10. Validation

```text
AI binder/validator
→ early feedback

Domain API/use case
→ definitive validation/business authority
```

Não relaxar backend rules para IA.

## 11. Outcome e Evidence

Write só pode ser narrado como executado após outcome real.

Possíveis estados/erros:

```text
validation_error
permission_denied
not_found
conflict
policy_blocked
decision_required
decision_expired
provider_unavailable
timeout
ambiguous_outcome
business_rule_violation
partial_failure
```

Ambiguous outcome exige verificação/reconciliation antes de retry cego.

## 12. Idempotency

Preferir garantia do domínio.

Retry write somente quando:

- idempotency suportada/provada; ou
- reconciliation demonstra que efeito não ocorreu e policy permite.

Isso é necessário para Durable Workflow/reload futuro e por isso semantics são definidas em C0.

## 13. Coverage matrix por app

| UI function | Use case/API | OpenAPI | Permission | Risk | Decision Gate | Idempotency | Outcome/Evidence | AI-ready level |
|---|---|---|---|---|---|---|---|---|

A matriz deve ser baseada em código/contratos reais.

## 14. Ordem canônica de parity

```text
C3 reads de alto valor
→ cross-domain reads/Graph
→ C4 prepare/Decision Gate
→ non-destructive writes
→ approvals/high-risk/destructive
→ C5 composição durável
```

Não implementar “create request demo” antes da foundation de Decision/idempotency só para demonstrar write.

## 15. Iframe

Mesmo que a UI esteja em iframe:

```text
Copilot → Business Action/API
```

Nunca `view.click_button` como substituto.

## 16. Generalization

Novo endpoint/provider semanticamente bem descrito e permitido deve funcionar pelo pipeline genérico sem selector específico por path/provider/opId.

## 17. Benefício

Paridade bem implementada melhora simultaneamente UI, integrações, automação, workflow e Copilot porque força o negócio para contracts reutilizáveis e verificáveis.