# Minha DELPI Copilot — Especificação de Expertise Packs

**Status:** contrato arquitetural proposto  
**Objetivo:** permitir especialização dinâmica do Copilot sem criar agentes independentes por departamento.

## 1. Definição

`Expertise Pack` é um pacote versionado de conhecimento operacional e heurísticas de análise que melhora a atuação do mesmo Copilot em um domínio.

Ele responde principalmente a:

- quais conceitos importam neste domínio?;
- quais evidências devem ser buscadas?;
- quais métodos de análise são adequados?;
- quais playbooks podem ser úteis?;
- quais knowledge scopes devem receber boost?;
- quais capacidades multimodais são relevantes?;
- quais riscos/limitações devem ser explicitados?

Ele **não** define permissões nem endpoints.

## 2. Estrutura conceitual

```json
{
  "schemaVersion": 1,
  "key": "quality-industrial",
  "version": "1.0.0",
  "label": "Qualidade Industrial",
  "description": "Especialização para análise de qualidade, não conformidade e causa raiz.",
  "domains": ["quality", "manufacturing"],
  "signals": ["nonconformity", "inspection", "complaint", "8d"],
  "knowledgeScopes": ["global:quality"],
  "preferredPlaybooks": ["quality.8d", "quality.root-cause"],
  "recommendedCapabilities": ["knowledge.search", "analysis.compare", "document.vision"],
  "multimodalNeeds": ["image", "pdf", "technical-drawing"],
  "terminology": {},
  "analysisGuidance": [],
  "safetyNotes": [],
  "outputGuidance": [],
  "evalSuites": ["quality-core-v1"],
  "owner": "quality-platform-owner",
  "status": "active"
}
```

Esse shape é conceitual até C0.S1 confirmar padrões de schema existentes.

## 3. Campos permitidos

### Identidade e governança

- `key` estável;
- `version` SemVer;
- `label`;
- `description`;
- `owner`;
- `status`.

### Semântica

- `domains`;
- `signals`;
- `terminology`;
- `analysisGuidance`;
- `outputGuidance`.

### Integração

- `knowledgeScopes`;
- `preferredPlaybooks`;
- `recommendedCapabilities` por capability key sem endpoint técnico;
- `multimodalNeeds`;
- `evalSuites`.

## 4. Campos proibidos

Não incluir como authority de roteamento:

```text
path
method
operationId
provider-specific selector
pathMarker
operationIdMarker
routeSegment
parameterStrategy
permission override
JWT/secret
hardcoded department → endpoint
```

Se uma capability técnica depende de OpenAPI, a authority continua no OpenAPI + Action Catalog.

## 5. Ativação

Ativação deve ser automática e dinâmica.

```text
goals/context/attachments
→ expertise retriever
→ top-K packs
→ compatibility/policy filter
→ compose runtime context
```

O usuário não precisa escolher explicitamente o pack para uma pergunta normal.

A UI pode exibir de forma leve algo como:

> Conhecimentos aplicados: Engenharia · Qualidade

sem transformar isso em troca de agente.

## 6. Composição

Mais de um pack pode ser carregado no mesmo turno.

Regras de merge:

1. base behavior e policy sempre vencem;
2. guidance não pode reduzir safety;
3. knowledge scopes são união após autorização;
4. terminology é namespaceado quando houver colisão;
5. playbooks são candidates, não execução automática;
6. capability recommendation não concede access;
7. output guidance deve ser reconciliado pelo planner/presenter.

## 7. Ranking

O retriever pode considerar:

```text
goal/domain match
workspace app/entity
attachment type
recognized terminology
selected capability candidates
recent structured context
project preferences
```

Não usar `agent_id` como requisito para ativação.

## 8. Knowledge

Pack pode sugerir scopes, mas a recuperação final precisa aplicar:

```text
identity
+ knowledge ACL
+ tenant/context
+ source policy
```

Pack não amplia visibilidade de documentos.

## 9. Relação com capabilities

Expertise melhora seleção e interpretação, porém não substitui discovery.

```text
Expertise: "Qualidade Industrial"
Capability: "Consultar reclamações de cliente"
Action authority: OpenAPI/Action Catalog
```

## 10. Relação com playbooks

Um pack pode recomendar playbooks sem copiá-los.

Exemplo:

```text
quality-industrial
→ quality.8d
→ quality.root-cause
→ quality.nonconformity-triage
```

O playbook possui ciclo de vida próprio.

## 11. Relação com multimodalidade

Pack pode declarar que certos formatos merecem capacidades específicas.

Exemplo Engenharia:

```text
technical-drawing attachment
→ document vision
→ drawing structure extraction
→ engineering expertise
→ drawing-review playbook
```

## 12. Versionamento

Mudança de conteúdo que altera comportamento material deve incrementar versão e invalidar evidence afetada.

Registrar quando aplicável:

```text
expertisePackKey
expertisePackVersion
contentHash
evalSuiteHash
```

## 13. Observabilidade

Tracing deve registrar sem conteúdo sensível excessivo:

- packs candidates;
- packs selecionados;
- score/reasonCode;
- versão/hash;
- playbooks selecionados;
- knowledge scopes consultados;
- tools/capabilities utilizadas;
- outcome/eval.

## 14. Evals mínimos por pack

```text
positive domain query
semantic sibling
cross-domain composition
negative unrelated query
unauthorized knowledge
prompt injection from knowledge
attachment-triggered multimodal case
unknown/new pack contract test
version regression
```

## 15. Administração

Um pack só pode ir para `active` após:

```text
schema valid
owner definido
knowledge scopes válidos
playbook refs válidos
capability refs sem autoridade técnica duplicada
evals mínimos PASS
security review quando sensível
```

## 16. Packs iniciais recomendados

A criação efetiva deve ocorrer após inventário, porém o desenho deve suportar:

- `quality-industrial`;
- `product-engineering`;
- `supplies`;
- `commercial`;
- `finance`;
- `production`;
- `maintenance`;
- `hr`;
- `it-support`;
- `legal-compliance`.

Não criar todos antes de validar o contrato com 2–3 pilotos reais.