# Minha DELPI Copilot — Especificação de Domain Playbooks

**Status:** contrato arquitetural proposto  
**Objetivo:** transformar métodos de trabalho corporativos em conhecimento operacional estruturado e reutilizável pelo Copilot.

## 1. Definição

`Domain Playbook` representa um método, procedimento analítico ou roteiro de decisão que o Copilot pode usar para organizar uma tarefa.

Ele não é um agente e não é um workflow técnico de endpoints.

Exemplos:

- análise 8D;
- Ishikawa;
- 5 Porquês;
- triagem de não conformidade;
- análise de desenho técnico;
- análise de atraso de entrega;
- análise de risco de fornecimento;
- preparação de reunião de engenharia;
- análise de variação financeira.

## 2. Separação obrigatória

```text
Playbook
→ método / evidências / perguntas / critérios

Workflow Runtime
→ plano executável / dependências / status

Capability
→ ação disponível

OpenAPI/Action Catalog
→ contrato técnico da ação
```

O playbook pode pedir semanticamente uma evidência ou capability, mas não deve conter path/method/operationId como roteamento.

## 3. Estrutura conceitual

```json
{
  "schemaVersion": 1,
  "key": "quality.8d",
  "version": "1.0.0",
  "label": "Análise 8D",
  "purpose": "Estruturar investigação e plano de ação para problema de qualidade.",
  "applicability": {
    "domains": ["quality"],
    "signals": ["nonconformity", "customer-complaint", "recurrence"]
  },
  "inputs": ["problemStatement", "evidenceRefs"],
  "stages": [],
  "evidenceChecklist": [],
  "decisionRules": [],
  "recommendedCapabilities": [],
  "artifactTemplates": [],
  "completionCriteria": [],
  "safetyNotes": [],
  "owner": "quality-owner",
  "status": "active"
}
```

## 4. Stages

Uma etapa descreve o que precisa ser resolvido, não como chamar tecnicamente uma API.

Exemplo:

```json
{
  "stageId": "containment",
  "goal": "Definir contenção imediata",
  "requiredEvidence": ["affectedScope", "riskAssessment"],
  "optionalCapabilityKinds": ["business.read", "knowledge.search"],
  "produces": ["containmentProposal"]
}
```

## 5. Evidence checklist

Playbooks devem indicar evidências esperadas para reduzir respostas superficiais.

Exemplo para análise de atraso:

- carteira/pedido;
- estoque disponível;
- ordens de produção;
- compras abertas;
- lead times;
- bloqueios de qualidade;
- eventos/logs relevantes;
- limitações de dados.

O Copilot deve distinguir:

```text
PROVEN
INFERRED
MISSING
NOT_APPLICABLE
```

## 6. Decision rules

Regras podem orientar análise, mas não podem bypassar policy.

Exemplo:

```text
se estoque = 0 e compra crítica atrasada
→ classificar risco de abastecimento
→ recomendar revisão com Compras
```

Essa recomendação não cria automaticamente uma solicitação sem capability/policy adequada.

## 7. Playbook → Workflow

O planner pode converter um playbook aplicável em plano operacional:

```text
playbook stages
+ capabilities autorizadas
+ contexto atual
+ dependências
→ WorkflowPlanV1
```

O workflow resultante deve ser observável e pode divergir do playbook quando etapas não forem aplicáveis, registrando reason codes.

## 8. Playbooks multimodais

Playbooks podem exigir inspeção de anexos.

Exemplo `engineering.drawing-review`:

```text
1. identificar revisão/documento
2. extrair quadro/título/notas/cotas críticas quando possível
3. identificar símbolos/tolerâncias relevantes
4. correlacionar com item/processo
5. consultar normas/procedimentos autorizados
6. listar riscos, dúvidas e evidências
7. gerar checklist ou parecer preliminar
```

## 9. Playbooks não são SOP executável cego

Mesmo que um procedimento interno tenha sequência definida, o Copilot deve:

- validar contexto;
- verificar applicability;
- respeitar versões vigentes;
- explicitar evidência faltante;
- não inventar conclusão;
- confirmar writes quando policy exigir.

## 10. Conhecimento e normas

Playbook pode referenciar knowledge categories/scopes semanticamente.

Normas/documentos precisam permanecer no RAG/knowledge store com controle de versão e ACL.

Não copiar documento inteiro para o playbook.

## 11. Versionamento

Mudança de decisão, critério ou sequência material exige nova versão.

Telemetry/evidence deve registrar:

```text
playbookKey
playbookVersion
contentHash
stagesApplied
stagesSkipped
```

## 12. Evals

Cada playbook relevante deve possuir casos:

- cenário completo;
- evidência faltante;
- evidência contraditória;
- cenário sibling;
- não aplicável;
- cross-domain;
- injection em documento/evidência;
- write proposto mas não autorizado;
- version regression.

## 13. Administração e autoria

Fluxo recomendado:

```text
draft
→ domain review
→ architecture/schema validation
→ security review quando necessário
→ eval
→ published
→ deprecated
```

Owners de domínio podem evoluir conteúdo sem editar o planner central.

## 14. Playbooks iniciais de referência

### Qualidade

- `quality.8d`;
- `quality.root-cause`;
- `quality.nonconformity-triage`;
- `quality.customer-complaint-analysis`.

### Engenharia

- `engineering.drawing-review`;
- `engineering.change-impact-analysis`;
- `engineering.technical-comparison`.

### Suprimentos

- `supplies.shortage-risk`;
- `supplies.purchase-delay-analysis`;
- `supplies.supplier-comparison`.

### Operação cross-domain

- `operations.delivery-delay-analysis`.

A implantação real deve começar por poucos playbooks de alto valor e alta disponibilidade de evidência.